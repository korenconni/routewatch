"""Tests for routewatch.sla."""
import pytest

from routewatch.tracker import RouteTracker
from routewatch.sla import (
    SLATarget,
    SLAResult,
    SLAReport,
    set_sla,
    get_sla,
    remove_sla,
    check_sla,
    sla_text_report,
    _store,
)


@pytest.fixture(autouse=True)
def clear_store():
    _store.clear()
    yield
    _store.clear()


@pytest.fixture
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    return t


def test_set_sla_returns_target(tracker):
    target = set_sla(tracker, "GET", "/users", min_hits=10)
    assert isinstance(target, SLATarget)
    assert target.method == "GET"
    assert target.path == "/users"
    assert target.min_hits == 10


def test_set_sla_normalises_method(tracker):
    target = set_sla(tracker, "get", "/users", min_hits=5)
    assert target.method == "GET"


def test_set_sla_auto_registers_route():
    t = RouteTracker()
    set_sla(t, "DELETE", "/items", min_hits=1)
    assert "DELETE:/items" in t.routes


def test_get_sla_returns_target(tracker):
    set_sla(tracker, "GET", "/users", min_hits=10)
    result = get_sla("GET", "/users")
    assert result is not None
    assert result.min_hits == 10


def test_get_sla_missing_returns_none():
    assert get_sla("GET", "/nonexistent") is None


def test_remove_sla_returns_true_when_exists(tracker):
    set_sla(tracker, "GET", "/users", min_hits=5)
    assert remove_sla("GET", "/users") is True


def test_remove_sla_returns_false_when_missing():
    assert remove_sla("GET", "/ghost") is False


def test_remove_sla_deletes_target(tracker):
    set_sla(tracker, "GET", "/users", min_hits=5)
    remove_sla("GET", "/users")
    assert get_sla("GET", "/users") is None


def test_check_sla_met_when_hits_sufficient(tracker):
    set_sla(tracker, "GET", "/users", min_hits=3)
    from routewatch.tracker import record
    for _ in range(3):
        record(tracker, "GET", "/users")
    report = check_sla(tracker)
    assert report.results[0].met is True
    assert report.results[0].shortfall == 0


def test_check_sla_violated_when_hits_insufficient(tracker):
    set_sla(tracker, "GET", "/users", min_hits=10)
    from routewatch.tracker import record
    record(tracker, "GET", "/users")
    report = check_sla(tracker)
    assert report.results[0].met is False
    assert report.results[0].shortfall == 9


def test_sla_report_has_violations(tracker):
    set_sla(tracker, "GET", "/users", min_hits=100)
    report = check_sla(tracker)
    assert report.has_violations is True
    assert len(report.violations) == 1


def test_sla_report_no_violations(tracker):
    set_sla(tracker, "GET", "/users", min_hits=0)
    report = check_sla(tracker)
    assert report.has_violations is False


def test_sla_text_report_contains_ok(tracker):
    set_sla(tracker, "GET", "/users", min_hits=0)
    report = check_sla(tracker)
    text = sla_text_report(report)
    assert "OK" in text
    assert "/users" in text


def test_sla_text_report_contains_fail(tracker):
    set_sla(tracker, "GET", "/users", min_hits=999)
    report = check_sla(tracker)
    text = sla_text_report(report)
    assert "FAIL" in text


def test_sla_text_report_empty():
    t = RouteTracker()
    report = check_sla(t)
    text = sla_text_report(report)
    assert "No SLA targets registered" in text


def test_sla_period_label_stored(tracker):
    set_sla(tracker, "POST", "/users", min_hits=5, period_label="daily")
    target = get_sla("POST", "/users")
    assert target.period_label == "daily"
