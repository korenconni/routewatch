"""Tests for routewatch.scoring."""

import pytest

from routewatch.tracker import RouteTracker
from routewatch.scoring import (
    RouteScore,
    score_route,
    build_scores,
    average_score,
    scoring_report,
    _grade,
)


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/")
    t.register("GET", "/about")
    t.register("POST", "/submit")
    for _ in range(10):
        t.record("GET", "/")
    for _ in range(3):
        t.record("GET", "/about")
    # /submit intentionally left at 0 hits
    return t


def test_score_route_zero_hits():
    assert score_route(0, 10) == 0.0


def test_score_route_max_hits_returns_100():
    assert score_route(50, 50) == 100.0


def test_score_route_partial():
    s = score_route(3, 10)
    assert 0.0 < s < 100.0


def test_score_route_zero_max():
    assert score_route(5, 0) == 0.0


def test_grade_boundaries():
    assert _grade(95) == "A"
    assert _grade(90) == "A"
    assert _grade(89) == "B"
    assert _grade(75) == "B"
    assert _grade(74) == "C"
    assert _grade(50) == "C"
    assert _grade(49) == "D"
    assert _grade(25) == "D"
    assert _grade(24) == "F"
    assert _grade(0) == "F"


def test_build_scores_length(tracker):
    scores = build_scores(tracker)
    assert len(scores) == 3


def test_build_scores_are_route_score_instances(tracker):
    for rs in build_scores(tracker):
        assert isinstance(rs, RouteScore)


def test_build_scores_sorted_descending(tracker):
    scores = build_scores(tracker)
    values = [rs.score for rs in scores]
    assert values == sorted(values, reverse=True)


def test_uncovered_route_scores_zero(tracker):
    scores = build_scores(tracker)
    submit = next(rs for rs in scores if rs.path == "/submit")
    assert submit.score == 0.0
    assert submit.grade == "F"


def test_top_route_scores_100(tracker):
    scores = build_scores(tracker)
    top = scores[0]
    assert top.score == 100.0
    assert top.hits == 10


def test_average_score_empty():
    t = RouteTracker()
    assert average_score(t) == 0.0


def test_average_score_between_zero_and_100(tracker):
    avg = average_score(tracker)
    assert 0.0 <= avg <= 100.0


def test_scoring_report_contains_grade(tracker):
    report = scoring_report(tracker)
    assert "Grade" in report
    assert "Average score" in report


def test_scoring_report_empty_tracker():
    t = RouteTracker()
    assert scoring_report(t) == "No routes registered."
