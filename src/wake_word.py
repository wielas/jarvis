import openwakeword
from openwakeword.model import Model
import numpy as np
from src.config import WakeWordConfig
from src.logger import setup_logger

logger = setup_logger("WakeWord")

class WakeWordDetector:
    def __init__(self, config: WakeWordConfig):
        self.config = config
        self.model = None
        self._load_model()

    def _load_model(self):
        logger.info("Loading Wake Word Model...")
        try:
            # Get the pre-trained model paths
            all_model_paths = openwakeword.get_pretrained_model_paths()
            
            selected_paths = []
            for name in self.config.model_names:
                # Find the path that contains the model name
                # This is a simple matching strategy, might need refinement if names are ambiguous
                matches = [p for p in all_model_paths if name in p]
                if matches:
                    selected_paths.append(matches[0])
                else:
                    logger.warning(f"Model '{name}' not found in pre-trained models.")

            if not selected_paths:
                raise ValueError("No valid wake word models found.")

            self.model = Model(
                wakeword_model_paths=selected_paths
            )
            logger.info(f"Wake Word Model loaded: {self.config.model_names}")
            
        except Exception as e:
            logger.error(f"Failed to load Wake Word Model: {e}")
            raise

    def detect(self, audio_chunk: np.ndarray) -> float:
        """
        Feeds audio chunk to the model and returns the prediction score for the primary wake word.
        Assumes the first model in config is the primary one.
        """
        if not self.model:
            return 0.0

        # Flatten if necessary (openwakeword expects 1D array or (N, samples))
        prediction = self.model.predict(audio_chunk.flatten())
        
        # Get score for the first configured model
        # Note: openwakeword keys might include version suffixes (e.g. 'hey_jarvis_v0.1')
        # We need to find the key that matches our target
        
        primary_name = self.config.model_names[0]
        
        # Try exact match first
        if primary_name in prediction:
            return prediction[primary_name]
            
        # Try partial match
        for key in prediction:
            if primary_name in key:
                return prediction[key]
                
        return 0.0
