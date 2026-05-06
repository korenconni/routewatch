"""Framework integration helpers for RouteWatch.

Provides convenience functions to attach RouteWatch middleware
to FastAPI and Flask applications with minimal boilerplate.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from routewatch.tracker import RouteTracker
from routewatch.middleware import RouteWatchMiddleware, AsyncRouteWatchMiddleware

if TYPE_CHECKING:
    pass


def attach_to_flask(app, tracker: Optional[RouteTracker] = None) -> RouteTracker:
    """Wrap a Flask application with RouteWatchMiddleware.

    Args:
        app: A Flask application instance.
        tracker: An existing RouteTracker to use, or None to create a new one.

    Returns:
        The RouteTracker being used so callers can inspect it later.

    Example::

        from flask import Flask
        from routewatch.integrations import attach_to_flask

        flask_app = Flask(__name__)
        tracker = attach_to_flask(flask_app)
    """
    if tracker is None:
        tracker = RouteTracker()

    # Register all routes already defined on the Flask app.
    for rule in app.url_map.iter_rules():
        for method in rule.methods or []:
            if method in ("HEAD", "OPTIONS"):
                continue
            tracker.register(rule.rule, method)

    middleware = RouteWatchMiddleware(app.wsgi_app, tracker=tracker)
    app.wsgi_app = middleware  # type: ignore[assignment]
    return tracker


def attach_to_fastapi(app, tracker: Optional[RouteTracker] = None) -> RouteTracker:
    """Add AsyncRouteWatchMiddleware to a FastAPI application.

    Args:
        app: A FastAPI application instance.
        tracker: An existing RouteTracker to use, or None to create a new one.

    Returns:
        The RouteTracker being used so callers can inspect it later.

    Example::

        from fastapi import FastAPI
        from routewatch.integrations import attach_to_fastapi

        fastapi_app = FastAPI()
        tracker = attach_to_fastapi(fastapi_app)
    """
    if tracker is None:
        tracker = RouteTracker()

    # Register routes already declared on the FastAPI app.
    for route in getattr(app, "routes", []):
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or []
        if path is None:
            continue
        for method in methods:
            tracker.register(path, method)

    app.add_middleware(AsyncRouteWatchMiddleware, tracker=tracker)
    return tracker
