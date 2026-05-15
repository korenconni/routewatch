"""Route notes — attach freeform text notes to routes for documentation and ops."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from routewatch.tracker import RouteTracker

_store: Dict[str, List["Note"]] = {}


def _key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


@dataclass
class Note:
    method: str
    path: str
    text: str
    author: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def key(self) -> str:
        return _key(self.method, self.path)


def add_note(
    tracker: RouteTracker,
    method: str,
    path: str,
    text: str,
    author: str = "unknown",
) -> Note:
    """Attach a note to a route, auto-registering it if unknown."""
    k = _key(method, path)
    if k not in tracker.routes:
        tracker.register(method, path)
    note = Note(method=method, path=path, text=text, author=author)
    _store.setdefault(k, []).append(note)
    return note


def get_notes(tracker: RouteTracker, method: str, path: str) -> List[Note]:
    """Return all notes for a route, or an empty list."""
    k = _key(method, path)
    return list(_store.get(k, []))


def remove_notes(tracker: RouteTracker, method: str, path: str) -> int:
    """Remove all notes for a route. Returns the number of notes removed."""
    k = _key(method, path)
    removed = _store.pop(k, [])
    return len(removed)


def all_notes() -> Dict[str, List[Note]]:
    """Return a copy of the full notes store keyed by route key."""
    return {k: list(v) for k, v in _store.items() if v}


def notes_report(tracker: RouteTracker) -> str:
    """Render a plain-text report of all routes with attached notes."""
    lines: List[str] = ["Route Notes Report", "=================="]
    store = all_notes()
    if not store:
        lines.append("(no notes recorded)")
        return "\n".join(lines)
    for k, notes in sorted(store.items()):
        lines.append(f"\n{k}  ({len(notes)} note(s))")
        for i, note in enumerate(notes, 1):
            lines.append(f"  [{i}] {note.created_at}  @{note.author}")
            lines.append(f"      {note.text}")
    return "\n".join(lines)
