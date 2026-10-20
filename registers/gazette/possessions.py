"""A mortgagee's entry into possession (profile `gazette-mortgagee-possession`):
every notice in the Gazette's section `gn` whose title or opening words say a
mortgagee has entered into possession of mortgaged land or goods, or is
receiving the income from mortgaged property (Property Law Act 2007 s 156
and s 157, 1952 Act s 92 and its kin). No model.

The notice has no one form. Its parts, each read where printed:

  mortgagee   the lender: the name before "("the mortgagee")", ", the
              mortgagee", ", as mortgagee", or after "the mortgagee" or
              "Mortgagee:", else the subject of "… gives notice" or
              "… entered into possession"; with its company number where printed
  mortgagor   the borrower, where printed: after "the mortgagor",
              "Mortgagor:", "granted by", "in the matter of <company>", or
              before ", as mortgagor"; a company, a person, or not printed
  asset       land or goods: the title's word, else the text's
  entered_on  the day of entry: "with effect from <day>", else the day in
              the sentence that enters into possession
  property    the land's description (an address, often a home) or the
              goods' description; and the goods' registration numbers

A mortgagor who is a person, the property and the registration numbers go
to the private schema only (hard limit 15) and are never published,
printed or logged. A mortgagee read as a person is held the same way. A
part the reader cannot find is a catch-log line, never a guess; the text
of a part set aside is never kept.

    recognise(code, title, text)    the reasons, empty if not this profile
    read(title, text)               Reading(asset, action, mortgagee, mortgagor, entered_on, …, unread)
    public_title(title)             the title with any property it names cut off
    join(idx, party, on, year, glued)   (the name to show, register key, how)
    firm(name)                      whether a name with "and" in it is one body's
"""
import re
from dataclasses import dataclass, field

from registers.gazette import liquidations as LQ

CODE = "gn"
PROFILE = "gazette-mortgagee-possession"
_TITLE = re.compile(r"possession|mortgaged\s+(?:land|goods?|propert)|receipt\s+of\s+income", re.I)
_ENTRY = re.compile(r"(?:entered|enter|entering|enters|taken|take|taking|took|went)\s+(?:in)?to\s+possession|possession\s+of\s+the\s+mortgaged"
                    r"|entry\s+into\s+possession|(?:taken|took|take|taking)\s+possession", re.I)
_UNCLAIMED = re.compile(r"\bunclaimed\b", re.I)
_INCOME = re.compile(r"receipt\s+of\s+(?:the\s+)?income|receiv\w*\s+(?:the\s+)?income", re.I)
#: the end of a lender's or borrower's name
_ORG = (r"(?:Limited|LIMITED|Ltd|LTD|Incorporated|INCORPORATED|Inc|Bank|BANK|Corporation|CORPORATION|Society|SOCIETY|Council|COUNCIL|"
        r"Trustees?|TRUSTEES?|Company|COMPANY|Association|ASSOCIATION|Union|UNION|plc|PLC|N\.A|LP|Partnership|PARTNERSHIP|Trust|TRUST|"
        r"Board|BOARD|Authority|AUTHORITY|Custodians|CUSTODIANS|Nominees|NOMINEES)")
_ORG_END = re.compile(rf"\b{_ORG}\.?$|^(?:The\s+)?Bank\s+of\s+New\s+Zealand$")
_CONNECT = {"of", "and", "the", "for", "&", "de", "du", "la", "le", "van", "von", "der", "te", "in"}
_LEAD = re.compile(r"^(?:(?:the|Public|Take|Notice|NOTICE|TAKE|PUBLIC|Is|IS|Hereby|HEREBY|Given|GIVEN|That|THAT|The|THE|And|AND|Of|OF|"
                   r"In|IN|Matter|MATTER|Pursuant|PURSUANT|To|TO|By|BY)\s+)+")
#: a bracket that ends the name and is not its own: a number, a defined term, a status ("(in receivership)")
#: what runs into a name from before it: a day, a section of the Act
_FRONT = re.compile(rf"^(?:(?:On|on)\s+)?(?:(?:the\s+)?{LQ._DAY}|[A-Z][a-z]+\s+\d{{4}})\s*|^.*?\bAct\s+\d{{4}}\s*")
_TAIL = re.compile(r"\s*(?:\((?!\d{4}\))[^()]*(?:\d|[“\"”'‘]|\b(?:in|the|formerly|now|NZBN|No|Company|Number|trading|as)\b)[^()]*\)|[“\"”'‘,;\s])+$")
_NUMBER = re.compile(r"\(\s*(?:(?:NZ\s*)?Company\s+(?:No\.?|Number)\s*:?\s*|NZBN\s*:?\s*|No\.?\s*)?(?P<n>\d{4,8}|\d{13})\s*\)")

_MORTGAGEE_BEFORE = re.compile(r"\(\s*(?:together\s+)?[“\"”'‘]?\s*(?:the\s+)?[“\"”'‘]?\s*mortgagees?\b|,?\s+(?:as\s+|being\s+)(?:the\s+)?mortgagees?\b"
                               r"|,\s*(?:the\s+|a\s+)?mortgagees?\b", re.I)
_MORTGAGEE_AFTER = re.compile(r"\bthe\s+mortgagees?\s*,?\s*(?=[A-Z0-9])|\bmortgagees?(?:[’']s\s+(?:full\s+)?name)?\s*:\s*", re.I)
_SUBJECT_BEFORE = re.compile(r",\s*(?:whose|of|at|having)\s+(?:its\s+)?registered\s+office|\s*,?\s+(?:hereby\s+)?gives?\s+(?:public\s+)?notice"
                             r"|\s+(?:has|have)\s+(?:on\s+[^,.]{3,40},?\s+)?(?:entered|taken|taken\s+possession)|\s+(?:entered|took|went)\s+into\s+possession"
                             r"|\s+took\s+possession")
#: "<company> of <place>" or "at <place>": a company only
_SUBJECT_PLACE = re.compile(r"\s+(?:of|at)\s+(?:its\s+)?(?=[A-Z0-9])")
_SUBJECT_AFTER = re.compile(r"\b(?:notice\s+is\s+(?:hereby\s+)?given\s+that|take\s+notice\s+that|that)\s+(?:on\s+[^,]{3,40},\s*)?(?=[A-Z0-9])", re.I)

_MORTGAGOR_AFTER = re.compile(r"^\s*To\s*:\s*|\bthe\s+mortgagors?\s*,\s*(?=[A-Z0-9])|\bthe\s+mortgagors?\s+(?=[A-Z0-9])|\bmortgagors?(?:[’']s\s+(?:full\s+)?name)?\s*:\s*"
                              r"|\b(?:granted|given|executed)\s+by\s+(?!the\s+mortgagor)(?=[A-Z0-9])"
                              r"|\bmortgage\s+(?:by|from)\s+(?=[A-Z0-9])")
_MORTGAGOR_BEFORE = re.compile(r"\s*\(\s*[“\"”'‘]?\s*(?:the\s+)?[“\"”'‘]?\s*mortgagors?\b|,?\s+as\s+(?:the\s+)?mortgagors?\b|,\s*(?:the\s+)?mortgagors?\b", re.I)
_MATTER_OF = re.compile(r"\bin\s+the\s+matter\s+of\s+(?!(?:section|sections|mortgage|the|a|an|part|Part|Section|Mortgage|The)\b)(?=[A-Z0-9])", re.I)
_MORTGAGOR_WORD = re.compile(r"\bmortgagors?\b", re.I)

_WITH_EFFECT = re.compile(rf"with\s+effect\s+(?:from|on)?\s*(?:the\s+)?(?:on\s+)?(?P<d>{LQ._DAY})", re.I)
_DAY = re.compile(rf"(?P<d>{LQ._DAY})")
_ON_DAY = re.compile(rf"(?<![Dd]ated\s)\b(?:on|as\s+from|from)\s+(?:or\s+about\s+)?(?:the\s+)?(?P<d>{LQ._DAY})")
_GOODS = re.compile(r"mortgaged\s+goods?|security\s+agreement|registration\s+(?:no|number|plate)|\bVIN\b|serial\s+(?:no|number)|chattels?", re.I)
_LAND = re.compile(r"mortgaged\s+land|certificate\s+of\s+title|computer\s+(?:freehold|unit|leasehold)\s+register|record\s+of\s+title|\bLot\s+\d|\bDP\s*\d"
                   r"|fee\s+simple|land\s+registry|\bidentifier\b|unit\s+title|leasehold\s+estate", re.I)
_PROPERTY = re.compile(r"(?:description\s+of\s+the\s+(?:mortgaged\s+)?(?:land|property|properties|goods)\s+(?:is|are)?|mortgaged\s+(?:land|property|properties)\s+(?:is|are)"
                       r"|Description\s+of\s+(?:the\s+)?Mortgaged\s+Goods|propert(?:y|ies)\s+(?:situated\s+|located\s+|known\s+as\s+)?at|situated\s+at|known\s+as)\s*:?\s*", re.I)
_PROPERTY_END = re.compile(r"\.\s+The\s+address|The\s+address\s+to\s+which|Address\s+of\s+(?:the\s+)?Mortgagee|\bDated\b|\bSigned\b|\bcommunications\b", re.I)
_REGISTRATION = re.compile(r"\b(?:Registration|Rego|Reg\.?)\s*(?:No\.?|Number|Plate)?\s*[:.]?\s*:?\s*(?P<r>[A-Z0-9]{2,7})\b")
_VIN = re.compile(r"\b(?:VIN|Chassis\s+(?:No\.?|Number)|Serial\s+(?:No\.?|Number))\s*[:.]?\s*:?\s*(?P<r>[A-Z0-9\-]{5,20})\b", re.I)


@dataclass
class Party:
    name: str
    kind: str                     # company | person
    number: str = None


@dataclass
class Reading:
    asset: str = None             # land | goods | not stated
    action: str = "entry into possession"
    statute: str = None
    mortgagee: Party = None
    mortgagor: Party = None
    mortgagor_printed: bool = False
    glued: bool = False           # the mortgagee's name runs on from the borrowers' ("in the matter of <persons> <lender>"): private until the register parts them
    entered_on: str = None
    entered_basis: str = None     # with effect from | in the entry's sentence
    dated_on: str = None
    corrigendum: bool = False
    property: str = None          # private: the land's or the goods' description
    registration: str = None      # private: the goods' registration, VIN or serial numbers
    unread: list = field(default_factory=list)


#: a receiver's appointment over mortgaged property (Receiverships Act s 8) is the appointment profile's
_APPOINTMENT = re.compile(r"^\s*(?:Corrigendum\W*)?(?:Notice\s+of\s+)?(?:Re-?)?Appointments?\b(?!.*possession)", re.I | re.S)


def recognise(code: str, title: str, text: str) -> list:
    if code != CODE or _UNCLAIMED.search(title or "") or _APPOINTMENT.match(title or ""):
        return []
    if _TITLE.search(title or "") or _ENTRY.search((text or "")[:3000]):
        return ["the Gazette's section gn, a mortgagee's entry into possession or receipt of income"]
    return []


def public_title(title: str) -> str:
    """The title less a property it names ("… of the Property at <address>"), cut at its first "at" or the
    first word with a digit in it: a title is published, an address never."""
    return re.split(r"\s+(?:at|situated\s+at|known\s+as)\s+|\s+(?=\S*\d)", title or "", maxsplit=1, flags=re.I)[0].strip(" ,")


def _spaced(text: str) -> str:
    """The capture runs words together at a bracket or a stop ("(“the mortgage”)TEA Custodians", "2010.The"): part them."""
    return re.sub(r"(?<=[a-z\d)”\"’])\.(?=[A-Z][a-z])|(?<=[)”\":])(?=[A-Z])|(?<=\d{4})(?=[A-Z][a-z]|[A-Z]{2})", lambda m: m.group(0) + " ", text)


def _run_back(s: str) -> tuple:
    """The run of name words at the end of `s` and where it starts: capitalised words, digits, brackets and the
    few small words a name holds, back to the first word that is not one."""
    toks, depth = list(re.finditer(r"\S+", s))[-40:], 0
    out = []
    for m in reversed(toks):
        t = m.group(0)
        if depth or t.endswith(")") and "(" not in t:
            depth += t.count(")") - t.count("(")
            out.append(m)
            continue
        if t.endswith((":", ";")) or (t.endswith(".") and out and not re.fullmatch(r"(?:[A-Z]\.)+|Ltd\.|LTD\.|Co\.|N\.Z\.|No\.", t)):
            break
        if t[0].isupper() or t[0].isdigit() or t[0] in "&(“\"" or t in _CONNECT:
            out.append(m)
            if len(out) > 16:
                break
            continue
        break
    while out and out[-1].group(0).lower() in _CONNECT:
        out.pop()
    if not out:
        return "", len(s)
    return " ".join(m.group(0) for m in reversed(out)), out[-1].start()


def _tokens_back(s: str) -> str:
    return _run_back(s)[0]


def _tokens_forward(s: str) -> str:
    out = []
    for t in re.findall(r"\S+", s)[:20]:
        if t[0].isupper() or t[0].isdigit() or t[0] in "&(“\"" or t in _CONNECT:
            out.append(t)
            if t.endswith((",", ";", ":")) and not re.match(rf"{_ORG}\b", t) or t.endswith(".") and (
                    _ORG_END.search(t.rstrip(".")) or not re.fullmatch(r"(?:[A-Z]\.)+|Co\.|N\.Z\.|No\.|St\.", t)):
                break
            continue
        break
    return " ".join(out)


def _party(raw: str, forward: bool = False) -> Party:
    """A name and what it is, from the words around a marker; None where it is neither a company nor a person."""
    if not raw:
        return None
    s = LQ._clean(raw)
    number = None
    m = _NUMBER.search(s)
    if m:
        number = m.group("n")
    if forward:                                      # cut at the last legal ending in the run
        ends = list(re.finditer(rf"\b{_ORG}\b\.?(?:\s*\((?:N\.?Z\.?|New Zealand|\d{{4}})\))?", s))
        if ends:
            s = s[:ends[-1].end()]
        else:
            s = re.split(r"\s*[,(;]", s)[0]
    s = LQ._clean(_TAIL.sub("", s))
    if s.count("(") > s.count(")"):                  # a bracket the run opened and never closed is not the name's
        s = LQ._clean(s[:s.rfind("(")])
    c = list(re.finditer(rf",(?!\s*{_ORG}\b)", s))
    if c:                                            # a list or a date before the name: the name is after its last comma
        s = LQ._clean(s[c[-1].end():])
    s = LQ._clean(_FRONT.sub("", s))
    s = _LEAD.sub("", s)
    s = LQ._clean(re.sub(r"^(?:[“\"”'‘(]|\b(?:on|by)\b\s)+", "", s))
    if not s or len(s) > 160:
        return None
    if re.search(r"\bBank\s+of\s+New\s+Zealand\b", s):
        s = s[:re.search(r"\bBank\s+of\s+New\s+Zealand\b", s).end()]
    if _ORG_END.search(s) and not re.fullmatch(rf"{_ORG}\.?", s) and len(re.findall(r"\S+", s)) >= 2 or re.fullmatch(r"[A-Z]{2,5}", s):
        return Party(s, "company", number)
    words = s.replace(" and ", " ").split()
    if 2 <= len(words) <= 9 and all(re.fullmatch(r"[A-Z][\w’'\-]*\.?|[A-Z]\.?|van|de|der|von|du|le|la|te|&|,", w.rstrip(",")) for w in words) \
            and not re.search(r"\b(?:Property|Law|Act|Notice|Registry|Land|Mortgage|Section|Street|Road|Auckland|Wellington|Christchurch)\b", s):
        return Party(s, "person", number)
    return None


def _body(text: str) -> str:
    """The text before the mortgagee's own address and the signature: the parts are all there."""
    m = re.search(r"The\s+address\s+to\s+which|Address\s+of\s+(?:the\s+)?Mortgagee|\bSigned\s+by\b", text)
    return text[:m.start()] if m and m.start() > 200 else text[:4000]


def _mortgagee(body: str):
    """(the mortgagee, whether its name may run on from the borrowers' names)."""
    for m in _MORTGAGEE_BEFORE.finditer(body):
        before = body[max(0, m.start() - 400):m.start()]
        run, at = _run_back(before)
        p = _party(run)
        if p:
            return p, bool(re.search(r"\bmatter\s+of\s*$|\bTo\s*:\s*$", before[:at]))
    return _mortgagee_else(body), False


def _mortgagee_else(body: str):
    for m in _MORTGAGEE_AFTER.finditer(body):
        p = _party(_tokens_forward(body[m.end():m.end() + 300]), forward=True)
        if p:
            return p
    for m in _SUBJECT_BEFORE.finditer(body):
        p = _party(_tokens_back(body[max(0, m.start() - 400):m.start()]))
        if p:
            return p
    for m in _SUBJECT_PLACE.finditer(body[:1500]):
        p = _party(_tokens_back(body[max(0, m.start() - 400):m.start()]))
        if p and p.kind == "company":
            return p
    for m in _SUBJECT_AFTER.finditer(body):
        p = _party(_tokens_forward(body[m.end():m.end() + 300]), forward=True)
        if p and p.kind == "company":
            return p
    return None


def _mortgagor(body: str, mortgagee: Party):
    lender = LQ._key(mortgagee.name) if mortgagee else None
    found = []
    for m in _MORTGAGOR_AFTER.finditer(body):
        found.append(_party(_tokens_forward(body[m.end():m.end() + 300]), forward=True))
    for m in _MORTGAGOR_BEFORE.finditer(body):
        found.append(_party(_tokens_back(body[max(0, m.start() - 400):m.start()])))
    for m in _MATTER_OF.finditer(body[:1500]):
        p = _party(_tokens_forward(body[m.end():m.end() + 300]), forward=True)
        found.append(p if p and p.kind == "company" else None)
    return next((p for p in found if p and LQ._key(p.name) != lender and not re.search(r"\bmortgag", p.name, re.I)), None)


def _entered(text: str):
    m = _WITH_EFFECT.search(text)
    if m:
        return LQ._date(m.group("d")), "with effect from"
    for e in _ENTRY.finditer(text):
        a = max(text.rfind(". ", 0, e.start()), text.rfind(".\n", 0, e.start()), 0)
        b = text.find(". ", e.end())
        b = len(text) if b < 0 else b
        days = [d for d in _DAY.finditer(text, a, b)
                if not re.search(r"(?:dated|of|mortgage|agreement)\s+(?:on\s+or\s+about\s+)?(?:the\s+)?$", text[max(0, d.start() - 30):d.start()], re.I)]
        if days:
            d = min(days, key=lambda d: abs(d.start() - e.start()))
            return LQ._date(d.group("d")), "in the entry's sentence"
    m = _ON_DAY.search(_body(text))
    if m:
        return LQ._date(m.group("d")), "the notice's first 'on' or 'as from' day"
    return None, None


def _asset(title: str, text: str) -> str:
    if re.search(r"\bgoods?\b", title, re.I):
        return "goods"
    if re.search(r"\bland\b", title, re.I):
        return "land"
    g, l = bool(_GOODS.search(text)), bool(_LAND.search(text))
    return "goods" if g and not l else "land" if l and not g else "not stated"


def read(title: str, text: str) -> Reading:
    title, text = title or "", _spaced(text or "")
    r = Reading(corrigendum=bool(LQ._CORRIGENDUM.match(title) or LQ._CORRIGENDUM.match(text[:40])))
    inc, entry = bool(_INCOME.search(f"{title} {text[:1500]}")), bool(_ENTRY.search(f"{title} {text[:3000]}"))
    r.action = ("entry into possession and receipt of income" if entry else "receipt of income") if inc else "entry into possession"
    sec = LQ._SECTION.search(text)
    if sec:
        r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}"
    else:
        a = re.search(r"Property\s+Law\s+Act\s+(\d{4})", text)
        r.statute = f"Property Law Act {a.group(1)}" if a else None
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    r.asset = _asset(title, text)
    body = _body(text)
    r.mortgagee, r.glued = _mortgagee(body)
    if r.mortgagee is None:
        r.unread.append(("mortgagee", "no mortgagee the reader can name"))
    r.mortgagor = _mortgagor(body, r.mortgagee)
    r.mortgagor_printed = bool(r.mortgagor or _MORTGAGOR_WORD.search(body))
    r.entered_on, r.entered_basis = _entered(text)
    if r.entered_on is None:
        r.unread.append(("day", "no day of entry the reader can find"))
    p = _PROPERTY.search(body)
    if p:
        e = _PROPERTY_END.search(text, p.end())
        r.property = LQ._clean(text[p.end():e.start() if e and e.start() - p.end() < 800 else p.end() + 600]) or None
    regs = [m.group("r") for m in _REGISTRATION.finditer(body) if re.search(r"\d", m.group("r"))] + [m.group("r") for m in _VIN.finditer(body)]
    r.registration = "; ".join(dict.fromkeys(regs)) or None
    return r


def firm(name: str) -> bool:
    """A name that joins two with "and" or "&" and is still one body's: one word before it ("Smith & Jones
    Limited") or a word only a body's name holds ("Bank", "Nominees")."""
    head = re.split(r"\s(?:and|&)\s", name, maxsplit=1)[0]
    return bool(_ORG_END.search(name)) and (len(head.split()) == 1 or bool(re.search(
        r"\b(?:Bank|Finance|Financial|Trust|Trustees?|Nominees?|Custodians|Holdings|Investments?|Securities|Mortgages?|Lawyers|"
        r"Solicitors|Partners|Group|Company|Corporation|Society|Credit|Capital|Funding|Lending|Properties|Property|Services)\b", head, re.I)))


def join(idx, party: Party, on, year: int, glued: bool = False) -> tuple:
    """(the name to publish, register key, how) for a company party, against register.Index `idx`. A name
    printed without its legal ending is tried with "Limited". A run that may begin with the borrowers' names
    (`glued`) publishes only the end of it whose name the register holds, else no name at all."""
    from registers.gazette import register as R
    words = party.name.split()
    tails = [" ".join(words[i:]) for i in range(len(words) - 1)] if glued else [party.name]
    last = R.NOT_HELD
    for name in tails:
        if glued and not _ORG_END.search(name):
            continue
        k, how = idx.match(name, party.number, on, year)
        if k is None and not re.search(r"\b(?:Limited|LIMITED|Ltd|LTD|Incorporated|INCORPORATED)\.?$", name):
            k2, how2 = idx.match(f"{name} Limited", None, on, year)
            if k2:
                k, how = k2, R.NAME_LIMITED
        if k and (not glued or how != R.NUMBER_NAME_DIFFERS):
            return name, k, how
        if k:
            return None, k, how                        # the number names the entity; the printed run is not shown
        last = how
    return (None if glued else party.name), None, last
