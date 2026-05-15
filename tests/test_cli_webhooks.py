"""Tests for routewatch.cli_webhooks."""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

import routewatch.webhooks as wh
from routewatch.cli_webhooks import _build_parser, main
from routewatch.snapshot import dump_snapshot
from routewatch.tracker import RouteTracker


@pytest.fixture(autouse=True)
def _clean():
    wh.clear_webhooks()
    yield
    wh.clear_webhooks()


@pytest.fixture()
def snapshot_path(tmp_path):
    t = RouteTracker()
    t.register("GET", "/health")
    t.record("GET", "/health")
    data = dump_snapshot(t)
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_parser_register_command():
    p = _build_parser()
    args = p.parse_args(["register", "http://hook.io", "new_route"])
    assert args.command == "register"
    assert args.url == "http://hook.io"
    assert args.event == "new_route"


def test_parser_register_with_secret():
    p = _build_parser()
    args = p.parse_args(["register", "http://hook.io", "new_route", "--secret", "abc"])
    assert args.secret == "abc"


def test_parser_unregister_command():
    p = _build_parser()
    args = p.parse_args(["unregister", "http://hook.io", "coverage_drop"])
    assert args.command == "unregister"


def test_parser_list_command():
    p = _build_parser()
    args = p.parse_args(["list", "route_uncovered"])
    assert args.command == "list"
    assert args.event == "route_uncovered"


def test_parser_fire_command():
    p = _build_parser()
    args = p.parse_args(["fire", "snap.json", "new_route"])
    assert args.command == "fire"
    assert args.snapshot == "snap.json"


def test_main_register_exits_zero():
    rc = main(["register", "http://hook.io", "new_route"])
    assert rc == 0
    assert len(wh.get_webhooks("new_route")) == 1


def test_main_unregister_exits_zero_when_present():
    wh.register_webhook("http://hook.io", "new_route")
    rc = main(["unregister", "http://hook.io", "new_route"])
    assert rc == 0
    assert wh.get_webhooks("new_route") == []


def test_main_unregister_exits_one_when_absent():
    rc = main(["unregister", "http://missing.io", "new_route"])
    assert rc == 1


def test_main_list_no_hooks(capsys):
    rc = main(["list", "new_route"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No webhooks" in out


def test_main_list_shows_registered(capsys):
    wh.register_webhook("http://hook.io", "new_route", secret="s")
    main(["list", "new_route"])
    out = capsys.readouterr().out
    assert "http://hook.io" in out
    assert "[secret]" in out


def _fake_urlopen(req, timeout):
    m = MagicMock()
    m.__enter__ = lambda s: s
    m.__exit__ = MagicMock(return_value=False)
    m.status = 200
    return m


def test_main_fire_registered_hook(snapshot_path, capsys):
    wh.register_webhook("http://hook.io", "new_route")
    with patch("urllib.request.urlopen", side_effect=_fake_urlopen):
        rc = main(["fire", snapshot_path, "new_route"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "OK" in out


def test_main_fire_no_hooks_exits_one(snapshot_path):
    rc = main(["fire", snapshot_path, "new_route"])
    assert rc == 1


def test_main_fire_specific_url(snapshot_path, capsys):
    with patch("urllib.request.urlopen", side_effect=_fake_urlopen):
        rc = main(["fire", snapshot_path, "new_route", "--url", "http://custom.io"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "http://custom.io" in out
