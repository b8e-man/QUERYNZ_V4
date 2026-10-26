"""Where a published text's shape names an address (hard limit 15, ruling 102).

The views carry the question, the reply and the pages' text whole; beside
each such column the load sets `<column>_names_address`, true where the
value names a place by one of three shapes, and a product applies hard
limit 15 at its own surface by that flag. The board shows the text whole.
The three shapes are the Gazette lane's (registers/gazette/cut.py), written
here again as this lane's own (a lane may not import another):

  street      a house number and a street: "12 Sample Street", "2/14A Sample Road",
              "12-14 SAMPLE AVENUE"
  legal       the land's legal description: "Lot 2 DP 12345", "Section 5 Block II",
              "Record of Title NA12/34", "CT 12A/345", "Unit 3"
  numbered    a number led by the word that places it and followed by a name:
              "at 12 Sample", "property 12 Sample", ", of 12 Sample"

Not an address: a company's name ("12 Sample Street Limited", the Companies
Office's own name for it); a number a highway, an Act or a clause carries
("State Highway 2 Sample Road", "section 5 Sample Act"); a year ("in 2019
Sample Road works"); a time, a count of days or a date after "at".

    shape(text)   the first shape the text names ('street', 'legal', 'numbered'), or None
    names(text)   whether it names one
"""
import re

_NUMBER = r"\d{1,4}[A-Za-z]?(?:\s*[-/]\s*\d{1,4}[A-Za-z]?)?"
_KINDS = ("Street St Road Rd Avenue Ave Drive Dr Place Pl Crescent Cres Terrace Tce Lane Way Parade Highway Hwy "
          "Grove Close Court Ct Rise Quay Square Boulevard Esplanade Track Mews Heights Glade Row Loop Walk Promenade "
          "Strand Mall Circle Common Ridge Vale Downs Line Valley Hill View Green Gardens Park Point Reach Key").split()
_KIND = "(?:" + "|".join(sorted({w for k in _KINDS for w in (k, k.upper())}, key=len, reverse=True)) + ")"
# words whose number is not a house's: a route, a law's part, a list's item
_NOT_HOUSE = "".join(f"(?<!{re.escape(w)} )" for w in (
    "Highway", "highway", "Hwy", "SH", "No", "No.", "no.", "Act", "Regulations", "Rule", "Order", "Notice", "Section",
    "section", "Schedule", "schedule", "Part", "part", "Clause", "clause", "Reg", "Route", "route", "Question",
    "question", "Bill", "bill", "Level", "level", "Alert", "alert", "Phase", "phase", "Stage", "stage", "Tranche"))
_YEAR = r"(?!(?:18|19|20)\d\d\b)"
STREET = re.compile(rf"(?<![\w/.,-]){_NOT_HOUSE}{_YEAR}{_NUMBER},?\s+(?:[A-Z][\w'’.-]*\s+){{1,4}}{_KIND}\b")
LEGAL = re.compile(
    r"\bLots?\s+\d+[A-Za-z]?(?:\s*(?:,|and|&)\s*\d+[A-Za-z]?)*,?\s+(?:on\s+)?(?:DP|Deposited\s+Plan|LT|SO)\b"
    r"|\bDP\s*\d{3,}\b|\bDeposited\s+Plan\s+(?:No\.?\s*)?\d"
    r"|\bSections?\s+\d+[A-Za-z]?(?:\s*(?:,|and|&)\s*\d+[A-Za-z]?)*,?\s+(?:Block|Town|Suburban|Village|Rural|SO|DP)\b"
    r"|\b(?:Record\s+of\s+Title|Certificate\s+of\s+Title|Computer\s+(?:Freehold|Unit|Leasehold)\s+Register)\s+"
    r"(?:No\.?\s*)?\S*\d"
    r"|\bCT\s+[A-Z]{0,3}\d+[A-Z]?/\d+"
    r"|\b(?:Unit|Flat)\s+\d{1,4}[A-Za-z]?,?\s+(?=\d{1,4}[A-Za-z]?\s+[A-Z])")
NUMBERED = re.compile(
    r"(?:\b(?:at|known\s+as|premises|propert(?:y|ies)|dwelling|house|residence|home)\s+(?:No\.?\s*)?"
    r"|,\s*(?:formerly\s+|late\s+)?of\s+)"
    rf"{_YEAR}\d{{1,4}}[A-Za-z]?\s+"
    r"(?!(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b)(?!(?:am|pm|AM|PM)\b)[A-Z][a-z'’-]+\b")
# a company's name: up to four more words, then its legal ending
_COMPANY = re.compile(r"[\s,]*(?:[A-Z(][\w'’&().-]*\s+){0,4}(?:Limited|Ltd|LIMITED|LTD|Incorporated|Inc)\b")
SHAPES = (("street", STREET), ("legal", LEGAL), ("numbered", NUMBERED))


def shape(text):
    """The shape the text names first, or None."""
    if not isinstance(text, str) or not text:
        return None
    best = None
    for name, pat in SHAPES:
        for m in pat.finditer(text):
            if not _COMPANY.match(text, m.end()):
                if best is None or m.start() < best[0]:
                    best = (m.start(), name)
                break
    return best[1] if best else None


def names(text) -> bool:
    return shape(text) is not None
