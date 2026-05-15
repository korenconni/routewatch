"""Route hit retention policies — automatically expire old hit data."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from routewatch.tracker import RouteTracker


@dataclass
class RetentionPolicy:
    """Configuration for a retention policy."""
    max_age_seconds: float  # hits older than this are discarded
    min_hits_to_keep: int = 0  # always keep at least this many hits regardless of age

    def __post_init__(self) -> None:
        if self.max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")
        if self.min_hits_to_keep < 0:
            raise ValueError("min_hits_to_keep must be >= 0")


@dataclass
class RetentionResult:
    """Summary of a retention sweep."""
    routes_checked: int
    routes_zeroed: int
    routes_kept: int
    details: Dict[str, int] = field(default_factory=dict)  # route_key -> hits removed

    @property
    def any_expired(self) -> bool:
        return self.routes_zeroed > 0


# Internal store: route_key -> last_hit_timestamp
_last_hit: Dict[str, float] = {}


def record_hit_time(method: str, path: str, ts: Optional[float] = None) -> None:
    """Record the timestamp of the most recent hit for a route."""
    key = f"{method.upper()} {path}"
    _last_hit[key] = ts if ts is not None else time.time()


def get_last_hit_time(method: str, path: str) -> Optional[float]:
    """Return the last recorded hit timestamp for a route, or None."""
    return _last_hit.get(f"{method.upper()} {path}")


def apply_retention(tracker: RouteTracker, policy: RetentionPolicy,
                    now: Optional[float] = None) -> RetentionResult:
    """Zero out hit counts for routes whose last hit exceeds max_age_seconds.

    Routes with no recorded hit time are left untouched.
    Routes whose hit count is <= min_hits_to_keep are also left untouched.
    """
    if now is None:
        now = time.time()

    routes_zeroed = 0
    routes_kept = 0
    details: Dict[str, int] = {}

    for route in tracker.routes.values():
        key = f"{route.method} {route.path}"
        last = _last_hit.get(key)
        if last is None:
            routes_kept += 1
            continue
        age = now - last
        if age > policy.max_age_seconds and route.hits > policy.min_hits_to_keep:
            details[key] = route.hits
            route.hits = 0
            routes_zeroed += 1
        else:
            routes_kept += 1

    return RetentionResult(
        routes_checked=len(tracker.routes),
        routes_zeroed=routes_zeroed,
        routes_kept=routes_kept,
        details=details,
    )


def clear_hit_times() -> None:
    """Clear all recorded hit timestamps (useful for testing)."""
    _last_hit.clear()
