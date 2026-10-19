"""The reading (plan 1.11, 4.1): one return's bytes → one register row, or a
line in the catch log saying why not.

The shape is measured first (`pages.read_from`), and the shape picks the
route. No model is called anywhere here, so the fast tier runs the same
code.

- **text** (every page has a text layer): the document profile
  `ec-party-return-text` (its current version) through the reader
  contract; the page texts are stamped and stored by
  `support.docread.read`, and the declaration page is read by
  `declaration.read`.
- **pixels or mixed** (some pages are images): the text pages go through
  the reader contract under `ec-party-return-scan` or
  `ec-party-return-image-declaration`, and each image page is REPLAYED
  from the page reader's stored reading (GLM-OCR Q8_0 at 300 dots, prompt
  `OCR`: the reader step 3 kept, ruling 60). A stored reading is taken
  under any version of the party-return profiles, because the versions
  since differ in nothing the page reader does, and the row names the
  profile and version the reading was made under. An image page with no
  stored reading sets the return aside and names it, so a re-read can be
  asked for (step 2.14); this module never asks the model itself. The
  declaration page is the first page carrying the donations total line,
  read by `pixels.read` when it came from pixels; the year, which the page
  reader drops from that page, comes from `pixels.return_year`.

A return the profile does not recognise, or whose declaration page cannot
be reconciled with its own total, publishes nothing: it is set aside with
the stage and the reason.

    result = read_return(data, sha256, store)
    result.row          the register row (a dict under the row contract), or None
    result.set_aside    [(stage, reason)]
"""
import datetime as dt
from dataclasses import dataclass, field

from keys import parties
from support import profiles
from support import reader as rd
from support.docread import pages
from support.docread.read import read_document
from registers.party_returns import declaration, pixels

PROFILE = "ec-party-return-text"
SCAN = "ec-party-return-scan"
IMAGE_DECLARATION = "ec-party-return-image-declaration"
#: every profile a stored page reading of a party return may have been made under
READING_PROFILES = (SCAN, IMAGE_DECLARATION, "ec-party-return-handwritten", PROFILE)
PAGE_MODEL = "glm-ocr"
#: the settings stamped on the page reader's readings, exactly (the trial's incumbent, `support.trials.readers`;
#: and the re-read job's shorter stamp). A test holds the first equal to the trial's own.
PAGE_SETTINGS = (
    {"dpi": 300, "prompt": "OCR", "prompt_sha": "5e5bea5354e3f22e", "system": None, "level": "q8_0",
     "temperature": 0.0, "max_tokens": 8000, "thinking": "default", "server_build": None,
     "weights": ["GLM-OCR-Q8_0.gguf", "mmproj-GLM-OCR-Q8_0.gguf"]},
    {"dpi": 300, "prompt": "OCR"},
)


@dataclass
class Result:
    document: str
    row: dict = None
    set_aside: list = field(default_factory=list)
    declaration: declaration.Declaration = None
    pages: int = 0


def current_profile(slug: str = PROFILE) -> dict:
    p = profiles.profile(slug)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return p


def recognise(texts: dict, prof: dict) -> str:
    """'' when the document has the text profile's shape, else why not. By
    shape, never by phrase (contract: the document profile, rule 2)."""
    sig = prof.get("signals") or {}
    if not texts:
        return "no pages"
    how = pages.read_from(b"%PDF", texts)
    if how != "text":
        thin = pages.thin_pages(texts)
        return f"{len(thin)} of {len(texts)} pages have no text layer ({how}): needs the page reader"
    if len(texts.get(1, "").strip()) < int(sig.get("page1_chars_min") or 0):
        return f"page 1 carries {len(texts[1].strip())} characters, under the profile's {sig['page1_chars_min']}"
    total = sum(len(t.strip()) for t in texts.values())
    if total < int(sig.get("doc_chars_min") or 0):
        return f"the document carries {total} characters, under the profile's {sig['doc_chars_min']}"
    return ""


def stored_page(store: rd.Store, sha256: str, page: int):
    """The page reader's stored reading of one page, or None. Newest
    profile version first; the first settings stamp first."""
    for slug in READING_PROFILES:
        for version in sorted((int(h["version"]) for h in profiles.history(slug)), reverse=True):
            for settings in PAGE_SETTINGS:
                key = rd.reading_key(sha256, page, PAGE_MODEL, settings, slug, version)
                if store.has(key):
                    return store.get(key)
    return None


def _row(sha256, page, decl, reading, year_from, loaded_at) -> dict:
    party, basis = parties.party_name(decl.party_label)
    return {
        "key": f"{sha256}/declaration",
        "document": sha256,
        "page": page,
        "place": "declaration",
        "reader": f"{reading.reader}: {reading.model}",
        "profile": reading.profile,
        "profile_version": reading.profile_version,
        "read_from": reading.read_from,
        "loaded_at": loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "filed": {
            "party": party,
            "party_label": decl.party_label,
            "party_basis": basis,
            "year": decl.year,
            "year_from": year_from,
            "declared_total": round(decl.total, 2),
            "part_a": decl.parts.get("A"), "part_c": decl.parts.get("C"), "part_d": decl.parts.get("D"),
            "part_f": decl.parts.get("F"), "part_g": decl.parts.get("G"),
            "declared_parts": decl.total_letters,
            "total_check": decl.check,
        },
    }


def _publish_or_set_aside(out: Result, decl, extra: list = ()) -> bool:
    out.declaration = decl
    problems = decl.problems() + list(extra)
    if decl.party_label is None:
        problems.append("no party name on the declaration page")
    if problems:
        out.set_aside.append(("declaration", "; ".join(problems)))
        return False
    return True


def read_text(data, sha256, texts, store, out, loaded_at) -> Result:
    prof = current_profile()
    why = recognise(texts, prof)
    if why:
        out.set_aside.append(("recognise", why))
        return out
    reading = read_document(data, sha256, profile=PROFILE, profile_version=int(prof["version"]), store=store, texts=texts)
    decl = declaration.read(reading.texts.get(1, ""))
    if _publish_or_set_aside(out, decl):
        out.row = _row(sha256, 1, decl, reading.readings[0], "declaration page", loaded_at)
    return out


def read_pixels(data, sha256, texts, how, store, out, loaded_at) -> Result:
    slug = SCAN if how == "pixels" else IMAGE_DECLARATION
    reading = read_document(data, sha256, profile=slug, profile_version=int(current_profile(slug)["version"]),
                            store=store, texts=texts)
    by_page = {r.page: r for r in reading.readings}
    missing = []
    for p in reading.unread:
        r = stored_page(store, sha256, p)
        if r is None:
            missing.append(p)
        else:
            by_page[p] = r
    if missing:
        out.set_aside.append(("read", f"{len(missing)} of {len(texts)} pages are images with no stored page reading "
                                      f"(pages {', '.join(map(str, missing[:12]))}{' …' if len(missing) > 12 else ''}): "
                                      f"ask for a re-read of {sha256}"))
        return out
    full = {p: r.text for p, r in by_page.items()}
    page = pixels.declaration_page(full)
    if page is None:
        out.set_aside.append(("declaration", "no page carries the donations total line (A + …)"))
        return out
    r = by_page[page]
    decl = pixels.read(r.text) if r.read_from == "pixels" else declaration.read(r.text)
    year_from, extra = "declaration page", []
    if decl.year is None:
        decl.year, year_from = pixels.return_year(full)
        if decl.year is None:
            extra = [year_from]
    if _publish_or_set_aside(out, decl, extra):
        out.row = _row(sha256, page, decl, r, year_from, loaded_at)
    return out


def read_return(data: bytes, sha256: str, store: rd.Store = None, loaded_at: str = None) -> Result:
    store = store or rd.Store()
    texts = pages.text_pages(data)
    out = Result(sha256, pages=len(texts))
    if not texts:
        out.set_aside.append(("recognise", "no pages"))
        return out
    how = pages.read_from(b"%PDF", texts)
    if how == "text":
        return read_text(data, sha256, texts, store, out, loaded_at)
    return read_pixels(data, sha256, texts, how, store, out, loaded_at)
