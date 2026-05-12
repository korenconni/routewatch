"""Tests for routewatch.grouping."""

import pytest

from routewatch.tracker import RouteTracker
from routewatch.grouping import (
    group_by_prefix,
    group_by_key,
    group_hit_counts,
    group_coverage,
)


@pytest.fixture()
def tracker() -> RouteTracker:
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/users/profile")
    t.register("GET", "/orders")
    t.register("POST", "/orders")
    t.register("GET", "/health")
    return t


def test_group_by_prefix_single_depth(tracker):
    groups = group_by_prefix(tracker, depth=1)
    assert set(groups.keys()) == {"/users", "/orders", "/health"}


def test_group_by_prefix_routes_assigned_correctly(tracker):
    groups = group_by_prefix(tracker, depth=1)
    assert "GET /users" in groups["/users"]
    assert "POST /users" in groups["/users"]
    assert "GET /users/profile" in groups["/users"]


def test_group_by_prefix_depth_two(tracker):
    groups = group_by_prefix(tracker, depth=2)
    # /users/profile lands in /users/profile; /users stays in /users
    assert "/users/profile" in groups
    assert "GET /users/profile" in groups["/users/profile"]


def test_group_by_prefix_root_route():
    t = RouteTracker()
    t.register("GET", "/")
    groups = group_by_prefix(t, depth=1)
    assert "/" in groups
    assert "GET /" in groups["/"]


def test_group_by_key_custom_fn(tracker):
    groups = group_by_key(tracker, key_fn=lambda method, path: method)
    assert set(groups.keys()) == {"GET", "POST"}
    assert "GET /users" in groups["GET"]
    assert "POST /orders" in groups["POST"]


def test_group_by_key_returns_sorted_routes(tracker):
    groups = group_by_key(tracker, key_fn=lambda m, p: m)
    for routes in groups.values():
        assert routes == sorted(routes)


def test_group_hit_counts_all_zero(tracker):
    groups = group_by_prefix(tracker, depth=1)
    counts = group_hit_counts(tracker, groups)
    assert all(v == 0 for v in counts.values())


def test_group_hit_counts_after_hits(tracker):
    from routewatch.tracker import record
    record(tracker, "GET", "/users")
    record(tracker, "GET", "/users")
    record(tracker, "POST", "/users")
    groups = group_by_prefix(tracker, depth=1)
    counts = group_hit_counts(tracker, groups)
    assert counts["/users"] == 3
    assert counts["/orders"] == 0


def test_group_coverage_zero_when_no_hits(tracker):
    groups = group_by_prefix(tracker, depth=1)
    cov = group_coverage(tracker, groups)
    assert all(v == 0.0 for v in cov.values())


def test_group_coverage_partial(tracker):
    from routewatch.tracker import record
    record(tracker, "GET", "/users")
    groups = group_by_prefix(tracker, depth=1)
    cov = group_coverage(tracker, groups)
    # /users group has 3 routes, 1 covered → 33.33 %
    assert cov["/users"] == pytest.approx(33.33, rel=1e-2)


def test_group_coverage_full(tracker):
    from routewatch.tracker import record
    record(tracker, "GET", "/health")
    groups = group_by_prefix(tracker, depth=1)
    cov = group_coverage(tracker, groups)
    assert cov["/health"] == 100.0
