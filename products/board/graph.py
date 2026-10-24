"""The graph tab (ruling 80; plan 4.9, second version): the rows a search
matches are nodes; every connection their registers assert is an edge, one
hop out, typed and coloured, with a key below the picture. The picture is
SVG written here, with no script and no library: every node is an href that
re-centres on it, and every edge's label is an href to the register row that
asserts the connection, so every edge is cited.

Edges come from two places only, both published: a catalogue `Relation`
(this row's column names a row of another view, as the lane's own pane.md
says) and `pub.links` (the links' same-person verdicts, confirmed solid and
near dashed). The board matches no name by looking (plan 4.9: no link is
made by looking), and draws no address edge of any kind (hard limit 15).

`build` reads; `layout` and `svg`/`pane` are pure."""
from __future__ import annotations

import math
import urllib.parse
import re

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


def build(conn, q: str, regs=None, centre: str = "") -> dict:
    """{'nodes': {id: {v, row, matched, centre, order}}, 'edges': [...],
    'drawn': {kind: n}, 'not_drawn': {kind: n}, 'matched_total', 'unresolved'}.
    An edge: kind, a, b (node ids), label, cite (the asserting row's id)."""
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
    elif q:
        res = search.search(conn, q, limit=PER_VIEW, registers=regs)
        for register, _ in cat.REGISTERS:
            for v, total, rows in res.get(register, []):
                g["matched_total"] += total
                matched.extend((v, r) for r in rows)
        matched = matched[:MAX_MATCHED]
    for v, r in matched:
        g["nodes"][node_id(v, r)] = {"v": v, "row": r, "matched": True, "centre": bool(centre), "order": len(g["nodes"]), "parent": None}
    seen = set()

    def add_edge(kind, a, b, label, cite):
        k = (kind, min(a, b), max(a, b), label)
        if k in seen:
            return
        seen.add(k)
        g["edges"].append({"kind": kind, "a": a, "b": b, "label": label, "cite": cite})
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
                    add_edge(kind, me, nid, str(l["rule"]), me)
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


def svg(g: dict, q: str, regs=()) -> str:
    pos = layout(g)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" '
           f'aria-label="register rows as nodes, the connections their registers assert as edges">',
           '<style>text{font:11px system-ui,sans-serif;fill:#222}text.reg{font-size:9px;fill:#666}'
           'text.lab{font-size:9px;fill:#444;paint-order:stroke;stroke:#fff;stroke-width:3px}'
           'a:hover text{text-decoration:underline}</style>',
           f'<rect width="{W}" height="{H}" fill="#fcfcfb"/>']
    for e in g["edges"]:
        (x1, y1), (x2, y2) = pos[e["a"]], pos[e["b"]]
        colour, dash = KIND[e["kind"]]
        d = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{colour}" stroke-width="2"{d}>'
                   f'<title>{panes.esc(e["kind"])}: {panes.esc(e["label"])}</title></line>')
    for e in g["edges"]:
        (x1, y1), (x2, y2) = pos[e["a"]], pos[e["b"]]
        cite = panes.href(q, [e["cite"]], regs)
        out.append(f'<a href="{panes.esc(cite)}"><text class="lab" x="{(x1 + x2) / 2:.1f}" y="{(y1 + y2) / 2:.1f}" '
                   f'text-anchor="middle">{panes.esc(short(e["label"], 26))}</text></a>')
    for nid, n in sorted(g["nodes"].items(), key=lambda kv: kv[1]["order"]):
        x, y = pos[nid]
        v, r = n["v"], n["row"]
        title = panes.title_of(v, r)
        rad = 11 if n["centre"] else (8 if n["matched"] else 6)
        fill, stroke, sw = ("#fde68a", "#222", 2.5) if n["matched"] else ("#ffffff", "#555", 1.5)
        to = panes.href(q, [], regs, "/graph") + "&" + urllib.parse.urlencode({"c": nid})
        out.append(f'<a href="{panes.esc(to)}"><title>{panes.esc(title)} · {panes.esc(panes.register_heading(v.register))} · {panes.esc(v.name)}</title>'
                   f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
                   f'<text x="{x:.1f}" y="{y + rad + 12:.1f}" text-anchor="middle">{panes.esc(short(title))}</text>'
                   f'<text class="reg" x="{x:.1f}" y="{y + rad + 23:.1f}" text-anchor="middle">{panes.esc(short(v.register.replace("_", " "), 34))}</text></a>')
    out.append("</svg>")
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


def pane(g: dict, q: str, regs=()) -> str:
    out = ['<section class="pane graph" id="graph">', '<div class="reg">graph</div>']
    if not g["nodes"]:
        out.append("<h2>Graph</h2>")
        out.append('<p class="why">' + ("none found" if (q or g.get("centre")) else "Type a name, an address or a number in the search box.") + "</p>")
        out.append(key_table(g) + "</section>")
        return "\n".join(out)
    matched = [n for n in g["nodes"].values() if n["matched"]]
    if g.get("centre"):
        n = matched[0]
        out.append(f"<h2>{panes.esc(panes.title_of(n['v'], n['row']))}</h2>")
        out.append(f'<p class="note">centred on one row; <a href="{panes.esc(panes.href(q, [g["centre"]], regs))}">its pane</a>'
                   f' · <a href="{panes.esc(panes.href(q, [], regs, "/graph"))}">back to the search</a></p>')
    else:
        out.append(f"<h2>{panes.esc(q)}</h2>")
        more = g["matched_total"] - len(matched)
        out.append(f'<p class="note">{len(matched)} matching rows drawn' + (f"; {more:,} more match: narrow the search or the registers" if more > 0 else "") + "</p>")
    out.append('<p class="note">Rows are nodes; an edge is a connection the registers themselves assert, or a same-person verdict of the links. '
               "No edge is made by matching names here. Click a node to centre on it; an edge's label opens the row that asserts it.</p>")
    out.append(svg(g, q, regs))
    out.append(key_table(g))
    if g["unresolved"]:
        out.append(f'<p class="note">{g["unresolved"]} linked rows were not found in the published views and are not drawn</p>')
    out.append(f'<h3>Edges <span class="count">{len(g["edges"]):,}</span></h3><ul>')
    for e in g["edges"]:
        a, b = g["nodes"][e["a"]], g["nodes"][e["b"]]
        out.append(f'<li><span class="meta">{panes.esc(e["kind"])}</span> {panes.esc(panes.title_of(a["v"], a["row"]))} '
                   f'<a href="{panes.esc(panes.href(q, [e["cite"]], regs))}">{panes.esc(e["label"])}</a> '
                   f'{panes.esc(panes.title_of(b["v"], b["row"]))}</li>')
    out.append("</ul></section>")
    return "\n".join(out)
