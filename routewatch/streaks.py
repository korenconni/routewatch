"""Track consecutive-hit streaks for routes.

A streak is the number of consecutive time windows in which a route
received at least one hit.  Streaks reset to zero when a window passes
with no recorded activity.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from routewatch.tracker import RouteTracker

# module-level store: route_key -> (current_streak, last_window_id)
_store: Dict[str, tuple[int, int]] = {}


def _window_id(ts: float, window_seconds: int) -> int:
    """Return an integer bucket index for *ts* given *window_seconds*."""
    return int(ts // window_seconds)


@dataclass
class StreakResult:
    route: str
    method: str
    current_streak: int
    last_window: int

    @property
    def key(self) -> str:
        return f"{self.method.upper()} {self.route}"


def record_streak(
    route: str,
    method: str,
    tracker: RouteTracker,
    *,
    window_seconds: int = 3600,
    ts: Optional[float] = None,
) -> StreakResult:
    """Record a hit for *route*/*method* and update its streak.

    A streak increments when the hit falls in the window immediately
    following the last recorded window.  If more than one window has
    elapsed the streak resets to 1.
    """
    if ts is None:
        ts = time.time()

    key = f"{method.upper()} {route}"
    tracker.register(route, method)

    current_window = _window_id(ts, window_seconds)
    prev_streak, last_window = _store.get(key, (0, -1))

    if last_window == -1:
        new_streak = 1
    elif current_window == last_window:
        # Same window — streak unchanged (hit already counted this window)
        new_streak = prev_streak
    elif current_window == last_window + 1:
        new_streak = prev_streak + 1
    else:
        # Gap — streak broken
        new_streak = 1

    _store[key] = (new_streak, current_window)
    return StreakResult(
        route=route,
        method=method.upper(),
        current_streak=new_streak,
        last_window=current_window,
    )


def get_streak(route: str, method: str) -> int:
    """Return the current streak for *route*/*method* (0 if unknown)."""
    key = f"{method.upper()} {route}"
    return _store.get(key, (0, -1))[0]


def top_streaks(n: int = 10) -> list[StreakResult]:
    """Return the *n* routes with the longest current streaks."""
    results = [
        StreakResult(
            route=k.split(" ", 1)[1],
            method=k.split(" ", 1)[0],
            current_streak=streak,
            last_window=window,
        )
        for k, (streak, window) in _store.items()
    ]
    results.sort(key=lambda r: r.current_streak, reverse=True)
    return results[:n]


def clear_streaks() -> None:
    """Remove all streak data (useful in tests)."""
    _store.clear()
