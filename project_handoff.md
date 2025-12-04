# Project Handoff: The Local Voice Commander

## 1. Project Overview
**Goal**: Build a privacy-first, offline voice assistant ("Jarvis") to control a Smart Home.
**Core Philosophy**: Offline-first, Low Latency (<2s), Async-Native.

## 2. Hardware & Architecture
**Target Server**: IdeaPad Laptop (Ubuntu 24.04 LTS)
- **Specs**: i5-8250U, 8GB RAM, Nvidia 920MX.
- **Role**: Runs the AI Agent (Hearing + Brain).
- **Deployment**: Docker Containers (Bare Metal). *Decision: No Proxmox due to 8GB RAM limit.*

**Home Automation**: Raspberry Pi 4
- **Role**: Runs Home Assistant OS.
- **Integration**: Agent calls HA API to control devices (e.g., Shelly 2PM switches).

## 3. Tech Stack
- **Language**: Python 3.13
- **Wake Word**: `openwakeword` (Model: "Hey Jarvis"). *Why: CPU efficient.*
- **STT (Ears)**: `faster-whisper` (int8 quantization). *Why: Fast on CPU.*
- **Brain**: Ollama running **Phi-3** (3.8B). *Decision: Chosen over Llama 3 to prevent OOM on 8GB RAM.*
- **Orchestration**: `asyncio` + `sounddevice` (Non-blocking audio loop).

## 4. Current Progress (Phase 1 Complete)
**"The Hearing Aid"** is built and verified.
- **Code**:
    - `audio_engine.py`: Async loop, buffers audio, detects wake word, records 5s, transcribes.
    - `main.py`: Entry point.
    - `Dockerfile`: Debian-based Python image with PortAudio.
- **Status**:
    - Verified locally on Mac (Python venv).
    - Docker container built.
    - **Bug Fix**: Fixed `openwakeword` input shape error (flattened numpy array).

## 5. Next Steps (Phase 2: The Brain)
1.  **Ollama Setup**: Deploy Ollama container with Phi-3 model.
2.  **Intent Parsing**:
    - Create `brain.py`.
    - Define Pydantic models for intents (e.g., `TurnOnLight(device_name: str)`).
    - Connect transcribed text -> Ollama -> Structured JSON.

## 6. Quick Start (On New Machine)
1.  **Clone Repo**: Get the code.
2.  **Install Dependencies**:
    ```bash
    sudo apt install portaudio19-dev ffmpeg
    pip install -r requirements.txt
    ```
3.  **Run**:
    ```bash
    python main.py
    ```
