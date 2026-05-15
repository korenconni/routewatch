"""Tests for routewatch.webhooks."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

import routewatch.webhooks as wh
from routewatch.webhooks import (
    WebhookConfig,
    WebhookDelivery,
    clear_webhooks,
    fire_event,
    get_webhooks,
    register_webhook,
    unregister_webhook,
    EVENT_COVERAGE_DROP,
    EVENT_NEW_ROUTE,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_webhooks()
    yield
    clear_webhooks()


def test_webhook_config_is_dataclass():
    cfg = WebhookConfig(url="http://example.com", event=EVENT_NEW_ROUTE)
    assert cfg.url == "http://example.com"
    assert cfg.event == EVENT_NEW_ROUTE


def test_webhook_config_key_format():
    cfg = WebhookConfig(url="http://x.io", event=EVENT_COVERAGE_DROP)
    assert cfg.key == f"{EVENT_COVERAGE_DROP}::http://x.io"


def test_register_webhook_returns_config():
    cfg = register_webhook("http://hook.io", EVENT_NEW_ROUTE)
    assert isinstance(cfg, WebhookConfig)
    assert cfg.url == "http://hook.io"


def test_register_webhook_is_idempotent():
    register_webhook("http://hook.io", EVENT_NEW_ROUTE)
    register_webhook("http://hook.io", EVENT_NEW_ROUTE)
    assert len(get_webhooks(EVENT_NEW_ROUTE)) == 1


def test_register_multiple_urls_same_event():
    register_webhook("http://a.io", EVENT_NEW_ROUTE)
    register_webhook("http://b.io", EVENT_NEW_ROUTE)
    assert len(get_webhooks(EVENT_NEW_ROUTE)) == 2


def test_get_webhooks_unknown_event_returns_empty():
    assert get_webhooks("unknown_event") == []


def test_unregister_webhook_returns_true_when_present():
    register_webhook("http://hook.io", EVENT_NEW_ROUTE)
    result = unregister_webhook("http://hook.io", EVENT_NEW_ROUTE)
    assert result is True
    assert get_webhooks(EVENT_NEW_ROUTE) == []


def test_unregister_webhook_returns_false_when_absent():
    result = unregister_webhook("http://missing.io", EVENT_NEW_ROUTE)
    assert result is False


def test_webhook_delivery_success_flag():
    d = WebhookDelivery(url="http://x.io", event=EVENT_NEW_ROUTE, payload={}, status_code=200)
    assert d.success is True


def test_webhook_delivery_failure_flag():
    d = WebhookDelivery(url="http://x.io", event=EVENT_NEW_ROUTE, payload={}, status_code=500)
    assert d.success is False


def test_webhook_delivery_no_status_is_failure():
    d = WebhookDelivery(url="http://x.io", event=EVENT_NEW_ROUTE, payload={}, error="timeout")
    assert d.success is False


def _fake_urlopen(req, timeout):
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.status = 200
    return mock


def test_fire_event_calls_registered_hooks():
    register_webhook("http://hook.io", EVENT_NEW_ROUTE)
    with patch("urllib.request.urlopen", side_effect=_fake_urlopen):
        deliveries = fire_event(EVENT_NEW_ROUTE, {"route": "GET /foo"})
    assert len(deliveries) == 1
    assert deliveries[0].success is True


def test_fire_event_no_hooks_returns_empty():
    deliveries = fire_event(EVENT_NEW_ROUTE, {})
    assert deliveries == []


def test_fire_event_network_error_captured():
    register_webhook("http://bad.io", EVENT_COVERAGE_DROP)
    with patch("urllib.request.urlopen", side_effect=OSError("unreachable")):
        deliveries = fire_event(EVENT_COVERAGE_DROP, {})
    assert len(deliveries) == 1
    assert deliveries[0].success is False
    assert "unreachable" in deliveries[0].error


def test_fire_event_sends_secret_header():
    register_webhook("http://secure.io", EVENT_NEW_ROUTE, secret="s3cr3t")
    captured = {}

    def fake_open(req, timeout):
        captured["headers"] = dict(req.headers)
        return _fake_urlopen(req, timeout)

    with patch("urllib.request.urlopen", side_effect=fake_open):
        fire_event(EVENT_NEW_ROUTE, {})

    assert captured["headers"].get("X-routewatch-secret") == "s3cr3t"
