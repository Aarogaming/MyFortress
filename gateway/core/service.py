import asyncio
import logging
import threading

import uvicorn
from gateway.api.grpc_server import serve_grpc
from gateway.config import get_settings

logger = logging.getLogger(__name__)


def run_http(settings):
    uvicorn.run(
        "gateway.api.server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=False,
    )


def run() -> None:
    settings = get_settings()
    settings.check_upstreams()

    # Run HTTP in a separate thread
    http_thread = threading.Thread(target=run_http, args=(settings,), daemon=True)
    http_thread.start()

    # Run gRPC in the main event loop
    logger.info("Starting MyFortress service (HTTP + gRPC)")
    try:
        asyncio.run(serve_grpc(settings))
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
