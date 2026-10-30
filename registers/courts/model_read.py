"""The text reader's reading of a court document (ruling 128): every person
and body the document names with the role the text gives each (party,
counsel, witness, judge, company, agency), counsel for each party, and a
one-line summary. Flash-Next (profile `text-reader`, the standing server;
ruling 121) through the model client, which names the model and refuses an
answer from any other; one reading per document, stamped with the reader's
version, the served model and the prompt's hash, stored by the document's
hash in the reader store and replayed from there by every load (ruling 50:
the fast tier calls no model). A document without a stored reading is
"waiting: text reader" in `courts.documents`; this module's job reads it.

    python -m registers.courts.model_read --pieces [--database D]   the documents waiting, one key a line (for the integrator's enqueue)
    python -m registers.courts.model_read --piece SHA256            one piece of qv4-courts-read (QV4_MODEL_URL, QV4_MODEL from the worker)
    python -m registers.courts.model_read --piece SHA256 --wait     from a session: wait for the standing server to come back

The reading's text goes to the model and nowhere else (hard limit 10: the
server is on this box; limit 11: no page text is printed or logged here).
A reading the model answers with no JSON object is not stored: the piece
fails, the job's alarm says so, and the document stays waiting.
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error

from support import modelclient
from support import reader as rd

READER = "registers.courts.model_read 1"
LANE = "courts"
TEXT_MODEL = os.environ.get("QV4_COURTS_TEXT_MODEL") or "qwen4exp"      # profiles.toml [profiles.text-reader] model
URL = os.environ.get("QV4_MODEL_URL") or "http://127.0.0.1:8060/v1/chat/completions"
HEAD_CHARS, TAIL_CHARS = 36000, 6000
MAX_TOKENS = 4096
ROLES = ("party", "counsel", "witness", "judge", "company", "agency", "other")
KINDS = ("person", "body")
PROMPT = (
    "You read one New Zealand court document: a judgment, a media release, a hearing transcript, counsel's submissions, "
    "a case synopsis or a court's case web page. Answer with ONE JSON object and nothing else:\n"
    '{"summary": "<one sentence, at most 40 words, saying what the document is and what it decides or concerns>",\n'
    ' "people": [{"name": "<the name exactly as the document prints it>", "kind": "person" | "body", '
    '"role": "party" | "counsel" | "witness" | "judge" | "company" | "agency" | "other", '
    '"role_text": "<the role in the document\'s own words, e.g. appellant, counsel for the respondent, expert witness, sentencing judge>", '
    '"for": "<for counsel: the party acted for, as the document names it; otherwise null>"}]}\n'
    "Rules. List every person and every body (company, trust, iwi, public agency, court) the document names, each once, "
    "with the role the text gives it; a judge is role judge; a lawyer appearing is role counsel with the party in \"for\"; "
    "a company or incorporated body is kind body, role company; a government department, council, commission or police "
    "is kind body, role agency; a party to the case is role party whatever its kind. Keep initials, honorifics and "
    "spelling as printed; never expand an initial or a pseudonym; never add an address, an age or a date of birth; "
    "never name anyone the text does not name. The summary describes the document in neutral words and names nobody.")
_JSON = re.compile(r"\{.*\}", re.S)


def settings(prompt: str = PROMPT) -> dict:
    return {"prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()[:16], "head_chars": HEAD_CHARS,
            "tail_chars": TAIL_CHARS, "temperature": 0.0, "max_tokens": MAX_TOKENS, "thinking": False}


def key_for(sha256: str, profile: str, version: int, model: str = TEXT_MODEL) -> str:
    return rd.reading_key(sha256, 1, model, settings(), profile, version)


def excerpt(texts: dict) -> str:
    """The document's text for the model: every page in order, the head and
    the tail when it is long (a judgment's caption, counsel and judges are at
    the front; its result and the names it ends on at the back)."""
    body = "\n\n".join(f"[page {p}]\n{texts[p]}" for p in sorted(texts) if (texts[p] or "").strip())
    if len(body) <= HEAD_CHARS + TAIL_CHARS:
        return body
    return body[:HEAD_CHARS] + "\n\n[… pages omitted …]\n\n" + body[-TAIL_CHARS:]


def parse_answer(text: str):
    """The JSON object in the model's answer, checked: None when there is no
    usable object (the reading is then not stored)."""
    m = _JSON.search(text or "")
    if not m:
        return None
    try:
        body = json.loads(m.group(0))
    except ValueError:
        return None
    if not isinstance(body, dict) or not isinstance(body.get("people"), list):
        return None
    people = []
    for item in body["people"]:
        if not isinstance(item, dict):
            continue
        name = re.sub(r"\s+", " ", str(item.get("name") or "")).strip()
        if not name:
            continue
        role = str(item.get("role") or "other").strip().lower()
        role = role if role in ROLES else "other"
        kind = str(item.get("kind") or "").strip().lower()
        if kind not in KINDS:
            kind = "body" if role in ("company", "agency") else "person"
        for_party = item.get("for")
        for_party = re.sub(r"\s+", " ", str(for_party)).strip() if for_party not in (None, "", "null") else None
        people.append({"name": name, "kind": kind, "role": role,
                       "role_text": (re.sub(r"\s+", " ", str(item.get("role_text") or "")).strip() or None),
                       "for": for_party})
    summary = re.sub(r"\s+", " ", str(body.get("summary") or "")).strip() or None
    return {"summary": summary, "people": people}


def ask(texts: dict, *, url: str, model: str, post=None, request: dict = None, timeout: float = 900.0) -> tuple:
    """(parsed answer or None, served model). One call; the client reads the
    served model back and refuses another."""
    extra = {"temperature": 0.0, "max_tokens": MAX_TOKENS, "chat_template_kwargs": {"enable_thinking": False}}
    for k, v in (request or {}).items():
        if k not in ("temperature", "max_tokens"):
            extra.setdefault(k, v)
    out = modelclient.chat(url, lane=LANE, model=model,
                           messages=[{"role": "system", "content": PROMPT},
                                     {"role": "user", "content": "DOCUMENT TEXT:\n\n" + excerpt(texts)}],
                           extra=extra, timeout=timeout, post=post)
    answer = (out["choices"][0]["message"]["content"] or "").strip()
    return parse_answer(answer), out.get("model") or model


def read_one(sha256: str, texts: dict, *, profile: str, version: int, url: str = None, model: str = None,
             store: rd.Store = None, post=None, request: dict = None) -> dict:
    """The document read once and stored; a stored reading is replayed, never
    remade. Raises when the model gives no usable answer (nothing stored)."""
    store = store or rd.Store()
    model = model or TEXT_MODEL
    key = key_for(sha256, profile, version, model)
    if store.has(key):
        return {**_unpack(store.get(key)), "replayed": True}
    parsed, served = ask(texts, url=url or URL, model=model, post=post, request=request)
    if parsed is None:
        raise RuntimeError(f"the text reader answered with no usable JSON object for {sha256[:12]}: not stored")
    reading = rd.Reading(sha256, 1, READER, served, settings(), profile, version, "text",
                         json.dumps(parsed, ensure_ascii=False, sort_keys=True), rows=parsed["people"],
                         checks={"people": len(parsed["people"]), "summary": bool(parsed["summary"])},
                         made_at=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
    store.put(reading)
    return {**_unpack(reading), "replayed": False}


def _unpack(reading: rd.Reading) -> dict:
    parsed = parse_answer(reading.text) or {"summary": None, "people": []}
    return {"summary": parsed["summary"], "people": parsed["people"], "model": reading.model, "reader": reading.reader,
            "made_at": reading.made_at, "key": reading.key}


def stored(sha256: str, profile: str, version: int, store: rd.Store, model: str = TEXT_MODEL):
    """The stored reading, unpacked, or None: the load replays and never asks."""
    key = key_for(sha256, profile, version, model)
    if not store.has(key):
        return None
    return _unpack(store.get(key))


def people_rows(sha256: str, reading: dict, doc: dict, profile: str, version: int, now: str) -> list:
    """One row per person or body the reading names, in the reading's order."""
    from registers.courts.read import KIND_OF
    out = []
    for n, p in enumerate(reading["people"], 1):
        out.append({"key": f"{sha256}/person/{n}", "name": p["name"], "kind": p["kind"], "role": p["role"],
                    "role_text": p.get("role_text"), "for_party": p.get("for"), "citation": doc.get("citation"),
                    "case_slug": doc.get("case_slug"), "document_kind": KIND_OF.get(profile, "document"),
                    "dated": doc.get("dated"), "withheld": False, "document": sha256, "page": 1,
                    "place": f"text reader, name {n}", "read_from": "text", "reader": reading["reader"],
                    "model": reading["model"], "profile": profile, "profile_version": version, "loaded_at": now})
    return out


def kept_under_suppression(row: dict) -> bool:
    """Under a suppression every name is withheld but the court's officers
    (judges, counsel), a public agency and the Crown (hard limit 16: the row
    stays, the name goes)."""
    from registers.courts.caption import CROWN
    if row["role"] in ("judge", "counsel", "agency"):
        return True
    return bool(CROWN.match((row.get("name") or "").upper()))


# ── the job ───────────────────────────────────────────────────────────────────────────────────────────────────
def waiting(conn, schema: str = "courts") -> list:
    """The documents waiting on the text reader, the kinds people ask about
    first: judgments, releases, transcripts, submissions, synopses, then case
    pages. [(sha256, profile, profile_version, url)]."""
    from registers.courts.read import WAIT_TEXT, JUDGMENT_SLUGS, RELEASE, TRANSCRIPT, SUBMISSION, SYNOPSIS, CASE_PAGE
    rank = {**{s: 0 for s in JUDGMENT_SLUGS}, RELEASE: 1, TRANSCRIPT: 2, SUBMISSION: 3, SYNOPSIS: 4, CASE_PAGE: 5}
    rows = conn.execute(f"SELECT DISTINCT document, profile, profile_version, url FROM {schema}.documents "
                        "WHERE outcome = %s AND document IS NOT NULL", (WAIT_TEXT,)).fetchall()
    return sorted(rows, key=lambda r: (rank.get(r[1], 9), r[3]))


def piece(sha256: str, *, url: str, model: str, store: rd.Store = None, conn=None, post=None, request: dict = None,
          wait_s: float = 0.0) -> dict:
    """One piece of `qv4-courts-read`: the document's text (text layer, or
    its stored page readings), its profile as the load recognised it, one
    call, one stored reading. Counts and the hash only."""
    from support.docstore.landing import read_bytes
    from registers.courts import read as R
    store = store or rd.Store()
    data = read_bytes(sha256)
    row = None
    if conn is not None:
        row = conn.execute("SELECT key, url, kind, case_slug, profile, profile_version FROM courts.documents WHERE document = %s "
                           "ORDER BY loaded_at DESC LIMIT 1", (sha256,)).fetchone()
    entry = {"url": row[1] if row else "", "kind": row[2] if row else None, "case_slug": row[3] if row else None}
    if data.startswith(b"%PDF"):
        texts, how, unread = R._texts_of(data, sha256, store, R.profile_version(R.SCANNED))
        slug, why = R.recognise(entry, data, texts)
    else:
        page = R.case_page(data, entry["url"])
        slug, why = R.recognise(entry, data)
        texts = R._page_text_for_model(page) if page else {}
    if slug is None or slug == R.SCANNED:
        raise RuntimeError(f"{sha256[:12]}: not readable by the text reader: {why}")
    version = R.profile_version(slug)
    deadline = time.monotonic() + wait_s
    while True:
        try:
            got = read_one(sha256, texts, profile=slug, version=version, url=url, model=model, store=store, post=post,
                           request=request)
            break
        except (urllib.error.URLError, ConnectionError, modelclient.WrongModel) as exc:
            if time.monotonic() >= deadline:
                raise
            print(f"courts read: the model is not answering ({type(exc).__name__}); waiting a minute", file=sys.stderr)
            time.sleep(60)
    return {"document": sha256, "profile": f"{slug}@{version}", "model": got["model"], "people": len(got["people"]),
            "summary": bool(got["summary"]), "replayed": got["replayed"], "chars": sum(len(t) for t in texts.values())}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    if "--pieces" in argv:
        with db.connect(db.READ_KEY, database) as conn:
            conn.execute("SET statement_timeout = '60s'")
            for sha, slug, version, url in waiting(conn):
                print(sha)
        return 0
    if "--piece" in argv:
        sha = argv[-1]
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            print("--piece takes the document's sha256 as the last argument", file=sys.stderr)
            return 2
        request = json.loads(os.environ.get("QV4_MODEL_REQUEST") or "{}")
        try:
            conn = db.connect(db.OWNER_KEY, database)
            conn.execute("SET statement_timeout = '60s'")
        except Exception:  # noqa: BLE001 — a piece without the database still reads: the profile comes from the bytes
            conn = None
        try:
            line = piece(sha, url=os.environ.get("QV4_MODEL_URL") or URL, model=os.environ.get("QV4_MODEL") or TEXT_MODEL,
                         conn=conn, request=request, wait_s=5400 if "--wait" in argv else 0)
        finally:
            if conn is not None:
                conn.close()
        print(f"courts read: {line['document'][:12]} {line['profile']} by {line['model']}: {line['people']} name(s), "
              f"summary {line['summary']}, {'replayed' if line['replayed'] else 'read now'}, {line['chars']} chars")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
