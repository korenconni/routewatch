"""Tests for routewatch.reset module."""

import pytest

from routewatch.tracker import RouteTracker
from routewatch.reset import (
    reset_tracker,
    unregister_route,
    prune_uncovered,
    prune_below,
)


@pytest.fixture()
def tracker() -> RouteTracker:
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/items")
    t.record("GET", "/users")  # 1 hit
    t.record("GET", "/users")  # 2 hits
    t.record("POST", "/users")  # 1 hit
    # GET /items has 0 hits
    return t


# ---------------------------------------------------------------------------
# reset_tracker
# ---------------------------------------------------------------------------

def test_reset_tracker_zeroes_hits(tracker: RouteTracker) -> None:
    reset_tracker(tracker)
    for route in tracker._routes.values():
        assert route.hits == 0


def test_reset_tracker_keeps_routes(tracker: RouteTracker) -> None:
    original_count = len(tracker._routes)
    reset_tracker(tracker)
    assert len(tracker._routes) == original_count


# ---------------------------------------------------------------------------
# unregister_route
# ---------------------------------------------------------------------------

def test_unregister_existing_route(tracker: RouteTracker) -> None:
    removed = unregister_route(tracker, "GET", "/users")
    assert removed is True
    assert len(tracker._routes) == 2


def test_unregister_nonexistent_route(tracker: RouteTracker) -> None:
    removed = unregister_route(tracker, "DELETE", "/users")
    assert removed is False
    assert len(tracker._routes) == 3


def test_unregister_is_case_insensitive(tracker: RouteTracker) -> None:
    removed = unregister_route(tracker, "get", "/users")
    assert removed is True


# ---------------------------------------------------------------------------
# prune_uncovered
# ---------------------------------------------------------------------------

def test_prune_uncovered_removes_zero_hit_routes(tracker: RouteTracker) -> None:
    pruned = prune_uncovered(tracker)
    assert "GET:/items" in pruned or any("/items" in k for k in pruned)
    assert len(tracker._routes) == 2


def test_prune_uncovered_returns_removed_keys(tracker: RouteTracker) -> None:
    pruned = prune_uncovered(tracker)
    assert len(pruned) == 1


def test_prune_uncovered_empty_when_all_hit() -> None:
    t = RouteTracker()
    t.record("GET", "/ping")
    pruned = prune_uncovered(t)
    assert pruned == []


# ---------------------------------------------------------------------------
# prune_below
# ---------------------------------------------------------------------------

def test_prune_below_removes_routes_under_threshold(tracker: RouteTracker) -> None:
    pruned = prune_below(tracker, min_hits=2)
    # POST /users (1 hit) and GET /items (0 hits) should be pruned
    assert len(tracker._routes) == 1
    assert len(pruned) == 2


def test_prune_below_keeps_routes_at_threshold(tracker: RouteTracker) -> None:
    pruned = prune_below(tracker, min_hits=1)
    # Only GET /items (0 hits) should be pruned
    assert len(tracker._routes) == 2
    assert len(pruned) == 1


def test_prune_below_raises_on_invalid_min_hits(tracker: RouteTracker) -> None:
    with pytest.raises(ValueError):
        prune_below(tracker, min_hits=0)
