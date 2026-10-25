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


def _scan(v, words, number, limit, exclude_key, whole=False, fields=None, mode="all"):
    got = view_sql(v, words, number, limit, exclude_key, whole, fields, mode)
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


def _alternatives(w: str) -> str:
    """A word with its alternatives (ruling 92 (4): "garry|gareth", chosen
    from the near names), its empty alternatives dropped; "" when none is left."""
    return "|".join(x for x in w.split("|") if x)


def words_of(term: str) -> list:
    return [a for a in (_alternatives(w) for w in re.split(r"[\s,;]+", cat.fold_term(term))) if a]


def word_re(w: str) -> str:
    """A word as a pattern: "garry|gareth" matches either in the word's place."""
    alts = [re.escape(x) for x in w.split("|") if x]
    return alts[0] if len(alts) == 1 else "(?:" + "|".join(alts) + ")"


def base_term(text: str) -> str:
    """The text with each word's alternatives dropped to the first, as typed."""
    return " ".join(w.split("|")[0] for w in (text or "").split() if w.split("|")[0])


def add_alternative(text: str, typed: str, variant: str) -> str:
    """`text` with `variant` added as an alternative to its first word whose
    first form folds to `typed` (ruling 92 (4): an "or" within the name's place)."""
    words = (text or "").split()
    for i, w in enumerate(words):
        forms = w.split("|")
        if cat.fold_term(forms[0]).strip(".,;") == typed:
            if variant not in [cat.fold_term(f) for f in forms]:
                words[i] = w + "|" + variant
            break
    return " ".join(words)


def drop_alternative(text: str, variant: str) -> str:
    """`text` with `variant` taken out of every word's alternatives (never a word's first form)."""
    out = []
    for w in (text or "").split():
        forms = w.split("|")
        out.append("|".join([forms[0]] + [f for f in forms[1:] if cat.fold_term(f) != variant]))
    return " ".join(out)


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
    return [a for a in (_alternatives(w) for w in re.split(r"[\s,;.]+", cat.fold_term(value or ""))) if a]


def phrase(value: str) -> str:
    """The pattern for a field's words in a row, together and whole: de lu matches DE LU, never DELUCA;
    a word with alternatives matches any of them in its place."""
    return r"\m" + r"\s+".join(word_re(w) for w in field_words(value)) + r"\M"


def whole_words(expr: str, value: str) -> tuple:
    """Every word of `value` a whole word of `expr`."""
    ws = field_words(value)
    return " and ".join(f"{expr} ~ %s" for _ in ws), [r"\m" + word_re(w) + r"\M" for w in ws]


#: post-nominals and a trailing "MP" are not part of a name (keys.names._POST, through the board's copy)
_POST_SQL = fold._POST.pattern.replace(r"\b", r"\y")
#: what may follow the family name at the end of a given-first name: a bracket ("(Acting)", "(H)"), a
#: post-nominal the end-cut left before one ("Dean MP (H)"), punctuation
_TAIL = r"(?:\s*\([^)]*\)|,?\s+(?:kc|qc|mp|jp|onzm|cnzm|dnzm|knzm|mnzm|qso|qsm)\M\.?)*\W*$"


def name_patterns(field: str, value: str, order: str) -> tuple:
    """(no comma, with a comma, one word) patterns for a name field over a
    one-string name read in its view's order (ruling 85), applied after an
    honorific is cut from the front and post-nominals from the end.

    With a comma ("Family, Given") in any order, the family is before it,
    the first name is the first word after it, a middle name a later one.
    With no comma: GIVEN_FAMILY puts the first name first, the last name at
    the end, a middle name between; FAMILY_GIVEN puts the last name first
    and the given names after it (where the family name ends is not marked,
    so a first name is any word after the first and a middle name any after
    the second); AMBIGUOUS lets a first or last name be any word, and a
    middle name any word but the first of a name of three words or more.
    A one-word name is matched by a first or last name (None for a middle)."""
    p = phrase(value)
    if field == "first":
        comma, one = r",\s*" + p, p
        plain = {cat.GIVEN_FAMILY: r"^\W*" + p + r"\S*\s+\S", cat.FAMILY_GIVEN: r"\S\s+\S*" + p}.get(order, p)
    elif field == "last":
        comma, one = "^[^,]*" + p, p
        plain = {cat.GIVEN_FAMILY: r"\S\s+\S*" + p + _TAIL, cat.FAMILY_GIVEN: r"^\W*" + p + r"\S*\s+\S"}.get(order, p)
    else:
        comma, one = r",\s*\S+\s+.*" + p, None
        plain = {cat.GIVEN_FAMILY: r"\S\s+\S*" + p + r"\S*\s+\S",
                 cat.FAMILY_GIVEN: r"\S\s+\S+\s+\S*" + p}.get(order, r"^(?=\W*\S+\s+\S+\s+\S).*\S\s+\S*" + p)
    return plain, comma, one


def stripped_sql(col: str) -> str:
    """A one-string name folded, its honorifics cut from the front and its post-nominals from the end."""
    return f"regexp_replace(regexp_replace({fold_sql(col)}, %s, ''), %s, '')"


def _name_whole(g: cat.Name, want: dict) -> tuple:
    """A one-string name: every name field asked, by name_patterns in the Name's order."""
    n = stripped_sql(g.whole)
    parts, params = [], []
    for f in NAME_FIELDS:
        if not want.get(f):
            continue
        plain, comma, one = name_patterns(f, want[f], g.order)
        alt = f"({n} !~ ',' and {n} ~ %s) or ({n} ~ ',' and {n} ~ %s)"
        ps = [_HON_SQL, _POST_SQL, _HON_SQL, _POST_SQL, plain, _HON_SQL, _POST_SQL, _HON_SQL, _POST_SQL, comma]
        if one:
            alt += f" or ({n} !~ %s and {n} ~ %s)"
            ps += [_HON_SQL, _POST_SQL, r"\S\s+\S", _HON_SQL, _POST_SQL, one]
        parts.append(f"({fold_sql(g.whole)} ~ %s and (" + alt + "))")     # the cheap whole-word test first
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


#: how the filled fields combine (ruling 92 (6)): every one must match, or any one may
ALL, ANY = "all", "any"
MODES = ((ALL, "all fields must match"), (ANY, "any field may match"))


def _name_clause(fs: cat.Fields, want: dict):
    """The name fields asked, over every Name of the view (any one of them, all the fields in that one)."""
    alts, aps = [], []
    for g in fs.names:
        got = _name_whole(g, want) if g.whole else _name_parts(g, want)
        if got:
            alts.append("(" + got[0] + ")")
            aps += got[1]
    return ("(" + " or ".join(alts) + ")", aps) if alts else None


def field_clauses(v: cat.View, fields: dict, mode: str = ALL) -> list:
    """[(the fields it reads, clause or None, params)] for the filled fields
    over one view, None where the view holds no column for them (or the year
    is not four digits). With ALL the name fields are one clause, all of them
    in one Name; with ANY each field is its own (ruling 92 (6))."""
    fs = cat.fields_of(v)
    out = []
    want = {f: fields[f] for f in NAME_FIELDS if fields.get(f) and field_words(fields[f])}
    for part in ([{f: x} for f, x in want.items()] if mode == ANY else [want] if want else []):
        got = _name_clause(fs, part)
        out.append((tuple(part), *(got or (None, []))))
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
        out.append((("org",), "(" + " or ".join(alts) + ")" if alts else None, aps))
    if fields.get("address") and field_words(fields["address"]):
        if fs.address:
            c, ps = whole_words(fold_sql("concat_ws(' ', " + ", ".join(fs.address) + ")"), fields["address"])
            out.append((("address",), "(" + c + ")", ps))
        else:
            out.append((("address",), None, []))
    if (fields.get("year") or "").strip():
        y = year_of(fields["year"])
        if y is None or not (fs.year or fs.dates):
            out.append((("year",), None, []))
        else:
            alts = [f"{c} = %s" for c in fs.year] + [f"extract(year from {c}) = %s" for c in fs.dates]
            out.append((("year",), "(" + " or ".join(alts) + ")", [y] * len(alts)))
    return out


def fields_sql(v: cat.View, fields: dict, mode: str = ALL):
    """(clause, params) for the filled fields over one view. ALL: every
    field "and" the others, None when the view holds no column for one of
    them (or the year is not four digits), so the view is not searched.
    ANY (ruling 92 (6)): any field it holds a column for, "or" the others;
    None when it holds none."""
    got = field_clauses(v, fields, mode)
    if mode == ANY:
        got = [g for g in got if g[1] is not None]
        if not got:
            return None
        return "(" + " or ".join(c for _, c, _ in got) + ")", [p for _, _, ps in got for p in ps]
    if any(c is None for _, c, _ in got):
        return None
    return " and ".join(c for _, c, _ in got), [p for _, _, ps in got for p in ps]


def matched_sql(v: cat.View, fields: dict) -> tuple:
    """(select expressions, params): under ANY, one boolean column per field
    clause, `_matched_<field>`, so the results say which field a row matched."""
    exprs, params = [], []
    for fs, c, ps in field_clauses(v, fields, ANY):
        if c is not None:
            exprs.append(f", coalesce({c}, false) as _matched_{fs[0]}")
            params += ps
    return "".join(exprs), params


def match_sql(v: cat.View, words: list, number: str = None, whole: bool = False, fields: dict = None, mode: str = ALL):
    """(clause, params): the search box's words (each begins a word of the
    row's search columns; with `whole`, is a whole word) or its number, "and"
    the filled fields. ("true", []) when nothing is asked; None when the view
    cannot hold a field asked for."""
    haystack = fold_sql("concat_ws(' ', " + ", ".join(v.search) + ")")
    where, params = [], []
    for w in words:
        where.append(f"{haystack} ~ %s")
        params.append(r"\m" + word_re(w) + (r"\M" if whole else ""))
    clause = "(" + " and ".join(where) + ")" if where else ""
    if number and v.numbers:
        clause = "(" + (clause or "false") + " or " + " or ".join(f"{c} = %s" for c in v.numbers) + ")"
        params += [number] * len(v.numbers)
    if fields and any((fields.get(f) or "").strip() for f, _ in FIELDS):
        got = fields_sql(v, fields, mode)
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
             whole: bool = False, fields: dict = None, mode: str = ALL):
    """(sql, params): the matching rows of one view with the view's total
    as `total` on every row. Each word must begin a word in the row's
    search columns ("hart" finds HART and HARTLEY); with `whole`, each must
    be a whole word (a namesake search: HART is not HARTLEY). The filled
    fields (ruling 82) narrow it further; None when the view holds no
    column for one of them. Under ANY (ruling 92 (6)) a row matches on
    any filled field, and carries `_matched_<field>` for each."""
    got = match_sql(v, words, number, whole, fields, mode)
    if got is None:
        return None
    clause, params = got
    if not words and not number and clause == "true":
        clause = "false"                 # nothing asked finds nothing
    g, gp = guard_sql(v, exclude_key)
    sel, sp = matched_sql(v, fields) if mode == ANY and fields else ("", [])
    sql = (f"select *, {v.key_col} as key, count(*) over () as total{sel} from pub.{v.name} where {clause}{g} "
           f"order by {v.default_order} nulls last, {v.key_col} limit %s")
    return sql, sp + params + gp + [limit]


def held_registers(held: set) -> list:
    """The registers, in the catalogue's order, that have at least one view published."""
    return [r for r, _ in cat.REGISTERS if any(v.name in held for v in cat.views_of(r))]


TABLE_PAGE = 100     # rows a register's table shows, and each "more" appends (ruling 92 (5))
TABLE_MAX = 1000     # rows a table shows at most; past it, search


class Boxes(NamedTuple):
    """The left pane's check boxes (ruling 81): "search all" and the register
    boxes are two separate states, so turning "search all" off and on loses
    no tick; and the filled fields of the expanded search (ruling 82),
    `fields` as (parameter, value) in FIELDS order; the register table open
    (ruling 92 (5)), `table` its view and `upto` the offset of its last
    page appended; `mode`, how the fields combine (ruling 92 (6): "all",
    else "any", written only when "any"). All travel as query parameters on
    every href (`params`)."""
    all: bool = True
    ticked: tuple = ()
    fields: tuple = ()
    table: str = ""
    upto: int = 0
    mode: str = "all"

    def params(self) -> list:
        table = [("t", self.table), ("o", str(self.upto))] if self.table else []
        mode = [("mode", self.mode)] if self.mode != ALL else []
        return [("all", "1" if self.all else "0")] + [("r", x) for x in self.ticked] + list(self.fields) + mode + table

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
    table = (qs.get("t") or [""])[0]
    table = table if table in cat.BY_NAME else ""
    o = (qs.get("o") or ["0"])[0]
    upto = min(max(int(o) // TABLE_PAGE * TABLE_PAGE, 0), TABLE_MAX - TABLE_PAGE) if o.isdigit() and table else 0
    mode = ANY if (qs.get("mode") or [""])[0] == ANY else ALL
    return Boxes("1" in alls if alls else not ticked, ticked, fields, table, upto, mode)


def selection(boxes: Boxes, held: list) -> tuple:
    """The registers a search runs over: every held register while "search
    all" is ticked, whatever is ticked below it; the ticked held registers
    alone when it is not, so none ticked searches nothing."""
    return tuple(held) if boxes.all else tuple(r for r in held if r in boxes.ticked)


def search(conn, term: str, limit: int = LIMIT, views=None, exclude_key: str = None, whole: bool = False,
           registers=None, fields: dict = None, mode: str = ALL) -> dict:
    """{register: [(view, total, rows)]} for the views that matched, plus
    'held' (the pub views present) so the caller can say "not held".
    `registers`, when given, scans only those registers' views; `fields`,
    the filled fields of the expanded search ({parameter: value}), narrow it
    (ruling 82): a view with no column for one of them is not scanned;
    `mode` ANY: a row matches on any filled field (ruling 92 (6))."""
    words = words_of(term)
    number = re.sub(r"\s", "", term) if is_number(term) else None
    fields = {f: x for f, x in (fields or {}).items() if (x or "").strip()}
    held = db.pub_views(conn)
    out = {}
    wanted = [v for v in (views or cat.VIEWS) if v.name in held and (words or number or fields)
              and (registers is None or v.register in registers)]
    futures = [_pool.submit(_scan, v, words, number, limit, exclude_key, whole, fields, mode) for v in wanted]
    for f in futures:
        v, found = f.result()
        if found:
            out.setdefault(v.register, []).append((v, int(found[0]["total"]), found))
    out["held"] = held
    return out


def table(conn, v: cat.View, upto: int = 0) -> tuple:
    """(count of all rows, the first upto + TABLE_PAGE rows) of one view in
    its default order (ruling 92 (5)): every row, a suppressed one included,
    for the pane to show as panes.shown() does."""
    total = db.rows(conn, f"select count(*) as n from pub.{v.name}")[0]["n"]
    rows = db.rows(conn, f"select *, {v.key_col} as key from pub.{v.name} "
                         f"order by {v.default_order} nulls last, {v.key_col} limit %s", (min(upto, TABLE_MAX - TABLE_PAGE) + TABLE_PAGE,))
    return int(total), rows


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


def far_rows(conn, pairs, held: set = None) -> dict:
    """{(far view, far column, value): far row, or None where it is not held}
    for every column of the (view, row) pairs that names another view's row
    (catalogue.pointers, ruling 92 (2)): the values collected first, then
    one query per far view for the whole page. A far view not in `held` is
    not asked, and its values read None."""
    want = {}
    for v, r in pairs:
        if v is None or not r:
            continue
        for c, (fv, fc) in cat.pointers(v).items():
            x = r.get(c)
            if x not in (None, ""):
                want.setdefault(fv, {}).setdefault(fc, set()).add(str(x))
    out = {(fv, fc, x): None for fv, cols in want.items() for fc, xs in cols.items() for x in xs}
    for fv, cols in want.items():
        if held is not None and fv not in held:
            continue
        t = cat.BY_NAME[fv]
        cs = sorted(cols)
        where = " or ".join(f"{fc} = any(%s)" for fc in cs)
        for r in db.rows(conn, f"select *, {t.key_col} as key from pub.{fv} where {where}", [sorted(cols[fc]) for fc in cs]):
            for fc in cs:
                k = (fv, fc, str(r.get(fc)))
                if k in out and out[k] is None:
                    out[k] = r
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
