"""One joined row of a scan's query turned into one line of the list: for
each step, the row's ref, title, dates, citation and the columns the
template carries, with a suppressed name shown as "name suppressed" on
every surface; the line's grade (confirmed, near, contested) and the
reasons; the citations numbered once per (view, key) in the order they are
first met, as the report numbers them. No word of cause anywhere: a line
states what each register states, side by side. Pure functions."""
from __future__ import annotations

import datetime as dt
import decimal

from products.scan import views as cat
from products.scan.plan import CONTESTED_WHOLE
from products.scan.template import Template

SUPPRESSED = "name suppressed"
NOT_STATED = "not stated"
UNDATED = "undated"
GRADES = ("confirmed", "near", "contested")
NEAR_THROUGH_PEOPLE = "the path passes through more than one person: near, never confirmed (the through-people setting)"
NEAR_LINK_DEFAULT = "the rule that joined these rows grades the link near"
CONTESTED_DECISION = "a decision contests this link"
NEAR_BY_NAME = ("joined by name alone: the two names are the same text once case, macrons, punctuation and a legal ending such as "
                "Limited are set aside; an official number does not join these rows")
NAMESAKES = "one of {n} rows of pub.{view} that carry this name: namesakes, each a line of its own; the registers do not say which, if any, is the {here}"


def fmt_date(d) -> str:
    if isinstance(d, dt.datetime):
        d = d.date()
    return d.strftime("%-d %B %Y") if isinstance(d, dt.date) else str(d)


def fmt(value) -> str:
    if value is None or value == "":
        return NOT_STATED
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (dt.date, dt.datetime)):
        return fmt_date(value)
    if isinstance(value, decimal.Decimal):
        return f"{value:,}"
    if isinstance(value, (list, tuple)):
        return "; ".join(" ".join(str(y) for y in x.values()) if isinstance(x, dict) else str(x) for x in value) or NOT_STATED
    if isinstance(value, dict):
        return "; ".join(f"{k}: {x}" for k, x in value.items()) or NOT_STATED
    return str(value)


def is_suppressed(v: cat.View, r: dict) -> bool:
    return bool(v.suppressed and r.get(v.suppressed))


def shown(v: cat.View, r: dict, column: str):
    if column in v.names and is_suppressed(v, r):
        return SUPPRESSED
    return r.get(column)


def title(v: cat.View, r: dict) -> str:
    parts = [fmt(shown(v, r, c)) for c in v.title if shown(v, r, c) not in (None, "")]
    return " · ".join(parts) or f"({v.name} {r.get(v.key_col, '')})"


def dates(v: cat.View, r: dict) -> dict:
    """How the row is dated, as the report dates a row: from/to, an `on`
    date saying what it dates, a year, a publication day; undated when none,
    with the files it was seen in beside as a bound, never as a date."""
    start = r.get(v.start) if v.start else None
    end = r.get(v.end) if v.end else None
    on = r.get(v.on) if v.on else None
    year = r.get(v.year) if v.year else None
    published = r.get(v.published) if v.published else None
    period = tuple(r.get(c) if c else None for c in v.period) if v.period else ()
    bits = []
    if start:
        bits.append(f"from {fmt_date(start)}")
    if end:
        bits.append(f"to {fmt_date(end)}")
    elif start and v.end:
        bits.append("no end filed")
    if on:
        basis = (str(r.get(v.on_basis) or "").strip().lower() if v.on_basis else "") or v.on_label
        word = cat.ON_BASIS_WORD.get(basis, basis)
        bits.append(f"{word} {fmt_date(on)}".strip())
    if year and not (start or on):
        bits.append(f"{year} (the year the row is filed under)")
    if published:
        bits.append(f"published {fmt_date(published)}")
    undated = not (start or end or on or year or published)
    if undated:
        bits.append(UNDATED)
        a, b = (period + (None, None))[:2]
        if a and b:
            bits.append(f"in the files from {fmt(a)} to {fmt(b)}")
        elif b:
            bits.append(f"last seen in the file {fmt(b)}")
    return {"start": start, "end": end, "on": on, "year": year, "published": published, "undated": undated, "text": "; ".join(bits)}


def citation(v: cat.View, r: dict) -> dict:
    c = {"view": v.name, "key": str(r.get(v.key_col, "")), "register": v.register, "document": r.get("document"),
         "page": r.get("page"), "place": r.get("place"), "url": str(r[v.url]) if v.url and r.get(v.url) else None}
    return c


def cite_text(c: dict) -> str:
    bits = [f"pub.{c['view']} {c['key']}"]
    if c.get("document"):
        bits.append(f"document {str(c['document'])[:12]}…")
        if c.get("page") not in (None, ""):
            bits.append(f"page {c['page']}")
        if c.get("place") not in (None, ""):
            bits.append(f"place {c['place']}")
    else:
        bits.append("document not stated")
    if c.get("url"):
        bits.append(c["url"])
    return "; ".join(bits)


class Numbering:
    """Citations numbered once per row, in the order first met: a row is its
    (view, key) and the document, page and place it was read from, because a
    published key need not name one row (the iwi directory's settlement key is
    the settlement's, one row per body whose entry names it, each read from
    that body's page)."""

    def __init__(self):
        self.number = {}
        self.citations = []

    def cite(self, c: dict) -> int:
        key = (c["view"], c["key"], c.get("document"), c.get("page"), c.get("place"))
        if key not in self.number:
            self.number[key] = len(self.number) + 1
            self.citations.append({"n": self.number[key], **c})
        return self.number[key]


def step_row(rec: dict, i: int) -> dict:
    pre = f"s{i}__"
    return {k[len(pre):]: x for k, x in rec.items() if k.startswith(pre)}


def grade_of(t: Template, settings: dict, rec: dict) -> tuple:
    """(grade, reasons) for a joined row: contested when any person step
    crosses a contested group or a contested decision; else near when any
    link is near or the path passes through more than one person (under
    the through-people setting); else confirmed."""
    reasons, contested, near = [], False, False
    for i, s in enumerate(t.steps):
        if s.by == "name":
            if rec.get(f"s{i}__by") == "name":
                near = True
                reasons.append(f"{s.label}: {NEAR_BY_NAME}")
            if (rec.get(f"s{i}__namesakes") or 0) > 1:
                near = True
                reasons.append(f"{s.label}: " + NAMESAKES.format(n=rec[f"s{i}__namesakes"], view=s.view, here=t.steps[i - 1].label))
            continue
        if s.by not in ("person", "link"):
            continue
        if rec.get(f"s{i}__contested"):
            contested = True
            reasons.append(f"{s.label}: {CONTESTED_WHOLE}")
        g = rec.get(f"s{i}__grade")
        if g is not None:
            if rec.get(f"s{i}__decision") == "contested":
                contested = True
                reasons.append(f"{s.label}: {rec.get(f's{i}__reason') or CONTESTED_DECISION}")
            elif g != "confirmed":
                near = True
                reasons.append(f"{s.label}: {rec.get(f's{i}__reason') or NEAR_LINK_DEFAULT} ({rec.get(f's{i}__rule')})")
    if contested:
        return "contested", reasons
    if settings["through_people"]["value"] == "near" and t.person_steps > 1:
        near = True
        reasons.append(NEAR_THROUGH_PEOPLE)
    return ("near" if near else "confirmed"), reasons


def line_of(t: Template, settings: dict, start: str, rec: dict, numbering: Numbering) -> dict:
    """The line: steps (ref, view, label, title, dates, citation number,
    suppressed, values), grade, reasons, cites. Hubs are added by `hubs`."""
    steps = []
    for i, s in enumerate(t.steps):
        view = start if i == 0 else s.view
        v = cat.BY_NAME[view]
        r = step_row(rec, i)
        if s.optional and r.get(v.key_col) is None:   # nothing there: the step is listed as none found, uncited
            how = s.fold_note if s.by == "name" else f"by {s.on[1]}"
            steps.append({"label": s.label, "view": view, "register": v.register, "kind": v.kind, "ref": None, "absent": True,
                          "title": f"none found in pub.{view} {how}", "dates": "", "cite": None, "cite_text": "", "suppressed": False,
                          "values": {}, "group": None, "link": None})
            continue
        c = citation(v, r)
        n = numbering.cite(c)
        steps.append({"label": s.label, "view": view, "register": v.register, "kind": v.kind, "ref": cat.ref_of(v, r.get(v.key_col)),
                      "title": title(v, r), "dates": dates(v, r)["text"], "cite": n, "cite_text": cite_text(c), "suppressed": is_suppressed(v, r),
                      "values": {c_: fmt(shown(v, r, c_)) for c_ in s.columns},
                      "group": rec.get(f"s{i}__group"), "link": rec.get(f"s{i}__link")})
    grade, reasons = grade_of(t, settings, rec)
    return {"grade": grade, "reasons": reasons, "hubs": [], "cites": sorted({s["cite"] for s in steps if s["cite"]}), "steps": steps}
