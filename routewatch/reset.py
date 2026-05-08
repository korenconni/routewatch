"""Utilities for resetting and pruning RouteTracker state."""

from __future__ import annotations

from typing import List, Optional

from routewatch.tracker import RouteTracker


def reset_tracker(tracker: RouteTracker) -> None:
    """Clear all recorded hits while keeping registered routes intact.

    Useful between test runs or when starting a new observation window
    without discarding the route registry.
    """
    for key in list(tracker._routes.keys()):
        tracker._routes[key].hits = 0


def unregister_route(tracker: RouteTracker, method: str, path: str) -> bool:
    """Remove a single route from the tracker.

    Returns True if the route existed and was removed, False otherwise.
    """
    key = tracker._key(method.upper(), path)
    if key in tracker._routes:
        del tracker._routes[key]
        return True
    return False


def prune_uncovered(tracker: RouteTracker) -> List[str]:
    """Remove all routes that have never been hit.

    Returns the list of keys that were pruned.
    """
    to_remove = [
        key for key, route in tracker._routes.items() if route.hits == 0
    ]
    for key in to_remove:
        del tracker._routes[key]
    return to_remove


def prune_below(tracker: RouteTracker, min_hits: int) -> List[str]:
    """Remove all routes whose hit count is strictly below *min_hits*.

    Returns the list of keys that were pruned.
    """
    if min_hits < 1:
        raise ValueError("min_hits must be >= 1")
    to_remove = [
        key for key, route in tracker._routes.items() if route.hits < min_hits
    ]
    for key in to_remove:
        del tracker._routes[key]
    return to_remove
