"""Typing every notice: the family the Gazette itself gives it, and the
format the lane recognises in its text.

The notice number embeds the Gazette's own section code and its place in one
sequence a year (`2025-go7375`: 2025, section `go`, the 7,375th notice that
year), so the family is exact and is never guessed from the title. The
format is the document profile a reader is built for, recognised from the
notice's own words (celebrants.recognise); a notice no reader recognises
has the format `not read` and is held, typed, for a later reader.

A notice the old estate captured twice is two lines of the export with one
number and slightly different text (1,328 of them, none identical). The
copy the old classifier read is kept and the other is a catch-log line.

    number(notice)          (year, section code, number) or None
    family(code)            the family's label
    pick(lines)             (kept line, [(line, why)]) for one notice number
"""
import re

_NUMBER = re.compile(r"^(?P<year>\d{4})-(?P<code>[a-z]+)(?P<n>\d+)$")

#: The Gazette's section codes, named after what the old estate measured each
#: to hold (`data-layer/gazette_register/parse.py`, CODE_TYPE); `md` corrected by
#: reading every notice in it (gazette 3): notices to creditors, not administrations.
FAMILY = {
    "al": "insolvency: liquidator appointed", "ar": "insolvency: receivership",
    "aw": "insolvency: winding-up application", "ds": "insolvency: liquidation and removal",
    "md": "insolvency: notice to creditors", "aa": "insolvency: administration",
    "ba": "bankruptcy", "cb": "overseas company", "pn": "partnership", "ot": "companies: other",
    "is": "incorporated society", "ct": "charitable trust", "fs": "friendly society",
    "gn": "general", "go": "government", "au": "authority", "sl": "secondary legislation",
    "gs": "standards", "ln": "land", "lt": "land transfer", "vr": "vice-regal",
    "ps": "parliamentary", "cu": "trade", "rs": "corrigendum", "dl": "fisheries bylaw",
    "pb": "private bill", "vw": "vice-regal warrant",
}


def number(notice: str):
    m = _NUMBER.match(notice or "")
    return (int(m.group("year")), m.group("code"), int(m.group("n"))) if m else None


def family(code: str) -> str:
    return FAMILY.get(code, "unknown section")


def pick(lines: list) -> tuple:
    """One notice's export lines → (the line read, [(line set aside, why)])."""
    if len(lines) == 1:
        return lines[0], []
    kept = next((l for l in lines if l.get("old_article") == l.get("article")), None)
    kept = kept or min(lines, key=lambda l: l["article"])
    why = ("captured twice; the copy the old classifier read is kept" if kept.get("old_article") == kept.get("article")
           else "captured twice; the first article kept")
    return kept, [(l, why) for l in lines if l is not kept]
