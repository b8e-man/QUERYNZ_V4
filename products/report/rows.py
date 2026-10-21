"""One row of a published view, by its ref (`<register>:<key>`, as the
board and `pub.links` name a row), and what the report says about it: its
title, the dates that date the connection it makes, its citation and its
one-sentence statement. Every rule for what a product shows applies here
(design: "Rules for everything a product shows"): a suppressed name reads
"name suppressed" on every surface; a withheld text reads "withheld"; a
blank reads "not stated"; a figure read from pixels is marked; a connection
with no date is marked "undated". Reads `pub.*` only."""
from __future__ import annotations

import datetime as dt
import decimal

from products.report import catalogue as cat
from products.report import db

SUPPRESSED = "name suppressed"
WITHHELD = "withheld (hard limit 15; a ruling is owed before it is shown)"
NOT_STATED = "not stated"
UNDATED = "undated"
PIXELS = "read from pixels: weaker evidence"
MONEY = {"amount", "amount_original", "declared_total", "donations", "expenses", "loans", "part_a", "part_c", "part_d",
         "part_f", "part_g", "loans_h", "loans_i", "loans_total", "items_sum", "form_total", "total", "figure"}


# ── refs ────────────────────────────────────────────────────────────────────

def split_ref(ref: str) -> tuple:
    register, _, key = (ref or "").partition(":")
    return register.strip(), key.strip()


def ref_of(v: cat.View, key: str) -> str:
    return f"{v.register}:{key}"


# ── what a value shows ──────────────────────────────────────────────────────

def is_suppressed(v: cat.View, r: dict) -> bool:
    if v.suppressed and r.get(v.suppressed):
        return True
    if v.hide_names:
        import re
        return bool(re.search(v.hide_names[1], str(r.get(v.hide_names[0]) or ""), re.I))
    return False


def is_withheld(v: cat.View, r: dict) -> bool:
    return bool(v.withheld and r.get(v.withheld))


def shown(v: cat.View, r: dict, column: str):
    if column in v.names and is_suppressed(v, r):
        return SUPPRESSED
    if column == "text" and is_withheld(v, r):
        return WITHHELD
    return r.get(column)


def fmt_date(d) -> str:
    if isinstance(d, dt.datetime):
        d = d.date()
    return d.strftime("%-d %B %Y") if isinstance(d, dt.date) else str(d)


def fmt(value, column: str = "") -> str:
    """One value as the memo prints it (plain text, unescaped)."""
    if value is None or value == "":
        return NOT_STATED
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (dt.date, dt.datetime)):
        return fmt_date(value)
    if isinstance(value, (int, decimal.Decimal, float)):
        if column in MONEY:
            return f"${decimal.Decimal(value):,.2f}"
        return str(value) if isinstance(value, int) else f"{decimal.Decimal(value):,}"
    if isinstance(value, dict):
        return "; ".join(f"{k}: {x}" for k, x in value.items()) or NOT_STATED
    if isinstance(value, (list, tuple)):
        return "; ".join(str(x) for x in value) or NOT_STATED
    return str(value)


def title(v: cat.View, r: dict) -> str:
    parts = []
    for c in v.title:
        x = shown(v, r, c)
        if x not in (None, ""):
            parts.append(fmt(x, c))
    return " · ".join(parts) or f"({v.name} {r.get(v.key_col, '')})"


# ── dating a connection ─────────────────────────────────────────────────────

def dates(v: cat.View, r: dict) -> dict:
    """How the row is dated: {'start', 'end', 'on', 'year', 'filed',
    'published', 'period', 'undated', 'text'}. The `on` date says what it
    dates when the view knows (a notice's hearing day, the last day for
    objections, an appointment); a filing day and a publication day are
    stated beside it, and a row with only a publication day is dated by it.
    A row with none of its view's date columns filled is undated and says
    so; the files it was seen in are stated beside, as a bound on when,
    never as the date of anything."""
    start = r.get(v.start) if v.start else None
    end = r.get(v.end) if v.end else None
    on = r.get(v.on) if v.on else None
    year = r.get(v.year) if v.year else None
    filed = r.get(v.filed) if v.filed else None
    published = r.get(v.published) if v.published else None
    period = tuple(r.get(c) if c else None for c in v.period) if v.period else ()
    as_in = r.get(v.as_in) if v.as_in else None
    bits = []
    if start:
        bits.append(f"from {fmt_date(start)}")
    if end:
        bits.append(f"to {fmt_date(end)}")
    elif start and v.end:
        bits.append("no end filed" + (" (in the latest file)" if r.get("in_latest") else
                                     "" if "in_latest" not in r else " (not in the latest file: the file states no end)"))
    if on:
        basis = (str(r.get(v.on_basis) or "").strip().lower() if v.on_basis else "") or v.on_label
        word = cat.ON_BASIS_WORD.get(basis, basis)
        bits.append(f"{word} {fmt_date(on)}".strip())
    if year and not (start or on):
        bits.append(f"{year} (the year the row is filed under)")
    if filed:
        bits.append(f"filed {fmt_date(filed)}")
    if published:
        bits.append(f"published {fmt_date(published)}")
    if as_in:
        bits.append(f"as in the file {as_in}")
    undated = not (start or end or on or year or filed or published or as_in)
    if undated:
        bits.append(UNDATED)
    if period and any(period) and undated:
        a, b = (period + (None, None))[:2]
        if a and b:
            bits.append(f"in the files from {fmt(a)} to {fmt(b)}")
        elif b:
            bits.append(f"last seen in the file {fmt(b)}")
        elif a:
            bits.append(f"first seen in the file {fmt(a)}")
    return {"start": start, "end": end, "on": on, "year": year, "filed": filed, "published": published, "period": period, "as_in": as_in,
            "undated": undated, "text": "; ".join(bits)}


# ── the citation ────────────────────────────────────────────────────────────

def citation(v: cat.View, r: dict) -> dict:
    """The row's own citation: its view and key, and the document, page and
    place it was read from where the view states them. A row with no document
    cites its view and key and says the original is not held."""
    c = {"view": v.name, "key": str(r.get(v.key_col, "")), "register": v.register,
         "document": r.get("document"), "page": r.get("page"), "place": r.get("place"),
         "read_from": r.get("read_from"), "reader": r.get("reader"), "profile": r.get("profile"),
         "source_note": r.get("source_note") or (v.note if not r.get("document") and "not held" in v.note else None)}
    for u in ("url", "href"):
        if r.get(u):
            c["url"] = str(r[u])
            break
    return c


def cite_text(c: dict) -> str:
    bits = [f"pub.{c['view']} {c['key']}"]
    if c.get("document"):
        bits.append(f"document {c['document'][:12]}…")
        if c.get("page") not in (None, ""):
            bits.append(f"page {c['page']}")
        if c.get("place") not in (None, ""):
            bits.append(f"place {c['place']}")
        if c.get("read_from") == "pixels":
            bits.append(PIXELS)
        elif c.get("read_from"):
            bits.append(f"read from {c['read_from']}")
    else:
        bits.append("document not stated" + (f": {c['source_note']}" if c.get("source_note") else ""))
    if c.get("url"):
        bits.append(c["url"])
    return "; ".join(bits)


# ── the statement ───────────────────────────────────────────────────────────

class _Shown(dict):
    def __missing__(self, key):
        return NOT_STATED


def statement(v: cat.View, r: dict, entity_title: str = None) -> str:
    """The row's one sentence, from its view's pattern; every value shown
    through `shown`, money formatted, a blank "not stated". Never a word of
    cause: the pattern states what the register states."""
    values = _Shown()
    for k, x in r.items():
        values[k] = fmt(shown(v, r, k), k)
    values["title"] = title(v, r)
    values["role"] = fmt(shown(v, r, v.role)) if v.role else NOT_STATED
    values["amount"] = fmt(r.get(v.amount), v.amount) if v.amount else NOT_STATED
    values["on"] = fmt(r.get(v.on)) if v.on else NOT_STATED
    values["year"] = fmt(r.get(v.year)) if v.year else values.get("year", NOT_STATED)
    values["entity"] = entity_title or (fmt(r.get(v.entity[1])) if v.entity else NOT_STATED)
    text = v.statement.format_map(values) if v.statement else values["title"]
    return " ".join(text.split())


# ── reading rows ────────────────────────────────────────────────────────────

def row(conn, view_name: str, key: str) -> dict | None:
    v = cat.BY_NAME[view_name]
    got = db.rows(conn, f"select *, {v.key_col} as key from pub.{v.name} where {v.key_col} = %s limit 1", (key,))
    return got[0] if got else None


def rows_where(conn, view_name: str, column: str, value, limit: int = 200, order: str = None) -> tuple:
    """(total, rows): the rows of a view whose column equals the value, the
    view's total counted so the memo can say how many it leaves out."""
    v = cat.BY_NAME[view_name]
    order = order or v.key_col
    got = db.rows(conn, f"select *, {v.key_col} as key, count(*) over () as total from pub.{v.name} "
                        f"where {column} = %s order by {order} nulls last, {v.key_col} limit %s", (value, limit))
    total = got[0]["total"] if got else 0
    for r in got:
        r.pop("total", None)
    return total, got


def locate(conn, ref: str) -> tuple:
    """(view, row) for a ref, or (None, None). The search table across
    registers (`pub.names`) names the view of every person-bearing row; a
    row it does not carry (a company, a return, a notice) is looked for in
    each view of its register."""
    register, key = split_ref(ref)
    if not register or not key:
        return None, None
    if db.has_relation(conn, "pub", "names"):
        hit = db.rows(conn, "select view from pub.names where ref = %s limit 1", (ref,))
        if hit and hit[0]["view"] in cat.BY_NAME:
            r = row(conn, hit[0]["view"], key)
            if r:
                return cat.BY_NAME[hit[0]["view"]], r
    for v in cat.views_of(register):
        r = row(conn, v.name, key)
        if r:
            return v, r
    return None, None


def entity_of(conn, v: cat.View, r: dict) -> tuple:
    """The row this row sits on (a role's company, a donation's return, a
    practitioner's notice), or (None, None). The join is on the parent's key
    unless the view names another column (`entity_col`: a notice number, which
    several company rows of one notice share; the first is taken)."""
    if not v.entity:
        return None, None
    ev, col = v.entity
    key = r.get(col)
    if not key:
        return None, None
    if v.entity_col and v.entity_col != cat.BY_NAME[ev].key_col:
        got = rows_where(conn, ev, v.entity_col, key, 1)[1]
        e = got[0] if got else None
    else:
        e = row(conn, ev, key)
    return (cat.BY_NAME[ev], e) if e else (None, None)
