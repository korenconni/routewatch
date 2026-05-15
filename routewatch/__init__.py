"""RouteWatch — Lightweight HTTP route coverage tracker."""
from routewatch.tracker import RouteTracker, RouteHit, record
from routewatch.report import build_summary, coverage_percent, missing_routes, text_report
from routewatch.snapshot import dump_snapshot, save_snapshot, load_snapshot, loads_snapshot
from routewatch.exporter import export_json, export_csv, save_export
from routewatch.alerts import check_coverage_alert, on_alert
from routewatch.reset import reset_tracker, unregister_route, prune_uncovered, prune_below
from routewatch.diff import diff_trackers, diff_report
from routewatch.tags import tag_route, get_tags, routes_by_tag, filter_by_tag, remove_tag
from routewatch.history import RouteHistory
from routewatch.scoring import score_route, build_scores, average_score
from routewatch.grouping import group_by_prefix, group_coverage
from routewatch.heatmap import build_heatmap, heatmap_report
from routewatch.sampling import SamplingConfig, sampled_record
from routewatch.baseline import save_baseline, load_baseline, compare_to_baseline
from routewatch.throttle import ThrottleConfig, RouteThrottle
from routewatch.decay import DecayConfig, apply_decay
from routewatch.pinning import pin_route, unpin_route, check_pins
from routewatch.budgets import set_budget, check_budgets
from routewatch.labels import set_label, get_label, get_labels
from routewatch.annotations import annotate, get_annotation, get_annotations
from routewatch.deprecations import deprecate_route, undeprecate_route, get_deprecation
from routewatch.ownership import assign_owner, get_owner, ownership_report
from routewatch.retention import RetentionPolicy, check_retention
from routewatch.sla import set_sla, get_sla, remove_sla, check_sla, sla_text_report

__all__ = [
    "RouteTracker", "RouteHit", "record",
    "build_summary", "coverage_percent", "missing_routes", "text_report",
    "dump_snapshot", "save_snapshot", "load_snapshot", "loads_snapshot",
    "export_json", "export_csv", "save_export",
    "check_coverage_alert", "on_alert",
    "reset_tracker", "unregister_route", "prune_uncovered", "prune_below",
    "diff_trackers", "diff_report",
    "tag_route", "get_tags", "routes_by_tag", "filter_by_tag", "remove_tag",
    "RouteHistory",
    "score_route", "build_scores", "average_score",
    "group_by_prefix", "group_coverage",
    "build_heatmap", "heatmap_report",
    "SamplingConfig", "sampled_record",
    "save_baseline", "load_baseline", "compare_to_baseline",
    "ThrottleConfig", "RouteThrottle",
    "DecayConfig", "apply_decay",
    "pin_route", "unpin_route", "check_pins",
    "set_budget", "check_budgets",
    "set_label", "get_label", "get_labels",
    "annotate", "get_annotation", "get_annotations",
    "deprecate_route", "undeprecate_route", "get_deprecation",
    "assign_owner", "get_owner", "ownership_report",
    "RetentionPolicy", "check_retention",
    "set_sla", "get_sla", "remove_sla", "check_sla", "sla_text_report",
]
