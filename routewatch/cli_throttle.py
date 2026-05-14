"""CLI for inspecting throttle behaviour against a snapshot.

Usage examples::

    # Show which routes would be suppressed at max 5 hits / 30 s
    routewatch-throttle snapshot.json --max-hits 5 --window 30
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from routewatch.cli import _load_tracker_from_snapshot
from routewatch.throttle import RouteThrottle, ThrottleConfig
from routewatch.report import build_summary


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="routewatch-throttle",
        description="Simulate throttle suppression against a RouteWatch snapshot.",
    )
    p.add_argument("snapshot", help="Path to a .json snapshot file.")
    p.add_argument(
        "--max-hits",
        type=int,
        default=10,
        dest="max_hits",
        help="Maximum hits allowed per window (default: 10).",
    )
    p.add_argument(
        "--window",
        type=float,
        default=60.0,
        dest="window_seconds",
        help="Rolling window in seconds (default: 60).",
    )
    p.add_argument(
        "--show-suppressed",
        action="store_true",
        dest="show_suppressed",
        help="Only print routes whose hit count exceeds max-hits.",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:  # noqa: D401
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = ThrottleConfig(
            max_hits=args.max_hits,
            window_seconds=args.window_seconds,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    tracker = _load_tracker_from_snapshot(args.snapshot)
    summaries = build_summary(tracker)

    suppressed: List[str] = []
    recorded: List[str] = []

    for s in summaries:
        label = f"{s.method} {s.path}  (hits={s.hit_count})"
        if s.hit_count > cfg.max_hits:
            suppressed.append(label)
        else:
            recorded.append(label)

    if args.show_suppressed:
        rows = suppressed
        header = f"Suppressed routes (hits > {cfg.max_hits} in {cfg.window_seconds}s window)"
    else:
        rows = recorded + suppressed
        header = (
            f"Throttle simulation  max_hits={cfg.max_hits}  "
            f"window={cfg.window_seconds}s"
        )

    print(header)
    print("-" * len(header))
    for row in rows:
        prefix = "  [SUPPRESSED] " if row in suppressed else "  [recorded]   "
        print(prefix + row)

    print()
    print(
        f"Total: {len(recorded)} recorded, {len(suppressed)} suppressed "
        f"out of {len(summaries)} routes."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
