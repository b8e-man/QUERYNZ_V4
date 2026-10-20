"""The published text, cut before any property it names (hard limit 15). One
place every reader shares: `read.read` passes every row it built through
`rows`, so a notice's title (a possession notice's cut harder, by
possessions.public_title) and every other text column the lane publishes
(a company as printed, a plaintiff, a lender, a name) is cut the same way,
and the uncut value goes to `gazette_private.uncut` only.

A property is named three ways, and the cut is made at the first:

  street      a house number and a street: "12 Sample Street", "2/14A Sample
              Road", "12-14 SAMPLE AVENUE"; a highway's or a rule's number
              before a road's name is not one ("State Highway 2 Hutt Road")
  legal       the land's legal description: "Lot 2 DP 12345", "Section 5
              Block II", "Record of Title NA12/34", "CT 12A/345", "Unit 3"
  numbered    a number led by the word that places it: "at 12 Sample",
              "Properties 12 and 14", "situated at 7", ", of 12 Sample"

A company's name is not a property: "12 Sample Street Limited" is the
Companies Office register's own name for a company, published by the
companies lane, and is kept whole. What stands before the cut is kept less
the words that led into it ("at", "situated at", "known as", ", of", a
dash, a bracket); a title that is nothing but a property is published
empty. Measured on every notice on 21 October 2026: see pane.md.

    find(text)          the first property the text names, as a match, or None
    public(text)        the text cut before it (the text itself where it names none)
    rows(result, tables)  cuts every published text field of every row in place; returns
                        [(row key, column, uncut value)] for the private table
"""
import re

from registers.gazette import possessions

_NUM = r"\d{1,4}[A-Za-z]?(?:\s*[-/]\s*\d{1,4}[A-Za-z]?)?"
_STREET = (r"(?i:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Crescent|Cres|Terrace|Tce|Lane|Way|Parade|Highway|Hwy|"
           r"Grove|Close|Court|Ct|Rise|Quay|Square|Boulevard|Esplanade|Track|Mews|Heights|Glade|Row|Loop|Walk|Promenade|"
           r"Strand|Mall|Circle|Common|Ridge|Vale|Downs|Line|Valley|Hill|View|Green|Gardens|Park|Point|Reach|Key)")
# a number a highway, an Act, a rule or a part carries is not a house's
_NOT_A_HOUSE = "".join(f"(?<!{re.escape(w)} )" for w in ("Highway", "Hwy", "SH", "No", "No.", "Act", "Regulations", "Rule", "Order",
                                               "Notice", "Section", "Schedule", "Part", "Clause", "Reg", "Route"))
STREET = re.compile(rf"(?<![\w/.-]){_NOT_A_HOUSE}{_NUM},?\s+(?:[A-Z][\w'’.-]*\s+){{1,4}}{_STREET}\b")
LEGAL = re.compile(
    r"\bLots?\s+\d+[A-Za-z]?(?:\s*(?:,|and|&)\s*\d+[A-Za-z]?)*,?\s+(?:on\s+)?(?:DP|Deposited\s+Plan|LT|SO)\b"
    r"|\bDP\s*\d{3,}|\bDeposited\s+Plan\s+(?:No\.?\s*)?\d"
    r"|\bSections?\s+\d+[A-Za-z]?(?:\s*(?:,|and|&)\s*\d+[A-Za-z]?)*,?\s+(?:Block|Town|Suburban|Village|Rural|SO|DP)\b"
    r"|\b(?:Record\s+of\s+Title|Certificate\s+of\s+Title|Computer\s+(?:Freehold|Unit|Leasehold)\s+Register)\s+(?:No\.?\s*)?\S*\d"
    r"|\b(?-i:CT)\s+\S*\d|\bIdentifier\s+\S*\d|\b(?:Unit|Flat)\s+\d{1,4}[A-Za-z]?\b", re.I)
NUMBERED = re.compile(r"(?:\b(?:at|known\s+as|premises|propert(?:y|ies)|dwelling|house|residence)\s+(?:No\.?\s*)?"
                      r"|,\s*(?:formerly\s+|late\s+)?of\s+)(?!(?:18|19|20)\d\d\b)(\d{1,4}[A-Za-z]?)\b"
                      r"(?!\s*(?:am|pm|a\.m|p\.m|o'clock|hours?|days?|months?|years?|per\s*cent|%|st|nd|rd|th)\b)"
                      r"(?!\s*(?:day\s+of\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b)", re.I)
# the name of a company: up to four more words, then its legal ending
_COMPANY = re.compile(r"[\s,]*(?:[A-Z(][\w'’&().-]*\s+){0,4}(?:Limited|Ltd|Incorporated|Inc)\b", re.I)
_LEAD = re.compile(r"(?:[\s,;:(\[–—-]|\b(?:at|situated|known\s+as|being|of|formerly|late|on|re)\b)+$", re.I)
#: the fields that are not words from the notice: numbers, keys, dates, provenance
SKIP = {"notice", "url", "article", "source_note", "old_type", "supersedes", "superseded_by", "withheld_by", "key", "place",
        "document", "reader", "profile", "read_from", "family", "format", "status", "section", "published_on", "dated_on",
        "event_on", "filed_on", "starts_on", "ends_on", "entered_on", "appointed_on", "period_from", "period_to"}


def find(text: str):
    hits = []
    for pat in (STREET, LEGAL, NUMBERED):
        for m in pat.finditer(text or ""):
            if not _COMPANY.match(text, m.end()):
                hits.append((m.start(1) if pat is NUMBERED else m.start(), m))
                break
    return min(hits, key=lambda h: h[0])[1] if hits else None


#: a run of house numbers before the one a street follows: "12, 14 and 16 Sample Road"
_RUN = re.compile(r"(?:\b\d{1,4}[A-Za-z]?\s*(?:,|and|&|-|/)\s*)+$", re.I)


def _start(text: str, m) -> int:
    at = m.start(1) if m.re is NUMBERED else m.start()
    run = _RUN.search(text[:at])
    return run.start() if run else at


def public(text: str) -> str:
    m = find(text)
    if not m:
        return text
    return _LEAD.sub("", text[:_start(text, m)]).strip()


TABLES = ("notices", "celebrants", "prohibitions", "liquidations", "liquidators", "company_notices", "practitioners",
          "bankruptcies", "appointments", "possessions")


def rows(result, tables=TABLES) -> list:
    """Every row's published text cut in place, the uncut value returned for the private table."""
    uncut = []
    for t in tables:
        for r in getattr(result, t):
            filed = r.get("filed", {})
            for col, v in filed.items():
                if col in SKIP or col.startswith("_"):
                    continue
                if isinstance(v, str):
                    # a possession notice's title is cut harder: at its first "at" or its first number
                    cut = public(possessions.public_title(v) if t == "notices" and col == "title"
                                 and filed.get("format") == possessions.PROFILE else v)
                    if cut != v:
                        uncut.append((r["key"], col, v))
                        filed[col] = cut
                elif isinstance(v, list) and any(isinstance(x, str) and find(x) for x in v):
                    uncut.append((r["key"], col, "\n".join(x for x in v if isinstance(x, str))))
                    filed[col] = [public(x) if isinstance(x, str) else x for x in v]
    return uncut
