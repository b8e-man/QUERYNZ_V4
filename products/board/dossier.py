"""The dossier (ruling 110): one entity, or one lone row, on one pane, as the
old estate's DossierView gave it (its shape, not its code), built from the
published views and the links lane's tables alone: `pub.groups`,
`pub.links`, `pub.names`, `pub.decisions`. The board makes no link by
looking (plan 4.9); the estate has no claims lane yet, so there is no
claims section until one publishes.

What it shows: the name (the fullest filed, ruling 105's decision 1, said to
be no link) and its count; the names as filed, each with its count of rows;
the rows by register as a timeline, each with its role, the company or body
its register names, its dates and its citation, its own pane beside it; the
companies and bodies it holds a role on, in date order; its money as filed,
donations by year with the year's sum of the filed amounts the view lets be
added and every addend listed (the board sums nothing it does not show),
disclosures listed and never added, declared interests by year; related
companies (the related grade, the relation as the column says it); near
matches with their reasons; contested and every decision, said; the subject
report's address (products/report: `/report/<ref>`).

A row in a group opens its group's dossier. A row whose name is suppressed
is never gathered or named (hard limit 16): chosen, the pane says so and
names nothing; inside a group it is left out, as people.entity leaves it.
Text is shown whole and a flagged column carries its flag (ruling 102).

Every query is by row key or group id: people.entity's (groups_pkey,
groups_group, rows_pkey, the views' keys, links_row_a_row_b_rule_key,
links_row_b, decisions_rows), one per far view by its key or the column a
relation names, the declared interests by their return, and the documents'
states in one read."""
from __future__ import annotations

import datetime as dt
import decimal
import re
import urllib.parse

from products.board import catalogue as cat
from products.board import collapse, db, document, facts, graph, lineage, links_view, panes, people, search

ENTITY = people.ENTITY
MANY_AT = 300               # a group of more rows than this is shown by view (the many-rows shape); at or under it, whole as before
VIEW_ROWS = 50              # rows read per view in the many-rows shape, newest first; the rest a page of this many at a time
TIMELINE_ROWS = 40          # the newest rows the many-rows timeline lists; the rest counted, and reached by view
FOLD_GATHERED = 20          # a fold's members whose own dossier is gathered and shown under their names; the rest open their own
OPEN_AT = 40                # a register's rows open on the pane up to this many; past it closed to its name and count
NO_CLAIMS = "No claims lane has published yet: there is no claims section until one does"
NOT_A_LINK = ("Built from the published views and the links lane's tables alone (pub.groups, pub.links, pub.names, "
              "pub.decisions); the board makes no link by looking.")
MONEY_NOTE = ("As filed: each year's sum is of the amounts filed in the rows listed under it that the view lets be added "
              "(a return's donations); a disclosure is listed beside them and never added, its gift is also in that "
              "year's return; a row replaced by an amendment, or with no amount, is listed and not added. Nothing else is summed.")


def parse(d: str) -> str:
    """The chosen entity or row from the address (`d=`): `entity:<group id>`,
    `<view>:<key>` of a catalogued view, or a fold of the collapse section
    (`fold:<criteria>:<members>`, collapse.fold_id); '' for anything else."""
    d = (d or "").strip()
    if d.startswith(collapse.PREFIX):                  # ruling 112: a folded entry of the collapse section
        d = d[:8000]
        return d if collapse.parse(d) else ""
    d = d[:300]
    if d.startswith(ENTITY):
        return d if len(d) > len(ENTITY) else ""
    view, _, key = d.partition(":")
    return f"{view}:{key}" if view in cat.BY_NAME and key else ""


href = panes.dossier_href


def fragment_href(d: str, q: str = "", boxes=None) -> str:
    """GET /dossier: the pane alone, which graph.js puts under the graph."""
    return base(q, boxes) + "&" + urllib.parse.urlencode([("d", d)])


# ── gathering ───────────────────────────────────────────────────────────────

def first_date(v: cat.View, r: dict):
    """The row's first dated column as the timeline orders it, a year column
    of a gift view else; None where the row carries no date."""
    for _, c in v.dates:
        x = r.get(c)
        if isinstance(x, dt.datetime):
            return x.date()
        if isinstance(x, dt.date):
            return x
    gift = cat.GIFT_OF.get(v.name)
    y = graph.year_of(gift, r) if gift else r.get("year") if isinstance(r.get("year"), int) else None
    return dt.date(y, 1, 1) if isinstance(y, int) and 1000 < y < 3000 else None


def when_text(v: cat.View, r: dict) -> str:
    """The timeline's date: the day of a dated column, the year alone where the row files only a year."""
    for _, c in v.dates:
        if isinstance(r.get(c), (dt.date, dt.datetime)):
            return first_date(v, r).isoformat()
    y = year_of(v, r)
    return str(y) if y else "undated"


def year_of(v: cat.View, r: dict):
    gift = cat.GIFT_OF.get(v.name)
    if gift:
        return graph.year_of(gift, r)
    x = first_date(v, r)
    return x.year if x else None


def bodies(conn, rows: list) -> dict:
    """{(view, key of the row, relation index): (far view, far row)}: the
    company or body each row's relations name, one query per far view and
    column over every row at once; a relation matched to a column many far
    rows share reads one row per value, not every row (a member's 10,000
    turns were read to keep one, 31 October 2026)."""
    want = {}
    for _, v, r in rows:
        for i, rel in enumerate(v.relations):
            x = r.get(rel.column)
            if x not in (None, "") and rel.view in cat.BY_NAME:
                want.setdefault((rel.view, rel.to_column), set()).add(str(x))
    found = {}
    for (view, column), values in want.items():
        fv = cat.BY_NAME[view]
        col = fv.key_col if column == "key" else column
        if col == fv.key_col:
            sql = f"select *, {fv.key_col} as key from pub.{fv.name} where {col}::text = any(%s)"
        else:                                          # a column many rows share (a member's turns): the first row of each value, by its index
            sql = (f"select r.*, r.{fv.key_col} as key from unnest(%s::text[]) x(x), "
                   f"lateral (select * from pub.{fv.name} where {col}::text = x.x limit 1) r")
        for fr in db.rows(conn, sql, (sorted(values),)):
            found.setdefault((view, column, str(fr.get(col) if column != "key" else fr["key"])), (fv, fr))
    out = {}
    for _, v, r in rows:
        for i, rel in enumerate(v.relations):
            hit = found.get((rel.view, rel.to_column, str(r.get(rel.column))))
            if hit:
                out[(v.name, str(r["key"]), i)] = hit
    return out


def interests_of(conn, rows: list) -> list:
    """[(view, row)]: the declared interests (pub.mp_interests) of the
    returns among `rows`, and the interest rows among them: one query by
    the returns' keys."""
    v = cat.BY_NAME["mp_interests"]
    returns = sorted({str(r["key"]) for _, rv, r in rows if rv.name == "mp_interest_returns"})
    own = {str(r["key"]): (rv, r) for _, rv, r in rows if rv.name == "mp_interests"}
    if returns:
        for r in db.rows(conn, f"select *, {v.key_col} as key from pub.{v.name} where member_return = any(%s) "
                               "order by as_at, key", (returns,)):
            own.setdefault(str(r["key"]), (v, r))
    return sorted(own.values(), key=lambda x: (x[1].get("as_at") or dt.date.min, str(x[1]["key"])))


def gather(conn, d: str, report_url: str = "", view: str = "", offset: int = 0) -> dict:
    """The dossier's data for `d` (parse): {'kind': entity | row | suppressed
    | none, 'chosen', 'why', 'group_id', 'describe', 'rows' [(ref, view,
    row)], 'names', 'links', 'near', 'near_total', 'related', 'decisions',
    'far' (rows the links name, resolved), 'bodies', 'interests', 'docs',
    'report', 'via' (the title of the row chosen when it opened its group)};
    a group of more than MANY_AT rows is read by view (gather_many), `view`
    and `offset` paging that view's rows."""
    d = parse(d)
    if not d:
        return {"kind": "none", "chosen": "", "why": "nothing chosen: click a result or tap a node"}
    if d.startswith(collapse.PREFIX):
        return gather_fold(conn, d, report_url)
    via = ""
    if d.startswith(ENTITY):
        gid = d[len(ENTITY):]
    else:
        view, key = d.split(":", 1)
        v = cat.BY_NAME[view]
        r = search.row(conn, view, key)
        if r is None:
            return {"kind": "none", "chosen": d, "why": "row not found in the published view: its key has moved or it was withdrawn"}
        if panes.is_suppressed(v, r):                  # hard limit 16: never gathered, never named
            return {"kind": "suppressed", "chosen": d, "why": "this row's name is suppressed: no dossier gathers it (hard limit 16); "
                                                              "the row and its figures stay in its register"}
        ref = links_view.ref(v, r["key"])
        hit = people.groups_of(conn, [ref]).get(ref)
        if hit is None:
            return lone(conn, d, ref, v, r, report_url)
        gid, via = hit[0], panes.title_of(v, r)
    c = counted(conn, gid)                         # one statement: the group's size, and past MANY_AT its counts and keys
    if c["total"] > MANY_AT:
        return gather_many(conn, gid, c, d, via, report_url, view, offset)
    ent = people.entity(conn, gid)
    if ent is None:
        return {"kind": "none", "chosen": d, "why": "no group has that id in pub.groups: the links lane has rebuilt its groups since"}
    refs = [ref for ref, _, _ in ent["rows"]]
    names = ent.get("names") or {}
    return finish(conn, {**ent, "kind": "entity", "chosen": d, "via": via,
                         "report": panes.report_href(report_url, gid if gid in refs else (refs[0] if refs else gid)),
                         "names": count_names([(names.get(ref) or panes.title_of(v, r)) for ref, v, r in ent["rows"]])})


# ── many rows: counted in SQL, read by view ─────────────────────────────────

def hidden_sql(v: cat.View) -> str:
    """The SQL test, on the view's row `r`, that its name is suppressed or
    hidden (hard limit 16), as panes.is_suppressed reads it."""
    out = []
    if v.suppressed:
        out.append(f"coalesce(r.{v.suppressed}::text, '') not in ('', 'false')")
    if v.hide_names:
        out.append(f"coalesce(r.{v.hide_names[0]}::text, '') ~* '{v.hide_names[1].replace(chr(39), chr(39) * 2)}'")
    return "(" + " or ".join(out) + ")" if out else "false"


def date_sql(v: cat.View) -> str:
    """The row's first date as first_date reads it, in SQL: its dated columns,
    then a gift view's year columns, then a `year` field, as a date."""
    parts = [f"r.{c}::date" for _, c in v.dates]
    gift = cat.GIFT_OF.get(v.name)
    years = [c for c in (gift.years if gift else ()) if c not in {c for _, c in v.dates}]
    if not gift and "year" in {c for _, c in v.fields}:
        years.append("year")
    parts += [f"make_date(r.{c}::int, 1, 1)" for c in years]
    return f"coalesce({', '.join(parts)})" if parts else "null::date"


def counted(conn, gid: str) -> dict:
    """The group's rows counted in SQL, none gathered: {'views': [(view, rows
    shown)] in the catalogue's register order, 'names': [(name as filed,
    rows)] over the shown rows, 'keys' {view: [key]} the shown rows' keys,
    'hidden' and 'hidden_by' {view: rows} (suppressed: for the check's sums alone, never shown),
    'unread' (rows no catalogued view holds), 'total' (every row of the
    group) and 'contested'}. One statement for the group (pub.groups joined
    to pub.names once, by group id, the keys gathered per view and name),
    then one per view that can suppress, by those keys: the group's 30,849
    rows are never joined again (31 October 2026: the join ran once per
    view and once per gift view, 0.08 s each)."""
    by, keys, filed_of = {}, {}, {}
    total, contested = 0, False
    for r in db.rows(conn, "select n.view, n.name_filed, count(*) as n, array_agg(n.key) filter (where n.key is not null) as keys, "
                           "bool_or(g.contested) as contested from pub.groups g left join pub.names n on n.ref = g.row_key "
                           "where g.group_id = %s group by 1, 2", (gid,)):
        total += int(r["n"])
        contested = contested or bool(r["contested"])
        by.setdefault(r["view"], {})[r["name_filed"] or ""] = int(r["n"])
        if r["view"] is not None and r["view"] in cat.BY_NAME:
            keys.setdefault(r["view"], []).extend(r["keys"] or [])
            filed_of.setdefault(r["view"], {}).update({k: r["name_filed"] or "" for k in r["keys"] or []})
    hidden = unread = 0
    hidden_by = {}
    for view, ks in keys.items():
        v = cat.BY_NAME[view]
        if not (v.suppressed or v.hide_names) or not ks:
            continue
        found = {str(r["key"]) for r in db.rows(conn, f"select r.{v.key_col}::text as key from pub.{v.name} r "
                                                     f"where r.{v.key_col}::text = any(%s) and {hidden_sql(v)}", (ks,))}
        if found:
            keys[view] = [k for k in ks if k not in found]
            for k in found:
                by[view][filed_of[view][k]] -= 1
            hidden += len(found)
            hidden_by[view] = hidden_by.get(view, 0) + len(found)
    names, views = {}, []
    order = {r: i for i, (r, _) in enumerate(cat.REGISTERS)}
    for view, filed in by.items():
        if view is None or view not in cat.BY_NAME:
            unread += sum(filed.values())
            continue
        n = sum(filed.values())
        if n:
            views.append((cat.BY_NAME[view], n))
        for name, k in filed.items():
            if k > 0:
                names[name] = names.get(name, 0) + k
    views.sort(key=lambda vn: (order.get(vn[0].register, len(order)), -vn[1], vn[0].name))
    return {"views": views, "names": tally(names.items()), "keys": keys,
            "hidden": hidden, "hidden_by": hidden_by, "unread": unread, "total": total, "contested": contested}


def tally(pairs) -> list:
    """count_names over (name as filed, rows) pairs already counted."""
    n = {}
    for x, k in pairs:
        x = re.sub(r"\s+", " ", x or "").strip() or "no name filed"
        n[x] = n.get(x, 0) + k
    return sorted(n.items(), key=lambda kv: (-kv[1], kv[0].lower(), kv[0]))


def view_rows(conn, v: cat.View, keys: list, offset: int = 0, limit: int = VIEW_ROWS) -> list:
    """[(ref, view, row)]: the group's shown rows of one view (`keys`, from
    counted), newest first, a page of `limit` from `offset`. The keys and
    dates alone are read and sorted (a narrow pass over the view's key
    index), then the page's rows by key (an array, so a view built as a
    union reads each part by its index); the first and last day of every
    row ride each row (`_first_day`, `_last_day`, spans). The 29,365 written
    questions of ruling 116's largest group: 0.11 s against 0.17 s through
    the join, whose sort of the whole rows spilled to disk (31 October 2026)."""
    if not keys:
        return []
    d, h = date_sql(v), hidden_sql(v)
    sql = (f"with d as materialized (select r.{v.key_col}::text as key, {d} as d from pub.{v.name} r "
           f"where r.{v.key_col}::text = any(%s) and not {h}), "
           "b as (select min(d) as _first_day, max(d) as _last_day from d), "
           "p as materialized (select key from d order by d desc nulls last, key limit %s offset %s) "
           f"select r.*, b._first_day, b._last_day, r.{v.key_col} as key from pub.{v.name} r cross join b "
           f"where r.{v.key_col}::text = any(array(select key from p)) order by {d} desc nulls last, r.{v.key_col}")
    return [(links_view.ref(v, r["key"]), v, r) for r in db.rows(conn, sql, (list(keys), limit, max(0, offset)))]


def spans(rows: list) -> dict:
    """{view: (first day, last day)} over every shown row of the group of each
    view, as view_rows reads them beside its page (window aggregates over the
    rows it sorts anyway): a many-rows section's head says the years its
    records run (ruling 117)."""
    out = {}
    for _, v, r in rows:
        if v.name not in out and (r.get("_first_day") or r.get("_last_day")):
            out[v.name] = (r.get("_first_day"), r.get("_last_day"))
    return out


def money_counted(conn, views, keys: dict) -> list:
    """[(year or None, sum of the amounts added, how many added, rows filed)]
    over every shown gift row of the group (`keys`, from counted), summed in
    SQL as addends adds: an amount filed, the row not replaced, the view one
    that adds."""
    years = {}
    for v, _ in views:
        gift = cat.GIFT_OF.get(v.name)
        if gift is None or not keys.get(v.name):
            continue
        added = (f"r.{gift.amount} is not null" + (f" and r.{gift.replaced} is null" if gift.replaced else "")) if gift.added else "false"
        year = "coalesce(" + ", ".join(f"extract(year from r.{c})::int" if c in {c for _, c in v.dates} else f"r.{c}::int"
                                       for c in gift.years) + ")"
        for r in db.rows(conn, f"select {year} as year, count(*) as rows, count(*) filter (where {added}) as n, "
                               f"sum(r.{gift.amount}) filter (where {added}) as total from pub.{v.name} r "
                               f"where r.{v.key_col}::text = any(%s) and not {hidden_sql(v)} group by 1", (list(keys[v.name]),)):
            y = years.setdefault(r["year"], [decimal.Decimal(0), 0, 0])
            y[0] += decimal.Decimal(r["total"] or 0)
            y[1] += int(r["n"])
            y[2] += int(r["rows"])
    return [(y, *years[y]) for y in sorted(years, key=lambda y: (y is None, y or 0))]


def gather_many(conn, gid: str, c: dict, d: str, via: str, report_url: str, view: str = "", offset: int = 0) -> dict:
    """A group of more than MANY_AT rows (ruling 116's members hold tens of
    thousands), `c` its counts (counted): its rows counted by view and its
    names and money counted in SQL over every row; the newest VIEW_ROWS of
    each view read (`view` from `offset`), from which the timeline, roles,
    links and citations are drawn. The results pane's shape (ruling 108):
    by view, each collapsed to its count. A suppressed row is never read,
    named or counted on the page; its number is kept for the check alone
    ('hidden_count')."""
    rows, pages = [], {}
    for v, k in c["views"]:
        at = min(max(0, offset), max(0, k - 1)) if v.name == view else 0
        pages[v.name] = at
        rows += view_rows(conn, v, c["keys"].get(v.name, []), at)
    refs = [ref for ref, _, _ in rows]
    shown = sum(k for _, k in c["views"])
    registers = {v.register for v, _ in c["views"]}
    own = people.links_among(conn, refs)
    near = people.near_of(conn, refs)
    describe = {"group_id": gid, "label": people.fullest(nm for nm, _ in c["names"]) or f"group {gid}",
                "rows": shown, "registers": len(registers), "count": people.count_words(shown, len(registers)),
                "contested": c["contested"], "number": people.number_of(own)}
    return finish(conn, {"kind": "entity", "many": True, "chosen": d, "via": via, "group_id": gid, "total": c["total"],
                         "describe": describe, "rows": rows, "views": c["views"], "pages": pages, "opened": view if view in pages else "",
                         "hidden_count": c["hidden"], "hidden_by": c["hidden_by"], "unread": c["unread"], "hidden": set(), "names": c["names"],
                         "money_counted": money_counted(conn, c["views"], c["keys"]), "spans": spans(rows),
                         "links": own, "near": near[:people.PANE_NEAR], "near_total": len({(l["row_a"], l["row_b"], l["rule"]) for l in near}),
                         "related": lineage.related_of(conn, refs), "decisions": people.decisions_of(conn, refs),
                         "report": panes.report_href(report_url, gid)})


def gather_fold(conn, d: str, report_url: str = "") -> dict:
    """A folded entry of the collapse section (ruling 112): its members as the
    entities they are, each its name, counts, registers and its own dossier;
    the criteria that folded them, said to be no link. The first FOLD_GATHERED
    members carry their own dossier's data ('dossier': `gather` of the member,
    an entity's or a lone row's), so the pane shows what each member's records
    say under its name without another click; the rest open their own.
    Reads pub.groups and the rows by key; writes nothing. A suppressed member
    is counted, never named."""
    by, ids = collapse.parse(d)
    gids = [m[len(ENTITY):] for m in ids if m.startswith(ENTITY)]
    ents = people.gather(conn, [], {g: set() for g in gids})
    members, hidden, centre = [], 0, ""
    for m in ids:
        if m.startswith(ENTITY):
            e = ents["entity"].get(m[len(ENTITY):])
            if e is None:
                hidden += 1
                continue
            members.append({"id": m, "label": e["label"], "what": e.get("what") or "", "rows": e["rows"], "contested": e["contested"],
                            "registers": e.get("registers_named") or []})
            centre = centre or e.get("centre") or ""
            continue
        view, _, key = m.partition(":")
        r = search.row(conn, view, key) if view in cat.BY_NAME else None
        if r is None or panes.is_suppressed(cat.BY_NAME[view], r):
            hidden += 1
            continue
        v = cat.BY_NAME[view]
        members.append({"id": m, "label": panes.title_of(v, r), "what": facts.what_it_is([(v, r)]), "rows": 1, "contested": False,
                        "registers": [panes.REGISTER_NAME.get(v.register, v.register)]})
        centre = centre or m
    opened = set()
    for m in members[:FOLD_GATHERED]:                    # the member's own dossier, as its own address opens it
        own = gather(conn, m["id"], report_url)
        if own.get("kind") not in ("entity", "row"):
            continue
        key = own.get("group_id") or m["id"]
        if key in opened:                                # a fold of rows: six rows of one group open one dossier, shown once
            m["shown_above"] = True
            continue
        opened.add(key)
        m["dossier"] = own
    return {"kind": "fold", "chosen": d, "by": by, "members": members, "hidden": hidden, "centre": centre,
            "label": collapse.label([x["label"] for x in members if x["id"].startswith(ENTITY)],
                                    [x["label"] for x in members if not x["id"].startswith(ENTITY)]) or "collapsed here"}


def fold_pane(x: dict, q: str = "", boxes=None) -> str:
    """The dossier of a folded entry: the members listed as the entities they
    are, each opening its own dossier, and under each member's name what its
    records say (its own dossier's timeline, and its money where it has any),
    for the first FOLD_GATHERED members; the rest are listed and open their own."""
    out = [_head(x["chosen"], q, boxes), '<div class="reg">dossier · collapsed here, for this view alone</div>',
           f"<h2>{panes.esc(x['label'])}</h2>",
           f'<p class="fold">{panes.esc(collapse.words(x["by"]))}</p>',
           f'<p class="small">{len(x["members"])} entities. {panes.esc(collapse.NOTE)}</p>',
           f'<h3 id="d-members">Its members, each the entity it is <span class="count">{len(x["members"])}</span></h3><ul class="members">']
    for i, m in enumerate(x["members"]):
        out.append(f'<li><a class="row" href="{panes.esc(href(m["id"], q, boxes))}">{panes.esc(m["label"])}</a> '
                   f'<div class="what">{panes.esc(m["what"])}' + (' · <span class="warn">contested</span>' if m["contested"] else "")
                   + f'</div><div class="meta">from {panes.esc("; ".join(m["registers"]))}</div>')
        own = m.get("dossier")
        if m.get("shown_above"):
            out.append('<div class="note">one of the records shown under its entity above</div>')
        if own:                                           # what this member's records say, under its name
            out.append('<div class="member-rows">')
            out += timeline(own, q, boxes, ident=f"m{i}-rows")
            if own.get("many") or addends(own):
                out += money(own, q, boxes, ident=f"m{i}-money")
            out.append("</div>")
        out.append("</li>")
    out.append("</ul>")
    if len(x["members"]) > FOLD_GATHERED:
        out.append(f'<p class="note">the records of the first {FOLD_GATHERED} members are shown here; '
                   f'the other {len(x["members"]) - FOLD_GATHERED} open their own dossier</p>')
    if x["hidden"]:
        out.append(f'<p class="note">{x["hidden"]} more member{"s" if x["hidden"] != 1 else ""} not named: suppressed, or no longer held</p>')
    out.append("</section>")
    return "".join(out)


def lone(conn, d: str, ref: str, v: cat.View, r: dict, report_url: str) -> dict:
    """A row in no group: its own dossier, read as an entity of one row."""
    filed = db.rows(conn, "select name_filed from pub.names where ref = %s", (ref,))
    name = (filed[0]["name_filed"] if filed else "") or panes.title_of(v, r)
    near = people.near_of(conn, [ref])
    return finish(conn, {"kind": "row", "chosen": d, "via": "", "group_id": "", "rows": [(ref, v, r)], "links": [],
                         "describe": {"label": people.fullest([name]) or panes.title_of(v, r), "count": people.count_words(1, 1),
                                      "contested": False, "number": ""},
                         "near": near[:people.PANE_NEAR], "near_total": len({(l["row_a"], l["row_b"], l["rule"]) for l in near}),
                         "related": lineage.related_of(conn, [ref]), "decisions": people.decisions_of(conn, [ref]),
                         "hidden": set(), "names": count_names([name]), "report": panes.report_href(report_url, ref)})


def finish(conn, x: dict) -> dict:
    """The far rows the links name, the bodies, the interests and the documents' states."""
    mine = {ref for ref, _, _ in x["rows"]}
    others = {l["row_b"] if l.get("mine", l["row_a"]) == l["row_a"] else l["row_a"] for l in x["near"]}
    others |= {l["row_a"] for l in x["decisions"]} | {l["row_b"] for l in x["decisions"]}
    for l in x.get("related") or []:
        others |= {l["row_a"], l["row_b"]} | {p.get(k) for p in lineage.evidence(l).get("shared_rows") or []
                                              for k in ("earlier", "later") if p.get(k)}
    far = people.resolve_refs(conn, others - mine - set(x.get("hidden") or ()))
    x["far"] = {ref: hit for ref, hit in far.items() if not panes.is_suppressed(*hit)}
    near_rows = [(ref, *x["far"][ref]) for ref in sorted(x["far"])]
    x["bodies"] = bodies(conn, x["rows"] + near_rows)          # ruling 117: a near row's fact names its body too
    x["referred"] = facts.refer(conn, x["rows"] + near_rows)
    x["interests"] = interests_of(conn, x["rows"])
    x["docs"] = document.statuses(conn, [r.get("document") for _, _, r in x["rows"]] + [r.get("document") for _, r in x["interests"]])
    x["pointed"] = search.far_rows(conn, [(v, r) for _, v, r in x["rows"]] + list(x["interests"]))    # ruling 92 (2), one query per far view
    return x


def count_names(names) -> list:
    """[(name as filed, rows)], most rows first, then the name: a row counted once."""
    n = {}
    for x in names:
        x = re.sub(r"\s+", " ", x or "").strip()
        if x:
            n[x] = n.get(x, 0) + 1
    return sorted(n.items(), key=lambda kv: (-kv[1], kv[0].lower(), kv[0]))


# ── money, as filed ─────────────────────────────────────────────────────────

def addends(x: dict) -> list:
    """[{'year', 'amount', 'what', 'not_added', 'v', 'r', 'to'}]: the gift
    rows among the dossier's rows, as graph.gifts reads them: added only
    where the view adds, the row is not replaced and an amount is filed."""
    out = []
    for _, v, r in x["rows"]:
        gift = cat.GIFT_OF.get(v.name)
        if gift is None:
            continue
        why = ""
        if r.get(gift.amount) is None:
            why = "no amount filed, not added"
        elif gift.replaced and r.get(gift.replaced):
            why = "replaced by an amendment, not added"
        elif not gift.added:
            why = "a disclosure: its gift is also in the year's return, never added to it"
        rel = next((i for i, rel in enumerate(v.relations) if rel.kind == "money"), None)
        out.append({"year": graph.year_of(gift, r), "amount": r.get(gift.amount), "what": gift.what, "not_added": why,
                    "v": v, "r": r, "to": x["bodies"].get((v.name, str(r["key"]), rel)) if rel is not None else None})
    return sorted(out, key=lambda a: (a["year"] or 0, a["v"].name, str(a["r"]["key"])))


def sums(x: dict) -> dict:
    """{year: the sum added}, for the years where something is added: in SQL
    over every row for a many-rows dossier, from the listed addends else."""
    if x.get("many"):
        return {y: total for y, total, k, _ in x["money_counted"] if k}
    return {y: total for y, _, total, k in by_year(addends(x)) if k}


def sum_words(total, n: int) -> str:
    """'$1,500.00, the sum of 2 filed amounts', or 'none added'."""
    return f"{graph.money(total)}, the sum of {n} filed amount{'s' if n != 1 else ''}" if n else "none added"


def by_year(adds: list) -> list:
    """[(year or None, its addends, the sum of the added ones, how many added)]."""
    years = {}
    for a in adds:
        years.setdefault(a["year"], []).append(a)
    out = []
    for y in sorted(years, key=lambda y: (y is None, y or 0)):
        added = [a for a in years[y] if not a["not_added"]]
        out.append((y, years[y], sum((decimal.Decimal(a["amount"]) for a in added), decimal.Decimal(0)), len(added)))
    return out


# ── the pane ────────────────────────────────────────────────────────────────

def _row_href(q, boxes, v, r) -> str:
    return panes.href(q, [f"{v.name}:{r['key']}"], boxes)


def _a(q, boxes, v, r, cls: str = "row") -> str:
    return f'<a class="{cls}" href="{panes.esc(_row_href(q, boxes, v, r))}">{panes.esc(panes.title_of(v, r))}</a>'


def dates_text(v: cat.View, r: dict) -> str:
    return " · ".join(f"{panes.esc(label)} {panes.fmt(r.get(c))}" for label, c in v.dates if r.get(c) not in (None, ""))


def fields_text(v: cat.View, r: dict, pointed: dict = None, q: str = "", boxes=None) -> str:
    """Every field the view shows, whole, its flag beside it (ruling 102); a
    column naming another view's row as that row's name, linked, the key on
    hover (ruling 92 (2), panes.far_cell, from `pointed`, search.far_rows):
    since ruling 111 the dossier is where a row is read."""
    parts = []
    for label, c in v.fields:
        x = panes.shown(v, r, c)
        if x in (None, ""):
            continue
        cell = panes.far_cell(v, r, c, pointed, q, [], boxes)
        parts.append(f"{panes.esc(label)}: {cell if cell is not None else panes.fmt(x, c)}{panes.flag_notes(v, r, c)}")
    return " · ".join(parts)


def role_text(x: dict, v: cat.View, r: dict, q, boxes) -> str:
    """'director of <company>' for each relation the row asserts that names a row held."""
    out = []
    for i, rel in enumerate(v.relations):
        hit = x["bodies"].get((v.name, str(r["key"]), i))
        if hit:
            out.append(f'{panes.esc(rel.label or rel.kind)} {_a(q, boxes, *hit)}')
    return "; ".join(out)


def row_item(x: dict, v: cat.View, r: dict, q, boxes) -> str:
    """One row as filed, under its fact: its date, its pane, its role, its dates, its fields and its citation."""
    role = role_text(x, v, r, q, boxes)
    return (f'<li><span class="when">{panes.esc(when_text(v, r))}</span> '
            f'{panes.struck(v, r, _a(q, boxes, v, r))}'
            + (f'<div>{role}</div>' if role else "")
            + (f'<div class="meta">{dates_text(v, r)}</div>' if dates_text(v, r) else "")
            + (f'<div class="meta">{fields}</div>' if (fields := fields_text(v, r, x.get("pointed"), q, boxes)) else "")
            + panes.citation_line(v, r, x["docs"]) + "</li>")


def fact_item(x: dict, f: dict, q, boxes, bare: bool = False) -> str:
    """One fact (ruling 117): the sentence, the small line (dates, roles,
    counts), the citation line, and the rows as filed closed under it."""
    small = facts.small(f)
    return (f'<li class="fact" data-rows="{len(f["rows"])}"><div class="say">'
            f'{facts.sentence(f, lambda fv, fr: _a(q, boxes, fv, fr, "plain"), bare=bare)}</div>'
            + (f'<div class="small">{small}</div>' if small else "")
            + facts.cite(f, x["docs"])
            + '<details class="asfiled"><summary>as filed</summary><ol class="timeline">'
            + "".join(row_item(x, v, r, q, boxes) for _, v, r in f["rows"]) + "</ol></details></li>")


def page_href(d: str, q: str, boxes, view: str, offset: int) -> str:
    """The search page with the dossier of `d` under its graph, one view's rows
    paged from `offset` (the many-rows shape's way to the rest)."""
    return href(d, q, boxes) + "&" + urllib.parse.urlencode([("dv", view), ("do", max(0, offset))])


def whole_words(x: dict) -> str:
    """'30,836 records of 9 kinds', and the records the board cannot read said
    beside it; a suppressed row is neither counted nor named on the page (hard limit 16)."""
    n, k = sum(c for _, c in x["views"]), len(x["views"])
    out = f"{n:,} record{'s' if n != 1 else ''} of {k} kind{'s' if k != 1 else ''}"
    if x.get("unread"):
        out += f"; {x['unread']:,} more the board does not read"
    return out


def timeline_many(x: dict, q, boxes, ident: str = "d-rows") -> list:
    """The many-rows shape (ruling 108's): the newest rows, the rest counted;
    then every view collapsed to its count and expandable, its head the fact
    the view's rows say over all of them (ruling 117), its page of rows
    folded by what they say, newest first, a page at a time."""
    shown = sum(c for _, c in x["views"])
    newest = sorted(x["rows"], key=lambda rv: (first_date(rv[1], rv[2]) or dt.date.min, rv[1].name, str(rv[2]["key"])),
                    reverse=True)[:TIMELINE_ROWS]
    out = [f'<h3 id="{ident}">What the records say <span class="count">{len(x["views"]):,}</span></h3>',
           f'<p class="note">{panes.esc(whole_words(x))}. Each heading below is one kind of record over all of them, '
           f'and opens to its records newest first, {VIEW_ROWS} at a time.</p>',
           f'<h4>The newest {len(newest):,}</h4><ol class="timeline newest">']
    for ref, v, r in newest:
        f = {**facts.fold(x, [(ref, v, r)], apart=True)[0], "first": None}          # the day is said once, before it
        line = f'<a class="plain" href="{panes.esc(_row_href(q, boxes, v, r))}">{facts.sentence(f)}</a>'
        out.append(f'<li class="newest"><span class="when">{panes.esc(when_text(v, r))}</span> {panes.struck(v, r, line)}</li>')
    out.append("</ol>")
    if shown > len(newest):
        out.append(f'<p class="note">and {shown - len(newest):,} more records: each heading below lists them</p>')
    by_view = {}
    for ref, v, r in x["rows"]:
        by_view.setdefault(v.name, []).append((ref, v, r))
    for v, count in x["views"]:
        at = x["pages"].get(v.name, 0)
        items = by_view.get(v.name, [])
        first, last = (x.get("spans") or {}).get(v.name, (None, None))
        nouns = []
        for _, _, r in items:
            n = facts.card_word(v, r) or ""
            if n and n not in nouns:
                nouns.append(n)
        say, many = facts.view_words(v, count, first, last, nouns)
        head = (f'{say} <span class="small">{many} · {panes.esc(panes.REGISTER_NAME.get(v.register, v.register))} · '
                f'<a href="{panes.esc(panes.table_href(q, boxes, register=v.register))}">its register</a></span>')
        span = f"rows {at + 1:,} to {at + len(items):,} of {count:,}, newest first" if items else "no rows"
        nav = []
        if at > 0:
            nav.append(f'<a href="{panes.esc(page_href(x["chosen"], q, boxes, v.name, at - VIEW_ROWS))}">the newer {min(VIEW_ROWS, at):,}</a>')
        if at + len(items) < count:
            nav.append(f'<a href="{panes.esc(page_href(x["chosen"], q, boxes, v.name, at + VIEW_ROWS))}">'
                       f'the next {min(VIEW_ROWS, count - at - len(items)):,} of {count - at - len(items):,} older</a>')
        lines = sorted(facts.fold(x, items, apart=True), key=lambda f: (f["last"] or f["first"] or dt.date.min), reverse=True)
        out += [f'<details class="dview" data-view="{panes.esc(v.name)}" data-count="{count}"'
                + (" open" if x.get("opened") == v.name else "") + f'><summary>{head}</summary>',
                f'<p class="note">{panes.esc(span)}' + (" · " + " · ".join(nav) if nav else "") + "</p>",
                '<ol class="facts">'] + [fact_item(x, f, q, boxes, bare=True) for f in lines] + ["</ol></details>"]
    return out


def timeline(x: dict, q, boxes, ident: str = "d-rows") -> list:
    """The rows folded by what they say about the entity (ruling 117), one
    entry per fact in date order, each row as filed closed under its fact.
    `ident` is the heading's id: a fold's pane carries one timeline per member."""
    if x.get("many"):
        return timeline_many(x, q, boxes, ident)
    fs = facts.fold(x)
    return ([f'<h3 id="{ident}">What the records say <span class="count">{len(fs):,}</span></h3>', '<ol class="facts">']
            + [fact_item(x, f, q, boxes) for f in fs] + ["</ol>"])


def money(x: dict, q, boxes, ident: str = "d-money") -> list:
    adds = addends(x)
    out = [f'<h3 id="{ident}">Money, as filed</h3>', f'<p class="note">{panes.esc(MONEY_NOTE)}</p>', "<h4>Donations, by year</h4>"]
    if x.get("many"):
        out += money_many(x, adds, q, boxes)
    elif not adds:
        out.append('<p class="why">none: no row here is a donation in a return or a disclosure</p>')
    else:
        out.append('<table class="money"><tr><th>year</th><th>sum of filed amounts added</th><th>rows</th></tr>')
        for y, items, total, n in by_year(adds):
            out.append(f'<tr><td>{panes.esc(y if y is not None else "year not stated")}</td>'
                       f'<td>{sum_words(total, n)}</td>'
                       f'<td><ul>' + "".join(
                           f'<li>{panes.fmt(a["amount"], "amount")} {panes.esc(a["what"])} '
                           + (f'to {_a(q, boxes, *a["to"], cls="plain")} ' if a["to"] else "")
                           + f'· {_a(q, boxes, a["v"], a["r"], "plain")}'
                           + (f' <span class="note">{panes.esc(a["not_added"])}</span>' if a["not_added"] else "") + "</li>"
                           for a in items) + "</ul></td></tr>")
        out.append("</table>")
    ints = x["interests"]
    out.append(f'<h4>Declared interests, by year <span class="count">{len(ints):,}</span></h4>')
    if not ints:
        out.append('<p class="why">none: no row here is an MP\'s return of interests</p>')
        return out
    years = {}
    for v, r in ints:
        years.setdefault(year_of(v, r), []).append((v, r))
    for y in sorted(years, key=lambda y: (y is None, y or 0)):
        out.append(f'<div class="view"><strong>{panes.esc(y if y is not None else "year not stated")}</strong> '
                   f'<span class="count">{len(years[y]):,}</span></div><ul>')
        for v, r in years[y]:
            out.append(f'<li>{_a(q, boxes, v, r, "plain")}<div class="meta">{fields_text(v, r, x.get("pointed"), q, boxes)}</div>'
                       + panes.citation_line(v, r, x["docs"]) + "</li>")
        out.append("</ul>")
    return out


def money_many(x: dict, adds: list, q, boxes) -> list:
    """The many-rows shape's donations: each year's sum and counts in SQL over
    every row; the addends among the rows read listed, the rest counted."""
    if not x["money_counted"]:
        return ['<p class="why">none: no row here is a donation in a return or a disclosure</p>']
    listed = {}
    for a in adds:
        listed.setdefault(a["year"], []).append(a)
    out = ['<p class="note">Each year summed over every row of the group; the rows listed are those read below, the rest counted.</p>',
           '<table class="money"><tr><th>year</th><th>sum of filed amounts added</th><th>rows</th></tr>']
    for y, total, n, filed in x["money_counted"]:
        items = listed.get(y, [])
        out.append(f'<tr><td>{panes.esc(y if y is not None else "year not stated")}</td><td>{sum_words(total, n)}</td><td><ul>'
                   + "".join(f'<li>{panes.fmt(a["amount"], "amount")} {panes.esc(a["what"])} '
                             + (f'to {_a(q, boxes, *a["to"], cls="plain")} ' if a["to"] else "")
                             + f'· {_a(q, boxes, a["v"], a["r"], "plain")}'
                             + (f' <span class="note">{panes.esc(a["not_added"])}</span>' if a["not_added"] else "") + "</li>"
                             for a in items)
                   + (f'<li class="note">and {filed - len(items):,} more rows filed this year, under their view above</li>'
                      if filed > len(items) else "") + "</ul></td></tr>")
    out.append("</table>")
    return out


def near_part(x: dict, q, boxes) -> list:
    """The near links, folded by what the far rows say (ruling 117): five
    celebrant lists under one name are one entry, said of the name as filed,
    never of the entity; the rule, its reason and the row it leaves from in
    the small line."""
    mine = {ref: (v, r) for ref, v, r in x["rows"]}
    far = x.get("far") or {}
    hidden = set(x.get("hidden") or ())
    inner = [l for l in x["links"] if l["grade"] not in ("confirmed", "related")]
    groups, lost = {}, []
    for l in inner + list(x["near"]):
        m = l.get("mine") or l["row_a"]
        other = l["row_b"] if m == l["row_a"] else l["row_a"]
        if other in hidden:
            continue
        hit = mine.get(other) or far.get(other)
        if not hit:
            lost.append(other)
            continue
        v, r = hit
        g = groups.setdefault((facts.key_of(x, other, v, r), facts.name_of(v, r), str(l["rule"])), {"rows": [], "links": [], "from": []})
        if other not in {ref for ref, _, _ in g["rows"]}:
            g["rows"].append((other, v, r))
        g["links"].append(l)
        if m not in g["from"]:
            g["from"].append(m)
    entries = []
    for (_, name, rule), g in groups.items():
        f = facts.fold(x, g["rows"])[0]
        f["rows"] = sorted(g["rows"], key=lambda rv: (facts.first_day(rv[1], rv[2]) or dt.date.max, str(rv[2]["key"])))
        reasons = []
        for l in g["links"]:
            if l.get("reason") and l["reason"] not in reasons:
                reasons.append(l["reason"])
        frm = ", ".join(_a(q, boxes, *mine[m], cls="plain") if m in mine else f"<code>{panes.esc(m)}</code>" for m in g["from"])
        both = any(ref in mine for ref, _, _ in g["rows"])
        _, v0, r0 = f["rows"][0]
        small = facts.small(f)
        entries.append((f["first"] or dt.date.max, name.lower(),
                        f'<li class="fact near"><div class="say"><a class="row" href="{panes.esc(_row_href(q, boxes, v0, r0))}">'
                        f'{panes.esc(name)}</a>: {facts.sentence(f, lambda fv, fr: _a(q, boxes, fv, fr, "plain"), cap=False)}</div>'
                        f'<div class="small">near, never gathered: {panes.esc(cat.rule_words(rule))} {panes.esc(cat.rule_ref(rule))}'
                        + (f"; because {panes.esc('; '.join(reasons))}" if reasons else "") + f"; from {frm}"
                        + (" (both rows are here)" if both else "") + (f" · {small}" if small else "") + "</div>"
                        + facts.cite(f, x["docs"]) + "</li>"))
    entries.sort(key=lambda e: (e[0], e[1]))
    for other in lost:
        entries.append((dt.date.max, "", f'<li class="fact near"><code>{panes.esc(other)}</code> <span class="note">row not found '
                                         "in the published views, or its name is suppressed</span></li>"))
    out = [f'<h3 id="d-near">Near matches, never gathered <span class="count">{len(entries):,}</span></h3>',
           '<p class="note">A near link is a shared name or circumstance a rule did not take as the same person, '
           "listed with its reason; it never joins the rows. Each line is what the other record says of the name it files.</p>"]
    if not entries:
        out.append('<p class="why">none found</p>')
        return out
    more = x["near_total"] - len(x["near"])
    return out + ['<ol class="facts">'] + [e[2] for e in entries] + (
        [f'<li class="note">and {more:,} more near links from these rows, not read here</li>'] if more > 0 else []) + ["</ol>"]


def decided(x: dict, q, boxes) -> list:
    mine = {ref: (v, r) for ref, v, r in x["rows"]}
    far = x.get("far") or {}
    d = x["describe"]
    out = ['<h3 id="d-decided">Contested and decisions</h3>',
           '<p class="warn">contested: the watch flagged this group as a whole</p>' if d.get("contested")
           else '<p class="note">not contested: the watch has not flagged this group</p>' if x["kind"] == "entity" else
           '<p class="note">in no group, so nothing to contest</p>']
    shown = []
    for z in x["decisions"]:
        a, b = mine.get(z["row_a"]) or far.get(z["row_a"]), mine.get(z["row_b"]) or far.get(z["row_b"])
        if a is None or b is None:
            continue                                   # an end suppressed or not held: the decision names nobody here
        shown.append(f'<li>{_a(q, boxes, *a, cls="plain")} and {_a(q, boxes, *b, cls="plain")}: <strong>{panes.esc(z["verdict"])}</strong>'
                     f' <span class="meta">by {panes.esc(z["made_by"])}, {panes.fmt(z.get("made_at"))}</span></li>')
    out.append(f'<p class="note">{facts.count_words(len(shown), "decision", "decisions")} recorded on a pair of these records</p>')
    if shown:
        out += ["<ul>"] + shown + ["</ul>"]
    return out


def base(q: str = "", boxes=None) -> str:
    """/dossier with the search and the boxes, for graph.js to add `&d=` to."""
    return "/dossier?" + urllib.parse.urlencode([("q", q)] + (boxes.params() if boxes is not None else []))


def _head(chosen: str, q: str, boxes, hidden: bool = False) -> str:
    return (f'<section class="pane dossier" id="dossier" data-chosen="{panes.esc(chosen)}" '
            f'data-base="{panes.esc(base(q, boxes))}"{" hidden" if hidden else ""}>')


def pane(x: dict, q: str = "", boxes=None) -> str:
    """The dossier's pane (`gather`'s data), the section graph.js puts under the graph."""
    if x["kind"] == "fold":
        return fold_pane(x, q, boxes)
    head = _head(x.get("chosen") or "", q, boxes)
    if x["kind"] in ("none", "suppressed"):
        return (head + '<div class="reg">dossier</div><h2>Dossier</h2>'
                f'<p class="why">{panes.esc(x["why"])}</p></section>')
    d = x["describe"]
    entity = x["kind"] == "entity"
    what = facts.what_it_is([(v, r) for _, v, r in x["rows"]] + [(v, None) for v, _ in x.get("views") or ()])
    out = [head, '<div class="reg">dossier</div>', f"<h2>{panes.esc(d['label'])}</h2>",
           f'<p class="what">{panes.esc(what)}' + (f" · {panes.esc(d['number'])}" if d.get("number") else "")
           + (' · <span class="warn">contested</span>' if d.get("contested") else "") + "</p>"]
    if x.get("many"):
        out.append(f'<p class="small whole">{panes.esc(whole_words(x))}</p>')
    links = [f'<a href="{panes.esc(x["report"])}">the full subject report</a>'] if x.get("report") else \
        ['<span class="note">no report server named (QV4_REPORT_URL)</span>']
    if entity:
        links.append(f'<a href="{panes.esc(panes.href(q, [people.entity_id(x["group_id"])], boxes))}">its entity pane</a>')
    out.append('<p class="small">' + (f"Gathered by the links lane's rules. The {panes.esc(panes.ENTITY_LABEL_NOTE)}. " if entity
                                      else "In no group: no links rule joins this record to another. ")
               + (f'Opened from {panes.esc(x["via"])}, one of its records. ' if x.get("via") else "") + " · ".join(links) + "</p>")
    out.append(f'<h3 id="d-names">Names as filed <span class="count">{len(x["names"]):,}</span></h3><ul>'
               + "".join(f'<li>{panes.esc(n)} <span class="small">on {panes.esc(facts.count_words(k, "record", "records"))}</span></li>'
                         for n, k in x["names"]) + "</ul>")
    out += timeline(x, q, boxes)
    out += money(x, q, boxes)
    mine = {ref: (v, r) for ref, v, r in x["rows"]}
    if x.get("related"):
        out.append(panes.related_section(x["related"], set(mine), q, [], lambda ref: mine.get(ref) or x["far"].get(ref), boxes))
    else:
        out.append('<h3 id="related">Related companies <span class="count">0</span></h3><p class="why">none found</p>')
    out += near_part(x, q, boxes)
    out += decided(x, q, boxes)
    out.append(f'<p class="small">{panes.esc(NOT_A_LINK)} {panes.esc(NO_CLAIMS)}.</p>')
    out.append("</section>")
    return "\n".join(out)


def placeholder(q: str = "", boxes=None) -> str:
    """The empty dossier the page carries for graph.js to fill, hidden until it does."""
    return (_head("", q, boxes, hidden=True) + '<div class="reg">dossier</div>'
            '<p class="why">click a result or tap a node to open its dossier here</p></section>')
