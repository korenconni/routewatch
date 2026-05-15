"""CLI for inspecting SLA violations from a snapshot."""
from __future__ import annotations

import argparse
import sys

from routewatch.snapshot import load_snapshot
from routewatch.sla import set_sla, check_sla, sla_text_report, _store


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch-sla",
        description="Check SLA hit targets against a RouteWatch snapshot.",
    )
    parser.add_argument("snapshot", help="Path to a .json snapshot file")
    parser.add_argument(
        "--sla",
        metavar="METHOD:PATH:MIN_HITS",
        action="append",
        default=[],
        help="SLA target in the form METHOD:PATH:MIN_HITS (repeatable)",
    )
    parser.add_argument(
        "--fail-on-violation",
        action="store_true",
        default=False,
        help="Exit with code 1 if any SLA target is not met",
    )
    return parser


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        tracker = load_snapshot(args.snapshot)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 2

    _store.clear()

    for raw in args.sla:
        parts = raw.split(":")
        if len(parts) != 3:
            print(f"Invalid SLA spec '{raw}' — expected METHOD:PATH:MIN_HITS", file=sys.stderr)
            return 2
        method, path, min_hits_str = parts
        try:
            min_hits = int(min_hits_str)
        except ValueError:
            print(f"MIN_HITS must be an integer, got '{min_hits_str}'", file=sys.stderr)
            return 2
        set_sla(tracker, method, path, min_hits)

    report = check_sla(tracker)
    print(sla_text_report(report))

    if args.fail_on_violation and report.has_violations:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
