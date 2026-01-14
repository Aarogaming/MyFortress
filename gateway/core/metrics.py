from collections import defaultdict
from typing import Dict, List

_COUNTERS: Dict[str, int] = defaultdict(int)
_LATENCIES: Dict[str, List[float]] = defaultdict(list)


def increment(name: str, value: int = 1) -> None:
    _COUNTERS[name] += value


def record_latency(name: str, duration_ms: float) -> None:
    _LATENCIES[name].append(duration_ms)


def export() -> Dict[str, object]:
    latency_summary = {
        name: {
            "count": len(values),
            "avg_ms": (sum(values) / len(values)) if values else 0.0,
            "max_ms": max(values) if values else 0.0,
        }
        for name, values in _LATENCIES.items()
    }
    return {"counters": dict(_COUNTERS), "latency_ms": latency_summary}
