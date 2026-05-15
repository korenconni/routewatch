"""Webhook notifications for RouteWatch events."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from routewatch.tracker import RouteTracker

_hooks: Dict[str, List["WebhookConfig"]] = {}

EVENT_COVERAGE_DROP = "coverage_drop"
EVENT_NEW_ROUTE = "new_route"
EVENT_ROUTE_UNCOVERED = "route_uncovered"


@dataclass
class WebhookConfig:
    url: str
    event: str
    secret: Optional[str] = None
    timeout: int = 5

    @property
    def key(self) -> str:
        return f"{self.event}::{self.url}"


@dataclass
class WebhookDelivery:
    url: str
    event: str
    payload: dict
    status_code: Optional[int] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.status_code is not None and 200 <= self.status_code < 300


def register_webhook(url: str, event: str, secret: Optional[str] = None, timeout: int = 5) -> WebhookConfig:
    """Register a webhook URL for a given event type."""
    cfg = WebhookConfig(url=url, event=event, secret=secret, timeout=timeout)
    _hooks.setdefault(event, [])
    if not any(h.key == cfg.key for h in _hooks[event]):
        _hooks[event].append(cfg)
    return cfg


def unregister_webhook(url: str, event: str) -> bool:
    """Remove a webhook. Returns True if it was present."""
    before = len(_hooks.get(event, []))
    _hooks[event] = [h for h in _hooks.get(event, []) if h.url != url]
    return len(_hooks.get(event, [])) < before


def get_webhooks(event: str) -> List[WebhookConfig]:
    """Return all registered webhooks for an event."""
    return list(_hooks.get(event, []))


def _send(cfg: WebhookConfig, payload: dict) -> WebhookDelivery:
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if cfg.secret:
        headers["X-RouteWatch-Secret"] = cfg.secret
    req = urllib.request.Request(cfg.url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout) as resp:
            return WebhookDelivery(url=cfg.url, event=cfg.event, payload=payload, status_code=resp.status)
    except urllib.error.HTTPError as exc:
        return WebhookDelivery(url=cfg.url, event=cfg.event, payload=payload, status_code=exc.code, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return WebhookDelivery(url=cfg.url, event=cfg.event, payload=payload, error=str(exc))


def fire_event(event: str, payload: dict) -> List[WebhookDelivery]:
    """Dispatch payload to all hooks registered for *event*."""
    return [_send(cfg, payload) for cfg in get_webhooks(event)]


def clear_webhooks() -> None:
    """Remove all registered webhooks (useful in tests)."""
    _hooks.clear()
