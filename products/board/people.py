"""The graph's people state (ruling 105): the rows graph folded into the
entities the links lane gathered. `graph.build` keeps its first step (the
rows and their record relations for the query), then `fold` reads
`pub.groups` for the row keys in hand, draws one node per group in place of
its rows, and rewrites every edge to its group ends, dropping an edge whose
two ends fall in one group and merging duplicates (each cause keeps the row
pairs it was lifted from, so a line's pane lists which rows). A row in no
group stays its own node, marked a lone row. `near` adds `pub.links`' near
grade one hop from the matched rows in hand (decision 2; the rows graph's
own hop, so every line still touches a matched node), dashed, the reason on the
edge, the far row pulled in as its own entity, never merged. A contested
group is marked; a `pub.decisions` row on a pair whose rows land on two
nodes shows on their line.

The board makes no link by looking (plan 4.9): this module reads
`pub.groups`, `pub.links`, `pub.decisions` and `pub.names`, and a row's own
view only to show it and to know whether its name is suppressed. A row
whose name is suppressed is never folded (hard limit 16): gathered with its
group, the group's label, its other rows and their links would say the
name. It stays its own node and draws no near link, as in the rows state,
and no group counts, lists or labels it.

Every query is by row key or group id, on an index: `groups_pkey`
(row_key), `groups_group`, `rows_pkey` (pub.names.ref),
`links_row_a_row_b_rule_key` and `links_row_b`, `decisions_rows`. A group's
label is the fullest filed name among its rows (decision 1): the most
words, then the most letters, then the first in order; the pane says it is
a display choice, not a link."""
from __future__ import annotations

import json
import re

from products.board import catalogue as cat
from products.board import db, facts, fold as names, lineage, links_view, panes, search

ENTITY = "entity:"
MAX_CHILDREN = 40           # rows drawn inside an opened entity; the pane lists every row
PANE_ROWS = 1500            # the entity pane's rows; the dossier reads a group past dossier.MANY_AT by view (30,836 rows, 28 October 2026)
NEAR_PER_ROW = 10           # near links drawn per row in hand; the rest counted
PANE_NEAR = 200
LABEL_NOTE = panes.ENTITY_LABEL_NOTE
CONFIRMED, NEAR = "same person, confirmed", "same person, near"


def entity_id(group_id: str) -> str:
    return ENTITY + group_id


def ref_of(n: dict) -> str:
    return links_view.ref(n["v"], n["row"]["key"])


# ── reads, each one query by key ────────────────────────────────────────────

def groups_of(conn, refs) -> dict:
    """{row ref: (group_id, contested)} for the refs that are in a group."""
    refs = sorted(set(refs))
    if not refs:
        return {}
    return {r["row_key"]: (r["group_id"], bool(r["contested"])) for r in
            db.rows(conn, "select row_key, group_id, contested from pub.groups where row_key = any(%s)", (refs,))}


def members_of(conn, gids) -> dict:
    """{group_id: [{'ref', 'view', 'key', 'register', 'name', 'kind'}]}, every
    row of each group in ref order; `view` None where pub.names lacks the
    row (an organisation joined by its official number)."""
    gids = sorted(set(gids))
    out = {g: [] for g in gids}
    if not gids:
        return out
    for r in db.rows(conn, "select g.group_id, g.row_key, n.view, n.key, n.register, n.name_filed, n.kind "
                           "from pub.groups g left join pub.names n on n.ref = g.row_key "
                           "where g.group_id = any(%s) order by g.group_id, g.row_key", (gids,)):
        register, key = links_view.split_ref(r["row_key"])
        out[r["group_id"]].append({"ref": r["row_key"], "view": r["view"], "key": r["key"] or key,
                                   "register": r["register"] or register, "name": r["name_filed"] or "", "kind": r["kind"] or ""})
    return out


def rows_by_key(conn, view: str, keys) -> dict:
    """{key: row} of one view, one query."""
    v = cat.BY_NAME.get(view)
    keys = sorted(set(keys))
    if v is None or not keys:
        return {}
    return {str(r["key"]): r for r in db.rows(conn, f"select *, {v.key_col} as key from pub.{v.name} "
                                                    f"where {v.key_col} = any(%s)", (keys,))}


def suppressed_refs(conn, members: list) -> set:
    """The refs among `members` whose row's name is suppressed or hidden
    (hard limit 16), by one query per view that can suppress."""
    by_view = {}
    for m in members:
        v = cat.BY_NAME.get(m["view"] or "")
        if v is not None and (v.suppressed or v.hide_names):
            by_view.setdefault(v.name, []).append(m)
    out = set()
    for view, ms in by_view.items():
        v = cat.BY_NAME[view]
        cols = ", ".join(sorted({c for c in (v.suppressed, v.hide_names[0] if v.hide_names else "") if c}))
        found = db.rows(conn, f"select {v.key_col} as key, {cols} from pub.{v.name} where {v.key_col} = any(%s)",
                        (sorted({m["key"] for m in ms}),))
        hidden = {str(r["key"]) for r in found if panes.is_suppressed(v, r)}
        out |= {m["ref"] for m in ms if m["key"] in hidden}
    return out


def resolve_refs(conn, refs, members: dict = None) -> dict:
    """{ref: (view, row)} for the refs a published view holds: by pub.names'
    view and key, one query per view; a ref pub.names lacks by its register's
    views (links_view.view_for)."""
    refs = sorted(set(refs))
    known = {m["ref"]: m for ms in (members or {}).values() for m in ms}
    missing = [r for r in refs if r not in known]
    if missing:
        for r in db.rows(conn, "select ref, view, key, register from pub.names where ref = any(%s)", (missing,)):
            known[r["ref"]] = {"ref": r["ref"], "view": r["view"], "key": r["key"], "register": r["register"]}
    by_view, out = {}, {}
    for ref in refs:
        m = known.get(ref)
        if m and m.get("view") in cat.BY_NAME:
            by_view.setdefault(m["view"], []).append((ref, m["key"]))
            continue
        register, key = links_view.split_ref(ref)
        v = links_view.view_for(conn, register, key) if register in dict(cat.REGISTERS) else None
        r = search.row(conn, v.name, key) if v else None
        if r:
            out[ref] = (v, r)
    for view, pairs in by_view.items():
        found = rows_by_key(conn, view, [k for _, k in pairs])
        for ref, key in pairs:
            if key in found:
                out[ref] = (cat.BY_NAME[view], found[key])
    return out


def links_among(conn, refs) -> list:
    """Every pub.links row with both ends in `refs` (a group's own links)."""
    refs = sorted(set(refs))
    if len(refs) < 2:
        return []
    return db.rows(conn, "select row_a, row_b, rule, grade, evidence, reason, decision from pub.links "
                         "where row_a = any(%s) and row_b = any(%s) order by grade, rule, row_a, row_b", (refs, refs))


def near_of(conn, refs) -> list:
    """The near links with either end in `refs`, at most NEAR_PER_ROW per row
    in hand (by rule, then the far row) and `total`, that row's count: one
    query, the view's decision column computed once."""
    refs = sorted(set(refs))
    if not refs:
        return []
    return db.rows(conn, "with hit as (select row_a, row_b, rule, reason, decision from pub.links "
                         "  where (row_a = any(%s) or row_b = any(%s)) and grade = 'near'), "
                         "ends as (select h.*, e.mine from hit h, lateral (values (h.row_a), (h.row_b)) e(mine) "
                         "  where e.mine = any(%s)) "
                         "select * from (select *, row_number() over w as nth, count(*) over (partition by mine) as total "
                         "  from ends window w as (partition by mine order by rule, row_a, row_b)) s "
                         "where nth <= %s order by mine, nth", (refs, refs, refs, NEAR_PER_ROW))


def decisions_of(conn, refs) -> list:
    refs = sorted(set(refs))
    if not refs:
        return []
    return db.rows(conn, "select row_a, row_b, verdict, made_by, made_at from pub.decisions "
                         "where row_a = any(%s) or row_b = any(%s) order by made_at, decision_id", (refs, refs))


# ── what an entity is called and counted ────────────────────────────────────

def fullest(names) -> str:
    """The fullest filed name: the most words, then the most letters, then
    the first in order (decision 1)."""
    best = ""
    for x in names:
        x = re.sub(r"\s+", " ", x or "").strip()
        if x and (len(x.split()), len(x)) > (len(best.split()), len(best)):
            best = x
    return best


def count_words(rows: int, registers: int) -> str:
    return f"{rows:,} row{'s' if rows != 1 else ''}, {registers} register{'s' if registers != 1 else ''}"


def number_of(links: list) -> str:
    """'company number 138293' where an official number joins the group (rules.RULE_NUMBER)."""
    for l in links:
        if str(l["rule"]).startswith("official-number@") and l["grade"] == "confirmed":
            ev = l.get("evidence") or {}
            ev = json.loads(ev) if isinstance(ev, str) else ev
            if ev.get("value"):
                return f"{ev.get('number') or 'official number'} {ev['value']}"
    return ""


def describe(gid: str, members: list, hidden: set, contested: bool, resolved: dict = None) -> dict:
    """An entity's label, counts and flags from its shown rows (the
    suppressed left out)."""
    shown = [m for m in members if m["ref"] not in hidden]
    label = fullest(m["name"] for m in shown)
    if not label and resolved:                       # an organisation pub.names lacks: its row's own title
        for m in shown:
            if m["ref"] in resolved:
                label = panes.title_of(*resolved[m["ref"]])
                break
    registers = {m["register"] for m in shown}
    return {"group_id": gid, "label": label or f"group {gid}", "rows": len(shown), "registers": len(registers),
            "count": count_words(len(shown), len(registers)), "contested": contested,
            "kinds": sorted({m["kind"] for m in shown if m["kind"]})}


CARD_KEYS = 2000            # rows of one view read for the entity cards' words on one page; past it the line's noun alone


def what_of(conn, members: dict, hidden: set) -> dict:
    """{group_id: 'director and shareholder, charity trustee'}: what each
    entity is (ruling 117 (2)), from its shown rows' words (facts.what_it_is).
    A view whose word reads a column (a charity officer's role, a celebrant's
    statute) is read by key, one query per view; every other by its line's
    noun, no read."""
    want = {}
    for ms in members.values():
        for m in ms:
            v = cat.BY_NAME.get(m["view"] or "")
            if v is not None and m["ref"] not in hidden and facts.card_columns(v):
                want.setdefault(v.name, set()).add(m["key"])
    read = {}
    for view, keys in want.items():
        v = cat.BY_NAME[view]
        if len(keys) > CARD_KEYS:
            continue
        cols = ", ".join(sorted(set(facts.card_columns(v))))
        for r in db.rows(conn, f"select {v.key_col}::text as key, {cols} from pub.{v.name} where {v.key_col}::text = any(%s)",
                         (sorted(keys),)):
            read[(view, r["key"])] = r
    out = {}
    for gid, ms in members.items():
        pairs = [(cat.BY_NAME[m["view"]], read.get((m["view"], m["key"]))) for m in ms
                 if m["ref"] not in hidden and m["view"] in cat.BY_NAME]
        out[gid] = facts.what_it_is(pairs)
    return out


# ── the fold ────────────────────────────────────────────────────────────────

def fold(conn, g: dict, near: bool = True, max_nodes: int = 120) -> dict:
    """The people graph from the rows graph `g` (graph.build with links off).
    Row nodes in one group become one node, `entity:<group_id>`, carrying
    the first row in hand as its representative (its register's colour, its
    place in the layout) and `entity` (label, counts, contested). A lone
    row keeps its id and carries `lone`. Edges are rewritten to their ends'
    nodes; one whose ends fall in one node leaves (`inside` counts them)."""
    rows = {nid: n for nid, n in g["nodes"].items()}
    title = {nid: graph_title(n) for nid, n in rows.items()}
    hidden_here = {nid for nid, n in rows.items() if panes.is_suppressed(n["v"], n["row"])}
    refs = {nid: ref_of(n) for nid, n in rows.items()}
    grp = groups_of(conn, [r for nid, r in refs.items() if nid not in hidden_here])
    nears = near_of(conn, [refs[nid] for nid, n in rows.items() if n["matched"] and nid not in hidden_here]) if near else []
    in_hand = set(refs.values())
    far_refs = sorted({(l["row_b"] if l["mine"] == l["row_a"] else l["row_a"]) for l in nears} - in_hand)
    grp.update(groups_of(conn, far_refs))
    members = members_of(conn, {gid for gid, _ in grp.values()})
    hidden = suppressed_refs(conn, [m for ms in members.values() for m in ms])
    far_rows = resolve_refs(conn, far_refs, members) if far_refs else {}
    out = {**g, "nodes": {}, "edges": [], "people": True, "inside": 0, "near_cut": 0, "decisions": {},
           "drawn": {k: 0 for k in g["drawn"]}, "not_drawn": dict(g["not_drawn"]), "entities": 0, "lone": 0}
    node_of = {}

    def place(nid: str, n: dict, ref: str) -> str:
        hit = grp.get(ref) if nid not in hidden_here and ref not in hidden else None
        if hit is None:
            node_of[nid] = nid
            if nid not in out["nodes"]:
                out["nodes"][nid] = {**n, "order": len(out["nodes"]), "lone": nid not in hidden_here,
                                     "apart": nid in hidden_here}
            return nid
        gid, contested = hit
        eid = entity_id(gid)
        node_of[nid] = eid
        if eid in out["nodes"]:
            e = out["nodes"][eid]
            e["matched"] = e["matched"] or n["matched"]
            e["centre"] = e["centre"] or n["centre"]
            e["entity"]["in_hand"].append(nid)
        else:
            d = describe(gid, members.get(gid, []), hidden, contested)
            d["in_hand"] = [nid]
            out["nodes"][eid] = {**n, "order": len(out["nodes"]), "title": d["label"], "entity": d, "lone": False}
        return eid

    for nid, n in sorted(rows.items(), key=lambda kv: kv[1]["order"]):
        place(nid, n, refs[nid])
    seen = {}

    def lift(e: dict, a: str, b: str, pair: tuple):
        if a == b:
            out["inside"] += 1
            return
        k = (e["kind"], min(a, b), max(a, b), e["label"], e.get("rule"))
        if k in seen:
            seen[k]["rows"].append(pair)
            return
        x = {**e, "a": a, "b": b, "rows": [pair]}
        seen[k] = x
        out["edges"].append(x)
        out["drawn"][e["kind"]] += 1

    for e in g["edges"]:
        if e["a"] in node_of and e["b"] in node_of:
            lift(e, node_of[e["a"]], node_of[e["b"]], (title[e["a"]], title[e["b"]], e["a"], e["b"]))
    by_ref = {r: nid for nid, r in refs.items()}
    for l in nears:
        mine = by_ref.get(l["mine"])
        other = l["row_b"] if l["mine"] == l["row_a"] else l["row_a"]
        if mine is None or mine in hidden_here or other in hidden:
            continue
        if other in by_ref:
            onid = by_ref[other]
            if onid in hidden_here:
                continue
        else:
            hit = far_rows.get(other)
            if not hit:
                out["unresolved"] += 1
                continue
            fv, fr = hit
            if panes.is_suppressed(fv, fr):
                continue
            onid = f"{fv.name}:{fr['key']}"
            target = entity_id(grp[other][0]) if other in grp and other not in hidden else onid
            if target not in out["nodes"] and len(out["nodes"]) >= max_nodes:
                out["not_drawn"][NEAR] += 1
                continue
            rows[onid] = {"v": fv, "row": fr, "matched": False, "centre": False, "order": len(rows), "parent": node_of[mine]}
            title[onid] = graph_title(rows[onid])
            refs[onid] = other
            by_ref[other] = onid
            place(onid, rows[onid], other)
        lift({"kind": NEAR, "label": l.get("reason") or cat.rule_words(l["rule"]), "cite": mine, "rule": str(l["rule"]),
              "reason": l.get("reason") or "", "decision": l.get("decision") or ""},
             node_of[mine], node_of[onid], (title[mine], title[onid], mine, onid))
    for ref in {l["mine"] for l in nears}:
        total = next(int(l["total"]) for l in nears if l["mine"] == ref)
        out["not_drawn"][NEAR] += max(total - NEAR_PER_ROW, 0)
    shown_refs = [refs[nid] for nid in node_of if nid not in hidden_here and refs[nid] not in hidden]
    for d in decisions_of(conn, shown_refs):
        a, b = by_ref.get(d["row_a"]), by_ref.get(d["row_b"])
        if a and b and node_of[a] != node_of[b]:
            k = tuple(sorted((node_of[a], node_of[b])))
            out["decisions"].setdefault(k, []).append({"verdict": d["verdict"], "made_by": d["made_by"],
                                                      "made_at": d["made_at"], "rows": (title[a], title[b])})
    stand_for(conn, out, members, hidden)
    out["lineage"] = lineage.relabel(g.get("lineage"), node_of)     # ruling 106 (2): each company its own node, a person once
    out["entities"] = sum(1 for n in out["nodes"].values() if n.get("entity"))
    out["lone"] = sum(1 for n in out["nodes"].values() if n.get("lone"))
    return out


def stand_for(conn, out: dict, members: dict, hidden: set) -> None:
    """Each entity node's row, the one that stands for its group (its
    register's colour, its family, its grow and pane addresses): the group's
    first shown row by ref in byte order, read by key where this answer did
    not draw it, so every answer draws one entity alike (ruling 117 (4), the
    lineage lesson of 28 October); it was the first row in hand, which
    swapped with the row an answer started from."""
    want = {}
    for eid, n in out["nodes"].items():
        e = n.get("entity")
        if not e:
            continue
        shown = sorted((m for m in members.get(e["group_id"], []) if m["ref"] not in hidden and m["view"] in cat.BY_NAME),
                       key=lambda m: m["ref"].encode())
        if shown and links_view.ref(n["v"], n["row"]["key"]) != shown[0]["ref"]:
            want[eid] = shown[0]
    by_view = {}
    for m in want.values():
        by_view.setdefault(m["view"], set()).add(m["key"])
    rows = {view: rows_by_key(conn, view, keys) for view, keys in by_view.items()}
    for eid, m in want.items():
        r = rows.get(m["view"], {}).get(m["key"])
        if r is not None:
            out["nodes"][eid].update({"v": cat.BY_NAME[m["view"]], "row": r})


def graph_title(n: dict) -> str:
    return n.get("title") or panes.title_of(n["v"], n["row"])


# ── an entity opened: its rows and their own links ──────────────────────────

def entity(conn, gid: str) -> dict:
    """{'group_id', 'describe', 'rows': [(ref, view, row)] shown rows in
    register order, 'links': the group's own links among shown rows,
    'near': near links from its rows (at most PANE_NEAR), 'related': the
    related links of its rows (lineage.related_of), 'decisions'}; the
    suppressed rows left out entirely. None when no group has that id."""
    found = db.rows(conn, "select contested from pub.groups where row_key = %s", (gid,))
    if not found:
        return None
    members = members_of(conn, [gid])[gid][:PANE_ROWS]
    hidden = suppressed_refs(conn, members)
    shown = [m for m in members if m["ref"] not in hidden]
    resolved = resolve_refs(conn, [m["ref"] for m in shown], {gid: shown})
    order = {r: i for i, (r, _) in enumerate(cat.REGISTERS)}
    rows = sorted(((m["ref"],) + resolved[m["ref"]] for m in shown if m["ref"] in resolved),
                  key=lambda x: (order.get(x[1].register, len(order)), panes.title_of(x[1], x[2]).lower(), x[0]))
    own = links_among(conn, [m["ref"] for m in shown])
    near = [l for l in near_of(conn, [m["ref"] for m in shown]) if (l["row_b"] if l["mine"] == l["row_a"] else l["row_a"]) not in hidden]
    d = describe(gid, members, hidden, bool(found[0]["contested"]), resolved)
    d["number"] = number_of(own)
    return {"group_id": gid, "describe": d, "rows": rows, "links": own, "near": near[:PANE_NEAR],
            "near_total": len({(l["row_a"], l["row_b"], l["rule"]) for l in near}),
            "related": lineage.related_of(conn, [m["ref"] for m in shown]),          # ruling 106 (2): one query by key
            "decisions": decisions_of(conn, [m["ref"] for m in shown]), "hidden": hidden,
            "names": {m["ref"]: m["name"] for m in shown}}                         # the names as filed, for the dossier (ruling 110)


# ── the results pane's entity state (ruling 108) ────────────────────────────

RESULT_ENTITIES = 50        # entities (groups) listed under one tab of the results pane; the rest counted
RESULT_LONE = 100           # single-row entities listed under one tab (ruling 111); the rest counted


def gather(conn, hits, named: dict = None) -> dict:
    """The groups the results' rows fall in (ruling 108 (1)), for the
    results pane to list: `hits` [(view, row)] the rows the search shows;
    `named` {group_id: {tab}} the groups the entity search found by name
    (ruling 108 (3), `named_groups`). {'group': {node id: group_id} for the
    rows in a group, 'entity': {group_id: people.describe plus 'registers_named'
    and 'centre', a node id of one of its shown rows for the graph}}. A row
    whose name is suppressed is never gathered (hard limit 16): it maps to
    no group and the pane shows it as a row. Three queries by key on an
    index (groups_pkey, groups_group with rows_pkey, the suppressing views'
    keys), whatever the number of rows."""
    named = named or {}
    refs = {}
    for v, r in hits:
        if not panes.is_suppressed(v, r):
            refs[f"{v.name}:{r['key']}"] = links_view.ref(v, r["key"])
    grp = groups_of(conn, refs.values())
    gids = {gid for gid, _ in grp.values()} | set(named)
    members = members_of(conn, gids)
    hidden = suppressed_refs(conn, [m for ms in members.values() for m in ms])
    contested = {gid: c for gid, c in grp.values()}
    if set(named) - set(contested):
        for r in db.rows(conn, "select group_id, bool_or(contested) as c from pub.groups where group_id = any(%s) group by 1",
                         (sorted(set(named) - set(contested)),)):
            contested[r["group_id"]] = bool(r["c"])
    order = {r: i for i, (r, _) in enumerate(cat.REGISTERS)}
    entity = {}
    for gid in gids:
        shown = [m for m in members.get(gid, []) if m["ref"] not in hidden]
        if not shown:
            continue                                   # a group of suppressed rows alone names nobody
        d = describe(gid, members.get(gid, []), hidden, contested.get(gid, False))
        d["registers_named"] = [panes.REGISTER_NAME.get(x, x) for x in sorted({m["register"] for m in shown},
                                                                             key=lambda x: (order.get(x, len(order)), x))]
        d["centre"] = next((f"{m['view']}:{m['key']}" for m in shown if m["view"] in cat.BY_NAME), "")
        entity[gid] = d
    what = what_of(conn, {gid: members.get(gid, []) for gid in entity}, hidden)
    for gid, d in entity.items():                      # ruling 117 (2): what the entity is, not how many rows it has
        d["what"] = what.get(gid, "")
    related = lineage.related_refs(conn, [m["ref"] for gid in entity for m in members.get(gid, []) if m["ref"] not in hidden])
    for gid, d in entity.items():                      # ruling 106 (2): an entity with a related link says so, in a word
        d["related"] = sorted({related[m["ref"]] for m in members.get(gid, []) if m["ref"] in related})
    group = {nid: grp[ref][0] for nid, ref in refs.items() if ref in grp and ref not in hidden and grp[ref][0] in entity}
    return {"group": group, "entity": entity, "named": {g: set(t) for g, t in named.items() if g in entity}}


# ── entity search (ruling 108 (3)) ──────────────────────────────────────────

NAMED_ROWS = 5000           # pub.names rows read for one search; past it the count is said, not hidden


def key_fold(s: str) -> str:
    """links/rows.py's `fold`, the fold pub.names' fl_key and full_key are
    written in: diacritics off, lower, apostrophes out, spaces squashed.
    Products may not import links/ (imports run one way); check item 23 and
    tests/test_real.py hold it to the published keys."""
    return " ".join(names.fold_diacritics(s or "").lower().replace("'", "").replace("\u2019", "").split())


def name_keys(term: str = "", fields: dict = None) -> dict:
    """{'fl': key, 'full': key, 'person': key, 'org': key} for pub.names'
    indexed columns (rows_fl, rows_full, rows_name), read from the search box
    as the links lane reads a filed name (keys.names.person_name: honorifics
    off, "Family, Given" turned round, a one-word name a family name), or from
    the name fields when they are filled (first and last, with a middle;
    organisation). A key that cannot be read is absent. Each word's first
    alternative alone (ruling 92 (4)'s variants are not keys)."""
    fields = {f: search.base_term(x) for f, x in (fields or {}).items() if (x or "").strip()}
    out = {}
    if fields:
        first, middle, last = fields.get("first", ""), fields.get("middle", ""), fields.get("last", "")
        if first and last:
            givens = names.squash(f"{first} {middle}").split()
            out["fl"] = key_fold(f"{givens[0]} {last}")
            if len(givens) > 1:
                out["full"] = key_fold(" ".join(givens + [last]))
        if fields.get("org"):
            out["org"] = names.organisation_key(fields["org"])
        return out
    term = search.base_term(term)
    if not term.strip() or search.is_number(term):
        return out
    n = names.person_name(term)
    if n.given and n.family:
        out["fl"] = key_fold(f"{n.given} {n.family}")
        if n.middle:
            out["full"] = key_fold(n.full)
    out["person"] = names.person_key(term)
    out["org"] = names.organisation_key(term)
    return {k: x for k, x in out.items() if x}


def named_groups(conn, term: str = "", fields: dict = None, registers=None) -> dict:
    """{group_id: {tab}}: the groups holding a row whose filed name carries
    the name searched (ruling 108 (3)), read against pub.names by its indexed
    keys (name_keys) and folded into pub.groups by row key: one query on
    rows_fl, rows_full, rows_name and groups_pkey. The tab is the field the
    key matched: the first and last names (fl_key), with the middle
    (full_key), the organisation (an organisation's name_key), the last name
    alone or the first and last (a person's order-free name_key). With the
    fields filled and the box too, a name must also carry every word of the
    box. A row whose name is suppressed never finds its group (hard limit 16:
    pub.names leaves it out, and the views that can suppress are asked again).
    Only the registers searched. The board makes no link here: the groups
    are the links lane's."""
    keys = name_keys(term, fields)
    if not keys:
        return {}
    sql = ("select n.ref, n.view, n.key, n.register, n.kind, n.name_filed, n.has_middle, g.group_id, "
           "n.fl_key = %(fl)s as by_fl, n.full_key = %(full)s as by_full, n.name_key = %(person)s and n.kind = 'person' as by_person, "
           "n.name_key = %(org)s and n.kind <> 'person' as by_org "
           "from pub.names n join pub.groups g on g.row_key = n.ref "
           "where (n.fl_key = %(fl)s or n.full_key = %(full)s or n.name_key = %(person)s or n.name_key = %(org)s)"
           + (" and n.register = any(%(regs)s)" if registers is not None else "") + " limit %(limit)s")
    found = db.rows(conn, sql, {"fl": keys.get("fl"), "full": keys.get("full"), "person": keys.get("person"),
                                "org": keys.get("org"), "regs": list(registers or []), "limit": NAMED_ROWS})
    if fields and any((x or "").strip() for x in fields.values()) and search.words_of(term):
        words = search.words_of(search.base_term(term))
        found = [r for r in found if all(re.search(r"\b" + re.escape(w), key_fold(r["name_filed"])) for w in words)]
    hidden = suppressed_refs(conn, [{"ref": r["ref"], "view": r["view"], "key": r["key"]} for r in found])
    out = {}
    for r in found:
        if r["ref"] in hidden:
            continue
        tabs = set()
        if r["by_fl"]:
            tabs |= {"first", "last"}
        if r["by_full"]:
            tabs |= {"first", "last"} | ({"middle"} if r["has_middle"] else set())
        if r["by_person"]:
            tabs |= {"last"} if len(keys.get("person", "").split()) == 1 else {"first", "last"}
        if r["by_org"]:
            tabs.add("org")
        if tabs:
            out.setdefault(r["group_id"], set()).update(tabs)
    return out
