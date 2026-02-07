import time
from typing import Dict, List, Optional

from gateway.clients.http import build_async_client, request_with_retries
from gateway.config import Settings
from gateway.core import metrics
from gateway.domain.models import EntityReading, HomeMerlinSnapshot

_HA_STATE_CACHE: Dict[str, Dict[str, object]] = {}


class HomeMerlinClient:
    def __init__(
        self,
        settings: Settings,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        verify_ssl: bool = True,
    ) -> None:
        self.settings = settings
        self.base_url = (base_url or settings.home_assistant_url or "").rstrip("/")
        self.token = token or settings.home_assistant_token
        self.timeout = timeout or settings.home_assistant_timeout
        self.verify_ssl = verify_ssl

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def turn_on(self, entity_id: str) -> Dict[str, object]:
        domain = entity_id.split(".")[0]
        return await self.call_service(domain, "turn_on", {"entity_id": entity_id})

    async def turn_off(self, entity_id: str) -> Dict[str, object]:
        domain = entity_id.split(".")[0]
        return await self.call_service(domain, "turn_off", {"entity_id": entity_id})

    async def call_service(
        self, domain: str, service: str, data: Optional[Dict[str, object]] = None
    ) -> Dict[str, object]:
        if not self.base_url:
            return {"success": False, "error": "home_assistant_url not set"}
        payload = data or {}
        client = build_async_client(
            self.settings,
            base_url=self.base_url,
            headers=self._headers(),
            verify=self.verify_ssl,
            timeout=self.timeout,
        )
        async with client:
            try:
                start = time.time()
                resp = await request_with_retries(
                    client,
                    "POST",
                    f"/api/services/{domain}/{service}",
                    json=payload,
                    max_retries=self.settings.max_retries,
                )
                metrics.record_latency(
                    "home_assistant_service_ms", (time.time() - start) * 1000
                )
                return {"success": True, "response": resp.json()}
            except Exception as exc:
                metrics.increment("home_assistant_service_errors")
                return {"success": False, "error": str(exc)}

    async def set_state(
        self,
        entity_id: str,
        state: object,
        attributes: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        if not self.base_url:
            return {"success": False, "error": "home_assistant_url not set"}
        payload = {"state": state, "attributes": attributes or {}}
        client = build_async_client(
            self.settings,
            base_url=self.base_url,
            headers=self._headers(),
            verify=self.verify_ssl,
            timeout=self.timeout,
        )
        async with client:
            try:
                start = time.time()
                resp = await request_with_retries(
                    client,
                    "POST",
                    f"/api/states/{entity_id}",
                    json=payload,
                    max_retries=self.settings.max_retries,
                )
                metrics.record_latency(
                    "home_assistant_state_ms", (time.time() - start) * 1000
                )
                data = resp.json()
                return {
                    "success": True,
                    "state": data.get("state"),
                    "attributes": data.get("attributes", {}),
                }
            except Exception as exc:
                metrics.increment("home_assistant_state_errors")
                return {"success": False, "error": str(exc)}

    async def probe_entities(self, entities: List[str]) -> HomeMerlinSnapshot:
        now = time.time()
        readings: Dict[str, EntityReading] = {}
        if not self.base_url:
            return HomeMerlinSnapshot(
                healthy=False, readings=readings, error="home_assistant_url not set"
            )

        client = build_async_client(
            self.settings,
            base_url=self.base_url,
            headers=self._headers(),
            verify=self.verify_ssl,
            timeout=self.timeout,
        )

        async with client:
            for entity in entities:
                endpoint = f"/api/states/{entity}"
                try:
                    start = time.time()
                    resp = await request_with_retries(
                        client,
                        "GET",
                        endpoint,
                        max_retries=self.settings.max_retries,
                    )
                    metrics.record_latency(
                        "home_assistant_probe_ms", (time.time() - start) * 1000
                    )
                    data = resp.json()
                    reading = EntityReading(
                        entity_id=entity,
                        state=data.get("state"),
                        attributes=data.get("attributes", {}),
                    )
                    readings[entity] = reading
                    _HA_STATE_CACHE[entity] = {
                        "data": reading,
                        "expires_at": now + 30,  # 30s cache
                    }
                except Exception as exc:
                    metrics.increment("home_assistant_probe_errors")
                    readings[entity] = EntityReading(
                        entity_id=entity, error=str(exc), attributes={}
                    )

        healthy = any(r.error is None for r in readings.values()) or not entities
        error = None if healthy else "All entity reads failed"
        return HomeMerlinSnapshot(healthy=healthy, readings=readings, error=error)
