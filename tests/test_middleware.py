"""Tests for WSGI and ASGI middleware."""

from __future__ import annotations

import pytest

from routewatch.middleware import AsyncRouteWatchMiddleware, RouteWatchMiddleware
from routewatch.tracker import RouteTracker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_wsgi_app(status: str = "200 OK"):
    """Minimal WSGI app that returns a fixed status."""

    def app(environ, start_response):
        start_response(status, [("Content-Type", "text/plain")])
        return [b"ok"]

    return app


def make_environ(path: str = "/", method: str = "GET") -> dict:
    return {"REQUEST_METHOD": method, "PATH_INFO": path}


class FakeStartResponse:
    def __init__(self):
        self.status = None

    def __call__(self, status, headers):
        self.status = status


# ---------------------------------------------------------------------------
# WSGI middleware tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def wsgi_tracker():
    return RouteTracker()


def test_wsgi_records_hit(wsgi_tracker):
    middleware = RouteWatchMiddleware(make_wsgi_app(), wsgi_tracker)
    sr = FakeStartResponse()
    middleware(make_environ("/users", "GET"), sr)
    assert wsgi_tracker.hit_count("/users", "GET") == 1


def test_wsgi_passes_through_response(wsgi_tracker):
    middleware = RouteWatchMiddleware(make_wsgi_app("404 Not Found"), wsgi_tracker)
    sr = FakeStartResponse()
    result = middleware(make_environ("/missing", "GET"), sr)
    assert sr.status == "404 Not Found"
    assert result == [b"ok"]


def test_wsgi_multiple_hits(wsgi_tracker):
    middleware = RouteWatchMiddleware(make_wsgi_app(), wsgi_tracker)
    sr = FakeStartResponse()
    for _ in range(5):
        middleware(make_environ("/ping", "GET"), sr)
    assert wsgi_tracker.hit_count("/ping", "GET") == 5


# ---------------------------------------------------------------------------
# ASGI middleware tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def asgi_tracker():
    return RouteTracker()


async def fake_asgi_app(scope, receive, send):
    pass


@pytest.mark.asyncio
async def test_asgi_records_http_hit(asgi_tracker):
    middleware = AsyncRouteWatchMiddleware(fake_asgi_app, tracker=asgi_tracker)
    scope = {"type": "http", "method": "POST", "path": "/items"}
    await middleware(scope, None, None)
    assert asgi_tracker.hit_count("/items", "POST") == 1


@pytest.mark.asyncio
async def test_asgi_ignores_non_http_scope(asgi_tracker):
    middleware = AsyncRouteWatchMiddleware(fake_asgi_app, tracker=asgi_tracker)
    scope = {"type": "websocket", "path": "/ws"}
    await middleware(scope, None, None)
    assert asgi_tracker.hit_count("/ws", "GET") == 0


@pytest.mark.asyncio
async def test_asgi_creates_default_tracker():
    middleware = AsyncRouteWatchMiddleware(fake_asgi_app)
    scope = {"type": "http", "method": "GET", "path": "/health"}
    await middleware(scope, None, None)
    assert middleware.tracker.hit_count("/health", "GET") == 1
