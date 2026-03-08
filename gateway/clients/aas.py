import logging
from typing import Any, Dict, List, Optional

import httpx
from gateway.config import Settings

logger = logging.getLogger(__name__)


class MyFortressClient:
    """Python client for AAS plugins to consume MyFortress service."""

    @classmethod
    def from_settings(cls, settings: Settings):
        return cls(
            base_url=f"http://{settings.host}:{settings.port}",
            api_key=settings.api_key,
            timeout=settings.request_timeout,
        )

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def get_snapshot(self, entities: Optional[List[str]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/snapshot",
                json={"home_assistant_entities": entities or []},
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def call_ha_service(
        self, domain: str, service: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/home-assistant/service",
                json={"domain": domain, "service": service, "data": data},
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def set_ha_state(
        self, entity_id: str, state: Any, attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/home-assistant/state",
                json={
                    "entity_id": entity_id,
                    "state": state,
                    "attributes": attributes or {},
                },
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()
