"""Minimal CLI for routewatch — print a coverage report from a JSON snapshot."""

from __future__ import annotations

import argparse
import json
import sys

from routewatch.report import coverage_percent, text_report, json_report
from routewatch.tracker import RouteTracker


def _load_tracker_from_snapshot(path: str) -> RouteTracker:
    """Load a RouteTracker from a JSON snapshot file.

    Expected format::

        [
          {"path": "/users", "method": "GET", "hits": 3},
          ...
        ]
    """
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    tracker = RouteTracker()
    for entry in data:
        p, m, hits = entry["path"], entry["method"], int(entry.get("hits", 0))
        tracker.register(p, m)
        for _ in range(hits):
            tracker.record(p, m)
    return tracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch",
        description="Lightweight HTTP route coverage tracker.",
    )
    sub = parser.add_subparsers(dest="command")

    report_p = sub.add_parser("report", help="Print a coverage report.")
    report_p.add_argument("snapshot", help="Path to a JSON snapshot file.")
    report_p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    report_p.add_argument(
        "--fail-under",
        type=float,
        default=0.0,
        metavar="PCT",
        help="Exit with code 1 if coverage is below this percentage.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "report":
        try:
            tracker = _load_tracker_from_snapshot(args.snapshot)
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
            print(f"Error loading snapshot: {exc}", file=sys.stderr)
            return 2

        if args.format == "json":
            print(json_report(tracker))
        else:
            print(text_report(tracker))

        pct = coverage_percent(tracker)
        if pct < args.fail_under:
            print(
                f"\nFAILED: coverage {pct}% is below --fail-under {args.fail_under}%",
                file=sys.stderr,
            )
            return 1
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
