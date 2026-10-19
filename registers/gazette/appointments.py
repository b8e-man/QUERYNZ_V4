"""Appointments to public office (profile `gazette-public-appointment`):
every notice in the Gazette's government, vice-regal, authority,
parliamentary or general sections (`go`, `vr`, `au`, `ps`, `gn`) whose
title begins "Appointment" ("Appointment to the X Board", "Appointment of
Judges of the District Court", "Appointment of a Member to the …"). No
model.

The notice's own fields: the body, from the title ("… to the <BODY>", "… of
the <BODY>", else what follows "Appointment of"); the statute (the first
Act and section cited); who appointed (the Governor-General, a Minister,
another, as the notice's words say); the term's start and end where
printed. Then the operative clause: after "appoint", "appoints",
"appointed" or "reappoint…", a list of appointees, each a name, perhaps
", of <town>" or a description (a place, or anything holding a digit, read past
and never kept: where an appointee lives is not part of the office), perhaps
"as", "to be", "be" or "to the" and a role, the list running to "for a term",
"to take effect", "commencing" or the sentence's end, its people separated
by ";", "and" or a bullet. An appointee whose name the reader cannot take
is a catch-log line, never a guess.

    recognise(code, title, text)    the reasons, empty if not this profile
    read(title, text)               Reading(body, statute, by_whom, starts_on, ends_on, people, unread)
"""
import re
from dataclasses import dataclass, field

from registers.gazette import liquidations as LQ

CODES = ("go", "vr", "au", "ps", "gn")
_TITLE = re.compile(r"^\s*(?:Corrigendum\W*)?(?:Notice\s+of\s+)?(?:Re-?)?Appointments?\b", re.I)
_BODY_TITLE = (r"\b{prep}\s+(?:the\s+)?(?P<body>(?:[A-Z(ĀĒĪŌŪ][\w’'()\-.,&]*|of|and|the|for|in|on|to|de|o|ki|te|ā|a)"
                         r"(?:\s+(?:[A-Z(ĀĒĪŌŪ][\w’'()\-.,&]*|of|and|the|for|in|on|to|de|o|ki|te|ā|a))*)\s*(?:\(Notice\s+No\.[^)]*\))?\s*$")
#: the body follows "to the" where the title has one ("Appointment of Members to the X Board"), else "of the", "on", "for"
_HONORIFIC = r"(?:(?:The\s+)?(?:Right\s+)?(?:Honourable|Hon\.?)|Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Miss|Professor|Prof\.?|Judge|Justice|Sir|Dame|Associate\s+Professor|Rt\.?\s+Rev\.?|Rev\.?|Reverend|Colonel|Major|Captain|Commander|Admiral|General|Brigadier|Lieutenant|Inspector|Superintendent|Sergeant|Constable)"
_WORD = r"[A-ZĀĒĪŌŪ][\w'’\-]*\.?"
_PARTICLE = r"(?:van|de|der|von|du|le|la|te|ter|di|da|O’|O'|Mc|bin|binti|al|el|ki|o)"
_NAME = rf"(?:{_HONORIFIC}\s+)*{_WORD}(?:\s+(?:{_WORD}|{_PARTICLE}))*?\s+{_WORD}(?:\s*\((?:also\s+known\s+as\s+)?[^)]{{1,60}}\))?"
_CLAUSE = re.compile(r"\b(?:re)?appoint(?:ed|s|ing)?\b(?:\s+(?:the\s+following|as\s+follows))?(?:\s+(?:persons?|people|members?))?\s*[:,]?\s*", re.I)
_END = re.compile(r"\bfor\s+(?:a|the)\s+(?:term|period)\b|\bto\s+take\s+effect\b|\bwith\s+effect\b|\bcommencing\b|\beffective\b|"
                  r"\bfrom\s+(?:the\s+)?(?:date|\d)|\bwho\s+(?:will|shall)\b|\bpursuant\b|\bunder\s+section\b|\bDated\b|\.\s+[A-Z]|\.\s*$")
#: one appointee from the next: ";", "and" before a name, a bullet, a line, or "…, of Town, " before the next "Name, of"
_ITEM_SPLIT = re.compile(r"\s*(?:;\s*(?:and\s+)?|,?\s+and\s+(?!(?:Deputy|Chair\w*|Member|President|Vice|Acting|Chief|Senior|Principal|Presiding|Associate|Assistant|Co-)\b)(?=(?:{h}\s+)?[A-Z][\w'’\-]*\s+[A-Z])|[•·?]\s*|\n|"
                         r",\s*(?=(?:{h}\s+)?(?:[A-Z][\w'’\-]*\.?\s+){{1,5}}[A-Z][\w'’\-]*,\s*(?:of|from)\s)|"
                         r"(?<=[a-z’'])(?<!Honourable)(?<!Right)(?<!Reverend)\s+(?=(?:Dr\.?|Professor|Mr\.?|Mrs\.?|Ms\.?|Sir|Dame)\s+[A-Z][\w'’\-]+\s+[A-Z]))\s*".format(h=_HONORIFIC))
_ITEM = re.compile(rf"^(?P<name>{_NAME})(?:\s*,\s*(?P<desc>[^;]{{1,160}}?))?(?:\s*,)?"
                   rf"(?:\s+(?:as|to\s+be|be|to(?=\s+the\b)|(?=an?\s)|(?=the\s))\s*(?P<role>.+?))?\s*[,.;]?\s*$")
#: "appointed to the <BODY> <names> as members": the names begin after the body's own word
_TO_BODY = re.compile(r"\s*to\s+the\s+(?:[A-ZĀĒĪŌŪ(][\w’'()\-]*\s+|(?:of|and|for|the|o|ki|te)\s+){0,10}"
                      r"(?:Board|Council|Authority|Commission|Committee|Trust|Tribunal|Fund|Agency|Panel|Institute|Corporation|"
                      r"Service|Foundation|Group|Bank|Court|Office|Centre|Museum|Library|Society|Forum)\b(?:\s*\([^)]*\))?\s*[:,]?\s*")
_NOT_PERSON = re.compile(r"\b(?:Act|Board|Council|Authority|Commission|Committee|Ministry|Minister|Department|Court|Tribunal|"
                         r"Trust|Limited|Company|Corporation|Society|University|School|Zealand|Government|Crown|Governor|"
                         r"Pursuant|Section|Notice|Gazette|Regulations?|Order|Schedule|January|February|March|April|May|"
                         r"June|July|August|September|October|November|December|Her|His|Majesty|Excellency|Member|Members|"
                         r"Chairperson|Chair|Deputy|Following|Persons?)\b")
_BY = (("Governor-General", r"Governor[\s‑-]+General"), ("the Sovereign", r"\bHer\s+Majesty|\bHis\s+Majesty|\bthe\s+King\b|\bthe\s+Queen\b"),
       ("a Minister", r"\bMinister\b"), ("a Chief Justice or Chief Judge", r"\bChief\s+(?:Justice|Judge)\b"))
_TERM_END = re.compile(rf"(?:expiring|ending|until|to|and\s+(?:ending|expiring)\s+on)\s+(?:on\s+)?(?:the\s+)?(?P<d>{LQ._DAY})", re.I)
_TERM_START = re.compile(rf"(?:commencing|starting|effect(?:ive)?\s+(?:from|on)|take\s+effect\s+on|from)\s+(?:on\s+)?(?:the\s+)?(?P<d>{LQ._DAY})", re.I)


@dataclass
class Appointee:
    ordinal: int
    name: str
    role: str = None


@dataclass
class Reading:
    body: str = None
    statute: str = None
    by_whom: str = None
    starts_on: str = None
    ends_on: str = None
    dated_on: str = None
    corrigendum: bool = False
    people: list = field(default_factory=list)
    unread: list = field(default_factory=list)


def recognise(code: str, title: str, text: str) -> list:
    return ["an appointment to public office: a government section, titled 'Appointment…'"] if code in CODES and _TITLE.match(title or "") else []


def _body(title: str) -> str:
    t = re.sub(r"\s*\(Notice\s+No\.[^)]*\)\s*$", "", title or "")
    for prep in ("to", "of", "on", "for"):
        m = re.search(_BODY_TITLE.replace("{prep}", prep), t)
        if m:
            return LQ._clean(m.group("body"))
    m = re.match(r"^\s*(?:Corrigendum\W*)?(?:Notice\s+of\s+)?(?:Re-?)?Appointments?\s+of\s+(?P<b>.+)$", t, re.I)
    return LQ._clean(m.group("b")) if m else None


def _person(item: str):
    """(name, role) from one appointee's words, or None."""
    m = _ITEM.match(LQ._clean(item))
    if not m:
        return None
    name = LQ._clean(m.group("name"))
    bare = re.sub(rf"^(?:{_HONORIFIC}(?:\s+|$))+", "", name)
    if _NOT_PERSON.search(bare) or len(bare.split()) < 2 or len(re.sub(r"\s*\([^)]*\)", "", bare).split()) > 5 or re.search(r"\d", bare):
        return None
    desc = LQ._clean(m.group("desc") or "")
    if re.match(r"(?:of|from)\b", desc) or re.search(r"\d", desc):
        desc = ""                 # where the appointee lives is not part of the office, and is never kept
    role = LQ._clean(" ".join(x for x in (desc, m.group("role") or "") if x)) or None
    return name, (role[:160] if role else None)


def read(title: str, text: str) -> Reading:
    title, text = title or "", text or ""
    r = Reading(corrigendum=bool(LQ._CORRIGENDUM.match(title)), body=_body(title))
    sec = LQ._SECTION.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    head = text[:800]
    r.by_whom = next((who for who, p in _BY if re.search(p, head)), None)
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    s, e = _TERM_START.search(text), _TERM_END.search(text)
    r.starts_on = LQ._date(s.group("d")) if s else None
    r.ends_on = LQ._date(e.group("d")) if e else None
    for c in _CLAUSE.finditer(text):
        start = c.end()
        if (b := _TO_BODY.match(text, start)):
            start = b.end()       # "appointed to the X Board Ann Example …"
        elif re.match(r"\s*(?:to|by|under|on|in|the\s+date|a\s+date|date|from|with)\b", text[start:start + 12], re.I):
            continue              # "appointed by …", "appointed under …": not the start of a name
        end = _END.search(text, start)
        span = text[start:end.start() + (1 if end and end.group(0).startswith(".") else 0) if end else len(text)]
        items = [i for i in _ITEM_SPLIT.split(span) if i and i.strip(" ,.;:")]
        got = [_person(i) for i in items]
        if not any(got):
            continue
        for i, g in enumerate(got):
            if g:
                r.people.append(Appointee(len(r.people) + 1, *g))
            else:
                r.unread.append((f"after appointee {len(r.people)}", "an appointee the reader cannot take as a name"))
        break
    if not r.people:
        r.unread.append(("appointees", "the notice names no appointee the reader can take"))
    return r
