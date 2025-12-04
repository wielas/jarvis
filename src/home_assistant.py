import aiohttp
import asyncio
from typing import Optional, Dict, Any
from src.config import HomeAssistantConfig
from src.logger import setup_logger

logger = setup_logger("HomeAssistant")

class HomeAssistantClient:
    def __init__(self, config: HomeAssistantConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json",
        }
        self.base_url = config.url.rstrip("/") + "/api"
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def check_connection(self) -> bool:
        """Checks if HA is reachable"""
        if not self.config.token:
            logger.warning("No Home Assistant token provided. Skipping connection check.")
            return False
            
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    logger.info(f"Connected to Home Assistant at {self.config.url}")
                    return True
                else:
                    logger.error(f"Failed to connect to HA: {response.status} {response.reason}")
                    return False
        except Exception as e:
            logger.error(f"Home Assistant connection error: {e}")
            return False

    async def call_service(self, domain: str, service: str, service_data: Dict[str, Any] = None) -> bool:
        """Calls a Home Assistant service"""
        if not self.config.token:
            logger.warning(f"Mocking HA Call: {domain}.{service} with data {service_data}")
            return True

        url = f"{self.base_url}/services/{domain}/{service}"
        try:
            session = await self._get_session()
            async with session.post(url, json=service_data or {}) as response:
                if response.status == 200:
                    logger.info(f"Successfully called {domain}.{service}")
                    return True
                else:
                    logger.error(f"Failed to call service {domain}.{service}: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error calling service {domain}.{service}: {e}")
            return False

    async def get_states(self) -> list[dict]:
        """Fetches all entity states"""
        if not self.config.token:
            return []

        url = f"{self.base_url}/states"
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return []
        except Exception as e:
            logger.error(f"Error fetching states: {e}")
            return []
