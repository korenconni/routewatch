"""Tests for routewatch.sampling."""

import pytest

from routewatch.tracker import RouteTracker
from routewatch.sampling import (
    SamplingConfig,
    sampled_record,
    effective_hit_count,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tracker() -> RouteTracker:
    t = RouteTracker()
    t.register("GET", "/items")
    return t


# ---------------------------------------------------------------------------
# SamplingConfig
# ---------------------------------------------------------------------------

def test_sampling_config_defaults():
    cfg = SamplingConfig()
    assert cfg.rate == 1.0


def test_sampling_config_invalid_rate_high():
    with pytest.raises(ValueError):
        SamplingConfig(rate=1.5)


def test_sampling_config_invalid_rate_low():
    with pytest.raises(ValueError):
        SamplingConfig(rate=-0.1)


def test_should_record_always_at_full_rate():
    cfg = SamplingConfig(rate=1.0)
    assert all(cfg.should_record() for _ in range(100))


def test_should_record_never_at_zero_rate():
    cfg = SamplingConfig(rate=0.0)
    assert not any(cfg.should_record() for _ in range(100))


def test_should_record_seeded_reproducible():
    cfg1 = SamplingConfig(rate=0.5, seed=42)
    cfg2 = SamplingConfig(rate=0.5, seed=42)
    results1 = [cfg1.should_record() for _ in range(50)]
    results2 = [cfg2.should_record() for _ in range(50)]
    assert results1 == results2


def test_should_record_approximate_rate():
    """With enough samples the recorded fraction should be close to the rate."""
    cfg = SamplingConfig(rate=0.4, seed=0)
    hits = sum(1 for _ in range(2000) if cfg.should_record())
    assert 600 <= hits <= 1000  # generous bounds around 800


# ---------------------------------------------------------------------------
# sampled_record
# ---------------------------------------------------------------------------

def test_sampled_record_always_records_at_full_rate(tracker):
    cfg = SamplingConfig(rate=1.0)
    recorded = sampled_record(tracker, "GET", "/items", cfg)
    assert recorded is True
    assert tracker.hits("GET", "/items") == 1


def test_sampled_record_never_records_at_zero_rate(tracker):
    cfg = SamplingConfig(rate=0.0)
    for _ in range(10):
        sampled_record(tracker, "GET", "/items", cfg)
    assert tracker.hits("GET", "/items") == 0


def test_sampled_record_returns_false_when_skipped(tracker):
    cfg = SamplingConfig(rate=0.0)
    result = sampled_record(tracker, "GET", "/items", cfg)
    assert result is False


def test_sampled_record_auto_registers_unknown_route():
    t = RouteTracker()
    cfg = SamplingConfig(rate=1.0)
    sampled_record(t, "POST", "/new", cfg)
    assert t.hits("POST", "/new") == 1


# ---------------------------------------------------------------------------
# effective_hit_count
# ---------------------------------------------------------------------------

def test_effective_hit_count_full_rate():
    assert effective_hit_count(100, 1.0) == pytest.approx(100.0)


def test_effective_hit_count_half_rate():
    assert effective_hit_count(50, 0.5) == pytest.approx(100.0)


def test_effective_hit_count_zero_rate_raises():
    with pytest.raises(ValueError):
        effective_hit_count(10, 0.0)
