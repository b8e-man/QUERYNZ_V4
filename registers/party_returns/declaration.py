"""The declaration page of an EC party donations return, read from its
text layer (plan 1.11; document profile `ec-party-return-text`).

Page 1 of every return since the 2017 form states the year, the party, a
figure for each of Parts A, C, D, F and G, and the grand total
`Total (A + C + D + F + G)`. The old parser (`support.docread.parse`) was
tuned on a page reader's output, where label and figure share a line; in
`pdftotext -layout` output the figure often sits ALONE on the line above
or below its label, so this reader pairs them.

What was measured on the 22 text-layer returns of the seven front-page
parties, 2017 to 2025, on 18 October 2026:

- a figure sits on its label's line (most), on the line below (Part F and
  G where the right-hand checklist crowds the row), or on the line ABOVE
  its label (the grand total, nearly always);
- figures are printed `$ 237,463.33`, `$0.00`, `36410`, `218464.7` and,
  in an OCR layer the scanner embedded (Labour 2023, 2024), `$1 ,879,585.14`;
- that OCR layer also turns letters into digits: `Part 0:` for Part G,
  `(A+O+D+F+0)` for (A+C+D+F+G). So a part is known by the WORDS of its
  label, never by its letter, and the letters in the total's brackets are
  recorded as printed and not trusted;
- the step number `2` can stand alone at the left margin, which is why a
  figure alone on a line counts only from column 40, where the amount
  column is.

The check is the return's own arithmetic: the grand total equals the sum
of the parts read. A page that cannot be reconciled is reported, never
published as a number (contract: the reader, rule 6). Pure functions; no
file, no database.
"""
import re
from dataclasses import dataclass, field

MONEY = re.compile(r"(?:\$\s*)?(?:(?P<nil>NIL|Nil|nil)|(?P<num>\d{1,3}(?:\s?,\s?\d{3})+|\d+)(?:\.(?P<cents>\d{1,2}))?)(?![\d,])")
AMOUNT_COLUMN = 40          # a figure alone on a line is a figure only from here
LEFT_COLUMN = 70            # the form's own text ends about here; the right column is guidance
PART_WORDS = (                                 # C and D before A: their labels contain A's words
    ("C", re.compile(r"anonymous party donations", re.I)),
    ("D", re.compile(r"overseas party donations", re.I)),
    ("F", re.compile(r"donations protected from disclosure", re.I)),
    ("G", re.compile(r"other party donations up to", re.I)),
    ("A", re.compile(r"[:.]?\s*party donations of more than", re.I)),
)
PART_LINE = re.compile(r"^\s*P\w{1,3}\s*[A-Za-z0-9]{1,2}\s*[:.]?\s", re.I)   # `Port Fi` is an OCR layer's `Part F:`
TOTAL_LINE = re.compile(r"\bTotal\b[^(\n]{0,30}\(\s*(?P<letters>A\s*(?:\+\s*[A-Z0-9]\s*)+)\)", re.I)
LOANS = re.compile(r"TOTAL\s*PART[A-Za-z/]*\s*LOANS|Part\s+H\s*:", re.I)
YEAR = re.compile(r"year\s+end(?:ing|ed)\s+31\s+December,?\s+(\d{4})", re.I)
PARTY_NAME = re.compile(r"Party\s+name\s*:?", re.I)
NOT_A_NAME = re.compile(r"secretary|address|phone|email|completing the return|or by hand|electronically", re.I)
EXPECTED_PARTS = ("A", "C", "D", "F", "G")


@dataclass
class Declaration:
    year: int = None
    party_label: str = None
    parts: dict = field(default_factory=dict)        # letter → amount as printed
    total: float = None
    total_letters: str = ""                           # inside the total's brackets, as printed
    total_is_nil: bool = False
    unpaired: list = field(default_factory=list)     # figures found with no label to take them

    @property
    def parts_sum(self) -> float:
        return round(sum(self.parts.values()), 2)

    def problems(self) -> list:
        """Why this page cannot be published, as plain lines; empty when
        the return's own arithmetic holds."""
        out = []
        if self.year is None:
            out.append("no year on the declaration page")
        if self.total is None:
            out.append("no declared total on the declaration page")
            return out
        if self.total_is_nil and not self.parts:
            return out                                 # a declared NIL is a complete return
        missing = [p for p in EXPECTED_PARTS if p not in self.parts]
        if missing:
            out.append("part " + ", ".join(missing) + " not read: nothing to reconcile the total against")
        if abs(self.parts_sum - self.total) > 0.011:
            out.append(f"parts sum to {self.parts_sum:.2f} but the declared total is {self.total:.2f}")
        if self.unpaired:
            out.append(f"{len(self.unpaired)} figure(s) on the page paired with no label")
        return out

    @property
    def check(self) -> str:
        if self.total_is_nil and not self.parts:
            return "declared-nil"
        return "parts-sum"


def amount(m) -> float:
    if m.group("nil"):
        return 0.0
    whole = re.sub(r"[\s,]", "", m.group("num"))
    cents = (m.group("cents") or "").ljust(2, "0")
    return float(f"{whole}.{cents}")


def figure_after(line: str, start: int):
    """The filed figure to the right of a label: the first money token
    preceded by two or more spaces (the label's own threshold, `more than
    $15,000`, follows one space and is never it)."""
    tail = line[start:]
    for m in MONEY.finditer(tail):
        before = tail[:m.start()]
        gap = len(before) - len(before.rstrip())
        if gap >= 2 or (before.strip() == "" and (gap >= 1 or tail.startswith("$"))):
            return amount(m)
    return None


def figure_alone(line: str):
    """A figure standing alone in the amount column (text may follow it:
    the right-hand checklist), or None."""
    m = MONEY.match(line.lstrip())
    if not m:
        return None
    col = len(line) - len(line.lstrip())
    if col < AMOUNT_COLUMN:
        return None
    return amount(m)


def part_of(line: str):
    """The part a label line names, by its words."""
    if not PART_LINE.match(line):
        return None
    left = line[:LEFT_COLUMN + 30]
    for letter, words in PART_WORDS:
        if words.search(left):
            return letter
    return None


def label_end(line: str, part: str) -> int:
    for letter, words in PART_WORDS:
        if letter == part:
            m = words.search(line)
            # the label runs on past its words ("of more than $15,000"): skip that threshold
            after = re.compile(r"\$\s*\d[\d,]*").search(line, m.end())
            return after.end() if after and after.start() - m.end() < 6 else m.end()
    return 0


def read(text: str) -> Declaration:
    d = Declaration()
    lines = (text or "").splitlines()
    pending_labels, pending_figures = [], []

    def pair():
        while pending_labels and pending_figures:
            label = pending_labels.pop(0)
            fig, is_nil = pending_figures.pop(0)
            if label == "TOTAL":
                d.total, d.total_is_nil = fig, is_nil
            else:
                d.parts[label] = fig

    for i, line in enumerate(lines):
        if LOANS.search(line):
            break
        y = YEAR.search(line)
        if y and d.year is None:
            d.year = int(y.group(1))
        pn = PARTY_NAME.search(line)
        if pn and d.party_label is None:
            rest = line[pn.end():LEFT_COLUMN].strip()
            cand = re.split(r"\s{3,}", rest)[0].strip() if rest else ""
            if not cand or NOT_A_NAME.search(cand):
                for nxt in lines[i + 1:i + 4]:
                    c = nxt[:LEFT_COLUMN].strip()
                    if c and not NOT_A_NAME.search(c) and len(c) > 2:
                        cand = c
                        break
            d.party_label = cand or None
            continue
        part = part_of(line)
        if part:
            fig = figure_after(line, label_end(line, part))
            if fig is None:
                pending_labels.append(part)
            else:
                d.parts[part] = fig
            pair()
            continue
        t = TOTAL_LINE.search(line)
        if t and d.total is None and "TOTAL" not in pending_labels:
            d.total_letters = re.sub(r"\s+", "", t.group("letters")).upper()
            fig = figure_after(line, t.end())
            if fig is None:
                pending_labels.append("TOTAL")
            else:
                m = MONEY.search(line, t.end())
                d.total, d.total_is_nil = fig, bool(m and m.group("nil"))
            pair()
            continue
        if d.total is not None and not pending_labels:
            break                       # the monetary / non-monetary split below the total is not read
        fa = figure_alone(line)
        if fa is not None:
            pending_figures.append((fa, bool(MONEY.match(line.lstrip()).group("nil"))))
            pair()
    d.unpaired = [f for f, _ in pending_figures]
    return d
