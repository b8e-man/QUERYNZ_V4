"""The text reader's reading of a Beehive release (Arthur, 31 October 2026:
"a pipeline that is continuously gathering, ingesting, OCRing and reading
names ... and getting other important information"): every person and body
the release names, with its kind (person, company, agency, body, place), the
role as the text says it, the organisation a person is "of", and one
summary line. Flash-Next (profile `text-reader`, the standing server;
ruling 121) through the model client, which names the model and refuses an
answer from any other; one reading per document (the record's hash),
stamped with the reader's version, the served model and the prompt's hash,
stored in the reader store and replayed from there by every load (ruling
50: the fast tier calls no model). A release without a stored reading is
"waiting: text reader" in `beehive.releases`; this module's job reads it.
The ministers the site tags a release with are the site's own rows
(`release_ministers`) and are not re-read.

    python -m registers.beehive.model_read --pieces [--database D]   every release waiting, newest first, one sha256 a line
    python -m registers.beehive.model_read --piece SHA256            one piece of qv4-beehive-read (QV4_MODEL_URL, QV4_MODEL from the worker)
    python -m registers.beehive.model_read --piece SHA256 --wait     from a session: wait for the standing server to come back

The release's text goes to the model and nowhere else (hard limit 10: the
server is on this box; limit 11: no text is printed or logged here). An
answer with no usable JSON object is asked for again once; after the
attempts the document is stored as set aside at stage read with the
reason (a reading with `usable` false), so the load accounts for it and
no job asks for it again. A record with no body, or one under MIN_WORDS
words, is set aside the same way without a call.
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
from support import profiles
from support import reader as rd

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
READER = "registers.beehive.model_read 1"
LANE = "beehive"
PROFILE = "beehive-release-body"
TEXT_MODEL = os.environ.get("QV4_BEEHIVE_TEXT_MODEL") or "qwen4exp"     # profiles.toml [profiles.text-reader] model
URL = os.environ.get("QV4_MODEL_URL") or "http://127.0.0.1:8060/v1/chat/completions"
HEAD_CHARS, TAIL_CHARS = 28000, 4000   # about 8,000 tokens; the text-reader profile's context is 16,384 with MAX_TOKENS to answer in
MAX_TOKENS = 4096
ATTEMPTS = 2
MIN_WORDS = 20
WAIT_TEXT = "waiting: text reader"
KINDS = ("person", "company", "agency", "body", "place")
ROLES = ("minister", "member of parliament", "official", "chief executive", "chair", "board member", "appointee",
         "recipient", "award", "spokesperson", "speaker", "organisation", "mentioned", "other")
PROMPT = (
    "You read one New Zealand Government release from beehive.govt.nz: a ministerial media release, a speech, a feature "
    "or a page. Answer with ONE JSON object and nothing else:\n"
    '{"summary": "<one sentence, at most 40 words, saying what the release announces or concerns>",\n'
    ' "people": [{"name": "<the name exactly as the text prints it>", '
    '"kind": "person" | "company" | "agency" | "body" | "place", '
    '"role": "minister" | "member of parliament" | "official" | "chief executive" | "chair" | "board member" | '
    '"appointee" | "recipient" | "award" | "spokesperson" | "speaker" | "organisation" | "mentioned" | "other", '
    '"role_text": "<the role in the text\'s own words, e.g. Minister of Finance, Chief Executive of Pharmac, chair of '
    'the board, recipient of the Queen\'s Service Medal>", '
    '"of": "<for a person, the organisation the text says they are of or speak for; otherwise null>"}]}\n'
    "Rules. List every person and every body (company, trust, iwi, charity, public agency, council, court, board, "
    "school, union) the text names, each once, with the role the text gives it. A minister named or quoted is role "
    "minister; a member of parliament role member of parliament; a public servant role official; a chief executive or "
    "a chair as said; a person appointed to a position role appointee; a person or body given money, a grant or a "
    "contract role recipient; a person given an honour, a medal or a prize role award; a person who speaks for a body "
    "role spokesperson; the person giving a speech role speaker; a body named for itself role organisation; a name "
    "with no role role mentioned. A government department, ministry, council, commission, the police or a Crown entity "
    "is kind agency; a company kind company; any other body kind body; a town, region, country, building or site kind "
    "place. Keep spelling, honorifics and macrons as printed; never expand an initial; never add an address, an age or "
    "a date of birth; never name anyone the text does not name. The summary describes the release in neutral words "
    "and names nobody.")
NUDGE = "Your answer held no JSON object. Answer again with the ONE JSON object described, and nothing else."
_JSON = re.compile(r"\{.*\}", re.S)


def profile_version(slug: str = PROFILE) -> int:
    """The ledger's version; until the integrator appends it, the lane's
    proposed line (merge request beehive-2)."""
    held = [p for p in (profiles.profile(slug), profiles.profile(slug, path=PROPOSED) if os.path.exists(PROPOSED) else None) if p]
    if not held:
        raise LookupError(f"no document profile {slug}")
    return max(int(p["version"]) for p in held)


def settings(prompt: str = PROMPT) -> dict:
    return {"prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()[:16], "head_chars": HEAD_CHARS,
            "tail_chars": TAIL_CHARS, "temperature": 0.0, "max_tokens": MAX_TOKENS, "thinking": False,
            "attempts": ATTEMPTS}


def key_for(sha256: str, version: int, model: str = TEXT_MODEL, profile: str = PROFILE) -> str:
    return rd.reading_key(sha256, 1, model, settings(), profile, version)


def words(body) -> int:
    return len(body.split()) if isinstance(body, str) else 0


def recognise_body(rec) -> str:
    """'' when the record carries a body this profile reads, else why not
    (the reason the release is set aside at stage read)."""
    from registers.beehive import read as R
    why = R.recognise(rec)
    if why:
        return why
    body = rec.get("body_text")
    if not isinstance(body, str) or not body.strip():
        return "no body"
    n = words(body)
    if n < MIN_WORDS:
        return f"body under {MIN_WORDS} words ({n})"
    return ""


def excerpt(title, body: str) -> str:
    """The release's text for the model: the title, then the body, the head
    and the tail when it is long (a release names its minister and its
    subject at the top and ends on contacts and notes)."""
    text = (f"TITLE: {title.strip()}\n\n" if isinstance(title, str) and title.strip() else "") + "BODY:\n" + (body or "").strip()
    if len(text) <= HEAD_CHARS + TAIL_CHARS:
        return text
    return text[:HEAD_CHARS] + "\n\n[… text omitted …]\n\n" + text[-TAIL_CHARS:]


def _clean(v):
    return re.sub(r"\s+", " ", str(v)).strip() if v not in (None, "", "null") else None


def parse_answer(text: str):
    """The JSON object in the model's answer, checked and normalised: None
    when there is no usable object."""
    m = _JSON.search(text or "")
    if not m:
        return None
    try:
        body = json.loads(m.group(0))
    except ValueError:
        return None
    if not isinstance(body, dict) or not isinstance(body.get("people"), list):
        return None
    people, seen = [], set()
    for item in body["people"]:
        if not isinstance(item, dict):
            continue
        name = _clean(item.get("name"))
        if not name:
            continue
        kind = (str(item.get("kind") or "").strip().lower().replace("-", " "))
        kind = {"organisation": "body", "organization": "body", "place not a person": "place"}.get(kind, kind)
        if kind not in KINDS:
            kind = "person"
        role = re.sub(r"\s+", " ", str(item.get("role") or "other").strip().lower())
        role = {"mp": "member of parliament", "ceo": "chief executive", "chairperson": "chair", "chairman": "chair",
                "chairwoman": "chair"}.get(role, role)
        if role not in ROLES:
            role = "other"
        if kind != "person" and role in ("minister", "member of parliament", "speaker", "spokesperson"):
            role = "other"
        mark = (name.lower(), kind)
        if mark in seen:
            continue
        seen.add(mark)
        people.append({"name": name, "kind": kind, "role": role, "role_text": _clean(item.get("role_text")),
                       "of": _clean(item.get("of")) if kind == "person" else None})
    summary = _clean(body.get("summary"))
    return {"summary": summary, "people": people}


def ask(title, body: str, *, url: str, model: str, post=None, request: dict = None, timeout: float = 600.0) -> tuple:
    """(parsed answer or None, served model, attempts made, the last
    answer's length). Up to ATTEMPTS calls; the client reads the served
    model back and refuses another."""
    extra = {"temperature": 0.0, "max_tokens": MAX_TOKENS, "chat_template_kwargs": {"enable_thinking": False}}
    for k, v in (request or {}).items():
        if k not in ("temperature", "max_tokens"):
            extra.setdefault(k, v)
    messages = [{"role": "system", "content": PROMPT}, {"role": "user", "content": excerpt(title, body)}]
    served, parsed, n, chars = model, None, 0, 0
    for n in range(1, ATTEMPTS + 1):
        out = modelclient.chat(url, lane=LANE, model=model, messages=messages, extra=extra, timeout=timeout, post=post)
        answer = (out["choices"][0]["message"]["content"] or "").strip()
        served, chars = out.get("model") or model, len(answer)
        parsed = parse_answer(answer)
        if parsed is not None:
            break
        messages = messages + [{"role": "assistant", "content": answer[:2000]}, {"role": "user", "content": NUDGE}]
    return parsed, served, n, chars


def read_one(sha256: str, title, body: str, *, version: int, url: str = None, model: str = None,
             store: rd.Store = None, post=None, request: dict = None) -> dict:
    """The document read once and stored; a stored reading is replayed, never
    remade. A record with no usable body, or a model that gives no usable
    answer after the attempts, is stored as set aside (usable false) with
    the reason: never asked again, never a failed row."""
    store = store or rd.Store()
    model = model or TEXT_MODEL
    key = key_for(sha256, version, model)
    if store.has(key):
        return {**_unpack(store.get(key)), "replayed": True}
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    why = "no body" if not isinstance(body, str) or not body.strip() else (
        f"body under {MIN_WORDS} words ({words(body)})" if words(body) < MIN_WORDS else "")
    if why:
        reading = rd.Reading(sha256, 1, READER, model, settings(), PROFILE, version, "text", "", rows=[],
                             checks={"usable": False, "reason": why, "attempts": 0}, made_at=now)
        store.put(reading)
        return {**_unpack(reading), "replayed": False}
    parsed, served, attempts, chars = ask(title, body, url=url or URL, model=model, post=post, request=request)
    if parsed is None:
        reading = rd.Reading(sha256, 1, READER, served, settings(), PROFILE, version, "text", "", rows=[],
                             checks={"usable": False, "attempts": attempts, "answer_chars": chars,
                                     "reason": f"no usable JSON object in the answer after {attempts} attempt(s)"},
                             made_at=now)
    else:
        reading = rd.Reading(sha256, 1, READER, served, settings(), PROFILE, version, "text",
                             json.dumps(parsed, ensure_ascii=False, sort_keys=True), rows=parsed["people"],
                             checks={"usable": True, "attempts": attempts, "people": len(parsed["people"]),
                                     "summary": bool(parsed["summary"])}, made_at=now)
    store.put(reading)
    return {**_unpack(reading), "replayed": False}


def _unpack(reading: rd.Reading) -> dict:
    usable = bool((reading.checks or {}).get("usable", True)) and bool(reading.text)
    parsed = (parse_answer(reading.text) if usable else None) or {"summary": None, "people": []}
    return {"usable": usable, "reason": None if usable else (reading.checks or {}).get("reason") or "unusable",
            "summary": parsed["summary"], "people": parsed["people"], "model": reading.model, "reader": reading.reader,
            "made_at": reading.made_at, "key": reading.key, "profile": reading.profile,
            "profile_version": reading.profile_version}


def stored(sha256: str, version: int, store: rd.Store, model: str = TEXT_MODEL):
    """The stored reading, unpacked, or None: the load replays and never asks."""
    key = key_for(sha256, version, model)
    if not store.has(key):
        return None
    return _unpack(store.get(key))


def stored_under_other_versions(sha256: str, version: int, store: rd.Store) -> list:
    """The profile versions this document has a text-reader reading under,
    other than `version` (the check: a reading the load does not expect)."""
    folder = os.path.dirname(store._path(key_for(sha256, version)))
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    out = set()
    for n in names:
        m = re.match(rf"p1__{re.escape(PROFILE)}@(\d+)__", n)
        if m and int(m.group(1)) != version:
            out.add(int(m.group(1)))
    return sorted(out)


def people_rows(sha256: str, reading: dict, release: dict, now: str) -> list:
    """One row per person or body the reading names, in the reading's order."""
    out = []
    for n, p in enumerate(reading["people"], 1):
        out.append({"key": f"{sha256}/person/{n}", "name": p["name"], "kind": p["kind"], "role": p["role"],
                    "role_text": p.get("role_text"), "of": p.get("of"), "release": release["key"],
                    "published_on": release.get("published_on"), "type": release.get("type"),
                    "document": sha256, "page": 1, "place": f"text reader, name {n}", "read_from": "text",
                    "reader": reading["reader"], "model": reading["model"], "profile": reading["profile"],
                    "profile_version": reading["profile_version"], "loaded_at": now})
    return out


NOT_A_RECORD = "not read: old estate export"


def replay(releases: list, bodies: dict, store: rd.Store = None, now: str = None, version: int = None) -> tuple:
    """The load's side: every release's stored reading replayed (never
    made). Sets `reading`, `summary`, `names` and `read_model` on each
    release; returns (people rows, set-aside lines at stage read, counts).
    A release read from the old estate's export is not a record and is
    not read; a body under MIN_WORDS words is set aside without a reading;
    a release with no stored reading waits."""
    from registers.beehive import read as R
    store = store or rd.Store()
    now = now or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    version = version or profile_version()
    people, aside = [], []
    n = {"documents read": 0, "documents waiting": 0, "set aside at read": 0, "not read": 0, "names read": 0}
    for rel in releases:
        rel.update(summary=None, names=0, read_model=None)
        if rel.get("profile") != R.PROFILE or not rel.get("mcp_document"):
            rel["reading"] = NOT_A_RECORD
            n["not read"] += 1
            continue
        body = bodies.get(rel["key"])
        if words(body) < MIN_WORDS:
            why = "no body" if not words(body) else f"body under {MIN_WORDS} words ({words(body)})"
            rel["reading"] = "set aside"
            aside.append((rel["key"], "read", why + ": not read"))
            n["set aside at read"] += 1
            continue
        got = stored(rel["document"], version, store)
        if got is None:
            rel["reading"] = WAIT_TEXT
            n["documents waiting"] += 1
            continue
        if not got["usable"]:
            rel["reading"] = "set aside"
            rel["read_model"] = got["model"]
            aside.append((rel["key"], "read", f"the text reader: {got['reason']}"))
            n["set aside at read"] += 1
            continue
        rows = people_rows(rel["document"], got, rel, now)
        rel.update(reading="read", summary=got["summary"], names=len(rows), read_model=got["model"])
        people += rows
        n["documents read"] += 1
        n["names read"] += len(rows)
    return people, aside, n


# ── the job ───────────────────────────────────────────────────────────────────────────────────────────────────
def waiting(conn, store: rd.Store = None, version: int = None, view: str = "pub.beehive_releases") -> list:
    """The releases waiting on the text reader, newest first: every MCP
    record with a body of MIN_WORDS words or more and no stored reading
    under the profile version the load expects. [(sha256, published_on, key)]."""
    store = store or rd.Store()
    version = version or profile_version()
    rows = conn.execute(f"SELECT document, published_on, key FROM {view} WHERE origin = 'mcp' AND document IS NOT NULL "
                        f"AND coalesce(word_count, 0) >= %s ORDER BY published_on DESC NULLS LAST, key", (MIN_WORDS,)).fetchall()
    return [tuple(r) for r in rows if not store.has(key_for(r[0], version))]


def piece(sha256: str, *, url: str, model: str, store: rd.Store = None, post=None, request: dict = None,
          wait_s: float = 0.0) -> dict:
    """One piece of `qv4-beehive-read`: the record's bytes from the document
    store, recognised, its title and body, one reading stored. Counts and
    the hash only; no database."""
    from support.docstore.landing import read_bytes
    store = store or rd.Store()
    version = profile_version()
    try:
        rec = json.loads(read_bytes(sha256))
    except (OSError, ValueError) as e:
        raise RuntimeError(f"{sha256[:12]}: not a record this reader can open: {type(e).__name__}") from None
    why = recognise_body(rec)
    if why and not why.startswith("no body") and not why.startswith("body under"):
        raise RuntimeError(f"{sha256[:12]}: not a beehive record: {why}")
    title, body = rec.get("title"), rec.get("body_text") if isinstance(rec.get("body_text"), str) else ""
    deadline = time.monotonic() + wait_s
    t0 = time.monotonic()
    while True:
        try:
            got = read_one(sha256, title, body, version=version, url=url, model=model, store=store, post=post,
                           request=request)
            break
        except (urllib.error.URLError, ConnectionError, modelclient.WrongModel) as exc:
            if time.monotonic() >= deadline:
                raise
            print(f"beehive read: the model is not answering ({type(exc).__name__}); waiting a minute", file=sys.stderr)
            time.sleep(60)
    return {"document": sha256, "profile": f"{PROFILE}@{version}", "model": got["model"], "usable": got["usable"],
            "reason": got["reason"], "people": len(got["people"]), "summary": bool(got["summary"]),
            "replayed": got["replayed"], "words": words(body), "seconds": round(time.monotonic() - t0, 1)}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    if "--pieces" in argv:
        with db.connect(db.READ_KEY, database) as conn:
            conn.execute("SET statement_timeout = '60s'")
            for sha, _on, _key in waiting(conn):
                print(sha)
        return 0
    if "--piece" in argv:
        sha = argv[-1]
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            print("--piece takes the document's sha256 as the last argument", file=sys.stderr)
            return 2
        request = json.loads(os.environ.get("QV4_MODEL_REQUEST") or "{}")
        line = piece(sha, url=os.environ.get("QV4_MODEL_URL") or URL, model=os.environ.get("QV4_MODEL") or TEXT_MODEL,
                     request=request, wait_s=5400 if "--wait" in argv else 0)
        state = ("replayed" if line["replayed"] else "read now") if line["usable"] else f"set aside: {line['reason']}"
        print(f"beehive read: {line['document'][:12]} {line['profile']} by {line['model']}: {line['people']} name(s), "
              f"summary {line['summary']}, {state}, {line['words']} words, {line['seconds']} s")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
