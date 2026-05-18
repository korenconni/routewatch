"""Tests for routewatch.streaks."""
from __future__ import annotations

import pytest

from routewatch.tracker import RouteTracker
from routewatch.streaks import (
    StreakResult,
    clear_streaks,
    get_streak,
    record_streak,
    top_streaks,
)

WINDOW = 3600  # 1-hour windows for all tests


@pytest.fixture(autouse=True)
def clean():
    clear_streaks()
    yield
    clear_streaks()


@pytest.fixture()
def tracker():
    return RouteTracker()


# ---------------------------------------------------------------------------
# StreakResult dataclass
# ---------------------------------------------------------------------------

def test_streak_result_is_dataclass(tracker):
    result = record_streak("/api/v1", "GET", tracker, window_seconds=WINDOW, ts=0.0)
    assert isinstance(result, StreakResult)


def test_streak_result_key_is_uppercase(tracker):
    result = record_streak("/ping", "get", tracker, window_seconds=WINDOW, ts=0.0)
    assert result.key == "GET /ping"


# ---------------------------------------------------------------------------
# First hit starts streak at 1
# ---------------------------------------------------------------------------

def test_first_hit_streak_is_one(tracker):
    result = record_streak("/a", "GET", tracker, window_seconds=WINDOW, ts=0.0)
    assert result.current_streak == 1


def test_get_streak_unknown_route_returns_zero():
    assert get_streak("/unknown", "DELETE") == 0


# ---------------------------------------------------------------------------
# Same window — streak stays the same
# ---------------------------------------------------------------------------

def test_same_window_streak_unchanged(tracker):
    record_streak("/a", "GET", tracker, window_seconds=WINDOW, ts=100.0)
    result = record_streak("/a", "GET", tracker, window_seconds=WINDOW, ts=200.0)
    assert result.current_streak == 1


# ---------------------------------------------------------------------------
# Consecutive windows — streak increments
# ---------------------------------------------------------------------------

def test_consecutive_windows_increment_streak(tracker):
    record_streak("/a", "GET", tracker, window_seconds=WINDOW, ts=0.0)
    result = record_streak("/a", "GET", tracker, window_seconds=WINDOW, ts=float(WINDOW))
    assert result.current_streak == 2


def test_three_consecutive_windows(tracker):
    for i in range(3):
        r = record_streak("/a", "GET", tracker, window_seconds=WINDOW, ts=float(i * WINDOW))
    assert r.current_streak == 3


# ---------------------------------------------------------------------------
# Gap resets streak
# ---------------------------------------------------------------------------

def test_gap_resets_streak(tracker):
    record_streak("/a", "GET", tracker, window_seconds=WINDOW, ts=0.0)
    result = record_streak("/a", "GET", tracker, window_seconds=WINDOW, ts=float(WINDOW * 3))
    assert result.current_streak == 1


# ---------------------------------------------------------------------------
# Method normalisation
# ---------------------------------------------------------------------------

def test_method_case_normalised(tracker):
    record_streak("/b", "post", tracker, window_seconds=WINDOW, ts=0.0)
    assert get_streak("/b", "POST") == 1


# ---------------------------------------------------------------------------
# top_streaks
# ---------------------------------------------------------------------------

def test_top_streaks_ordering(tracker):
    # /a gets 3 windows, /b gets 1
    for i in range(3):
        record_streak("/a", "GET", tracker, window_seconds=WINDOW, ts=float(i * WINDOW))
    record_streak("/b", "GET", tracker, window_seconds=WINDOW, ts=0.0)

    top = top_streaks(n=5)
    assert top[0].route == "/a"
    assert top[0].current_streak == 3
    assert top[1].route == "/b"


def test_top_streaks_respects_n(tracker):
    for i in range(5):
        record_streak(f"/r{i}", "GET", tracker, window_seconds=WINDOW, ts=0.0)
    assert len(top_streaks(n=3)) == 3


def test_top_streaks_empty_returns_empty():
    assert top_streaks() == []


# ---------------------------------------------------------------------------
# Auto-registers unknown routes
# ---------------------------------------------------------------------------

def test_record_streak_auto_registers_route(tracker):
    record_streak("/new", "PATCH", tracker, window_seconds=WINDOW, ts=0.0)
    assert tracker.is_registered("/new", "PATCH")
