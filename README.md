# AURA — Pi Edge Smart Display

**AURA (Autonomous Ubiquitous Robotic Assistant)** is a Raspberry Pi–based edge AI smart display that combines **offline wake-word detection, local speech recognition, local LLM inference, text-to-speech, computer vision, and a real-time web dashboard**.

The project is designed as a self-contained assistant: voice interaction and AI inference are performed locally on the device, while the display exposes the assistant state and system telemetry.

![AURA Smart Display](images/capture.jpg)

## Why This Project?

AURA explores how a modern multimodal assistant can be built on affordable edge hardware without making a cloud API the central dependency.

The system combines:

- 🎙️ Offline wake-word detection
- 🗣️ Local speech-to-text
- 🧠 Local LLM inference
- 🔊 Local text-to-speech
- 👁️ Camera-based computer vision
- 🖥️ Browser-based smart-display UI
- 📊 Live CPU, RAM, and temperature telemetry
- ⚡ Raspberry Pi hardware integration
- 🧪 Unit and integration tests
- 🧩 3D-printable display enclosure assets

## System Architecture

```text
                         ┌─────────────────────┐
                         │   7" Smart Display   │
                         │   Web UI / Dashboard │
                         └──────────┬──────────┘
                                    │ WebSocket / HTTP
                                    ▼
┌──────────────┐          ┌─────────────────────┐
│ INMP441 Mic  │ ───────► │    AURA Runtime     │
└──────────────┘          │    src/main.py      │
                          └──────┬──────┬───────┘
                                 │      │
                    ┌────────────┘      └───────────────┐
                    ▼                                    ▼
             Wake Word Model                       Camera / Vision
            openWakeWord + ONNX                 OpenCV + TFLite
                    │                                    │
                    ▼                                    ▼
             Faster-Whisper                       Face Detection
                    │
                    ▼
              Ollama / Qwen
             Local LLM Runtime
                    │
                    ▼
                Piper TTS
                    │
                    ▼
          MAX98357A + Speaker

                 Raspberry Pi
        ┌─────────────────────────────┐
        │ CPU / RAM / Temperature     │
        │ ALSA / I2S Audio            │
        │ FastAPI Web Server           │
        └─────────────────────────────┘
```

### Interaction Flow

```text
STANDBY
   │
   ├── "Alexa" detected
   │
   ▼
RECORDING
   │
   ├── speech detected
   ├── silence / timeout
   ▼
TRANSCRIPTION
   │
   ▼
QUICK INTENT ──► instant system response
   │
   └────────────► Ollama / Qwen
                       │
                       ▼
                    RESPONSE
                       │
                       ▼
                    PIPER TTS
                       │
                       ▼
                    SPEAKING
                       │
                       ▼
                    STANDBY
```

## Hardware

| Component | Role |
|---|---|
| Raspberry Pi | Main edge-computing platform |
| 7-inch HDMI display | Smart-display interface |
| INMP441 | I2S microphone |
| MAX98357A | I2S audio amplifier |
| Speaker | Voice output |
| Camera | Computer-vision input |
| Optional Google VoiceHAT / ALSA audio hardware | Audio device routing |

The repository also contains **3D-printable enclosure and display-mount assets** under `hardware/3d-printed-enclosure/`.

## Software Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3 |
| API / UI backend | FastAPI + Uvicorn |
| Speech recognition | Faster-Whisper |
| Wake word | openWakeWord + ONNX |
| LLM | Ollama |
| Example model | Qwen 2.5 1.5B |
| Text-to-speech | Piper |
| Audio | sounddevice, SoundFile, ALSA |
| Vision | OpenCV + TFLite Runtime |
| Computer vision model | BlazeFace TFLite model |
| System telemetry | psutil |
| Frontend | HTML/CSS/JavaScript |
| Testing | pytest |

## Repository Structure

```text
.
├── audio_files/              # Audio samples / development recordings
├── hardware/
│   └── 3d-printed-enclosure/ # Display enclosure CAD/print assets
├── images/                   # Project and vision test images
├── models/                   # Local vision model assets
├── src/
│   ├── audio/
│   │   └── audio_to_text.py  # Audio device + Whisper helper
│   ├── gui/
│   │   ├── server.py         # FastAPI + WebSocket backend
│   │   ├── static/           # Frontend CSS/JS
│   │   └── templates/        # Smart-display HTML
│   ├── llm/
│   │   └── llm_node.py       # Ollama integration
│   ├── vision/
│   │   └── camera.py         # Camera + TFLite vision
│   └── main.py               # AURA orchestration
├── tests/
│   ├── audio_to_text_node_test.py
│   ├── llm_node_test.py
│   └── vision_node_test.py
├── pytest.ini
├── requirements.txt
└── start_aura.sh
```

## Key Engineering Features

### 1. Offline Voice Pipeline

AURA uses local models for the interactive voice pipeline:

```text
Microphone
   ↓
openWakeWord
   ↓
Faster-Whisper
   ↓
Ollama / Qwen
   ↓
Piper
   ↓
Speaker
```

No cloud speech-recognition or LLM API is required for this core pipeline.

### 2. Resource-Aware Interaction

Common system requests such as time and device status are handled deterministically before invoking the LLM.

For example, a status request can report:

- CPU utilization
- RAM utilization
- CPU temperature

This avoids unnecessary model inference for simple system queries.

### 3. Voice Activity Detection

Recording uses an RMS-based speech threshold together with:

- configurable silence duration
- maximum recording duration
- speech-start detection

This provides bounded recording rather than continuously accumulating audio.

### 4. Streaming LLM Responses

The main runtime requests streamed responses from Ollama and updates the display while the response is generated.

Short response constraints are used to make spoken interaction faster and more natural on edge hardware.

### 5. Real-Time Web Dashboard

The FastAPI backend provides:

- Smart-display HTML interface
- REST endpoints
- WebSocket state updates
- CPU telemetry
- RAM telemetry
- temperature telemetry
- touch/query interaction

The browser receives state transitions such as:

```text
STANDBY → THINKING → SPEAKING → STANDBY
```

### 6. Computer Vision

The vision module supports:

- local or network camera capture
- OpenCV frame handling
- TensorFlow Lite inference
- confidence filtering
- non-maximum suppression
- face detection

A BlazeFace-compatible TFLite model is included under `models/`.

### 7. Physical Product Integration

This is not only a software prototype. The repository also contains CAD/3D-print assets for a 7-inch display enclosure, making the project suitable for development toward a physical smart-display device.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/AnasHussaink/Autonomous-Ubiquitous-Robotic-Assistant-on-the-Edge.git
cd Autonomous-Ubiquitous-Robotic-Assistant-on-the-Edge
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

The dependency set includes FastAPI, Faster-Whisper, Ollama, OpenCV, TFLite Runtime, sounddevice, Piper-related runtime integration, pytest, and supporting libraries.

### 4. Prepare the local LLM

Install Ollama on the Raspberry Pi and pull the model used by the runtime:

```bash
ollama pull qwen2.5:1.5b
```

You can change the model in `src/main.py` according to the available hardware resources.

### 5. Configure audio

AURA expects the Raspberry Pi audio stack to expose the configured microphone and speaker through ALSA.

Verify the available devices before starting the application:

```bash
arecord -l
aplay -l
```

### 6. Configure Piper

Set the Piper executable and model paths in `src/main.py` if your installation uses different locations.

### 7. Start AURA

For the configured Raspberry Pi deployment:

```bash
./start_aura.sh
```

Or start the Python runtime directly:

```bash
export PYTHONPATH=.
python3 src/main.py
```

The FastAPI dashboard runs on port `8000`.

## Configuration

Important runtime settings are centralized in `src/main.py`, including:

```text
WAKE_WORD
WAKE_THRESHOLD
SILENCE_DURATION
MAX_RECORD_TIME
SPEECH_RMS_THRESHOLD
AUDIO_OUTPUT
PIPER_BIN
PIPER_MODEL
```

Keep local model files, credentials, and machine-specific network addresses out of version control.

## Testing

The repository includes tests for the audio, LLM, and vision components.

Run the test suite with:

```bash
pytest
```

Integration tests can be separated using the configured pytest marker:

```bash
pytest -m "not integration"
```

## Development Notes

This project is intentionally modular. The current implementation separates:

- **Audio** — microphone discovery and speech recognition
- **LLM** — Ollama communication
- **Vision** — camera capture and TFLite inference
- **GUI** — FastAPI, WebSocket communication, frontend assets
- **Runtime orchestration** — state machine and assistant lifecycle

This structure makes it possible to replace an individual model or hardware component without redesigning the entire application.

## Roadmap

- Improve conversational memory and multi-turn interaction.
- Expand vision beyond face detection.
- Improve wake-word robustness.
- Add richer device controls through the UI.
- Optimize model selection for Raspberry Pi performance.
- Improve hardware abstraction for different audio configurations.
- Add more automated integration tests.
- Expand the physical enclosure and device-management features.

## Engineering Skills Demonstrated

**Edge AI · Embedded Linux · Python · FastAPI · WebSockets · Speech Recognition · LLM Integration · Text-to-Speech · Computer Vision · OpenCV · TensorFlow Lite · ONNX · I2S Audio · ALSA · Raspberry Pi · Hardware Integration · Testing · 3D-Printed Hardware**

## License

MIT — see [LICENSE](LICENSE).
