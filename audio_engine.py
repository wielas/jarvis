import asyncio
import sounddevice as sd
import numpy as np
import openwakeword
from openwakeword.model import Model
from faster_whisper import WhisperModel
import os

class AudioEngine:
    def __init__(self, model_path="tiny.en"):
        self.sample_rate = 16000
        self.chunk_size = 1280  # 80ms
        self.q = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
        
        print("Loading Wake Word Model...")
        openwakeword.utils.download_models()
        self.oww_model = Model(wakeword_models=["hey_jarvis"])
        
        print(f"Loading Whisper Model ({model_path})...")
        # Use int8 for speed on CPU
        self.whisper_model = WhisperModel(model_path, device="cpu", compute_type="int8")
        
        self.running = False
        self.stream = None

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"Audio callback status: {status}")
        self.loop.call_soon_threadsafe(self.q.put_nowait, indata.copy())

    async def start(self):
        self.running = True
        # Start the stream
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            channels=1,
            callback=self._callback,
            dtype="int16"
        )
        self.stream.start()
        print("Audio Engine started. Listening for 'Hey Jarvis'...")
        
        try:
            while self.running:
                chunk = await self.q.get()
                # chunk is (1280, 1) int16
                
                # Feed to wake word model
                # openwakeword handles int16 numpy arrays directly
                prediction = self.oww_model.predict(chunk)
                
                # Check for wake word
                # prediction is a dict like {'hey_jarvis': 0.001, ...}
                if prediction["hey_jarvis"] >= 0.5:
                    print(f"\nWake word detected! (Score: {prediction['hey_jarvis']:.2f})")
                    await self.capture_and_transcribe()
                    
                    # Clear the queue to avoid processing old audio after the recording
                    # This helps avoid triggering immediately again if the user kept talking
                    while not self.q.empty():
                        self.q.get_nowait()
                    
                    print("Resuming listening...")

        except asyncio.CancelledError:
            print("Audio processing cancelled.")
        finally:
            self.stop()

    async def capture_and_transcribe(self):
        print("Recording command (5 seconds)...")
        
        seconds = 5
        chunks_needed = int(self.sample_rate * seconds / self.chunk_size)
        audio_data = []
        
        # We might have some chunks already in the queue, but we want 'fresh' audio mostly.
        # However, for a seamless experience, capturing a bit of the buffer might be good.
        # For now, let's just consume new chunks.
        
        for _ in range(chunks_needed):
            chunk = await self.q.get()
            audio_data.append(chunk)
            
        print("Processing audio...")
        # Flatten
        full_audio = np.concatenate(audio_data).flatten()
        
        # Convert to float32 for Whisper [-1, 1]
        full_audio_float = full_audio.astype(np.float32) / 32768.0
        
        print("Transcribing...")
        segments, info = self.whisper_model.transcribe(full_audio_float, beam_size=5)
        
        text = ""
        for segment in segments:
            text += segment.text
            
        print(f"--> User said: {text.strip()}")

    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        print("Audio Engine stopped.")
