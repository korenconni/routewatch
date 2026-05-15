"""Tests for routewatch.quotas."""
import pytest

from routewatch.tracker import RouteTracker
from routewatch.quotas import (
    QuotaConfig,
    QuotaResult,
    QuotaReport,
    set_quota,
    remove_quota,
    get_quota,
    check_quotas,
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
    return t


def test_set_quota_returns_config(tracker):
    cfg = set_quota(tracker, "GET", "/users", min_hits=5, max_hits=100)
    assert isinstance(cfg, QuotaConfig)
    assert cfg.min_hits == 5
    assert cfg.max_hits == 100


def test_set_quota_key_is_uppercase(tracker):
    cfg = set_quota(tracker, "get", "/users", min_hits=1)
    assert cfg.key == "GET /users"


def test_set_quota_auto_registers_route():
    t = RouteTracker()
    set_quota(t, "DELETE", "/items", min_hits=0)
    assert t.is_registered("DELETE", "/items")


def test_set_quota_invalid_max_less_than_min(tracker):
    with pytest.raises(ValueError, match="max_hits"):
        set_quota(tracker, "GET", "/users", min_hits=10, max_hits=5)


def test_set_quota_invalid_negative_min(tracker):
    with pytest.raises(ValueError, match="min_hits"):
        set_quota(tracker, "GET", "/users", min_hits=-1)


def test_get_quota_returns_config(tracker):
    set_quota(tracker, "GET", "/users", min_hits=2)
    cfg = get_quota("GET", "/users")
    assert cfg is not None
    assert cfg.min_hits == 2


def test_get_quota_unknown_returns_none():
    assert get_quota("GET", "/nonexistent") is None


def test_remove_quota_returns_true(tracker):
    set_quota(tracker, "GET", "/users", min_hits=1)
    assert remove_quota("GET", "/users") is True


def test_remove_quota_nonexistent_returns_false():
    assert remove_quota("GET", "/ghost") is False


def test_check_quotas_within_bounds(tracker):
    set_quota(tracker, "GET", "/users", min_hits=1, max_hits=10)
    for _ in range(5):
        tracker.record("GET", "/users")
    report = check_quotas(tracker)
    assert not report.has_violations
    assert report.results[0].within_quota
    assert report.results[0].reason == "ok"


def test_check_quotas_below_min(tracker):
    set_quota(tracker, "GET", "/users", min_hits=10)
    tracker.record("GET", "/users")
    report = check_quotas(tracker)
    assert report.has_violations
    assert "below min" in report.violations[0].reason


def test_check_quotas_above_max(tracker):
    set_quota(tracker, "POST", "/users", min_hits=0, max_hits=2)
    for _ in range(5):
        tracker.record("POST", "/users")
    report = check_quotas(tracker)
    assert report.has_violations
    assert "above max" in report.violations[0].reason


def test_quota_report_violations_list(tracker):
    set_quota(tracker, "GET", "/users", min_hits=100)
    set_quota(tracker, "POST", "/users", min_hits=0, max_hits=50)
    for _ in range(3):
        tracker.record("POST", "/users")
    report = check_quotas(tracker)
    assert len(report.violations) == 1
    assert report.violations[0].method == "GET"


def test_quota_result_is_dataclass(tracker):
    set_quota(tracker, "GET", "/users", min_hits=0)
    report = check_quotas(tracker)
    r = report.results[0]
    assert isinstance(r, QuotaResult)
    assert r.key == "GET /users"
