"""How this lane's documents arrive (plan 1.10, case two: only text is held).

The old estate holds every Gazette notice it captured as article text in the
news database (`incoming_news.articles`, the rows whose address is a
`gazette.govt.nz/notice/id/` page), and its own classification of each in
`nzbn_canonical.gazette.notices`. Both were exported once, on 20 October
2026, to one JSON-lines file (`export_notices`), the way
`registers/parties/capture.py` exported the register's notices, and that
file is the document: every row read from it is "taken from the old
estate's tables; original not held", and cites the export's hash and the
Gazette's own notice number. The export's hash is pinned here; a second
export would be a new document and a new pin. Nothing is fetched, and the
export is never run at load.

One line per article row, so a notice the old estate captured twice is two
lines with one notice number (read.py keeps one and logs the other).

Every notice since then comes from DigitalNZ (2 November 2026, Arthur: "fix
the gazette notices and appointments gathering & ingestion"). Its "New
Zealand Gazette" collection carries one record per notice with the notice's
full text, and that text is the same text the old estate read from the
notice's own page: on 100 notices of October 2026 compared, all 100 equal
once the white space is folded. The Gazette's own pages answer the estate
with an Incapsula challenge (2 November 2026), which is a failed read
(hard limit 6), so they are not asked. Each DigitalNZ answer (one page of up
to 100 records) is landed once by hash and is the document behind every row
read from it (`capture_pages`). A notice the export holds is read from the
export; a notice the Gazette's robots file disallows by number (a
suppression request) is never read.

    forward     newest first, the current year's pages until a page holds no
                notice not held (and the year before in January)
    backwalk    per year, DigitalNZ's count against the notices held; a short
                year is paged until its gap is closed or the night's requests
                are spent. A year paged to its end that gave nothing new is
                recorded (`capture_years`) and skipped while its count stands

    export_notices()         the export's bytes, read through the old read-only login
    copy_all(conn)           land the export: ([(kind, DocumentRef, name, captured at)], [(item, why)])
    capture(conn, ...)       one night's DigitalNZ capture: counts
    pages_held(conn)         the landed DigitalNZ pages, oldest first: [(sha256, asked_at)]
    lines_of_page(data, sha) the export-shaped lines of one landed page
    python -m registers.gazette.capture --export PATH    write the export once
    python -m registers.gazette.capture --night [--anytime] [--requests N] [--budget-s N] [--no-backwalk]
"""
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.parse

from support.docstore.landing import land, path_for, read_bytes

SOURCE = "gazette"
EXPORT_NAME = "gazette-notices-2026-10-20.jsonl"
EXPORT_SHA = "47de7e0963b32e1e54d3a5ca4bea6a54af6e3f57dae8611354aa56ae58b73a95"
EXPORTED_AT = "2026-10-20T04:49:11+13:00"
EXPORT_NOTE = "taken from the old estate's tables; original not held"

_NOTICE_ID = re.compile(r"/notice/id/([^/?#]+)")

#: Both tables are the OLD databases', reached through the old read-only
#: login: the search path names the old schema so the query is not mistaken
#: for one into this estate's gazette lane (tests/test_imports_one_way.py).
_OLD_SCHEMA = "SET search_path TO gazette"
_NOTICES_SQL = "SELECT notice_id, published_date::text, notice_type, article_id FROM notices"
_ARTICLES_SQL = """
SELECT id::text, news_url, title, text_content, post_date_nz::date::text
  FROM articles
 WHERE news_url LIKE '%%gazette.govt.nz/notice/id/%%'
"""


def notice_of(url: str):
    m = _NOTICE_ID.search(url or "")
    return m.group(1) if m else None


def export_notices(connect=None) -> bytes:
    """One line per article row, sorted by notice number then article:
    the notice number, the day the old classifier says it was published (else
    the article's post day), the old type, its title, address and text.
    Read-only, every statement under a time limit; run once."""
    from support import db
    connect = connect or (lambda name: db.connect(db.OLD_READ_KEY, name, connect_timeout=10))
    with connect("nzbn_canonical") as c:
        c.execute("SET statement_timeout = '60s'")
        c.execute(_OLD_SCHEMA)
        typed = {r[0]: r for r in c.execute(_NOTICES_SQL).fetchall()}
    lines = []
    with connect("incoming_news") as c:
        c.execute("SET statement_timeout = '60s'")
        with c.transaction():
            cur = c.cursor(name="gazette_export")
            cur.itersize = 2000
            cur.execute(_ARTICLES_SQL)
            for aid, url, title, text, posted in cur:
                nid = notice_of(url)
                t = typed.get(nid)
                lines.append((nid or "", aid, json.dumps({
                    "notice": nid, "article": aid, "url": url, "title": html.unescape(title or ""),
                    "published_on": t[1] if t else posted, "posted_on": posted,
                    "old_type": t[2] if t else None, "old_article": t[3] if t else None,
                    "text": text or ""}, ensure_ascii=False, sort_keys=True)))
    lines.sort()
    return ("\n".join(l for _, _, l in lines) + "\n").encode("utf-8")


def copy_all(conn, export_sha: str = None, log=None) -> tuple:
    """The export landed from the store. Returns
    ([(kind, DocumentRef, name, captured at)], [(item, why)])."""
    sha = export_sha or EXPORT_SHA
    if not sha or not os.path.exists(path_for(sha)):
        raise LookupError(f"the notices export {sha} is not in the document store")
    ref, new = land(read_bytes(sha), name=EXPORT_NAME, source=SOURCE, conn=conn, fetched_at=EXPORTED_AT)
    if log:
        log(f"gazette: {'landed' if new else 'held'} {ref.sha256[:12]} {EXPORT_NAME}")
    return [("notices", ref, EXPORT_NAME, EXPORTED_AT)], []


# ── DigitalNZ: every notice after the export ──────────────────────────────────────────────────────────────────────

JOB = "qv4-gazette-capture"
DNZ_API = "https://api.digitalnz.org/v3/records.json"
COLLECTION = "New Zealand Gazette"
FIELDS = "id,title,dc_identifier,landing_url,date,fulltext"
PER_PAGE = 100
FLOOR_YEAR = 2000                       # DigitalNZ's Gazette coverage begins here
FLOOR_S = 5.0                           # the position's floor between requests (docs/legal/positions/digitalnz-api.md)
OFF_PEAK = (22, 7)                      # NZ local hours: from 22:00 to 07:00
RECHECK_DAYS = 30                       # a year counted whole is counted again after this many days
DNZ_NOTE = "read from DigitalNZ's record of the Gazette notice (its full text)"
ROBOTS = "https://gazette.govt.nz/robots.txt"
#: the notices the Gazette's robots file disallowed by number on 2 November 2026 (suppression requests); each
#: night's robots file adds to these, and none is ever read
SUPPRESSED = frozenset({"2012-ba4936", "2003-ba4319"})
_NOTICE_NO = re.compile(r"Notice Number:\s*(\d{4}-[a-z]+\d+)", re.I)
_ID_IN_URL = re.compile(r"/notice/id/(\d{4}-[a-z]+\d+)", re.I)

CAPTURE_SQL = """
CREATE SCHEMA IF NOT EXISTS {s};
-- every DigitalNZ answer asked: the capture's own record, kept across loads (load.py never drops it)
CREATE TABLE IF NOT EXISTS {s}.{p}capture_pages (
    asked_id      bigserial PRIMARY KEY,
    asked_at      timestamptz NOT NULL DEFAULT now(),
    mode          text NOT NULL,                     -- forward | backwalk | count
    year          integer NOT NULL,
    page          integer NOT NULL,
    status        integer,                           -- the HTTP status; NULL when nothing answered
    blocked       text,                              -- why the read failed, if it did
    result_count  integer,                           -- DigitalNZ's count for the year
    records       integer NOT NULL DEFAULT 0,
    notices       text[] NOT NULL DEFAULT '{{}}',    -- the notice numbers the answer carries
    new_notices   integer NOT NULL DEFAULT 0,        -- of those, not held when asked
    sha256        text CHECK (sha256 IS NULL OR sha256 ~ '^[0-9a-f]{{64}}$')
);
-- a year paged to its end that gave nothing new, at DigitalNZ's count then: skipped while the count stands
CREATE TABLE IF NOT EXISTS {s}.{p}capture_years (
    year        integer PRIMARY KEY,
    dnz_count   integer NOT NULL,
    held        integer NOT NULL,
    walked_at   timestamptz NOT NULL DEFAULT now()
);
-- every notice the Gazette's robots file has disallowed by number: never read
CREATE TABLE IF NOT EXISTS {s}.{p}capture_suppressed (
    notice   text PRIMARY KEY,
    seen_at  timestamptz NOT NULL DEFAULT now()
);
"""


def ctable(schema: str, t: str, shared: bool = False) -> str:
    return f"{schema}.{SOURCE}_{t}" if shared else f"{schema}.{t}"


def capture_tables(conn, schema: str = SOURCE, shared: bool = False) -> None:
    conn.execute(CAPTURE_SQL.format(s=schema, p=f"{SOURCE}_" if shared else ""))


def off_peak(t: dt.datetime) -> bool:
    """Off-peak in New Zealand: from 22:00 to 07:00 local time."""
    from zoneinfo import ZoneInfo
    h = t.astimezone(ZoneInfo("Pacific/Auckland")).hour if t.tzinfo else t.hour
    return h >= OFF_PEAK[0] or h < OFF_PEAK[1]


def notice_of_record(rec: dict):
    """A DigitalNZ record's notice number, lower case: its identifier, else its landing page; None when neither
    names one or the landing page is not the Gazette's."""
    url = rec.get("landing_url") or ""
    if "gazette.govt.nz" not in url:
        return None
    nid = next((m.group(1) for i in (rec.get("dc_identifier") or []) if (m := _NOTICE_NO.search(i or ""))), None)
    if not nid:
        m = _ID_IN_URL.search(url)
        nid = m.group(1) if m else None
    return nid.lower() if nid else None


def records_of(data: bytes) -> tuple:
    """(result_count, records) of one landed DigitalNZ answer."""
    s = json.loads(data.decode("utf-8"))["search"]
    return s.get("result_count") or 0, s.get("results") or []


def lines_of_page(data: bytes, sha: str) -> list:
    """The export-shaped lines of one landed answer, one per record that names a notice; each names its document.
    The text is folded to single spaces, as the old capture folded the page's text."""
    out = []
    for rec in records_of(data)[1]:
        nid = notice_of_record(rec)
        if not nid:
            continue
        day = next((d[:10] for d in (rec.get("date") or []) if d), None)
        out.append({"notice": nid, "article": f"digitalnz:{rec.get('id')}", "old_article": None, "old_type": None,
                    "url": f"https://gazette.govt.nz/notice/id/{nid}",
                    "title": " ".join(html.unescape(rec.get("title") or nid).split()),
                    "published_on": day, "posted_on": day, "text": " ".join((rec.get("fulltext") or "").split()),
                    "_document": sha, "_note": DNZ_NOTE})
    return out


def export_notice_ids(sha: str = None) -> set:
    """The notice numbers the pinned export holds, read from its lines without parsing them."""
    out = set()
    with open(path_for(sha or EXPORT_SHA), "rb") as f:
        for l in f:
            i = l.find(b'"notice": "') + 11
            if i >= 11:
                out.add(l[i:l.find(b'"', i)].decode())
    return out


def pages_held(conn, schema: str = SOURCE, shared: bool = False) -> list:
    """[(sha256, asked_at)] of every landed DigitalNZ answer that carried a record, oldest first; [] before the first."""
    t = ctable(schema, "capture_pages", shared)
    if conn.execute("SELECT to_regclass(%s)", (t,)).fetchone()[0] is None:
        return []
    return [tuple(r) for r in conn.execute(
        f"SELECT sha256, min(asked_at) FROM {t} WHERE sha256 IS NOT NULL AND records > 0 GROUP BY 1 ORDER BY 2, 1")]


def suppressed_held(conn, schema: str = SOURCE, shared: bool = False) -> set:
    t = ctable(schema, "capture_suppressed", shared)
    if conn.execute("SELECT to_regclass(%s)", (t,)).fetchone()[0] is None:
        return set(SUPPRESSED)
    return set(SUPPRESSED) | {r[0] for r in conn.execute(f"SELECT notice FROM {t}")}


class Night:
    """One night's asking: every request through the fetch gate, at most `requests`, one at a time, FLOOR_S apart;
    a failed read (a block, a challenge, no answer) stops the night."""

    def __init__(self, conn, schema=SOURCE, shared=False, *, requests=400, budget_s=3000.0, open_url=None,
                 sleep=time.sleep, clock=time.monotonic, positions_dir=None, root=None, log=print):
        from support import fetchgate
        self.conn, self.s, self.shared, self.log, self.root = conn, schema, shared, log, root
        self.left, self.deadline, self.clock, self.sleep = requests, clock() + budget_s, clock, sleep
        self.open = open_url or (lambda u: fetchgate.open_url(u, positions_dir=positions_dir, timeout=60))
        self.last = None
        self.stopped = ""
        self.counts = {"requests": 0, "pages landed": 0, "pages held": 0, "records": 0, "new notices": 0}
        self.held = set()

    def T(self, t):
        return ctable(self.s, t, self.shared)

    def spent(self) -> str:
        if self.stopped:
            return self.stopped
        if self.left <= 0:
            return "the night's requests are spent"
        if self.clock() >= self.deadline:
            return "the budget is spent"
        return ""

    def get(self, url: str):
        if self.last is not None:
            gap = FLOOR_S - (self.clock() - self.last)
            if gap > 0:
                self.sleep(gap)
        self.left -= 1
        self.counts["requests"] += 1
        try:
            f = self.open(url)
        except Exception as exc:  # noqa: BLE001 — a refusal or no answer is a failed read; the night stops
            self.last = self.clock()
            self.stopped = f"a failed read: {type(exc).__name__}: {str(exc)[:160]}"
            return None
        self.last = self.clock()
        if f.blocked or f.status != 200:
            self.stopped = f"a failed read: {f.blocked or f'HTTP {f.status}'} at {url[:120]}"
        return f

    def robots(self) -> bool:
        """The Gazette's robots file: every notice it disallows by number recorded as suppressed. Unreadable, the
        night does not run (a suppression request can only be honoured if it can be read)."""
        f = self.get(ROBOTS)
        if f is None or self.stopped:
            self.stopped = "the Gazette's robots file could not be read, so its suppressions are not known: " + self.stopped
            return False
        ids = {m.group(1).lower() for line in f.body.decode("utf-8", "replace").splitlines()
               if line.lower().startswith("disallow:") and (m := _ID_IN_URL.search(line))}
        for n in sorted(ids):
            self.conn.execute(f"INSERT INTO {self.T('capture_suppressed')} (notice) VALUES (%s) ON CONFLICT DO NOTHING", (n,))
        self.counts["suppressed"] = len(ids | SUPPRESSED)
        return True

    def ask(self, mode: str, year: int, page: int, per_page: int = None):
        """One DigitalNZ page for one year, newest first: landed by hash, recorded. Returns (result_count, [notice
        numbers], new) or None on a failed read."""
        q = {"and[primary_collection][]": COLLECTION, "and[year][]": str(year),
             "per_page": str(PER_PAGE if per_page is None else per_page),
             "page": str(page), "sort": "date", "direction": "desc", "fields": FIELDS}
        url = f"{DNZ_API}?{urllib.parse.urlencode(q)}"
        f = self.get(url)
        if f is None or self.stopped:
            self.conn.execute(f"INSERT INTO {self.T('capture_pages')} (mode, year, page, status, blocked) VALUES "
                              "(%s, %s, %s, %s, %s)", (mode, year, page, f.status if f else None, self.stopped))
            return None
        count, recs = records_of(f.body)
        ids = [n for n in (notice_of_record(r) for r in recs) if n]
        new = [n for n in ids if n not in self.held]
        sha = None
        if recs:
            ref, landed = land(f.body, name=url, source=SOURCE, conn=self.conn, name_kind="url",
                               fetched_at=dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                               content_type="application/json", root=self.root)
            sha = ref.sha256
            self.counts["pages landed" if landed else "pages held"] += 1
        self.conn.execute(f"INSERT INTO {self.T('capture_pages')} (mode, year, page, status, result_count, records, "
                          "notices, new_notices, sha256) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                          (mode, year, page, f.status, count, len(recs), ids, len(new), sha))
        self.held |= set(ids)
        self.counts["records"] += len(recs)
        self.counts["new notices"] += len(new)
        return count, ids, len(new)

    def forward(self, year: int) -> None:
        """The year's pages newest first until one carries nothing not held, or the year ends."""
        page = 1
        while not self.spent():
            got = self.ask("forward", year, page)
            if got is None:
                return
            count, ids, new = got
            if not ids or not new or page * PER_PAGE >= count:
                return
            page += 1

    def have(self, year: int) -> int:
        return sum(1 for n in self.held if n.startswith(f"{year}-"))

    def settle(self, year: int, count: int) -> None:
        self.conn.execute(f"INSERT INTO {self.T('capture_years')} (year, dnz_count, held) VALUES (%s, %s, %s) "
                          "ON CONFLICT (year) DO UPDATE SET dnz_count = excluded.dnz_count, held = excluded.held, "
                          "walked_at = now()", (year, count, self.have(year)))

    def backwalk(self, years) -> None:
        """Each year short of DigitalNZ's count paged newest first until its gap closes. A year counted and found whole,
        or paged to its end without anything new, is recorded and not asked again for RECHECK_DAYS (a year DigitalNZ
        digitises more of is met at the next count)."""
        recent = {y for (y,) in self.conn.execute(
            f"SELECT year FROM {self.T('capture_years')} WHERE walked_at > now() - make_interval(days => %s)", (RECHECK_DAYS,))}
        for year in years:
            if self.spent():
                return
            if year in recent:
                continue
            got = self.ask("count", year, 1, per_page=0)
            if got is None:
                return
            count = got[0]
            if self.have(year) >= count:
                self.settle(year, count)
                continue
            page, gave = 1, 0
            while not self.spent() and self.have(year) < count:
                got = self.ask("backwalk", year, page)
                if got is None:
                    return
                _, ids, new = got
                gave += new
                if not ids or page * PER_PAGE >= count:
                    if not gave:
                        self.settle(year, count)
                    break
                page += 1
            if self.have(year) >= count:
                self.settle(year, count)


def capture(conn, schema: str = SOURCE, shared: bool = False, *, requests: int = 400, budget_s: float = 3000.0,
            backwalk: bool = True, today: dt.date = None, open_url=None, sleep=time.sleep, clock=time.monotonic,
            held: set = None, positions_dir=None, root=None, log=print) -> dict:
    """One night: the robots file's suppressions, then forward, then the backwalk. `held` is the notices already
    held (default: the export's and every landed page's). Returns the counts, with `stopped` and `ok`."""
    capture_tables(conn, schema, shared)
    today = today or dt.date.today()
    n = Night(conn, schema, shared, requests=requests, budget_s=budget_s, open_url=open_url, sleep=sleep, clock=clock,
              positions_dir=positions_dir, root=root, log=log)
    if held is None:
        held = export_notice_ids()
        for ids, in conn.execute(f"SELECT notices FROM {n.T('capture_pages')} WHERE sha256 IS NOT NULL"):
            held |= set(ids)
    n.held = set(held)
    if n.robots():
        for y in ([today.year - 1] if today.month == 1 else []) + [today.year]:
            if not n.spent():
                n.forward(y)
        if backwalk and not n.spent():
            n.backwalk(range(today.year, FLOOR_YEAR - 1, -1))
    stopped = n.spent() or "done"
    ok = not stopped.startswith(("a failed read", "the Gazette's robots"))
    return {**n.counts, "stopped": stopped, "ok": ok}


def night(argv) -> int:
    """The job: off-peak only (unless --anytime), under the owner login."""
    from support import db, jobrun
    started = jobrun.now()
    if "--anytime" not in argv and not off_peak(started):
        print(f"{JOB}: not off-peak ({started:%H:%M}); nothing asked")
        jobrun.record(JOB, True, "not off-peak; nothing asked", started, {})
        return 0
    req = int(argv[argv.index("--requests") + 1]) if "--requests" in argv else 400
    budget = float(argv[argv.index("--budget-s") + 1]) if "--budget-s" in argv else 3000.0
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.autocommit = True
        conn.execute("SET statement_timeout = '60s'")
        got = capture(conn, requests=req, budget_s=budget, backwalk="--no-backwalk" not in argv)
    detail = ", ".join(f"{k} {v}" for k, v in got.items() if k not in ("ok", "stopped")) + f"; {got['stopped']}"
    print(f"{JOB}: {detail}")
    jobrun.record(JOB, got["ok"], detail, started, {k: v for k, v in got.items() if k not in ("ok", "stopped")})
    return 0 if got["ok"] else 1


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--night" in argv:
        return night(argv)
    if "--export" not in argv:
        print("usage: python -m registers.gazette.capture --export PATH | --night [--anytime] [--requests N] "
              "[--budget-s N] [--no-backwalk]")
        return 2
    path = argv[argv.index("--export") + 1]
    if os.path.exists(path):
        print(f"{path} exists: the export is run once")
        return 1
    data = export_notices()
    with open(path, "wb") as f:
        f.write(data)
    from support.docstore import sha256_file
    print(f"{path}: {data.count(b'\n')} lines, sha256 {sha256_file(path)}, {dt.datetime.now().astimezone().isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
