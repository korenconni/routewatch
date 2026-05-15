"""Route dependency tracking: record which routes depend on shared resources."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set

from routewatch.tracker import RouteTracker

_store: Dict[str, Set[str]] = {}  # resource -> set of route keys


def _key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


@dataclass
class DependencyResult:
    resource: str
    routes: Set[str] = field(default_factory=set)

    @property
    def route_count(self) -> int:
        return len(self.routes)


def add_dependency(
    tracker: RouteTracker,
    method: str,
    path: str,
    resource: str,
) -> DependencyResult:
    """Record that a route depends on *resource*.

    The route is auto-registered in *tracker* if it is not already known.
    """
    k = _key(method, path)
    if k not in tracker.routes:
        tracker.register(method, path)
    _store.setdefault(resource, set()).add(k)
    return DependencyResult(resource=resource, routes=set(_store[resource]))


def remove_dependency(
    method: str,
    path: str,
    resource: str,
) -> bool:
    """Remove the dependency link between a route and *resource*.

    Returns True if the link existed and was removed, False otherwise.
    """
    k = _key(method, path)
    if resource in _store and k in _store[resource]:
        _store[resource].discard(k)
        if not _store[resource]:
            del _store[resource]
        return True
    return False


def get_dependencies(resource: str) -> DependencyResult:
    """Return all routes that depend on *resource*."""
    routes = set(_store.get(resource, set()))
    return DependencyResult(resource=resource, routes=routes)


def routes_for_resource(resource: str) -> Set[str]:
    """Convenience: return the raw set of route keys for *resource*."""
    return set(_store.get(resource, set()))


def resources_for_route(method: str, path: str) -> Set[str]:
    """Return every resource that the given route depends on."""
    k = _key(method, path)
    return {res for res, routes in _store.items() if k in routes}


def all_resources() -> Set[str]:
    """Return the set of all tracked resource names."""
    return set(_store.keys())
