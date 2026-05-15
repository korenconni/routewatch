"""Tests for routewatch.audit."""
import time
import pytest

from routewatch.tracker import RouteTracker
from routewatch.audit import (
    AuditEntry,
    record_audit,
    get_audit_log,
    clear_audit_log,
    audit_report,
)


@pytest.fixture(autouse=True)
def clear_store():
    clear_audit_log()
    yield
    clear_audit_log()


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    return t


def test_audit_entry_key_is_uppercase(tracker):
    entry = record_audit(tracker, "get", "/users", actor="alice")
    assert entry.key == "GET /users"


def test_record_audit_returns_entry(tracker):
    entry = record_audit(tracker, "GET", "/users", actor="bob")
    assert isinstance(entry, AuditEntry)
    assert entry.actor == "bob"
    assert entry.path == "/users"


def test_record_audit_stores_entry(tracker):
    record_audit(tracker, "GET", "/users", actor="alice")
    log = get_audit_log("GET", "/users")
    assert len(log) == 1
    assert log[0].actor == "alice"


def test_record_audit_accumulates_entries(tracker):
    record_audit(tracker, "GET", "/users", actor="alice")
    record_audit(tracker, "GET", "/users", actor="bob")
    log = get_audit_log("GET", "/users")
    assert len(log) == 2


def test_record_audit_auto_registers_unknown_route(tracker):
    entry = record_audit(tracker, "DELETE", "/items", actor="carol")
    assert "DELETE /items" in tracker.routes
    assert entry.path == "/items"


def test_record_audit_stores_metadata(tracker):
    record_audit(tracker, "POST", "/users", actor="dan", metadata={"ip": "127.0.0.1"})
    log = get_audit_log("POST", "/users")
    assert log[0].metadata["ip"] == "127.0.0.1"


def test_record_audit_respects_max_entries(tracker):
    for i in range(10):
        record_audit(tracker, "GET", "/users", actor=f"user{i}", max_entries=5)
    log = get_audit_log("GET", "/users")
    assert len(log) == 5
    assert log[-1].actor == "user9"


def test_get_audit_log_unknown_route_returns_empty():
    log = get_audit_log("GET", "/nonexistent")
    assert log == []


def test_clear_audit_log_specific_route(tracker):
    record_audit(tracker, "GET", "/users", actor="alice")
    record_audit(tracker, "POST", "/users", actor="bob")
    clear_audit_log("GET", "/users")
    assert get_audit_log("GET", "/users") == []
    assert len(get_audit_log("POST", "/users")) == 1


def test_clear_audit_log_all(tracker):
    record_audit(tracker, "GET", "/users", actor="alice")
    record_audit(tracker, "POST", "/users", actor="bob")
    clear_audit_log()
    assert get_audit_log("GET", "/users") == []
    assert get_audit_log("POST", "/users") == []


def test_audit_entry_has_timestamp(tracker):
    before = time.time()
    entry = record_audit(tracker, "GET", "/users", actor="eve")
    after = time.time()
    assert before <= entry.timestamp <= after


def test_audit_report_contains_route_keys(tracker):
    record_audit(tracker, "GET", "/users", actor="alice")
    report = audit_report(tracker)
    assert "GET /users" in report
    assert "1 audit entries" in report


def test_audit_report_shows_actor(tracker):
    record_audit(tracker, "GET", "/users", actor="frank")
    report = audit_report(tracker)
    assert "frank" in report
