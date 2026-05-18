"""Route segment analysis — break routes into path segments and aggregate hit stats."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from routewatch.tracker import RouteTracker


@dataclass
class SegmentNode:
    """Represents a single path segment with aggregated hit counts."""
    segment: str
    total_hits: int = 0
    route_count: int = 0
    covered_count: int = 0
    children: Dict[str, "SegmentNode"] = field(default_factory=dict)

    @property
    def coverage_percent(self) -> float:
        if self.route_count == 0:
            return 0.0
        return round(self.covered_count / self.route_count * 100, 2)


def _split_path(path: str) -> List[str]:
    """Split a URL path into non-empty segments."""
    return [p for p in path.strip("/").split("/") if p]


def build_segment_tree(tracker: RouteTracker) -> Dict[str, SegmentNode]:
    """Build a tree of SegmentNodes from all registered routes.

    The top-level dict is keyed by the first path segment (or '__root__' for '/').
    """
    roots: Dict[str, SegmentNode] = {}

    for key, hit in tracker._routes.items():
        method, path = key.split(" ", 1)
        segments = _split_path(path)
        if not segments:
            segments = ["__root__"]

        top = segments[0]
        if top not in roots:
            roots[top] = SegmentNode(segment=top)
        node = roots[top]
        node.route_count += 1
        node.total_hits += hit.hits
        if hit.hits > 0:
            node.covered_count += 1

        current = node
        for seg in segments[1:]:
            if seg not in current.children:
                current.children[seg] = SegmentNode(segment=seg)
            child = current.children[seg]
            child.route_count += 1
            child.total_hits += hit.hits
            if hit.hits > 0:
                child.covered_count += 1
            current = child

    return roots


def flat_segment_stats(tracker: RouteTracker) -> List[SegmentNode]:
    """Return a flat list of top-level SegmentNodes sorted by total_hits descending."""
    roots = build_segment_tree(tracker)
    return sorted(roots.values(), key=lambda n: n.total_hits, reverse=True)


def segment_report(tracker: RouteTracker) -> str:
    """Return a human-readable segment coverage report."""
    nodes = flat_segment_stats(tracker)
    if not nodes:
        return "No routes registered.\n"
    lines = ["Segment Coverage Report", "=" * 30]
    for node in nodes:
        lines.append(
            f"/{node.segment:<20} routes={node.route_count}  "
            f"hits={node.total_hits}  coverage={node.coverage_percent}%"
        )
    return "\n".join(lines) + "\n"
