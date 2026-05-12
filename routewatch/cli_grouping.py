"""CLI sub-command: ``routewatch groups`` — display route groups and coverage."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from routewatch.snapshot import load_snapshot
from routewatch.grouping import group_by_prefix, group_hit_counts, group_coverage


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="routewatch groups",
        description="Show route coverage grouped by URL prefix.",
    )
    p.add_argument("snapshot", help="Path to a .json snapshot file.")
    p.add_argument(
        "--depth",
        type=int,
        default=1,
        metavar="N",
        help="Number of URL segments used to form the group key (default: 1).",
    )
    p.add_argument(
        "--min-coverage",
        type=float,
        default=0.0,
        dest="min_coverage",
        metavar="PCT",
        help="Only show groups below this coverage %% (default: show all).",
    )
    return p


def _render(groups, counts, coverage, min_coverage: float) -> str:
    lines: list[str] = []
    header = f"{'Group':<30} {'Routes':>6} {'Hits':>8} {'Coverage':>10}"
    lines.append(header)
    lines.append("-" * len(header))
    for group in sorted(groups):
        cov = coverage.get(group, 0.0)
        if min_coverage > 0 and cov >= min_coverage:
            continue
        route_count = len(groups[group])
        hit_total = counts.get(group, 0)
        lines.append(f"{group:<30} {route_count:>6} {hit_total:>8} {cov:>9.1f}%")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        tracker = load_snapshot(args.snapshot)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    groups = group_by_prefix(tracker, depth=args.depth)
    counts = group_hit_counts(tracker, groups)
    coverage = group_coverage(tracker, groups)

    print(_render(groups, counts, coverage, args.min_coverage))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
