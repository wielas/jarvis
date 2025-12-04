import pyttsx3
import asyncio
from src.logger import setup_logger

logger = setup_logger("Voice")

class Voice:
    def __init__(self):
        self.loop = asyncio.get_running_loop()
        self._engine = None
        # Initialize engine in a way that doesn't block immediately if possible, 
        # but pyttsx3 init is usually fast.
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', 150)  # Speed
            self._engine.setProperty('volume', 1.0) # Volume
            
            # Select a voice (optional, usually defaults to system default)
            voices = self._engine.getProperty('voices')
            if voices:
                # Prefer a female voice if available (often index 1 on some systems, but varies)
                # self._engine.setProperty('voice', voices[1].id)
                pass
                
            logger.info("Voice engine initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize voice engine: {e}")

    async def speak(self, text: str):
        """
        Speaks the given text asynchronously.
        """
        if not self._engine:
            logger.warning(f"Voice engine not available. Would say: '{text}'")
            return

        logger.info(f"Speaking: '{text}'")
        
        # Run the blocking speak loop in a separate executor
        await self.loop.run_in_executor(None, self._speak_sync, text)

    def _speak_sync(self, text: str):
        """
        Blocking speak function to be run in a thread.
        """
        try:
            # We need to create a new engine instance for each thread if the main one isn't thread safe
            # pyttsx3 is known to be finicky with threads. 
            # Best practice often involves a dedicated event loop for the engine or re-init.
            # However, runAndWait() blocks.
            
            # Simple approach: use the existing engine but ensure lock if needed.
            # For now, let's try direct usage. If it crashes, we might need a dedicated process.
            
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            logger.error(f"Error during speech: {e}")
