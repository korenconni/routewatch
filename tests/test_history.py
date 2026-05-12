"""Tests for routewatch.history."""

import time

import pytest

from routewatch.history import HitEvent, RouteHistory


@pytest.fixture()
def history() -> RouteHistory:
    return RouteHistory(max_events=10)


def test_hit_event_key_is_uppercase(history):
    event = history.record("get", "/users")
    assert event.key == "GET /users"


def test_record_returns_hit_event(history):
    event = history.record("POST", "/items")
    assert isinstance(event, HitEvent)
    assert event.method == "POST"
    assert event.path == "/items"


def test_record_stores_event(history):
    history.record("GET", "/ping")
    assert len(history) == 1


def test_record_respects_max_events():
    h = RouteHistory(max_events=3)
    for i in range(5):
        h.record("GET", f"/route/{i}")
    assert len(h) == 3


def test_record_evicts_oldest_first():
    h = RouteHistory(max_events=2)
    h.record("GET", "/first")
    h.record("GET", "/second")
    h.record("GET", "/third")
    paths = [e.path for e in h.events()]
    assert "/first" not in paths
    assert "/third" in paths


def test_events_returns_all_by_default(history):
    history.record("GET", "/a")
    history.record("GET", "/b")
    assert len(history.events()) == 2


def test_events_since_filters_old(history):
    past = time.time() - 100
    future_boundary = time.time() - 1
    history.record("GET", "/old", timestamp=past)
    history.record("GET", "/new")
    recent = history.events(since=future_boundary)
    assert len(recent) == 1
    assert recent[0].path == "/new"


def test_hits_per_route_counts_correctly(history):
    history.record("GET", "/users")
    history.record("GET", "/users")
    history.record("POST", "/users")
    counts = history.hits_per_route()
    assert counts["GET /users"] == 2
    assert counts["POST /users"] == 1


def test_hits_per_route_empty_returns_empty(history):
    assert history.hits_per_route() == {}


def test_most_active_returns_top_n(history):
    for _ in range(3):
        history.record("GET", "/popular")
    history.record("GET", "/rare")
    top = history.most_active(n=1)
    assert top[0][0] == "GET /popular"
    assert top[0][1] == 3


def test_most_active_respects_n_limit(history):
    for path in ["/a", "/b", "/c"]:
        history.record("GET", path)
    assert len(history.most_active(n=2)) == 2


def test_clear_removes_all_events(history):
    history.record("GET", "/x")
    history.clear()
    assert len(history) == 0
    assert history.events() == []
