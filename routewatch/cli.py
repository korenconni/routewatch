"""Command-line interface for routewatch."""

from __future__ import annotations

import argparse
import sys

from routewatch.exporter import save_export
from routewatch.report import coverage_percent, missing_routes, text_report
from routewatch.snapshot import load_snapshot


def _load_tracker_from_snapshot(path: str):
    """Load a RouteTracker from a snapshot file."""
    try:
        return load_snapshot(path)
    except FileNotFoundError:
        print(f"Error: snapshot file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch",
        description="Lightweight HTTP route coverage tracker.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- report sub-command ---
    report_p = sub.add_parser("report", help="Print a coverage report from a snapshot.")
    report_p.add_argument("snapshot", help="Path to the snapshot JSON file.")
    report_p.add_argument(
        "--missing",
        action="store_true",
        help="List only uncovered routes.",
    )

    # --- export sub-command ---
    export_p = sub.add_parser("export", help="Export route data to JSON or CSV.")
    export_p.add_argument("snapshot", help="Path to the snapshot JSON file.")
    export_p.add_argument("output", help="Destination file path.")
    export_p.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        dest="fmt",
        help="Output format (default: json).",
    )

    # --- coverage sub-command ---
    cov_p = sub.add_parser("coverage", help="Print coverage percentage and exit non-zero if below threshold.")
    cov_p.add_argument("snapshot", help="Path to the snapshot JSON file.")
    cov_p.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        metavar="PCT",
        help="Fail (exit 1) if coverage is below this percentage (0-100).",
    )

    return parser


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "report":
        tracker = _load_tracker_from_snapshot(args.snapshot)
        if args.missing:
            routes = missing_routes(tracker)
            if not routes:
                print("All routes covered.")
            else:
                for method, path in routes:
                    print(f"  {method:7s} {path}")
        else:
            print(text_report(tracker))

    elif args.command == "export":
        tracker = _load_tracker_from_snapshot(args.snapshot)
        save_export(tracker, args.output, fmt=args.fmt)
        print(f"Exported to {args.output} ({args.fmt}).")

    elif args.command == "coverage":
        tracker = _load_tracker_from_snapshot(args.snapshot)
        pct = coverage_percent(tracker)
        print(f"Coverage: {pct:.1f}%")
        if pct < args.threshold:
            print(
                f"FAIL: coverage {pct:.1f}% is below threshold {args.threshold:.1f}%",
                file=sys.stderr,
            )
            sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
