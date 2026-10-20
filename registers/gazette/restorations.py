"""The Registrar's notices of intention to restore a company to the register
(profile `gazette-restoration-notice`): every notice in the Gazette's
section `ot` ("companies: other") whose title or opening words restore a
company or a limited partnership (Companies Act 1993 s 328/329, Limited
Partnerships Act 2008). No model.

The notice is a list, one company or many: "Take notice that the Registrar
of Companies proposes to restore the following companies to the Register,
on the application of the persons named below …: ABLE LIMITED. Applicant:
<a person or a firm>, <their address>. BAKER LIMITED (123456). Applicant:
…". The applicant is often a person and the address often a home, so
neither is read: each company is the text before an "Applicant:", less
everything up to the last comma (an address always has one, a company's
name almost never) and the address's closing town or postcode. A row that
does not then end in a legal suffix is a catch-log line, never a guess.
The day objections close is read where printed.

    recognise(code, title, text)    the reasons, empty if not this profile
    read(title, text)               Reading(shape, companies, action, statute, event_on, …, unread)
"""
import re

from registers.gazette import liquidations as LQ
from registers.gazette.entries import Entry, Reading

CODE = "ot"
_RESTORE = re.compile(r"\brestor(?:e|es|ed|ing|ation)\b", re.I)
_APPLICANT = re.compile(r"\bApplicants?\s*:", re.I)
_LIST_END = re.compile(r"\bAny\s+person\b|\bAny\s+objections?\b|\bObjections?\s+(?:to|must|should)\b|\bDated\b|\bUnless\b", re.I)
#: the end of the address before a name: a postcode or a word, then a stop ("Auckland 1010." "Wellington.")
_ADDRESS_END = re.compile(r"^.*?(?:\d|[a-z])\.\s*", re.S)
#: a number after the name, perhaps behind the old registry office's two letters ("Limited. AK. 123456.")
_NAME = re.compile(rf"^(?P<name>[A-Z0-9(“\"](?:[^,]|,(?=\s*{LQ._SUFFIX}\b))*?(?:\b{LQ._SUFFIX}|\bLP)\b\.?(?:\s*\([^()]*\))*)\s*"
                   rf"(?:\.?\s*(?:[A-Z]{{2}}\s*\.?\s*)?\(?(?P<n>\d{{4,8}})\)?\s*)?\.?\s*$")
#: the last comma that is the address's, not one inside a name ("Able Company, Limited")
_LAST_COMMA = re.compile(rf",(?!\s*{LQ._SUFFIX}\b)(?!.*,(?!\s*{LQ._SUFFIX}\b))", re.S)
_OBJECT_BY = re.compile(rf"\bobject\w*\b[^.]{{0,200}}?\bby\s+(?:[A-Z][a-z]+day,?\s+)?(?:the\s+)?(?P<d>{LQ._DAY})")


def recognise(code: str, title: str, text: str) -> list:
    if code != CODE:
        return []
    if _RESTORE.search(title or "") or re.search(r"\bpropose[sd]?\s+to\s+restore\b|\bintend\s+to\s+restore\b", (text or "")[:600], re.I):
        return ["the Gazette's section ot, a notice that restores a company to the register"]
    return []


def _name(tail: str):
    """(name, number) where `tail` is a company's name and nothing else, else None."""
    m = _NAME.match(re.sub(r"^\s*Section\s+\d+\w*(?:\s*\(\s*\w+\s*\))*\s*", "", LQ._clean(tail)))
    if not m:
        return None
    name, number = m.group("name"), m.group("n")
    b = re.search(r"\s*\((\d{4,8})\)\s*$", name)
    if b:
        name, number = name[:b.start()], number or b.group(1)
    name = LQ._clean(LQ._PAREN.sub(" ", name))
    if (len(name) > 160 or re.search(r"\b(?:Street|Road|Box|Avenue|Drive|Place|Level)\b", name) or re.fullmatch(LQ._SUFFIX, name)
            or re.search(r"\b[a-z]{2,}\s+[a-z]{2,}\b", name)):
        return None
    return name, number


def _row(piece: str):
    """The company at the end of the text before an "Applicant:", or None."""
    piece = LQ._clean(piece)
    c = _LAST_COMMA.search(piece)
    tail = piece[c.end():] if c else piece
    if c:                                             # the applicant's address ran up to here: drop its last line
        tail = _ADDRESS_END.sub("", tail, count=1) if re.search(r"(?:\d|[a-z])\.\s*\S", tail) else ""
    return _name(tail)


def _first(head: str):
    """The first company, after the notice's opening words: the longest end
    of `head` after a sentence's stop that is a company's name and no prose."""
    head = LQ._clean(head)
    for m in re.finditer(r"(?:[a-z)\d]\.|:)\s*(?=\S)", head):
        got = _name(head[m.end():])
        if got:
            return got
    return None


def read(title: str, text: str) -> Reading:
    title, text = title or "", text or ""
    r = Reading(shape="list", action="intention to restore", by_whom="Registrar",
                corrigendum=bool(LQ._CORRIGENDUM.match(title) or LQ._CORRIGENDUM.match(text[:40])))
    if re.search(r"\bcourt\s+order\b", f"{title} {text[:300]}", re.I):
        r.action, r.by_whom = "court order restoring", "court"
    sec = LQ._SECTION.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    o = _OBJECT_BY.search(text)
    if o:
        r.event_on, r.event_basis = LQ._date(o.group("d")), "objections by"
    a = _APPLICANT.search(text)
    if not a:
        r.unread.append(("list", "no list of companies with their applicants the reader can find"))
        return r
    pieces = _APPLICANT.split(text[a.start():])[1:]
    heads = [text[:a.start()]] + pieces[:-1]
    end = _LIST_END.search(pieces[-1])
    rows = []
    for k, piece in enumerate(heads):
        got = _first(piece) if k == 0 else _row(piece)
        if got:
            rows.append(got)
        else:
            r.unread.append((f"row {k + 1}", "the text before an applicant does not end in a company's name"))
    if end is None:
        r.unread.append(("list", "the list's end is not where the reader expects it"))
    r.companies = [Entry(i, n, number=num) for i, (n, num) in enumerate(rows, 1)]
    if not r.companies:
        r.unread.append(("list", "a restoration list with no company the reader can take"))
    return r
