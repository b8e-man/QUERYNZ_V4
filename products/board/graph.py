"""The graph tab (ruling 80; plan 4.9, second version): the rows a search
matches are nodes; every connection their registers assert is an edge, one
hop out, typed and coloured, with a key below the picture. The picture is
SVG written here, with no script and no library: every node is an href that
re-centres on it, and every edge keeps its hover title and its line in the
list under the key, with an href to the register row that asserts it, so
every edge is cited. Ruling 84: two rows joined more than once get one line
and its causes are listed; the links' rules read in words
(`catalogue.RULE_WORDS`) and their ids appear only in a tooltip or the list.
Ruling 86: no edge numbers; an edge's words are drawn on its line only where
their box touches no other text box, node label or circle (`place`,
deterministic, held on the rendered picture by `text_boxes`); the list is
grouped by the far row.

Edges come from two places only, both published: a catalogue `Relation`
(this row's column names a row of another view, as the lane's own pane.md
says) and `pub.links` (the links' same-person verdicts, confirmed solid and
near dashed). The board matches no name by looking (plan 4.9: no link is
made by looking), and draws no address edge of any kind (hard limit 15).

`build` reads; `layout`, `lines`, `place` and `svg`/`pane` are pure."""
from __future__ import annotations

import datetime as dt
import decimal
import html
import math
import re
import urllib.parse

from products.board import catalogue as cat
from products.board import db, links_view, panes, search

MAX_MATCHED = 16        # matched rows drawn; the rest are counted and the search can be narrowed
PER_VIEW = 8            # matched rows taken from any one view
PER_RELATION = 10       # neighbours drawn per relation (or per links grade) per matched row
MAX_NODES = 120
MAX_FILED = 200         # rows read per donor name per view, for its money edges (ruling 86 (3)); more is said, not hidden
KIND = {name: (colour, dash) for name, colour, dash in cat.EDGE_KINDS}
CONFIRMED, NEAR = "same person, confirmed", "same person, near"


def incoming() -> dict:
    """{target view: [(source view, relation)]}: the relations that point at a view."""
    out = {}
    for v in cat.VIEWS:
        for rel in v.relations:
            out.setdefault(rel.view, []).append((v, rel))
    return out


INCOMING = incoming()


def node_id(v: cat.View, r: dict) -> str:
    return f"{v.name}:{r['key']}"


def _rows(conn, v: cat.View, column: str, value, limit: int) -> tuple:
    found = db.rows(conn, f"select *, {v.key_col} as key, count(*) over () as total from pub.{v.name} "
                          f"where {column} = %s order by {v.default_order} nulls last, {v.key_col} limit %s", (value, limit))
    return (int(found[0]["total"]) if found else 0), found


def _resolver(conn):
    cache = {}

    def resolve(ref: str):
        if ref not in cache:
            register, key = links_view.split_ref(ref)
            v = links_view.view_for(conn, register, key) if register else None
            r = search.row(conn, v.name, key) if v else None
            cache[ref] = (v, r) if r else None
        return cache[ref]
    return resolve


def build(conn, q: str, regs=None, centre: str = "", fields: dict = None) -> dict:
    """{'nodes': {id: {v, row, matched, centre, order}}, 'edges': [...],
    'drawn': {kind: n}, 'not_drawn': {kind: n}, 'matched_total', 'unresolved'}.
    An edge is one cause: kind, a, b (node ids), label (plain words), cite
    (the asserting row's id), rule (the links rule id, or None); `lines`
    folds the causes between two rows into one line."""
    g = {"nodes": {}, "edges": [], "drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS},
         "not_drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS}, "matched_total": 0, "unresolved": 0, "centre": centre}
    held = db.pub_views(conn)
    matched = []
    if centre:
        view, _, key = centre.partition(":")
        r = search.row(conn, view, key) if view in held else None
        if r:
            matched.append((cat.BY_NAME[view], r))
        g["matched_total"] = len(matched)
    elif q or fields:
        res = search.search(conn, q, limit=PER_VIEW, registers=regs, fields=fields)
        for register, _ in cat.REGISTERS:
            for v, total, rows in res.get(register, []):
                g["matched_total"] += total
                matched.extend((v, r) for r in rows)
        matched = matched[:MAX_MATCHED]
    donors = {}                                             # a donor name as filed -> its node (ruling 86 (3))
    node_of = {}                                            # each matched row -> the node it is drawn as
    for v, r in matched:
        name = filed_name(v, r)
        if name and name in donors:
            node_of[node_id(v, r)] = donors[name]
            continue
        nid = node_id(v, r)
        node_of[nid] = nid
        g["nodes"][nid] = {"v": v, "row": r, "matched": True, "centre": bool(centre), "order": len(g["nodes"]), "parent": None}
        if name:
            donors[name] = nid
            g["nodes"][nid]["title"] = str(r.get(cat.GIFT_OF[v.name].name))
    seen = set()

    def add_edge(kind, a, b, label, cite, rule=None, **extra):
        k = (kind, min(a, b), max(a, b), label, rule)
        if k in seen:
            return
        seen.add(k)
        g["edges"].append({"kind": kind, "a": a, "b": b, "label": label, "cite": cite, "rule": rule, **extra})
        g["drawn"][kind] += 1

    def add_node(v, r, parent):
        nid = node_id(v, r)
        if nid not in g["nodes"]:
            if len(g["nodes"]) >= MAX_NODES:
                return None
            g["nodes"][nid] = {"v": v, "row": r, "matched": False, "centre": False, "order": len(g["nodes"]), "parent": parent}
        return nid

    resolve = _resolver(conn)
    for name, nid in donors.items():
        gifts(conn, g, nid, name, held, add_node, add_edge)
    for v, r in matched:
        me = node_of[node_id(v, r)]
        for rel in (() if filed_name(v, r) else v.relations):     # a donor's money is drawn by gifts(), one edge per recipient                             # this row names the far end
            value = r.get(rel.column)
            far = cat.BY_NAME[rel.view]
            if value in (None, "") or far.name not in held:
                continue
            total, rows = _rows(conn, far, rel.to_column, value, PER_RELATION)
            drawn = 0
            for fr in rows:
                nid = add_node(far, fr, me)
                if nid:
                    add_edge(rel.kind, me, nid, rel.label, me)
                    drawn += 1
            g["not_drawn"][rel.kind] += total - drawn
        for src, rel in (() if filed_name(v, r) else INCOMING.get(v.name, ())):     # another view's rows name this row
            value = r.get(rel.to_column)
            if value in (None, "") or src.name not in held:
                continue
            total, rows = _rows(conn, src, rel.column, value, PER_RELATION)
            drawn = 0
            for sr in rows:
                nid = add_node(src, sr, me)
                if nid:
                    add_edge(rel.kind, nid, me, rel.label, nid)
                    drawn += 1
            g["not_drawn"][rel.kind] += total - drawn
        if panes.is_suppressed(v, r):                        # a suppressed row's namesakes would say its name
            continue
        links = links_view.links_of(conn, links_view.ref(v, r["key"]))
        for grade, kind in (("confirmed", CONFIRMED), ("near", NEAR)):
            items = links.get(grade) or []
            drawn = 0
            for l in items[:PER_RELATION]:
                hit = resolve(l["other"])
                if not hit:
                    g["unresolved"] += 1
                    continue
                ov, orow = hit
                nid = add_node(ov, orow, me)
                if nid:
                    add_edge(kind, me, nid, cat.rule_words(l["rule"]), me, str(l["rule"]))     # words, never the id (ruling 84)
                    drawn += 1
            g["not_drawn"][kind] += len(items) - drawn
    return g


# ── a donor's money, one edge per recipient (ruling 86 (3)) ─────────────────

def filed_name(v: cat.View, r: dict) -> str:
    """The donor name a gift row is filed under, folded (case, macrons,
    spacing); empty for a row that is no gift, or whose name is suppressed."""
    gift = cat.GIFT_OF.get(v.name)
    if not gift or panes.is_suppressed(v, r) or not r.get(gift.name):
        return ""
    return cat.fold_term(str(r[gift.name]))


def year_of(gift: cat.Gift, r: dict):
    for c in gift.years:
        x = r.get(c)
        if isinstance(x, (dt.date, dt.datetime)):
            return x.year
        if isinstance(x, int):
            return x
    return None


def money(x) -> str:
    return f"${decimal.Decimal(x):,.2f}"


def summed(addends: list) -> dict:
    """The total of the addends that are added, and what the label says: a
    sum of the register's own amounts and nothing more."""
    added = [x for x in addends if not x.get("not_added")]
    total = sum((decimal.Decimal(x["amount"]) for x in added), decimal.Decimal(0))
    return {"total": total, "added": added, "records": len({x.get("record") or x["cite"] for x in added}),
            "years": sorted({x["year"] for x in added if x.get("year") is not None})}


def years_words(years: list) -> str:
    return "year not stated" if not years else (str(years[0]) if years[0] == years[-1] else f"{years[0]}–{years[-1]}")


def gift_label(addends: list) -> str:
    """"donated $<total> (<n> returns, <first year>–<last year>)", then the
    rows listed apart: a disclosure's own sum, never added to a return's."""
    s = summed(addends)
    parts = []
    if s["added"]:
        n = s["records"]
        parts.append(f"donated {money(s['total'])} ({n} return{'s' if n != 1 else ''}, {years_words(s['years'])})")
    apart = [x for x in addends if x.get("not_added") and x.get("apart")]
    if apart:
        d = sum((decimal.Decimal(x["amount"]) for x in apart if x.get("amount") is not None), decimal.Decimal(0))
        ys = sorted({x["year"] for x in apart if x.get("year") is not None})
        parts.append(f"disclosed {money(d)} ({len(apart)} disclosure{'s' if len(apart) != 1 else ''}, {years_words(ys)}), not added")
    if not parts:
        parts.append(f"donated: {len(addends)} row{'s' if len(addends) != 1 else ''}, none added (see the list)")
    return "; ".join(parts)


def gifts(conn, g: dict, nid: str, name: str, held: set, add_node, add_edge):
    """Every row filed under `name` in the gift views, one money edge per
    recipient from the donor's node `nid`, its addends listed under it."""
    by = {}                     # recipient key -> {"rows": [(gift, row, recipient row)], ...}
    for gift in cat.GIFTS:
        v, far = cat.BY_NAME[gift.view], cat.BY_NAME[gift.to_view]
        if v.name not in held or far.name not in held:
            continue
        rows = db.rows(conn, f"select *, {v.key_col} as key, count(*) over () as total from pub.{v.name} "
                             f"where regexp_replace(btrim({search.fold_sql(gift.name)}), '\\s+', ' ', 'g') = %s "
                             f"order by {v.key_col} limit %s", (name, MAX_FILED))
        if rows and int(rows[0]["total"]) > len(rows):
            g["gifts_cut"] = g.get("gifts_cut", 0) + int(rows[0]["total"]) - len(rows)
        cache = {}
        for r in rows:
            if panes.is_suppressed(v, r):
                continue
            value = r.get(gift.column)
            if value in (None, ""):
                g["gifts_unplaced"] = g.get("gifts_unplaced", 0) + 1
                continue
            if value not in cache:
                cache[value] = _rows(conn, far, gift.to_column, value, 1)[1]
            if not cache[value]:
                g["gifts_unplaced"] = g.get("gifts_unplaced", 0) + 1
                continue
            rr = cache[value][0]
            k = (far.name,) + (tuple(cat.fold_term(str(rr.get(c) or "")) for c in gift.one_recipient) if gift.one_recipient else (rr["key"],))
            by.setdefault(k, []).append((gift, v, r, far, rr))
    for k in sorted(by, key=lambda k: (k[0] != "parties", k)):
        items = sorted(by[k], key=lambda x: (year_of(x[0], x[2]) or 0, x[1].name, x[2]["key"]))
        far = items[0][3]
        node_row = max((x[4] for x in items), key=lambda rr: (rr.get("year") or 0, rr["key"]))     # a candidate: the latest return
        far_id = add_node(far, node_row, nid)
        if not far_id:
            g["not_drawn"]["money"] += 1
            continue
        addends = []
        for gift, v, r, _, rr in items:
            why = ""
            if r.get("amount") is None:
                why = "no amount filed, not added"
            elif gift.replaced and r.get(gift.replaced):
                why = "replaced by an amendment, not added"
            elif not gift.added:
                why = "a disclosure: its gift is also in the year's return, never added to it"
            addends.append({"year": year_of(gift, r), "amount": r.get(gift.amount), "what": gift.what,
                            "cite": node_id(v, r), "not_added": why, "apart": not gift.added and not (gift.replaced and r.get(gift.replaced)),
                            "record": f"{gift.record_view}:{r[gift.record]}" if gift.record and r.get(gift.record) else "",
                            "record_words": "the return" if gift.record else ""})
        if far.name == "candidate_return_totals":
            g["nodes"][far_id]["title"] = " ".join(str(node_row.get(c) or "") for c in ("given_names", "surname")).strip() or None
        add_edge("money", nid, far_id, gift_label(addends), addends[0]["cite"], addends=addends)


# ── layout and drawing: pure ────────────────────────────────────────────────

# The layered layout (ruling 92 (1)): the matched rows on one horizontal line
# in the middle, by register then title, evenly spaced; like a family tree
# both ways. A row a matched row names (its company, party, return,
# recipient: what it belongs to or pays) sits above; a row that names a
# matched row (its directors, shareholders, officers, donors) below; a
# same-person row beside its match on the middle line, one each side where the
# width allows, else below with the people. Every node of a layer stands in a
# block: one per set of matched rows it is joined to, centred at their mean x
# (so a node joined to several is drawn once, between them), its width shared
# by need, wrapped into tiers when its nodes outnumber its slots, every node
# at its own x so a deeper tier's drop passes between the nearer tier's nodes.
# Every edge has right angles: vertical from the matched row, a horizontal run
# on a channel between the middle line and the layer, vertical to the far
# node. One matched row's edges on one side share one run, the family tree's
# bar; bars whose spans overlap take different channels, ordered to cross least.
SLOT = 110              # px between two nodes of one row (a node's label is shortened to its slot)
MARGIN = 60             # px left clear at each side
W_MIN, W_MAX = 1000, 2000     # the picture's width: the pane's, and the most the middle line may take with rows beside
TIER = 46               # px between two tiers of a layer: a circle and its two-line label
MID_ROOM = 42           # px from the middle line to the nearest channel: a matched row's label, either side
CH = 7                  # px between two channels
NEAR_CH = 16            # px from the farthest channel to the nearest tier's circles
EDGE_ROOM = 34          # px beyond the outermost tier: its labels
PORT = 4                # px between the ends of a shared node's edges, so they fan from it
REG_ORDER = {r: i for i, (r, _) in enumerate(cat.REGISTERS)}


def matched_order(g: dict) -> list:
    """The matched rows, left to right: by register (the catalogue's order), then title, then id."""
    return sorted((nid for nid, n in g["nodes"].items() if n["matched"]),
                  key=lambda nid: (REG_ORDER.get(g["nodes"][nid]["v"].register, len(REG_ORDER)), node_title(g["nodes"][nid]).lower(), nid))


def side_of(g: dict, lns: list) -> tuple:
    """({node id: "up", "down", "beside" or "mid"}, {line n: the line's side}).
    A line's side is its first cause's: a relation from the matched row (it
    names the far row) is "up", to it (the far row names it) is "down", a
    same-person verdict is "beside"; between two matched rows "mid". A node
    takes "up" if any of its lines does, else "down", else "beside" when one
    matched row alone reaches it."""
    line_side, sides = {}, {}
    for ln in lns:
        a, b = g["nodes"][ln["a"]], g["nodes"][ln["b"]]
        if a["matched"] and b["matched"]:
            line_side[ln["n"]] = "mid"
            continue
        m, o = (ln["a"], ln["b"]) if a["matched"] else (ln["b"], ln["a"])
        first = ln["causes"][0]
        s = "beside" if first["kind"] in (CONFIRMED, NEAR) else ("up" if first["a"] == m else "down")
        line_side[ln["n"]] = s
        sides.setdefault(o, []).append(s)
    node = {nid: "mid" for nid, n in g["nodes"].items() if n["matched"]}
    for o, ss in sides.items():
        node[o] = "up" if "up" in ss else ("down" if "down" in ss or len(ss) > 1 else "beside")
    for nid in g["nodes"]:
        node.setdefault(nid, "down")                   # a row drawn with no line of its own (never expected): below
    return node, line_side


def segments(path: list) -> list:
    return [(path[i], path[i + 1]) for i in range(len(path) - 1) if path[i] != path[i + 1]]


def _cross(p, q) -> bool:
    """A horizontal and a vertical segment meet strictly inside both."""
    (a, b), (c, d) = p, q
    if a[1] == b[1] and c[0] == d[0]:
        (a, b), (c, d) = (c, d), (a, b)
    if not (a[0] == b[0] and c[1] == d[1]):
        return False
    x, y = a[0], c[1]
    return min(c[0], d[0]) < x < max(c[0], d[0]) and min(a[1], b[1]) < y < max(a[1], b[1])


def crossings(paths: dict, ends: dict) -> int:
    """Pairs of segments of two lines that cross, the lines sharing no node."""
    segs = {n: segments(p) for n, p in paths.items()}
    keys = sorted(segs)
    return sum(1 for i, m in enumerate(keys) for n in keys[i + 1:] if not (ends[m] & ends[n])
               for s in segs[m] for t in segs[n] if _cross(s, t))


def orthogonal(path: list) -> bool:
    return all(a[0] == b[0] or a[1] == b[1] for a, b in segments(path))


def layout(g: dict, lns: list = None) -> dict:
    """{'pos': {node id: (x, y)}, 'paths': {line n: [(x, y), …]}, 'w', 'h',
    'bands': the channel bands, where no node label goes, 'crossings': the
    count of crossing segments, 'tiers': {side: n}}; deterministic and pure."""
    lns = lines(g) if lns is None else lns
    mids = matched_order(g)
    node_side, line_side = side_of(g, lns)
    m_of = {}                                       # a non-matched node -> its matched neighbours
    for ln in lns:
        if line_side[ln["n"]] != "mid":
            m, o = (ln["a"], ln["b"]) if g["nodes"][ln["a"]]["matched"] else (ln["b"], ln["a"])
            m_of.setdefault(o, []).append(m)
    for nid, n in g["nodes"].items():
        if not n["matched"] and nid not in m_of and mids:
            m_of[nid] = [n["parent"] if n.get("parent") in mids else mids[0]]
    beside = {}
    for o in sorted((o for o, s in node_side.items() if s == "beside"), key=lambda o: g["nodes"][o]["order"]):
        beside.setdefault(m_of[o][0], []).append(o)
    per_side = 1 if beside and len(mids) * 3 * SLOT + 2 * MARGIN <= W_MAX else 0
    for m, os_ in beside.items():
        for o in os_[2 * per_side:]:
            node_side[o] = "down"                    # no room beside: below, with the people
    step = SLOT * (1 + 2 * per_side)
    layer = {s: sorted(o for o, x in node_side.items() if x == s) for s in ("up", "down")}
    w = max(W_MIN, len(mids) * step + 2 * MARGIN)      # only the middle line widens the picture; a full layer wraps into tiers
    left = (w - len(mids) * step) / 2
    xm = {m: left + step * (i + 0.5) for i, m in enumerate(mids)}
    pos = {m: (xm[m], 0.0) for m in mids}
    for m, os_ in beside.items():
        for j, o in enumerate(os_[:2 * per_side]):
            pos[o] = (xm[m] + (SLOT if j % 2 == 0 else -SLOT), 0.0)
    tiers, tier_of = {}, {}
    for s in ("up", "down"):
        # a block per set of matched rows a node is joined to, centred at their mean x where the layer has room
        groups = {}
        for o in layer[s]:
            groups.setdefault(tuple(sorted(set(m_of[o]), key=mids.index)), []).append(o)
        keys = sorted(groups, key=lambda k: (sum(xm[m] for m in k) / len(k), [mids.index(m) for m in k]))
        room = w - 2 * MARGIN
        widths = [SLOT * len(groups[k]) for k in keys]          # a slot a node; a full layer shares its width by need
        if sum(widths) > room:
            widths = [x * room / sum(widths) for x in widths]
        starts, at = [], MARGIN
        for k, bw in zip(keys, widths):
            centre = sum(xm[m] for m in k) / len(k)
            starts.append(max(at, centre - bw / 2))
            at = starts[-1] + bw
        for i in range(len(keys) - 1, -1, -1):
            starts[i] = min(starts[i], (starts[i + 1] if i + 1 < len(keys) else w - MARGIN) - widths[i])
        at = []
        for k, bw, x0 in zip(keys, widths, starts):
            os_ = sorted(groups[k], key=lambda o: (node_title(g["nodes"][o]).lower(), o))
            at += [(x0 + bw * (i + 0.5) / len(os_), o) for i, o in enumerate(os_)]
        # every block is scaled alike, so its nodes stand evenly; the k-th node of the layer, left to right, goes to
        # tier k mod tiers, which keeps a slot between two nodes of a tier and every node at its own x
        tiers[s] = math.ceil(SLOT * len(at) / sum(widths)) if at else 0
        for i, (x, o) in enumerate(sorted(at)):
            pos[o], tier_of[o] = (x, 0.0), i % tiers[s]
    # ports: a node joined to several matched rows takes each edge at its own x, so the edges fan from it
    port = {}
    for o, ms in m_of.items():
        ms = sorted(set(ms), key=lambda m: xm[m])
        for j, m in enumerate(ms):
            port[(o, m)] = pos[o][0] + (j - (len(ms) - 1) / 2) * PORT
    # the bars: one per matched row and side, and one per line between two matched rows (drawn below)
    bars, mid_lines = {}, []
    for ln in lns:
        s = line_side[ln["n"]]
        if s == "mid":
            a, b = sorted((ln["a"], ln["b"]), key=lambda m: xm[m])
            if not any(xm[a] < pos[o][0] < xm[b] for o in pos if o not in tier_of and o not in (a, b)):
                continue                                             # neighbours on the middle line: a straight run between them
            mid_lines.append((ln["n"], xm[a] + PORT, xm[b] - PORT))
            continue
        m, o = (ln["a"], ln["b"]) if g["nodes"][ln["a"]]["matched"] else (ln["b"], ln["a"])
        s = node_side[o]
        if s == "beside":
            continue
        bar = bars.setdefault((m, s), {"side": s, "lines": [], "xs": [xm[m]]})
        bar["lines"].append(ln["n"])
        bar["xs"].append(port.get((o, m), pos[o][0]))

    def paths_of(k: tuple, y0: float, yc: float, ys: dict) -> dict:
        b = bars[k]
        if k[0] == "mid":
            (xa, xb), n = b["xs"], b["lines"][0]
            return {n: [(xa, y0), (xa, yc), (xb, yc), (xb, y0)]}
        m, out = k[0], {}
        for n in b["lines"]:
            ln = lns[n - 1]
            o = ln["b"] if ln["a"] == m else ln["a"]
            xo = port.get((o, m), pos[o][0])
            out[n] = [(xm[m], y0), (xm[m], yc), (xo, yc), (xo, ys[o])]
        return out

    for n, xa, xb in mid_lines:
        # a line between two matched rows runs on the side where fewer drops and trunks stand inside its span
        inside = {sd: sum(1 for b in bars.values() if b["side"] == sd for x in b["xs"] if xa < x < xb) for sd in ("up", "down")}
        bars[("mid", n)] = {"side": "up" if inside["up"] <= inside["down"] else "down", "lines": [n], "xs": [xa, xb]}
    ends = {ln["n"]: {ln["a"], ln["b"]} for ln in lns}
    span = {k: (min(b["xs"]), max(b["xs"])) for k, b in bars.items()}
    chan = {}
    for s in ("up", "down"):
        # each pair of bars whose spans overlap crosses a set number of times whichever channel is nearer the middle
        # line, and only that order matters: count both orders on a sketch (the middle line at 0, the channels at
        # 1 and 2, the tiers beyond), order the bars to spend the least, then share a channel where spans part
        sign = -1 if s == "up" else 1
        sketch = {nid: sign * (1000 + tier_of[nid]) for nid in tier_of}
        mine = sorted((k for k, b in bars.items() if b["side"] == s), key=lambda k: (span[k][1] - span[k][0], span[k], str(k)))
        cost = {}
        for i, a in enumerate(mine):
            for b in mine[i + 1:]:
                if span[a][0] <= span[b][1] + CH and span[b][0] <= span[a][1] + CH:
                    for near, far in ((a, b), (b, a)):
                        pa, pb = paths_of(near, 0, sign, sketch), paths_of(far, 0, 2 * sign, sketch)
                        both = {**pa, **pb}
                        cost[(near, far)] = crossings(both, ends) - crossings(pa, ends) - crossings(pb, ends)
        order = list(mine)
        for _ in range(4):                       # move each bar to its cheapest place, until none moves
            moved = False
            for k in list(order):
                rest = [x for x in order if x != k]
                spend = [sum(cost.get((x, k), 0) for x in rest[:i]) + sum(cost.get((k, x), 0) for x in rest[i:]) for i in range(len(rest) + 1)]
                best = min(range(len(spend)), key=lambda i: (spend[i], i))
                if rest[:best] + [k] + rest[best:] != order and spend[best] < spend[order.index(k)]:
                    order, moved = rest[:best] + [k] + rest[best:], True
            if not moved:
                break
        for i, k in enumerate(order):
            chan[k] = 1 + max([chan[x] for x in order[:i] if span[x][0] <= span[k][1] + CH and span[k][0] <= span[x][1] + CH], default=-1)
    count = {s: 1 + max([c for k, c in chan.items() if bars[k]["side"] == s], default=-1) for s in ("up", "down")}
    up_ch, dn_ch = count["up"], count["down"]
    top = 20 + (EDGE_ROOM + (tiers["up"] - 1) * TIER + NEAR_CH + max(up_ch - 1, 0) * CH if tiers["up"] else 0)
    y0 = top + MID_ROOM
    yc = {k: y0 + (-1 if bars[k]["side"] == "up" else 1) * (MID_ROOM + c * CH) for k, c in chan.items()}
    tier_y = {"up": lambda t: y0 - MID_ROOM - max(up_ch - 1, 0) * CH - NEAR_CH - t * TIER,
              "down": lambda t: y0 + MID_ROOM + max(dn_ch - 1, 0) * CH + NEAR_CH + t * TIER}
    ys = {nid: (tier_y[node_side[nid]](tier_of[nid]) if nid in tier_of else y0) for nid in pos}
    h = (tier_y["down"](tiers["down"] - 1) + EDGE_ROOM if tiers["down"] else y0 + MID_ROOM) + 20
    paths = {}
    for k in bars:
        paths.update(paths_of(k, y0, yc[k], ys))
    for ln in lns:
        if ln["n"] not in paths:                                 # beside, or two neighbours, on the middle line
            paths[ln["n"]] = [(pos[ln["a"]][0], y0), (pos[ln["b"]][0], y0)]
    paths = {n: [(round(x, 1), round(y, 1)) for x, y in p] for n, p in paths.items()}
    bands = []
    for s in ("up", "down"):
        cs = [y for k, y in yc.items() if bars[k]["side"] == s]
        if cs:
            bands.append((0, min(cs) - 3, w, max(cs) + 3))
    final = {nid: (round(pos[nid][0], 1), round(ys[nid], 1)) for nid in pos}
    room = {}                                       # the width a node's label may take: the gap to its nearest neighbour on its row
    for nid, (x, y) in final.items():
        gaps = [abs(x - x2) for j, (x2, y2) in final.items() if j != nid and y2 == y] + [2 * x, 2 * (w - x)]
        room[nid] = min(gaps)
    return {"pos": final, "paths": paths, "w": w, "h": h, "bands": bands, "crossings": crossings(paths, ends),
            "tiers": dict(tiers), "y0": y0, "room": room, "side": node_side}


def node_title(n: dict) -> str:
    """A node's name: the row's title, or the donor's name as filed and a
    candidate's name where the node stands for several rows (ruling 86 (3))."""
    return n.get("title") or panes.title_of(n["v"], n["row"])


def short(text: str, n: int = 30) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[:n - 1] + "…"


KIND_ORDER = {k: i for i, (k, _, _) in enumerate(cat.EDGE_KINDS)}


def cause_text(e: dict, with_rule: bool = True) -> str:
    """One cause in words: "same person, near: same name, nothing else
    (links rule name-only, version 1)". The rule id only here, for a
    tooltip or the list (ruling 84)."""
    return f"{e['kind']}: {e['label']}" + (f" {cat.rule_ref(e['rule'])}" if with_rule and e.get("rule") else "")


def lines(g: dict) -> list:
    """One line per pair of rows (ruling 84: causes listed, not drawn over
    each other), in the order the pairs were found, `n` an index that is
    never drawn (ruling 86):
    {'n', 'a', 'b', 'causes': [edges in the key's order], 'kind': the
    first cause's kind, which sets the stroke}."""
    out, at = [], {}
    for e in g["edges"]:
        pair = frozenset((e["a"], e["b"]))
        if pair not in at:
            at[pair] = len(out)
            out.append({"n": len(out) + 1, "a": e["a"], "b": e["b"], "causes": []})
        out[at[pair]]["causes"].append(e)
    for ln in out:
        ln["causes"].sort(key=lambda e: KIND_ORDER[e["kind"]])       # stable: found order within a kind
        ln["kind"] = ln["causes"][0]["kind"]
    return out


# Estimated text boxes, so no text is drawn touching another. The widths are
# generous averages for the fonts the stylesheet sets (11px names, 9px
# registers and edge words); a box is (x0, y0, x1, y1). `text_boxes` reads
# the same boxes back from the rendered SVG, so the rule is held on what is
# drawn, not on what was meant.
NAME_W, REG_W, WORD_W = 6.4, 5.2, 5.2
GAP = 2                                              # boxes keep this far apart: "touch" is within it
LABEL_LENGTHS = (30, 22, 16, 11, 7)                 # a node's name shortened step by step until it clears
WORDS_AT = (0.5,) + tuple(t for d in range(1, 10) for t in (0.5 - 0.045 * d, 0.5 + 0.045 * d))   # along a line, from its middle out
WORDS_MAX = 28                                       # an edge's words on the picture; the tooltip and the list carry them whole


def _hits(box: tuple, boxes: list, gap: float, size: tuple) -> bool:
    x0, y0, x1, y1 = box
    if x0 < 0 or y0 < 0 or x1 > size[0] or y1 > size[1]:
        return True
    return any(x0 - gap < b[2] and b[0] < x1 + gap and y0 - gap < b[3] and b[1] < y1 + gap for b in boxes)


def radius(n: dict) -> int:
    return 11 if n["centre"] else (8 if n["matched"] else 6)


def words_of_line(ln: dict) -> str:
    """What a line says on the picture: its first cause's words, and how many
    more causes the tooltip and the list carry."""
    more = len(ln["causes"]) - 1
    return short(ln["causes"][0]["label"], WORDS_MAX) + (f" (+{more})" if more else "")


def along(path: list, t: float) -> tuple:
    """The point a fraction t of the way along a path, by its length."""
    segs = segments(path) or [(path[0], path[0])]
    total = sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in segs) or 1.0
    at = t * total
    for a, b in segs:
        d = abs(b[0] - a[0]) + abs(b[1] - a[1])
        if at <= d or (a, b) == segs[-1]:
            f = at / d if d else 0
            return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        at -= d
    return path[-1]


def place(g: dict, lay: dict, lns: list) -> dict:
    """Deterministic placement of every node label and edge's words, pure.
    {'labels': {node id: (name, register, x, y_name, y_register, anchor,
    box) or None}, 'words': {line n: (text, x, y, box) or None}}. A node's
    label sits above its circle in the upper layer and under it in the lower
    (outward, so a tier never takes the next one's room), under or else above
    on the middle line, no wider than the gap to its row's nearest node,
    shortened until it clears every label placed before it, every other circle
    and every channel band (ruling 92: a label is never on a channel), the
    register line dropped last of all; a node with no room
    keeps its name in its tooltip. An edge's words sit on its path, moved
    along it from its middle until their box touches no label, no other words
    and no circle (GAP apart); with no room they are left off the picture and
    kept in the tooltip and the list."""
    pos, size, side = lay["pos"], (lay["w"], lay["h"]), lay["side"]
    placed, labels, words = [], {}, {}
    circle = {nid: (pos[nid][0] - radius(n) - 1, pos[nid][1] - radius(n) - 1, pos[nid][0] + radius(n) + 1, pos[nid][1] + radius(n) + 1)
              for nid, n in g["nodes"].items()}
    bands = lay.get("bands", [])
    order = sorted(g["nodes"].items(), key=lambda kv: (not kv[1]["matched"], kv[1]["order"]))     # the matched rows' names first
    for nid, n in order:
        x, y = pos[nid]
        rad = radius(n)
        name, reg = node_title(n), n["v"].register.replace("_", " ")
        others = [b for k, b in circle.items() if k != nid] + bands
        labels[nid] = None
        tries = [(k, True) for k in LABEL_LENGTHS] + [(k, False) for k in LABEL_LENGTHS[-2:]]
        for k, with_reg in tries:
            t1, t2 = short(name, k), (short(reg, k + 4) if with_reg else "")
            w = max(len(t1) * NAME_W, len(t2) * REG_W) + 2
            if w > lay["room"][nid] - GAP and k != LABEL_LENGTHS[-1]:
                continue
            h = 25 if with_reg else 14
            below, above = (x - w / 2, y + rad + 1 + GAP), (x - w / 2, y - rad - 1 - GAP - h)
            spots = {"up": (above,), "down": (below,)}.get(side.get(nid), (below, above))     # a layer's names face outward
            for left, top in spots:
                box = (left, top, left + w, top + h)
                if not _hits(box, placed, GAP, size) and not _hits(box, others, 0, size):
                    labels[nid] = (t1, t2, left + w / 2, top + 11, top + 22, "middle", box)
                    placed.append(box)
                    break
            if labels[nid]:
                break
    circles = list(circle.values())
    for ln in lns:
        path = lay["paths"][ln["n"]]
        text = words_of_line(ln)
        w = len(text) * WORD_W / 2 + 2
        words[ln["n"]] = None
        for t in WORDS_AT:
            x, y = along(path, t)
            box = (x - w, y - 6, x + w, y + 6)
            if not _hits(box, placed + circles, GAP, size):
                words[ln["n"]] = (text, x, y, box)
                placed.append(box)
                break
    return {"labels": labels, "words": words}


def overlaps(placement: dict) -> list:
    """Pairs of drawn labels or words whose boxes touch (within GAP); the check wants none."""
    boxes = [("label " + k, v[-1]) for k, v in placement["labels"].items() if v] + \
            [(f"words of line {k}", v[-1]) for k, v in placement["words"].items() if v]
    return [(a, b) for i, (a, ba) in enumerate(boxes) for b, bb in boxes[i + 1:] if touch(ba, bb)]


def touch(a: tuple, b: tuple, gap: float = 0) -> bool:
    return a[0] - gap < b[2] and b[0] < a[2] + gap and a[1] - gap < b[3] and b[1] < a[3] + gap


#: per class of <text> on the picture: (width of a character, rise above the baseline, fall below it)
TEXT_SIZES = {"": (NAME_W, 10, 2), "reg": (REG_W, 7, 2), "words": (WORD_W, 7, 2)}


def text_boxes(picture: str) -> list:
    """Every <text> the rendered SVG draws, as (text, class, box), its box
    worked out from what the SVG says alone: its x and y, its anchor, its
    class (which sets its size in the stylesheet) and its characters."""
    out = []
    for attrs, body in re.findall(r"<text\b([^>]*)>(.*?)</text>", picture, flags=re.S):
        a = dict(re.findall(r'([a-z-]+)="([^"]*)"', attrs))
        cls = a.get("class", "")
        cw, rise, fall = TEXT_SIZES.get(cls, TEXT_SIZES[""])
        t = html.unescape(body)
        x, y, w = float(a["x"]), float(a["y"]), len(t) * cw + 2
        x0 = {"middle": x - w / 2, "start": x - 1, "end": x + 1 - w}[a.get("text-anchor", "start")]
        out.append((t, cls, (x0, y - rise, x0 + w, y + fall)))
    return out


def touching_text(picture: str) -> list:
    """Pairs of text boxes on the rendered picture that touch; empty when none does."""
    boxes = text_boxes(picture)
    return [(a[0], b[0]) for i, a in enumerate(boxes) for b in boxes[i + 1:] if touch(a[2], b[2])]


def path_d(path: list) -> str:
    """An SVG path of right angles: M, then H or V for each segment."""
    out = [f"M{path[0][0]:.1f} {path[0][1]:.1f}"]
    for a, b in segments(path):
        out.append(f"H{b[0]:.1f}" if a[1] == b[1] else f"V{b[1]:.1f}")
    return " ".join(out)


def svg(g: dict, q: str, boxes=None, lns: list = None, placement: dict = None, lay: dict = None) -> str:
    lns = lines(g) if lns is None else lns
    lay = layout(g, lns) if lay is None else lay
    pos, W, H = lay["pos"], lay["w"], lay["h"]
    placement = place(g, lay, lns) if placement is None else placement
    out = [f'<div class="picture"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-label="register rows as nodes, the matched rows on the middle line, what they belong to above and what belongs '
           f'to them below, the connections their registers assert as right-angled edges coloured by kind">',
           f'<rect class="bg" width="{W}" height="{H}"/>']        # styled by the page's one stylesheet (panes.CSS)
    for ln in lns:
        colour, dash = KIND[ln["kind"]]
        d = f' stroke-dasharray="{dash}"' if dash else ""
        title = "; ".join(cause_text(e) for e in ln["causes"])
        out.append(f'<path class="edge" d="{path_d(lay["paths"][ln["n"]])}" stroke="{colour}"{d}>'
                   f'<title>{panes.esc(title)}</title></path>')
    for ln in lns:
        at = placement["words"].get(ln["n"])
        if not at:
            continue
        text, x, y, _ = at
        cite = panes.href(q, [ln["causes"][0]["cite"]], boxes)
        out.append(f'<a href="{panes.esc(cite)}"><title>{panes.esc("; ".join(cause_text(e) for e in ln["causes"]))}</title>'
                   f'<text class="words" x="{x:.1f}" y="{y + 3:.1f}" text-anchor="middle">{panes.esc(text)}</text></a>')
    for nid, n in sorted(g["nodes"].items(), key=lambda kv: kv[1]["order"]):
        x, y = pos[nid]
        v, r = n["v"], n["row"]
        title = node_title(n)
        rad = radius(n)
        to = panes.href(q, [], boxes, "/graph") + "&" + urllib.parse.urlencode({"c": nid})
        lab = placement["labels"].get(nid)
        text = ""
        if lab:
            t1, t2, lx, y1, y2, anchor, _ = lab
            text = f'<text x="{lx:.1f}" y="{y1:.1f}" text-anchor="{anchor}">{panes.esc(t1)}</text>'
            if t2:
                text += f'<text class="reg" x="{lx:.1f}" y="{y2:.1f}" text-anchor="{anchor}">{panes.esc(t2)}</text>'
        out.append(f'<a href="{panes.esc(to)}"><title>{panes.esc(title)} · {panes.esc(panes.register_heading(v.register))} · {panes.esc(v.name)}</title>'
                   f'<circle class="{"matched" if n["matched"] else "other"}" cx="{x:.1f}" cy="{y:.1f}" r="{rad}"/>{text}</a>')
    out.append("</svg></div>")
    return "".join(out)


def far_end(g: dict, ln: dict) -> tuple:
    """(near node id, far node id) of a line: the far end is the row reached
    from a matched one; between two matched rows, the one found later."""
    a, b = g["nodes"][ln["a"]], g["nodes"][ln["b"]]
    if a["matched"] != b["matched"]:
        return (ln["a"], ln["b"]) if a["matched"] else (ln["b"], ln["a"])
    return (ln["a"], ln["b"]) if a["order"] <= b["order"] else (ln["b"], ln["a"])


def addends_list(e: dict, q: str, boxes=None) -> str:
    """The rows a summed edge adds (tranche 3), each amount and year with its
    href, and the rows listed but not added, with the reason."""
    out = []
    for x in e.get("addends") or []:
        why = f' <span class="warn">{panes.esc(x["not_added"])}</span>' if x.get("not_added") else ""
        ret = f' · <a href="{panes.esc(panes.href(q, [x["record"]], boxes))}">{panes.esc(x["record_words"])}</a>' if x.get("record") else ""
        out.append(f'<li>{panes.esc(x["year"] if x.get("year") is not None else "year not stated")} · '
                   f'{panes.fmt(x["amount"], "amount")} · {panes.esc(x["what"])}{why} · '
                   f'<a href="{panes.esc(panes.href(q, [x["cite"]], boxes))}">the row</a>{ret}</li>')
    return f'<ul class="addends">{"".join(out)}</ul>' if out else ""


def edge_list(g: dict, lns: list, placement: dict, q: str, boxes=None) -> str:
    """Under the key (ruling 86, replacing ruling 84's numbers): one heading
    per connected row, by its title, its edges beneath, each cause with its
    kind, its words and an href to the row asserting it; the rows in the
    key's order of their first edge, then by title."""
    groups = {}
    for ln in lns:
        near_id, far_id = far_end(g, ln)
        groups.setdefault(far_id, []).append((near_id, ln))
    matched = sum(1 for n in g["nodes"].values() if n["matched"])

    def title(nid):
        n = g["nodes"][nid]
        return node_title(n)

    order = sorted(groups, key=lambda f: (min(KIND_ORDER[ln["kind"]] for _, ln in groups[f]), title(f).lower(), f))
    out = [f'<h3>Edges, by the row they reach <span class="count">{len(order):,} rows, {len(lns):,} lines</span></h3>']
    if len(g["edges"]) > len(lns):
        out.append(f'<p class="note">{len(g["edges"]):,} connections on {len(lns):,} lines: two rows joined more than once get one line, '
                   "its colour the first cause in the key's order, and every cause is listed here.</p>")
    off = sum(1 for ln in lns if not placement["words"].get(ln["n"]))
    if off:
        out.append(f'<p class="note">{off:,} lines have no room for their words on the picture: each keeps its tooltip and its place here.</p>')
    out.append('<div class="edges">')
    for f in order:
        n = g["nodes"][f]
        out.append(f'<h4>{panes.esc(title(f))} <span class="meta">{panes.esc(panes.register_heading(n["v"].register))} · {panes.esc(n["v"].name)}</span></h4><ul>')
        for near_id, ln in sorted(groups[f], key=lambda x: (KIND_ORDER[x[1]["kind"]], title(x[0]).lower())):
            frm = f' <span class="meta">from {panes.esc(title(near_id))}</span>' if matched > 1 else ""
            for e in ln["causes"]:
                rule = f' <span class="meta">{panes.esc(cat.rule_ref(e["rule"]))}</span>' if e.get("rule") else ""
                out.append(f'<li><span class="meta">{panes.esc(e["kind"])}</span> {panes.esc(e["label"])}{rule}{frm} · '
                           f'<a href="{panes.esc(panes.href(q, [e["cite"]], boxes))}">the row that asserts it</a>'
                           f'{addends_list(e, q, boxes)}</li>')
        out.append("</ul>")
    out.append("</div>")
    return "".join(out)


def key_table(g: dict) -> str:
    """The key below the picture: each colour named, with its edges counted."""
    out = ['<h3>Key</h3><table class="key"><tr><th></th><th>connection</th><th>edges drawn</th><th>not drawn (one hop, capped)</th></tr>']
    for kind, colour, dash in cat.EDGE_KINDS:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        swatch = f'<svg width="36" height="10"><line x1="0" y1="5" x2="36" y2="5" stroke="{colour}" stroke-width="3"{d}/></svg>'
        out.append(f"<tr><td>{swatch}</td><td>{panes.esc(kind)}</td><td>{g['drawn'][kind]:,}</td><td>{g['not_drawn'][kind]:,}</td></tr>")
    out.append("</table>")
    return "".join(out)


def pane(g: dict, q: str, boxes=None, regs=None) -> str:
    """`boxes` the check boxes every href carries; `regs` the registers searched (None: all)."""
    out = ['<section class="pane graph" id="graph">', '<div class="reg">graph</div>']
    if not g["nodes"]:
        out.append("<h2>Graph</h2>")
        if regs is not None and not regs and not g.get("centre"):
            out.append(f'<p class="why">{panes.NOTHING_TICKED}</p>' + key_table(g) + "</section>")
            return "\n".join(out)
        out.append('<p class="why">' + ("none found" if (q or g.get("centre") or (boxes is not None and boxes.fields)) else "Type a name, an address or a number in the search box.") + "</p>")
        out.append(key_table(g) + "</section>")
        return "\n".join(out)
    matched = [n for n in g["nodes"].values() if n["matched"]]
    if g.get("centre"):
        n = matched[0]
        out.append(f"<h2>{panes.esc(node_title(n))}</h2>")
        out.append(f'<p class="note">centred on one row; <a href="{panes.esc(panes.href(q, [g["centre"]], boxes))}">its pane</a>'
                   f' · <a href="{panes.esc(panes.href(q, [], boxes, "/graph"))}">back to the search</a></p>')
    else:
        out.append(f"<h2>{panes.esc(q) if q else 'By field'}</h2>" + panes.narrowed_line(boxes))
        more = g["matched_total"] - len(matched)
        out.append(f'<p class="note">{len(matched)} matching rows drawn' + (f"; {more:,} more match: narrow the search or the registers" if more > 0 else "") + "</p>")
    out.append('<p class="note">Rows are nodes; an edge is a connection the registers themselves assert, or a same-person verdict of the links. '
               "No edge is made by matching names here. Click a node to centre on it; an edge's words, where they fit, open the row "
               "that asserts it; hover a line for all it says; under the key the edges are listed by the row they reach.</p>")
    lns = lines(g)
    lay = layout(g, lns)
    placement = place(g, lay, lns)
    out.append(svg(g, q, boxes, lns, placement, lay))
    out.append(key_table(g))
    if any(e.get("addends") for e in g["edges"]):
        out.append('<p class="note">A donor\'s donations to one party or one candidate are one edge, its total the sum of the '
                   "return rows' own amounts, every addend listed under the edge below; the rows are those filed under one "
                   "donor name exactly as filed (case and macrons aside), which is not a finding that they are one person. "
                   "A disclosure is listed beside them and never added: its gift is also in that year's return.</p>")
    if g.get("gifts_cut"):
        out.append(f'<p class="note">{g["gifts_cut"]:,} more rows are filed under these names than one picture reads ({MAX_FILED} per view): '
                   "the totals are of the rows listed.</p>")
    if g.get("gifts_unplaced"):
        out.append(f'<p class="note">{g["gifts_unplaced"]:,} donation rows name no party or return the published views hold, and are not drawn</p>')
    if g["unresolved"]:
        out.append(f'<p class="note">{g["unresolved"]} linked rows were not found in the published views and are not drawn</p>')
    out.append(edge_list(g, lns, placement, q, boxes))
    out.append("</section>")
    return "\n".join(out)
