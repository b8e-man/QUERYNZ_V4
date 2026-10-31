"""The text reader's reading of the lane's documents (Arthur's common rules
for the MCP names readers, 31 October 2026; ruling 130 pending): every
person and body an archived parliament.nz page or a written question and
its reply names, with kind (person, company, agency, body, other), role
(member, minister, official, witness, submitter, other), the role in the
text's own words, the organisation a person is "of", and one summary line.
Flash-Next (profile `text-reader`, ruling 121) through the model client,
which names the model and refuses an answer from any other; temperature 0;
one reading per document hash, stamped with the reader, the served model
and the prompt's hash, stored in the reader store and replayed by every
load (ruling 50: the fast tier calls no model). Never a link, never a
claim: the load puts the names in `parliament.people`.

THE BUDGET AND THE SPLIT (the profile's `config`, profile-proposed.jsonl,
version 2). The reader never excerpts. A document's text under the budget
(24,000 characters: the text-reader context is 16,384 tokens, the answer
may take MAX_TOKENS, the prompt about 700) goes whole; one over it is read
in pieces cut by the profile's rule (a speaker turn where the text marks
one, else a paragraph end, else a sentence end, the last such boundary in
the window past a third of it) and the pieces' readings are joined under
the one hash, each name saying its piece. A text with no boundary inside
the budget cannot be split: `pieces_of` raises, the load sets the document
aside at stage `read`, named, and no job asks for it.

SEVERAL SHORT DOCUMENTS IN ONE REQUEST. A written question is about 300
characters; 683,524 of them one request each is a month of the cards. So
a request may carry several documents of one profile, each under a line
`[document dK]`, the answer keyed back by `dK`; each document's reading is
still stored once under its own hash, with the same key whether it was
read alone or with others (the prompt is one prompt; a single document is
a batch of one). A document the answer misses is asked once more alone;
still nothing, and an `unusable` reading is stored with the reason, so
the piece ends done, the load sets the document aside at stage `read`,
and nothing loops. An answer cut at the token cap is salvaged to its
complete entries and the cut document's reading says `truncated`.

    python -m registers.parliament.model_read --pieces [--database D]    the pieces waiting, one key a line, the pages first (newest first), then the questions' batch leaders
    python -m registers.parliament.model_read --piece SHA256             one piece of qv4-parliament-read (QV4_MODEL_URL, QV4_MODEL, QV4_MODEL_REQUEST from the worker)
    python -m registers.parliament.model_read --piece SHA256 --wait      from a session: wait for the standing server to come back

A piece is one archived page (its pieces, when split, one request each)
or one batch of written questions: the questions of one year whose
numbers share a range of BATCH_DOCS (`question_number // 16`), keyed by
the newest of them still waiting; the piece reads every one of its batch
not yet stored, so a later piece for a question already read replays in
a moment. The text goes to the model and nowhere else (hard limit 10: the
server is on this box; limit 11: no text is printed or logged here).
"""
import concurrent.futures as cf
import datetime as dt
import functools
import hashlib
import json
import os
import re
import sys
import time
import urllib.error

from support import modelclient, profiles
from support import reader as rd

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
READER = "registers.parliament.model_read 1"
LANE = "parliament"
TEXT_MODEL = os.environ.get("QV4_PARLIAMENT_TEXT_MODEL") or "qwen3.6-35b-a3b-q4km"      # profiles.toml [profiles.text-reader] model (Qwen 3.6 from 1 November 2026; Flash-Next readings stand: support.reader.EARLIER_MODELS)
URL = os.environ.get("QV4_MODEL_URL") or "http://127.0.0.1:8060/v1/chat/completions"
MAX_TOKENS = 4096
WAYBACK, WQ = "mcp-parliament-wayback-page", "mcp-parliament-written-question"
TABLE_OF = {WAYBACK: "wayback_pages", WQ: "written_questions"}
PROFILE_OF = {v: k for k, v in TABLE_OF.items()}
DEFAULT_BUDGET = 24000
BATCH_DOCS = 16                  # written questions in one request at most; the batch is one year's number range
ATTEMPTS = 2
BUSY_WAIT_S, BUSY_TRIES = 30, 40      # a 429 is the server saying its slots are full: wait, politely, up to 20 minutes
PIECE_STREAMS = 4                     # the pieces of one split page read this many at a time (a 29-piece page inside one job piece)
KINDS = ("person", "company", "agency", "body", "other")
ROLES = ("member", "minister", "official", "witness", "submitter", "other")
UNUSABLE = "the text reader answered with no usable object for the document in %d attempts"
CANNOT_SPLIT = "the profile cannot split the text: no speaker turn, paragraph end or sentence end inside the budget of %d characters"
HEADER = {WAYBACK: "an archived parliament.nz page", WQ: "a written question to a Minister and the Minister's reply"}
PROMPT = (
    "You read documents of the New Zealand Parliament: archived parliament.nz pages (debates, committee pages, "
    "member pages, news, bills) and written questions with the Minister's reply. A request carries one or more "
    "documents, each under a line [document dK]; a long page may come as one part of several. Answer with ONE JSON "
    "object and nothing else:\n"
    '{"documents": [{"key": "<dK, exactly as given>",\n'
    '  "summary": "<one sentence, at most 40 words, saying what the document is about; it names nobody>",\n'
    '  "people": [{"name": "<the name exactly as the document prints it>",\n'
    '              "kind": "person" | "company" | "agency" | "body" | "other",\n'
    '              "role": "member" | "minister" | "official" | "witness" | "submitter" | "other",\n'
    '              "role_text": "<the role in the document\'s own words, e.g. Minister of Health, chairperson, '
    'chief executive, submitter, witness; null when it gives none>",\n'
    '              "of": "<the organisation the document says the person belongs to or speaks for; null when it says none>"}]}]}\n'
    "One entry per document, in the order given, keys exactly as given. Rules. List every person and every body "
    "(company, government department or ministry, council, commission, agency, police, political party, trust, "
    "iwi, school, union, association, court) the document names, each once per document, with the role the text "
    "gives it: a member of Parliament is role member; a Minister is role minister; a public servant, a clerk, an "
    "officer of Parliament, a council or agency officer is role official; a person giving evidence to a committee "
    "is role witness; a person or body making a submission is role submitter; otherwise other. A company is kind "
    "company; a government department, ministry, council, commission, agency or police is kind agency; any other "
    "organisation is kind body; a person is kind person. \"of\" is the organisation the text says the person is "
    "with. Keep spelling, initials and honorifics as printed; never expand an initial; never add an address, an "
    "age or a date of birth; never name anyone the text does not name. For a written question, the asking member "
    "and the answering Minister are known already: list them only where the text names them in another "
    "connection; list the third parties the question and the reply name. A page's menus and navigation name "
    "nobody. The summary describes the document in neutral words.")
_JSON = re.compile(r"\{.*\}", re.S)
# the boundaries a split may fall on, in the order the profile prefers them
TURN = re.compile(r"(?:(?:Rt )?Hon |Dr |)(?:[A-ZĀĒĪŌŪ][A-ZĀĒĪŌŪ'’\-]+ ){1,4}\([^()]{3,90}\):")
PARAGRAPH = re.compile(r"\n\s*\n|\n")
SENTENCE = re.compile(r"[.!?][”’\")\]]*\s(?=[A-Z“\"(\[])")
MARKS = (("turn", TURN, "start"), ("paragraph", PARAGRAPH, "end"), ("sentence", SENTENCE, "end"))


class CannotSplit(ValueError):
    """The text has no boundary the profile allows inside the budget."""


# ── the profile ──────────────────────────────────────────────────────────────────────────────────────────────
@functools.lru_cache(maxsize=None)
def profile_of(slug: str) -> dict:
    """The newest version of the profile, from the ledger or the lane's proposed line (the integrator appends
    it at the merge), whichever is higher. Read once a process: the load asks for 705,000 keys."""
    held = [p for p in (profiles.profile(slug), profiles.profile(slug, path=PROPOSED)) if p]
    if not held:
        raise LookupError(f"no document profile {slug}")
    return max(held, key=lambda p: int(p["version"]))


def profile_version(slug: str) -> int:
    return int(profile_of(slug)["version"])


def budget(slug: str) -> int:
    """The reader's context budget in characters, the profile's own figure."""
    return int(((profile_of(slug).get("config") or {}).get("reader_budget_chars")) or DEFAULT_BUDGET)


@functools.lru_cache(maxsize=None)
def settings(profile: str, prompt: str = PROMPT) -> dict:
    return {"prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()[:16], "budget_chars": budget(profile),
            "temperature": 0.0, "max_tokens": MAX_TOKENS, "thinking": False}


def key_for(sha256: str, profile: str, version: int, model: str = TEXT_MODEL) -> str:
    return rd.reading_key(sha256, 1, model, settings(profile), profile, version)


# ── the text and its pieces ──────────────────────────────────────────────────────────────────────────────────
def document_text(profile: str, row: dict) -> str:
    """What the model reads: a page's text; a question and its reply (the record's own fields, never the
    provider's `text`). `row` is the lane's row or the record's own fields."""
    if profile == WAYBACK:
        return (row.get("text") or "").strip()
    q = (row.get("question_text") if "question_text" in row else row.get("questionText")) or ""
    r = (row.get("reply_text") if "reply_text" in row else row.get("replyText")) or ""
    return f"QUESTION: {q.strip()}\nREPLY: {r.strip()}"


def _cut(window: str) -> int | None:
    """Where the window is cut: the last boundary past a third of it, by the first mark that has one."""
    floor = len(window) // 3
    for _, pat, side in MARKS:
        last = None
        for m in pat.finditer(window):
            at = m.start() if side == "start" else m.end()
            if at > floor and at < len(window):
                last = at
        if last is not None:
            return last
    return None


def pieces_of(text: str, limit: int) -> list:
    """The text whole when it is within the budget, else in pieces each within it, cut by the profile's rule.
    Raises CannotSplit when a window has no boundary."""
    text = text or ""
    out, i = [], 0
    while len(text) - i > limit:
        window = text[i:i + limit]
        cut = _cut(window)
        if cut is None:
            raise CannotSplit(CANNOT_SPLIT % limit)
        out.append(window[:cut].strip())
        i += cut
    tail = text[i:].strip()
    if tail or not out:
        out.append(tail)
    return out


# ── the answer ───────────────────────────────────────────────────────────────────────────────────────────────
def _object(text: str):
    """(the answer's object with a `documents` list, whether it was salvaged) or (None, False). A whole object
    first; failing that, the text from its first brace cut at each closing brace from the end and closed after
    it, until one parses: the entries before the cut are complete, the cut one is dropped."""
    m = _JSON.search(text)
    if m:
        try:
            body = json.loads(m.group(0))
            if isinstance(body, dict) and isinstance(body.get("documents"), list):
                return body, False
        except ValueError:
            pass
    start = text.find("{")
    if start < 0 or '"documents"' not in text:
        return None, False
    cut = len(text)
    for _ in range(600):
        cut = text.rfind("}", start + 1, cut)
        if cut < 0:
            break
        for tail in ("]}]}", "]}", "}"):
            try:
                body = json.loads(text[start:cut + 1] + tail)
            except ValueError:
                continue
            if isinstance(body, dict) and isinstance(body.get("documents"), list):
                return body, True
    return None, False


def _clean(v) -> str | None:
    return (re.sub(r"\s+", " ", str(v)).strip() or None) if v not in (None, "", "null") else None


def _people(items) -> list:
    out, seen = [], set()
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        name = _clean(item.get("name"))
        if not name:
            continue
        role = str(item.get("role") or "other").strip().lower()
        role = role if role in ROLES else "other"
        kind = str(item.get("kind") or "").strip().lower()
        if kind not in KINDS:
            kind = "person" if role in ("member", "minister", "witness") else "other"
        if (name.upper(), role) in seen:          # each once (the prompt's rule); a model that loops repeats a name
            continue
        seen.add((name.upper(), role))
        out.append({"name": name, "kind": kind, "role": role, "role_text": _clean(item.get("role_text")),
                    "of": _clean(item.get("of"))})
    return out


def parse_answer(text: str):
    """{key: {"summary", "people", "truncated"}} for the documents the answer holds, or None when it holds no
    usable object. When the answer was cut at the token cap the last document it holds is marked truncated;
    documents after the cut are simply absent."""
    body, truncated = _object(text or "")
    if body is None:
        return None
    out = {}
    docs = [d for d in body["documents"] if isinstance(d, dict)]
    for n, d in enumerate(docs):
        key = _clean(d.get("key"))
        if not key or key in out:
            continue
        out[key] = {"summary": _clean(d.get("summary")), "people": _people(d.get("people")),
                    "truncated": truncated and n == len(docs) - 1}
    return out


# ── the call ─────────────────────────────────────────────────────────────────────────────────────────────────
def ask(docs: list, *, url: str, model: str, post=None, request: dict = None, timeout: float = 900.0,
        attempt: int = 1, sleep: float = None) -> tuple:
    """docs: [(key, header, text)]. (parsed answer by key or None, served model). One call; the client reads
    the served model back and refuses another. The second attempt, after an answer that missed a document,
    asks for the object alone; there is no third. A 429 (the server's slots are full, shared by every lane) or
    a server not answering (a connection refused or reset while it loads) waits BUSY_WAIT_S and asks again, up
    to BUSY_TRIES times: a busy or loading server is not a failed read. Any other HTTP error raises."""
    extra = {"temperature": 0.0, "max_tokens": MAX_TOKENS, "chat_template_kwargs": {"enable_thinking": False}}
    for k, v in (request or {}).items():
        if k not in ("temperature", "max_tokens"):
            extra.setdefault(k, v)
    body = f"DOCUMENTS: {len(docs)}\n\n" + "\n\n".join(f"[document {k}] {h}\n{t}" for k, h, t in docs)
    if attempt > 1:
        body = "Answer with the one JSON object only: no words before or after it, no code fence.\n\n" + body
    for busy in range(BUSY_TRIES + 1):
        try:
            out = modelclient.chat(url, lane=LANE, model=model,
                                   messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": body}],
                                   extra=extra, timeout=timeout, post=post)
            break
        except (urllib.error.URLError, ConnectionError) as exc:      # HTTPError is a URLError
            code = getattr(exc, "code", None)
            if (code is not None and code != 429) or busy == BUSY_TRIES:
                raise
            time.sleep(BUSY_WAIT_S if sleep is None else sleep)
    answer = (out["choices"][0]["message"]["content"] or "").strip()
    return parse_answer(answer), out.get("model") or model


def _reading(sha256: str, profile: str, version: int, served: str, parsed: dict, made: str, batch: int,
             attempts: int) -> rd.Reading:
    text = json.dumps(parsed, ensure_ascii=False, sort_keys=True)
    return rd.Reading(sha256, 1, READER, served, settings(profile), profile, version, "text", text,
                      rows=parsed["people"],
                      checks={"people": len(parsed["people"]), "summary": bool(parsed["summary"]),
                              "pieces": parsed["pieces"], "truncated": bool(parsed["truncated"]), "batch": batch,
                              "attempts": attempts}, made_at=made)


def _unusable(sha256: str, profile: str, version: int, served: str, made: str, why: str) -> rd.Reading:
    return rd.Reading(sha256, 1, READER, served, settings(profile), profile, version, "text", "",
                      checks={"people": 0, "summary": False, "pieces": 0, "unusable": why, "attempts": ATTEMPTS},
                      made_at=made)


def read_batch(docs: list, *, profile: str, version: int, url: str = None, model: str = None,
               store: rd.Store = None, post=None, request: dict = None) -> dict:
    """docs: [(sha256, text)], every text within the budget, every one of one profile. Each document is read
    once and stored under its own hash; a stored reading is replayed, never remade. One request for the batch;
    a document the answer misses is asked once more alone; still missing, an `unusable` reading is stored.
    Returns {sha256: unpacked reading}."""
    store = store or rd.Store()
    model = model or TEXT_MODEL
    url = url or URL
    out = {}
    pending = []
    for sha, text in docs:
        key = key_for(sha, profile, version, model)
        if store.has(key):
            out[sha] = {**_unpack(store.get(key)), "replayed": True}
        else:
            pending.append((sha, text))
    if not pending:
        return out
    keys = {f"d{n}": sha for n, sha in enumerate((s for s, _ in pending), 1)}
    texts = dict(pending)
    asked = [(k, HEADER[profile], texts[s]) for k, s in keys.items()]
    parsed, served = ask(asked, url=url, model=model, post=post, request=request, attempt=1)
    made = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    got = {}
    for k, sha in keys.items():
        if parsed and k in parsed:
            got[sha] = (parsed[k], len(asked), 1)
    for k, sha in keys.items():                       # the second attempt: alone, the object only
        if sha in got:
            continue
        again, served2 = ask([(k, HEADER[profile], texts[sha])], url=url, model=model, post=post, request=request,
                             attempt=2)
        served = served2 or served
        if again and k in again:
            got[sha] = (again[k], 1, 2)
    for sha in texts:
        if sha in got:
            answer, batch, attempts = got[sha]
            reading = _reading(sha, profile, version, served or model, {**answer, "pieces": 1,
                               "people": [{**p, "piece": 1} for p in answer["people"]]}, made, batch, attempts)
        else:
            reading = _unusable(sha, profile, version, served or model, made, UNUSABLE % ATTEMPTS)
        store.put(reading)
        out[sha] = {**_unpack(reading), "replayed": False}
    return out


def read_split(sha256: str, pieces: list, *, profile: str, version: int, url: str = None, model: str = None,
               store: rd.Store = None, post=None, request: dict = None) -> dict:
    """A document over the budget: each piece one request, PIECE_STREAMS of them at a time, the readings joined
    under the one hash (each name says its piece; the summary is the first piece's). A piece the model answers
    twice with nothing makes the whole document's reading `unusable`, the piece named."""
    store = store or rd.Store()
    model = model or TEXT_MODEL
    url = url or URL
    key = key_for(sha256, profile, version, model)
    if store.has(key):
        return {**_unpack(store.get(key)), "replayed": True}
    n = len(pieces)

    def one(p: int) -> tuple:
        """(piece number, the answer or None, served model, attempts)."""
        served = None
        for attempt in range(1, ATTEMPTS + 1):
            parsed, served = ask([("d1", f"{HEADER[profile]}, part {p} of {n}", pieces[p - 1])], url=url, model=model,
                                 post=post, request=request, attempt=attempt)
            if parsed and "d1" in parsed:
                return p, parsed["d1"], served, attempt
        return p, None, served, ATTEMPTS
    with cf.ThreadPoolExecutor(min(PIECE_STREAMS, n)) as ex:
        got = sorted(ex.map(one, range(1, n + 1)))
    served = next((s for _, _, s, _ in got if s), None) or model
    attempts = max(a for _, _, _, a in got)
    made = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    failed = [p for p, a, _, _ in got if a is None]
    if failed:
        reading = _unusable(sha256, profile, version, served, made, f"{UNUSABLE % ATTEMPTS} (piece {failed[0]} of {n})")
        store.put(reading)
        return {**_unpack(reading), "replayed": False}
    people = [{**x, "piece": p} for p, a, _, _ in got for x in a["people"]]
    reading = _reading(sha256, profile, version, served,
                       {"summary": next((a["summary"] for _, a, _, _ in got if a["summary"]), None), "people": people,
                        "pieces": n, "truncated": any(a["truncated"] for _, a, _, _ in got)}, made, 1, attempts)
    store.put(reading)
    return {**_unpack(reading), "replayed": False}


def _unpack(reading: rd.Reading) -> dict:
    try:
        parsed = json.loads(reading.text) if reading.text else {}
    except ValueError:
        parsed = {}
    checks = reading.checks or {}
    people = [p for p in (parsed.get("people") or []) if isinstance(p, dict) and p.get("name")]
    return {"summary": parsed.get("summary"), "people": people,
            "pieces": int(parsed.get("pieces") or checks.get("pieces") or 0), "truncated": bool(parsed.get("truncated")),
            "unusable": checks.get("unusable"), "batch": checks.get("batch"), "model": reading.model,
            "reader": reading.reader, "made_at": reading.made_at, "key": reading.key}


def stored(sha256: str, profile: str, version: int, store: rd.Store, model: str = TEXT_MODEL):
    """The stored reading, unpacked, or None: the load replays and never asks."""
    key = key_for(sha256, profile, version, model)
    if not store.has(key):
        return None
    return _unpack(store.get(key))


def people_rows(sha256: str, reading: dict, doc: dict, profile: str, version: int, now: str) -> list:
    """One row per person or body the reading names, in the reading's order. `doc`: source_table, source_key,
    dated, citation_url of the document's own row."""
    out = []
    for n, p in enumerate(reading["people"], 1):
        out.append({"key": f"{sha256}/person/{n}", "name": p["name"], "kind": p.get("kind") or "other",
                    "role": p.get("role") or "other", "role_text": p.get("role_text"), "of_organisation": p.get("of"),
                    "source_table": doc["source_table"], "source_key": doc["source_key"], "dated": doc.get("dated"),
                    "citation_url": doc.get("citation_url"), "document": sha256, "page": 1,
                    "place": f"text reader, piece {p.get('piece') or 1}, name {n}", "read_from": "text",
                    "reader": reading["reader"], "model": reading["model"], "profile": profile,
                    "profile_version": version, "loaded_at": now})
    return out


# ── the job ──────────────────────────────────────────────────────────────────────────────────────────────────
def _bucket(year, number) -> tuple:
    return (year, (number or 0) // BATCH_DOCS)


def waiting(conn, schema: str = "parliament", store: rd.Store = None, model: str = TEXT_MODEL) -> list:
    """The pieces waiting on the text reader: every archived page without a stored reading (and an older
    version whose text differs), newest first; then the written questions' batch leaders, the newest waiting
    question of each year-and-number-range batch, newest first. A document set aside at stage read is not
    waiting. [(sha256, profile)]."""
    store = store or rd.Store()
    aside = {r[0] for r in conn.execute(f"SELECT item FROM {schema}.set_aside WHERE stage = 'read'").fetchall()}
    out = []
    vw = profile_version(WAYBACK)
    pages = conn.execute(f"SELECT document, archived_at FROM {schema}.wayback_pages WHERE served "
                         f"UNION ALL SELECT f.sha256, p.archived_at FROM {schema}.files f "
                         f"JOIN {schema}.wayback_pages p ON p.key = f.record_id "
                         "WHERE f.corpus = 'parliament-wayback' AND f.status = 'older text' "
                         "ORDER BY 2 DESC NULLS LAST, 1").fetchall()
    for sha, _ in pages:
        if sha not in aside and not store.has(key_for(sha, WAYBACK, vw, model)):
            out.append((sha, WAYBACK))
    vq = profile_version(WQ)
    leaders = {}
    rows = conn.execute(f"SELECT document, question_year, question_number FROM {schema}.written_questions "
                        "WHERE served ORDER BY question_released_on DESC NULLS LAST, question_year DESC, "
                        "question_number DESC, key").fetchall()
    for sha, year, number in rows:
        b = _bucket(year, number)
        if b in leaders or sha in aside or store.has(key_for(sha, WQ, vq, model)):
            continue
        leaders[b] = sha
    out += [(sha, WQ) for sha in leaders.values()]
    return out


def _record(sha256: str) -> dict:
    from support.docstore.landing import read_bytes
    return json.loads(read_bytes(sha256))


def _profile_of_record(rec: dict) -> str | None:
    if isinstance(rec, dict) and isinstance(rec.get("questionNumber"), int):
        return WQ
    if isinstance(rec, dict) and isinstance(rec.get("snapshot_url"), str):
        return WAYBACK
    return None


def _mates(conn, schema: str, rec: dict, store: rd.Store, model: str, version: int) -> list:
    """The documents of the question's batch still waiting, the question itself first."""
    year, number = rec.get("questionYear"), rec.get("questionNumber")
    lo = (number // BATCH_DOCS) * BATCH_DOCS
    rows = conn.execute(f"SELECT document FROM {schema}.written_questions WHERE served AND question_year = %s "
                        "AND question_number >= %s AND question_number < %s ORDER BY question_number",
                        (year, lo, lo + BATCH_DOCS)).fetchall()
    aside = {r[0] for r in conn.execute(f"SELECT item FROM {schema}.set_aside WHERE stage = 'read'").fetchall()}
    return [r[0] for r in rows if r[0] not in aside and not store.has(key_for(r[0], WQ, version, model))]


def piece(sha256: str, *, url: str, model: str, store: rd.Store = None, conn=None, schema: str = "parliament",
          post=None, request: dict = None, wait_s: float = 0.0) -> dict:
    """One piece of `qv4-parliament-read`: the document's record from the store, its profile by its shape, the
    text whole or in pieces, one stored reading per document. For a written question with the database at
    hand, the rest of its batch rides in the same request. Counts and hashes only."""
    store = store or rd.Store()
    rec = _record(sha256)
    profile = _profile_of_record(rec)
    if profile is None:
        raise RuntimeError(f"{sha256[:12]}: not a written question nor an archived page: not readable by the text reader")
    version = profile_version(profile)
    limit = budget(profile)
    docs = [sha256]
    if profile == WQ and conn is not None:
        mates = _mates(conn, schema, rec, store, model, version)
        docs = [sha256] + [m for m in mates if m != sha256]
    texts = {sha256: document_text(profile, rec)}
    for m in docs[1:]:
        texts[m] = document_text(profile, _record(m))
    t0 = time.monotonic()
    deadline = time.monotonic() + wait_s
    got = {}
    while True:
        try:
            whole, split = [], []
            for s in docs:
                p = pieces_of(texts[s], limit)         # raises CannotSplit: the load sets it aside, named
                (whole if len(p) == 1 else split).append((s, p))
            for s, p in split:
                got[s] = read_split(s, p, profile=profile, version=version, url=url, model=model, store=store,
                                    post=post, request=request)
            batch, chars = [], 0
            for s, p in whole:
                if batch and (len(batch) >= BATCH_DOCS or chars + len(p[0]) > limit):
                    got.update(read_batch(batch, profile=profile, version=version, url=url, model=model,
                                          store=store, post=post, request=request))
                    batch, chars = [], 0
                batch.append((s, p[0]))
                chars += len(p[0])
            if batch:
                got.update(read_batch(batch, profile=profile, version=version, url=url, model=model, store=store,
                                      post=post, request=request))
            break
        except (urllib.error.URLError, ConnectionError, modelclient.WrongModel) as exc:
            if time.monotonic() >= deadline:
                raise
            print(f"parliament read: the model is not answering ({type(exc).__name__}); waiting a minute",
                  file=sys.stderr)
            time.sleep(60)
    seconds = round(time.monotonic() - t0, 1)
    me = got[sha256]
    return {"document": sha256, "profile": f"{profile}@{version}", "model": me["model"], "documents": len(got),
            "read_now": sum(1 for g in got.values() if not g["replayed"]),
            "people": sum(len(g["people"]) for g in got.values()), "pieces": me["pieces"],
            "summary": bool(me["summary"]), "replayed": me["replayed"], "truncated": any(g["truncated"] for g in got.values()),
            "unusable": [s[:12] for s, g in got.items() if g["unusable"]],
            "chars": sum(len(t) for t in texts.values()), "seconds": seconds}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "parliament"
    from support import db
    if "--pieces" in argv:
        with db.connect(db.READ_KEY if schema == "parliament" else db.OWNER_KEY, database) as conn:
            conn.execute("SET statement_timeout = '600s'")
            for sha, _ in waiting(conn, schema):
                print(sha)
        return 0
    if "--piece" in argv:
        sha = argv[argv.index("--piece") + 1] if argv.index("--piece") + 1 < len(argv) else ""
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            print("--piece takes the document's sha256", file=sys.stderr)
            return 2
        request = json.loads(os.environ.get("QV4_MODEL_REQUEST") or "{}")
        try:
            conn = db.connect(db.OWNER_KEY, database)
            conn.execute("SET statement_timeout = '60s'")
        except Exception:  # noqa: BLE001 — a piece without the database still reads its one document
            conn = None
        try:
            line = piece(sha, url=os.environ.get("QV4_MODEL_URL") or URL, model=os.environ.get("QV4_MODEL") or TEXT_MODEL,
                         conn=conn, schema=schema, request=request, wait_s=5400 if "--wait" in argv else 0)
        except CannotSplit as exc:
            print(f"parliament read: {sha[:12]} set aside at read: {exc}")
            return 0
        finally:
            if conn is not None:
                conn.close()
        print(f"parliament read: {line['document'][:12]} {line['profile']} by {line['model']}: {line['documents']} "
              f"document(s), {line['read_now']} read now, {line['people']} name(s), {line['pieces']} piece(s), "
              f"summary {line['summary']}, {line['chars']} chars, {line['seconds']} s"
              + (", an answer cut at the token cap: the complete entries kept" if line["truncated"] else "")
              + (f"; UNUSABLE {line['unusable']}: the next load sets them aside" if line["unusable"] else ""))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
