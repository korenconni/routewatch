"""CLI entry point for route pattern matching.

Usage examples::

    routewatch-patterns snapshot.json --glob "/api/v1/*"
    routewatch-patterns snapshot.json --regex "^/api/v[0-9]+/" --method GET
    routewatch-patterns snapshot.json --glob "/admin/*" --method DELETE --fail-on-empty
"""
from __future__ import annotations

import argparse
import sys
from typing import List

from routewatch.snapshot import load_snapshot
from routewatch.routing_patterns import match_glob, match_regex, PatternMatch


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="routewatch-patterns",
        description="Match routes in a snapshot using glob or regex patterns.",
    )
    p.add_argument("snapshot", help="Path to a routewatch snapshot JSON file.")

    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--glob", metavar="PATTERN", help="Glob pattern to match route paths.")
    group.add_argument("--regex", metavar="PATTERN", help="Regex pattern to match route paths.")

    p.add_argument(
        "--method",
        metavar="METHOD",
        default=None,
        help="Filter by HTTP method (e.g. GET, POST).",
    )
    p.add_argument(
        "--fail-on-empty",
        action="store_true",
        default=False,
        help="Exit with code 1 if no routes match the pattern.",
    )
    p.add_argument(
        "--show-hits",
        action="store_true",
        default=False,
        help="Include hit counts in the output.",
    )
    return p


def _render(matches: List[PatternMatch], show_hits: bool) -> str:
    if not matches:
        return "(no matching routes)"
    lines = []
    for m in sorted(matches, key=lambda x: (x.method, x.path)):
        line = m.key
        if show_hits:
            line += f"  [{m.hit_count} hits]"
        lines.append(line)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    tracker = load_snapshot(args.snapshot)

    if args.glob:
        matches = match_glob(tracker, args.glob, method=args.method)
        pattern_desc = f"glob '{args.glob}'"
    else:
        matches = match_regex(tracker, args.regex, method=args.method)
        pattern_desc = f"regex '{args.regex}'"

    method_desc = f" [method={args.method.upper()}]" if args.method else ""
    print(f"Pattern: {pattern_desc}{method_desc}")
    print(f"Matched: {len(matches)} route(s)")
    print()
    print(_render(matches, show_hits=args.show_hits))

    if args.fail_on_empty and not matches:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
