"""Command-line interface for routewatch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from routewatch.alerts import check_coverage_alert
from routewatch.exporter import save_export
from routewatch.report import text_report
from routewatch.snapshot import load_snapshot
from routewatch.tracker import RouteTracker


def _load_tracker_from_snapshot(path: str) -> RouteTracker:
    return load_snapshot(Path(path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch",
        description="Lightweight HTTP route coverage tracker.",
    )
    sub = parser.add_subparsers(dest="command")

    # --- report ---
    rep = sub.add_parser("report", help="Print a coverage report from a snapshot.")
    rep.add_argument("snapshot", help="Path to a .json snapshot file.")

    # --- export ---
    exp = sub.add_parser("export", help="Export snapshot data to JSON or CSV.")
    exp.add_argument("snapshot", help="Path to a .json snapshot file.")
    exp.add_argument("-f", "--format", choices=["json", "csv"], default="json")
    exp.add_argument("-o", "--output", required=True, help="Output file path.")

    # --- alert ---
    ale = sub.add_parser("alert", help="Exit with code 1 when coverage is below threshold.")
    ale.add_argument("snapshot", help="Path to a .json snapshot file.")
    ale.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=80.0,
        help="Minimum required coverage percent (default: 80).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:  # noqa: UP007
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    tracker = _load_tracker_from_snapshot(args.snapshot)

    if args.command == "report":
        print(text_report(tracker))
        return 0

    if args.command == "export":
        save_export(tracker, Path(args.output), fmt=args.format)
        print(f"Exported to {args.output}")
        return 0

    if args.command == "alert":
        result = check_coverage_alert(tracker, threshold=args.threshold)
        print(result.message)
        return 1 if result.triggered else 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
