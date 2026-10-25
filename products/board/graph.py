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
W, H = 1000, 780
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
    for v, r in matched:
        g["nodes"][node_id(v, r)] = {"v": v, "row": r, "matched": True, "centre": bool(centre), "order": len(g["nodes"]), "parent": None}
    seen = set()

    def add_edge(kind, a, b, label, cite, rule=None):
        k = (kind, min(a, b), max(a, b), label, rule)
        if k in seen:
            return
        seen.add(k)
        g["edges"].append({"kind": kind, "a": a, "b": b, "label": label, "cite": cite, "rule": rule})
        g["drawn"][kind] += 1

    def add_node(v, r, parent):
        nid = node_id(v, r)
        if nid not in g["nodes"]:
            if len(g["nodes"]) >= MAX_NODES:
                return None
            g["nodes"][nid] = {"v": v, "row": r, "matched": False, "centre": False, "order": len(g["nodes"]), "parent": parent}
        return nid

    resolve = _resolver(conn)
    for v, r in matched:
        me = node_id(v, r)
        for rel in v.relations:                             # this row names the far end
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
        for src, rel in INCOMING.get(v.name, ()):           # another view's rows name this row
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


# ── layout and drawing: pure ────────────────────────────────────────────────

def layout(g: dict) -> dict:
    """{node id: (x, y)}, deterministic: each matched row gets a sector of
    the circle sized to its neighbours; it sits on an inner ring (alone, in
    the middle) and its neighbours fan out on the outer ring within its
    sector, in the order they were found, so a row's edges stay together."""
    cx, cy = W / 2, H / 2
    nodes = sorted(g["nodes"].items(), key=lambda kv: kv[1]["order"])
    inner = [nid for nid, n in nodes if n["matched"]]
    kids = {nid: [] for nid in inner}
    for nid, n in nodes:
        if not n["matched"]:
            kids.setdefault(n["parent"], []).append(nid)
    pos = {}
    r1 = 0 if len(inner) <= 1 else min(90 + 14 * len(inner), 230)
    rx, ry = W / 2 - 120, H / 2 - 60
    weights = [3 + len(kids.get(nid, [])) for nid in inner] or [1]      # a floor of three, so a row with few neighbours still has room
    total = float(sum(weights))
    at = -math.pi / 2 - math.pi * weights[0] / total          # the first row's sector is centred at the top
    for nid, w in zip(inner, weights):
        span = 2 * math.pi * w / total
        mid = at + span / 2
        pos[nid] = (cx + r1 * math.cos(mid), cy + r1 * math.sin(mid))
        ks = kids.get(nid, [])
        for i, k in enumerate(ks):
            a = at + span * (i + 1) / (len(ks) + 1) if len(inner) > 1 else at + span * (i + 0.5) / len(ks)
            ring = 1.0 if (len(ks) <= 8 or i % 2 == 0) else 0.82        # two rings when a fan is crowded, so labels clear
            pos[k] = (cx + rx * ring * math.cos(a), cy + ry * ring * math.sin(a))
        at += span
    return pos


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


def _hits(box: tuple, boxes: list, gap: float = 0) -> bool:
    x0, y0, x1, y1 = box
    if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
        return True
    return any(x0 - gap < b[2] and b[0] < x1 + gap and y0 - gap < b[3] and b[1] < y1 + gap for b in boxes)


def radius(n: dict) -> int:
    return 11 if n["centre"] else (8 if n["matched"] else 6)


def words_of_line(ln: dict) -> str:
    """What a line says on the picture: its first cause's words, and how many
    more causes the tooltip and the list carry."""
    more = len(ln["causes"]) - 1
    return short(ln["causes"][0]["label"], WORDS_MAX) + (f" (+{more})" if more else "")


def place(g: dict, pos: dict, lns: list) -> dict:
    """Deterministic placement of every node label and edge's words, pure.
    {'labels': {node id: (name, register, x, y_name, y_register, anchor,
    box) or None}, 'words': {line n: (text, x, y, box) or None}}. A node's
    label sits below its circle, else above, right or left, shortened until
    it clears every label placed before it and every other circle, the
    register line dropped last of all; a node with no room keeps its name in
    its tooltip. An edge's words sit on its line, moved along it until their
    box touches no label, no other words and no circle (GAP apart); with no
    room they are left off the picture and kept in the tooltip and the list."""
    placed, labels, words = [], {}, {}
    circle = {nid: (pos[nid][0] - radius(n) - 1, pos[nid][1] - radius(n) - 1, pos[nid][0] + radius(n) + 1, pos[nid][1] + radius(n) + 1)
              for nid, n in g["nodes"].items()}
    for nid, n in sorted(g["nodes"].items(), key=lambda kv: kv[1]["order"]):
        x, y = pos[nid]
        rad = radius(n)
        name, reg = panes.title_of(n["v"], n["row"]), n["v"].register.replace("_", " ")
        others = [b for k, b in circle.items() if k != nid]
        labels[nid] = None
        tries = [(k, True) for k in LABEL_LENGTHS] + [(k, False) for k in LABEL_LENGTHS[-2:]]
        for k, with_reg in tries:
            t1, t2 = short(name, k), (short(reg, k + 4) if with_reg else "")
            w = max(len(t1) * NAME_W, len(t2) * REG_W) + 2
            h = 25 if with_reg else 14
            spots = ((x - w / 2, y + rad + 1 + GAP, "middle"), (x - w / 2, y - rad - 1 - GAP - h, "middle"),     # below, above
                     (x + rad + 3 + GAP, y - h / 2, "start"), (x - rad - 3 - GAP - w, y - h / 2, "end"))         # right, left
            for left, top, anchor in spots:
                box = (left, top, left + w, top + h)
                if not _hits(box, placed, GAP) and not _hits(box, others):
                    tx = {"middle": left + w / 2, "start": left + 1, "end": left + w - 1}[anchor]
                    labels[nid] = (t1, t2, tx, top + 11, top + 22, anchor, box)
                    placed.append(box)
                    break
            if labels[nid]:
                break
    circles = list(circle.values())
    for ln in lns:
        (x1, y1), (x2, y2) = pos[ln["a"]], pos[ln["b"]]
        text = words_of_line(ln)
        w = len(text) * WORD_W / 2 + 2
        words[ln["n"]] = None
        for t in WORDS_AT:
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            box = (x - w, y - 6, x + w, y + 6)
            if not _hits(box, placed + circles, GAP):
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


def svg(g: dict, q: str, boxes=None, lns: list = None, placement: dict = None) -> str:
    pos = layout(g)
    lns = lines(g) if lns is None else lns
    placement = place(g, pos, lns) if placement is None else placement
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" '
           f'aria-label="register rows as nodes, the connections their registers assert as edges, coloured by kind">',
           f'<rect class="bg" width="{W}" height="{H}"/>']        # styled by the page's one stylesheet (panes.CSS)
    for ln in lns:
        (x1, y1), (x2, y2) = pos[ln["a"]], pos[ln["b"]]
        colour, dash = KIND[ln["kind"]]
        d = f' stroke-dasharray="{dash}"' if dash else ""
        title = "; ".join(cause_text(e) for e in ln["causes"])
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{colour}" stroke-width="2"{d}>'
                   f'<title>{panes.esc(title)}</title></line>')
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
        title = panes.title_of(v, r)
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
    out.append("</svg>")
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
        return panes.title_of(n["v"], n["row"])

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
        out.append(f"<h2>{panes.esc(panes.title_of(n['v'], n['row']))}</h2>")
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
    placement = place(g, layout(g), lns)
    out.append(svg(g, q, boxes, lns, placement))
    out.append(key_table(g))
    if g["unresolved"]:
        out.append(f'<p class="note">{g["unresolved"]} linked rows were not found in the published views and are not drawn</p>')
    out.append(edge_list(g, lns, placement, q, boxes))
    out.append("</section>")
    return "\n".join(out)
