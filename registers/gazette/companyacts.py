"""The Registrar's other company notices under the Gazette's section `ot`
("companies: other"), four profiles, each recognised by `ot` and its own
words, then read. No model.

  gazette-amalgamation-proposal   a proposal to amalgamate (Companies Act 1993 s 221):
       every company it names, the one that continues marked so ("will
       continue as the amalgamated company"); the day it takes effect
  gazette-register-rectification  the Registrar's intention to rectify (correct)
       the register (s 360A): a list, "ACME LIMITED (1234567) – rectification
       will be by …", each company with its number; what is corrected, as a
       word from a fixed list (director, shareholding, …), never the
       sentence; each person a correction names, and an applicant who is a
       person, by initials and surname only; the day objections close
  gazette-transfer-out            a company's intention to be removed from the
       register on becoming incorporated elsewhere (s 343): the company, the
       place it goes, the day after which it applies
  gazette-deed-of-company-arrangement   a deed's execution, variation or end
       (Part 15A): the company, the action and day, the deed administrators
       as signed

No address is read: a rectification's sentences can print one, and only
the fixed words and the initials leave them. A part the reader cannot take
is a catch-log line, never a guess.

    Amalgamation, Rectification, TransferOut, DeedOfArrangement   .recognise / .read
    initials(name)        "Ann Mary Example" → "A. M. Example"
"""
import re

from registers.gazette import liquidations as LQ
from registers.gazette import restorations as RS
from registers.gazette.entries import Entry, Reading

CODE = "ot"
_SUFFIX = (r"(?:LIMITED|Limited|LTD|Ltd|INCORPORATED|Incorporated|PARTNERSHIP|Partnership|TRUST|Trust|COMPANY|Company|"
           r"PTY\s+LTD|Pty\s+Ltd|PLC|plc|LP|AG|GmbH|SA|BV|NV|Inc\.?|INC\.?|Corporation|CORPORATION)")
_SMALL = {"of", "the", "for", "&", "de", "du", "la", "le", "van", "von", "der", "te", "in"}
#: a bracket after a name that is not its own: a status, a defined term, a number
_AFTER = re.compile(r"(?:\s*\((?![A-Z]{2,4}\)|N\.?Z\.?\)|\d{4}\))[^()]*(?:\([^()]*\)[^()]*)*\))+")
_PARTICLE = {"van", "de", "der", "von", "du", "le", "la", "te", "da", "di", "Mc", "Mac", "St", "O"}


def initials(name: str) -> str:
    """A person's name as initials and surname: every word but the surname to its first letter."""
    words = [w for w in re.split(r"[\s.]+", name or "") if w]
    if not words:
        return None
    k = len(words) - 1
    while k > 0 and words[k - 1] in _PARTICLE:
        k -= 1
    sur = " ".join(words[k:])
    return " ".join([f"{w[0].upper()}." for w in words[:k]] + [sur])


def _back(s: str, small=_SMALL) -> str:
    """The run of name words at the end of `s`, back to the first word that is not one ("and" ends it: a list's)."""
    out, depth = [], 0
    for t in reversed(re.findall(r"\S+", s)[-30:]):
        if depth or (t.endswith(")") and "(" not in t):
            depth += t.count(")") - t.count("(")
            out.append(t)
            continue
        if t.endswith((":", ";", ",")) or (t.endswith(".") and out and not re.fullmatch(r"(?:[A-Z]\.)+|Co\.|No\.", t)):
            break
        if t[0].isupper() or t[0].isdigit() or t[0] in "&(“\"" or t in small:
            out.append(t)
            continue
        break
    while out and out[-1].lower() in small | {"the", "and"}:
        out.pop()
    return " ".join(reversed(out))


_LEAD = re.compile(r"^(?:(?:Notice|NOTICE|Public|PUBLIC|Given|By|That|The|THE|It|Proposed|Is|Hereby|Pursuant|To|Section|Of|And|"
                   r"Amalgamation|Amalgamated|Company|Companies|Act|Proposal|In|On|With|Under|Between|Following)\s+)+")


def names_in(text: str) -> list:
    """Every company's name the prose prints, once each, in order: the words before each legal ending."""
    out, seen = [], set()
    for m in re.finditer(rf"\b{_SUFFIX}(?=[\s.,;:)(”\"’]|$)(?!\s+(?:No\b|Number|Limited|LIMITED|Ltd|LTD))", text):
        run = _back(text[:m.end()])
        run = LQ._clean(_LEAD.sub("", LQ._clean(run)))
        run = re.sub(r"^(?:\(?[“\"']?(?:the|of|and|in|for)\s+)+|^\(?[“\"']", "", run).strip()
        words = run.split()
        if len(words) < 2 or re.search(r"\b(?:Act|Section|Register|Registrar|Companies\s+Office)\b", run) \
                or all(re.fullmatch(r"(?i:amalgamated|amalgamating|continuing|holding|subsidiary|each|every|other|new|the|said|"
                                    r"above-named|parent|surviving|resulting|proposed|non-surviving|private)", w) for w in words[:-1]):
            continue
        k = LQ._key(run)
        if k not in seen:
            seen.add(k)
            out.append(run)
    return out


def _number(text: str, name: str):
    """The number printed in brackets right after `name`, else None."""
    i = text.find(name)
    m = re.match(r"\s*(?:\([^()0-9]*\)\s*)*\(\s*(?:Company\s+(?:No\.?|Number)\s*:?\s*)?(\d{4,8})\s*\)", text[i + len(name):]) if i >= 0 else None
    return m.group(1) if m else None


def _base(title: str, text: str, action: str) -> Reading:
    r = Reading(shape="notice", action=action, by_whom=None,
                corrigendum=bool(LQ._CORRIGENDUM.match(title) or LQ._CORRIGENDUM.match(text[:40])))
    sec = LQ._SECTION.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    return r


def _title_names(title: str, text: str) -> list:
    if re.match(r"^\s*(?:Corrigendum\W*)?(?:Public\s+)?(?:Notice|Advertisement)\b", title or "", re.I):
        return []
    names, left = LQ.split_names(LQ._title_head(title, text))
    return names


def _spaced(text: str) -> str:
    return re.sub(r"(?<=[a-z\d)”\"’])\.(?=[A-Z][a-z]|[A-Z]{2}|[A-Z]\.)|(?<=[a-z)”\"])(?=[A-Z][a-z])|(?<=\d{4})(?=[A-Z][a-z]|[A-Z]{2})|(?<=[;:])(?=[A-Z])",
                  lambda m: m.group(0) + " ", text)


class _Ot:
    profile, why, words = None, None, None

    @classmethod
    def recognise(cls, code: str, title: str, text: str) -> list:
        if code != CODE or RS.recognise(code, title, text):
            return []
        return [cls.why] if re.search(cls.words, f"{title or ''} {(text or '')[:600]}", re.I) else []


class Amalgamation(_Ot):
    profile, why = "gazette-amalgamation-proposal", "the Gazette's section ot, a proposal to amalgamate"
    words = r"\bamalgamat"
    _CONTINUES = [re.compile(p, re.I | re.S) for p in (
        r"(?P<x>.{0,200}?)\s*(?:\([^()]*\)\s*)?,?\s*(?:will|is\s+(?:intended\s+)?to|shall|are\s+to)\s+(?:continue\s+as|be\s+continued\s+as|become)"
        r"\s+(?:the|an)\s+amalgamated",
        r"(?P<x>.{0,200}?)\s*(?:\([^()]*\)\s*)?,?\s+(?:continuing|to\s+continue)\s+as\s+(?:the|an)\s+amalgamated",
        r"(?P<x>.{0,200}?)\s*(?:\([^()]*\)\s*)?,?\s+which\s+(?:shall|will)\s+(?:become|be|continue\s+as)\s+the\s+amalgamated",
        r"amalgamated\s+(?:\(continuing\)\s+)?company\s*,?\s*(?:\(\s*)?(?:being|namely|which\s+will\s+be|will\s+be|shall\s+be|is)\s+(?P<y>.{0,200})",
        r"amalgamated\s+company\s*:\s*(?P<y>.{0,200})",
        r"amalgamate\s+(?:in)?to\s+(?P<y>.{0,200})")]
    _OPERATIVE_END = re.compile(r"(?i:Copies\s+of\s+the\s+(?:amalgamation\s+)?proposal|available\s+for\s+inspection|registered\s+offices?)|\bDated\b")

    @classmethod
    def read(cls, title: str, text: str) -> Reading:
        title, text = title or "", _spaced(text or "")
        r = _base(title, text, "amalgamation proposal")
        e = cls._OPERATIVE_END.search(text, 80)
        body = text[:e.start()] if e else text[:1500]
        names = _title_names(title, text) + names_in(body)
        names = list({LQ._key(n): n for n in reversed(names)}.values())[::-1]
        order = {LQ._key(n): i for i, n in enumerate(names)}
        names.sort(key=lambda n: order[LQ._key(n)])
        continuing = None
        for p in cls._CONTINUES:
            m = p.search(body)
            if m:
                part = m.groupdict().get("x") or m.groupdict().get("y") or ""
                got = names_in(part)
                if got:
                    continuing = LQ._key(got[-1] if m.groupdict().get("x") is not None else got[0])
                    break
        w = re.search(rf"(?:with\s+effect\s+(?:from|on)|take\s+effect\s+on|effective\s+(?:from|on|date\s*:?))\s+(?:the\s+)?(?P<d>{LQ._DAY})", text, re.I)
        if w:
            r.event_on, r.event_basis = LQ._date(w.group("d")), "takes effect"
        r.companies = [Entry(i, n, number=_number(text, n)) for i, n in enumerate(names, 1)]
        for c in r.companies:
            c.role = "amalgamated company" if LQ._key(c.name) == continuing else "amalgamating company"
        if not r.companies:
            r.unread.append(("company", "an amalgamation that names no company the reader can find"))
        elif continuing is None:
            r.unread.append(("continuing", "the company that continues is not named where the reader looks"))
        return r


class TransferOut(_Ot):
    profile, why = "gazette-transfer-out", "the Gazette's section ot, a company leaving the register to be incorporated elsewhere"
    words = (r"transfer\w*\s+(?:of\s+)?(?:its\s+)?(?:registration|incorporation)|by\s+transfer|other\s+jurisdiction"
             r"|removed\s+from\s+the\s+New\s+Zealand\s+register\s+in\s+connection\s+with")
    _WHERE = re.compile(r"incorporated\s+(?:under\s+the\s+law(?:s)?\s+(?:in\s+force\s+)?(?:in|of)|in)\s+(?:the\s+)?"
                        r"(?P<j>(?:State\s+of\s+|Province\s+of\s+|Commonwealth\s+of\s+)?[A-Z][A-Za-z]+(?:[ ,]+(?:[A-Z][A-Za-z]+|of)){0,5})")
    _AFTER = re.compile(rf"after\s+(?:the\s+)?(?P<d>{LQ._DAY})", re.I)

    @classmethod
    def read(cls, title: str, text: str) -> Reading:
        title, text = title or "", _spaced(text or "")
        r = _base(title, text, "intention to transfer registration out of New Zealand")
        names = _title_names(title, text)
        if not names:
            m = re.search(r"(?P<x>.{0,200}?)\s*(?:\([^()]*\)\s*)?(?:hereby\s+)?gives?\s+(?:public\s+)?notice", text[:1200])
            names = names_in(m.group("x"))[-1:] if m else []
        if not names:
            names = names_in(text[:800])[:1]
        j = cls._WHERE.search(text)
        if j:
            r.ground = LQ._clean(re.split(r"\s+(?:Dated|and|by|on|with|Signed)\b", j.group("j"))[0])
        a = cls._AFTER.search(text)
        if a:
            r.event_on, r.event_basis = LQ._date(a.group("d")), "applies after"
        r.companies = [Entry(i, n, number=_number(text, n)) for i, n in enumerate(names, 1)]
        if not r.companies:
            r.unread.append(("company", "a transfer that names no company the reader can find"))
        if not r.ground:
            r.unread.append(("where", "the place it is to be incorporated is not where the reader looks"))
        return r


class DeedOfArrangement(_Ot):
    profile, why = "gazette-deed-of-company-arrangement", "the Gazette's section ot, a deed of company arrangement"
    words = r"deed\s+of\s+company\s+arrangement"
    _ACTIONS = (("deed terminated", r"terminat\w*|\bended\b|come\s+to\s+an\s+end"), ("deed varied", r"\bvari(?:ed|ation)\b"),
                ("deed executed", r"\bexecut\w*"), ("notice to creditors", r"creditors"))
    _SIGNED = re.compile(r"(?P<names>(?<![A-Za-z])[A-Z](?:[^.:;|]|(?<=\b[A-Z])\.){1,150}?),\s*(?P<role>(?:Joint\s+(?:and\s+Several\s+)?)?"
                         r"Deed\s+[Aa]dministrators?)\b")

    @classmethod
    def read(cls, title: str, text: str) -> Reading:
        title, text = title or "", _spaced(text or "")
        r = _base(title, text, None)
        head = f"{title} {text[:800]}"
        r.action = next((a for a, p in cls._ACTIONS if re.search(p, head, re.I)), "deed of company arrangement")
        names = _title_names(title, text) or names_in(text[:800])[:1]
        names = [LQ._clean(re.sub(r"\s*\((?:subject|under)\s+to?\s*deed[^()]*\)", "", n, flags=re.I)) for n in names]
        o = re.search(rf"\bOn\s+(?:the\s+)?(?P<d>{LQ._DAY})", text)
        if o:
            r.event_on, r.event_basis = LQ._date(o.group("d")), r.action
        r.companies = [Entry(i, n, number=_number(text, n)) for i, n in enumerate(names, 1)]
        r.people, bad = LQ._liquidators(text, cls._SIGNED)
        if bad:
            r.unread.append(bad)
        if not r.companies:
            r.unread.append(("company", "a deed that names no company the reader can find"))
        return r


#: what a rectification corrects, as the register's own words: the first of these each row's sentences hold
GROUNDS = (("director", r"\bdirectors?\b"), ("shareholding", r"\bshare(?:s|holders?|holding|holdings)?\b|\ballotment"),
           ("liquidation", r"\bliquidat\w*"), ("receivership", r"\breceivers?(?:hip)?\b"), ("administration", r"\badministrat\w*"),
           ("company name", r"\bname\b"), ("annual return", r"annual\s+returns?"), ("address", r"\baddress\w*|registered\s+office"),
           ("constitution", r"\bconstitution\b"), ("amalgamation", r"\bamalgamat\w*"), ("removal or restoration", r"\bremov(?:al|ed)\s+from|\brestor\w*"),
           ("ultimate holding company", r"ultimate\s+holding"))
_WORD = r"[A-Z][a-zA-Z'’\-]+"
_PERSON = rf"(?:(?:[A-Z]\.\s?){{1,3}}|(?:{_WORD}\s+){{1,4}})(?:(?:van|de|der|von|du|le|la|te|Mc|Mac)\s+)?{_WORD}"
#: where a correction names a person: the name between these words
_NAMED = [re.compile(p) for p in (
    rf"(?:appointment|resignation|removal|cessation|particulars|consent)\s+of\s+(?P<p>{_PERSON})(?=\s+(?:as|was|is|from|to|dated|on)\b)",
    rf"(?:that|show|showing|record|recording|reflect|reflecting|leaving|being|and|with|by|;)\s+(?P<p>{_PERSON})(?=\s+(?:as|was|is|remains?|ceased|resigned|"
    rf"has|had|holds?|held|incorrectly|having|became|be|being)\b)",
    rf"(?:^|[.;:]\s+)(?P<p>{_PERSON})(?=\s+(?:as\s+having|incorrectly|was\s+(?:incorrectly|not|never)|remains?|is\s+the|ceased))",
    rf"\bname\s+of\s+(?P<p>{_PERSON})\s+was\s+\w+\s+to\b",
    rf"\bto\s+(?P<p>{_PERSON})(?=[.;]|\s+(?:as|and)\b)")]
_NOT_PERSON = re.compile(r"\b(?:Remove|Removing|Record|Recording|Show|Showing|Delete|Deleting|Amend|Amended|Register|Registrar|Registered|Particulars|"
                         r"Director|Directors|Shareholder|Shareholders|Shares?|Company|Companies|Limited|LIMITED|Ltd|Act|New|Zealand|Notice|"
                         r"Application|Applicant|Annual|Return|Returns|Liquidator|Liquidators|Receiver|Receivers|Form|Forms|Office|Change|"
                         r"Consent|Resolution|The|That|This|To|Any|Effect|Allotment|Trust|Trustees?|Holdings?|Group|Board|January|February|"
                         r"March|April|May|June|July|August|September|October|November|December|Monday|Tuesday|Wednesday|Thursday|Friday|"
                         r"Correct|Correction|Rectification|Rectify|Inquiries|Enquiries|Contact|Email|Postal|Private|Bag|Street|Road|Auckland|"
                         r"Wellington|Christchurch|Level|PO|Box)\b")
_APPLIED = re.compile(r"\(\s*(?:the\s+)?(?:application|applied\s+for)\s+by\s+(?:the\s+)?(?P<a>[^()]{2,160}?)\s*\)", re.I)
_ROLE_APPLICANT = re.compile(r"^(?:company|companies|directors?|liquidators?|receivers?|administrators?|shareholders?|secretary|"
                             r"solicitors?|lawyers?|accountants?)(?:\s+of\s+the\s+company)?$", re.I)
#: a row's head: "ACME LIMITED (in liquidation) (1234567) –"
_ROW = re.compile(r"(?P<n>\(\s*\d{4,8}\s*\))\s*[–—\-:]\s*")
_LIST_END = re.compile(r"(?i:Any\s+person\s+who\s+wishes|Any\s+objections?)|\bDated\b")       # "dated 3 October" is inside a row


#: the only form a person leaves a rectification in
INITIALLED = re.compile(r"(?:[A-Z]\. )+(?:(?:van|de|der|von|du|le|la|te|da|di|Mc|Mac|St|O) )*[A-Z][\w'’\-]+")


def _people(segment: str) -> list:
    """The persons a correction's sentences name, by initials and surname, once each."""
    seg = _APPLIED.sub(" ", segment)
    out = []
    for p in _NAMED:
        for m in p.finditer(seg):
            name = m.group("p")
            words = name.split()
            while words and _NOT_PERSON.fullmatch(words[0]):
                words.pop(0)
            if len(words) < 2 or any(_NOT_PERSON.fullmatch(w.rstrip(".")) for w in words) or re.match(rf"\s*{_SUFFIX}\b", seg[m.end():]):
                continue
            got = initials(" ".join(words))
            if got and INITIALLED.fullmatch(got) and got not in out:
                out.append(got)
    return out


def _applicant(segment: str):
    """Who applied, where a row says so: a company by name, a role as a word, a person by initials and surname."""
    m = _APPLIED.search(segment)
    if not m:
        return None
    a = LQ._clean(m.group("a"))
    if re.search(rf"\b{_SUFFIX}\.?$", a) and not re.search(r",", a):
        return a
    if _ROLE_APPLICANT.match(a):
        return a.lower()
    words = re.findall(r"[A-Z][\w'’\-]*\.?", a)
    if 2 <= len(words) <= 6 and len(" ".join(words)) >= len(a) - 6 and not any(_NOT_PERSON.fullmatch(w.rstrip(".")) for w in words):
        got = initials(" ".join(words))
        return got if INITIALLED.fullmatch(got) else "not read"
    return "not read"


def _row_name(head: str):
    """The company before a row's number: its capitals and brackets, back to the sentence before it."""
    head = LQ._clean(head)
    toks = re.findall(r"\S+", head)
    out, depth = [], 0
    for t in reversed(toks[-30:]):
        if depth or (t.endswith(")") and "(" not in t):
            depth += t.count(")") - t.count("(")
            out.append(t)
            continue
        core = re.sub(r"[^A-Za-z0-9]", "", t)
        if t.endswith((".", ":", ";")) and out and not re.fullmatch(r"(?:[A-Z]\.)+|CO\.|LTD\.|N\.Z\.", t):
            break
        if core and (core.isupper() or core.isdigit()) or t in ("&", "-", "–") or (t.startswith("(") and t.endswith(")")):
            out.append(t)
            continue
        break
    name = " ".join(reversed(out))
    name = LQ._clean(LQ._PAREN.sub(" ", re.sub(r"^(?:\([^()]*\)\s*)+", "", name))) if name else ""
    if len(re.sub(r"[^A-Z]", "", name)) >= 2 and len(name.split()) >= 2 or re.search(rf"\b{_SUFFIX}$", name):
        return name
    mixed = LQ._clean(_LEAD.sub("", LQ._clean(LQ._PAREN.sub(" ", _back(head)))))
    return mixed if re.search(rf"\b{_SUFFIX}\.?$", mixed) and len(mixed.split()) >= 2 else None


class Rectification(_Ot):
    profile, why = "gazette-register-rectification", "the Gazette's section ot, the Registrar's intention to rectify the register"
    words = r"correct\s+(?:the\s+)?(?:New\s+Zealand\s+)?register|\brectif\w*\s+(?:the\s+)?(?:New\s+Zealand\s+)?(?:\w+\s+)?register"

    @classmethod
    def read(cls, title: str, text: str) -> Reading:
        title, text = title or "", _spaced(text or "")
        r = _base(title, text, "intention to rectify the register")
        r.shape, r.by_whom = "list", "Registrar"
        o = RS._OBJECT_BY.search(text)
        if o:
            r.event_on, r.event_basis = LQ._date(o.group("d")), "objections by"
        end = _LIST_END.search(text, 200)
        body = text[:end.start()] if end else text
        heads = list(_ROW.finditer(body))
        rows, starts = [], []
        for k, m in enumerate(heads):
            start = heads[k - 1].end() if k else 0
            name = _row_name(body[start:m.start()])
            if name is None:
                r.unread.append((f"row {k + 1}", "the text before a number does not end in a company's name"))
                continue
            begins = body.rfind(name.split()[0], start, m.start())
            starts.append((name, m.group("n").strip("() "), m.end(), begins if begins >= 0 else m.start()))
        for i, (name, number, at, _) in enumerate(starts):
            nxt = starts[i + 1][3] if i + 1 < len(starts) else len(body)       # up to the next row's company
            seg = body[at:nxt]
            grounds = [g for g, p in GROUNDS if re.search(p, seg, re.I)]
            e = Entry(len(rows) + 1, name, number=number)
            e.ground = "; ".join(grounds[:3]) or "other"
            e.people = "; ".join(_people(seg)) or None
            e.party = _applicant(seg)
            rows.append(e)
        r.companies = rows
        if not rows:
            r.unread.append(("list", "a rectification with no company and number the reader can take"))
        return r
