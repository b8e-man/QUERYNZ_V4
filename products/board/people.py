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
from products.board import db, links_view, panes, search

ENTITY = "entity:"
MAX_CHILDREN = 40           # rows drawn inside an opened entity; the pane lists every row
PANE_ROWS = 1500            # the largest live group is 1,220 rows (28 October 2026)
NEAR_PER_ROW = 10           # near links drawn per row in hand; the rest counted
PANE_NEAR = 200
LABEL_NOTE = ("the name shown is the fullest filed among the group's rows, a display choice and not a link "
              "(ruling 105, decision 1)")
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
    out["entities"] = sum(1 for n in out["nodes"].values() if n.get("entity"))
    out["lone"] = sum(1 for n in out["nodes"].values() if n.get("lone"))
    return out


def graph_title(n: dict) -> str:
    return n.get("title") or panes.title_of(n["v"], n["row"])


# ── an entity opened: its rows and their own links ──────────────────────────

def entity(conn, gid: str) -> dict:
    """{'group_id', 'describe', 'rows': [(ref, view, row)] shown rows in
    register order, 'links': the group's own links among shown rows,
    'near': near links from its rows (at most PANE_NEAR), 'decisions'}; the
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
            "decisions": decisions_of(conn, [m["ref"] for m in shown]), "hidden": hidden}
