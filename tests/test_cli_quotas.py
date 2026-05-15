"""Tests for routewatch.cli_quotas."""
import json
import tempfile
import os
import pytest

from routewatch.tracker import RouteTracker
from routewatch.snapshot import save_snapshot
from routewatch.quotas import _store
from routewatch.cli_quotas import _build_parser, _parse_quota, main


@pytest.fixture(autouse=True)
def clear_quota_store():
    _store.clear()
    yield
    _store.clear()


@pytest.fixture()
def snapshot_path():
    t = RouteTracker()
    t.register("GET", "/items")
    t.register("POST", "/items")
    for _ in range(4):
        t.record("GET", "/items")
    t.record("POST", "/items")
    with tempfile.NamedTemporaryFile(
        suffix=".json", mode="w", delete=False
    ) as f:
        path = f.name
    save_snapshot(t, path)
    yield path
    os.unlink(path)


def test_parser_snapshot_positional():
    p = _build_parser()
    args = p.parse_args(["snap.json"])
    assert args.snapshot == "snap.json"


def test_parser_quota_flag():
    p = _build_parser()
    args = p.parse_args(["snap.json", "--quota", "GET:/items:1:10"])
    assert args.quotas == ["GET:/items:1:10")


def test_parser_fail_on_violation_flag():
    p = _build_parser()
    args = p.parse_args(["snap.json", "--fail-on-violation"])
    assert args.fail_on_violation is True


def test_parse_quota_without_max():
    method, path, min_hits, max_hits = _parse_quota("GET:/items:2")
    assert method == "GET"
    assert path == "/items"
    assert min_hits == 2
    assert max_hits is None


def test_parse_quota_with_max():
    method, path, min_hits, max_hits = _parse_quota("POST:/items:0:50")
    assert max_hits == 50


def test_main_no_quotas_prints_no_quotas(snapshot_path, capsys):
    rc = main([snapshot_path])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No quotas defined" in out


def test_main_within_quota_exit_zero(snapshot_path, capsys):
    rc = main([snapshot_path, "--quota", "GET:/items:1:10"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "OK" in out


def test_main_violation_no_flag_exit_zero(snapshot_path, capsys):
    rc = main([snapshot_path, "--quota", "GET:/items:100"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "VIOLATION" in out


def test_main_violation_with_flag_exit_one(snapshot_path):
    rc = main([snapshot_path, "--quota", "GET:/items:100", "--fail-on-violation"])
    assert rc == 1


def test_main_bad_snapshot_path(capsys):
    rc = main(["/nonexistent/path.json"])
    assert rc == 2
    assert "Error" in capsys.readouterr().err


def test_main_bad_quota_spec(snapshot_path, capsys):
    rc = main([snapshot_path, "--quota", "BADSPEC"])
    assert rc == 2
