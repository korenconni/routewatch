"""CLI for managing route notes."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from routewatch.snapshot import load_snapshot
from routewatch import notes as notes_mod
from routewatch.notes import add_note, get_notes, remove_notes, notes_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch-notes",
        description="Manage freeform notes attached to routes.",
    )
    parser.add_argument("snapshot", help="Path to a routewatch snapshot JSON file.")
    sub = parser.add_subparsers(dest="command", required=True)

    # report
    sub.add_parser("report", help="Print all route notes.")

    # add
    p_add = sub.add_parser("add", help="Add a note to a route.")
    p_add.add_argument("method", help="HTTP method (e.g. GET).")
    p_add.add_argument("path", help="Route path (e.g. /users).")
    p_add.add_argument("text", help="Note text.")
    p_add.add_argument("--author", default="unknown", help="Author name.")

    # show
    p_show = sub.add_parser("show", help="Show notes for a specific route.")
    p_show.add_argument("method", help="HTTP method.")
    p_show.add_argument("path", help="Route path.")

    # remove
    p_rm = sub.add_parser("remove", help="Remove all notes for a route.")
    p_rm.add_argument("method", help="HTTP method.")
    p_rm.add_argument("path", help="Route path.")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        tracker = load_snapshot(args.snapshot)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.command == "report":
        print(notes_report(tracker))
        return 0

    if args.command == "add":
        note = add_note(tracker, args.method, args.path, args.text, author=args.author)
        print(f"Note added to {note.key} by {note.author}.")
        return 0

    if args.command == "show":
        route_notes = get_notes(tracker, args.method, args.path)
        key = f"{args.method.upper()} {args.path}"
        if not route_notes:
            print(f"No notes for {key}.")
            return 0
        print(f"{key}  ({len(route_notes)} note(s))")
        for i, n in enumerate(route_notes, 1):
            print(f"  [{i}] {n.created_at}  @{n.author}")
            print(f"      {n.text}")
        return 0

    if args.command == "remove":
        count = remove_notes(tracker, args.method, args.path)
        key = f"{args.method.upper()} {args.path}"
        print(f"Removed {count} note(s) from {key}.")
        return 0

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
