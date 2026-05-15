"""Route audit log: record who triggered a route hit and when."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from routewatch.tracker import RouteTracker

_DEFAULT_MAX_ENTRIES = 200

# module-level store: key -> list of AuditEntry
_store: Dict[str, List["AuditEntry"]] = {}


@dataclass
class AuditEntry:
    method: str
    path: str
    actor: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.method.upper()} {self.path}"


def _get_store() -> Dict[str, List[AuditEntry]]:
    return _store


def record_audit(
    tracker: RouteTracker,
    method: str,
    path: str,
    actor: str,
    metadata: Optional[Dict[str, str]] = None,
    max_entries: int = _DEFAULT_MAX_ENTRIES,
) -> AuditEntry:
    """Record an audit entry for a route hit, auto-registering the route."""
    key = f"{method.upper()} {path}"
    if key not in tracker.routes:
        tracker.register(method, path)

    entry = AuditEntry(
        method=method.upper(),
        path=path,
        actor=actor,
        metadata=metadata or {},
    )
    bucket = _store.setdefault(key, [])
    bucket.append(entry)
    if len(bucket) > max_entries:
        bucket.pop(0)
    return entry


def get_audit_log(method: str, path: str) -> List[AuditEntry]:
    """Return all audit entries for a route, oldest first."""
    key = f"{method.upper()} {path}"
    return list(_store.get(key, []))


def clear_audit_log(method: Optional[str] = None, path: Optional[str] = None) -> None:
    """Clear audit entries. If method+path given, clear only that route."""
    if method is not None and path is not None:
        key = f"{method.upper()} {path}"
        _store.pop(key, None)
    else:
        _store.clear()


def audit_report(tracker: RouteTracker) -> str:
    """Return a human-readable audit summary for all registered routes."""
    lines: List[str] = ["Route Audit Report", "=================="]
    for key in sorted(tracker.routes):
        entries = _store.get(key, [])
        lines.append(f"{key}: {len(entries)} audit entries")
        for e in entries[-3:]:
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(e.timestamp))
            lines.append(f"  [{ts}] actor={e.actor} meta={e.metadata}")
    return "\n".join(lines)
