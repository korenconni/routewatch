"""CLI for routewatch deprecation inspection."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Optional

from routewatch.snapshot import load_snapshot
from routewatch import deprecations
from routewatch.deprecations import deprecate_route, deprecation_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch-deprecations",
        description="Inspect or report deprecated routes in a snapshot.",
    )
    parser.add_argument("snapshot", help="Path to a routewatch snapshot file")
    sub = parser.add_subparsers(dest="command", required=True)

    report_p = sub.add_parser("report", help="Print deprecation report")
    report_p.add_argument(
        "--fail-on-hits",
        action="store_true",
        help="Exit non-zero if any deprecated route has been hit",
    )

    mark_p = sub.add_parser("mark", help="Mark a route as deprecated (dry-run report)")
    mark_p.add_argument("method", help="HTTP method, e.g. GET")
    mark_p.add_argument("path", help="Route path, e.g. /users")
    mark_p.add_argument("--reason", required=True, help="Deprecation reason")
    mark_p.add_argument("--sunset", help="Sunset date YYYY-MM-DD", default=None)
    mark_p.add_argument("--replacement", help="Replacement route", default=None)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    tracker = load_snapshot(args.snapshot)

    if args.command == "report":
        report = deprecation_report(tracker)
        print(report)
        if args.fail_on_hits:
            deprecated = deprecations.get_deprecated_routes(tracker)
            for k in deprecated:
                method, path = k.split(":", 1)
                route_key = f"{method.upper()}:{path}"
                hits = tracker._routes.get(route_key, 0)
                if hits and hits > 0:
                    print(
                        f"\nFAIL: deprecated route {k} has been hit.",
                        file=sys.stderr,
                    )
                    return 1
        return 0

    if args.command == "mark":
        sunset: Optional[date] = None
        if args.sunset:
            sunset = date.fromisoformat(args.sunset)
        info = deprecate_route(
            tracker,
            args.method,
            args.path,
            reason=args.reason,
            sunset_on=sunset,
            replacement=args.replacement,
        )
        print(f"Marked {args.method.upper()}:{args.path} as deprecated.")
        print(f"  Reason     : {info.reason}")
        print(f"  Since      : {info.deprecated_on}")
        if info.sunset_on:
            print(f"  Sunset     : {info.sunset_on}")
        if info.replacement:
            print(f"  Replacement: {info.replacement}")
        return 0

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
