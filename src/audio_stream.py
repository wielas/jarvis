import asyncio
import sounddevice as sd
import numpy as np
from src.config import AudioConfig
from src.logger import setup_logger

logger = setup_logger("AudioStream")

class AudioStream:
    def __init__(self, config: AudioConfig):
        self.config = config
        self.queue = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
        self.stream = None
        self.running = False

    def _callback(self, indata: np.ndarray, frames: int, time: any, status: sd.CallbackFlags):
        """Callback for sounddevice input stream"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # We must use call_soon_threadsafe because this callback runs in a separate thread
        self.loop.call_soon_threadsafe(self.queue.put_nowait, indata.copy())

    def start(self):
        """Starts the audio input stream"""
        if self.running:
            return

        logger.info(f"Starting audio stream (Rate: {self.config.sample_rate}, Chunk: {self.config.chunk_size})")
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                blocksize=self.config.chunk_size,
                channels=self.config.channels,
                callback=self._callback,
                dtype=self.config.dtype
            )
            self.stream.start()
            self.running = True
            logger.info("Audio stream started successfully")
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            raise

    def stop(self):
        """Stops the audio input stream"""
        if not self.running:
            return

        logger.info("Stopping audio stream...")
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        self.running = False
        logger.info("Audio stream stopped")

    async def get_chunk(self) -> np.ndarray:
        """Async generator to yield audio chunks"""
        return await self.queue.get()

    def clear_queue(self):
        """Clears the internal queue"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
