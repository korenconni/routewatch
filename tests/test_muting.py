"""Tests for routewatch.muting."""
import pytest

from routewatch.tracker import RouteTracker
from routewatch.muting import (
    MuteResult,
    mute_route,
    unmute_route,
    is_muted,
    get_muted,
    muted_record,
    mute_report,
    _muted,
)


@pytest.fixture(autouse=True)
def clear_muted():
    """Ensure the global mute store is clean before every test."""
    _muted.clear()
    yield
    _muted.clear()


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/health")
    return t


# --- MuteResult dataclass ---

def test_mute_result_key_is_uppercase():
    r = mute_route("get", "/users")
    assert r.key == "GET /users"


def test_mute_result_muted_flag():
    r = mute_route("GET", "/users")
    assert r.muted is True


def test_unmute_result_muted_flag():
    mute_route("GET", "/users")
    r = unmute_route("GET", "/users")
    assert r.muted is False


# --- mute_route / unmute_route ---

def test_mute_route_adds_to_store():
    mute_route("GET", "/users")
    assert is_muted("GET", "/users")


def test_mute_route_normalises_method():
    mute_route("get", "/users")
    assert is_muted("GET", "/users")


def test_unmute_route_removes_from_store():
    mute_route("GET", "/users")
    unmute_route("GET", "/users")
    assert not is_muted("GET", "/users")


def test_unmute_nonexistent_is_safe():
    # Should not raise even if route was never muted
    result = unmute_route("DELETE", "/ghost")
    assert result.muted is False


def test_mute_is_idempotent():
    mute_route("GET", "/users")
    mute_route("GET", "/users")
    assert len(get_muted()) == 1


# --- get_muted ---

def test_get_muted_returns_copy():
    mute_route("GET", "/a")
    mute_route("POST", "/b")
    snapshot = get_muted()
    _muted.clear()
    assert len(snapshot) == 2  # original copy unaffected


# --- muted_record ---

def test_muted_record_suppresses_muted_route(tracker):
    mute_route("GET", "/health")
    recorded = muted_record(tracker, "GET", "/health")
    assert recorded is False
    assert tracker.routes["GET /health"].hits == 0


def test_muted_record_allows_active_route(tracker):
    recorded = muted_record(tracker, "GET", "/users")
    assert recorded is True
    assert tracker.routes["GET /users"].hits == 1


def test_muted_record_auto_registers_unknown_active_route(tracker):
    recorded = muted_record(tracker, "PATCH", "/new")
    assert recorded is True
    assert tracker.routes["PATCH /new"].hits == 1


# --- mute_report ---

def test_mute_report_contains_muted_label(tracker):
    mute_route("GET", "/health")
    report = mute_report(tracker)
    assert "[MUTED]" in report
    assert "/health" in report


def test_mute_report_summary_counts(tracker):
    mute_route("GET", "/health")
    report = mute_report(tracker)
    assert "3 routes" in report
    assert "1 muted" in report


def test_mute_report_no_mutes(tracker):
    report = mute_report(tracker)
    assert "0 muted" in report
    assert "[MUTED]" not in report
