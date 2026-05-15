"""Time-window hit counting for RouteTracker routes."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional, Tuple

from routewatch.tracker import RouteTracker

# Module-level store: (method, path) -> deque of epoch timestamps
_hit_times: Dict[Tuple[str, str], Deque[float]] = {}


def _key(method: str, path: str) -> Tuple[str, str]:
    return method.upper(), path


def record_hit_time(
    method: str,
    path: str,
    *,
    ts: Optional[float] = None,
    max_events: int = 10_000,
) -> float:
    """Append *ts* (default: now) to the hit-time log for the route."""
    k = _key(method, path)
    if k not in _hit_times:
        _hit_times[k] = deque(maxlen=max_events)
    stamp = ts if ts is not None else time.time()
    _hit_times[k].append(stamp)
    return stamp


def hits_in_window(
    method: str,
    path: str,
    window_seconds: float,
    *,
    now: Optional[float] = None,
) -> int:
    """Return the number of recorded hits within the last *window_seconds*."""
    k = _key(method, path)
    if k not in _hit_times:
        return 0
    cutoff = (now if now is not None else time.time()) - window_seconds
    return sum(1 for t in _hit_times[k] if t >= cutoff)


@dataclass
class WindowReport:
    method: str
    path: str
    window_seconds: float
    hit_count: int
    rate_per_minute: float


def build_window_report(
    tracker: RouteTracker,
    window_seconds: float = 60.0,
    *,
    now: Optional[float] = None,
) -> list[WindowReport]:
    """Build a WindowReport for every registered route."""
    reports: list[WindowReport] = []
    for (method, path) in tracker.routes:
        count = hits_in_window(method, path, window_seconds, now=now)
        rate = (count / window_seconds) * 60.0 if window_seconds > 0 else 0.0
        reports.append(
            WindowReport(
                method=method,
                path=path,
                window_seconds=window_seconds,
                hit_count=count,
                rate_per_minute=round(rate, 4),
            )
        )
    return sorted(reports, key=lambda r: (-r.hit_count, r.method, r.path))


def clear_hit_times(method: Optional[str] = None, path: Optional[str] = None) -> None:
    """Clear stored timestamps.  Pass both args to clear a single route."""
    if method is not None and path is not None:
        _hit_times.pop(_key(method, path), None)
    else:
        _hit_times.clear()
