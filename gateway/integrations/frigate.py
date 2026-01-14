import time
from typing import Dict, List, Optional, cast

from gateway.clients.http import build_async_client, request_with_retries
from gateway.config import Settings
from gateway.core import metrics
from gateway.domain.models import FrigateSnapshot, FrigateVersion
from gateway.integrations.frigate_events_stream import stream_events


class FrigateClient:
    def __init__(
        self,
        settings: Settings,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.settings = settings
        self.base_url = (base_url or settings.frigate_url or "").rstrip("/")
        self.api_key = api_key or settings.frigate_api_key
        self.timeout = timeout or settings.frigate_timeout

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def list_cameras(self) -> Dict[str, object]:
        if not self.base_url:
            return {"success": False, "error": "frigate_url not set", "cameras": []}
        client = build_async_client(
            self.settings,
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self.timeout,
        )
        async with client:
            try:
                start = time.time()
                resp = await request_with_retries(
                    client,
                    "GET",
                    "/api/config",
                    max_retries=self.settings.max_retries,
                )
                metrics.record_latency(
                    "frigate_config_ms", (time.time() - start) * 1000
                )
                data = resp.json()
                cameras = list((data or {}).get("cameras", {}).keys())
                return {"success": True, "cameras": cameras, "config": data}
            except Exception as exc:
                metrics.increment("frigate_config_errors")
                return {"success": False, "error": str(exc), "cameras": []}

    async def fetch_version(self) -> FrigateSnapshot:
        if not self.base_url:
            return FrigateSnapshot(
                healthy=False, version=None, error="frigate_url not set"
            )

        client = build_async_client(
            self.settings,
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self.timeout,
        )

        async with client:
            try:
                start = time.time()
                resp = await request_with_retries(
                    client,
                    "GET",
                    "/api/version",
                    max_retries=self.settings.max_retries,
                )
                metrics.record_latency(
                    "frigate_probe_ms", (time.time() - start) * 1000
                )
                data = resp.json()
                version = data.get("version") if isinstance(data, dict) else None
                return FrigateSnapshot(
                    healthy=True,
                    version=FrigateVersion(version=version, extra=data),
                )
            except Exception as exc:
                metrics.increment("frigate_probe_errors")
                return FrigateSnapshot(
                    healthy=False, version=None, error=str(exc)
                )

    async def fetch_snapshot(self) -> FrigateSnapshot:
        snapshot = await self.fetch_version()
        cameras_result = await self.list_cameras()
        if cameras_result.get("success"):
            cameras = cast(List[str], cameras_result.get("cameras", []))
            snapshot.cameras = cameras
        else:
            error = cameras_result.get("error")
            snapshot.error = snapshot.error or (str(error) if error is not None else None)
        return snapshot

    async def fetch_events(self, limit: int = 50) -> Dict[str, object]:
        if not self.base_url:
            return {"success": False, "error": "frigate_url not set", "events": []}
        client = build_async_client(
            self.settings,
            base_url=self.base_url,
            headers=self._headers(),
            timeout=self.timeout,
        )
        async with client:
            try:
                start = time.time()
                resp = await request_with_retries(
                    client,
                    "GET",
                    "/api/events",
                    params={"limit": limit},
                    max_retries=self.settings.max_retries,
                )
                metrics.record_latency(
                    "frigate_events_ms", (time.time() - start) * 1000
                )
                events = resp.json()
                events_list = events if isinstance(events, list) else []
                return {"success": True, "events": events_list}
            except Exception as exc:
                metrics.increment("frigate_events_errors")
                return {"success": False, "error": str(exc), "events": []}

    async def stream_events(self, api_key: Optional[str] = None):
        return stream_events(self.settings, self.base_url, api_key or self.api_key)
