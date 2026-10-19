"""The Commission's Gazette notices on the Register of Political Parties →
events. One notice holds one or more resolutions; each is read into an
event with the day the Commission decided it:

  registered     a party entered on the register (its name, and its abbreviation where stated)
  cancelled      a party taken off it
  renamed        a change of name the Commission states: old name → new name
  abbreviation   a party's abbreviation registered, changed or removed (abbreviation None)
  corrected      a corrigendum: in notice <ref>, text <old> is replaced by <new>
  logo           a party logo registered, substituted or cancelled (no party is resolved from it)
  components     a change to a party's component parties

The text is the old estate's capture, flattened and often glued at block
boundaries ("Kiwi Partyat the party's request", "Internet PartyThe Internet
Party logo"), so a name ends at the first of the delimiters below, glue
included. A resolution the reader sees and cannot read is a catch-log line,
never a guess.

    read(text, notice_id, published_on)   Reading(events, unread)
"""
import html
import re
from dataclasses import dataclass, field

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DATE = re.compile(rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTHS})\s*,?\s*((?:19|20)\d\d)")
_MONTH_N = {m: i for i, m in enumerate(MONTHS.split("|"), 1)}

#: where a resolution begins
_CLAUSE = re.compile(rf"(?=Pursuant to|(?<![A-Za-z])On \d{{1,2}} (?:{MONTHS}) \d{{4}},|At its meeting on|In the notice titled)")
_SIGNATURE = re.compile(r"Dated at Wellington.*?(?:Electoral Commission\.?|(?:19|20)\d\d\.)"
                        r"|(?:DR\s+)?[A-Z]{2,}[A-Z.'’ ]{2,},\s*(?:Chief|Deputy|Electoral)[A-Za-z ]*(?:,\s*Electoral Commission)?\.?", re.S)

#: a name ends at the first of these (glue included: no space is required in front)
_END = re.compile("|".join((
    r"\s*\(?\s*(?:Party\s+)?(?:Name\s+)?[Aa]bbreviation\s*:",
    r"\s*(?:New|Previous|Old)\s+(?:Party|party)\s+(?:Name|name|[Aa]bbreviation)\s*:",
    r"\s*Party\s+(?:Secretary|Name)\s*:",
    r"\s*Component\s+Part",
    r"\s*Date of Amendment",
    r"\s*,?\s*a registered political party",
    r"\s*and its logo",
    r"\s*and to remove",
    r"\s*from the Register",
    r"\s*in accordance",
    r"\s*at the party",
    r"(?:\s+|(?<!Zeal)(?<!Isl)(?<!Heartl))and\s+to\s+(?:amend|delete|remove|enter)",
    r"\s+and\s+(?:to\s+)?(?:enter|register|cancel)",
    r"\s+to\s+(?:amend|change)",
    r"\s*['’]s\s+(?:party\s+)?logo",
    r"\s+(?:party\s+)?logo\b",
    r"(?<=[A-Za-z0-9).])(?=The\s)",
    r"(?<=[a-z0-9).])(?=(?:Their|A)\s)",
    r"(?<=[a-z0-9).])(?=(?:Dated|Pursuant|Cancellation|Registration|Application|Party Name|Previous|New Party))",
    r"\s*;",
    r"\.(?=\s|$|\d\.|[A-Z][a-z]{2,}|and\b)",
    r"\s*[.;]$",
    r"\s*\(\d\)",
    r"\s*\(\s*[“\"]",
    r"\s*\((?:[a-z])\)",
    r"\s+(?:The party details|The registered|The substitute|The logo|The Register|The register|Their respective)",
    r"\s*&nbsp",
    r"\s*$",
)))


@dataclass
class Event:
    notice: str
    ordinal: int
    kind: str
    decided_on: str = None          # ISO; None when the notice states no day (the 2008 year's list)
    name: str = None                # the party as printed (the old name, for a rename)
    new_name: str = None
    abbreviation: str = None
    old_abbreviation: str = None
    ref: str = None                 # a corrigendum's notice
    clause: str = ""                # the resolution's own text, for the citation


@dataclass
class Reading:
    events: list = field(default_factory=list)
    unread: list = field(default_factory=list)      # (place, reason)


def normalise(text: str) -> str:
    t = html.unescape(text or "").replace("\xa0", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", t).strip()


def iso(m) -> str:
    return f"{int(m.group(3)):04d}-{_MONTH_N[m.group(2)]:02d}-{int(m.group(1)):02d}"


def cut(s: str) -> str:
    """The name at the start of `s`, up to the first delimiter, quotes and
    a lowercase leading article off. None when nothing is left."""
    s = s.lstrip(" :“”\"'")
    m = _END.search(s, 1)
    name = s[:m.start()] if m else s
    name = name.strip(" ,:;“”\"'")
    name = re.sub(r"^the\s+", "", name)
    words = name.split()
    half = len(words) // 2
    if half and len(words) % 2 == 0 and [w.rstrip("'’s") for w in words[half:]] == words[:half]:
        name = " ".join(words[:half])           # "1Law4All 1Law4All's logo": the name, then the name again
    return name or None


def _abbr(s: str):
    a = cut(s)
    return None if a is None or a.lower() == "none" else a


def clauses(text: str) -> list:
    body = _SIGNATURE.sub(" ", normalise(text))
    parts = [p.strip() for p in _CLAUSE.split(body)]
    return [p for p in parts if p]


_ACTS = re.compile(r"regist|cancel|change|substitut|approv|amend|replaced", re.I)

_REG_LIST = re.compile(r"register(?:ed)? the following (?:\w+ )?political part(?:y|ies)(?: and logos?)?\s*:?", re.I)
_REG_STOP = re.compile(r"\d\.\s*Register the following abbreviation|register the logos? of|Pursuant to", re.I)
_YEAR_LIST = re.compile(r"The following parties have been registered:\s*(.+?)\.\s*(?:A logo|$)")
_CANCEL = re.compile(r"cancel (?:the )?registration of\s*", re.I)
_RENAME = re.compile(r"change (?:of )?(?:the )?(?:registered |party )?name of\s*(?:the\s+)?(?P<old>.+?)\s*to\s*:?\s*(?:the\s+)?(?=[“\"A-Z])(?P<rest>.*)")
_RENAME_ITS = re.compile(r"by (?:the )?(?P<old>.+?) to change its party name to\s*(?P<rest>.*)")
_NEW_NAME = re.compile(r"New Party Name\s*:\s*")
_OLD_NAME = re.compile(r"(?:Old|Previous) Party Name\s*:\s*")
_NEW_ABBR = re.compile(r"New (?:Party|party) [Aa]bbreviation\s*:\s*")
_OLD_ABBR = re.compile(r"Previous (?:Party|party) [Aa]bbreviation\s*:\s*")
_REMOVE_ABBR = re.compile(r"remove the party abbreviation|delete the registered abbreviation", re.I)
_ABBR_AS = re.compile(r"(?:register|registration of)\s*(?P<abbr>.+?)\s*as the (?:party name )?abbreviation (?:of|for) (?:the name of )?(?P<rest>.*)")
_ABBR_FROM = re.compile(r"change (?:of\s*)?(?:the )?abbreviat(?:ion|ed party name) of\s*(?:the )?(?P<party>.+?) from\s*(?P<old>.+?)\s*to\s*(?P<rest>.*)")
_ABBR_BE = re.compile(r"determined that (?:the )?(?P<party>.+?)['’]s abbreviated name be changed from (?P<old>.+?) to (?P<rest>.*)")
_ABBR_OLDNEW = re.compile(r"abbreviation of (?:the )?(?P<party>.+?) as follows:\s*Old Party Name Abbreviation:\s*(?P<old>.+?)\s*New Party Name Abbreviation:\s*(?P<rest>.*)")
_ABBR_FOR = re.compile(r"register the following abbreviation of the party name for (?P<party>.+?), a registered political party\s*:\s*Abbreviation\s*:\s*(?P<rest>.*)")
_ABBR_LIST = re.compile(r"Register the following abbreviation\s*:\s*Party Name\s*:\s*(?P<party>.+?)\.?\s*Party Abbreviation\s*:\s*(?P<rest>.*)")
_CORRIGENDUM = re.compile(r"Notice No\.?\s*(?P<ref>\d{4}-[a-z]{2}\d+) the following text: “(?P<old>[^”]+)” is replaced (?:as|by|with) “(?P<new>[^”]+)”")
_ENTRY = re.compile(r"Party Name\s*:\s*")


def _date(clause: str):
    m = DATE.search(clause)
    return iso(m) if m else None


def _read_clause(clause: str, notice: str, published_on: str) -> list:
    """[(kind, fields)] for one resolution."""
    out = []
    m = _CORRIGENDUM.search(clause)
    if m:
        return [("corrected", {"ref": m.group("ref"), "name": m.group("old"), "new_name": m.group("new")})]
    m = _YEAR_LIST.search(clause)
    if m:
        for n in m.group(1).split(";"):
            if n.strip():
                out.append(("registered", {"name": n.strip(), "decided_on": None}))
        return out
    m = _REG_LIST.search(clause)
    if m:
        seg = clause[m.end():]
        stop = _REG_STOP.search(seg)
        seg = seg[:stop.start()] if stop else seg
        entries = list(_ENTRY.finditer(seg))
        if entries:
            for i, e in enumerate(entries):
                part = seg[e.end():entries[i + 1].start() if i + 1 < len(entries) else len(seg)]
                a = re.search(r"(?:Party\s+)?(?:Name\s+)?[Aa]bbreviation\s*:\s*", part)
                out.append(("registered", {"name": cut(part), "abbreviation": _abbr(part[a.end():]) if a else None}))
        else:
            out.append(("registered", {"name": cut(seg)}))
        if _REG_STOP.search(clause[m.end():] or "") and re.search(r"Register the following abbreviation", clause):
            m2 = _ABBR_LIST.search(clause)
            if m2:
                out.append(("abbreviation", {"name": cut(m2.group("party")), "abbreviation": _abbr(m2.group("rest"))}))
        return out
    pos = 0
    while True:                         # one clause may approve two changes of name: (a) …; and (b) …
        m = _RENAME.search(clause, pos)
        if not m:
            break
        out.append(("renamed", {"name": cut(m.group("old")), "new_name": cut(m.group("rest"))}))
        pos = m.start("rest")
    m = None if out else _RENAME_ITS.search(clause)
    if m:
        out.append(("renamed", {"name": cut(m.group("old")), "new_name": cut(m.group("rest"))}))
    if not out and _NEW_NAME.search(clause) and _OLD_NAME.search(clause):
        new = cut(clause[_NEW_NAME.search(clause).end():])
        old = cut(clause[_OLD_NAME.search(clause).end():])
        out.append(("renamed", {"name": old, "new_name": new}))
    if out:
        new = out[-1][1]["new_name"]
        na = _NEW_ABBR.search(clause)
        oa = _OLD_ABBR.search(clause)
        if na:
            out.append(("abbreviation", {"name": new, "abbreviation": _abbr(clause[na.end():]),
                                         "old_abbreviation": _abbr(clause[oa.end():]) if oa else None}))
        elif _REMOVE_ABBR.search(clause):
            out.append(("abbreviation", {"name": new, "abbreviation": None,
                                         "old_abbreviation": _abbr(clause[oa.end():]) if oa else None}))
        m = _ABBR_FROM.search(clause)
        if m:
            out.append(("abbreviation", {"name": cut(m.group("party")), "old_abbreviation": cut(m.group("old")),
                                         "abbreviation": _abbr(m.group("rest"))}))
        return out
    for rx in (_ABBR_OLDNEW, _ABBR_FOR, _ABBR_LIST, _ABBR_FROM, _ABBR_BE):
        m = rx.search(clause)
        if m:
            f = {"name": cut(m.group("party")), "abbreviation": _abbr(m.group("rest"))}
            if "old" in m.groupdict():
                f["old_abbreviation"] = cut(m.group("old"))
            out.append(("abbreviation", f))
            return out
    m = _ABBR_AS.search(clause)
    if m:
        return [("abbreviation", {"name": cut(m.group("rest")), "abbreviation": _abbr(m.group("abbr"))})]
    for m in _CANCEL.finditer(clause):
        rest = clause[m.end():]
        if re.match(r"(?:the\s+)?logo\b", rest, re.I):
            out.append(("logo", {}))
            continue
        name = cut(rest)
        if name and re.search(r"\blogo$", name, re.I):
            out.append(("logo", {}))
            continue
        out.append(("cancelled", {"name": name}))
    if out:
        return out
    if re.search(r"logos?\b", clause, re.I):
        return [("logo", {})]
    if re.search(r"component part", clause, re.I):
        return [("components", {})]
    return []


def read(text: str, notice: str, published_on: str = None) -> Reading:
    out = Reading()
    n = 0
    for i, clause in enumerate(clauses(text), 1):
        if not _ACTS.search(clause) or not (DATE.search(clause) or "Electoral Commission" in clause):
            continue
        got = _read_clause(clause, notice, published_on)
        if not got:
            out.unread.append((f"{notice} clause {i}", "a resolution the reader could not read"))
            continue
        decided = _date(clause)
        for kind, f in got:
            if kind in ("registered", "cancelled", "renamed", "abbreviation") and not f.get("name"):
                out.unread.append((f"{notice} clause {i}", f"a {kind} resolution with no party name read"))
                continue
            if kind == "renamed" and not f.get("new_name"):
                out.unread.append((f"{notice} clause {i}", "a change of name with no new name read"))
                continue
            n += 1
            out.events.append(Event(notice=notice, ordinal=n, kind=kind,
                                    decided_on=f.pop("decided_on", decided) if "decided_on" in f else decided,
                                    clause=clause[:600], **f))
    if not out.events and not out.unread:
        out.unread.append((notice, "no resolution found in the notice"))
    return out
