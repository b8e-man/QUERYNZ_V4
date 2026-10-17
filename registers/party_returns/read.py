"""The reading (plan 1.11): one return's bytes → one register row, or a
line in the catch log saying why not.

Run from the document profile `ec-party-return-text` (its current
version) through the reader contract: the shape is measured first (every
page has a text layer, the first page carries at least the profile's
minimum of text), the page texts are stamped and stored as readings by
`support.docread.read`, and the declaration page is read by
`declaration.read`. A return the profile does not recognise, or whose
declaration page cannot be reconciled with its own total, publishes
nothing: it is set aside with the stage and the reason. No model is
called anywhere here, so the fast tier runs the same code.

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
from support.docread.read import READER, read_document
from registers.party_returns import declaration

PROFILE = "ec-party-return-text"


@dataclass
class Result:
    document: str
    row: dict = None
    set_aside: list = field(default_factory=list)
    declaration: declaration.Declaration = None
    pages: int = 0


def current_profile() -> dict:
    p = profiles.profile(PROFILE)
    if p is None:
        raise LookupError(f"no document profile {PROFILE}")
    return p


def recognise(texts: dict, prof: dict) -> str:
    """'' when the document has the profile's shape, else why not. By
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


def read_return(data: bytes, sha256: str, store: rd.Store = None, loaded_at: str = None) -> Result:
    store = store or rd.Store()
    prof = current_profile()
    version = int(prof["version"])
    texts = pages.text_pages(data)
    out = Result(sha256, pages=len(texts))
    why = recognise(texts, prof)
    if why:
        out.set_aside.append(("recognise", why))
        return out
    reading = read_document(data, sha256, profile=PROFILE, profile_version=version, store=store, texts=texts)
    decl = declaration.read(reading.texts.get(1, ""))
    out.declaration = decl
    problems = decl.problems()
    if decl.party_label is None:
        problems.append("no party name on the declaration page")
    if problems:
        out.set_aside.append(("declaration", "; ".join(problems)))
        return out
    party, basis = parties.party_name(decl.party_label)
    out.row = {
        "key": f"{sha256}/declaration",
        "document": sha256,
        "page": 1,
        "place": "declaration",
        "reader": READER,
        "profile": PROFILE,
        "profile_version": version,
        "read_from": "text",
        "loaded_at": loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "filed": {
            "party": party,
            "party_label": decl.party_label,
            "party_basis": basis,
            "year": decl.year,
            "declared_total": round(decl.total, 2),
            "part_a": decl.parts.get("A"), "part_c": decl.parts.get("C"), "part_d": decl.parts.get("D"),
            "part_f": decl.parts.get("F"), "part_g": decl.parts.get("G"),
            "declared_parts": decl.total_letters,
            "total_check": decl.check,
        },
    }
    return out
