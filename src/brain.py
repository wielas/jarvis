import ollama
from pydantic import BaseModel, Field
from typing import Optional, Literal
from src.config import AppConfig
from src.logger import setup_logger

logger = setup_logger("Brain")

# --- Intent Models ---

class LightControl(BaseModel):
    intent: Literal["light_control"] = "light_control"
    location: str = Field(..., description="The room or location of the light (e.g., 'living room', 'kitchen')")
    action: Literal["on", "off", "toggle", "dim", "brighten", "set_color"] = Field(..., description="The action to perform")
    color: Optional[str] = Field(None, description="The color to set (if applicable)")
    brightness: Optional[int] = Field(None, description="Brightness level 0-100 (if applicable)")

class MusicControl(BaseModel):
    intent: Literal["music_control"] = "music_control"
    action: Literal["play", "pause", "next", "previous", "volume_up", "volume_down"] = Field(..., description="Music action")
    song: Optional[str] = Field(None, description="Song name if requested")
    artist: Optional[str] = Field(None, description="Artist name if requested")

class GeneralQuery(BaseModel):
    intent: Literal["general_query"] = "general_query"
    query: str = Field(..., description="The user's general question or request")

# Union of all possible intents
# For now, we'll just ask the LLM to return a JSON that matches one of these structures.

class Brain:
    def __init__(self, config: AppConfig):
        self.config = config
        self.model_name = config.brain.model_name
        self.client = ollama.AsyncClient(host=config.brain.ollama_host)
        
        # We can't await in __init__, so we'll do the check lazily or start a task
        # For simplicity, we'll just log that we are ready
        logger.info(f"Brain initialized with model: {self.model_name}")

    async def ensure_model(self):
        try:
            logger.info(f"Checking for model '{self.model_name}'...")
            models = await self.client.list()
            # models['models'] is a list of objects
            model_names = [m['name'] for m in models['models']]
            
            # Check if model exists
            if not any(self.model_name in m for m in model_names):
                logger.info(f"Model '{self.model_name}' not found. Pulling... (this may take a while)")
                await self.client.pull(self.model_name)
                logger.info(f"Model '{self.model_name}' pulled successfully.")
            else:
                logger.info(f"Model '{self.model_name}' is ready.")
                
        except Exception as e:
            logger.error(f"Failed to connect to Ollama or pull model: {e}")

    async def process(self, text: str) -> dict:
        """
        Process the user's text and return a structured intent.
        """
        logger.info(f"Thinking about: '{text}'")
        
        system_prompt = """
        You are Jarvis, a smart home assistant.
        Analyze the user's input and extract the intent.
        Output MUST be a valid JSON object matching one of the following schemas:
        
        1. Light Control: {"intent": "light_control", "location": "room name", "action": "on/off/...", "color": "...", "brightness": 0-100}
        2. Music Control: {"intent": "music_control", "action": "play/pause/...", "song": "...", "artist": "..."}
        3. General Query: {"intent": "general_query", "query": "..."}
        
        If the input is unclear, default to General Query.
        Do not output any markdown or explanations, ONLY the JSON object.
        """
        
        try:
            response = await self.client.chat(model=self.model_name, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': text},
            ], format='json')
            
            content = response['message']['content']
            logger.info(f"Brain thought: {content}")
            
            import json
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Brain processing failed: {e}")
            return {"intent": "error", "message": str(e)}
