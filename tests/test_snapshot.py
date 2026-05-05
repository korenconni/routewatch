"""Tests for routewatch.snapshot serialization module."""

import json
import os
import tempfile
import time

import pytest

from routewatch.snapshot import (
    SNAPSHOT_VERSION,
    _tracker_from_dict,
    dump_snapshot,
    load_snapshot,
    loads_snapshot,
    save_snapshot,
)
from routewatch.tracker import RouteTracker


@pytest.fixture()
def populated_tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.record("GET", "/users")
    t.record("GET", "/users")
    return t


def test_dump_snapshot_version(populated_tracker):
    data = dump_snapshot(populated_tracker)
    assert data["version"] == SNAPSHOT_VERSION


def test_dump_snapshot_has_created_at(populated_tracker):
    before = time.time()
    data = dump_snapshot(populated_tracker)
    after = time.time()
    assert before <= data["created_at"] <= after


def test_dump_snapshot_route_count(populated_tracker):
    data = dump_snapshot(populated_tracker)
    assert len(data["routes"]) == 2


def test_dump_snapshot_hit_counts(populated_tracker):
    data = dump_snapshot(populated_tracker)
    by_key = {(r["method"], r["path"]): r for r in data["routes"]}
    assert by_key[("GET", "/users")]["count"] == 2
    assert by_key[("POST", "/users")]["count"] == 0


def test_roundtrip_via_string(populated_tracker):
    raw = json.dumps(dump_snapshot(populated_tracker))
    restored = loads_snapshot(raw)
    assert restored.coverage_percent() == populated_tracker.coverage_percent()
    hit = restored._routes[restored._key("GET", "/users")]
    assert hit.count == 2


def test_save_and_load_snapshot(populated_tracker):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
        path = fh.name
    try:
        save_snapshot(populated_tracker, path)
        assert os.path.exists(path)
        restored = load_snapshot(path)
        assert len(restored._routes) == 2
        hit = restored._routes[restored._key("POST", "/users")]
        assert hit.count == 0
    finally:
        os.unlink(path)


def test_unsupported_version_raises():
    bad_data = {"version": 99, "routes": []}
    with pytest.raises(ValueError, match="Unsupported snapshot version"):
        _tracker_from_dict(bad_data)


def test_empty_snapshot_roundtrip():
    t = RouteTracker()
    raw = json.dumps(dump_snapshot(t))
    restored = loads_snapshot(raw)
    assert len(restored._routes) == 0
