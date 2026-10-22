"""How this lane's documents arrive (plan 1.10): agencies' own lists of the
contracts they hold, as structured files on the government data catalogue.

The survey of 22 October 2026 (`survey.md`) found one collected file of
awards, the ministry's GETS award notices, already held by the tenders lane;
of 24 agencies' own sites surveyed by spend, nine refused or challenged us
and the rest send readers to GETS. The catalogue lists two agencies' files about
their contracts: ACC's "Health contract data" (CC BY 3.0 NZ; an Official
Information Act answer of claims and costs by contract class, region and
year, no supplier named) and MSD's contracted funding for 2019/20 (no
licence stated). A package is landed only
when the catalogue states an open licence that allows commercial use
(`OPEN_LICENCES`); MSD's is recorded and not landed (its position).

Case 3, `refresh` (the monthly job): one request for each package's
catalogue description (`package_show`), landed; then each CSV or XLSX
resource whose catalogue date or size is not one already held, one at a
time, through the fetch gate, the estate's one User-Agent, off-peak. A
redirect is never followed; a 403, 429 or a challenge is a failed read: a
catch-log line and the run STOPS (hard limit 6). Nothing is fetched twice:
a resource already held at the date the catalogue gives is not asked.

Case 1, `copy`: the files this session fetched on 22 October 2026, landed
from the document store by their pinned hashes (`PINNED`), so the live
database's first run does not fetch them again.

Every line printed is a count or a status. No row is ever printed.

    python -m registers.contract_disclosures.capture --copy
    python -m registers.contract_disclosures.capture --refresh [--anytime]
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
from zoneinfo import ZoneInfo

import support.fetchgate as fg

SOURCE = SCHEMA = "contract_disclosures"
JOB = "qv4-contract-disclosures-refresh"
HERE = os.path.dirname(os.path.abspath(__file__))
#: until the integrator moves `position/agency-contract-disclosures.md` to docs/legal/positions/, a session runs
#: with QV4_POSITIONS pointing at a folder holding it.
POSITIONS = os.environ.get("QV4_POSITIONS") or None
NZ = ZoneInfo("Pacific/Auckland")
CATALOGUE = "https://catalogue.data.govt.nz/api/3/action/package_show?id="
#: package → the agency that publishes it (as the catalogue names its organisation)
PACKAGES = {
    "health-contract-data": "Accident Compensation Corporation (ACC)",
    "msd-and-myd-contracted-funding-f20": "Ministry of Social Development",
}
#: licences that allow copying and commercial reuse with attribution (the catalogue's licence ids)
OPEN_LICENCES = ("CC-BY-4.0", "CC-BY-NZ-3.0", "CC-BY-3.0-NZ", "CC-BY-NZ-4.0", "cc-by", "CC0-1.0", "cc-zero")
FILE_FORMATS = ("CSV", "XLSX", "XLS")
FLOOR_S = 10.0                    # the catalogue's own crawl delay
OFF_PEAK = (22, 6)
REFRESH_DAYS = 28
BLOCK_REST_DAYS = 7
#: what this session fetched through the gate on 22 October 2026 (the two descriptions at 19:57 in the survey, the
#: file at 22:00), landed by hash (case 1): url → (sha256, package, role, resource, licence id)
_ACC_FILE = ("https://catalogue.data.govt.nz/dataset/0f9e53e8-cfcb-43c9-aa2f-0ba4b44a322b/resource/"
             "0a2cf78e-49b7-422a-aec9-1da83538e1bc/download/ar-3944-response.xlsx")
PINNED = {
    CATALOGUE + "health-contract-data": (
        "ad5219f9864e0f58679b458bdee32fad07f981e1826fb7a42de48ebc036e2307", "health-contract-data", "catalogue", None,
        "CC-BY-NZ-3.0"),
    _ACC_FILE: (
        "eef2490b6d7b333b64cdffa52bd5cab3b67a432f279f61fe1da95b6142db725d", "health-contract-data", "data",
        {"id": "0a2cf78e-49b7-422a-aec9-1da83538e1bc", "name": "Health Contract Data", "format": "XLSX",
         "modified": "2023-08-18T06:53:43.565340"}, "CC-BY-NZ-3.0"),
    CATALOGUE + "msd-and-myd-contracted-funding-f20": (
        "139f0d2215065886c6c2ba4aa9aeed2f062bba9cd6d4a41c69b9a07423f385c9", "msd-and-myd-contracted-funding-f20",
        "catalogue", None, ""),
}


# ── pure pieces ───────────────────────────────────────────────────────────────

def off_peak(t: dt.datetime) -> bool:
    h = t.astimezone(NZ).hour
    return h >= OFF_PEAK[0] or h < OFF_PEAK[1]


def package_of(body: bytes) -> dict:
    """The parts of a package_show answer the capture uses."""
    j = json.loads(body)
    if not j.get("success") or "result" not in j:
        raise ValueError("not a package_show answer")
    r = j["result"]
    files = []
    for x in r.get("resources") or []:
        fmt = (x.get("format") or "").upper().lstrip(".")
        if fmt in FILE_FORMATS:
            files.append({"id": x.get("id") or "", "name": x.get("name") or "", "url": x.get("url") or "",
                          "format": fmt, "modified": x.get("last_modified") or x.get("created") or "",
                          "size": x.get("size")})
    return {"name": r.get("name"), "organisation": (r.get("organization") or {}).get("title") or "",
            "licence_id": r.get("license_id") or "", "licence_title": r.get("license_title") or "",
            "modified": r.get("metadata_modified") or "", "files": files}


def licence_open(licence_id: str) -> bool:
    return (licence_id or "").strip().lower() in {x.lower() for x in OPEN_LICENCES}


def looks_like_file(body: bytes, fmt: str) -> bool:
    if fmt == "XLSX":
        return body[:4] == b"PK\x03\x04"
    if fmt == "XLS":
        return body[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    head = body[:512].lstrip(b"\xef\xbb\xbf").lstrip()
    return bool(head) and not head.startswith(b"<") and b"," in head.split(b"\n", 1)[0]


# ── the capture's tables ──────────────────────────────────────────────────────

READING = "-- ── the reading"


def table(schema: str, t: str, shared: bool = False) -> str:
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


_NAMES = re.compile(rf"(?<![A-Za-z0-9_]){SCHEMA}(_private)?\.")


def tables_sql(schema: str = SCHEMA) -> str:
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        text = f.read().split(READING)[0]
    return _NAMES.sub(lambda m: f"{schema}{m.group(1) or ''}.", text)


class Tables:
    """The capture's record over a connection in autocommit mode."""

    def __init__(self, conn, schema: str = SCHEMA):
        self.conn, self.s = conn, schema

    def create(self):
        self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.s}")
        self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.s}_private")
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

    def add_file(self, run_id, *, package, role, url, ref, new, how, resource=None, licence_id="", agency=""):
        r = resource or {}
        self.conn.execute(
            f"INSERT INTO {self.s}.capture_files (run_id, package, agency, role, url, sha256, size, resource_id, "
            "resource_name, resource_format, resource_modified, licence_id, how, new) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (run_id, package, agency, role, url, ref.sha256, ref.size, r.get("id"), r.get("name"), r.get("format"),
             r.get("modified"), licence_id, how, new))

    def set_aside(self, run_id, item, stage, reason):
        self.conn.execute(f"INSERT INTO {self.s}.capture_set_aside (run_id, item, stage, reason) "
                          "VALUES (%s, %s, %s, %s)", (run_id, item, stage, reason[:500]))

    def held(self, resource_id: str, modified: str) -> bool:
        return self.conn.execute(f"SELECT 1 FROM {self.s}.capture_files WHERE role = 'data' AND resource_id = %s "
                                 "AND resource_modified IS NOT DISTINCT FROM %s LIMIT 1",
                                 (resource_id, modified or None)).fetchone() is not None

    def asked_since(self, since) -> bool:
        return self.conn.execute(f"SELECT 1 FROM {self.s}.capture_runs WHERE mode = 'refresh' AND started_at >= %s "
                                 "AND requests > 0 LIMIT 1", (since,)).fetchone() is not None

    def blocked_since(self, since) -> bool:
        return self.conn.execute(f"SELECT 1 FROM {self.s}.capture_set_aside WHERE stage = 'fetch' AND at >= %s "
                                 "AND reason LIKE '%%hard limit 6%%' LIMIT 1", (since,)).fetchone() is not None


# ── case 1: what the session fetched, from the store by hash ─────────────────

def copy_pinned(tables, land_fn, read_bytes, pins: dict = None, log=print) -> dict:
    """Land each pinned document from the document store under its URL. A
    hash not in the store, or bytes that are not its hash, are catch-log
    lines, never landed."""
    from support.docstore import sha256_bytes
    pins = PINNED if pins is None else pins
    run = tables.begin("copy")
    counts = {"requests": 0, "landed": 0, "already_held": 0, "set_aside": 0}
    for url, (sha, package, role, resource, licence_id) in pins.items():
        try:
            data = read_bytes(sha)
        except OSError as exc:
            tables.set_aside(run, url, "copy", f"not in the document store: {type(exc).__name__}")
            counts["set_aside"] += 1
            continue
        if sha256_bytes(data) != sha:
            tables.set_aside(run, url, "copy", "its bytes are not the pinned ones: not landed")
            counts["set_aside"] += 1
            continue
        ref, new = land_fn(data, name=url, name_kind="url", content_type="")
        tables.add_file(run, package=package, role=role, url=url, ref=ref, new=new, how="copied",
                        resource=resource, licence_id=licence_id, agency=PACKAGES.get(package, ""))
        counts["landed" if new else "already_held"] += 1
    tables.finish(run, counts)
    log(f"{SOURCE}: copy run {run}: {counts['landed']} landed, {counts['already_held']} already held, "
        f"{counts['set_aside']} set aside")
    return {**counts, "run_id": run}


# ── case 3: the monthly refresh through the gate ──────────────────────────────

class Stop(RuntimeError):
    """The run stops here: a block, a challenge, a redirect off the host."""


class Refresh:
    def __init__(self, tables, *, land_fn, opener=None, clock=None, sleep=None, now=None, anytime=False,
                 packages=None, log=print):
        self.t, self.land_fn, self.log = tables, land_fn, log
        self.opener = opener or (lambda url, timeout: fg.open_url(url, timeout=timeout, positions_dir=POSITIONS,
                                                                  same_host_hops=0))
        self.pacer = fg.Pacer(now=clock or time.monotonic, sleep=sleep or time.sleep)
        self.now = now or (lambda: dt.datetime.now(NZ))
        self.anytime = anytime
        self.packages = PACKAGES if packages is None else packages
        self.run_id = None
        self.counts = {"requests": 0, "landed": 0, "already_held": 0, "set_aside": 0, "unchanged": 0,
                       "not_open": 0}

    def aside(self, item, stage, why):
        self.t.set_aside(self.run_id, item, stage, why)
        self.counts["set_aside"] += 1

    def get(self, url: str):
        """One gated request after the floor: the Fetched, or None on an
        answer that is not a 200; Stop on a block, a challenge or a redirect."""
        if not self.anytime and not off_peak(self.now()):
            raise Stop("off-peak is over")
        self.pacer.wait(fg.host_of(url), FLOOR_S)
        self.counts["requests"] += 1
        try:
            f = self.opener(url, 300)
        except fg.Refused:
            raise
        except Exception as exc:  # noqa: BLE001 — a transport failure is a line
            self.aside(url, "fetch", f"transport: {type(exc).__name__}: {str(exc)[:200]}")
            return None
        if f.blocked:
            self.aside(url, "fetch", f.blocked)
            raise Stop(f.blocked)
        if f.status in fg.REDIRECT_STATUSES:
            why = f"HTTP {f.status}, redirected to {fg.host_of(f.location) or 'nowhere'}: not followed"
            self.aside(url, "fetch", why)
            return None
        if f.status != 200 or not f.body:
            self.aside(url, "fetch", f"HTTP {f.status}")
            return None
        return f

    def run(self) -> dict:
        now = self.now()
        if not self.anytime and not off_peak(now):
            return {**self.counts, "stopped": "not off-peak: nothing asked"}
        if self.t.asked_since(now - dt.timedelta(days=REFRESH_DAYS)):
            return {**self.counts, "stopped": f"not due: asked within {REFRESH_DAYS} days"}
        if self.t.blocked_since(now - dt.timedelta(days=BLOCK_REST_DAYS)):
            return {**self.counts, "stopped": f"resting: a block or a challenge within {BLOCK_REST_DAYS} days"}
        self.run_id = self.t.begin("refresh")
        stopped = ""
        try:
            for package, agency in self.packages.items():
                url = CATALOGUE + package
                f = self.get(url)
                if f is None:
                    continue
                try:
                    p = package_of(f.body)
                except (ValueError, KeyError, TypeError) as exc:
                    self.aside(url, "parse", f"not the catalogue's description: {type(exc).__name__}")
                    continue
                ref, new = self.land_fn(f.body, name=url, name_kind="url", content_type="application/json")
                self.t.add_file(self.run_id, package=package, role="catalogue", url=url, ref=ref, new=new,
                                how="fetched", licence_id=p["licence_id"], agency=agency)
                self.counts["landed" if new else "already_held"] += 1
                if not licence_open(p["licence_id"]):
                    self.counts["not_open"] += 1
                    self.aside(url, "licence", f"the catalogue states licence {p['licence_id'] or 'none'!r}: "
                                               "not an open licence that allows commercial use, so no file is landed")
                    continue
                for r in p["files"]:
                    if self.t.held(r["id"], r["modified"]):
                        self.counts["unchanged"] += 1
                        continue
                    got = self.get(r["url"])
                    if got is None:
                        continue
                    if not looks_like_file(got.body, r["format"]):
                        self.aside(r["url"], "recognise", f"the answer is not a {r['format']} file: not landed")
                        continue
                    ref, new = self.land_fn(got.body, name=r["url"], name_kind="url", content_type="")
                    self.t.add_file(self.run_id, package=package, role="data", url=r["url"], ref=ref, new=new,
                                    how="fetched", resource=r, licence_id=p["licence_id"], agency=agency)
                    self.counts["landed" if new else "already_held"] += 1
        except Stop as exc:
            stopped = f"stopped: {exc}"
        self.t.finish(self.run_id, self.counts, stopped)
        return {**self.counts, "stopped": stopped, "run_id": self.run_id}


def landing(conn):
    """land_fn(data, name, name_kind, content_type): the landing wrapper."""
    from support.docstore.landing import land

    def land_fn(data, *, name, name_kind, content_type=""):
        return land(data, name=name, source=SOURCE, conn=conn, name_kind=name_kind, content_type=content_type)
    return land_fn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m registers.contract_disclosures.capture")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--copy", action="store_true", help="case 1: the session's fetches, from the store by hash")
    g.add_argument("--refresh", action="store_true", help="case 3: the catalogue's packages through the gate")
    ap.add_argument("--anytime", action="store_true", help="outside off-peak (by hand)")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default=SCHEMA)
    a = ap.parse_args(argv)
    from support import db, jobrun
    from support.docstore.landing import read_bytes
    with db.connect(db.OWNER_KEY, a.database, autocommit=True) as conn:
        conn.execute("SET statement_timeout = '60s'")
        t = Tables(conn, a.schema)
        t.create()
        if not t.try_lock():
            print(f"{SOURCE}: another run holds the lane; this one asks for nothing")
            return 0
        if a.copy:
            out = copy_pinned(t, landing(conn), read_bytes)
            return 0 if out["set_aside"] == 0 else 1
        started = jobrun.now()
        out = Refresh(t, land_fn=landing(conn), anytime=a.anytime).run()
    ok = not out["stopped"].startswith("stopped:")
    detail = (f"{out['requests']} requests, {out['landed']} landed, {out['already_held']} already held, "
              f"{out['unchanged']} unchanged, {out['not_open']} packages not under an open licence, "
              f"{out['set_aside']} set aside; {out['stopped'] or 'done'}")
    print(f"{SOURCE}: {detail}")
    if a.database == "querynz_v4":
        jobrun.record(JOB, ok, detail, started, out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
