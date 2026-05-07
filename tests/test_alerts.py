"""Tests for routewatch.alerts."""

import pytest

from routewatch.alerts import AlertResult, check_coverage_alert, on_alert
from routewatch.tracker import RouteTracker


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("/users", "GET")
    t.register("/users", "POST")
    t.register("/items", "GET")
    t.register("/items", "DELETE")
    # Hit only two of the four routes
    t.record("/users", "GET")
    t.record("/users", "POST")
    return t  # 50 % coverage


def test_alert_result_is_dataclass(tracker):
    result = check_coverage_alert(tracker, threshold=80.0)
    assert isinstance(result, AlertResult)


def test_alert_triggered_below_threshold(tracker):
    result = check_coverage_alert(tracker, threshold=80.0)
    assert result.triggered is True


def test_alert_not_triggered_above_threshold(tracker):
    result = check_coverage_alert(tracker, threshold=40.0)
    assert result.triggered is False


def test_alert_exact_threshold_not_triggered(tracker):
    # 50 % coverage, threshold 50 % — should NOT trigger (coverage == threshold)
    result = check_coverage_alert(tracker, threshold=50.0)
    assert result.triggered is False


def test_alert_coverage_value(tracker):
    result = check_coverage_alert(tracker, threshold=80.0)
    assert result.coverage == pytest.approx(50.0)


def test_alert_threshold_stored(tracker):
    result = check_coverage_alert(tracker, threshold=75.0)
    assert result.threshold == 75.0


def test_alert_uncovered_routes(tracker):
    result = check_coverage_alert(tracker, threshold=80.0)
    assert set(result.uncovered) == {"GET /items", "DELETE /items"}


def test_alert_message_contains_coverage(tracker):
    result = check_coverage_alert(tracker, threshold=80.0)
    assert "50.0%" in result.message


def test_invalid_threshold_raises(tracker):
    with pytest.raises(ValueError):
        check_coverage_alert(tracker, threshold=150.0)


def test_on_alert_callback_called_when_triggered(tracker):
    calls = []
    result = on_alert(tracker, callback=calls.append, threshold=80.0)
    assert len(calls) == 1
    assert calls[0] is result


def test_on_alert_callback_not_called_when_ok(tracker):
    calls = []
    on_alert(tracker, callback=calls.append, threshold=30.0)
    assert calls == []


def test_on_alert_returns_result(tracker):
    result = on_alert(tracker, callback=lambda r: None, threshold=80.0)
    assert isinstance(result, AlertResult)


def test_empty_tracker_full_coverage_no_alert():
    t = RouteTracker()
    result = check_coverage_alert(t, threshold=80.0)
    # 0 routes → 100 % by convention (nothing to miss)
    assert result.triggered is False
