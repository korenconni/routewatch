"""Tests for routewatch.labels."""
import pytest

from routewatch.tracker import RouteTracker
from routewatch.labels import (
    set_label,
    get_label,
    get_labels,
    remove_label,
    routes_by_label,
    clear_labels,
)


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/health")
    return t


def test_set_and_get_label(tracker):
    set_label(tracker, "GET", "/users", "owner", "team-a")
    assert get_label(tracker, "GET", "/users", "owner") == "team-a"


def test_get_label_missing_key_returns_none(tracker):
    assert get_label(tracker, "GET", "/users", "nonexistent") is None


def test_get_label_unknown_route_returns_none(tracker):
    assert get_label(tracker, "DELETE", "/gone", "x") is None


def test_set_label_auto_registers_unknown_route(tracker):
    set_label(tracker, "PATCH", "/new", "env", "prod")
    assert "PATCH /new" in tracker.routes


def test_get_labels_returns_all(tracker):
    set_label(tracker, "POST", "/users", "owner", "team-b")
    set_label(tracker, "POST", "/users", "env", "staging")
    labels = get_labels(tracker, "POST", "/users")
    assert labels == {"owner": "team-b", "env": "staging"}


def test_get_labels_empty_for_unlabelled_route(tracker):
    assert get_labels(tracker, "GET", "/health") == {}


def test_set_label_overwrites_existing(tracker):
    set_label(tracker, "GET", "/users", "owner", "team-a")
    set_label(tracker, "GET", "/users", "owner", "team-z")
    assert get_label(tracker, "GET", "/users", "owner") == "team-z"


def test_remove_label_returns_true_when_present(tracker):
    set_label(tracker, "GET", "/users", "owner", "team-a")
    result = remove_label(tracker, "GET", "/users", "owner")
    assert result is True
    assert get_label(tracker, "GET", "/users", "owner") is None


def test_remove_label_returns_false_when_absent(tracker):
    result = remove_label(tracker, "GET", "/health", "missing")
    assert result is False


def test_routes_by_label_finds_matches(tracker):
    set_label(tracker, "GET", "/users", "env", "prod")
    set_label(tracker, "POST", "/users", "env", "prod")
    set_label(tracker, "GET", "/health", "env", "staging")
    matches = routes_by_label(tracker, "env", "prod")
    assert set(matches) == {"GET /users", "POST /users"}


def test_routes_by_label_empty_when_no_match(tracker):
    assert routes_by_label(tracker, "env", "canary") == []


def test_clear_labels_removes_all(tracker):
    set_label(tracker, "GET", "/users", "a", 1)
    set_label(tracker, "GET", "/users", "b", 2)
    clear_labels(tracker, "GET", "/users")
    assert get_labels(tracker, "GET", "/users") == {}


def test_label_values_can_be_non_string(tracker):
    set_label(tracker, "GET", "/health", "priority", 42)
    set_label(tracker, "GET", "/health", "active", True)
    assert get_label(tracker, "GET", "/health", "priority") == 42
    assert get_label(tracker, "GET", "/health", "active") is True
