import asyncio
import sys
from audio_engine import AudioEngine
from colorama import Fore

async def main():
    print(Fore.BLUE + "Initializing Jarvis Audio Engine...")
    
    # Initialize engine
    # Using 'base.en' as per requirements (default in AudioEngine now)
    engine = AudioEngine()
    
    try:
        await engine.start()
    except KeyboardInterrupt:
        print(Fore.RED + "\nStopping via KeyboardInterrupt...")
    finally:
        engine.stop()

if __name__ == "__main__":
    try:
        # Python 3.7+
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
