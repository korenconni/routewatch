"""Route pattern matching utilities for routewatch.

Provides wildcard and regex-based pattern matching against registered routes,
enabling bulk operations and filtered reporting.
"""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import List, Optional, Pattern

from routewatch.tracker import RouteTracker


@dataclass
class PatternMatch:
    """Result of a pattern match operation."""
    method: str
    path: str
    hit_count: int

    @property
    def key(self) -> str:
        return f"{self.method.upper()} {self.path}"


def match_glob(
    tracker: RouteTracker,
    pattern: str,
    method: Optional[str] = None,
) -> List[PatternMatch]:
    """Return all routes whose path matches a glob *pattern*.

    Args:
        tracker: The RouteTracker instance to search.
        pattern: A glob pattern, e.g. ``"/api/v1/*"``.
        method: Optional HTTP method filter (case-insensitive).

    Returns:
        List of :class:`PatternMatch` objects for matching routes.
    """
    results: List[PatternMatch] = []
    for route_key, hit in tracker.routes.items():
        route_method, route_path = route_key.split(" ", 1)
        if method and route_method != method.upper():
            continue
        if fnmatch.fnmatch(route_path, pattern):
            results.append(PatternMatch(method=route_method, path=route_path, hit_count=hit.count))
    return results


def match_regex(
    tracker: RouteTracker,
    pattern: str,
    method: Optional[str] = None,
) -> List[PatternMatch]:
    """Return all routes whose path matches a regex *pattern*.

    Args:
        tracker: The RouteTracker instance to search.
        pattern: A regular expression string, e.g. ``r"^/api/v[0-9]+/"``.
        method: Optional HTTP method filter (case-insensitive).

    Returns:
        List of :class:`PatternMatch` objects for matching routes.

    Raises:
        re.error: If *pattern* is not a valid regular expression.
    """
    compiled: Pattern[str] = re.compile(pattern)
    results: List[PatternMatch] = []
    for route_key, hit in tracker.routes.items():
        route_method, route_path = route_key.split(" ", 1)
        if method and route_method != method.upper():
            continue
        if compiled.search(route_path):
            results.append(PatternMatch(method=route_method, path=route_path, hit_count=hit.count))
    return results


def keys_for_pattern(
    tracker: RouteTracker,
    pattern: str,
    use_regex: bool = False,
    method: Optional[str] = None,
) -> List[str]:
    """Convenience wrapper returning route keys (``"METHOD /path"``) for a pattern."""
    fn = match_regex if use_regex else match_glob
    return [m.key for m in fn(tracker, pattern, method=method)]
