"""SLA (Service Level Agreement) tracking for route hit targets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from routewatch.tracker import RouteTracker

_store: Dict[str, "SLATarget"] = {}


@dataclass
class SLATarget:
    method: str
    path: str
    min_hits: int
    period_label: str = "total"

    def key(self) -> str:
        return f"{self.method.upper()}:{self.path}"


@dataclass
class SLAResult:
    target: SLATarget
    actual_hits: int
    met: bool
    shortfall: int


@dataclass
class SLAReport:
    results: List[SLAResult] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return any(not r.met for r in self.results)

    @property
    def violations(self) -> List[SLAResult]:
        return [r for r in self.results if not r.met]


def set_sla(tracker: RouteTracker, method: str, path: str, min_hits: int, period_label: str = "total") -> SLATarget:
    """Register an SLA target for a route."""
    method = method.upper()
    tracker.register(method, path)
    target = SLATarget(method=method, path=path, min_hits=min_hits, period_label=period_label)
    _store[target.key()] = target
    return target


def get_sla(method: str, path: str) -> Optional[SLATarget]:
    """Retrieve an SLA target, or None if not set."""
    return _store.get(f"{method.upper()}:{path}")


def remove_sla(method: str, path: str) -> bool:
    """Remove an SLA target. Returns True if it existed."""
    key = f"{method.upper()}:{path}"
    if key in _store:
        del _store[key]
        return True
    return False


def check_sla(tracker: RouteTracker) -> SLAReport:
    """Evaluate all registered SLA targets against current hit counts."""
    report = SLAReport()
    for key, target in _store.items():
        hit = tracker.routes.get(key)
        actual = hit.count if hit else 0
        met = actual >= target.min_hits
        shortfall = max(0, target.min_hits - actual)
        report.results.append(SLAResult(target=target, actual_hits=actual, met=met, shortfall=shortfall))
    return report


def sla_text_report(report: SLAReport) -> str:
    """Render a human-readable SLA report."""
    lines = ["SLA Report", "=" * 40]
    for r in report.results:
        status = "OK" if r.met else "FAIL"
        lines.append(
            f"[{status}] {r.target.method} {r.target.path} "
            f"hits={r.actual_hits}/{r.target.min_hits} "
            f"(period: {r.target.period_label})"
        )
    if not report.results:
        lines.append("No SLA targets registered.")
    lines.append("=" * 40)
    lines.append(f"Violations: {len(report.violations)}/{len(report.results)}")
    return "\n".join(lines)
