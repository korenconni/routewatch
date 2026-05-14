"""CLI for inspecting route labels stored in a snapshot."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from routewatch.snapshot import load_snapshot
from routewatch.labels import get_labels, routes_by_label


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="routewatch-labels",
        description="Inspect route labels from a RouteWatch snapshot.",
    )
    p.add_argument("snapshot", help="Path to the .json snapshot file.")
    sub = p.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Show all labels for a specific route.")
    show.add_argument("method", help="HTTP method (e.g. GET).")
    show.add_argument("path", help="Route path (e.g. /users).")

    find = sub.add_parser("find", help="Find routes with a given label key=value.")
    find.add_argument("key", help="Label key to search.")
    find.add_argument("value", help="Label value to match.")

    return p


def main(argv: Optional[list[str]] = None) -> int:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        tracker = load_snapshot(args.snapshot)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"ERROR: could not load snapshot — {exc}", file=sys.stderr)
        return 1

    if args.command == "show":
        labels = get_labels(tracker, args.method, args.path)
        route_key = f"{args.method.upper()} {args.path}"
        if not labels:
            print(f"No labels found for {route_key}.")
        else:
            print(f"Labels for {route_key}:")
            for k, v in sorted(labels.items()):
                print(f"  {k}: {v}")

    elif args.command == "find":
        matches = routes_by_label(tracker, args.key, args.value)
        if not matches:
            print(f"No routes with label {args.key!r} = {args.value!r}.")
        else:
            print(f"Routes where {args.key!r} = {args.value!r}:")
            for route in sorted(matches):
                print(f"  {route}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
