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
aside whole at stage `declaration`. A published return then has its Part A
read from its text-layer pages (`donors.py`): published whole when the rows
add to the page's own total and the declaration's Part A, otherwise set
aside whole beside the row (stage `part-a`, which is not a return's stage:
the row stands). A scanned return's Part A is read from the stored readings of
the pages after its declaration (`pixels.py`), under the same reconciliation;
one with none of them stored is set aside naming its pages for a re-read (ruling
62; `replay rereads`), and a Part A the declaration left blank is never taken for
nil. The candidate, year, electorate and
party come from the Commission (`join.py`), never from the file name; the
page's own words for them are kept as filed beside.

    result = read_return(data, sha256, store)
    result.row          the register row (a dict under the row contract), or None
    result.declaration  the Declaration read, or None
    result.donors       Part A rows, each with its key, name and amount; the address beside it is private
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
from registers.candidate_returns import declaration, donors, pixels

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
TEXT = "ec-candidate-return-text"
SCAN = "ec-candidate-return-scan"
#: every profile a stored page reading of a candidate return may have been made under
READING_PROFILES = (SCAN, "ec-candidate-expenses-return", TEXT)
PAGE_MODEL = "glm-ocr"
PAGE_PROMPT = "OCR"
PAGES_MAX = 20
#: the words a Part A set-aside line opens its re-read request with, for `replay rereads`
REREAD = "Part A is on image pages with no stored page reading: re-read"


@dataclass
class Result:
    document: str
    row: dict = None
    declaration: object = None
    set_aside: list = field(default_factory=list)
    pages: int = 0
    route: str = None
    donors: list = field(default_factory=list)       # Part A rows, published only when the part reconciled


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


def _part_a(out: Result, data: bytes, texts: dict, store) -> None:
    """Part A from the text-layer pages, stamped with each page's own reading."""
    f = out.row["filed"]
    declared = f.get("part_a")
    if declared is None:
        declared = 0.0 if f.get("donations") == 0 else None
    if out.route != "text":
        _part_a_pixels(out, texts, store, declared)
        return
    thick = {p: t for p, t in texts.items() if p not in set(pages.thin_pages(texts))}
    part = donors.read(thick, declared)
    f["donors_check"] = part.check or None
    if part.problems:
        thin_a = [p for p in pages.thin_pages(texts) if p > out.row["page"]]
        extra = f" ({len(thin_a)} later pages are images)" if thin_a and declared else ""
        out.set_aside.append(("part-a", "; ".join(part.problems)[:1800] + extra))
        return
    if not part.rows:
        return
    reading = read_document(data, out.document, profile=TEXT, profile_version=profile_version(TEXT), store=store,
                            texts={p: thick[p] for p in sorted({r["page"] for r in part.rows})})
    _stamp(out, part.rows, {r.page: r for r in reading.readings})


def _stamp(out: Result, rows: list, by_page: dict) -> None:
    for k, r in enumerate(rows, 1):
        rd_ = by_page[r["page"]]
        out.donors.append({**r, "key": f"{out.document}/A/{k}", "place": f"A/{k}", "ordinal": k, "document": out.document,
                           "return_key": out.row["key"], "reader": f"{rd_.reader}: {rd_.model}", "profile": rd_.profile,
                           "profile_version": int(rd_.profile_version), "read_from": rd_.read_from,
                           "loaded_at": out.row["loaded_at"]})


def _part_a_pixels(out: Result, texts: dict, store, declared) -> None:
    """Part A from the page reader's stored readings of the pages after the declaration (`pixels.py`). A part with
    none of its pages stored is set aside naming the pages a re-read job would read (`replay rereads`)."""
    f = out.row["filed"]
    f["donors_check"] = None
    if declared == 0.0:
        f["donors_check"] = "declared-nil"
        return
    after = [p for p in sorted(texts) if p > out.row["page"]]
    stored = {p: r for p in after if (r := stored_page(store, out.document, p)) is not None}
    carrying = {p: r for p, r in stored.items() if donors.HEADING.search(r.text) or donors.TOTAL.search(r.text)}
    if not carrying:
        missing = [p for p in after if p not in stored][:3]
        why = (f"{REREAD} {out.document} pages {', '.join(map(str, missing))}" if missing
               else "no stored page reading carries Part A's heading or printed total")
        out.set_aside.append(("part-a", why))
        return
    part = pixels.read({p: r.text for p, r in carrying.items()}, declared)
    f["donors_check"] = part.check or None
    if part.problems:
        out.set_aside.append(("part-a", "; ".join(part.problems)[:1800]))
        return
    _stamp(out, part.rows, carrying)


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
        _publish_or_set_aside(out, declaration.read(r.text), page, r, loaded_at)
        if out.row:
            _part_a(out, data, texts, store)
        return out
    out.route = "scan"
    missing = []
    for p in sorted(texts):                           # an image page, or a scanner's own OCR layer that lost the heading
        r = stored_page(store, sha256, p)
        if r is None:
            missing.append(p)
            continue
        if has_heading(r.text):
            _publish_or_set_aside(out, declaration.read(r.text, layout=False), p, r, loaded_at)
            if out.row:
                _part_a(out, data, texts, store)
            return out
    if missing:
        kind = "images" if set(missing) <= thin else "images or carry a scanner's own OCR layer without the heading"
        shown = ", ".join(map(str, missing))
        out.set_aside.append(("read", f"no text page carries the declaration; {len(missing)} of {len(texts)} pages are "
                                      f"{kind}, with no stored page reading (pages {shown}): ask for a re-read of {sha256}"))
    else:
        out.set_aside.append(("recognise", "no page, text or stored reading, carries the donations heading"))
    return out
