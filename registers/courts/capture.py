"""How this lane's documents arrive (plan 1.10), two cases:

1. **Copied by hash from the old estate** (case one). The old estate holds
   the judgments it captured as PDFs under `/home/user/querynz-data/documents/`
   and lists them in its news database (`incoming_news.documents`: source,
   ref, URL, sha256, path). That listing was exported once, on 21 October
   2026, for the three sources this lane covers (courtsofnz.govt.nz,
   waitangitribunal.govt.nz, districtcourts.govt.nz), to one JSON-lines file
   (`export_listing`), landed by its hash and pinned here (`LISTING_SHA`).
   `copy_all` lands every listed file whose bytes still hash to the listed
   sha256 (`support.docstore.landing.copy_from_old`, read-only); a listed
   file that is gone, or whose bytes differ, is a catch-log line. Nothing is
   fetched, and the export is never run at load.

2. **Captured once, politely** (case three), the job `qv4-courts-capture`:
   each court's RSS feed on courtsofnz.govt.nz for cadence (`RSS`), the case
   page each item links to, and the judgment PDF on that page
   (`/assets/cases/…`, never the `MR-` media release), plus the listed
   judgments whose old file is gone (their URL is in the listing). Through
   `support.fetchgate.open_url` and the landing wrapper only, one request at
   a time, `FLOOR_S` apart, off-peak, nothing fetched twice. A block, a
   challenge or a redirect off the host stops the run (hard limit 6); the
   back-catalogue search (`/search/`) is never asked (plan 5.4 item 6). The
   gate refuses the host until the position in this folder
   (`legal-position-court-judgments.md`) is moved to `docs/legal/positions/`
   by the integrator. The District Court's judgments are not captured yet:
   its listing has not been looked at (card).

    export_listing()           the listing's bytes, read through the old read-only login
    copy_all(conn)             ([(entry, DocumentRef)], [(item, why)])
    python -m registers.courts.capture --export PATH     write the listing once
    python -m registers.courts.capture [--budget-s N] [--max-items N] [--anytime]   the capture job
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse

SOURCE = SCHEMA = "courts"
JOB = "qv4-courts-capture"
LISTING_NAME = "courts-listing-2026-10-21.jsonl"
LISTING_SHA = "8285d0068216f1675561dc260eb370ca9b6f1d78fae26e3d483d3a35aab79572"
EXPORTED_AT = "2026-10-21T14:44:31+13:00"
LISTING_NOTE = "copied by hash from the old estate's documents folder; listed by its news database"
OLD_SOURCES = ("courtsofnz.govt.nz", "waitangitribunal.govt.nz", "districtcourts.govt.nz")
HOST = "www.courtsofnz.govt.nz"
BASE = f"https://{HOST}"
COURTS = {"supreme-court": "NZSC", "court-of-appeal": "NZCA", "high-court": "NZHC"}
RSS = {code: f"{BASE}/judgments/{section}/RSS" for section, code in COURTS.items()}
FLOOR_S = 5.0
OFF_PEAK = (22, 6)
STOP_AFTER_FAILURES = 3
DEFAULT_BUDGET_S = 3600
ITEMS_PER_FEED = 60
HERE = os.path.dirname(os.path.abspath(__file__))

_LISTING_SQL = """
SELECT source, ref, url, filename, sha256, pdf_path, pages, char_count, status, created_at::text,
       suppressed_at IS NOT NULL
  FROM documents
 WHERE source = ANY(%s)
 ORDER BY source, ref, sha256
"""
_CASE_PDF = re.compile(r'href="(/assets/cases/[^"]+?\.pdf)"', re.I)
_RSS_LINK = re.compile(r"<link>\s*(https?://[^<\s]+/cases/[^<\s]+)\s*</link>")
_FILE_CITE = re.compile(r"(\d{4})-(NZ(?:SC|CA|HC))-(\d{1,5})", re.I)


# ── case one: the old estate's files ──────────────────────────────────────────

def export_listing(connect=None) -> bytes:
    """One line per listed document of the three sources, sorted; no text.
    Read-only, under a time limit; run once."""
    from support import db
    connect = connect or (lambda name: db.connect(db.OLD_READ_KEY, name, connect_timeout=10))
    lines = []
    with connect("incoming_news") as c:
        c.execute("SET statement_timeout = '60s'")
        for src, ref, url, fn, sha, path, pages, chars, status, created, supp in c.execute(_LISTING_SQL, (list(OLD_SOURCES),)):
            lines.append(json.dumps({"source": src, "ref": ref, "url": url, "file": fn, "sha256": sha, "old_path": path,
                                     "pages": pages, "chars": chars, "status": status, "captured_at": created,
                                     "old_suppressed": supp}, ensure_ascii=False, sort_keys=True))
    return ("\n".join(lines) + "\n").encode("utf-8")


def listing(data: bytes) -> list:
    return [json.loads(l) for l in data.decode("utf-8").splitlines() if l.strip()]


def land_listing(conn, sha: str = None):
    """The pinned listing, landed from the store (or the session's scratch
    folder where the once-only export wrote it). Returns (DocumentRef, entries)."""
    from support.docstore.landing import land, path_for, read_bytes
    sha = sha or LISTING_SHA
    if os.path.exists(path_for(sha)):
        data = read_bytes(sha)
    else:
        p = os.path.join(scratch_dir(), LISTING_NAME)
        if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != sha:
            raise LookupError(f"the courts listing {sha} is neither in the document store nor at {p}")
        data = open(p, "rb").read()
    ref, _ = land(data, name=LISTING_NAME, source=SOURCE, conn=conn, fetched_at=EXPORTED_AT)
    return ref, listing(data)


def scratch_dir() -> str:
    return os.environ.get("QV4_COURTS_EXPORT_DIR") or "/home/user/querynzv4-work/scratch/courts-1"


def copy_all(conn, entries: list, only: set = None, log=None) -> tuple:
    """Every listed file landed by hash: ([(entry, DocumentRef)], [(item, why)]).
    `only`: the sha256s to take (the sample's), None for all."""
    from support.docstore.landing import copy_from_old, path_for, read_bytes, land
    held, aside = [], []
    for e in entries:
        sha = e["sha256"]
        if only is not None and sha not in only:
            continue
        if os.path.exists(path_for(sha)):
            ref, _ = land(read_bytes(sha), name=e["file"] or e["url"], source=SOURCE, conn=conn,
                          fetched_at=e["captured_at"])
            held.append((e, ref))
            continue
        p = e.get("old_path")
        if not p or not os.path.exists(p):
            aside.append((sha, f"not held: the old estate lists {e['ref']} but its file is gone; the capture job fetches it"))
            continue
        with open(p, "rb") as f:
            got = hashlib.sha256(f.read()).hexdigest()
        if got != sha:
            aside.append((sha, f"not held: the old file for {e['ref']} hashes to {got[:12]}, not the listed hash"))
            continue
        ref, _ = copy_from_old(p, SOURCE, conn)
        if e.get("url"):
            land(read_bytes(ref.sha256), name=e["url"], source=SOURCE, conn=conn, name_kind="url",
                 fetched_at=e["captured_at"])        # the URL it was published at is one of its names
        held.append((e, ref))
    if log:
        log(f"courts: {len(held)} listed documents held, {len(aside)} not held")
    return held, aside


# ── case three: the capture job ───────────────────────────────────────────────

def case_links(rss: str) -> list:
    """The case pages an RSS feed links to, in feed order, once each."""
    return list(dict.fromkeys(_RSS_LINK.findall(rss or "")))


def judgment_pdfs(page: str) -> list:
    """The judgment PDFs a case page links to: (citation, absolute URL); a
    media release (`MR-…`) is never a judgment."""
    out = []
    for href in dict.fromkeys(_CASE_PDF.findall(page or "")):
        name = urllib.parse.unquote(href.rsplit("/", 1)[-1])
        if name.upper().startswith("MR-") or "media" in name.lower():
            continue
        m = _FILE_CITE.search(name)
        if not m:
            continue
        out.append((f"[{m.group(1)}] {m.group(2).upper()} {m.group(3)}", BASE + href))
    return out


def off_peak(now_local: dt.datetime) -> bool:
    start, end = OFF_PEAK
    return now_local.hour >= start or now_local.hour < end


class Stop(RuntimeError):
    """The run stops here: a block, a challenge, or the host not answering."""


class CaptureTables:
    """The capture job's own record, kept across loads (the reading's tables are
    wiped and rebuilt; these are not): what was found, fetched and refused."""

    def __init__(self, conn, schema: str = SCHEMA):
        self.conn, self.s = conn, schema

    def create(self):
        from registers.courts import load
        self.conn.execute(load.capture_tables_sql(self.s))

    def try_lock(self) -> bool:
        return bool(self.conn.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (JOB,)).fetchone()[0])

    def held(self, url: str) -> bool:
        """Landed by the job, or held under that URL already (a copied old file carries it as a name)."""
        from support.docstore.landing import find_by_name
        row = self.conn.execute(f"SELECT 1 FROM {self.s}.captures WHERE url = %s AND document IS NOT NULL", (url,)).fetchone()
        return row is not None or bool(find_by_name(url, self.conn))

    def found(self, citation, url, via):
        self.conn.execute(f"INSERT INTO {self.s}.captures (url, citation, found_via) VALUES (%s, %s, %s) "
                          "ON CONFLICT (url) DO NOTHING", (url, citation, via))

    def captured(self, url, sha):
        self.conn.execute(f"UPDATE {self.s}.captures SET document = %s, captured_at = now() WHERE url = %s", (sha, url))

    def feed(self, court, url, sha, items):
        self.conn.execute(f"INSERT INTO {self.s}.feeds (court, url, document, items) VALUES (%s, %s, %s, %s)",
                          (court, url, sha, items))

    def pending(self) -> list:
        return [(r[0], r[1]) for r in self.conn.execute(
            f"SELECT url, citation FROM {self.s}.captures WHERE document IS NULL "
            f"AND url NOT IN (SELECT item FROM {self.s}.capture_log WHERE stage = 'fetch') ORDER BY found_at, url")]

    def log(self, item, stage, reason):
        self.conn.execute(f"INSERT INTO {self.s}.capture_log (item, stage, reason) VALUES (%s, %s, %s)",
                          (item, stage, reason[:500]))


class Run:
    def __init__(self, tables, *, land_fn, opener=None, pacer=None, clock=None, now_local=None,
                 budget_s: float = DEFAULT_BUDGET_S, max_items: int = 200, anytime: bool = False, log=print):
        import support.fetchgate as fg
        self.fg = fg
        self.t, self.land_fn, self.opener = tables, land_fn, opener or fg.open_url
        self.pacer = pacer or fg.Pacer()
        self.clock = clock or time.monotonic
        self.now_local = now_local or (lambda: dt.datetime.now().astimezone())
        self.budget_s, self.max_items, self.anytime, self.log = budget_s, max_items, anytime, log
        self.started, self.failures, self.stopped = self.clock(), 0, ""
        self.counts = {"requests": 0, "feeds": 0, "found": 0, "landed": 0, "already_held": 0, "set_aside": 0}

    def time_left(self) -> bool:
        if self.clock() - self.started >= self.budget_s:
            self.stopped = self.stopped or "budget spent"
            return False
        if not self.anytime and not off_peak(self.now_local()):
            self.stopped = self.stopped or "off-peak is over"
            return False
        return True

    def get(self, url: str):
        """One gated, paced request; None on a transport failure (a catch-log
        line); Stop on a block, a challenge, a redirect off the host or three
        failures in a row. A gate refusal is never caught."""
        if "/search/" in url:
            raise Stop("the back-catalogue search is never asked (plan 5.4 item 6)")
        self.pacer.wait(HOST, FLOOR_S)
        self.counts["requests"] += 1
        try:
            f = self.opener(url, timeout=60)
        except self.fg.Refused:
            raise
        except Exception as exc:  # noqa: BLE001 — a transport failure is a line, three in a row a stop
            self.failures += 1
            self.t.log(url, "fetch", f"transport: {type(exc).__name__}: {str(exc)[:200]}")
            self.counts["set_aside"] += 1
            if self.failures >= STOP_AFTER_FAILURES:
                raise Stop(f"{self.failures} transport failures in a row")
            return None
        self.failures = 0
        if f.blocked:
            self.t.log(url, "fetch", f.blocked)
            self.counts["set_aside"] += 1
            if f.status >= 500 and not self.fg.looks_challenged(200, f.body or b""):
                # the server's own error, no challenge on the page: a failed read, and the run goes on
                # (lesson: a gate status verdict is not a block)
                return None
            raise Stop(f.blocked)
        if self.fg.host_of(f.final_url or url) != HOST:
            why = f"redirected to {self.fg.host_of(f.final_url)}: not landed, and the run stops"
            self.t.log(url, "fetch", why)
            raise Stop(why)
        return f

    def read_feeds(self):
        for court, url in RSS.items():
            if not self.time_left():
                return
            f = self.get(url)
            if f is None or f.status != 200:
                self.t.log(url, "feed", f"HTTP {getattr(f, 'status', 'none')}")
                continue
            ref, _ = self.land_fn(f.body, name=url, source=SOURCE, name_kind="url", content_type="application/rss+xml")
            links = case_links(f.body.decode("utf-8", "replace"))
            self.t.feed(court, url, ref.sha256, len(links))
            self.counts["feeds"] += 1
            for case in links[:ITEMS_PER_FEED]:
                if not self.time_left():
                    return
                page = self.get(case)
                if page is None or page.status != 200:
                    continue
                for citation, pdf in judgment_pdfs(page.body.decode("utf-8", "replace")):
                    if not self.t.held(pdf):
                        self.t.found(citation, pdf, "rss")
                        self.counts["found"] += 1

    def fetch_pending(self):
        done = 0
        for url, citation in self.t.pending():
            if done >= self.max_items or not self.time_left():
                return
            f = self.get(url)
            done += 1
            if f is None:
                continue
            if f.status != 200 or not f.body.startswith(b"%PDF"):
                self.t.log(url, "fetch", f"HTTP {f.status}" + ("" if f.status != 200 else ", not a PDF"))
                self.counts["set_aside"] += 1
                continue
            ref, new = self.land_fn(f.body, name=url, source=SOURCE, name_kind="url", content_type="application/pdf")
            self.t.captured(url, ref.sha256)
            self.counts["landed" if new else "already_held"] += 1

    def run(self, missing: list = ()) -> dict:
        """missing: (citation, url) of listed judgments whose old file is gone."""
        try:
            for citation, url in missing:
                self.t.found(citation, url, "listing")
            if self.time_left():
                self.read_feeds()
            self.fetch_pending()
        except Stop as exc:
            self.stopped = f"stopped: {exc}"
        return {**self.counts, "stopped": self.stopped}


def missing_from_listing(entries: list) -> list:
    """(citation, url) of each listed courtsofnz judgment whose old file is gone."""
    out = []
    for e in entries:
        if e["source"] == "courtsofnz.govt.nz" and not (e.get("old_path") and os.path.exists(e["old_path"])):
            m = _FILE_CITE.search(e["url"] or "")
            if m:
                out.append((f"[{m.group(1)}] {m.group(2).upper()} {m.group(3)}", e["url"]))
    return out


def landing(conn):
    from support.docstore.landing import land

    def land_fn(data, *, name, source, name_kind, content_type):
        return land(data, name=name, source=source, conn=conn, name_kind=name_kind, content_type=content_type)
    return land_fn


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--export" in argv:
        path = argv[argv.index("--export") + 1]
        if os.path.exists(path):
            print(f"{path} exists: the export is run once")
            return 1
        data = export_listing()
        with open(path, "wb") as f:
            f.write(data)
        print(f"{path}: {data.count(b'\n')} lines, sha256 {hashlib.sha256(data).hexdigest()}, "
              f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')}")
        return 0
    ap = argparse.ArgumentParser(prog="registers.courts.capture")
    ap.add_argument("--budget-s", type=float, default=DEFAULT_BUDGET_S)
    ap.add_argument("--max-items", type=int, default=200)
    ap.add_argument("--anytime", action="store_true", help="run outside off-peak (by hand, on purpose)")
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    from support import db, jobrun
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, a.database, autocommit=True) as conn:
        conn.execute("SET statement_timeout = '60s'")
        t = CaptureTables(conn)
        t.create()
        if not t.try_lock():
            jobrun.record(JOB, True, "skipped: another run holds the lane", started, {})
            return 0
        _, entries = land_listing(conn)
        out = Run(t, land_fn=landing(conn), budget_s=a.budget_s, max_items=a.max_items,
                  anytime=a.anytime).run(missing_from_listing(entries))
    ok = not out["stopped"].startswith("stopped:") or out["landed"] > 0     # a polite early stop that landed something is green
    detail = (f"{out['feeds']} feeds, {out['found']} found, {out['landed']} landed, {out['already_held']} already held, "
              f"{out['set_aside']} set aside; {out['stopped'] or 'done'}")
    print(f"courts: {detail}")
    jobrun.record(JOB, ok, detail, started, out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
