"""Part A: the donors a return names (plan 4.1, tranche 2).

The rows come from `schedule.rows`; this module cuts each cell into the
donor's name and the street address, and reconciles the part. Only Part A
names donors (Part G is an aggregate, Part F is protected by law).

**The reconciliation.** The rows of a part are published only when they
add up, to the cent, to the part's total as the return prints it: the
declaration page's Part A figure, and the Part A page's own `TOTAL FOR
PART A` where that was read. Either one disagreeing sets the whole part
aside with both figures; a part that is nil on the declaration publishes
no rows and needs none. A part with nothing to reconcile against is set
aside, never published on its own say (lesson: a document with nothing to
reconcile looks exactly like a clean one).

**The cut.** The form prints the name and the street address in one cell.
The name is the text before the first figure or address word (`Level`,
`Flat`, `PO Box`, `C/-`, `RD 3`), and before the comma or semicolon that
opens a part holding a street word, so the published name never carries a
house number or a street; with no figure in the cell, a street word with
no separator before it leaves no name (with a figure, `Brian Lane, 4 …`
is a name). The rest of the cell is the address and goes only to
`party_returns_private` (hard limit 15). A cell that leaves no name, or
that `support.docread.rows.malformed` refuses (a column heading, a date
swallowed, an address with no name), sets the part aside: its money cannot
be put beside a donor.

    read(texts, src, declared)     Part(rows, printed, check, problems)
"""
import re
from dataclasses import dataclass, field

from support.docread import rows as R
from registers.party_returns import schedule

HEADING = re.compile(r"PART\s*A\s*[:.\-–]?\s*PARTY\s+DONATIONS?\s+OF\s+MORE\s+THAN", re.I)
END = re.compile(r"instructions?\s+for\s+part\s+[B-I]\b|^\W*part\s*[B-I]\s*[:.\-–]|total\s+for\s+part\s+[B-I]\b", re.I)
#: where the address begins: a figure, or a word that opens an address
ADDRESS_START = re.compile(r"\d|\bc\s*/\s*[-o](?!\w)|\b(?:care\s+of|level|lvl|floor|flat|unit|apt|apartment|suite|shed|building|bldg|"
                           r"p\.?\s*o\.?\s*box|private\s+bag|rd\s*\d)\b", re.I)
STREET = re.compile(r"\b(?:street|st|road|rd|avenue|ave|lane|place|pl|terrace|tce|drive|dr|crescent|cres|parade|pde|"
                    r"highway|hwy|quay|way|close|grove|court|esplanade|rise|mews|boulevard|line|valley|heights)\b\.?", re.I)
LEADING_N = re.compile(r"^\s*(\d{1,3})\.?\s+(?=[A-Za-z])")
CENT = 0.005


@dataclass
class Part:
    rows: list = field(default_factory=list)       # dicts: n, name, address, amount, dates, yes_no, page, paired_by, read_from
    printed: float = None                            # TOTAL FOR PART A, as the part's page prints it
    declared: float = None                           # Part A on the declaration page
    check: str = ""                                  # parts-sum | declared-nil | '' when set aside
    problems: list = field(default_factory=list)


def split(cell: str):
    """(name, address) from one name-and-address cell; name None when
    nothing before the address is a name. A cell read over several lines
    takes its name from the first line only: the lines below it are the
    address."""
    if "\n" in (cell or "").strip():
        first, rest = cell.strip().split("\n", 1)
        name, address = split(first)
        return (None, " ".join(cell.split())) if name is None else (name, " ".join(f"{address} {rest}".split()))
    cell = " ".join((cell or "").split()).strip(" ,;")
    m = ADDRESS_START.search(cell)
    head, rest = (cell[:m.start()], cell[m.start():]) if m else (cell, "")
    parts = re.split(r"(?<=[,;])", head)
    for i in range(len(parts)):                     # `Name, Main Road, Town`: no figure, still a street
        if STREET.search(parts[i]):
            if i == 0:
                if m:                               # a number marks the address: `Brian Lane, 4 …` is a name
                    continue
                return None, cell                   # a street and no separator to cut at
            head, rest = "".join(parts[:i]), "".join(parts[i:]) + (" " + rest if rest else "")
            break
    name = re.sub(r"[,;]\s*\w{1,2}\W*$", "", head.strip()).strip(" ,;:-–(")    # `…, L3`: the level's letter
    if len(R.name_key(name)) < 3:
        return None, cell
    return name, rest.strip(" ,;")


def _row(r: schedule.Row) -> dict:
    cell, n = r.cell, r.n
    m = LEADING_N.match(cell)
    if m and n is None:
        n, cell = int(m.group(1)), cell[m.end():]
    name, address = split(cell)
    dates = ", ".join(m.group(0).strip(" ,") for m in schedule.DATE.finditer(r.dates or ""))   # the dates, never what sat beside them
    return {"n": n, "name": name, "address": address, "cell": " ".join(cell.split()), "amount": round(r.amount, 2), "dates": dates,
            "yes_no": r.yes_no, "page": r.page, "paired_by": r.paired_by, "read_from": r.read_from}


def read(texts: dict, src: dict, declared) -> Part:
    found, printed, problems = schedule.rows(texts, src, HEADING, END, "A")
    out = Part(printed=printed, declared=declared, problems=list(problems))
    rows = [_row(r) for r in found]
    for i, r in enumerate(rows, 1):
        why = R.malformed(R.Row(donor=r["cell"], part="A"))
        if r["name"] is None:
            why = why or "no name before the address"
        if why:
            out.problems.append(f"row {i} (page {r['page']}): {why}")
    total = round(sum(r["amount"] for r in rows), 2)
    wants = [(what, x) for what, x in (("the declaration's Part A", declared), ("TOTAL FOR PART A", printed)) if x is not None]
    if not wants:
        out.problems.append("nothing to reconcile against: neither the declaration's Part A nor TOTAL FOR PART A was read")
    for what, x in wants:
        if abs(total - x) >= CENT:
            out.problems.append(f"the {len(rows)} rows read add to {total:,.2f}; {what} is {x:,.2f}")
    if out.problems:
        return out
    out.rows = rows
    out.check = "declared-nil" if not rows else "parts-sum"
    return out
