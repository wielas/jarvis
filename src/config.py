from dataclasses import dataclass, field
import os

@dataclass
class AudioConfig:
    sample_rate: int = 16000
    chunk_size: int = 1280  # 80ms
    channels: int = 1
    dtype: str = "int16"

@dataclass
class WakeWordConfig:
    model_names: list[str] = None
    threshold: float = 0.5
    inference_framework: str = "onnx"

    def __post_init__(self):
        if self.model_names is None:
            self.model_names = ["hey_jarvis_v0.1"]

@dataclass
class TranscriberConfig:
    model_size: str = "base.en"
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 5

@dataclass
class BrainConfig:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model_name: str = os.getenv("OLLAMA_MODEL", "phi3")

@dataclass
class HomeAssistantConfig:
    url: str = os.getenv("HA_URL", "http://homeassistant.local:8123")
    token: str = os.getenv("HA_TOKEN", "")
    timeout: int = 5

@dataclass
class AppConfig:
    audio: AudioConfig = field(default_factory=AudioConfig)
    wake_word: WakeWordConfig = field(default_factory=WakeWordConfig)
    transcriber: TranscriberConfig = field(default_factory=TranscriberConfig)
    brain: BrainConfig = field(default_factory=BrainConfig)
    ha: HomeAssistantConfig = field(default_factory=HomeAssistantConfig)
    
    # Recording settings
    record_seconds: int = 5
    
    # Test mode flag
    test_mode: bool = False
