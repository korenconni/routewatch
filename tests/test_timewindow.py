"""Tests for routewatch.timewindow."""
import time
import pytest

from routewatch.tracker import RouteTracker
from routewatch.timewindow import (
    build_window_report,
    clear_hit_times,
    hits_in_window,
    record_hit_time,
    WindowReport,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_hit_times()
    yield
    clear_hit_times()


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/health")
    return t


# --- record_hit_time ---

def test_record_hit_time_returns_timestamp():
    ts = record_hit_time("GET", "/users")
    assert isinstance(ts, float)


def test_record_hit_time_uses_provided_ts():
    ts = record_hit_time("GET", "/users", ts=1_000_000.0)
    assert ts == 1_000_000.0


def test_record_hit_time_method_normalised():
    record_hit_time("get", "/users", ts=1.0)
    assert hits_in_window("GET", "/users", window_seconds=10, now=5.0) == 1


# --- hits_in_window ---

def test_hits_in_window_empty_returns_zero():
    assert hits_in_window("GET", "/missing", 60) == 0


def test_hits_in_window_counts_recent_hits():
    now = time.time()
    for delta in [5, 10, 20]:
        record_hit_time("GET", "/users", ts=now - delta)
    assert hits_in_window("GET", "/users", 15, now=now) == 2


def test_hits_in_window_excludes_old_hits():
    now = 1_000.0
    record_hit_time("GET", "/users", ts=900.0)   # 100 s ago
    record_hit_time("GET", "/users", ts=990.0)   # 10 s ago
    assert hits_in_window("GET", "/users", 60, now=now) == 1


def test_hits_in_window_boundary_inclusive():
    now = 100.0
    record_hit_time("GET", "/users", ts=40.0)  # exactly at boundary (100-60=40)
    assert hits_in_window("GET", "/users", 60, now=now) == 1


# --- build_window_report ---

def test_build_window_report_length(tracker):
    reports = build_window_report(tracker, 60)
    assert len(reports) == 3


def test_build_window_report_returns_window_report_instances(tracker):
    for r in build_window_report(tracker, 60):
        assert isinstance(r, WindowReport)


def test_build_window_report_hit_counts(tracker):
    now = 1_000.0
    record_hit_time("GET", "/users", ts=990.0)
    record_hit_time("GET", "/users", ts=995.0)
    record_hit_time("POST", "/users", ts=998.0)
    reports = {(r.method, r.path): r for r in build_window_report(tracker, 60, now=now)}
    assert reports[("GET", "/users")].hit_count == 2
    assert reports[("POST", "/users")].hit_count == 1
    assert reports[("GET", "/health")].hit_count == 0


def test_build_window_report_rate_per_minute(tracker):
    now = 1_000.0
    for _ in range(6):
        record_hit_time("GET", "/users", ts=990.0)
    reports = {(r.method, r.path): r for r in build_window_report(tracker, 60, now=now)}
    assert reports[("GET", "/users")].rate_per_minute == 6.0


def test_build_window_report_sorted_by_hit_count_desc(tracker):
    now = 1_000.0
    record_hit_time("GET", "/health", ts=999.0)
    record_hit_time("GET", "/health", ts=998.0)
    record_hit_time("GET", "/users", ts=997.0)
    reports = build_window_report(tracker, 60, now=now)
    assert reports[0].hit_count >= reports[1].hit_count


# --- clear_hit_times ---

def test_clear_hit_times_single_route():
    record_hit_time("GET", "/users", ts=1.0)
    record_hit_time("GET", "/health", ts=1.0)
    clear_hit_times("GET", "/users")
    assert hits_in_window("GET", "/users", 60, now=100) == 0
    assert hits_in_window("GET", "/health", 60, now=100) == 1


def test_clear_hit_times_all():
    record_hit_time("GET", "/users", ts=1.0)
    record_hit_time("POST", "/users", ts=1.0)
    clear_hit_times()
    assert hits_in_window("GET", "/users", 60, now=100) == 0
    assert hits_in_window("POST", "/users", 60, now=100) == 0
