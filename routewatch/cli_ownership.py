"""CLI for route ownership inspection."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from routewatch.snapshot import load_snapshot
from routewatch.ownership import (
    assign_owner,
    get_owner,
    routes_by_team,
    unowned_routes,
    ownership_report,
    _store,
    _key,
    OwnerInfo,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="routewatch-ownership",
        description="Inspect and report route ownership.",
    )
    p.add_argument("snapshot", help="Path to a routewatch snapshot JSON file")
    sub = p.add_subparsers(dest="command", required=True)

    # report sub-command
    rep = sub.add_parser("report", help="Print full ownership report")
    rep.add_argument(
        "--fail-on-unowned",
        action="store_true",
        help="Exit with code 1 if any routes are unowned",
    )

    # team sub-command
    team_cmd = sub.add_parser("team", help="List routes owned by a team")
    team_cmd.add_argument("team", help="Team name to filter by")

    # unowned sub-command
    sub.add_parser("unowned", help="List routes with no owner assigned")

    return p


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the routewatch-ownership CLI.

    Args:
        argv: Optional list of command-line arguments. Defaults to sys.argv.

    Returns:
        Exit code: 0 on success, 1 on error or when --fail-on-unowned is set
        and unowned routes are found, 2 on invalid input.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        tracker = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"Error: snapshot file not found: '{args.snapshot}'", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Error: failed to load snapshot: {exc}", file=sys.stderr)
        return 2

    if args.command == "report":
        print(ownership_report(tracker))
        if args.fail_on_unowned and unowned_routes(tracker):
            return 1
        return 0

    if args.command == "team":
        routes = routes_by_team(args.team)
        if not routes:
            print(f"No routes found for team '{args.team}'.")
        else:
            print(f"Routes owned by '{args.team}':")
            for r in sorted(routes):
                info = _store.get(r)
                contact = f" <{info.contact}>" if info and info.contact else ""
                print(f"  {r}{contact}")
        return 0

    if args.command == "unowned":
        missing = unowned_routes(tracker)
        if not missing:
            print("All routes have owners assigned.")
        else:
            print(f"{len(missing)} unowned route(s):")
            for r in sorted(missing):
                print(f"  {r}")
        return 0

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
