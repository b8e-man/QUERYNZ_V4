"""Notices of a liquidator's appointment (profile
`gazette-liquidator-appointment`): every notice in the Gazette's section
`al`, recognised by that code, then read. No model.

Two shapes:

  notice   one or more companies, named in the title ("ACME LIMITED (in
           liquidation)"; the capture sometimes carries the end of a long
           title into the text, before "Notice of"), or in the body when the
           title is only "Appointment of Liquidator"; the operative sentence
           ("X and Y were appointed joint and several liquidators of the
           company by special resolution of the shareholders on 9 May 2016 at
           10.30am, pursuant to section 241(2)(a)…"); a claims date; "Dated";
           the liquidators' signature ("X and Y, Joint Liquidators"); then
           their business contact lines, which are never read
  list     the Official Assignee's "Liquidations": `NAME LIMITED | 9 May 2022`
           repeated; the Official Assignee is the liquidator

Who appointed the liquidator is the section where it is cited (241(2)(a)
the shareholders, (b) the board, (c) the court), else the notice's own
words. The appointment date is read only where the notice prints one
(with its time) or the companies share one; a notice that gives each of
several companies its own date gives none to any, and says so. The
liquidators are read from the signature, each checked against the
notice's text above it (`named_in_body`: the full name, only the surname,
as when "J. Example" signs for "Jane Example", or no); a notice with no
signature names them only in the operative sentence ("…, insolvency
practitioner, was appointed liquidator"), and they are read from there; otherwise none is named. No address, telephone or email is read.

The old reader (`data-layer/gazette_register/parse.py`, parse_insolvency)
split titles on every "and", so `SMITH AND JONES LIMITED` became
`JONES LIMITED`; here a title is cut only where each part ends in a legal
suffix, and a part that cannot be placed is a catch-log line.

    recognise(code, title, text)    the reasons, empty if not this profile
    read(title, text)               Reading(shape, companies, liquidators, appointed_by, statute, …, unread)
"""
import re
from dataclasses import dataclass, field

from keys.dates import filed_date

CODE = "al"
_SUFFIX = r"(?:LIMITED|LTD|Limited|Ltd|INCORPORATED|Incorporated|PARTNERSHIP|Partnership|TRUST|Trust)"
_ENDS = re.compile(rf"(?:\b{_SUFFIX}|\(N\.?Z\.?\)\s+{_SUFFIX})\.?$")
#: a bracket that is not part of the name: a status, a former name, a number, a defined term ("(in liquidation)",
#: "(formerly …)", '("the company")');
#: "(2019)", "(NZ)" and "(BAY OF ISLANDS)" are the name's own and stay
_PAREN = re.compile(r"\s*\((?:\s*[a-z\"“'‘]|\s*(?i:in|formerly|previously|now|company|nzbn|receivers?|all|both|trading|subject|also)\b)[^()]*(?:\([^()]*\)[^()]*)*\)")
_CORRIGENDUM = re.compile(r"^\s*Corrigendum\s*[—–\-:]*\s*", re.I)
_BARE = re.compile(r"^\s*(?:Notice\s+of\s+)?(?:Appointment\s+of\s+)?Liquidat(?:or|ors|ion|ions)\b|^\s*The\s+Companies\s+Act", re.I)
_LIST_HEAD = re.compile(r"following\s+liquidations?\s*:", re.I)
_DAY = r"\d{1,2}(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?[A-Z][a-z]+,?\s+\d{4}"
_LIST_ROW = re.compile(rf"(?P<name>[^|]+?)\s*\|\s*(?P<d>{_DAY})")
_NOTICE_OF = re.compile(r"Notice\s+of\b|Pursuant\s+to\b|In\s+the\s+matter", re.I)
_BODY_CO = re.compile(rf"(?:liquidators?\s+of|that)\s+(?:the\s+company\s+)?(?P<co>(?:[A-Z0-9][\w&'’.,()\-]*\s+){{0,10}}?{_SUFFIX})\b")
_S241 = re.compile(r"section\s+241\s*\(\s*2\s*\)\s*\(\s*([abc])\s*\)", re.I)
_BY_SECTION = {"a": "shareholders", "b": "board", "c": "court"}
_SECTION = re.compile(r"[Ss]ection\s+(?P<s>\d+[A-Z]?(?:\s*\(\s*\w+\s*\))*)\s+of\s+the\s+(?P<act>(?:[A-Z][a-z]+\s+){1,4}Act\s+\d{4})")
_WHEN = re.compile(rf"(?P<d>{_DAY})(?:,?\s+at\s+(?P<t>\d{{1,2}}(?:[.:]\s*\d{{2}})?\s*[ap]\.?\s*m\.?))?")
_APPOINTED = re.compile(r"\bappoint(?:ed|ment)\b|\bresolved\b|\bliquidation\s+commenced\b", re.I)
_DATED = re.compile(rf"Dated\b[^.]{{0,40}}?(?P<d>{_DAY})")
_NUMBER = re.compile(r"Company\s+(?:No\.?|Number)\s*:?\s*\.?\s*:?\s*(\d{4,8})", re.I)
_SIGNED = re.compile(r"(?P<names>(?<![A-Za-z])[A-Z](?:[^.:;|]|(?<=\b[A-Z])\.){1,150}?),\s*(?P<role>(?:Joint\s+(?:and\s+Several\s+)?|Former\s+|Provisional\s+|Interim\s+|Replacement\s+)?"
                     r"[Ll]iquidators?)\b(?!\s+of\b)")
_PERSON = re.compile(r"^(?:[A-Z](?:\.\s?|\s)){0,3}[A-Z][\w’'\-]+(?:\s+(?:[A-Z]\.?|[A-Z][\w’'\-]+|van|de|der|von|du|le|la|te|ter|di|da)){0,4}$")
#: a post-nominal ("C.A.", "FCA"); a signature printed in capitals ("ANN EXAMPLE") is a name, not this
_QUALIFICATION = re.compile(r"^(?:[A-Z]{1,4}\.\s?){1,5}$|^(?:CA|FCA|ACA|CPA|FCPA|CAANZ|CA ANZ|ACIS|LLB|BCom|MBA|QSM|JP|MInstD)$")
_NOT_NAME = re.compile(r"\b(?:Limited|LIMITED|Ltd|Company|Liquidator|Liquidators|Notice|Dated|Insolvency|Assignee|"
                       r"Chartered|Accountants?|Partners?|Associates|Court|Official|Contact|Phone|Telephone|Email)\b")


def recognise(code: str, title: str, text: str) -> list:
    """Every notice under the Gazette's own section `al` is a liquidator's
    appointment: the code is the Gazette's classification, never a guess."""
    return ["the Gazette's section al (appointment of liquidators)"] if code == CODE else []


@dataclass
class Company:
    ordinal: int
    name: str
    number: str = None
    appointed_on: str = None
    appointed_at: str = None      # the time printed with the date, as printed: "10.30am"
    date_basis: str = None        # appointment | list date


@dataclass
class Liquidator:
    ordinal: int
    name: str
    role: str                     # as signed (Liquidator, Joint Liquidators, Former Liquidator, …), or 'named as appointed'
    named_in_body: str = "no"     # full | surname | no: the name, or only its surname, printed above the signature


@dataclass
class Reading:
    shape: str = None             # notice | list
    companies: list = field(default_factory=list)
    liquidators: list = field(default_factory=list)
    appointed_by: str = None      # shareholders | board | court | creditors | None
    statute: str = None
    dated_on: str = None
    corrigendum: bool = False
    dates_per_company: bool = False
    unread: list = field(default_factory=list)      # (place, why)


def _date(text):
    if not text:
        return None
    d = filed_date(re.sub(r"(\d)(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?", r"\1 ", text, count=1).replace(",", ""))
    return d.isoformat() if d else None


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip(" .,;:—–-")


def _key(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


def split_names(head: str) -> tuple:
    """A title's company names: cut at ", " and " and " only where every
    part ends in a legal suffix. ([names], [parts that could not be placed])."""
    head = _PAREN.sub(" ", _CORRIGENDUM.sub("", head or ""))
    head = _clean(re.sub(r"\s*\([^)]*$", "", head))     # a bracket the title's capture cut off
    parts = re.split(r"(,\s*|\s+and\s+|\s+&\s+(?=[A-Z0-9][^,]*\b" + _SUFFIX + r"\b))", head)
    names, buf = [], ""
    for i in range(0, len(parts), 2):
        piece = parts[i]
        sep = parts[i - 1] if i else ""
        buf = f"{buf}{sep}{piece}" if buf else piece
        if _ENDS.search(_clean(buf)):
            names.append(_clean(buf))
            buf = ""
    left = _clean(buf)
    if left and not names:
        return [left], []         # one name with no suffix (a partnership, a trust board)
    return names, ([left] if left else [])


def _title_head(title: str, text: str) -> str:
    """The title, with its end where the capture carried it into the text."""
    t = title or ""
    if re.search(r"(?:,|\band|&)\s*$", t) or not re.search(r"\)\s*$|" + _SUFFIX + r"\.?\s*$", t):
        m = _NOTICE_OF.search(text[:400])
        if m and m.start() and _ENDS.search(_clean(_PAREN.sub(" ", text[:m.start()]))):
            t = f"{t} {text[:m.start()]}"
    return t


def _liquidators(text: str) -> tuple:
    sig = list(_SIGNED.finditer(text))
    if not sig:
        return [], None
    m = sig[-1]
    raw = m.group("names").strip()   # a stop inside it is an initial's: a sentence cannot end inside the names
    out = []
    for i, n in enumerate(p for p in re.split(r"\s*,\s*|\s+and\s+|\s*&\s*", raw) if p.strip()):
        n = _clean(n)
        if _QUALIFICATION.match(n) and out:
            continue              # "Ann Example, C.A." : a post-nominal, not a person
        if not _PERSON.match(n) or _NOT_NAME.search(n) or _QUALIFICATION.match(n):
            return [], ("signature", "the signature is not a list of names")
        out.append(n)
    above = _key(text[:m.start()])
    role = _clean(m.group("role"))
    def seen(n):
        return "full" if _key(n) in above else "surname" if _key(n.split()[-1]) in above else "no"
    return [Liquidator(i, n, role, seen(n)) for i, n in enumerate(out, 1)], None


#: a list's name ends at its suffix; TRUST ends a name only as a word with no LIMITED, BOARD or COMPANY after it
#: ("ABLE TRUSTEES LIMITED" and "ABLE TRUST LIMITED" are one name each)
_LIST_SUFFIX = r"(?:\b(?:LIMITED|LTD|Limited|Ltd|INCORPORATED|Incorporated)(?!\s+(?:PARTNERSHIP|Partnership)\b)|\b(?:TRUST|Trust|PARTNERSHIP|Partnership)\b(?!\s*(?:LIMITED|Limited|LTD|Ltd|INCORPORATED|Incorporated|BOARD|Board|COMPANY|Company)\b))"
_LIST_NAME = re.compile(rf"\s*(?P<name>[A-Z0-9][^|]*?{_LIST_SUFFIX})(?:\s*\([^()]*(?:\([^()]*\)[^()]*)*\))*\.?(?=\s*(?:[A-Z0-9]|$))")


def _list(text: str, r: Reading) -> Reading:
    """The Official Assignee's list: `NAME | date` rows, or (before about
    2016) a date and then the names liquidated that day, each ending in its
    suffix and a stop."""
    r.shape = "list"
    head = _LIST_HEAD.search(text)
    seg = text[head.end():] if head else text
    rows = []
    if "|" in seg:
        for m in _LIST_ROW.finditer(seg):
            rows.append((_clean(m.group("name")), m.group("d")))
    else:
        days = list(re.finditer(_DAY, seg))
        for i, d in enumerate(days):
            chunk = seg[d.end():days[i + 1].start() if i + 1 < len(days) else len(seg)]
            pos = 0
            while True:
                m = _LIST_NAME.match(chunk, pos)
                if not m:
                    break
                rows.append((_clean(m.group("name")), d.group(0)))
                pos = m.end()
    n = 0
    for name, day in rows:
        if not name or len(name) > 160 or re.search(r"[a-z]{3,}\s+[a-z]{3,}", name):
            r.unread.append((f"row {n + 1}", "a list row that is not a company name"))
            continue
        n += 1
        r.companies.append(Company(n, name, appointed_on=_date(day), date_basis="list date"))
    if not r.companies:
        r.unread.append(("list", "an Official Assignee's list with no rows the reader can cut"))
    r.liquidators = [Liquidator(1, "Official Assignee", "Liquidator", "full")] if "Official Assignee" in text else []
    return r


_TIME = r"\d{1,2}(?:[.:]\s*\d{2})?\s*[ap]\.?\s*m\.?"
_BELOW = re.compile(r"(?:below|following\s+compan(?:y|ies)(?:\s+on)?(?:\s+the\s+\w+\s+and\s+times?\s+\w+)?)\s*:", re.I)
_BELOW_ROW = re.compile(rf"[\s?•·.;]*(?:(?:on\s+)?(?P<d>{_DAY})\s*)?[\s?•·]*(?P<name>[A-Z0-9][^?•·;:]*?\b{_SUFFIX})\.?"
                        rf"(?:\s*\([^)]*\))*\s*(?:at\s*(?P<t>{_TIME}))?")


def _below(text: str) -> list:
    """[(name, date, time)] from "on the dates and times below: 9 May 2016
    ACME LIMITED at 10.30am. BETA LIMITED at 11.00am." (a date carries on
    to the names after it until the next)."""
    m = _BELOW.search(text)
    if not m:
        return []
    out, pos, day = [], m.end(), None
    while True:
        row = _BELOW_ROW.match(text, pos)
        if not row or row.end() == pos or re.search(r"\b[a-z]{3,}\s+[a-z]{3,}\b", row.group("name")):
            break                 # prose, or a firm's name in the contact lines: the rows have ended
        day = row.group("d") or day
        out.append((_clean(row.group("name")), _date(day), _clean(row.group("t") or "") or None))
        pos = row.end()
    return out


_NAMES = r"(?P<names>(?:[A-Z][\w’'\-]*\.?\s+){1,4}[A-Z][\w’'\-]+(?:(?:,\s*|\s+and\s+)(?:[A-Z][\w’'\-]*\.?\s+){1,4}[A-Z][\w’'\-]+)*)"
_SENTENCE = re.compile(
    rf"(?:\bappointed\s+|\bthat\s+|\bappointment\s+of\s+|\bLiquidators?\s+|^|[.:]\s*|(?<=\d)){_NAMES}(?:,[^.;:]{{0,120}}?,?)?\s+"
    r"(?:(?:was|were|has\s+been|have\s+been|be)\s+appointed|as\s+(?:the\s+)?(?:joint\s+(?:and\s+several\s+)?)?liquidators?\b)", re.M)


def _from_sentence(text: str) -> list:
    """The liquidators named in the operative sentence, for a notice that
    prints no signature."""
    m = _SENTENCE.search(text)
    if not m:
        return []
    names = [_clean(n) for n in re.split(r"\s*,\s*|\s+and\s+", m.group("names")) if n.strip()]
    if not names or any(_NOT_NAME.search(n) or not _PERSON.match(n) for n in names):
        return []
    return [Liquidator(i, n, "named as appointed", "full") for i, n in enumerate(names, 1)]


def read(title: str, text: str) -> Reading:
    title, text = title or "", text or ""
    r = Reading(corrigendum=bool(_CORRIGENDUM.match(title) or _CORRIGENDUM.match(text[:40])))
    s = _S241.search(text)
    r.appointed_by = _BY_SECTION[s.group(1).lower()] if s else (
        "court" if re.search(r"High Court|order of the Court|by the Court", text) else
        "shareholders" if re.search(r"shareholder", text, re.I) else
        "board" if re.search(r"\bboard\b", text, re.I) else
        "creditors" if re.search(r"creditors\s+(?:resolved|appointed)|meeting\s+of\s+creditors", text, re.I) else None)
    sec = _SECTION.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    d = _DATED.search(text)
    r.dated_on = _date(d.group("d")) if d else None
    if _LIST_HEAD.search(text) or re.match(r"^\s*Liquidations?\s*$", title):
        return _list(text, r)
    r.shape = "notice"
    below = _below(text)
    if _BARE.match(_CORRIGENDUM.sub("", title)):
        names = [n for n, _, _ in below] or [_clean(m.group("co")) for m in _BODY_CO.finditer(text)]
        names, left = list(dict.fromkeys(n for n in names if n)), []
        if not names:
            r.unread.append(("title", "the title names no company and the body names none the reader can find"))
    else:
        names, left = split_names(_title_head(title, text))
    for x in left:
        r.unread.append(("title", "a part of the title that ends in no legal suffix"))
    numbers = list(dict.fromkeys(_NUMBER.findall(text)))
    # the appointment's date: the dates near the operative words, with their time where printed
    whens = []
    for a in _APPOINTED.finditer(text):
        for w in _WHEN.finditer(text, max(0, a.start() - 200), min(len(text), a.end() + 250)):
            whens.append((_date(w.group("d")), _clean(w.group("t") or "") or None))
        if whens:
            break
    timed = list(dict.fromkeys(w for w in whens if w[1]))
    days = list(dict.fromkeys(w[0] for w in whens if w[0]))
    when = timed[0] if len(timed) == 1 else ((days[0], None) if len(days) == 1 and not timed else None)
    own = {_key(n): (d, t) for n, d, t in below if d}
    r.dates_per_company = bool(own) or (when is None and len(names) > 1 and len(timed) > 1)
    for i, n in enumerate(names, 1):
        c = Company(i, n, number=numbers[0] if len(names) == 1 and len(numbers) == 1 else None)
        if _key(n) in own:
            (c.appointed_on, c.appointed_at), c.date_basis = own[_key(n)], "appointment"
        elif when and not own:
            c.appointed_on, c.appointed_at, c.date_basis = when[0], when[1], "appointment"
        r.companies.append(c)
    r.liquidators, bad = _liquidators(text)
    if not r.liquidators and not bad:
        r.liquidators = _from_sentence(text)
    if bad:
        r.unread.append(bad)
    return r
