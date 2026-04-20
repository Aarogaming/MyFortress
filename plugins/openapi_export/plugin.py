from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

from core.plugin_manifest import get_hive_metadata
from loguru import logger

MYFORTRESS_ROOT = Path(__file__).resolve().parents[2]
if str(MYFORTRESS_ROOT) not in sys.path:
    sys.path.insert(0, str(MYFORTRESS_ROOT))

try:
    from fastapi.openapi.utils import get_openapi
    from gateway.api.server import app
except Exception as exc:  # pragma: no cover - import guard
    get_openapi = None
    app = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class Plugin:
    def __init__(self, hub: Any = None, manifest: Dict[str, Any] | None = None):
        self.hub = hub
        self.manifest = manifest or {}
        hive_meta = get_hive_metadata(self.manifest)
        self.hive = str(hive_meta.get("hive") or "myfortress").lower()

    def commands(self) -> Dict[str, Any]:
        return {
            "myfortress.openapi.export": self.export_openapi,
        }

    def export_openapi(self, output_path: str = "artifacts/openapi.json") -> Dict[str, Any]:
        if get_openapi is None or app is None:
            return {
                "ok": False,
                "error": f"MyFortress OpenAPI import failed: {_IMPORT_ERROR}",
            }

        try:
            schema = get_openapi(
                title=app.title,
                version=app.version,
                routes=app.routes,
            )
            target = Path(output_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning(f"OpenAPI export failed: {exc}")
            return {"ok": False, "error": str(exc)}

        return {
            "ok": True,
            "output_path": str(target),
            "bytes": target.stat().st_size,
        }
