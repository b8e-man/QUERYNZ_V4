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
TABLE_START = re.compile(r"^\s*(?:\|\s*)*(?:donor.?s?\s+name|name\s+and\s+(?:street\s+)?address\s+of|lender.?s?\s+name)", re.I)
ROW_NUMBER = re.compile(r"^\s{0,3}(\d{1,3})(?=\s|$)")     # the form prints it at the margin; a wrapped address is indented further
NUMBERED = re.compile(r"^\s*(\d{1,3})\.\s+(.*)$")
DATE_HEAD = re.compile(r"Date\s+donation|aggregated\s+donations|dd/mm/yyyy|Date\s+(?:of\s+)?(?:the\s+)?loan", re.I)
#: a donor's own subtotal under its dated rows (`Jane Doe  Aggregated total  $ 24,150.00`)
SUBTOTAL = re.compile(r"\baggregated\s+total\W*$", re.I)
#: a row that points at an attached schedule carries the schedule's total, not a donor
POINTER = re.compile(r"\bsee\s+(?:the\s+)?(?:attach(?:ed|ment)|schedule|appendix|over|list|separate)", re.I)
CENT = 0.005
FULL_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/(?:\d{4}|\d{2})\b,?")    # with its year: a flat number `3/12` has none
RULE = re.compile(r"^[Il|!]$")    # a table rule the text layer kept as a letter
#: a figure printed with no cents (`150000`, `$ 12,500`): an amount only where the amount column puts it
WHOLE = re.compile(r"^\$?\s*(\d{1,3}(?:,\d{3})+|\d{3,7})$")
AMOUNT_HEAD = re.compile(r"\$0\.00|\(including\s+gst\)", re.I)
BARE_NUMBER = re.compile(r"^\s*\d{1,3}\s*$")
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
    subtotal: bool = False     # a donor's `Aggregated total` line: restates the rows above it, never a row


def money(s: str):
    ms = list(MONEY.finditer(s or ""))
    if not ms:
        return None
    m = ms[-1]
    return float(m.group(1).replace(",", "") + "." + m.group(2))


def whole(s: str):
    """A figure with no cents as an amount, or None."""
    m = WHOLE.match((s or "").strip())
    return float(m.group(1).replace(",", "")) if m else None


#: the form's own column heading, as a table of the reader's carries it
FORM_HEAD = re.compile(r"donor.?s?\s+name\s+and\s+(?:street\s+)?address|name\s+and\s+(?:street\s+)?address\s+of|"
                       r"lender.?s?\s+name\s+and", re.I)
TR = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S | re.I)
CELL = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", re.S | re.I)


def unhtml(text: str) -> str:
    """A page the reader returned as an HTML table, as lines: one
    `| cell | … |` line per table row (the markdown table's shape), the
    text around the table kept as it is. Only a table under the form's own
    column heading is the form's: a filer's own breakdown (one line per
    dated payment beside a donor's total) restates rows the form already
    has, and is left as the one line it was. A page with no table is
    unchanged."""
    if not re.search(r"<tr\b", text or "", re.I):
        return text
    def row(m):
        cells = [" ".join(re.sub(r"<[^>]+>", " ", c).split()) for c in CELL.findall(m.group(1))]
        return "\n| " + " | ".join(cells) + " |\n"
    out = "\n".join(re.sub(r"</?(?:table|thead|tbody|tfoot)\b[^>]*>", "\n", TR.sub(row, text), flags=re.I).splitlines())
    return out if FORM_HEAD.search(out) else text


def region(texts: dict, heading, end) -> list:
    """The lines of one part's table, in page order: [(page, line)]. The
    form's instructions between a heading and the table's column headings
    are dropped, its printed total kept."""
    out, state = [], "off"
    for p in sorted(texts):
        lines = unhtml(texts[p] or "").splitlines()
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
        while len(cells) > 1 and not cells[-1]:           # an empty column after the figure
            cells.pop()
        amount = (money(cells[-1]) if money(cells[-1]) is not None else whole(cells[-1])) if cells else None
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
    """The page reader's list, each row under its printed number (`3. NO`,
    `3. $ 5,000.00`), or a numbered name line with the rest of its row on
    the unnumbered lines below it (the address, the date, Yes/No, the
    figure), which are that row's until the next number. A figure with no
    cents counts only after the row's Yes/No, as in `_stacked`. A row given
    two figures is refused (None): which one is its own is a guess."""
    by = {}
    order = []
    n = None
    for line in lines:
        m = NUMBERED.match(line)
        if m:
            if _furniture(m.group(2)):
                continue
            n, body = int(m.group(1)), m.group(2).strip()
        else:
            body = line.strip()
            if n is None or not body or _furniture(body):
                if n is None and body and not _furniture(body) and MONEY_ONLY.match(body) and money(body):
                    return None                 # a figure above the first number: whose is it
                continue
        if n not in by:
            by[n] = {"cell": [], "amount": None, "dates": [], "yes_no": ""}
            order.append(n)
        row = by[n]
        closer = None if MONEY_ONLY.match(body) else _closer(body)
        figure = money(body) if MONEY_ONLY.match(body) else (whole(body) if (not m and row["yes_no"]) else None)
        if figure is not None:
            if row["amount"] and figure:
                return None
            row["amount"] = figure or row["amount"]
        elif closer and closer[0].strip():         # the whole row on its numbered line: `3. name, address 2/4/19 NO $ 4,025.00`
            if row["amount"]:
                return None
            text, row["amount"] = closer
            yn = re.search(r"(?:^|\s)(yes|no)\s*$", text, re.I)
            if yn:
                row["yes_no"], text = yn.group(1), text[:yn.start()]
            row["dates"] += [d.group(0) for d in DATE.finditer(text)]
            row["cell"].append(_cell_words(text))
        elif YESNO.match(body):
            row["yes_no"] = body
        elif DATE.fullmatch(body.split(",")[0].strip()):
            row["dates"].append(body)
        else:
            row["cell"].append(body)
    got = [Row(page, "\n".join(by[n]["cell"]), by[n]["amount"], " ".join(by[n]["dates"]), by[n]["yes_no"], n, "numbered")
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
        yn = re.match(r"^(yes|no)\s+(\S.*)$", s, re.I)          # `No 35000`: the Yes/No and the figure on one line
        if yn and (MONEY_ONLY.match(yn.group(2)) or whole(yn.group(2)) is not None):
            pending["yes_no"], s = yn.group(1), yn.group(2)
        figure = money(s) if MONEY_ONLY.match(s) else (whole(s) if pending["yes_no"] else None)
        if MONEY_ONLY.match(s) or figure is not None:
            if not figure:
                continue
            if not pending["cell"]:
                return None
            out.append(Row(page, "\n".join(pending["cell"]), figure, " ".join(pending["dates"]), pending["yes_no"],
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
    and its numbers do not climb. A number standing alone on its line is an
    empty row of the form, or a number printed beside its cell; where a
    scanner's text layer misread one (`64` between `53` and `56`) the
    margin is measured without them, and the alone numbers are then no row's."""
    found = [(k, m.start(1), m.end(1), int(m.group(1))) for k, l in enumerate(lines) if (m := ROW_NUMBER.match(l))]
    best = set()
    for edge in (1, 2):                         # numbers set flush left, or right-aligned (`9` under `10`)
        for x in {f[edge] for f in found}:
            at = [(f[0], f[3]) for f in found if x <= f[edge] <= x + 1]      # a column's width of drift (` 1` over `2`)
            for keep in (at, [a for a in at if not BARE_NUMBER.match(lines[a[0]])]):
                ns = [n for _, n in keep]
                if all(b > a for a, b in zip(ns, ns[1:])):
                    if len(keep) > len(best):
                        best = {k for k, _ in keep}
                    break
    return best


def _items(lines, page) -> list:
    """One page of the text layer as items: per line, its printed row
    number, the name-and-address text, the dates, Yes/No and the amount."""
    date_x = amount_x = None
    for line in lines:
        m = DATE_HEAD.search(line)
        if m and (date_x is None or m.start() < date_x):
            date_x = m.start()
        m = AMOUNT_HEAD.search(line)
        if m and (amount_x is None or m.start() > amount_x):
            amount_x = m.start()
    edge = (date_x - 10) if date_x and date_x > 40 else DONOR_COLUMN    # the dates sit a little left of their heading
    lines = [l for l in lines if l.strip() and not _furniture(l)]
    numbered = _row_numbers(lines)
    items = []
    for k, line in enumerate(lines):
        if k not in numbered and BARE_NUMBER.match(line):
            continue                            # an empty row whose printed number the text layer misread
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
            elif amount_x is not None and seg.start() >= max(edge, amount_x - 10) and whole(t) is not None:
                amount = whole(t)               # a figure with no cents, in the amount column
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
        items.append({"n": n, "name": " ".join(name), "dates": " ".join(dates), "yes_no": yes_no, "amount": amount,
                      "page": page})
    return items


def _opener(items, j):
    """The line a row opens on, given the line with its printed number: the
    line above when the number stands alone in the middle of its cell, the
    name over it and the address under it."""
    def text_only(i):
        return 0 <= i < len(items) and items[i]["name"] and items[i]["n"] is None \
            and not items[i]["dates"] and not items[i]["amount"]
    if not items[j]["name"] and text_only(j - 1) and text_only(j + 1):
        return j - 1
    return j


def _layout(lines, page, carry=()):
    """The text layer, `pdftotext -layout`: (rows | None, tail). `tail` is
    the items of a row whose figure is not on this page (the row runs over
    the page break), for the next page to finish; `carry` is the tail the
    page before left. A carried row is finished only by a page whose lines
    above its first figure name nobody: a second name there would leave
    one of the two rows without its figure."""
    own = _items(lines, page)
    items = list(carry) + own
    anchors = [i for i, it in enumerate(items) if it["amount"]]
    if carry and (not anchors or any(it["name"] for it in items[len(carry):anchors[0]])):
        return None, []
    if not anchors:
        return [], []
    if len(anchors) > 2 and items[anchors[-1]]["n"] is None and \
            abs(items[anchors[-1]]["amount"] - sum(items[a]["amount"] for a in anchors[:-1])) < CENT:
        anchors = anchors[:-1]          # the filer's page subtotal under the table: it owns no line
    last = anchors[-1]
    # after the page's last figure only the end of that row's address; a numbered line, or a name
    # further down, opens a row whose figure is not on this page
    tail_at = next((j for j in range(last + 1, len(items)) if items[j]["n"] is not None), None)
    if tail_at is not None:
        tail_at = _opener(items, tail_at)
    else:
        tail_at = next((j for j in range(last + 3, len(items)) if items[j]["name"]), None)
    tail = []
    if tail_at is not None and any(it["name"] for it in items[tail_at:]):
        tail = items[tail_at:]
        items = items[:tail_at]
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
            owner[i] = before
            continue
        gap = range(anchors[before] + 1, anchors[after])
        opener = next((j for j in gap if items[j]["n"] is not None), None)
        if opener is None and items[anchors[after]]["n"] is not None and items[anchors[after]]["name"]:
            opener = anchors[after]                 # the next row opens on its own figure's line
            above = items[anchors[after] - 1]
            if anchors[after] - 1 > anchors[before] and above["name"] and above["dates"] and \
                    not items[anchors[after]]["dates"] and items[anchors[before]]["dates"]:
                opener -= 1     # unless its date, and the name beside it, sit on the line above: `Name … 04/03/22`
                                # over `10  Auckland 1010 … $ 100,000.00`, the row above dated on its own line
        if opener is not None:
            owner[i] = after if i >= opener else before
        else:
            owner[i] = before if (i - anchors[before]) < (anchors[after] - i) else after
    out = []
    for k, a in enumerate(anchors):
        mine = [items[i] for i in range(len(items)) if owner[i] == k]
        n = next((it["n"] for it in mine if it["n"] is not None), None)
        out.append(Row(page, "\n".join(it["name"] for it in mine if it["name"]), items[a]["amount"],
                       " ".join(it["dates"] for it in mine if it["dates"]),
                       next((it["yes_no"] for it in mine if it["yes_no"]), ""), n, "layout"))
    return out, tail


def page_rows(lines: list, page: int, src: str, carry=()):
    """One page's rows by the route its shape calls for: (rows | None,
    tail). None when its cells and figures do not pair; `tail` is a text
    page's unfinished last row (see `_layout`)."""
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
    tail = []
    if src == "text":
        got, tail = _layout(body, page, carry)
    elif sum(1 for l in body if l.count("|") >= 3 and MONEY.search(l)) >= 1:
        got = _table(body, page)
    elif sum(1 for l in body if NUMBERED.match(l)) >= 2:
        got = _numbered(body, page)
    elif any((c := _closer(l.strip())) and c[0].strip() and not MONEY_ONLY.match(l) for l in body if not _furniture(l)):
        got = _inline(body, page)
    else:
        got = _stacked(body, page)
    if got is None:
        return None, []
    got = [r for r in got if r.amount and not POINTER.search(r.cell)]
    # a last figure with no cell that equals the page's rows above it is the filer's page subtotal
    if len(got) > 1 and not got[-1].cell.strip() and abs(got[-1].amount - sum(r.amount for r in got[:-1])) < CENT:
        got = got[:-1]
    out = []
    for r in got:
        r.read_from = src
        if SUBTOTAL.search(" ".join(r.cell.split())):
            r.subtotal = True
            out.append(r)
            continue
        if not r.cell.strip():                  # the same donor's next dated donation
            if not out:
                continue                        # nobody above it on this page: the part's total refuses the loss
            r.cell, r.n = out[-1].cell, out[-1].n
        out.append(r)
    return out, tail


def rows(texts: dict, src: dict, heading, end, letter: str):
    """(rows, printed_total, problems) for one part of a return. A text
    page's row whose figure is on the next page is carried there (the next
    page of the part, read from text too); one left unfinished is a problem."""
    lines = region(texts, heading, end)
    total = printed_total(lines, letter)
    out, problems = [], []
    pages_ = sorted({p for p, _ in lines})
    carry = []
    for i, p in enumerate(pages_):
        how = src.get(p, "pixels")
        if carry and how != "text":
            problems.append(f"page {pages_[i - 1]}: a row runs over the page break onto a page not read from text")
            carry = []
        got, tail = page_rows([l for q, l in lines if q == p], p, how, carry)
        if got is None:
            problems.append(f"page {p}: the cells and the figures do not pair (a row left unfinished, or the page read column by column)"
                            if not carry else f"page {p}: a row carried over the page break from page {pages_[i - 1]} "
                                              "does not meet its figure")
            carry = []
            continue
        if tail and (i + 1 == len(pages_) or pages_[i + 1] != p + 1):
            problems.append(f"page {p}: the cells and the figures do not pair (a row left unfinished, or the page read column by column)")
            carry = []
            continue
        out += got
        carry = tail
    return _subtotals(out, problems), total, problems


def _subtotals(found: list, problems: list) -> list:
    """The rows with each donor's `Aggregated total` line taken out, where it
    equals, to the cent, the rows since the one before it (it may sit on
    the next page). One that does not is a problem: a row above it was
    misread, or it is not a subtotal."""
    out, since = [], []
    for r in found:
        if not r.subtotal:
            out.append(r)
            since.append(r)
            continue
        if not since or abs(sum(x.amount for x in since) - r.amount) >= CENT:
            problems.append(f"page {r.page}: an aggregated total of {r.amount:,.2f} is not the "
                            f"{sum(x.amount for x in since):,.2f} of the {len(since)} rows above it")
        since = []
    return out
