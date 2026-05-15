"""CLI for inspecting and applying retention policies to a snapshot."""

from __future__ import annotations

import argparse
import sys
import time

from routewatch.snapshot import load_snapshot
from routewatch.retention import RetentionPolicy, apply_retention, record_hit_time


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch-retention",
        description="Apply a hit-age retention policy to a RouteWatch snapshot.",
    )
    parser.add_argument("snapshot", help="Path to the .json snapshot file")
    parser.add_argument(
        "--max-age",
        type=float,
        default=86400.0,
        metavar="SECONDS",
        help="Expire hits older than this many seconds (default: 86400 = 24 h)",
    )
    parser.add_argument(
        "--min-hits",
        type=int,
        default=0,
        metavar="N",
        help="Always keep routes with at most N hits regardless of age (default: 0)",
    )
    parser.add_argument(
        "--fail-on-expired",
        action="store_true",
        help="Exit with code 1 if any routes were expired",
    )
    return parser


def main(argv: list[str] | None = None) -> int:  # pragma: no cover — thin CLI glue
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        tracker = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"error: snapshot not found: {args.snapshot}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load snapshot: {exc}", file=sys.stderr)
        return 2

    try:
        policy = RetentionPolicy(
            max_age_seconds=args.max_age,
            min_hits_to_keep=args.min_hits,
        )
    except ValueError as exc:
        print(f"error: invalid policy: {exc}", file=sys.stderr)
        return 2

    # Seed last-hit timestamps from snapshot hit counts as a best-effort proxy.
    # Real deployments should call record_hit_time() from middleware instead.
    now = time.time()
    for route in tracker.routes.values():
        if route.hits > 0:
            record_hit_time(route.method, route.path, ts=now)

    result = apply_retention(tracker, policy)

    print(f"Routes checked : {result.routes_checked}")
    print(f"Routes expired : {result.routes_zeroed}")
    print(f"Routes kept    : {result.routes_kept}")

    if result.routes_zeroed:
        print("\nExpired routes:")
        for key, removed in sorted(result.details.items()):
            print(f"  {key}  ({removed} hit(s) removed)")

    if args.fail_on_expired and result.any_expired:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
