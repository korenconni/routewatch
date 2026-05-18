"""Tests for routewatch.cli_segments."""
import json
import pathlib
import pytest

from routewatch.tracker import RouteTracker
from routewatch.snapshot import dump_snapshot
from routewatch.cli_segments import _build_parser, main


def _make_snapshot(tmp_path: pathlib.Path, hits: dict | None = None) -> pathlib.Path:
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/items")
    if hits:
        for (method, path), count in hits.items():
            for _ in range(count):
                from routewatch.tracker import record
                record(t, method, path)
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(dump_snapshot(t)))
    return p


@pytest.fixture()
def snapshot_path(tmp_path):
    return _make_snapshot(tmp_path)


def test_parser_snapshot_positional(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([str(snapshot_path)])
    assert args.snapshot == str(snapshot_path)


def test_parser_depth_default(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([str(snapshot_path)])
    assert args.depth == 1


def test_parser_depth_custom(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([str(snapshot_path), "--depth", "3"])
    assert args.depth == 3


def test_parser_min_routes_default(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([str(snapshot_path)])
    assert args.min_routes == 0


def test_parser_fail_below_default(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([str(snapshot_path)])
    assert args.fail_below is None


def test_parser_fail_below_custom(snapshot_path):
    parser = _build_parser()
    args = parser.parse_args([str(snapshot_path), "--fail-below", "80"])
    assert args.fail_below == 80.0


def test_main_runs_without_error(snapshot_path, capsys):
    main([str(snapshot_path)])
    out = capsys.readouterr().out
    assert "Segment Coverage Report" in out


def test_main_shows_segment_names(snapshot_path, capsys):
    main([str(snapshot_path)])
    out = capsys.readouterr().out
    assert "users" in out
    assert "items" in out


def test_main_empty_snapshot(tmp_path, capsys):
    t = RouteTracker()
    p = tmp_path / "empty.json"
    p.write_text(json.dumps(dump_snapshot(t)))
    main([str(p)])
    out = capsys.readouterr().out
    assert "No routes" in out


def test_main_fail_below_exits_1(tmp_path):
    snap = _make_snapshot(tmp_path)  # zero hits => 0% coverage
    with pytest.raises(SystemExit) as exc_info:
        main([str(snap), "--fail-below", "50"])
    assert exc_info.value.code == 1


def test_main_fail_below_passes_when_covered(tmp_path):
    from routewatch.tracker import record
    snap = _make_snapshot(
        tmp_path,
        hits={("GET", "/users"): 1, ("POST", "/users"): 1, ("GET", "/items"): 1},
    )
    # Should not raise — all routes hit => 100% coverage
    main([str(snap), "--fail-below", "50"])


def test_main_min_routes_filters(snapshot_path, capsys):
    # items has 1 route; users has 2 — with min-routes=2 only users should appear
    main([str(snapshot_path), "--min-routes", "2"])
    out = capsys.readouterr().out
    assert "users" in out
    assert "items" not in out
