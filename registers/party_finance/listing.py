"""The Commission's own tables of what was spent, read (contract: the
reader; profiles `ec-party-expenses-listing` and
`ec-promoter-expenses-listing`, proposed in `profile-proposed.jsonl`).

One table per page, one row per filer. The page is the Commission
transcribing the returns it links, so it is the outside figure every
reading of a return is checked against, and a second opinion, not an
authority: it has printed Part A alone as two parties' 2020 totals and
ACT's 2020 total as `$108,2166.64` (facts and traps: Electoral Commission
forms).

  party expenses, 2023    party (the link to its return) | limit | total expenses | allocation |
                          allocation spent | audit report
  party expenses, 2020    party | limit | total expenses | allocation | allocation spent | the link
  promoter expenses, 2023 promoter (the link) | election expenses
  promoter expenses, 2020 promoter | election | cannabis referendum | end-of-life referendum | the link

A row may link two returns, an amendment and its original; the link text
says which ("(amended)"), and that statement is read, never inferred. Each
link's URL is joined to a held document through the old job's manifest
(capture.manifest), never through a file name.

Money is read as printed: `NIL` is a figure, zero; `N/A` says there was no
allocation and is no figure; a footnote star is kept in the printed text
and taken off the figure. Commas are dropped, not checked, so ACT's
misplaced comma reads as the digits printed; the printed text stays
beside every figure. Deterministic: a regex over captured HTML, no model.

    read_expenses(html_bytes, year)   -> Reading(rows, skipped)
    read_promoters(html_bytes, year)  -> Reading(rows, skipped)
"""
import html as _html
import re
from dataclasses import dataclass, field

BASE = "https://elections.nz"
READER = "registers.party_finance.listing 1"
MODEL = "html"
EXPENSES_PROFILE = "ec-party-expenses-listing"
PROMOTERS_PROFILE = "ec-promoter-expenses-listing"

_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL = re.compile(r"<t([hd])[^>]*>(.*?)</t[hd]>", re.S | re.I)
_HREF = re.compile(r"""<a\b[^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>""", re.S | re.I)
_DOC = re.compile(r"\.(pdf|jpe?g|png)$", re.I)
_TABLE = re.compile(r"<table\b.*?</table>", re.S | re.I)
#: what the party cell carries after the name: the file's size, the word PDF
_SIZE = re.compile(r"\[?\s*(?:PDF,?\s*)?\d+(?:[.,]\d+)?\s*[KM]B\s*\]?", re.I)
_NOTE = re.compile(r"\(([^)]*)\)\s*$")


@dataclass
class Link:
    text: str            # the link text as printed, whitespace folded
    url: str             # absolute
    amended: bool        # the link text says "amended"


@dataclass
class Row:
    ordinal: int                 # the row's place in the table, data rows from 1
    label: str                   # the filer as the table names it, notes taken off
    note: str                    # a bracketed note after the name, verbatim ('' when none)
    printed: list                # every cell after the first, as printed
    figures: dict                # column → figure (float, 0.0 for NIL, None for no figure)
    links: list = field(default_factory=list)


@dataclass
class Reading:
    rows: list = field(default_factory=list)
    skipped: list = field(default_factory=list)      # (ordinal or 0, why)
    columns: tuple = ()


def text(cell_html: str) -> str:
    return " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", cell_html or "")).split())


def money(printed: str):
    """(figure, ok). NIL and Nil are zero; N/A and an empty cell are no
    figure; a star is a footnote mark. ok is False when the cell is none of
    these and carries no readable amount."""
    s = (printed or "").replace("*", "").strip()
    if not s or s.upper() in ("N/A", "NA", "-", "—"):
        return None, True
    if s.upper().startswith("NIL"):
        return 0.0, True
    digits = re.sub(r"[^0-9.]", "", s)
    if not re.fullmatch(r"\d+(\.\d\d)?", digits or ""):
        return None, False
    return round(float(digits), 2), True


def links(row_html: str) -> list:
    """The documents a row links, in page order, one per URL. Two anchors
    to one URL (Te Pāti Māori 2023 prints its note across a line break) are
    one link, their texts joined."""
    out, seen = [], {}
    for href, inner in _HREF.findall(row_html):
        if not _DOC.search(href.split("?")[0]):
            continue
        url = href if href.startswith("http") else BASE + href
        t = text(inner)
        if url in seen:
            seen[url].text = (seen[url].text + " " + t).strip()
            seen[url].amended = "amended" in seen[url].text.lower()
            continue
        if not t:
            continue        # an anchor with no text is not the row's own (lesson: the first link…)
        seen[url] = Link(t, url, "amended" in t.lower())
        out.append(seen[url])
    return out


def label_of(first_cell_html: str) -> tuple:
    """(label, note). The 2023 tables print the name as the link, the
    original under the amendment; the 2020 tables print it as plain text and
    the link in a last cell. The label is the first cell's first link text,
    or the cell's text, with its size and its bracketed note taken off."""
    own = links(first_cell_html)
    first = own[0].text if own else text(first_cell_html)
    first = _SIZE.split(first)[0].strip()
    note = ""
    m = _NOTE.search(first)
    if m:
        note, first = m.group(1).strip(), first[:m.start()].strip()
    elif "(" in first and ")" not in first:        # the note runs into a second anchor
        first, note = (s.strip() for s in first.split("(", 1))
    return " ".join(first.split()).strip(" ,"), note


def _rows(data: bytes):
    page = data.decode("utf-8", errors="replace")
    tables = _TABLE.findall(page)
    if len(tables) != 1:
        raise ValueError(f"expected one table on the page, found {len(tables)}")
    for row_html in _ROW.findall(tables[0]):
        cells = [(tag.lower(), c) for tag, c in _CELL.findall(row_html)]
        yield row_html, cells


def _read(data: bytes, columns: tuple, header_word: str) -> Reading:
    out = Reading(columns=columns)
    n = 0
    for row_html, cells in _rows(data):
        texts = [text(c) for _, c in cells]
        # the 2020 tables open some rows with an empty cell
        while len(texts) > 1 and not texts[0]:
            texts, cells = texts[1:], cells[1:]
        if not any(texts):
            continue
        if any(tag == "th" for tag, _ in cells) or texts[0].lower().startswith(header_word):
            continue
        n += 1
        row_links = links(row_html)
        label, note = label_of(cells[0][1])
        printed = [t for t in texts[1:] if not re.fullmatch(r"\[?\s*(PDF,?\s*)?\d+(\.\d+)?\s*[KM]B\s*\]?", t, re.I)]
        if len(printed) != len(columns):
            out.skipped.append((n, f"row {n} ({label!r}) has {len(printed)} figure cells, not {len(columns)}: {printed}"))
            continue
        figures, bad = {}, []
        for col, cell in zip(columns, printed):
            if col == "audited":
                figures[col] = {"yes": True, "": None}.get(cell.lower(), None)
                continue
            figures[col], ok = money(cell)
            if not ok:
                bad.append(f"{col}={cell!r}")
        if bad:
            out.skipped.append((n, f"row {n} ({label!r}): unreadable {', '.join(bad)}"))
            continue
        if not label:
            out.skipped.append((n, f"row {n}: no filer named"))
            continue
        out.rows.append(Row(n, label, note, printed, figures, row_links))
    return out


EXPENSE_COLUMNS = {
    2023: ("expense_limit", "total_expenses", "allocation", "allocation_spent", "audited"),
    2020: ("expense_limit", "total_expenses", "allocation", "allocation_spent"),
}
PROMOTER_COLUMNS = {
    2023: ("election_expenses",),
    2020: ("election_expenses", "cannabis_referendum_expenses", "end_of_life_referendum_expenses"),
}


def read_expenses(data: bytes, year: int) -> Reading:
    if year not in EXPENSE_COLUMNS:
        raise ValueError(f"no party-expenses table shape known for {year}")
    return _read(data, EXPENSE_COLUMNS[year], "party")


def read_promoters(data: bytes, year: int) -> Reading:
    if year not in PROMOTER_COLUMNS:
        raise ValueError(f"no promoter-expenses table shape known for {year}")
    return _read(data, PROMOTER_COLUMNS[year], "registered promoter")


def rows_seen(data: bytes) -> int:
    """Data rows on the page by the plain count (a row with any text that is
    not a header): what rows read plus rows skipped must equal."""
    n = 0
    for _, cells in _rows(data):
        texts = [t for t in (text(c) for _, c in cells)]
        while len(texts) > 1 and not texts[0]:
            texts = texts[1:]
        if any(texts) and not any(tag == "th" for tag, _ in cells) \
                and not texts[0].lower().startswith(("party", "registered promoter")):
            n += 1
    return n
