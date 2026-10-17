"""The unit a reader produces and every other module consumes: a ROW.

One row is one line of a filed form — the number printed in its first column,
the donor, the date, the amount. A reader that cannot find one of these says
None; it never guesses and it never omits the row, because an omitted row is
invisible to every check downstream and a None is not.

`n` is the number PRINTED ON THE FORM, not the row's position in our list.
That distinction is the whole point: position is what we derived and can get
wrong, `n` is what the filer asserted, and an invariant that compares the two
is the cheapest error detector this service has.
"""
from __future__ import annotations

import dataclasses
import re
import unicodedata

#: A money cell as the EC forms print it: $1,002,516.53
MONEY = re.compile(r"\$?\s*(\d{1,3}(?:,\d{3})*|\d+)\.(\d{2})\b")



def fragment(m) -> bool:
    """Did this money match BEGIN MID-NUMBER?

    Money is not written with leading zeros, so an integer part of "088" is
    not eighty-eight dollars: it is the tail of a figure whose first digits
    were not read. That one question decides which of two disagreeing reads
    of a cell to keep, and it is the only honest way to tell the two apart —
    "$10,088.00" read as "$088.00" at page scale and "$6,138.48" read as
    "96,138.48" at cell scale are the SAME SHAPE (one read is the other with
    a digit on the front), so preferring the larger gets one of them wrong
    every time. A leading zero is present in the first and absent in the
    second.
    """
    whole = m.group(1).replace(",", "").replace(" ", "")
    return len(whole) > 1 and whole[0] == "0"

#: dd/mm/yyyy — the only date form these returns use.
DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")


@dataclasses.dataclass(frozen=True)
class Row:
    """One line of a filed table, as read.

    Every field except `reader` may be None: a reader that did not find a cell
    must say so rather than inventing one. `raw` keeps the text the row was
    read from so a reviewer can see what the machine saw.
    """
    n: int | None = None
    donor: str | None = None
    date: str | None = None
    amount: float | None = None
    page: int | None = None
    part: str | None = None
    reader: str | None = None
    raw: str | None = None
    #: Where this row sits on the rendered page, (x0, y0, x1, y1) in pixels at
    #: `dpi`. Only a reader that works from geometry can fill it; it is what
    #: lets the review queue show a person the actual cell instead of the
    #: whole page, which is the difference between a glance and a hunt.
    bbox: tuple[float, float, float, float] | None = None
    dpi: int | None = None
    #: Set by `arbitrate.merge`: both readers found this row and agreed on
    #: every field. Recorded HERE, where both rows are in hand, because
    #: nothing downstream can recover it — the merged row carries the
    #: transcriber's donor text and the agreed row the geometric reader's, so
    #: they do not even share a name to be matched on (2026-09-23).
    agreed: bool = False

    def key(self) -> tuple:
        """What makes two readings THE SAME ROW for comparison."""
        return (self.part, self.n)


@dataclasses.dataclass(frozen=True)
class Document:
    """A read of one filed document: its rows and what it says about itself.

    `stated_totals` is part letter -> the total the form PRINTS for that part.
    It is evidence from the document, never a sum we computed; keeping the two
    apart is what lets an invariant compare them.
    """
    stem: str
    rows: tuple[Row, ...] = ()
    stated_totals: dict[str, float] = dataclasses.field(default_factory=dict)
    year: int | None = None
    pages: int = 0
    reader: str | None = None
    #: The file this was read from, relative to the repo. Carried so a review
    #: item can find its document directly instead of globbing for a stem
    #: that may not be the filename.
    source: str | None = None
    #: What the form declares for the WHOLE return — the summary line on its
    #: first page, `Total Party Donations (A + C + D + F + G) $1,500,307.55` —
    #: and the parts it says that total covers, taken FROM the line rather
    #: than assumed (C418, 2026-10-10).
    #:
    #: WHY IT IS HERE AT ALL. The per-part totals used to come from the
    #: geometric reader, which read them off the ruled table footer; it was
    #: retired on 2026-09-25 and **15 of the 107 party returns in scope lost
    #: every stated total with it**, so nothing could reconcile them — Labour
    #: 2021, Te Pāti Māori 2025 and NZ First's amended return among them.
    #: Every one of those documents prints this summary line, and 106 of the
    #: 107 do. It is the party's own arithmetic over its own parts, which is
    #: exactly the evidence a reconciliation needs, and no reader had ever
    #: looked at it.
    declared_total: float | None = None
    declared_parts: tuple[str, ...] = ()

    def part(self, letter: str) -> tuple[Row, ...]:
        return tuple(r for r in self.rows if r.part == letter)

    def parts(self) -> tuple[str, ...]:
        return tuple(sorted({r.part for r in self.rows if r.part}))


def money(s: str) -> float | None:
    """Read a money cell. None when the text holds no money at all."""
    m = MONEY.search(s or "")
    if not m:
        return None
    return float(m.group(1).replace(",", "") + "." + m.group(2))


def date(s: str) -> str | None:
    """Read a dd/mm/yyyy date, returned ISO. None when absent or impossible."""
    m = DATE.search(s or "")
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= d <= 31 and 1 <= mo <= 12 and 1900 <= y <= 2100):
        return None
    return f"{y:04d}-{mo:02d}-{d:02d}"


def name_key(s: str | None) -> str:
    """A donor name reduced to what two readers can be expected to agree on.

    Letters only, case-folded, accents stripped. Addresses, punctuation and
    OCR's wandering commas are all noise for the purpose of asking whether two
    readers found the SAME donor.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s.lower() if c.isalpha())


#: Parts whose rows name a DONOR. Part C and the expense parts carry banded
#: aggregates ("Donations exceeding $1,500 but not exceeding $5,000"), which
#: are not donors and must not be checked as though they were.
NAMED_DONOR_PARTS = frozenset({"A", "B", "E"})

_FIRST_DIGIT = re.compile(r"\d")


#: Phrases the EC's own forms print as COLUMN HEADERS. A reader that returns
#: one of these as a donor has read the header band as a data row — the defect
#: behind six rows on National 2021 whose donor is `No` (the Yes/No column) and
#: two whose donor is the money column's own caption.
_HEADER_PHRASES = (
    "donor's name", "donors name", "street address",
    "date donation", "aggregated donations received",
    "does the donation contain", "contributions from another person",
    "amount of contribution", "amount of donation",
    "total aggregated", "including gst",
    "the number of and aggregate amount",
    "description of donation", "unpaid balance", "balance of loan",
    "name of lender", "interest rate", "terms of the loan", "terms of loan",
    "date loan", "aggregate amount of loans",
    "write 'nil'", 'write "nil"', "complete parts",
)

#: A donor cell that swallowed the date column. The forms print a donor's name
#: and street address in ONE cell (which is normal and `donor_key` handles it)
#: but never a date, so a date in the donor cell is a column boundary lost.
_DATE_IN_CELL = re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b")

#: A donor cell that is a STREET ADDRESS and nothing else — the name was lost
#: and the address kept, which is geometry's own failure mode. Green 2023 p5
#: filed `11A Moody Avenue Whangarei` as a donor; the printed name is Nicholas
#: R Karlovsky. Both halves are required, so a company whose name opens with a
#: number (`3M New Zealand`, `2degrees`) is NOT caught: it has no street word.
_HOUSE_NUMBER = re.compile(r"^\s*\d+[A-Za-z]?\b")
_STREET_WORD = re.compile(
    r"\b(street|road|avenue|ave|lane|place|terrace|drive|crescent|cresent|parade|"
    r"highway|quay|way|close|grove|court|esplanade|rise|mews|boulevard|"
    r"st|rd|pde|cres|tce)\b", re.I)

# C424, 2026-09-23. The guard above catches an address only when the cell
# STARTS with a bare house number, and on Green 2023 that missed four shapes
# out of four: a leading cell-boundary artefact (`|30 Findlay Street
# Mangawhai`), a unit word (`Flat 1 86 McLauchlan Street Blenheim`), a
# care-of (`C/O GPANZLS / 108 The Terrace 161 Barnard Street`), and the blend
# itself. 56 of that return's 60 donor cells in the gold set hold a street
# address, and they were staged at tier AGREED — both readers returned the
# address, agreed with each other, and the cells were therefore offered as
# CALIBRATION, which is the one tier that must not be in doubt.
_ADDR_LEAD = re.compile(
    r"^[\s|_/,.\-]*(?:c\s*/?\s*o\b[^0-9]{0,40}|flat\b|unit\b|apt\b|apartment\b|"
    r"suite\b|level\b|shop\b|po\s+box\b)?[\s|_/,.\-]*", re.I)
#: A house-number-shaped token anywhere in the cell, used only for counting.
_HOUSE_RUN = re.compile(r"(?<![\w/])\d{1,4}[A-Za-z]?(?=\s)")


def _address_shaped(donor: str) -> bool:
    """Is this cell an address with no name, whatever it begins with?"""
    return bool(_HOUSE_NUMBER.match(_ADDR_LEAD.sub("", donor))
                and _STREET_WORD.search(donor))


#: the words before the first house number — where a filed name lives, because
#: the EC form prints the donor's address AFTER the name on the same line
_BEFORE_NUMBER = re.compile(r"^([^\d]*)")
_NAME_TOKEN = re.compile(r"[A-Za-z][A-Za-z'\-\u0100-\u017f]{1,}")


def _names_the_donor(donor: str) -> bool:
    """Does this cell carry a NAME before its first number?

    C424, corrected the same night. The blend rule below fired on
    `Julie Anne Genter, 16 Chatham Street, 16 Chatham Street, Wellington, 6`
    — two street words and two house numbers, and the donor's name right there
    at the front. Refusing that loses a real donor, which is the opposite of
    what this guard is for, and it is C426's own premise: the form prints the
    address BESIDE the name, so text before the first digit is the name.

    Two tokens, because one leading word is as likely to be `Flat` or `Unit`
    as a given name.
    """
    lead = _BEFORE_NUMBER.match(donor or "").group(1)
    lead = _ADDR_LEAD.sub("", lead)
    return len(_NAME_TOKEN.findall(lead)) >= 2


def _address_blend(donor: str) -> bool:
    """Has this cell swallowed MORE THAN ONE row's address?

    Arthur, reading the scans: "this runs on into the cell below it",
    "blended cells". Both halves are required — two street words AND two
    house numbers — because a company may legitimately carry one street word
    in its name (`Queen Street Investments`) and never two with two numbers.
    And a cell that NAMES its donor before the first number is a name with an
    address after it, however many addresses follow.
    """
    return (len(_STREET_WORD.findall(donor)) >= 2
            and len(_HOUSE_RUN.findall(donor)) >= 2
            and not _names_the_donor(donor))


def malformed(row: "Row") -> str | None:
    """Why this row did not parse, or None if nothing is provably wrong.

    C423, 2026-09-23. 43 of 55 cells the gold tab offered as IMPLICATED asked a
    person about a row that was never read: a column header, the Yes/No column,
    an empty donor. Confirming any of them launders a bad read into gold, which
    is the one thing a gold set must not do. So a row that fails to parse is a
    FINDING — it goes to the reader's queue, not to a person for confirmation.

    Deliberately narrow: every clause is a fact about the cell's own content,
    never a judgment about whether a name looks real. `Chaistopher Yaakin` is a
    garble and stays a row, because abstaining is what we do when we cannot
    prove the defect (ruling 191, and LESSONS §2).
    """
    donor = (row.donor or "").strip()
    low = donor.lower()
    if any(h in low for h in _HEADER_PHRASES):
        return "the donor cell holds a column header"
    if low in ("yes", "no", "y", "n"):
        return "the donor cell holds the Yes/No column"
    if _DATE_IN_CELL.search(donor):
        return "the donor cell swallowed the date column"
    if not donor and row.part in NAMED_DONOR_PARTS:
        return "no donor was read, in a part that names its donors"
    if row.part in NAMED_DONOR_PARTS:
        # the blend first: it is the stronger statement, and it says WHY the
        # money on that row cannot be attributed to anyone
        if _address_blend(donor):
            return "the donor cell has run several rows' addresses together"
        if _address_shaped(donor):
            return "the donor cell holds a street address with no name"
    return None


def donor_key(s: str | None) -> str:
    """A donor name with its street address removed.

    The forms print name and address in ONE cell and the address is where OCR
    and the filer both vary: "Hagaman, Lianna 10 Coldstream Court,
    Christchurch" and "…10 Coldstream Court, Ilam, Christchurch" are one
    donor. NZ street addresses begin with a number, so the name is what
    precedes the first digit — and where that leaves too little to be a name
    (a donor whose name contains a digit), the whole cell is used instead.
    """
    if not s:
        return ""
    m = _FIRST_DIGIT.search(s)
    head = s[:m.start()] if m else s
    key = name_key(head)
    return key if len(key) >= 3 else name_key(s)


def donor_name(s: str | None) -> str:
    """The readable donor name with the street address trimmed off.

    `donor_key` for a human: same cut, no case-folding, so a report can show
    what it matched on.
    """
    if not s:
        return ""
    m = _FIRST_DIGIT.search(s)
    head = " ".join((s[:m.start()] if m else s).split()).strip(" ,;")
    return head if len(name_key(head)) >= 3 else " ".join(s.split())
