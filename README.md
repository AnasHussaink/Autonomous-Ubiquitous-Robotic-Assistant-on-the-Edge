# Pi Edge Smart Display — Local AI Assistant

A privacy-focused edge AI assistant and interactive smart display built around Raspberry Pi hardware. The system combines local speech processing, LLM reasoning, computer vision, web UI, and hardware audio I/O.

## Architecture

Microphone → speech recognition → local LLM → TTS → speaker  
Camera → Coral Edge TPU vision → FastAPI backend → display/UI

The backend separates audio, LLM, vision, API, and UI services so components can be developed and tested independently.

## Hardware

- Raspberry Pi 4/5
- Google Coral USB Edge TPU
- 7-inch HDMI display
- OV5647 CSI camera
- INMP441 I2S microphone
- MAX98357A I2S amplifier and speaker

## Software Stack

| Layer | Technology |
|---|---|
| Backend | Python + FastAPI |
| Speech-to-text | Whisper.cpp |
| LLM | Ollama / llama.cpp |
| Local models | Qwen / Llama-family |
| TTS | Piper |
| Vision | TensorFlow Lite + Coral Edge TPU |
| Frontend | React/Vue + Vite |
| Testing | pytest |
| Display | Chromium kiosk mode |

## Design Goals

### Privacy-first
Core speech, reasoning, and vision workloads are designed for local processing so sensitive data can remain on the device.

### Hardware acceleration
The Coral Edge TPU accelerates supported computer-vision workloads and reduces CPU load.

### Modular services
Audio, LLM, vision, API, UI, and hardware configuration are separated into focused modules.

## Project Structure

hardware/ — Raspberry Pi and ALSA configuration  
models/ — local model files, excluded from Git  
src/api/ — FastAPI routes  
src/audio/ — I2S, wake word, and TTS  
src/llm/ — prompts and local LLM integration  
src/vision/ — camera and Edge TPU processing  
tests/ — unit and integration tests  
ui/ — web interface  
scripts/ — setup and kiosk launch scripts

## Installation

The project targets Python 3.10+ on Raspberry Pi. Create an isolated environment, install the Python dependencies, configure the required local AI runtimes, and keep model weights and credentials outside Git.

For the configured Ollama workflow, the example model is qwen2.5:1.5b.

## Testing

Fast tests can be run without integration dependencies. Integration tests require the configured local AI services and hardware.

## Engineering Highlights

Edge AI on constrained hardware, local speech and language processing, hardware-accelerated vision, I2S audio, FastAPI orchestration, web-based dashboard development, and automated testing.

## Roadmap

Improve conversational state handling, expand vision, optimize inference latency, improve device-status UI, and add more autonomous assistant behaviours.

## License

MIT — see LICENSE.
