"""The one reading of an address (contract: docs/contracts/keys.md).

An address never confirms a link alone: one address holds 1,060 companies,
and address alone once grouped 25 ministers at Parliament. What this gives
is a key for EQUALITY, nothing fuzzier, and the cleaning every page-read row
passes through once.

- `clean_address` strips the date a reader sometimes puts in front of the
  address, and a flag after it, and refuses a page dump (over 200
  characters); a cell that was never read becomes no address.
- `address_key` folds for equality: diacritics decomposed, lower, the common
  abbreviations spelled one way, "New Zealand" dropped, a PO Box kept as
  `pobox<number>`. Street numbers are KEPT whole: an older key dropped
  numbers under three digits and 160 folds were withdrawn for it. A key is
  letters and digits only.
- `is_po_box`: a box is not a street, so a street rule never applies to it
  (the old street key returned nothing for boxes).
"""
import re

from keys.names import fold_diacritics, squash

MAX_ADDRESS = 200
_DATE = re.compile(r"(\d{1,3})[/.-](\d{1,2})[/.-](\d{2,4})")
_LEAD_DATE = re.compile(r"^\s*\d{1,3}[/.-]\d{1,2}[/.-]\d{2,4}\s*[,;]?\s*")
_FLAG = re.compile(r"^\s*(yes|no|y|n)\b[,;]?\s*", re.I)
_PO_BOX = re.compile(r"\b(p\.?\s*o\.?\s*box|po\s*box|private\s*bag|pobox)\s*(\d+)", re.I)
_ABBREV = (
    (r"\b(street|st)\b", "st"), (r"\b(road|rd)\b", "rd"), (r"\b(avenue|ave)\b", "ave"),
    (r"\b(drive|dr)\b", "dr"), (r"\b(place|pl)\b", "pl"), (r"\b(crescent|cres)\b", "cres"),
    (r"\b(terrace|tce)\b", "tce"), (r"\b(lane|ln)\b", "ln"), (r"\b(highway|hwy)\b", "hwy"),
    (r"\b(mount|mt)\b", "mt"), (r"\b(saint|st\.)\s", "st "),
)


def clean_address(raw):
    """(address or None, the date that stood in front of it or None)."""
    if raw is None:
        return None, None
    s = squash(str(raw))
    if not s:
        return None, None
    if len(s) > MAX_ADDRESS:
        return None, "page dump"
    found = []
    m = _LEAD_DATE.match(s)
    body = s
    if m:
        found.append(m.group(0).strip(" ,;."))
        body = _FLAG.sub("", s[m.end():])
    body = _DATE.sub(lambda mm: (found.append(mm.group(0)) or " ")
                     if (1 <= int(mm.group(1)) <= 31 and 1 <= int(mm.group(2)) <= 12) or len(mm.group(3)) == 4
                     else mm.group(0), body)
    if not found:
        return s, None
    rest = squash(body).replace(" ,", ",").strip(" ,;.")
    if not any(c.isalpha() for c in rest):
        rest = ""
    return (rest or None), " · ".join(found)


def is_po_box(raw: str) -> bool:
    return bool(_PO_BOX.search(raw or ""))


def address_key(raw: str) -> str:
    """Letters and digits only, for equality. '' for nothing."""
    s = fold_diacritics(raw or "").lower()
    s = _PO_BOX.sub(lambda m: f" pobox{m.group(2)} ", s)
    for pat, rep in _ABBREV:
        s = re.sub(pat, rep, s)
    s = re.sub(r"\b(new zealand|nz|aotearoa)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", "", s)


# ── an address in parts, read the same way on every side (Arthur, 4 November 2026: "match them") ──────────────────
# A judgment prints "Flat 2, 14A Smith Street, Ponsonby, Auckland"; LINZ gives "2/14A Smith Street, Ponsonby, Auckland";
# a registered office comes in four lines and a postcode. `street_parts` reads each into the same parts, so two sides
# meet (`meet`) at a named level within one `street_key`. Equality only, as `address_key`.

_STREET_TYPES = {
    "street": "st", "st": "st", "road": "rd", "rd": "rd", "avenue": "ave", "ave": "ave", "drive": "dr", "dr": "dr",
    "place": "pl", "pl": "pl", "crescent": "cres", "cres": "cres", "terrace": "tce", "tce": "tce", "lane": "ln",
    "ln": "ln", "highway": "hwy", "hwy": "hwy", "grove": "gr", "gr": "gr", "close": "cl", "cl": "cl", "parade": "pde",
    "pde": "pde", "boulevard": "blvd", "blvd": "blvd", "way": "way", "quay": "qy", "square": "sq", "sq": "sq",
    "esplanade": "esp", "esp": "esp", "rise": "rise", "heights": "hts", "hts": "hts", "mews": "mews", "glade": "glade",
    "track": "trk", "court": "ct", "ct": "ct", "valley": "vly", "view": "view", "loop": "loop", "row": "row",
    "walk": "walk", "green": "grn", "point": "pt", "common": "common", "rapids": "rapids", "street east": "st",
}
_UNIT_WORDS = r"(?:flat|unit|apartment|apt|suite|shop|villa|room)"
_LEVEL = r"(?:level|lvl|floor)\s+[a-z0-9]{1,4}"
_PARTS = re.compile(
    rf"^(?:{_LEVEL}\s+)?(?:{_UNIT_WORDS}\s+(?P<unit_w>[a-z0-9]{{1,5}})\s+)?(?:{_LEVEL}\s+)?"   # Level 4, Flat 2
    r"(?:(?P<unit>[a-z0-9]{1,5})\s*/\s*)?"                              # 2/14A
    r"(?P<number>\d{1,5}[a-z]?)(?:\s*-\s*\d{1,5}[a-z]?)?\s+"            # 14A (a range 14-16 reads its first)
    r"(?P<street>[a-z' ]{2,48}?)\s+(?P<type>" + "|".join(sorted(_STREET_TYPES, key=len, reverse=True)) + r")\b"
    r"(?P<rest>.*)$")


def _folded(raw: str) -> str:
    s = fold_diacritics(raw or "").lower().replace("’", "'")
    s = re.sub(r"[^a-z0-9/' -]+", " , ", s.replace(",", " , "))
    return re.sub(r"\s+", " ", s).strip(" ,")


def street_parts(raw: str):
    """{unit, number, street, type, places} of the first street address the text names, or None (a PO Box, a road
    with no number, a place name alone). `places` are the folded words after the street, one per comma part, a
    postcode and the country dropped: the suburb and the town."""
    if not raw or is_po_box(raw):
        return None
    segs = [p.strip(" -") for p in _folded(raw).split(",") if p.strip(" -")]
    for i in range(len(segs)):
        j = i
        while j < len(segs) - 1 and re.fullmatch(rf"(?:{_UNIT_WORDS}\s+[a-z0-9]{{1,5}}|{_LEVEL})", segs[j]):
            j += 1                                                       # "Level 3, Flat 2, 14A …" read as one line
        line = " ".join(segs[i:j + 1])
        m = _PARTS.match(line)
        if not m:
            continue
        used = j + 1
        places = []
        for p in [m.group("rest")] + segs[used:]:
            p = re.sub(r"\b\d{4}\b", " ", p)
            p = re.sub(r"\b(new zealand|nz|aotearoa)\b", " ", p)
            p = re.sub(r"[^a-z]", "", p)
            if p:
                places.append(p)
        unit = m.group("unit") or m.group("unit_w")
        return {"unit": unit or "", "number": m.group("number"), "street": re.sub(r"[^a-z]", "", m.group("street")),
                "type": _STREET_TYPES[m.group("type")], "places": tuple(places)}
    return None


#: the levels two addresses may meet at, strongest first
MATCH_LEVELS = ("unit, number, street and place", "number, street and place", "number and street")


def street_key(parts: dict) -> str:
    """The number, street and type: the block two addresses are compared within (`meet` says at what level)."""
    return f"{parts['number']}|{parts['street']}|{parts['type']}" if parts else ""


def meet(a: dict, b: dict):
    """The strongest level two addresses (`street_parts`) meet at, or None: never when the streets differ, when both
    name a place and none is shared, or when both name a unit and the units differ (two dwellings at one number)."""
    if not a or not b or (a["number"], a["street"], a["type"]) != (b["number"], b["street"], b["type"]):
        return None
    pa, pb = set(a["places"]), set(b["places"])
    if pa and pb and not pa & pb:
        return None
    if a["unit"] and b["unit"] and a["unit"] != b["unit"]:
        return None
    if pa & pb:
        return MATCH_LEVELS[0] if a["unit"] and a["unit"] == b["unit"] else MATCH_LEVELS[1]
    return MATCH_LEVELS[2]
