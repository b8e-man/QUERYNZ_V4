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
import json
import re
import urllib.parse

from products.board import catalogue as cat
from products.board import document
from products.board.search import FIELD_LABEL, FIELDS, MODES, TABS, field_words, words_of
from products.board.search import add_alternative as search_add, drop_alternative as search_drop
from products.board.search import FIRST as FIRST_BOXES, TABLE_MAX as TABLE_MAX_N, TABLE_PAGE as TABLE_PAGE_N

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

#: night mode (ruling 86 (1)): one dark scheme, no second theme and no toggle. Every text colour reads at 4.5:1 or
#: more on every background the sheet sets (tests/test_night.py and the check read the pairs from this string);
#: the graph's picture is styled here too, so its labels and its surface are held by the same test
CSS = """
:root{color-scheme:dark}
body{margin:0;font:14px/1.4 system-ui,sans-serif;color:#e8eaed;background:#0e1014}
header{display:flex;gap:1rem;align-items:center;padding:.5rem 1rem;background:#161a20;border-bottom:1px solid #3a404c;position:sticky;top:0;z-index:2}
header h1{font-size:15px;margin:0 1rem 0 0;font-weight:600}
header input[type=search]{width:28rem;padding:.35rem .5rem;font-size:14px}
input,button{color:#e8eaed;background:#232833;border:1px solid #5a6270;border-radius:3px}
input::placeholder{color:#aab1bc}
main{display:flex;gap:.75rem;padding:.75rem;overflow-x:auto;align-items:flex-start;min-height:calc(100vh - 3.5rem)}
.pane{flex:0 0 26rem;max-width:26rem;background:#161a20;border:1px solid #3a404c;border-radius:4px;padding:.75rem;max-height:calc(100vh - 5rem);overflow-y:auto}
.pane.pinned{border:2px solid #e0b84d}
.pane h2{font-size:15px;margin:.25rem 0}
.pane h3{font-size:12px;margin:1rem 0 .25rem;text-transform:uppercase;letter-spacing:.04em;color:#aab1bc;border-bottom:1px solid #3a404c}
.reg{font-size:11px;color:#aab1bc;text-transform:uppercase;letter-spacing:.04em}
.note,.why{font-size:12px;color:#aab1bc;font-style:italic}
.warn{color:#ffb26b;font-weight:600}
.lineage{color:#80f040;font-weight:600}
table.f{border-collapse:collapse;width:100%;font-size:13px}
table.f th{text-align:left;font-weight:normal;color:#aab1bc;vertical-align:top;padding:.1rem .5rem .1rem 0;width:40%}
table.f td{padding:.1rem 0;vertical-align:top;word-break:break-word}
div.text{white-space:pre-wrap;word-break:break-word;max-width:60rem;line-height:1.45}
ul{margin:.25rem 0;padding-left:1.1rem}
li{margin:.1rem 0}
li .meta,.meta{color:#aab1bc;font-size:12px}
.count{color:#aab1bc;font-weight:normal}
a{color:#8cb8ff}
a:visited{color:#c3b5ff}
a.row{text-decoration:none}
a.row:hover{text-decoration:underline}
form.inline{display:inline}
button{font:inherit;font-size:12px;padding:.15rem .5rem}
.actions{display:flex;gap:.5rem;margin:.5rem 0;flex-wrap:wrap}
code{font-size:12px;word-break:break-all;color:#e8eaed}
.pane.left{flex:0 0 19rem;max-width:19rem}
.pane.wide{flex:0 0 46rem;max-width:46rem}
.pane.graph{flex:0 0 64rem;max-width:64rem}
.pane.graph .picture{overflow-x:auto}
.pane input[type=search]{width:12rem;padding:.3rem .4rem}
ul.boxes{list-style:none;padding-left:0;font-size:13px}
label.all{display:block;margin:.5rem 0;font-weight:600}
.greyed{color:#aab1bc;font-style:italic}
mark{background:#4d3b00;color:#f3c969;padding:0}
article.hit{border-top:1px solid #3a404c;padding:.4rem 0}
.cite{font-size:12px;color:#aab1bc;margin-top:.2rem}
.view{margin-top:.5rem}
nav.tabs a{padding:.25rem .6rem;border:1px solid #5a6270;border-bottom:none;border-radius:4px 4px 0 0;text-decoration:none}
nav.tabs a.on{background:#1d3a5f;color:#e8eaed;border-color:#8cb8ff}
div.edges h4{font-size:13px;margin:.7rem 0 .1rem}
ul.addends{font-size:12px;color:#aab1bc}
table.key td,table.key th{padding:.1rem .5rem;font-size:13px;text-align:left}
table.uc{border-collapse:collapse;width:100%;font-size:13px}
table.uc th,table.uc td{text-align:left;vertical-align:top;padding:.3rem .5rem;border-top:1px solid #3a404c}
details.fields{margin:.5rem 0}
details.fields label{display:block;margin:.2rem 0;font-size:13px}
details.fields input{width:11rem;padding:.2rem .3rem;float:right}
details.fields label::after{content:"";display:block;clear:both}
details.fields p.modes label{display:inline;margin-right:.75rem}
details.fields p.modes label::after{display:none}
details.fields p.modes input{width:auto;float:none}
details.near{margin-top:1rem;border-top:2px solid #3a404c;padding-top:.5rem}
details.near summary{font-weight:600;cursor:pointer}
.nearwhy{font-size:12px;color:#ffb26b}
.pane.uses{flex:0 0 78rem;max-width:78rem}
.pane.table{flex:0 0 72rem;max-width:72rem}
table.grid{border-collapse:collapse;font-size:12px;table-layout:fixed;width:100%}
table.grid th,table.grid td{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:.1rem .4rem;border-top:1px solid #3a404c;text-align:left}
table.grid th{color:#aab1bc;font-weight:normal}
header span.db{margin-left:auto;font-size:12px;font-variant-numeric:tabular-nums;cursor:help}
svg rect.bg{fill:#161a20}
svg text{font:11px system-ui,sans-serif;fill:#e8eaed;paint-order:stroke;stroke:#161a20;stroke-width:3px}
svg text.reg{font-size:9px;fill:#aab1bc}
svg text.words{font-size:9px;fill:#e8eaed;paint-order:stroke;stroke:#161a20;stroke-width:3px}
svg path.edge{fill:none;stroke-width:2}
svg circle.matched{fill:#f3c969;stroke:#e8eaed;stroke-width:2.5}
svg circle.other{fill:#0e1014;stroke:#aab1bc;stroke-width:1.5}
svg a:hover text{text-decoration:underline}
.canvas{display:none;position:relative}
.canvas.on{display:block}
.canvas .tools{margin:.25rem 0 .4rem}
div.cy{height:66vh;min-height:26rem;color:#e8eaed;background:#161a20;outline-color:#8cb8ff;border:1px solid #3a404c;border-radius:4px}
.legend{font-size:12px;color:#aab1bc;margin:0 0 .3rem}
.legend span.swatch{display:inline-block;width:10px;height:10px;border-radius:50%;margin:0 .3rem 0 .8rem;vertical-align:middle}
div.tip{position:absolute;z-index:3;max-width:250px;pointer-events:none;font-size:12px;color:#e8eaed;background:#232833;border:1px solid #5a6270;border-radius:3px;padding:.3rem .45rem}
div.ftabs{margin-top:.5rem}
div.ftabs input.ft{position:absolute;opacity:0;width:1px;height:1px}
div.ftabs label{display:inline-block;margin:0 .2rem .3rem 0;padding:.2rem .55rem;border:1px solid #5a6270;border-radius:4px;cursor:pointer;font-size:13px}
div.ftabs input.ft:checked+label{background:#1d3a5f;color:#e8eaed;border-color:#8cb8ff}
div.ftabs input.ft:focus-visible+label{outline:2px solid #8cb8ff}
div.ftab{display:none;border-top:1px solid #3a404c}
#ft-first:checked~#ftab-first{display:block}
#ft-middle:checked~#ftab-middle{display:block}
#ft-last:checked~#ftab-last{display:block}
#ft-address:checked~#ftab-address{display:block}
#ft-org:checked~#ftab-org{display:block}
#ft-year:checked~#ftab-year{display:block}
#ft-number:checked~#ftab-number{display:block}
#ft-other:checked~#ftab-other{display:block}
details.regs{border-top:1px solid #3a404c;padding:.3rem 0}
details.regs summary{cursor:pointer;font-size:13px;font-weight:600}
article.hit[data-graph]{cursor:pointer}
article.hit.on{background:#1d3a5f}
article.entity{border-left:3px solid #8cb8ff;padding-left:.5rem}
div.duo{display:flex;gap:.75rem;align-items:flex-start;flex:0 0 auto}
.pane.side{display:none;flex:0 0 40rem;max-width:40rem;position:sticky;top:3.75rem}
.pane.side.on{display:block}
.pane.side div.cy{height:60vh;min-height:20rem}
@media (max-width:75rem){div.duo{flex-direction:column}.pane.side{position:static;flex-basis:auto;width:46rem;max-width:calc(100vw - 2rem)}}
"""
TEXT_FLOOR = 4.5         # the common accessibility floor for text (WCAG 2 AA)
EDGE_FLOOR = 3.0         # for a line or a mark that is not text (WCAG 2 non-text contrast)
EDGE_APART = 15.0        # every two edge colours of the key at least this far apart in OKLab (x100), the normal-vision floor


def oklab(hexcolour: str) -> tuple:
    """An sRGB colour in OKLab (Björn Ottosson's matrices)."""
    h = hexcolour.lstrip("#")
    lin = [(lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]
    r, g, b = lin
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def apart(a: str, b: str) -> float:
    """How far apart two colours are, OKLab distance x100."""
    return 100 * sum((x - y) ** 2 for x, y in zip(oklab(a), oklab(b))) ** 0.5


def luminance(hexcolour: str) -> float:
    """The relative luminance of an sRGB colour, `#rgb` or `#rrggbb` (WCAG 2)."""
    h = hexcolour.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def over(colour: str, surface: str, opacity: float) -> str:
    """`colour` laid at `opacity` over `surface`, as the canvas fills a compound node (a lineage frame)."""
    c, b = (colour.lstrip("#"), surface.lstrip("#"))
    return "#" + "".join(f"{round(int(c[i:i + 2], 16) * opacity + int(b[i:i + 2], 16) * (1 - opacity)):02x}" for i in (0, 2, 4))


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


_HEX = r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\b"


def sheet_colours(css: str = None) -> tuple:
    """(text colours, backgrounds), read from the stylesheet: text is every
    `color`, and the `fill` of an SVG text rule; a background is every
    `background`, and the `fill` of the picture's surface (a rect). Every
    text colour is held against every background, so a pair that can meet
    on the page is among them."""
    text, back = set(), set()
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", CSS if css is None else css):
        for prop, val in re.findall(r"(?:^|;)\s*([a-z-]+)\s*:\s*([^;]+)", body):
            found = re.findall(_HEX, val)
            if not found:
                continue
            if prop == "color" or (prop == "fill" and "text" in sel):
                text.update(found)
            elif prop in ("background", "background-color") or (prop == "fill" and "rect" in sel):
                back.update(found)
    return text, back


def contrast_problems(css: str = None, edges=None, nodes=None) -> list:
    """Every text colour on every background at TEXT_FLOOR or more; every
    edge colour of the key (catalogue.EDGE_KINDS) and every register's node
    colour (catalogue.REGISTER_COLOURS, ruling 100) at EDGE_FLOOR or more on
    the picture's surfaces (the SVG's rect and the canvas's box; the key's
    swatches sit on the pane, the same colour), and every two edge colours,
    and every two node colours (a family of registers shares one), EDGE_APART or
    more apart; empty when the sheet holds."""
    text, back = sheet_colours(css)
    out = []
    if not text or not back:
        out.append("the stylesheet sets no text colour or no background")
    for t in sorted(text):
        for b in sorted(back):
            if contrast(t, b) < TEXT_FLOOR:
                out.append(f"text {t} on {b}: {contrast(t, b):.2f}:1, under {TEXT_FLOOR}:1")
    surfaces = {c for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", CSS if css is None else css) if "rect" in sel
                for c in re.findall(r"fill\s*:\s*(" + _HEX + ")", body)}
    surfaces |= {c for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", CSS if css is None else css) if "div.cy" in sel
                 for c in re.findall(r"(?:^|;)\s*background(?:-color)?\s*:\s*(" + _HEX + ")", body)}
    if not surfaces:
        out.append("the stylesheet sets no surface for the picture")
    for kind, colour, _ in (cat.EDGE_KINDS if edges is None else edges):
        for b in sorted(surfaces):
            if contrast(colour, b) < EDGE_FLOOR:
                out.append(f"the {kind} edge {colour} on {b}: {contrast(colour, b):.2f}:1, under {EDGE_FLOOR}:1")
    colours = sorted({colour for _, colour, _ in (cat.EDGE_KINDS if edges is None else edges)})
    for i, a in enumerate(colours):
        for b in colours[i + 1:]:
            if apart(a, b) < EDGE_APART:
                out.append(f"the edge colours {a} and {b} are {apart(a, b):.1f} apart, under {EDGE_APART}")
    marks = list(cat.REGISTER_COLOURS if nodes is None else nodes)
    for register, colour in marks:
        for b in sorted(surfaces):
            if contrast(colour, b) < EDGE_FLOOR:
                out.append(f"the {register} node {colour} on {b}: {contrast(colour, b):.2f}:1, under {EDGE_FLOOR}:1")
    if nodes is None:
        out += [f"the register {r} has no node colour" for r, _ in cat.REGISTERS if r not in cat.REGISTER_COLOUR]
    fills = sorted({colour for _, colour in marks})         # a family shares one colour, as two same-person kinds share a hue
    for i, a in enumerate(fills):
        for b in fills[i + 1:]:
            if apart(a, b) < EDGE_APART:
                out.append(f"the node colours {a} and {b} are {apart(a, b):.1f} apart, under {EDGE_APART}")
    return out


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


def _title_value(x) -> str:
    return x.strftime("%-d %B %Y") if isinstance(x, dt.date) else str(x)


def title_of(v: cat.View, r: dict) -> str:
    if v.title_format:
        cols = re.findall(r"\{(\w+)\}", v.title_format)
        values = {c: shown(v, r, c) for c in cols}
        if all(x not in (None, "") for x in values.values()):
            return v.title_format.format(**{c: _title_value(x) for c, x in values.items()})
    parts = []
    for c in v.title:
        x = shown(v, r, c)
        if x not in (None, ""):
            parts.append(_title_value(x))
    return " · ".join(parts) or f"({v.name} {r.get('key', '')})"


WITHDRAWN = "withdrawn by the source"


def is_withdrawn(v: cat.View, r: dict) -> bool:
    """A row the source no longer serves (its `served` column false): shown struck through."""
    return bool(v.served) and r.get(v.served) is False


def struck(v: cat.View, r: dict, html: str) -> str:
    """A title's html, struck through with "withdrawn by the source" where the row is withdrawn."""
    return f'<s>{html}</s> <span class="warn">{WITHDRAWN}</span>' if is_withdrawn(v, r) else html


def flag_notes(v: cat.View, r: dict, column: str) -> str:
    """The small notes a column's cell carries where its flags are set (catalogue View.flags, ruling 102)."""
    return "".join(f' <span class="note">({esc(words)})</span>' for c, flag, words in v.flags if c == column and r.get(flag))


def says_of(v: cat.View, r: dict) -> list:
    """The lines a row carries (catalogue.Say) where its columns hold them,
    the words filled from the row as a title fills them."""
    return [say.words.format(**{c: NOT_STATED if r.get(c) in (None, "") else _title_value(r.get(c)) for c in re.findall(r"\{(\w+)\}", say.words)})
            for say in v.says if say.holds(r)]


def row_link(q: str, path: list, v: cat.View, r: dict, meta: str = "", boxes=None, words=()) -> str:
    t = mark(title_of(v, r), words)
    pix = f' <span class="warn">{PIXELS}</span>' if r.get("read_from") == "pixels" else ""
    m = f' <span class="meta">{esc(meta)}</span>' if meta else ""
    a = f'<a class="row" href="{esc(href(q, path + [f"{v.name}:{r["key"]}"], boxes))}">{t}</a>'
    return f'<li>{struck(v, r, a)}{m}{pix}</li>'


NOT_HELD_ROW = "(row not held)"


def far_cell(v: cat.View, r: dict, column: str, far, q: str, path: list, boxes=None, words=()):
    """A column naming another view's row (ruling 92 (2)): the far row's
    title as a link to its pane, the key in the hover title; the key with
    "(row not held)" where the published view lacks it. None when the column
    names no row, or `far` (search.far_rows) was not resolved for the page."""
    p = cat.pointers(v).get(column)
    x = r.get(column)
    if far is None or not p or x in (None, ""):
        return None
    fv, fc = p
    fr = far.get((fv, fc, str(x)))
    if fr is None:
        return f'<code>{esc(x)}</code> <span class="note">{NOT_HELD_ROW}</span>'
    tv = cat.BY_NAME[fv]
    return (f'<a class="row" href="{esc(href(q, path + [f"{fv}:{fr["key"]}"], boxes))}" title="{esc(x)}">'
            f'{mark(title_of(tv, fr), words)}</a>')


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


def register_boxes(held_regs: list, boxes, q: str = None) -> str:
    """"search all", then a check box per register in the catalogue's order;
    a register no lane has published is greyed, "not held", and cannot be
    checked. The two states are shown as they are (ruling 81): "search all"
    ticked leaves the register ticks as the user left them. The hidden
    `all=0` tells an unticked "search all" from an address that never had
    the form (search.boxes_of). With `q` (the search tab), each held
    register's name is a link opening its table (ruling 92 (5))."""
    out = ['<input type="hidden" name="all" value="0">',
           f'<label class="all"><input type="checkbox" name="all" value="1"{" checked" if boxes.all else ""}> search all</label>',
           '<ul class="boxes">']
    for register, plain in cat.REGISTERS:
        if register in held_regs:
            on = " checked" if register in boxes.ticked else ""
            if q is None:
                out.append(f'<li><label><input type="checkbox" name="r" value="{esc(register)}"{on}> {esc(plain)}</label></li>')
            else:
                out.append(f'<li><label><input type="checkbox" name="r" value="{esc(register)}"{on}></label> '
                           f'<a class="row" href="{esc(table_href(q, boxes, register))}" title="open the register as a table">{esc(plain)}</a></li>')
        else:
            out.append(f'<li class="greyed"><label><input type="checkbox" disabled> {esc(plain)} <span class="meta">not held</span></label></li>')
    for register, plain in cat.NOT_HELD:
        out.append(f'<li class="greyed"><label><input type="checkbox" disabled> {esc(plain)} <span class="meta">not held</span></label></li>')
    out.append("</ul>")
    return "".join(out)


def field_boxes(boxes) -> str:
    """The expanded search (ruling 82): a details element, closed until
    clicked or until a field is filled, holding the six fields."""
    asked = boxes.asked() if boxes is not None else {}
    out = [f'<details class="fields"{" open" if asked else ""}><summary>narrow by field</summary>']
    for f, label in FIELDS:
        extra = ' inputmode="numeric" maxlength="4"' if f == "year" else ""
        out.append(f'<label>{esc(label)} <input name="{f}" value="{esc(asked.get(f, ""))}"{extra}></label>')
    mode = getattr(boxes, "mode", "all") if boxes is not None else "all"
    out.append('<p class="modes">' + " ".join(
        f'<label><input type="radio" name="mode" value="{m}"{" checked" if m == mode else ""}> {esc(label)}</label>'
        for m, label in MODES) + "</p>")
    out.append('<p class="note">Each field is matched as whole words in the columns that hold it: a surname or given-names '
               "column where a register prints one, else the words of the name in their places; organisation, a company, "
               "party, charity or society name; year, the year or the year of a date; address, the registered addresses "
               "organisations publish, never a person's home address (no published table holds one). With all fields, "
               "every filled field must match, and a register with no column for one is not searched; with any field, a "
               "row matches on any one of them, and each result says which. The box above must match either way.</p></details>")
    return "".join(out)


def removed_box(boxes) -> str:
    """Ruling 93: "show removed companies", under the register ticks,
    unticked on the first view; an unticked box sends nothing, so the
    address carries `removed=1` only when it is ticked."""
    on = " checked" if getattr(boxes, "removed", False) else ""
    return (f'<p class="removed"><label><input type="checkbox" name="removed" value="1"{on}> show removed companies</label> '
            f'<span class="note">a company whose status reads {esc(", ".join(sorted(cat.REMOVED_STATUS)))}; '
            "a row opened by its own link opens whatever its status</span></p>")


def hidden_line(n: int) -> str:
    """The count a search or table left out as removed (ruling 93); "" for none."""
    return f' <span class="note">{n:,} removed hidden</span>' if n else ""


def left_pane(q: str, held_regs: list, boxes, action: str = "/", title: str = "Search the registers") -> str:
    return "\n".join([
        '<section class="pane left" id="search">', '<div class="reg">search</div>', f"<h2>{esc(title)}</h2>",
        f'<form method="get" action="{esc(action)}">',
        f'<input type="search" name="q" value="{esc(q)}" placeholder="a name, an address, a number" autofocus> <button>search</button>'
        + (' <button name="near" value="1" title="given names near the one typed, with the same surname: nicknames, '
           'spellings, common forms">near names</button>' if action == "/" else ""),
        field_boxes(boxes),
        '<p class="note">Every word must appear, macrons folded; a number is matched exactly. '
        "A suppressed name is never found by name. Search all searches every held register, whatever is ticked; "
        "untick it to search the registers ticked alone.</p>",
        register_boxes(held_regs, boxes, q if action == "/" else None),
        removed_box(boxes),
        (f'<input type="hidden" name="t" value="{esc(boxes.table)}"><input type="hidden" name="o" value="{boxes.upto}">'
         if action == "/" and boxes is not None and boxes.table else ""),
        "<p><button>search</button></p></form></section>"])


NEAR_NAMES_NOTE = ("A variant is a candidate you choose to add to the search, never a link the board made: the board makes "
                   "no link by looking (plan 4.9), and two names sharing a surname are not one person. The forms come from a "
                   "table of common nicknames, spellings and Māori forms (given_names.py), and from the given names filed "
                   "with this surname that share the first three letters or are one letter apart. Each count is the rows in "
                   "the registers searched that file that given name with the surname. Adding one searches either name in "
                   "that place.")


def near_names_pane(q: str, data: dict, boxes) -> str:
    """The near-names pane (ruling 92 (4)): for each given name typed, its
    variants filed with the same surname words, each with its count and a
    link that adds it to the search as an alternative in that place
    (search.add_alternative: "garry|gareth"), the pane kept open (`near=1`)."""
    out = ['<section class="pane" id="near-names">', '<div class="reg">near names</div>', "<h2>Near names</h2>",
           f'<p class="note">{esc(NEAR_NAMES_NOTE)}</p>']
    if data.get("why"):
        out.append(f'<p class="why">{esc(data["why"])}</p></section>')
        return "\n".join(out)
    asked = boxes.asked() if boxes is not None else {}

    def with_term(change) -> str:
        if data.get("from_fields"):
            f = change[0]
            fields = tuple((k, change[1](x) if k == f else x) for k, x in boxes.fields)
            return href(q, [], boxes._replace(fields=fields)) + "&near=1"
        return href(change[1](q), [], boxes) + "&near=1"

    sur = " ".join(data.get("surname") or [])
    for g in data.get("given") or []:
        field = g.get("field") or ""
        out.append(f'<h3>{esc(g["typed"])} {esc(sur)} <span class="count">{g["count"]:,} rows</span></h3>')
        if g["chosen"]:
            items = [f'{esc(c)} <a href="{esc(with_term((field, lambda t, c=c: search_drop(t, c))))}">remove</a>'
                     for c in g["chosen"]]
            out.append(f'<p>in the search as alternatives: {", ".join(items)}</p>')
        if not g["variants"]:
            out.append(f'<p class="why">none found: no other given name near {esc(g["typed"])} is filed with {esc(sur)}</p>')
            continue
        out.append("<ul>")
        for w, n, why in g["variants"]:
            if w in g["chosen"]:
                link = f"<strong>{esc(w)}</strong> <span class=\"meta\">in the search</span>"
            else:
                link = f'<a href="{esc(with_term((field, lambda t, w=w, typed=g["typed"]: search_add(t, typed, w))))}">{esc(w)}</a>'
            out.append(f'<li>{link} <span class="count">{n:,}</span> <span class="meta">{esc(why)}</span></li>')
        out.append("</ul>")
    out.append("</section>")
    return "\n".join(out)


# ── a register as a table (ruling 92 (5)) ─────────────────────────────────

CELL_CHARS = 40      # a cell's text is cut here, the whole value in its hover title


def table_href(q: str, boxes, register: str = "", view: str = "", upto: int = 0) -> str:
    """The search tab with a register's table open: its main view (the first
    of its views the catalogue lists; the server takes the first published
    one, main_view, where it is not; the chooser offers the rest), or
    `view`, from row 1 to upto + 100."""
    view = view or cat.main_view_of(register)
    b = (boxes or FIRST_BOXES)._replace(table=view, upto=upto)
    return href(q, [], b) + "#table"


def main_view(register: str, held: set):
    """The register's main view where it is published, else its first published view."""
    first = cat.BY_NAME[cat.main_view_of(register)]
    return first if first.name in held else next((v for v in cat.views_of(register) if v.name in held), None)


def one_line(text: str) -> tuple:
    """(the cell's text cut to CELL_CHARS, escaped, the whole value for its title, escaped): one line, always."""
    t = " ".join(str(text).split())
    return esc(t if len(t) <= CELL_CHARS else t[:CELL_CHARS - 1] + "…"), esc(t)


def plain(value, column: str = "") -> str:
    """A value as fmt() shows it, as plain text."""
    return html.unescape(re.sub(r"<[^>]+>", "", fmt(value, column)))


def table_pane(q: str, v: cat.View, total: int, rows: list, boxes, held: set = (), far: dict = None, hidden: int = 0) -> str:
    """One register's view as a table (ruling 92 (5)): the count of all its
    rows at the top, then the first rows in the view's default order, one
    line each, the title and the catalogue's fields in fixed columns, cut
    with the whole value on hover; the title opens the row's pane; a key
    column shows the far row's title (ruling 92 (2)); "more" appends the next
    TABLE_PAGE (its href carries the offset); a chooser for the register's
    other views. A suppressed name and withheld text as panes.shown();
    `hidden`, the removed companies left out (ruling 93), on the count line."""
    out = ['<section class="pane table" id="table">', f'<div class="reg">{register_heading(v.register)} · table</div>',
           f'<h2>{register_heading(v.register)} <span class="count">{total:,} rows in {esc(v.name)}</span>{hidden_line(hidden)}</h2>']
    others = [w for w in cat.views_of(v.register) if w.name in held]
    if len(others) > 1:
        out.append('<p class="note">views: ' + " · ".join(
            f"<strong>{esc(w.name)}</strong>" if w.name == v.name else f'<a href="{esc(table_href(q, boxes, view=w.name))}">{esc(w.name)}</a>'
            for w in others) + "</p>")
    out.append(f'<p class="note">rows 1 to {len(rows):,} of {total:,}, in the view order ({esc(v.default_order)}); one line each, '
               "the whole value on hover; a name the register suppresses reads " + SUPPRESSED + ".</p>")
    cols = [("title", "")] + [(label, c) for label, c in v.fields]
    out.append('<table class="grid"><tr>' + "".join(f"<th>{esc(label)}</th>" for label, _ in cols) + "</tr>")
    for r in rows:
        cells = []
        t, full = one_line(title_of(v, r))
        a = f'<a class="row" href="{esc(href(q, [f"{v.name}:{r["key"]}"], boxes))}">{t}</a>'
        cells.append(f'<td title="{full}">{struck(v, r, a)}</td>')
        for _, c in cols[1:]:
            p = cat.pointers(v).get(c)
            x = r.get(c)
            if far is not None and p and x not in (None, ""):
                fr = far.get((p[0], p[1], str(x)))
                if fr is None:
                    t, _ = one_line(f"{x} {NOT_HELD_ROW}")
                    cells.append(f'<td title="{esc(x)}">{t}</td>')
                else:
                    t, _ = one_line(title_of(cat.BY_NAME[p[0]], fr))
                    cells.append(f'<td title="{esc(x)}"><a class="row" href="{esc(href(q, [f"{p[0]}:{fr["key"]}"], boxes))}">{t}</a></td>')
                continue
            t, full = one_line(plain(shown(v, r, c), c))
            cells.append(f'<td title="{full}">{t}</td>')
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</table>")
    if len(rows) < total:
        upto = boxes.upto + TABLE_PAGE_N
        if upto < TABLE_MAX_N:
            out.append(f'<p><a href="{esc(table_href(q, boxes, view=v.name, upto=upto))}">more: the next {TABLE_PAGE_N}</a></p>')
        else:
            out.append(f'<p class="note">the table shows {TABLE_MAX_N:,} rows at most; search to find the rest</p>')
    out.append("</section>")
    return "\n".join(out)


def narrowed_line(boxes) -> str:
    """Which fields narrowed the search, as the results pane says it."""
    asked = boxes.asked() if boxes is not None else {}
    if not asked:
        return ""
    parts = [f"{esc(label)} “{esc(asked[f])}”" for f, label in FIELDS if f in asked]
    how = " (any field may match)" if getattr(boxes, "mode", "all") == "any" and len(parts) > 1 else ""
    return f'<p class="note">narrowed by: {", ".join(parts)}{how}</p>'


def search_words(q: str, boxes) -> list:
    """The words marked in the results: the box's, then every filled text field's."""
    asked = boxes.asked() if boxes is not None else {}
    words = list(words_of(q))
    for f, _ in FIELDS:
        if f != "year" and asked.get(f):
            words += [w for w in field_words(asked[f]) if w not in words]
    return [x for w in words for x in w.split("|") if x]      # a word's alternatives (ruling 92 (4)) are each marked


def source_link(v: cat.View, r: dict, docs: dict = None) -> str:
    """First in every citation (ruling 86 (4)): "source", the captured
    document on the board (`/doc/<sha256>`, a PDF at its page), whatever
    its source (ruling 88); "document not held here" where the store has no
    copy, the reason where it is withdrawn. A suppressed row or withheld text
    offers no document: it would print what the row hides (hard limit 16)."""
    doc = r.get("document")
    st = (docs or {}).get(doc) if doc else None
    if not st or st["state"] == document.ABSENT:
        why = st["why"] if st else document.NOT_HELD
        return f'<span class="note">{esc(why)}</span>'
    if is_suppressed(v, r) or is_withheld(v, r):
        return '<span class="note">source not opened: the row hides a name or a text the document prints</span>'
    return f'<a class="source" href="{esc(document.href(doc, st["kind"], r.get("page")))}">source</a>'


def citation_line(v: cat.View, r: dict, docs: dict = None) -> str:
    parts = [source_link(v, r, docs)]
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
    if v.no_url and not any(r.get(c) for c in v.urls):
        parts.append(f'<span class="note">{esc(v.no_url)}</span>')
    for label, c in v.cite:
        if r.get(c) not in (None, ""):
            parts.append(f"{esc(label)} <code>{esc(r[c])}</code>")
    return '<div class="cite">' + " · ".join(parts) + "</div>"


def hit(q: str, v: cat.View, r: dict, words, boxes=None, why: str = "", docs: dict = None, far: dict = None) -> str:
    """One matching row in the results pane: every field its View shows,
    its dates, its source's address and its citation, the words marked;
    `why`, for a near match, says which kind it is (ruling 83); `far`, the
    rows its key columns name (search.far_rows, ruling 92 (2))."""
    link = f'<a class="row" href="{esc(href(q, [f"{v.name}:{r["key"]}"], boxes))}"><strong>{mark(title_of(v, r), words)}</strong></a>'
    out = [f'<article class="hit" data-graph="{esc(graph_href(f"{v.name}:{r["key"]}", boxes))}">'] + (
           [f'<div class="nearwhy">near: {esc(why)}</div>'] if why else []) + [
           f'<div>{struck(v, r, link)} '
           f'<span class="meta">{esc(v.name)}</span>' + (
               f' · <span class="lineage" title="{esc("a related company: " + str(r["_related"]) + ", never one entity (ruling 106 (2))")}">'
               "related</span>" if r.get("_related") else "") + "</div>"]
    if is_suppressed(v, r):
        out.append(f'<div class="warn">{SUPPRESSED}: the row and its figures stay (hard limit 16)</div>')
    out += [f'<div class="note">{esc(line)}</div>' for line in says_of(v, r)]
    matched = [FIELD_LABEL[k[len("_matched_"):]] for k in r if k.startswith("_matched_") and r[k]]
    if matched:
        out.append(f'<div class="nearwhy">matched: {esc(", ".join(matched))}</div>')     # ruling 92 (6), any field
    rows, blank = [], []
    for label, c in tuple(v.fields) + tuple(v.dates):
        if c not in r:
            continue
        x = shown(v, r, c)
        if x is None or x == "":
            blank.append(label)
            continue
        cell = far_cell(v, r, c, far, q, [], boxes, words)
        rows.append(f"<tr><th>{esc(label)}</th><td>{cell if cell is not None else fmt_marked(x, c, words)}{flag_notes(v, r, c)}</td></tr>")
    if rows:
        out.append('<table class="f">' + "".join(rows) + "</table>")
    if blank:
        out.append(f'<div class="note">not stated: {esc(", ".join(blank))}</div>')
    out.append(citation_line(v, r, docs))
    out.append("</article>")
    return "".join(out)


def graph_href(nid: str, boxes=None) -> str:
    """/graph.json centred on one row, the check boxes carried and with them the state (ruling 105's `g=entities`):
    a node's one hop on the graph tab, and the graph a result opens beside the results (ruling 108 (4))."""
    return "/graph.json?" + urllib.parse.urlencode([("c", nid)] + (boxes.params() if boxes is not None else []))


RESULTS_ENTITY_NOTE = ("The groups the links lane built (pub.groups) that the matching rows fall in, and those whose rows "
                       "carry the name searched (pub.names), each with its count of rows and registers; the board makes no "
                       "link by looking. The ")
TAB_FIELDS_NOTE = ("A tab for each field that matched, its count the rows under it; a row matching several fields is under each. "
                   "Each register opens to its rows.")


def entity_hit(q: str, e: dict, in_hand: list, words, boxes=None) -> str:
    """One entity in the results pane (ruling 108 (1)): its name (the fullest
    filed, people.describe), "n rows, n registers", contested marked, the
    registers named (ruling 110 (1): the rows of this search it holds are
    not listed, they all carry the one name); its link opens its pane, a
    click on it the graph beside the results, centred on it."""
    centre = f"{in_hand[0][0].name}:{in_hand[0][1]['key']}" if in_hand else e.get("centre") or ""
    link = f'<a class="row" href="{esc(href(q, ["entity:" + e["group_id"]], boxes))}"><strong>{mark(e["label"], words)}</strong></a>'
    out = [f'<article class="hit entity"{f" data-graph={chr(34)}{esc(graph_href(centre, boxes))}{chr(34)}" if centre else ""}>',
           f'<div>{link} <span class="meta">entity</span></div>',
           f'<div class="note">{esc(e["count"])}' + (' · <span class="warn">contested</span>' if e["contested"] else "")
           + (f' · <span class="lineage" title="{esc("a related company: " + "; ".join(e["related"]) + ", never one entity (ruling 106 (2))")}">'
              "related</span>" if e.get("related") else "") + "</div>",
           f'<div class="meta">{esc("; ".join(e.get("registers_named") or []))}</div>']
    if not in_hand:                                    # ruling 110 (1): the rows in hand are not listed, they share the name
        out.append('<div class="meta">found by its rows\' filed name (pub.names), no row heading this list</div>')
    out.append("</article>")
    return "".join(out)


def _register_rows(q, register, plain, hits, words, boxes, docs, far, collapsed: bool, hidden: int = 0) -> list:
    """One register's rows under a results heading; with `collapsed`, a
    details element closed to its name and count (ruling 108 (2))."""
    total = sum(n for _, n, _ in hits)
    body = []
    for v, n, rows in hits:
        body.append(f'<div class="view"><strong>{esc(v.name)}</strong> <span class="count">{n:,}</span></div>')
        for r in rows:
            body.append(hit(q, v, r, words, boxes, docs=docs, far=far))
        if n > len(rows):
            body.append(f'<p class="note">and {n - len(rows):,} more in {esc(v.name)}; narrow the search</p>')
    if collapsed:
        return [f'<details class="regs"><summary>{esc(plain)} <span class="count">{total:,}</span>{hidden_line(hidden)}</summary>']\
            + body + ["</details>"]
    return [f'<h3>{esc(plain)} <span class="count">{total:,}</span>{hidden_line(hidden)}</h3>'] + body


def _entities_part(q, rows, ents: dict, words, boxes, tab: str = None) -> tuple:
    """(html lines, ids of the rows gathered): the entities `rows` [(v, r)]
    fall in, then those the entity search found under `tab` (ruling 108 (3)),
    most rows of this search first; RESULT_ENTITIES at most, the rest counted."""
    from products.board.people import RESULT_ENTITIES
    hand, gathered = {}, set()
    for v, r in rows:
        gid = ents["group"].get(f"{v.name}:{r['key']}")
        if gid is not None:
            hand.setdefault(gid, []).append((v, r))
            gathered.add(f"{v.name}:{r['key']}")
    named = [g for g, t in ents.get("named", {}).items() if g not in hand and (tab is None or tab in t)]
    gids = sorted(hand, key=lambda g: (-len(hand[g]), -ents["entity"][g]["rows"], ents["entity"][g]["label"], g)) \
        + sorted(named, key=lambda g: (-ents["entity"][g]["rows"], ents["entity"][g]["label"], g))
    out = [f'<h3>Entities <span class="count">{len(gids):,}</span></h3>']
    if not gids:
        out.append('<p class="why">none found: no matching row is in a group</p>')
    for g in gids[:RESULT_ENTITIES]:
        out.append(entity_hit(q, ents["entity"][g], hand.get(g, []), words, boxes))
    if len(gids) > RESULT_ENTITIES:
        out.append(f'<p class="note">and {len(gids) - RESULT_ENTITIES:,} more entities; narrow the search</p>')
    return out, gathered


def _listing(q, by_reg: dict, regs: tuple, held: set, boxes, words, docs, far, hidden: dict, ents: dict = None,
             tab: str = None, collapsed: bool = False, asked: dict = None) -> list:
    """The results under one tab, or the one list: by register in the
    catalogue's order. In the entity state (`ents`, people.gather) the
    entities first, then the rows in no group, as rows (ruling 108 (1))."""
    out = []
    if ents is not None:
        rows = [(v, r) for register, _ in cat.REGISTERS for v, _, rs in by_reg.get(register, []) for r in rs]
        part, gathered = _entities_part(q, rows, ents, words, boxes, tab)
        out += part
        out.append('<h3>Rows in no group</h3>')
        by_reg = {reg: [(v, n, [r for r in rs if f"{v.name}:{r['key']}" not in gathered]) for v, n, rs in by_reg.get(reg, [])]
                  for reg, _ in cat.REGISTERS}
        by_reg = {reg: [(v, n, rs) for v, n, rs in hits if rs] for reg, hits in by_reg.items()}
        if not any(by_reg.values()):
            out.append('<p class="why">none: every row shown is in an entity above</p>')
    for register, plain in cat.REGISTERS:
        if register not in regs:
            continue
        hits = by_reg.get(register, [])
        present = [v for v in cat.views_of(register) if v.name in held]
        hid = sum(n for x, n in (hidden or {}).items() if x in {v.name for v in present})
        if collapsed or ents is not None:
            if hits:
                out += _register_rows(q, register, plain, hits, words, boxes, docs, far, collapsed, hid)
            continue
        if not present:
            out.append(f'<h3>{esc(plain)} <span class="count">0</span></h3><p class="why">not held</p>')
            continue
        if not hits:
            out.append(f'<h3>{esc(plain)} <span class="count">0</span>{hidden_line(hid)}</h3>')
            lacking = [label for f, label in FIELDS if (asked or {}).get(f) and not any(holds(v, f) for v in present)]
            if getattr(boxes, "mode", "all") == "any" and len(lacking) < len(asked or {}):
                lacking = []                                  # any field: a register holding one of them was searched
            out.append(f'<p class="why">none found{": none of its views holds a column for " + esc(", ".join(lacking)) if lacking else ""}</p>')
            continue
        out += _register_rows(q, register, plain, hits, words, boxes, docs, far, False, hid)
    return out


def tabbed(results: dict, ents: dict = None) -> list:
    """[(tab, label, rows under it, {register: [(view, count under the tab, its rows)]})]
    for the tabs with a row, or with an entity the entity search found under it
    (ruling 108 (2), (3)), in search.TABS order; the counts are each view's
    `_n_<tab>` (search.tab_sql), the whole count, not the rows shown."""
    named = {t for ts in ((ents or {}).get("named") or {}).values() for t in ts}
    out = []
    for t, label in TABS:
        by_reg, n = {}, 0
        for register, _ in cat.REGISTERS:
            for v, _, rows in results.get(register, []):
                k = int(rows[0].get(f"_n_{t}") or 0) if rows else 0
                if k:
                    by_reg.setdefault(register, []).append((v, k, [r for r in rows if r.get(f"_tab_{t}")]))
                    n += k
        if n or t in named:
            out.append((t, label, n, by_reg))
    return out


def results_pane(q: str, results: dict, held: set, regs: tuple, boxes, words=(), near: dict = None, docs: dict = None,
                 far: dict = None, ents: dict = None) -> str:
    """The wider pane beside the left one: every matching row, grouped by
    register with the register's count, over `regs`, the registers searched
    (search.selection); `boxes` the check boxes every href carries, and the
    filled fields (ruling 82); `near`, the near matches below (ruling 83);
    `docs`, the cited documents' states (document.statuses, ruling 86 (4)).
    Ruling 108: where the search ran with tabs (`results['tabs']`, the
    search box alone or "any field may match"), one tab per field matched,
    each register under it closed to its name and count; `ents`
    (people.gather) the entity state, entities first, then the rows in no
    group. A click on a result opens the graph beside the pane (graph.js)."""
    out = ['<section class="pane wide" id="results">', '<div class="reg">results' + (" · entities" if ents is not None else "") + "</div>"]
    asked = boxes.asked() if boxes is not None else {}
    if not boxes.all and not regs:
        out.append(f"<h2>Results</h2><p class=\"why\">{NOTHING_TICKED}</p></section>")
        return "\n".join(out)
    if not q and not asked:
        out.append("<h2>Results</h2><p class=\"why\">Type a name, an address or a number in the search box.</p></section>")
        return "\n".join(out)
    out.append(results_switch(q, boxes))
    out.append(f"<h2>{esc(q) if q else 'By field'}</h2>")
    out.append(f'<p class="note">searched: {"every held register" if boxes.all else esc(", ".join(REGISTER_NAME.get(x, x) for x in regs))}</p>')
    out.append(narrowed_line(boxes))
    if asked.get("year") and not re.fullmatch(r"\d{4}", asked["year"].strip()):
        out.append('<p class="warn">a year is four digits: nothing was searched</p>')
    if ents is not None:
        out.append(f'<p class="note">{esc(RESULTS_ENTITY_NOTE)}{esc(ENTITY_LABEL_NOTE)}. A row whose name is suppressed is never gathered.</p>')
    hidden = results.get("hidden") or {}
    tabs = tabbed(results, ents) if results.get("tabs") else None
    if tabs is None:
        out += _listing(q, results, regs, held, boxes, words, docs, far, hidden, ents, asked=asked)
    elif not tabs:
        out.append('<p class="why">none found</p>')
    else:
        out.append(register_totals(results, regs, held, hidden))
        out.append(f'<p class="note">{esc(TAB_FIELDS_NOTE)}</p><div class="ftabs">')
        for i, (t, label, n, _) in enumerate(tabs):
            out.append(f'<input type="radio" class="ft" name="ftab" id="ft-{t}"{" checked" if i == 0 else ""}>'
                       f'<label for="ft-{t}">{esc(label)} <span class="count">{n:,}</span></label>')
        for t, label, n, by_reg in tabs:
            out.append(f'<div class="ftab" id="ftab-{t}">')
            out += _listing(q, by_reg, regs, held, boxes, words, docs, far, {}, ents, tab=t, collapsed=True)
            out.append("</div>")
        out.append("</div>")
    if near is not None:
        out.append(near_section(q, near, words, boxes, docs, far))
    out.append("</section>")
    return "\n".join(out)


def register_totals(results: dict, regs: tuple, held: set, hidden: dict) -> str:
    """Above the tabs: each register searched that matched, with its count of
    rows matched and its removed rows hidden (ruling 93), the one place the
    tabs' registers are counted whole."""
    parts = []
    for register, plain in cat.REGISTERS:
        hits = (results.get(register) or []) if register in regs else []
        n = sum(x for _, x, _ in hits)
        names = {v.name for v in cat.views_of(register) if v.name in held}
        hid = sum(x for k, x in (hidden or {}).items() if k in names)
        if n or hid:
            parts.append(f'<span class="regtotal">{esc(plain)} <span class="count">{n:,}</span>{hidden_line(hid)}</span>')
    return '<p class="meta">matched: ' + (" · ".join(parts) or "none") + "</p>"


def results_switch(q: str, boxes) -> str:
    """Ruling 105's one switch, on the results pane too (ruling 108 (1)):
    rows or entities, the state in the address (`g=entities`), the path dropped."""
    parts = []
    for label, on in (("rows", False), ("entities", True)):
        if on == bool(getattr(boxes, "people", False)):
            parts.append(f'<strong aria-current="true">{label}</strong>')
        else:
            parts.append(f'<a href="{esc(href(q, [], boxes._replace(people=on)))}">{label}</a>')
    return '<p class="switch" id="state">show: ' + " · ".join(parts) + "</p>"


def holds(v: cat.View, field: str) -> bool:
    """Whether a view has a column for a field of the expanded search."""
    fs = cat.fields_of(v)
    if field in ("first", "middle", "last"):
        return bool(fs.names)
    return bool({"org": fs.organisation + fs.named, "address": fs.address, "year": fs.year + fs.dates}.get(field))


NEAR_CLASSES = (("names", "Given name and surname reversed", "given name and surname reversed"),
                ("addresses", "Addresses, a close match", "a close address"))


NEAR_NONE_FROM_BOX = ("the plain box matches words in any order, so a reversed name is already an exact match; "
                      "use the name fields to see reversed names apart")


def near_section(q: str, near: dict, words, boxes=None, docs: dict = None, far: dict = None) -> str:
    """Near matches (ruling 83), below the exact results and never among
    them or in their count: a details element, closed until clicked, with
    its two classes, each row saying which, capped with the whole count."""
    total = sum(near.get(k, {}).get("total", 0) for k, _, _ in NEAR_CLASSES)
    plain = len((q or "").split()) >= 2
    out = [f'<details class="near" id="near"><summary>Near matches <span class="count">{total:,}</span>'
           + (f' <span class="note">{esc(NEAR_NONE_FROM_BOX)}</span>' if total == 0 and plain else "") + '</summary>',
           '<p class="note">Not exact matches and not counted with them. Candidates by name or address alone, never a link.</p>']
    for k, heading, why in NEAR_CLASSES:
        c = near.get(k) or {}
        out.append(f'<h3>{esc(heading)} <span class="count">{c.get("total", 0):,}{"+" if c.get("more") else ""}</span></h3>')
        if c.get("why"):
            out.append(f'<p class="why">{esc(c["why"])}</p>')
            continue
        if c.get("note"):
            out.append(f'<p class="note">{esc(c["note"])}</p>')
        if not c.get("rows"):
            out.append('<p class="why">none found</p>')
            continue
        for v, r in c["rows"]:
            out.append(hit(q, v, r, words, boxes, why=why, docs=docs, far=far))
        shown_n = len(c["rows"])
        if c["total"] > shown_n:
            out.append(f'<p class="note">and {c["total"] - shown_n:,}{" or more" if c.get("more") else ""} more; narrow the search</p>')
    out.append("</details>")
    return "".join(out)


# ── a row's pane ────────────────────────────────────────────────────────────

def citation(v: cat.View, r: dict, doc_names: list, docs: dict = None) -> str:
    out = ['<h3>Citation</h3><table class="f">', f"<tr><th>source</th><td>{source_link(v, r, docs)}</td></tr>"]
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
    if v.no_url and not any(r.get(c) for c in v.urls):
        out.append(f'<tr><th>address</th><td><span class="note">{esc(v.no_url)}</span></td></tr>')
    for label, c in v.cite:
        if r.get(c) not in (None, ""):
            out.append(f"<tr><th>{esc(label)}</th><td><code>{esc(r[c])}</code></td></tr>")
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
        out.append(f'<tr><th>source note</th><td>{esc(r["source_note"])}</td></tr>')
    if r.get("loaded_at"):
        out.append(f'<tr><th>row written</th><td>{fmt(r["loaded_at"])} <span class="note">(never a date of anything)</span></td></tr>')
    out.append("</table>")
    out.append('<p class="note">"source" opens the captured document, whole as the lane captured it, the addresses it prints '
               "included: this board is on the local network only (ruling 88). A suppressed row or withheld text offers no "
               "document.</p>")
    return "\n".join(out)


def links_section(links: dict, group: dict, q: str, path: list, resolve, boxes=None) -> str:
    """resolve(ref) -> (view, row) or None, so a link opens the next pane."""
    out = ["<h3>Links</h3>"]
    if not links.get("built"):
        out.append(f'<p class="why">{esc(links.get("why"))}</p>')
        return "\n".join(out)
    if not links["confirmed"] and not links["near"] and not links.get("related"):
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
                    out.append(row_link(q, path, tv, tr, meta=f"{cat.rule_words(l['rule'])} {cat.rule_ref(l['rule'])}" + (f"; near because {l['reason']}" if l.get("reason") else ""), boxes=boxes))
                else:
                    out.append(f'<li>{esc(l["other"])} <span class="meta">row not found in the published views; {esc(cat.rule_words(l["rule"]))} {esc(cat.rule_ref(l["rule"]))}</span></li>')
                for d in l.get("decisions") or []:
                    out.append(f'<li class="meta">decision: {esc(d.get("verdict"))} by {esc(d.get("made_by"))}, {fmt(d.get("made_at"))}</li>')
            out.append("</ul>")
    if links.get("related"):
        mine = {l["link"]["row_a"] if l["other"] == l["link"]["row_b"] else l["link"]["row_b"] for l in links["related"]}
        out.append(related_section([l["link"] for l in links["related"]], mine, q, path, resolve, boxes))
    return "\n".join(out)


RELATED_NOTE = ("A related link is a relation the links lane found between two companies, never one entity: companies under "
                "one name, one carrying a year in brackets, with a person confirmed on both (ruling 106 (2)). Read in date "
                "order of registration. The graph draws it as a lineage frame.")


def related_section(links: list, mine: set, q: str, path: list, resolve, boxes=None, heading: str = "h3") -> str:
    """The related links (pub.links' related grade) of a row or of an
    entity's rows `mine`, under their own heading: the relation read in date
    order, the other company and the years, the people on both (each row of
    theirs on this side, suppressed ones counted, never named)."""
    from products.board import lineage
    items = lineage.pane_items(links, mine, resolve)
    out = [f'<{heading} id="related">Related companies <span class="count">{len(items):,}</span></{heading}>',
           f'<p class="note">{esc(RELATED_NOTE)}</p>', "<ul>"]
    for x in items:
        if x["other_hit"]:
            tv, tr = x["other_hit"]
            other = f'<a class="row" href="{esc(href(q, path + [f"{tv.name}:{tr["key"]}"], boxes))}">{esc(title_of(tv, tr))}</a>'
        else:
            other = f'<code>{esc(x["other"])}</code> <span class="note">row not found in the published views</span>'
        mine_y, other_y = x["years"]
        if x["earlier"]:
            line = f'this company ({esc(mine_y or "?")}) <strong>{esc(x["relation"])}</strong> {other} ({esc(other_y or "?")})'
        else:
            line = f'{other} ({esc(other_y or "?")}) <strong>{esc(x["relation"])}</strong> this company ({esc(mine_y or "?")})'
        names = ", ".join(f'<a href="{esc(href(q, path + [f"{v.name}:{r["key"]}"], boxes))}">{esc(title_of(v, r))}</a>' for v, r in x["people"])
        more = x["shared_people"] - len(x["people"]) - x["hidden"]
        people = (f'on both: {names}' if names else "on both: none shown") + (
            f'; {x["hidden"]:,} whose name is suppressed or whose row is not found, not named' if x["hidden"] else "") + (
            f"; and {more:,} more" if more > 0 else "")
        out.append(f'<li class="related">{line} <span class="meta">{esc(cat.rule_words(x["rule"]))} {esc(cat.rule_ref(x["rule"]))}'
                   + (f'; {esc(x["order"])}' if x["order"] else "") + "</span>"
                   + f'<div class="meta">{x["shared_people"]:,} {"person" if x["shared_people"] == 1 else "people"} {people}</div>'
                   + (f'<div class="meta">decision: {esc(x["decision"])}</div>' if x["decision"] else "") + "</li>")
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
           f"<h2>{struck(v, r, esc(title_of(v, r)))}</h2>"]
    if is_suppressed(v, r):
        out.append(f'<p class="warn">{SUPPRESSED}: the row and its figures stay (hard limit 16)</p>')
    if v.note:
        out.append(f'<p class="note">{esc(v.note)}</p>')
    out += [f'<p class="note">{esc(line)}</p>' for line in says_of(v, r)]
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
        cell = far_cell(v, r, c, ctx.get("far"), q, path, boxes)
        out.append(f"<tr><th>{esc(label)}</th><td>{cell if cell is not None else fmt(shown(v, r, c), c)}{flag_notes(v, r, c)}</td></tr>")
    out.append("</table>")
    for label, c, empty in v.text:      # a long text, whole, in this pane alone (never a results hit or the table)
        x = shown(v, r, c)
        out.append(f"<h3>{esc(label)}{flag_notes(v, r, c)}</h3>" + (f'<div class="text">{esc(x)}</div>' if x not in (None, "")
                                                 else f'<p class="why">{esc(empty)}</p>'))
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
    out.append(citation(v, r, ctx.get("doc_names") or [], ctx.get("docs")))
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


# ── an entity's pane (ruling 105) ───────────────────────────────────────────

ENTITY_LABEL_NOTE = ("name shown is the fullest filed among the group's rows, a display choice and not a link "
                     "(ruling 105, decision 1)")

def evidence_text(ev) -> str:
    """What a rule saw (pub.links' evidence), whole, one "field: value" after another."""
    if isinstance(ev, str):
        try:
            ev = json.loads(ev)
        except ValueError:
            return ev
    if not isinstance(ev, dict):
        return "" if ev is None else str(ev)
    parts = []
    for k, x in ev.items():
        if isinstance(x, list):
            x = ", ".join(json.dumps(y, ensure_ascii=False, default=str) if isinstance(y, (dict, list)) else str(y) for y in x)
        elif isinstance(x, dict):
            x = json.dumps(x, ensure_ascii=False, default=str)
        parts.append(f"{k.replace('_', ' ')}: {x}")
    return "; ".join(parts)


def entity_pane(ent, q: str, path: list, boxes=None) -> str:
    """A group the links lane gathered (pub.groups), opened from the graph's
    people state: its name (the fullest filed, said to be no link), its
    count, contested where flagged; its rows by register; the rules and
    evidence that gathered them, each decision on a pair; the near links
    from its rows, one hop, each with its reason, never gathered. `ent` is
    people.entity's, with `far`, the near rows resolved; the rows whose name
    is suppressed are never in it (hard limit 16)."""
    if ent is None:
        return '<section class="pane"><div class="reg">entity</div><p class="why">no group has that id in pub.groups: the links lane has rebuilt its groups since this path was saved</p></section>'
    d = ent["describe"]
    out = ['<section class="pane">', f'<div class="reg">entity · gathered by the links lane (pub.groups) · {esc(ent["group_id"])}</div>',
           f"<h2>{esc(d['label'])}</h2>", f'<p class="note">{esc(d["count"])}' + (f" · {esc(d['number'])}" if d.get("number") else "") + "</p>",
           f'<p class="note">The {esc(ENTITY_LABEL_NOTE)}.</p>']
    if d["contested"]:
        out.append('<p class="warn">contested: the watch flagged this group as a whole</p>')
    at = {ref: (v, r) for ref, v, r in ent["rows"]}

    def a(ref: str) -> str:
        if ref not in at:
            return f"<code>{esc(ref)}</code>"
        v, r = at[ref]
        return f'<a class="row" href="{esc(href(q, path + [f"{v.name}:{r["key"]}"], boxes))}">{esc(title_of(v, r))}</a>'

    out.append(f'<h3>The rows <span class="count">{len(ent["rows"]):,}</span></h3>')
    by_reg = {}
    for ref, v, r in ent["rows"]:
        by_reg.setdefault(v.register, []).append((v, r))
    for register, _ in cat.REGISTERS:
        if register in by_reg:
            out.append(f'<div class="reg">{register_heading(register)}</div><ul>'
                       + "".join(row_link(q, path, v, r, meta=v.name, boxes=boxes) for v, r in by_reg[register]) + "</ul>")
    decided = {}
    for x in ent["decisions"]:
        decided.setdefault((x["row_a"], x["row_b"]), []).append(x)
    own = [l for l in ent["links"] if l["grade"] == "confirmed"]
    out.append(f'<h3>The rules that gathered them <span class="count">{len(own):,}</span></h3>')
    if not own:
        out.append('<p class="why">none among the rows shown</p>')
    out.append("<ul>")
    for l in own:
        ev = evidence_text(l.get("evidence"))
        out.append(f'<li>{a(l["row_a"])} and {a(l["row_b"])} <span class="meta">{esc(cat.rule_words(l["rule"]))} {esc(cat.rule_ref(l["rule"]))}</span>'
                   + (f'<div class="meta">evidence: {esc(ev)}</div>' if ev else "")
                   + "".join(f'<div class="meta">decision: {esc(x["verdict"])} by {esc(x["made_by"])}, {fmt(x.get("made_at"))}</div>'
                             for x in decided.get((l["row_a"], l["row_b"]), [])) + "</li>")
    out.append("</ul>")
    far = ent.get("far") or {}
    if ent.get("related"):                             # ruling 106 (2): under its own heading, never with near
        out.append(related_section(ent["related"], set(at), q, path, lambda ref: at.get(ref) or far.get(ref), boxes))
    inner_near = [l for l in ent["links"] if l["grade"] not in ("confirmed", "related")]
    near = ent["near"]
    out.append(f'<h3>Near, one hop, never gathered <span class="count">{ent["near_total"]:,}</span></h3>')
    out.append('<p class="note">A near link is a shared name or circumstance a rule did not take as the same person; it is listed with '
               "its reason and never joins the rows into the group.</p>")
    if not near and not inner_near:
        out.append('<p class="why">none found</p>')
    out.append("<ul>")
    far = ent.get("far") or {}
    for l in inner_near + near:
        mine = l.get("mine") or l["row_a"]
        other = l["row_b"] if mine == l["row_a"] else l["row_a"]
        hit = at.get(other) or far.get(other)
        target = (f'<a class="row" href="{esc(href(q, path + [f"{hit[0].name}:{hit[1]["key"]}"], boxes))}">{esc(title_of(*hit))}</a>'
                  if hit else f'<code>{esc(other)}</code> <span class="note">row not found in the published views</span>')
        why = l.get("reason") or ""
        out.append(f'<li>{target} <span class="meta">near: {esc(cat.rule_words(l["rule"]))} {esc(cat.rule_ref(l["rule"]))}'
                   + (f"; because {esc(why)}" if why else "") + f"; from {a(mine)}"
                   + (" (both rows are in this group)" if other in at else "") + "</span>"
                   + "".join(f'<div class="meta">decision: {esc(x["verdict"])} by {esc(x["made_by"])}, {fmt(x.get("made_at"))}</div>'
                             for x in decided.get(tuple(sorted((mine, other))), [])) + "</li>")
    if ent["near_total"] > len(near):
        out.append(f'<li class="note">and {ent["near_total"] - len(near):,} more near links from these rows</li>')
    out.append("</ul></section>")
    return "\n".join(out)


# ── the use cases tab (ruling 87) ───────────────────────────────────────────

NONE_NAMED = '<span class="note">none named</span>'


def new_tab(label: str, url: str, cls: str = "") -> str:
    """A link that opens in a new browser tab, so a use case's interface stays apart from the board (ruling 89)."""
    c = f' class="{cls}"' if cls else ""
    return f'<a{c} href="{esc(url)}" target="_blank" rel="noopener">{label}</a>'


def use_name(r: dict) -> str:
    """The use case's name: a link to its interface's first page, the rest
    listed beside; with none, not a link, and what holds it."""
    links, held = r.get("links") or [], r.get("held") or ""
    if not links:
        return f'<strong>{esc(r["name"])}</strong><br><span class="note">{esc(held)}</span>'
    out = new_tab(f'<strong>{esc(r["name"])}</strong>', links[0][1], "uc")
    if len(links) > 1:
        out += '<br><span class="meta">also: ' + ", ".join(new_tab(esc(label), url) for label, url in links[1:]) + "</span>"
    return out


def uses_pane(rows: list, missing: str = "", source: str = "") -> str:
    """The plan's use cases in its order, each with the scan templates built
    for it and the registers the plan's reference names for it, held or not
    held. `missing`, the plan file's path when the copy the board runs from
    has none; `source`, the file read."""
    out = ['<section class="pane uses" id="uses">', '<div class="reg">use cases</div>', "<h2>The plan's use cases</h2>"]
    if missing:
        out.append(f'<p class="why">the plan\'s use-case table is not in the copy the board runs from: {esc(missing)} is missing</p></section>')
        return "\n".join(out)
    out.append(f'<p class="note">{len(rows)} use cases, in the plan\'s order, read now from <code>{esc(source)}</code>. '
               "A use case's name opens its interface in a new browser tab, on its own server (ruling 89): the subject report's "
               "form for its template, the register scan's page for each of its templates, the site preview for Follow the Money; "
               "one with no interface says what holds it. Templates: those built for each, on their shape (products/templates, "
               "products/scan/templates). Registers: the sources the plan's reference names for each, in its not-held table "
               "(the held tables name no use case), and whether a published view holds them today. Nothing here is written.</p>")
    out.append('<table class="uc"><tr><th>#</th><th>use case</th><th>who it serves</th><th>the question</th><th>shape</th>'
               "<th>step</th><th>templates built</th><th>registers the reference names</th></tr>")
    for r in rows:
        ts = "<br>".join(f'<code>{esc(t["name"])}</code> <span class="meta">{esc(t["shape"])}: {esc(t["title"])}</span>'
                         for t in r["templates"]) or '<span class="note">none built</span>'
        regs = []
        for src, found in r["registers"]:
            if not found:
                regs.append(f'{esc(src)}: <span class="note">not held, no lane</span>')
                continue
            state = ", ".join(f'{esc(plain)} <span class="{"meta" if ok else "warn"}">{"held" if ok else "not held"}</span>'
                              for _, plain, ok in found)
            regs.append(f"{esc(src)}: {state}")
        out.append(f'<tr><td>{esc(r["number"])}</td><td>{use_name(r)}</td><td>{esc(r["who"])}</td>'
                   f'<td>{esc(r["question"])}</td><td>{esc(r["shape"])}</td><td>{esc(r["step"])}</td><td>{ts}</td>'
                   f'<td>{"<br>".join(regs) or NONE_NAMED}</td></tr>')
    out.append("</table></section>")
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


# ── the database connection counter (ruling 90) ────────────────────────────

#: the logins the counter names on hover, in this order; any other login counts as "other"
LOGINS = ("qv4_product", "qv4_owner", "qv4_read", "qv4_oldread")


def db_counter(answer) -> str:
    """"db <in use>/<max_connections>" for the nav bar, the count by login in
    its hover title; `answer` is db.connections' {'max', 'by'}, or None when
    the query failed, which reads "db ?"."""
    if not answer:
        return '<span class="db" title="the connection count could not be read">db ?</span>'
    by = {k: 0 for k in LOGINS + ("other",)}
    for login, n in (answer.get("by") or {}).items():
        by[login if login in LOGINS else "other"] += int(n)
    title = ", ".join(f"{k} {n}" for k, n in by.items())
    return f'<span class="db" title="{esc(title)}">db {sum(by.values())}/{esc(answer.get("max"))}</span>'


def page(q: str, path: list, panes: list, message: str = "", boxes=None, tab: str = "search", db=None) -> str:
    """The page: three tabs, search (`/`, as before) and graph (`/graph`),
    each an href carrying the term and the registers checked (ruling 80),
    and use cases (`/uses`, ruling 87); the database connection counter at
    the bar's end (ruling 90; `db`, db.connections' answer, None reads "db ?")."""
    save = ""
    if path:
        save = (f'<form class="inline" method="post" action="/save"><input type="hidden" name="q" value="{esc(q)}">'
                f'<input type="hidden" name="p" value="{esc("|".join(path))}">'
                + hidden_boxes(boxes) +
                f'<input name="name" placeholder="name this path" size="18"> <button>save path</button></form>')
    msg = f'<span class="note">{esc(message)}</span>' if message else ""
    tabs = (f'<nav class="tabs"><a class="{"on" if tab == "search" else ""}" href="{esc(href(q, [] if tab != "search" else path, boxes))}">search</a> '
            f'<a class="{"on" if tab == "graph" else ""}" href="{esc(href(q, [], boxes, "/graph"))}">graph</a> '
            f'<a class="{"on" if tab == "uses" else ""}" href="/uses">use cases</a></nav>')
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>QueryNZ board</title>"
            f"<style>{CSS}</style></head><body><header><h1>QueryNZ board</h1>{tabs}"
            f"{save}<a href=\"/pinned\">pinned</a><a href=\"/saved\">saved paths</a>{msg}{db_counter(db)}</header>"
            f"<main>{''.join(panes)}</main></body></html>")
