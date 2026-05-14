"""Tests for routewatch.cli_sampling."""

import json
import os
import tempfile

import pytest

from routewatch.cli_sampling import _build_parser, main
from routewatch.snapshot import save_snapshot
from routewatch.tracker import RouteTracker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snapshot(tracker: RouteTracker) -> str:
    """Save tracker to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    save_snapshot(tracker, path)
    return path


@pytest.fixture()
def snapshot_path():
    t = RouteTracker()
    t.register("GET", "/items")
    t.register("POST", "/items")
    t.register("GET", "/users")
    for _ in range(8):
        t.record("GET", "/items")
    for _ in range(2):
        t.record("POST", "/items")
    path = _make_snapshot(t)
    yield path
    os.unlink(path)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_parser_defaults():
    parser = _build_parser()
    args = parser.parse_args(["snap.json"])
    assert args.rate == 1.0
    assert args.min_hits == 0


def test_parser_custom_rate():
    parser = _build_parser()
    args = parser.parse_args(["snap.json", "--rate", "0.25"])
    assert args.rate == pytest.approx(0.25)


def test_parser_min_hits():
    parser = _build_parser()
    args = parser.parse_args(["snap.json", "--min-hits", "5"])
    assert args.min_hits == 5


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def test_main_returns_zero_on_success(snapshot_path, capsys):
    rc = main([snapshot_path])
    assert rc == 0


def test_main_output_contains_route(snapshot_path, capsys):
    main([snapshot_path])
    out = capsys.readouterr().out
    assert "GET /items" in out or "GET:/items" in out or "/items" in out


def test_main_invalid_rate_returns_2(snapshot_path):
    rc = main([snapshot_path, "--rate", "1.5"])
    assert rc == 2


def test_main_zero_rate_returns_2(snapshot_path):
    rc = main([snapshot_path, "--rate", "0.0"])
    assert rc == 2


def test_main_missing_file_returns_1():
    rc = main(["nonexistent_file.json"])
    assert rc == 1


def test_main_min_hits_filters_routes(snapshot_path, capsys):
    main([snapshot_path, "--min-hits", "5"])
    out = capsys.readouterr().out
    # POST /items has only 2 hits and should be filtered out
    assert "POST" not in out


def test_main_half_rate_doubles_estimates(snapshot_path, capsys):
    main([snapshot_path, "--rate", "0.5"])
    out = capsys.readouterr().out
    # GET /items has 8 raw hits → 16.0 estimated
    assert "16.0" in out
