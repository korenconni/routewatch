import pytest

from routewatch.tracker import RouteTracker
from routewatch.annotations import (
    annotate,
    get_annotation,
    get_annotations,
    remove_annotation,
    routes_with_annotation,
    clear_annotations,
)


@pytest.fixture
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/health")
    yield t
    clear_annotations(t)


def test_annotate_sets_field(tracker):
    annotate(tracker, "GET", "/users", "owner", "team-backend")
    assert get_annotation(tracker, "GET", "/users", "owner") == "team-backend"


def test_get_annotation_missing_field_returns_none(tracker):
    assert get_annotation(tracker, "GET", "/users", "nonexistent") is None


def test_get_annotation_unknown_route_returns_none(tracker):
    assert get_annotation(tracker, "DELETE", "/unknown", "owner") is None


def test_annotate_auto_registers_unknown_route(tracker):
    annotate(tracker, "PATCH", "/new-route", "deprecated", "true")
    assert ("PATCH", "/new-route") in [
        (r.method, r.path) for r in tracker.routes()
    ]


def test_annotate_overwrites_existing_field(tracker):
    annotate(tracker, "GET", "/users", "owner", "team-a")
    annotate(tracker, "GET", "/users", "owner", "team-b")
    assert get_annotation(tracker, "GET", "/users", "owner") == "team-b"


def test_annotate_multiple_fields(tracker):
    annotate(tracker, "GET", "/users", "owner", "team-backend")
    annotate(tracker, "GET", "/users", "deprecated", "false")
    annotations = get_annotations(tracker, "GET", "/users")
    assert annotations["owner"] == "team-backend"
    assert annotations["deprecated"] == "false"


def test_get_annotations_returns_empty_dict_for_unannotated(tracker):
    result = get_annotations(tracker, "GET", "/health")
    assert result == {}


def test_get_annotations_returns_copy(tracker):
    annotate(tracker, "GET", "/users", "owner", "team-backend")
    result = get_annotations(tracker, "GET", "/users")
    result["owner"] = "mutated"
    assert get_annotation(tracker, "GET", "/users", "owner") == "team-backend"


def test_remove_annotation_returns_true_when_present(tracker):
    annotate(tracker, "POST", "/users", "sla", "high")
    assert remove_annotation(tracker, "POST", "/users", "sla") is True
    assert get_annotation(tracker, "POST", "/users", "sla") is None


def test_remove_annotation_returns_false_when_absent(tracker):
    assert remove_annotation(tracker, "GET", "/health", "missing") is False


def test_routes_with_annotation_returns_matching_keys(tracker):
    annotate(tracker, "GET", "/users", "deprecated", "true")
    annotate(tracker, "POST", "/users", "deprecated", "false")
    annotate(tracker, "GET", "/health", "owner", "platform")
    result = routes_with_annotation(tracker, "deprecated")
    assert "GET /users" in result
    assert "POST /users" in result
    assert "GET /health" not in result


def test_routes_with_annotation_returns_sorted(tracker):
    annotate(tracker, "POST", "/users", "owner", "b")
    annotate(tracker, "GET", "/users", "owner", "a")
    result = routes_with_annotation(tracker, "owner")
    assert result == sorted(result)


def test_clear_annotations_removes_all(tracker):
    annotate(tracker, "GET", "/users", "owner", "team-backend")
    annotate(tracker, "POST", "/users", "sla", "high")
    clear_annotations(tracker)
    assert get_annotations(tracker, "GET", "/users") == {}
    assert get_annotations(tracker, "POST", "/users") == {}
