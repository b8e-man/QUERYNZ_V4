"""A registered promoter's expense return: each part's own figure, read
(contract: the reader; profile `ec-promoter-expenses-return`).

The declaration states each part on its own: Part A election advertising;
in 2020 also Part B, the cannabis referendum, and Part C, the End of Life
Choice Act referendum. The parts are never added: the form says a cost that
is both election and referendum advertising counts in full in each (Family
First 2020 states $141,224.34 in all three). Each part's schedule prints
`TOTAL FOR PART <X>`. A part's figure is checked by the return's own two
statements of it, the declaration's box and the schedule's total:

    declared-and-schedule   both read and equal
    declared-only           the declaration's box alone
    schedule-only           the schedule's total alone
    (none)                  the two disagree, or neither is read: a catch-log line

A part written N/A is not read as zero: the page reader drops handwriting
(PSA 2020 wrote N/A by hand in all three), and no typed N/A was met.

Pages come through the reader contract as in `expenses.py`: the text layer
where a page has one, else the page reader's stored reading (GLM-OCR at the
profile's 200 dots, prompt `OCR`), replayed and never called; a second pass
takes the stored reading of every page that has one.

    read_return(data, sha256, store, year) -> Result
"""
import re
from dataclasses import dataclass, field

from support import profiles
from support import reader as rd
from registers.party_finance import expenses

PROFILE = "ec-promoter-expenses-return"
#: the part letter → the Commission's column, by the form's year (2023 has Part A alone)
COLUMNS = {2020: {"A": "election_expenses", "B": "cannabis_referendum_expenses", "C": "end_of_life_referendum_expenses"},
           2023: {"A": "election_expenses"}}
TOLERANCE = 0.011

FIG = r"\$\s*(?<![\d.,])([\d][\d,]*\.\d\d)\b"
#: the figure below its label, blank lines between allowed (the page reader reads the boxes one by one)
BELOW = r"[ \t]*\n(?:[ \t]*\n)*[ \t]*" + FIG
#: the declaration's box: `Part A: Election advertising … $ 5,692.14`, the `$` required, on the label's line or below
DECLARED = re.compile(r"^[^\n\S]*Part\s+([A-C])\s*:\s*(?:Election|Referendum)\b(?:[^\n$]*?" + FIG
                      + r"|[^\n$]*" + BELOW + ")", re.I | re.M)
SCHEDULE = re.compile(r"TOTAL\s+FOR\s+PART\s*([A-C])\b(?:[^\n$]*?" + FIG + "|" + BELOW + ")", re.I)
PLACE = {"declared-and-schedule": "Part {0} on the declaration and TOTAL FOR PART {0}",
         "declared-only": "Part {0} on the declaration", "schedule-only": "TOTAL FOR PART {0}"}


@dataclass
class Part:
    letter: str
    figure: float = None
    check: str = None
    declared: float = None
    declared_page: int = None
    schedule: float = None
    schedule_page: int = None

    @property
    def page(self):
        return self.declared_page if self.check in ("declared-and-schedule", "declared-only") else self.schedule_page


@dataclass
class Result:
    document: str
    year: int
    parts: dict = field(default_factory=dict)        # letter → Part, every part the year's form has
    pages: dict = field(default_factory=dict)        # page → (read_from, profile, version)
    profile_version: int = None
    passes: str = ""
    unread: list = field(default_factory=list)
    set_aside: list = field(default_factory=list)     # (part letter, why)


def scan(page_texts: dict, letters) -> dict:
    """letter → Part with what the pages state; the first hit for each wins."""
    out = {k: Part(k) for k in letters}
    for p in sorted(page_texts):
        t = page_texts[p] or ""
        for rx, attr in ((DECLARED, "declared"), (SCHEDULE, "schedule")):
            for m in rx.finditer(t):
                part = out.get(m.group(1).upper())
                v = expenses.money(m.group(2) or m.group(3))
                if part and getattr(part, attr) is None and v is not None:
                    setattr(part, attr, v)
                    setattr(part, attr + "_page", p)
    return out


def judge(part: Part) -> str:
    """Sets the part's figure and check; returns why not, or ''."""
    d, s = part.declared, part.schedule
    if d is not None and s is not None:
        if abs(d - s) <= TOLERANCE:
            part.figure, part.check = d, "declared-and-schedule"
            return ""
        return f"Part {part.letter}: the declaration's {d:.2f} is not the schedule's total {s:.2f}"
    if d is not None:
        part.figure, part.check = d, "declared-only"
    elif s is not None:
        part.figure, part.check = s, "schedule-only"
    else:
        return f"Part {part.letter}: no figure read on the declaration or the schedule"
    return ""


def read_return(data: bytes, sha256: str, store: rd.Store, year: int) -> Result:
    prof = profiles.profile(PROFILE)
    if prof is None:
        raise LookupError(f"no document profile {PROFILE}")
    res = Result(sha256, year, profile_version=int(prof["version"]))
    letters = tuple(COLUMNS.get(year, {}))
    if not letters:
        res.set_aside.append(("", f"no form known for {year}"))
        return res
    if not data.startswith(b"%PDF"):
        res.set_aside.append(("", "not a PDF"))
        return res
    for pass_name, all_pixels in (("first", False), ("pixels", True)):
        texts, unread = expenses.page_texts(data, sha256, store, res.profile_version, all_pixels, PROFILE)
        parts = scan({p: t for p, (t, *_) in texts.items()}, letters)
        whys = [(k, w) for k, w in ((k, judge(parts[k])) for k in letters) if w]
        res.parts, res.unread, res.passes = parts, unread, pass_name
        res.pages = {p: tuple(v[1:]) for p, v in texts.items()}
        if not whys:
            return res
    tail = f"; pages with no text layer and no stored reading: {res.unread}" if res.unread else ""
    res.set_aside = [(k, w + tail) for k, w in whys]
    return res
