"""THE EMBED JOB (`qv4-embed`, plan step 2.15 "Embedding: search"): one
piece per document. The document's text pages are cut into chunks that fit
the embedding profile's per-request context, each chunk goes through the
model client's `embed()` to the card that holds the profile, and the
vectors are stored as a READING in the reader store, keyed by the
document's hash, the served model and the chunking settings (ruling 50:
every model reading is kept and replayed, never re-made by accident). A
page with no usable text layer is skipped and counted: embedding pixels
is the page reader's job first (`qv4-reread-pages`), then this one.

Nothing here decides what search does with the vectors; search (a later
step) reads them from the store by key. One search query embeds on the
processor and never comes through here.

`embed()` is the model client's (docs/contracts/model-client.md); until
the integrator lands it, the piece fails with that one line.
"""
from __future__ import annotations

import datetime as dt
import json
import os

from support import reader as rd
from support.docread import pages
from support.docstore import landing
from support.scheduler import LIVE

READER = "support.scheduler.embed 1"
PROFILE = "embedding"
LANE = "search"
CHUNK_CHARS = 1500          # ~400 tokens of English; well inside the profile's 8,192-token request
OVERLAP_CHARS = 200
LEDGER = os.path.join(LIVE, "scheduler", "embeds.jsonl")


def chunks(text: str, size: int = CHUNK_CHARS, overlap: int = OVERLAP_CHARS) -> list[dict]:
    """Windows of `size` characters stepping by `size - overlap`, on the
    page's text as it is; a page shorter than one window is one chunk.
    Each chunk knows its offset so a hit can be shown in its page."""
    text = text or ""
    if not text.strip():
        return []
    out, step, i = [], max(1, size - overlap), 0
    while i < len(text):
        piece = text[i:i + size]
        if piece.strip():
            out.append({"offset": i, "chars": len(piece), "text": piece})
        if i + size >= len(text):
            break
        i += step
    return out


def embed_fn():
    from support import modelclient
    fn = getattr(modelclient, "embed", None)
    if fn is None:
        raise RuntimeError("support.modelclient has no embed(): a contract change the integrator lands "
                           "(merge request scheduler-2-embed, the patch beside it)")
    return fn


def piece(sha256: str, *, url: str, model: str, store: rd.Store = None, embed=None, ledger: str = None, run_id: str = "",
          max_pages: int = None, size: int = CHUNK_CHARS, overlap: int = OVERLAP_CHARS, data: bytes = None) -> dict:
    """One document embedded page by page; returns the summary line."""
    store = store or rd.Store()
    embed = embed or embed_fn()
    data = data if data is not None else landing.read_bytes(sha256)
    texts = pages.text_pages(data, max_pages=max_pages)
    settings = {"chunk_chars": size, "overlap_chars": overlap, "reader": READER}
    made, thin, replayed, dims = 0, 0, 0, 0
    for page in sorted(texts):
        text = texts[page]
        if pages.is_thin(text):
            thin += 1
            continue
        key = rd.reading_key(sha256, page, model, settings, PROFILE, 0)
        if store.has(key):
            replayed += 1
            continue
        cs = chunks(text, size, overlap)
        vectors = embed(url, lane=LANE, model=model, texts=[c["text"] for c in cs])
        dims = len(vectors[0]) if vectors else dims
        rows = [{"chunk": i, "offset": c["offset"], "chars": c["chars"], "vector": v} for i, (c, v) in enumerate(zip(cs, vectors))]
        reading = rd.Reading(sha256, page, READER, model, settings, PROFILE, 0, "text", "", rows=rows,
                             checks={"chunks": len(cs), "dims": dims},
                             made_at=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
        store.put(reading)
        made += 1
    line = {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "run_id": run_id, "document": sha256,
            "model": model, "pages": len(texts), "embedded": made, "replayed": replayed, "thin": thin, "dims": dims}
    ledger = ledger or LEDGER
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    return line
