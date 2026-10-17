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
