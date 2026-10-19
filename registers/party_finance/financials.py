"""The Commission's roster of party financial statements, read (contract:
the reader; profile `ec-financial-statements-listing`, proposed in
`profile-proposed.jsonl`).

Registered parties have filed annual financial statements with the
Commission since the 2023 financial year (Electoral Act 1993, s 210F on).
The Commission lists them on one page, one table per year of filing, each
under a heading `<year> Financial Statements`: party (with the link to each
statement it filed, an amended or audited one beside the first) | balance
date | deadline for filing | date filed | audit requirement. The page
prints no figures: the figures are in the statements, which this roster
links, and reading them is separate work.

`Date filed` is free text where the filing was partial or amended
("Statement 30/06/25, amended statement and audit report 18/08/25"); it is
kept as printed, and read as a date only when it is one. Dates are read by
`keys.dates.filed_date`, the one reading of a filed date; a shape it does
not read leaves the date empty and the printed text standing. A trailing
`*` or `**` is the page's footnote mark, kept as printed. Deterministic: a
regex over captured HTML, no model.

    read(html_bytes) -> Reading(rows, skipped)
"""
import re
from dataclasses import dataclass, field

from keys.dates import filed_date
from registers.party_finance.listing import BASE, Link, links, text

READER = "registers.party_finance.financials 1"
MODEL = "html"
PROFILE = "ec-financial-statements-listing"

_TABLE = re.compile(r"<table\b.*?</table>", re.S | re.I)
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.S | re.I)
_YEAR = re.compile(r"(\d{4})\s+Financial Statements", re.I)
_SIZE = re.compile(r"[\[(]\s*(?:PDF,?\s*)?[\d.,]+\s*[KM]B\s*[\])]", re.I)
_MARK = re.compile(r"\s*(\*+)\s*$")
COLUMNS = ("balance_date", "deadline", "date_filed", "audit_requirement")


@dataclass
class Row:
    filed_year: int        # the year the table is headed with
    ordinal: int           # the row's place in its table, from 1
    label: str             # the party as printed, sizes, notes and marks off
    note: str              # a bracketed note after the name ('audited'), verbatim
    mark: str
    printed: dict          # column → the cell as printed
    dates: dict            # balance_date, deadline, date_filed → ISO or None
    links: list = field(default_factory=list)


@dataclass
class Reading:
    rows: list = field(default_factory=list)
    skipped: list = field(default_factory=list)       # (table year, ordinal, why)
    tables: list = field(default_factory=list)        # the years, in page order


def _label(cell_html: str) -> tuple:
    own = links(cell_html)
    first = own[0].text if own else text(cell_html)
    first = _SIZE.sub(" ", first)
    t = " ".join(first.split())
    m = _MARK.search(text(cell_html))
    mark = m.group(1) if m else ""
    t = t.rstrip("* ").strip()
    note = ""
    n = re.search(r"\(([^)]*\b(?:amended|audited)\b[^)]*)\)\s*$", t, re.I)    # '(TOP)' is the name's own
    if n:
        note, t = n.group(1).strip(), t[:n.start()].strip()
    return t, note, mark


def _iso(printed: str):
    d = filed_date(printed.replace("*", ""))
    return d.isoformat() if d else None


def read(data: bytes) -> Reading:
    page = data.decode("utf-8", errors="replace")
    out = Reading()
    pos = 0
    for t in _TABLE.finditer(page):
        years = _YEAR.findall(text(page[pos:t.start()]))
        pos = t.end()
        if not years:
            out.skipped.append((None, 0, "a table with no '<year> Financial Statements' heading before it"))
            continue
        year = int(years[-1])
        out.tables.append(year)
        n = 0
        for row_html in _ROW.findall(t.group(0)):
            cells = _CELL.findall(row_html)
            texts = [text(c) for c in cells]
            if not any(texts) or texts[0].lower() == "party":
                continue
            n += 1
            if len(cells) != 1 + len(COLUMNS):
                out.skipped.append((year, n, f"row {n} ({texts[0][:40]!r}): {len(cells)} cells, not {1 + len(COLUMNS)}"))
                continue
            label, note, mark = _label(cells[0])
            if not label:
                out.skipped.append((year, n, f"row {n}: no party named"))
                continue
            printed = dict(zip(COLUMNS, texts[1:]))
            dates = {k: _iso(printed[k]) for k in ("balance_date", "deadline")}
            filed = printed["date_filed"]
            dates["date_filed"] = _iso(filed) if re.fullmatch(r"[\d/.\-A-Za-z ]{6,12}\**", filed or "") else None
            out.rows.append(Row(year, n, label, note, mark, printed, dates, links(cells[0])))
    return out
