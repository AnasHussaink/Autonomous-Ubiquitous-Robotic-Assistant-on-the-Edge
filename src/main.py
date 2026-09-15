import os
import sys
import time
import logging
import threading
import asyncio
import queue
import re
from datetime import datetime
import uvicorn
import numpy as np
import sounddevice as sd
import soundfile as sf
import psutil
import ollama
from openwakeword.model import Model
from faster_whisper import WhisperModel

from src.audio.audio_to_text import get_i2c_mic_id
from src.gui.server import (
    app as fastapi_app, 
    broadcast_state, 
    server_loop, 
    telemetry_loop,
    get_cpu_temp
)
import src.gui.server as gui_module

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("AURA-OS")

AUDIO_OUTPUT = "default"
PIPER_BIN = os.path.expanduser("~/piper/piper/piper")
PIPER_MODEL = "models/piper/en_US-lessac-medium.onnx"
RECORD_DIR = "audio_files"
RECORD_FILE = "live_input.wav"
AUDIO_PATH = os.path.join(RECORD_DIR, RECORD_FILE)

WAKE_WORD = "alexa"
WAKE_THRESHOLD = 0.5

SILENCE_DURATION = 0.9   # Snappier turn-around on user speech
MAX_RECORD_TIME = 8.0
SPEECH_RMS_THRESHOLD = 0.004

touch_query_queue = queue.Queue()

def handle_touch_query(prompt_text: str):
    logger.info(f"Touch Input Received: '{prompt_text}'")
    touch_query_queue.put(prompt_text)

gui_module.on_user_query_callback = handle_touch_query

def start_gui_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    gui_module.server_loop = loop
    loop.create_task(telemetry_loop())

    config = uvicorn.Config(
        app=fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="warning",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())

def speak_response(text: str):
    if not text:
        return
    sanitized = text.replace('"', '').replace("'", "").replace("\n", " ").strip()
    cmd = (
        f'echo "{sanitized}" | '
        f'{PIPER_BIN} --model {PIPER_MODEL} --output-raw | '
        f'aplay -r 22050 -f S16_LE -t raw -D {AUDIO_OUTPUT} 2>/dev/null'
    )
    os.system(cmd)

def play_sound(wav_path: str):
    if os.path.exists(wav_path):
        os.system(f"aplay -D {AUDIO_OUTPUT} {wav_path} 2>/dev/null")
    else:
        speak_response("Yes?")

def get_time_greeting() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        period = "Good morning"
    elif 12 <= hour < 18:
        period = "Good afternoon"
    else:
        period = "Good evening"
    return f"{period}! Hope you are having a wonderful day. Say Alexa to wake me up."

def listen_for_wake_word_or_touch(mic_id: int, oww_model: Model) -> str:
    oww_model.reset()
    stop_event = threading.Event()

    def callback(indata, frames, time_info, status):
        audio_mono = indata[:, 0]
        audio_16k = audio_mono[::3]
        audio_int16 = (audio_16k * 32767).astype(np.int16)

        oww_model.predict(audio_int16)
        score = oww_model.prediction_buffer[WAKE_WORD][-1]

        if score > WAKE_THRESHOLD:
            logger.info(f"Wake word '{WAKE_WORD}' detected (Confidence: {score:.2f})")
            stop_event.set()

    with sd.InputStream(device=mic_id, channels=2, samplerate=48000, blocksize=1280 * 3, callback=callback):
        while not stop_event.is_set():
            if not touch_query_queue.empty():
                return touch_query_queue.get()
            sd.sleep(30)
    
    return None

def record_until_silence(mic_id: int, output_path: str) -> bool:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    recorded_chunks = []
    stop_event = threading.Event()

    speech_started = False
    last_speech_time = None
    start_time = time.time()

    def vad_callback(indata, frames, time_info, status):
        nonlocal speech_started, last_speech_time
        audio_mono = indata[:, 0].copy()
        recorded_chunks.append(audio_mono)

        rms = np.sqrt(np.mean(audio_mono ** 2))
        now = time.time()

        if rms > SPEECH_RMS_THRESHOLD:
            if not speech_started:
                logger.info("Speech detected...")
            speech_started = True
            last_speech_time = now

        if speech_started and last_speech_time:
            if (now - last_speech_time) > SILENCE_DURATION:
                stop_event.set()

        if (now - start_time) > MAX_RECORD_TIME:
            stop_event.set()

    with sd.InputStream(device=mic_id, channels=2, samplerate=48000, blocksize=2400, callback=vad_callback):
        while not stop_event.is_set():
            sd.sleep(30)

    if not recorded_chunks:
        return False

    audio_array = np.concatenate(recorded_chunks, axis=0)
    sf.write(output_path, audio_array, 48000)
    return speech_started

def handle_quick_intents(user_prompt: str):
    """Instant deterministic replies for system queries (Zero LLM latency)."""
    p = user_prompt.lower()
    
    if "time" in p and ("what" in p or "tell" in p or "current" in p):
        current_time = datetime.now().strftime("%I:%M %p")
        return f"It is currently {current_time}."
    
    if "status" in p or "telemetry" in p:
        temp = get_cpu_temp()
        cpu = int(psutil.cpu_percent())
        ram = int(psutil.virtual_memory().percent)
        return f"System is nominal. CPU load is {cpu} percent, temperature is {temp}, and RAM usage is {ram} percent."

    if "about" in p or "capabilities" in p:
        return "I am Aura, an offline multimodal voice assistant running entirely on local Raspberry Pi hardware."

    return None

def stream_and_speak_smooth(user_prompt: str):
    # Check for instant deterministic answer first
    quick_reply = handle_quick_intents(user_prompt)
    if quick_reply:
        broadcast_state(state="SPEAKING", user_text=user_prompt, assistant_text=quick_reply)
        speak_response(quick_reply)
        broadcast_state(state="STANDBY", user_text=user_prompt, assistant_text=quick_reply)
        return quick_reply

    stream = ollama.chat(
        model="qwen2.5:1.5b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are AURA, an edge smart display assistant. "
                    "Provide a direct, conversational answer in exactly one short sentence under 14 words. "
                    "Never use bullet points, lists, colons, or semicolons."
                )
            },
            {"role": "user", "content": user_prompt}
        ],
        options={
            "num_predict": 35,       # Further reduced to guarantee 1.5s generation
            "temperature": 0.2
        },
        stream=True
    )

    buffer = ""
    full_response = []

    for chunk in stream:
        token = chunk["message"]["content"]
        buffer += token
        full_response.append(token)

        broadcast_state(
            state="SPEAKING",
            user_text=user_prompt,
            assistant_text="".join(full_response)
        )

        words = buffer.strip().split()
        # Reduced threshold to 5 words so speech triggers faster
        if len(words) >= 5 and re.search(r'[.!?]\s*$', buffer):
            to_speak = buffer.strip().replace(";", ",").replace("*", "")
            buffer = ""
            speak_response(to_speak)

    if buffer.strip():
        remaining = buffer.strip().replace(";", ",").replace("*", "")
        speak_response(remaining)

    final_text = "".join(full_response).strip()
    broadcast_state(state="STANDBY", user_text=user_prompt, assistant_text=final_text)
    return final_text

def main():
    logger.info("Initializing AURA-OS Smart Display System...")

    gui_thread = threading.Thread(target=start_gui_server, daemon=True)
    gui_thread.start()
    logger.info("AURA Dashboard active on port 8000")

    if not os.path.exists(PIPER_BIN) or not os.path.exists(PIPER_MODEL):
        logger.error("Piper TTS assets missing.")
        sys.exit(1)

    mic_id = get_i2c_mic_id()
    logger.info(f"Microphone Device Index: {mic_id}")

    logger.info("Loading openWakeWord model ('alexa')...")
    oww_model = Model(wakeword_models=[WAKE_WORD], inference_framework="onnx")

    logger.info("Pre-loading Faster-Whisper ('tiny.en')...")
    stt_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")

    welcome_msg = get_time_greeting()
    broadcast_state(state="STANDBY", assistant_text=welcome_msg)
    logger.info(f"Greeting: {welcome_msg}")
    speak_response(welcome_msg)

    logger.info("AURA-OS Armed. Press Ctrl+C to terminate.")

    try:
        while True:
            broadcast_state(state="STANDBY")
            logger.info(f"Standby: Listening for '{WAKE_WORD}' or Touch...")
            touch_prompt = listen_for_wake_word_or_touch(mic_id, oww_model)

            if touch_prompt:
                broadcast_state(state="THINKING", user_text=touch_prompt, assistant_text="...")
                logger.info(f"Processing Touch Prompt: \"{touch_prompt}\"")
                stream_and_speak_smooth(touch_prompt)
                continue

            broadcast_state(state="LISTENING")
            play_sound("sounds/yes.wav")

            logger.info("VAD Active: Listening for command...")
            has_speech = record_until_silence(mic_id, AUDIO_PATH)

            if not has_speech:
                logger.info("No speech detected. Returning to standby.")
                continue

            broadcast_state(state="THINKING")
            logger.info("Transcribing speech...")
            segments, _ = stt_model.transcribe(AUDIO_PATH)
            user_text = " ".join([s.text for s in segments]).strip()

            if not user_text:
                logger.info("No words recognized. Returning to standby.")
                continue

            logger.info(f"User: \"{user_text}\"")
            broadcast_state(state="THINKING", user_text=user_text, assistant_text="...")

            logger.info("Processing response...")
            stream_and_speak_smooth(user_text)

    except KeyboardInterrupt:
        logger.info("\nShutting down AURA-OS.")
        farewell = "Goodbye! Have a great day ahead."
        broadcast_state(state="STANDBY", assistant_text=farewell)
        speak_response(farewell)

if __name__ == "__main__":
    main()