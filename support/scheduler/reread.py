"""THE RE-READ JOB TYPE (plan step 2.14): re-reading a set of documents after
a reader, a document profile or a rule changes is queued like any other
bulk job, cut into pieces (one per document), and each new reading is
COMPARED with what it would replace before anything lands. Nobody fires it
by hand (ruling 45): a session or a lane queues it.

One piece: fetch the document's bytes from the document store by hash;
take the declaration page's text layer (or, for `--pixels`, the page
rendered at the profile's dots per inch through the page-reader profile);
ask the model on the card the worker was given (`QV4_MODEL_URL`,
`QV4_MODEL`; the client refuses an answer from any other model) for the
declared total; store the reading in the reader store under the model and
its settings (ruling 50: one reading per document, model and settings,
never overwritten); and write one comparison line to
`<live>/scheduler/rereads.jsonl`: the published figure, the new figure,
equal or not. Nothing here publishes: the comparison is the output, and a
lane decides what to do with a difference.

No page text, no donor and no address is ever printed: counts, hashes,
totals and the verdict only (hard limits 11, 15).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import tempfile

from support import modelclient
from support import profiles as doc_profiles
from support import reader as rd
from support.docread import pagereader, pages
from support.docstore import landing
from support.scheduler import LIVE

READER = "support.scheduler.reread 1"
LANE = "reread"
PROFILE = "ec-party-return-text"
LEDGER = os.path.join(LIVE, "scheduler", "rereads.jsonl")
ASK = ("\n\nFrom the DECLARATION page text below, answer with ONE JSON object and nothing else: "
       '{"declared_total": <number or null>, "parts": {"A": <number or null>, "C": ..., "D": ..., "F": ..., "G": ...}}. '
       "Figures as plain numbers with no currency sign and no thousands separators; NIL is 0; a part the page does "
       "not state is null.\n\nPAGE TEXT:\n")
PAGE = 1


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.\-]", "", str(v))
    try:
        return float(s) if s else None
    except ValueError:
        return None


def parse_answer(text: str) -> dict:
    """The JSON object in a model's answer, however it is wrapped."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        body = json.loads(m.group(0))
    except ValueError:
        return {}
    if not isinstance(body, dict):
        return {}
    parts = body.get("parts") if isinstance(body.get("parts"), dict) else {}
    return {"declared_total": _num(body.get("declared_total")), "parts": {k: _num(v) for k, v in parts.items()}}


def digits(x) -> str:
    """A figure as its digits only, for finding it in page text."""
    if x is None:
        return ""
    s = f"{float(x):.2f}"
    return s[:-3] if s.endswith(".00") else s.replace(".", "")


def published(conn, sha256: str) -> dict | None:
    row = conn.execute("SELECT party, year, declared_total, page FROM pub.party_return_totals WHERE document = %s",
                       (sha256,)).fetchone()
    return {"party": row[0], "year": row[1], "declared_total": float(row[2]) if row[2] is not None else None, "page": row[3]} if row else None


def read_text_page(data: bytes, page: int) -> str:
    return pages.page_text(data, page)


def ask_model(text: str, prompt: str, url: str, model: str, post=None) -> tuple[dict, str]:
    out = modelclient.chat(url, lane=LANE, model=model,
                           messages=[{"role": "system", "content": prompt}, {"role": "user", "content": ASK + text[:40000]}],
                           extra={"temperature": 0.0, "max_tokens": 400}, timeout=600, post=post)
    answer = (out["choices"][0]["message"]["content"] or "").strip()
    return parse_answer(answer), out.get("model") or model


def piece(sha256: str, *, conn, url: str, model: str, profile: str = PROFILE, pixels: bool = False, store: rd.Store = None,
          ledger: str = None, post=None, run_id: str = "", dpi: int = 300) -> dict:
    """One document re-read and compared. Returns the comparison line."""
    store = store or rd.Store()
    prof = doc_profiles.profile(profile) or {}
    version = int(prof.get("version") or 0)
    prompt = prof.get("prompt") or ""
    data = landing.read_bytes(sha256)
    old = published(conn, sha256)
    page = (old or {}).get("page") or PAGE
    settings = {"prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()[:16], "ask_sha": hashlib.sha256(ASK.encode()).hexdigest()[:16],
                "temperature": 0.0, "max_tokens": 400}
    if pixels:
        with tempfile.TemporaryDirectory() as td:
            png = pagereader.render(data, page, td, dpi)
            if not png:
                raise RuntimeError("the page could not be rendered")
            text = pagereader.read_page(png, url=url, model=model, post=post)
        settings = {"dpi": dpi, "prompt": pagereader.PROMPT}
        read_from, served = "pixels", model
        found = digits((old or {}).get("declared_total"))
        new_total = None
        equal = bool(found) and found in re.sub(r"[,\s$]", "", text)
        answer = {"ocr_chars": len(text), "published_total_found_in_text": equal}
        stored_text = text
    else:
        text = read_text_page(data, page)
        if pages.is_thin(text):
            raise RuntimeError(f"page {page} has no usable text layer: needs the page-reader half (qv4-reread-pages)")
        answer, served = ask_model(text, prompt, url, model, post=post)
        read_from = "text"
        new_total = answer.get("declared_total")
        equal = old is not None and new_total is not None and old["declared_total"] is not None \
            and abs(new_total - old["declared_total"]) < 0.005
        stored_text = json.dumps(answer, sort_keys=True)
    reading = rd.Reading(sha256, page, READER, served, settings, profile, version, read_from, stored_text,
                         rows=[{"declared_total": new_total}] if not pixels else [],
                         checks={"published": (old or {}).get("declared_total"), "equal": equal},
                         made_at=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
    store.put(reading)
    line = {"at": reading.made_at, "run_id": run_id, "document": sha256, "page": page, "profile": f"{profile}@{version}",
            "model": served, "read_from": read_from, "published": (old or {}).get("declared_total"),
            "party": (old or {}).get("party"), "year": (old or {}).get("year"), "new": new_total if not pixels else None,
            "equal": equal, "key": reading.key}
    ledger = ledger or LEDGER
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    return line


def summary(ledger: str = None) -> dict:
    """What the re-reads found: per model, equal and different counts."""
    out: dict[str, dict] = {}
    try:
        with open(ledger or LEDGER, encoding="utf-8") as f:
            for l in f:
                try:
                    r = json.loads(l)
                except ValueError:
                    continue
                s = out.setdefault(r.get("model") or "?", {"equal": 0, "different": 0, "unpublished": 0})
                if r.get("published") is None:
                    s["unpublished"] += 1
                elif r.get("equal"):
                    s["equal"] += 1
                else:
                    s["different"] += 1
    except OSError:
        pass
    return out
