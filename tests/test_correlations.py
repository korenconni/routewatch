"""Tests for routewatch.correlations."""
import pytest

from routewatch.correlations import (
    CorrelationPair,
    clear_correlations,
    correlations_for,
    flush_session,
    record_correlation,
    top_correlations,
)


@pytest.fixture(autouse=True)
def clean():
    clear_correlations()
    yield
    clear_correlations()


def test_correlation_pair_is_dataclass():
    cp = CorrelationPair(route_a="GET /a", route_b="GET /b", count=3)
    assert cp.route_a == "GET /a"
    assert cp.route_b == "GET /b"
    assert cp.count == 3


def test_record_correlation_single_hit_no_pairs():
    record_correlation("s1", "GET", "/a")
    assert top_correlations() == []


def test_record_correlation_two_routes_creates_pair():
    record_correlation("s1", "GET", "/a")
    record_correlation("s1", "POST", "/b")
    pairs = top_correlations()
    assert len(pairs) == 1
    assert pairs[0].count == 1


def test_record_correlation_increments_count():
    for _ in range(3):
        clear_correlations()
        record_correlation("sx", "GET", "/a")
        record_correlation("sx", "GET", "/b")
    # After 3 clear+record cycles each pair count == 1; test accumulation
    clear_correlations()
    record_correlation("s1", "GET", "/a")
    record_correlation("s1", "GET", "/b")
    record_correlation("s2", "GET", "/a")
    record_correlation("s2", "GET", "/b")
    pairs = top_correlations()
    assert pairs[0].count == 2


def test_top_correlations_respects_n():
    for i in range(5):
        record_correlation(f"s{i}", "GET", "/x")
        record_correlation(f"s{i}", "GET", f"/route{i}")
    pairs = top_correlations(n=3)
    assert len(pairs) <= 3


def test_top_correlations_sorted_descending():
    record_correlation("s1", "GET", "/a")
    record_correlation("s1", "GET", "/b")
    record_correlation("s2", "GET", "/a")
    record_correlation("s2", "GET", "/b")
    record_correlation("s3", "GET", "/a")
    record_correlation("s3", "GET", "/c")
    pairs = top_correlations()
    assert pairs[0].count >= pairs[-1].count


def test_correlations_for_returns_related_routes():
    record_correlation("s1", "GET", "/dashboard")
    record_correlation("s1", "GET", "/users")
    record_correlation("s2", "GET", "/dashboard")
    record_correlation("s2", "GET", "/orders")
    related = correlations_for("GET", "/dashboard", n=5)
    routes = {r.route_b for r in related}
    assert "GET /users" in routes
    assert "GET /orders" in routes


def test_correlations_for_unknown_route_returns_empty():
    assert correlations_for("GET", "/nonexistent") == []


def test_flush_session_removes_buffer():
    record_correlation("s1", "GET", "/a")
    flush_session("s1")
    # New hit in same session should not pair with pre-flush routes
    record_correlation("s1", "GET", "/b")
    assert top_correlations() == []


def test_clear_correlations_resets_store():
    record_correlation("s1", "GET", "/a")
    record_correlation("s1", "GET", "/b")
    clear_correlations()
    assert top_correlations() == []
