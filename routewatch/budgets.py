"""Route hit budget enforcement for routewatch.

Allows setting minimum and maximum hit budgets per route and checking
whether routes are within their expected traffic bounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from routewatch.tracker import RouteTracker


@dataclass
class BudgetResult:
    route: str
    method: str
    hits: int
    min_hits: Optional[int]
    max_hits: Optional[int]
    under_budget: bool
    over_budget: bool

    @property
    def in_budget(self) -> bool:
        return not self.under_budget and not self.over_budget


@dataclass
class BudgetReport:
    results: list[BudgetResult] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return any(not r.in_budget for r in self.results)

    @property
    def violations(self) -> list[BudgetResult]:
        return [r for r in self.results if not r.in_budget]


# Internal registry: key -> (min_hits, max_hits)
_budgets: Dict[Tuple[str, str], Tuple[Optional[int], Optional[int]]] = {}


def _key(method: str, route: str) -> Tuple[str, str]:
    return (method.upper(), route)


def set_budget(
    method: str,
    route: str,
    min_hits: Optional[int] = None,
    max_hits: Optional[int] = None,
) -> None:
    """Register a hit budget for a route. At least one bound must be provided."""
    if min_hits is None and max_hits is None:
        raise ValueError("At least one of min_hits or max_hits must be specified.")
    if min_hits is not None and min_hits < 0:
        raise ValueError("min_hits must be >= 0.")
    if max_hits is not None and max_hits < 0:
        raise ValueError("max_hits must be >= 0.")
    if min_hits is not None and max_hits is not None and min_hits > max_hits:
        raise ValueError("min_hits must be <= max_hits.")
    _budgets[_key(method, route)] = (min_hits, max_hits)


def remove_budget(method: str, route: str) -> bool:
    """Remove a budget for a route. Returns True if a budget existed."""
    return _budgets.pop(_key(method, route), None) is not None


def get_budget(method: str, route: str) -> Tuple[Optional[int], Optional[int]]:
    """Return (min_hits, max_hits) for a route, or (None, None) if unset."""
    return _budgets.get(_key(method, route), (None, None))


def check_budgets(tracker: RouteTracker) -> BudgetReport:
    """Evaluate all budgeted routes against current hit counts."""
    results: list[BudgetResult] = []
    for (method, route), (min_hits, max_hits) in _budgets.items():
        hits = tracker.hits(method, route)
        under = min_hits is not None and hits < min_hits
        over = max_hits is not None and hits > max_hits
        results.append(
            BudgetResult(
                route=route,
                method=method,
                hits=hits,
                min_hits=min_hits,
                max_hits=max_hits,
                under_budget=under,
                over_budget=over,
            )
        )
    return BudgetReport(results=results)


def clear_budgets() -> None:
    """Remove all registered budgets."""
    _budgets.clear()
