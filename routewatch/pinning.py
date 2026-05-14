"""Route pinning: mark specific routes as critical and assert they remain covered."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from routewatch.tracker import RouteTracker

_PINNED_VERSION = 1


@dataclass
class PinResult:
    pinned: List[str]
    failing: List[str]  # pinned but zero hits
    passing: List[str]  # pinned and has hits

    @property
    def has_failures(self) -> bool:
        return len(self.failing) > 0


def pin_route(tracker: RouteTracker, method: str, path: str) -> None:
    """Mark a route as pinned (critical). Auto-registers if unknown."""
    key = f"{method.upper()} {path}"
    if key not in tracker.routes:
        tracker.register(method, path)
    if not hasattr(tracker, "_pinned"):
        tracker._pinned: Set[str] = set()  # type: ignore[attr-defined]
    tracker._pinned.add(key)


def unpin_route(tracker: RouteTracker, method: str, path: str) -> None:
    """Remove a pin from a route."""
    key = f"{method.upper()} {path}"
    pinned: Set[str] = getattr(tracker, "_pinned", set())
    pinned.discard(key)


def get_pinned(tracker: RouteTracker) -> Set[str]:
    """Return the set of pinned route keys."""
    return set(getattr(tracker, "_pinned", set()))


def check_pins(tracker: RouteTracker) -> PinResult:
    """Check all pinned routes and report which are covered vs failing."""
    pinned = get_pinned(tracker)
    failing: List[str] = []
    passing: List[str] = []
    for key in sorted(pinned):
        hit = tracker.routes.get(key)
        if hit is None or hit.count == 0:
            failing.append(key)
        else:
            passing.append(key)
    return PinResult(pinned=sorted(pinned), failing=failing, passing=passing)


def save_pins(tracker: RouteTracker, path: str | Path) -> None:
    """Persist pinned routes to a JSON file."""
    data = {
        "version": _PINNED_VERSION,
        "pinned": sorted(get_pinned(tracker)),
    }
    Path(path).write_text(json.dumps(data, indent=2))


def load_pins(tracker: RouteTracker, path: str | Path) -> List[str]:
    """Load pinned routes from a JSON file and apply them to the tracker."""
    data = json.loads(Path(path).read_text())
    loaded: List[str] = []
    for key in data.get("pinned", []):
        try:
            method, route_path = key.split(" ", 1)
        except ValueError:
            continue
        pin_route(tracker, method, route_path)
        loaded.append(key)
    return loaded
