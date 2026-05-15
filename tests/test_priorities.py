"""Tests for routewatch.priorities."""
import pytest

from routewatch.priorities import (
    PriorityResult,
    _store,
    get_priority,
    priority_report,
    remove_priority,
    routes_by_priority,
    set_priority,
)
from routewatch.tracker import RouteTracker


@pytest.fixture(autouse=True)
def clear_store():
    _store.clear()
    yield
    _store.clear()


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/health")
    return t


def test_priority_result_is_dataclass(tracker):
    result = set_priority(tracker, "GET", "/users", 1)
    assert isinstance(result, PriorityResult)


def test_set_priority_returns_correct_fields(tracker):
    result = set_priority(tracker, "GET", "/users", 2)
    assert result.method == "GET"
    assert result.path == "/users"
    assert result.priority == 2


def test_priority_result_key_is_uppercase(tracker):
    result = set_priority(tracker, "get", "/users", 1)
    assert result.key == "GET /users"


def test_priority_result_label_critical(tracker):
    result = set_priority(tracker, "GET", "/users", 1)
    assert result.label == "critical"


def test_priority_result_label_medium(tracker):
    result = set_priority(tracker, "GET", "/users", 3)
    assert result.label == "medium"


def test_priority_result_label_minimal(tracker):
    result = set_priority(tracker, "GET", "/users", 5)
    assert result.label == "minimal"


def test_set_priority_invalid_too_low(tracker):
    with pytest.raises(ValueError, match="priority must be between"):
        set_priority(tracker, "GET", "/users", 0)


def test_set_priority_invalid_too_high(tracker):
    with pytest.raises(ValueError, match="priority must be between"):
        set_priority(tracker, "GET", "/users", 6)


def test_set_priority_auto_registers_unknown_route():
    t = RouteTracker()
    set_priority(t, "DELETE", "/items", 2)
    assert "DELETE /items" in t.routes


def test_get_priority_returns_default_when_unset(tracker):
    assert get_priority("GET", "/users") == 3


def test_get_priority_returns_set_value(tracker):
    set_priority(tracker, "GET", "/users", 1)
    assert get_priority("GET", "/users") == 1


def test_remove_priority_reverts_to_default(tracker):
    set_priority(tracker, "GET", "/users", 1)
    removed = remove_priority("GET", "/users")
    assert removed is True
    assert get_priority("GET", "/users") == 3


def test_remove_priority_nonexistent_returns_false(tracker):
    assert remove_priority("GET", "/nonexistent") is False


def test_routes_by_priority_returns_matching(tracker):
    set_priority(tracker, "GET", "/users", 1)
    set_priority(tracker, "POST", "/users", 1)
    results = routes_by_priority(tracker, 1)
    keys = [r.key for r in results]
    assert "GET /users" in keys
    assert "POST /users" in keys


def test_routes_by_priority_excludes_others(tracker):
    set_priority(tracker, "GET", "/users", 1)
    results = routes_by_priority(tracker, 1)
    keys = [r.key for r in results]
    assert "GET /health" not in keys


def test_priority_report_includes_all_routes(tracker):
    report = priority_report(tracker)
    assert len(report) == 3


def test_priority_report_sorted_by_priority(tracker):
    set_priority(tracker, "GET", "/health", 1)
    set_priority(tracker, "POST", "/users", 5)
    report = priority_report(tracker)
    assert report[0].priority <= report[-1].priority


def test_priority_report_uses_default_for_unset(tracker):
    report = priority_report(tracker)
    for result in report:
        assert result.priority == 3
