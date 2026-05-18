"""Tests for routewatch.cli_correlations."""
import json
import os
import tempfile

import pytest

from routewatch.cli_correlations import _build_parser, main
from routewatch.correlations import clear_correlations
from routewatch.snapshot import save_snapshot
from routewatch.tracker import RouteTracker


@pytest.fixture(autouse=True)
def clean_corr():
    clear_correlations()
    yield
    clear_correlations()


def _make_snapshot(routes: dict[str, int]) -> str:
    """Write a minimal snapshot and return its path."""
    tracker = RouteTracker()
    for spec, hits in routes.items():
        method, path = spec.split(" ", 1)
        tracker.register(method, path)
        for _ in range(hits):
            tracker.record(method, path)
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    save_snapshot(tracker, path)
    return path


@pytest.fixture()
def snapshot_path():
    path = _make_snapshot({"GET /a": 3, "GET /b": 2, "POST /c": 1})
    yield path
    os.unlink(path)


def test_parser_snapshot_positional():
    parser = _build_parser()
    args = parser.parse_args(["snap.json"])
    assert args.snapshot == "snap.json"


def test_parser_top_default():
    parser = _build_parser()
    args = parser.parse_args(["snap.json"])
    assert args.top == 10


def test_parser_top_custom():
    parser = _build_parser()
    args = parser.parse_args(["snap.json", "--top", "5"])
    assert args.top == 5


def test_parser_min_count_default():
    parser = _build_parser()
    args = parser.parse_args(["snap.json"])
    assert args.min_count == 1


def test_parser_route_flag():
    parser = _build_parser()
    args = parser.parse_args(["snap.json", "--route", "GET /users"])
    assert args.route == "GET /users"


def test_main_missing_snapshot_returns_1():
    rc = main(["nonexistent_file.json"])
    assert rc == 1


def test_main_runs_without_error(snapshot_path):
    rc = main([snapshot_path])
    assert rc == 0


def test_main_with_top_flag(snapshot_path):
    rc = main([snapshot_path, "--top", "3"])
    assert rc == 0


def test_main_with_invalid_route_flag_returns_1(snapshot_path):
    rc = main([snapshot_path, "--route", "BADFORMAT"])
    assert rc == 1


def test_main_with_valid_route_flag(snapshot_path):
    rc = main([snapshot_path, "--route", "GET /a"])
    assert rc == 0
