"""Per-route hit quotas: define expected hit ranges and check compliance."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from routewatch.tracker import RouteTracker

_store: Dict[str, "QuotaConfig"] = {}


def _key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


@dataclass
class QuotaConfig:
    method: str
    path: str
    min_hits: int = 0
    max_hits: Optional[int] = None

    @property
    def key(self) -> str:
        return _key(self.method, self.path)


@dataclass
class QuotaResult:
    method: str
    path: str
    hits: int
    min_hits: int
    max_hits: Optional[int]
    within_quota: bool
    reason: str

    @property
    def key(self) -> str:
        return _key(self.method, self.path)


@dataclass
class QuotaReport:
    results: List[QuotaResult] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return any(not r.within_quota for r in self.results)

    @property
    def violations(self) -> List[QuotaResult]:
        return [r for r in self.results if not r.within_quota]


def set_quota(
    tracker: RouteTracker,
    method: str,
    path: str,
    *,
    min_hits: int = 0,
    max_hits: Optional[int] = None,
) -> QuotaConfig:
    """Register a quota for a route, auto-registering it in the tracker."""
    if max_hits is not None and max_hits < min_hits:
        raise ValueError("max_hits must be >= min_hits")
    if min_hits < 0:
        raise ValueError("min_hits must be >= 0")
    tracker.register(method, path)
    cfg = QuotaConfig(method=method, path=path, min_hits=min_hits, max_hits=max_hits)
    _store[cfg.key] = cfg
    return cfg


def remove_quota(method: str, path: str) -> bool:
    """Remove a quota definition. Returns True if it existed."""
    return _store.pop(_key(method, path), None) is not None


def get_quota(method: str, path: str) -> Optional[QuotaConfig]:
    return _store.get(_key(method, path))


def check_quotas(tracker: RouteTracker) -> QuotaReport:
    """Evaluate all registered quotas against current hit counts."""
    results: List[QuotaResult] = []
    for k, cfg in _store.items():
        hits = tracker.hits(cfg.method, cfg.path)
        if hits < cfg.min_hits:
            within = False
            reason = f"hits {hits} below min {cfg.min_hits}"
        elif cfg.max_hits is not None and hits > cfg.max_hits:
            within = False
            reason = f"hits {hits} above max {cfg.max_hits}"
        else:
            within = True
            reason = "ok"
        results.append(
            QuotaResult(
                method=cfg.method,
                path=cfg.path,
                hits=hits,
                min_hits=cfg.min_hits,
                max_hits=cfg.max_hits,
                within_quota=within,
                reason=reason,
            )
        )
    return QuotaReport(results=results)
