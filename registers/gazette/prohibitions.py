"""Notices prohibiting a person from managing companies (profile
`gazette-director-prohibition`): recognised, then read. No model.

One template since 2001, printed under section `ot` (a few under `go` and
`gn`): the person, then their address, then the operative words.

  Pursuant to Section 385 of the Companies Act 1993 To: <name>. Of:
  <address>. Pursuant to section 385(1) …, I, <officer>, Deputy Registrar
  of Companies, hereby prohibit <name> from being a director or promoter
  of … for a period of <years and months> as from the date of this
  notice. Dated at Wellington this <n>th day of <Month> <year>.

The old reader (`data-layer/gazette_register/parse.py`, parse_prohibition)
took the `To:`/`Of:` fields and published the address with the name. Here
the address goes to the private schema only (hard limit 15), and the
operative words say which of six things the notice is:

  prohibition       the Registrar's own (Companies Act s 385)
  court order       the Registrar gives notice of a court's order (s 382 and
                    383): "by order of the High Court at …"
  banning order     the Financial Markets Conduct Act's (s 108 and 109)
  variation         a court has set aside the Registrar's term and directed
                    another; names the notice it varies
  substitution      a prohibition with a note that it revokes an earlier
                    notice, named, and is substituted for it
  revocation        revokes a named notice, and names nobody to prohibit: a
                    notice revoked "as published in error" may name the
                    person it wrongly identified, which is never read

A person's name is printed twice, in the `To:` field and in the operative
sentence; `named_twice` says whether both agree. A field `Formerly of:` is
an address too. An alias in brackets ("also known as …") is kept apart from
the name.

    recognise(title, text)   the reasons, empty if not this profile
    read(text)               Reading(action, statute, months, permanent, starts_on, …, persons, acts_on, unread)
"""
import calendar
import re
from dataclasses import dataclass, field

from keys.dates import filed_date

_ACTS = r"(?:Companies Act 1993|Financial Markets Conduct Act 2013)"
_TITLE = re.compile(r"prohibiting\s+(?:a\s+)?persons?\b", re.I)
_OPERATIVE = re.compile(r"hereby\s+prohibit\b|is\s+(?:permanently\s+)?prohibited|banning\s+order|"
                        r"made\s+an\s+order\s+on|must\s+not\b|hereby\s+revokes|revoked\s+the\s+notice\s+of\s+prohibition", re.I)
_DIRECTOR = re.compile(r"director\s+or\s+promoter|concerned\s+in|taking\s+part|management\s+of", re.I)
_TO = re.compile(r"To\s*:\s*")
_OF = re.compile(r"\.?\s*(?P<formerly>Formerly\s+)?Of\s*:\s*", re.I)
#: what closes an address: the operative sentence, the case heading of a banning order, the next person
_ADDRESS_END = re.compile(r"Pursuant\s+to\b|\bTo\s*:|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*:\s+(?:Financial|[A-Z][a-z]+\s+v\b)|"
                          r"In\s+the\s+matter|Re\s*:", re.S)
_ALIAS = re.compile(r"\s*\((?P<cue>also known as|formerly known as|known as|aka|also)?\s*(?P<a>[^)]*)\)", re.I)
_SECTION = re.compile(rf"[Ss]ection\s+(?P<s>\d+[A-Z]?(?:\s*\(\w+\))*(?:\s*,?\s*(?:\(\w+\)|and\s+\(\w+\)))*)\s+of\s+the\s+(?P<act>{_ACTS})")
_DATED = re.compile(r"Dated\b[^.]{0,60}?\b(?P<d>\d{1,2})(?:st|nd|rd|th)?\s+(?:day\s+)?(?:of\s+)?(?P<m>[A-Z][a-z]+),?\s+(?P<y>\d{4})")
_DAY = r"\d{1,2}(?:st|nd|rd|th)?\s+[A-Z][a-z]+,?\s+\d{4}"
_STARTS = re.compile(rf"took\s+effect\s+(?:from|on)\s+(?P<d>{_DAY})|(?:makes|made)\s+(?:a\s+banning\s+order|an\s+order)\s+on\s+(?P<o>{_DAY})|"
                     rf"for\s+a\s+term\s+of\s+.{{0,60}}?\bfrom\s+(?P<t>{_DAY})", re.S)
_FROM_NOTICE = re.compile(r"from\s+the\s+date\s*of\s*this\s+notice|from\s+the\s+date\s+the\s+banning\s+order\s+was\s+made", re.I)
_PERIOD = re.compile(r"for\s+(?:a|the)\s+(?:period|term)\s+of\s+(?P<p>.{1,60}?)(?=\s*(?:as\s+from|from|,|without|\.|$))", re.I | re.S)
_PERMANENT = re.compile(r"permanently\s+prohibited", re.I)
_REFERS = re.compile(r"Notice\s+No\.?\s*(?P<y>\d{4})\s*[‐‑–\-]\s*(?P<c>[a-z]{2})\s*(?P<n>\d+)")
_SET_ASIDE = re.compile(r"has\s+set\s+aside", re.I)
_REVOKES = re.compile(r"hereby\s+revokes", re.I)
_REVOKED_NOTE = re.compile(r"revoked\s+the\s+notice\s+of\s+prohibition", re.I)
_COURT = re.compile(r"by\s+order\s+of\s+the\b", re.I)
_FMC = re.compile(r"Financial\s+Markets\s+Conduct\s+Act", re.I)

_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20}


def recognise(title: str, text: str) -> list:
    """The reasons this notice is a prohibition from managing companies;
    empty if not. The Companies Act or the Financial Markets Conduct Act and
    the management words are both required: "hereby prohibit" alone is also
    a drug-prescribing order, a vaccine notice and a fisheries rule."""
    text = text or ""
    why = []
    if _TITLE.search(title or ""):
        why.append("title: prohibiting a person")
    if _OPERATIVE.search(text) and re.search(_ACTS, text) and (_DIRECTOR.search(text) or _REVOKES.search(text)):
        why.append("operative words under the Companies Act or the Financial Markets Conduct Act")
    return why if len(why) == 2 or (why and why[0].startswith("operative") and _TO.search(text)) else []


def months(phrase: str):
    """'four years and six months', '5 years', 'two-and-a-half years' → months; None if unread."""
    p = phrase.lower().replace("-", " ")
    total, found = 0, False
    for n, unit in re.findall(r"(\d+|[a-z]+(?: and a half)?)\s+(years?|months?)", p):
        half = n.endswith(" and a half")
        n = n.replace(" and a half", "")
        v = int(n) if n.isdigit() else _NUM.get(n)
        if v is None:
            return None
        total += (v * 12 + (6 if half else 0)) if unit.startswith("year") else v
        found = True
    return total if found else None


def _date(text):
    """'9th day of May 2016', '9 May 2016' → ISO date, or None."""
    if not text:
        return None
    d = filed_date(re.sub(r"(\d)(?:st|nd|rd|th)?\s+day\s+of\s+", r"\1 ", re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", text)))
    return d.isoformat() if d else None


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip(" .,;:")


def _key(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


@dataclass
class Person:
    ordinal: int
    name: str
    also_known_as: str = None
    address: str = None          # private: never published
    formerly: bool = False       # the address was printed "Formerly of:"
    named_twice: bool = False    # the operative sentence names the same person
    printed: str = field(default=None, repr=False)   # the `To:` field as printed, aliases in place


@dataclass
class Reading:
    action: str = None
    statute: str = None
    months: int = None
    permanent: bool = False
    starts_on: str = None
    starts_basis: str = None     # stated | date of the notice
    dated_on: str = None
    acts_on: list = field(default_factory=list)     # notice numbers revoked, substituted or varied
    persons: list = field(default_factory=list)
    unread: list = field(default_factory=list)      # (place, why)


def _persons(text: str) -> tuple:
    out, bad = [], []
    starts = [m for m in _TO.finditer(text)]
    for i, m in enumerate(starts, 1):
        nxt = starts[i].start() if i < len(starts) else len(text)
        of = _OF.search(text, m.end(), nxt)
        if not of:
            bad.append((f"person {i}", "no `Of:` closes the name"))
            continue
        raw = text[m.end():of.start()]
        aliases = [_clean(a.group("a")) for a in _ALIAS.finditer(raw)]
        name = _clean(_ALIAS.sub(" ", raw))
        if not name or len(name) > 80 or re.search(r"\d|Pursuant|Companies Act", name):
            bad.append((f"person {i}", "the `To:` field is not a name"))
            continue
        end = _ADDRESS_END.search(text, of.end(), nxt if nxt > of.end() else len(text))
        address = _clean(text[of.end():end.start() if end else nxt])
        out.append(Person(i, name, "; ".join(a for a in aliases if a) or None, address or None, bool(of.group("formerly")),
                          printed=_clean(raw)))
    return out, bad


_WHOLE = re.compile(r"Dated\b[^.]{0,60}?\d{4}\.(?=.{0,200}?To\s*:)", re.S)


def read(text: str) -> Reading:
    """One notice. A capture that ran two whole notices together (two
    templates, each with its `Dated`) is read as each; the people are kept
    when both say the same thing, else the notice is set aside."""
    text = text or ""
    cuts = [m.end() for m in _WHOLE.finditer(text)]
    if not cuts:
        return _read_one(text)
    parts = [_read_one(t) for t in (text[a:b] for a, b in zip([0] + cuts, cuts + [len(text)])) if t.strip()]
    first = parts[0]
    same = all((p.action, p.statute, p.months, p.permanent, p.starts_on, p.dated_on)
               == (first.action, first.statute, first.months, first.permanent, first.starts_on, first.dated_on)
               for p in parts)
    if not same:
        return Reading(action=first.action, unread=[("notice", f"{len(parts)} notices printed as one, with different terms")])
    first.persons = [x for p in parts for x in p.persons]
    for i, x in enumerate(first.persons, 1):
        x.ordinal = i
    first.unread = [u for p in parts for u in p.unread]
    return first


def _read_one(text: str) -> Reading:
    r = Reading()
    refs = [f"{m.group('y')}-{m.group('c')}{int(m.group('n'))}" for m in _REFERS.finditer(text)]
    if _REVOKES.search(text) and not _TO.search(text):
        r.action, r.acts_on = "revocation", refs
    elif _SET_ASIDE.search(text):
        r.action, r.acts_on = "variation", refs
    elif _REVOKED_NOTE.search(text):
        r.action, r.acts_on = "substitution", refs
    elif _FMC.search(text):
        r.action = "banning order"
    elif _COURT.search(text):
        r.action = "court order"
    elif re.search(r"hereby\s+prohibit\b", text, re.I):
        r.action = "prohibition"
    else:
        r.unread.append(("notice", "no operative words the reader knows"))
        return r
    if r.action in ("revocation", "variation", "substitution") and not refs:
        r.unread.append(("notice", f"a {r.action} that names no notice by number"))
    secs = list(_SECTION.finditer(text))
    if secs:
        best = max(secs, key=lambda m: ("(" in m.group("s"), -m.start()))
        r.statute = f"{best.group('act')} s {re.sub(r'\s+', '', best.group('s'))}"
    d = _DATED.search(text)
    r.dated_on = _date(f"{d.group('d')} {d.group('m')} {d.group('y')}") if d else None
    if r.action == "revocation":
        return r                 # it prohibits nobody; a name in it is never read
    r.permanent = bool(_PERMANENT.search(text))
    tail = text[_SET_ASIDE.search(text).end():] if r.action == "variation" else text
    p = _PERIOD.search(tail)
    if p:
        r.months = months(p.group("p"))
        if r.months is None:
            r.unread.append(("period", "a period the reader cannot count"))
    elif not r.permanent:
        r.unread.append(("period", "no period and not permanent"))
    s = _STARTS.search(tail)
    if s:
        r.starts_on, r.starts_basis = _date(s.group("d") or s.group("o") or s.group("t")), "stated"
    elif _FROM_NOTICE.search(tail) and r.dated_on:
        r.starts_on, r.starts_basis = r.dated_on, "date of the notice"
    r.persons, bad = _persons(text)
    r.unread += bad
    if not r.persons and not bad:
        r.unread.append(("notice", "no `To:` names the person"))
    body = _key(text[text.find("Pursuant to section", 20):] if "Pursuant to section" in text[20:] else text)
    for x in r.persons:
        x.named_twice = _key(x.name) in body or _key(x.printed) in body
    return r


def ends_on(starts_on: str, months_: int):
    """The day a term of whole months ends, from its start; None where either is unknown."""
    if not starts_on or months_ is None:
        return None
    y, m, d = (int(v) for v in starts_on.split("-"))
    m0 = m - 1 + months_
    y, m = y + m0 // 12, m0 % 12 + 1
    return f"{y:04d}-{m:02d}-{min(d, calendar.monthrange(y, m)[1]):02d}"
