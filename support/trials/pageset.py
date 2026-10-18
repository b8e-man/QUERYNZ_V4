"""THE PAGE SET (plan step 3.3): which pages of which election documents the
page readers are tried on, drawn from DISTINCT HASHES of the captured
documents, with text-or-scan decided PER PAGE.

    python -m support.trials.pageset build        measure every candidate and write pageset.jsonl
    python -m support.trials.pageset show         counts by kind, year and shape
    pageset.load()                                the set: one record per document
    pageset.locate(sha256)                        the bytes, by hash (a name only finds them)

A document is its bytes (condition 2): the old corpus held one return under
several names, so everything here is keyed by sha256 and a file name is an
attribute kept only so the bytes can be found. The window is 2019 onward
(ruling 347). Every shape is in: all text, image first page, full scan,
mixed, handwritten (by name: the profile names Vision NZ 2020), raster
photographs; every kind the plan lists: party donation and loan returns
(every distinct 2019+ return, because these are the product), candidate
returns (which carry the candidate's expenses), party expense returns,
large-donation disclosures, party financial statements, promoter returns,
the other kinds sampled by stratum. The three named cases are fixed tests.

Per page: the text layer is measured (`pdftotext -layout`, one page at a
time, as the reader contract does) and a page under the profile's
threshold goes to the page reader (`pixels`); a page with a layer stays
with the text reader and is also a FREE KEY for the page readers (3.4):
rendered and read, the text layer is the answer. Text pages are capped per
document so the set stays a few thousand pages; scan pages are all in.

The set is hashes, page numbers, shapes and labels, never bytes, rows or
a person's address; a party label is a party. Nothing here calls a model.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

from support.docread import pages as pg
from support.docread.pagereader import is_pdf, page_total

HERE = os.path.dirname(os.path.abspath(__file__))
PAGESET = os.path.join(HERE, "pageset.jsonl")
OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
STAGING = os.path.join(OLD_LIVE, "var", "staging")
WINDOW_FROM = 2019                 # ruling 347
PAGE_TEXT_MIN = pg.PAGE_TEXT_MIN   # the reader contract's per-page threshold (80); the profiles say 50: both recorded
PROFILE_PAGE_MIN = 50
TEXT_KEY_PAGES = 4                 # free-key pages kept per text document: 1, 2, 3 and the last
SAMPLE_PER_STRATUM = 12            # kind-year strata other than party returns
RASTER_SAMPLE = 4

# where each kind's files are, and how the year is read off the name
ARCHIVE_PARTY = re.compile(r"^Party-donations-and-loans__(?P<n>\d{4})-returns__.*\.pdf$", re.I)      # N-returns = year N-1
ARCHIVE_2021 = re.compile(r"^2021-annual-returns-__.*\.pdf$", re.I)
CAND_2023 = re.compile(r"^(Uploads__|candidate-returns__2023).*(2023).*\.pdf$", re.I)
DISC_2026 = re.compile(r"^2026-20k\+-donations__.*\.(pdf|jpg|jpeg|png)$", re.I)
YEAR = re.compile(r"(20[12]\d)")

# the fixed tests (3.3): found by name, kept by hash; party and year only
NAMED_CASES = (
    ("nz-first-2023", "party-return", 2023, re.compile(r"(nz|new-zealand)-?first.*2023", re.I)),
    ("one-party-2020", "party-return", 2020, re.compile(r"(?<![a-z0-9])one-?party.*2020", re.I)),
    ("maori-party-2020", "party-return", 2020, re.compile(r"maori-party.*2020", re.I)),
    ("vision-nz-2020-handwritten", "party-return", 2020, re.compile(r"vision-?(nz|new-zealand).*2020", re.I)),
)
TWENTY = 20                        # the compression comparison's pages (3.1): a fixed subset, scans and text alike


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def candidates(staging: str = None) -> list[dict]:
    """Every captured election file in the window: path, kind, year."""
    staging = staging or STAGING
    out = []

    def add(path, kind, year):
        if year is not None and year >= WINDOW_FROM:
            out.append({"path": path, "kind": kind, "year": year})

    archive = os.path.join(staging, "ec-donations", "archive")
    for f in sorted(os.listdir(archive)) if os.path.isdir(archive) else []:
        p = os.path.join(archive, f)
        m = ARCHIVE_PARTY.match(f)
        if m:
            add(p, "party-return", int(m.group("n")) - 1)
        elif ARCHIVE_2021.match(f):
            add(p, "party-return", 2021)
        elif CAND_2023.match(f):
            add(p, "candidate-return", 2023)
        elif DISC_2026.match(f):
            add(p, "disclosure-20k", 2026)
    residue = os.path.join(staging, "ec-donations", "residue")
    for dirpath, dirs, files in os.walk(os.path.join(residue, "party_returns")):
        dirs.sort()
        for f in sorted(files):
            if f.lower().endswith(".pdf"):
                m = YEAR.search(dirpath.split(residue)[-1] + "/" + f)
                add(os.path.join(dirpath, f), "party-return", int(m.group(1)) if m else None)
    for dirpath, dirs, files in os.walk(os.path.join(residue, "candidate_returns_2020")):
        dirs.sort()
        for f in sorted(files):
            if f.lower().endswith(".pdf"):
                add(os.path.join(dirpath, f), "candidate-return", 2020)
    for dirpath, dirs, files in os.walk(os.path.join(residue, "donations_20k")):
        dirs.sort()
        for f in sorted(files):
            if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png")):
                m = YEAR.search(f)
                add(os.path.join(dirpath, f), "disclosure-20k", int(m.group(1)) if m else 2023)
    for folder, kind in (("ec-expenses", "party-expenses"), ("ec-financials", "financial-statements"),
                         ("ec-promoters", "promoter-return")):
        d = os.path.join(staging, folder)
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if f.lower().endswith(".pdf"):
                m = YEAR.search(f)
                add(os.path.join(d, f), kind, int(m.group(1)) if m else None)
    return out


def label_of(path: str) -> str:
    """A party or filer label from the file name: the name is an attribute,
    never the key."""
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = re.sub(r"^(Party-donations-and-loans__\d{4}-returns__|2021-annual-returns-__|2026-20k\+-donations__|"
                  r"party-expenses__\d{4}__|Financial-statements__\d{4}__|promoter-return__\d{4}__|Uploads__)", "", stem)
    return stem


def shape_of(texts: dict, raster: bool) -> str:
    if raster:
        return "raster"
    if not texts:
        return "scan"
    thin = pg.thin_pages(texts)
    if not thin:
        return "text"
    if len(thin) == len(texts):
        return "scan"
    if thin == [1]:
        return "image-first-page"
    return "mixed"


def measure(path: str) -> dict:
    """One document measured without reading: hash, pages, each page's
    text-layer length."""
    with open(path, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    raster = not is_pdf(data)
    if raster:
        return {"sha256": sha, "bytes": len(data), "pages": 1, "chars": {1: 0}, "shape": "raster"}
    texts = pg.text_pages(data)
    return {"sha256": sha, "bytes": len(data), "pages": page_total(data), "chars": {p: len(t.strip()) for p, t in texts.items()},
            "shape": shape_of(texts, False)}


def pick_pages(rec: dict) -> list[dict]:
    """Which pages are in: every scan page; text pages capped as free keys."""
    chars = rec["chars"]
    pixels = [p for p, c in sorted(chars.items()) if c < PAGE_TEXT_MIN]
    text = [p for p, c in sorted(chars.items()) if c >= PAGE_TEXT_MIN]
    if rec.get("all_pages"):
        keep_text = text
    else:
        last = text[-1:] if text else []
        keep_text = sorted(set(text[:TEXT_KEY_PAGES - 1] + last))
    out = [{"page": p, "read_from": "pixels", "chars": chars[p]} for p in pixels]
    out += [{"page": p, "read_from": "text", "chars": chars[p]} for p in keep_text]
    return sorted(out, key=lambda r: r["page"])


def build(staging: str = None, out_path: str = None, log=print, workers: int = 6) -> list[dict]:
    cands = candidates(staging)
    log(f"pageset: {len(cands)} captured files in the window")
    by_path = {c["path"]: c for c in cands}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        measured = list(pool.map(lambda c: (c["path"], measure(c["path"])), cands))
    docs: dict[str, dict] = {}
    for path, m in measured:
        c = by_path[path]
        d = docs.get(m["sha256"])
        if d is None:
            d = docs[m["sha256"]] = {"sha256": m["sha256"], "bytes": m["bytes"], "kind": c["kind"], "year": c["year"],
                                     "label": label_of(path), "names": [], "pages": m["pages"], "chars": m["chars"],
                                     "shape": m["shape"], "named_case": None, "all_pages": False}
        d["names"].append(os.path.relpath(path, staging or STAGING))
        if c["kind"] == "party-return":          # a return is the product: it outranks any other kind's label
            d["kind"], d["year"], d["label"] = c["kind"], c["year"], label_of(path)
    log(f"pageset: {len(docs)} distinct documents ({len(cands) - len(docs)} names are duplicates by hash)")
    # the named cases, by name, kept by hash
    for case, kind, year, rx in NAMED_CASES:
        hits = [d for d in docs.values() if d["kind"] == kind and d["year"] == year and any(rx.search(n) for n in d["names"])]
        for d in hits:
            d["named_case"], d["all_pages"] = case, True
        log(f"pageset: named case {case}: {len(hits)} document(s)")
    # selection: every party return; the other kinds sampled per kind-year, scans first, then by hash order
    chosen = []
    strata: dict = defaultdict(list)
    for d in docs.values():
        if d["kind"] == "party-return" or d["named_case"]:
            chosen.append(d)
        else:
            strata[(d["kind"], d["year"])].append(d)
    rank = {"scan": 0, "mixed": 1, "image-first-page": 2, "raster": 3, "text": 4}
    for (kind, year), ds in sorted(strata.items()):
        ds.sort(key=lambda d: (rank.get(d["shape"], 9), d["sha256"]))
        rasters = [d for d in ds if d["shape"] == "raster"][:RASTER_SAMPLE]
        rest = [d for d in ds if d["shape"] != "raster"]
        # half from the scan end, half spread across the rest so text documents are keys too
        n = SAMPLE_PER_STRATUM
        head = rest[: n // 2]
        tail = rest[n // 2:]
        step = max(1, len(tail) // max(1, n - len(head))) if tail else 1
        spread = tail[::step][: n - len(head)]
        chosen += rasters + head + spread
    for d in chosen:
        d["selected_pages"] = pick_pages(d)
    chosen.sort(key=lambda d: (d["kind"], d["year"] or 0, d["sha256"]))
    out_path = out_path or PAGESET
    stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "pageset-header", "version": 1, "built_at": stamp, "window_from": WINDOW_FROM,
                            "page_text_min": PAGE_TEXT_MIN, "profile_page_min": PROFILE_PAGE_MIN,
                            "text_key_pages": TEXT_KEY_PAGES, "sample_per_stratum": SAMPLE_PER_STRATUM,
                            "candidates": len(cands), "distinct": len(docs), "documents": len(chosen),
                            "pages": sum(len(d["selected_pages"]) for d in chosen)}) + "\n")
        for d in chosen:
            rec = {k: d[k] for k in ("sha256", "bytes", "kind", "year", "label", "names", "pages", "shape", "named_case")}
            rec["chars"] = {str(p): c for p, c in sorted(d["chars"].items())}
            rec["selected_pages"] = d["selected_pages"]
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    log(f"pageset: {len(chosen)} documents, {sum(len(d['selected_pages']) for d in chosen)} pages → {out_path}")
    return chosen


def header(path: str = None) -> dict:
    with open(path or PAGESET, encoding="utf-8") as f:
        return json.loads(f.readline())


def load(path: str = None) -> list[dict]:
    out = []
    with open(path or PAGESET, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if r.get("kind") != "pageset-header":
                    out.append(r)
    return out


def twenty(path: str = None, n: int = TWENTY) -> list[tuple[str, int]]:
    """A fixed subset of pages for comparing two compressions of one model:
    half scan pages, half text pages, spread across kinds, chosen by hash
    order so the choice is the same on every run."""
    docs = sorted(load(path), key=lambda d: d["sha256"])
    scans = [(d["sha256"], p["page"]) for d in docs for p in d["selected_pages"] if p["read_from"] == "pixels"]
    texts = [(d["sha256"], p["page"]) for d in docs for p in d["selected_pages"] if p["read_from"] == "text"]
    half = n // 2

    def spread(items, k):
        if not items:
            return []
        step = max(1, len(items) // k)
        return items[::step][:k]
    return spread(scans, half) + spread(texts, n - half)


def identity(path: str = None) -> str:
    """The set's own hash, so a reading can say which page set it was made under."""
    return sha256_file(path or PAGESET)[:16]


def locate(sha256: str, path: str = None, staging: str = None) -> str | None:
    """Where the bytes are: the first of the document's names that still
    exists, under the old folder (read-only), or the document store."""
    for d in load(path):
        if d["sha256"] == sha256:
            for n in d["names"]:
                p = os.path.join(staging or STAGING, n)
                if os.path.exists(p):
                    return p
    try:
        from support.docstore import landing
        p = landing.path_for(sha256) if hasattr(landing, "path_for") else None
        if p and os.path.exists(p):
            return p
    except Exception:  # noqa: BLE001
        pass
    return None


def read_bytes(sha256: str, path: str = None) -> bytes:
    p = locate(sha256, path)
    if not p:
        raise FileNotFoundError(f"no bytes for {sha256[:12]}")
    with open(p, "rb") as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError(f"the bytes under the name do not hash to {sha256[:12]}: the name moved")
    return data


def show(path: str = None) -> str:
    docs = load(path)
    h = header(path)
    lines = [f"page set v{h['version']} built {h['built_at']}: {h['documents']} documents, {h['pages']} pages "
             f"(from {h['candidates']} files, {h['distinct']} distinct)"]
    by = Counter((d["kind"], d["year"], d["shape"]) for d in docs)
    pages = Counter()
    for d in docs:
        for p in d["selected_pages"]:
            pages[(d["kind"], p["read_from"])] += 1
    for (kind, year, shape), n in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0, kv[0][2])):
        lines.append(f"  {kind:22s} {year} {shape:17s} {n:4d}")
    lines.append("pages by kind and how they are read:")
    for (kind, how), n in sorted(pages.items()):
        lines.append(f"  {kind:22s} {how:7s} {n:5d}")
    between = sum(1 for d in docs for p in d["selected_pages"] if PROFILE_PAGE_MIN <= p["chars"] < PAGE_TEXT_MIN)
    lines.append(f"pages between the profile's {PROFILE_PAGE_MIN} and the contract's {PAGE_TEXT_MIN} characters: {between}")
    lines.append("named cases: " + ", ".join(f"{d['named_case']}={d['sha256'][:12]}" for d in docs if d["named_case"]))
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "show"
    if cmd == "build":
        build()
        print(show())
        return 0
    if cmd == "show":
        print(show())
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
