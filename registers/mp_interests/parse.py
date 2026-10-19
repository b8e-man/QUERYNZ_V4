"""One edition of the Register of Pecuniary and Other Specified Interests,
from its text layer (pdftotext with the layout kept, page by page), into
members and their declarations. No model; no guess.

What the measured editions (2006 to 2026) share:

  the front     a title page ("… Summary of annual returns as at 31 January
                2018"), the Registrar's letter, and an introduction that
                lists the categories by number and heading, in the
                statutory wording ("10 Debts owed by a member (clauses …)")
  the members   a header line per member, "Name (Party, Electorate)"; then
                for each category declared a line "N   Heading", in the
                return's wording ("10 Debts owed by you"), and the
                declarations beneath it, indented, one per line; a
                declaration too long for the line wraps onto the next, which
                then starts lower-case
  the annex     after the last member, every edition reprints the rules
                (Appendix B of the Standing Orders), whose clause numbers
                look exactly like category lines. It is cut at its heading,
                the first after the last member header, and never read as
                anybody's declarations

THE CATEGORY IS THE HEADING, NEVER THE NUMBER. The register renumbered its
categories between the 2017 and 2018 editions (thirteen to fourteen, a new
"Managed investment schemes" at 8): 9 is "Creditors" up to 2017 and
"Debtors" after, 10 is "Overseas travel" before and "Creditors" after. So a
declaration is keyed on its heading's wording (`HEADINGS`), and the number
is kept as printed beside it, as an attribute. A wording the map has never
seen is not guessed: its declarations are catch-log lines.

    edition(pages)      Edition: as_at, categories (the introduction's own list), members, declarations, set_aside
    heading_of(text)    the category slug for a heading's wording, or None
"""
import datetime as dt
import re
from dataclasses import dataclass, field

#: heading wording (folded: lower case, single spaces, no trailing stop) → category slug. Every wording here was
#: read off the 21 held editions, in the members' sections and in each introduction's own list.
HEADINGS = {
    "company directorships and controlling interests": "directorships",
    "interests (such as shares and bonds) in companies and business entities": "business-interests",
    "other companies and business entities": "business-interests",
    "employment": "employment",
    "beneficial interests in trusts": "trusts",
    "beneficial interests in, and trusteeships of, trusts": "trusts",
    "interests in trusts": "trusts",
    "trusts": "trusts",
    "organisations and trusts seeking government funding": "seeking-government-funding",
    "real property": "real-property",
    "superannuation schemes": "retirement-schemes",
    "retirement schemes": "retirement-schemes",
    "managed investment schemes": "managed-investment-schemes",
    "investment schemes": "managed-investment-schemes",
    "debtors": "debts-owed-to-member",
    "debts owed to you": "debts-owed-to-member",
    "debts owed to a member": "debts-owed-to-member",
    "creditors": "debts-owed-by-member",
    "debts owed by you": "debts-owed-by-member",
    "debts owed by a member": "debts-owed-by-member",
    "overseas travel": "overseas-travel",
    "overseas travel costs": "overseas-travel",
    "gifts": "gifts",
    "discharged debts": "discharged-debts",
    "payments for activities": "payments-for-activities",
    "payment for activities": "payments-for-activities",
}
#: the categories whose declarations can place a member's home: held in the private schema, never published
#: (hard limit 15; the decision queue asks Arthur whether the property kind may be shown)
PRIVATE_CATEGORIES = ("real-property",)

#: a member's header; a nickname in brackets may sit inside the name ("Tutehounuku (Nuk) Korako (National, List)")
_MEMBER = re.compile(r"^\s*([A-ZĀĒĪŌŪ](?:[^()]|\([^(),]*\))*?[^\s(])\s+\(([^,()]+),\s*([^()]+)\)\s*$")
#: a member the edition prints with one bracket, the electorate, and no party (an independent: 2019-20, 2023, 2026,
#: sometimes with a footnote mark); taken only at the margin of the category line that follows it, so a declaration
#: such as "Example Family Trust (beneficiary)", indented deeper, is never taken for a member
_MEMBER_ONE = re.compile(r"^([A-ZĀĒĪŌŪ](?:[^()]|\([^(),]*\))*?[^\s(])\s+\(([^,()]+)\)\s*[*∗⁎]?\s*$")
#: what keeps a one-bracket declaration from being read as a member: an organisation's word in the name, or a role
#: in the bracket ("Example Family Trust (beneficiary)", "Example Fund – Example (South Africa)"), measured on the 21 editions
_NOT_A_MEMBER = re.compile(r"\b(trust|fund|foundation|limited|ltd|runanga|rūnanga|scheme|society|incorporated|inc)\b|[–—]", re.I)
_ROLE = re.compile(r"\b(trustee|beneficiary|settlor|director|shareholder|resolution)\b", re.I)
_CATEGORY = re.compile(r"^\s*(\d{1,2})\s{2,}(\S.*?)\s*$")
_ANNEX = re.compile(r"^\s*(annex\b.*|(standing orders\s*[—–\-]\s*)?appendix\s+b\b.*)$", re.I)
_CONT = re.compile(r"^(?!www\.|https?://)[a-z(]")
#: the page footnote on a low-interest debt opens with its marker at the margin, or on a line of its own (2015)
_FOOTNOTE = re.compile(r"^(\s{0,8}[*∗⁎](\s|$)|\s*[*∗⁎]\s*$)")
_RUNNING = re.compile(r"^\s*(register of pecuniary.*|annual returns\b.*|j\.\s*7\b.*|\d{1,3})\s*$", re.I)
_AS_AT = re.compile(r"as at\s+(\d{1,2})\s+([A-Za-z]+)\s+((?:19|20)\d{2})", re.I)
_PARTY_WORDS = ("national", "labour", "green", "act", "new zealand first", "nz first", "māori", "maori", "te pāti",
                "te paati", "united future", "progressive", "mana", "independent", "opportunity")
_PARTY = re.compile(r"\b(" + "|".join(re.escape(w) for w in _PARTY_WORDS) + r")\b", re.I)
MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december")


def fold(s: str) -> str:
    return " ".join((s or "").split()).lower().rstrip(".:;")


def heading_of(text: str):
    return HEADINGS.get(fold(text))


@dataclass
class Declaration:
    page: int
    line: int                    # the line on its page, from 1, where it starts
    member: int                  # index into Edition.members
    number: str                  # the category number as printed
    heading: str                 # the heading as printed (folded whitespace)
    category: str                # the slug (HEADINGS)
    text: str                    # verbatim, wrapped lines joined with a space


@dataclass
class Member:
    page: int
    line: int
    printed: str                 # the header line as printed
    name: str
    party: str                   # None where the header prints no party
    electorate: str
    statement: str = None        # a line the edition prints for the member in place of declarations
                                 # ("No interests declared …", "Return not received by due date")


@dataclass
class Edition:
    as_at: dt.date = None
    as_at_printed: str = None
    categories: dict = field(default_factory=dict)       # the introduction's own list: number → (heading, slug)
    members: list = field(default_factory=list)
    declarations: list = field(default_factory=list)
    set_aside: list = field(default_factory=list)        # [(page, line, stage, reason)]
    annex_at: tuple = None                               # (page, line) where the reprinted rules begin
    wrapped: int = 0                                     # declarations joined across a wrap


def is_member(raw: str):
    m = _MEMBER.match(raw)
    if not m or not _PARTY.search(m.group(2)):
        return None
    return m


def _lines(pages: dict) -> list:
    """[(page, line on page, text)] for every non-blank line, running heads and page numbers dropped."""
    out = []
    for p in sorted(pages):
        for i, raw in enumerate((pages[p] or "").splitlines(), 1):
            if raw.strip() and not _RUNNING.match(raw):
                out.append((p, i, raw.rstrip()))
    return out


def _as_at(lines: list):
    head = " ".join(t for p, _, t in lines if p <= 2)
    m = _AS_AT.search(" ".join(head.split()))
    if not m:
        return None, None
    d, mon, y = m.groups()
    if mon.lower() not in MONTHS:
        return None, m.group(0)
    return dt.date(int(y), MONTHS.index(mon.lower()) + 1, int(d)), m.group(0)


def _intro_list(lines: list) -> dict:
    """The introduction's numbered list of categories, before the first member: number → (heading, slug).
    A heading wraps onto the next line before its clause reference closes; the reference is dropped."""
    out, cur = {}, None
    for p, i, t in lines:
        if is_member(t):
            break
        m = _CATEGORY.match(t)
        if m and 1 <= int(m.group(1)) <= 14 and m.group(1) not in out:
            cur = [m.group(1), m.group(2)]
            out[cur[0]] = cur
        elif cur and not _CATEGORY.match(t) and "(clause" in t.lower() and "(clause" not in cur[1].lower():
            cur[1] += " " + t.strip()                     # "… in companies and business" / "entities (clause …)"
            cur = None
        elif cur and heading_of(cur[1] + " " + t.strip()) and "(clause" not in cur[1].lower():
            cur[1] += " " + t.strip()
            cur = None
        else:
            cur = None
    res = {}
    for n, (_, h) in out.items():
        h = re.split(r"\s*\(clauses?\b", h, flags=re.I)[0].strip().rstrip(".")
        res[n] = (" ".join(h.split()), heading_of(h))
    return res


def edition(pages: dict) -> Edition:
    ed = Edition()
    lines = _lines(pages)
    ed.as_at, ed.as_at_printed = _as_at(lines)
    ed.categories = _intro_list(lines)
    last = max((k for k, (_, _, t) in enumerate(lines) if is_member(t)), default=None)
    if last is None:
        ed.set_aside.append((None, None, "edition", "no member header found"))
        return ed
    cut = next((k for k in range(last + 1, len(lines)) if _ANNEX.match(lines[k][2])), None)
    if cut is not None:
        ed.annex_at = lines[cut][:2]
        lines = lines[:cut]
    else:
        ed.set_aside.append((None, None, "edition", "no reprint of the rules found after the last member; "
                                                    "the edition is read to its end"))
    cur = number = heading = category = None
    in_footnote = False
    k = 0
    while k < len(lines):
        p, i, raw = lines[k]
        m = is_member(raw)
        one = None
        if not m and k + 1 < len(lines):
            # only at the margin a category line takes, with a category line next
            one = _MEMBER_ONE.match(raw.strip())
            nxt_raw = lines[k + 1][2]
            nxt = _CATEGORY.match(nxt_raw)
            if not (one and nxt and heading_of(nxt.group(2))
                    and len(raw) - len(raw.lstrip()) <= len(nxt_raw) - len(nxt_raw.lstrip())
                    and not _NOT_A_MEMBER.search(one.group(1)) and not _ROLE.search(one.group(2))):
                one = None
        if m or one:
            name, party, electorate = (m.group(1), m.group(2), m.group(3)) if m else (one.group(1), None, one.group(2))
            ed.members.append(Member(p, i, " ".join(raw.split()), name.strip(), party and party.strip(),
                                     electorate.strip()))
            cur = len(ed.members) - 1
            number = heading = category = None
            in_footnote = False
            k += 1
            continue
        if cur is None:
            k += 1
            continue
        if _FOOTNOTE.match(raw):
            in_footnote = True
            k += 1
            continue
        c = _CATEGORY.match(raw)
        if c and int(c.group(1)) <= 14:
            number, heading = c.group(1), " ".join(c.group(2).split())
            category = heading_of(heading)
            if category is None and k + 1 < len(lines):
                joined = heading + " " + lines[k + 1][2].strip()       # a heading wrapped by the layout (2006-08)
                if heading_of(joined):
                    heading, category = " ".join(joined.split()), heading_of(joined)
                    k += 1
            in_footnote = False
            k += 1
            continue
        if in_footnote:
            k += 1
            continue
        indent = len(raw) - len(raw.lstrip())
        text = raw.strip()
        if number is None and sum(ch.isalpha() for ch in text) >= 2:
            mem = ed.members[cur]
            mem.statement = f"{mem.statement} {text}" if mem.statement else text
            k += 1
            continue
        last_d = ed.declarations[-1] if ed.declarations else None
        mine = last_d is not None and last_d.member == cur and last_d.number == number and number is not None
        # a wrap: the remainder starts lower-case, or closes a bracket the line above left open ("… in March" / "2015)")
        open_paren = mine and last_d.text.count("(") > last_d.text.count(")")
        if not open_paren and (number is None or indent < 4 or sum(ch.isalpha() for ch in text) < 2):
            ed.set_aside.append((p, i, "line", f"a line outside any category: {text[:80]!r}"))
            k += 1
            continue
        if mine and (_CONT.match(text) or open_paren):
            last_d.text = f"{last_d.text} {text}"
            ed.wrapped += 1
            k += 1
            continue
        ed.declarations.append(Declaration(p, i, cur, number, heading, category, text))
        k += 1
    return ed
