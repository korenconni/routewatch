"""Human-readable and machine-readable coverage reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import List

from routewatch.tracker import RouteTracker


@dataclass
class RouteSummary:
    path: str
    method: str
    hits: int
    covered: bool


def build_summary(tracker: RouteTracker) -> List[RouteSummary]:
    """Return a list of RouteSummary objects for all registered routes."""
    summaries: List[RouteSummary] = []
    for (path, method), hit in tracker._routes.items():
        summaries.append(
            RouteSummary(
                path=path,
                method=method,
                hits=hit.count,
                covered=hit.count > 0,
            )
        )
    return sorted(summaries, key=lambda s: (s.path, s.method))


def coverage_percent(tracker: RouteTracker) -> float:
    """Return the percentage of registered routes that have been hit."""
    summaries = build_summary(tracker)
    if not summaries:
        return 0.0
    covered = sum(1 for s in summaries if s.covered)
    return round(covered / len(summaries) * 100, 2)


def missing_routes(tracker: RouteTracker) -> List[RouteSummary]:
    """Return a list of RouteSummary objects for routes that have not been hit.

    Useful for quickly identifying uncovered endpoints without parsing the
    full report output.
    """
    return [s for s in build_summary(tracker) if not s.covered]


def text_report(tracker: RouteTracker) -> str:
    """Render a plain-text coverage table."""
    summaries = build_summary(tracker)
    if not summaries:
        return "No routes registered."

    lines = [
        f"{'METHOD':<8} {'PATH':<40} {'HITS':>6}  STATUS",
        "-" * 62,
    ]
    for s in summaries:
        status = "COVERED" if s.covered else "MISSING"
        lines.append(f"{s.method:<8} {s.path:<40} {s.hits:>6}  {status}")

    pct = coverage_percent(tracker)
    lines.append("-" * 62)
    lines.append(f"Coverage: {pct}%  ({sum(s.covered for s in summaries)}/{len(summaries)} routes)")
    return "\n".join(lines)


def json_report(tracker: RouteTracker) -> str:
    """Render a JSON coverage report."""
    summaries = build_summary(tracker)
    payload = {
        "coverage_percent": coverage_percent(tracker),
        "total": len(summaries),
        "covered": sum(s.covered for s in summaries),
        "routes": [asdict(s) for s in summaries],
    }
    return json.dumps(payload, indent=2)
