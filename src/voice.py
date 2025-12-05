import pyttsx3
import asyncio
import threading
import queue
from src.logger import setup_logger

logger = setup_logger("Voice")

class Voice:
    def __init__(self):
        self.loop = asyncio.get_running_loop()
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="TTS-Thread")
        self._thread.start()
        logger.info("Voice engine thread started.")

    def _run_loop(self):
        """
        Runs the TTS engine in a dedicated thread.
        This ensures thread safety for pyttsx3/espeak.
        """
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 1.0)
            
            # Optional: Select voice
            # voices = engine.getProperty('voices')
            # if voices: engine.setProperty('voice', voices[1].id)
            
            while True:
                try:
                    text = self._queue.get()
                    if text is None: # Sentinel to stop
                        break
                    
                    logger.debug(f"Speaking: {text}")
                    engine.say(text)
                    engine.runAndWait()
                    self._queue.task_done()
                except Exception as e:
                    logger.error(f"Error in TTS loop: {e}")
                    
        except Exception as e:
            logger.critical(f"Failed to initialize TTS engine in thread: {e}")

    async def speak(self, text: str):
        """
        Queues the text to be spoken.
        This method is non-blocking.
        """
        logger.info(f"Queueing speech: '{text}'")
        self._queue.put(text)
        # We don't await here because we want to return control immediately
        # If we wanted to wait for speech to finish, we'd need a callback or future.

    def stop(self):
        """Stops the TTS thread"""
        self._queue.put(None)
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
