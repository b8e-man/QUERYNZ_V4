"""A release's tables, found by their labels in a workbook's cells. Both
publishers' workbooks are read by this one walk; their profiles say how
each lays its table out (`profile-proposed.jsonl`).

A sheet may hold more than one table: the ministers' release for a quarter
that spans a change of government prints one table per government, each
under its own title row. So a sheet is walked top to bottom:

  title row    one text cell naming the expenses and the period ("…
               EXPENSES FROM 1 OCTOBER TO 31 DECEMBER 2025"); opens a table
  header row   the column headings: a names column ("Member", "Member of
               the Executive", "Minister…", or "Party" where the names sit
               under it) and three or more figure headings. A second header
               row beneath (the Parliamentary Service's "Wellington | Non
               Wellington | Air | Surface") is joined to the first, so a
               heading is its path: "Accommodation / Wellington"
  member row   a name and at least one figure
  party row    a name and no figure: the party the rows below belong to
  total row    a name carrying the word "total": a party's or the table's
               own printed total, checked, never published as a member
  notes        from a "Notes" line or a footnote "(A) …" to the next table

The total column is the first heading naming a total ("Grand Total",
"Subtotal Parliamentary Service", "Sub Total Internal Costs"): columns to
its left are the categories it adds up, columns to its right are money it
does not include (the Inter-Parliamentary Office's travel; Cabinet-approved
international travel), held beside it and never added in.

    read(cells, sheet_name, sheet_index)   [Table…], [(ref, reason)] skipped
    number(text)                           (value or None, marker or None)
    period(text)                           (start, end) dates or None
"""
import calendar
import datetime as dt
import difflib
import re
from dataclasses import dataclass, field

from registers.expenses.sheet import grid

MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december")
_FIGURE_WORDS = re.compile(r"accommodation|travel|total|wellington|transport|air\b|surface|international|domestic|vip\b", re.I)
_NAMES_HEAD = re.compile(r"^(member|minister|name)\b|member of the executive", re.I)
_TOTAL_HEAD = re.compile(r"grand total|sub ?total", re.I)
_TOTAL_ROW = re.compile(r"\btotals?\b", re.I)
_NOTE_ROW = re.compile(r"^\s*(notes?\s*:?\s*$|\(?[a-z0-9]{1,2}\)\s|\*)", re.I)
_TITLE = re.compile(r"expense", re.I)
_MARK = re.compile(r"\(\s*([A-Za-z0-9]{1,2})\s*\)")
_NIL = ("-", "–", "—", "nil", "")


@dataclass
class Column:
    col: int
    heading: str                 # the heading path as printed, whitespace folded
    role: str = "category"       # category | total | outside


@dataclass
class Line:
    row: int
    kind: str                    # member | total
    name: str                    # as printed (whitespace folded)
    party_printed: str = None    # the party cell on this row, where the table has a party column
    party: str = None            # the party heading or cell this row sits under
    marks: list = field(default_factory=list)          # footnote markers on the row ("C", "3")
    figures: dict = field(default_factory=dict)        # col → (value or None, printed, ref)


@dataclass
class Table:
    sheet: str
    sheet_index: int             # from 1: the page of the row contract
    title: str = None
    title_ref: str = None
    period_printed: str = None
    period: tuple = None         # (start, end) from the title, or None
    header_row: int = None
    names_col: int = None
    party_col: int = None
    columns: list = field(default_factory=list)
    lines: list = field(default_factory=list)
    notes: list = field(default_factory=list)          # [(ref, text)]

    @property
    def total_col(self):
        return next((c.col for c in self.columns if c.role == "total"), None)

    def members(self):
        return [ln for ln in self.lines if ln.kind == "member"]


def fold(s) -> str:
    return " ".join(str(s or "").split())


def number(text):
    """A figure cell's text → (value or None, marker or None). A dash or a
    blank is nil (zero), as the tables print it; a figure in brackets is
    negative; a footnote marker beside the figure is kept apart ("1,391
    (D)"). Words ("Allocated Crown Owned Property", "N/A") are no figure."""
    s = fold(text)
    marks = _MARK.findall(s)
    core = _MARK.sub("", s).replace(",", "").replace("$", "").strip().lstrip("*").strip()
    mark = marks[0] if marks else None
    if core.lower() in _NIL:
        return 0.0, mark
    core = re.sub(r"^-\s+(?=\d)", "-", core)
    neg = core.startswith("(") and core.endswith(")")
    try:
        v = float(core.strip("()"))
    except ValueError:
        return None, mark
    return (-v if neg else v), mark


def _month(word: str):
    w = word.lower()
    for i, m in enumerate(MONTHS, 1):
        if w == m or (len(w) >= 3 and m.startswith(w)) or (w in ("sept",) and m == "september"):
            return i
    close = difflib.get_close_matches(w, MONTHS, n=1, cutoff=0.7)   # "APIL" (2024's title)
    return MONTHS.index(close[0]) + 1 if close else None


_END = r"(?:(\d{1,2})\s+)?([A-Za-z]{3,9})\.?(?:\s+((?:19|20)\d{2}))?"
_RANGE = re.compile(r"(?:(\d{1,2})\s+)?([A-Za-z]{3,9})\.?(?:\s+((?:19|20)\d{2}))?\s*(?:-|–|to)\s*" + _END + r"(?!\w)",
                    re.I)


def period(text):
    """'FROM 1 OCTOBER 2019-31 DECEMBER 2019', '1 APIL TO 30 JUNE 2024',
    'April - June 2022', '27 NOVEMBER TO 31 DECEMBER 2023' → (start, end).
    A month with no day runs from its first day to its last. Tried at every
    word, so "Disclosure - October to December" finds its months."""
    text = text or ""
    for w in re.finditer(r"\b\w", text):
        m = _RANGE.match(text, w.start())
        if not m:
            continue
        d1, m1, y1, d2, m2, y2 = m.groups()
        mm1, mm2 = _month(m1), _month(m2)
        if not (mm1 and mm2) or not (y1 or y2):
            continue
        y2 = int(y2 or y1)
        y1 = int(y1) if y1 else (y2 if mm1 <= mm2 else y2 - 1)
        try:
            start = dt.date(y1, mm1, int(d1) if d1 else 1)
            end = dt.date(y2, mm2, int(d2) if d2 else calendar.monthrange(y2, mm2)[1])
        except ValueError:
            continue
        if start <= end and (end - start).days < 400:
            return start, end
    return None


def _texts(row: dict) -> dict:
    return {c: fold(cell.text) for c, cell in row.items() if isinstance(cell.value, str) and fold(cell.text)}


def _is_title(row: dict) -> bool:
    t = _texts(row)
    return len(t) == 1 and bool(_TITLE.search(next(iter(t.values())))) and period(next(iter(t.values()))) is not None


def _header(row: dict):
    """(names col, party col or None, {col: heading}) when this row is a header, else None."""
    t = _texts(row)
    if len(t) < 4 or any(isinstance(c.value, float) for c in row.values()):
        return None
    figures = {c: h for c, h in t.items() if _FIGURE_WORDS.search(h)}
    if len(figures) < 3:
        return None
    names = next((c for c, h in sorted(t.items()) if _NAMES_HEAD.search(h) and c not in figures), None)
    party = next((c for c, h in sorted(t.items()) if h.lower().strip(" :") == "party"), None)
    if names is None:
        names, party = party, None                        # the names sit under "Party"
    if names is None:
        return None
    return names, party, {c: h for c, h in t.items() if c > max(names, party or 0)}


def read(cells: list, sheet_name: str, sheet_index: int) -> tuple:
    g = grid(cells)
    rows = sorted(g)
    tables, skipped = [], []
    cur, title, in_notes, party, i = None, None, False, None, 0
    while i < len(rows):
        r = rows[i]
        row = g[r]
        if _is_title(row):
            title = next(iter(row[c] for c in sorted(row) if isinstance(row[c].value, str) and fold(row[c].text)))
            i += 1
            continue
        h = _header(row)
        if h:
            names, pcol, heads = h
            nxt = g.get(rows[i + 1]) if i + 1 < len(rows) else None
            sub = {}
            if nxt and not any(isinstance(c.value, float) for c in nxt.values()):
                # cells left of the names column on the second row (2024-25's hidden "New Cost Centre | Name"
                # helper columns) are not headings of this table and are not read
                st = {c: h for c, h in _texts(nxt).items() if c > max(names, pcol or 0)}
                if st and any(_FIGURE_WORDS.search(h) for h in st.values()):
                    sub = st
            cols = sorted(set(heads) | set(sub))
            columns, top = [], None
            for c in cols:
                if c in heads:
                    top = heads[c]
                elif top is None:
                    continue
                path = [heads[c] if c in heads else top]
                if c in sub and fold(sub[c]).lower() != fold(path[0]).lower():
                    path.append(sub[c])
                columns.append(Column(c, " / ".join(fold(p) for p in path)))
            # a heading carried right from a merged top cell applies only where the second row names the column
            columns = [x for x in columns if x.col in heads or x.col in sub]
            seen_total = False
            for x in columns:
                if seen_total:
                    x.role = "outside"
                elif _TOTAL_HEAD.search(x.heading) and not x.heading.lower().startswith("inter-parliamentary"):
                    x.role, seen_total = "total", True
                elif x.heading.lower().startswith("inter-parliamentary"):
                    x.role = "outside"
            cur = Table(sheet_name, sheet_index, title=fold(title.text) if title else None,
                        title_ref=title.ref if title else None, header_row=r, names_col=names, party_col=pcol,
                        columns=columns)
            cur.period_printed = cur.title
            cur.period = period(cur.title) if cur.title else None
            tables.append(cur)
            title, in_notes, party = None, False, None
            i += 2 if sub else 1
            continue
        if cur is None:
            i += 1
            continue
        fig_cols = {x.col for x in cur.columns}
        name_cell = row.get(cur.names_col)
        name = fold(name_cell.text) if name_cell is not None and isinstance(name_cell.value, str) else ""
        pcell = row.get(cur.party_col) if cur.party_col else None
        ptext = fold(pcell.text) if pcell is not None and isinstance(pcell.value, str) else ""
        label = name or ptext
        figs = {c: row[c] for c in fig_cols if c in row and fold(row[c].text) != ""}
        has_figure = any(number(cell.text)[0] is not None or isinstance(cell.value, float) for cell in figs.values())
        if label and _NOTE_ROW.match(label) and not has_figure:
            in_notes = True
        if in_notes and not (label and _TOTAL_ROW.search(label) and has_figure):
            text = " ".join(fold(row[c].text) for c in sorted(row) if fold(row[c].text))
            if text:
                cur.notes.append((row[min(row)].ref, text))
            i += 1
            continue
        if not label:
            if has_figure and any(number(cell.text)[0] not in (0.0, None) for cell in figs.values()):
                skipped.append((row[min(figs)].ref, "figures on a row that names nobody"))
            i += 1
            continue
        if not has_figure and not figs:
            if ptext and not name and cur.party_col:
                party = ptext                               # a party cell alone, on its own line
            elif name and not ptext:
                party = name                                # a party heading row ("National")
            else:
                skipped.append((row[min(row)].ref, f"{label!r}: a name and no figure"))
            i += 1
            continue
        name_in_party_col = bool(ptext and not name and not _TOTAL_ROW.search(ptext))
        if name_in_party_col:
            # 2012-14's ministers' tables list members outside the parties (international travel alone)
            # below "Total All Parties" with the name in the party column: a member, party not stated
            ptext, party = "", None
        elif ptext and cur.party_col and not _TOTAL_ROW.search(ptext):
            party = ptext
        marks = []
        for c, cell in row.items():
            if c not in fig_cols and c not in (cur.names_col, cur.party_col):
                marks += _MARK.findall(fold(cell.text))
        marks += _MARK.findall(label)
        line = Line(r, "total" if _TOTAL_ROW.search(label) else "member", label,
                    party_printed=ptext or None, party=party, marks=marks)
        for c in sorted(fig_cols):
            cell = row.get(c)
            if cell is None:
                continue
            if isinstance(cell.value, float):
                line.figures[c] = (cell.value, cell.text, cell.ref)
            elif cell.formula and cell.value in (None, ""):
                line.figures[c] = (None, f"={cell.formula}", cell.ref)
            else:
                v, mk = number(cell.text)
                line.figures[c] = (v, fold(cell.text), cell.ref)
                if mk:
                    line.marks.append(mk)
        cur.lines.append(line)
        if line.kind == "total":
            party = None                                    # every block names its party again; rows after a
                                                            # "Total All Parties" belong to none the table states
        i += 1
    return tables, skipped
