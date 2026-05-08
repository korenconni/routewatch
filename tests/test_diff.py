"""Tests for routewatch.diff — snapshot diff utility."""

import pytest

from routewatch.tracker import RouteTracker
from routewatch.diff import RouteDiff, diff_trackers, diff_report


@pytest.fixture()
def base_tracker() -> RouteTracker:
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/items")
    t.record("GET", "/users")  # 1 hit
    t.record("GET", "/users")  # 2 hits
    return t


@pytest.fixture()
def updated_tracker() -> RouteTracker:
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/orders")  # new route
    # /items removed
    t.record("GET", "/users")  # 1 hit (was 2)
    t.record("GET", "/users")
    t.record("GET", "/users")  # now 3 hits
    return t


def test_diff_result_is_dataclass(base_tracker, updated_tracker):
    result = diff_trackers(base_tracker, updated_tracker)
    assert isinstance(result, RouteDiff)


def test_added_routes(base_tracker, updated_tracker):
    result = diff_trackers(base_tracker, updated_tracker)
    assert "GET /orders" in result.added


def test_removed_routes(base_tracker, updated_tracker):
    result = diff_trackers(base_tracker, updated_tracker)
    assert "GET /items" in result.removed


def test_hit_changes_detected(base_tracker, updated_tracker):
    result = diff_trackers(base_tracker, updated_tracker)
    assert "GET /users" in result.hit_changes
    old_hits, new_hits = result.hit_changes["GET /users"]
    assert old_hits == 2
    assert new_hits == 3


def test_no_change_for_identical_trackers(base_tracker):
    # Compare tracker with itself — no diff expected
    result = diff_trackers(base_tracker, base_tracker)
    assert not result.has_changes
    assert result.added == []
    assert result.removed == []
    assert result.hit_changes == {}


def test_has_changes_true_when_routes_added(base_tracker, updated_tracker):
    result = diff_trackers(base_tracker, updated_tracker)
    assert result.has_changes is True


def test_diff_report_no_changes():
    t = RouteTracker()
    t.register("GET", "/ping")
    result = diff_trackers(t, t)
    report = diff_report(result)
    assert "No changes detected" in report


def test_diff_report_shows_added(base_tracker, updated_tracker):
    result = diff_trackers(base_tracker, updated_tracker)
    report = diff_report(result)
    assert "+ GET /orders" in report


def test_diff_report_shows_removed(base_tracker, updated_tracker):
    result = diff_trackers(base_tracker, updated_tracker)
    report = diff_report(result)
    assert "- GET /items" in report


def test_diff_report_shows_hit_changes(base_tracker, updated_tracker):
    result = diff_trackers(base_tracker, updated_tracker)
    report = diff_report(result)
    assert "GET /users" in report
    assert "2 -> 3" in report
