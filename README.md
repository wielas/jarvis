# Jarvis - Local Voice Commander

A privacy-first, offline voice assistant for Smart Home control.

## Architecture

The project is structured into modular components for better maintainability and scalability.

```
jarvis/
├── src/
│   ├── __init__.py
│   ├── config.py          # Centralized configuration (Dataclasses)
│   ├── logger.py          # Structured logging with color support
│   ├── audio_stream.py    # Async audio input stream handler (sounddevice)
│   ├── wake_word.py       # Wake word detection (openwakeword)
│   ├── transcriber.py     # Speech-to-text (faster-whisper)
│   └── engine.py          # Main orchestration logic
├── main.py                # Application entry point
└── requirements.txt       # Python dependencies
```

## Components

### 1. Audio Stream (`src/audio_stream.py`)
Handles the raw audio input from the microphone using `sounddevice`. It runs in a separate thread (via callback) and feeds audio chunks into an `asyncio.Queue`.

### 2. Wake Word Detector (`src/wake_word.py`)
Uses `openwakeword` to detect the wake word ("Hey Jarvis"). It loads the model efficiently and provides a simple `detect(chunk)` method.

### 3. Transcriber (`src/transcriber.py`)
Uses `faster-whisper` for local, offline speech-to-text. It runs the heavy transcription task in a separate thread executor to avoid blocking the main asyncio event loop.

### 4. Audio Engine (`src/engine.py`)
The brain of the "Hearing Aid". It manages the state machine:
- **LISTENING**: Waiting for the wake word.
- **RECORDING**: Capturing audio after wake word detection.
- **TRANSCRIBING**: Converting speech to text.

## Running the Project

### Prerequisites
- Python 3.12+
- PortAudio (`sudo apt install portaudio19-dev`)
- FFmpeg (`sudo apt install ffmpeg`)

### Setup
```bash
# Create venv
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Execution
```bash
python main.py
```

## Configuration
Configuration is managed in `src/config.py`. You can adjust:
- Sample rate and chunk size
- Wake word model and threshold
- Whisper model size (default: `base.en`)
- Recording duration
