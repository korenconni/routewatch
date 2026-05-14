"""Hit decay: age-weighted dampening of route hit counts."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from routewatch.tracker import RouteTracker


@dataclass
class DecayConfig:
    """Configuration for hit-count decay."""

    half_life_seconds: float = 86_400.0  # 1 day
    min_hits: float = 0.0

    def __post_init__(self) -> None:
        if self.half_life_seconds <= 0:
            raise ValueError("half_life_seconds must be positive")
        if self.min_hits < 0:
            raise ValueError("min_hits must be >= 0")


@dataclass
class DecayedRoute:
    key: str
    raw_hits: int
    decayed_hits: float
    age_seconds: float


def _decay_factor(age_seconds: float, half_life: float) -> float:
    """Return exponential decay multiplier in [0, 1]."""
    import math

    return math.pow(0.5, age_seconds / half_life)


def apply_decay(
    tracker: RouteTracker,
    config: Optional[DecayConfig] = None,
    *,
    reference_time: Optional[float] = None,
) -> Dict[str, DecayedRoute]:
    """Return a mapping of route key -> DecayedRoute with decayed hit counts.

    Routes that have never been hit are returned with decayed_hits == 0.
    The *reference_time* parameter (epoch seconds) is exposed for testing.
    """
    if config is None:
        config = DecayConfig()

    now = reference_time if reference_time is not None else time.time()
    results: Dict[str, DecayedRoute] = {}

    for key, route_hit in tracker._routes.items():
        last_hit: Optional[float] = getattr(route_hit, "last_hit_at", None)

        if route_hit.hits == 0 or last_hit is None:
            age = 0.0
            decayed = 0.0
        else:
            age = max(0.0, now - last_hit)
            factor = _decay_factor(age, config.half_life_seconds)
            decayed = max(config.min_hits, route_hit.hits * factor)

        results[key] = DecayedRoute(
            key=key,
            raw_hits=route_hit.hits,
            decayed_hits=round(decayed, 4),
            age_seconds=round(age, 2),
        )

    return results


def decay_report(tracker: RouteTracker, config: Optional[DecayConfig] = None) -> str:
    """Return a human-readable decay report."""
    rows = apply_decay(tracker, config)
    if not rows:
        return "No routes registered.\n"

    lines = [f"{'Route':<45} {'Raw':>6} {'Decayed':>10} {'Age(s)':>10}"]
    lines.append("-" * 75)
    for dr in sorted(rows.values(), key=lambda r: r.decayed_hits, reverse=True):
        lines.append(
            f"{dr.key:<45} {dr.raw_hits:>6} {dr.decayed_hits:>10.2f} {dr.age_seconds:>10.1f}"
        )
    return "\n".join(lines) + "\n"
