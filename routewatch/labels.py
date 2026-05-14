"""Route labelling: attach arbitrary key/value metadata to routes."""
from __future__ import annotations

from typing import Any, Dict, Optional

from routewatch.tracker import RouteTracker

# {tracker_id -> {route_key -> {label_key -> value}}}
_store: Dict[int, Dict[str, Dict[str, Any]]] = {}


def _get_store(tracker: RouteTracker) -> Dict[str, Dict[str, Any]]:
    tid = id(tracker)
    if tid not in _store:
        _store[tid] = {}
    return _store[tid]


def set_label(tracker: RouteTracker, method: str, path: str, key: str, value: Any) -> None:
    """Attach *key*/*value* metadata to a route, auto-registering it if needed."""
    route_key = f"{method.upper()} {path}"
    if route_key not in tracker.routes:
        tracker.register(method, path)
    store = _get_store(tracker)
    if route_key not in store:
        store[route_key] = {}
    store[route_key][key] = value


def get_label(tracker: RouteTracker, method: str, path: str, key: str) -> Optional[Any]:
    """Return the label value for *key*, or ``None`` if not set."""
    route_key = f"{method.upper()} {path}"
    return _get_store(tracker).get(route_key, {}).get(key)


def get_labels(tracker: RouteTracker, method: str, path: str) -> Dict[str, Any]:
    """Return all labels for a route as a dict (empty dict if none)."""
    route_key = f"{method.upper()} {path}"
    return dict(_get_store(tracker).get(route_key, {}))


def remove_label(tracker: RouteTracker, method: str, path: str, key: str) -> bool:
    """Remove a single label key.  Returns True if the key existed."""
    route_key = f"{method.upper()} {path}"
    labels = _get_store(tracker).get(route_key, {})
    if key in labels:
        del labels[key]
        return True
    return False


def routes_by_label(tracker: RouteTracker, key: str, value: Any) -> list[str]:
    """Return route keys whose *key* label equals *value*."""
    store = _get_store(tracker)
    return [
        route_key
        for route_key, labels in store.items()
        if labels.get(key) == value
    ]


def clear_labels(tracker: RouteTracker, method: str, path: str) -> None:
    """Remove all labels for a route."""
    route_key = f"{method.upper()} {path}"
    _get_store(tracker).pop(route_key, None)
