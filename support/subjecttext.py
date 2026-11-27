"""A subject's name in a text: folding and stems, shared by the news subjects gate (registers.news.subjects) and the
board's feeds (products.board.feeds), which may import only from support (tests/test_imports_one_way.py; moved here 28
November 2026)."""
from __future__ import annotations

import re
import unicodedata


def fold(s: str) -> str:
    """Macrons and accents folded, lower case, every run of other than a letter or digit one space."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


SUFFIXES = ("ings", "ing", "ed", "es", "s")


def stem(word: str) -> str:
    for x in SUFFIXES:
        if len(word) > len(x) + 2 and word.endswith(x):
            return word[: -len(x)]
    return word


STOP = {"the", "a", "an", "of", "in", "on", "and", "for", "to", "at", "by", "new", "zealand", "nz"}


def stems(s: str) -> list[str]:
    """A name's stems, its small words left out: "3D printing" → ["3d", "print"]; "3D-printed guns" → ["3d", "print", "gun"]."""
    return [stem(w) for w in fold(s).split() if w not in STOP]


GAP = 2


def names_in(name: str, text: str) -> bool:
    """True when the name's stems are in the text's stems in order, any ending, with at most GAP words between two of
    them: "3D printing" is in "3D-printed guns"; "illegal firearms" in "illegal 3D-printed firearms"; "the Seoul crowd
    crush" is not in "a crowd crush in Seoul" (the order differs), so that one is inferred."""
    want = stems(name)
    if not want:
        return False
    have = stems(text)
    for i, w in enumerate(have):
        if w != want[0]:
            continue
        at, ok = i, True
        for nxt in want[1:]:
            window = have[at + 1: at + 2 + GAP]
            if nxt not in window:
                ok = False
                break
            at = at + 1 + window.index(nxt)
        if ok:
            return True
    return False
