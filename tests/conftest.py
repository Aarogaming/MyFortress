import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure tmpdir is writable in environments with odd defaults (e.g., WSL -> Windows temp).
os.environ.setdefault("TMPDIR", "/tmp")
