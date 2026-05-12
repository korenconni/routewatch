"""Route health scoring for routewatch.

Assigns a numeric health score (0–100) to each tracked route based on
hit frequency, recency, and whether the route has been covered at all.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

from routewatch.tracker import RouteTracker


@dataclass
class RouteScore:
    method: str
    path: str
    hits: int
    score: float  # 0.0 – 100.0
    grade: str    # A / B / C / D / F


def _grade(score: float) -> str:
    """Convert a numeric score to a letter grade."""
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 50:
        return "C"
    if score >= 25:
        return "D"
    return "F"


def score_route(hits: int, max_hits: int) -> float:
    """Return a 0-100 score for a single route.

    Uses a logarithmic scale so that the first few hits matter most.
    A route with zero hits always scores 0.
    A route matching *max_hits* scores 100.
    """
    if hits <= 0 or max_hits <= 0:
        return 0.0
    raw = math.log1p(hits) / math.log1p(max_hits)
    return round(min(raw * 100.0, 100.0), 2)


def build_scores(tracker: RouteTracker) -> List[RouteScore]:
    """Compute a RouteScore for every registered route."""
    all_hits = [tracker.routes[k].hits for k in tracker.routes]
    max_hits = max(all_hits, default=0)

    scores: List[RouteScore] = []
    for key, route_hit in tracker.routes.items():
        method, path = key.split(" ", 1)
        s = score_route(route_hit.hits, max_hits)
        scores.append(
            RouteScore(
                method=method,
                path=path,
                hits=route_hit.hits,
                score=s,
                grade=_grade(s),
            )
        )
    scores.sort(key=lambda r: r.score, reverse=True)
    return scores


def average_score(tracker: RouteTracker) -> float:
    """Return the mean health score across all registered routes."""
    scores = build_scores(tracker)
    if not scores:
        return 0.0
    return round(sum(r.score for r in scores) / len(scores), 2)


def scoring_report(tracker: RouteTracker) -> str:
    """Return a human-readable scoring report."""
    scores = build_scores(tracker)
    if not scores:
        return "No routes registered."
    lines = [f"{'Grade':<6} {'Score':>6}  {'Hits':>6}  Route"]
    lines.append("-" * 50)
    for rs in scores:
        lines.append(
            f"{rs.grade:<6} {rs.score:>6.1f}  {rs.hits:>6}  {rs.method} {rs.path}"
        )
    lines.append("-" * 50)
    lines.append(f"Average score: {average_score(tracker):.1f}")
    return "\n".join(lines)
