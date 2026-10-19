"""Bankruptcy notices: every notice in the Gazette's section `ba`, recognised
by that code and then by its operative words, three profiles. No model.

  gazette-bankruptcy-list      the Official Assignee's adjudications, two forms:
      to about 2008  "The following persons were adjudicated bankrupt on the
                     dates (and times) below:" a date, then the people that
                     day: "SURNAME, Given Names, occupation, of <address>, at
                     10.30 a.m." (two people joined by "and" share one record)
      after          "The official assignee advises the following
                     bankruptcies:" "Surname, Given Names (also known as …),
                     <address> – 9 May 2012." repeated
  gazette-no-asset-procedure-list  the same newer form for "no asset procedures"
  gazette-bankruptcy-notice    one person: an annulment, a discharge, an
                     adjudication, a meeting or a dividend; the person read
                     where printed as "<Surname>, <Given>, <address>, was|who …"

Every person's address goes to the private schema and nowhere else (hard
limit 15); the occupation is kept. A record the reader cannot cut into a
name is a catch-log line, and its text is never kept. A person named in an
annulment is marked so the published view withholds the name (read.py), as
a revoked prohibition's person is.

    kind_of(code, title, text)   the profile slug, or None if not section ba
    read(slug, title, text)      Reading(kind, shape, persons, statute, court, unread)
"""
import re
from dataclasses import dataclass, field

from registers.gazette import liquidations as LQ

CODE = "ba"
LIST, NAP, NOTICE = "gazette-bankruptcy-list", "gazette-no-asset-procedure-list", "gazette-bankruptcy-notice"
_DAY = LQ._DAY
_OLD_HEAD = re.compile(r"following\s+(?:(?:persons?|people|bankrupts?|individuals?)\s+)?(?:were|was|have\s+been|has\s+been)\s+"
                       r"adjudicated\s+bankrupts?\b[^:]{0,80}:", re.I)
_NEW_HEAD = re.compile(r"(?:Official\s+Assignee|advises?)\b[^:.]{0,60}?\bthe\s+following\b(?P<what>[^:.]{0,40}?)\s*:", re.I)
#: the newer form's records each end in a dash and the day: "Surname, Given, <address> – 9 May 2012."
_DASHED = re.compile(rf"[–—-]\s*{_DAY}")
_WORD = r"[A-ZĀĒĪŌŪ][\w'’\-]*"
_NAME = rf"{_WORD}(?:\s+(?:{_WORD}|van|de|der|von|du|le|la|te|ter|di|da|O'|Mc))*"
_PERSON = re.compile(rf"^(?P<sur>{_NAME}),\s*(?P<given>{_NAME})"
                     rf"(?:\s*\((?:also\s+known\s+as|formerly(?:\s+known\s+as)?|aka|née|nee)\s*(?P<aka>[^)]*)\))?(?:,\s*(?P<rest>.*))?$", re.S)
_OCCUPATION = re.compile(r"^(?P<occ>[a-z][a-z /&'’\-]*?)(?:,\s*|\s+)(?=of\b)")
_TIME = re.compile(rf",?\s*at\s+(?P<t>{LQ._TIME})\s*$")
_FORMERLY = re.compile(r",?\s*(?:and\s+)?formerly\s+(?:of\s+)?", re.I)
_REC_START = rf"(?=\s*(?:{_NAME},\s*{_NAME}\s*(?:,|\(|\band\b)|{_DAY}|[A-Z]{{4,}}\b|$))"
_OLD_REC = re.compile(rf"[\s.;:]*(?P<rec>{_NAME},.*?)(?:\.{_REC_START}|\s*$)", re.S)     # a day's last record may have no stop
_LEAD = r"(?:\bof|\bagainst|\bfor|\badjudication\s+of|\bbankrupt|\bthat|\bdischarge\s+of|:)\s+"
_TAIL = r",?\s+(?:who\s+|was\s+|has\s+|is\s+|on\s+)"
#: one person: "SMITH, John Paul, <address>, was …" first; else "John Paul SMITH, of <address>, was …" (natural order: the
#: surname is the last word, or the words in capitals)
_SINGLE = re.compile(rf"{_LEAD}(?P<sur>{_NAME}),\s*(?P<given>{_NAME})(?:\s*\((?P<aka>[^)]*)\))?,\s*(?P<rest>.{{0,240}}?){_TAIL}", re.S)
_CAPWORD = r"[A-ZĀĒĪŌŪ][\w'’\-]+"
_NATURAL = re.compile(rf"{_LEAD}(?P<nat>{_CAPWORD}(?:\s+{_CAPWORD}){{1,4}})(?:\s*\((?P<aka>[^)]*)\))?(?:,\s*|\s+(?=of\s))"
                      rf"(?P<rest>.{{0,240}}?){_TAIL}", re.S)
_NOT_PERSON = re.compile(r"\b(?:High|Court|Official|Assignee|Insolvency|Act|Notice|Bankruptcy|Bankrupt|Adjudication|Annulment|"
                         r"Discharge|Limited|January|February|March|April|May|June|July|August|September|October|November|"
                         r"December|The|New|Zealand|Trustee|Service|Ministry)\b")
_ACTIONS = (("annulment", r"\bannul"), ("discharge", r"\bdischarg"), ("meeting", r"\bmeeting\s+of\s+creditors"),
            ("dividend", r"\bdividend"), ("adjudication", r"adjudicated\s+bankrupt|\badjudication\b"))


@dataclass
class Person:
    ordinal: int
    surname: str
    given_names: str
    also_known_as: str = None
    occupation: str = None
    address: str = None           # private: the reader's caller puts it in gazette_private only
    formerly: str = None          # private too
    event_on: str = None
    event_at: str = None


@dataclass
class Reading:
    kind: str = None              # adjudication | no asset procedure | annulment | discharge | meeting | dividend | other
    shape: str = None             # list | notice
    persons: list = field(default_factory=list)
    statute: str = None
    court: str = None
    dated_on: str = None
    unread: list = field(default_factory=list)      # (place, why): never the text


def kind_of(code: str, title: str, text: str):
    if code != CODE:
        return None
    head = (text or "")[:600]
    nap = bool(re.search(r"\bno[\s-]+asset\s+procedures?\b", f"{title} {head}", re.I))
    if _OLD_HEAD.search(head) or _NEW_HEAD.search(head) or (len(_DASHED.findall(head)) >= 2 and re.search(r"Bankrupt|Asset", title or "", re.I)):
        return NAP if nap else LIST
    return NOTICE


def _newer(text: str) -> bool:
    return not _OLD_HEAD.search(text[:600]) and len(_DASHED.findall(text[:1500])) >= 2


#: a name field that reads as an address: two words or more ending in a thoroughfare, or any digit. A single
#: word is a surname (Lane, Court, Way and Close are); a mis-cut record must not publish a street
_THOROUGHFARE = re.compile(r"\s(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Crescent|Cres|Terrace|Tce|Highway|Hwy|"
                           r"Grove|Parade|Square|Quay|Boulevard|Esplanade|Mews)\.?$")


def addressy(*fields) -> bool:
    return any(f and (re.search(r"\d", f) or _THOROUGHFARE.search(f.strip())) for f in fields)


def _clean(s):
    return re.sub(r"\s+", " ", s or "").strip(" .,;:—–-")


def _split_rest(rest: str) -> tuple:
    """(occupation, address, formerly, time) from what follows a name in the older lists."""
    rest = _clean(rest)
    t = _TIME.search(rest)
    at = _clean(t.group("t")) if t else None
    rest = rest[:t.start()] if t else rest
    o = _OCCUPATION.match(rest)
    occ = _clean(o.group("occ")) if o else None
    rest = rest[o.end():] if o else rest
    rest = re.sub(r"^of\s+", "", rest)
    f = _FORMERLY.search(rest)
    addr, formerly = (rest[:f.start()], rest[f.end():]) if f else (rest, None)
    return occ, _clean(addr) or None, _clean(formerly) or None, at


def _person(i, sur, given, aka=None):
    """A Person, or None where a name field reads as an address (the record is then set aside)."""
    sur, given, aka = _clean(sur), _clean(given), _clean(aka) or None
    return None if addressy(sur, given, aka) else Person(i, sur, given, aka)


ADDRESSY = "a record whose name reads as an address: set aside"


def _old_list(text: str, r: Reading) -> None:
    head = _OLD_HEAD.search(text)
    body = text[head.end():] if head else text
    days = list(re.finditer(_DAY, body))
    chunks = [(None, body)] if not days else [(d, body[d.end():days[i + 1].start() if i + 1 < len(days) else len(body)])
                                               for i, d in enumerate(days)]
    for d, chunk in chunks:
        on = LQ._date(d.group(0)) if d else None
        pos = 0
        while (m := _OLD_REC.match(chunk, pos)) and m.end() > pos:
            pos = m.end()
            rec = _clean(m.group("rec"))
            people = re.split(rf"\s+and\s+(?={_NAME},)", rec)
            last = _PERSON.match(people[-1])
            if not last or not last.group("rest"):
                r.unread.append((f"after person {len(r.persons)}", "a record the reader cannot cut into a name"))
                continue
            occ, addr, formerly, at = _split_rest(last.group("rest"))
            heads = [_PERSON.match(p + ", x") for p in people[:-1]]
            if not all(heads):
                r.unread.append((f"after person {len(r.persons)}", "a joint record the reader cannot cut into names"))
                continue
            people = [_person(len(r.persons) + 1 + i, h.group("sur"), h.group("given"), h.group("aka"))
                      for i, h in enumerate(heads + [last])]
            if not all(people):
                r.unread.append((f"after person {len(r.persons)}", ADDRESSY))
                continue
            for p in people:
                p.occupation, p.address, p.formerly, p.event_on, p.event_at = occ, addr, formerly, on, at
                r.persons.append(p)
        rest = _clean(chunk[pos:])
        if re.search(rf"{_NAME},\s*{_NAME}", rest) and not re.match(r"^OFFICIAL\s+ASSIGNEE", rest):
            r.unread.append((f"after person {len(r.persons)}", "the rest of a day's list the reader cannot cut"))


def _new_list(text: str, r: Reading) -> None:
    """The records are what lies between one "– <day>." ending and the next, so a record the reader cannot
    take costs only itself; a spaced dash inside a record separates its fields, as a comma does."""
    head = _NEW_HEAD.search(text[:600])
    pos = head.end() if head else 0
    for end in _DASHED.finditer(text, pos):
        rec = _clean(re.sub(r"\s+[–—-]\s+", ", ", text[pos:end.start()]))
        pos = end.end()
        if text[pos:pos + 1] == ".":
            pos += 1
        p = _PERSON.match(rec)
        if not p:
            r.unread.append((f"after person {len(r.persons)}", "a record the reader cannot cut into a name"))
            continue
        x = _person(len(r.persons) + 1, p.group("sur"), p.group("given"), p.group("aka"))
        if not x:
            r.unread.append((f"after person {len(r.persons)}", ADDRESSY))
            continue
        x.address, x.event_on = _clean(p.group("rest")) or None, LQ._date(re.sub(r"^[–—-]\s*", "", end.group(0)))
        r.persons.append(x)
    if re.search(rf"{_NAME},\s*{_NAME},", text[pos:pos + 300]):
        r.unread.append((f"after person {len(r.persons)}", "the rest of the list the reader cannot cut"))


def _natural(nat: str) -> tuple:
    """(surname, given names) from a name in natural order: the words in capitals, else the last word."""
    words = nat.split()
    caps = [w for w in words if w.isupper() and len(w) > 1]
    if caps and words[-len(caps):] == caps:
        return " ".join(caps), " ".join(words[:-len(caps)])
    return words[-1], " ".join(words[:-1])


def _notice(title: str, text: str, r: Reading) -> None:
    t = f"{title} {text[:500]}"
    r.kind = next((k for k, p in _ACTIONS if re.search(p, t, re.I)), "other")
    m = _SINGLE.search(text)
    n = _NATURAL.search(text)
    if n and _NOT_PERSON.search(n.group("nat")):
        n = None
    if m and _NOT_PERSON.search(f"{m.group('sur')} {m.group('given')}"):
        m = None
    if m and n and n.start() < m.start():
        m = None                  # the natural-order name comes first: it is the person
    if m:
        x = _person(1, m.group("sur"), m.group("given"), m.group("aka"))
    elif n:
        x = _person(1, *_natural(n.group("nat")), n.group("aka"))
        m = n
    else:
        r.unread.append(("person", "the notice names no person the reader can find"))
        return
    if not x:
        r.unread.append(("person", ADDRESSY))
        return
    rest = _clean(m.group("rest"))
    o = _OCCUPATION.match(rest)                                   # "company director, of <address>"
    if o:
        x.occupation, rest = _clean(o.group("occ")), rest[o.end():]
    elif re.fullmatch(r"[a-z][a-z /&'’\-]*", rest):              # an occupation and no address
        x.occupation, rest = rest, ""
    x.address = re.sub(r"^of\s+", "", rest) or None
    for w in LQ._WHEN.finditer(text, m.end(), min(len(text), m.end() + 300)):
        x.event_on = LQ._date(w.group("d"))
        break
    r.persons.append(x)


def read(slug: str, title: str, text: str) -> Reading:
    title, text = title or "", text or ""
    r = Reading()
    sec = LQ._SECTION.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    c = re.search(r"\bHigh\s+Court\s+(?:at|in)\s+(?P<p>[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
    r.court = f"High Court at {c.group('p')}" if c else None
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    if slug == NOTICE:
        r.shape = "notice"
        _notice(title, text, r)
    else:
        r.shape, r.kind = "list", "no asset procedure" if slug == NAP else "adjudication"
        (_new_list if _newer(text) else _old_list)(text, r)
        if not r.persons:
            r.unread.append(("list", "a list with no record the reader can cut"))
    return r
