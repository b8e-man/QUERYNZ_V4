"""Incorporated societies and charitable trust boards dissolved, revived or
about to be (profile `gazette-society-dissolution`): every notice in the
Gazette's sections `is` and `ct` whose title dissolves, revokes a
dissolution, or gives notice of an intention to remove or restore
(Incorporated Societies Act 1908 s 28 and 2022 Act, Charitable Trusts Act
1957 s 26). No model.

The Registrar's notice is a list: an opening sentence ("The Registrar …
is satisfied that these societies are no longer carrying on their
operations and hereby declares them to be dissolved …:"), then each body's
name and its registration number ("ABLE TENNIS CLUB INCORPORATED 123456."),
a revocation printing the dissolution's day after the number ("… 123456 (3
May 2004)."), up to "Dated". A row is the text up to the next number; one
that reads as prose, or a list with no numbers, is a catch-log line. A
notice to dissolve on a body's own request ("I have received a request …")
is read the same way. No address is printed or read. A direction for the
disposition of a dissolved body's surplus assets and an application to vary
a trust are not this profile.

    recognise(code, title, text)    the reasons, empty if not this profile
    read(title, text)               Reading(shape, companies, action, statute, …, unread)
"""
import re

from registers.gazette import liquidations as LQ
from registers.gazette.entries import Entry, Reading

CODES = ("is", "ct")
#: the registers a printed number is looked up in (register.py): the societies' and the trust boards'
REGISTERS = ("other_incorporated", "charitable_trust_board")
TITLE = re.compile(r"\b(?:dissolution|revocation|revoking|intention\s+to\s+(?:remove|restore|dissolve)|restor\w*|"
                   r"removal\s+of\s+(?:\w+\s+){0,3}(?:societ|trust))", re.I)
_NOT = re.compile(r"\bdisposition\b|\bsurplus\s+assets\b|\bscheme\b|\bvar(?:y|iation)\b|\bfinancial\s+statements\b", re.I)
_DATE = r"\d{1,2}(?:st|nd|rd|th)?\s+[A-Z][a-z]+\s+\d{4}"
#: a row: the name up to its registration number, the dissolution's day after it where printed ("(3 May 2004)", or the
#: older "Date of Dissolution: 2 October 1997.")
_ROW = re.compile(rf"(?P<name>.+?)\s*[(\[]?(?P<n>(?<![\d/])\d{{5,8}}(?!\d))[)\]]?"
                  rf"(?:\s*\((?P<d>[^()]{{0,40}})\)|\s*Date\s+of\s+\w+\s*:\s*(?P<d2>{_DATE}))?\s*[.;,]?\s*", re.S)
#: a list that prints no numbers: each name ends in its legal word and the day in brackets
_ROW_DATED = re.compile(rf"(?P<name>.+?)\s*\((?P<d>{_DATE})\)\s*[.;,]?\s*", re.S)
_END = re.compile(r"\bDated\b|\bAny\s+(?:person|objection)|\bObjections?\b|\bUnless\b|\b\w+\s+this\s+publication\b", re.I)
#: the opening's end: a colon, or a stop after a word of prose or the Act's year (never "Inc." or "N.Z.")
_OPEN_END = re.compile(r":|(?<=[a-z]{3})\.(?!\d)|(?<=Act \d{4})\.")
#: the old registry office's letters after a name: "I.S.", "C.T.", "AK.", "WN" ("… INCORPORATED AK. I.S. 123456")
_OFFICE = re.compile(r"(?:\s+(?:(?:[A-Z]\.\s?){1,2}[A-Z]\.?|[A-Z]{2}\.?)(?=\s|$))+\s*$")
#: the older lists print the day before the name: "Date of Dissolution: 2 October 1997.ABLE CLUB INCORPORATED … 25692"
_DAY_FIRST = re.compile(rf"^\s*Date\s+of\s+\w+\s*:\s*(?P<d>{_DATE})\.?\s*")
#: words of the notice's own sentence, never of a body's name
_PROSE = re.compile(r"\b(?:is|are|has|have|was|were|that|hereby|satisfied|declared|dissolved|revoked|following|accordingly|"
                    r"carrying|operations|registrar|section)\b")


def titled(title: str) -> bool:
    """The title is this profile's: the check asks it of every such notice in is and ct."""
    return bool(TITLE.search(title or "")) and not _NOT.search(title or "")


def recognise(code: str, title: str, text: str) -> list:
    if code not in CODES or not titled(title):
        return []
    return [f"the Gazette's section {code}, a notice that dissolves, revives or will remove or restore registered bodies"]


def _action(title: str, head: str) -> str:
    t = f"{title} {head}"
    if re.search(r"\brevo(?:cation|ked?|king)\b|\brevived\b", t, re.I):
        return "revocation of dissolution"
    if re.search(r"\bintend\s+to\s+restore\b|\bintention\s+to\s+restore\b|\brestor", t, re.I):
        return "intention to restore"
    if re.search(r"\bintend\s+to\s+(?:remove|dissolve)\b|\bintention\s+to\s+(?:remove|dissolve)\b|\breceived\s+a\s+request\b", t, re.I):
        return "intention to dissolve"
    if re.search(r"\bdissol", t, re.I):
        return "dissolution"
    return None


def _start(text: str) -> int:
    """Where the list begins: after the opening's colon, else its first stop
    after prose before the first registration number."""
    first = re.search(r"(?<![\d/])\d{5,8}(?!\d)", text) or re.search(rf"\((?:{_DATE})\)", text)
    if not first:
        return -1
    ends = [m.end() for m in _OPEN_END.finditer(text, 0, first.start())]
    colon = text.rfind(":", 0, first.start())
    return colon + 1 if colon >= 0 else (ends[-1] if ends else 0)


def read(title: str, text: str) -> Reading:
    title, text = title or "", text or ""
    r = Reading(shape="list", by_whom="Registrar", corrigendum=bool(LQ._CORRIGENDUM.match(title) or LQ._CORRIGENDUM.match(text[:40])))
    sec = LQ._SECTION.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    r.action = _action(title, text[:500])
    if r.action is None:
        r.unread.append(("action", "the notice does not say what it does to the bodies it names"))
    pos = _start(text)
    if pos < 0:
        r.unread.append(("list", "the notice prints neither a registration number nor a dated list: its list is not cut"))
        return r
    end = _END.search(text, pos)
    seg = text[pos:end.start() if end else len(text)]
    rows, k = [], 0
    row = _ROW if re.search(r"(?<![\d/])\d{5,8}(?!\d)", seg) else _ROW_DATED
    for m in row.finditer(seg):
        k += 1
        name, day = LQ._clean(m.group("name")), m.group("d") or m.groupdict().get("d2")
        first = _DAY_FIRST.match(name)
        if first:
            name, day = name[first.end():], first.group("d")
        name = re.sub(rf"^{_DATE}\s*", "", re.sub(r"(INCORPORATED|Incorporated)(?=[A-Z]\.)", r"\1 ", name))
        name = _OFFICE.sub("", LQ._clean(name))
        if _PROSE.search(name):                       # a one-body notice: the name after the sentence's "that"
            name = re.sub(r"^.*\b(?:that|accordingly)\s*[:.]?\s*(?=[A-Z0-9“\"(])", "", name)
        name = LQ._clean(name)
        if not name or len(name) > 160 or _PROSE.search(name):
            r.unread.append((f"row {k}", "the text before a registration number is not a body's name"))
            continue
        rows.append(Entry(len(rows) + 1, name, number=m.groupdict().get("n"), event_on=LQ._date(day) if day else None))
    rest = LQ._clean(seg[max((m.end() for m in row.finditer(seg)), default=0):])
    rest = re.sub(r"[^.]*,\s*(?:Assistant\s+|Deputy\s+)?Registrar\b.*$", "", rest, flags=re.S)   # the signature
    if rest and re.search(r"[A-Z][a-z]+\s+[A-Z]|[A-Z]{3,}", rest) and not _PROSE.search(rest):    # prose: the sentence's end
        r.unread.append(("list", "the list's end the reader cannot cut"))
    if any(e.event_on for e in rows):
        r.event_basis = "dissolved on"           # the day a revocation undoes, or the older lists' "Date of Dissolution"
    r.companies = rows
    if not rows:
        r.unread.append(("list", "a list with no body the reader can take"))
    return r
