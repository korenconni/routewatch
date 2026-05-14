"""CLI entry-point: display sampling-adjusted hit estimates from a snapshot."""

from __future__ import annotations

import argparse
import sys

from routewatch.cli import _load_tracker_from_snapshot
from routewatch.sampling import effective_hit_count


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="routewatch-sampling",
        description="Show sampling-adjusted hit estimates from a RouteWatch snapshot.",
    )
    p.add_argument("snapshot", help="Path to a .json snapshot file")
    p.add_argument(
        "--rate",
        type=float,
        default=1.0,
        metavar="RATE",
        help="Sampling rate that was used when recording hits (0.0–1.0, default 1.0)",
    )
    p.add_argument(
        "--min-hits",
        type=int,
        default=0,
        metavar="N",
        help="Only show routes with at least N raw hits (default 0)",
    )
    return p


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not 0.0 < args.rate <= 1.0:
        print("error: --rate must be in the range (0.0, 1.0]", file=sys.stderr)
        return 2

    try:
        tracker = _load_tracker_from_snapshot(args.snapshot)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rows = []
    for key, route in tracker._routes.items():
        raw = route.hit_count
        if raw < args.min_hits:
            continue
        estimated = effective_hit_count(raw, args.rate)
        rows.append((key, raw, estimated))

    rows.sort(key=lambda r: r[2], reverse=True)

    col_w = max((len(r[0]) for r in rows), default=5)
    header = f"{'ROUTE':<{col_w}}  {'RAW HITS':>10}  {'EST. HITS':>12}"
    print(header)
    print("-" * len(header))
    for key, raw, est in rows:
        print(f"{key:<{col_w}}  {raw:>10}  {est:>12.1f}")

    print()
    print(f"Sampling rate : {args.rate}")
    print(f"Routes shown  : {len(rows)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
