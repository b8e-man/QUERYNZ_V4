"""A table on a PDF's text layer, read by word boxes (`pdftotext -tsv`): the
column heads a profile names fix each column's left edge on every page, and
each row is anchored by its one line that carries a figure in the profile's
anchor column. A spreadsheet exported to PDF wraps a long cell onto more lines
and aligns it in its row: to the bottom (Excel's default: the wrapped lines
stand above the anchor line), to the top (below it) or the middle; or
centres it on the anchor line, line for line (`centred`: a cell of two lines
stands half a line above and below the anchor, one of three a line above and
below it, so a line a whole line from its anchor is that row's only if the
row has its mirror, or the page's edge cuts it; else it is a name the page
break cut, which joins the row on the other side of the break). The
profile says which, and every line that is not an anchor joins the anchor its
alignment points to. Lines before the head and lines no anchor claims are kept
as the page's other text (a title, a key, a total, a page number), never as a
row. Nothing here reads a value's meaning; the layout's reader does.

    words(data)                       [Word] for the whole document
    pages_of(words)                   {page: [Line]}
    find_head(lines, heads)           (head line index, {column: left edge}) or None
    table(data, heads, anchor, align) Table: rows of {column: text}, and the other text
"""
import collections
import csv
import io
import re
import subprocess
from dataclasses import dataclass, field

LINE_TOL = 2.5         # points: words whose tops differ by less sit on one line (an Excel cell's baseline shifts 0.6)
EDGE_SLACK = 3.0       # points: a word starting this far left of a column's edge still belongs to it
RUN_ON = re.compile(r"^(.*[^\s$\d,.(-])(\$\s?[\d,]+\.\d{2})$")
MONEY = re.compile(r"^-?\$?\s?-?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?$|^-?\$?\s?-?\d+(?:\.\d{1,2})?$")


@dataclass
class Word:
    page: int
    x0: float
    top: float
    x1: float
    text: str


@dataclass
class Line:
    page: int
    top: float
    words: list = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w.text for w in sorted(self.words, key=lambda w: w.x0))


@dataclass
class Table:
    rows: list = field(default_factory=list)       # [{"page", "line" (the anchor's top), "anchor_cells", column: text}]
    other: list = field(default_factory=list)      # [(page, text)] lines that are not in a row
    totals: list = field(default_factory=list)     # [(page, [figures])] lines of figures alone
    pages: int = 0
    pages_with_head: int = 0
    text_pages: int = 0


def words(data: bytes) -> list:
    """Every word on the text layer with its box, page by page."""
    r = subprocess.run(["pdftotext", "-q", "-tsv", "-", "-"], input=data, capture_output=True, timeout=300)
    out = []
    for row in csv.reader(io.StringIO(r.stdout.decode("utf-8", "replace")), delimiter="\t", quoting=csv.QUOTE_NONE):
        if len(row) < 12 or row[0] != "5":
            continue
        try:
            page, left, top, width = int(row[1]), float(row[6]), float(row[7]), float(row[8])
        except ValueError:
            continue
        text = row[11].strip()
        m = RUN_ON.match(text)
        if m:                                  # a name the text layer ran into its figure: two words, split by share
            cut = left + width * len(m.group(1)) / len(text)
            out += [Word(page, left, top, cut, m.group(1)), Word(page, cut, top, left + width, m.group(2))]
        elif text:
            out.append(Word(page, left, top, left + width, text))
    return out


def page_count(data: bytes) -> int:
    r = subprocess.run(["pdfinfo", "-"], input=data, capture_output=True, timeout=60)
    m = re.search(rb"Pages:\s+(\d+)", r.stdout)
    return int(m.group(1)) if m else 0


def pages_of(ws: list) -> dict:
    """{page: [Line]} top to bottom; a word joins the line whose top is within LINE_TOL of its own."""
    out = {}
    for w in sorted(ws, key=lambda w: (w.page, w.top, w.x0)):
        lines = out.setdefault(w.page, [])
        if lines and abs(lines[-1].top - w.top) < LINE_TOL:
            lines[-1].words.append(w)
        else:
            lines.append(Line(w.page, w.top, [w]))
    return out


def _seq(line: Line, label: str):
    """(x0, x1) of `label` (its words in order, adjacent) on the line, or None."""
    want = label.lower().split()
    got = sorted(line.words, key=lambda w: w.x0)
    texts = [w.text.lower() for w in got]
    for i in range(len(texts) - len(want) + 1):
        if texts[i:i + len(want)] == want:
            return got[i].x0, got[i + len(want) - 1].x1
    return None


def find_head(lines: list, heads: dict, mode: str = "left"):
    """The first line carrying every column head in left-to-right order, and each column's left edge. `heads`:
    {column: label or [labels]}, in the table's order; a head may stand on the line above or below the head line (a
    head over two or three lines), so those are looked at too, and the head's lines are not rows. A column starts where its head starts (a head printed at its column's left), or,
    for the columns `mode` names (or every column with `mode="gap"`), halfway between its head and the one before (a
    head centred over left-set text)."""
    for i, line in enumerate(lines):
        spans, low = {}, i
        for col, labels in heads.items():
            for label in ([labels] if isinstance(labels, str) else labels):
                x, at = _seq(line, label), i
                for j in (i - 1, i + 1):           # a head over two or three lines: the line above or below
                    if x is None and 0 <= j < len(lines) and abs(lines[j].top - line.top) < 25:
                        x, at = _seq(lines[j], label), j
                if x is not None:
                    spans[col] = x
                    low = max(low, at)
                    break
            if col not in spans:
                break
        starts = [x0 for x0, _ in spans.values()]
        if len(spans) == len(heads) and starts == sorted(starts):
            cols = list(spans)
            edges = {c: x0 for c, (x0, _) in spans.items()}
            gap = cols[1:] if mode == "gap" else [c for c in cols[1:] if c in (mode or ())]
            for a, b in zip(cols, cols[1:]):
                if b in gap:
                    edges[b] = (spans[a][1] + spans[b][0]) / 2
            return low, edges
    return None


SHIFT_GAP = 8.0         # points: a shifted column starts at least this far right of the column before it
SHIFT_MIN = 3           # lines: a left edge the text shares at least this often


def _shifted(lines: list, edges: dict, shift) -> dict:
    """The page's edges with each column in `shift` moved to where its text starts: the left edge most of its lines'
    first words share, between the column before it and its head. For a head centred over left-set text, whose column
    starts left of the head (Milestone's 2020 to 2022 lists): no rule from the heads alone finds that edge."""
    out = dict(edges)
    cols = sorted(edges.items(), key=lambda kv: kv[1])
    for (prev, px), (col, x) in zip(cols, cols[1:]):
        if col not in shift:
            continue
        starts = collections.Counter(round(w.x0) for ln in lines for w in ln.words
                                     if not is_money(w.text) and px + SHIFT_GAP < w.x0 <= x + EDGE_SLACK)
        if starts:
            at, n = starts.most_common(1)[0]
            if n >= SHIFT_MIN:
                out[col] = at - 0.5
    return out


def _cells(line: Line, edges: dict) -> dict:
    cols = sorted(edges.items(), key=lambda kv: kv[1])
    out = {}
    for w in sorted(line.words, key=lambda w: w.x0):
        col = cols[0][0]
        at = w.x1 - EDGE_SLACK if is_money(w.text) else w.x0 + EDGE_SLACK    # a figure is placed by its right edge
        for name, x in cols:
            if at >= x:
                col = name
        out.setdefault(col, []).append(w.text)
    return {k: " ".join(v) for k, v in out.items()}


def is_money(text: str) -> bool:
    return bool(text) and bool(MONEY.match(text.replace(" ", "")))


#: `centred`: a line this near an anchor is its (half a line: a cell of two lines); a line up to `CENTRED_FAR` away is a
#: whole line off (a cell of three)
CENTRED_NEAR = 11.0
CENTRED_FAR = 24.0
CENTRED_MIRROR = 3.5


def _centred(body: list, anchors: list) -> dict:
    """{body index: anchor index, or "prev" (the tail of the row the page break cut, before this page's first
    anchor), or "next" (the head of the next page's first row, after this page's last anchor)}. A line half a line
    from an anchor is its; a line a whole line from an anchor is its only where the anchor's own line carries the
    cell's middle line (words besides its figures) and the anchor has the mirror line on its other side or the page's
    body ends there (a cell is the line's own columns); else the line is a name the page break cut."""
    tops = {i: body[i][0].top for i in range(len(body))}
    plain = [i for i, (_, c) in enumerate(body) if "_section" not in c and i not in anchors]
    first, last = (min(tops.values()), max(tops.values())) if tops else (0, 0)
    out = {}
    for i in plain:
        near = sorted((abs(tops[a] - tops[i]), a) for a in anchors if abs(tops[a] - tops[i]) < CENTRED_FAR)
        if near and near[0][0] < CENTRED_NEAR:
            out[i] = near[0][1]
            continue
        for d, a in near:
            if not any(body[a][1].get(col) for col in body[i][1]):
                continue                      # the anchor's line carries no middle line of the cell: an even count
            mirror = 2 * tops[a] - tops[i]
            if (mirror < first - CENTRED_MIRROR or mirror > last + CENTRED_MIRROR or
                    any(abs(tops[j] - mirror) < CENTRED_MIRROR for j in plain if j != i)):
                out[i] = a
                break
        else:
            if anchors and tops[i] > tops[anchors[-1]]:
                out[i] = "next"
            elif anchors and tops[i] < tops[anchors[0]]:
                out[i] = "prev"
            else:
                out[i] = None
    return out


def table(data: bytes, heads: dict, anchor: str, align: str = "bottom", ws: list = None,
          carry: bool = True, edges: dict = None, skip: list = (), stop: list = (), sections: list = (),
          anchor_kind: str = "money", mode: str = "left", total_lines: str = "figures", head_tail: str = None,
          shift: tuple = ()) -> Table:
    """Every row of the table, page by page. A page with no head line takes the edges of the last page that had
    one when `carry` (a spreadsheet printed without its head row repeated); else, or before any head, it is all
    other text. A list printed with no head row at all gives its columns' left `edges` in points instead of
    `heads`; a line matching a `skip` pattern (a title, a running line) is other text, and from a line matching a
    `stop` pattern (a legend after the table) the rest of the document is. A line matching a `sections` pattern (a
    sub-table's own title) is no row's and names the section of every row below it. A line of figures and nothing
    else (a total) is never a row's fragment: it is kept in `totals`."""
    ws = words(data) if ws is None else ws
    pages = pages_of(ws)
    out = Table(pages=page_count(data) or max(pages, default=0), text_pages=len(pages))
    skip = [re.compile(p, re.I) for p in skip]
    stop = [re.compile(p, re.I) for p in stop]
    sections = [re.compile(p, re.I) for p in sections]
    section, ended = None, False
    fixed = edges
    carried = []            # `centred`: lines at a page's foot that open the next page's first row
    for page in sorted(pages):
        if ended:
            out.other += [(page, x.text) for x in pages[page]]
            continue
        lines = []
        for k, ln in enumerate(pages[page]):
            if any(p.search(ln.text) for p in stop):
                out.other += [(page, x.text) for x in pages[page][k:]]
                ended = True
                break
            if any(p.search(ln.text) for p in skip):
                out.other.append((page, ln.text))
            elif any(p.search(ln.text) for p in sections):
                out.other.append((page, ln.text))
                lines.append(Line(page, ln.top, [], ))
                lines[-1].section = ln.text
            elif total_lines and any(is_money(w.text) for w in ln.words) and all(
                    is_money(w.text) or w.text in ("$", ":") or w.text.lower().rstrip(":") == "total" for w in ln.words) \
                    and (total_lines == "figures" or any(w.text.lower().rstrip(":") == "total" for w in ln.words)):
                out.totals.append((page, [w.text for w in sorted(ln.words, key=lambda w: w.x0) if is_money(w.text)]))
            else:
                lines.append(ln)
        found = (-1, fixed) if fixed else find_head(lines, heads, mode)
        if found is None and not (carry and edges):
            out.other += [(page, ln.text) for ln in lines]
            continue
        if found is not None:
            out.pages_with_head += 1
            hi, edges = found
        else:
            hi = -1
        if hi + 1 < len(lines) and found is not None and lines[hi + 1].top - lines[hi].top < 15 and not any(
                is_money(w.text) for w in lines[hi + 1].words):
            hi += 1                                 # the head's third line ('Amount Amount Amount')
        while head_tail and found is not None and hi + 1 < len(lines) and lines[hi + 1].top - lines[hi].top < 15 \
                and re.match(head_tail, lines[hi + 1].text):
            hi += 1                                 # a head of four or five lines: its words alone, close under it
        out.other += [(page, ln.text) for ln in lines[:hi + 1]]
        if shift and found is not None:
            edges = _shifted(lines[hi + 1:], edges, shift)
        body = []
        for ln in lines[hi + 1:]:
            if getattr(ln, "section", None):
                body.append((ln, {"_section": ln.section}))
            else:
                body.append((ln, _cells(ln, edges)))
        test = is_money if anchor_kind == "money" else (lambda x: bool(re.fullmatch(r"\d{1,5}", x)))
        pick = (lambda x: x.split(" ")[-1]) if anchor_kind == "money" else (lambda x: x.split(" ")[0])
        anchors = [i for i, (_, c) in enumerate(body) if "_section" not in c and test(pick(c.get(anchor, "")))]
        claimed = {i: [] for i in anchors}
        marks = {}
        carried_in, carried = carried, []      # the lines the last page's foot left for this page's first row
        if align == "centred":
            to_of = _centred(body, anchors)
        for i, (ln, c) in enumerate(body):
            if "_section" in c:
                section = c["_section"]
                continue
            marks[i] = section
            if i in claimed:
                continue
            if align == "centred":
                to = to_of.get(i)
                if to == "next":
                    carried.append(body[i][1])
                    continue
                if to == "prev":
                    prev = out.rows[-1] if out.rows else None
                    if prev is None:
                        out.other.append((page, ln.text))
                    else:
                        for col, text in c.items():
                            prev[col] = (prev[col] + " " + text) if col in prev else text
                    continue
            elif align == "bottom":
                to = next((a for a in anchors if a > i), None)
            elif align == "top":
                to = next((a for a in reversed(anchors) if a < i), None)
            else:
                near = [a for a in anchors if abs(body[a][0].top - ln.top) < 30]
                to = min(near, key=lambda a: abs(body[a][0].top - ln.top)) if near else None
            if to is None and align == "top" and out.rows and (not anchors or i < anchors[0]):
                prev = out.rows[-1]                  # a row the page break cut: its tail tops the next page
                for col, text in c.items():
                    prev[col] = (prev[col] + " " + text) if col in prev else text
            elif to is None:
                out.other.append((page, ln.text))
            else:
                claimed[to].append(i)
        for a in anchors:
            parts = sorted(claimed[a] + [a])
            row = {"page": page, "line": round(body[a][0].top, 1), "anchor_cells": dict(body[a][1]),
                   "section": marks.get(a)}
            pieces = [body[i][1] for i in parts]
            if carried_in and a == anchors[0]:
                pieces, carried_in = carried_in + pieces, []
            for cells in pieces:
                for col, text in cells.items():
                    row[col] = (row[col] + " " + text) if col in row else text
            out.rows.append(row)
        if carried_in:                          # no row on this page to take them
            out.other += [(page, " ".join(c.values())) for c in carried_in]
    out.other += [(max(pages, default=0), " ".join(c.values())) for c in carried]    # no page after to take them
    return out
