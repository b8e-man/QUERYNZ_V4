"""A copy of the readings of keys/names.py and keys/addresses.py the board
needs for its field search and near matches (rulings 82 and 83): products
may import only support/ (imports run one way), so each piece below is the
keys/ source character for character, and tests/test_fold.py holds every
one equal to its original. Change keys/, then copy here; never edit here."""
import re
import unicodedata
from dataclasses import dataclass

# ── from keys/names.py ──

HONORIFICS = ("rt hon", "right honourable", "hon", "honourable", "dr", "sir", "dame",
              "mr", "mrs", "ms", "miss", "prof", "professor")


_HON = re.compile(r"^((" + "|".join(HONORIFICS) + r")[\s.]+)+", re.I)


_POST = re.compile(r"(,\s*(kc|qc|mp|jp|onzm|cnzm|dnzm|knzm|mnzm|qso|qsm)\b\.?)+\s*$|\s+mp\s*$", re.I)


_STATUS = re.compile(r"(?i)\s*\(?\b(deceased|dec'?d)\b\)?\s*$")


_APOS = re.compile(r"['‘’ʼ`]")


ORG_WORDS = re.compile(
    r"\b(limited|ltd|incorporated|inc|trust|trustees?|society|foundation|partnership|"
    r"co-?operative|holdings|group|estate of|"
    r"union|association|federation|council|club|chambers|committee|branch|institute|"
    r"board|electorate|centre|center|rooms|guild|league|lodge|collective|network|"
    r"enterprises?|investments?|properties|farms?|consulting|services|industries|"
    r"partners|nominees|securities|capital|ventures|developments?|contractors|"
    r"engineering|construction|motors|transport|freight|marine|fisheries|forestry|"
    r"orchards?|vineyards?|wines?|hotels?|pty|plc|llc|gmbh|corp|corporation|company|co|"
    r"party|nz|new zealand|lp)\b", re.I)


WEAK_SURNAMES = frozenset({"chambers", "orchard", "lodge", "guild", "board", "branch", "wine"})


def fold_diacritics(s: str) -> str:
    """Decompose and drop the combining marks: 'Te Pāti Māori' → 'Te Pati Maori',
    'Chlöe' → 'Chloe'. A letter with no decomposition (ø, æ) survives. The
    letter is never deleted."""
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))


def squash(s: str) -> str:
    return " ".join((s or "").split())


def strip_honorifics(name: str) -> str:
    """'Rt Hon Dr Winston Peters' → 'Winston Peters'; 'Hon Judith Collins, KC' → 'Judith Collins'."""
    s = _HON.sub("", squash(name))
    return _POST.sub("", s).strip()


def strip_trailing_comma(name: str) -> str:
    return re.sub(r"\s*,\s*$", "", squash(name))


@dataclass(frozen=True)
class PersonName:
    as_filed: str
    given: str            # first given name
    middle: str           # the rest of the given names, space-joined; '' when none
    family: str
    inverted: bool        # filed 'Family, Given'

    @property
    def full(self) -> str:
        return " ".join(p for p in (self.given, self.middle, self.family) if p)

    @property
    def display(self) -> str:
        """Given-first, honorifics and the trailing comma gone, spelling as filed."""
        return self.full


def person_name(raw: str) -> PersonName:
    """Read a filed person name: honorifics and post-nominals off, a
    deceased marker off, 'Family, Given' turned round. Spelling, case and
    macrons are kept as filed. A one-word name is a family name."""
    s = strip_trailing_comma(_STATUS.sub("", strip_honorifics(raw)))
    inverted = False
    if "," in s:
        family, rest = s.split(",", 1)
        s = squash(rest) + " " + squash(family)
        inverted = True
    toks = s.split()
    if not toks:
        return PersonName(squash(raw), "", "", "", inverted)
    if len(toks) == 1:
        return PersonName(squash(raw), "", "", toks[0], inverted)
    return PersonName(squash(raw), toks[0], " ".join(toks[1:-1]), toks[-1], inverted)


# ── from keys/addresses.py ──

_PO_BOX = re.compile(r"\b(p\.?\s*o\.?\s*box|po\s*box|private\s*bag|pobox)\s*(\d+)", re.I)


_ABBREV = (
    (r"\b(street|st)\b", "st"), (r"\b(road|rd)\b", "rd"), (r"\b(avenue|ave)\b", "ave"),
    (r"\b(drive|dr)\b", "dr"), (r"\b(place|pl)\b", "pl"), (r"\b(crescent|cres)\b", "cres"),
    (r"\b(terrace|tce)\b", "tce"), (r"\b(lane|ln)\b", "ln"), (r"\b(highway|hwy)\b", "hwy"),
    (r"\b(mount|mt)\b", "mt"), (r"\b(saint|st\.)\s", "st "),
)


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
