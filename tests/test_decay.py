"""Tests for routewatch.decay."""
from __future__ import annotations

import time
import math
import pytest

from routewatch.tracker import RouteTracker
from routewatch.decay import (
    DecayConfig,
    DecayedRoute,
    apply_decay,
    decay_report,
    _decay_factor,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tracker() -> RouteTracker:
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/items")
    return t


# ---------------------------------------------------------------------------
# DecayConfig
# ---------------------------------------------------------------------------


def test_decay_config_defaults():
    cfg = DecayConfig()
    assert cfg.half_life_seconds == 86_400.0
    assert cfg.min_hits == 0.0


def test_decay_config_invalid_half_life():
    with pytest.raises(ValueError, match="half_life_seconds"):
        DecayConfig(half_life_seconds=0)


def test_decay_config_invalid_min_hits():
    with pytest.raises(ValueError, match="min_hits"):
        DecayConfig(min_hits=-1)


# ---------------------------------------------------------------------------
# _decay_factor
# ---------------------------------------------------------------------------


def test_decay_factor_zero_age():
    assert _decay_factor(0, 86_400) == pytest.approx(1.0)


def test_decay_factor_one_half_life():
    assert _decay_factor(86_400, 86_400) == pytest.approx(0.5)


def test_decay_factor_two_half_lives():
    assert _decay_factor(172_800, 86_400) == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# apply_decay
# ---------------------------------------------------------------------------


def test_apply_decay_returns_all_routes(tracker):
    result = apply_decay(tracker)
    assert set(result.keys()) == {"GET /users", "POST /users", "GET /items"}


def test_apply_decay_zero_hits_gives_zero_decayed(tracker):
    now = time.time()
    result = apply_decay(tracker, reference_time=now)
    for dr in result.values():
        assert dr.decayed_hits == 0.0
        assert dr.raw_hits == 0


def test_apply_decay_fresh_hit_minimal_decay(tracker):
    now = time.time()
    tracker.record("GET", "/users")
    # Simulate last_hit_at being just 1 second ago
    tracker._routes["GET /users"].last_hit_at = now - 1
    result = apply_decay(tracker, reference_time=now)
    dr = result["GET /users"]
    assert dr.raw_hits == 1
    assert dr.decayed_hits > 0.99  # almost no decay


def test_apply_decay_old_hit_significant_decay(tracker):
    now = time.time()
    tracker.record("GET", "/users")
    # 10 half-lives ago
    tracker._routes["GET /users"].last_hit_at = now - 86_400 * 10
    result = apply_decay(tracker, reference_time=now)
    dr = result["GET /users"]
    expected = 1 * math.pow(0.5, 10)
    assert dr.decayed_hits == pytest.approx(expected, abs=1e-3)


def test_apply_decay_respects_min_hits(tracker):
    cfg = DecayConfig(half_life_seconds=1.0, min_hits=0.5)
    now = time.time()
    tracker.record("GET", "/users")
    tracker._routes["GET /users"].last_hit_at = now - 1_000_000
    result = apply_decay(tracker, cfg, reference_time=now)
    assert result["GET /users"].decayed_hits >= 0.5


def test_apply_decay_result_is_dataclass(tracker):
    result = apply_decay(tracker)
    for dr in result.values():
        assert isinstance(dr, DecayedRoute)


# ---------------------------------------------------------------------------
# decay_report
# ---------------------------------------------------------------------------


def test_decay_report_empty_tracker():
    t = RouteTracker()
    assert "No routes" in decay_report(t)


def test_decay_report_contains_route_keys(tracker):
    report = decay_report(tracker)
    assert "GET /users" in report
    assert "POST /users" in report
    assert "GET /items" in report


def test_decay_report_is_string(tracker):
    assert isinstance(decay_report(tracker), str)
