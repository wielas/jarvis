import asyncio
import sounddevice as sd
import numpy as np
import openwakeword
from openwakeword.model import Model
from faster_whisper import WhisperModel
from colorama import Fore, Style, init
import collections

# Initialize colorama
init(autoreset=True)

class AudioEngine:
    def __init__(self, model_path="base.en"):
        self.sample_rate = 16000
        self.chunk_size = 1280  # 80ms
        self.q = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
        
        print(Fore.CYAN + "Loading Wake Word Model...")
        openwakeword.utils.download_models()
        self.oww_model = Model(wakeword_models=["hey_jarvis"])
        
        print(Fore.CYAN + f"Loading Whisper Model ({model_path})...")
        # Use int8 for speed on CPU
        self.whisper_model = WhisperModel(model_path, device="cpu", compute_type="int8")
        
        self.running = False
        self.stream = None

    def _callback(self, indata, frames, time, status):
        if status:
            print(Fore.RED + f"Audio callback status: {status}")
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
        print(Fore.GREEN + "Audio Engine started.")
        
        try:
            await self.process_audio_loop()
        except asyncio.CancelledError:
            print(Fore.YELLOW + "Audio processing cancelled.")
        finally:
            self.stop()

    async def process_audio_loop(self):
        # State 1: Listening
        print(Fore.GREEN + "Listening for Wake Word...")
        
        while self.running:
            chunk = await self.q.get()
            
            # Feed to wake word model
            prediction = self.oww_model.predict(chunk)
            
            # Check for wake word
            if prediction["hey_jarvis"] >= 0.5:
                # State 2: Recording
                print(Fore.YELLOW + f"\nWake Word Detected! (Score: {prediction['hey_jarvis']:.2f}) Recording...")
                
                # Capture 5 seconds of audio
                audio_buffer = await self.capture_audio(seconds=5)
                
                # State 3: Transcribing
                print(Fore.CYAN + "Transcribing...")
                text = await self.transcribe_audio(audio_buffer)
                
                print(Fore.MAGENTA + f"User Said: {text}")
                
                # Reset to State 1
                print(Fore.GREEN + "Listening for Wake Word...")
                
                # Clear queue to avoid processing old audio
                while not self.q.empty():
                    self.q.get_nowait()

    async def capture_audio(self, seconds):
        chunks_needed = int(self.sample_rate * seconds / self.chunk_size)
        audio_data = []
        
        for _ in range(chunks_needed):
            chunk = await self.q.get()
            audio_data.append(chunk)
            
        return np.concatenate(audio_data).flatten()

    async def transcribe_audio(self, audio_data):
        # Convert to float32 for Whisper [-1, 1]
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        # Run blocking transcribe in executor
        segments, info = await self.loop.run_in_executor(
            None, 
            lambda: self.whisper_model.transcribe(audio_float, beam_size=5)
        )
        
        text = ""
        for segment in segments:
            text += segment.text
            
        return text.strip()

    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        print(Fore.RED + "Audio Engine stopped.")
