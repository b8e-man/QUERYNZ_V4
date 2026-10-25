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
NOTHING_TICKED = "tick a register, or search all"     # "search all" off and no register ticked: nothing is searched (ruling 81)
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
.pane.left{flex:0 0 19rem;max-width:19rem}
.pane.wide{flex:0 0 46rem;max-width:46rem}
.pane.graph{flex:0 0 64rem;max-width:64rem}
.pane input[type=search]{width:12rem;padding:.3rem .4rem}
ul.boxes{list-style:none;padding-left:0;font-size:13px}
label.all{display:block;margin:.5rem 0;font-weight:600}
.greyed{color:#aaa}
mark{background:#fde68a;color:inherit;padding:0}
article.hit{border-top:1px solid #eee;padding:.4rem 0}
.cite{font-size:12px;color:#555;margin-top:.2rem}
.view{margin-top:.5rem}
nav.tabs a{padding:.25rem .6rem;border:1px solid #ccc;border-bottom:none;border-radius:4px 4px 0 0;text-decoration:none}
nav.tabs a.on{background:#246;color:#fff;border-color:#246}
table.key td,table.key th{padding:.1rem .5rem;font-size:13px;text-align:left}
"""


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def encode_path(path: list) -> str:
    return urllib.parse.quote("|".join(path), safe="")


def href(q: str, path: list, boxes=None, tab: str = "/") -> str:
    """A page's address: the search tab's is `/?q=&p=` as before, so a saved
    path still opens; the check boxes (search.Boxes) follow as `all=` and
    `r=`. None writes neither, which opens as the first view (search all)."""
    return tab + "?" + urllib.parse.urlencode([("q", q), ("p", "|".join(path))] + (boxes.params() if boxes is not None else []))


def hidden_boxes(boxes) -> str:
    """The check boxes as hidden inputs, for the pin and save forms."""
    return "".join(f'<input type="hidden" name="{k}" value="{esc(x)}">' for k, x in (boxes.params() if boxes is not None else []))


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


def row_link(q: str, path: list, v: cat.View, r: dict, meta: str = "", boxes=None, words=()) -> str:
    t = mark(title_of(v, r), words)
    pix = f' <span class="warn">{PIXELS}</span>' if r.get("read_from") == "pixels" else ""
    m = f' <span class="meta">{esc(meta)}</span>' if meta else ""
    return f'<li><a class="row" href="{esc(href(q, path + [f"{v.name}:{r["key"]}"], boxes))}">{t}</a>{m}{pix}</li>'


def report_href(base: str, ref: str) -> str:
    """The subject report's stable address for a row, `<base>/report/<register>:<key>`;
    empty when no report server is named (`QV4_REPORT_URL`)."""
    if not base:
        return ""
    return f"{base.rstrip('/')}/report/{urllib.parse.quote(ref, safe=':/')}"


def report_link(ctx: dict) -> str:
    return f'<a href="{esc(ctx["report"])}">report from here</a>' if ctx.get("report") else ""


def register_heading(register: str) -> str:
    return esc(REGISTER_NAME.get(register, register))


# ── the search tab: the left pane and the results beside it (ruling 80) ──

_FOLD = str.maketrans(cat.MACRONS[0], cat.MACRONS[1])


def fold_chars(text: str) -> str:
    """The search's fold, one character for one character, so a place in the
    folded text is the same place in the text as filed."""
    out = []
    for c in text:
        f = c.lower().translate(_FOLD)
        out.append(f[0] if len(f) >= 1 else c)
    return "".join(out)


def mark(text, words) -> str:
    """`text` escaped, with every place a search word begins a word marked:
    the same rule and the same fold the search used, so "Maori" marks
    "Māori" and "Māori" marks "Maori"."""
    text = "" if text is None else str(text)
    if not words or not text:
        return esc(text)
    folded = fold_chars(text)
    spans = []
    for w in words:
        if not w:
            continue
        for m in re.finditer(r"(?<!\w)" + re.escape(w), folded):
            spans.append((m.start(), m.end()))
    if not spans:
        return esc(text)
    spans.sort()
    merged = [list(spans[0])]
    for s0, s1 in spans[1:]:
        if s0 <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], s1)
        else:
            merged.append([s0, s1])
    out, at = [], 0
    for s0, s1 in merged:
        out.append(esc(text[at:s0]) + "<mark>" + esc(text[s0:s1]) + "</mark>")
        at = s1
    out.append(esc(text[at:]))
    return "".join(out)


def fmt_marked(value, column: str, words) -> str:
    """fmt(), with the search words marked where the value is text."""
    if words and isinstance(value, str) and value:
        return mark(value, words)
    return fmt(value, column)


def register_boxes(held_regs: list, boxes) -> str:
    """"search all", then a check box per register in the catalogue's order;
    a register no lane has published is greyed, "not held", and cannot be
    checked. The two states are shown as they are (ruling 81): "search all"
    ticked leaves the register ticks as the user left them. The hidden
    `all=0` tells an unticked "search all" from an address that never had
    the form (search.boxes_of)."""
    out = ['<input type="hidden" name="all" value="0">',
           f'<label class="all"><input type="checkbox" name="all" value="1"{" checked" if boxes.all else ""}> search all</label>',
           '<ul class="boxes">']
    for register, plain in cat.REGISTERS:
        if register in held_regs:
            on = " checked" if register in boxes.ticked else ""
            out.append(f'<li><label><input type="checkbox" name="r" value="{esc(register)}"{on}> {esc(plain)}</label></li>')
        else:
            out.append(f'<li class="greyed"><label><input type="checkbox" disabled> {esc(plain)} <span class="meta">not held</span></label></li>')
    for register, plain in cat.NOT_HELD:
        out.append(f'<li class="greyed"><label><input type="checkbox" disabled> {esc(plain)} <span class="meta">not held</span></label></li>')
    out.append("</ul>")
    return "".join(out)


def left_pane(q: str, held_regs: list, boxes, action: str = "/", title: str = "Search the registers") -> str:
    return "\n".join([
        '<section class="pane left" id="search">', '<div class="reg">search</div>', f"<h2>{esc(title)}</h2>",
        f'<form method="get" action="{esc(action)}">',
        f'<input type="search" name="q" value="{esc(q)}" placeholder="a name, an address, a number" autofocus> <button>search</button>',
        '<p class="note">Every word must appear, macrons folded; a number is matched exactly. '
        "A suppressed name is never found by name. Search all searches every held register, whatever is ticked; "
        "untick it to search the registers ticked alone.</p>",
        register_boxes(held_regs, boxes), "<p><button>search</button></p></form></section>"])


def citation_line(v: cat.View, r: dict) -> str:
    parts = []
    doc = r.get("document")
    parts.append(f'document <code title="{esc(doc)}">{esc(doc[:12])}…</code>' if doc else f'document <span class="note">{NOT_STATED}</span>')
    for label, c in (("page", "page"), ("place", "place")):
        if r.get(c) not in (None, ""):
            parts.append(f"{label} {fmt(r.get(c))}")
    if r.get("read_from"):
        parts.append(f'<span class="warn">{PIXELS}</span>' if r["read_from"] == "pixels" else f"read from {esc(r['read_from'])}")
    for c in v.urls:
        if r.get(c):
            u = str(r[c])
            parts.append(f'<a href="{esc(u)}" rel="noopener">{esc(u[:60])}</a>')
    return '<div class="cite">' + " · ".join(parts) + "</div>"


def hit(q: str, v: cat.View, r: dict, words, boxes=None) -> str:
    """One matching row in the results pane: every field its View shows,
    its dates, its source's address and its citation, the words marked."""
    out = ['<article class="hit">',
           f'<div><a class="row" href="{esc(href(q, [f"{v.name}:{r["key"]}"], boxes))}"><strong>{mark(title_of(v, r), words)}</strong></a> '
           f'<span class="meta">{esc(v.name)}</span></div>']
    if is_suppressed(v, r):
        out.append(f'<div class="warn">{SUPPRESSED}: the row and its figures stay (hard limit 16)</div>')
    rows, blank = [], []
    for label, c in tuple(v.fields) + tuple(v.dates):
        if c not in r:
            continue
        x = shown(v, r, c)
        if x is None or x == "":
            blank.append(label)
            continue
        rows.append(f"<tr><th>{esc(label)}</th><td>{fmt_marked(x, c, words)}</td></tr>")
    if rows:
        out.append('<table class="f">' + "".join(rows) + "</table>")
    if blank:
        out.append(f'<div class="note">not stated: {esc(", ".join(blank))}</div>')
    out.append(citation_line(v, r))
    out.append("</article>")
    return "".join(out)


def results_pane(q: str, results: dict, held: set, regs: tuple, boxes, words=()) -> str:
    """The wider pane beside the left one: every matching row, grouped by
    register with the register's count, over `regs`, the registers searched
    (search.selection); `boxes` the check boxes every href carries."""
    out = ['<section class="pane wide" id="results">', '<div class="reg">results</div>']
    if not boxes.all and not regs:
        out.append(f"<h2>Results</h2><p class=\"why\">{NOTHING_TICKED}</p></section>")
        return "\n".join(out)
    if not q:
        out.append("<h2>Results</h2><p class=\"why\">Type a name, an address or a number in the search box.</p></section>")
        return "\n".join(out)
    out.append(f"<h2>{esc(q)}</h2>")
    out.append(f'<p class="note">searched: {"every held register" if boxes.all else esc(", ".join(REGISTER_NAME.get(x, x) for x in regs))}</p>')
    for register, plain in cat.REGISTERS:
        if register not in regs:
            continue
        hits = results.get(register, [])
        present = [v for v in cat.views_of(register) if v.name in held]
        total = sum(n for _, n, _ in hits)
        out.append(f'<h3>{esc(plain)} <span class="count">{total:,}</span></h3>')
        if not present:
            out.append('<p class="why">not held</p>')
            continue
        if not hits:
            out.append('<p class="why">none found</p>')
            continue
        for v, n, rows in hits:
            out.append(f'<div class="view"><strong>{esc(v.name)}</strong> <span class="count">{n:,}</span></div>')
            for r in rows:
                out.append(hit(q, v, r, words, boxes))
            if n > len(rows):
                out.append(f'<p class="note">and {n - len(rows):,} more in {esc(v.name)}; narrow the search</p>')
    out.append("</section>")
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


def links_section(links: dict, group: dict, q: str, path: list, resolve, boxes=None) -> str:
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
                    out.append(row_link(q, path, tv, tr, meta=f"rule {l['rule']}" + (f"; near because {l['reason']}" if l.get("reason") else ""), boxes=boxes))
                else:
                    out.append(f'<li>{esc(l["other"])} <span class="meta">row not found in the published views; rule {esc(l["rule"])}</span></li>')
                for d in l.get("decisions") or []:
                    out.append(f'<li class="meta">decision: {esc(d.get("verdict"))} by {esc(d.get("made_by"))}, {fmt(d.get("made_at"))}</li>')
            out.append("</ul>")
    return "\n".join(out)


def same_name_section(same: dict, q: str, path: list, words: list, boxes=None) -> str:
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
                out.append(row_link(q, path, v, r, boxes=boxes))
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
    boxes = ctx.get("boxes")
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
               + hidden_boxes(boxes) +
               f'<button>{"pinned" if ctx.get("pinned") else "pin"}</button></form>')
    if v.kind == "person" and not is_suppressed(v, r):
        out.append(f'<a href="{esc(href(q, path + [f"person:{v.name}:{r["key"]}"], boxes))}">person: the group and namesakes</a>')
    out.append(report_link(ctx))
    words = ctx.get("same_words") or []
    if words:
        out.append(f'<a href="{esc(href(" ".join(words), [], boxes))}">search this name afresh</a>')
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
            out.append("<ul>" + row_link(q, path, cat.BY_NAME[view], prow, boxes=boxes) + "</ul>")
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
            out.append(row_link(q, path, tv, cr, boxes=boxes))
        if total > len(rows):
            out.append(f'<li class="note">and {total - len(rows):,} more</li>')
        out.append("</ul>")
    out.append(links_section(ctx.get("links") or {}, ctx.get("group") or {}, q, path, ctx.get("resolve") or (lambda ref: None), boxes))
    if v.names:
        out.append(same_name_section(ctx.get("same") or {}, q, path, words, boxes))
    out.append(citation(v, r, ctx.get("doc_names") or []))
    out.append("</section>")
    return "\n".join(out)


# ── a person's pane ─────────────────────────────────────────────────────────

def person_pane(ctx: dict) -> str:
    """ctx: v, row, q, path, group ({'built', 'why', 'rows': [refs]}),
    members [(view, row)] resolved from the group, same (namesakes by name),
    same_words, links."""
    v, r, q, path = ctx["v"], ctx["row"], ctx["q"], ctx["path"]
    boxes = ctx.get("boxes")
    out = ['<section class="pane">', f'<div class="reg">person · from {register_heading(v.register)} · {esc(v.name)}</div>',
           f"<h2>{esc(title_of(v, r))}</h2>"]
    if ctx.get("report"):
        out.append(f'<div class="actions">{report_link(ctx)}</div>')
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
                out.append(row_link(q, path, mv, mr, meta=mv.name, boxes=boxes))
            out.append("</ul>")
    out.append("<ul>" + row_link(q, path, v, r, meta="this row", boxes=boxes) + "</ul>")
    out.append(links_section(ctx.get("links") or {}, group, q, path, ctx.get("resolve") or (lambda ref: None), boxes))
    out.append("<h3>Possible namesakes, apart</h3>")
    out.append(same_name_section(ctx.get("same") or {}, q, path, ctx.get("same_words") or [], boxes).split("</h3>", 1)[1])
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


def page(q: str, path: list, panes: list, message: str = "", boxes=None, tab: str = "search") -> str:
    """The page: two tabs, search (`/`, as before) and graph (`/graph`), each
    an href carrying the term and the registers checked (ruling 80)."""
    save = ""
    if path:
        save = (f'<form class="inline" method="post" action="/save"><input type="hidden" name="q" value="{esc(q)}">'
                f'<input type="hidden" name="p" value="{esc("|".join(path))}">'
                + hidden_boxes(boxes) +
                f'<input name="name" placeholder="name this path" size="18"> <button>save path</button></form>')
    msg = f'<span class="note">{esc(message)}</span>' if message else ""
    tabs = (f'<nav class="tabs"><a class="{"on" if tab == "search" else ""}" href="{esc(href(q, [] if tab != "search" else path, boxes))}">search</a> '
            f'<a class="{"on" if tab == "graph" else ""}" href="{esc(href(q, [], boxes, "/graph"))}">graph</a></nav>')
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>QueryNZ board</title>"
            f"<style>{CSS}</style></head><body><header><h1>QueryNZ board</h1>{tabs}"
            f"{save}<a href=\"/pinned\">pinned</a><a href=\"/saved\">saved paths</a>{msg}</header>"
            f"<main>{''.join(panes)}</main></body></html>")
