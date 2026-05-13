"""Route heatmap: bucket routes by hit-frequency into heat bands."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from routewatch.tracker import RouteTracker

# Heat bands from coldest to hottest
BANDS: List[Tuple[str, int]] = [
    ("cold", 0),
    ("cool", 1),
    ("warm", 10),
    ("hot", 50),
    ("blazing", 200),
]


@dataclass
class HeatBand:
    name: str
    min_hits: int
    routes: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.routes)


def _band_for_hits(hits: int) -> str:
    """Return the heat band name for a given hit count."""
    result = "cold"
    for name, threshold in BANDS:
        if hits >= threshold:
            result = name
    return result


def build_heatmap(tracker: RouteTracker) -> Dict[str, HeatBand]:
    """Build a mapping of band-name -> HeatBand from tracker state."""
    bands: Dict[str, HeatBand] = {
        name: HeatBand(name=name, min_hits=threshold)
        for name, threshold in BANDS
    }
    for key, route in tracker._routes.items():
        band_name = _band_for_hits(route.hits)
        bands[band_name].routes.append(key)
    # Sort routes within each band for deterministic output
    for band in bands.values():
        band.routes.sort()
    return bands


def heatmap_report(tracker: RouteTracker) -> str:
    """Return a human-readable heatmap report string."""
    bands = build_heatmap(tracker)
    lines: List[str] = ["Route Heatmap", "=" * 40]
    for name, _ in reversed(BANDS):
        band = bands[name]
        lines.append(f"[{name.upper():^8}]  (>= {band.min_hits} hits)  {band.count} route(s)")
        for route in band.routes:
            lines.append(f"  {route}")
    return "\n".join(lines)
