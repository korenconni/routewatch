"""Snapshot diff utility: compare two RouteTracker snapshots to detect added/removed/changed routes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from routewatch.tracker import RouteTracker


@dataclass
class RouteDiff:
    """Result of comparing two snapshots."""

    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    hit_changes: Dict[str, tuple] = field(default_factory=dict)  # key -> (old_hits, new_hits)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.hit_changes)


def diff_trackers(old: RouteTracker, new: RouteTracker) -> RouteDiff:
    """Compare two RouteTracker instances and return a RouteDiff.

    Args:
        old: The baseline tracker (e.g. loaded from a previous snapshot).
        new: The current tracker to compare against.

    Returns:
        A RouteDiff describing what changed between the two trackers.
    """
    old_routes = dict(old.routes)
    new_routes = dict(new.routes)

    old_keys = set(old_routes)
    new_keys = set(new_routes)

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)

    hit_changes: Dict[str, tuple] = {}
    for key in old_keys & new_keys:
        old_hits = old_routes[key].hits
        new_hits = new_routes[key].hits
        if old_hits != new_hits:
            hit_changes[key] = (old_hits, new_hits)

    return RouteDiff(added=added, removed=removed, hit_changes=hit_changes)


def diff_report(diff: RouteDiff) -> str:
    """Render a human-readable diff report.

    Args:
        diff: A RouteDiff produced by :func:`diff_trackers`.

    Returns:
        A multi-line string suitable for printing to stdout.
    """
    lines: List[str] = ["=== RouteWatch Diff ==="]

    if not diff.has_changes:
        lines.append("No changes detected.")
        return "\n".join(lines)

    if diff.added:
        lines.append(f"\nAdded routes ({len(diff.added)}):")
        for key in diff.added:
            lines.append(f"  + {key}")

    if diff.removed:
        lines.append(f"\nRemoved routes ({len(diff.removed)}):")
        for key in diff.removed:
            lines.append(f"  - {key}")

    if diff.hit_changes:
        lines.append(f"\nHit count changes ({len(diff.hit_changes)}):")
        for key, (old_hits, new_hits) in sorted(diff.hit_changes.items()):
            lines.append(f"  ~ {key}: {old_hits} -> {new_hits}")

    return "\n".join(lines)
