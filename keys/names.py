"""The one reading of a person's or an organisation's name (contract:
docs/contracts/keys.md). Pure functions; the standard library only.

Rules, each paid for in the old estate (reference/old-estate/names-addresses-and-capture.md):

- **Macrons are kept.** A comparison key folds diacritics by DECOMPOSING
  the letter and dropping the mark (Rāwiri and Rawiri meet as `rawiri`); it
  never deletes the letter. The old graph's `[^a-z]` fold turned Rāwiri into
  `r wiri` and read every macronised given name as an initial.
- **Nicknames are never merged on.** A map of 371 filer-stated pairs found
  nothing beyond chance. Initials and spellings do not fold either.
- **An honorific is not part of a name;** a post-nominal is not either. The
  list is the old estate's one list.
- **"Surname, Given" is the Commission's inversion;** a bare two- or
  three-word person name is keyed order-free, because one filer wrote
  "MILLS PHILLIP" for everybody else's "Phillip Mills".
- **A trailing comma is filing punctuation, not a name.** 104 donors were
  once published twice over one.
- **Telling a person from an organisation:** an organisation word anywhere
  says organisation, except when a two- or three-word name ends in a weak
  word (Chambers, Orchard, Lodge, Guild, Board, Branch, Wine) and begins
  with a given name. The Companies Office director register is the
  authority for given names (old ruling 360): `given_names.txt`, every given
  name filed ten or more times.
- **A joint filed name is one donor**, flagged as joint; a shape nobody has
  judged is left unexamined (None), never guessed.
- **"X via Y" names X;** Y is the conduit, kept apart.
"""
import os
import re
import unicodedata
from dataclasses import dataclass

HONORIFICS = ("rt hon", "right honourable", "hon", "honourable", "dr", "sir", "dame",
              "mr", "mrs", "ms", "miss", "prof", "professor")
_HON = re.compile(r"^((" + "|".join(HONORIFICS) + r")[\s.]+)+", re.I)
_POST = re.compile(r"(,\s*(kc|qc|mp|jp|onzm|cnzm|dnzm|knzm|mnzm|qso|qsm)\b\.?)+\s*$|\s+mp\s*$", re.I)
_STATUS = re.compile(r"(?i)\s*\(?\b(deceased|dec'?d)\b\)?\s*$")
_VIA = re.compile(r"(?i)\s+via\s+(.+)$")
_ESTATE = re.compile(r"\bestate\s+of\b|,\s*estate\s+of\b", re.I)
_APOS = re.compile(r"['‘’ʼ`]")
_TRAIL_NOISE = re.compile(r"\s*(?:\((?:chair|contact|attn|att|per)[^)]*\)|!+|\.+)\s*$", re.I)
_PAREN_INC = re.compile(r"\(\s*(inc|incorporated)\.?\s*\)", re.I)

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
_AMP = r"(?:&|\band\b)"
_JOINT_PLAIN = re.compile(rf"^\s*[A-Z][A-Za-z'’-]+\s*{_AMP}\s*[A-Z][A-Za-z'’-]+(?:\s+[A-Z][A-Za-z'’-]+)*\s+[A-Z][A-Za-z'’-]+\s*$")
_JOINT_INVERTED = re.compile(rf"^\s*[A-Z][A-Za-z'’-]+\s*,\s*[A-Z][A-Za-z'’-]+(?:\s+[A-Z][A-Za-z'’-]+)*\s*{_AMP}\s*[A-Z][A-Za-z'’-]+\s*$")
_CORP_SUFFIXES = (" limited", " ltd", " incorporated", " inc")

_GIVEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "given_names.txt")
_GIVEN = None


def given_names() -> frozenset:
    """The given-name vocabulary from the director register, read once."""
    global _GIVEN
    if _GIVEN is None:
        with open(_GIVEN_PATH, encoding="utf-8") as f:
            _GIVEN = frozenset(l.strip() for l in f if l.strip() and not l.startswith("#"))
    return _GIVEN


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


def split_via(name: str):
    """'MA Capital Ltd via Ross George' → ('MA Capital Ltd', 'Ross George')."""
    m = _VIA.search(name or "")
    if not m:
        return squash(name), None
    return squash(name[: m.start()]), squash(m.group(1))


def clean_corporate(name: str) -> str:
    """Filing noise that is never part of a legal name: '(Inc)' spelled out,
    a trailing '(contact …)', bangs and dots."""
    s = _PAREN_INC.sub("INCORPORATED", squash(name))
    return _TRAIL_NOISE.sub("", s).strip(" ,;")


def organisation_key(name: str) -> str:
    """The organisation fold: lower, diacritics decomposed, possessive and a
    leading 'the' off, corporate suffixes off, 'nz ' → 'new zealand '.
    An apostrophe is not a spelling (Talley's is Talleys). ' party' is NOT
    folded: a region must never match a party."""
    o = fold_diacritics(clean_corporate(name)).lower().strip()
    if o.endswith("'s"):
        o = o[:-2].strip()
    o = _APOS.sub("", o)
    if o.startswith("the "):
        o = o[4:]
    for suf in _CORP_SUFFIXES:
        if o.endswith(suf):
            o = o[: -len(suf)]
    o = o.strip(" .,")
    if o.startswith("nz "):
        o = "new zealand " + o[3:]
    return squash(o)


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


def person_key(raw: str) -> str:
    """The comparison key for a person: diacritics decomposed, lower,
    apostrophes out, punctuation to spaces; a bare two- or three-word name
    is order-free. Initials, nicknames and spellings never fold."""
    n = person_name(raw)
    s = fold_diacritics(n.full).lower()
    s = _APOS.sub("", s)
    toks = re.sub(r"[^a-z0-9]+", " ", s).split()
    if 2 <= len(toks) <= 3 and all(len(w) > 1 and w.isalpha() for w in toks):
        toks = sorted(toks)
    return " ".join(toks)


def is_organisation(name: str) -> bool:
    """An organisation word anywhere says organisation, unless the name is a
    person with a weak word for a surname ('Richard Chambers')."""
    entity, _ = split_via(name)
    if _ESTATE.search(entity):
        return False
    if not ORG_WORDS.search(entity):
        return False
    return not _person_with_a_weak_surname(entity)


def _person_with_a_weak_surname(entity: str) -> bool:
    toks = [w.strip(".,;:'\"()") for w in (entity or "").lower().split()]
    toks = [w for w in toks if w]
    if not (2 <= len(toks) <= 3):
        return False
    if toks[-1] not in WEAK_SURNAMES:
        return False
    if ORG_WORDS.search(" ".join(toks[:-1])):
        return False
    return toks[0] in given_names()


def name_kind(name: str, party_keys=()) -> str:
    """'person' | 'organisation' | 'estate' | 'party'. A party's own organ
    (branch, electorate committee) is the party when `party_keys` holds the
    folded label; the order matters, because an organ's name carries an
    organisation word."""
    if _ESTATE.search(name or ""):
        return "estate"
    entity, _ = split_via(name or "")
    if party_keys and organisation_key(entity) in party_keys:
        return "party"
    return "organisation" if is_organisation(entity) else "person"


def is_joint_name(name: str):
    """True: two people filed as one line ('Laurence & Katrina Day'). False:
    one donor, an organisation with an ampersand in its name among them.
    None: a shape nobody has judged ('M & J Ruka'); never guessed."""
    s = squash(name)
    if not s:
        return None
    if not re.search(rf"[A-Za-z]\s*{_AMP}\s*[A-Z]", s):
        return False
    if ORG_WORDS.search(s):
        return False
    if _JOINT_PLAIN.match(s) or _JOINT_INVERTED.match(s):
        return True
    return None
