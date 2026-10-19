"""A suppressed name is suppressed on every surface; the row and the money
stay (hard limit 16; the old estate's C084: "we suppress their name from
the interfaces, not the documents").

The list is a published view the template names in its settings
(`suppressed_names_view`, default `pub.suppressed_names`: name, name_key,
released_at). No lane publishes it yet, so the list is empty and the build
says so; the machinery is here so that the day the view exists nothing
else changes. A name is matched by its form, case and spacing aside, in
every string of every payload; a matching string becomes
"[name suppressed]" and nothing else in the row moves.
"""
from __future__ import annotations

import re

MARK = "[name suppressed]"


def form_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def load_forms(tables, view: str) -> list:
    """The forms in force (released_at null), or [] when the view is not published."""
    if not view or not tables.has_view(view):
        return []
    rows = tables.get(view) if view in tables.allowed else []
    return sorted({form_key(r.get("name")) for r in rows if r.get("name") and not r.get("released_at")} - {""})


def redact(obj, forms: list):
    """A copy of obj with every string whose form is a suppressed form replaced by MARK. Counts in the second value."""
    keys = set(forms)
    n = 0

    def walk(x):
        nonlocal n
        if isinstance(x, str):
            if keys and form_key(x) in keys:
                n += 1
                return MARK
            return x
        if isinstance(x, list):
            return [walk(v) for v in x]
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        return x
    return walk(obj), n


def find(obj, forms: list) -> int:
    """How many strings in obj carry a suppressed form (0 when none)."""
    return redact(obj, forms)[1]
