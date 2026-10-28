"""The collapse section (ruling 112): a fixed list of criteria a reader may
tick above the results, each folding the listed entities further for this
view alone. The links lane's groups are the default and always on (the
entities themselves, ruling 111); the others are a shared first and last
name (pub.names' `fl_key`, the folded key the entity search reads; a row
of a view the links lane does not read is keyed the same way from its own
Name columns, row_name_keys), a
shared full name with middle names (`full_key` where `has_middle`), a
shared registered address (a company's registered office from
pub.company_addresses, read by the organisation's own key; never a
person's address: a person's row is never asked) and a shared official
number (an organisation row's own NZBN, company, charity or incorporation
number, never a number a row names for someone else).

A fold here is a display choice for this page. It is never a link and
never written: this module only reads (pub.names, pub.groups through
people.members_of, pub.company_addresses), every folded entry says so in a
word, and the dossier of a folded entry lists its members as the entities
they are (dossier.gather_fold). The links lane's rules alone make links
(plan 4.9). A row whose name is suppressed is never folded (hard limit 16):
it carries no key. The address carries the criteria ticked (`cl=`,
search.Boxes.collapse), so a view reopens folded; the graph beside the
results folds the same way (`fold_graph`) with the same words on the node."""
from __future__ import annotations

import re
import urllib.parse

from products.board import catalogue as cat
from products.board import db, fold, links_view, panes, people, search

#: (criterion, what the section says beside its box, the word a folded entry carries); "groups" is always on
CRITERIA = (("groups", "the links lane's groups (always on: the entities themselves)", ""),
            ("name", "a shared first and last name", "shared name"),
            ("full", "a shared full name, with middle names", "shared full name"),
            ("address", "a shared registered address (a company's registered office; never a person's address)",
             "shared registered address"),
            ("number", "a shared official number (an organisation's own NZBN, company, charity or incorporation number)",
             "shared official number"))
CHOICES = search.COLLAPSE_CHOICES     # the address's order; tests/test_collapse.py holds it to CRITERIA
WORD = {c: w for c, _, w in CRITERIA}
PREFIX = "fold:"
MAX_MEMBERS = 100           # members named in a folded entry's dossier address; the entry counts every one
NOTE = ("A fold here is a display choice for this page alone: never a link, never written to any table. The links lane's "
        "rules alone make links; the dossier of a folded entry lists its members as the entities they are.")

#: an organisation row's own official numbers: (column, the number's namespace); any other `numbers` column
#: (a holder's, a body's, a mortgagee's, a bill's, an id) names someone or something else and never folds
OWN_NUMBERS = {"nzbn": "NZBN", "company_number": "company number", "charity_number": "charity number",
               "incorporation_number": "incorporation number"}


def label(group_labels, row_titles) -> str:
    """A folded entry's name: the fullest of its groups' names (people.fullest,
    each the fullest filed among its rows), else of its lone rows' titles, so a
    row's title with its year or register after the name never heads a fold."""
    return people.fullest(group_labels) or people.fullest(row_titles) or next(iter(list(group_labels) + list(row_titles)), "")


def words(by) -> str:
    """'collapsed here by shared name; not a link' for the criteria that joined an entry."""
    return "collapsed here by " + " and ".join(WORD[c] for c in CHOICES if c in by) + "; not a link"


def chosen(values) -> tuple:
    """The criteria ticked, in the section's order, from the address's `cl` values; unknown words dropped."""
    got = set(values or ())
    return tuple(c for c in CHOICES if c in got)


# ── keys ────────────────────────────────────────────────────────────────────

#: links/rows.py's reading: a nickname or a footnote mark in brackets is no name
_BRACKETED = re.compile(r"\s*\([^()]*\)")


def row_name_keys(v: cat.View, r: dict):
    """(fl_key, full_key, has_middle) read from a row's own first declared
    Name (catalogue Fields.names, read in its order, ruling 85) as the links
    lane reads a name (links/rows.py read_name): for a row of a view pub.names
    does not hold, so a board-made key and pub.names' key for one name are
    equal. Only the first Name, the row's subject: a second names an alias
    or another party (a mortgagor beside the mortgagee). None where the row
    is suppressed, names nobody, or carries an organisation word (abstain:
    the lane's weak-surname exception is not copied, so such a name stays apart)."""
    names = cat.fields_of(v).names
    if not names or panes.is_suppressed(v, r):
        return None
    g = names[0]
    if g.whole:
        raw = str(r.get(g.whole) or "")
        if g.order == cat.FAMILY_GIVEN and "," not in raw:
            toks = fold.strip_honorifics(raw).split()
            raw = f"{toks[0]}, {' '.join(toks[1:])}" if len(toks) > 1 else raw
        whole = raw
    else:
        first, middle = str(r.get(g.first or g.given) or ""), str(r.get(g.middle) or "") if g.first else ""
        whole = " ".join(p for p in (first, middle, str(r.get(g.last) or "")) if p)
    if not whole.strip() or whole.strip().lower() == "name suppressed" or fold.ORG_WORDS.search(whole):
        return None
    if g.whole:
        n = fold.person_name(_BRACKETED.sub("", whole))
        given, mid, family = n.given, n.middle, n.family
    else:
        givens = fold.squash(_BRACKETED.sub("", f"{first} {middle}")).split()
        given, mid, family = (givens[0] if givens else ""), " ".join(givens[1:]), fold.squash(str(r.get(g.last) or ""))
    fl = people.key_fold(f"{given} {family}") if given and family else None
    full = people.key_fold(" ".join(p for p in (given, mid, family) if p)) or None
    return fl, full, bool(mid)


def number_keys(v: cat.View, r: dict) -> set:
    """An organisation row's own official numbers, each with its namespace; a person's row has none."""
    if v.kind != "organisation" or panes.is_suppressed(v, r):
        return set()
    out = set()
    for c in v.numbers:
        x = re.sub(r"\s+", "", str(r.get(c) or ""))
        if not x or not re.search(r"\d", x):
            continue
        if c in OWN_NUMBERS:
            out.add(f"{OWN_NUMBERS[c]}:{x}")
        elif c == "number":
            out.add(f"{'company number' if v.name == 'companies' else v.register + ' number'}:{x}")
    return out


def address_key(r: dict) -> str:
    """A registered office's lines and postcode folded: case, punctuation and spacing off."""
    parts = [str(r.get(c) or "") for c in ("line_1", "line_2", "line_3", "line_4", "postcode")]
    return " ".join(re.findall(r"[a-z0-9]+", fold.fold_diacritics(" ".join(parts)).lower()))


def address_keys(conn, units: list) -> dict:
    """{unit id: {address key}}: the registered office (pub.company_addresses, in the latest file) of each
    organisation row a unit holds, read by the row's own key or its entity_key; one query, only when ticked."""
    want = {}
    for u in units:
        for v, r in u["rows"]:
            if v.kind == "organisation" and not panes.is_suppressed(v, r):
                for k in {str(r.get("key") or ""), str(r.get("entity_key") or "")} - {""}:
                    want.setdefault(k, set()).add(u["id"])
    out = {}
    if not want:
        return out
    for a in db.rows(conn, "select entity_key, line_1, line_2, line_3, line_4, postcode from pub.company_addresses "
                           "where in_latest and entity_key = any(%s)", (sorted(want),)):
        k = address_key(a)
        if k:
            for uid in want.get(a["entity_key"], ()):
                out.setdefault(uid, set()).add(k)
    return out


def keys(conn, units: list, criteria: tuple) -> dict:
    """{unit id: {criterion: {key}}} for the criteria ticked. A unit is
    {'id', 'group': group id or None, 'rows': [(view, row)] in hand}. A
    group's name keys are its shown members' (pub.names, the suppressed left
    out); a lone row's its own, unless suppressed: pub.names' entry by ref,
    else, for a view the links lane does not read, its own Name columns
    (row_name_keys). Reads only."""
    out = {u["id"]: {c: set() for c in criteria} for u in units}
    if not criteria or not units:
        return out
    refs, own = {}, {}
    if {"name", "full"} & set(criteria):
        members = people.members_of(conn, {u["group"] for u in units if u["group"]})
        hidden = people.suppressed_refs(conn, [m for ms in members.values() for m in ms])
        for u in units:
            if u["group"]:
                mine = [m["ref"] for m in members.get(u["group"], []) if m["ref"] not in hidden]
            else:
                mine = []
                for v, r in u["rows"]:
                    if not panes.is_suppressed(v, r):
                        mine.append(links_view.ref(v, r["key"]))
                        own[mine[-1]] = (v, r)
            for ref in mine:
                refs.setdefault(ref, set()).add(u["id"])
        named = []
        if refs:
            named = db.rows(conn, "select ref, kind, fl_key, full_key, has_middle from pub.names where ref = any(%s)",
                            (sorted(refs),))
        held = {n["ref"] for n in named}
        for ref, vr in own.items():             # a row pub.names holds no entry of: its own Name columns
            if ref not in held:
                got = row_name_keys(*vr)
                if got:
                    named.append({"ref": ref, "kind": "person", "fl_key": got[0], "full_key": got[1], "has_middle": got[2]})
        for n in named:
            if n["kind"] != "person":
                continue
            for uid in refs.get(n["ref"], ()):
                if "name" in criteria and n["fl_key"]:
                    out[uid]["name"].add(n["fl_key"])
                if "full" in criteria and n["full_key"] and n["has_middle"]:
                    out[uid]["full"].add(n["full_key"])
    if "number" in criteria:
        for u in units:
            for v, r in u["rows"]:
                out[u["id"]]["number"] |= number_keys(v, r)
    if "address" in criteria:
        for uid, ks in address_keys(conn, units).items():
            out[uid]["address"] |= ks
    return out


# ── the fold ────────────────────────────────────────────────────────────────

def union(ids: list, ks: dict, criteria: tuple) -> list:
    """[(member ids in their first order, {criteria that joined them})] for
    every set of two or more units sharing a key of a ticked criterion,
    joined through any chain of shared keys; units alone are left out."""
    parent = {i: i for i in ids}
    how = {}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen = {}
    for i in ids:
        for c in criteria:
            for k in sorted(ks.get(i, {}).get(c, ())):
                j = seen.setdefault((c, k), i)
                if j == i:
                    continue
                a, b = find(i), find(j)
                if a != b:
                    parent[b] = a
                    how[a] = how.pop(a, set()) | how.pop(b, set()) | {c}
                else:
                    how[a] = how.get(a, set()) | {c}
    sets = {}
    for i in ids:
        sets.setdefault(find(i), []).append(i)
    return [(ms, how.get(root, set())) for root, ms in sets.items() if len(ms) > 1]


def fold_id(members: list, by) -> str:
    """The dossier's address for a folded entry: fold:<criteria>:<member ids, each quoted, comma-joined>."""
    return PREFIX + "+".join(c for c in CHOICES if c in by) + ":" + ",".join(urllib.parse.quote(m, safe="") for m in members[:MAX_MEMBERS])


def parse(d: str):
    """(criteria, [member ids]) from a fold's dossier address; None when it is not one."""
    if not d.startswith(PREFIX):
        return None
    crit, _, rest = d[len(PREFIX):].partition(":")
    by = chosen(crit.split("+"))
    members = [urllib.parse.unquote(m) for m in rest.split(",") if m][:MAX_MEMBERS]
    return (by, members) if by and len(members) > 1 else None


def folder(conn, criteria: tuple):
    """fold_entries for one page: the keys read once per entry across the
    tabs (an entity under several tabs is asked once); None when nothing is ticked."""
    if not criteria:
        return None
    memo = {}

    def fold(xs):
        return fold_entries(conn, xs, criteria, memo)
    return fold


def fold_entries(conn, xs: list, criteria: tuple, memo: dict = None) -> list:
    """The results pane's entries (panes.entries) folded by the criteria
    ticked: each set of two or more becomes one entry {'id': fold_id,
    'fold': (by, [the member entries])} at its first member's place; the
    rest are as they were. Nothing is written."""
    if not criteria or len(xs) < 2:
        return xs
    memo = {} if memo is None else memo
    units = [{"id": x["id"], "group": x["group"], "rows": x["in_hand"]} for x in xs]
    fresh = [u for u in units if u["id"] not in memo]
    memo.update(keys(conn, fresh, criteria) if fresh else {})
    sets = union([x["id"] for x in xs], memo, criteria)
    if not sets:
        return xs
    by_id = {x["id"]: x for x in xs}
    first = {}
    for ms, by in sets:
        first[ms[0]] = (ms, by)
        for m in ms[1:]:
            first[m] = None
    out = []
    for x in xs:
        f = first.get(x["id"], x)
        if f is None:
            continue
        if f is x:
            out.append(x)
            continue
        ms, by = f
        members = [by_id[m] for m in ms]
        out.append({"id": fold_id(ms, by), "group": None, "in_hand": [vr for m in members for vr in m["in_hand"]],
                    "fold": (by, members)})
    return out


def fold_graph(conn, g: dict, criteria: tuple, rows_of: dict = None) -> dict:
    """The graph beside the results folded the same way (ruling 112): its
    entity, lone and row nodes sharing a key of a ticked criterion become
    one node `fold:<member>`, carrying the member `stands_for` names as its representative and
    `fold` ({'words', 'members': [node ids], 'count'}), the same words as the
    results; edges are lifted to the folded ends, one inside a fold dropped
    and counted (`inside`), duplicates merged. A node kept apart (its name
    suppressed) or in a lineage frame is never folded. `rows_of`, the rows
    graph's nodes before the people fold, for an entity's rows in hand."""
    if not criteria or not g["nodes"]:
        return g
    framed = {x for f in g.get("lineage") or [] for x in list(f.get("companies") or []) + list(f.get("people") or [])}
    rows_of = rows_of or g["nodes"]
    units = []
    for nid, n in sorted(g["nodes"].items(), key=lambda kv: kv[1]["order"]):
        if nid in framed or n.get("apart") or panes.is_suppressed(n["v"], n["row"]):
            continue
        e = n.get("entity")
        if e:
            hand = [(rows_of[h]["v"], rows_of[h]["row"]) for h in e.get("in_hand") or () if h in rows_of]
            units.append({"id": nid, "group": e["group_id"], "rows": hand or [(n["v"], n["row"])]})
        else:
            units.append({"id": nid, "group": None, "rows": [(n["v"], n["row"])]})
    sets = union([u["id"] for u in units], keys(conn, units, criteria), criteria)
    if not sets:
        return g
    node_of = {nid: nid for nid in g["nodes"]}
    nodes = {}
    for ms, by in sets:
        lead_id = stands_for(ms)
        fid = f"{PREFIX}{lead_id}"                     # ruling 117 (4): named by its member, never by its place in this answer
        for m in ms:
            node_of[m] = fid
        lead = g["nodes"][lead_id]
        titles = [g["nodes"][m].get("title") or panes.title_of(g["nodes"][m]["v"], g["nodes"][m]["row"]) for m in ms]
        grouped = [t for m, t in zip(ms, titles) if g["nodes"][m].get("entity")]
        rows = sum((g["nodes"][m].get("entity") or {}).get("rows", 1) for m in ms)
        nodes[fid] = {**{k: x for k, x in lead.items() if k not in ("entity", "lone")},
                      "title": label(grouped, [t for t in titles if t not in grouped]) or titles[0],
                      "matched": any(g["nodes"][m]["matched"] for m in ms), "centre": any(g["nodes"][m]["centre"] for m in ms),
                      "fold": {"words": words(by), "members": ms, "by": sorted(by),
                               "count": f"{len(ms)} entities, {rows:,} row{'s' if rows != 1 else ''}",
                               "dossier": fold_id([member_dossier(g["nodes"][m], m) for m in ms], by)}}
    out = {**g, "nodes": {}, "edges": [], "inside": g.get("inside", 0), "folds": len(sets)}
    for nid, n in sorted(g["nodes"].items(), key=lambda kv: kv[1]["order"]):
        to = node_of[nid]
        if to not in out["nodes"]:
            out["nodes"][to] = {**(nodes.get(to) or n), "order": len(out["nodes"])}
    seen = {}
    for e in g["edges"]:
        a, b = node_of.get(e["a"], e["a"]), node_of.get(e["b"], e["b"])
        if a == b:
            out["inside"] += 1
            continue
        k = (e["kind"], min(a, b), max(a, b), e["label"], e.get("rule"))
        if k in seen:
            seen[k].setdefault("rows", []).extend(e.get("rows") or [])
            continue
        x = {**e, "a": a, "b": b}
        seen[k] = x
        out["edges"].append(x)
    out["decisions"] = {}
    for (a, b), ds in (g.get("decisions") or {}).items():
        a, b = node_of.get(a, a), node_of.get(b, b)
        if a != b:
            out["decisions"].setdefault(tuple(sorted((a, b))), []).extend(ds)
    return out


def stands_for(ms: list) -> str:
    """The member that stands for a fold on the graph, by an order every answer
    shares: an entity first (a group outlives the rows an answer drew), then
    by id in byte order. The fold was `fold:<n>`, its place in this answer, so
    two answers gave one id to two folds and the canvas, which adds a node
    only when its id is new, swapped them."""
    return min(ms, key=lambda m: (not m.startswith(people.ENTITY), m.encode()))


def member_dossier(n: dict, nid: str) -> str:
    """The dossier address of one member of a graph fold: its entity, else its row."""
    return people.entity_id(n["entity"]["group_id"]) if n.get("entity") else nid
