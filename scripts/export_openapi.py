import json
import sys
from pathlib import Path

from fastapi.openapi.utils import get_openapi

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gateway.api.server import app  # noqa: E402


def main() -> None:
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    target = artifacts_dir / "openapi.json"
    target.write_text(json.dumps(openapi_schema, indent=2))
    print(f"Wrote {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
