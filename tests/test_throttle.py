"""Tests for routewatch.throttle."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from routewatch.throttle import RouteThrottle, ThrottleConfig
from routewatch.tracker import RouteTracker


# ---------------------------------------------------------------------------
# ThrottleConfig
# ---------------------------------------------------------------------------


def test_throttle_config_defaults():
    cfg = ThrottleConfig()
    assert cfg.max_hits == 10
    assert cfg.window_seconds == 60.0


def test_throttle_config_invalid_max_hits():
    with pytest.raises(ValueError, match="max_hits"):
        ThrottleConfig(max_hits=0)


def test_throttle_config_invalid_window():
    with pytest.raises(ValueError, match="window_seconds"):
        ThrottleConfig(window_seconds=0)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/api/data")
    return t


@pytest.fixture()
def throttle():
    return RouteThrottle(ThrottleConfig(max_hits=3, window_seconds=5.0))


# ---------------------------------------------------------------------------
# should_record
# ---------------------------------------------------------------------------


def test_should_record_allows_up_to_max_hits(throttle):
    for _ in range(3):
        assert throttle.should_record("GET", "/api/data") is True


def test_should_record_suppresses_after_max_hits(throttle):
    for _ in range(3):
        throttle.should_record("GET", "/api/data")
    assert throttle.should_record("GET", "/api/data") is False


def test_should_record_independent_per_route(throttle):
    for _ in range(3):
        throttle.should_record("GET", "/a")
    # /b has its own window
    assert throttle.should_record("GET", "/b") is True


def test_should_record_independent_per_method(throttle):
    for _ in range(3):
        throttle.should_record("GET", "/api/data")
    assert throttle.should_record("POST", "/api/data") is True


def test_should_record_resets_after_window(throttle):
    base = 1_000.0
    with patch("routewatch.throttle.time.monotonic", return_value=base):
        for _ in range(3):
            throttle.should_record("GET", "/api/data")

    # Advance beyond the 5-second window
    with patch("routewatch.throttle.time.monotonic", return_value=base + 6.0):
        assert throttle.should_record("GET", "/api/data") is True


# ---------------------------------------------------------------------------
# throttled_record
# ---------------------------------------------------------------------------


def test_throttled_record_returns_true_when_recorded(throttle, tracker):
    result = throttle.throttled_record(tracker, "GET", "/api/data")
    assert result is True
    assert tracker.hit_count("GET", "/api/data") == 1


def test_throttled_record_returns_false_when_suppressed(throttle, tracker):
    for _ in range(3):
        throttle.throttled_record(tracker, "GET", "/api/data")
    result = throttle.throttled_record(tracker, "GET", "/api/data")
    assert result is False
    assert tracker.hit_count("GET", "/api/data") == 3


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


def test_reset_specific_route_clears_window(throttle):
    for _ in range(3):
        throttle.should_record("GET", "/api/data")
    throttle.reset("GET", "/api/data")
    assert throttle.should_record("GET", "/api/data") is True


def test_reset_all_clears_all_windows(throttle):
    for _ in range(3):
        throttle.should_record("GET", "/a")
    for _ in range(3):
        throttle.should_record("POST", "/b")
    throttle.reset()
    assert throttle.should_record("GET", "/a") is True
    assert throttle.should_record("POST", "/b") is True
