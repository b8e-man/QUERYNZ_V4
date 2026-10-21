"""Part H: the loans a return names (plan 4.1, tranche 2).

**The declared figures.** The declaration page's step 2 prints `Part H:
Party loans exceeding $30,000`, `Part I: Party loans between $1,500 –
$30,000` and `Total (H + I)`. `declared(text)` reads the three, the
thresholds cut out first (they are the form's words, never a figure); a
figure the label does not carry is the next figure alone in the amount
column, as on the donations half. The return's own arithmetic checks
them: H + I equals the total, or differs by less than $100 (ruling 66,
`reconcile.py`: the row carries the `issue`), or the loans are not taken.

**The lenders.** Part H is not a table: the form prints one block per
loan, opening with `Lender's name and street address`, then the amount,
the date entered into, the repayment date, a guarantor, the interest rate,
the security and any terms. A block's loan amount is its first figure
under the lender or under `Loan amount`; the unpaid balance and the
figure under `Total aggregated loan amount from the same lender` (the
lender's running total) are never added. Every block is
published only when the blocks add up to Part H on the declaration page
and to `TOTAL FOR PART H` where that was read, or differ from each by less
than $100 (ruling 66: each lender row carries the `issue`). The
lender's name is cut from the address the way a donor's is
(`donors.split`); the address goes only to `party_returns_private`, and so
does a guarantor's name and address (a guarantor is a private person the
form names in passing, not a party to the published row).

Part I is an aggregate (a count and a total): it has no lender to name.

    declared(text)                 Loans(h, i, total, problems)
    read(texts, src, declared_h)   Part (as donors.Part; rows: lender, address, amount, entered, repay, interest)
"""
import re
from dataclasses import dataclass, field

from support.docread import declaration as D
from registers.party_returns import donors, pixels, reconcile, schedule

LOANS_START = re.compile(r"TOTAL\s*PART[A-Za-z/]*\s*LOANS|TOTAL\s+\w+\s+LOANS", re.I)
LABEL_H = re.compile(r"party\s+loans\s+exceeding", re.I)
LABEL_I = re.compile(r"party\s+loans\s+between", re.I)
LABEL_T = re.compile(r"Total\s*\(\s*H\s*\+\s*I\s*\)", re.I)
THRESHOLD = re.compile(r"^\s*\$\s*\d[\d,]*(?:\s*[–-]\s*\$\s*\d[\d,]*)?")     # right after its label: the form's words
DECLARE = re.compile(r"I\s+declare\s+that", re.I)
HEADING = re.compile(r"PART\s*H\s*[:.\-–]?\s*PARTY\s+LOANS?\s+EXCEEDING", re.I)
END = re.compile(r"instructions?\s+for\s+part\s+I\b|^\W*part\s*I\s*[:.\-–]|total\s+for\s+part\s+I\b", re.I)
LENDER = re.compile(r"lender.?s?\s+name", re.I)
FIELD = re.compile(r"loan\s+amount|\(?including\s+gst\)?|date\s+(?:the\s+)?loan|repayment\s+date|no\s+repayment\s+date|"
                   r"guarantor|unpaid\s+balance|interest\s+rate|security|total\s+aggregated|any\s+terms|reduce\s+or\s+extinguish",
                   re.I)
AMOUNT_FIELDS = (None, "loan amount", "including gst", "(including gst)")
RATE = re.compile(r"\b\d{1,2}(?:\.\d+)?\s*%|\binterest[\s-]+free\b|\bnil\b|\bnone\b", re.I)


@dataclass
class Loans:
    h: float = None
    i: float = None
    total: float = None
    problems: list = field(default_factory=list)
    issue: str = None                                # ruling 66: H + I differs from the total by less than $100


def _figure(rest: str, threshold: bool = True):
    """The first figure after a label, the label's threshold cut out."""
    body = THRESHOLD.sub(" ", rest) if threshold else rest
    m = D.MONEY.search(body)
    if not m:
        return None
    return 0.0 if m.group("nil") else D.amount(m)


def declared(text: str) -> Loans:
    out = Loans()
    lines = [pixels.clean(l) for l in (text or "").splitlines()]
    start = next((k for k, l in enumerate(lines) if LOANS_START.search(l)), None)
    if start is None:
        out.problems.append("no loans step on the declaration page")
        return out
    pending = []
    for line in lines[start + 1:]:
        if DECLARE.search(line):
            break
        left = line[:D.LEFT_COLUMN + 30] if len(line) > D.LEFT_COLUMN + 30 and "|" not in line else line
        for label, rx in (("i", LABEL_I), ("h", LABEL_H), ("total", LABEL_T)):
            m = rx.search(left)
            if m:
                got = _figure(left[m.end():], threshold=label != "total")
                if got is None:
                    pending.append(label)
                else:
                    setattr(out, label, got)
                break
        else:
            s = left.strip()
            if pending and s and (D.MONEY.fullmatch(s.lstrip("$ ").strip()) or re.fullmatch(r"nil", s, re.I)):
                setattr(out, pending.pop(0), 0.0 if re.fullmatch(r"\$?\s*nil", s, re.I) else D.amount(D.MONEY.search(s)))
    if out.total is None and out.h is not None and out.i is not None:
        out.total = round(out.h + out.i, 2)          # the total left blank: the parts stand, the check below is moot
    for name in ("h", "i"):
        if getattr(out, name) is None:
            out.problems.append(f"Part {name.upper()} on the declaration page was not read")
    if not out.problems:
        if not reconcile.within(round(out.h + out.i, 2), out.total):
            out.problems.append(f"Part H {out.h:,.2f} + Part I {out.i:,.2f} is not the total {out.total:,.2f}")
        else:
            out.issue = reconcile.issue(round(out.h + out.i, 2), out.total, "the declaration's Part H + Part I against its Total (H + I)")
    return out


def _blocks(lines: list) -> list:
    """[(page, [lines])] one per `Lender's name and street address`."""
    out = []
    for p, line in lines:
        if LENDER.search(line):
            out.append((p, [line]))
        elif out:
            out[-1][1].append(line)
    return out


def _block_row(page: int, lines: list, src: str) -> dict:
    cell, amounts, dates, rate, field_now = [], [], [], "", None
    for line in lines:
        s = " ".join(line.replace("|", " ").split())
        if not s or schedule.PRINTED_TOTAL.search(s) or LENDER.search(s):
            continue
        f = FIELD.search(s)
        if f:
            field_now = f.group(0).lower()
            s = FIELD.sub(" ", s).strip(" :()")
            if not s:
                continue
        if schedule.MONEY_ONLY.match(s) or (field_now is None and schedule.money(s) is not None and cell):
            if field_now in AMOUNT_FIELDS and schedule.money(s):
                amounts.append(schedule.money(s))     # never the unpaid balance, a guarantee or the lender's running total
            continue
        if schedule.FULL_DATE.search(s):
            dates += [m.group(0).strip(" ,") for m in schedule.FULL_DATE.finditer(s)]
            continue
        if field_now and "interest" in field_now and RATE.search(s):
            rate = RATE.search(s).group(0)
            continue
        if field_now is None:
            cell.append(s)
    name, address = donors.split(" ".join(cell))
    return {"page": page, "cell": " ".join(cell), "name": name, "address": address,
            "amount": round(amounts[0], 2) if amounts else None, "dates": ", ".join(dates), "interest": rate,
            "paired_by": "block", "read_from": src}


def _block_row_text(page: int, lines: list) -> dict:
    """A lender block from the text layer: the form's two rows of columns.
    The name cell is what sits left of the amount column (its heading,
    `(including GST)`, is on the lender heading's own line); the amount is
    the first figure in that column, cents or none; the interest rate sits
    under its own heading in the second row."""
    head = lines[0] if lines else ""
    amount_x = next((m.start() for m in (re.search(r"\(including\s+GST\)|Loan\s+amount", l, re.I) for l in lines[:3]) if m), 55)
    rate_x, second, cell, amount, dates, rate = None, False, [], None, [], ""
    for line in lines:
        if re.search(r"guarantor", line, re.I):
            second = True
            m = re.search(r"interest\s+rate", line, re.I)
            rate_x = m.start() if m else rate_x
            continue
        if FIELD.search(line) or schedule.FURNITURE.search(line) or LENDER.search(line):
            continue
        dates += [m.group(0).strip(" ,") for m in schedule.FULL_DATE.finditer(line)]
        for seg in re.finditer(r"\S+(?:\s{1,2}\S+)*", schedule.FULL_DATE.sub(lambda m: " " * len(m.group(0)), line)):
            t, x = seg.group(0), seg.start()
            if not second and x < amount_x - 8:
                cell.append(t)
            elif not second and amount is None and (m := D.MONEY.fullmatch(t.lstrip("$ ").strip())) and not m.group("nil"):
                amount = D.amount(m) or None
            elif second and rate_x is not None and abs(x - rate_x) < 12 and RATE.search(t):
                rate = RATE.search(t).group(0)
    name, address = donors.split(" ".join(cell))
    return {"page": page, "cell": " ".join(cell), "name": name, "address": address,
            "amount": round(amount, 2) if amount else None, "dates": ", ".join(dates), "interest": rate,
            "paired_by": "block", "read_from": "text"}


def read(texts: dict, src: dict, declared_h) -> donors.Part:
    lines = schedule.region(texts, HEADING, END)
    printed = schedule.printed_total(lines, "H")
    out = donors.Part(printed=printed, declared=declared_h)
    blocks = [_block_row_text(p, ls) if src.get(p) == "text" else _block_row(p, ls, src.get(p, "pixels"))
              for p, ls in _blocks(lines)]
    rows = [r for r in blocks if r["amount"]]
    if declared_h and any(not r["amount"] and r["cell"] for r in blocks):
        out.problems.append(f"{sum(1 for r in blocks if not r['amount'] and r['cell'])} lender block(s) read with no loan amount")
    for k, r in enumerate(rows, 1):
        if r["name"] is None and r["cell"]:
            out.problems.append(f"lender {k} (page {r['page']}): no name before the address")
        if not r["cell"]:
            out.problems.append(f"lender {k} (page {r['page']}): no lender read")
    total = round(sum(r["amount"] or 0 for r in rows), 2)
    wants = [(what, x) for what, x in (("the declaration's Part H", declared_h), ("TOTAL FOR PART H", printed)) if x is not None]
    if not wants:
        out.problems.append("nothing to reconcile against: neither the declaration's Part H nor TOTAL FOR PART H was read")
    issues = []
    for what, x in wants:
        if not reconcile.within(total, x) or (not rows and reconcile.cents(x)):    # nothing read is not a difference
            out.problems.append(f"the {len(rows)} loans read add to {total:,.2f}; {what} is {x:,.2f}")
        issues.append(reconcile.issue(total, x, f"the {len(rows)} Part H loans against {what}"))
    if out.problems:
        return out
    out.issue = reconcile.join(issues)
    out.rows = [{**r, "n": k, "issue": out.issue} for k, r in enumerate(rows, 1)]
    out.check = "declared-nil" if not rows else "parts-sum"
    return out
