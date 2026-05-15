"""CLI for managing RouteWatch webhooks and firing test events."""
from __future__ import annotations

import argparse
import sys

from routewatch.snapshot import load_snapshot
from routewatch.webhooks import (
    EVENT_COVERAGE_DROP,
    EVENT_NEW_ROUTE,
    EVENT_ROUTE_UNCOVERED,
    fire_event,
    get_webhooks,
    register_webhook,
    unregister_webhook,
)

_EVENTS = [EVENT_COVERAGE_DROP, EVENT_NEW_ROUTE, EVENT_ROUTE_UNCOVERED]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="routewatch-webhooks",
        description="Manage webhooks and fire test notifications.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # register
    reg = sub.add_parser("register", help="Register a webhook URL for an event.")
    reg.add_argument("url", help="Webhook endpoint URL")
    reg.add_argument("event", choices=_EVENTS, help="Event type to subscribe to")
    reg.add_argument("--secret", default=None, help="Optional shared secret")
    reg.add_argument("--timeout", type=int, default=5, help="Request timeout in seconds")

    # unregister
    unreg = sub.add_parser("unregister", help="Remove a registered webhook.")
    unreg.add_argument("url", help="Webhook endpoint URL")
    unreg.add_argument("event", choices=_EVENTS, help="Event type")

    # list
    lst = sub.add_parser("list", help="List registered webhooks for an event.")
    lst.add_argument("event", choices=_EVENTS, help="Event type")

    # fire
    fire = sub.add_parser("fire", help="Fire a test event against registered webhooks.")
    fire.add_argument("snapshot", help="Path to snapshot file (used to build payload)")
    fire.add_argument("event", choices=_EVENTS, help="Event type to fire")
    fire.add_argument("--url", default=None, help="Fire to a specific URL only")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "register":
        cfg = register_webhook(args.url, args.event, secret=args.secret, timeout=args.timeout)
        print(f"Registered: {cfg.key}")
        return 0

    if args.command == "unregister":
        removed = unregister_webhook(args.url, args.event)
        if removed:
            print(f"Removed webhook {args.url} for event {args.event}.")
        else:
            print(f"No webhook found for {args.url} / {args.event}.", file=sys.stderr)
        return 0 if removed else 1

    if args.command == "list":
        hooks = get_webhooks(args.event)
        if not hooks:
            print(f"No webhooks registered for '{args.event}'.")
        for h in hooks:
            secret_hint = " [secret]" if h.secret else ""
            print(f"  {h.url}{secret_hint} (timeout={h.timeout}s)")
        return 0

    if args.command == "fire":
        tracker = load_snapshot(args.snapshot)
        payload = {"event": args.event, "snapshot": args.snapshot,
                   "total_routes": len(tracker.routes)}
        targets = get_webhooks(args.event)
        if args.url:
            from routewatch.webhooks import WebhookConfig
            targets = [WebhookConfig(url=args.url, event=args.event)]
        if not targets:
            print("No webhooks to fire.", file=sys.stderr)
            return 1
        from routewatch.webhooks import _send
        results = [_send(t, payload) for t in targets]
        ok = all(r.success for r in results)
        for r in results:
            status = "OK" if r.success else f"FAIL({r.error or r.status_code})"
            print(f"  {r.url} -> {status}")
        return 0 if ok else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
