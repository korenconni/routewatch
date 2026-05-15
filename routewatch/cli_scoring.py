"""CLI helper that prints a scoring report for a saved snapshot.

Intended to be wired into the main routewatch CLI as a sub-command, but
can also be run directly::

    python -m routewatch.cli_scoring snapshot.json
"""

from __future__ import annotations

import argparse
import sys

from routewatch.snapshot import load_snapshot
from routewatch.scoring import scoring_report, average_score, build_scores


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routewatch-score",
        description="Display health scores for routes in a snapshot file.",
    )
    parser.add_argument("snapshot", help="Path to a routewatch JSON snapshot file.")
    parser.add_argument(
        "--min-grade",
        choices=["A", "B", "C", "D", "F"],
        default=None,
        help="Only show routes at or below this grade threshold.",
    )
    parser.add_argument(
        "--fail-below",
        type=float,
        default=None,
        metavar="SCORE",
        help="Exit with code 1 if the average score is below this value.",
    )
    return parser


_GRADE_ORDER = ["A", "B", "C", "D", "F"]


def _grade_lte(grade: str, threshold: str) -> bool:
    """Return True if *grade* is less than or equal to *threshold* (worse or equal)."""
    return _GRADE_ORDER.index(grade) >= _GRADE_ORDER.index(threshold)


def _print_filtered_routes(scores: list, min_grade: str) -> None:
    """Print routes whose grade is at or below *min_grade* (i.e. worse or equal).

    Args:
        scores: List of ``RouteScore`` objects returned by :func:`build_scores`.
        min_grade: Upper-bound grade threshold (inclusive).  Routes graded
            *min_grade* or worse are printed.
    """
    filtered = [rs for rs in scores if _grade_lte(rs.grade, min_grade)]
    if not filtered:
        print(f"No routes with grade {min_grade} or worse.")
    else:
        print(f"Routes graded {min_grade} or worse:")
        for rs in filtered:
            print(f"  [{rs.grade}] {rs.score:>5.1f}  {rs.hits:>4} hits  {rs.method} {rs.path}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        tracker = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"Error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 2

    if args.min_grade:
        scores = build_scores(tracker)
        _print_filtered_routes(scores, args.min_grade)
    else:
        print(scoring_report(tracker))

    if args.fail_below is not None:
        avg = average_score(tracker)
        if avg < args.fail_below:
            print(
                f"\nFAIL: average score {avg:.1f} is below threshold {args.fail_below:.1f}",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
