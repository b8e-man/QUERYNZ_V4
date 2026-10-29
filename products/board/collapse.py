"""The collapse section (ruling 112): a fixed list of criteria a reader may
tick above the results, each folding the listed entities further for this
view alone. The links lane's groups are the default and always on (the
entities themselves, ruling 111); the others are a shared first and last
name (pub.names' `fl_key`, the folded key the entity search reads; a row
of a view the links lane does not read is keyed the same way from its own
Name columns, row_name_keys), a
shared registered address (a company's registered office from
pub.company_addresses, read by the organisation's own key; never a
person's address: a person's row is never asked) and a shared official
number (an organisation row's own NZBN, company, charity or incorporation
number, never a number a row names for someone else). A shared full name
with middle names left the list (ruling 118): it is the links lane's own
rule 1 and folded nothing the groups had not; an address carrying `cl=full`
is read without it.

A fold here is a display choice for this page. It is never a link and
never written: this module only reads (pub.names, pub.groups through
people.members_of, pub.company_addresses), every folded entry says so in a
word, and the dossier of a folded entry lists its members as the entities
they are (dossier.gather_fold). The links lane's rules alone make links
(plan 4.9). A row whose name is suppressed is never folded (hard limit 16):
it carries no key. The address carries the criteria ticked (`cl=`,
search.Boxes.collapse), so a view reopens folded; the graph beside the
results folds the same way (`fold_graph`) with the same words on the node.

A fold by hand (ruling 119): the reader ticks organisation entities in the
results (`organisations`: a group the links lane read as an organisation, a
row of a view the catalogue marks "organisation", or a row naming an
organisation by its own column or by pub.names' kind) and collapses the
ticked into one entry for this view (`hand_fold`), named by the fullest
name among them (`label`), saying "collapsed here by hand; not a link"; the
graph draws it as one node (`fold_graph`). A person entity is never folded
by hand, whatever the address names: a person's identity is the links
lane's and the review's. The fold travels in the address alone (`hf=`,
search.Boxes.hand), and in a saved path's address; never a link, never a
decision, never written anywhere else."""
from __future__ import annotations

import re
import urllib.parse

from products.board import catalogue as cat
from products.board import db, fold, links_view, panes, people, search

#: (criterion, what the section says beside its box, the word a folded entry carries); "groups" is always on
CRITERIA = (("groups", "the links lane's groups (always on: the entities themselves)", ""),
            ("name", "a shared first and last name", "shared name"),
            ("address", "a shared registered address (a company's registered office; never a person's address)",
             "shared registered address"),
            ("number", "a shared official number (an organisation's own NZBN, company, charity or incorporation number)",
             "shared official number"))
CHOICES = search.COLLAPSE_CHOICES     # the address's order; tests/test_collapse.py holds it to CRITERIA
HAND = "hand"                         # ruling 119: the fold by hand, said before any criterion
ORDER = (HAND,) + CHOICES             # how a fold's words and its dossier address name what joined it
WORD = {c: w for c, _, w in CRITERIA} | {HAND: "hand"}
PREFIX = "fold:"
MAX_MEMBERS = 100           # members named in a folded entry's dossier address; the entry counts every one
NOTE = ("A fold here is a display choice for this page alone: never a link, never written to any table. The links lane's "
        "rules alone make links; the dossier of a folded entry lists its members as the entities they are.")

HAND_NOTE = ("tick two or more organisations in the results and collapse them into one entry for this view, by hand; "
             "a person is not collapsed by hand (a person's identity is the links lane's and the review's).")

#: an organisation row's own official numbers: (column, the number's namespace); any other `numbers` column
#: (a holder's, a body's, a mortgagee's, a bill's, an id) names someone or something else and never folds
OWN_NUMBERS = {"nzbn": "NZBN", "company_number": "company number", "charity_number": "charity number",
               "incorporation_number": "incorporation number"}

#: a row of a person view that names an organisation by its own column (column, the value that says so): the
#: Companies Office's holder type; a row of any other person view is an organisation only where pub.names says so
ORG_ROWS = {"shareholders": ("shareholder_type", "company")}


def label(group_labels, row_titles) -> str:
    """A folded entry's name: the fullest of its groups' names (people.fullest,
    each the fullest filed among its rows), else of its lone rows' titles, so a
    row's title with its year or register after the name never heads a fold."""
    return people.fullest(group_labels) or people.fullest(row_titles) or next(iter(list(group_labels) + list(row_titles)), "")


def words(by) -> str:
    """'collapsed here by shared name; not a link' for the criteria that joined an entry."""
    return "collapsed here by " + " and ".join(WORD[c] for c in ORDER if c in by) + "; not a link"


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
    if "name" in criteria:
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
            named = db.rows(conn, "select ref, kind, fl_key from pub.names where ref = any(%s)",
                            (sorted(refs),))
        held = {n["ref"] for n in named}
        for ref, vr in own.items():             # a row pub.names holds no entry of: its own Name columns
            if ref not in held:
                got = row_name_keys(*vr)
                if got:
                    named.append({"ref": ref, "kind": "person", "fl_key": got[0]})
        for n in named:
            if n["kind"] != "person":
                continue
            for uid in refs.get(n["ref"], ()):
                if n["fl_key"]:
                    out[uid]["name"].add(n["fl_key"])
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
    return PREFIX + "+".join(c for c in ORDER if c in by) + ":" + ",".join(urllib.parse.quote(m, safe="") for m in members[:MAX_MEMBERS])


def parse(d: str):
    """(criteria, [member ids]) from a fold's dossier address; None when it is not one."""
    if not d.startswith(PREFIX):
        return None
    crit, _, rest = d[len(PREFIX):].partition(":")
    by = tuple(c for c in ORDER if c in set(crit.split("+")))
    members = [urllib.parse.unquote(m) for m in rest.split(",") if m][:MAX_MEMBERS]
    return (by, members) if by and len(members) > 1 else None


def folder(conn, criteria: tuple, hand: tuple = (), ents: dict = None):
    """The results' entries for one page: each organisation entity marked
    `org` (its tick box, ruling 119), the folds by hand made, then the
    criteria ticked folded (fold_entries); the keys and kinds read once per
    entry across the tabs (an entity under several tabs is asked once)."""
    memo, kinds = {}, {}

    def fold(xs):
        orgs = organisations(conn, xs, ents, kinds)
        xs = [{**x, "org": True} if x["id"] in orgs else x for x in xs]
        xs = hand_fold(xs, hand, orgs) if hand else xs
        return fold_entries(conn, xs, criteria, memo) if criteria else xs
    return fold


# ── the fold by hand (ruling 119) ───────────────────────────────────────────

def names_kinds(conn, refs) -> dict:
    """{ref: pub.names' kind} for the refs given; one query by key, none when there are none."""
    refs = sorted(set(refs))
    if not refs:
        return {}
    return {r["ref"]: r["kind"] for r in db.rows(conn, "select ref, kind from pub.names where ref = any(%s)", (refs,))}


def organisation_row(v: cat.View, r: dict, kind: str = "") -> bool:
    """Whether a row is an organisation's: its view's kind, its own column
    (ORG_ROWS), else pub.names' `kind` (a donor's row, a figure, is read there).
    A suppressed row never is (hard limit 16)."""
    if panes.is_suppressed(v, r):
        return False
    if v.kind == "organisation" or kind == "organisation":
        return True
    col, value = ORG_ROWS.get(v.name, ("", None))
    return bool(col) and str(r.get(col) or "").strip().lower() == value


def organisation_group(e: dict, rows: list) -> bool:
    """Whether a group is an organisation: the links lane's kinds of its
    shown rows (pub.names) all organisation; with none (organisations
    joined by number, which pub.names does not hold), every row in hand an
    organisation's. An empty group, or one with a person's row, is not."""
    kinds = set((e or {}).get("kinds") or ())
    if kinds:
        return kinds == {"organisation"}
    return bool(e) and bool(rows) and all(organisation_row(v, r) for v, r in rows)


def organisations(conn, xs: list, ents: dict = None, memo: dict = None) -> set:
    """The ids of the entries that are organisation entities, the ones a
    reader may tick (ruling 119): a group by organisation_group, a lone row
    by organisation_row, pub.names' kind read in one query for the rows
    neither their view nor their own column settles; `memo` keeps the kinds read across the tabs. A fold is not offered."""
    memo = {} if memo is None else memo
    ask = {links_view.ref(v, r["key"]) for x in xs if x["group"] is None and not x.get("fold") for v, r in x["in_hand"][:1]
           if v.kind != "organisation" and v.name not in ORG_ROWS and not panes.is_suppressed(v, r)} - set(memo)
    if ask:
        got = names_kinds(conn, ask)
        memo.update({ref: got.get(ref, "") for ref in ask})
    out = set()
    for x in xs:
        if x.get("fold"):
            continue
        if x["group"] is not None:
            if organisation_group(((ents or {}).get("entity") or {}).get(x["group"]), x["in_hand"]):
                out.add(x["id"])
        elif x["in_hand"]:
            v, r = x["in_hand"][0]
            if organisation_row(v, r, memo.get(links_view.ref(v, r["key"]), "")):
                out.add(x["id"])
    return out


def hand_fold(xs: list, folds: tuple, orgs: set) -> list:
    """The results' entries with each fold by hand made: the organisation
    entities a fold names that are listed here become one entry {'id':
    fold_id, 'fold': (('hand',), [the member entries]), 'hand': the fold as
    the address names it} at its first member's place, the members in the
    list's order; an id named by an earlier fold, a person or an id not
    listed is left as it is, and a fold left with fewer than two folds
    nothing. Nothing is written."""
    by_id = {x["id"]: x for x in xs}
    order = {x["id"]: i for i, x in enumerate(xs)}
    taken, lead = set(), {}
    for f in folds:
        ms = sorted({m for m in f if m in orgs and m in by_id and m not in taken and not by_id[m].get("fold")}, key=order.get)
        if len(ms) > 1:
            taken |= set(ms)
            lead[ms[0]] = (ms, f)
    if not lead:
        return xs
    out = []
    for x in xs:
        if x["id"] in lead:
            ms, f = lead[x["id"]]
            members = [by_id[m] for m in ms]
            out.append({"id": fold_id(ms, {HAND}), "group": None, "in_hand": [vr for m in members for vr in m["in_hand"]],
                        "fold": ((HAND,), members), "hand": f})
        elif x["id"] not in taken:
            out.append(x)
    return out


def fold_entries(conn, xs: list, criteria: tuple, memo: dict = None) -> list:
    """The results pane's entries (panes.entries) folded by the criteria
    ticked: each set of two or more becomes one entry {'id': fold_id,
    'fold': (by, [the member entries])} at its first member's place; the
    rest are as they were. Nothing is written."""
    plain = [x for x in xs if not x.get("fold")]        # a fold by hand stays as the reader made it
    if not criteria or len(plain) < 2:
        return xs
    memo = {} if memo is None else memo
    units = [{"id": x["id"], "group": x["group"], "rows": x["in_hand"]} for x in plain]
    fresh = [u for u in units if u["id"] not in memo]
    memo.update(keys(conn, fresh, criteria) if fresh else {})
    sets = union([x["id"] for x in plain], memo, criteria)
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
    one node `fold:<member>`, named by the member `stands_for` names, its
    name the fullest of every member's and its register (type and colour)
    the one most of every member's rows in hand are in (`drawn_as`), and
    `fold` ({'words', 'members': [node ids], 'count', 'in_hand': the matching
    rows its matched members hold, for the "more match" note}), the same words as the
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
        lead = {**g["nodes"][lead_id], **dict(zip(("v", "row"), drawn_as(g["nodes"], ms, rows_of)))}
        titles = [g["nodes"][m].get("title") or panes.title_of(g["nodes"][m]["v"], g["nodes"][m]["row"]) for m in ms]
        grouped = [t for m, t in zip(ms, titles) if g["nodes"][m].get("entity")]
        rows = sum((g["nodes"][m].get("entity") or {}).get("rows", 1) for m in ms)
        nodes[fid] = {**{k: x for k, x in lead.items() if k not in ("entity", "lone")},
                      "title": label(grouped, [t for t in titles if t not in grouped]) or titles[0],
                      "matched": any(g["nodes"][m]["matched"] for m in ms), "centre": any(g["nodes"][m]["centre"] for m in ms),
                      "fold": {"words": words(by), "members": ms, "by": sorted(by),
                               "count": f"{len(ms)} entities, {rows:,} row{'s' if rows != 1 else ''}",
                               "in_hand": sum(len((g["nodes"][m].get("entity") or {}).get("in_hand") or [m])
                                              for m in ms if g["nodes"][m]["matched"]),
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
            people.cite_latest(seen[k], e, rows_of)
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


def member_order(m: str) -> tuple:
    """A fold's members in an order every answer shares: an entity first, then by id in byte order."""
    return (not m.startswith(people.ENTITY), m.encode())


def stands_for(ms: list) -> str:
    """The member whose id names a fold on the graph, by an order every answer
    shares: an entity first (a group outlives the rows an answer drew), then
    by id in byte order. The fold was `fold:<n>`, its place in this answer, so
    two answers gave one id to two folds and the canvas, which adds a node
    only when its id is new, swapped them."""
    return min(ms, key=member_order)


def drawn_as(nodes: dict, ms: list, rows_of: dict) -> tuple:
    """(view, row) a fold is typed and coloured by, from the whole fold: the
    register most of its members' rows in hand are in (a tie to the
    catalogue's order), and of that register the first such row, the members
    in `stands_for`'s order. The member that sorts first stood for the fold,
    so seven rows, six of them a company's, were drawn as a charity."""
    rows = []
    for m in sorted(ms, key=member_order):
        n = nodes[m]
        hand = [(rows_of[h]["v"], rows_of[h]["row"]) for h in (n.get("entity") or {}).get("in_hand") or () if h in rows_of]
        rows += hand or [(n["v"], n["row"])]
    count = {}
    for v, _ in rows:
        count[v.register] = count.get(v.register, 0) + 1
    order = {r: i for i, (r, _) in enumerate(cat.REGISTERS)}
    most = min(count, key=lambda r: (-count[r], order.get(r, len(order)), r))
    return next((v, r) for v, r in rows if v.register == most)


def member_dossier(n: dict, nid: str) -> str:
    """The dossier address of one member of a graph fold: its entity, else its row."""
    return people.entity_id(n["entity"]["group_id"]) if n.get("entity") else nid
