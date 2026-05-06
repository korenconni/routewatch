"""Tests for routewatch.integrations — Flask and FastAPI attach helpers."""

from __future__ import annotations

import io
import pytest

from routewatch.tracker import RouteTracker
from routewatch.middleware import RouteWatchMiddleware
from routewatch.integrations import attach_to_flask, attach_to_fastapi


# ---------------------------------------------------------------------------
# Minimal Flask-like stub
# ---------------------------------------------------------------------------

class FakeRule:
    def __init__(self, rule: str, methods):
        self.rule = rule
        self.methods = methods


class FakeUrlMap:
    def __init__(self, rules):
        self._rules = rules

    def iter_rules(self):
        return iter(self._rules)


class FakeFlaskApp:
    """Minimal object that looks like a Flask app to attach_to_flask."""

    def __init__(self):
        self.url_map = FakeUrlMap([
            FakeRule("/", {"GET", "HEAD", "OPTIONS"}),
            FakeRule("/users", {"GET", "POST"}),
            FakeRule("/users/<int:user_id>", {"GET", "PUT", "DELETE"}),
        ])
        self.wsgi_app = self._bare_wsgi

    def _bare_wsgi(self, environ, start_response):
        start_response("200 OK", [])
        return [b"ok"]


# ---------------------------------------------------------------------------
# Minimal FastAPI-like stub
# ---------------------------------------------------------------------------

class FakeRoute:
    def __init__(self, path: str, methods):
        self.path = path
        self.methods = methods


class FakeFastAPIApp:
    """Minimal object that looks like a FastAPI app to attach_to_fastapi."""

    def __init__(self):
        self.routes = [
            FakeRoute("/items", {"GET"}),
            FakeRoute("/items/{item_id}", {"GET", "PUT", "DELETE"}),
        ]
        self._middlewares = []

    def add_middleware(self, cls, **kwargs):
        self._middlewares.append((cls, kwargs))


# ---------------------------------------------------------------------------
# Flask integration tests
# ---------------------------------------------------------------------------

def test_attach_to_flask_returns_tracker():
    flask_app = FakeFlaskApp()
    tracker = attach_to_flask(flask_app)
    assert isinstance(tracker, RouteTracker)


def test_attach_to_flask_wraps_wsgi():
    flask_app = FakeFlaskApp()
    attach_to_flask(flask_app)
    assert isinstance(flask_app.wsgi_app, RouteWatchMiddleware)


def test_attach_to_flask_registers_routes():
    flask_app = FakeFlaskApp()
    tracker = attach_to_flask(flask_app)
    # HEAD and OPTIONS should be skipped; GET + POST + PUT + DELETE expected
    keys = list(tracker._routes.keys())
    assert ("GET", "/") in keys
    assert ("GET", "/users") in keys
    assert ("POST", "/users") in keys


def test_attach_to_flask_skips_head_options():
    flask_app = FakeFlaskApp()
    tracker = attach_to_flask(flask_app)
    keys = list(tracker._routes.keys())
    assert ("HEAD", "/") not in keys
    assert ("OPTIONS", "/") not in keys


def test_attach_to_flask_accepts_existing_tracker():
    flask_app = FakeFlaskApp()
    existing = RouteTracker()
    returned = attach_to_flask(flask_app, tracker=existing)
    assert returned is existing


# ---------------------------------------------------------------------------
# FastAPI integration tests
# ---------------------------------------------------------------------------

def test_attach_to_fastapi_returns_tracker():
    fastapi_app = FakeFastAPIApp()
    tracker = attach_to_fastapi(fastapi_app)
    assert isinstance(tracker, RouteTracker)


def test_attach_to_fastapi_adds_middleware():
    fastapi_app = FakeFastAPIApp()
    attach_to_fastapi(fastapi_app)
    assert len(fastapi_app._middlewares) == 1
    cls, kwargs = fastapi_app._middlewares[0]
    assert cls is AsyncRouteWatchMiddleware


def test_attach_to_fastapi_registers_routes():
    fastapi_app = FakeFastAPIApp()
    tracker = attach_to_fastapi(fastapi_app)
    keys = list(tracker._routes.keys())
    assert ("GET", "/items") in keys
    assert ("PUT", "/items/{item_id}") in keys


def test_attach_to_fastapi_accepts_existing_tracker():
    fastapi_app = FakeFastAPIApp()
    existing = RouteTracker()
    returned = attach_to_fastapi(fastapi_app, tracker=existing)
    assert returned is existing
