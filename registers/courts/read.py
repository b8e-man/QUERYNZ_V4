"""The reading: each held judgment → one row per judgment, one row per
party and role, its numbered paragraphs; deterministic, no model, so the
fast tier runs the same code (docs/research/legal-documents.md).

Profiles before readers: each document is recognised by shape (its host,
the citation in its file name, a text layer on page 1, the court line and
the case-number form) as one of the profiles in `PROFILES`, read page by
page from its text layer through the reader contract
(`support.docread.read.read_document`, stamped and stored by hash), and
parsed by the caption grammar (`caption.parse`). A judgment with no text
layer on page 1 waits for the page reader (ruling 62) and is a catch-log
line; a Waitangi Tribunal report is recognised, held and not read into
judgment rows (it has claims, not parties; card).

Suppression (hard limit 16; plan 5.4: "A court's suppression order binds
every product"): a judgment that carries a suppression banner or an order
in its text, or whose citation or document is in the lane's ledger of
orders (suppress.py), has every party's name withheld except the Crown's
and an initial the court itself printed; the row and its role stay, the
name goes to the private table only. A suppression on any document of a
citation withholds the names on every document of it.

Items in equal items out plus items set aside: every listed document is a
judgment row or a catch-log line, asserted.

    read(docs, orders, store=None)    Result
"""
import datetime as dt
import os
from dataclasses import dataclass, field

from support import profiles
from support import reader as rd
from support.docread import pages as P
from support.docread.pagereader import page_total
from registers.courts import caption

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
READER = caption.VERSION
WAITANGI = "waitangi-tribunal-report"
PROFILES = {"NZSC": "courts-nzsc-judgment", "NZCA": "courts-nzca-judgment",
            "NZHC-civil": "courts-nzhc-civil-judgment", "NZHC-criminal": "courts-nzhc-criminal-judgment"}
COURT_LINES = {"NZSC": "SUPREME COURT", "NZCA": "COURT OF APPEAL", "NZHC": "HIGH COURT"}
WITHHELD_MARKER = "a suppression marker in the judgment"


@dataclass
class Result:
    judgments: list = field(default_factory=list)
    parties: list = field(default_factory=list)
    paragraphs: list = field(default_factory=list)     # (judgment key, number, page, document)
    withheld: list = field(default_factory=list)       # (party key, name, capacity): the private table only
    files: list = field(default_factory=list)          # (document, source, ref, url, profile, outcome, pages)
    set_aside: list = field(default_factory=list)      # (item, stage, reason)
    counts: dict = field(default_factory=dict)


def profile_version(slug: str) -> int:
    """The ledger's version; until the integrator appends it, the lane's
    proposed line (merge request courts-1)."""
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


def recognise(entry: dict, page1: str) -> tuple:
    """(profile slug, why) by shape, or (None, why). `page1` is the first
    page's text layer, '' for a scan."""
    if entry["source"] == "waitangitribunal.govt.nz":
        return WAITANGI, "the Waitangi Tribunal's document service"
    name = os.path.basename(entry.get("url") or entry.get("file") or "")
    fc = caption.file_citation(name)
    if not fc:
        return None, f"no neutral citation in the file name {name!r}"
    court = fc.split()[1]
    if court not in COURT_LINES:
        return None, f"no profile for {court}"
    if P.is_thin(page1):
        return None, "no text layer on page 1: waits for the page reader (ruling 62)"
    cl = caption.COURT_LINE.search(page1)
    if not cl or cl.group(1).strip() != COURT_LINES[court]:
        return None, f"page 1 has no court line for {court}"
    if court != "NZHC":
        return PROFILES[court], "court line and citation agree"
    criminal = bool(caption.CASE_NO.search(page1) and caption.CASE_NO.search(page1).group(1).startswith(("CRI", "CRC")))
    return PROFILES["NZHC-criminal" if criminal else "NZHC-civil"], "High Court; case number " + ("CRI" if criminal else "CIV")


def _ordered(citation: str, document: str, orders: list):
    for o in orders:
        if (o.get("citation") and o["citation"] == citation) or (o.get("document") and o["document"] == document):
            return o
    return None


def read(docs: list, orders: list = (), store: rd.Store = None, data_of=None) -> Result:
    """docs: [(entry, sha256)] of held documents (entry: the listing's line or a
    capture's); orders: the ledger's rows ({citation, document, reason}).
    `data_of(sha)` gives a document's bytes (the store's, by default)."""
    from support.docread.read import read_document
    from support.docstore.landing import read_bytes
    data_of = data_of or read_bytes
    store = store or rd.Store()
    res = Result()
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    parsed = []
    for entry, sha in docs:
        data = data_of(sha)
        page1 = P.page_text(data, 1)
        slug, why = recognise(entry, page1)
        npages = page_total(data)
        if slug is None or slug == WAITANGI:
            reason = why if slug is None else "a Waitangi Tribunal report: held and profiled, not read into judgment rows (card)"
            res.set_aside.append((sha, "recognise", reason))
            res.files.append((sha, entry["source"], entry.get("ref"), entry.get("url"), slug, "set aside", npages))
            continue
        version = profile_version(slug)
        reading = read_document(data, sha, profile=slug, profile_version=version, store=store)
        texts = reading.texts
        j = caption.parse(texts, os.path.basename(entry.get("url") or entry.get("file") or ""))
        res.files.append((sha, entry["source"], entry.get("ref"), entry.get("url"), slug, "read", len(texts)))
        if reading.unread:
            j.notes.append(f"{len(reading.unread)} pages with no text layer not read")
        parsed.append((entry, sha, slug, version, j))
    rows(res, parsed, orders, now)
    n_in = len(docs)
    n_out = len(res.judgments) + sum(1 for _, stage, _ in res.set_aside if stage == "recognise")
    if n_in != n_out:
        raise AssertionError(f"courts: {n_in} documents in, {n_out} out (judgments plus set aside): the reading does not reconcile")
    res.counts = {"documents": n_in, "judgments": len(res.judgments), "parties": len(res.parties),
                  "withheld": len(res.withheld), "set_aside": len(res.set_aside),
                  **{s: sum(1 for x in res.judgments if x["status"] == s) for s in ("parsed", "partial", "unparsed")}}
    return res


def rows(res: Result, parsed: list, orders: list = (), now: str = "") -> Result:
    """The rows from parsed judgments [(entry, sha, slug, version, caption.Judgment)],
    the suppression rule applied. Pure: no database, no file."""
    # a suppression on any document of a citation withholds the names on every document of it
    marked = {j.citation for _, _, _, _, j in parsed if j.suppression and j.citation}
    for entry, sha, slug, version, j in parsed:
        order = _ordered(j.citation, sha, orders)
        kinds = list(j.suppression_kinds) + (["ledger"] if order else [])
        if not j.suppression and j.citation in marked:
            kinds.append("another document of the citation")
        withheld = (f"suppression order: {order['reason']}" if order else
                    WITHHELD_MARKER if kinds else None)
        # the caption is read from page 1's text layer (a scan is set aside above); pages with no layer are
        # left out of the paragraph index and counted in the notes
        stamp = {"document": sha, "read_from": "text",
                 "reader": READER, "profile": slug, "profile_version": version, "loaded_at": now}
        key = f"{sha}/judgment"
        res.judgments.append({
            "key": key, "citation": j.citation, "court": j.court, "court_name": j.court_name, "registry": j.registry,
            "case_numbers": j.case_numbers, "judgment_date": j.judgment_date, "date_basis": j.date_basis,
            "hearing": j.hearing, "judges": j.judges, "heading": j.heading, "caption_shape": j.caption_shape,
            "outcome": j.outcome, "paragraphs": len(j.paragraphs), "parties": len(j.parties),
            "suppression": bool(kinds), "suppression_kinds": kinds, "withheld": withheld, "status": j.status,
            "missing": j.missing, "unrecognised": len(j.unrecognised), "notes": j.notes, "source": entry["source"],
            "source_url": entry.get("url"), "source_note": entry.get("note") or "", "page": 1, "place": "caption",
            **stamp})
        for p in j.parties:
            pkey = f"{sha}/party/{p.position}"
            hide = bool(withheld) and not p.crown and not p.anonymised
            if hide:
                res.withheld.append((pkey, p.name, p.capacity))
            res.parties.append({
                "key": pkey, "judgment": key, "citation": j.citation, "position": p.position, "block": p.block,
                "role": p.role, "name": None if hide else p.name, "withheld": hide, "anonymised": p.anonymised,
                "crown": p.crown, "confidence": p.confidence, "capacity": None if hide else p.capacity,
                "page": 1, "place": f"caption, block {p.block}, party {p.position}", **stamp})
        res.paragraphs += [(key, n, pg, sha) for n, pg in j.paragraphs]
        if j.status != "parsed":
            res.set_aside.append((key, "parse", f"{j.status}: missing {', '.join(j.missing)}"))
    return res
