"""The reading (plan 4.1): one candidate return's bytes → one register row
of its declared totals, or a line in the catch log saying why not. No model
is called anywhere here, so the fast tier runs the same code.

The shape picks the route (profiles before readers; the lane's proposed
profiles are in `profile-proposed.jsonl` until the integrator appends
them):

- **text** (`ec-candidate-return-text`): the first page with a text layer
  carrying the donations heading is the declaration page, read through the
  reader contract (`support.docread.read.read_document`, which stamps and
  stores the page texts) and `declaration.read`.
- **scan** (`ec-candidate-return-scan`): no text page carries it (the
  pages are images, or a scanner's own OCR layer that lost the heading:
  `ELECTTON`, nothing at all), so the pages are REPLAYED from the page reader's stored readings (GLM-OCR,
  prompt "OCR"; the trial stored them under `ec-candidate-expenses-return`
  at 200 dots, so any GLM-OCR reading with that prompt under a candidate
  profile is taken, newest version first), and the first that carries the
  heading is read in plain mode. A return with no such reading is set aside
  naming its image pages, for a re-read job (step 2.14); this module never
  asks the model itself.

A return is published when each section it declares reads under the page's
own arithmetic (`declaration.Declaration.problems`); otherwise it is set
aside whole at stage `declaration`. The candidate, year, electorate and
party come from the Commission (`join.py`), never from the file name; the
page's own words for them are kept as filed beside.

    result = read_return(data, sha256, store)
    result.row          the register row (a dict under the row contract), or None
    result.declaration  the Declaration read, or None
    result.set_aside    [(stage, reason)]
"""
import datetime as dt
import glob
import json
import os
from dataclasses import dataclass, field

from support import profiles
from support import reader as rd
from support.docread import pages
from support.docread.read import read_document
from registers.candidate_returns import declaration

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
TEXT = "ec-candidate-return-text"
SCAN = "ec-candidate-return-scan"
#: every profile a stored page reading of a candidate return may have been made under
READING_PROFILES = (SCAN, "ec-candidate-expenses-return", TEXT)
PAGE_MODEL = "glm-ocr"
PAGE_PROMPT = "OCR"
PAGES_MAX = 20


@dataclass
class Result:
    document: str
    row: dict = None
    declaration: object = None
    set_aside: list = field(default_factory=list)
    pages: int = 0
    route: str = None


def profile_version(slug: str) -> int:
    """The ledger's version; until the integrator appends it, the lane's proposed line."""
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


def stored_page(store: rd.Store, sha256: str, page: int):
    """The page reader's stored reading of one page, or None: GLM-OCR with the prompt "OCR" under a candidate-return
    profile, the profile order first and its newest version first."""
    roots = [s.root for s in (store, getattr(store, "shared", None)) if s is not None]
    for slug in READING_PROFILES:
        found = []
        paths = [p for root in roots
                 for p in glob.glob(os.path.join(root, sha256[:2], sha256, f"p{page}__{slug}@*__{PAGE_MODEL}__*.json"))]
        for path in paths:
            try:
                version = int(os.path.basename(path).split("__")[1].split("@")[1])
                with open(path, encoding="utf-8") as f:
                    r = json.load(f)
            except (ValueError, IndexError, OSError):
                continue
            if (r.get("settings") or {}).get("prompt") == PAGE_PROMPT and r.get("read_from") == "pixels":
                found.append((version, r))
        if found:
            version, r = max(found, key=lambda x: x[0])
            return rd.Reading(r["document"], r["page"], r["reader"], r["model"], r["settings"], r["profile"],
                              int(r["profile_version"]), r["read_from"], r["text"], made_at=r.get("made_at"))
    return None


def has_heading(text: str) -> bool:
    return bool(declaration.SECTIONS[0][1].search(text or ""))


def _row(sha256, page, decl, reading, loaded_at) -> dict:
    filed = {"year_as_printed": decl.year, "candidate_as_printed": decl.candidate, "party_as_printed": decl.party_label,
             "electorate_as_printed": decl.electorate, "signed": decl.signed}
    for name in ("donations", "expenses", "loans"):
        s = decl.sections.get(name)
        filed[name] = decl.figure(name) if s is not None else None
        filed[f"{name}_check"] = decl.check(name) if s is not None else None
    s = decl.sections.get("donations")
    filed.update({f"part_{k.lower()}": (s.parts.get(k) if s else None) for k in ("A", "C", "D")})
    s = decl.sections.get("expenses")
    filed.update({f"part_{k.lower()}": (s.parts.get(k) if s else None) for k in ("F", "G")})
    return {
        "key": f"{sha256}/declaration",
        "document": sha256,
        "page": page,
        "place": "declaration",
        "reader": f"{reading.reader}: {reading.model}",
        "profile": reading.profile,
        "profile_version": int(reading.profile_version),
        "read_from": reading.read_from,
        "loaded_at": loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "filed": filed,
    }


def _publish_or_set_aside(out: Result, decl, page: int, reading, loaded_at) -> Result:
    out.declaration = decl
    problems = []
    for name in ("donations", "expenses"):
        problems += decl.problems(name)
    if "loans" in decl.sections:
        problems += decl.problems("loans")
    if problems:
        out.set_aside.append(("declaration", f"page {page}: " + "; ".join(problems)))
        return out
    out.row = _row(out.document, page, decl, reading, loaded_at)
    return out


def read_return(data: bytes, sha256: str, store: rd.Store = None, loaded_at: str = None) -> Result:
    store = store or rd.Store()
    texts = pages.text_pages(data)
    out = Result(sha256, pages=len(texts))
    if not texts:
        out.set_aside.append(("recognise", "no pages: not a PDF the text layer reader can open"))
        return out
    if len(texts) > PAGES_MAX:
        out.set_aside.append(("recognise", f"{len(texts)} pages, over the profiles' {PAGES_MAX}"))
        return out
    thin = set(pages.thin_pages(texts))
    page = next((p for p in sorted(texts) if p not in thin and has_heading(texts[p])), None)
    if page is not None:
        out.route = "text"
        reading = read_document(data, sha256, profile=TEXT, profile_version=profile_version(TEXT), store=store,
                                texts={page: texts[page]})
        r = reading.readings[0]
        return _publish_or_set_aside(out, declaration.read(r.text), page, r, loaded_at)
    out.route = "scan"
    missing = []
    for p in sorted(texts):                           # an image page, or a scanner's own OCR layer that lost the heading
        r = stored_page(store, sha256, p)
        if r is None:
            missing.append(p)
            continue
        if has_heading(r.text):
            return _publish_or_set_aside(out, declaration.read(r.text, layout=False), p, r, loaded_at)
    if missing:
        kind = "images" if set(missing) <= thin else "images or carry a scanner's own OCR layer without the heading"
        shown = ", ".join(map(str, missing[:12])) + (" …" if len(missing) > 12 else "")
        out.set_aside.append(("read", f"no text page carries the declaration; {len(missing)} of {len(texts)} pages are "
                                      f"{kind}, with no stored page reading (pages {shown}): ask for a re-read of {sha256}"))
    else:
        out.set_aside.append(("recognise", "no page, text or stored reading, carries the donations heading"))
    return out
