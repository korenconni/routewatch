"""Route hit history: timestamped log of route accesses for trend analysis."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class HitEvent:
    """A single timestamped hit event for a route."""
    method: str
    path: str
    timestamp: float = field(default_factory=time.time)

    @property
    def key(self) -> str:
        return f"{self.method.upper()} {self.path}"


class RouteHistory:
    """Maintains a bounded timestamped history of route hits."""

    def __init__(self, max_events: int = 1000) -> None:
        self._max_events = max_events
        self._events: List[HitEvent] = []

    def record(self, method: str, path: str, timestamp: Optional[float] = None) -> HitEvent:
        """Append a hit event; evicts oldest entry when capacity is exceeded."""
        event = HitEvent(
            method=method.upper(),
            path=path,
            timestamp=timestamp if timestamp is not None else time.time(),
        )
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events.pop(0)
        return event

    def events(self, since: Optional[float] = None) -> List[HitEvent]:
        """Return all events, optionally filtered to those after *since*."""
        if since is None:
            return list(self._events)
        return [e for e in self._events if e.timestamp >= since]

    def hits_per_route(self, since: Optional[float] = None) -> Dict[str, int]:
        """Return a mapping of route key -> hit count within the time window."""
        counts: Dict[str, int] = defaultdict(int)
        for event in self.events(since=since):
            counts[event.key] += 1
        return dict(counts)

    def most_active(self, n: int = 5, since: Optional[float] = None) -> List[tuple]:
        """Return the top *n* routes by hit count as (key, count) pairs."""
        counts = self.hits_per_route(since=since)
        return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:n]

    def clear(self) -> None:
        """Remove all recorded events."""
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)
