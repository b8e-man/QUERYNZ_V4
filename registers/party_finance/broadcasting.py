"""The broadcasting allocation, read (contract: the reader; profile
`ec-broadcasting-allocation-page`, proposed in `profile-proposed.jsonl`).

The Commission allocates public money for election broadcasting to each
eligible party (Broadcasting Act 1989, Part 6), and varies the decision as
parties register or drop out. One page per general election, one table,
and the page is the document: the 2020 table has two rounds (the original
and the varied allocation), the 2023 table three (12 May, 1 August,
8 September). A `<thead>` names the rounds; a `<tfoot>` prints `TOTAL
allocated` and `TOTAL available` for each; the body is split by a
full-width row into parties eligible and parties not eligible.

Every round is a column of rows, and the page prints its own total for
each, so every column is scored against it: rows read and the total
printed must agree to the dollar, or the column publishes nothing. A blank
cell is no allocation in that round (the party was out by then), not
zero. A trailing `*` or `**` on a party is the page's footnote mark, kept
as printed. Deterministic: a regex over captured HTML, no model.

    read(html_bytes) -> Reading(rounds, rows, totals, skipped)
"""
import re
from dataclasses import dataclass, field

from registers.party_finance.listing import text

READER = "registers.party_finance.broadcasting 1"
MODEL = "html"
PROFILE = "ec-broadcasting-allocation-page"

_SECTION = {"thead": re.compile(r"<thead\b.*?</thead>", re.S | re.I), "tbody": re.compile(r"<tbody\b.*?</tbody>", re.S | re.I),
            "tfoot": re.compile(r"<tfoot\b.*?</tfoot>", re.S | re.I)}
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL = re.compile(r"<t[hd]([^>]*)>(.*?)</t[hd]>", re.S | re.I)
_MARK = re.compile(r"\s*(\*+)\s*$")


@dataclass
class Row:
    ordinal: int          # the party's place in the body, from 1
    label: str            # the party as printed, footnote mark off
    mark: str             # '*', '**' or ''
    eligible: bool        # under 'Parties eligible…' (True) or 'Parties not eligible…' (False)
    amounts: list         # one per round: whole dollars, or None for a blank cell
    printed: list


@dataclass
class Reading:
    rounds: list = field(default_factory=list)        # the round labels as printed
    rows: list = field(default_factory=list)
    totals: dict = field(default_factory=dict)        # 'allocated' | 'available' → [amount per round]
    printed_totals: dict = field(default_factory=dict)
    skipped: list = field(default_factory=list)       # (where, why)
    failed_rounds: list = field(default_factory=list) # round indexes whose rows do not add to the printed total


def dollars(printed: str):
    """(amount, ok): whole dollars; a blank cell is (None, True)."""
    s = (printed or "").strip()
    if not s:
        return None, True
    digits = re.sub(r"[^0-9]", "", s)
    if not digits or not re.fullmatch(r"\$?\s*[\d,]+", s):
        return None, False
    return int(digits), True


def _rows(section_html: str) -> list:
    return [[(attrs, text(c)) for attrs, c in _CELL.findall(r)] for r in _ROW.findall(section_html or "")]


def read(data: bytes) -> Reading:
    page = data.decode("utf-8", errors="replace")
    out = Reading()
    parts = {k: rx.findall(page) for k, rx in _SECTION.items()}
    if any(len(v) != 1 for v in parts.values()):
        raise ValueError(f"expected one thead, tbody and tfoot, found { {k: len(v) for k, v in parts.items()} }")
    head = [c for c in _rows(parts["thead"][0]) if any(t for _, t in c)]
    if len(head) != 1 or not head[0][0][1].lower().startswith("political party"):
        raise ValueError("the table's head does not name 'Political Party' and the rounds")
    out.rounds = [t for _, t in head[0][1:]]
    n = len(out.rounds)
    eligible, ordinal = None, 0
    for cells in _rows(parts["tbody"][0]):
        texts = [t for _, t in cells]
        if not any(texts):
            continue
        if len(cells) == 1 or "colspan" in cells[0][0].lower():
            low = texts[0].lower()
            eligible = False if "not eligible" in low else True if "eligible" in low else eligible
            continue
        ordinal += 1
        label, figures = texts[0], texts[1:]
        if len(figures) < n:
            figures = figures + [""] * (n - len(figures))       # a row the page closes early: its last rounds blank
        if len(figures) != n or eligible is None:
            out.skipped.append((f"row {ordinal}", f"{label!r}: {len(figures)} figure cells for {n} rounds, section {eligible}"))
            continue
        amounts, bad = [], []
        for cell in figures:
            a, ok = dollars(cell)
            amounts.append(a)
            if not ok:
                bad.append(cell)
        m = _MARK.search(label)
        mark = m.group(1) if m else ""
        label = label[:m.start()].strip() if m else label
        if bad or not label:
            out.skipped.append((f"row {ordinal}", f"{label!r}: unreadable {bad}"))
            continue
        out.rows.append(Row(ordinal, label, mark, eligible, amounts, figures))
    for cells in _rows(parts["tfoot"][0]):
        texts = [t for _, t in cells]
        key = texts[0].lower().replace("total", "").strip() if texts else ""
        if key in ("allocated", "available"):
            out.printed_totals[key] = texts[1:]
            out.totals[key] = [dollars(t)[0] for t in texts[1:]]
    allocated = out.totals.get("allocated") or []
    for i in range(n):
        s = sum(r.amounts[i] or 0 for r in out.rows)
        if i >= len(allocated) or allocated[i] is None or s != allocated[i] or out.skipped:
            out.failed_rounds.append(i)
    return out


_YEAR = re.compile(r"Past elections\s+(\d{4}) General Election", re.I)


def election_year(data: bytes):
    """The general election the page is about, from its own breadcrumb
    ('Past elections › 2023 General Election'); None when it states none."""
    years = set(_YEAR.findall(text(data.decode("utf-8", errors="replace"))))
    return int(years.pop()) if len(years) == 1 else None
