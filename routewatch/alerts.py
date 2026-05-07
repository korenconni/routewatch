"""Alert system for routewatch — notify when coverage drops below a threshold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from routewatch.report import coverage_percent, missing_routes
from routewatch.tracker import RouteTracker


@dataclass
class AlertResult:
    """Result of an alert check."""

    triggered: bool
    coverage: float
    threshold: float
    uncovered: List[str]
    message: str


def check_coverage_alert(
    tracker: RouteTracker,
    threshold: float = 80.0,
) -> AlertResult:
    """Return an AlertResult indicating whether coverage is below *threshold* percent."""
    if not (0.0 <= threshold <= 100.0):
        raise ValueError(f"threshold must be between 0 and 100, got {threshold}")

    coverage = coverage_percent(tracker)
    uncovered = missing_routes(tracker)
    triggered = coverage < threshold

    if triggered:
        message = (
            f"Coverage alert: {coverage:.1f}% is below the required {threshold:.1f}%. "
            f"{len(uncovered)} route(s) never hit."
        )
    else:
        message = (
            f"Coverage OK: {coverage:.1f}% meets the required {threshold:.1f}%."
        )

    return AlertResult(
        triggered=triggered,
        coverage=coverage,
        threshold=threshold,
        uncovered=uncovered,
        message=message,
    )


def on_alert(
    tracker: RouteTracker,
    callback: Callable[[AlertResult], None],
    threshold: float = 80.0,
) -> AlertResult:
    """Run *callback* with the AlertResult when coverage drops below *threshold*.

    The callback is invoked only when the alert is triggered.
    Returns the AlertResult regardless.
    """
    result = check_coverage_alert(tracker, threshold=threshold)
    if result.triggered:
        callback(result)
    return result
