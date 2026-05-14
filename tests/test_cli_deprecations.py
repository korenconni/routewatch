"""Tests for routewatch.cli_deprecations."""
import json
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from routewatch.tracker import RouteTracker
from routewatch import deprecations
from routewatch.deprecations import deprecate_route
from routewatch.snapshot import save_snapshot
from routewatch.cli_deprecations import _build_parser, main


@pytest.fixture(autouse=True)
def clear_store():
    deprecations._store.clear()
    yield
    deprecations._store.clear()


def _make_snapshot(tracker: RouteTracker) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    save_snapshot(tracker, tmp.name)
    return Path(tmp.name)


@pytest.fixture
def snapshot_path():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("DELETE", "/users/{id}")
    from routewatch.tracker import record
    record(t, "GET", "/users")
    return _make_snapshot(t)


def test_parser_report_command(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([str(snapshot_path), "report"])
    assert args.command == "report"
    assert args.fail_on_hits is False


def test_parser_report_fail_on_hits_flag(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([str(snapshot_path), "report", "--fail-on-hits"])
    assert args.fail_on_hits is True


def test_parser_mark_command(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args(
        [str(snapshot_path), "mark", "GET", "/old", "--reason", "removed"]
    )
    assert args.command == "mark"
    assert args.method == "GET"
    assert args.path == "/old"
    assert args.reason == "removed"


def test_main_report_no_deprecated(snapshot_path, capsys):
    rc = main([str(snapshot_path), "report"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No deprecated routes" in out


def test_main_report_with_deprecated(snapshot_path, capsys):
    from routewatch.snapshot import load_snapshot
    t = load_snapshot(str(snapshot_path))
    deprecate_route(t, "GET", "/users", reason="Use /members")
    rc = main([str(snapshot_path), "report"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "GET:/users" in out


def test_main_mark_prints_info(snapshot_path, capsys):
    rc = main(
        [str(snapshot_path), "mark", "GET", "/users", "--reason", "legacy"]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "GET:/users" in out
    assert "legacy" in out


def test_main_mark_with_sunset(snapshot_path, capsys):
    rc = main(
        [
            str(snapshot_path),
            "mark", "GET", "/users",
            "--reason", "old",
            "--sunset", "2025-12-31",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "2025-12-31" in out


def test_main_mark_with_replacement(snapshot_path, capsys):
    rc = main(
        [
            str(snapshot_path),
            "mark", "DELETE", "/users/{id}",
            "--reason", "old",
            "--replacement", "/members/{id}",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "/members/{id}" in out
