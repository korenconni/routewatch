"""CLI for inspecting per-route hit quotas from a snapshot."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from routewatch.snapshot import load_snapshot
from routewatch.quotas import set_quota, check_quotas, QuotaReport


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="routewatch-quotas",
        description="Check per-route hit quotas against a snapshot.",
    )
    p.add_argument("snapshot", help="Path to a routewatch snapshot JSON file.")
    p.add_argument(
        "--quota",
        metavar="METHOD:PATH:MIN[:MAX]",
        action="append",
        dest="quotas",
        default=[],
        help="Quota definition, e.g. GET:/users:5:100. Repeatable.",
    )
    p.add_argument(
        "--fail-on-violation",
        action="store_true",
        default=False,
        help="Exit with code 1 if any quota is violated.",
    )
    return p


def _parse_quota(spec: str):
    """Parse 'METHOD:PATH:MIN[:MAX]' into (method, path, min, max|None)."""
    parts = spec.split(":")
    if len(parts) < 3:
        raise argparse.ArgumentTypeError(f"Invalid quota spec: {spec!r}")
    method = parts[0]
    path = parts[1]
    min_hits = int(parts[2])
    max_hits = int(parts[3]) if len(parts) >= 4 else None
    return method, path, min_hits, max_hits


def _print_report(report: QuotaReport) -> None:
    if not report.results:
        print("No quotas defined.")
        return
    for r in report.results:
        status = "OK" if r.within_quota else "VIOLATION"
        max_str = str(r.max_hits) if r.max_hits is not None else "∞"
        print(
            f"[{status}] {r.key}  hits={r.hits}  "
            f"quota=[{r.min_hits}, {max_str}]  {r.reason}"
        )


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        tracker = load_snapshot(args.snapshot)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 2

    for spec in args.quotas:
        try:
            method, path, min_hits, max_hits = _parse_quota(spec)
        except (argparse.ArgumentTypeError, ValueError) as exc:
            print(f"Bad quota spec {spec!r}: {exc}", file=sys.stderr)
            return 2
        set_quota(tracker, method, path, min_hits=min_hits, max_hits=max_hits)

    report = check_quotas(tracker)
    _print_report(report)

    if args.fail_on_violation and report.has_violations:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
