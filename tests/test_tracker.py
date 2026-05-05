"""Tests for routewatch.tracker module."""

import pytest
from routewatch.tracker import RouteTracker, RouteHit


@pytest.fixture
def tracker() -> RouteTracker:
    return RouteTracker()


def test_register_route(tracker):
    tracker.register("GET", "/users")
    assert tracker.report()["total_registered"] == 1


def test_register_is_idempotent(tracker):
    tracker.register("GET", "/users")
    tracker.register("GET", "/users")
    assert tracker.report()["total_registered"] == 1


def test_record_hit_increments_count(tracker):
    tracker.register("POST", "/items")
    tracker.record_hit("POST", "/items")
    tracker.record_hit("POST", "/items")
    route = tracker._registered["POST:/items"]
    assert route.hit_count == 2
    assert route.last_hit is not None


def test_record_hit_auto_registers(tracker):
    tracker.record_hit("DELETE", "/things/1")
    assert tracker.report()["total_registered"] == 1
    assert tracker.report()["total_hit"] == 1


def test_coverage_zero_when_no_routes(tracker):
    assert tracker.coverage() == 0.0


def test_coverage_partial(tracker):
    tracker.register("GET", "/a")
    tracker.register("GET", "/b")
    tracker.record_hit("GET", "/a")
    assert tracker.coverage() == pytest.approx(0.5)


def test_coverage_full(tracker):
    tracker.register("GET", "/a")
    tracker.register("POST", "/a")
    tracker.record_hit("GET", "/a")
    tracker.record_hit("POST", "/a")
    assert tracker.coverage() == pytest.approx(1.0)


def test_missed_routes(tracker):
    tracker.register("GET", "/hit-me")
    tracker.register("GET", "/miss-me")
    tracker.record_hit("GET", "/hit-me")
    missed = tracker.missed_routes()
    assert len(missed) == 1
    assert missed[0].path == "/miss-me"


def test_report_structure(tracker):
    tracker.register("GET", "/x")
    report = tracker.report()
    assert "total_registered" in report
    assert "total_hit" in report
    assert "coverage_pct" in report
    assert "missed" in report
    assert report["missed"][0]["method"] == "GET"


def test_reset_clears_hits(tracker):
    tracker.register("GET", "/reset-me")
    tracker.record_hit("GET", "/reset-me")
    assert tracker.coverage() == 1.0
    tracker.reset()
    assert tracker.coverage() == 0.0
    assert tracker.report()["total_registered"] == 1
