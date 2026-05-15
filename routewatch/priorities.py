"""Route priority management for RouteWatch.

Allows routes to be assigned a numeric priority level (1=critical, 5=low)
so that reports and alerts can be filtered or weighted accordingly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from routewatch.tracker import RouteTracker

_DEFAULT_PRIORITY = 3
_MIN_PRIORITY = 1
_MAX_PRIORITY = 5

# module-level store: key -> priority int
_store: Dict[str, int] = {}


def _key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


@dataclass
class PriorityResult:
    method: str
    path: str
    priority: int

    @property
    def key(self) -> str:
        return _key(self.method, self.path)

    @property
    def label(self) -> str:
        labels = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}
        return labels.get(self.priority, "unknown")


def set_priority(
    tracker: RouteTracker,
    method: str,
    path: str,
    priority: int,
) -> PriorityResult:
    """Assign a priority level (1-5) to a route."""
    if not (_MIN_PRIORITY <= priority <= _MAX_PRIORITY):
        raise ValueError(
            f"priority must be between {_MIN_PRIORITY} and {_MAX_PRIORITY}, got {priority}"
        )
    k = _key(method, path)
    if k not in tracker.routes:
        tracker.register(method, path)
    _store[k] = priority
    return PriorityResult(method=method, path=path, priority=priority)


def get_priority(method: str, path: str) -> int:
    """Return the priority for a route, defaulting to 3 (medium)."""
    return _store.get(_key(method, path), _DEFAULT_PRIORITY)


def remove_priority(method: str, path: str) -> bool:
    """Remove an explicitly set priority, reverting to default. Returns True if removed."""
    k = _key(method, path)
    if k in _store:
        del _store[k]
        return True
    return False


def routes_by_priority(
    tracker: RouteTracker, priority: int
) -> List[PriorityResult]:
    """Return all registered routes that match the given priority level."""
    results = []
    for k in tracker.routes:
        method, path = k.split(" ", 1)
        if get_priority(method, path) == priority:
            results.append(PriorityResult(method=method, path=path, priority=priority))
    return results


def priority_report(tracker: RouteTracker) -> List[PriorityResult]:
    """Return a list of PriorityResult for all registered routes, sorted by priority."""
    results = []
    for k in tracker.routes:
        method, path = k.split(" ", 1)
        p = get_priority(method, path)
        results.append(PriorityResult(method=method, path=path, priority=p))
    results.sort(key=lambda r: (r.priority, r.key))
    return results
