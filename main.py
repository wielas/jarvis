import asyncio
import sys
import signal
from src.config import AppConfig
from src.engine import AudioEngine
from src.logger import setup_logger

logger = setup_logger("Main")

async def main():
    logger.info("Initializing Jarvis...")
    
    # Load configuration
    config = AppConfig()
    
    # Initialize Engine
    try:
        engine = AudioEngine(config)
        
        # Setup signal handlers
        loop = asyncio.get_running_loop()
        stop_signal = asyncio.Event()
        
        def signal_handler():
            logger.info("Signal received, stopping...")
            stop_signal.set()
            
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
            
        # Start engine as a task
        engine_task = asyncio.create_task(engine.start())
        
        # Wait for stop signal
        await stop_signal.wait()
        
        # Stop engine
        engine_task.cancel()
        try:
            await engine_task
        except asyncio.CancelledError:
            logger.info("Engine stopped successfully")
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
