"""The scanned declaration's own printed total, from a page reading.

The s 210C form prints, under "Total donation and date received", a
"Total amount" box and, beside it, a grid of the gifts that make it up.
The Commission prints the same amount in its table, so the two are two
statements by the Commission of one figure: the comparison costs nothing
and is the only check that does not depend on a reading being plausible
(old lesson, 8-reading-documents.md:638). The form's own boilerplate quotes
$20,000 in several places, so a figure is taken only from the lines just
under the label, never from anywhere on the page.

    total(pages) -> Total(amount, page, why)      pages: {page: text}
    stored(sha256, profile, model)                the held page readings of one scan

Readings are replayed, never made here: the fast tier calls no model. A
stored reading is taken under its own stamp (reader, settings, profile
version), whoever made it; step 3's trial made the first thirty.
"""
import glob
import json
import os
import re
from dataclasses import dataclass

from support import reader as rd
from registers.disclosures.listing import money

PROFILE = "ec-donation-disclosure-20k"
MODEL = "glm-ocr"

LABEL = re.compile(r"total\s+donation\s+and\s+date\s+received|total\s+amount", re.I)
BOILERPLATE = re.compile(r"exceed|more than|over \$|threshold|aggregat|\$20,000\b(?!\.\d)", re.I)
WINDOW = 4


@dataclass
class Total:
    amount: float = None
    page: int = None
    why: str = ""


def total(pages: dict) -> Total:
    for page in sorted(pages):
        lines = (pages[page] or "").splitlines()
        for i, ln in enumerate(lines):
            if not LABEL.search(ln):
                continue
            for nxt in lines[i:i + 1 + WINDOW]:
                if BOILERPLATE.search(nxt):
                    continue
                amt = money(nxt)
                if amt is not None and amt > 0:
                    return Total(amt, page, "")
    return Total(None, None, "no figure under the form's total label")


def stored(sha256: str, profile: str = PROFILE, model: str = MODEL, root: str = None) -> list:
    """[Reading] for every page of one scan the store holds under `profile`
    (any version) and `model`, one per page: the newest profile version,
    then the newest reading. [] when none is held."""
    folder = os.path.join(root or rd.STORE, sha256[:2], sha256)
    best = {}
    for path in glob.glob(os.path.join(folder, f"p*__{profile}@*__{model}__*.json")):
        with open(path, encoding="utf-8") as f:
            r = rd.Reading(**json.load(f))
        have = best.get(r.page)
        if have is None or (r.profile_version, r.made_at) > (have.profile_version, have.made_at):
            best[r.page] = r
    return [best[p] for p in sorted(best)]
