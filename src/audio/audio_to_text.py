import os
import logging
import sounddevice as sd
from faster_whisper import WhisperModel

logger = logging.getLogger("AudioDevice")

def get_i2c_mic_id():
    """
    Returns None to tell sounddevice to bind directly to ALSA's default device.
    With /etc/asound.conf configured, ALSA routes capture and playback straight
    to the Google voiceHAT hardware without PortAudio index ambiguities.
    """
    logger.info("Using system ALSA default audio device (voiceHAT via /etc/asound.conf)")
    return None

class SpeechRecognizer:
    def __init__(self, model_size: str = "tiny.en", device: str = "cpu", compute_type: str = "int8"):
        logger.info(f"Initializing Faster-Whisper ({model_size}) on {device} [{compute_type}]...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> str:
        if not os.path.exists(audio_path):
            logger.warning(f"Audio file not found: {audio_path}")
            return ""

        segments, info = self.model.transcribe(audio_path, beam_size=1)
        text = " ".join([segment.text for segment in segments]).strip()
        return text