"""Tests for the report module."""

from __future__ import annotations

import json

import pytest

from routewatch.report import (
    build_summary,
    coverage_percent,
    json_report,
    text_report,
)
from routewatch.tracker import RouteTracker


@pytest.fixture()
def populated_tracker():
    t = RouteTracker()
    t.register("/users", "GET")
    t.register("/users", "POST")
    t.register("/items", "GET")
    t.record("/users", "GET")  # only one route hit
    return t


def test_build_summary_length(populated_tracker):
    summaries = build_summary(populated_tracker)
    assert len(summaries) == 3


def test_build_summary_covered_flag(populated_tracker):
    summaries = {(s.path, s.method): s for s in build_summary(populated_tracker)}
    assert summaries[("/users", "GET")].covered is True
    assert summaries[("/users", "POST")].covered is False
    assert summaries[("/items", "GET")].covered is False


def test_coverage_percent(populated_tracker):
    assert coverage_percent(populated_tracker) == pytest.approx(33.33)


def test_coverage_percent_empty():
    assert coverage_percent(RouteTracker()) == 0.0


def test_coverage_percent_full():
    t = RouteTracker()
    t.register("/ping", "GET")
    t.record("/ping", "GET")
    assert coverage_percent(t) == 100.0


def test_text_report_contains_routes(populated_tracker):
    report = text_report(populated_tracker)
    assert "/users" in report
    assert "COVERED" in report
    assert "MISSING" in report


def test_text_report_empty_tracker():
    report = text_report(RouteTracker())
    assert report == "No routes registered."


def test_json_report_structure(populated_tracker):
    raw = json_report(populated_tracker)
    data = json.loads(raw)
    assert "coverage_percent" in data
    assert "routes" in data
    assert data["total"] == 3
    assert data["covered"] == 1


def test_json_report_route_fields(populated_tracker):
    data = json.loads(json_report(populated_tracker))
    route = data["routes"][0]
    assert {"path", "method", "hits", "covered"} == set(route.keys())
