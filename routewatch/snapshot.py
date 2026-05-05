"""Snapshot serialization and deserialization for RouteTracker state."""

import json
import time
from typing import Any, Dict

from routewatch.tracker import RouteTracker


SNAPSHOT_VERSION = 1


def dump_snapshot(tracker: RouteTracker) -> Dict[str, Any]:
    """Serialize a RouteTracker to a plain dict suitable for JSON output."""
    routes = []
    for key, hit in tracker._routes.items():
        method, path = key
        routes.append(
            {
                "method": method,
                "path": path,
                "count": hit.count,
                "last_seen": hit.last_seen,
            }
        )

    return {
        "version": SNAPSHOT_VERSION,
        "created_at": time.time(),
        "routes": routes,
    }


def save_snapshot(tracker: RouteTracker, filepath: str) -> None:
    """Write a RouteTracker snapshot to a JSON file."""
    data = dump_snapshot(tracker)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def load_snapshot(filepath: str) -> RouteTracker:
    """Load a RouteTracker from a previously saved JSON snapshot file."""
    with open(filepath, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return _tracker_from_dict(data)


def loads_snapshot(raw: str) -> RouteTracker:
    """Load a RouteTracker from a JSON string."""
    data = json.loads(raw)
    return _tracker_from_dict(data)


def _tracker_from_dict(data: Dict[str, Any]) -> RouteTracker:
    """Reconstruct a RouteTracker from a snapshot dict."""
    version = data.get("version", 1)
    if version != SNAPSHOT_VERSION:
        raise ValueError(
            f"Unsupported snapshot version {version!r}; expected {SNAPSHOT_VERSION}"
        )

    tracker = RouteTracker()
    for entry in data.get("routes", []):
        method = entry["method"]
        path = entry["path"]
        tracker.register(method, path)
        hit = tracker._routes[tracker._key(method, path)]
        hit.count = entry.get("count", 0)
        hit.last_seen = entry.get("last_seen")

    return tracker
