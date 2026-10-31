"""The text reader's reading of a sitting day (profile `hansard-day`; Arthur,
31 October 2026, the common rules for every MCP names reader): every person,
company, agency and body the speakers name in their speeches, with its kind,
the role as the text says it, the organisation the person is "of", and one
summary line per piece. Flash-Next (profile `text-reader`, the standing
server on this box) through the model client, which names the model and
refuses an answer from any other; temperature 0, thinking off.

A day is far over the reader's budget (the median day is 337,000
characters; the budget is `BUDGET` characters, measured against the
profile's 16,384-token context with `MAX_TOKENS` to answer in), so it is
read in pieces by the profile's split rule (split.pieces_of: one piece per
section; a section over the budget cut at speaker turns, then paragraphs,
then lines). Each piece's reading is stored under the day's hash as page p
(ruling 50: one reading per hash and settings, replayed and never remade),
and when every piece is read the readings are joined into one reading at
page 1 under the `joined` settings, which the load picks up. A piece that
dies half-way loses nothing: the next run replays the pieces already stored.

An answer cut off at the token cap is salvaged to its complete entries and
stamped `truncated`; an answer with no JSON object is asked once more on the
first half of the piece, and failing that an `unusable` reading is stored
with the reason, so nothing loops. The speakers themselves are the turns'
own rows (split.py) and are not asked for.

    python -m registers.hansard.model_read --pieces [--database D]   the days waiting on the reader, newest first, one sha256 a line
    python -m registers.hansard.model_read --piece SHA256            one piece of qv4-hansard-read: the whole day (QV4_MODEL_URL, QV4_MODEL, QV4_MODEL_REQUEST from the worker)
    python -m registers.hansard.model_read --piece SHA256 --wait     from a session: wait for the standing server to come back
    python -m registers.hansard.model_read --piece SHA256 --threads 4   this many of the day's pieces in flight at once (default THREADS)

The text goes to the model and nowhere else (hard limit 10: the server is
on this box; limit 11: no speech text is printed or logged here).
"""
import datetime as dt
from concurrent.futures import ThreadPoolExecutor
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
from registers.hansard import split as S

READER = "registers.hansard.model_read 1"
LANE = "hansard"
PROFILE = "hansard-day"
TEXT_MODEL = os.environ.get("QV4_HANSARD_TEXT_MODEL") or "qwen3.6-35b-a3b-q4km"      # profiles.toml [profiles.text-reader] model (Qwen 3.6 from 1 November 2026; Flash-Next readings stand: support.reader.EARLIER_MODELS)
URL = os.environ.get("QV4_MODEL_URL") or "http://127.0.0.1:8060/v1/chat/completions"
#: characters of speech per request. The text-reader context is 16,384 tokens; MAX_TOKENS answer; the prompt about
#: 420 tokens; Hansard English measured at 4.3 characters a token on the sample (31 October 2026), so 40,000
#: characters is about 9,300 tokens and the request about 13,800 of the 16,384
#: 31 October 2026, 22:40, for speed: about 20,000 tokens of text and 11,000 to answer in the 32,768-token slot
#: (Radiance --max-model-len 32768); the chunk trial of 22:35 measured 20,000 tokens as the fastest size with no answer cut
BUDGET = 84000
MAX_TOKENS = 11000
ATTEMPTS = 2
#: a day's pieces in flight at once (the job runs `concurrency` days at once besides; the text-reader profile has 16 slots)
THREADS = int(os.environ.get("QV4_HANSARD_THREADS") or 2)
KINDS = ("person", "company", "agency", "body", "other")
UNUSABLE = "the text reader answered with no usable JSON object in %d attempts"
PROMPT = (
    "You read one piece of a New Zealand parliamentary debate (Hansard): speeches by members, each opening with the "
    "speaker's name in capitals or a role such as SPEAKER, then what they said. Answer with ONE JSON object and nothing else:\n"
    '{"summary": "<one sentence, at most 40 words, saying what this piece of the debate is about, naming nobody>",\n'
    ' "names": [{"name": "<a person or body named in the speeches, exactly as printed>", '
    '"kind": "person" | "company" | "agency" | "body" | "other", '
    '"role": "<the role the text gives them, in the text\'s own words, e.g. Minister of Finance, chief executive, '
    'constituent, former member, the applicant; null when none>", '
    '"of": "<for a person: the organisation the text says they are of or from, as printed; otherwise null>"}]}\n'
    "Rules. List every person, company, government agency or department, council, court, iwi, trust, union, charity and "
    "other body that a speaker NAMES in a speech, each once. Do not list the speakers themselves (the names that open "
    "a paragraph before a colon) unless another speaker names them in a speech. A company or incorporated business is "
    "kind company; a ministry, department, Crown entity, council, police or court is kind agency; any other organisation "
    "is kind body; a named individual is kind person; use other when the kind cannot be told. Keep spelling, initials and "
    "honorifics as printed; never expand an initial; never add an address, an age or any fact the text does not state; "
    "never name anyone the text does not name. A role or party alone (\"the Minister\", \"National\") is not a name. "
    "When the text is marked in sections ([SECTION 12] and so on), give each name the number of the section it is named "
    "in as \"section\": 12, and list a name once in each section that names it.")
_JSON = re.compile(r"\{.*\}", re.S)


def profile_version(slug: str = PROFILE) -> int:
    from registers.hansard import read
    p = profiles.profile(slug) or profiles.profile(slug, path=read.PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


def budget_of(slug: str = PROFILE) -> int:
    """The profile's reading budget in characters, from its config; BUDGET when the profile has none."""
    from registers.hansard import read
    p = profiles.profile(slug) or profiles.profile(slug, path=read.PROPOSED)
    try:
        return int((p or {}).get("config", {}).get("budget_chars") or BUDGET)
    except (TypeError, ValueError):
        return BUDGET


def settings(prompt: str = PROMPT, joined: bool = False) -> dict:
    out = {"prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()[:16], "budget_chars": BUDGET,
           "temperature": 0.0, "max_tokens": MAX_TOKENS, "thinking": False, "split": S.RULE}
    if joined:
        out["joined"] = True
    return out


def piece_key(sha256: str, piece: int, profile: str, version: int, model: str = TEXT_MODEL) -> str:
    return rd.reading_key(sha256, piece, model, settings(), profile, version)


def key_for(sha256: str, profile: str, version: int, model: str = TEXT_MODEL) -> str:
    """The joined reading's key: page 1 under the `joined` settings (a piece's reading at page 1 has the plain ones)."""
    return rd.reading_key(sha256, 1, model, settings(joined=True), profile, version)


# ── the answer ────────────────────────────────────────────────────────────────────────────────────────────────
def _object(text: str):
    """(the answer's object with a `names` list, whether it was salvaged) or (None, False): a whole object
    first; failing that, the text from its first brace cut at each closing brace from the end, the list and the
    object closed after it, until one parses (the entries before the cut are complete, the cut one is dropped)."""
    m = _JSON.search(text)
    if m:
        try:
            body = json.loads(m.group(0))
            if isinstance(body, dict) and isinstance(body.get("names"), list):
                return body, False
        except ValueError:
            pass
    start = text.find("{")
    if start < 0 or '"names"' not in text:
        return None, False
    cut = len(text)
    for _ in range(600):
        cut = text.rfind("}", start + 1, cut)
        if cut < 0:
            break
        for tail in ("]}", "}"):
            try:
                body = json.loads(text[start:cut + 1] + tail)
            except ValueError:
                continue
            if isinstance(body, dict) and isinstance(body.get("names"), list):
                return body, True
    return None, False


def _clean(v):
    if v in (None, "", "null"):
        return None
    v = re.sub(r"\s+", " ", str(v)).strip()
    return v or None


def parse_answer(text: str):
    """The JSON object in the model's answer, checked: None when there is no usable object. Each name once (by
    name and kind); a name that is only a role or a party is dropped."""
    body, truncated = _object(text or "")
    if body is None:
        return None
    names, seen = [], set()
    for item in body["names"]:
        if not isinstance(item, dict):
            continue
        name = _clean(item.get("name"))
        if not name or len(name) < 2:
            continue
        kind = (str(item.get("kind") or "other").strip().lower())
        kind = kind if kind in KINDS else "other"
        try:
            section = int(item.get("section")) if item.get("section") not in (None, "", "null") else None
        except (TypeError, ValueError):
            section = None
        if (name.upper(), kind, section) in seen:
            continue
        seen.add((name.upper(), kind, section))
        entry = {"name": name, "kind": kind, "role": _clean(item.get("role")), "of": _clean(item.get("of"))}
        if section is not None:
            entry["section"] = section
        names.append(entry)
    return {"summary": _clean(body.get("summary")), "names": names, "truncated": truncated}


def ask(text: str, *, url: str, model: str, post=None, request: dict = None, timeout: float = 900.0,
        attempt: int = 1) -> tuple:
    """(parsed answer or None, served model, usage). One call; the client reads the served model back and
    refuses another. The second attempt, after an answer with no object, sends the first half of the piece and
    asks for the object alone; there is no third."""
    extra = {"temperature": 0.0, "max_tokens": MAX_TOKENS, "chat_template_kwargs": {"enable_thinking": False}}
    for k, v in (request or {}).items():
        if k not in ("temperature", "max_tokens"):
            extra.setdefault(k, v)
    if attempt == 1:
        user = "DEBATE TEXT:\n\n" + text
    else:
        user = ("Answer with the one JSON object only: no words before or after it, no code fence.\n\nDEBATE TEXT:\n\n"
                + text[:len(text) // 2])
    out = modelclient.chat(url, lane=LANE, model=model,
                           messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": user}],
                           extra=extra, timeout=timeout, post=post)
    answer = (out["choices"][0]["message"]["content"] or "").strip()
    return parse_answer(answer), out.get("model") or model, out.get("usage") or {}


def read_piece(sha256: str, piece: S.Piece, *, profile: str, version: int, url: str = None, model: str = None,
               store: rd.Store = None, post=None, request: dict = None) -> dict:
    """One piece read once and stored at page `piece.number`; a stored reading is replayed. After ATTEMPTS
    answers with no usable object an `unusable` reading is stored; nothing raises."""
    store = store or rd.Store()
    model = model or TEXT_MODEL
    key = piece_key(sha256, piece.number, profile, version, model)
    if store.has(key):
        return {**_unpack(store.get(key)), "replayed": True, "seconds": 0.0, "prompt_tokens": None}
    parsed = served = None
    usage = {}
    t0 = time.monotonic()
    for attempt in range(1, ATTEMPTS + 1):
        parsed, served, usage = ask(piece.text, url=url or URL, model=model, post=post, request=request, attempt=attempt)
        if parsed is not None:
            break
    made = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    checks = {"piece": piece.number, "section": piece.section, "ids": list(piece.ids), "part": piece.part, "parts": piece.parts,
              "chars": piece.chars, "turns": piece.turns, "attempts": attempt,
              "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens")}
    if parsed is None:
        reading = rd.Reading(sha256, piece.number, READER, served or model, settings(), profile, version, "text", "",
                             checks={**checks, "names": 0, "summary": False, "unusable": UNUSABLE % ATTEMPTS}, made_at=made)
    else:
        reading = rd.Reading(sha256, piece.number, READER, served, settings(), profile, version, "text",
                             json.dumps(parsed, ensure_ascii=False, sort_keys=True), rows=parsed["names"],
                             checks={**checks, "names": len(parsed["names"]), "summary": bool(parsed["summary"]),
                                     "truncated": bool(parsed.get("truncated"))}, made_at=made)
    store.put(reading)
    return {**_unpack(reading), "replayed": False, "seconds": round(time.monotonic() - t0, 1),
            "prompt_tokens": usage.get("prompt_tokens")}


def _unpack(reading: rd.Reading) -> dict:
    parsed = parse_answer(reading.text) or {"summary": None, "names": [], "truncated": False}
    c = reading.checks or {}
    return {"piece": reading.page, "section": c.get("section"), "ids": c.get("ids") or [], "part": c.get("part"), "parts": c.get("parts"),
            "chars": c.get("chars"), "turns": c.get("turns"), "summary": parsed["summary"], "names": parsed["names"],
            "truncated": bool(parsed.get("truncated") or c.get("truncated")), "unusable": c.get("unusable"),
            "model": reading.model, "reader": reading.reader, "made_at": reading.made_at, "key": reading.key}


def join(sha256: str, readings: list, *, profile: str, version: int, model: str, store: rd.Store) -> rd.Reading:
    """The day's one reading: every piece's reading in order under page 1 and the `joined` settings."""
    pieces = [{k: r.get(k) for k in ("piece", "section", "ids", "part", "parts", "chars", "turns", "summary", "names",
                                      "truncated", "unusable", "model", "made_at")} for r in readings]
    names = sum(len(p["names"]) for p in pieces)
    reading = rd.Reading(sha256, 1, READER, model, settings(joined=True), profile, version, "text",
                         json.dumps({"pieces": pieces}, ensure_ascii=False, sort_keys=True),
                         rows=[n for p in pieces for n in p["names"]],
                         checks={"pieces": len(pieces), "names": names,
                                 "unusable": sum(1 for p in pieces if p["unusable"]),
                                 "truncated": sum(1 for p in pieces if p["truncated"]),
                                 "chars": sum(p["chars"] or 0 for p in pieces)},
                         made_at=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
    store.put(reading)
    return reading


def earlier_joined(sha256: str, profile: str, version: int, store: rd.Store):
    """The day's joined reading under the latest EARLIER version of the profile, or None (Arthur, 1 November 2026: the
    readings already made are kept). hansard-day 2 only packed whole sections into fewer requests; a day read whole
    under 1 is a reading of the same day by the same rules, so it stands until the day is read under the current one.
    A joined reading is told from a piece's (both at page 1) by its text: {"pieces": [...]}."""
    folder = os.path.dirname(store._path(key_for(sha256, profile, version)))
    try:
        names = os.listdir(folder)
    except OSError:
        return None
    best = None
    for n in names:
        m = re.match(rf"p1__{re.escape(profile)}@(\d+)__.*\.json$", n)
        if not m or int(m.group(1)) >= version or (best and int(m.group(1)) <= best[0]):
            continue
        try:
            with open(os.path.join(folder, n), encoding="utf-8") as f:
                r = rd.Reading(**json.load(f))
            if isinstance(json.loads(r.text).get("pieces"), list):
                best = (int(m.group(1)), r)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
    return best[1] if best else None


def stored(sha256: str, profile: str, version: int, store: rd.Store, model: str = TEXT_MODEL):
    """The day's joined reading, unpacked ({pieces: [...], names, ...}), or None: the load replays, never asks. A day
    with no reading under `version` replays its reading under an earlier one (earlier_joined)."""
    key = key_for(sha256, profile, version, model)
    if store.has(key):
        r = store.get(key)
    else:
        r = earlier_joined(sha256, profile, version, store)
        if r is None:
            return None
    try:
        pieces = json.loads(r.text)["pieces"]
    except (ValueError, KeyError, TypeError):
        pieces = []
    return {"pieces": pieces, "model": r.model, "reader": r.reader, "made_at": r.made_at, "key": r.key,
            "checks": r.checks or {}}


def people_rows(sha256: str, reading: dict, day: dict, profile: str, version: int, now: str) -> list:
    """One row per name a piece's reading holds, numbered through the day's pieces in order."""
    out, n = [], 0
    for p in reading["pieces"]:
        ids = set(p.get("ids") or [])
        for item in p["names"]:
            n += 1
            sec = item.get("section") if item.get("section") in ids else p["section"]
            out.append({"key": f"{sha256}/person/{n}", "name": item["name"], "kind": item["kind"],
                        "role": item.get("role"), "role_text": item.get("role"), "of": item.get("of"),
                        "day": day["key"], "sitting_on": day["key"], "section": f"{day['key']}/{sec}",
                        "piece": p["piece"], "document": sha256, "page": 1,
                        "place": f"text reader, piece {p['piece']}, name {n}", "read_from": "text",
                        "reader": reading["reader"], "model": p.get("model") or reading["model"], "profile": profile,
                        "profile_version": version, "loaded_at": now,
                        "source_note": "named in a speech as the text reader read it; the speaker is the turn's row"})
    return out


# ── the job ───────────────────────────────────────────────────────────────────────────────────────────────────
def waiting(conn, schema: str = "hansard") -> list:
    """The days without a joined reading, newest first: [(sha256, day)]."""
    rows = conn.execute(f"SELECT document, key FROM {schema}.days WHERE reading IS DISTINCT FROM 'read' "
                        f"AND left(reading, 9) <> 'set aside' ORDER BY sitting_on DESC").fetchall()
    return [tuple(r) for r in rows]


def piece(sha256: str, *, url: str, model: str, store: rd.Store = None, post=None, request: dict = None,
          wait_s: float = 0.0, log=None, threads: int = None) -> dict:
    """One piece of `qv4-hansard-read`: the whole day. The record from the store, split by the profile's rule,
    every piece read (the stored ones replayed), the readings joined. Counts and the hash only."""
    from support.docstore.landing import read_bytes
    store = store or rd.Store()
    threads = THREADS if threads is None else threads
    rec = json.loads(read_bytes(sha256))
    day_key = rec.get("sitting_date") or ""
    version = profile_version()
    budget = budget_of()
    day = S.split(rec.get("text") or "", day_key)
    if day.reason:
        raise RuntimeError(f"{sha256[:12]} ({day_key}): the profile cannot split it: {day.reason}")
    pieces = S.packed(S.pieces_of(day, budget), budget)
    over = [p for p in pieces if p.chars > budget]
    if over:
        raise RuntimeError(f"{sha256[:12]} ({day_key}): {len(over)} piece(s) over the budget after every cut "
                           f"(piece {over[0].number}, {over[0].chars} chars)")
    deadline = time.monotonic() + wait_s
    if not store.has(key_for(sha256, PROFILE, version, model)):
        old = earlier_joined(sha256, PROFILE, version, store)
        if old is not None:      # read whole under an earlier version: kept, not read again (1 November 2026)
            got = json.loads(old.text)["pieces"]
            return {"document": sha256, "day": day_key, "layout": day.layout, "profile": f"{PROFILE}@{old.profile_version}",
                    "model": old.model, "pieces": len(got), "replayed": len(got), "names": (old.checks or {}).get("names"),
                    "unusable": (old.checks or {}).get("unusable"), "truncated": (old.checks or {}).get("truncated"),
                    "chars": (old.checks or {}).get("chars"), "seconds": 0.0, "chars_per_token": None}

    def one(p):
        while True:
            try:
                return read_piece(sha256, p, profile=PROFILE, version=version, url=url, model=model, store=store,
                                  post=post, request=request)
            except (urllib.error.URLError, ConnectionError, modelclient.WrongModel) as exc:
                if time.monotonic() >= deadline:
                    raise
                print(f"hansard read: the model is not answering ({type(exc).__name__}); waiting a minute", file=sys.stderr)
                time.sleep(60)
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=max(1, threads)) as pool:   # the server's slots are shared; THREADS requests in flight
        readings = list(pool.map(one, pieces))
    seconds, replayed, tokens = round(time.monotonic() - t0, 1), 0, []
    for p, got in zip(pieces, readings):
        replayed += got["replayed"]
        if got.get("prompt_tokens") and not got["replayed"]:
            tokens.append((p.chars, got["prompt_tokens"]))
        if log:
            log(f"hansard read: {sha256[:12]} {day_key} piece {p.number}/{len(pieces)} section {p.section} "
                f"{p.chars} chars: {len(got['names'])} name(s), {'replayed' if got['replayed'] else f'{got['seconds']} s'}"
                + (", cut at the token cap" if got["truncated"] else "") + (", UNUSABLE" if got["unusable"] else ""))
    joined = join(sha256, readings, profile=PROFILE, version=version, model=model, store=store)
    return {"document": sha256, "day": day_key, "layout": day.layout, "profile": f"{PROFILE}@{version}",
            "model": joined.model, "pieces": len(pieces), "replayed": replayed, "names": joined.checks["names"],
            "unusable": joined.checks["unusable"], "truncated": joined.checks["truncated"],
            "chars": joined.checks["chars"], "seconds": seconds,
            "chars_per_token": round(sum(c for c, _ in tokens) / sum(t for _, t in tokens), 2) if tokens else None}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    if "--pieces" in argv:
        with db.connect(db.READ_KEY, database) as conn:
            conn.execute("SET statement_timeout = '60s'")
            for sha, _day in waiting(conn):
                print(sha)
        return 0
    if "--piece" in argv:
        sha = argv[argv.index("--piece") + 1] if argv.index("--piece") + 1 < len(argv) else ""
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            print("--piece takes the document's sha256", file=sys.stderr)
            return 2
        request = json.loads(os.environ.get("QV4_MODEL_REQUEST") or "{}")
        threads = int(argv[argv.index("--threads") + 1]) if "--threads" in argv else None
        line = piece(sha, url=os.environ.get("QV4_MODEL_URL") or URL, model=os.environ.get("QV4_MODEL") or TEXT_MODEL,
                     request=request, wait_s=5400 if "--wait" in argv else 0, log=lambda s: print(s, file=sys.stderr),
                     threads=threads)
        print(f"hansard read: {line['document'][:12]} {line['day']} ({line['layout']}) {line['profile']} by {line['model']}: "
              f"{line['pieces']} piece(s), {line['replayed']} replayed, {line['names']} name(s), {line['chars']} chars, "
              f"{line['seconds']} s" + (f", {line['chars_per_token']} chars a token" if line["chars_per_token"] else "")
              + (f", {line['truncated']} cut at the token cap" if line["truncated"] else "")
              + (f"; {line['unusable']} UNUSABLE piece(s)" if line["unusable"] else ""))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
