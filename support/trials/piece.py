"""ONE PIECE OF THE TRIAL (plan steps 3.5 and 3.6): one document of the page
set, every selected page rendered and read by the page reader the worker
has put on this box's card, each reading stored against the document's
hash, the page, the model, its build and settings, and the document
profile's slug and version (condition 2), and one line per page in the
trial's ledger and its scratch table. Nothing here publishes.

    python -m support.trials piece SHA256        run by the scheduler (QV4_MODEL_URL, QV4_MODEL, QV4_PROFILE, QV4_ARGS)

QV4_ARGS (the job's args, JSON): `pass` ("one" | "two" | "twenty"),
`dpi` (an override; the document profile's otherwise), `pages`
("selected", the page set's choice, or "all"), `old_cache` (compare a
GLM-OCR reading at 200 dpi with the old estate's cached page text, keyed
by the rendered page's own bytes, which is how pass one matches the
readings the old estate holds by hash and page).

No page text, no donor and no address is printed: hashes, counts and
seconds only (hard limits 11, 15). The reading itself goes to the reader
store, where the fast tier replays it.
"""
from __future__ import annotations

import base64
import datetime as dt
import difflib
import hashlib
import json
import os
import sys
import tempfile
import time

from support import modelclient
from support import profiles as doc_profiles
from support import reader as rd
from support.docread import pagereader
from support.trials import pageset, readers

READER = "support.trials 1"
LANE = "trial"
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
LEDGER = os.path.join(LIVE, "trials", "pages.jsonl")
OLD_CACHE = os.path.join(pageset.OLD_LIVE, "var", "ocr-cache")
SCHEMA = "scratch_trial"
OLD_DPI = 200                 # the old estate rendered at 200 (ec_pageread.vision_ocr.DPI)

# the document profile a page-set document is read under (condition 1): by kind and shape
PROFILE_FOR = {
    ("party-return", "scan"): "ec-party-return-scan", ("party-return", "mixed"): "ec-party-return-scan",
    ("party-return", "image-first-page"): "ec-party-return-image-declaration", ("party-return", "text"): "ec-party-return-text",
    ("party-return", "raster"): "ec-party-return-scan",
    ("candidate-return", None): "ec-candidate-expenses-return", ("disclosure-20k", None): "ec-donation-disclosure-20k",
    ("party-expenses", None): "ec-party-expenses-return", ("financial-statements", None): "ec-party-financial-statements",
    ("promoter-return", None): "ec-promoter-expenses-return",
}
TABLES = f"""
CREATE SCHEMA IF NOT EXISTS {SCHEMA};
CREATE TABLE IF NOT EXISTS {SCHEMA}.page_reads (
    key             text PRIMARY KEY,
    document        text NOT NULL,
    page            int NOT NULL,
    reader          text NOT NULL,
    model           text NOT NULL,
    level           text,
    dpi             int,
    prompt_sha      text,
    profile         text,
    profile_version int,
    read_from       text,
    pass            text,
    chars           int,
    seconds         real,
    ok              boolean NOT NULL,
    error           text,
    old_cache       text,
    old_equal       boolean,
    old_ratio       real,
    image_sha       text,
    run_id          text,
    at              timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS page_reads_doc ON {SCHEMA}.page_reads (document, page);
CREATE INDEX IF NOT EXISTS page_reads_reader ON {SCHEMA}.page_reads (reader, pass);
"""


def doc_profile(doc: dict) -> tuple[str, int, int]:
    """The document profile's slug, version and dots per inch for a page-set document."""
    if doc.get("named_case") == "vision-nz-2020-handwritten":
        slug = "ec-party-return-handwritten"
    else:
        slug = PROFILE_FOR.get((doc["kind"], doc["shape"])) or PROFILE_FOR.get((doc["kind"], None)) or "default"
    prof = doc_profiles.profile(slug) or {}
    dpi = int(((prof.get("ocr") or {}).get("dpi")) or 300)
    return slug, int(prof.get("version") or 0), dpi


def old_cached_text(png_path: str, model_name: str = "glm-ocr") -> str | None:
    """The old estate's reading of this very page image, if it has one:
    keyed by the sha256 of the PNG bytes (ec_pageread.vision_ocr._cache_path)."""
    with open(png_path, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    p = os.path.join(OLD_CACHE, f"{model_name}-{h}.txt")
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def image_sha(png_path: str) -> str:
    with open(png_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def compare_texts(a: str, b: str) -> tuple[bool, float]:
    """Equal after whitespace normalisation, and a similarity ratio."""
    na, nb = " ".join((a or "").split()), " ".join((b or "").split())
    if na == nb:
        return True, 1.0
    return False, round(difflib.SequenceMatcher(None, na, nb, autojunk=False).ratio(), 4)


def _conn():
    import support.db as db
    conn = db.connect(db.OWNER_KEY, "querynz_v4", autocommit=True)
    conn.execute(TABLES)
    return conn


def _row(conn, line: dict) -> None:
    cols = ["key", "document", "page", "reader", "model", "level", "dpi", "prompt_sha", "profile", "profile_version", "read_from",
            "pass", "chars", "seconds", "ok", "error", "old_cache", "old_equal", "old_ratio", "image_sha", "run_id"]
    vals = [line.get(c) for c in cols]
    conn.execute(f"INSERT INTO {SCHEMA}.page_reads ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))}) "
                 f"ON CONFLICT (key) DO UPDATE SET chars = EXCLUDED.chars, seconds = EXCLUDED.seconds, ok = EXCLUDED.ok, "
                 f"error = EXCLUDED.error, old_cache = EXCLUDED.old_cache, old_equal = EXCLUDED.old_equal, "
                 f"old_ratio = EXCLUDED.old_ratio, image_sha = EXCLUDED.image_sha, run_id = EXCLUDED.run_id, at = now()", vals)


def _ledger(line: dict, ledger: str = None) -> None:
    ledger = ledger or LEDGER
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


def read_page(reader: readers.Reader, png: str, url: str, post=None, timeout: float = 900.0) -> tuple[str, str]:
    with open(png, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    out = modelclient.chat(url, lane=LANE, model=reader.model,
                           messages=readers.messages(reader, b64, pagereader.media_type(png)),
                           extra=readers.extra(reader), timeout=timeout, post=post)
    return (out["choices"][0]["message"]["content"] or "").strip(), out.get("model") or reader.model


def run(sha256: str, *, reader: readers.Reader, url: str, args: dict = None, store: rd.Store = None, conn=None,
        post=None, run_id: str = "", log=print, ledger: str = None, doc: dict = None, server_build: str = None) -> dict:
    """Every selected page of one document through one reader. Returns
    counts: pages read, replayed, failed, and the old-cache tally."""
    args = args or {}
    store = store or rd.Store()
    doc = doc or next((d for d in pageset.load() if d["sha256"] == sha256), None)
    if doc is None:
        raise LookupError(f"{sha256[:12]} is not in the page set")
    slug, version, prof_dpi = doc_profile(doc)
    dpi = int(args.get("dpi") or prof_dpi)
    which = args.get("pages") or "selected"
    want_old = bool(args.get("old_cache", reader.name == readers.INCUMBENT and dpi == OLD_DPI))
    pass_name = str(args.get("pass") or "one")
    if isinstance(args.get("twenty"), dict) and args["twenty"].get(sha256):
        pages = [int(p) for p in args["twenty"][sha256]]          # the compression comparison: its pages of this document
    elif which == "all":
        pages = list(range(1, int(doc["pages"]) + 1))
    elif isinstance(which, list):
        pages = [int(p) for p in which]
    else:
        pages = [p["page"] for p in doc["selected_pages"]]
    data = pageset.read_bytes(sha256)
    settings = readers.settings(reader, dpi, server_build)
    tally = {"document": sha256, "reader": reader.name, "pages": len(pages), "read": 0, "replayed": 0, "failed": 0,
             "old_hits": 0, "old_equal": 0, "seconds": 0.0}
    with tempfile.TemporaryDirectory() as td:
        for p in pages:
            key = rd.reading_key(sha256, p, reader.model, settings, slug, version)
            if store.has(key):
                tally["replayed"] += 1
                continue
            t0 = time.monotonic()
            png = pagereader.render(data, p, td, dpi)
            line = {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "key": key, "document": sha256,
                    "page": p, "reader": reader.name, "model": reader.model, "level": reader.level, "dpi": dpi,
                    "prompt_sha": reader.prompt_sha, "profile": slug, "profile_version": version, "read_from": "pixels",
                    "pass": pass_name, "run_id": run_id, "ok": False, "chars": 0, "seconds": 0.0, "error": None,
                    "old_cache": None, "old_equal": None, "old_ratio": None, "image_sha": None}
            if not png:
                line["error"] = "the page could not be rendered"
                tally["failed"] += 1
            else:
                line["image_sha"] = image_sha(png)
                try:
                    text, served = read_page(reader, png, url, post=post)
                    if not text.strip():
                        raise RuntimeError("the reader returned nothing")
                    line.update(ok=True, chars=len(text))
                except Exception as e:  # noqa: BLE001 — recorded; the page is unread
                    line["error"] = f"{type(e).__name__}: {str(e)[:160]}"
                    tally["failed"] += 1
                    text, served = "", reader.model
                if line["ok"] and want_old:
                    old = old_cached_text(png, "glm-ocr")
                    if old is None:
                        line["old_cache"] = "miss"
                    else:
                        eq, ratio = compare_texts(text, old)
                        line.update(old_cache="hit", old_equal=eq, old_ratio=ratio)
                        tally["old_hits"] += 1
                        tally["old_equal"] += int(eq)
                if line["ok"]:
                    reading = rd.Reading(sha256, p, READER, served, settings, slug, version, "pixels", text,
                                         checks={"trial_pass": pass_name, "old_cache": line["old_cache"], "old_equal": line["old_equal"],
                                                 "old_ratio": line["old_ratio"], "image_sha": line["image_sha"], "seconds": None},
                                         made_at=line["at"])
                    store.put(reading)
                    tally["read"] += 1
            line["seconds"] = round(time.monotonic() - t0, 2)
            tally["seconds"] += line["seconds"]
            _ledger(line, ledger)
            if conn is not None:
                _row(conn, line)
            log(f"trial: {sha256[:12]} p{p} {reader.name}@{dpi}dpi: {'ok' if line['ok'] else 'FAILED'} {line['chars']} chars "
                f"{line['seconds']}s" + (f" old:{line['old_cache']}{'=' if line['old_equal'] else '≠' if line['old_cache'] == 'hit' else ''}"
                                        if want_old else ""))
    return tally


def old_cache_check(n_docs: int = 40, pages_per_doc: int = 2, dpi: int = OLD_DPI, log=print) -> dict:
    """Does the join to the old estate's page cache work on real pages?
    Render scan pages at the old dots per inch, hash the image, look for
    the old text. Counts only; nothing is read by a model."""
    from collections import Counter
    docs = [d for d in pageset.load() if d["kind"] == "party-return" and d["shape"] in ("scan", "mixed")]
    c = Counter()
    with tempfile.TemporaryDirectory() as td:
        for d in docs[:n_docs]:
            data = pageset.read_bytes(d["sha256"])
            for p in [p["page"] for p in d["selected_pages"] if p["read_from"] == "pixels"][:pages_per_doc]:
                png = pagereader.render(data, p, td, dpi)
                if not png:
                    c["render-failed"] += 1
                    continue
                c["hit" if old_cached_text(png) is not None else "miss"] += 1
                os.remove(png)
    log(f"old cache at {dpi} dpi: {dict(c)} over {sum(c.values())} pages of {min(n_docs, len(docs))} documents")
    return dict(c)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    sha = argv[0]
    url = os.environ.get("QV4_MODEL_URL")
    profile = os.environ.get("QV4_PROFILE")
    if not url or not profile:
        print("trial: no card: QV4_MODEL_URL and QV4_PROFILE come from the worker", file=sys.stderr)
        return 3
    reader = readers.by_profile(profile)
    if reader is None:
        print(f"trial: no reader is served by profile {profile!r}", file=sys.stderr)
        return 3
    if os.environ.get("QV4_MODEL") and os.environ["QV4_MODEL"] != reader.model:
        print(f"trial: the card holds {os.environ['QV4_MODEL']!r}, the reader wants {reader.model!r}", file=sys.stderr)
        return 3
    try:
        args = json.loads(os.environ.get("QV4_ARGS") or "{}")
    except ValueError:
        args = {}
    conn = None
    try:
        conn = _conn()
    except Exception as e:  # noqa: BLE001 — the ledger still records; the table is a convenience
        print(f"trial: no scratch table ({type(e).__name__}); the ledger alone records this piece", file=sys.stderr)
    tally = run(sha, reader=reader, url=url, args=args, conn=conn, run_id=os.environ.get("QV4_RUN_ID", ""))
    print(f"trial: {sha[:12]} {reader.name}: {tally['read']} read, {tally['replayed']} replayed, {tally['failed']} failed, "
          f"old cache {tally['old_hits']} hits {tally['old_equal']} equal, {tally['seconds']:.0f}s")
    return 1 if tally["failed"] and not tally["read"] else 0


if __name__ == "__main__":
    sys.exit(main())
