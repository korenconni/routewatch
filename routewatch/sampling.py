"""Route hit sampling — record only a fraction of hits to reduce overhead."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from routewatch.tracker import RouteTracker


@dataclass
class SamplingConfig:
    """Configuration for hit sampling."""

    rate: float = 1.0  # 0.0 – 1.0; 1.0 means record every hit
    seed: Optional[int] = None
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not 0.0 <= self.rate <= 1.0:
            raise ValueError(f"Sampling rate must be between 0.0 and 1.0, got {self.rate}")
        self._rng = random.Random(self.seed)

    def should_record(self) -> bool:
        """Return True if this hit should be recorded given the current rate."""
        if self.rate >= 1.0:
            return True
        if self.rate <= 0.0:
            return False
        return self._rng.random() < self.rate

    def reset(self, seed: Optional[int] = None) -> None:
        """Reset the internal RNG, optionally with a new seed.

        Useful in tests or when you want to replay a deterministic sequence
        from a known starting point without creating a new SamplingConfig.
        """
        self.seed = seed
        self._rng = random.Random(self.seed)


def sampled_record(
    tracker: RouteTracker,
    method: str,
    path: str,
    config: SamplingConfig,
) -> bool:
    """Record a hit only if the sampler allows it.

    Returns True when the hit was actually recorded, False when it was skipped.
    """
    if config.should_record():
        tracker.record(method, path)
        return True
    return False


def effective_hit_count(raw_count: int, rate: float) -> float:
    """Estimate the true hit count by scaling up a sampled raw count.

    Raises ValueError when *rate* is zero to avoid division by zero.
    """
    if rate <= 0.0:
        raise ValueError("Cannot estimate effective count with a zero sampling rate.")
    return raw_count / rate
