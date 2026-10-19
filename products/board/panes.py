"""The panes, rendered to HTML with no script: the search pane, a row's
pane, a person's pane, and the lists of pins and saved paths. Pure: takes
the data it is given and returns a string. Every value is escaped. Every
rule for what a product shows applies here (design: "Rules for everything
a product shows"): a figure names its document; a blank says "none found"
or "not stated"; a figure read from pixels is marked; a suppressed name
reads "name suppressed"; a withheld text reads "withheld"."""
from __future__ import annotations

import datetime as dt
import decimal
import html
import re
import urllib.parse

from products.board import catalogue as cat

SUPPRESSED = "name suppressed"
WITHHELD = "withheld (hard limit 15; a ruling is owed before it is shown)"
NOT_STATED = "not stated"
PIXELS = "READ FROM PIXELS: weaker evidence"
MONEY = {"amount", "amount_original", "items_sum", "form_total", "figure", "printed_total", "rows_sum", "total",
         "declared_total", "part_a", "part_b", "part_c", "part_d", "part_f", "part_g", "loans_h", "loans_i", "loans_total",
         "expense_limit", "total_expenses", "allocation", "allocation_spent", "return_total", "election_expenses",
         "cannabis_referendum_expenses", "end_of_life_referendum_expenses"}
REGISTER_NAME = dict(cat.REGISTERS)

CSS = """
body{margin:0;font:14px/1.4 system-ui,sans-serif;color:#222;background:#f4f4f2}
header{display:flex;gap:1rem;align-items:center;padding:.5rem 1rem;background:#fff;border-bottom:1px solid #ddd;position:sticky;top:0;z-index:2}
header h1{font-size:15px;margin:0 1rem 0 0;font-weight:600}
header input[type=search]{width:28rem;padding:.35rem .5rem;font-size:14px}
header a{color:#246}
main{display:flex;gap:.75rem;padding:.75rem;overflow-x:auto;align-items:flex-start;min-height:calc(100vh - 3.5rem)}
.pane{flex:0 0 26rem;max-width:26rem;background:#fff;border:1px solid #d8d8d4;border-radius:4px;padding:.75rem;max-height:calc(100vh - 5rem);overflow-y:auto}
.pane.pinned{border-color:#b8860b}
.pane h2{font-size:15px;margin:.25rem 0}
.pane h3{font-size:12px;margin:1rem 0 .25rem;text-transform:uppercase;letter-spacing:.04em;color:#555;border-bottom:1px solid #eee}
.reg{font-size:11px;color:#666;text-transform:uppercase;letter-spacing:.04em}
.note,.why{font-size:12px;color:#666;font-style:italic}
.warn{color:#8a3b00;font-weight:600}
table.f{border-collapse:collapse;width:100%;font-size:13px}
table.f th{text-align:left;font-weight:normal;color:#666;vertical-align:top;padding:.1rem .5rem .1rem 0;width:40%}
table.f td{padding:.1rem 0;vertical-align:top;word-break:break-word}
ul{margin:.25rem 0;padding-left:1.1rem}
li{margin:.1rem 0}
li .meta{color:#777;font-size:12px}
.count{color:#777;font-weight:normal}
a{color:#246}
a.row{text-decoration:none}
a.row:hover{text-decoration:underline}
form.inline{display:inline}
button{font:inherit;font-size:12px;padding:.15rem .5rem}
.actions{display:flex;gap:.5rem;margin:.5rem 0;flex-wrap:wrap}
code{font-size:12px;word-break:break-all}
"""


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def encode_path(path: list) -> str:
    return urllib.parse.quote("|".join(path), safe="")


def href(q: str, path: list) -> str:
    return "/?" + urllib.parse.urlencode({"q": q, "p": "|".join(path)})


def fmt(value, column: str = "") -> str:
    """One value as the pane shows it, escaped."""
    if value is None or value == "":
        return f'<span class="note">{NOT_STATED}</span>'
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, dt.datetime):
        return esc(value.strftime("%-d %B %Y %H:%M"))
    if isinstance(value, dt.date):
        return esc(value.strftime("%-d %B %Y"))
    if isinstance(value, (int, decimal.Decimal, float)) and not isinstance(value, bool):
        if column in MONEY:
            return esc(f"${decimal.Decimal(value):,.2f}")
        return esc(str(value)) if isinstance(value, int) else esc(f"{decimal.Decimal(value):,}")   # a year or an ordinal is not grouped
    if isinstance(value, dict):
        return esc("; ".join(f"{k}: {v}" for k, v in value.items())) or f'<span class="note">{NOT_STATED}</span>'
    if isinstance(value, (list, tuple)):
        return esc("; ".join(str(x) for x in value)) or f'<span class="note">{NOT_STATED}</span>'
    return esc(value)


def is_suppressed(v: cat.View, r: dict) -> bool:
    if v.suppressed and r.get(v.suppressed):
        return True
    return bool(v.hide_names and re.search(v.hide_names[1], str(r.get(v.hide_names[0]) or ""), re.I))


def is_withheld(v: cat.View, r: dict) -> bool:
    return bool(v.withheld and r.get(v.withheld))


def shown(v: cat.View, r: dict, column: str):
    """The value a column shows: a suppressed row's name columns and a
    withheld row's text are replaced before anything is rendered."""
    if column in v.names and is_suppressed(v, r):
        return SUPPRESSED
    if column == "text" and is_withheld(v, r):
        return WITHHELD
    return r.get(column)


def title_of(v: cat.View, r: dict) -> str:
    parts = []
    for c in v.title:
        x = shown(v, r, c)
        if x not in (None, ""):
            parts.append(x.strftime("%-d %B %Y") if isinstance(x, dt.date) else str(x))
    return " · ".join(parts) or f"({v.name} {r.get('key', '')})"


def row_link(q: str, path: list, v: cat.View, r: dict, meta: str = "") -> str:
    t = esc(title_of(v, r))
    pix = f' <span class="warn">{PIXELS}</span>' if r.get("read_from") == "pixels" else ""
    m = f' <span class="meta">{esc(meta)}</span>' if meta else ""
    return f'<li><a class="row" href="{esc(href(q, path + [f"{v.name}:{r["key"]}"]))}">{t}</a>{m}{pix}</li>'


def register_heading(register: str) -> str:
    return esc(REGISTER_NAME.get(register, register))


# ── the first pane: the search ──────────────────────────────────────────────

def search_pane(q: str, results: dict, held: set) -> str:
    out = ['<section class="pane" id="search">', f'<div class="reg">search</div>']
    if not q:
        out.append("<h2>One search across every register</h2>")
        out.append('<p class="note">A name, an address, a company number or an NZBN. Every word must appear. '
                   "A suppressed name is never found by name.</p>")
    else:
        out.append(f"<h2>{esc(q)}</h2>")
    for register, plain in cat.REGISTERS:
        views = cat.views_of(register)
        present = [v for v in views if v.name in held]
        out.append(f"<h3>{esc(plain)}</h3>")
        if not present:
            out.append('<p class="why">not held</p>')
            continue
        hits = results.get(register, []) if q else []
        if q and not hits:
            out.append('<p class="why">none found</p>')
        for v, total, rows in hits:
            out.append(f'<div><strong>{esc(v.name)}</strong> <span class="count">{total:,}</span></div><ul>')
            for r in rows:
                out.append(row_link(q, [], v, r))
            if total > len(rows):
                out.append(f'<li class="note">and {total - len(rows):,} more; narrow the search</li>')
            out.append("</ul>")
    out.append("<h3>Not held</h3><ul>")
    for register, plain in cat.NOT_HELD:
        out.append(f'<li>{esc(plain)} <span class="meta">not held</span></li>')
    out.append("</ul></section>")
    return "\n".join(out)


# ── a row's pane ────────────────────────────────────────────────────────────

def citation(v: cat.View, r: dict, doc_names: list) -> str:
    out = ['<h3>Citation</h3><table class="f">']
    doc = r.get("document")
    if doc:
        out.append(f'<tr><th>document</th><td><code title="{esc(doc)}">{esc(doc[:12])}…</code></td></tr>')
    else:
        out.append(f'<tr><th>document</th><td><span class="note">{NOT_STATED}</span></td></tr>')
    for label, c in (("page", "page"), ("place", "place"), ("reader", "reader"), ("profile", "profile")):
        if c in r and r.get(c) not in (None, ""):
            out.append(f"<tr><th>{label}</th><td>{fmt(r.get(c))}</td></tr>")
    if r.get("read_from"):
        mark = f'<span class="warn">{PIXELS}</span>' if r["read_from"] == "pixels" else esc(r["read_from"])
        out.append(f"<tr><th>read from</th><td>{mark}</td></tr>")
    for c in v.urls:
        if r.get(c):
            u = str(r[c])
            out.append(f'<tr><th>{esc(c)}</th><td><a href="{esc(u)}" rel="noopener">{esc(u[:80])}</a></td></tr>')
    if doc_names:
        items = []
        for n in doc_names[:6]:
            if n.startswith("http://") or n.startswith("https://"):
                items.append(f'<a href="{esc(n)}" rel="noopener">{esc(n[:80])}</a>')
            else:
                items.append(esc(n))
        out.append(f'<tr><th>the document\'s names</th><td>{"<br>".join(items)}</td></tr>')
    elif doc:
        out.append('<tr><th>the document\'s names</th><td><span class="note">none recorded in the store</span></td></tr>')
    if r.get("source_note"):
        out.append(f'<tr><th>source</th><td>{esc(r["source_note"])}</td></tr>')
    if r.get("loaded_at"):
        out.append(f'<tr><th>row written</th><td>{fmt(r["loaded_at"])} <span class="note">(never a date of anything)</span></td></tr>')
    out.append("</table>")
    out.append('<p class="note">The document is cited, not opened: captured documents can carry addresses.</p>')
    return "\n".join(out)


def links_section(links: dict, group: dict, q: str, path: list, resolve) -> str:
    """resolve(ref) -> (view, row) or None, so a link opens the next pane."""
    out = ["<h3>Links</h3>"]
    if not links.get("built"):
        out.append(f'<p class="why">{esc(links.get("why"))}</p>')
        return "\n".join(out)
    if not links["confirmed"] and not links["near"]:
        out.append('<p class="why">none found: no rule joined this row to another</p>')
    for grade in ("confirmed", "near"):
        if not links[grade]:
            continue
        out.append(f"<div><strong>{grade}</strong> <span class=\"count\">{len(links[grade])}</span></div>")
        by_reg = {}
        for l in links[grade]:
            by_reg.setdefault(l["register"], []).append(l)
        for register in sorted(by_reg):
            out.append(f'<div class="reg">{register_heading(register)}</div><ul>')
            for l in by_reg[register]:
                target = resolve(l["other"])
                if target:
                    tv, tr = target
                    out.append(row_link(q, path, tv, tr, meta=f"rule {l['rule']}" + (f"; near because {l['reason']}" if l.get("reason") else "")))
                else:
                    out.append(f'<li>{esc(l["other"])} <span class="meta">row not found in the published views; rule {esc(l["rule"])}</span></li>')
                for d in l.get("decisions") or []:
                    out.append(f'<li class="meta">decision: {esc(d.get("verdict"))} by {esc(d.get("made_by"))}, {fmt(d.get("made_at"))}</li>')
            out.append("</ul>")
    return "\n".join(out)


def same_name_section(same: dict, q: str, path: list, words: list) -> str:
    out = ["<h3>Same name elsewhere</h3>"]
    if not words:
        out.append('<p class="why">not searched: this row\'s name is suppressed or empty</p>')
        return "\n".join(out)
    out.append('<p class="note">By name alone: every word of this row\'s name appears. Candidates, not identity; '
               "nothing here is a link.</p>")
    any_hit = False
    for register, _ in cat.REGISTERS:
        hits = same.get(register, [])
        if not hits:
            continue
        any_hit = True
        out.append(f'<div class="reg">{register_heading(register)}</div>')
        for v, total, rows in hits:
            out.append(f'<div><strong>{esc(v.name)}</strong> <span class="count">{total:,}</span></div><ul>')
            for r in rows:
                out.append(row_link(q, path, v, r))
            if total > len(rows):
                out.append(f'<li class="note">and {total - len(rows):,} more</li>')
            out.append("</ul>")
    if not any_hit:
        out.append('<p class="why">none found</p>')
    return "\n".join(out)


def row_pane(ctx: dict) -> str:
    """ctx: v, row, q, path (the path up to and including this pane),
    parent (label, view, row|None) or None, children [(join, total, rows)],
    doc_names, links, group, same, same_words, resolve, pinned (bool)."""
    v, r, q, path = ctx["v"], ctx["row"], ctx["q"], ctx["path"]
    before = path[:-1]
    out = [f'<section class="pane{" pinned" if ctx.get("pinned") else ""}">',
           f'<div class="reg">{register_heading(v.register)} · {esc(v.name)} · {esc(v.kind)}</div>',
           f"<h2>{esc(title_of(v, r))}</h2>"]
    if is_suppressed(v, r):
        out.append(f'<p class="warn">{SUPPRESSED}: the row and its figures stay (hard limit 16)</p>')
    if v.note:
        out.append(f'<p class="note">{esc(v.note)}</p>')
    out.append('<div class="actions">')
    out.append(f'<form class="inline" method="post" action="/pin"><input type="hidden" name="view" value="{esc(v.name)}">'
               f'<input type="hidden" name="key" value="{esc(r["key"])}"><input type="hidden" name="title" value="{esc(title_of(v, r))}">'
               f'<input type="hidden" name="q" value="{esc(q)}"><input type="hidden" name="p" value="{esc("|".join(path))}">'
               f'<button>{"pinned" if ctx.get("pinned") else "pin"}</button></form>')
    if v.kind == "person" and not is_suppressed(v, r):
        out.append(f'<a href="{esc(href(q, path + [f"person:{v.name}:{r["key"]}"]))}">person: the group and namesakes</a>')
    words = ctx.get("same_words") or []
    if words:
        out.append(f'<a href="{esc("/?" + urllib.parse.urlencode({"q": " ".join(words)}))}">search this name afresh</a>')
    out.append("</div>")
    # fields
    out.append('<h3>Fields</h3><table class="f">')
    for label, c in v.fields:
        if c not in r:
            continue
        out.append(f"<tr><th>{esc(label)}</th><td>{fmt(shown(v, r, c), c)}</td></tr>")
    out.append("</table>")
    if v.dates:
        out.append('<h3>Dates, as filed</h3><table class="f">')
        for label, c in v.dates:
            out.append(f"<tr><th>{esc(label)}</th><td>{fmt(r.get(c), c)}</td></tr>")
        out.append("</table>")
    # parent
    if ctx.get("parent"):
        label, view, prow = ctx["parent"]
        out.append(f"<h3>{esc(label)}</h3>")
        if prow:
            out.append("<ul>" + row_link(q, path, cat.BY_NAME[view], prow) + "</ul>")
        else:
            out.append('<p class="why">not held: the row it points at is not in the published view</p>')
    # children, in the same register
    for j, total, rows in ctx.get("children") or []:
        out.append(f'<h3>{esc(j.label)} <span class="count">{total:,}</span></h3>')
        if not rows:
            out.append('<p class="why">none found</p>')
            continue
        tv = cat.BY_NAME[j.view]
        out.append("<ul>")
        for cr in rows:
            out.append(row_link(q, path, tv, cr))
        if total > len(rows):
            out.append(f'<li class="note">and {total - len(rows):,} more</li>')
        out.append("</ul>")
    out.append(links_section(ctx.get("links") or {}, ctx.get("group") or {}, q, path, ctx.get("resolve") or (lambda ref: None)))
    if v.names:
        out.append(same_name_section(ctx.get("same") or {}, q, path, words))
    out.append(citation(v, r, ctx.get("doc_names") or []))
    out.append("</section>")
    return "\n".join(out)


# ── a person's pane ─────────────────────────────────────────────────────────

def person_pane(ctx: dict) -> str:
    """ctx: v, row, q, path, group ({'built', 'why', 'rows': [refs]}),
    members [(view, row)] resolved from the group, same (namesakes by name),
    same_words, links."""
    v, r, q, path = ctx["v"], ctx["row"], ctx["q"], ctx["path"]
    out = ['<section class="pane">', f'<div class="reg">person · from {register_heading(v.register)} · {esc(v.name)}</div>',
           f"<h2>{esc(title_of(v, r))}</h2>"]
    group = ctx.get("group") or {}
    out.append("<h3>The group</h3>")
    if not group.get("built"):
        out.append(f'<p class="why">{esc(group.get("why"))}</p>')
        out.append('<p class="note">Until then the group is this one row. Everything below is a namesake, apart.</p>')
    else:
        if group.get("contested"):
            out.append('<p class="warn">contested: the watch flagged this group as a whole</p>')
        if group.get("why"):
            out.append(f'<p class="why">{esc(group["why"])}</p>')
        members = ctx.get("members") or []
        by_reg = {}
        for mv, mr in members:
            by_reg.setdefault(mv.register, []).append((mv, mr))
        for register, _ in cat.REGISTERS:
            if register not in by_reg:
                continue
            out.append(f'<div class="reg">{register_heading(register)}</div><ul>')
            for mv, mr in by_reg[register]:
                out.append(row_link(q, path, mv, mr, meta=mv.name))
            out.append("</ul>")
    out.append("<ul>" + row_link(q, path, v, r, meta="this row") + "</ul>")
    out.append(links_section(ctx.get("links") or {}, group, q, path, ctx.get("resolve") or (lambda ref: None)))
    out.append("<h3>Possible namesakes, apart</h3>")
    out.append(same_name_section(ctx.get("same") or {}, q, path, ctx.get("same_words") or []).split("</h3>", 1)[1])
    out.append("</section>")
    return "\n".join(out)


# ── the lists ───────────────────────────────────────────────────────────────

def pins_pane(pins: list) -> str:
    out = ['<section class="pane"><div class="reg">pinned</div><h2>Pinned panes</h2>']
    if not pins:
        out.append('<p class="why">none yet</p>')
    out.append("<ul>")
    for p in pins:
        out.append(f'<li><a class="row" href="{esc(href(p.get("title") or "", [f"{p["view"]}:{p["key"]}"]))}">{esc(p["title"])}</a> '
                   f'<span class="meta">{esc(p["view"])}, {fmt(p.get("made_at"))}</span></li>')
    out.append("</ul></section>")
    return "\n".join(out)


def paths_pane(paths: list) -> str:
    out = ['<section class="pane"><div class="reg">saved</div><h2>Saved paths</h2>']
    if not paths:
        out.append('<p class="why">none yet</p>')
    out.append("<ul>")
    for p in paths:
        steps = [s for s in (p.get("path") or "").split("\n") if s]
        out.append(f'<li><a class="row" href="{esc(href(p.get("query") or "", steps))}">{esc(p["name"])}</a> '
                   f'<span class="meta">{len(steps)} panes from “{esc(p.get("query"))}”, {fmt(p.get("made_at"))}</span></li>')
    out.append("</ul></section>")
    return "\n".join(out)


def page(q: str, path: list, panes: list, message: str = "") -> str:
    save = ""
    if path:
        save = (f'<form class="inline" method="post" action="/save"><input type="hidden" name="q" value="{esc(q)}">'
                f'<input type="hidden" name="p" value="{esc("|".join(path))}">'
                f'<input name="name" placeholder="name this path" size="18"> <button>save path</button></form>')
    msg = f'<span class="note">{esc(message)}</span>' if message else ""
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>QueryNZ board</title>"
            f"<style>{CSS}</style></head><body><header><h1>QueryNZ board</h1>"
            f'<form method="get" action="/"><input type="search" name="q" value="{esc(q)}" placeholder="a name, an address, a number" autofocus> '
            f"<button>search</button></form>{save}<a href=\"/pinned\">pinned</a><a href=\"/saved\">saved paths</a>{msg}</header>"
            f"<main>{''.join(panes)}</main></body></html>")
