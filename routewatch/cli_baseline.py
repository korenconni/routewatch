"""CLI entry-point for baseline comparison operations.

Usage examples::

    # Save current snapshot as baseline
    python -m routewatch.cli_baseline save snapshot.json baseline.json

    # Compare snapshot against saved baseline
    python -m routewatch.cli_baseline compare snapshot.json baseline.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from routewatch.baseline import (
    baseline_report,
    compare_to_baseline,
    load_baseline,
    save_baseline,
)
from routewatch.snapshot import load_snapshot, _tracker_from_dict


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch-baseline",
        description="Save or compare route coverage baselines.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # save sub-command
    save_p = sub.add_parser("save", help="Save current snapshot as baseline.")
    save_p.add_argument("snapshot", help="Path to routewatch snapshot JSON.")
    save_p.add_argument("baseline", help="Output path for baseline JSON.")

    # compare sub-command
    cmp_p = sub.add_parser("compare", help="Compare snapshot against baseline.")
    cmp_p.add_argument("snapshot", help="Path to routewatch snapshot JSON.")
    cmp_p.add_argument("baseline", help="Path to saved baseline JSON.")
    cmp_p.add_argument(
        "--fail-on-regression",
        action="store_true",
        default=False,
        help="Exit with code 1 if any regressions are found.",
    )

    return parser


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "save":
        snap = load_snapshot(args.snapshot)
        tracker = _tracker_from_dict(snap)
        save_baseline(tracker, args.baseline)
        print(f"Baseline saved to {args.baseline}")

    elif args.command == "compare":
        snap = load_snapshot(args.snapshot)
        tracker = _tracker_from_dict(snap)
        baseline = load_baseline(args.baseline)
        result = compare_to_baseline(tracker, baseline)
        print(baseline_report(result))
        if args.fail_on_regression and result.has_regressions:
            sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
