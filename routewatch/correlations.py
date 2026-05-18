"""Route correlation tracking — detect routes that are frequently hit together."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Tuple

from routewatch.tracker import RouteTracker

# co-occurrence counts: frozenset({key_a, key_b}) -> count
_store: Dict[FrozenSet[str], int] = defaultdict(int)

# per-request buffer: session_id -> list of keys seen
_sessions: Dict[str, List[str]] = defaultdict(list)


def _key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def record_correlation(session_id: str, method: str, path: str) -> None:
    """Record a route hit within a session context."""
    k = _key(method, path)
    seen = _sessions[session_id]
    for existing in seen:
        pair: FrozenSet[str] = frozenset({existing, k})
        _store[pair] += 1
    seen.append(k)


def flush_session(session_id: str) -> None:
    """Discard buffered session data."""
    _sessions.pop(session_id, None)


@dataclass
class CorrelationPair:
    route_a: str
    route_b: str
    count: int


def top_correlations(n: int = 10) -> List[CorrelationPair]:
    """Return the *n* most co-occurring route pairs."""
    ranked: List[Tuple[FrozenSet[str], int]] = sorted(
        _store.items(), key=lambda x: x[1], reverse=True
    )
    results: List[CorrelationPair] = []
    for pair, count in ranked[:n]:
        a, b = sorted(pair)
        results.append(CorrelationPair(route_a=a, route_b=b, count=count))
    return results


def correlations_for(method: str, path: str, n: int = 5) -> List[CorrelationPair]:
    """Return routes most often seen alongside *method* + *path*."""
    target = _key(method, path)
    related: List[Tuple[str, int]] = []
    for pair, count in _store.items():
        if target in pair:
            other = next(iter(pair - {target}))
            related.append((other, count))
    related.sort(key=lambda x: x[1], reverse=True)
    return [
        CorrelationPair(route_a=target, route_b=other, count=cnt)
        for other, cnt in related[:n]
    ]


def clear_correlations() -> None:
    """Reset all co-occurrence data."""
    _store.clear()
    _sessions.clear()
