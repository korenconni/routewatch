"""Core route coverage tracker for routewatch."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Set
import time


@dataclass
class RouteHit:
    """Represents a single recorded hit on a route."""
    method: str
    path: str
    hit_count: int = 0
    last_hit: Optional[float] = None

    def record(self) -> None:
        """Increment hit count and update last hit timestamp."""
        self.hit_count += 1
        self.last_hit = time.time()


class RouteTracker:
    """Tracks which HTTP routes have been hit during the application lifecycle."""

    def __init__(self) -> None:
        self._registered: Dict[str, RouteHit] = {}
        self._hit_keys: Set[str] = set()

    @staticmethod
    def _key(method: str, path: str) -> str:
        return f"{method.upper()}:{path}"

    def register(self, method: str, path: str) -> None:
        """Register a route as known/expected."""
        key = self._key(method, path)
        if key not in self._registered:
            self._registered[key] = RouteHit(method=method.upper(), path=path)

    def record_hit(self, method: str, path: str) -> None:
        """Record that a route was hit. Auto-registers if not already known."""
        key = self._key(method, path)
        if key not in self._registered:
            self.register(method, path)
        self._registered[key].record()
        self._hit_keys.add(key)

    def coverage(self) -> float:
        """Return fraction of registered routes that have been hit (0.0 – 1.0)."""
        if not self._registered:
            return 0.0
        return len(self._hit_keys) / len(self._registered)

    def missed_routes(self) -> list[RouteHit]:
        """Return list of registered routes that have never been hit."""
        return [
            route
            for key, route in self._registered.items()
            if key not in self._hit_keys
        ]

    def report(self) -> dict:
        """Return a summary report of route coverage."""
        return {
            "total_registered": len(self._registered),
            "total_hit": len(self._hit_keys),
            "coverage_pct": round(self.coverage() * 100, 2),
            "missed": [
                {"method": r.method, "path": r.path}
                for r in self.missed_routes()
            ],
        }

    def reset(self) -> None:
        """Clear all hit records while keeping registered routes."""
        self._hit_keys.clear()
        for route in self._registered.values():
            route.hit_count = 0
            route.last_hit = None
