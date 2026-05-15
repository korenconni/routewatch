"""Tests for routewatch.cli_sla."""
import json
import tempfile
import os
import pytest

from routewatch.tracker import RouteTracker
from routewatch.snapshot import dump_snapshot
from routewatch.sla import _store
from routewatch.cli_sla import _build_parser, main


@pytest.fixture(autouse=True)
def clear_sla_store():
    _store.clear()
    yield
    _store.clear()


def _make_snapshot(hit_map: dict) -> str:
    t = RouteTracker()
    for (method, path), hits in hit_map.items():
        t.register(method, path)
        for _ in range(hits):
            from routewatch.tracker import record
            record(t, method, path)
    data = dump_snapshot(t)
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    json.dump(data, tmp)
    tmp.close()
    return tmp.name


@pytest.fixture
def snapshot_path():
    path = _make_snapshot({("GET", "/users"): 5, ("POST", "/users"): 0})
    yield path
    os.unlink(path)


def test_parser_snapshot_positional():
    parser = _build_parser()
    args = parser.parse_args(["snap.json"])
    assert args.snapshot == "snap.json"


def test_parser_sla_flag():
    parser = _build_parser()
    args = parser.parse_args(["snap.json", "--sla", "GET:/users:3"])
    assert args.sla == ["GET:/users:3"]


def test_parser_multiple_sla_flags():
    parser = _build_parser()
    args = parser.parse_args(["snap.json", "--sla", "GET:/a:1", "--sla", "POST:/b:2"])
    assert len(args.sla) == 2


def test_parser_fail_on_violation_default():
    parser = _build_parser()
    args = parser.parse_args(["snap.json"])
    assert args.fail_on_violation is False


def test_parser_fail_on_violation_flag():
    parser = _build_parser()
    args = parser.parse_args(["snap.json", "--fail-on-violation"])
    assert args.fail_on_violation is True


def test_main_returns_zero_no_violations(snapshot_path, capsys):
    rc = main([snapshot_path, "--sla", "GET:/users:3"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "OK" in out


def test_main_returns_zero_without_fail_flag(snapshot_path):
    rc = main([snapshot_path, "--sla", "POST:/users:999"])
    assert rc == 0


def test_main_returns_one_with_fail_flag(snapshot_path):
    rc = main([snapshot_path, "--sla", "POST:/users:999", "--fail-on-violation"])
    assert rc == 1


def test_main_invalid_snapshot_returns_two(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{\"not\": \"valid\"}")
    rc = main([str(bad)])
    assert rc == 2


def test_main_invalid_sla_spec(snapshot_path):
    rc = main([snapshot_path, "--sla", "BADSPEC"])
    assert rc == 2


def test_main_non_integer_min_hits(snapshot_path):
    rc = main([snapshot_path, "--sla", "GET:/users:abc"])
    assert rc == 2


def test_main_output_contains_route(snapshot_path, capsys):
    main([snapshot_path, "--sla", "GET:/users:1"])
    out = capsys.readouterr().out
    assert "/users" in out
