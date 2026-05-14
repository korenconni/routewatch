"""Tests for routewatch.pinning."""
import json
import pytest
from pathlib import Path

from routewatch.tracker import RouteTracker
from routewatch.pinning import (
    PinResult,
    check_pins,
    get_pinned,
    load_pins,
    pin_route,
    save_pins,
    unpin_route,
)


@pytest.fixture()
def tracker() -> RouteTracker:
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("DELETE", "/users/{id}")
    return t


def test_pin_route_adds_to_pinned_set(tracker):
    pin_route(tracker, "GET", "/users")
    assert "GET /users" in get_pinned(tracker)


def test_pin_route_auto_registers_unknown(tracker):
    pin_route(tracker, "GET", "/unknown")
    assert "GET /unknown" in tracker.routes
    assert "GET /unknown" in get_pinned(tracker)


def test_pin_route_is_case_insensitive_on_method(tracker):
    pin_route(tracker, "get", "/users")
    assert "GET /users" in get_pinned(tracker)


def test_unpin_route_removes_from_set(tracker):
    pin_route(tracker, "GET", "/users")
    unpin_route(tracker, "GET", "/users")
    assert "GET /users" not in get_pinned(tracker)


def test_unpin_nonexistent_route_is_safe(tracker):
    unpin_route(tracker, "GET", "/nonexistent")  # should not raise


def test_get_pinned_returns_empty_when_none_pinned(tracker):
    assert get_pinned(tracker) == set()


def test_check_pins_failing_when_no_hits(tracker):
    pin_route(tracker, "GET", "/users")
    result = check_pins(tracker)
    assert "GET /users" in result.failing
    assert result.has_failures is True


def test_check_pins_passing_after_hit(tracker):
    pin_route(tracker, "GET", "/users")
    tracker.record("GET", "/users")
    result = check_pins(tracker)
    assert "GET /users" in result.passing
    assert "GET /users" not in result.failing


def test_check_pins_has_failures_false_when_all_pass(tracker):
    pin_route(tracker, "GET", "/users")
    tracker.record("GET", "/users")
    result = check_pins(tracker)
    assert result.has_failures is False


def test_pin_result_lists_all_pinned(tracker):
    pin_route(tracker, "GET", "/users")
    pin_route(tracker, "POST", "/users")
    result = check_pins(tracker)
    assert set(result.pinned) == {"GET /users", "POST /users"}


def test_save_pins_creates_file(tracker, tmp_path):
    pin_route(tracker, "GET", "/users")
    out = tmp_path / "pins.json"
    save_pins(tracker, out)
    assert out.exists()


def test_save_pins_json_structure(tracker, tmp_path):
    pin_route(tracker, "GET", "/users")
    pin_route(tracker, "DELETE", "/users/{id}")
    out = tmp_path / "pins.json"
    save_pins(tracker, out)
    data = json.loads(out.read_text())
    assert data["version"] == 1
    assert "GET /users" in data["pinned"]
    assert "DELETE /users/{id}" in data["pinned"]


def test_load_pins_restores_pinned_routes(tracker, tmp_path):
    pin_route(tracker, "POST", "/users")
    out = tmp_path / "pins.json"
    save_pins(tracker, out)

    fresh = RouteTracker()
    loaded = load_pins(fresh, out)
    assert "POST /users" in get_pinned(fresh)
    assert "POST /users" in loaded


def test_load_pins_returns_list_of_keys(tracker, tmp_path):
    pin_route(tracker, "GET", "/users")
    out = tmp_path / "pins.json"
    save_pins(tracker, out)
    fresh = RouteTracker()
    loaded = load_pins(fresh, out)
    assert isinstance(loaded, list)
    assert len(loaded) == 1
