import time
from typing import Any, Dict, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from gateway.api.intelligence_routes import router as intelligence_router
from gateway.api.middleware import (
    ApiKeyMiddleware,
    LoggingMiddleware,
    RequestIDMiddleware,
)
from gateway.api.routes import router as api_router
from gateway.config import get_settings
from gateway.core import metrics
from gateway.intelligence.manager import initialize_intelligence_manager

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

app = FastAPI(title="MyFortress", version="0.1.0")
app.state.start_time = time.time()
app.state.request_count = 0
app.state.settings = get_settings()

initialize_intelligence_manager(app.state.settings)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(api_router)
app.include_router(intelligence_router)

if OTEL_AVAILABLE:
    FastAPIInstrumentor.instrument_app(app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "type": exc.__class__.__name__,
            "path": request.url.path,
        },
    )


@app.middleware("http")
async def _count_requests(request, call_next):
    response = await call_next(request)
    request.app.state.request_count += 1
    return response


@app.get("/system/info")
async def system_info() -> dict:
    import platform
    import sys

    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "python_version": sys.version,
        "app_version": "0.1.0",
        "start_time": app.state.start_time,
    }


@app.get("/health")
async def health() -> dict:
    from gateway.integrations.frigate import FrigateClient
    from gateway.integrations.home_assistant import HomeMerlinClient

    settings = get_settings()
    ha_ok = False
    frigate_ok = False

    if settings.home_assistant_url:
        ha_client = HomeMerlinClient(settings=settings)
        try:
            res = await ha_client.probe_entities([])
            ha_ok = res.healthy
        except Exception:
            ha_ok = False
    else:
        ha_ok = True  # Not configured

    if settings.frigate_url:
        frigate_client = FrigateClient(settings=settings)
        try:
            frigate_version = await frigate_client.fetch_version()
            frigate_ok = frigate_version.healthy
        except Exception:
            frigate_ok = False
    else:
        frigate_ok = True  # Not configured

    status = "ok" if ha_ok and frigate_ok else "error"
    return {
        "status": status,
        "home_assistant": "ok" if ha_ok else "error",
        "frigate": "ok" if frigate_ok else "error",
    }


@app.get("/readiness")
async def readiness() -> dict:
    return {"status": "ready"}


@app.get("/metrics")
async def metrics_endpoint() -> dict:
    uptime = time.time() - app.state.start_time
    return {
        "request_count": app.state.request_count,
        "uptime_seconds": uptime,
        "upstream": metrics.export(),
    }


@app.get("/metrics/prom")
async def metrics_prometheus() -> str:
    data = metrics.export()
    counters: Dict[str, Any] = cast(
        Dict[str, Any],
        data["counters"] if isinstance(data, dict) and "counters" in data else {},
    )
    latency: Dict[str, Dict[str, Any]] = cast(
        Dict[str, Dict[str, Any]],
        data["latency_ms"] if isinstance(data, dict) and "latency_ms" in data else {},
    )
    gauges = {
        "uptime_seconds": time.time() - app.state.start_time,
        "request_count": app.state.request_count,
    }
    lines = []
    for name, value in gauges.items():
        lines.append(f"# HELP {name} gauge")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")
    # counters
    for name, value in counters.items():
        lines.append(f"# HELP {name} upstream counter")
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{name} {value}")
    # latencies
    for name, stats in latency.items():
        lines.append(f"# HELP {name} upstream latency ms")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f'{name}_count {stats.get("count", 0)}')
        lines.append(f'{name}_avg_ms {stats.get("avg_ms", 0)}')
        lines.append(f'{name}_max_ms {stats.get("max_ms", 0)}')
    return "\n".join(lines) + "\n"


def create_app() -> FastAPI:
    return app
