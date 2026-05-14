"""Tests for routewatch.baseline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from routewatch.baseline import (
    BaselineResult,
    baseline_report,
    compare_to_baseline,
    load_baseline,
    save_baseline,
)
from routewatch.tracker import RouteTracker


@pytest.fixture()
def tracker() -> RouteTracker:
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/items")
    t.record("GET", "/users")
    t.record("GET", "/users")
    return t


# ---------------------------------------------------------------------------
# save_baseline / load_baseline
# ---------------------------------------------------------------------------

def test_save_baseline_creates_file(tmp_path, tracker):
    p = tmp_path / "baseline.json"
    save_baseline(tracker, p)
    assert p.exists()


def test_save_baseline_has_version(tmp_path, tracker):
    p = tmp_path / "baseline.json"
    data = save_baseline(tracker, p)
    assert data["version"] == 1


def test_save_baseline_has_created_at(tmp_path, tracker):
    p = tmp_path / "baseline.json"
    data = save_baseline(tracker, p)
    assert "created_at" in data


def test_save_baseline_route_count(tmp_path, tracker):
    p = tmp_path / "baseline.json"
    data = save_baseline(tracker, p)
    assert len(data["routes"]) == 3


def test_load_baseline_returns_dict(tmp_path, tracker):
    p = tmp_path / "baseline.json"
    save_baseline(tracker, p)
    loaded = load_baseline(p)
    assert isinstance(loaded, dict)
    assert "routes" in loaded


def test_load_baseline_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_baseline(tmp_path / "nonexistent.json")


# ---------------------------------------------------------------------------
# compare_to_baseline
# ---------------------------------------------------------------------------

def _make_baseline(routes: dict) -> dict:
    return {"version": 1, "routes": routes}


def test_compare_matched_route(tracker):
    baseline = _make_baseline({
        "GET /users": {"hits": 5, "covered": True},
    })
    result = compare_to_baseline(tracker, baseline)
    assert "GET /users" in result.matched


def test_compare_regressed_route(tracker):
    baseline = _make_baseline({
        "POST /users": {"hits": 3, "covered": True},
    })
    result = compare_to_baseline(tracker, baseline)
    assert "POST /users" in result.regressed


def test_compare_improved_route(tracker):
    baseline = _make_baseline({
        "GET /users": {"hits": 0, "covered": False},
    })
    result = compare_to_baseline(tracker, baseline)
    assert "GET /users" in result.improved


def test_compare_unknown_route(tracker):
    baseline = _make_baseline({})
    result = compare_to_baseline(tracker, baseline)
    assert "GET /users" in result.unknown


def test_has_regressions_true(tracker):
    baseline = _make_baseline({
        "POST /users": {"hits": 1, "covered": True},
    })
    result = compare_to_baseline(tracker, baseline)
    assert result.has_regressions is True


def test_has_regressions_false(tracker):
    baseline = _make_baseline({
        "GET /users": {"hits": 1, "covered": True},
    })
    result = compare_to_baseline(tracker, baseline)
    assert result.has_regressions is False


# ---------------------------------------------------------------------------
# baseline_report
# ---------------------------------------------------------------------------

def test_baseline_report_contains_header():
    result = BaselineResult(matched=["GET /a"], regressed=[], improved=[], unknown=[])
    report = baseline_report(result)
    assert "Baseline Comparison" in report


def test_baseline_report_lists_regressed():
    result = BaselineResult(matched=[], regressed=["GET /gone"], improved=[], unknown=[])
    report = baseline_report(result)
    assert "GET /gone" in report


def test_baseline_report_lists_improved():
    result = BaselineResult(matched=[], regressed=[], improved=["POST /new"], unknown=[])
    report = baseline_report(result)
    assert "POST /new" in report
