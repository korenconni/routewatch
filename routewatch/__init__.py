"""routewatch — Lightweight HTTP route coverage tracker for FastAPI and Flask."""
from routewatch.tracker import RouteTracker, RouteHit
from routewatch.report import build_summary, coverage_percent, missing_routes, text_report
from routewatch.snapshot import dump_snapshot, save_snapshot, load_snapshot
from routewatch.exporter import export_json, export_csv
from routewatch.alerts import check_coverage_alert, on_alert
from routewatch.reset import reset_tracker, unregister_route, prune_uncovered, prune_below
from routewatch.diff import diff_trackers, diff_report
from routewatch.tags import tag_route, get_tags, routes_by_tag, filter_by_tag
from routewatch.history import RouteHistory
from routewatch.scoring import score_route, build_scores, average_score
from routewatch.grouping import group_by_prefix, group_coverage
from routewatch.heatmap import build_heatmap, heatmap_report
from routewatch.sampling import SamplingConfig, sampled_record
from routewatch.baseline import save_baseline, load_baseline, compare_to_baseline
from routewatch.throttle import ThrottleConfig, RouteThrottle
from routewatch.decay import DecayConfig, apply_decay
from routewatch.pinning import pin_route, unpin_route, check_pinned
from routewatch.budgets import BudgetReport, check_budgets
from routewatch.labels import set_label, get_label, get_labels
from routewatch.annotations import annotate, get_annotation, get_annotations
from routewatch.deprecations import deprecate_route, undeprecate_route, get_deprecation
from routewatch.ownership import assign_owner, get_owner, remove_owner
from routewatch.retention import RetentionPolicy, check_retention
from routewatch.sla import set_sla, check_sla
from routewatch.audit import record_audit, get_audit_log
from routewatch.muting import mute_route, unmute_route, is_muted
from routewatch.routing_patterns import match_glob, match_regex
from routewatch.notes import add_note, get_notes
from routewatch.webhooks import register_webhook, fire_webhooks
from routewatch.dependencies import add_dependency, remove_dependency, get_dependencies
from routewatch.timewindow import record_hit_time, hits_in_window, build_window_report
from routewatch.quotas import set_quota, remove_quota, get_quota, check_quotas

__all__ = [
    "RouteTracker", "RouteHit",
    "build_summary", "coverage_percent", "missing_routes", "text_report",
    "dump_snapshot", "save_snapshot", "load_snapshot",
    "export_json", "export_csv",
    "check_coverage_alert", "on_alert",
    "reset_tracker", "unregister_route", "prune_uncovered", "prune_below",
    "diff_trackers", "diff_report",
    "tag_route", "get_tags", "routes_by_tag", "filter_by_tag",
    "RouteHistory",
    "score_route", "build_scores", "average_score",
    "group_by_prefix", "group_coverage",
    "build_heatmap", "heatmap_report",
    "SamplingConfig", "sampled_record",
    "save_baseline", "load_baseline", "compare_to_baseline",
    "ThrottleConfig", "RouteThrottle",
    "DecayConfig", "apply_decay",
    "pin_route", "unpin_route", "check_pinned",
    "BudgetReport", "check_budgets",
    "set_label", "get_label", "get_labels",
    "annotate", "get_annotation", "get_annotations",
    "deprecate_route", "undeprecate_route", "get_deprecation",
    "assign_owner", "get_owner", "remove_owner",
    "RetentionPolicy", "check_retention",
    "set_sla", "check_sla",
    "record_audit", "get_audit_log",
    "mute_route", "unmute_route", "is_muted",
    "match_glob", "match_regex",
    "add_note", "get_notes",
    "register_webhook", "fire_webhooks",
    "add_dependency", "remove_dependency", "get_dependencies",
    "record_hit_time", "hits_in_window", "build_window_report",
    "set_quota", "remove_quota", "get_quota", "check_quotas",
]
