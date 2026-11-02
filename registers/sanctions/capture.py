"""How this lane's documents arrive: case 3 of plan 1.10 (one capture of its
own, politely, through the fetch gate and the landing wrapper only), or, for
the one list whose terms bar automated access, a file a person downloaded,
landed by hash.

Three lists New Zealand law applies, each as its publisher issues it:

  mfat-russia    the Ministry of Foreign Affairs and Trade's Russia Sanctions
                 Register (Russia Sanctions Act 2022): one workbook,
                 `Russia-Sanctions-Register.xlsx`, linked from the register
                 page with the day it was updated
  un-sc          the United Nations Security Council Consolidated List, as
                 the UN publishes it (XML), given effect in New Zealand under
                 the United Nations Act 1946
  nz-police-tsa  the New Zealand Police list of designated terrorist
                 entities (Terrorism Suppression Act 2002): one workbook
                 (`designated-entities-<day>.xlsx`, linked from the
                 resolutions 1267/1989/2253/1988 page, with sheets for the
                 UN-derived individuals and organisations, the Resolution
                 1373 designations, revocations and expirations) and the
                 Resolution 1373 page, which states the current count

Each list is fetched only when the position
(`docs/legal/positions/sanctions-lists.md`) carries a line
`authorised: <list> <date> <how>`. Ruling 132 (Arthur, 2 November 2026:
"copy: ... the sanctions lists") added all three, over the terms below, which
were the reason for the hold; a challenge or a bot wall is still a failed
read (hard limit 6):

  mfat-russia    MFAT's terms of use: "You must not access or attempt to
                 access our websites ... through automated tools (including
                 the use of scripts, web-crawlers, robots or screen-scrapers)".
                 The copy itself is allowed (Crown copyright, CC BY 4.0), so a
                 workbook a PERSON downloads in a browser may be landed by
                 hand: `--file PATH --version DAY`. The file also sits behind
                 a bot wall (Incapsula); it is never got around (hard limit 6)
  un-sc          the UN's terms: download and copy "for the User's personal,
                 non-commercial use, without any right to resell or
                 redistribute them or to compile or create derivative works"
  nz-police-tsa  Police's copyright statement: save "for non-commercial
                 private purposes only"; any other purpose "requires
                 permission"

Every fetch goes through the gate, one request at a time, at least `FLOOR_S`
apart (Police's and the UN site's robots files ask 10 s; the gate honours
that), off-peak unless `--anytime`; a 403, 429, 5xx or challenge page is a
failed read: it is set aside, that list stops, and the next list is asked.
The cadence is weekly, kept by the record and not the calendar: a list is
asked for only when nothing was asked of it in the last `CADENCE_DAYS`
(a landing or a failed read), unless `--due-now`. Nothing fetched twice: the
documents about a list (its terms) are fetched once; MFAT's workbook only
when the register page names a day not yet landed, Police's only when the
page links a file not yet landed; a list whose bytes are already held adds a
name, not a document. Every line printed is a count.

    python -m registers.sanctions.capture [--lists un-sc,nz-police-tsa,mfat-russia] [--anytime] [--due-now]
    python -m registers.sanctions.capture --file PATH --list mfat-russia --version 2026-09-09
"""
import argparse
import datetime as dt
import os
import re
import sys
import time
from zoneinfo import ZoneInfo

import support.fetchgate as fg

SOURCE = SCHEMA = "sanctions"
JOB = "qv4-sanctions-capture"
FLOOR_S = 10.0
OFF_PEAK = (22, 6)
STOP_AFTER_FAILURES = 3
NZ = ZoneInfo("Pacific/Auckland")
HERE = os.path.dirname(os.path.abspath(__file__))
#: the gate's own folder (docs/legal/positions/) unless QV4_POSITIONS says otherwise
POSITIONS = os.environ.get("QV4_POSITIONS") or None
#: the lists' cadence: weekly (the job runs nightly; a list asked within this many days is not asked again)
CADENCE_DAYS = 6.5
LISTS = ("mfat-russia", "un-sc", "nz-police-tsa")
#: the lists a person may land by hand while the automated fetch is held: the copy is allowed, the robot is not
BY_HAND = ("mfat-russia",)
MFAT_PAGE = ("https://www.mfat.govt.nz/en/countries-and-regions/europe/ukraine/russian-invasion-of-ukraine/"
             "sanctions/russia-sanctions-register")
MFAT_FILE = "https://www.mfat.govt.nz/assets/Countries-and-Regions/Europe/Ukraine/Russia-Sanctions-Register.xlsx"
UN_XML = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
POLICE_UN_PAGE = ("https://www.police.govt.nz/advice/personal-community/counterterrorism/designated-entities/"
                  "lists-associated-with-resolutions-1267-1989-2253-1988")
POLICE_1373_PAGE = ("https://www.police.govt.nz/advice/personal-community/counterterrorism/designated-entities/"
                    "lists-associated-with-resolution-1373")
#: the documents about each list, landed with its first authorised run (never parsed here)
DOCS = {
    "mfat-russia": {"terms-of-use": "https://www.mfat.govt.nz/en/terms-of-use", "copyright": "https://www.mfat.govt.nz/en/copyright"},
    "un-sc": {"terms-of-use": "https://www.un.org/en/about-us/terms-of-use"},
    "nz-police-tsa": {"copyright": "https://www.police.govt.nz/about-site-and-nz-police-app/copyright"},
}
_POLICE_XLSX = re.compile(r'href="(/sites/default/files/publications/designated-entities-[^"]+\.xlsx)"')
_POLICE_DAY = re.compile(r"designated-entities-(\d{1,2})-([a-z]+)-(\d{4})\.xlsx")
_MFAT_DAY = re.compile(r"(?:updated|current as at)\D{0,40}?(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", re.I)
_MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
           "november", "december")


class Held(RuntimeError):
    """The list is held: the position records no authorisation for it."""


class Stop(RuntimeError):
    """The run stops here: a block, a challenge, or the host not answering."""


# ── pure pieces ───────────────────────────────────────────────────────────────

def authorisation(list_id: str, positions_dir: str = None):
    """The position's `authorised: <list> …` line, or None."""
    folder = positions_dir or POSITIONS or fg.POSITIONS_DIR
    cls = fg.position_for("www.mfat.govt.nz", folder) or fg.position_for("scsanctions.un.org", folder)
    if not cls:
        return None
    try:
        with open(os.path.join(folder, cls + ".md"), encoding="utf-8") as f:
            m = re.search(rf"^authorised:\s*{re.escape(list_id)}\s+(\S.*)$", f.read(), re.M)
    except OSError:
        return None
    return m.group(1) if m else None


def police_workbook(page: bytes):
    """(url, version day) of the Police workbook the 1267 page links to, or None."""
    m = _POLICE_XLSX.search(page.decode("utf-8", "replace"))
    if not m:
        return None
    d = _POLICE_DAY.search(m.group(1))
    day = None
    if d and d.group(2).lower() in _MONTHS:
        day = dt.date(int(d.group(3)), _MONTHS.index(d.group(2).lower()) + 1, int(d.group(1))).isoformat()
    return "https://www.police.govt.nz" + m.group(1), day


def mfat_day(page: bytes):
    """The day MFAT's register page says the register was updated, YYYY-MM-DD, or None."""
    text = re.sub(r"<[^>]+>", " ", page.decode("utf-8", "replace"))
    for m in _MFAT_DAY.finditer(text):
        if m.group(2).lower() in _MONTHS:
            return dt.date(int(m.group(3)), _MONTHS.index(m.group(2).lower()) + 1, int(m.group(1))).isoformat()
    return None


def off_peak(t: dt.datetime) -> bool:
    h = t.astimezone(NZ).hour
    return h >= OFF_PEAK[0] or h < OFF_PEAK[1]


# ── the lane's capture tables ─────────────────────────────────────────────────

READING = "-- ── the reading"


def tables_sql(schema: str = SCHEMA) -> str:
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        return f.read().split(READING)[0].replace(f"{SCHEMA}.", f"{schema}.")


class Tables:
    def __init__(self, conn, schema: str = SCHEMA):
        self.conn, self.s = conn, schema

    def create(self):
        self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.s}")
        self.conn.execute(tables_sql(self.s))

    def landed(self, list_id, role, url, sha, version, new, how, by=None):
        self.conn.execute(f"INSERT INTO {self.s}.capture_documents (list_id, role, url, sha256, version, new, how, by_whom) "
                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (list_id, role, url, sha, version, new, how, by))

    def set_aside(self, list_id, item, stage, reason):
        self.conn.execute(f"INSERT INTO {self.s}.capture_set_aside (list_id, item, stage, reason) VALUES (%s, %s, %s, %s)",
                          (list_id, item, stage, reason[:500]))

    def last_asked(self, list_id):
        """When the list was last asked after: its newest landing of the list or of the page that names its version,
        or its newest failed fetch; None if never."""
        return self.conn.execute(
            f"SELECT greatest((SELECT max(at) FROM {self.s}.capture_documents WHERE list_id = %s "
            "AND role IN ('list', 'register-page', 'page-1267')), "
            f"(SELECT max(at) FROM {self.s}.capture_set_aside WHERE list_id = %s AND stage = 'fetch'))",
            (list_id, list_id)).fetchone()[0]

    def held(self, list_id):
        """{role: {url: version}} of what is landed for the list."""
        out = {}
        for role, url, version in self.conn.execute(
                f"SELECT role, url, version FROM {self.s}.capture_documents WHERE list_id = %s ORDER BY at", (list_id,)):
            out.setdefault(role, {})[url] = version
        return out

    def versions(self, list_id, role="list"):
        return {r[0] for r in self.conn.execute(
            f"SELECT version FROM {self.s}.capture_documents WHERE list_id = %s AND role = %s AND version IS NOT NULL",
            (list_id, role))}


# ── a run ─────────────────────────────────────────────────────────────────────

class Run:
    def __init__(self, tables, *, land_fn, lists=LISTS, opener=None, authorised=None, clock=None, sleep=None,
                 now=None, anytime=False, due_now=False, log=print):
        self.t, self.land_fn, self.lists = tables, land_fn, lists
        #: the UN's XML redirects to a signed copy on another host (named in the position): one hop, judged by the gate
        self.opener = opener or (lambda url, timeout: fg.open_url(url, timeout=timeout, positions_dir=POSITIONS,
                                                                  follow=1 if url == UN_XML else 0))
        self.authorised = authorised or authorisation
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.now = now or (lambda: dt.datetime.now(NZ))
        self.anytime, self.due_now, self.log = anytime, due_now, log
        self.last_end = None
        self.failures = 0
        self.counts = {"requests": 0, "landed": 0, "new": 0, "already_held": 0, "held": 0, "not_due": 0,
                       "unchanged": 0, "set_aside": 0, "failed_lists": 0}
        self.stopped = ""
        self.failed = {}

    def get(self, list_id, url):
        if self.last_end is not None:
            gap = self.last_end + FLOOR_S - self.clock()
            if gap > 0:
                self.sleep(gap)
        self.counts["requests"] += 1
        try:
            f = self.opener(url, 120)
        except fg.Refused:
            raise
        except Exception as exc:  # noqa: BLE001
            self.last_end = self.clock()
            self.failures += 1
            self._aside(list_id, url, "fetch", f"transport: {type(exc).__name__}")
            if self.failures >= STOP_AFTER_FAILURES:
                raise Stop(f"{self.failures} transport failures in a row")
            return None
        self.last_end = self.clock()
        self.failures = 0
        if f.blocked:
            self._aside(list_id, url, "fetch", f.blocked)
            raise Stop(f.blocked)
        if f.status != 200 or not f.body:
            self._aside(list_id, url, "fetch", f"HTTP {f.status}" + ("" if f.body else ", empty"))
            return None
        return f

    def _aside(self, list_id, item, stage, why):
        self.t.set_aside(list_id, item, stage, why)
        self.counts["set_aside"] += 1

    def _land(self, list_id, role, url, body, version, content_type):
        ref, new = self.land_fn(body, name=url, source=SOURCE, name_kind="url", content_type=content_type)
        self.t.landed(list_id, role, url, ref.sha256, version, new, "fetched through the gate")
        self.counts["landed"] += 1
        self.counts["new" if new else "already_held"] += 1
        return ref

    def due(self, list_id) -> bool:
        if self.due_now:
            return True
        last = self.t.last_asked(list_id)
        return last is None or (self.now() - last).total_seconds() >= CADENCE_DAYS * 86400

    def one(self, list_id):
        if not self.authorised(list_id):
            self.counts["held"] += 1
            self.log(f"{SOURCE}: {list_id}: held on its publisher's terms; nothing asked for")
            return
        if not self.due(list_id):
            self.counts["not_due"] += 1
            self.log(f"{SOURCE}: {list_id}: asked within {CADENCE_DAYS} days; not due")
            return
        held = self.t.held(list_id)
        for role, url in DOCS[list_id].items():
            if url in held.get(role, {}):
                continue
            f = self.get(list_id, url)
            if f is not None:
                self._land(list_id, role, url, f.body, None, "text/html")
        if list_id == "un-sc":
            f = self.get(list_id, UN_XML)
            if f is not None:
                m = re.search(rb'dateGenerated="([^"]+)"', f.body[:2000])
                self._land(list_id, "list", UN_XML, f.body, m.group(1).decode() if m else None, "application/xml")
        elif list_id == "nz-police-tsa":
            page = self.get(list_id, POLICE_UN_PAGE)
            f1373 = self.get(list_id, POLICE_1373_PAGE)
            if f1373 is not None:
                self._land(list_id, "page-1373", POLICE_1373_PAGE, f1373.body, None, "text/html")
            if page is None:
                return
            self._land(list_id, "page-1267", POLICE_UN_PAGE, page.body, None, "text/html")
            wb = police_workbook(page.body)
            if wb is None:
                self._aside(list_id, POLICE_UN_PAGE, "parse", "the page links no designated-entities workbook")
                return
            if wb[0] in held.get("list", {}):
                self.counts["unchanged"] += 1
                self.log(f"{SOURCE}: {list_id}: the page links the workbook already landed; not fetched again")
                return
            f = self.get(list_id, wb[0])
            if f is not None:
                self._land(list_id, "list", wb[0], f.body, wb[1],
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        elif list_id == "mfat-russia":
            page = self.get(list_id, MFAT_PAGE)
            day = None
            if page is not None:
                self._land(list_id, "register-page", MFAT_PAGE, page.body, None, "text/html")
                day = mfat_day(page.body)
                if day and day in self.t.versions(list_id):
                    self.counts["unchanged"] += 1
                    self.log(f"{SOURCE}: {list_id}: the page says {day}, already landed; not fetched again")
                    return
            f = self.get(list_id, MFAT_FILE)
            if f is not None:
                if not f.body.startswith(b"PK"):
                    self._aside(list_id, MFAT_FILE, "fetch", "not a workbook (an .xlsx is a zip): a wall's page, not read")
                    raise Stop("the workbook address answered with a page that is not a workbook")
                self._land(list_id, "list", MFAT_FILE, f.body, day,
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def run(self) -> dict:
        if not self.anytime and not off_peak(self.now()):
            return {**self.counts, "stopped": "not off-peak; nothing asked for"}
        for list_id in self.lists:
            try:
                self.one(list_id)
            except Stop as exc:
                # a failed read of one list (hard limit 6): logged, set aside, never got around; the next list is asked
                self.failed[list_id] = str(exc)
                self.counts["failed_lists"] += 1
                self.log(f"{SOURCE}: {list_id}: failed read, set aside: {exc}")
        if self.failed:
            self.stopped = "stopped: " + "; ".join(f"{k}: {v}" for k, v in self.failed.items())
        return {**self.counts, "stopped": self.stopped, "failed": dict(self.failed)}


def by_hand(tables, land_fn, list_id: str, path: str, version: str, by: str) -> tuple:
    """A workbook a person downloaded in a browser, landed by hash with the
    publisher's address as a name. Only for a list whose terms allow the copy
    and bar only the robot (`BY_HAND`)."""
    if list_id not in BY_HAND:
        raise Held(f"{list_id}: a file by hand is not a way round its terms; it is held until authorised")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", version or ""):
        raise ValueError("--version is the day the publisher says the list was updated, YYYY-MM-DD")
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(b"PK"):
        raise ValueError("not a workbook (an .xlsx is a zip)")
    ref, new = land_fn(data, name=MFAT_FILE, source=SOURCE, name_kind="url",
                       content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    tables.landed(list_id, "list", MFAT_FILE, ref.sha256, version, new, "downloaded by a person and landed by hand", by)
    return ref, new


def landing(conn):
    from support.docstore.landing import land

    def land_fn(data, *, name, source, name_kind, content_type):
        return land(data, name=name, source=source, conn=conn, name_kind=name_kind, content_type=content_type)
    return land_fn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.sanctions.capture")
    ap.add_argument("--lists", default=",".join(LISTS))
    ap.add_argument("--anytime", action="store_true")
    ap.add_argument("--due-now", action="store_true", help="ask each list whatever its last ask (still off-peak)")
    ap.add_argument("--file", help="a workbook a person downloaded (mfat-russia only)")
    ap.add_argument("--list", default="mfat-russia")
    ap.add_argument("--version", help="the day the publisher says the list was updated")
    ap.add_argument("--by", default="arthur", help="who downloaded it")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default=SCHEMA)
    a = ap.parse_args(argv)
    from support import db, jobrun
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, a.database, autocommit=True) as conn:
        conn.execute("SET statement_timeout = '60s'")
        t = Tables(conn, a.schema)
        t.create()
        if a.file:
            try:
                ref, new = by_hand(t, landing(conn), a.list, a.file, a.version, a.by)
            except (Held, ValueError) as exc:
                print(f"{SOURCE}: refused: {exc}")
                return 2
            print(f"{SOURCE}: {a.list}: landed by hand ({'new' if new else 'already held'})")
            return 0
        out = Run(t, land_fn=landing(conn), lists=[x for x in a.lists.split(",") if x], anytime=a.anytime,
                  due_now=a.due_now).run()
    ok = not out["stopped"].startswith("stopped:")
    detail = (f"{out['requests']} requests, {out['landed']} landed ({out['new']} new), {out['held']} lists held, "
              f"{out['not_due']} not due, {out['unchanged']} unchanged, {out['set_aside']} set aside, "
              f"{out['failed_lists']} lists failed; {out['stopped'] or 'done'}")
    print(f"{SOURCE}: {detail}")
    if a.database == "querynz_v4":
        jobrun.record(JOB, ok, detail, started, out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
