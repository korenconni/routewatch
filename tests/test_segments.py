"""Tests for routewatch.segments."""
import pytest

from routewatch.tracker import RouteTracker
from routewatch.segments import (
    SegmentNode,
    _split_path,
    build_segment_tree,
    flat_segment_stats,
    segment_report,
)


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/users/profile")
    t.register("GET", "/items")
    t.register("DELETE", "/items/123")
    t.register("GET", "/")
    return t


def test_split_path_basic():
    assert _split_path("/users/profile") == ["users", "profile"]


def test_split_path_root():
    assert _split_path("/") == []


def test_split_path_no_leading_slash():
    assert _split_path("items/detail") == ["items", "detail"]


def test_build_segment_tree_top_level_keys(tracker):
    tree = build_segment_tree(tracker)
    assert "users" in tree
    assert "items" in tree
    assert "__root__" in tree


def test_build_segment_tree_route_count(tracker):
    tree = build_segment_tree(tracker)
    # GET /users, POST /users, GET /users/profile => 3 routes under 'users'
    assert tree["users"].route_count == 3


def test_build_segment_tree_child_route_count(tracker):
    tree = build_segment_tree(tracker)
    assert "profile" in tree["users"].children
    assert tree["users"].children["profile"].route_count == 1


def test_build_segment_tree_no_hits_initially(tracker):
    tree = build_segment_tree(tracker)
    assert tree["users"].total_hits == 0
    assert tree["users"].covered_count == 0


def test_build_segment_tree_hits_after_record(tracker):
    from routewatch.tracker import record
    record(tracker, "GET", "/users")
    record(tracker, "GET", "/users")
    tree = build_segment_tree(tracker)
    assert tree["users"].total_hits == 2
    assert tree["users"].covered_count >= 1


def test_coverage_percent_zero_routes():
    node = SegmentNode(segment="x")
    assert node.coverage_percent == 0.0


def test_coverage_percent_partial():
    node = SegmentNode(segment="x", route_count=4, covered_count=2)
    assert node.coverage_percent == 50.0


def test_flat_segment_stats_sorted_by_hits(tracker):
    from routewatch.tracker import record
    record(tracker, "GET", "/items")
    record(tracker, "GET", "/items")
    record(tracker, "GET", "/items")
    record(tracker, "GET", "/users")
    stats = flat_segment_stats(tracker)
    assert stats[0].segment == "items"


def test_flat_segment_stats_empty_tracker():
    t = RouteTracker()
    assert flat_segment_stats(t) == []


def test_segment_report_contains_segment_name(tracker):
    report = segment_report(tracker)
    assert "users" in report
    assert "items" in report


def test_segment_report_empty_tracker():
    t = RouteTracker()
    report = segment_report(t)
    assert "No routes" in report


def test_segment_report_contains_coverage(tracker):
    report = segment_report(tracker)
    assert "coverage=" in report
