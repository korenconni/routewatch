"""CLI for inspecting the route audit log from a snapshot."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from routewatch.snapshot import load_snapshot
from routewatch.audit import get_audit_log, audit_report, record_audit


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch-audit",
        description="Inspect the RouteWatch audit log.",
    )
    parser.add_argument("snapshot", help="Path to a .json snapshot file.")
    sub = parser.add_subparsers(dest="command")

    rp = sub.add_parser("report", help="Print audit summary for all routes.")
    rp.add_argument(
        "--fail-on-empty",
        action="store_true",
        default=False,
        help="Exit with code 1 if any registered route has zero audit entries.",
    )

    lp = sub.add_parser("log", help="Print audit entries for a specific route.")
    lp.add_argument("method", help="HTTP method (e.g. GET).")
    lp.add_argument("path", help="Route path (e.g. /users).")
    lp.add_argument(
        "--last",
        type=int,
        default=10,
        metavar="N",
        help="Show last N entries (default: 10).",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    tracker = load_snapshot(args.snapshot)

    if args.command == "report":
        print(audit_report(tracker))
        if args.fail_on_empty:
            for key in tracker.routes:
                method, _, path = key.partition(" ")
                if not get_audit_log(method, path):
                    print(
                        f"[FAIL] No audit entries for {key}",
                        file=sys.stderr,
                    )
                    return 1
        return 0

    if args.command == "log":
        entries = get_audit_log(args.method, args.path)
        if not entries:
            print(f"No audit entries for {args.method.upper()} {args.path}.")
            return 0
        shown = entries[-args.last :]
        print(f"Audit log for {args.method.upper()} {args.path} "
              f"(showing last {len(shown)} of {len(entries)}):")
        for e in shown:
            import time
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(e.timestamp))
            print(f"  [{ts}] actor={e.actor} meta={e.metadata}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
