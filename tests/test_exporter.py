"""Tests for routewatch.exporter."""

from __future__ import annotations

import csv
import io
import json
import os
import tempfile

import pytest

from routewatch.exporter import export_csv, export_json, save_export
from routewatch.tracker import RouteTracker


@pytest.fixture()
def populated_tracker() -> RouteTracker:
    tracker = RouteTracker()
    tracker.register("GET", "/users")
    tracker.register("POST", "/users")
    tracker.register("GET", "/items")
    tracker.record("GET", "/users")  # one hit
    tracker.record("GET", "/users")  # second hit
    tracker.record("POST", "/users")  # one hit
    # GET /items intentionally left uncovered
    return tracker


# --- JSON export ---

def test_export_json_is_valid_json(populated_tracker):
    result = export_json(populated_tracker)
    data = json.loads(result)  # must not raise
    assert isinstance(data, dict)


def test_export_json_total_routes(populated_tracker):
    data = json.loads(export_json(populated_tracker))
    assert data["total_routes"] == 3


def test_export_json_covered_routes(populated_tracker):
    data = json.loads(export_json(populated_tracker))
    assert data["covered_routes"] == 2


def test_export_json_hit_counts(populated_tracker):
    data = json.loads(export_json(populated_tracker))
    get_users = next(r for r in data["routes"] if r["method"] == "GET" and r["path"] == "/users")
    assert get_users["hits"] == 2


def test_export_json_uncovered_flag(populated_tracker):
    data = json.loads(export_json(populated_tracker))
    get_items = next(r for r in data["routes"] if r["path"] == "/items")
    assert get_items["covered"] is False
    assert get_items["hits"] == 0


# --- CSV export ---

def test_export_csv_has_header(populated_tracker):
    result = export_csv(populated_tracker)
    assert result.startswith("method,path,hits,covered")


def test_export_csv_row_count(populated_tracker):
    result = export_csv(populated_tracker)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 3


def test_export_csv_hit_value(populated_tracker):
    result = export_csv(populated_tracker)
    reader = csv.DictReader(io.StringIO(result))
    rows = {(r["method"], r["path"]): r for r in reader}
    assert rows[("GET", "/users")]["hits"] == "2"


# --- save_export ---

def test_save_export_json(populated_tracker):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        path = tmp.name
    try:
        save_export(populated_tracker, path, fmt="json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["total_routes"] == 3
    finally:
        os.unlink(path)


def test_save_export_csv(populated_tracker):
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        path = tmp.name
    try:
        save_export(populated_tracker, path, fmt="csv")
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        assert "method,path,hits,covered" in content
    finally:
        os.unlink(path)


def test_save_export_invalid_format(populated_tracker):
    with pytest.raises(ValueError, match="Unsupported export format"):
        save_export(populated_tracker, "/tmp/out.xml", fmt="xml")
