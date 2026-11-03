"""The estate's own capture of the court decisions the MCP lacks (ruling 140, 3 November 2026; the survey
docs/research/courts-sources-2026-11-03.md). Tranche 1: Judicial Decisions Online (JDO), the Ministry of Justice's own
publication of ten courts' decisions at www.justice.govt.nz (position docs/legal/positions/court-judgments.md).

JDO's search answers JSON (`/jdo-search-api`): for one court and a judgment-date range, a `count` and 50 `results` a
page, each a case name and a PDF address under `/jdo_documents/`. A query answers at most 10,000 results, so the walk
asks one court and one year at a time (a year at the cap is asked a month at a time). The courts are the taxonomy's
own (`/jdo-taxonomy-api/courts`), named as it names them. The walk:

  - every listing page and every PDF goes through the fetch gate (support/fetchgate), one request at a time, at
    least FLOOR_S apart; each is landed by hash, source `courts-jdo`, under its address;
  - a PDF whose address the MCP has already landed (`mcpsource.files.url`) or the ledger holds is not fetched: the
    MCP stays first; a file the MCP later captures too is read once, by hash, as the MCP's (capture.for_load);
  - a failed read stops the run (hard limits 6 and 7): a 403, 429 or 5xx, a challenge page, a reset connection, a
    timeout, a listing that is not JSON, a "PDF" that is not one. A 404 is the host answering: the address is
    recorded `absent` and the walk goes on. Nothing is retried in the run, solved or got around;
  - 22:00 to 06:00 New Zealand time only (`--anytime` for a supervised trial), inside a budget of seconds and of
    requests; resumable: the cursor (`courts.own_cursor`) keeps each court-year's pages walked, and a past year
    walked to its end is not asked again. The current year and the one before are walked again each night from
    page one, newest first, until a page holds nothing new.

No case name is written anywhere by this module: the listing's names stay in the landed listing page, and the
document's own caption is read by the load like any other file.

    python -m registers.courts.own --jdo [--budget-s N] [--max-requests N] [--anytime] [--court NAME] [--year Y]
"""
import argparse
import datetime as dt
import json
import sys
import time
import urllib.parse
from zoneinfo import ZoneInfo

NZ = ZoneInfo("Pacific/Auckland")
SOURCE = "courts-jdo"
SCHEMA = "courts"
BASE = "https://www.justice.govt.nz"
TAXONOMY = BASE + "/jdo-taxonomy-api/courts"
SEARCH = BASE + "/jdo-search-api"
PAGE_SIZE = 50
CAP = 10_000
FLOOR_S = 5.0
EARLIEST_YEAR = 1990
#: the walk's order: the courts the MCP lacks most first (the survey's counts); the Supreme Court last (the MCP holds more)
ORDER = ("HIGH COURT", "COURT OF APPEAL", "DISTRICT COURT", "FAMILY COURT", "YOUTH COURT", "EMPLOYMENT COURT",
         "ENVIRONMENT COURT", "MAORI LAND COURT", "MĀORI LAND COURT", "MAORI APPELLATE COURT", "MĀORI APPELLATE COURT",
         "SUPREME COURT")


class Stop(Exception):
    """A failed read: the run stops here (hard limits 6 and 7)."""


def now_nz() -> dt.datetime:
    return dt.datetime.now(NZ)


def off_peak(t: dt.datetime) -> bool:
    """22:00 to 06:00 New Zealand time."""
    h = t.astimezone(NZ).hour
    return h >= 22 or h < 6


def search_url(court: str, start: dt.date, end: dt.date, page: int) -> str:
    """The address JDO's own form asks (its bundle, landed by the survey): every field present, empty where unused."""
    span = f"['{start.year}-{start.month}-{start.day}T00:00:00Z','{end.year}-{end.month}-{end.day}T23:59:59Z']"
    q = [("court", court), ("location", ""), ("judge", ""), ("counsel", ""), ("caseName", ""), ("fileNumber", ""),
         ("citation", ""), ("judgmentDate", span), ("minuteReference", ""), ("searchTerms", ""), ("page", str(page)),
         ("sort", "judgmentdate desc")]
    return SEARCH + "?" + urllib.parse.urlencode(q, safe=":,", quote_via=urllib.parse.quote)


def spans(year: int, count: int) -> list:
    """The date ranges a year is asked in: the whole year, or its months when the year reaches the cap."""
    if count < CAP:
        return [(dt.date(year, 1, 1), dt.date(year, 12, 31))]
    out = []
    for m in range(1, 13):
        last = (dt.date(year + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1))
        out.append((dt.date(year, m, 1), last))
    return out


def courts_in_order(names: list) -> list:
    rank = {c: i for i, c in enumerate(ORDER)}
    return sorted(names, key=lambda n: (rank.get(n.strip().upper(), len(ORDER) - 1), n))


class Walk:
    """One run's state: the connection, the gate's injectables, the budget and the counts."""

    def __init__(self, conn, *, schema: str = SCHEMA, mcp_schema: str = "mcpsource", budget_s: float = 7 * 3600,
                 max_requests: int = None, anytime: bool = False, fetch=None, pacer=None, positions_dir: str = None,
                 ledger_dir: str = None, clock=time.monotonic, sleep=time.sleep, now=now_nz, log=print, land=None,
                 courts: list = None, years: list = None):
        self.conn, self.schema, self.mcp_schema = conn, schema, mcp_schema
        self.deadline = clock() + budget_s
        self.max_requests, self.anytime = max_requests, anytime
        self.fetch, self.pacer, self.positions_dir, self.ledger_dir = fetch, pacer, positions_dir, ledger_dir
        self.clock, self.sleep, self.now, self.log = clock, sleep, now, log
        self._last = float("-inf")
        self.only_courts, self.only_years = courts, years
        self._land = land
        self.counts = {"requests": 0, "listing_pages": 0, "listed": 0, "landed": 0, "skipped_mcp": 0,
                       "skipped_held": 0, "absent": 0, "new_files": 0}
        self.mcp_urls = self._mcp_urls()
        self.held = {r[0] for r in conn.execute(f"SELECT url FROM {schema}.own_files").fetchall()}

    def _mcp_urls(self) -> set:
        if not self.conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = 'files'",
                                 (self.mcp_schema,)).fetchone():
            return set()
        return {r[0] for r in self.conn.execute(f"SELECT DISTINCT url FROM {self.mcp_schema}.files WHERE corpus = 'courts'")}

    # ── the budget ──────────────────────────────────────────────────────────────────────────────────────────────
    def spent(self) -> str:
        if self.max_requests is not None and self.counts["requests"] >= self.max_requests:
            return "the run's request budget spent"
        if self.clock() >= self.deadline:
            return "the run's time budget spent"
        if not self.anytime and not off_peak(self.now()):
            return "outside 22:00 to 06:00 New Zealand time"
        return ""

    # ── one gated request ───────────────────────────────────────────────────────────────────────────────────────
    def get(self, url: str, accept: str):
        from support import fetchgate
        self.counts["requests"] += 1
        gap = self._last + FLOOR_S - self.clock()
        if gap > 0 and self.fetch is None:
            self.sleep(gap)                    # the lane's own floor, slower than the gate's default (the position)
        try:
            got = fetchgate.open_url(url, timeout=60, headers={"Accept": accept}, pacer=self.pacer, fetch=self.fetch,
                                     positions_dir=self.positions_dir, ledger_dir=self.ledger_dir)
        except fetchgate.Refused as exc:
            raise Stop(f"the gate refused it: {exc}") from None
        except OSError as exc:
            raise Stop(f"no answer ({type(exc).__name__}): a failed read") from None
        finally:
            self._last = self.clock()
        if got.blocked:
            raise Stop(got.blocked)
        if got.status == 404:
            return None
        if got.status != 200:
            raise Stop(f"HTTP {got.status}: a failed read")
        return got.body

    def land(self, data: bytes, url: str, content_type: str) -> str:
        if self._land is not None:
            return self._land(data, url, content_type)
        from support.docstore.landing import land
        ref, _ = land(data, name=url, source=SOURCE, conn=self.conn, name_kind="url", content_type=content_type,
                      fetched_at=self.now().isoformat(timespec="seconds"))
        return ref.sha256

    # ── the walk ────────────────────────────────────────────────────────────────────────────────────────────────
    def courts(self) -> list:
        body = self.get(TAXONOMY, "application/json")
        if body is None:
            raise Stop("the court taxonomy answered 404")
        try:
            names = [c["Name"] for c in json.loads(body) if c.get("Name")]
        except (ValueError, TypeError, KeyError):
            raise Stop("the court taxonomy is not the JSON list it was") from None
        self.land(body, TAXONOMY, "application/json")
        return courts_in_order(names)

    def listing(self, court: str, start: dt.date, end: dt.date, page: int):
        url = search_url(court, start, end, page)
        body = self.get(url, "application/json")
        if body is None:
            raise Stop("a listing page answered 404")
        try:
            data = json.loads(body)
            count, results = int(data["count"]), list(data["results"])
        except (ValueError, TypeError, KeyError):
            raise Stop("a listing page that is not JDO's JSON: a failed read") from None
        sha = self.land(body, url, "application/json")
        self.counts["listing_pages"] += 1
        return count, results, sha

    def file(self, court: str, year: int, listing_sha: str, href: str) -> bool:
        """One listed decision: skipped when held, else fetched and recorded. True when the file is new to us."""
        url = urllib.parse.urljoin(BASE, href)
        self.counts["listed"] += 1
        if url in self.mcp_urls:
            self.counts["skipped_mcp"] += 1
            return False
        if url in self.held:
            self.counts["skipped_held"] += 1
            return False
        if self.spent():
            raise Budget(self.spent())
        body = self.get(url, "application/pdf")
        if body is None:
            self.conn.execute(f"INSERT INTO {self.schema}.own_files (url, source, court, year, listing, status) "
                              f"VALUES (%s, %s, %s, %s, %s, 'absent') ON CONFLICT (url) DO NOTHING",
                              (url, SOURCE, court, year, listing_sha))
            self.counts["absent"] += 1
        else:
            if not body.startswith(b"%PDF"):
                raise Stop("a decision's address answered something that is not a PDF: a failed read")
            sha = self.land(body, url, "application/pdf")
            self.conn.execute(f"INSERT INTO {self.schema}.own_files (url, source, court, year, listing, sha256, bytes, "
                              f"status) VALUES (%s, %s, %s, %s, %s, %s, %s, 'landed') ON CONFLICT (url) DO NOTHING",
                              (url, SOURCE, court, year, listing_sha, sha, len(body)))
            self.counts["landed"] += 1
        self.held.add(url)
        self.conn.commit()
        self.counts["new_files"] += 1
        return True

    def cursor(self, court: str, year: int):
        r = self.conn.execute(f"SELECT total, pages_done, done FROM {self.schema}.own_cursor WHERE source = %s AND "
                              f"court = %s AND year = %s", (SOURCE, court, year)).fetchone()
        return (r[0], r[1], r[2]) if r else (None, 0, False)

    def advance(self, court: str, year: int, total: int, pages_done: int, done: bool) -> None:
        self.conn.execute(f"INSERT INTO {self.schema}.own_cursor (source, court, year, total, pages_done, done, at) "
                          f"VALUES (%s, %s, %s, %s, %s, %s, now()) ON CONFLICT (source, court, year) DO UPDATE SET "
                          f"total = EXCLUDED.total, pages_done = EXCLUDED.pages_done, done = EXCLUDED.done, at = now()",
                          (SOURCE, court, year, total, pages_done, done))
        self.conn.commit()

    def year(self, court: str, year: int, recent: bool) -> None:
        """One court-year. A past year resumes at the page after the last one walked and is done at its last page; a
        recent one (this year and last) starts at page one each night and stops at its first page that holds
        nothing new, as the listing is sorted newest first."""
        total, pages_done, done = self.cursor(court, year)
        if done and not recent:
            return
        page = 1 if recent else pages_done + 1
        while True:
            if self.spent():
                raise Budget(self.spent())
            count, results, sha = self.listing(court, dt.date(year, 1, 1), dt.date(year, 12, 31), page)
            if count >= CAP:
                for start, end in spans(year, count):      # at the cap: a month at a time (no court is near it today)
                    self._span(court, year, start, end)
                self.advance(court, year, count, 0, not recent)
                return
            pages = max(1, -(-count // PAGE_SIZE))
            new = sum(self.file(court, year, sha, r["url"]) for r in results if r.get("url"))
            last = page >= pages
            self.advance(court, year, count, max(pages_done, page) if recent else page, last and not recent)
            if last or (recent and new == 0):
                return
            page += 1

    def _span(self, court: str, year: int, start: dt.date, end: dt.date) -> None:
        page = 1
        while True:
            if self.spent():
                raise Budget(self.spent())
            count, results, sha = self.listing(court, start, end, page)
            for r in results:
                if r.get("url"):
                    self.file(court, year, sha, r["url"])
            if page * PAGE_SIZE >= count:
                return
            page += 1

    def run(self, courts: list = None, years: list = None) -> dict:
        """The walk to its end, the budget, the hours or a failed read. Returns the counts, `ok` and why it stopped."""
        stopped = "end"
        ok = True
        try:
            if self.spent():
                raise Budget(self.spent())
            names = courts or self.only_courts or self.courts()
            this = self.now().year
            for court in names:
                for y in (years or self.only_years or range(this, EARLIEST_YEAR - 1, -1)):
                    self.year(court, y, recent=y >= this - 1)
        except Budget as b:
            stopped = str(b)
        except Stop as s:
            stopped, ok = f"a failed read: {s}", False
            self.conn.rollback()
        out = {**self.counts, "ok": ok, "stopped": stopped}
        self.log("courts own capture (JDO): " + ", ".join(f"{k} {v}" for k, v in out.items()))
        return out


class Budget(Exception):
    """The run's budget or hours are spent: not a failure."""


def job(argv=None, log=print) -> int:
    from support import db, jobrun
    ap = argparse.ArgumentParser(prog="python -m registers.courts.own")
    ap.add_argument("--jdo", action="store_true", required=True)
    ap.add_argument("--budget-s", type=float, default=7.5 * 3600)
    ap.add_argument("--max-requests", type=int)
    ap.add_argument("--anytime", action="store_true", help="a supervised trial outside 22:00 to 06:00")
    ap.add_argument("--court", action="append", help="the court as the taxonomy names it; repeatable")
    ap.add_argument("--year", type=int, action="append")
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    from registers.courts import load as L
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute(L.capture_tables_sql(SCHEMA))
        conn.commit()
        out = Walk(conn, budget_s=a.budget_s, max_requests=a.max_requests, anytime=a.anytime, log=log).run(
            courts=a.court, years=a.year)
    detail = ", ".join(f"{k} {v}" for k, v in out.items() if k != "ok")
    jobrun.record("qv4-courts-jdo-capture", out["ok"], detail[:2000], started,
                  {k: v for k, v in out.items() if isinstance(v, int) and not isinstance(v, bool)})
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(job())
