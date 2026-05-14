"""Tests for routewatch.deprecations."""
from datetime import date

import pytest

from routewatch.tracker import RouteTracker
from routewatch import deprecations
from routewatch.deprecations import (
    deprecate_route,
    undeprecate_route,
    get_deprecation,
    get_deprecated_routes,
    deprecation_report,
    DeprecationInfo,
)


@pytest.fixture(autouse=True)
def clear_store():
    deprecations._store.clear()
    yield
    deprecations._store.clear()


@pytest.fixture
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("DELETE", "/users/{id}")
    return t


def test_deprecate_route_returns_info(tracker):
    info = deprecate_route(tracker, "GET", "/users", reason="Use /members instead")
    assert isinstance(info, DeprecationInfo)
    assert info.reason == "Use /members instead"


def test_deprecate_route_stores_info(tracker):
    deprecate_route(tracker, "GET", "/users", reason="old")
    result = get_deprecation("GET", "/users")
    assert result is not None
    assert result.reason == "old"


def test_deprecate_route_auto_registers(tracker):
    deprecate_route(tracker, "POST", "/legacy", reason="removed")
    assert "POST:/legacy" in tracker._routes


def test_deprecate_route_with_sunset(tracker):
    sunset = date(2025, 12, 31)
    info = deprecate_route(tracker, "GET", "/users", reason="old", sunset_on=sunset)
    assert info.sunset_on == sunset


def test_deprecate_route_with_replacement(tracker):
    info = deprecate_route(
        tracker, "GET", "/users", reason="old", replacement="/members"
    )
    assert info.replacement == "/members"


def test_deprecate_route_default_deprecated_on(tracker):
    info = deprecate_route(tracker, "GET", "/users", reason="old")
    assert info.deprecated_on == date.today()


def test_undeprecate_removes_info(tracker):
    deprecate_route(tracker, "GET", "/users", reason="old")
    removed = undeprecate_route("GET", "/users")
    assert removed is True
    assert get_deprecation("GET", "/users") is None


def test_undeprecate_nonexistent_returns_false(tracker):
    result = undeprecate_route("GET", "/nonexistent")
    assert result is False


def test_get_deprecation_unknown_route_returns_none(tracker):
    assert get_deprecation("GET", "/unknown") is None


def test_get_deprecated_routes_returns_only_registered(tracker):
    deprecate_route(tracker, "GET", "/users", reason="old")
    deprecated = get_deprecated_routes(tracker)
    assert "GET:/users" in deprecated
    assert "DELETE:/users/{id}" not in deprecated


def test_get_deprecated_routes_empty_when_none(tracker):
    assert get_deprecated_routes(tracker) == set()


def test_deprecation_report_no_deprecated(tracker):
    report = deprecation_report(tracker)
    assert report == "No deprecated routes."


def test_deprecation_report_includes_route(tracker):
    deprecate_route(tracker, "GET", "/users", reason="Use /members")
    report = deprecation_report(tracker)
    assert "GET:/users" in report
    assert "Use /members" in report


def test_deprecation_report_includes_sunset(tracker):
    deprecate_route(
        tracker, "DELETE", "/users/{id}", reason="old", sunset_on=date(2025, 6, 1)
    )
    report = deprecation_report(tracker)
    assert "2025-06-01" in report


def test_deprecation_report_includes_replacement(tracker):
    deprecate_route(
        tracker, "GET", "/users", reason="old", replacement="/members"
    )
    report = deprecation_report(tracker)
    assert "/members" in report
