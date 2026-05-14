"""Baseline comparison: lock a snapshot as the expected coverage baseline
and compare current tracker state against it."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from routewatch.tracker import RouteTracker


@dataclass
class BaselineResult:
    """Outcome of comparing a tracker against a saved baseline."""

    matched: List[str] = field(default_factory=list)
    regressed: List[str] = field(default_factory=list)   # covered in baseline, not now
    improved: List[str] = field(default_factory=list)    # not covered in baseline, now covered
    unknown: List[str] = field(default_factory=list)     # present now but not in baseline

    @property
    def has_regressions(self) -> bool:
        return bool(self.regressed)


def save_baseline(tracker: RouteTracker, path: str | Path) -> Dict:
    """Persist the current coverage state as a baseline JSON file."""
    path = Path(path)
    data: Dict = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "routes": {
            key: {"hits": info.hits, "covered": info.hits > 0}
            for key, info in tracker._routes.items()
        },
    }
    path.write_text(json.dumps(data, indent=2))
    return data


def load_baseline(path: str | Path) -> Dict:
    """Load a baseline file from disk."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Baseline file not found: {path}")
    return json.loads(path.read_text())


def compare_to_baseline(
    tracker: RouteTracker,
    baseline: Dict,
) -> BaselineResult:
    """Compare *tracker* coverage against a previously saved *baseline* dict."""
    baseline_routes: Dict = baseline.get("routes", {})
    result = BaselineResult()

    for key, info in tracker._routes.items():
        currently_covered = info.hits > 0
        if key not in baseline_routes:
            result.unknown.append(key)
            continue
        was_covered = baseline_routes[key].get("covered", False)
        if was_covered and currently_covered:
            result.matched.append(key)
        elif was_covered and not currently_covered:
            result.regressed.append(key)
        elif not was_covered and currently_covered:
            result.improved.append(key)
        else:
            result.matched.append(key)

    return result


def baseline_report(result: BaselineResult) -> str:
    """Return a human-readable text report of a BaselineResult."""
    lines = ["=== Baseline Comparison ==="]
    lines.append(f"  Matched   : {len(result.matched)}")
    lines.append(f"  Improved  : {len(result.improved)}")
    lines.append(f"  Regressed : {len(result.regressed)}")
    lines.append(f"  Unknown   : {len(result.unknown)}")
    if result.regressed:
        lines.append("\nRegressed routes (were covered, now missing hits):")
        for r in sorted(result.regressed):
            lines.append(f"  - {r}")
    if result.improved:
        lines.append("\nImproved routes (newly covered):")
        for r in sorted(result.improved):
            lines.append(f"  + {r}")
    return "\n".join(lines)
