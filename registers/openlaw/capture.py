"""How this lane's documents arrive: case 3 of plan 1.10, one capture of its
own, politely, through the fetch gate and the landing wrapper only.

The source is OpenLaw NZ's GraphQL interface (`api.openlaw.nz/graphql`,
PostGraphile, `x-apikey` header, our own key). About 47,000 parsed cases;
lists are paged by `first` and `offset` with no total count, so the
interface's own figure is found by probing offsets (`probe_total`). Ids are
stable strings.

HELD. OpenLaw's API terms (3.6(a)) bar "permanent copies" and "building
databases" of what the interface returns, without OpenLaw's express
authorisation (the position, `position/openlaw-case-law.md`, question 3).
So a run lands nothing until the position on file carries a line

    authorised: <date>, <how OpenLaw said so, and where the letter is held>

and refuses with `Held` otherwise, before any case record is asked for.
Counting the cases (ids only, held nowhere) is transient use and is not held.

What is copied, once authorised: every case record verbatim as the
interface returns it to the lane's one query (`CASES_QUERY`: the case's own
fields, its court, PDF, citations, the cases it cites, its statute links and
its party table; not its counsel), ten cases a page, newest first, each page
landed by hash with a listing row (`capture_pages`). Passes:

  sample   the first night: about 2,000 cases, newest first; the capture
           is sized from it (pages, bytes, seconds)
  full     every case, newest first, resumable by offset; weekly
  head     nightly between full passes: newest first until a page holds no
           case the listing lacks

Politeness (hard limit 7): one request at a time; `FLOOR_S` of rest after
each answer and the gate's floor from each start, whichever is slower;
off-peak only unless `--anytime`; a page whose bytes are already held adds a
name, not a document. A 403, 429, 5xx, a challenge page or an answer with
GraphQL `errors` is a failed read (hard limit 6): a catch-log line, and the
night STOPS. Three transport failures in a row stop it too. A gate refusal
is never caught. The key is read at use from the credential folder and is
never printed, logged, landed or put in a URL.

Every line printed is a count.

    python -m registers.openlaw.capture [--mode sample|full|head] [--budget-s N] [--anytime]
    python -m registers.openlaw.capture --probe      # the interface's own count, by offset (ids only, nothing kept)
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import support.fetchgate as fg

SOURCE = SCHEMA = "openlaw"
JOB = "qv4-openlaw-capture"
HOST = "api.openlaw.nz"
URL = f"https://{HOST}/graphql"
KEY_FILE, KEY_HEADER = "openlaw_api_key", "x-apikey"
PAGE = 10                        # cases a page: caseText is a whole judgment
FLOOR_S = 3.0                    # rest after each answer (the brief's floor is 2 s); the gate's floor from each start binds too
OFF_PEAK = (22, 6)               # NZ local hours
SAMPLE = 2000
FULL_EVERY_DAYS = 7
STOP_AFTER_FAILURES = 3
DEFAULT_BUDGET_S = 14400
ORDER = "[CASE_DATE_DESC, ID_DESC]"
HERE = os.path.dirname(os.path.abspath(__file__))
#: where the position is read from: None is the gate's default (docs/legal/positions/). Until the integrator moves
#: the page there, a session runs with QV4_POSITIONS=registers/openlaw/position
POSITIONS = None
CASE_FIELDS = """id caseName caseDate courtFilingNumber location isValid lastModified parsersVersion courtId pdfId caseText
  court { id name acronyms }
  pdf { pdfId pdfUrl pdfProvider fetchDate }
  caseCitations { id citation year }
  casesCitedsByCaseOrigin { caseCited citationCount }
  legislationToCases { legislationId section count extractionConfidence legislation { id title year } }
  experimentalPartyAndRepresentatives { partyType names }"""
#: the documents about the interface, landed with the first authorised run (never parsed here)
DOCS = {
    "api-terms": "https://s3-ap-southeast-2.amazonaws.com/assets.openlaw.nz/apiterms.pdf",
    "our-mission": "https://www.openlaw.nz/our-mission",
    "api-key-page": "https://www.openlaw.nz/api-key",
}
CONTENT_TYPES = {"api-terms": "application/pdf", "our-mission": "text/html", "api-key-page": "text/html"}


class Held(RuntimeError):
    """The capture is held: the position on file records no authorisation from OpenLaw."""


class Stop(RuntimeError):
    """The night stops here: a block, a challenge, errors, or the host not answering."""


# ── pure pieces ───────────────────────────────────────────────────────────────

def cases_query(offset: int, first: int = PAGE) -> str:
    return f"{{ cases(first: {int(first)}, offset: {int(offset)}, orderBy: {ORDER}) {{ {CASE_FIELDS} }} }}"


def ids_query(offset: int, first: int = 1) -> str:
    return f"{{ cases(first: {int(first)}, offset: {int(offset)}, orderBy: [ID_ASC]) {{ id }} }}"


def page_name(offset: int, first: int = PAGE) -> str:
    """The listing's name for a page: the query's place, never the key."""
    return f"{URL}#cases?first={first}&offset={offset}&orderBy=CASE_DATE_DESC,ID_DESC&fields=v1"


def authorisation(positions_dir: str = None):
    """The `authorised:` line of the position covering the host, or None."""
    folder = positions_dir or fg.POSITIONS_DIR
    cls = fg.position_for(HOST, folder)
    if not cls:
        return None
    try:
        with open(os.path.join(folder, cls + ".md"), encoding="utf-8") as f:
            m = re.search(r"^authorised:\s*(\S.*)$", f.read(), re.M)
    except OSError:
        return None
    return m.group(1).strip() if m else None


def answer(body: bytes):
    """(cases, '') from an answer; (None, why) for errors or a wrong shape."""
    try:
        j = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return None, "the answer is not JSON"
    if not isinstance(j, dict):
        return None, "the answer is not a JSON object"
    if j.get("errors"):
        return None, f"the interface answered with {len(j['errors'])} error(s)"
    cases = (j.get("data") or {}).get("cases") if isinstance(j.get("data"), dict) else None
    if not isinstance(cases, list):
        return None, "no data.cases list"
    return cases, ""


def off_peak(now_local: dt.datetime) -> bool:
    start, end = OFF_PEAK
    return now_local.hour >= start or now_local.hour < end


def plan_pass(open_pass: bool, sample_done, full_done, now: dt.datetime, mode: str = None) -> str:
    """'resume', 'sample', 'full' or 'head'. Pure. A mode asked for by hand
    wins unless a pass is open."""
    if open_pass:
        return "resume"
    if mode:
        return mode
    if sample_done is None and full_done is None:
        return "sample"
    if full_done is None or now - full_done >= dt.timedelta(days=FULL_EVERY_DAYS):
        return "full"
    return "head"


def api_key() -> str:
    """Our OpenLaw key, read now from the credential folder. Never print it."""
    from support import db
    try:
        with open(os.path.join(db.CRED_DIR, KEY_FILE), encoding="utf-8") as f:
            key = f.read().strip()
    except OSError as exc:
        raise RuntimeError(f"no OpenLaw credential file: {type(exc).__name__}") from None
    if "=" in key:
        key = key.split("=", 1)[1].strip().strip("\"'")
    if not key:
        raise RuntimeError("the OpenLaw credential file is empty")
    return key


def poster(query: str, key: str):
    """The transport for one POST, in the gate's `fetch(url, timeout)` shape;
    the one User-Agent; the key only in its header."""
    def fetch(url, timeout):
        req = urllib.request.Request(url, data=json.dumps({"query": query}).encode(), method="POST",
                                     headers={"User-Agent": fg.UA, KEY_HEADER: key, "Content-Type": "application/json",
                                              "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(), r.geturl()
        except urllib.error.HTTPError as e:
            return e.code, b"", url
    return fetch


def gated(query: str, timeout: int = 120, key: str = None, positions_dir: str = None, transport=None):
    """One gated POST: the gate checks and paces, then the transport goes."""
    fetch = (transport(query) if transport else poster(query, key or api_key()))
    return fg.open_url(URL, timeout=timeout, fetch=fetch, positions_dir=positions_dir or POSITIONS)


def probe_total(ask, start: int = 32768, cap: int = 1 << 22) -> tuple:
    """The interface's own count, by offset: (count, requests). `ask(offset)`
    → True when a case sits at that offset (ids only, held nowhere). Doubles
    to an empty offset, then halves to the last full one."""
    n = 0
    lo, hi = -1, None          # lo: an offset known to hold a case; hi: one known empty
    probe = start
    while hi is None:
        n += 1
        if ask(probe):
            lo, probe = probe, probe * 2
            if probe > cap:
                raise ValueError("no empty offset below the cap")
        else:
            hi = probe
    if lo == -1:
        n += 1
        if not ask(0):
            return 0, n
        lo = 0
    while hi - lo > 1:
        mid = (lo + hi) // 2
        n += 1
        if ask(mid):
            lo = mid
        else:
            hi = mid
    return lo + 1, n


# ── the lane's capture tables ─────────────────────────────────────────────────

READING = "-- ── the reading"


def tables_sql(schema: str = SCHEMA) -> str:
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        text = f.read().split(READING)[0]
    return re.sub(r"(?<![A-Za-z0-9_])openlaw(_private)?\.", lambda m: f"{schema}{m.group(1) or ''}.", text) \
        .replace("CREATE SCHEMA IF NOT EXISTS openlaw;", f"CREATE SCHEMA IF NOT EXISTS {schema};") \
        .replace("CREATE SCHEMA IF NOT EXISTS openlaw_private;", f"CREATE SCHEMA IF NOT EXISTS {schema}_private;")


class Tables:
    """The capture's record over a connection in autocommit mode."""

    def __init__(self, conn, schema: str = SCHEMA):
        self.conn, self.s = conn, schema

    def create(self):
        self.conn.execute(tables_sql(self.s))

    def try_lock(self) -> bool:
        return bool(self.conn.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (JOB,)).fetchone()[0])

    def open_pass(self):
        r = self.conn.execute(f"SELECT pass_id, mode, next_offset, pages, cases_landed, target FROM {self.s}.capture_passes "
                              "WHERE finished_at IS NULL ORDER BY pass_id DESC LIMIT 1").fetchone()
        return None if r is None else dict(zip(("pass_id", "mode", "next_offset", "pages", "cases_landed", "target"), r))

    def last_done(self, mode: str):
        r = self.conn.execute(f"SELECT max(finished_at) FROM {self.s}.capture_passes WHERE mode = %s AND finished_at IS NOT NULL",
                              (mode,)).fetchone()
        return r[0] if r else None

    def held_ids(self) -> set:
        return {r[0] for r in self.conn.execute(f"SELECT DISTINCT unnest(ids) FROM {self.s}.capture_pages")}

    def begin(self, mode: str, target=None, probed=None) -> dict:
        pid = self.conn.execute(f"INSERT INTO {self.s}.capture_passes (mode, target, probed_total) VALUES (%s, %s, %s) "
                                "RETURNING pass_id", (mode, target, probed)).fetchone()[0]
        return {"pass_id": pid, "mode": mode, "next_offset": 0, "pages": 0, "cases_landed": 0, "target": target}

    def add_page(self, p, offset, url, sha, ids, new):
        p["pages"] += 1
        p["cases_landed"] += len(ids)
        p["next_offset"] = offset + PAGE
        self.conn.execute(
            f"INSERT INTO {self.s}.capture_pages (pass_id, page_no, page_offset, url, sha256, cases, ids, new) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (p["pass_id"], p["pages"], offset, url, sha, len(ids), list(ids), new))
        self.conn.execute(f"UPDATE {self.s}.capture_passes SET pages = pages + 1, cases_landed = cases_landed + %s, "
                          "next_offset = %s WHERE pass_id = %s", (len(ids), p["next_offset"], p["pass_id"]))

    def finish(self, p):
        self.conn.execute(f"UPDATE {self.s}.capture_passes SET finished_at = now() WHERE pass_id = %s", (p["pass_id"],))

    def set_aside(self, pass_id, item, stage, reason):
        self.conn.execute(f"INSERT INTO {self.s}.capture_set_aside (pass_id, item, stage, reason) VALUES (%s, %s, %s, %s)",
                          (pass_id, item, stage, reason[:500]))
        if pass_id is not None:
            self.conn.execute(f"UPDATE {self.s}.capture_passes SET set_aside = set_aside + 1 WHERE pass_id = %s", (pass_id,))


# ── a run ─────────────────────────────────────────────────────────────────────

class Run:
    """One night. `post(query) -> Fetched` is the gated POST (injectable);
    `get(url) -> Fetched` the gated GET for the documents about the
    interface."""

    def __init__(self, tables, *, land_fn, post=None, get=None, authorised=None, clock=None, sleep=None,
                 now_local=None, budget_s: float = DEFAULT_BUDGET_S, anytime: bool = False, mode: str = None,
                 log=print):
        self.t, self.land_fn = tables, land_fn
        self.post = post or (lambda q: gated(q))
        self.get_doc = get or (lambda url: fg.open_url(url, timeout=60, positions_dir=POSITIONS))
        self.authorised = authorised if authorised is not None else authorisation
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.now_local = now_local or (lambda: dt.datetime.now().astimezone())
        self.budget_s, self.anytime, self.mode, self.log = budget_s, anytime, mode, log
        self.started = self.clock()
        self.last_end = None
        self.failures = 0
        self.counts = {"requests": 0, "pages": 0, "cases": 0, "new": 0, "already_held": 0, "set_aside": 0,
                       "bytes": 0, "passes_finished": 0}
        self.stopped = ""

    def time_left(self) -> bool:
        if self.clock() - self.started >= self.budget_s:
            self.stopped = self.stopped or "budget spent"
            return False
        if not self.anytime and not off_peak(self.now_local()):
            self.stopped = self.stopped or "off-peak is over"
            return False
        return True

    def _rest(self):
        if self.last_end is not None:
            gap = self.last_end + FLOOR_S - self.clock()
            if gap > 0:
                self.sleep(gap)

    def call(self, do, item: str, pass_id=None):
        """One request after the rest: the Fetched, or None on a lone
        transport failure; Stop on a block, a challenge, a non-200, or three
        failures in a row."""
        self._rest()
        self.counts["requests"] += 1
        try:
            f = do()
        except fg.Refused:
            raise
        except Exception as exc:  # noqa: BLE001 — a transport failure is a line, three in a row a stop
            self.last_end = self.clock()
            self.failures += 1
            self._aside(pass_id, item, "fetch", f"transport: {type(exc).__name__}")
            if self.failures >= STOP_AFTER_FAILURES:
                raise Stop(f"{self.failures} transport failures in a row; the host may be in trouble")
            return None
        self.last_end = self.clock()
        self.failures = 0
        if f.blocked:
            self._aside(pass_id, item, "fetch", f.blocked)
            raise Stop(f.blocked)
        if f.status != 200:
            self._aside(pass_id, item, "fetch", f"HTTP {f.status}")
            raise Stop(f"HTTP {f.status}")
        return f

    def _aside(self, pass_id, item, stage, why):
        if self.t is not None:
            self.t.set_aside(pass_id, item, stage, why)
        self.counts["set_aside"] += 1

    def _land(self, body, name, content_type="application/json"):
        ref, new = self.land_fn(body, name=name, source=SOURCE, name_kind="url", content_type=content_type)
        self.counts["new" if new else "already_held"] += 1
        self.counts["bytes"] += len(body)
        return ref, new

    def docs(self):
        for name, url in DOCS.items():
            if not self.time_left():
                return
            f = self.call(lambda: self.get_doc(url), url)
            if f is not None:
                self._land(f.body, url, CONTENT_TYPES[name])

    def walk(self, p: dict, held: set):
        while self.time_left():
            if p["target"] is not None and p["cases_landed"] >= p["target"]:
                break
            off = p["next_offset"]
            name = page_name(off)
            f = self.call(lambda: self.post(cases_query(off)), name, p["pass_id"])
            if f is None:
                raise Stop(f"a page failed; the pass resumes from offset {off} next run")
            cases, why = answer(f.body)
            if cases is None:
                self._aside(p["pass_id"], name, "answer", why)
                raise Stop(why)
            ids = [c.get("id") for c in cases if isinstance(c, dict) and isinstance(c.get("id"), str)]
            if len(ids) != len(cases):
                self._aside(p["pass_id"], name, "answer", f"{len(cases) - len(ids)} record(s) with no id; landed as returned")
            ref, new = self._land(f.body, name)
            self.t.add_page(p, off, name, ref.sha256, ids, new)
            self.counts["pages"] += 1
            self.counts["cases"] += len(cases)
            if not cases or len(cases) < PAGE:
                break
            if p["mode"] == "head" and set(ids) <= held:
                break
            held.update(ids)
        else:
            return False
        self.t.finish(p)
        self.counts["passes_finished"] += 1
        self.log(f"{SOURCE}: {p['mode']} pass {p['pass_id']} finished: {p['pages']} pages, {p['cases_landed']} cases")
        return True

    def probe(self) -> int:
        def ask(offset):
            f = self.call(lambda: self.post(ids_query(offset)), f"probe offset {offset}")
            if f is None:
                raise Stop("the probe failed")
            cases, why = answer(f.body)
            if cases is None:
                raise Stop(why)
            return bool(cases)
        total, _ = probe_total(ask)
        return total

    def run(self) -> dict:
        auth = self.authorised()
        if not auth:
            raise Held("OpenLaw's API terms (3.6(a)) bar permanent copies without its express authorisation, and the "
                       "position on file records none (an `authorised:` line); nothing is asked for or landed")
        now = self.now_local()
        try:
            if not self.time_left():
                return {**self.counts, "stopped": self.stopped}
            p = self.t.open_pass()
            what = plan_pass(p is not None, self.t.last_done("sample"), self.t.last_done("full"), now, self.mode)
            if what != "resume":
                if self.t.last_done("sample") is None and self.t.last_done("full") is None:
                    self.docs()
                probed = self.probe() if what in ("sample", "full") else None
                p = self.t.begin(what, SAMPLE if what == "sample" else None, probed)
            self.walk(p, self.t.held_ids() if p["mode"] == "head" else set())
        except Stop as exc:
            self.stopped = f"stopped: {exc}"
        return {**self.counts, "stopped": self.stopped}


def landing(conn):
    from support.docstore.landing import land

    def land_fn(data, *, name, source, name_kind, content_type):
        return land(data, name=name, source=source, conn=conn, name_kind=name_kind, content_type=content_type)
    return land_fn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.openlaw.capture")
    ap.add_argument("--mode", choices=("sample", "full", "head"))
    ap.add_argument("--budget-s", type=float, default=DEFAULT_BUDGET_S)
    ap.add_argument("--anytime", action="store_true", help="run outside off-peak (by hand, on Arthur's word)")
    ap.add_argument("--probe", action="store_true", help="the interface's own count, by offset; nothing is kept")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default=SCHEMA)
    a = ap.parse_args(argv)
    if a.probe:
        r = Run(None, land_fn=None, anytime=True)
        try:
            total = r.probe()
        except Stop as exc:
            print(f"{SOURCE}: probe stopped: {exc}")
            return 1
        print(f"{SOURCE}: the interface holds {total} cases ({r.counts['requests']} requests)")
        return 0
    from support import db, jobrun
    started = jobrun.now()
    if not authorisation():
        detail = "held: OpenLaw has not authorised permanent copies (API terms 3.6(a)); nothing asked for or landed"
        print(f"{SOURCE}: {detail}")
        jobrun.record(JOB, True, detail, started, {})
        return 0
    with db.connect(db.OWNER_KEY, a.database, autocommit=True) as conn:
        conn.execute("SET statement_timeout = '60s'")
        t = Tables(conn, a.schema)
        t.create()
        if not t.try_lock():
            print(f"{SOURCE}: another run holds the lane; this one asks for nothing")
            jobrun.record(JOB, True, "skipped: another run holds the lane", started, {})
            return 0
        out = Run(t, land_fn=landing(conn), budget_s=a.budget_s, anytime=a.anytime, mode=a.mode).run()
    ok = not out["stopped"].startswith("stopped:")
    detail = (f"{out['requests']} requests, {out['pages']} pages ({out['cases']} cases, {out['bytes']} bytes), "
              f"{out['new']} new, {out['already_held']} already held, {out['set_aside']} set aside, "
              f"{out['passes_finished']} passes finished; {out['stopped'] or 'done'}")
    print(f"{SOURCE}: {detail}")
    jobrun.record(JOB, ok, detail, started, out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
