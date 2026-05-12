"""Route grouping utilities — bucket routes by prefix or custom key."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List, Optional

from routewatch.tracker import RouteTracker


def _default_prefix(route: str, depth: int = 1) -> str:
    """Return the first *depth* path segments of *route* as a group key."""
    parts = [p for p in route.split("/") if p]
    if not parts:
        return "/"
    return "/" + "/".join(parts[:depth])


def group_by_prefix(
    tracker: RouteTracker,
    depth: int = 1,
) -> Dict[str, List[str]]:
    """Group registered routes by their URL prefix at *depth* segments.

    Returns a mapping of ``prefix -> [route, ...]`` sorted alphabetically.
    """
    groups: Dict[str, List[str]] = defaultdict(list)
    for key in tracker.routes:
        method, path = key.split(" ", 1)
        prefix = _default_prefix(path, depth)
        groups[prefix].append(key)
    return {k: sorted(v) for k, v in sorted(groups.items())}


def group_by_key(
    tracker: RouteTracker,
    key_fn: Callable[[str, str], str],
) -> Dict[str, List[str]]:
    """Group routes using a custom *key_fn(method, path) -> group_name*.

    Returns a mapping of ``group -> [route, ...]`` sorted alphabetically.
    """
    groups: Dict[str, List[str]] = defaultdict(list)
    for route_key in tracker.routes:
        method, path = route_key.split(" ", 1)
        group = key_fn(method, path)
        groups[group].append(route_key)
    return {k: sorted(v) for k, v in sorted(groups.items())}


def group_hit_counts(
    tracker: RouteTracker,
    groups: Dict[str, List[str]],
) -> Dict[str, int]:
    """Sum hit counts for each group.

    *groups* is the mapping returned by :func:`group_by_prefix` or
    :func:`group_by_key`.
    """
    totals: Dict[str, int] = {}
    for group, keys in groups.items():
        totals[group] = sum(tracker.routes[k].hits for k in keys if k in tracker.routes)
    return totals


def group_coverage(
    tracker: RouteTracker,
    groups: Dict[str, List[str]],
) -> Dict[str, float]:
    """Return the coverage percentage (0-100) for each group."""
    result: Dict[str, float] = {}
    for group, keys in groups.items():
        valid = [k for k in keys if k in tracker.routes]
        if not valid:
            result[group] = 0.0
            continue
        covered = sum(1 for k in valid if tracker.routes[k].hits > 0)
        result[group] = round(covered / len(valid) * 100, 2)
    return result
