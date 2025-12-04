import asyncio
import numpy as np
from src.config import AppConfig
from src.logger import setup_logger
from src.audio_stream import AudioStream
from src.wake_word import WakeWordDetector
from src.transcriber import Transcriber
from src.brain import Brain
from src.home_assistant import HomeAssistantClient
from src.dispatcher import Dispatcher
from src.voice import Voice

logger = setup_logger("AudioEngine")

class AudioEngine:
    def __init__(self, config: AppConfig):
        self.config = config
        self.stream = AudioStream(config.audio)
        self.wake_word_detector = WakeWordDetector(config.wake_word)
        self.transcriber = Transcriber(config.transcriber)
        self.brain = Brain(config)
        self.ha_client = HomeAssistantClient(config.ha)
        self.dispatcher = Dispatcher(self.ha_client)
        self.voice = Voice()
        self.running = False

    async def start(self):
        """Starts the main event loop"""
        self.running = True
        
        # Ensure brain model is ready
        await self.brain.ensure_model()
        
        # Check HA connection
        await self.ha_client.check_connection()
        
        self.stream.start()
        logger.info("Engine started. Listening for commands...")
        
        # Greet the user
        await self.voice.speak("Jarvis is online.")
        
        try:
            await self._event_loop()
        except asyncio.CancelledError:
            logger.info("Engine task cancelled")
        finally:
            self.stop()

    def stop(self):
        """Stops the engine and releases resources"""
        self.running = False
        self.stream.stop()
        logger.info("Engine stopped")

    async def _event_loop(self):
        """Main processing loop: Listen -> Detect -> Record -> Transcribe -> Think -> Act -> Speak"""
        logger.info("State: LISTENING")
        
        while self.running:
            chunk = await self.stream.get_chunk()
            
            # 1. Wake Word Detection
            score = self.wake_word_detector.detect(chunk)
            
            if score >= self.config.wake_word.threshold:
                logger.info(f"Wake Word Detected! (Score: {score:.2f})")
                
                # 2. Record Audio
                logger.info("State: RECORDING")
                audio_buffer = await self._capture_audio(seconds=self.config.record_seconds)
                
                # 3. Transcribe
                logger.info("State: TRANSCRIBING")
                text = await self.transcriber.transcribe(audio_buffer)
                
                if text:
                    logger.info(f"User Command: {text}")
                    
                    # 4. Brain Processing
                    logger.info("State: THINKING")
                    intent = await self.brain.process(text)
                    logger.info(f"Intent: {intent}")
                    
                    # 5. Action Dispatch & Speech
                    if isinstance(intent, dict) and intent.get("intent") != "error":
                        logger.info("State: ACTING")
                        await self.dispatcher.dispatch(intent)
                        
                        # 6. Voice Feedback
                        if intent.get("intent") == "general_query":
                            response = intent.get("response")
                            if response:
                                await self.voice.speak(response)
                        elif intent.get("intent") == "light_control":
                             # Simple confirmation
                             action = intent.get("action", "switching")
                             location = intent.get("location", "lights")
                             await self.voice.speak(f"Turning {action} {location} lights.")
                        elif intent.get("intent") == "music_control":
                             await self.voice.speak("Playing music.")
                    
                else:
                    logger.warning("No speech detected or transcription failed.")
                
                # Reset to Listening
                logger.info("State: LISTENING")
                self.stream.clear_queue()

    async def _capture_audio(self, seconds: int) -> np.ndarray:
        """Captures audio for a fixed duration"""
        chunks_needed = int(self.config.audio.sample_rate * seconds / self.config.audio.chunk_size)
        audio_data = []
        
        for _ in range(chunks_needed):
            chunk = await self.stream.get_chunk()
            audio_data.append(chunk)
            
        return np.concatenate(audio_data).flatten()
