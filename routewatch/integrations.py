"""Framework integrations: attach RouteWatch tracking to Flask or FastAPI apps."""

from __future__ import annotations

from typing import TYPE_CHECKING

from routewatch.tracker import RouteTracker
from routewatch.sampling import SamplingConfig, sampled_record

if TYPE_CHECKING:  # pragma: no cover
    pass


def attach_to_flask(
    app,
    tracker: RouteTracker,
    sampling: SamplingConfig | None = None,
) -> None:
    """Register all URL rules from a Flask app and wire up before/after hooks.

    Parameters
    ----------
    app:
        A Flask application instance.
    tracker:
        The :class:`RouteTracker` that will receive hit recordings.
    sampling:
        Optional :class:`SamplingConfig`.  When *None* every hit is recorded.
    """
    cfg = sampling or SamplingConfig(rate=1.0)

    # Pre-register all known routes so they appear in reports even before
    # they receive any traffic.
    for rule in app.url_map.iter_rules():
        for method in rule.methods or []:
            if method in ("HEAD", "OPTIONS"):
                continue
            tracker.register(method, rule.rule)

    @app.before_request
    def _routewatch_before():  # pragma: no cover
        pass

    @app.after_request
    def _routewatch_after(response):  # pragma: no cover
        from flask import request

        if request.url_rule is not None:
            sampled_record(tracker, request.method, request.url_rule.rule, cfg)
        return response


def attach_to_fastapi(
    app,
    tracker: RouteTracker,
    sampling: SamplingConfig | None = None,
) -> None:
    """Register all routes from a FastAPI app and add a middleware hook.

    Parameters
    ----------
    app:
        A FastAPI application instance.
    tracker:
        The :class:`RouteTracker` that will receive hit recordings.
    sampling:
        Optional :class:`SamplingConfig`.  When *None* every hit is recorded.
    """
    cfg = sampling or SamplingConfig(rate=1.0)

    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or []
        if path is None:
            continue
        for method in methods:
            tracker.register(method.upper(), path)

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class _SampledMiddleware(BaseHTTPMiddleware):  # pragma: no cover
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            scope_route = request.scope.get("route")
            if scope_route is not None:
                path = getattr(scope_route, "path", None)
                if path:
                    sampled_record(tracker, request.method, path, cfg)
            return response

    app.add_middleware(_SampledMiddleware)
