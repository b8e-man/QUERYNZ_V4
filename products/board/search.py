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
from products.board import db, fold

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


def _scan(v, words, number, limit, exclude_key, whole=False, fields=None):
    got = view_sql(v, words, number, limit, exclude_key, whole, fields)
    if got is None:
        return v, []
    sql, params = got
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


#: the fields of the expanded search (ruling 82), in the order the form shows them: (parameter, label)
FIELDS = (("first", "first name"), ("middle", "middle name"), ("last", "last name"), ("address", "address"),
          ("org", "organisation"), ("year", "year"))
FIELD_LABEL = dict(FIELDS)
NAME_FIELDS = ("first", "middle", "last")
FIELD_MAX = 100
#: an honorific in front of a one-string name is not part of it (keys.names.HONORIFICS, through the board's copy)
_HON_SQL = r"^\W*((" + "|".join(re.escape(h).replace("\\ ", " ") for h in fold.HONORIFICS) + r")[\s.]+)+"
#: an organisation word anywhere (keys.names.ORG_WORDS), in the database's dialect: \b is \y there
ORG_WORDS_SQL = fold.ORG_WORDS.pattern.replace(r"\b", r"\y")


def field_words(value: str) -> list:
    """A field's words, folded as the search folds: '.', ',' and ';' are not words."""
    return [w for w in re.split(r"[\s,;.]+", cat.fold_term(value or "")) if w]


def phrase(value: str) -> str:
    """The pattern for a field's words in a row, together and whole: de lu matches DE LU, never DELUCA."""
    return r"\m" + r"\s+".join(re.escape(w) for w in field_words(value)) + r"\M"


def whole_words(expr: str, value: str) -> tuple:
    """Every word of `value` a whole word of `expr`."""
    ws = field_words(value)
    return " and ".join(f"{expr} ~ %s" for _ in ws), [r"\m" + re.escape(w) + r"\M" for w in ws]


def name_patterns(field: str, value: str) -> tuple:
    """(no comma, with a comma, one word) patterns for a name field over a
    one-string name (ruling 82), applied after the honorific is cut from the
    front: a first or middle name is never the last word and a last or middle
    name never the first, when the name has two words or more; with a comma
    ("Family, Given") the family is before it and the given names after.
    A one-word name is matched by a first or last name (None for a middle)."""
    p = phrase(value)
    if field == "first":
        return p + r"\S*\s+\S", "," + ".*" + p, p
    if field == "last":
        return r"\S\s+\S*" + p, "^[^,]*" + p, p
    return r"\S\s+\S*" + p + r"\S*\s+\S", r",\s*\S+\s+.*" + p, None


def _name_whole(col: str, want: dict) -> tuple:
    """A one-string name: every name field asked, by name_patterns."""
    n = f"regexp_replace({fold_sql(col)}, %s, '')"
    parts, params = [], []
    for f in NAME_FIELDS:
        if not want.get(f):
            continue
        plain, comma, one = name_patterns(f, want[f])
        alt = f"({n} !~ ',' and {n} ~ %s) or ({n} ~ ',' and {n} ~ %s)"
        ps = [_HON_SQL, _HON_SQL, plain, _HON_SQL, _HON_SQL, comma]
        if one:
            alt += f" or ({n} !~ %s and {n} ~ %s)"
            ps += [_HON_SQL, r"\S\s+\S", _HON_SQL, one]
        parts.append(f"({fold_sql(col)} ~ %s and (" + alt + "))")     # the cheap whole-word test first
        params += [phrase(want[f])] + ps
    return " and ".join(parts), params


def _name_parts(g: cat.Name, want: dict):
    """A name held in parts: each name field matches whole words of its own
    column; with one column for every given name, a middle name is any of
    them but the first. None when the parts cannot hold a field asked for."""
    parts, params = [], []
    for f in NAME_FIELDS:
        if not want.get(f):
            continue
        p = phrase(want[f])
        if f == "first" and (g.first or g.given):
            parts.append(f"{fold_sql(g.first or g.given)} ~ %s")
            params.append(p)
        elif f == "middle" and g.middle:
            parts.append(f"{fold_sql(g.middle)} ~ %s")
            params.append(p)
        elif f == "middle" and g.given:
            parts.append(f"{fold_sql(g.given)} ~ %s")
            params.append(r"\S\s+\S*" + p)
        elif f == "last" and g.last:
            parts.append(f"{fold_sql(g.last)} ~ %s")
            params.append(p)
        else:
            return None
    return " and ".join(parts), params


def year_of(value: str):
    v = (value or "").strip()
    return int(v) if re.fullmatch(r"\d{4}", v) else None


def fields_sql(v: cat.View, fields: dict):
    """(clause, params) for the filled fields over one view, every field
    "and" the others; None when the view holds no column for one of them
    (or the year is not four digits), so the view is not searched."""
    fs = cat.fields_of(v)
    where, params = [], []
    want = {f: fields[f] for f in NAME_FIELDS if fields.get(f) and field_words(fields[f])}
    if want:
        alts, aps = [], []
        for g in fs.names:
            got = _name_whole(g.whole, want) if g.whole else _name_parts(g, want)
            if got:
                alts.append("(" + got[0] + ")")
                aps += got[1]
        if not alts:
            return None
        where.append("(" + " or ".join(alts) + ")")
        params += aps
    if fields.get("org") and field_words(fields["org"]):
        alts, aps = [], []
        if fs.organisation:
            c, ps = whole_words(fold_sql("concat_ws(' ', " + ", ".join(fs.organisation) + ")"), fields["org"])
            alts.append("(" + c + ")")
            aps += ps
        for col in fs.named:
            c, ps = whole_words(fold_sql(col), fields["org"])
            alts.append(f"({fold_sql(col)} ~ %s and {c})")
            aps += [ORG_WORDS_SQL] + ps
        if not alts:
            return None
        where.append("(" + " or ".join(alts) + ")")
        params += aps
    if fields.get("address") and field_words(fields["address"]):
        if not fs.address:
            return None
        c, ps = whole_words(fold_sql("concat_ws(' ', " + ", ".join(fs.address) + ")"), fields["address"])
        where.append("(" + c + ")")
        params += ps
    if (fields.get("year") or "").strip():
        y = year_of(fields["year"])
        if y is None or not (fs.year or fs.dates):
            return None
        alts = [f"{c} = %s" for c in fs.year] + [f"extract(year from {c}) = %s" for c in fs.dates]
        where.append("(" + " or ".join(alts) + ")")
        params += [y] * len(alts)
    return " and ".join(where), params


def match_sql(v: cat.View, words: list, number: str = None, whole: bool = False, fields: dict = None):
    """(clause, params): the search box's words (each begins a word of the
    row's search columns; with `whole`, is a whole word) or its number, "and"
    the filled fields. ("true", []) when nothing is asked; None when the view
    cannot hold a field asked for."""
    haystack = fold_sql("concat_ws(' ', " + ", ".join(v.search) + ")")
    where, params = [], []
    for w in words:
        where.append(f"{haystack} ~ %s")
        params.append(r"\m" + re.escape(w) + (r"\M" if whole else ""))
    clause = "(" + " and ".join(where) + ")" if where else ""
    if number and v.numbers:
        clause = "(" + (clause or "false") + " or " + " or ".join(f"{c} = %s" for c in v.numbers) + ")"
        params += [number] * len(v.numbers)
    if fields and any((fields.get(f) or "").strip() for f, _ in FIELDS):
        got = fields_sql(v, fields)
        if got is None:
            return None
        clause = (clause + " and " if clause else "") + "(" + got[0] + ")"
        params += got[1]
    return (clause or "true"), params


def guard_sql(v: cat.View, exclude_key: str = None) -> tuple:
    """A suppressed or revoked row is never matched by name (hard limit 16)."""
    clause, params = "", []
    if v.suppressed:
        clause += f" and not coalesce({v.suppressed}, false)"
    if v.hide_names:
        clause += f" and not coalesce({v.hide_names[0]}, '') ~* %s"
        params.append(v.hide_names[1])
    if exclude_key:
        clause += f" and {v.key_col} <> %s"
        params.append(exclude_key)
    return clause, params


def view_sql(v: cat.View, words: list, number: str = None, limit: int = LIMIT, exclude_key: str = None,
             whole: bool = False, fields: dict = None):
    """(sql, params): the matching rows of one view with the view's total
    as `total` on every row. Each word must begin a word in the row's
    search columns ("hart" finds HART and HARTLEY); with `whole`, each must
    be a whole word (a namesake search: HART is not HARTLEY). The filled
    fields (ruling 82) narrow it further; None when the view holds no
    column for one of them."""
    got = match_sql(v, words, number, whole, fields)
    if got is None:
        return None
    clause, params = got
    if not words and not number and clause == "true":
        clause = "false"                 # nothing asked finds nothing
    g, gp = guard_sql(v, exclude_key)
    sql = (f"select *, {v.key_col} as key, count(*) over () as total from pub.{v.name} where {clause}{g} "
           f"order by {v.default_order} nulls last, {v.key_col} limit %s")
    return sql, params + gp + [limit]


def held_registers(held: set) -> list:
    """The registers, in the catalogue's order, that have at least one view published."""
    return [r for r, _ in cat.REGISTERS if any(v.name in held for v in cat.views_of(r))]


class Boxes(NamedTuple):
    """The left pane's check boxes (ruling 81): "search all" and the register
    boxes are two separate states, so turning "search all" off and on loses
    no tick; and the filled fields of the expanded search (ruling 82),
    `fields` as (parameter, value) in FIELDS order. All travel as query
    parameters on every href (`params`)."""
    all: bool = True
    ticked: tuple = ()
    fields: tuple = ()

    def params(self) -> list:
        return [("all", "1" if self.all else "0")] + [("r", x) for x in self.ticked] + list(self.fields)

    def asked(self) -> dict:
        return dict(self.fields)


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
    fields = tuple((f, v) for f, v in ((f, " ".join(((qs.get(f) or [""])[0]).split())[:FIELD_MAX]) for f, _ in FIELDS) if v)
    return Boxes("1" in alls if alls else not ticked, ticked, fields)


def selection(boxes: Boxes, held: list) -> tuple:
    """The registers a search runs over: every held register while "search
    all" is ticked, whatever is ticked below it; the ticked held registers
    alone when it is not, so none ticked searches nothing."""
    return tuple(held) if boxes.all else tuple(r for r in held if r in boxes.ticked)


def search(conn, term: str, limit: int = LIMIT, views=None, exclude_key: str = None, whole: bool = False,
           registers=None, fields: dict = None) -> dict:
    """{register: [(view, total, rows)]} for the views that matched, plus
    'held' (the pub views present) so the caller can say "not held".
    `registers`, when given, scans only those registers' views; `fields`,
    the filled fields of the expanded search ({parameter: value}), narrow it
    (ruling 82): a view with no column for one of them is not scanned."""
    words = words_of(term)
    number = re.sub(r"\s", "", term) if is_number(term) else None
    fields = {f: x for f, x in (fields or {}).items() if (x or "").strip()}
    held = db.pub_views(conn)
    out = {}
    wanted = [v for v in (views or cat.VIEWS) if v.name in held and (words or number or fields)
              and (registers is None or v.register in registers)]
    futures = [_pool.submit(_scan, v, words, number, limit, exclude_key, whole, fields) for v in wanted]
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
