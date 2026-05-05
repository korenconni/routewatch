"""Export route coverage data to various formats (JSON, CSV)."""

from __future__ import annotations

import csv
import io
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from routewatch.tracker import RouteTracker


def export_json(tracker: "RouteTracker", indent: int = 2) -> str:
    """Serialize tracker route data to a JSON string."""
    routes = []
    for key, hit in tracker._routes.items():
        method, path = key
        routes.append(
            {
                "method": method,
                "path": path,
                "hits": hit.count,
                "covered": hit.count > 0,
            }
        )
    payload = {
        "total_routes": len(routes),
        "covered_routes": sum(1 for r in routes if r["covered"]),
        "routes": routes,
    }
    return json.dumps(payload, indent=indent)


def export_csv(tracker: "RouteTracker") -> str:
    """Serialize tracker route data to a CSV string."""
    output = io.StringIO()
    fieldnames = ["method", "path", "hits", "covered"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for key, hit in tracker._routes.items():
        method, path = key
        writer.writerow(
            {
                "method": method,
                "path": path,
                "hits": hit.count,
                "covered": hit.count > 0,
            }
        )
    return output.getvalue()


def save_export(tracker: "RouteTracker", filepath: str, fmt: str = "json") -> None:
    """Write exported data to *filepath*.

    Args:
        tracker: The RouteTracker instance to export.
        filepath: Destination file path.
        fmt: One of ``'json'`` or ``'csv'``.

    Raises:
        ValueError: If *fmt* is not supported.
    """
    if fmt == "json":
        content = export_json(tracker)
    elif fmt == "csv":
        content = export_csv(tracker)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(content)
