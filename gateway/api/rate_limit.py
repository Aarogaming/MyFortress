import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

RateKey = Tuple[str, str]  # (client_id, path)
_WINDOWS: Dict[RateKey, Deque[float]] = defaultdict(deque)


def allow(
    client_id: str, path: str, limit: int = 60, window_seconds: int = 60
) -> bool:
    now = time.time()
    key = (client_id, path)
    dq = _WINDOWS[key]

    while dq and dq[0] < now - window_seconds:
        dq.popleft()

    if len(dq) >= limit:
        return False
    dq.append(now)
    return True
