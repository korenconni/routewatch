"""Tag-based grouping and filtering for tracked routes."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set

from routewatch.tracker import RouteTracker


def tag_route(tracker: RouteTracker, method: str, path: str, *tags: str) -> None:
    """Attach one or more tags to a registered route.

    If the route is not yet registered it will be auto-registered first.
    """
    key = tracker._key(method, path)
    if key not in tracker._routes:
        tracker.register(method, path)
    existing: Set[str] = tracker._routes[key].get("tags", set())  # type: ignore[assignment]
    existing.update(tags)
    tracker._routes[key]["tags"] = existing  # type: ignore[index]


def get_tags(tracker: RouteTracker, method: str, path: str) -> Set[str]:
    """Return the set of tags for a route, or an empty set if none."""
    key = tracker._key(method, path)
    route = tracker._routes.get(key)
    if route is None:
        return set()
    return set(route.get("tags", set()))  # type: ignore[arg-type]


def routes_by_tag(tracker: RouteTracker) -> Dict[str, List[dict]]:
    """Return a mapping of tag -> list of route info dicts.

    Routes without any tags appear under the key ``"untagged"``.
    """
    mapping: Dict[str, List[dict]] = defaultdict(list)
    for key, route in tracker._routes.items():
        tags: Set[str] = route.get("tags", set())  # type: ignore[assignment]
        if not tags:
            mapping["untagged"].append({"key": key, **route})
        else:
            for tag in tags:
                mapping[tag].append({"key": key, **route})
    return dict(mapping)


def filter_by_tag(tracker: RouteTracker, tag: str) -> List[dict]:
    """Return route info dicts for all routes carrying *tag*."""
    result = []
    for key, route in tracker._routes.items():
        tags: Set[str] = route.get("tags", set())  # type: ignore[assignment]
        if tag in tags:
            result.append({"key": key, **route})
    return result


def remove_tag(tracker: RouteTracker, method: str, path: str, tag: str) -> bool:
    """Remove a single tag from a route.  Returns True if the tag was present."""
    key = tracker._key(method, path)
    route = tracker._routes.get(key)
    if route is None:
        return False
    tags: Set[str] = route.get("tags", set())  # type: ignore[assignment]
    if tag not in tags:
        return False
    tags.discard(tag)
    tracker._routes[key]["tags"] = tags  # type: ignore[index]
    return True
