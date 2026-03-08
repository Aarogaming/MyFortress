import subprocess
import sys
from pathlib import Path


def _validate(path: Path) -> str | None:
    if not path.is_file():
        return None

    result = subprocess.run(
        [sys.executable, "-m", "json.tool", str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return None
    stderr = result.stderr.strip() or result.stdout.strip() or "unknown JSON parse error"
    return f"{path}: {stderr}"


def main() -> int:
    paths = [Path(raw) for raw in sys.argv[1:]]
    if not paths:
        return 0

    errors = []
    for path in paths:
        err = _validate(path)
        if err:
            errors.append(err)

    if not errors:
        return 0

    sys.stderr.write("JSON_TOOL_VALIDATION_FAIL\n")
    for err in errors:
        sys.stderr.write(f"- {err}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
