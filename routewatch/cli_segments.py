"""CLI entry point for the segment analysis report."""
from __future__ import annotations

import argparse
import sys

from routewatch.snapshot import load_snapshot
from routewatch.segments import build_segment_tree, segment_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch-segments",
        description="Display path-segment coverage breakdown from a snapshot.",
    )
    parser.add_argument("snapshot", help="Path to a routewatch snapshot JSON file.")
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        metavar="N",
        help="How many segment levels to display (default: 1).",
    )
    parser.add_argument(
        "--min-routes",
        type=int,
        default=0,
        metavar="N",
        help="Only show segments with at least N routes.",
    )
    parser.add_argument(
        "--fail-below",
        type=float,
        default=None,
        metavar="PCT",
        help="Exit with code 1 if any top-level segment coverage is below PCT.",
    )
    return parser


def _render_node(node, depth: int, max_depth: int, indent: int = 0) -> None:
    prefix = "  " * indent
    print(
        f"{prefix}/{node.segment:<22} routes={node.route_count:<4} "
        f"hits={node.total_hits:<6} coverage={node.coverage_percent}%"
    )
    if depth < max_depth:
        for child in sorted(node.children.values(), key=lambda n: n.total_hits, reverse=True):
            _render_node(child, depth + 1, max_depth, indent + 1)


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    tracker = load_snapshot(args.snapshot)
    tree = build_segment_tree(tracker)

    if not tree:
        print("No routes registered.")
        sys.exit(0)

    print("Segment Coverage Report")
    print("=" * 40)

    failed = False
    nodes = sorted(tree.values(), key=lambda n: n.total_hits, reverse=True)
    for node in nodes:
        if node.route_count < args.min_routes:
            continue
        _render_node(node, depth=1, max_depth=args.depth)
        if args.fail_below is not None and node.coverage_percent < args.fail_below:
            failed = True

    if failed:
        print(
            f"\n[FAIL] One or more segments below {args.fail_below}% coverage.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
