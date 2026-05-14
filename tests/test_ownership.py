"""Tests for routewatch.ownership."""
import pytest

from routewatch.tracker import RouteTracker
from routewatch.ownership import (
    OwnerInfo,
    assign_owner,
    get_owner,
    remove_owner,
    routes_by_team,
    unowned_routes,
    ownership_report,
    _store,
)


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


def test_assign_owner_returns_owner_info(tracker):
    info = assign_owner(tracker, "GET", "/users", team="backend")
    assert isinstance(info, OwnerInfo)
    assert info.team == "backend"


def test_assign_owner_stores_contact(tracker):
    assign_owner(tracker, "GET", "/users", team="backend", contact="eng@example.com")
    info = get_owner("GET", "/users")
    assert info is not None
    assert info.contact == "eng@example.com"


def test_assign_owner_auto_registers_unknown_route(tracker):
    assign_owner(tracker, "DELETE", "/unknown", team="ops")
    assert tracker._key("DELETE", "/unknown") in tracker._routes


def test_get_owner_returns_none_for_unassigned(tracker):
    assert get_owner("GET", "/health") is None


def test_get_owner_case_insensitive_method(tracker):
    assign_owner(tracker, "get", "/users", team="frontend")
    info = get_owner("GET", "/users")
    assert info is not None
    assert info.team == "frontend"


def test_remove_owner_returns_true_when_present(tracker):
    assign_owner(tracker, "GET", "/users", team="backend")
    assert remove_owner("GET", "/users") is True


def test_remove_owner_returns_false_when_absent(tracker):
    assert remove_owner("GET", "/nonexistent") is False


def test_remove_owner_clears_entry(tracker):
    assign_owner(tracker, "GET", "/users", team="backend")
    remove_owner("GET", "/users")
    assert get_owner("GET", "/users") is None


def test_routes_by_team(tracker):
    assign_owner(tracker, "GET", "/users", team="backend")
    assign_owner(tracker, "POST", "/users", team="backend")
    assign_owner(tracker, "GET", "/health", team="infra")
    result = routes_by_team("backend")
    assert "GET:/users" in result
    assert "POST:/users" in result
    assert "GET:/health" not in result


def test_routes_by_team_empty_for_unknown_team(tracker):
    assert routes_by_team("ghost-team") == []


def test_unowned_routes_returns_all_when_none_assigned(tracker):
    result = unowned_routes(tracker)
    assert len(result) == 3


def test_unowned_routes_excludes_assigned(tracker):
    assign_owner(tracker, "GET", "/users", team="backend")
    result = unowned_routes(tracker)
    assert "GET:/users" not in result
    assert "POST:/users" in result


def test_ownership_report_contains_team(tracker):
    assign_owner(tracker, "GET", "/users", team="backend", contact="eng@x.com")
    report = ownership_report(tracker)
    assert "backend" in report
    assert "eng@x.com" in report


def test_ownership_report_marks_unowned(tracker):
    report = ownership_report(tracker)
    assert "(unowned)" in report
