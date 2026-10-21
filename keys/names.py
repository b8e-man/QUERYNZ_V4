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
  judged is left unexamined (None), never guessed. `joint_parts` reads the
  people it names (ruling 73: the row stays one, the links join it to each):
  "A & B Surname" and "Surname, A & B" share the surname, "A Surname and B
  Other" and "Surname, A & Other, B" name two whole names. A part whose
  given name is an initial is not read, and one of the parts must carry a
  given name the director register knows ("Bread and Roses Auction" is no
  couple).
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
    if _joint_people(s):
        return True
    if _JOINT_TITLES.match(s):
        return True
    return None


def joint_parts(name: str) -> tuple:
    """The people a joint filed name names, each a one-line given-first name
    ('Craig & Shayne Greenlees' → ('Craig Greenlees', 'Shayne Greenlees');
    'Douglas, Jeffrey Graeme & Christine Elizabeth' → ('Jeffrey Graeme
    Douglas', 'Christine Elizabeth Douglas'); 'Stewart Menzies and Megan Jean
    Harrison' → both whole). Empty when the name is not joint, or is joint
    but names nobody by a given name ('Mr & Mrs McCabe')."""
    s = squash(name)
    if not s or is_joint_name(s) is not True:
        return ()
    return tuple(_joint_people(s) or ())


# the couple form with titles and no given name: 'Mr & Mrs McCabe', 'Dr & Mrs GMO Becroft' (joint, naming nobody by a given name)
_JOINT_TITLES = re.compile(rf"(?i)^\s*(?:{'|'.join(HONORIFICS)})\.?\s*{_AMP}\s*(?:{'|'.join(HONORIFICS)})\.?(?:\s+[A-Z][A-Za-z'’-]*)+\s*$")
_PART_TITLES = re.compile(r"^((" + "|".join(HONORIFICS + ("lady", "lord")) + r")(?:[\s.]+|$))+", re.I)
_TOKEN = re.compile(r"^[A-Z][A-Za-z'’-]*\.?$")
#: the words that begin a surname of two words ('Janet De Lu', 'Mere Te Rangi', 'Anna van der Berg')
SURNAME_PARTICLES = frozenset({"de", "da", "di", "del", "della", "der", "den", "du", "la", "le", "van", "von", "te", "ten", "ter", "st"})


def _is_initial(tok: str) -> bool:
    return len(tok.rstrip(".")) == 1


def _tokens(part: str):
    """A part's words, its titles off; None when any word is not a name word."""
    toks = _PART_TITLES.sub("", part.strip()).split()
    for t in toks:
        if not (_TOKEN.match(t) or t.lower() in SURNAME_PARTICLES):
            return None
    return toks


def _surname_split(toks: list) -> tuple:
    """(given words, surname words) of a given-first name: the last word, and
    the particles before it ('Janet De Lu' → (['Janet'], ['De', 'Lu']))."""
    i = len(toks) - 1
    while i > 1 and toks[i - 1].lower() in SURNAME_PARTICLES:
        i -= 1
    return toks[:i], toks[i:]


def _joint_people(s: str):
    """The names of a joint filed line, or None when it is not one of the
    judged shapes. Exactly one '&' or 'and'; every part a name of words; no
    part's given name an initial; one given name known to the register."""
    halves = re.split(rf"\s*{_AMP}\s*", s)
    if len(halves) != 2 or not all(h.strip() for h in halves):
        return None
    left, right = halves
    lc, rc = left.count(","), right.count(",")
    if lc > 1 or rc > 1:
        return None
    if lc and rc:                        # 'Thompson, Peter & Grooton, Eddie'
        lf, lg = (_tokens(x) for x in left.split(","))
        rf, rg = (_tokens(x) for x in right.split(","))
        if not (lf and lg and rf and rg):
            return None
        people = [(lg, lf), (rg, rf)]
    elif lc:                             # 'Mills, Phillip & Jackie': one surname, filed first
        fam, lg = (_tokens(x) for x in left.split(","))
        rg = _tokens(right)
        if not (fam and lg and rg) or len(rg) > 3:
            return None
        people = [(lg, fam), (rg, fam)]
    elif rc:
        return None
    else:
        lt, rt = _tokens(left), _tokens(right)
        if not lt or not rt or len(rt) < 2 or len(lt) > 4 or len(rt) > 4:
            return None
        rg, fam = _surname_split(rt)
        if len(lt) == 1 or all(_is_initial(t) for t in lt[1:]):   # 'Craig & Shayne Greenlees', 'Gregory J & Paula R Dickson'
            people = [(lt, fam), (rg, fam)]
        else:                                                      # 'Stewart Menzies and Megan Jean Harrison'
            lg, lfam = _surname_split(lt)
            people = [(lg, lfam), (rg, fam)]
    if any(not g or not f or _is_initial(g[0]) for g, f in people):
        return None
    known = given_names()
    if not any(fold_diacritics(g[0]).lower() in known for g, _ in people):
        return None
    return [" ".join(g + f) for g, f in people]
