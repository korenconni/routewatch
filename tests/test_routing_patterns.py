"""Tests for routewatch.routing_patterns."""
import pytest

from routewatch.tracker import RouteTracker
from routewatch.routing_patterns import (
    match_glob,
    match_regex,
    keys_for_pattern,
    PatternMatch,
)


@pytest.fixture()
def tracker() -> RouteTracker:
    rt = RouteTracker()
    for method, path in [
        ("GET", "/api/v1/users"),
        ("POST", "/api/v1/users"),
        ("GET", "/api/v1/orders"),
        ("GET", "/api/v2/users"),
        ("DELETE", "/admin/purge"),
        ("GET", "/health"),
    ]:
        rt.register(method, path)
    rt.record("GET", "/api/v1/users")
    rt.record("GET", "/api/v1/users")
    rt.record("GET", "/health")
    return rt


# --- PatternMatch dataclass ---

def test_pattern_match_key_is_uppercase(tracker):
    matches = match_glob(tracker, "/health")
    assert matches[0].key == "GET /health"


def test_pattern_match_hit_count(tracker):
    matches = match_glob(tracker, "/health")
    assert matches[0].hit_count == 1


# --- match_glob ---

def test_glob_wildcard_matches_multiple(tracker):
    matches = match_glob(tracker, "/api/v1/*")
    paths = {m.path for m in matches}
    assert paths == {"/api/v1/users", "/api/v1/orders"}


def test_glob_no_match_returns_empty(tracker):
    assert match_glob(tracker, "/nonexistent/*") == []


def test_glob_exact_match(tracker):
    matches = match_glob(tracker, "/health")
    assert len(matches) == 1
    assert matches[0].path == "/health"


def test_glob_method_filter_includes(tracker):
    matches = match_glob(tracker, "/api/v1/users", method="POST")
    assert len(matches) == 1
    assert matches[0].method == "POST"


def test_glob_method_filter_excludes(tracker):
    matches = match_glob(tracker, "/api/v1/users", method="DELETE")
    assert matches == []


def test_glob_method_filter_case_insensitive(tracker):
    matches = match_glob(tracker, "/api/v1/users", method="get")
    assert len(matches) == 1


def test_glob_double_wildcard_across_versions(tracker):
    matches = match_glob(tracker, "/api/*/users")
    paths = {m.path for m in matches}
    assert "/api/v1/users" in paths
    assert "/api/v2/users" in paths


# --- match_regex ---

def test_regex_matches_versioned_prefix(tracker):
    matches = match_regex(tracker, r"^/api/v[0-9]+/")
    assert len(matches) == 4  # all /api/vN/ routes


def test_regex_no_match_returns_empty(tracker):
    assert match_regex(tracker, r"^/metrics") == []


def test_regex_method_filter(tracker):
    matches = match_regex(tracker, r"/users$", method="GET")
    methods = {m.method for m in matches}
    assert methods == {"GET"}


def test_regex_invalid_pattern_raises(tracker):
    import re
    with pytest.raises(re.error):
        match_regex(tracker, r"[invalid")


def test_regex_hit_counts_preserved(tracker):
    matches = match_regex(tracker, r"^/api/v1/users$", method="GET")
    assert matches[0].hit_count == 2


# --- keys_for_pattern ---

def test_keys_for_pattern_glob(tracker):
    keys = keys_for_pattern(tracker, "/api/v1/*")
    assert "GET /api/v1/users" in keys
    assert "POST /api/v1/users" in keys


def test_keys_for_pattern_regex(tracker):
    keys = keys_for_pattern(tracker, r"^/admin/", use_regex=True)
    assert "DELETE /admin/purge" in keys


def test_keys_for_pattern_with_method(tracker):
    keys = keys_for_pattern(tracker, "/api/*", method="DELETE")
    assert keys == []
