"""Command-line interface for routewatch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from routewatch.snapshot import load_snapshot
from routewatch.report import text_report, coverage_percent
from routewatch.exporter import export_json, export_csv, save_export
from routewatch.reset import reset_tracker, prune_uncovered, prune_below


def _load_tracker_from_snapshot(path: str):
    return load_snapshot(Path(path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch",
        description="Lightweight HTTP route coverage tracker.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # report
    rp = sub.add_parser("report", help="Print a coverage report from a snapshot.")
    rp.add_argument("snapshot", help="Path to snapshot JSON file.")

    # export
    ep = sub.add_parser("export", help="Export snapshot data to JSON or CSV.")
    ep.add_argument("snapshot", help="Path to snapshot JSON file.")
    ep.add_argument("--format", choices=["json", "csv"], default="json")
    ep.add_argument("--output", "-o", help="Output file path (stdout if omitted).")

    # reset
    rsp = sub.add_parser("reset", help="Reset hit counts in a snapshot and re-save.")
    rsp.add_argument("snapshot", help="Path to snapshot JSON file.")

    # prune
    pp = sub.add_parser("prune", help="Prune routes from a snapshot and re-save.")
    pp.add_argument("snapshot", help="Path to snapshot JSON file.")
    pp.add_argument(
        "--min-hits",
        type=int,
        default=0,
        help="Remove routes with fewer than this many hits (0 = uncovered only).",
    )

    return parser


def main(argv=None) -> int:  # noqa: ANN001
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "report":
        tracker = _load_tracker_from_snapshot(args.snapshot)
        print(text_report(tracker))
        pct = coverage_percent(tracker)
        print(f"\nCoverage: {pct:.1f}%")
        return 0

    if args.command == "export":
        tracker = _load_tracker_from_snapshot(args.snapshot)
        if args.format == "json":
            data = export_json(tracker)
        else:
            data = export_csv(tracker)
        if args.output:
            save_export(data, Path(args.output))
            print(f"Exported to {args.output}")
        else:
            print(data)
        return 0

    if args.command == "reset":
        snap_path = Path(args.snapshot)
        tracker = _load_tracker_from_snapshot(args.snapshot)
        reset_tracker(tracker)
        from routewatch.snapshot import save_snapshot
        save_snapshot(tracker, snap_path)
        print(f"Hit counts reset and saved to {snap_path}")
        return 0

    if args.command == "prune":
        snap_path = Path(args.snapshot)
        tracker = _load_tracker_from_snapshot(args.snapshot)
        if args.min_hits > 0:
            removed = prune_below(tracker, min_hits=args.min_hits)
        else:
            removed = prune_uncovered(tracker)
        from routewatch.snapshot import save_snapshot
        save_snapshot(tracker, snap_path)
        print(f"Pruned {len(removed)} route(s) and saved to {snap_path}")
        return 0

    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
