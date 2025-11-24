import asyncio
import sys
from audio_engine import AudioEngine

async def main():
    print("Initializing Jarvis Audio Engine...")
    
    # Initialize engine
    # We use 'tiny.en' for faster inference on CPU for this demo
    engine = AudioEngine(model_path="tiny.en")
    
    try:
        await engine.start()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        engine.stop()

if __name__ == "__main__":
    try:
        # Python 3.7+
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
