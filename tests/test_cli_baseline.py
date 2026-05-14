"""Tests for routewatch.cli_baseline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from routewatch.cli_baseline import _build_parser, main
from routewatch.snapshot import dump_snapshot
from routewatch.tracker import RouteTracker


def _make_snapshot(tmp_path: Path, hit_get: bool = True) -> Path:
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    if hit_get:
        t.record("GET", "/users")
    data = dump_snapshot(t)
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(data))
    return p


@pytest.fixture()
def snapshot_path(tmp_path):
    return _make_snapshot(tmp_path)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_parser_save_command():
    parser = _build_parser()
    args = parser.parse_args(["save", "snap.json", "base.json"])
    assert args.command == "save"
    assert args.snapshot == "snap.json"
    assert args.baseline == "base.json"


def test_parser_compare_command():
    parser = _build_parser()
    args = parser.parse_args(["compare", "snap.json", "base.json"])
    assert args.command == "compare"
    assert args.fail_on_regression is False


def test_parser_compare_fail_on_regression_flag():
    parser = _build_parser()
    args = parser.parse_args(["compare", "snap.json", "base.json", "--fail-on-regression"])
    assert args.fail_on_regression is True


# ---------------------------------------------------------------------------
# main() — save
# ---------------------------------------------------------------------------

def test_main_save_creates_baseline(tmp_path, snapshot_path, capsys):
    baseline_path = tmp_path / "baseline.json"
    main(["save", str(snapshot_path), str(baseline_path)])
    assert baseline_path.exists()
    data = json.loads(baseline_path.read_text())
    assert "routes" in data


def test_main_save_prints_confirmation(tmp_path, snapshot_path, capsys):
    baseline_path = tmp_path / "baseline.json"
    main(["save", str(snapshot_path), str(baseline_path)])
    captured = capsys.readouterr()
    assert "Baseline saved" in captured.out


# ---------------------------------------------------------------------------
# main() — compare
# ---------------------------------------------------------------------------

def _write_baseline(tmp_path: Path, routes: dict) -> Path:
    p = tmp_path / "baseline.json"
    p.write_text(json.dumps({"version": 1, "routes": routes}))
    return p


def test_main_compare_prints_report(tmp_path, snapshot_path, capsys):
    baseline_path = _write_baseline(tmp_path, {
        "GET /users": {"hits": 3, "covered": True},
    })
    main(["compare", str(snapshot_path), str(baseline_path)])
    captured = capsys.readouterr()
    assert "Baseline Comparison" in captured.out


def test_main_compare_no_regression_exits_zero(tmp_path, snapshot_path):
    baseline_path = _write_baseline(tmp_path, {
        "GET /users": {"hits": 1, "covered": True},
    })
    # Should not raise SystemExit
    main(["compare", str(snapshot_path), str(baseline_path), "--fail-on-regression"])


def test_main_compare_regression_exits_one(tmp_path, tmp_path_factory, capsys):
    # Snapshot where GET /users has NO hits
    snap_path = _make_snapshot(tmp_path, hit_get=False)
    baseline_path = _write_baseline(tmp_path, {
        "GET /users": {"hits": 5, "covered": True},
    })
    with pytest.raises(SystemExit) as exc_info:
        main(["compare", str(snap_path), str(baseline_path), "--fail-on-regression"])
    assert exc_info.value.code == 1
