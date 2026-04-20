import asyncio
from typing import Any, Dict, Optional

import httpx
from gateway.config import Settings


def build_async_client(
    settings: Settings,
    base_url: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    verify: bool = True,
    timeout: Optional[float] = None,
) -> httpx.AsyncClient:
    """Construct a configured AsyncClient with sane defaults."""
    effective_timeout = timeout if timeout is not None else settings.request_timeout
    client_headers = headers or {}
    kwargs: Dict[str, Any] = {
        "headers": client_headers,
        "timeout": httpx.Timeout(effective_timeout),
        "verify": verify,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return httpx.AsyncClient(**kwargs)


async def request_with_retries(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    max_retries: int = 0,
    backoff: float = 0.5,
    **kwargs: Any,
) -> httpx.Response:
    """Issue a request with simple retry/backoff for transient errors."""
    attempt = 0
    while True:
        try:
            resp = await client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception:
            attempt += 1
            if attempt > max_retries:
                raise
            await asyncio.sleep(backoff * attempt)
