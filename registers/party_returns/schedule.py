"""A part's table, read from a return's page texts (plan 4.1, tranche 2):
Part A's donors, Part H's loans. One row is one line of the form: the
name-and-address cell, the dates as printed, the Yes/No column and the
amount. No model is called; the page texts are the text layer or the page
reader's stored readings, as `read.py` gathered them.

A part's region runs from its heading (`PART A: PARTY DONATIONS OF MORE
THAN …`, known by its words) to the next part's heading, instructions or
total, and starts again wherever the heading is repeated: a continuation
sheet repeats it. The declaration page is never part of a region (its
part lines carry the same words).

The same table comes out of the readers in four shapes, and each has its
own route. Each row says which route paired its cell with its amount
(`paired_by`), because that is where a reading goes wrong:

- **layout** (the text layer, `pdftotext -layout`): a row spreads over two
  or three lines, the amount on one, the name above or below it, the end
  of the address after it. Every amount opens a row; the lines between
  two amounts go to the nearer, a line opening with a printed row number
  starts the next row, and a tie goes to the later row (the form prints a
  name before its figure). The name cell is the text left of the date
  column, measured from the page's own column heading.
- **table** (the page reader's markdown): one row per line. A blank first
  cell is the same donor's next dated donation.
- **numbered** (the page reader's list, `3. NO`, `3. $ 5,000.00`): the
  printed row number pairs the cell with its amount; when the numbers
  leave a figure with no cell they are the reader's own list numbers,
  and the page goes the stacked route.
- **stacked** (the page reader's lines with no markup): each row's cell,
  dates, Yes/No and amount in turn, every amount closing a row.

A page the reader went down column by column (every name, then every
amount) is refused, never paired by order: a name shifted by one row still
adds up, so the part's total cannot catch it. A page that fits none of
these yields no rows, and the reconciliation in the caller says so.
`TOTAL FOR PART A $ x` is the part's own printed total; the blank form's
`$0.00`, a zero row, a row pointing at an attached schedule and a page
subtotal (a last figure equal to the figures above it) are not rows.

    region(texts, heading, end)        [(page, line)]
    rows(texts, src, heading, end)     (rows, printed_total, problems)
"""
import re
from dataclasses import dataclass

#: a money cell: `$ 12,000.00`, `$12000.00`, `12,000.00`
MONEY = re.compile(r"\$?\s*(\d{1,3}(?:,\d{3})+|\d+)\.(\d{2})(?!\d)")
MONEY_ONLY = re.compile(r"^\W{0,3}\$?\s*(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}\s*\|?\s*$")
DATE = re.compile(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b|\b(?:various|ongoing|monthly|weekly)\b", re.I)
YESNO = re.compile(r"^(?:yes|no)$", re.I)
DECLARATION = re.compile(r"\bTotal\b[^(\n]{0,30}\(\s*A\s*\+", re.I)
#: the column headings and the form's own words inside a table: never a cell
FURNITURE = re.compile(
    r"donor.?s?\s+name|street\s+address|date\s+donation|aggregated\s+donations|dd\s*/\s*mm\s*/\s*yyyy|"
    r"enter\s+yes\s+or\s+no|does\s+the\s+donation|contain\s+contributions|from\s+another\s+person|"
    r"of\s+more\s+than\s+\$|total\s+aggregated|including\s+gst|amount\s+of\s+(?:donation|loan)|write\s+.nil|"
    r"^\W*received\W*$|^\W*donations\W*$|^\W*page:?\s*\d+\W*$|^\W*part\s+[a-i]\W*(?:page:?\s*\d+)?\W*$|"
    r"name\s+and\s+(?:street\s+)?address\s+of|lender.?s?\s+name|date\s+(?:of\s+)?(?:the\s+)?loan|interest\s+rate|"
    r"balance\s+of|repayment|terms\s+of\s+(?:the\s+)?loan|security\s+(?:given|for)|amount\s+of\s+the\s+loan|"
    r"instructions?\s+for|^\s*\|?\s*:?-{3,}|^\W*nil\W*$", re.I)
PRINTED_TOTAL = re.compile(r"TOTAL\s+FOR\s+PART\s+([A-I])\b", re.I)
TABLE_START = re.compile(r"^\s*\|?\s*(?:donor.?s?\s+name|name\s+and\s+(?:street\s+)?address\s+of|lender.?s?\s+name)", re.I)
ROW_NUMBER = re.compile(r"^\s{0,3}(\d{1,3})(?=\s|$)")     # the form prints it at the margin; a wrapped address is indented further
NUMBERED = re.compile(r"^\s*(\d{1,3})\.\s+(.*)$")
DATE_HEAD = re.compile(r"Date\s+donation|aggregated\s+donations|dd/mm/yyyy|Date\s+(?:of\s+)?(?:the\s+)?loan", re.I)
#: a row that points at an attached schedule carries the schedule's total, not a donor
POINTER = re.compile(r"\bsee\s+(?:the\s+)?(?:attach(?:ed|ment)|schedule|appendix|over|list|separate)", re.I)
CENT = 0.005
FULL_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/(?:\d{4}|\d{2})\b,?")    # with its year: a flat number `3/12` has none
RULE = re.compile(r"^[Il|!]$")    # a table rule the text layer kept as a letter
DONOR_COLUMN = 60          # the name cell ends about here when the page prints no column heading


@dataclass
class Row:
    page: int
    cell: str                  # the name-and-address cell as read; never published whole
    amount: float
    dates: str = ""
    yes_no: str = ""
    n: int = None              # the printed row number, when there is one
    paired_by: str = ""        # layout | table | numbered | stacked
    read_from: str = ""        # text | pixels


def money(s: str):
    ms = list(MONEY.finditer(s or ""))
    if not ms:
        return None
    m = ms[-1]
    return float(m.group(1).replace(",", "") + "." + m.group(2))


def region(texts: dict, heading, end) -> list:
    """The lines of one part's table, in page order: [(page, line)]. The
    form's instructions between a heading and the table's column headings
    are dropped, its printed total kept."""
    out, state = [], "off"
    for p in sorted(texts):
        lines = (texts[p] or "").splitlines()
        if any(DECLARATION.search(l) for l in lines):
            state = "off"
            continue
        for line in lines:
            if heading.search(line):
                state = "head"
            elif state != "off" and end.search(line):
                state = "off"
            elif state == "head" and TABLE_START.search(line):
                state = "on"
                out.append((p, line))
            elif state == "on" or (state == "head" and (PRINTED_TOTAL.search(line) or MONEY_ONLY.match(line))):
                out.append((p, line))
    return out


def printed_total(lines: list, letter: str):
    """`TOTAL FOR PART A $ x`, or the figure alone on the next line."""
    for i, (p, line) in enumerate(lines):
        m = PRINTED_TOTAL.search(line)
        if not m or m.group(1).upper() != letter:
            continue
        got = money(line[m.end():])
        if got is None and i + 1 < len(lines) and MONEY_ONLY.match(lines[i + 1][1]):
            got = money(lines[i + 1][1])
        if got is not None:
            return got
    return None


def _furniture(line: str) -> bool:
    return bool(FURNITURE.search(line)) or bool(PRINTED_TOTAL.search(line))


# --- the routes ----------------------------------------------------------------

def _table(lines, page) -> list:
    out = []
    for line in lines:
        s = line.strip()
        if s.count("|") < 3 or _furniture(s):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        amount = money(cells[-1]) if cells else None
        if amount is None or len(cells) < 3:
            continue
        cell, rest = cells[0], cells[1:-1]
        n = None
        m = re.fullmatch(r"(\d{1,3})\.?", cell)
        if m and len(cells) >= 4:                         # a row-number column
            n, cell, rest = int(m.group(1)), cells[1], cells[2:-1]
        if not cell and out:
            cell, n = out[-1].cell, out[-1].n
        yes_no = next((c for c in rest if YESNO.match(c)), "")
        dates = " ".join(c for c in rest if DATE.search(c))
        out.append(Row(page, cell, amount, dates, yes_no, n, "table"))
    return out


def _numbered(lines, page) -> list:
    by = {}
    order = []
    for line in lines:
        m = NUMBERED.match(line)
        if not m or _furniture(m.group(2)):
            continue
        n, body = int(m.group(1)), m.group(2).strip()
        if n not in by:
            by[n] = {"cell": [], "amount": None, "dates": [], "yes_no": ""}
            order.append(n)
        if MONEY_ONLY.match(body):
            by[n]["amount"] = money(body)
        elif YESNO.match(body):
            by[n]["yes_no"] = body
        elif DATE.fullmatch(body.split(",")[0].strip()):
            by[n]["dates"].append(body)
        else:
            by[n]["cell"].append(body)
    got = [Row(page, " ".join(by[n]["cell"]), by[n]["amount"], " ".join(by[n]["dates"]), by[n]["yes_no"], n, "numbered")
           for n in order if by[n]["amount"]]
    if any(not r.cell for r in got):            # the reader numbered its own list items, not the form's rows
        return _stacked([m.group(2) if (m := NUMBERED.match(l)) else l for l in lines], page)
    return got


def _stacked(lines, page):
    """Lines with no table markup: each row's cell, its dates, Yes/No and
    amount in turn, every amount closing a row. None when an amount has no
    cell before it or a cell is left with no amount: the reader went down
    the columns, and pairing a column of names with a column of figures by
    their order is the one thing the totals cannot check (a shifted name
    still adds up)."""
    out, pending = [], {"cell": [], "dates": [], "yes_no": ""}
    for line in lines:
        s = line.strip()
        if not s or _furniture(s):
            continue
        if MONEY_ONLY.match(s):
            if not money(s):
                continue
            if not pending["cell"]:
                return None
            out.append(Row(page, "\n".join(pending["cell"]), money(s), " ".join(pending["dates"]), pending["yes_no"],
                           None, "stacked"))
            pending = {"cell": [], "dates": [], "yes_no": ""}
        elif YESNO.match(s):
            pending["yes_no"] = s
        elif DATE.match(s) and not re.search(r"[A-Za-z]{4,}", DATE.sub("", s)):
            pending["dates"].append(s)
        else:
            pending["cell"].append(s)
    if not out:                                 # an auditor's stamp, a stray mark: no money, no row
        return []
    return None if pending["cell"] else out


def _closer(s: str):
    """(text before the figure, amount) when a line ends in its one money
    figure, else None."""
    ms = list(MONEY.finditer(s))
    if len(ms) != 1 or s[ms[0].end():].strip(" |"):
        return None
    return s[:ms[0].start()].rstrip(" $|"), money(ms[0].group(0))


def _inline(lines, page):
    """The page reader's lines with no markup where a row's figure ends a
    line that may carry the rest of the row (`1 name, address 3/4/2025 No
    $ 5,000.00`). Every such line closes a row, its own text and the lines
    since the last row being the row's cell, dates and Yes/No. A closing
    line that carries a cell after lines that also carry one is refused
    (None): which row a stray line belongs to is a guess. So are a figure
    with no cell, two numbered cells waiting for one figure (the reader went
    down the columns), and text left after the last figure. A bare row
    number is an empty row of the form."""
    out, pending = [], []
    for line in lines:
        s = line.strip()
        if not s or _furniture(s) or re.fullmatch(r"\d{1,3}\.?", s):
            continue
        got = _closer(s)
        if got is None:
            if out and not pending and not _cell_words(s):
                out[-1].dates = " ".join([out[-1].dates] + [d.group(0) for d in DATE.finditer(s)]).strip()
            else:
                pending.append(s)
            continue
        text, amount = got
        if not amount:
            continue
        yes_no, n = "", None
        yn = re.search(r"(?:^|\s)(yes|no)\s*$", text, re.I)
        if yn:
            yes_no, text = yn.group(1), text[:yn.start()]
        m = re.match(r"^\s*(\d{1,3})\.?(?:\s+|$)", text)
        if m and not _cell_words(text[m.end():]):
            n, text = int(m.group(1)), text[m.end():]
        waiting = [p for p in pending if _cell_words(p)]
        numbers = [int(m.group(1)) for p in waiting if (m := re.match(r"^(\d{1,3})\.?\s+[A-Za-z]", p))]
        if (_cell_words(text) and waiting) or any(b == a + 1 for a, b in zip(numbers, numbers[1:])):
            return None
        cell = [w for w in (_cell_words(p) for p in pending + [text]) if w]
        if not cell:
            return None
        m = re.match(r"^(\d{1,3})\.?\s+(?=[A-Za-z])", cell[0])
        if m:
            if n is not None and int(m.group(1)) != n:
                return None
            n, cell[0] = int(m.group(1)), cell[0][m.end():]
        dates = [d.group(0) for p in pending + [text] for d in DATE.finditer(p)]
        out.append(Row(page, "\n".join(cell), amount, " ".join(dates), yes_no, n, "inline"))
        pending = []
    if any(_cell_words(p) for p in pending):
        return None
    ns = [r.n for r in out]
    if any(x is not None for x in ns) and (None in ns or any(b != a + 1 for a, b in zip(ns, ns[1:]))):
        return None                             # a figure paired with the wrong row number: a name went missing
    return out


def _cell_words(s: str) -> str:
    """A line's text with its dates (and the dashes between them) taken out."""
    return " ".join(re.sub(r"(?:^|\s)[-–](?=\s|$)", " ", DATE.sub(" ", s)).split()).strip(" ,-–")


def _row_numbers(lines: list) -> set:
    """The lines that open with the form's printed row number: the numbers
    at the page's leftmost margin, taken only when they climb in order. A
    wrapped address that starts with its house number sits at a margin too,
    and its numbers do not climb."""
    found = [(k, m.start(1), m.end(1), int(m.group(1))) for k, l in enumerate(lines) if (m := ROW_NUMBER.match(l))]
    best = set()
    for edge in (1, 2):                         # numbers set flush left, or right-aligned (`9` under `10`)
        for x in {f[edge] for f in found}:
            at = [(f[0], f[3]) for f in found if f[edge] == x]
            ns = [n for _, n in at]
            if len(at) > len(best) and all(b > a for a, b in zip(ns, ns[1:])):
                best = {k for k, _ in at}
    return best


def _layout(lines, page) -> list:
    """The text layer, `pdftotext -layout`."""
    date_x = None
    for line in lines:
        m = DATE_HEAD.search(line)
        if m and (date_x is None or m.start() < date_x):
            date_x = m.start()
    edge = (date_x - 10) if date_x and date_x > 40 else DONOR_COLUMN    # the dates sit a little left of their heading
    lines = [l for l in lines if l.strip() and not _furniture(l)]
    numbered = _row_numbers(lines)
    items = []
    for k, line in enumerate(lines):
        n = None
        body = line
        m = ROW_NUMBER.match(line) if k in numbered else None
        if m:
            n = int(m.group(1))
            body = " " * m.end() + line[m.end():]
        name, dates, yes_no, amount = [], [], "", None
        for seg in re.finditer(r"\S+(?:\s{1,2}\S+)*", body):
            t = seg.group(0)
            if RULE.match(t):
                continue
            if MONEY_ONLY.match(t) and seg.start() >= edge:
                amount = money(t)
            elif YESNO.match(t):
                yes_no = t
            elif seg.start() < edge and not DATE.fullmatch(t):
                # a dated token run on to the name by a space or two is the date column, never the address
                dates += [m.group(0) for m in FULL_DATE.finditer(t)]
                rest = " ".join(FULL_DATE.sub(" ", t).split()).strip(" ,")
                if rest:
                    name.append(rest)
            elif DATE.search(t) or seg.start() >= edge:
                dates.append(t)
        items.append({"n": n, "name": " ".join(name), "dates": " ".join(dates), "yes_no": yes_no, "amount": amount})
    anchors = [i for i, it in enumerate(items) if it["amount"]]
    if not anchors:
        return []
    if len(anchors) > 2 and items[anchors[-1]]["n"] is None and \
            abs(items[anchors[-1]]["amount"] - sum(items[a]["amount"] for a in anchors[:-1])) < CENT:
        anchors = anchors[:-1]          # the filer's page subtotal under the table: it owns no line
    owner = [None] * len(items)
    for k, a in enumerate(anchors):
        owner[a] = k
    for i in range(len(items)):
        if owner[i] is not None:
            continue
        before = max((k for k, a in enumerate(anchors) if a < i), default=None)
        after = min((k for k, a in enumerate(anchors) if a > i), default=None)
        if before is None:
            owner[i] = after
            continue
        if after is None:
            # after the page's last figure only the end of that row's address; a numbered line
            # with a name there, or a name further down, is a row whose figure is not on this page
            tail = range(anchors[before] + 1, i + 1)
            if items[i]["name"] and (i - anchors[before] > 2 or any(items[j]["n"] is not None for j in tail)):
                return None
            owner[i] = before
            continue
        gap = range(anchors[before] + 1, anchors[after])
        opener = next((j for j in gap if items[j]["n"] is not None), None)
        if opener is None and items[anchors[after]]["n"] is not None and items[anchors[after]]["name"]:
            opener = anchors[after]                 # the next row opens on its own figure's line
        if opener is not None:
            owner[i] = after if i >= opener else before
        else:
            owner[i] = before if (i - anchors[before]) < (anchors[after] - i) else after
    out = []
    for k, a in enumerate(anchors):
        mine = [items[i] for i in range(len(items)) if owner[i] == k]
        n = next((it["n"] for it in mine if it["n"] is not None), None)
        out.append(Row(page, " ".join(it["name"] for it in mine if it["name"]), items[a]["amount"],
                       " ".join(it["dates"] for it in mine if it["dates"]),
                       next((it["yes_no"] for it in mine if it["yes_no"]), ""), n, "layout"))
    return out


def page_rows(lines: list, page: int, src: str) -> list:
    """One page's rows by the route its shape calls for; None when its
    cells and figures do not pair."""
    body, after_total = [], False
    for l in lines:
        if PRINTED_TOTAL.search(l):
            after_total = money(l[PRINTED_TOTAL.search(l).end():]) is None
            continue
        if after_total and MONEY_ONLY.match(l):
            after_total = False
            continue
        if l.strip():
            body.append(l)
            after_total = False
    if src == "text":
        got = _layout(body, page)
    elif sum(1 for l in body if l.count("|") >= 3 and MONEY.search(l)) >= 1:
        got = _table(body, page)
    elif sum(1 for l in body if NUMBERED.match(l)) >= 2:
        got = _numbered(body, page)
    elif any((c := _closer(l.strip())) and c[0].strip() and not MONEY_ONLY.match(l) for l in body if not _furniture(l)):
        got = _inline(body, page)
    else:
        got = _stacked(body, page)
    if got is None:
        return None
    got = [r for r in got if r.amount and not POINTER.search(r.cell)]
    # a last figure with no cell that equals the page's rows above it is the filer's page subtotal
    if len(got) > 1 and not got[-1].cell.strip() and abs(got[-1].amount - sum(r.amount for r in got[:-1])) < CENT:
        got = got[:-1]
    out = []
    for r in got:
        r.read_from = src
        if not r.cell.strip():                  # the same donor's next dated donation
            if not out:
                continue                        # nobody above it on this page: the part's total refuses the loss
            r.cell, r.n = out[-1].cell, out[-1].n
        out.append(r)
    return out


def rows(texts: dict, src: dict, heading, end, letter: str):
    """(rows, printed_total, problems) for one part of a return."""
    lines = region(texts, heading, end)
    total = printed_total(lines, letter)
    out, problems = [], []
    for p in sorted({p for p, _ in lines}):
        got = page_rows([l for q, l in lines if q == p], p, src.get(p, "pixels"))
        if got is None:
            problems.append(f"page {p}: the cells and the figures do not pair (a row left unfinished, or the page read column by column)")
            continue
        out += got
    return out, total, problems
