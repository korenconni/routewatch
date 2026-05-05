"""WSGI/ASGI middleware for automatic route hit recording."""

from __future__ import annotations

from typing import Callable, Optional

from routewatch.tracker import RouteTracker


class RouteWatchMiddleware:
    """WSGI middleware that records route hits into a RouteTracker.

    Works with Flask (and any WSGI-compatible framework).

    Example::

        from flask import Flask
        from routewatch.middleware import RouteWatchMiddleware
        from routewatch.tracker import RouteTracker

        app = Flask(__name__)
        tracker = RouteTracker()
        app.wsgi_app = RouteWatchMiddleware(app.wsgi_app, tracker)
    """

    def __init__(self, app: Callable, tracker: RouteTracker) -> None:
        self.app = app
        self.tracker = tracker

    def __call__(self, environ: dict, start_response: Callable) -> object:
        method: str = environ.get("REQUEST_METHOD", "GET").upper()
        path: str = environ.get("PATH_INFO", "/")
        self.tracker.record(path, method)
        return self.app(environ, start_response)


class AsyncRouteWatchMiddleware:
    """ASGI middleware that records route hits into a RouteTracker.

    Works with FastAPI / Starlette.

    Example::

        from fastapi import FastAPI
        from routewatch.middleware import AsyncRouteWatchMiddleware
        from routewatch.tracker import RouteTracker

        app = FastAPI()
        tracker = RouteTracker()
        app.add_middleware(AsyncRouteWatchMiddleware, tracker=tracker)
    """

    def __init__(self, app: Callable, tracker: Optional[RouteTracker] = None) -> None:
        self.app = app
        self.tracker = tracker or RouteTracker()

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope.get("type") == "http":
            method: str = scope.get("method", "GET").upper()
            path: str = scope.get("path", "/")
            self.tracker.record(path, method)
        await self.app(scope, receive, send)
