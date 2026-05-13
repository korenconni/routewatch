"""Tests for routewatch.heatmap."""
import pytest

from routewatch.tracker import RouteTracker
from routewatch.heatmap import (
    HeatBand,
    _band_for_hits,
    build_heatmap,
    heatmap_report,
    BANDS,
)


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/cold")          # 0 hits
    t.register("GET", "/cool")          # 1 hit
    t.register("GET", "/warm")          # 10 hits
    t.register("GET", "/hot")           # 50 hits
    t.register("GET", "/blazing")       # 200 hits
    for _ in range(1):
        t.record("GET", "/cool")
    for _ in range(10):
        t.record("GET", "/warm")
    for _ in range(50):
        t.record("GET", "/hot")
    for _ in range(200):
        t.record("GET", "/blazing")
    return t


def test_band_for_hits_zero():
    assert _band_for_hits(0) == "cold"


def test_band_for_hits_one():
    assert _band_for_hits(1) == "cool"


def test_band_for_hits_warm_boundary():
    assert _band_for_hits(10) == "warm"


def test_band_for_hits_hot_boundary():
    assert _band_for_hits(50) == "hot"


def test_band_for_hits_blazing_boundary():
    assert _band_for_hits(200) == "blazing"


def test_band_for_hits_intermediate():
    assert _band_for_hits(25) == "warm"


def test_build_heatmap_returns_all_bands(tracker):
    heatmap = build_heatmap(tracker)
    expected_bands = {name for name, _ in BANDS}
    assert set(heatmap.keys()) == expected_bands


def test_build_heatmap_cold_route(tracker):
    heatmap = build_heatmap(tracker)
    assert "GET /cold" in heatmap["cold"].routes


def test_build_heatmap_blazing_route(tracker):
    heatmap = build_heatmap(tracker)
    assert "GET /blazing" in heatmap["blazing"].routes


def test_build_heatmap_band_counts(tracker):
    heatmap = build_heatmap(tracker)
    assert heatmap["cold"].count == 1
    assert heatmap["cool"].count == 1
    assert heatmap["warm"].count == 1
    assert heatmap["hot"].count == 1
    assert heatmap["blazing"].count == 1


def test_build_heatmap_routes_sorted():
    t = RouteTracker()
    t.register("GET", "/z")
    t.register("GET", "/a")
    heatmap = build_heatmap(t)
    routes = heatmap["cold"].routes
    assert routes == sorted(routes)


def test_heatband_is_dataclass():
    band = HeatBand(name="warm", min_hits=10)
    assert band.name == "warm"
    assert band.min_hits == 10
    assert band.routes == []


def test_heatmap_report_is_string(tracker):
    report = heatmap_report(tracker)
    assert isinstance(report, str)


def test_heatmap_report_contains_header(tracker):
    report = heatmap_report(tracker)
    assert "Route Heatmap" in report


def test_heatmap_report_contains_band_names(tracker):
    report = heatmap_report(tracker)
    for name, _ in BANDS:
        assert name.upper() in report
