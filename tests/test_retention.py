"""Tests for routewatch.retention."""

import time
import pytest

from routewatch.tracker import RouteTracker
from routewatch.retention import (
    RetentionPolicy,
    RetentionResult,
    apply_retention,
    record_hit_time,
    get_last_hit_time,
    clear_hit_times,
)


@pytest.fixture(autouse=True)
def _clean_hit_times():
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


# --- RetentionPolicy validation ---

def test_policy_invalid_max_age():
    with pytest.raises(ValueError, match="max_age_seconds"):
        RetentionPolicy(max_age_seconds=0)


def test_policy_invalid_min_hits():
    with pytest.raises(ValueError, match="min_hits_to_keep"):
        RetentionPolicy(max_age_seconds=60, min_hits_to_keep=-1)


def test_policy_valid_defaults():
    p = RetentionPolicy(max_age_seconds=3600)
    assert p.min_hits_to_keep == 0


# --- record_hit_time / get_last_hit_time ---

def test_record_and_get_hit_time():
    ts = time.time()
    record_hit_time("GET", "/users", ts=ts)
    assert get_last_hit_time("GET", "/users") == ts


def test_get_hit_time_unknown_route_returns_none():
    assert get_last_hit_time("DELETE", "/nope") is None


def test_record_hit_time_normalises_method():
    ts = time.time()
    record_hit_time("get", "/users", ts=ts)
    assert get_last_hit_time("GET", "/users") == ts


# --- apply_retention ---

def test_apply_retention_zeroes_old_route(tracker):
    old_ts = time.time() - 7200  # 2 hours ago
    record_hit_time("GET", "/users", ts=old_ts)
    tracker.routes["GET /users"].hits = 10

    policy = RetentionPolicy(max_age_seconds=3600)
    result = apply_retention(tracker, policy)

    assert tracker.routes["GET /users"].hits == 0
    assert result.routes_zeroed == 1
    assert "GET /users" in result.details
    assert result.details["GET /users"] == 10


def test_apply_retention_keeps_recent_route(tracker):
    record_hit_time("GET", "/users", ts=time.time())
    tracker.routes["GET /users"].hits = 5

    policy = RetentionPolicy(max_age_seconds=3600)
    result = apply_retention(tracker, policy)

    assert tracker.routes["GET /users"].hits == 5
    assert result.routes_zeroed == 0


def test_apply_retention_skips_routes_with_no_hit_time(tracker):
    tracker.routes["GET /health"].hits = 3
    policy = RetentionPolicy(max_age_seconds=60)
    result = apply_retention(tracker, policy)

    assert tracker.routes["GET /health"].hits == 3


def test_apply_retention_respects_min_hits_to_keep(tracker):
    old_ts = time.time() - 7200
    record_hit_time("POST", "/users", ts=old_ts)
    tracker.routes["POST /users"].hits = 2

    policy = RetentionPolicy(max_age_seconds=3600, min_hits_to_keep=5)
    result = apply_retention(tracker, policy)

    # hits (2) <= min_hits_to_keep (5), so not zeroed
    assert tracker.routes["POST /users"].hits == 2
    assert result.routes_zeroed == 0


def test_retention_result_any_expired_false_when_none_zeroed(tracker):
    policy = RetentionPolicy(max_age_seconds=3600)
    result = apply_retention(tracker, policy)
    assert result.any_expired is False


def test_retention_result_any_expired_true_when_zeroed(tracker):
    record_hit_time("GET", "/users", ts=time.time() - 9000)
    tracker.routes["GET /users"].hits = 1
    policy = RetentionPolicy(max_age_seconds=3600)
    result = apply_retention(tracker, policy)
    assert result.any_expired is True


def test_apply_retention_routes_checked_count(tracker):
    policy = RetentionPolicy(max_age_seconds=60)
    result = apply_retention(tracker, policy)
    assert result.routes_checked == 3
