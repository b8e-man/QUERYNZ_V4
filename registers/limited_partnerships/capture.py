"""How this lane's documents arrive: case 3 of plan 1.10, one capture of its
own, politely, through the fetch gate and the landing wrapper only.

The source is the NZBN register's entity detail, asked one limited
partnership at a time with our own key, as the companies lane's monitor
asks (registers/companies/monitor.py; this lane does not import it):

    GET https://api.business.govt.nz/gateway/nzbn/v5/entities/{nzbn}

The frame is the Companies Office's own list: every limited partnership the
monthly file names as registered, read from `pub.companies` (entity type
`NZ Limited Partnership` or `Overseas Limited Partnership`, status
`registered`; 4,114 on 21 October 2026). The Limited Partnerships Act 2008
makes the partnership and its general partners public; limited partners are
not public and are never sought. The Companies Office's web register
(`app.companiesoffice.govt.nz`) is not used: it answered a 500 to our one
read on 21 October 2026 and its robots file disallows everything; a failed
read is not tried again.

Each answer is landed verbatim by hash and listed in `capture_asks`; the
reading (read.py) reads only answers the listing names. A night asks the
stalest slice of the frame: partnerships never asked first, then the ones
asked longest ago, at most `PER_NIGHT` (a seventh of the frame), so the
whole frame is asked weekly.

Politeness (hard limit 7): one call at a time, at least `FLOOR_S` apart
(the gate's floor for the host is the same 5 s; the slower holds), in
`WINDOW` (21:00 to 22:00 New Zealand time, before the companies monitor's
22:00 and the societies lane's 01:00 asks of the same host), never in the
interface's Wednesday 21:00 to 23:00 maintenance window, nothing asked twice
in a day. A 403, 429, 5xx or a challenge is a failed read (hard limit 6):
a catch-log line and the night stops. A 404 is the register answering that
it holds no such entity: a catch-log line, and the night goes on. Three
transport failures in a row stop the night. A gate refusal is never caught.

The key is read at the moment of use from the credential folder
(`nzbn.env`, `NZBN_API_KEY`), sent only in its header, never printed or
logged. Every line printed is a count.

    python -m registers.limited_partnerships.capture --night [--anytime] [--max N] [--budget-s N]
    python -m registers.limited_partnerships.capture --fetch NZBN [NZBN ...]   a handful, to prove the path
    python -m registers.limited_partnerships.capture --land-file PATH NZBN ASKED_AT   an answer fetched through the gate
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

import support.fetchgate as fg

SOURCE = SCHEMA = "limited_partnerships"
JOB = "qv4-limited-partnerships-capture"
HOST = "api.business.govt.nz"
BASE = os.environ.get("QV4_NZBN_API_BASE") or f"https://{HOST}/gateway/nzbn/v5"
KEY_FILE, KEY_NAME, KEY_HEADER = "nzbn.env", "NZBN_API_KEY", "Ocp-Apim-Subscription-Key"
FRAME_TYPES = ("NZ Limited Partnership", "Overseas Limited Partnership")
FRAME_STATUS = "registered"
FLOOR_S = 5.0
WINDOW = (21, 22)                 # NZ local hours: start at 21:00, stop at 22:00
PER_NIGHT = 600                   # a seventh of the frame (4,114) and a little over
DEFAULT_BUDGET_S = 3300           # 55 minutes
STOP_AFTER_FAILURES = 3
NZ = ZoneInfo("Pacific/Auckland")
HERE = os.path.dirname(os.path.abspath(__file__))
#: where the position is read from. None is the gate's default (docs/legal/positions/), where
#: `nzbn-register-entities.md` covers the host already; this lane's own page
#: (`position/limited-partnerships-register.md`) moves there at the merge.
POSITIONS = None


class Stop(RuntimeError):
    """The night stops here: a block, a challenge, or the host not answering."""


# ── pure pieces ───────────────────────────────────────────────────────────────

def entity_url(nzbn: str) -> str:
    if not (isinstance(nzbn, str) and len(nzbn) == 13 and nzbn.isdigit()):
        raise ValueError(f"not an NZBN: {nzbn!r}")
    return f"{BASE}/entities/{nzbn}"


def in_window(t: dt.datetime) -> bool:
    nz = t.astimezone(NZ)
    if nz.weekday() == 2:            # Wednesday: the interface's maintenance window covers ours
        return False
    return WINDOW[0] <= nz.hour < WINDOW[1]


def nz_day(t: dt.datetime) -> dt.date:
    return t.astimezone(NZ).date()


def slice_for(frame: list, last_asked: dict, today: dt.date, limit: int = PER_NIGHT) -> list:
    """Tonight's NZBNs: never asked first (frame order), then the longest
    ago; none asked today. Pure."""
    never = [n for n in frame if n not in last_asked]
    asked = sorted((last_asked[n], n) for n in frame if n in last_asked and nz_day(last_asked[n]) < today)
    return (never + [n for _, n in asked])[:limit]


def api_key() -> str:
    """Our NZBN key, read now from the credential folder. Never print it."""
    from support import db
    path = os.path.join(db.CRED_DIR, KEY_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(KEY_NAME + "="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError as exc:
        raise RuntimeError(f"no NZBN credential file: {type(exc).__name__}") from None
    raise RuntimeError(f"{KEY_NAME} is not set in {KEY_FILE}")


# ── the lane's capture tables ─────────────────────────────────────────────────

READING = "-- ── the reading"


def tables_sql(schema: str = SCHEMA) -> str:
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        return f.read().split(READING)[0].replace(f"{SCHEMA}.", f"{schema}.")


class Tables:
    """The capture's record, over a psycopg connection in autocommit mode."""

    def __init__(self, conn, schema: str = SCHEMA):
        self.conn, self.s = conn, schema

    def create(self):
        self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.s}")
        self.conn.execute(tables_sql(self.s))

    def try_lock(self) -> bool:
        return bool(self.conn.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (JOB,)).fetchone()[0])

    def last_asked(self) -> dict:
        return {r[0]: r[1] for r in self.conn.execute(
            f"SELECT nzbn, max(asked_at) FROM {self.s}.capture_asks GROUP BY nzbn")}

    def begin(self, frame_size: int, note: str) -> int:
        return self.conn.execute(f"INSERT INTO {self.s}.capture_passes (frame_size, frame_note) VALUES (%s, %s) "
                                 "RETURNING pass_id", (frame_size, note)).fetchone()[0]

    def ask(self, pass_id, nzbn, asked_at, status, sha, new):
        self.conn.execute(f"INSERT INTO {self.s}.capture_asks (pass_id, nzbn, asked_at, status, sha256, new) "
                          "VALUES (%s, %s, %s, %s, %s, %s)", (pass_id, nzbn, asked_at, status, sha, new))

    def set_aside(self, pass_id, item, stage, reason):
        self.conn.execute(f"INSERT INTO {self.s}.capture_set_aside (pass_id, item, stage, reason) VALUES (%s, %s, %s, %s)",
                          (pass_id, item, stage, reason[:500]))

    def finish(self, pass_id, counts: dict, stopped: str):
        self.conn.execute(f"UPDATE {self.s}.capture_passes SET finished_at = now(), asked = %s, set_aside = %s, "
                          "stopped = %s WHERE pass_id = %s",
                          (counts["asked"], counts["set_aside"], stopped or None, pass_id))


# ── a night ───────────────────────────────────────────────────────────────────

class Run:
    def __init__(self, tables, frame: list, *, land_fn, opener=None, key=None, clock=None, sleep=None, now=None,
                 budget_s: float = DEFAULT_BUDGET_S, max_asks: int = PER_NIGHT, anytime: bool = False, log=print):
        self.t, self.frame, self.land_fn = tables, frame, land_fn
        self.key = key
        self.opener = opener or self._gated
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.now = now or (lambda: dt.datetime.now(NZ))
        self.budget_s, self.max_asks, self.anytime, self.log = budget_s, max_asks, anytime, log
        self.counts = {"asked": 0, "answered": 0, "new": 0, "already_held": 0, "not_found": 0, "set_aside": 0}
        self.stopped = ""
        self.started = self.clock()
        self.last_end = None
        self.failures = 0

    def _gated(self, url, timeout):
        if self.key is None:
            self.key = api_key()
        return fg.open_url(url, timeout=timeout, headers={KEY_HEADER: self.key, "Accept": "application/json"},
                           positions_dir=POSITIONS)

    def time_left(self) -> bool:
        if self.clock() - self.started >= self.budget_s:
            self.stopped = self.stopped or "budget spent"
        elif self.counts["asked"] >= self.max_asks:
            self.stopped = self.stopped or "tonight's slice asked"
        elif not self.anytime and not in_window(self.now()):
            self.stopped = self.stopped or "outside the window"
        else:
            return True
        return False

    def one(self, pass_id, nzbn):
        if self.last_end is not None:
            gap = self.last_end + FLOOR_S - self.clock()
            if gap > 0:
                self.sleep(gap)
        url = entity_url(nzbn)
        asked_at = self.now()
        self.counts["asked"] += 1
        try:
            f = self.opener(url, 60)
        except fg.Refused:
            raise
        except Exception as exc:  # noqa: BLE001 — a transport failure is a line, three in a row a stop
            self.last_end = self.clock()
            self.failures += 1
            self._aside(pass_id, nzbn, "fetch", f"transport: {type(exc).__name__}")
            if self.failures >= STOP_AFTER_FAILURES:
                raise Stop(f"{self.failures} transport failures in a row")
            return
        self.last_end = self.clock()
        self.failures = 0
        if f.blocked:
            self._aside(pass_id, nzbn, "fetch", f.blocked)
            raise Stop(f.blocked)
        if f.status == 404:
            self.counts["not_found"] += 1
            self.t.ask(pass_id, nzbn, asked_at, 404, None, False)
            self._aside(pass_id, nzbn, "fetch", "HTTP 404: the register holds no entity under this NZBN")
            return
        if f.status != 200:
            self._aside(pass_id, nzbn, "fetch", f"HTTP {f.status}")
            return
        try:
            json.loads(f.body)
        except ValueError:
            self._aside(pass_id, nzbn, "parse", "the answer is not JSON")
            return
        ref, new = self.land_fn(f.body, name=url, source=SOURCE, name_kind="url", content_type="application/json")
        self.counts["answered"] += 1
        self.counts["new" if new else "already_held"] += 1
        self.t.ask(pass_id, nzbn, asked_at, 200, ref.sha256, new)

    def _aside(self, pass_id, item, stage, why):
        self.t.set_aside(pass_id, item, stage, why)
        self.counts["set_aside"] += 1

    def run(self) -> dict:
        tonight = slice_for(self.frame, self.t.last_asked(), nz_day(self.now()), self.max_asks)
        pass_id = self.t.begin(len(self.frame), f"{len(tonight)} in tonight's slice")
        try:
            for nzbn in tonight:
                if not self.time_left():
                    break
                self.one(pass_id, nzbn)
        except Stop as exc:
            self.stopped = f"stopped: {exc}"
        self.t.finish(pass_id, self.counts, self.stopped)
        return {**self.counts, "slice": len(tonight), "frame": len(self.frame), "stopped": self.stopped}


def frame(conn) -> list:
    """The Companies Office's own list: every registered limited partnership
    the monthly file names, by NZBN, oldest number first."""
    return [r[0] for r in conn.execute(
        "SELECT nzbn FROM pub.companies WHERE entity_type = ANY(%s) AND status = %s AND nzbn IS NOT NULL "
        "ORDER BY number", (list(FRAME_TYPES), FRAME_STATUS))]


def landing(conn):
    from support.docstore.landing import land

    def land_fn(data, *, name, source, name_kind, content_type):
        return land(data, name=name, source=source, conn=conn, name_kind=name_kind, content_type=content_type)
    return land_fn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.limited_partnerships.capture")
    ap.add_argument("--night", action="store_true")
    ap.add_argument("--fetch", nargs="+", metavar="NZBN", help="a handful, to prove the path (into --database)")
    ap.add_argument("--land-file", nargs=3, metavar=("PATH", "NZBN", "ASKED_AT"),
                    help="land an answer already fetched through the gate (a proof read kept in scratch)")
    ap.add_argument("--anytime", action="store_true", help="outside the window (by hand, a proof or a first night)")
    ap.add_argument("--max", type=int, default=PER_NIGHT)
    ap.add_argument("--budget-s", type=float, default=DEFAULT_BUDGET_S)
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default=SCHEMA)
    a = ap.parse_args(argv)
    from support import db, jobrun
    started = jobrun.now()
    with db.connect(db.READ_KEY, "querynz_v4") as src:
        src.execute("SET statement_timeout = '60s'")
        whole = frame(src)
    with db.connect(db.OWNER_KEY, a.database, autocommit=True) as conn:
        conn.execute("SET statement_timeout = '60s'")
        t = Tables(conn, a.schema)
        t.create()
        if a.land_file:
            path, nzbn, asked_at = a.land_file
            with open(path, "rb") as f:
                data = f.read()
            json.loads(data)
            ref, new = landing(conn)(data, name=entity_url(nzbn), source=SOURCE, name_kind="url",
                                     content_type="application/json")
            pid = t.begin(len(whole), "a proof read, landed from the session's scratch copy")
            t.ask(pid, nzbn, dt.datetime.fromisoformat(asked_at), 200, ref.sha256, new)
            t.finish(pid, {"asked": 1, "set_aside": 0}, "")
            print(f"{SOURCE}: landed 1 answer ({'new' if new else 'already held'})")
            return 0
        if not t.try_lock():
            print(f"{SOURCE}: another run holds the lane; this one asks for nothing")
            return 0
        if a.fetch:
            run = Run(t, a.fetch, land_fn=landing(conn), anytime=True, max_asks=len(a.fetch))
        elif a.night:
            run = Run(t, whole, land_fn=landing(conn), anytime=a.anytime, max_asks=a.max, budget_s=a.budget_s)
        else:
            ap.print_help()
            return 2
        out = run.run()
    ok = not out["stopped"].startswith("stopped:")
    detail = (f"frame {out['frame']}, slice {out['slice']}: {out['asked']} asked, {out['answered']} answered "
              f"({out['new']} new, {out['already_held']} already held), {out['not_found']} not found, "
              f"{out['set_aside']} set aside; {out['stopped'] or 'done'}")
    print(f"{SOURCE}: {detail}")
    if a.night and a.database == "querynz_v4":
        jobrun.record(JOB, ok, detail, started, out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
