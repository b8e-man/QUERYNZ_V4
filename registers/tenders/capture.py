"""How this lane's documents arrive (plan 1.10). Two cases, one listing.

The source is the Ministry of Business, Innovation and Employment's open
data of award notices from the Government Electronic Tenders Service
(GETS): four CSV files for the current era (July 2019 on, refreshed
quarterly) and four for the historic era (July 2014 to June 2019, fixed),
each of award notices, supplier data, region by tender and product
categories, with a schema workbook beside them. Licence CC BY 3.0 NZ, the
attribution required (the government data catalogue's own description of
the package, `catalogue.data.govt.nz` package_show, landed here).

Case 1, `copy`: the old estate's raw acquisition of 14 August 2026, kept
verbatim at `~/source-raws/gets-2026-08-14/` on node2 (the old estate's
`ops/retired/ingest_gets_open_data.py` loaded its tables from it), copied
by hash, read-only, the old path one of each document's names. The hashes
are pinned (`OLD_RAWS`); a file whose bytes differ is not landed. Those
bytes were fetched by the old estate with a browser-like User-Agent past an
Incapsula challenge that meets a plain one: the new estate never does that
(hard limit 6), and whether it keeps the old copy is on the queue.

Case 3, `refresh`: the quarterly job. One request for the catalogue's
description of the package (`CATALOGUE`), landed; then each file it lists,
through the fetch gate with the estate's one User-Agent, one at a time,
each once a quarter (`REFRESH_DAYS`): a set whose current file was
acquired within that window is not asked for again, and a run with nothing
due asks nothing, not even the catalogue. After a block or a challenge the
host rests a week (`BLOCK_REST_DAYS`) before it is asked again. A 404 on the catalogue's upper-case name is followed by
one request for the lower-case name the publisher's assets carry (the old
estate's note of 14 August 2026). A 403, a 429, a challenge page or a 5xx
showing a challenge is a failed read (hard limit 6): one catch-log line and
the run STOPS. Nothing is retried in the same run, solved or got around.
A body that is not a CSV a profile recognises is set aside, not listed.
On 21 October 2026 the ministry's host answered 403 to both files asked
and `www.data.govt.nz` showed an Incapsula challenge; the catalogue
answered. The historic files are fixed and never asked for again.

A release is one run: the reading takes, per era, the newest run that holds
all four of its files, so a refresh stopped half-way never mixes quarters.

Every line printed is a count or a status. No row is ever printed.

    python -m registers.tenders.capture --copy          # case 1, once
    python -m registers.tenders.capture --refresh       # case 3, the quarterly job
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
from zoneinfo import ZoneInfo

import support.fetchgate as fg

SOURCE = SCHEMA = "tenders"
JOB = "qv4-tenders-refresh"
HERE = os.path.dirname(os.path.abspath(__file__))
#: the draft position sits in the lane folder until the integrator moves it to docs/legal/positions/
#: (ruling 61); then this goes back to None, the gate's default
POSITIONS = None   # the position moved to docs/legal/positions/ at the merge of tenders-1; None is the gate's own folder
NZ = ZoneInfo("Pacific/Auckland")
PACKAGE = "new-zealand-government-procurement-award-notices"
CATALOGUE = f"https://catalogue.data.govt.nz/api/3/action/package_show?id={PACKAGE}"
REFRESH_DAYS = 80                 # a quarter, less a fortnight: a set acquired within it is not asked for again
BLOCK_REST_DAYS = 7               # after a block or a challenge, a week before the host is asked again
FLOOR_S = 10.0                    # rest after each answer; the gate's own floor (the catalogue's crawl delay) binds too
OFF_PEAK = (22, 6)
STOP_AFTER_FAILURES = 2
SETS = {"award-notices": "notices", "supplier-data": "suppliers", "region-by-tender": "regions",
        "product-categories": "categories"}
OLD_DIR = os.path.expanduser("~/source-raws/gets-2026-08-14")
OLD_ACQUIRED = "2026-08-14T07:40:00+12:00"
#: the old estate's raw acquisition: file name → sha256, read 21 October 2026 (sha256sum)
OLD_RAWS = {
    "gets-award-notices.csv": "a6528eaaec0ed549f6cc7b665f1051c3f827e72306ddcb3a5457ee8624912364",
    "gets-award-notices-historic.csv": "dcf55d3f4705c481db30a9fb584b6b3c863695d8c07c2984d00eabcafeca1fed",
    "gets-product-categories.csv": "e03993a5ebb05ca4ceffe29e532b8364b7ff86d042e3583249b89d6bd3b4adb2",
    "gets-product-categories-historic.csv": "db1b426c0a1b6caabdb6b1e3e5c57b875ec82cb87061b15ff287c42175f42d8e",
    "gets-region-by-tender.csv": "b63aa4eba21d030bccf5717add3f21c6168f41cf50d71fc5b95ee93fd37767fd",
    "gets-region-by-tender-historic.csv": "99b375f4ab2927d1703356cc0e9a14b22e0005abc9ec87b33ec9d234e6605a60",
    "gets-supplier-data.csv": "412cd7cd3f8069e639cb6f369ca3d20497ed0d52e1c9f7661c80434bd843a675",
    "gets-supplier-data-historic.csv": "5d286f9ab56ea608b78ec29c31acef6e56013211d69aa0494f2317ddc3cb761c",
    "schema-and-documentation.xlsx": "ac1f4c17db225453841f3db0ddcb6d86f82b9f19701a2cd50b8382a648940a0e",
}
#: the catalogue's description, fetched once through the gate by this session on 21 October 2026 (15:57 NZDT) while
#: the position was drafted; landed from the session's scratch copy so it is not fetched twice
PROBED = {"name": CATALOGUE, "sha256": "2ed62b084adbf7f4dd00b12f8b819a111a7d73d801c17e732cca1451f352606d",
          "at": "2026-10-21T15:57:00+13:00", "path": "/home/user/querynzv4-work/scratch/tenders-1/probe"}
#: the session's failed reads of 21 October 2026, recorded in the first copy run's catch log
PROBE_FAILURES = (
    ("https://www.mbie.govt.nz/assets/Data-Files/NZGPP-GETS-Open-Data/GETS-product-categories.csv",
     "HTTP 403: a block or a challenge; a challenged read is a failed read (hard limit 6)"),
    ("https://www.mbie.govt.nz/assets/Data-Files/NZGPP-GETS-Open-Data/gets-product-categories-historic.csv",
     "HTTP 403: a block or a challenge; a challenged read is a failed read (hard limit 6)"),
    ("https://www.data.govt.nz/about/terms-of-use/",
     "a challenge page ('incapsula'); a challenged read is a failed read (hard limit 6)"),
)


# ── pure pieces ───────────────────────────────────────────────────────────────

def classify(name: str):
    """(role, set, era) from a file's name or URL, as the publisher names its
    files; (None, None, None) for a name this lane does not hold."""
    base = urllib.parse.unquote(os.path.basename(urllib.parse.urlsplit(name).path or name)).lower()
    if base.startswith("schema-and-documentation"):
        return "dictionary", None, None
    if not base.endswith(".csv") or not base.startswith("gets-"):
        return None, None, None
    stem = base[len("gets-"):-len(".csv")]
    era = "historic" if stem.endswith("-historic") else "current"
    stem = stem[:-len("-historic")] if era == "historic" else stem
    s = SETS.get(stem)
    return ("data", s, era) if s else (None, None, None)


def listed_files(body: bytes) -> list:
    """The catalogue's own list of the package's files: [(name, url)] for
    every CSV resource, from a package_show answer."""
    j = json.loads(body)
    if not j.get("success") or "result" not in j:
        raise ValueError("not a package_show answer")
    out = []
    for r in j["result"].get("resources") or []:
        url = r.get("url") or ""
        if (r.get("format") or "").upper() == "CSV" or url.lower().endswith(".csv"):
            out.append((r.get("name") or "", url))
    return out


def licence_of(body: bytes) -> dict:
    r = json.loads(body)["result"]
    return {"id": r.get("license_id"), "title": r.get("license_title"), "url": r.get("license_url")}


def lower_name(url: str) -> str:
    """The same URL with its file name in lower case (the publisher's asset names)."""
    p = urllib.parse.urlsplit(url)
    head, _, base = p.path.rpartition("/")
    return urllib.parse.urlunsplit((p.scheme, p.netloc, f"{head}/{base.lower()}", p.query, p.fragment))


def looks_like_csv(body: bytes) -> bool:
    head = body[:512].lstrip(b"\xef\xbb\xbf").lstrip()
    return bool(head) and not head.startswith(b"<") and b"," in head.split(b"\n", 1)[0]


def off_peak(now_local: dt.datetime) -> bool:
    start, end = OFF_PEAK
    return now_local.hour >= start or now_local.hour < end


# ── the capture's tables ──────────────────────────────────────────────────────

READING = "-- ── the reading"


def tables_sql(schema: str = SCHEMA) -> str:
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        text = f.read().split(READING)[0]
    return text.replace("tenders_private", f"{schema}_private").replace(f"{SCHEMA}.", f"{schema}.") \
        .replace("SCHEMA IF NOT EXISTS tenders;", f"SCHEMA IF NOT EXISTS {schema};")


class Tables:
    """The capture's record over a connection in autocommit mode."""

    def __init__(self, conn, schema: str = SCHEMA):
        self.conn, self.s = conn, schema

    def create(self):
        self.conn.execute(tables_sql(self.s))

    def try_lock(self) -> bool:
        return bool(self.conn.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (JOB,)).fetchone()[0])

    def begin(self, mode: str) -> int:
        return self.conn.execute(f"INSERT INTO {self.s}.capture_runs (mode) VALUES (%s) RETURNING run_id",
                                 (mode,)).fetchone()[0]

    def finish(self, run_id, counts, stopped=""):
        self.conn.execute(f"UPDATE {self.s}.capture_runs SET finished_at = now(), requests = %s, landed = %s, "
                          "set_aside = %s, stopped = %s WHERE run_id = %s",
                          (counts["requests"], counts["landed"], counts["set_aside"], stopped or None, run_id))

    def add_file(self, run_id, name, url, ref, new, how, held_from, acquired_at):
        role, s, era = classify(name if how == "old-raw" else url)
        if url == CATALOGUE or name == CATALOGUE:
            role = "catalogue"
        self.conn.execute(
            f"INSERT INTO {self.s}.capture_files (run_id, name, url, sha256, size, role, set_name, era, how, "
            "held_from, acquired_at, new) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (run_id, name, url, ref.sha256, ref.size, role, s, era, how, held_from, acquired_at, new))

    def set_aside(self, run_id, item, stage, reason):
        self.conn.execute(f"INSERT INTO {self.s}.capture_set_aside (run_id, item, stage, reason) VALUES (%s, %s, %s, %s)",
                          (run_id, item, stage, reason[:500]))

    def acquired_since(self, set_name: str, since: dt.datetime) -> bool:
        """A current file of this set acquired (fetched by the ministry's
        clock, or by the old estate) since then."""
        return self.conn.execute(f"SELECT 1 FROM {self.s}.capture_files WHERE role = 'data' AND era = 'current' "
                                 "AND set_name = %s AND acquired_at >= %s LIMIT 1", (set_name, since)).fetchone() is not None

    def blocked_since(self, since: dt.datetime) -> bool:
        return self.conn.execute(f"SELECT 1 FROM {self.s}.capture_set_aside WHERE stage = 'fetch' AND at >= %s "
                                 "AND (reason LIKE '%%hard limit 6%%') LIMIT 1", (since,)).fetchone() is not None


# ── case 1: the old estate's raw files, by hash ──────────────────────────────

def copy_old(tables, land_fn, old_dir: str = OLD_DIR, pins: dict = None, probed: dict = PROBED, log=print) -> dict:
    """Land the pinned raw files from the old estate's folder, read-only, and
    the catalogue answer this session fetched. A file missing or with other
    bytes is a catch-log line, never landed."""
    from support.docstore import sha256_bytes
    pins = OLD_RAWS if pins is None else pins
    run = tables.begin("copy")
    counts = {"requests": 0, "landed": 0, "already_held": 0, "set_aside": 0}
    for name, sha in pins.items():
        path = os.path.join(old_dir, name)
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as exc:
            tables.set_aside(run, path, "copy", f"not readable: {type(exc).__name__}")
            counts["set_aside"] += 1
            continue
        if sha256_bytes(data) != sha:
            tables.set_aside(run, path, "copy", "its bytes are not the pinned ones: not landed")
            counts["set_aside"] += 1
            continue
        ref, new = land_fn(data, name=name, name_kind="file", fetched_at=OLD_ACQUIRED,
                           content_type="text/csv" if name.endswith(".csv") else "")
        land_fn(data, name=path, name_kind="old-path", fetched_at=OLD_ACQUIRED)
        tables.add_file(run, name, None, ref, new, "old-raw", path, OLD_ACQUIRED)
        counts["landed" if new else "already_held"] += 1
    if probed:
        path = os.path.join(probed["path"], probed["sha256"])
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            data = None
        if data is not None and sha256_bytes(data) == probed["sha256"]:
            ref, new = land_fn(data, name=probed["name"], name_kind="url", fetched_at=probed["at"],
                               content_type="application/json")
            tables.add_file(run, probed["name"], probed["name"], ref, new, "fetched", probed["name"], probed["at"])
            counts["landed" if new else "already_held"] += 1
        for url, why in PROBE_FAILURES:
            tables.set_aside(run, url, "fetch", f"21 October 2026, this session's probe: {why}")
            counts["set_aside"] += 1
    tables.finish(run, {**counts, "landed": counts["landed"]})
    log(f"{SOURCE}: copy run {run}: {counts['landed']} landed, {counts['already_held']} already held, "
        f"{counts['set_aside']} set aside")
    return {**counts, "run_id": run}


# ── case 3: the quarterly refresh through the gate ────────────────────────────

class Stop(RuntimeError):
    """The run stops here: a block, a challenge, or the host not answering."""


class Refresh:
    def __init__(self, tables, *, land_fn, opener=None, clock=None, sleep=None, now=None, anytime=False, log=print):
        self.t, self.land_fn, self.log = tables, land_fn, log
        self.opener = opener or (lambda url, timeout: fg.open_url(url, timeout=timeout, positions_dir=POSITIONS))
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.now = now or (lambda: dt.datetime.now(NZ))
        self.anytime = anytime
        self.last_end = None
        self.failures = 0
        self.run_id = None
        self.counts = {"requests": 0, "landed": 0, "already_held": 0, "set_aside": 0, "skipped": 0}

    def aside(self, item, stage, why):
        self.t.set_aside(self.run_id, item, stage, why)
        self.counts["set_aside"] += 1

    def get(self, url: str):
        """One gated request after the rest: the Fetched, or None on a 404 or a
        lone transport failure; Stop on a block or a challenge."""
        if self.last_end is not None:
            gap = self.last_end + FLOOR_S - self.clock()
            if gap > 0:
                self.sleep(gap)
        self.counts["requests"] += 1
        try:
            f = self.opener(url, 300)
        except fg.Refused:
            raise
        except Exception as exc:  # noqa: BLE001 — a transport failure is a line; two in a row a stop
            self.last_end = self.clock()
            self.failures += 1
            self.aside(url, "fetch", f"transport: {type(exc).__name__}: {str(exc)[:200]}")
            if self.failures >= STOP_AFTER_FAILURES:
                raise Stop(f"{self.failures} transport failures in a row")
            return None
        self.last_end = self.clock()
        self.failures = 0
        if f.blocked:
            self.aside(url, "fetch", f.blocked)
            raise Stop(f.blocked)
        if fg.host_of(f.final_url or url) != fg.host_of(url):
            why = f"redirected to {fg.host_of(f.final_url)}: not landed, and the run stops"
            self.aside(url, "fetch", why)
            raise Stop(why)
        if f.status != 200:
            self.aside(url, "fetch", f"HTTP {f.status}")
            return None
        return f

    def run(self) -> dict:
        now = self.now()
        if not self.anytime and not off_peak(now):
            return {**self.counts, "stopped": "not off-peak: nothing asked"}
        due = {s for s in SETS.values() if not self.t.acquired_since(s, now - dt.timedelta(days=REFRESH_DAYS))}
        if not due:
            return {**self.counts, "stopped": "not due: every current file acquired this quarter"}
        if self.t.blocked_since(now - dt.timedelta(days=BLOCK_REST_DAYS)):
            return {**self.counts, "stopped": f"resting: a block or a challenge within {BLOCK_REST_DAYS} days"}
        self.run_id = self.t.begin("refresh")
        stopped = ""
        try:
            f = self.get(CATALOGUE)
            if f is None:
                raise Stop("the catalogue's description could not be read")
            try:
                files = listed_files(f.body)
            except (ValueError, KeyError, TypeError) as exc:
                self.aside(CATALOGUE, "parse", f"not the catalogue's description: {type(exc).__name__}")
                raise Stop("the catalogue's answer could not be trusted")
            ref, new = self.land_fn(f.body, name=CATALOGUE, name_kind="url", fetched_at=None,
                                    content_type="application/json")
            self.t.add_file(self.run_id, CATALOGUE, CATALOGUE, ref, new, "fetched", CATALOGUE, now)
            self.counts["landed" if new else "already_held"] += 1
            for _, url in files:
                role, s, era = classify(url)
                if role != "data":
                    self.aside(url, "listing", "the catalogue lists a file this lane does not know: not fetched")
                    continue
                if era == "historic":
                    continue                       # fixed since 2019: held, never asked again
                if s not in due:
                    self.counts["skipped"] += 1    # acquired this quarter: not fetched twice
                    continue
                got = self.get(url)
                if got is None:
                    alt = lower_name(url)
                    if alt != url:
                        got = self.get(alt)
                if got is None:
                    continue
                if not looks_like_csv(got.body):
                    self.aside(url, "recognise", "the answer is not a CSV file: not landed")
                    continue
                ref, new = self.land_fn(got.body, name=os.path.basename(urllib.parse.urlsplit(got.url).path),
                                        name_kind="file", fetched_at=None, content_type="text/csv")
                self.land_fn(got.body, name=got.url, name_kind="url", content_type="text/csv")
                self.t.add_file(self.run_id, os.path.basename(urllib.parse.urlsplit(got.url).path), url, ref, new,
                                "fetched", got.url, now)
                self.counts["landed" if new else "already_held"] += 1
        except Stop as exc:
            stopped = f"stopped: {exc}"
        self.t.finish(self.run_id, self.counts, stopped)
        return {**self.counts, "stopped": stopped, "run_id": self.run_id}


def landing(conn):
    """land_fn(data, name, name_kind, fetched_at, content_type): the landing
    wrapper. Landing the same bytes again under another name adds the name
    and nothing more, which is how a document gets its second name."""
    from support.docstore.landing import land

    def land_fn(data, *, name, name_kind, fetched_at=None, content_type=""):
        return land(data, name=name, source=SOURCE, conn=conn, name_kind=name_kind, fetched_at=fetched_at,
                    content_type=content_type)
    return land_fn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m registers.tenders.capture")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--copy", action="store_true", help="case 1: the old estate's raw files, by hash (once)")
    g.add_argument("--refresh", action="store_true", help="case 3: the ministry's files through the gate")
    ap.add_argument("--anytime", action="store_true", help="refresh outside off-peak (by hand)")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default=SCHEMA)
    a = ap.parse_args(argv)
    from support import db, jobrun
    with db.connect(db.OWNER_KEY, a.database, autocommit=True) as conn:
        conn.execute("SET statement_timeout = '60s'")
        t = Tables(conn, a.schema)
        t.create()
        if not t.try_lock():
            print(f"{SOURCE}: another run holds the lane; this one asks for nothing")
            return 0
        if a.copy:
            out = copy_old(t, landing(conn))
            return 0 if out["set_aside"] <= len(PROBE_FAILURES) else 1
        started = jobrun.now()
        out = Refresh(t, land_fn=landing(conn), anytime=a.anytime).run()
    ok = not out["stopped"].startswith("stopped:")
    detail = (f"{out['requests']} requests, {out['landed']} landed, {out['already_held']} already held, "
              f"{out['skipped']} landed this quarter, {out['set_aside']} set aside; {out['stopped'] or 'done'}")
    print(f"{SOURCE}: {detail}")
    jobrun.record(JOB, ok, detail, started, out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
