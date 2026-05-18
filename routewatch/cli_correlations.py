"""CLI for inspecting route correlation data from a snapshot."""
from __future__ import annotations

import argparse
import sys

from routewatch.correlations import CorrelationPair, record_correlation, top_correlations
from routewatch.snapshot import load_snapshot


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="routewatch-correlations",
        description="Show route co-occurrence correlations derived from a snapshot.",
    )
    p.add_argument("snapshot", help="Path to a routewatch snapshot JSON file")
    p.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Number of top correlated pairs to display (default: 10)",
    )
    p.add_argument(
        "--route",
        metavar="'METHOD /path'",
        default=None,
        help="Show correlations for a specific route, e.g. 'GET /users'",
    )
    p.add_argument(
        "--min-count",
        type=int,
        default=1,
        metavar="N",
        help="Only show pairs with co-occurrence count >= N",
    )
    return p


def _render(pairs: list[CorrelationPair], min_count: int) -> None:
    filtered = [p for p in pairs if p.count >= min_count]
    if not filtered:
        print("No correlations found.")
        return
    width = max(len(p.route_a) + len(p.route_b) for p in filtered) + 10
    print(f"{'Route A':<35} {'Route B':<35} {'Count':>6}")
    print("-" * 80)
    for p in filtered:
        print(f"{p.route_a:<35} {p.route_b:<35} {p.count:>6}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        tracker = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load snapshot: {exc}", file=sys.stderr)
        return 1

    # Synthesise co-occurrence data from hit counts as a best-effort proxy.
    for route in tracker.routes.values():
        for _ in range(route.hits):
            record_correlation("__snapshot__", route.method, route.path)

    if args.route:
        parts = args.route.strip().split(" ", 1)
        if len(parts) != 2:
            print("error: --route must be 'METHOD /path'", file=sys.stderr)
            return 1
        method, path = parts
        pairs = correlations_for_cli(method, path, n=args.top)
    else:
        pairs = top_correlations(n=args.top)

    _render(pairs, min_count=args.min_count)
    return 0


def correlations_for_cli(method: str, path: str, n: int = 10) -> list[CorrelationPair]:
    from routewatch.correlations import correlations_for
    return correlations_for(method, path, n=n)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
