"""Tests for routewatch.budgets."""

import pytest

from routewatch.tracker import RouteTracker
from routewatch.budgets import (
    BudgetResult,
    BudgetReport,
    set_budget,
    remove_budget,
    get_budget,
    check_budgets,
    clear_budgets,
)


@pytest.fixture(autouse=True)
def _clear(tracker):
    """Ensure budget registry is clean before every test."""
    clear_budgets()
    yield
    clear_budgets()


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    t.register("GET", "/health")
    for _ in range(5):
        t.record("GET", "/users")
    t.record("POST", "/users")
    # /health has 0 hits
    return t


def test_budget_result_is_dataclass(tracker):
    set_budget("GET", "/users", min_hits=1)
    report = check_budgets(tracker)
    assert isinstance(report.results[0], BudgetResult)


def test_in_budget_when_within_bounds(tracker):
    set_budget("GET", "/users", min_hits=1, max_hits=10)
    report = check_budgets(tracker)
    result = report.results[0]
    assert result.in_budget is True
    assert result.under_budget is False
    assert result.over_budget is False


def test_under_budget_when_hits_below_min(tracker):
    set_budget("GET", "/health", min_hits=3)
    report = check_budgets(tracker)
    result = report.results[0]
    assert result.under_budget is True
    assert result.in_budget is False


def test_over_budget_when_hits_exceed_max(tracker):
    set_budget("GET", "/users", max_hits=2)
    report = check_budgets(tracker)
    result = report.results[0]
    assert result.over_budget is True
    assert result.in_budget is False


def test_has_violations_true_when_any_violation(tracker):
    set_budget("GET", "/health", min_hits=10)
    report = check_budgets(tracker)
    assert report.has_violations is True


def test_has_violations_false_when_all_in_budget(tracker):
    set_budget("GET", "/users", min_hits=1, max_hits=10)
    report = check_budgets(tracker)
    assert report.has_violations is False


def test_violations_returns_only_failing(tracker):
    set_budget("GET", "/users", min_hits=1, max_hits=10)  # in budget
    set_budget("GET", "/health", min_hits=5)               # under budget
    report = check_budgets(tracker)
    assert len(report.violations) == 1
    assert report.violations[0].route == "/health"


def test_remove_budget_returns_true_if_existed(tracker):
    set_budget("GET", "/users", min_hits=1)
    assert remove_budget("GET", "/users") is True


def test_remove_budget_returns_false_if_missing(tracker):
    assert remove_budget("GET", "/nonexistent") is False


def test_get_budget_returns_none_none_when_unset():
    assert get_budget("GET", "/unknown") == (None, None)


def test_get_budget_returns_set_values():
    set_budget("POST", "/items", min_hits=2, max_hits=50)
    assert get_budget("POST", "/items") == (2, 50)


def test_set_budget_raises_if_no_bounds():
    with pytest.raises(ValueError, match="At least one"):
        set_budget("GET", "/x")


def test_set_budget_raises_if_min_exceeds_max():
    with pytest.raises(ValueError, match="min_hits must be <= max_hits"):
        set_budget("GET", "/x", min_hits=10, max_hits=5)


def test_set_budget_raises_on_negative_min():
    with pytest.raises(ValueError, match=">= 0"):
        set_budget("GET", "/x", min_hits=-1)


def test_method_is_case_insensitive(tracker):
    set_budget("get", "/users", min_hits=1, max_hits=10)
    report = check_budgets(tracker)
    assert report.results[0].method == "GET"
    assert report.results[0].in_budget is True
