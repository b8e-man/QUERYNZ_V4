"""The re-read taxonomy — one home for the extraction artifacts we have named,
and for what the SOURCE DOCUMENT has to show before one may be acted on.

Arthur, 2026-09-21, on C241's 2,639 abstains:

    "for these kind of errors we need a pipeline to return to the document,
     identify the glued name and find the actual name for extraction. This
     pipeline should be used for all obvious extraction debris and artifacts
     that we have taxonomised."

WHY A RE-READ AND NOT A BETTER RULE. C241 abstained because the STRING carries
no evidence: `Laing Properties)Dokyun` could be either side, and picking one is
a coin toss. The document is not ambiguous at all —

    1st place: Dokyun Kim (Laing Properties)Dokyun delivered an outstanding...

— the name is `Dokyun Kim`, which is NEITHER side of the seam. No rule reading
the string alone could have produced it. Three of the four classes below
recover names the string does not contain.

WHAT THE 1,217 ABSTAINS ACTUALLY ARE, measured 2026-09-21 by re-reading each
one's own document (the headline finding: most of them were never glued names):

     62.6%  neither side is a word     — footnote markers and OCR garble
     29.4%  exactly one side is a word — footnotes off a real name, emails
      5.4%  both sides are words       — the caption glue the card described

The classes, in the order `classify` tries them:

  email-address      `Suze.RedmayneMP@parliament.govt.nz` minted as an
                     organisation. The owner is named in the document's own
                     byline; the address never is a name.
  footnote-marker    `corruption.16`, `Community Mental Health Survey.353` —
                     a superscript note number flattened into the text layer.
                     The document proves the convention by using it repeatedly.
  parenthetical-glue `Infrastructure)Emma Healy` — the surface begins INSIDE a
                     parenthetical. The document has the opening bracket, and
                     the name either precedes it or follows the close.
  ocr-garble         `loag)Jfo`, `ASfJf)6iATiON` — no token a printer could
                     have set, and the document never uses the form again.

EVERY READING IS ONE OF THREE. `recover` names the entity the document
supports; `discard` says the surface was never a name (the lane quarantines,
reversibly, never deletes); `abstain` leaves the row exactly as it was. Abstain
is not failure — it is the design, and a class that cannot read its document
must reach it rather than guess.

Pure: no database, no network, no I/O. The document arrives as a string, which
is what makes every case below testable against the corpus text verbatim.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# the classes, in the order classify() tries them — first match wins
DEFECTS = ("email-address", "footnote-marker", "ocr-garble", "parenthetical-glue")

RECOVER, DISCARD, ABSTAIN = "recover", "discard", "abstain"


@dataclass(frozen=True)
class Reading:
    """What the document said. `name` is set only for RECOVER."""
    verdict: str
    name: str = ""
    defect: str = ""
    because: str = ""

    def __bool__(self) -> bool:            # truthy only when it decided
        return self.verdict != ABSTAIN


def _abstain(defect: str, because: str) -> Reading:
    return Reading(ABSTAIN, "", defect, because)


# ── name shape ───────────────────────────────────────────────────────────────

_VOWEL = re.compile(r"[aeiouyāēīōū]", re.I)
_LETTER = re.compile(r"[A-Za-zĀĒĪŌŪāēīōū]")
_TOKEN_OK = re.compile(r"[A-Za-zĀĒĪŌŪāēīōū'’.\-]+")


def wordlike(tok: str) -> bool:
    """A token a printer could have set: letters and the marks names carry, a
    vowel somewhere in it, no case flip inside it, more than one character.

    The case-flip clause is what separates `Jficeab` and `ASfJf` from `McKay`
    and `O'Brien` — a lowercase letter followed by an uppercase one INSIDE a
    token is a scanning artifact, not orthography, once the `Mc`/`Mac`/`O'`
    prefixes are allowed for."""
    t = tok.strip(" .,;:'’-")
    if len(t) < 2 or not _TOKEN_OK.fullmatch(t) or not _VOWEL.search(t):
        return False
    if re.match(r"(?:Mc|Mac|O['’])[A-ZĀĒĪŌŪ]", t):
        return True
    return not re.search(r"[a-zāēīōū][A-ZĀĒĪŌŪ]", t)


def namelike(side: str) -> bool:
    """Every token a word, and at least one of them capitalised."""
    toks = side.split()
    return bool(toks) and all(wordlike(t) for t in toks) and any(t[:1].isupper() for t in toks)


# ── reading the document ─────────────────────────────────────────────────────

def _locate(surface: str, doc: str, offset: int = -1) -> int:
    """Where the surface sits in its document.

    The mention's own `first_char` is preferred and VERIFIED before use: the
    offsets were written by several extractor versions across three eras, and
    one that no longer lands on its surface must not be allowed to point the
    reader at unrelated prose 200 characters away."""
    if offset is not None and offset >= 0 and doc[offset:offset + len(surface)] == surface:
        return offset
    return doc.find(surface)


def _elsewhere(side: str, doc: str, at: int, span: int) -> bool:
    """Does the side stand alone in the document, away from the seam itself?"""
    if not side:
        return False
    blank = doc if at < 0 else doc[:at] + " " * span + doc[at + span:]
    return re.search(r"(?<![\w)])" + re.escape(side) + r"(?![\w.)])", blank) is not None


_CAP = r"[A-ZĀĒĪŌŪ][\w'’\-]*"


def _run_before(doc: str, i: int, cap: int = 6) -> str:
    """The capitalised run that ends just before index i."""
    head = doc[max(0, i - 120):i].rstrip()
    toks: list[str] = []
    for tok in reversed(head.split()):
        if not re.fullmatch(_CAP, tok) or not wordlike(tok):
            break
        toks.insert(0, tok)
        if len(toks) >= cap:
            break
    return " ".join(toks)


def _run_at(doc: str, i: int, cap: int = 6) -> str:
    """The capitalised run that starts at index i.

    A closing comma or full stop ENDS the run but still belongs to the word it
    sits on: "(Territorial Commander)The Salvation Army, New Zealand Fiji &
    Tonga Territory" is The Salvation Army. Refusing the token outright cut it
    to "The Salvation", and reading past the comma would have run two names
    together — the very defect this lane exists to undo."""
    toks: list[str] = []
    for tok in doc[i:i + 120].split():
        bare = tok.rstrip(",.;:")
        if not re.fullmatch(_CAP, bare) or not wordlike(bare):
            break
        toks.append(bare)
        if len(toks) >= cap or len(bare) < len(tok):
            break
    return " ".join(toks)


# ── the classes ──────────────────────────────────────────────────────────────

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# what an address puts after a name and a person does not carry in theirs
_ADDRESS_SUFFIX = {"mp", "office", "electorate", "admin", "info", "contact",
                   "enquiries", "media", "press", "team"}
_CAMEL = re.compile(r"[A-ZĀĒĪŌŪ][a-zāēīōū]+|[A-ZĀĒĪŌŪ]+(?![a-zāēīōū])|[a-zāēīōū]+")

# `corruption.16` — a word, a full stop, a note number, and nothing after it.
_FOOTNOTE = re.compile(r"^(?P<left>.+?)\)?\.(?P<num>\d{1,4})$")
# A reference abbreviation is not a name, however capitalised it looks. Found
# by the lane recovering `No` from `No.14` — which the document shows is a
# rugby jersey ("the No.14 was there to pounce"), not an entity at all.
_REFERENCE_WORD = {"no", "nos", "p", "pp", "fig", "figs", "vol", "ch", "chap",
                   "s", "ss", "cl", "para", "paras", "art", "sec", "r", "reg", "n"}
# the same shape anywhere in the document: how a document proves it uses notes
_CONVENTION = re.compile(r"[A-Za-zāēīōū)]\.\d{1,4}(?![\d\w])")
MIN_CONVENTION = 3

# the surface begins inside a parenthetical: a close bracket with no open one
_GLUE = re.compile(r"^(?P<left>[^()]*[^\s()])\)(?P<right>[^()]+)$")
GLUE_REACH = 300           # how far back the opening bracket may be


def _read_email(surface: str, doc: str, at: int) -> Reading:
    m = _EMAIL.search(surface)
    toks: list[str] = []
    for part in re.split(r"[._\-+]+", m.group(0).split("@")[0]):
        toks += _CAMEL.findall(part)
    while toks and toks[-1].lower() in _ADDRESS_SUFFIX:
        toks.pop()
    cand = " ".join(t[:1].upper() + t[1:] for t in toks)
    if len(toks) >= 2 and _elsewhere(cand, doc, at, len(surface)):
        return Reading(RECOVER, cand, "email-address",
                       "the address's owner, named in the document in their own right")
    return Reading(DISCARD, "", "email-address",
                   "an address is not a name, and the document does not name its owner")


def _read_footnote(surface: str, doc: str, at: int) -> Reading:
    m = _FOOTNOTE.match(surface)
    left = m.group("left").strip(" )")
    # `car.2026`, `September.2026` — four digits in the range a date falls in
    # is a date, and a note numbered 2026 is not a note this corpus carries.
    if 1800 <= int(m.group("num")) <= 2099 and len(m.group("num")) == 4:
        return _abstain("footnote-marker", "the digits are a year, not a note number")
    if len(_CONVENTION.findall(doc)) < MIN_CONVENTION:
        return _abstain("footnote-marker",
                        "the document does not use note markers, so the digits may be part of the name")
    # A version, a price or a decimal is not a note. `Nano Banana 2.0` is a
    # product, `chosen$1.99` is money — both were QUARANTINED by the first
    # live tranche, which is exactly the harm the reversibility rule exists to
    # let us undo, and exactly the harm not to repeat. The tells: a left side
    # ending in a digit, a currency mark anywhere in the surface, and a note
    # numbered 0, which no document sets.
    if re.search(r"\d$", left) or re.search(r"[$€£¥]", surface) or m.group("num").lstrip("0") == "":
        return _abstain("footnote-marker",
                        "a version, a price or a decimal — the digits are part of what is named")
    words = left.split()
    # A reference abbreviation at EITHER end and the digits are not a note at
    # all: `QIC Trust No.1` and `Waipa Gang No.2` are names whose number is
    # part of them, and `p.115` is a page. Both ends are asked because reading
    # the first token only recovered "QIC Trust No", which names nothing —
    # and because ABSTAIN is the answer here, not discard: quarantining a real
    # trust over a suffix the rule misread would be the worse error by far.
    if any(w.lower().rstrip(".") in _REFERENCE_WORD for w in (words[:1] + words[-1:])):
        return _abstain("footnote-marker",
                        "a reference abbreviation, so the digits belong to it and not to a note")
    if not (namelike(left) and left[:1].isupper()):
        return Reading(DISCARD, "", "footnote-marker",
                       "prose carrying a note number — there is no name here to keep")
    # A single-token recovery needs the document to name it in its own right:
    # two tokens are already a name shape, one is a word that might be
    # anything. This is C241's "a single token must fold, never rename" asked
    # of the document instead of of the graph.
    if len(words) >= 2 or _elsewhere(left, doc, at, len(surface)):
        return Reading(RECOVER, left, "footnote-marker",
                       "the name the note number was set against")
    return _abstain("footnote-marker",
                    "one word with a note number, and the document never names it again")


def _read_glue(surface: str, doc: str, at: int) -> Reading:
    m = _GLUE.match(surface)
    left, right = m.group("left").strip(), m.group("right").strip()
    if at < 0:
        return _abstain("parenthetical-glue", "the surface is not in the document we hold")
    close = at + len(m.group("left"))
    opened = doc.rfind("(", max(0, close - GLUE_REACH), close)
    if opened < 0:
        return _abstain("parenthetical-glue",
                        "no bracket opens before the seam — the close may belong to the name")
    before = _run_before(doc, opened)
    first = right.split()[0] if right.split() else ""
    # The parenthetical is an aside on the name that PRECEDES it. Where the
    # text picks that name up again after the close — "Dokyun Kim (Laing
    # Properties)Dokyun delivered..." — the entity is the full name, which is
    # on NEITHER side of the seam and which no string rule could have reached.
    if first and before and first in before.split() and len(before.split()) >= 2:
        return Reading(RECOVER, before, "parenthetical-glue",
                       "the name the aside belongs to, picked up again after the close bracket")
    after_at = at + len(m.group("left")) + 1
    after = _run_at(doc, after_at)
    if len(after.split()) >= 2 and namelike(after) and _corroborated(after, doc, at, len(surface), after_at):
        return Reading(RECOVER, after, "parenthetical-glue",
                       "the name that follows the close bracket, read to its full extent")
    if len(before.split()) >= 2 and namelike(before) and not right:
        return Reading(RECOVER, before, "parenthetical-glue",
                       "the name the aside belongs to")
    return _abstain("parenthetical-glue",
                    "the document shows a bracket but no name long enough to stand on either side")


def _corroborated(run: str, doc: str, at: int, span: int, run_at: int) -> bool:
    """Does the document treat this run as a name in its own right?

    Two ways it can, both taken verbatim from the corpus. It is NAMED AGAIN
    somewhere else — "Captain Rio has sired over 300 winners" earlier in the
    same piece. Or it carries ITS OWN parenthetical, which is the roster shape
    the glue comes from in the first place:

        Fergus Eadie (Mairangi Bay)Joe Collins (Fitzroy)Louis Clark (...)

    Without one of the two the lane abstains, and that is what stops it
    renaming `Auckland)PO Box` to "PO Box" (a postal address, never named
    again) and `Lri)KSDALE MARFS ■J` to "KSDALE MARFS" (scanning debris with
    nothing after it but more debris).
    """
    if _elsewhere(run, doc, at, span):
        return True
    tail = doc[run_at + len(run):run_at + len(run) + 3].lstrip()
    return tail.startswith("(")


def _read_garble(surface: str, doc: str, at: int) -> Reading:
    if doc.count(surface) > 1:
        return _abstain("ocr-garble",
                        "the document sets the same form more than once, which a scanning slip does not do")
    return Reading(DISCARD, "", "ocr-garble",
                   "no token in it is a word, and the document never sets the form again")


_READERS = {"email-address": _read_email, "footnote-marker": _read_footnote,
            "parenthetical-glue": _read_glue, "ocr-garble": _read_garble}


def classify(surface: str) -> str | None:
    """Which taxonomised class this surface belongs to, from the string alone.

    This decides only WHICH DOCUMENT QUESTION to ask. Nothing is acted on here:
    the reading comes from `read`, which needs the document."""
    if not surface:
        return None
    if _EMAIL.search(surface):
        return "email-address"
    if _FOOTNOTE.match(surface):
        return "footnote-marker"
    # garble is tried BEFORE glue, and the order is load-bearing: `f)Q` and
    # `ASfJf)6iATiON` both match the glue shape, and asking the glue question
    # of them sends the reader hunting a bracket in a document that has none,
    # which abstains — when "no token in it is a word" was already the answer.
    toks = [t for t in re.split(r"[^\w'’ĀĒĪŌŪāēīōū]+", surface) if t]
    if toks and not any(wordlike(t) for t in toks):
        return "ocr-garble"
    if _GLUE.match(surface):
        return "parenthetical-glue"
    return None


def read(surface: str, doc: str, offset: int = -1) -> Reading:
    """Re-read one surface against the document it was extracted from.

    No document, no reading: a lane that cannot reach the source abstains
    rather than falling back on the string, which is the whole point."""
    defect = classify(surface)
    if defect is None:
        return _abstain("", "not a class this taxonomy has named")
    if not doc:
        return _abstain(defect, "the document is not held, so there is nothing to re-read")
    return _READERS[defect](surface, doc, _locate(surface, doc, offset))
