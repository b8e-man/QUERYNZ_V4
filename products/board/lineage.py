"""The links lane's third grade, `related` (ruling 106 (2); links-3's merge
request, "For the board"): two companies under one name, one carrying a
year in brackets, a person confirmed on both. A relation, never an
identity: `pub.links.relation` says what the one is to the other ("succeeded
by"), `evidence.earlier` is succeeded by `evidence.later` (by registration
date, `order` saying how a tie was broken), `evidence.shared_rows` the
people on both as pairs of row keys with their group id.

The board draws it as a lineage frame, in both of the graph's states: a
compound node around the companies in date order, labelled with the
relation and the years; each company stays its own node (a row, a lone
row, or its own entity; never merged into one), and each shared person is
drawn once inside the frame, joined to both by the record relation its own
two rows assert (a director row names its company). A chain (A succeeded by
B succeeded by C) is one frame in order. In the rows state a shared person
is one node standing for its two rows, as a donor name stands for its rows
(ruling 86 (3)); in the entity state it is its group's entity.

Reads `pub.links` by row key only (`links_row_a_row_b_rule_key`,
`links_row_b`): one query for every row in hand at once, then one for the
new ends of a chain while it grows (at most MAX_ROUNDS). A shared person's
rows are resolved through `people.resolve_refs` (pub.names by ref, one
query per view) and a row whose name is suppressed is never drawn (hard
limit 16): that person is counted, not named. Nothing here prints a name
from the evidence; every name drawn is its own row's title."""
from __future__ import annotations

import json

from products.board import catalogue as cat
from products.board import db, links_view, panes

GRADE = "related"
KIND = "lineage"            # the edge kind (catalogue.EDGE_KINDS) of the line from the earlier company to the later
FRAME = "lineage:"          # a frame's node id: this, then its earliest company's ref
COLOUR = next(c for k, c, _ in cat.EDGE_KINDS if k == KIND)
FILL_OPACITY = 0.10         # the frame's fill: its colour at this opacity over the picture's surface (tests/test_night.py)
MAX_ROUNDS = 3              # queries past the first that follow a chain's new ends
MAX_COMPANIES = 8           # companies drawn in one frame; the rest counted
MAX_FRAMES = 6              # frames drawn in one picture; the rest counted
MAX_PEOPLE = 12             # shared people drawn in one frame; the rest counted
WORDS = ("A lineage frame is the links lane's related grade (ruling 106 (2)): companies under one name, one carrying a "
         "year in brackets, with a person confirmed on both. It is a relation, never one entity: each company stays its "
         "own node, in date order of registration, and the people on both are drawn once inside the frame.")


def evidence(l: dict) -> dict:
    ev = l.get("evidence") or {}
    if isinstance(ev, str):
        try:
            ev = json.loads(ev)
        except ValueError:
            ev = {}
    return ev if isinstance(ev, dict) else {}


def relation(l: dict) -> str:
    """`pub.links.relation`, else the evidence's own copy (before the lane's republish carried the column)."""
    return str(l.get("relation") or evidence(l).get("relation") or "related")


def ends(l: dict) -> tuple:
    """(earlier, later) refs: the evidence's order, else the row order."""
    ev = evidence(l)
    a, b = ev.get("earlier"), ev.get("later")
    if {a, b} == {l["row_a"], l["row_b"]}:
        return a, b
    return l["row_a"], l["row_b"]


def year(date) -> str:
    return str(date or "")[:4]


# ── reads, by row key ───────────────────────────────────────────────────────

def related_of(conn, refs) -> list:
    """Every related link with either end in `refs`: one query (the lesson:
    ask pub.links for every row in hand at once)."""
    refs = sorted(set(refs))
    if not refs:
        return []
    return db.rows(conn, "select * from pub.links where (row_a = any(%s) or row_b = any(%s)) and grade = %s "
                         "order by row_a, row_b, rule", (refs, refs, GRADE))


def related_refs(conn, refs) -> dict:
    """{ref: relation} for the refs in `refs` that are an end of a related
    link: one query by key, for the results pane's word (ruling 108)."""
    refs = sorted(set(refs))
    if not refs:
        return {}
    out = {}
    for l in db.rows(conn, "select row_a, row_b, evidence from pub.links where (row_a = any(%s) or row_b = any(%s)) "
                           "and grade = %s", (refs, refs, GRADE)):
        for r in (l["row_a"], l["row_b"]):
            out.setdefault(r, relation(l))
    return {r: x for r, x in out.items() if r in set(refs)}


def chain(conn, refs, rounds: int = MAX_ROUNDS) -> list:
    """The related links reaching `refs`, followed along a chain from its new
    ends up to `rounds` more queries; each link once."""
    found, asked, todo = {}, set(), set(refs)
    for _ in range(rounds + 1):
        if not todo:
            break
        hits = related_of(conn, todo)
        asked |= todo
        for l in hits:
            found[(l["row_a"], l["row_b"], l["rule"])] = l
        todo = {x for l in hits for x in (l["row_a"], l["row_b"])} - asked
    return [found[k] for k in sorted(found)]


# ── frames, pure ────────────────────────────────────────────────────────────

def frames(links: list) -> list:
    """One frame per chain of related links (their companies joined by
    any link): {'key', 'relation', 'companies': [ref] in date order (each
    link's earlier before its later; then registration date; then ref),
    'registered': {ref: date}, 'links': [(earlier, later, link)], 'shared':
    [{'group', 'rows': [(person ref, company ref)]}] one per group}."""
    parent = {}

    def top(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for l in links:
        a, b = ends(l)
        parent[top(a)] = top(b)
    by = {}
    for l in links:
        by.setdefault(top(ends(l)[0]), []).append(l)
    out = []
    for ls in by.values():
        reg, after, pairs = {}, {}, []
        for l in ls:
            e, la = ends(l)
            ev = evidence(l)
            dates = list(ev.get("registered") or [None, None]) + [None, None]
            reg.setdefault(e, dates[0])
            reg.setdefault(la, dates[1])
            after.setdefault(e, set()).add(la)
            after.setdefault(la, set())
            pairs.append((e, la, l))
        order, done = [], set()
        incoming = {x: sum(1 for e, la, _ in pairs if la == x) for x in after}
        ready = sorted((x for x, n in incoming.items() if n == 0), key=lambda x: (str(reg.get(x) or "9999"), x))
        while ready:                                  # earlier before later; among the free, the earliest registered
            x = ready.pop(0)
            order.append(x)
            done.add(x)
            for y in after[x]:
                incoming[y] -= 1
                if incoming[y] == 0:
                    ready.append(y)
            ready.sort(key=lambda x: (str(reg.get(x) or "9999"), x))
        order += sorted((x for x in after if x not in done), key=lambda x: (str(reg.get(x) or "9999"), x))     # a cycle: never by the rule, but drawn
        shared = {}
        for e, la, l in pairs:
            for p in evidence(l).get("shared_rows") or []:
                gid = p.get("group") or f"{p.get('earlier')}|{p.get('later')}"
                s = shared.setdefault(gid, {"group": gid, "rows": []})
                for person, company in ((p.get("earlier"), e), (p.get("later"), la)):
                    if person and (person, company) not in s["rows"]:
                        s["rows"].append((person, company))
        rels = sorted({relation(l) for _, _, l in pairs})
        out.append({"key": order[0], "relation": "; ".join(rels), "companies": order, "registered": reg,
                    "links": sorted(pairs, key=lambda p: (order.index(p[0]), order.index(p[1]))),
                    "shared": [shared[k] for k in sorted(shared)],
                    "shared_people": sum(int(evidence(l).get("shared_people") or 0) for _, _, l in pairs)})
    out.sort(key=lambda f: f["key"])
    return out


def label(relation_words: str, years: list, chain: bool = True) -> str:
    """"succeeded by · 1984 → 2016": the relation and the companies' years of
    registration in order; arrows only where each company is succeeded by the
    next (a chain), else the years in order with the first apart: "1987 → 2011, 2013"
    for one company succeeded by two."""
    ys = [y or "?" for y in years]
    if not ys:
        return relation_words
    text = " \u2192 ".join(ys) if chain or len(ys) < 3 else f"{ys[0]} \u2192 " + ", ".join(ys[1:])
    return f"{relation_words} \u00b7 {text}"


def is_chain(f: dict, drawn: dict) -> bool:
    """Whether the frame's drawn companies, in order, are each succeeded by the next and by nothing else."""
    order = [c for c in f["companies"] if c in drawn]
    pairs = {(e, la) for e, la, _ in f["links"] if e in drawn and la in drawn}
    return pairs == set(zip(order, order[1:]))


# ── drawn into the rows graph (graph.build) ─────────────────────────────────

def person_relation(v: cat.View, company_view: str):
    """The record relation a person row asserts to its company (directors:
    "director of"), or None."""
    return next((rel for rel in v.relations if rel.view == company_view), None)


def draw(conn, g: dict, add_node, add_edge, resolve_refs) -> None:
    """Adds the related links reaching the rows in hand to the rows graph `g`
    (graph.build's own add_node and add_edge, so MAX_NODES holds) and writes
    `g['lineage']`, one entry per frame: {'id', 'label', 'relation', 'years',
    'companies': [node id] in order, 'people': [node id], 'cut', 'hidden',
    'shared_people', 'links'}. `resolve_refs(conn, refs)` -> {ref: (view, row)}."""
    g.setdefault("lineage", [])
    g.setdefault("lineage_cut", 0)
    shown = {nid: n for nid, n in g["nodes"].items() if not panes.is_suppressed(n["v"], n["row"])}
    nid_of = {links_view.ref(n["v"], n["row"]["key"]): nid for nid, n in shown.items()}
    found = frames(chain(conn, nid_of))
    if not found:
        return
    g["lineage_cut"] += max(len(found) - MAX_FRAMES, 0)
    found = found[:MAX_FRAMES]
    want = {c for f in found for c in f["companies"][:MAX_COMPANIES]} | {p for f in found for s in f["shared"] for p, _ in s["rows"]}
    got = resolve_refs(conn, sorted(want - set(nid_of)))
    for ref, nid in nid_of.items():
        got.setdefault(ref, (g["nodes"][nid]["v"], g["nodes"][nid]["row"]))
    stands = {}                                       # a shared person's drawn node -> the rows it stands for
    for f in found:
        anchor = next((nid_of[c] for c in f["companies"] if c in nid_of), None)
        companies, cut = {}, 0
        for c in f["companies"]:
            hit = got.get(c)
            nid = None
            if hit and len(companies) < MAX_COMPANIES and not panes.is_suppressed(*hit):
                nid = nid_of.get(c) or add_node(hit[0], hit[1], anchor)
            if nid is None:
                cut += 1
                continue
            companies[c] = nid
            nid_of[c] = nid
            anchor = anchor or nid
        for e, la, l in f["links"]:
            if e in companies and la in companies:
                add_edge(KIND, companies[e], companies[la], relation(l), companies[e], str(l["rule"]))
        people, hidden = [], 0
        for s in f["shared"]:
            rows = sorted(((p, c) for p, c in s["rows"] if c in companies), key=lambda x: (f["companies"].index(x[1]), x[0]))
            hits = [(p, c, got.get(p)) for p, c in rows]
            if not hits:
                continue
            if any(h is None or panes.is_suppressed(*h[:2]) for _, _, h in hits):
                hidden += 1                           # a row unresolved or suppressed: the person is counted, never named
                continue
            if len(people) >= MAX_PEOPLE:
                cut += 1
                continue
            ids = [f"{h[0].name}:{h[1]['key']}" for _, _, h in hits]
            drawn = [i for i in ids if i in g["nodes"]]
            keep = ids[0]                             # the person's row on the earliest company: one id in every answer
            if keep not in g["nodes"]:                # (a grown hop's frame finds the node it drew before)
                v, r = hits[0][2]
                if add_node(v, r, companies[hits[0][1]]) is None:
                    cut += 1
                    continue
            for i in drawn:
                if i != keep:
                    merge(g, keep, i)
                    if i in nid_of.values():
                        nid_of = {k: (keep if x == i else x) for k, x in nid_of.items()}
            for (p, c, (v, r)), i in zip(hits, ids):
                rel = person_relation(v, companies[c].split(":", 1)[0])
                if rel is not None:
                    add_edge(rel.kind, keep, companies[c], rel.label, i)
            stands.setdefault(keep, [])
            stands[keep] += [i for i in ids if i not in stands[keep]]
            if keep not in people:
                people.append(keep)
        years = [year(f["registered"].get(c)) for c in f["companies"] if c in companies]
        g["lineage"].append({"id": FRAME + f["key"], "relation": f["relation"], "years": years,
                             "label": label(f["relation"], years, is_chain(f, companies)), "companies": [companies[c] for c in f["companies"] if c in companies],
                             "people": people, "cut": cut, "hidden": hidden, "shared_people": f["shared_people"],
                             "links": [(companies.get(e), companies.get(la), relation(l), str(l["rule"])) for e, la, l in f["links"]]})
    for keep, ids in stands.items():
        if keep in g["nodes"] and len(ids) > 1:
            g["nodes"][keep]["stands_for"] = ids
    dedupe(g)


def merge(g: dict, keep: str, drop: str) -> None:
    """The node `drop` drawn as `keep` (one person's second row): its edges
    rewritten to `keep`, its matched and centre flags carried."""
    n = g["nodes"].pop(drop, None)
    if n is None:
        return
    k = g["nodes"][keep]
    k["matched"] = k["matched"] or n["matched"]
    k["centre"] = k["centre"] or n["centre"]
    for e in g["edges"]:
        e["a"] = keep if e["a"] == drop else e["a"]
        e["b"] = keep if e["b"] == drop else e["b"]


def dedupe(g: dict) -> None:
    """Drops an edge whose two ends are one node, and a second edge of one
    cause between one pair; recounts `drawn`."""
    seen, out = set(), []
    for e in g["edges"]:
        k = (e["kind"], min(e["a"], e["b"]), max(e["a"], e["b"]), e["label"], e.get("rule"), e.get("cite"))
        if e["a"] == e["b"] or k in seen:
            continue
        seen.add(k)
        out.append(e)
    g["edges"] = out
    g["drawn"] = {k: sum(1 for e in out if e["kind"] == k) for k in g["drawn"]}


def relabel(frames_: list, node_of: dict) -> list:
    """The frames of the rows graph with their node ids moved to the entity
    state's (people.fold's `node_of`): each company its entity or lone row,
    each shared person its group's entity, drawn once."""
    out = []
    for f in frames_ or []:
        companies = [node_of.get(x, x) for x in f["companies"]]
        people = []
        for x in f["people"]:
            y = node_of.get(x, x)
            if y not in people and y not in companies:
                people.append(y)
        out.append({**f, "companies": companies, "people": people,
                    "links": [(node_of.get(a, a), node_of.get(b, b), r, rule) for a, b, r, rule in f["links"]]})
    return out


# ── placed for the canvas (graph.answer) ────────────────────────────────────

FRAME_GAP = 170             # px between two companies of a frame, left to right in date order
PERSON_DROP = 90            # px from the companies' row to the shared people's first row
PERSON_GAP = 112            # px between two people on a row: a label's width (96 px) and a margin
PERSON_ROW = 60             # px between two rows of people
PER_ROW = 5                 # people on one row; more wrap beneath
BAND = 120                  # px left between one frame's last row and the next frame's companies


def places(frames_: list, top: float, width: float) -> dict:
    """{node id: (x, y)} for the frames' members, each frame its own band
    below the layered picture (`top`): the companies left to right in date
    order, the shared people beneath them, PER_ROW to a row, so no two
    labels meet. A node already placed by an earlier frame keeps its place."""
    out, y = {}, top
    for f in frames_:
        cs = [c for c in f["companies"] if c not in out]
        x0 = width / 2 - (len(cs) - 1) * FRAME_GAP / 2
        for j, c in enumerate(cs):
            out[c] = (round(x0 + j * FRAME_GAP, 1), round(y, 1))
        ps = [p for p in f["people"] if p not in out]
        rows = [ps[i:i + PER_ROW] for i in range(0, len(ps), PER_ROW)]
        for k, row in enumerate(rows):
            px0 = width / 2 - (len(row) - 1) * PERSON_GAP / 2
            for j, p in enumerate(row):
                out[p] = (round(px0 + j * PERSON_GAP, 1), round(y + PERSON_DROP + k * PERSON_ROW, 1))
        y += PERSON_DROP + max(len(rows) - 1, 0) * PERSON_ROW + BAND
    return out


# ── read for the panes ──────────────────────────────────────────────────────

def pane_items(links: list, mine: set, resolve) -> list:
    """The related links of a row or an entity, for its pane: each
    {'relation', 'direction' ("succeeded by" read from `mine`, or "succeeds"),
    'other' ref, 'other_hit' (view, row) or None, 'years' (mine, other),
    'people': [(view, row)] the shared people's rows on `mine`'s side shown,
    'hidden': the count of those suppressed or not found, 'shared_people',
    'rule', 'decision'}. `resolve(ref)` -> (view, row) or None."""
    out = []
    for l in links:
        e, la = ends(l)
        if e not in mine and la not in mine:
            continue
        ev = evidence(l)
        dates = list(ev.get("registered") or [None, None]) + [None, None]
        earlier = e in mine
        other = la if earlier else e
        people, hidden = [], 0
        for p in ev.get("shared_rows") or []:
            hit = resolve(p.get("earlier") if earlier else p.get("later"))
            if hit is None or panes.is_suppressed(*hit):
                hidden += 1
                continue
            people.append(hit)
        out.append({"relation": relation(l), "earlier": earlier, "other": other, "other_hit": resolve(other),
                    "years": (year(dates[0]), year(dates[1])) if earlier else (year(dates[1]), year(dates[0])),
                    "people": people, "hidden": hidden, "shared_people": int(ev.get("shared_people") or len(people) + hidden),
                    "rule": str(l["rule"]), "order": ev.get("order") or "", "decision": l.get("decision") or ""})
    return out
