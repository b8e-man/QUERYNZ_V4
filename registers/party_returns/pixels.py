"""A return's declaration read from the page reader's text (GLM-OCR), not
from a text layer (plan 4.1; profiles `ec-party-return-scan` and
`ec-party-return-image-declaration`).

The page reader writes a part's label and its figure on ONE line with one
space between (`Part C: Anonymous party donations of more than $1,500 0`),
where `pdftotext -layout` leaves a gap or a line break; the text-layer
reader in `support.docread.declaration` needs the gap and so misses every
`0` printed after a threshold. Here the threshold is cut out first and the
figure is the last amount after the label, or a figure alone on the next
line. A part is still known by the words of its label, never its letter
(`declaration.part_of`), and the check is still the return's own
arithmetic.

The page reader drops the form's title, so the declaration page carries no
year. The year is taken from the form's own words elsewhere in the return,
in this order, and a return whose pages state two different years under
the first rule that fires is set aside, never guessed:

1. the loans page: `unpaid balances as at 31 December 2023`, the return's
   balance date (the 2021 form misprints the sentence's first year:
   `during 2020 or unpaid balances as at 31 December 2021`);
2. `year ended 31 December 2023`, `year ending …`, `1 January 2023 to
   31 December 2023`, `… RETURN FOR 2023` anywhere (the auditor's report
   quotes its own comparatives, so this one goes by the most frequent,
   and a tie is a refusal).

The file name is never a source of the year (lesson: a declaration is its
party, its year and its total, not its file name).

    declaration_page(texts)       the first page carrying the donations total line, or None
    read(text)                    a Declaration (the same class the text reader returns)
    return_year(texts)            (year, how) or (None, why)
"""
import collections
import re

from support.docread import declaration as D

TAG = re.compile(r"</?\w+[^>]*>")
THRESHOLD = re.compile(r"(?:more\s+than|up\s+to|exceeding)\s*\$\s*\d[\d,]*", re.I)
LABEL = re.compile(r"^\s*P\w{1,3}\s*[A-Za-z0-9]{1,2}\s*[:.!]?\s")
LOAN_YEAR = re.compile(r"unpaid\s+balances?\s+as\s+at\s+31\s+December,?\s+(\d{4})\s+of\s+a", re.I)
YEAR_ENDED = re.compile(r"year\s+end(?:ed|ing)\s+31\s+December,?\s+(\d{4})"
                        r"|1\s+January\s+(\d{4})\s+to\s+31\s+December,?\s+\2\b"
                        r"|RETURN\s+FOR\s+(\d{4})\b", re.I)


def clean(line: str) -> str:
    """Table markup the reader may emit (`|`, `<td>`) becomes spacing."""
    return TAG.sub("  ", line).replace("|", "  ")


def declaration_page(texts: dict):
    for p in sorted(texts):
        if any(D.TOTAL_LINE.search(clean(l)) for l in (texts[p] or "").splitlines()):
            return p
    return None


def _last_amount(s: str):
    ms = list(D.MONEY.finditer(s))
    if not ms:
        return None
    m = ms[-1]
    return D.amount(m), bool(m.group("nil"))


def _alone(line: str):
    s = line.strip()
    m = D.MONEY.fullmatch(s.lstrip("$ ").strip()) if s else None
    if not m:
        return None
    return D.amount(m), bool(m.group("nil"))


def read(text: str) -> D.Declaration:
    d = D.Declaration()
    d.party_label = D.read(text).party_label
    pending = []
    lines = [clean(l) for l in (text or "").splitlines()]
    for line in lines:
        if D.LOANS.search(line):
            break
        part = D.part_of(line)
        if part:
            body = THRESHOLD.sub(" ", line[LABEL.match(line).end():])
            got = _last_amount(body)
            if got is None:
                pending.append(part)
            else:
                d.parts[part] = got[0]
            continue
        t = D.TOTAL_LINE.search(line)
        if t and d.total is None:
            d.total_letters = re.sub(r"\s+", "", t.group("letters")).upper()
            got = _last_amount(line[t.end():])
            if got is None:
                pending.append("TOTAL")
            else:
                d.total, d.total_is_nil = got
            continue
        if d.total is not None and not pending:
            break
        got = _alone(line)
        if got is None:
            continue
        if pending:
            label = pending.pop(0)
            if label == "TOTAL":
                d.total, d.total_is_nil = got
            else:
                d.parts[label] = got[0]
        else:
            d.unpaired.append(got[0])
    return d


def return_year(texts: dict):
    loan = {int(y) for p in texts for y in LOAN_YEAR.findall(texts[p] or "")}
    if len(loan) == 1:
        return loan.pop(), "loans page"
    if len(loan) > 1:
        return None, f"the loans page states {len(loan)} years: " + ", ".join(map(str, sorted(loan)))
    ended = collections.Counter(int(next(g for g in m.groups() if g))
                                for p in texts for m in YEAR_ENDED.finditer(texts[p] or ""))
    top = ended.most_common(2)
    if not top:
        return None, "no year stated on any page"
    if len(top) == 2 and top[0][1] == top[1][1]:
        return None, f"'year ended' states {top[0][0]} and {top[1][0]} equally often"
    return top[0][0], "year ended"
