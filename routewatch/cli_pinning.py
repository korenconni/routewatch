"""CLI for routewatch pinning: check and manage critical route pins."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from routewatch.pinning import check_pins, load_pins
from routewatch.snapshot import load_snapshot


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch-pins",
        description="Check pinned (critical) route coverage from a snapshot.",
    )
    parser.add_argument("snapshot", help="Path to a routewatch snapshot JSON file.")
    parser.add_argument(
        "--pins",
        default="pins.json",
        metavar="FILE",
        help="Path to pins JSON file (default: pins.json).",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        default=False,
        help="Exit with code 1 if any pinned routes have zero hits.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress output; only use exit code.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        print(f"[routewatch] snapshot not found: {snapshot_path}", file=sys.stderr)
        return 2

    pins_path = Path(args.pins)
    if not pins_path.exists():
        print(f"[routewatch] pins file not found: {pins_path}", file=sys.stderr)
        return 2

    tracker = load_snapshot(snapshot_path)
    load_pins(tracker, pins_path)
    result = check_pins(tracker)

    if not args.quiet:
        total = len(result.pinned)
        print(f"Pinned routes: {total}")
        print(f"  Passing : {len(result.passing)}")
        print(f"  Failing : {len(result.failing)}")
        if result.failing:
            print("\nFailing pinned routes (no hits recorded):")
            for key in result.failing:
                print(f"  ✗ {key}")
        if result.passing:
            print("\nPassing pinned routes:")
            for key in result.passing:
                print(f"  ✓ {key}")

    if args.fail_on_missing and result.has_failures:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
