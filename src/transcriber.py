from faster_whisper import WhisperModel
import numpy as np
import asyncio
from src.config import TranscriberConfig
from src.logger import setup_logger

logger = setup_logger("Transcriber")

class Transcriber:
    def __init__(self, config: TranscriberConfig):
        self.config = config
        self.model = None
        self.loop = asyncio.get_running_loop()
        self._load_model()

    def _load_model(self):
        logger.info(f"Loading Whisper Model ({self.config.model_size})...")
        try:
            self.model = WhisperModel(
                self.config.model_size, 
                device=self.config.device, 
                compute_type=self.config.compute_type
            )
            logger.info("Whisper Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper Model: {e}")
            raise

    async def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribes audio data to text.
        Runs the blocking transcribe call in a separate thread.
        """
        if not self.model:
            return ""

        # Convert to float32 and normalize to [-1, 1] if strictly int16
        # Whisper expects float32
        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32) / 32768.0
        else:
            audio_float = audio_data

        logger.debug("Starting transcription...")
        
        try:
            def _transcribe_sync():
                segments, _ = self.model.transcribe(audio_float, beam_size=self.config.beam_size)
                # Consume generator to force computation in thread
                return list(segments)

            # Run blocking transcribe in executor
            segments = await self.loop.run_in_executor(None, _transcribe_sync)
            
            text = ""
            for segment in segments:
                text += segment.text
                
            text = text.strip()
            logger.info(f"Transcribed: '{text}'")
            return text
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
