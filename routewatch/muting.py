"""Route muting — suppress tracking for specific routes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set, Optional

from routewatch.tracker import RouteTracker

# Module-level mute store: set of normalised "METHOD /path" keys
_muted: Set[str] = set()


def _key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


@dataclass
class MuteResult:
    method: str
    path: str
    muted: bool

    @property
    def key(self) -> str:
        return _key(self.method, self.path)


def mute_route(method: str, path: str) -> MuteResult:
    """Mark a route as muted so it is excluded from tracking."""
    k = _key(method, path)
    _muted.add(k)
    return MuteResult(method=method, path=path, muted=True)


def unmute_route(method: str, path: str) -> MuteResult:
    """Remove the mute flag from a route."""
    k = _key(method, path)
    _muted.discard(k)
    return MuteResult(method=method, path=path, muted=False)


def is_muted(method: str, path: str) -> bool:
    """Return True if the route is currently muted."""
    return _key(method, path) in _muted


def get_muted() -> Set[str]:
    """Return a copy of all muted route keys."""
    return set(_muted)


def muted_record(tracker: RouteTracker, method: str, path: str) -> bool:
    """Record a hit only if the route is not muted.

    Returns True if the hit was recorded, False if suppressed.
    """
    if is_muted(method, path):
        return False
    tracker.record(method, path)
    return True


def mute_report(tracker: RouteTracker) -> str:
    """Return a human-readable report of muted vs active routes."""
    lines = ["Route Muting Report", "=" * 36]
    all_keys = sorted(tracker.routes.keys())
    muted_count = 0
    for k in all_keys:
        status = "[MUTED] " if k in _muted else "[active]"
        if k in _muted:
            muted_count += 1
        lines.append(f"  {status}  {k}")
    lines.append("")
    lines.append(f"Total: {len(all_keys)} routes, {muted_count} muted")
    return "\n".join(lines)
