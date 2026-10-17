"""OCR text -> rows, without depending on a shape the model chose.

THE MISTAKE THIS REPLACES. The audit's parser anchored on the row number the
EC form prints in its first column — reasonable, because that is what makes a
row a row. But the number sits in a narrow grey column OUTSIDE the table's
ruled border, and a generative transcriber decides per page whether that is
part of the table. On National 2017 it kept the column on page 3 and dropped
it on page 2, same layout, same model, temperature 0. Anchoring on it
discarded twelve correctly-read rows and, across the corpus, 95.3% of
documents produced no rows at all.

So this parser anchors on what a data row ACTUALLY has: a money cell at the
end, and text before it. The row number is read WHEN PRINTED and left None
when not — never inferred, because an inferred number would defeat the
invariant that exists to notice the absence.
"""
from __future__ import annotations

import re

from .rows import Document, Row, date as read_date, money

#: "PART A: PARTY DONATIONS OF MORE THAN $15,000" — and the lowercase and
#: table-cell variants the model also emits.
PART = re.compile(r"\bPART\s+([A-G])\b\s*[:.]", re.I)

#: "TOTAL FOR PART A | $1,002,516.53" or "Total A $0.00"
TOTAL = re.compile(
    r"\bTOTALS?\s+(?:FOR\s+)?(?:PART\s+)?([A-G])\b[^\d$]*\$?\s*"
    r"(\d{1,3}(?:,\d{3})*|\d+)\.(\d{2})", re.I)

#: The RETURN's own total, from the summary on page 1, with the parts it
#: covers captured from the line itself: `Total Party Donations
#: (A + C + D + F + G) $1,500,307.55`. Ten spellings measured across the 107
#: party returns in scope on 2026-10-10 and 106 carry one — with and without
#: "Party Donations", with `$`, with `$ `, with `=`, with nothing, with `NIL`,
#: and with amounts that carry no thousands separators at all (NZ First's
#: amended return prints `1877416.69`).
#:
#: `(\s*A\s*\+` is load-bearing: the same page prints
#: `Total (H + I) $0.00` for party LOANS, which is not donations and must
#: never be read as this.
#:
#: THE LOOKAHEAD IS LOAD-BEARING TOO. The estate's other money patterns end
#: in a mandatory `\.(\d{2})`, which forces the alternation to backtrack onto
#: the whole number; cents are OPTIONAL here, so without `(?![\d,])` the
#: first alternative would match "187" of "1877416" and this would read
#: $187.00 for $1,877,416.69.
DOC_TOTAL = re.compile(
    r"\btotals?\b[^(\n]{0,40}\(\s*(A(?:\s*\+\s*[A-G])*)\s*\)\s*[:=]?\s*\$?\s*"
    r"(?:(NIL)|(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{2}))?(?![\d,]))", re.I)

#: A leading row number, printed in the form's first column. Optional by
#: design: `| Donor | date | No | $x |` is the same row without it.
LEADING_N = re.compile(r"^\|?\s*(\d{1,3})\s+(?=\S)")

#: A table row must END in money. Everything before the last two cells is the
#: donor and whatever the form puts between.
TRAILING_MONEY = re.compile(
    r"\$?\s*(\d{1,3}(?:,\d{3})*|\d+)\.(\d{2})\s*\|?\s*$")

#: Lines that are furniture, not data.
FURNITURE = re.compile(
    r"^\s*\|?\s*[:\-\s|]+\|?\s*$"                       # markdown rule
    r"|^\s*(page|part)\b"
    r"|donor'?s?\s+name"                                 # header cell
    r"|amount\s+of\s+donation"
    r"|write\s+'?nil'?"
    r"|\btotals?\b", re.I)


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_page(text: str, page: int, *, part: str | None = None,
               reader: str | None = None) -> tuple[list[Row], str | None,
                                                   dict[str, float]]:
    """One page's rows, the part it ended in, and any totals it printed."""
    out: list[Row] = []
    totals: dict[str, float] = {}
    declared: tuple[float, tuple[str, ...]] | None = None
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        d = DOC_TOTAL.search(s)
        if d and declared is None:
            letters = tuple(x.upper() for x in re.findall(r"[A-G]", d.group(1)))
            amount = 0.0 if d.group(2) else float(d.group(3).replace(",", "")
                                                 + "." + (d.group(4) or "00"))
            declared = (amount, letters)
        t = TOTAL.search(s)
        if t:
            totals[t.group(1).upper()] = float(
                t.group(2).replace(",", "") + "." + t.group(3))
        p = PART.search(s)
        if p:
            part = p.group(1).upper()
        if FURNITURE.search(s) or not TRAILING_MONEY.search(s):
            continue
        n = None
        body = s
        m = LEADING_N.match(s)
        if m:
            n = int(m.group(1))
            body = s[m.end():]
        cells = _cells(body)
        if len(cells) < 2:
            # Not a delimited row: the donor is whatever precedes the money.
            cut = TRAILING_MONEY.search(body)
            cells = [body[:cut.start()].strip(" |"), body[cut.start():]]
        amount = money(cells[-1])
        if amount is None:
            continue
        donor = cells[0].strip() or None
        when = None
        for c in cells[1:-1]:
            when = read_date(c) or when
        if when is None:
            when = read_date(body)
        out.append(Row(n=n, donor=donor, date=when, amount=amount, page=page,
                       part=part, reader=reader, raw=s))
    return out, part, totals, declared


def parse_document(stem: str, pages: dict[int, str], *, year: int | None = None,
                   reader: str | None = None) -> Document:
    """Every page of one document, in page order."""
    rows: list[Row] = []
    totals: dict[str, float] = {}
    part: str | None = None
    declared: tuple[float, tuple[str, ...]] | None = None
    for p in sorted(pages):
        got, part, tot, dec = parse_page(pages[p], p, part=part, reader=reader)
        rows.extend(got)
        for k, v in tot.items():
            totals.setdefault(k, v)
        # The FIRST one wins: the summary is on page 1 and a later page that
        # repeats it is a continuation sheet, not a second declaration.
        if dec and declared is None:
            declared = dec
    return Document(stem=stem, rows=tuple(rows), stated_totals=totals,
                    year=year, pages=len(pages), reader=reader,
                    declared_total=declared[0] if declared else None,
                    declared_parts=declared[1] if declared else ())
