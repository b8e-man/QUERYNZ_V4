"""One search across every published view (plan step 4.9). A term is cut
into words; a row matches when every word appears, after the fold, in the
row's search columns together; a term that is all digits is also matched
exactly against official-number columns. A suppressed row never matches
by name (hard limit 16): it is found through its company, where its name
reads "name suppressed".

Until links/ publishes the search table across registers, this is a scan
of each view; at October 2026 sizes the whole scan takes about a second."""
from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple

from products.board import catalogue as cat
from products.board import db

LIMIT = 10          # rows per view for "same name elsewhere"
RESULTS_LIMIT = 50  # rows per view in the search tab's results pane, with the view's whole count beside them
WORKERS = 3         # views are scanned on this many product-reader connections at once (its cap is 10)
_local = threading.local()
_pool = ThreadPoolExecutor(max_workers=WORKERS, thread_name_prefix="qv4-board-search")


def _conn():
    """One product-reader connection per worker thread, reopened if it has closed."""
    c = getattr(_local, "conn", None)
    if c is None or c.closed:
        c = _local.conn = db.scan_connect()
    return c


def _scan(v, words, number, limit, exclude_key, whole=False):
    sql, params = view_sql(v, words, number, limit, exclude_key, whole)
    try:
        return v, db.rows(_conn(), sql, params)
    except Exception:
        _local.conn = None     # a broken connection is dropped; the next scan reopens
        raise
MACRON_FROM, MACRON_TO = cat.MACRONS


def fold_sql(expr: str) -> str:
    return f"translate(lower({expr}), '{MACRON_FROM}', '{MACRON_TO}')"


def words_of(term: str) -> list:
    return [w for w in re.split(r"[\s,;]+", cat.fold_term(term)) if w]


def is_number(term: str) -> bool:
    return bool(re.fullmatch(r"\d[\d ]*", term.strip()))


def view_sql(v: cat.View, words: list, number: str = None, limit: int = LIMIT, exclude_key: str = None,
             whole: bool = False) -> tuple:
    """(sql, params): the matching rows of one view with the view's total
    as `total` on every row. Each word must begin a word in the row's
    search columns ("hart" finds HART and HARTLEY); with `whole`, each must
    be a whole word (a namesake search: HART is not HARTLEY)."""
    haystack = fold_sql("concat_ws(' ', " + ", ".join(v.search) + ")")
    where, params = [], []
    for w in words:
        where.append(f"{haystack} ~ %s")
        params.append(r"\m" + re.escape(w) + (r"\M" if whole else ""))
    clause = "(" + " and ".join(where) + ")" if where else "false"
    if number and v.numbers:
        clause = "(" + clause + " or " + " or ".join(f"{c} = %s" for c in v.numbers) + ")"
        params += [number] * len(v.numbers)
    if v.suppressed:
        clause += f" and not coalesce({v.suppressed}, false)"
    if v.hide_names:
        clause += f" and not coalesce({v.hide_names[0]}, '') ~* %s"
        params.append(v.hide_names[1])
    if exclude_key:
        clause += f" and {v.key_col} <> %s"
        params.append(exclude_key)
    sql = (f"select *, {v.key_col} as key, count(*) over () as total from pub.{v.name} where {clause} "
           f"order by {v.default_order} nulls last, {v.key_col} limit %s")
    params.append(limit)
    return sql, params


def held_registers(held: set) -> list:
    """The registers, in the catalogue's order, that have at least one view published."""
    return [r for r, _ in cat.REGISTERS if any(v.name in held for v in cat.views_of(r))]


class Boxes(NamedTuple):
    """The left pane's check boxes (ruling 81): "search all" and the register
    boxes are two separate states, so turning "search all" off and on loses
    no tick. Both travel as query parameters on every href (`params`)."""
    all: bool = True
    ticked: tuple = ()

    def params(self) -> list:
        return [("all", "1" if self.all else "0")] + [("r", x) for x in self.ticked]


FIRST = Boxes()     # the first view of either tab: "search all" ticked, every register unticked


def boxes_of(qs: dict) -> Boxes:
    """Boxes from a parsed query string or POST body. The form sends a
    hidden `all=0` before the "search all" box (`all=1`), because a GET form
    sends nothing for an unticked box: so `all` present says the boxes were
    sent, and "1" among its values says "search all" was ticked. An address
    with no `all` comes from before ruling 81: none of `r` is the first view
    (a saved path, an old address); `r` alone is board-2's narrowed link."""
    known = dict(cat.REGISTERS)
    ticked = tuple(dict.fromkeys(x for x in (qs.get("r") or [])[:60] if x in known))
    alls = qs.get("all") or []
    return Boxes("1" in alls if alls else not ticked, ticked)


def selection(boxes: Boxes, held: list) -> tuple:
    """The registers a search runs over: every held register while "search
    all" is ticked, whatever is ticked below it; the ticked held registers
    alone when it is not, so none ticked searches nothing."""
    return tuple(held) if boxes.all else tuple(r for r in held if r in boxes.ticked)


def search(conn, term: str, limit: int = LIMIT, views=None, exclude_key: str = None, whole: bool = False,
           registers=None) -> dict:
    """{register: [(view, total, rows)]} for the views that matched, plus
    'held' (the pub views present) so the caller can say "not held".
    `registers`, when given, scans only those registers' views."""
    words = words_of(term)
    number = re.sub(r"\s", "", term) if is_number(term) else None
    held = db.pub_views(conn)
    out = {}
    wanted = [v for v in (views or cat.VIEWS) if v.name in held and (words or number)
              and (registers is None or v.register in registers)]
    futures = [_pool.submit(_scan, v, words, number, limit, exclude_key, whole) for v in wanted]
    for f in futures:
        v, found = f.result()
        if found:
            out.setdefault(v.register, []).append((v, int(found[0]["total"]), found))
    out["held"] = held
    return out


def row(conn, view: str, key: str):
    v = cat.BY_NAME.get(view)
    if v is None:
        return None
    found = db.rows(conn, f"select *, {v.key_col} as key from pub.{v.name} where {v.key_col} = %s", (key,))
    return found[0] if found else None


def children(conn, v: cat.View, r: dict, limit: int = 200) -> list:
    """[(join, total, rows)] for every join of the view, empty joins kept
    so the pane can say 'none found'."""
    out = []
    for j in v.joins:
        value = r.get(j.key_column)
        if value is None:
            out.append((j, 0, []))
            continue
        target = cat.BY_NAME[j.view]
        found = db.rows(conn, f"select *, {target.key_col} as key, count(*) over () as total from pub.{target.name} "
                              f"where {j.column} = %s order by {j.order} nulls last, {target.key_col} limit %s", (value, limit))
        out.append((j, int(found[0]["total"]) if found else 0, found))
    return out


def parent(conn, v: cat.View, r: dict):
    if not v.parent:
        return None
    label, view, column = v.parent
    value = r.get(column)
    if not value:
        return (label, view, None)
    return (label, view, row(conn, view, value))


def names_of_row(v: cat.View, r: dict) -> list:
    """The name words a 'same name elsewhere' search uses: the row's name
    columns, joined; nothing for a suppressed row."""
    if (v.suppressed and r.get(v.suppressed)) or (v.hide_names and re.search(v.hide_names[1], str(r.get(v.hide_names[0]) or ""), re.I)):
        return []
    parts = [str(r.get(c) or "") for c in v.names]
    return words_of(" ".join(parts))


def same_name(conn, v: cat.View, r: dict, limit: int = LIMIT) -> dict:
    """Rows in every register carrying every word of this row's name: the
    namesake candidates, by name alone, never identity."""
    words = names_of_row(v, r)
    if not words:
        return {"held": set()}
    named = [w for w in cat.VIEWS if w.names]
    return search(conn, " ".join(words), limit=limit, views=named, exclude_key=r["key"], whole=True)
