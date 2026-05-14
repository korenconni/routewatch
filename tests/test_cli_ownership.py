"""Tests for routewatch.cli_ownership."""
import json
import tempfile
import os
import pytest

from routewatch.tracker import RouteTracker
from routewatch.snapshot import dump_snapshot
from routewatch.ownership import _store, assign_owner
from routewatch.cli_ownership import _build_parser, main


@pytest.fixture(autouse=True)
def clear_store():
    _store.clear()
    yield
    _store.clear()


@pytest.fixture()
def snapshot_path(tmp_path):
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/health")
    data = dump_snapshot(t)
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_parser_report_command(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([snapshot_path, "report"])
    assert args.command == "report"
    assert args.fail_on_unowned is False


def test_parser_report_fail_on_unowned_flag(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([snapshot_path, "report", "--fail-on-unowned"])
    assert args.fail_on_unowned is True


def test_parser_team_command(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([snapshot_path, "team", "backend"])
    assert args.command == "team"
    assert args.team == "backend"


def test_parser_unowned_command(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([snapshot_path, "unowned"])
    assert args.command == "unowned"


def test_main_report_exits_zero(snapshot_path, capsys):
    code = main([snapshot_path, "report"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Route Ownership Report" in out


def test_main_report_fail_on_unowned_exits_one(snapshot_path):
    code = main([snapshot_path, "report", "--fail-on-unowned"])
    assert code == 1


def test_main_report_fail_on_unowned_exits_zero_when_all_owned(snapshot_path):
    from routewatch.snapshot import load_snapshot
    tracker = load_snapshot(snapshot_path)
    assign_owner(tracker, "GET", "/users", team="a")
    assign_owner(tracker, "POST", "/users", team="a")
    assign_owner(tracker, "GET", "/health", team="b")
    code = main([snapshot_path, "report", "--fail-on-unowned"])
    assert code == 0


def test_main_team_no_routes(snapshot_path, capsys):
    code = main([snapshot_path, "team", "ghost"])
    assert code == 0
    out = capsys.readouterr().out
    assert "No routes found" in out


def test_main_unowned_lists_routes(snapshot_path, capsys):
    code = main([snapshot_path, "unowned"])
    assert code == 0
    out = capsys.readouterr().out
    assert "unowned" in out.lower()


def test_main_unowned_all_owned_message(snapshot_path, capsys):
    from routewatch.snapshot import load_snapshot
    tracker = load_snapshot(snapshot_path)
    assign_owner(tracker, "GET", "/users", team="a")
    assign_owner(tracker, "POST", "/users", team="a")
    assign_owner(tracker, "GET", "/health", team="b")
    code = main([snapshot_path, "unowned"])
    assert code == 0
    out = capsys.readouterr().out
    assert "All routes have owners" in out
