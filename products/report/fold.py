"""A copy of the readings of keys/names.py the report's name joins need (keys.names.person_name, the one shared reading,
Arthur 2 November 2026: "yea fix it"): products may import only support/ (imports run one way), so each piece below is the
keys/ source character for character, and tests/test_fold.py holds every one equal to its original, as the board's copy
(products/board/fold.py) is held. Change keys/, then copy here; never edit here."""
import os
import re
import unicodedata
from dataclasses import dataclass


HONORIFICS = ("rt hon", "right honourable", "hon", "honourable", "dr", "sir", "dame",
              "mr", "mrs", "ms", "miss", "prof", "professor")


_HON = re.compile(r"^((" + "|".join(HONORIFICS) + r")[\s.]+)+", re.I)


_POST = re.compile(r"(,\s*(kc|qc|mp|jp|onzm|cnzm|dnzm|knzm|mnzm|qso|qsm)\b\.?)+\s*$|\s+mp\s*$", re.I)


_STATUS = re.compile(r"(?i)\s*\(?\b(deceased|dec'?d)\b\)?\s*$")


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
