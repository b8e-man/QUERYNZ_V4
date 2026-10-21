"""How this lane's documents arrive: case 3 of plan 1.10, captured once,
politely, through the fetch gate and the landing wrapper only.

The Health and Disability Commissioner publishes its decisions at
`www.hdc.org.nz/decisions/search-decisions/`, twelve to a page, newest first,
and filters them by year (`?filter-year=2017&page=N`), each page stating
"Page N of M". Its case studies (`/decisions/case-studies-nga-matai-take/`)
are one page. A decision's page carries the whole decision (the PDF linked
from it is the same decision and is not fetched). Ruling 71: the window
opens in 2017, so the lane walks one listing per year from 2017 and the
case studies dated from 2017; nothing older is asked for.

HELD. The site's copyright terms (`/copyright/`, 3.1 and 3.2) let material
be reproduced "for personal, educational or research purposes without formal
permission"; any other purpose needs the Commissioner's prior written
permission. The estate's purpose includes a product that may be sold, so a
run into the real database lands nothing until the position on file carries
a line

    authorised: <date>, <how the Commissioner (or Arthur's ruling) said so, and where it is held>

and refuses otherwise, before anything is asked for. A proof into the sample
database (a research copy, at most `PROOF_ITEMS` pages) is allowed: it is
how this lane was built and tested.

A run, in order:

  1. the documents about the source (copyright, terms, privacy statement, the
     naming policy page and its PDF), at most every 30 days;
  2. a pass over each listing, at most weekly, resuming from its next page:
     every listing page landed by hash, every entry listed with its
     fingerprint (the tile's date and a hash of its heading);
  3. the entries listed and not held under that fingerprint, in listing
     order: an entry is fetched once, and again only when its tile changes.

Politeness (hard limit 7): one request at a time, at least `FLOOR_S` apart
(the site has no robots file; the gate's own floor binds too), off-peak
(22:00 to 06:00 NZ time) unless `--anytime`, a budget per run. A 403, 429,
any 5xx or a challenge page STOPS the run (hard limit 6; the brief). A
transport failure (a timeout, a reset) is a failed read set aside; three in
a row stop the run. A redirect to another host stops it. A gate refusal is
never caught. A run that stops early after landing something exits green
with a "stopped early" line; red only when nothing landed.

    python -m registers.hdc_decisions.capture [--anytime] [--max-items N] [--max-pages N] [--budget-s N]
"""
import argparse
import datetime as dt
import os
import re
import sys
import time
from zoneinfo import ZoneInfo

import support.fetchgate as fg
from registers.hdc_decisions import read

SOURCE = SCHEMA = "hdc_decisions"
JOB = "qv4-hdc-decisions-capture"
HOST = "www.hdc.org.nz"
BASE = f"https://{HOST}"
FLOOR_S = 5.0
OFF_PEAK = (22, 6)
FULL_EVERY_DAYS = 7
DOCS_EVERY_DAYS = 30
DEFAULT_BUDGET_S = 4 * 3600
STOP_AFTER_FAILURES = 3
PROOF_ITEMS = 40
FIRST_YEAR = read.SINCE.year
NZ = ZoneInfo("Pacific/Auckland")
HERE = os.path.dirname(os.path.abspath(__file__))
#: where the position is read from. Until the integrator moves `position/hdc-decisions.md` to docs/legal/positions/,
#: a session runs with QV4_POSITIONS pointing at this lane's position folder.
POSITIONS = os.environ.get("QV4_POSITIONS") or None
READING = "-- ── the reading"


class List:
    """One listing the lane walks: its pages, its reader, its entries' kind."""

    def __init__(self, name, page_url, per_page, kind):
        self.name, self.page_url, self.per_page, self.kind = name, page_url, per_page, kind


def year_list(year: int) -> List:
    return List(f"decisions-{year}",
                lambda n, y=year: f"{BASE}/decisions/search-decisions/?filter-year={y}" + (f"&page={int(n)}" if n > 1 else ""),
                read.PER_PAGE, "decision")


def all_lists(today: dt.date = None) -> tuple:
    today = today or dt.datetime.now(NZ).date()
    return tuple(year_list(y) for y in range(today.year, FIRST_YEAR - 1, -1)) + (
        List("case-studies", lambda n: f"{BASE}{read.CASE_STUDIES_PATH}", 1000, "case study"),)


DOCS = {
    "copyright": f"{BASE}/copyright/",
    "terms": f"{BASE}/terms-conditions/",
    "privacy": f"{BASE}/privacy-statement/",
    "naming-policy": f"{BASE}/decisions/naming-policy/",
    "naming-policy-pdf": f"{BASE}/media/0a1ki1sr/policy-for-naming-providers-in-public-hdc-reports-2023-06-19.pdf",
}


class Held(RuntimeError):
    """The Commissioner's terms: no copy for this purpose without written permission on file."""


def authorisation(positions_dir: str = None):
    """The `authorised:` line of the position covering the host, or None."""
    folder = positions_dir or POSITIONS or fg.POSITIONS_DIR
    cls = fg.position_for(HOST, folder)
    if not cls:
        return None
    try:
        with open(os.path.join(folder, cls + ".md"), encoding="utf-8") as f:
            m = re.search(r"^authorised:\s*(\S.*)$", f.read(), re.M)
    except OSError:
        return None
    return m.group(1).strip() if m else None


# ── pure pieces ───────────────────────────────────────────────────────────────

def off_peak(t: dt.datetime) -> bool:
    h = t.astimezone(NZ).hour
    return h >= OFF_PEAK[0] or h < OFF_PEAK[1]


def stops(status: int, body: bytes) -> str:
    """'' when the answer may be read; else why the run stops (a block, a challenge, the server's own error)."""
    if status in (403, 429) or 500 <= status <= 599:
        return f"HTTP {status}: the run stops (a block, a limit or the server's own error)"
    return fg.looks_challenged(200, body)


def table(schema: str, t: str) -> str:
    """The lane's own schema holds its tables by their names; any other (a session's scratch schema, a staging
    schema) carries the lane's prefix."""
    return f"{schema}.{t}" if schema == SCHEMA else f"{schema}.{SCHEMA}_{t}"


_NAMES = re.compile(rf"(?<![A-Za-z0-9_]){SCHEMA}(_private)?\.")


def capture_sql(schema: str = SCHEMA) -> str:
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        text = f.read().split(READING)[0]
    pre = "" if schema == SCHEMA else f"{SCHEMA}_"
    return _NAMES.sub(lambda m: f"{schema}{'_private' if m.group(1) and schema == SCHEMA else ''}.{pre}", text)


# ── the lane's capture tables ─────────────────────────────────────────────────

class Tables:
    """The capture's record over a psycopg connection in autocommit mode."""

    def __init__(self, conn, schema: str = SCHEMA):
        self.conn, self.s = conn, schema
        self.T = lambda t: table(schema, t)

    def create(self):
        self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.s}")
        self.conn.execute(capture_sql(self.s))

    def try_lock(self) -> bool:
        return bool(self.conn.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (JOB,)).fetchone()[0])

    def _pass(self, row):
        if row is None:
            return None
        return dict(zip(("pass_id", "list", "stated", "next_page", "pages", "items"), row))

    def open_pass(self, name):
        return self._pass(self.conn.execute(
            f"SELECT pass_id, list, stated, next_page, pages, items FROM {self.T('capture_passes')} "
            "WHERE list = %s AND finished_at IS NULL ORDER BY pass_id DESC LIMIT 1", (name,)).fetchone())

    def last_finished(self, name):
        return self.conn.execute(f"SELECT max(finished_at) FROM {self.T('capture_passes')} WHERE list = %s",
                                 (name,)).fetchone()[0]

    def begin(self, name):
        return self._pass(self.conn.execute(
            f"INSERT INTO {self.T('capture_passes')} (list) VALUES (%s) "
            "RETURNING pass_id, list, stated, next_page, pages, items", (name,)).fetchone())

    def add_page(self, p, page_no, url, sha, items, stated):
        self.conn.execute(f"INSERT INTO {self.T('capture_pages')} (pass_id, page_no, url, sha256, items) "
                          "VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", (p["pass_id"], page_no, url, sha, len(items)))
        for i, it in enumerate(items):
            self.conn.execute(f"INSERT INTO {self.T('capture_listed')} (pass_id, list, slug, url, card, listed_on, ordinal) "
                              "VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                              (p["pass_id"], p["list"], it["slug"], it["url"], it["card"], it["listed_on"],
                               (page_no - 1) * 1000 + i))
        n = self.conn.execute(f"SELECT count(*) FROM {self.T('capture_listed')} WHERE pass_id = %s",
                              (p["pass_id"],)).fetchone()[0]
        p.update(next_page=page_no + 1, pages=p["pages"] + 1, items=n, stated=p["stated"] if p["stated"] else stated)
        self.conn.execute(f"UPDATE {self.T('capture_passes')} SET next_page = %s, pages = %s, items = %s, stated = %s "
                          "WHERE pass_id = %s", (p["next_page"], p["pages"], p["items"], p["stated"], p["pass_id"]))

    def finish(self, p):
        self.conn.execute(f"UPDATE {self.T('capture_passes')} SET finished_at = now() WHERE pass_id = %s", (p["pass_id"],))

    def pending(self, name, limit):
        """Listed in the newest pass that listed anything, and not held under the card listed."""
        return [tuple(r) for r in self.conn.execute(
            f"SELECT l.slug, l.url, l.card FROM {self.T('capture_listed')} l "
            f"WHERE l.pass_id = (SELECT max(pass_id) FROM {self.T('capture_listed')} WHERE list = %s) "
            "AND (l.listed_on IS NULL OR l.listed_on >= %s) "
            f"AND NOT EXISTS (SELECT 1 FROM {self.T('capture_items')} i WHERE i.list = l.list AND i.slug = l.slug "
            "AND i.card = l.card) ORDER BY l.ordinal LIMIT %s", (name, read.SINCE, limit))]

    def add_item(self, name, slug, url, card, sha):
        self.conn.execute(f"INSERT INTO {self.T('capture_items')} (list, slug, url, card, sha256) VALUES "
                          "(%s, %s, %s, %s, %s) ON CONFLICT (list, slug, sha256) DO UPDATE SET card = EXCLUDED.card, "
                          "at = now()", (name, slug, url, card, sha))

    def docs_due(self, days) -> bool:
        last = self.conn.execute(f"SELECT max(at) FROM {self.T('capture_docs')}").fetchone()[0]
        return last is None or (dt.datetime.now(dt.timezone.utc) - last).days >= days

    def add_doc(self, name, url, sha, new):
        self.conn.execute(f"INSERT INTO {self.T('capture_docs')} (name, url, sha256, new) VALUES (%s, %s, %s, %s)",
                          (name, url, sha, new))

    def set_aside(self, pass_id, item, stage, reason):
        self.conn.execute(f"INSERT INTO {self.T('capture_set_aside')} (pass_id, item, stage, reason) "
                          "VALUES (%s, %s, %s, %s)", (pass_id, str(item), stage, reason[:500]))


# ── a run ─────────────────────────────────────────────────────────────────────

class Stop(RuntimeError):
    """The run stops here: a block, a challenge, the server's error, the host not answering, or a page not to be trusted."""


class Run:
    def __init__(self, tables, *, land_fn, opener=None, clock=None, sleep=None, now=None,
                 budget_s: float = DEFAULT_BUDGET_S, max_items: int = 100000, max_pages: int = 1000,
                 anytime: bool = False, lists=None, docs=DOCS, log=print):
        self.t, self.land_fn, self.log = tables, land_fn, log
        self.opener = opener or (lambda url, timeout: fg.open_url(url, timeout=timeout, positions_dir=POSITIONS))
        self.clock = clock or time.monotonic
        self.pacer = fg.Pacer(now=self.clock, sleep=sleep or time.sleep)
        self.now = now or (lambda: dt.datetime.now(NZ))
        self.budget_s, self.max_items, self.max_pages, self.anytime = budget_s, max_items, max_pages, anytime
        self.lists = lists if lists is not None else all_lists()
        self.docs = docs
        self.started = self.clock()
        self.failures = 0
        self.tried = set()
        self.counts = {"requests": 0, "pages": 0, "listed": 0, "passes_finished": 0, "items": 0, "landed": 0,
                       "already_held": 0, "docs": 0, "set_aside": 0}
        self.stopped = ""

    def time_left(self) -> bool:
        if self.clock() - self.started >= self.budget_s:
            self.stopped = self.stopped or "budget spent"
            return False
        if not self.anytime and not off_peak(self.now()):
            self.stopped = self.stopped or "off-peak is over"
            return False
        return True

    def aside(self, pass_id, item, stage, reason):
        self.t.set_aside(pass_id, item, stage, reason)
        self.counts["set_aside"] += 1

    def get(self, url: str, pass_id=None):
        """One gated, paced request: the answer, or None after a transport failure (set aside). Raises Stop on a
        403, 429, 5xx, a challenge, another host, or three failed reads in a row."""
        self.pacer.wait(HOST, FLOOR_S)
        self.counts["requests"] += 1
        try:
            f = self.opener(url, 60)
        except fg.Refused:
            raise
        except Exception as exc:  # noqa: BLE001 — a transport failure is a failed read, never the end of the night
            self.failures += 1
            self.aside(pass_id, url, "fetch", f"transport: {type(exc).__name__}: {str(exc)[:200]}")
            if self.failures >= STOP_AFTER_FAILURES:
                raise Stop(f"{self.failures} failed reads in a row; the host may be in trouble")
            return None
        self.failures = 0
        why = stops(f.status, f.body) or (f.blocked if f.status != 404 else "")
        if why:
            self.aside(pass_id, url, "fetch", why)
            raise Stop(why)
        if fg.host_of(f.final_url or url) != HOST:
            why = f"redirected to {fg.host_of(f.final_url)}: not landed, and the run stops"
            self.aside(pass_id, url, "fetch", why)
            raise Stop(why)
        return f

    def land(self, f, content_type="text/html"):
        return self.land_fn(f.body, name=f.url, source=SOURCE, name_kind="url", content_type=content_type)

    def land_docs(self):
        if not self.t.docs_due(DOCS_EVERY_DAYS):
            return
        for name, url in self.docs.items():
            if not self.time_left():
                return
            f = self.get(url)
            if f is None or f.status != 200:
                if f is not None:
                    self.aside(None, url, "doc", f"HTTP {f.status}")
                continue
            ref, new = self.land(f, "application/pdf" if url.endswith(".pdf") else "text/html")
            self.t.add_doc(name, url, ref.sha256, new)
            self.counts["docs"] += 1

    def walk(self, lst):
        """A pass over one listing, resumed from its next page; a new pass at most every FULL_EVERY_DAYS."""
        p = self.t.open_pass(lst.name)
        if p is None:
            last = self.t.last_finished(lst.name)
            if last is not None and (dt.datetime.now(dt.timezone.utc) - last).days < FULL_EVERY_DAYS:
                return
            p = self.t.begin(lst.name)
        walked = 0
        while self.time_left() and walked < self.max_pages:
            n = p["next_page"]
            url = lst.page_url(n)
            f = self.get(url, p["pass_id"])
            if f is None:
                return
            if f.status != 200:
                self.aside(p["pass_id"], url, "listing", f"HTTP {f.status}")
                return
            try:
                out = read.read_listing(f.body)
            except ValueError as exc:
                self.aside(p["pass_id"], url, "listing", f"not the listing's shape: {exc}")
                raise Stop(f"a listing page of {lst.name} is not its shape")
            if out["page"] != n:
                self.aside(p["pass_id"], url, "listing", f"asked for page {n}, the page says {out['page']}")
                raise Stop(f"{lst.name}: the listing did not give the page asked for")
            ref, _ = self.land(f)
            self.t.add_page(p, n, url, ref.sha256, out["items"], out["stated"])
            self.counts["pages"] += 1
            walked += 1
            self.counts["listed"] += len(out["items"])
            if n >= (p["stated"] or 1) or not out["items"]:
                self.t.finish(p)
                self.counts["passes_finished"] += 1
                self.log(f"{SOURCE}: {lst.name}: pass {p['pass_id']} finished, {p['items']} listed on "
                         f"{p['pages']} pages of {p['stated']}")
                return

    def fetch(self, lst):
        while self.counts["items"] < self.max_items and self.time_left():
            batch = [r for r in self.t.pending(lst.name, 100 + len(self.tried)) if (lst.name, r[0]) not in self.tried]
            if not batch:
                return
            for slug, url, card in batch:
                if self.counts["items"] >= self.max_items or not self.time_left():
                    return
                self.tried.add((lst.name, slug))
                self.counts["items"] += 1
                f = self.get(url)
                if f is None:
                    continue
                if f.status != 200:
                    self.aside(None, url, "item", f"HTTP {f.status}")
                    continue
                why = read.recognise_page(f.body)
                if why:
                    self.aside(None, url, "item", f"not a decision's shape: {why}; not landed")
                    continue
                ref, new = self.land(f)
                self.t.add_item(lst.name, slug, url, card, ref.sha256)
                self.counts["landed" if new else "already_held"] += 1

    def run(self) -> dict:
        try:
            self.land_docs()
            for lst in self.lists:
                self.walk(lst)
            for lst in self.lists:
                self.fetch(lst)
        except Stop as exc:
            self.stopped = f"stopped: {exc}"
        return {**self.counts, "stopped": self.stopped}


def outcome(out: dict):
    """(ok, the last words of the run's line): a polite early stop after landing something is green; red only when
    it stopped with nothing landed."""
    stopped = out["stopped"]
    if not stopped.startswith("stopped:"):
        return True, stopped or "done"
    if out["pages"] or out["landed"] or out["already_held"] or out["docs"]:
        return True, "stopped early: " + stopped[len("stopped:"):].strip()
    return False, stopped + "; nothing landed"


def held_for(database: str, max_items: int, max_pages: int, authorised=None) -> str:
    """'' when this run may go; else why it is held. Into the real database only with the authorisation on file; into
    the sample database only a proof (a research copy, copyright 3.1)."""
    if authorised is None:
        authorised = authorisation()
    if authorised:
        return ""
    if database == "querynz_v4":
        return ("held: the Commissioner's terms (copyright 3.2) want written permission for any use beyond research; "
                "no `authorised:` line on the position, nothing asked for")
    if max_items > PROOF_ITEMS or max_pages > PROOF_ITEMS:
        return f"held: a proof into the sample database is at most {PROOF_ITEMS} entries and {PROOF_ITEMS} pages per list"
    return ""


def landing(conn):
    from support.docstore.landing import land

    def land_fn(data, *, name, source, name_kind, content_type):
        return land(data, name=name, source=source, conn=conn, name_kind=name_kind, content_type=content_type)
    return land_fn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.hdc_decisions.capture")
    ap.add_argument("--anytime", action="store_true", help="outside off-peak (by hand: a proof)")
    ap.add_argument("--max-items", type=int, default=100000)
    ap.add_argument("--max-pages", type=int, default=1000, help="listing pages per list per run")
    ap.add_argument("--budget-s", type=float, default=DEFAULT_BUDGET_S)
    ap.add_argument("--list", help="walk and fetch this list only (decisions-2017 … decisions-<this year>, case-studies)")
    ap.add_argument("--no-docs", action="store_true", help="skip the documents about the source")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default=SCHEMA)
    a = ap.parse_args(argv)
    from support import db, jobrun
    started = jobrun.now()
    why = held_for(a.database, a.max_items, a.max_pages)
    if why:
        print(f"{SOURCE}: {why}")
        if a.database == "querynz_v4":
            jobrun.record(JOB, True, why, started, {})
        return 0
    chosen = [x for x in all_lists() if a.list in (None, x.name)]
    if not chosen:
        print(f"{SOURCE}: no list named {a.list}")
        return 2
    with db.connect(db.OWNER_KEY, a.database, autocommit=True) as conn:
        conn.execute("SET statement_timeout = '60s'")
        t = Tables(conn, a.schema)
        t.create()
        if not t.try_lock():
            print(f"{SOURCE}: another run holds the lane; this one asks for nothing")
            return 0
        out = Run(t, land_fn=landing(conn), anytime=a.anytime, max_items=a.max_items, max_pages=a.max_pages,
                  budget_s=a.budget_s, lists=chosen, docs={} if a.no_docs else DOCS).run()
    ok, last = outcome(out)
    detail = (f"{out['requests']} requests, {out['pages']} listing pages ({out['listed']} listed), "
              f"{out['passes_finished']} passes finished, {out['items']} entries tried, {out['landed']} landed, "
              f"{out['already_held']} already held, {out['docs']} documents about the source, "
              f"{out['set_aside']} set aside; {last}")
    print(f"{SOURCE}: {detail}")
    if a.database == "querynz_v4":
        jobrun.record(JOB, ok, detail, started, out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
