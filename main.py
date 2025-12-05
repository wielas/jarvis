import asyncio
import sys
import signal
import argparse
from src.config import AppConfig
from src.engine import AudioEngine
from src.logger import setup_logger

logger = setup_logger("Main")

async def main():
    parser = argparse.ArgumentParser(description="Jarvis Voice Assistant")
    parser.add_argument("-t", "--test", action="store_true", help="Run in minimal test mode (Wake Word -> Toggle Lights)")
    args = parser.parse_args()

    logger.info("Initializing Jarvis...")
    
    # Load configuration
    config = AppConfig()
    config.test_mode = args.test
    
    if config.test_mode:
        logger.info("⚠️ RUNNING IN TEST MODE: Wake Word will trigger 'Toggle Bedroom Lights' directly.")

    engine = AudioEngine(config)
    
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
