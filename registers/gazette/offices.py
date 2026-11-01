"""The office notices the appointment reader (appointments.py) does not take, because their titles do not begin
"Appointment…" (Arthur, 2 November 2026: "do it"). Five families, each its own profile, no model:

  gazette-judicial-appointment   "District Court Judge Appointed", "Acting District Court Judges Appointed", "Acting
                                 Community Magistrate Appointed", "Acting Judge of High Court Appointed", "Law Commissioner
                                 Appointment" (sections go, vr): each appointee by name, the role the notice gives
                                 ("to be an Acting District Court Judge"), the court from the title, statute, appointer,
                                 term. Who the appointee was before ("Barrister and Solicitor of Timaru", "retired
                                 District Court Judge") is never kept: the role is the office given
  gazette-jp-list                "Justices of the Peace Appointed" (each "Surname, Given names, <address>, <town>."),
                                 "Justices of the Peace (Retired)" and "… Resignations" (each "Given names Surname, of
                                 <town>."): each name as printed and its town only. The rest of a JP's entry is their
                                 home address and is never read into a row: the town is the last part of the entry, kept
                                 only when it holds no digit, no street word and nothing the lane's address cut finds
  gazette-mental-health-director  a Director of Area Mental Health Services named in an amending notice ("substituting
                                 the name and title “Name, title, of Place”", "Appoint Name as Director of Area Mental
                                 Health Services in respect of …"): the name and the area. A principal notice's schedule is
                                 a catch-log line
  gazette-reserve-appointment    a body appointed to control and manage a reserve, or that appointment revoked (section
                                 ln, Reserves Act 1977): the body as printed. The land's description is never read
  gazette-board-intervention     a school board put under a limited statutory manager, that direction amended or revoked,
                                 or the board dissolved and a commissioner directed (section go, Education Acts): one row
                                 per notice: the board as printed, its institution number, the action, the statute, who
                                 directed (the signature), the notices it names; a revocation marks what it revokes

    family(code, title)       the family's profile slug, or None
    judicial(title, text)     appointments.Reading with the court as body and the given role on every appointee
    jp_list(title, text)      JpReading(kind, people [(ordinal, name, locality)], unread)
    mental_health(text)       [(name, area)], unread
    reserve(title, text)      (body, action) or None
    intervention(title, text) Intervention
"""
import re
from dataclasses import dataclass, field

from registers.gazette import appointments as AP
from registers.gazette import cut
from registers.gazette import liquidations as LQ

JUDICIAL = "gazette-judicial-appointment"
JP = "gazette-jp-list"
MENTAL_HEALTH = "gazette-mental-health-director"
RESERVE = "gazette-reserve-appointment"
INTERVENTION = "gazette-board-intervention"
PROFILES = (JUDICIAL, JP, MENTAL_HEALTH, RESERVE, INTERVENTION)
READER = "registers.gazette.offices 1"

_CORR = r"^\s*(?:Corrigendum\W*)?"
_JUDICIAL_TITLE = re.compile(
    _CORR + r"(?:(?:Acting|Alternate|Temporary|Chief|Principal|Deputy)\s+)*(?P<court>.*?\b(?:Judges?|Magistrates?|Commissioners?)"
    r"(?:\s+of\s+(?:the\s+)?[A-Z][\w ]*?Court)?)\s+(?:Appointed|Appointments?)\s*$", re.I)
_JP_TITLE = re.compile(_CORR + r"Justices?\s+of\s+the\s+Peace\s*(?P<kind>Appointed|\(Retired\)|Resignations?)\s*$", re.I)
_MH_TITLE = re.compile(r"Directors?\s+of\s+Area\s+Mental\s+Health", re.I)
_RESERVE_TEXT = re.compile(r"\bto\s+control\s+and\s+manage\b", re.I)
#: a reserve notice by its title alone (the check's rule too): appointed to control and manage, whatever the text holds
RESERVE_TITLE = re.compile(r"appoint\w*.*control\s+and\s+manage|control\s+and\s+manage.*appoint", re.I)
_INTERVENTION_TITLE = re.compile(r"Limited\s+Statutory\s+Managers?|Dissolution\s+of\s+.*Board.*Commissioner", re.I)

GLUE = ((re.compile(r"\bappoint(?=[A-Z])"), "appoint "), (re.compile(r"(?<=[a-z0-9])(?=to\s+be\b)"), " "),
        (re.compile(r"(?<=[a-z])(?=as\s+(?:an?\s+)?(?:Acting\s+)?(?:District|Family|Youth|Employment|Environment|Community|High|Chief|Principal|Alternate|Temporary|Deputy|commissioner|limited)\b)"), " "))


def family(code: str, title: str, text: str = "") -> str | None:
    """The profile slug of the office family a notice belongs to, or None. The appointment reader's own titles are its
    own and are tried first in read.py; nothing here takes a title beginning 'Appointment'."""
    t = title or ""
    if code in ("go", "vr") and _JP_TITLE.match(t):
        return JP
    if code in ("go", "vr") and _JUDICIAL_TITLE.match(t) and not AP._TITLE.match(t):
        return JUDICIAL
    if code == "go" and _MH_TITLE.search(t):
        return MENTAL_HEALTH
    if code == "go" and _INTERVENTION_TITLE.search(t) and not AP._TITLE.match(t):
        return INTERVENTION
    if code == "ln" and (RESERVE_TITLE.search(t) or re.search(r"appoint", t, re.I) and _RESERVE_TEXT.search((text or "")[:3000])):
        return RESERVE
    return None


def _unglue(text: str) -> str:
    for p, r in GLUE:
        text = p.sub(r, text)
    return text


# --- judges and magistrates --------------------------------------------------------------------------------------------

#: the office given: "to be an Acting District Court Judge" first, else "as a District Court Judge"; never "as the Chief
#: District Court Judge may fix" (the judge who fixes the sittings, not the office given)
_GIVEN_ROLE = re.compile(r"\b(?:to\s+be|as(?!\s+the\b))\s+(?:an?\s+|the\s+)?(?P<role>(?:[Aa]cting\s+|[Aa]lternate\s+|[Tt]emporary\s+|Chief\s+|Principal\s+|Deputy\s+)*"
                         r"(?:[A-Z][\w]*\s+){0,4}(?:Judges?|Magistrates?|Commissioners?)(?:\s+of\s+the\s+[A-Z][\w ]*?Court)?)\b")


def judicial(title: str, text: str) -> AP.Reading:
    m = _JUDICIAL_TITLE.match(title or "")
    r = AP.read(title, _unglue(text or ""))
    court = LQ._clean(m.group("court")) if m else None
    r.body = court or r.body
    plain = _unglue(text or "")
    g = next((x for x in _GIVEN_ROLE.finditer(plain) if x.group(0).lower().startswith("to")), None) or _GIVEN_ROLE.search(plain)
    role = LQ._clean(g.group("role")) if g else None
    for p in r.people:
        p.role = role                         # the office given, never who they were before
    return r


# --- Justices of the Peace -------------------------------------------------------------------------------------------

@dataclass
class JpReading:
    kind: str = None          # appointed | retired | resigned
    corrigendum: bool = False
    dated_on: str = None
    statute: str = None
    people: list = field(default_factory=list)      # (ordinal, name as printed, town or None)
    unread: list = field(default_factory=list)


_JP_ROLE = {"appointed": "Justice of the Peace for New Zealand", "retired": "Justice of the Peace (retired)",
            "resigned": "resigned as a Justice of the Peace"}
_STREETY = re.compile(r"\d|\b(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Crescent|Cres|Terrace|Tce|Lane|Way|Parade|"
                      r"Highway|Hwy|Grove|Close|Court|Ct|Rise|Heights|Mews|Quay|Square|Esplanade|Boulevard|Track|Flat|Apartment|"
                      r"Unit|Box|Bag|R\.?\s?D\.?|Rural|Delivery|Estate|Farm|Station)\b", re.I)
#: where the names begin: after the list's colon, else (a resignation) after "noted for information [that]"
_LIST_COLON = re.compile(r"(?:Justices?\s*of\s*the\s*Peace(?:\s*for\s*New\s*Zealand)?|\(retired\)|following\s+persons[^:]{0,120})\s*:\s*[‘'“\"]?", re.I)
_LIST_NOTED = re.compile(r"\bnoted\s+for\s+information,?\s+(?:that,?\s+)?(?=[A-Z][\w'’\-]+\s+[A-Z])", re.I)
_JP_ACT = re.compile(r"[Ss]ection\s+(?P<s>\d+[A-Z]?(?:\s*\(\s*\w+\s*\))*)\s*of\s+the\s+Justices\s+of\s+the\s+Peace\s+Act\s+(?P<y>\d{4})")
_LIST_END = re.compile(r"\b(?:Dated\s+at|(?:have|has)\s+resigned|resigned\s+(?:their|his|her))\b")
#: an appointed entry: "Surname, Given names, …": the entries part at a full stop before the next "Surname, Given"
_APPOINTED_SPLIT = re.compile(r"(?<=[\wāēīōū\)’'])\.\s*(?=(?:[A-Z][\w'’\-]+\s+){0,3}[A-Z][\w'’\-]+,\s+[A-Z])")
_APPOINTED_ENTRY = re.compile(r"^\s*(?P<surname>(?:(?:van|de|der|von|du|le|la|te|Mc|O’|O')\s*)?[A-Z][\w'’\-]+(?:\s+[A-Z][\w'’\-]+){0,3}),\s+"
                              r"(?P<given>[A-Z][\w'’\-]+(?:\s+[A-Z(][\w'’\-)]*){0,5})\s*(?:,(?P<rest>.*))?$")
#: a retired or resigned entry: "Given names Surname, of Town", "Given names Surname, J.P., <address>, Town" or
#: "Given names Surname of <address>, Town": the name, then the entry's last part as its town
_OF_ENTRY = re.compile(rf"^\s*(?P<name>{AP._NAME})(?:\s*,\s*(?:J\.?\s?P\.?|JP)\.?)?(?:\s*,\s*(?:of\s+)?|\s+of\s+)(?P<rest>.+?)\s*\.?\s*$")
#: one retired or resigned entry from the next: a full stop before the next name (never inside "J.P.")
_OF_SPLIT = re.compile(r"(?<=[\wāēīōū’'\)])(?<![A-Z])\.\s*(?=[A-ZĀĒĪŌŪ][\w'’\-]+(?:\s+[A-ZĀĒĪŌŪ][\w'’\-]+){1,5}\s*(?:,|\s+of\s))|\n+|;\s*")


def town(part: str) -> str | None:
    """The town an entry ends with, or None: no digit, no street word, nothing the lane's address cut finds, at most four
    words. A JP's street and suburb are their home address and are never returned."""
    t = LQ._clean(re.sub(r"\s+\d{4}\s*$", "", part or "").strip(" .,;"))
    if not t or len(t.split()) > 4 or _STREETY.search(t) or cut.find(t) or not re.match(r"[A-ZĀĒĪŌŪ]", t):
        return None
    return t


def jp_list(title: str, text: str) -> JpReading:
    m = _JP_TITLE.match(title or "")
    k = (m.group("kind") or "").lower() if m else ""
    r = JpReading(kind="appointed" if k.startswith("appointed") else "retired" if "retired" in k else "resigned",
                  corrigendum=bool(LQ._CORRIGENDUM.match(title or "")))
    text = text or ""
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    sec = _JP_ACT.search(text)
    r.statute = f"Justices of the Peace Act {sec.group('y')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    s = _LIST_COLON.search(text) or _LIST_NOTED.search(text)
    if not s:
        r.unread.append(("list", "no list of names after the operative words"))
        return r
    e = _LIST_END.search(text, s.end())
    span = text[s.end():e.start() if e else len(text)]
    if r.kind == "appointed":
        entries = [x for x in _APPOINTED_SPLIT.split(span) if x.strip(" .;")]
        for i, x in enumerate(entries, start=1):
            em = _APPOINTED_ENTRY.match(LQ._clean(x))
            if not em or AP._NOT_PERSON.search(em.group("surname")):
                r.unread.append((f"entry {i}", "an entry the reader cannot take as 'Surname, Given names'"))
                continue
            parts = [p for p in (em.group("rest") or "").split(",") if p.strip(" .")]
            r.people.append((len(r.people) + 1, f"{em.group('surname')}, {LQ._clean(em.group('given'))}",
                             town(parts[-1]) if parts else None))
    else:
        entries = [x for x in _OF_SPLIT.split(span) if x and x.strip(" .;")]
        for i, x in enumerate(entries, start=1):
            x = LQ._clean(x)
            if len(re.findall(r"(?:,\s*|\s)of\s+", x)) > 1:
                r.unread.append((f"entry {i}", "names run together with no separator: which town is whose cannot be told"))
                continue
            em = _OF_ENTRY.match(x)
            bare = em and re.sub(rf"^(?:{AP._HONORIFIC}\s+)+", "", em.group("name"))
            if not em or AP._NOT_PERSON.search(bare) or not 2 <= len(bare.split()) <= 6:
                r.unread.append((f"entry {i}", "an entry the reader cannot take as 'Name, of Town'"))
                continue
            parts = [p for p in em.group("rest").split(",") if p.strip(" .")]
            r.people.append((len(r.people) + 1, LQ._clean(em.group("name")), town(parts[-1]) if parts else None))
    if not r.people and not r.unread:
        r.unread.append(("list", "the list names no one the reader can take"))
    return r


def jp_role(kind: str) -> str:
    return _JP_ROLE[kind]


# --- Directors of Area Mental Health Services ------------------------------------------------------------------------

_MH_SUBST = re.compile(r"substituting\s+the\s+name\s+and\s+title\s+[“\"](?P<who>[^”\"]{3,160})[”\"]", re.I)
_MH_APPOINT = re.compile(rf"\bAppoint\s+(?P<name>{AP._NAME})\s+as\s+(?:the\s+)?Director\s+of\s+Area\s+Mental\s+Health\s+Services?"
                         r"(?:\s+in\s+respect\s+of\s+(?:the\s+)?[“\"]?(?P<area>[^”\".,]{2,100}))?", re.I)
_MH_AREA = re.compile(r"in\s+respect\s+of\s+(?:the\s+)?[“\"]?(?P<area>Area\s+\d+|[^”\".,]{2,100})", re.I)


def mental_health(text: str) -> tuple:
    """([(name, area)], unread): the directors an amending notice names. A principal notice's schedule is not read."""
    text = text or ""
    out, unread, seen = [], [], set()
    for m in _MH_APPOINT.finditer(text):
        name = LQ._clean(m.group("name"))
        if name not in seen:
            seen.add(name)
            out.append((name, LQ._clean(m.group("area") or "") or None))
    for m in _MH_SUBST.finditer(text):
        who = LQ._clean(m.group("who"))
        name = LQ._clean(who.split(",")[0])
        bare = re.sub(rf"^(?:{AP._HONORIFIC}\s+)+", "", name)
        if AP._NOT_PERSON.search(bare) or len(bare.split()) < 2 or re.search(r"\d", bare):
            unread.append(("substitution", "a substituted name the reader cannot take"))
            continue
        if name in seen:
            continue
        seen.add(name)
        a = None
        for am in _MH_AREA.finditer(text[:m.start()]):
            a = am
        out.append((name, LQ._clean(a.group("area")) if a else None))
    if not out:
        unread.append(("directors", "no director named in an amendment the reader can take (a principal notice's schedule is not read)"))
    return out, unread


# --- reserves --------------------------------------------------------------------------------------------------------

_RESERVE_APPOINTS = re.compile(r"\b(?:hereby\s+|further\s+)?appoints?\s+(?:the\s+)?(?P<body>[A-ZĀĒĪŌŪ][^;:]{2,160}?)\s+to\s+control\s+and\s+manage\b")
_RESERVE_REVOKES = re.compile(r"\brevok\w*\s+(?:the\s+)?appointment\s+of\s+(?:the\s+)?(?P<body>[A-ZĀĒĪŌŪ][^;:]{2,160}?)\s+to\s+control\s+and\s+manage\b", re.I)


def reserve(title: str, text: str):
    """(body, action) or None: the body appointed to control and manage a reserve, or whose appointment is revoked."""
    text = text or ""
    m = _RESERVE_REVOKES.search(text)
    if m:
        return LQ._clean(m.group("body")), "appointment to control and manage a reserve revoked"
    m = _RESERVE_APPOINTS.search(text)
    if m:
        body = LQ._clean(m.group("body"))
        if re.search(r"\d", body) or len(body.split()) > 16:
            return None
        return body, "appointed to control and manage a reserve"
    return None


# --- school boards ---------------------------------------------------------------------------------------------------

@dataclass
class Intervention:
    action: str = None
    board: str = None
    institution_number: str = None
    statute: str = None
    directed_by: str = None
    dated_on: str = None
    names_notices: list = field(default_factory=list)
    corrigendum: bool = False


_SW = r"(?:[A-ZĀĒĪŌŪ][\w'’\-.]*|\(\s*[A-ZĀĒĪŌŪ][\w'’\- ]*\)|\(\d{1,5}\)|of|and|o|te|a|ki|the|for|&)"
#: "the Kaipara College (25) Board of Trustees", "the Limehills School (4012) Board"
_BOARD_AFTER = re.compile(rf"\b(?:for|to|of|that)\s+the\s+(?P<b>(?:{_SW}\s+){{1,14}}?(?:Combined\s+)?Board(?:\s+of\s+Trustees)?)\b")
#: "the Board of Trustees of Te Horo School (1234)", "the Combined Board of Trustees for Kelston …"
_BOARD_OF = re.compile(rf"\b(?P<b>(?:Combined\s+)?Board\s+of\s+Trustees\s+(?:of|for|at)\s+(?:the\s+)?[A-ZĀĒĪŌŪ][\w'’\-.]*(?:\s+{_SW}){{0,12}})")
#: a title's "… at <School>": the school, when the text gives no board
_AT_SCHOOL = re.compile(rf"\b(?:at|to)\s+(?!Appoint\b)(?P<b>[A-ZĀĒĪŌŪ][\w'’\-.]*(?:\s+{_SW}){{0,10}}?)\s*,?\s*$")


def board(s: str) -> str | None:
    """The board a school notice names, as printed, ending at the board or its school's institution number."""
    for p in (_BOARD_AFTER, _BOARD_OF):
        for m in p.finditer(s or ""):
            b = LQ._clean(m.group("b"))
            b = re.sub(r"\s+(?:of|and|for|the|o|te|a|ki|&)$", "", b)
            if re.fullmatch(r"(?:the\s+)?(?:Combined\s+)?Board(?:\s+of\s+Trustees)?(?:\s+(?:of|for|at))?", b, re.I):
                continue
            if p is _BOARD_OF:
                b = re.sub(r"(\(\d{1,5}\)).*$", r"\1", b)
            return b
    m = _AT_SCHOOL.search(re.sub(r"\s*\(Notice\s+No\.[^)]*\)\s*$", "", s or "")) if len(s or "") < 400 else None
    return LQ._clean(m.group("b")) if m else None


_INST = re.compile(r"\((?P<n>\d{1,5})\)")
#: the statute: an Act name may hold 'and' or 'of' ('Education and Training Act 2020'), which the liquidations' does not take
_STATUTE = re.compile(r"[Ss]ection\s+(?P<s>\d+[A-Z]*(?:\s*\(\s*\w+\s*\))*)\s+of\s+the\s+(?P<act>[A-Z][a-z]+(?:\s+(?:[A-Z][a-z]+|and|of))"
                      r"{0,5}\s+Act\s+\d{4})")
_NOTICE_NO = re.compile(r"Notice\s+No\.?\s*(?P<n>\d{4}-[a-z]{2}\d+)", re.I)
_SIGNED = re.compile(r"(?:\d{4}|\bday\s+of\s+\w+\s+\d{4})\s*\.?\s*(?P<who>(?:Hon\.?\s+|HON\s+|Dr\.?\s+)?[A-ZĀĒĪŌŪ][A-ZĀĒĪŌŪ'’.\- ]{3,60}[A-Z]),\s*(?P<office>[^.\n]{3,200})")


def intervention(title: str, text: str) -> Intervention:
    t = re.sub(r"\s*\(Notice\s+No\.[^)]*\)\s*$", "", title or "")
    r = Intervention(corrigendum=bool(LQ._CORRIGENDUM.match(t)))
    low = t.lower()
    if "dissolution" in low:
        r.action = "board dissolved; commissioner directed"
    elif re.search(r"^\W*(?:notice\s+of\s+)?revocation|^corrigendum\W*revocation", low):
        r.action = "statutory manager direction revoked"
    elif re.search(r"^\W*(?:further\s+)?amend", low):
        r.action = "statutory manager direction amended"
    else:
        r.action = "statutory manager directed"
    text = text or ""
    r.board = board(text[:1500]) or board(t)
    n = _INST.search(r.board or "") or _INST.search(t)
    r.institution_number = n.group("n") if n else None
    sec = _STATUTE.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    s = None
    for s in _SIGNED.finditer(text[-600:]):
        pass
    r.directed_by = LQ._clean(f"{s.group('who')}, {s.group('office')}")[:200] if s else None
    r.names_notices = sorted(set(m.group("n") for m in _NOTICE_NO.finditer(text)))
    return r
