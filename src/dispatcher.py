from src.home_assistant import HomeAssistantClient
from src.logger import setup_logger

logger = setup_logger("Dispatcher")

class Dispatcher:
    def __init__(self, ha_client: HomeAssistantClient):
        self.ha = ha_client

    async def dispatch(self, intent: dict):
        """Dispatches the intent to the appropriate handler"""
        intent_type = intent.get("intent")
        
        if intent_type == "light_control":
            await self._handle_light_control(intent)
        elif intent_type == "music_control":
            await self._handle_music_control(intent)
        elif intent_type == "general_query":
            await self._handle_general_query(intent)
        else:
            logger.warning(f"Unknown intent type: {intent_type}")

    async def _handle_light_control(self, intent: dict):
        location = intent.get("location", "").lower()
        action = intent.get("action", "on")
        
        entity_id = await self._find_entity_id("light", location)
        
        if not entity_id:
            logger.warning(f"No light entity found for location: {location}")
            return

        service = "turn_on" if action == "on" else "turn_off"
        # Handle toggle
        if action == "toggle": service = "toggle"
        
        data = {"entity_id": entity_id}
        if action == "on" and intent.get("brightness"):
             data["brightness_pct"] = intent["brightness"]

        logger.info(f"Dispatching Light Control: {service} -> {entity_id}")
        await self.ha.call_service("light", service, data)

    async def _handle_music_control(self, intent: dict):
        action = intent.get("action")
        # Try to find a media player, default to first found or specific one
        entity_id = await self._find_entity_id("media_player", "speaker") or "media_player.living_room_speaker"
        
        service_map = {
            "play": "media_play",
            "pause": "media_pause",
            "next": "media_next_track",
            "previous": "media_previous_track",
            "volume_up": "volume_up",
            "volume_down": "volume_down"
        }
        
        service = service_map.get(action)
        if service:
            logger.info(f"Dispatching Music Control: {service} -> {entity_id}")
            await self.ha.call_service("media_player", service, {"entity_id": entity_id})
        else:
            logger.warning(f"Unknown music action: {action}")

    async def _handle_general_query(self, intent: dict):
        query = intent.get("query")
        logger.info(f"General Query (No Action): {query}")

    async def _find_entity_id(self, domain: str, keyword: str) -> str:
        """
        Finds the best matching entity ID for a given domain and keyword.
        Fetches states from HA to do the lookup.
        """
        states = await self.ha.get_states()
        if not states:
            # Fallback for mock mode
            return f"{domain}.{keyword.replace(' ', '_')}"

        # Filter by domain
        candidates = [s for s in states if s['entity_id'].startswith(f"{domain}.")]
        
        # 1. Exact match on friendly_name
        for state in candidates:
            name = state.get('attributes', {}).get('friendly_name', '').lower()
            if keyword in name:
                return state['entity_id']
                
        # 2. Match on entity_id
        for state in candidates:
            if keyword in state['entity_id']:
                return state['entity_id']
                
        return None
