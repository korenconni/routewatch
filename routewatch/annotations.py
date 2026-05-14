"""
routewatch.annotations
~~~~~~~~~~~~~~~~~~~~~~
Attach free-form annotation strings to routes (e.g. deprecation notes,
ownership info, SLA tags).  Annotations are stored per (method, path) key
and are independent of hit-count data.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .tracker import RouteTracker

# module-level store: tracker_id -> key -> {field: value}
_store: Dict[int, Dict[str, Dict[str, str]]] = {}


def _get_store(tracker: RouteTracker) -> Dict[str, Dict[str, str]]:
    tid = id(tracker)
    if tid not in _store:
        _store[tid] = {}
    return _store[tid]


def _key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def annotate(
    tracker: RouteTracker,
    method: str,
    path: str,
    field: str,
    value: str,
) -> None:
    """Set *field* to *value* for the given route.

    The route is auto-registered in *tracker* if not already known.
    """
    tracker.register(method, path)
    store = _get_store(tracker)
    key = _key(method, path)
    if key not in store:
        store[key] = {}
    store[key][field] = value


def get_annotation(
    tracker: RouteTracker,
    method: str,
    path: str,
    field: str,
) -> Optional[str]:
    """Return the annotation value for *field*, or ``None`` if absent."""
    store = _get_store(tracker)
    return store.get(_key(method, path), {}).get(field)


def get_annotations(
    tracker: RouteTracker,
    method: str,
    path: str,
) -> Dict[str, str]:
    """Return all annotations for a route as a plain dict (may be empty)."""
    store = _get_store(tracker)
    return dict(store.get(_key(method, path), {}))


def remove_annotation(
    tracker: RouteTracker,
    method: str,
    path: str,
    field: str,
) -> bool:
    """Remove a single annotation field.  Returns ``True`` if it existed."""
    store = _get_store(tracker)
    key = _key(method, path)
    if key in store and field in store[key]:
        del store[key][field]
        return True
    return False


def routes_with_annotation(
    tracker: RouteTracker,
    field: str,
) -> List[str]:
    """Return sorted list of route keys that have *field* set."""
    store = _get_store(tracker)
    return sorted(k for k, v in store.items() if field in v)


def clear_annotations(tracker: RouteTracker) -> None:
    """Remove all annotations for *tracker*."""
    _store.pop(id(tracker), None)
