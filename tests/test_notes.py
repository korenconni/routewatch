"""Tests for routewatch.notes."""
from __future__ import annotations

import pytest

from routewatch.tracker import RouteTracker
from routewatch import notes as notes_mod
from routewatch.notes import (
    Note,
    add_note,
    get_notes,
    remove_notes,
    all_notes,
    notes_report,
)


@pytest.fixture(autouse=True)
def clear_store():
    notes_mod._store.clear()
    yield
    notes_mod._store.clear()


@pytest.fixture()
def tracker():
    t = RouteTracker()
    t.register("GET", "/users")
    t.register("POST", "/users")
    return t


def test_add_note_returns_note_instance(tracker):
    note = add_note(tracker, "GET", "/users", "Check pagination limits.", author="alice")
    assert isinstance(note, Note)


def test_add_note_stores_text(tracker):
    add_note(tracker, "GET", "/users", "Important endpoint.", author="bob")
    notes = get_notes(tracker, "GET", "/users")
    assert len(notes) == 1
    assert notes[0].text == "Important endpoint."


def test_add_note_stores_author(tracker):
    add_note(tracker, "GET", "/users", "Check this.", author="carol")
    notes = get_notes(tracker, "GET", "/users")
    assert notes[0].author == "carol"


def test_add_note_key_is_uppercase(tracker):
    note = add_note(tracker, "get", "/users", "lowercase method test")
    assert note.key == "GET /users"


def test_add_note_auto_registers_unknown_route(tracker):
    add_note(tracker, "DELETE", "/users/99", "Soft-delete only.")
    assert "DELETE /users/99" in tracker.routes


def test_add_note_is_additive(tracker):
    add_note(tracker, "GET", "/users", "First note.")
    add_note(tracker, "GET", "/users", "Second note.")
    assert len(get_notes(tracker, "GET", "/users")) == 2


def test_get_notes_empty_for_unregistered(tracker):
    assert get_notes(tracker, "GET", "/nonexistent") == []


def test_get_notes_returns_copy(tracker):
    add_note(tracker, "GET", "/users", "Original.")
    notes = get_notes(tracker, "GET", "/users")
    notes.clear()
    assert len(get_notes(tracker, "GET", "/users")) == 1


def test_remove_notes_returns_count(tracker):
    add_note(tracker, "GET", "/users", "Note A.")
    add_note(tracker, "GET", "/users", "Note B.")
    count = remove_notes(tracker, "GET", "/users")
    assert count == 2


def test_remove_notes_clears_entries(tracker):
    add_note(tracker, "GET", "/users", "To be removed.")
    remove_notes(tracker, "GET", "/users")
    assert get_notes(tracker, "GET", "/users") == []


def test_remove_notes_nonexistent_returns_zero(tracker):
    assert remove_notes(tracker, "GET", "/ghost") == 0


def test_all_notes_returns_all_routes(tracker):
    add_note(tracker, "GET", "/users", "Note 1.")
    add_note(tracker, "POST", "/users", "Note 2.")
    store = all_notes()
    assert "GET /users" in store
    assert "POST /users" in store


def test_notes_report_empty(tracker):
    report = notes_report(tracker)
    assert "no notes" in report


def test_notes_report_contains_route_key(tracker):
    add_note(tracker, "GET", "/users", "Check auth.", author="dave")
    report = notes_report(tracker)
    assert "GET /users" in report
    assert "dave" in report
    assert "Check auth." in report


def test_note_created_at_is_set(tracker):
    note = add_note(tracker, "GET", "/users", "Timestamp test.")
    assert note.created_at  # non-empty ISO string
