"""Route-level hit throttling: suppress recording when a route is hit
too frequently within a rolling time window."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional

from routewatch.tracker import RouteTracker


@dataclass
class ThrottleConfig:
    """Configuration for the throttle window.

    Attributes:
        max_hits: Maximum hits allowed within *window_seconds* before
                  further hits are suppressed.
        window_seconds: Rolling window length in seconds.
    """

    max_hits: int = 10
    window_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.max_hits < 1:
            raise ValueError("max_hits must be >= 1")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")


class RouteThrottle:
    """Tracks per-route hit timestamps and decides whether to record."""

    def __init__(self, config: Optional[ThrottleConfig] = None) -> None:
        self.config: ThrottleConfig = config or ThrottleConfig()
        # method+path -> deque of hit timestamps
        self._windows: Dict[str, Deque[float]] = {}

    def _key(self, method: str, path: str) -> str:
        return f"{method.upper()}:{path}"

    def _prune(self, dq: Deque[float], now: float) -> None:
        """Remove timestamps outside the current window."""
        cutoff = now - self.config.window_seconds
        while dq and dq[0] < cutoff:
            dq.popleft()

    def should_record(self, method: str, path: str) -> bool:
        """Return True if the hit should be forwarded to the tracker."""
        key = self._key(method, path)
        now = time.monotonic()
        dq = self._windows.setdefault(key, deque())
        self._prune(dq, now)
        if len(dq) < self.config.max_hits:
            dq.append(now)
            return True
        return False

    def throttled_record(
        self,
        tracker: RouteTracker,
        method: str,
        path: str,
    ) -> bool:
        """Record a hit on *tracker* only when not throttled.

        Returns True if the hit was recorded, False if suppressed.
        """
        if self.should_record(method, path):
            tracker.record(method, path)
            return True
        return False

    def reset(self, method: Optional[str] = None, path: Optional[str] = None) -> None:
        """Clear throttle state for one route or all routes."""
        if method is not None and path is not None:
            self._windows.pop(self._key(method, path), None)
        else:
            self._windows.clear()
