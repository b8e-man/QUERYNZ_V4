"""The reading of a council's register of members' pecuniary interests where
the council publishes it as a structured HTML page (profile
`interests-register-html-clause-rows` v1). No model, no PDF: a PDF register
is held and never read (ruling 79).

The shape, measured on Invercargill City Council's register (22 October
2026): one `<table>` per member; its first row a single cell with the
member's role and name in bold; each further row a number cell (`1.`) and a
cell whose bold text is the category as published, citing its clause of
the Local Government Act 2002 ("(section 54E(1)(a)"), followed by paragraphs, one
entry each. The category is the bold text; the entries are the plain
paragraphs.

What is never read (hard limit 15 and the queue's answer on real property):
a category whose heading names real property, land, a home, an address or a
contact, or a spouse's or partner's interests (a private person). Such a row is counted by its heading in `withheld` and nothing under
it is read, kept or printed. A kept entry shaped like a street address, an
email or a phone number is dropped and counted the same way.

    recognise(body) -> 'register' | 'page'
    read_register(body, sha, url) -> {'as_at', 'members': [...], 'rows': [...], 'withheld': Counter}
"""
import html
import re
from collections import Counter

READER = "registers/councillor_interests/read.py read_register"
PROFILE = "interests-register-html-clause-rows"
PROFILE_VERSION = 1
CLAUSE = re.compile(r"\(\s*(?:s|section)\.?\s*54[A-H]\s*\(\s*\d\s*\)\s*\(?\s*([a-z])\s*\)?\s*\)?", re.I)
WITHHELD = re.compile(r"real\s+property|\bland\b|\bproperty\b|\bhomes?\b|address|residen|contact|phone|e-?mail", re.I)
#: a spouse's or partner's interests describe a private person: never read (queue: may-a-councillor-s-spouse-s-interests-be-shown)
PRIVATE_PERSON = re.compile(r"\bspouse\b|\bpartner\b|\bwife\b|\bhusband\b|\bfamily members?\b", re.I)
ROLE = re.compile(r"^(Deputy Mayor|Mayor|Deputy Chair|Chairperson|Chair|Councillor|Cr\.?)\s+", re.I)
NIL = re.compile(r"^(nil|none|n/?a|not applicable|-|–)\.?$", re.I)
STREET = re.compile(r"\b\d{1,4}[A-Za-z]?\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)?\s+(Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|"
                    r"Terrace|Tce|Crescent|Cres|Lane|Way|Highway|Hwy|Parade|Quay)\b|\b(PO Box|P\.O\. Box|RD ?\d)\b")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(\+64|\b0)\d{1,2}[ -]?\d{3}[ -]?\d{3,4}\b")
AS_AT = re.compile(r"\bas at\s+(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})", re.I)
_TABLE = re.compile(r"<table\b.*?</table>", re.S | re.I)
_ROW = re.compile(r"<tr\b.*?</tr>", re.S | re.I)
_CELL = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", re.S | re.I)
_STRONG = re.compile(r"<(strong|b)\b[^>]*>(.*?)</\1>", re.S | re.I)
_P = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S | re.I)


class NotTheShape(ValueError):
    """The page is not a register of this shape."""


def text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def _member_tables(page: str) -> list:
    """The tables whose first row is one bold cell and whose other rows cite a clause of ss 54A to 54H."""
    out = []
    for t in _TABLE.findall(page):
        rows = _ROW.findall(t)
        if len(rows) < 2:
            continue
        head = _CELL.findall(rows[0])
        if len(head) != 1 or not _STRONG.search(head[0]):
            continue
        if sum(1 for r in rows[1:] if CLAUSE.search(text(r))) >= 1:
            out.append(rows)
    return out


def recognise(body: bytes) -> str:
    page = body.decode("utf-8", "replace") if isinstance(body, bytes) else body
    return "register" if len(_member_tables(page)) >= 2 else "page"


def withheld_entry(s: str) -> bool:
    return bool(STREET.search(s) or EMAIL.search(s) or PHONE.search(s))


def read_register(body: bytes, sha: str, url: str) -> dict:
    page = body.decode("utf-8", "replace")
    tables = _member_tables(page)
    if len(tables) < 2:
        raise NotTheShape("not a register of member tables citing a clause of ss 54A to 54H")
    m = AS_AT.search(text(page))
    as_at = m.group(1) if m else None
    members, rows, withheld = [], [], Counter()
    for ti, trs in enumerate(tables, 1):
        line = text(_CELL.findall(trs[0])[0])
        r = ROLE.match(line)
        role, name = (r.group(1), line[r.end():].strip()) if r else (None, line)
        members.append({"member": name, "role": role, "place": f"table {ti}"})
        for ri, tr in enumerate(trs[1:], 2):
            cells = _CELL.findall(tr)
            if len(cells) < 2:
                continue
            body_cell = cells[-1]
            label = " ".join(text(s[1]) for s in _STRONG.findall(body_cell))
            label = " ".join(label.split())
            if not label:
                continue
            clause = CLAUSE.search(label)
            category = re.sub(r"\(\s*s(ection)?\.?\s*$", "", CLAUSE.sub("", label)).strip(" :;,-–")
            if WITHHELD.search(category):
                withheld[(category, "real property, a home, an address or a contact: never read")] += 1
                continue
            if PRIVATE_PERSON.search(category):
                withheld[(category, "a spouse's or partner's interests: a private person, never read")] += 1
                continue
            plain = _STRONG.sub(" ", body_cell)
            entries = []
            for p in (_P.findall(plain) or [plain]):
                e = text(p)
                if not e or NIL.match(e):
                    continue
                if withheld_entry(e):
                    withheld[(category, "an entry shaped like an address, an email or a phone number: dropped")] += 1
                    continue
                entries.append(e)
            rows.append({"member": name, "role": role, "category": category,
                         "clause": clause.group(1).lower() if clause else None, "entries": entries,
                         "document": sha, "page": 1, "place": f"table {ti}, row {ri}", "url": url})
    return {"as_at": as_at, "members": members, "rows": rows, "withheld": withheld}
