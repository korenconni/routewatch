"""Route deprecation tracking for routewatch."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Optional, Set

from routewatch.tracker import RouteTracker

_store: Dict[str, "DeprecationInfo"] = {}


@dataclass
class DeprecationInfo:
    reason: str
    deprecated_on: date
    sunset_on: Optional[date] = None
    replacement: Optional[str] = None


def _key(method: str, path: str) -> str:
    return f"{method.upper()}:{path}"


def deprecate_route(
    tracker: RouteTracker,
    method: str,
    path: str,
    reason: str,
    deprecated_on: Optional[date] = None,
    sunset_on: Optional[date] = None,
    replacement: Optional[str] = None,
) -> DeprecationInfo:
    """Mark a route as deprecated, auto-registering it if necessary."""
    k = _key(method, path)
    if k not in tracker._routes:
        tracker.register(method, path)
    info = DeprecationInfo(
        reason=reason,
        deprecated_on=deprecated_on or date.today(),
        sunset_on=sunset_on,
        replacement=replacement,
    )
    _store[k] = info
    return info


def undeprecate_route(method: str, path: str) -> bool:
    """Remove deprecation info for a route. Returns True if it existed."""
    k = _key(method, path)
    if k in _store:
        del _store[k]
        return True
    return False


def get_deprecation(method: str, path: str) -> Optional[DeprecationInfo]:
    """Return deprecation info for a route, or None if not deprecated."""
    return _store.get(_key(method, path))


def get_deprecated_routes(tracker: RouteTracker) -> Set[str]:
    """Return the set of keys (METHOD:path) that are currently deprecated."""
    registered = set(tracker._routes.keys())
    return registered & set(_store.keys())


def deprecation_report(tracker: RouteTracker) -> str:
    """Produce a human-readable deprecation report."""
    deprecated = get_deprecated_routes(tracker)
    if not deprecated:
        return "No deprecated routes."
    lines = ["Deprecated routes:", ""]
    for k in sorted(deprecated):
        info = _store[k]
        line = f"  {k}  — {info.reason} (since {info.deprecated_on})"
        if info.sunset_on:
            line += f", sunset {info.sunset_on}"
        if info.replacement:
            line += f" → use {info.replacement}"
        lines.append(line)
    return "\n".join(lines)
