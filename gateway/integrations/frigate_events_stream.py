import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Optional

from gateway.clients.http import build_async_client
from gateway.config import Settings


async def stream_events(
    settings: Settings, base_url: Optional[str] = None, api_key: Optional[str] = None
) -> AsyncGenerator[Dict[str, object], None]:
    """Stream events from Frigate event SSE endpoint with basic reconnection/backoff."""
    url_base = (base_url or settings.frigate_url or "").rstrip("/")
    if not url_base:
        return
    headers = {}
    if api_key or settings.frigate_api_key:
        headers["Authorization"] = f"Bearer {api_key or settings.frigate_api_key}"
    backoff = 1.0
    last_event_time = time.time()
    while True:
        client = build_async_client(
            settings=settings, base_url=url_base, headers=headers
        )
        try:
            async with client:
                async with client.stream(
                    "GET", "/api/events/stream", timeout=None
                ) as resp:
                    async for line in resp.aiter_lines():
                        if not line or line.startswith(":"):
                            # heartbeat if idle for too long
                            if time.time() - last_event_time > 15:
                                yield {"raw": "heartbeat", "type": "heartbeat"}
                                last_event_time = time.time()
                            continue
                        last_event_time = time.time()

                        # Basic parsing of SSE data: line
                        data = line
                        if line.startswith("data: "):
                            data = line[6:]

                        try:
                            parsed = json.loads(data)
                            yield {"raw": line, "data": parsed, "type": "event"}
                        except Exception:
                            yield {"raw": line, "type": "raw"}
            backoff = 1.0  # reset if successful exit
        except Exception:
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)
