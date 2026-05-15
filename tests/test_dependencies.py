"""Tests for routewatch.dependencies."""
import pytest

from routewatch.tracker import RouteTracker
from routewatch import dependencies as dep
from routewatch.dependencies import (
    DependencyResult,
    add_dependency,
    remove_dependency,
    get_dependencies,
    routes_for_resource,
    resources_for_route,
    all_resources,
)


@pytest.fixture(autouse=True)
def _clear_store():
    dep._store.clear()
    yield
    dep._store.clear()


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    return t


def test_dependency_result_is_dataclass(tracker):
    result = add_dependency(tracker, "GET", "/users", "db.users")
    assert isinstance(result, DependencyResult)


def test_add_dependency_stores_route(tracker):
    add_dependency(tracker, "GET", "/users", "db.users")
    assert "GET /users" in routes_for_resource("db.users")


def test_add_dependency_returns_correct_resource(tracker):
    result = add_dependency(tracker, "GET", "/users", "db.users")
    assert result.resource == "db.users"


def test_add_dependency_auto_registers_unknown_route(tracker):
    add_dependency(tracker, "DELETE", "/items", "db.items")
    assert "DELETE /items" in tracker.routes


def test_add_dependency_is_additive(tracker):
    add_dependency(tracker, "GET", "/users", "db.users")
    add_dependency(tracker, "POST", "/users", "db.users")
    result = get_dependencies("db.users")
    assert result.route_count == 2


def test_add_dependency_multiple_resources(tracker):
    add_dependency(tracker, "GET", "/users", "db.users")
    add_dependency(tracker, "GET", "/users", "cache.users")
    assert "GET /users" in routes_for_resource("db.users")
    assert "GET /users" in routes_for_resource("cache.users")


def test_remove_dependency_returns_true_when_found(tracker):
    add_dependency(tracker, "GET", "/users", "db.users")
    assert remove_dependency("GET", "/users", "db.users") is True


def test_remove_dependency_returns_false_when_missing(tracker):
    assert remove_dependency("GET", "/users", "db.users") is False


def test_remove_dependency_cleans_empty_resource(tracker):
    add_dependency(tracker, "GET", "/users", "db.users")
    remove_dependency("GET", "/users", "db.users")
    assert "db.users" not in all_resources()


def test_get_dependencies_unknown_resource():
    result = get_dependencies("nonexistent")
    assert result.route_count == 0
    assert result.routes == set()


def test_resources_for_route_returns_all(tracker):
    add_dependency(tracker, "GET", "/users", "db.users")
    add_dependency(tracker, "GET", "/users", "cache.users")
    resources = resources_for_route("GET", "/users")
    assert resources == {"db.users", "cache.users"}


def test_resources_for_route_empty_when_none(tracker):
    assert resources_for_route("GET", "/users") == set()


def test_all_resources_reflects_additions(tracker):
    add_dependency(tracker, "GET", "/users", "db.users")
    add_dependency(tracker, "POST", "/users", "queue.jobs")
    assert all_resources() == {"db.users", "queue.jobs"}


def test_key_is_uppercase(tracker):
    add_dependency(tracker, "get", "/users", "db.users")
    assert "GET /users" in routes_for_resource("db.users")
