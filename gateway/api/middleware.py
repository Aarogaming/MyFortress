import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from gateway.api.rate_limit import allow as rate_allow
from gateway.config import get_settings
from gateway.core import metrics
from starlette.middleware.base import BaseHTTPMiddleware


def _sanitize_metric_suffix(path: str) -> str:
    suffix = path.strip("/") or "root"
    cleaned = []
    for ch in suffix:
        if ch.isalnum() or ch in (":", "_"):
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Ensure every request has a request ID header."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Basic structured logging for requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        method = request.method
        path = request.url.path
        status = response.status_code
        request_id = getattr(request.state, "request_id", "-")
        settings = getattr(request.app.state, "settings", get_settings())
        log_payload = {
            "component": "gateway",
            "method": method,
            "path": path,
            "status": status,
            "duration_ms": round(duration_ms, 1),
            "request_id": request_id,
        }
        if getattr(settings, "structured_logging", False):
            import json
            import logging
            logging.getLogger("gateway.access").info(json.dumps(log_payload))
        else:
            import logging
            logging.getLogger("gateway.access").info(
                f"{method} {path} -> {status} ({duration_ms:.1f} ms) request_id={request_id}"
            )
        return response


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Enforce static API key if configured."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = getattr(request.app.state, "settings", get_settings())
        if settings.api_key:
            provided = request.headers.get("x-api-key") or request.query_params.get(
                "api_key"
            )
            if provided != settings.api_key:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid API key"},
                )
        client_host = getattr(request.client, "host", None) if request.client else None
        client_id = request.headers.get("x-client-id") or client_host
        if client_id and not rate_allow(
            client_id,
            request.url.path,
            limit=settings.rate_limit_per_minute,
            window_seconds=settings.rate_limit_window_seconds,
        ):
            metrics.increment("rate_limit_hits")
            metrics.increment(f"rate_limit_hits_{_sanitize_metric_suffix(request.url.path)}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )
        return await call_next(request)
