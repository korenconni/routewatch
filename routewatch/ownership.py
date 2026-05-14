"""Route ownership tracking for routewatch."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from routewatch.tracker import RouteTracker

# module-level store: (METHOD, PATH) -> owner metadata
_store: Dict[str, "OwnerInfo"] = {}


@dataclass
class OwnerInfo:
    team: str
    contact: Optional[str] = None
    notes: Optional[str] = None


def _key(method: str, path: str) -> str:
    return f"{method.upper()}:{path}"


def assign_owner(
    tracker: RouteTracker,
    method: str,
    path: str,
    team: str,
    contact: Optional[str] = None,
    notes: Optional[str] = None,
) -> OwnerInfo:
    """Assign an owner to a route, auto-registering it if unknown."""
    k = _key(method, path)
    route_key = tracker._key(method, path)
    if route_key not in tracker._routes:
        tracker.register(method, path)
    info = OwnerInfo(team=team, contact=contact, notes=notes)
    _store[k] = info
    return info


def get_owner(method: str, path: str) -> Optional[OwnerInfo]:
    """Return the OwnerInfo for a route, or None if unassigned."""
    return _store.get(_key(method, path))


def remove_owner(method: str, path: str) -> bool:
    """Remove ownership info. Returns True if an entry was removed."""
    k = _key(method, path)
    if k in _store:
        del _store[k]
        return True
    return False


def routes_by_team(team: str) -> List[str]:
    """Return all route keys owned by *team*."""
    return [k for k, info in _store.items() if info.team == team]


def unowned_routes(tracker: RouteTracker) -> List[str]:
    """Return route keys present in the tracker that have no owner assigned."""
    result = []
    for rk in tracker._routes:
        method, path = rk.split(":", 1)
        if _key(method, path) not in _store:
            result.append(rk)
    return result


def ownership_report(tracker: RouteTracker) -> str:
    """Return a human-readable ownership report."""
    lines: List[str] = ["Route Ownership Report", "=" * 40]
    for rk in sorted(tracker._routes):
        method, path = rk.split(":", 1)
        info = get_owner(method, path)
        if info:
            contact_str = f" <{info.contact}>" if info.contact else ""
            lines.append(f"  {rk:40s}  {info.team}{contact_str}")
        else:
            lines.append(f"  {rk:40s}  (unowned)")
    return "\n".join(lines)
