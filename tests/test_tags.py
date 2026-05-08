"""Tests for routewatch.tags — tag-based grouping and filtering."""

import pytest

from routewatch.tracker import RouteTracker
from routewatch.tags import (
    tag_route,
    get_tags,
    routes_by_tag,
    filter_by_tag,
    remove_tag,
)


@pytest.fixture()
def tracker() -> RouteTracker:
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/health")
    return t


def test_tag_route_adds_tags(tracker):
    tag_route(tracker, "GET", "/users", "public", "v1")
    assert get_tags(tracker, "GET", "/users") == {"public", "v1"}


def test_tag_route_auto_registers_unknown_route(tracker):
    tag_route(tracker, "DELETE", "/items", "admin")
    key = tracker._key("DELETE", "/items")
    assert key in tracker._routes
    assert "admin" in get_tags(tracker, "DELETE", "/items")


def test_tag_route_is_additive(tracker):
    tag_route(tracker, "GET", "/users", "public")
    tag_route(tracker, "GET", "/users", "v1")
    assert get_tags(tracker, "GET", "/users") == {"public", "v1"}


def test_get_tags_returns_empty_set_for_untagged(tracker):
    assert get_tags(tracker, "GET", "/health") == set()


def test_get_tags_returns_empty_set_for_missing_route(tracker):
    assert get_tags(tracker, "PATCH", "/nonexistent") == set()


def test_routes_by_tag_groups_correctly(tracker):
    tag_route(tracker, "GET", "/users", "public")
    tag_route(tracker, "POST", "/users", "public", "write")
    grouped = routes_by_tag(tracker)
    assert "public" in grouped
    assert len(grouped["public"]) == 2
    assert "write" in grouped
    assert len(grouped["write"]) == 1


def test_routes_by_tag_untagged_bucket(tracker):
    tag_route(tracker, "GET", "/users", "public")
    grouped = routes_by_tag(tracker)
    # POST /users and GET /health have no tags
    untagged_keys = {r["key"] for r in grouped.get("untagged", [])}
    assert tracker._key("GET", "/health") in untagged_keys
    assert tracker._key("POST", "/users") in untagged_keys


def test_filter_by_tag_returns_matching_routes(tracker):
    tag_route(tracker, "GET", "/users", "public")
    tag_route(tracker, "GET", "/health", "public", "internal")
    results = filter_by_tag(tracker, "public")
    keys = {r["key"] for r in results}
    assert tracker._key("GET", "/users") in keys
    assert tracker._key("GET", "/health") in keys


def test_filter_by_tag_returns_empty_for_unknown_tag(tracker):
    assert filter_by_tag(tracker, "nonexistent") == []


def test_remove_tag_returns_true_when_present(tracker):
    tag_route(tracker, "GET", "/users", "public", "v1")
    assert remove_tag(tracker, "GET", "/users", "public") is True
    assert get_tags(tracker, "GET", "/users") == {"v1"}


def test_remove_tag_returns_false_when_absent(tracker):
    tag_route(tracker, "GET", "/users", "v1")
    assert remove_tag(tracker, "GET", "/users", "public") is False


def test_remove_tag_returns_false_for_missing_route(tracker):
    assert remove_tag(tracker, "DELETE", "/ghost", "any") is False
