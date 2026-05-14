"""routewatch — Lightweight HTTP route coverage tracker.

Public re-exports for the most commonly used symbols.
"""
from routewatch.tracker import RouteTracker, RouteHit  # noqa: F401
from routewatch.report import build_summary, coverage_percent, text_report  # noqa: F401
from routewatch.snapshot import dump_snapshot, save_snapshot, load_snapshot  # noqa: F401
from routewatch.baseline import (  # noqa: F401
    BaselineResult,
    save_baseline,
    load_baseline,
    compare_to_baseline,
    baseline_report,
)

__version__ = "0.9.0"
__all__ = [
    "RouteTracker",
    "RouteHit",
    "build_summary",
    "coverage_percent",
    "text_report",
    "dump_snapshot",
    "save_snapshot",
    "load_snapshot",
    "BaselineResult",
    "save_baseline",
    "load_baseline",
    "compare_to_baseline",
    "baseline_report",
]
