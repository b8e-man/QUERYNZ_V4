"""How this lane's documents arrive: the Insolvency Register API (MBIE's portal, product "Insolvency Register", subscribed
in the estate's name, Arthur, 2 November 2026), through the fetch gate, one call at a time, each answer landed once by hash.

  GET {BASE}/insolvencies?date-from&date-to&register&page&page-size     the search by adjudication date (the bulk route the
                                                                        API keeps for holders of a copy)
  GET {BASE}/insolvencies/{estate-id}                                   one estate's detail
  GET {BASE}/insolvencies/removalorcorrections?date-from&date-to&page   estates removed or corrected in a period

The key is sent in the `Ocp-Apim-Subscription-Key` header the API's definition names (read 2 November 2026); it is read
from ~/.querynz/insolvency.env (INSOLVENCY_API_KEY) at call time and is never printed, logged, landed or put in a URL.

Every answer is landed whole, as received (ruling 142, 4 November 2026; before that its address fields and month and year
of birth were taken out first and the bytes as received only hashed, `calls.received`). The identifying fields are also
kept by field in the private ledger, `insolvency_private.identifiers`. The hours are 21:00 to 22:00 New Zealand time, before the companies
lane's 22:05 asks of the same host, and never on Wednesday (the interface's 21:00 to 23:00 maintenance); one call every
FLOOR_S seconds (the position's floor). A failed read (a block, a challenge, a 401, 403, 429 or 5xx) stops the run; a
lone transport failure (no answer at all: a name lookup, a reset, an SSL EOF) in the removals job is a line and waits for
the next run, three in a row stop it (as the charities lane, 1cd04be; the gate holds the host at three).

    python -m registers.insolvency.capture --removals        the daily removals-and-corrections job (qv4-insolvency-removals)
    python -m registers.insolvency.capture --night [--budget-s N] [--anytime]     the nightly search and details
    python -m registers.insolvency.capture --lookup ESTATE [ESTATE ...]          on demand, at most ten
"""
import datetime as dt
import http.client
import json
import os
import sys
import time
import urllib.parse
from zoneinfo import ZoneInfo

from support import db
from support.docstore.landing import land
from registers.insolvency import read

SOURCE = "insolvency"
SCHEMA = "insolvency"
NZ = ZoneInfo("Pacific/Auckland")
BASE = os.environ.get("QV4_INSOLVENCY_API_BASE") or "https://api.business.govt.nz/gateway/insolvency-trustee-services/v5"   # the version is in the path (as the NZBN API's); without it every call is a 404 (2 November 2026)
KEY_FILE = "insolvency.env"
KEY_NAME = "INSOLVENCY_API_KEY"
KEY_HEADER = "Ocp-Apim-Subscription-Key"
FLOOR_S = 5.0                       # docs/legal/positions/insolvency-register.md: "Floor: 5 s between requests"
SEARCH_PAGE = 100
REMOVALS_PAGE = 1000
#: the search walks adjudication dates back to here, a month at a time; the register keeps nothing older that it shows
SEARCH_FROM = dt.date(1990, 1, 1)
#: the latest days searched again every night, for estates entered late and status changes
RECENT_DAYS = 60
#: a detail older than this is asked again (a discharge moves the window)
DETAIL_EVERY_DAYS = 30
REMOVALS_MAX_SPAN_DAYS = 90         # the API: date-to "cannot be more than 3 months from date-from"
LOOKUP_MAX = 10
#: the removals' re-asks a run, in seconds: the rest wait in the ledger for the next run (5 November 2026: 330 re-asks
#: at 5 s took 1,782 s of the job's 1,800 s, and 596 were still waiting)
REASK_BUDGET_S = 1200
#: transport failures in a row (no answer at all) that stop a run; the gate holds the host at the same count
STOP_AFTER_FAILURES = 3
JOB_REMOVALS = "qv4-insolvency-removals"
JOB_NIGHT = "qv4-insolvency-capture"
_LAST = {"at": 0.0}


def api_key() -> str:
    """The estate's key, read now from the credential folder. Never print it."""
    path = os.path.join(db.CRED_DIR, KEY_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(KEY_NAME + "="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError as exc:
        raise RuntimeError(f"no Insolvency Register credential file: {type(exc).__name__}") from None
    raise RuntimeError(f"{KEY_NAME} is not set in {KEY_FILE}")


def now_nz() -> dt.datetime:
    return dt.datetime.now(NZ)


def off_peak(t: dt.datetime) -> bool:
    """21:00 to 22:00 New Zealand time, never a Wednesday (the interface's maintenance runs 21:00 to 23:00)."""
    nz = t.astimezone(NZ)
    return nz.weekday() != 2 and nz.hour == 21


def tables_sql(schema: str = SCHEMA) -> str:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tables.sql"), encoding="utf-8") as f:
        return f.read().replace("{p}", private_of(schema)).replace("{s}", schema)


def private_of(schema: str = SCHEMA) -> str:
    """The lane's private schema beside `schema` (`insolvency_private`): the identifying fields, never seen by the
    session or product logins."""
    return schema + "_private"


def ledger_sql(schema: str = SCHEMA) -> str:
    """The capture's own tables only (calls, removals, cursor): made if missing, never dropped."""
    sql = tables_sql(schema)
    return sql.split("-- the reading: rebuilt whole by every load")[0]


def ledger_stamp(schema: str = SCHEMA) -> str:
    import hashlib
    return "insolvency ledger ddl " + hashlib.sha256(ledger_sql(schema).encode()).hexdigest()[:16]


def ensure_ledger(conn, schema: str = SCHEMA) -> bool:
    """The ledger's tables as ledger_sql declares them; True when the DDL ran. Its ALTER ... ADD COLUMN IF NOT EXISTS
    takes the table's exclusive lock even where the column is there, so it waited behind any reader of the ledger
    (7 November 2026: the night's capture cancelled at its 300 s statement limit on that line, before its first call).
    The DDL runs only when it is not the one applied last: its stamp is the comment on the cursor table, read from the
    catalogue with no lock on the tables; one job at a time under an advisory lock, the stamp read again once held."""
    stamp = ledger_stamp(schema)

    def current():
        row = conn.execute("SELECT obj_description(to_regclass(%s), 'pg_class')", (f"{schema}.cursor",)).fetchone()
        return bool(row) and row[0] == stamp
    if current():
        return False
    conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"{schema} ledger ddl",))
    if current():
        return False
    conn.execute(ledger_sql(schema))
    conn.execute(f"COMMENT ON TABLE {schema}.cursor IS '{stamp}'")
    return True


def url_for(path: str, params: dict = None) -> str:
    q = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
    return f"{BASE}{path}" + (f"?{q}" if q else "")


class Answer:
    def __init__(self, status, body, sha, blocked, total=None, call=None):
        self.status, self.body, self.sha, self.blocked, self.total, self.call = status, body, sha, blocked, total, call


def call(conn, path: str, params: dict, why: str, *, estate: int = None, schema: str = SCHEMA, key: str = None,
         fetch=None, pacer=None, positions_dir: str = None, ledger_dir: str = None, sleep=time.sleep,
         clock=time.monotonic, now=now_nz) -> Answer:
    """One gated call, never two at once, at least FLOOR_S apart; the answer landed whole, its identifying fields also
    kept in the private ledger; the call recorded."""
    import hashlib
    from support import fetchgate
    url = url_for(path, params)
    gap = _LAST["at"] + FLOOR_S - clock()
    if gap > 0 and fetch is None:
        sleep(gap)
    try:
        got = fetchgate.open_url(url, timeout=30, headers={KEY_HEADER: key or api_key(), "Accept": "application/json"},
                                 pacer=pacer, fetch=fetch, positions_dir=positions_dir, ledger_dir=ledger_dir)
    except (OSError, http.client.HTTPException) as exc:   # the gate re-raises both after counting the strike
        got = fetchgate.Fetched(url=url, status=0, body=b"", final_url=url,
                                blocked=f"no answer: {type(exc).__name__}: {str(exc)[:200]}")
    _LAST["at"] = clock()
    at = now()
    sha = received = total = None
    blocked = got.blocked
    body = b""
    if got.status == 200 and not blocked:
        try:
            body = got.body
            kind = read.recognise(json.loads(body))
            if kind is None:
                blocked = "HTTP 200 that is none of the three answers: a failed read"
            else:
                received = hashlib.sha256(got.body).hexdigest()
                total = json.loads(body).get("totalItems") if kind != "estate" else None
                ref, _ = land(body, name=url, source=SOURCE, conn=conn, name_kind="url",
                              fetched_at=at.isoformat(timespec="seconds"), content_type="application/json")
                sha = ref.sha256
        except ValueError:
            blocked = "HTTP 200 that is not JSON: a failed read"
    asked = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
    cid = conn.execute(f"INSERT INTO {schema}.calls (at, day, why, asked, estate, status, document, received, total_items, "
                       f"blocked) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                       (at, at.date(), why, f"{path}?{asked}" if asked else path, estate, got.status, sha, received,
                        total, blocked)).fetchone()[0]
    if sha:
        keep_identifiers(conn, json.loads(got.body), cid, at, schema)
    return Answer(got.status, body if sha else b"", sha, blocked, total, cid)


def keep_identifiers(conn, answer, call_id: int, at: dt.datetime, schema: str = SCHEMA) -> int:
    """The identifying fields, into the private ledger, by estate and field: a search page's results add or update
    theirs; a detail answer does too, and a field of that estate it no longer gives is marked `gone_at`, never deleted
    (ruling 142). Never published."""
    rows = read.identifiers(answer)
    p = private_of(schema)
    if read.recognise(answer) == "estate" and answer.get("estateNumber") is not None:
        conn.execute(f"UPDATE {p}.identifiers SET gone_at = %s WHERE estate = %s AND gone_at IS NULL AND at <= %s "
                     f"AND NOT (field = ANY(%s))", (at, int(answer["estateNumber"]), at,
                                                    [f for e, f, _ in rows if e == int(answer["estateNumber"])]))
    for estate, field, value in rows:
        conn.execute(f"INSERT INTO {p}.identifiers (estate, field, value, call, at) VALUES (%s, %s, %s, %s, %s) "
                     f"ON CONFLICT (estate, field) DO UPDATE SET value = EXCLUDED.value, call = EXCLUDED.call, "
                     f"at = EXCLUDED.at, gone_at = NULL, removed_at = NULL, removal_said = NULL "
                     f"WHERE {p}.identifiers.at <= EXCLUDED.at",
                     (estate, field, value, call_id, at))
    return len(rows)


def failed(a: Answer) -> bool:
    """A read that stops the run: anything but a landed 200 or the register's own 404."""
    return bool(a.blocked) or a.status not in (200, 404)


# --- the removals: the API's own term, recorded as a flag the moment an estate is named -------------------------------

def removal_said(removed_on) -> str:
    """The API's words for a removal, as the removals page gives them."""
    return f"removedOrCorrectedInsolvencies, removedDate {removed_on}"


def apply_removal(conn, estate: int, schema: str = SCHEMA, at: dt.datetime = None, removed_on=None) -> int:
    """The estate flagged at once (ruling 142: a removal a source states is a flag beside the row, never a delete): its
    row in the lane's tables gets `removed_on` and `removal_seen_at`, and its identifying fields from before the removal
    `removed_at` and the API's words. Nothing is deleted and no document is withdrawn. Returns the rows flagged."""
    at = at or now_nz()
    n = conn.execute(f"UPDATE {schema}.estates SET removed_on = %s, removal_seen_at = %s WHERE estate_number = %s",
                     (removed_on, at, estate)).rowcount \
        if conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"{schema}.estates",)).fetchone()[0] else 0
    conn.execute(f"UPDATE {private_of(schema)}.identifiers SET removed_at = %s, removal_said = %s WHERE estate = %s "
                 f"AND at <= %s", (at, removal_said(removed_on), estate, at))
    return n


def transport_failed(a: Answer) -> bool:
    """No answer at all (a name lookup, a reset, an SSL EOF, a timeout): not a refusal, a block or a status. The gate
    itself holds the host after three of these in a row (support/fetchgate)."""
    return a.status == 0 and (a.blocked or "").startswith("no answer:")


def maintenance(t: dt.datetime) -> bool:
    """The interface's maintenance: Wednesday 21:00 to 23:00 New Zealand time."""
    nz = t.astimezone(NZ)
    return nz.weekday() == 2 and 21 <= nz.hour < 23


def removals_items(body: bytes) -> dict:
    """{estate: sha256 of its item, keys sorted} on a removals page: the same item named again is the same event."""
    import hashlib
    return {int(r["estateNumber"]): hashlib.sha256(json.dumps(r, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            for r in (json.loads(body).get("removedOrCorrectedInsolvencies") or []) if r.get("estateNumber") is not None}


def reasks_wanted(conn, schema: str = SCHEMA) -> list:
    """Estates a removal or correction named that we hold (a search named it, or someone looked it up before the
    naming) with no answered detail (200 or 404) since the naming, the longest waiting first. A detail call that got no
    answer is not an answer (5 November 2026: the failed call would otherwise have counted as asked)."""
    return [r[0] for r in conn.execute(
        f"SELECT r.estate FROM {schema}.removals r WHERE NOT EXISTS (SELECT 1 FROM {schema}.calls c WHERE c.estate = "
        f"r.estate AND c.why = 'detail' AND c.status IN (200, 404) AND c.at > r.seen_at) AND (EXISTS (SELECT 1 FROM "
        f"{schema}.search_seen s WHERE s.estate = r.estate) OR EXISTS (SELECT 1 FROM {schema}.calls c WHERE c.estate = "
        f"r.estate AND c.why = 'lookup' AND c.at <= r.seen_at)) GROUP BY r.estate ORDER BY min(r.seen_at), r.estate"
    ).fetchall()]


def run_removals(conn, schema: str = SCHEMA, *, today: dt.date = None, log=print, now=now_nz, clock=time.monotonic,
                 budget_s: float = REASK_BUDGET_S, **gate) -> dict:
    """The daily job: every estate removed or corrected since the cursor, in spans of at most three months, every page;
    each one newly named flagged at once; the cursor moved to today once every page is read; then the estates named and
    held asked again (a correction comes back as a new detail; a removal stays flagged), at most `budget_s` of them a
    run, never in the Wednesday maintenance; what is left waits in the ledger for the next run.

    The span starts on the cursor's day, so an estate named yesterday is on today's page again: an item the same as the
    estate's latest naming is that naming, counted `repeated`, not recorded, flagged or asked again (5 November 2026:
    each day re-recorded the last days' namings under a new time, and every one was asked again). A lone transport
    failure (no answer at all) is a line: on a page, the pages stop there and the cursor stays for the next run; on a
    re-ask, that estate waits for the next run. Three in a row stop the run, as any refusal, block or status does."""
    today = today or now().date()
    t0 = clock()
    ensure_ledger(conn, schema)
    row = conn.execute(f"SELECT value FROM {schema}.cursor WHERE what = 'removals'").fetchone()
    start = dt.date.fromisoformat(row[0]) if row else today - dt.timedelta(days=REMOVALS_MAX_SPAN_DAYS)
    counts = {"calls": 0, "named": 0, "repeated": 0, "flagged": 0, "asked_again": 0, "corrected": 0, "no_answer": 0}
    notes, in_a_row, missed = [], 0, 0

    def give_up(a):
        conn.commit()
        why = (f"{in_a_row} transport failures in a row, the last {a.blocked}" if transport_failed(a)
               else a.blocked or f"HTTP {a.status}")
        return {**counts, "ok": False, "stopped": f"a failed read: {why}"}

    pages_whole = True
    while start <= today and pages_whole:
        end = min(today, start + dt.timedelta(days=REMOVALS_MAX_SPAN_DAYS - 1))
        page = 1
        while True:
            a = call(conn, "/insolvencies/removalorcorrections", {"date-from": start.isoformat(), "date-to": end.isoformat(),
                     "page": page, "page-size": REMOVALS_PAGE}, "removals", schema=schema, **gate)
            counts["calls"] += 1
            if transport_failed(a):
                in_a_row += 1
                counts["no_answer"] += 1
                conn.commit()
                if in_a_row >= STOP_AFTER_FAILURES:
                    return give_up(a)
                log(f"insolvency removals: a removals page got no answer ({a.blocked[:120]}); asked again from "
                    f"{start.isoformat()} next run")
                notes.append(f"the removals page from {start.isoformat()} got no answer and is asked again next run")
                pages_whole = False
                break
            if failed(a):
                return give_up(a)
            in_a_row = 0
            named, total = read.removals_named(a.body) if a.sha else ([], 0)
            items = removals_items(a.body) if a.sha else {}
            seen = conn.execute(f"SELECT at FROM {schema}.calls WHERE id = %s", (a.call,)).fetchone()[0]
            for estate, removed_on in named:
                counts["named"] += 1
                last = conn.execute(f"SELECT item_sha FROM {schema}.removals WHERE estate = %s ORDER BY seen_at DESC, "
                                    f"call DESC LIMIT 1", (estate,)).fetchone()
                if last and last[0] is not None and last[0] == items.get(estate):
                    counts["repeated"] += 1
                    continue
                conn.execute(f"INSERT INTO {schema}.removals (estate, removed_on, call, seen_at, item_sha) VALUES "
                             f"(%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                             (estate, removed_on, a.call, seen, items.get(estate)))
                counts["flagged"] += apply_removal(conn, estate, schema, seen, removed_on)
            conn.commit()
            if not named or page * REMOVALS_PAGE >= (total or 0):
                break
            page += 1
        start = end + dt.timedelta(days=1)
    if pages_whole:     # every page read: the namings are in the ledger and the re-asks below come from it
        conn.execute(f"INSERT INTO {schema}.cursor (what, value, at) VALUES ('removals', %s, now()) "
                     f"ON CONFLICT (what) DO UPDATE SET value = EXCLUDED.value, at = now()", (today.isoformat(),))
        conn.commit()
    # a correction: the estate asked again; a 200 is the corrected record (read by the next load), a 404 is gone. Only
    # an estate we hold (a search named it, or someone looked it up): one never seen comes in through the search like
    # any other, and the first run's list (1,511 named, back to the API's start) would take two hours at 5 s a call. A
    # detail call alone is not holding: the removals' own re-asks are detail calls, and counting them made every
    # estate the first run re-asked "held" the next day (3 November 2026)
    wanted = reasks_wanted(conn, schema)
    if wanted and maintenance(now()):
        notes.append(f"{len(wanted)} re-asks wait for the next run (the interface's Wednesday maintenance)")
        wanted = []
    for i, estate in enumerate(wanted):
        if clock() - t0 >= budget_s:
            notes.append(f"{len(wanted) - i} re-asks wait for the next run (the run's {budget_s:.0f} s)")
            break
        a = call(conn, f"/insolvencies/{estate}", {}, "detail", estate=estate, schema=schema, **gate)
        counts["calls"] += 1
        conn.commit()
        if transport_failed(a):
            in_a_row += 1
            counts["no_answer"] += 1
            if in_a_row >= STOP_AFTER_FAILURES:
                return give_up(a)
            missed += 1
            log(f"insolvency removals: estate {estate}'s re-ask got no answer ({a.blocked[:120]}); asked next run")
            continue
        if failed(a):
            return give_up(a)
        in_a_row = 0
        counts["asked_again"] += 1
        counts["corrected"] += 1 if a.sha else 0
    if missed:
        notes.append(f"{missed} re-ask(s) got no answer and are asked next run")
    log("insolvency removals: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + "".join(f"; {n}" for n in notes))
    return {**counts, "ok": True, "stopped": "; ".join(notes)}


# --- the nightly capture: the search by adjudication date, then the details it needs -----------------------------------

def windows(since: dt.date, today: dt.date):
    """Calendar months from `since` to today, oldest first: [(first day, last day)]."""
    d = since.replace(day=1)
    while d <= today:
        nxt = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        yield d, min(today, nxt - dt.timedelta(days=1))
        d = nxt


def details_wanted(conn, schema: str = SCHEMA, today: dt.date = None) -> list:
    """Estates a search page named whose detail is missing or older than DETAIL_EVERY_DAYS, never one removed since."""
    today = today or now_nz().date()
    return [r[0] for r in conn.execute(
        f"SELECT s.estate FROM {schema}.search_seen s WHERE NOT EXISTS (SELECT 1 FROM {schema}.calls c WHERE c.estate = "
        f"s.estate AND c.why IN ('detail', 'lookup') AND c.status IN (200, 404) AND c.day > %s) ORDER BY s.estate",
        (today - dt.timedelta(days=DETAIL_EVERY_DAYS),)).fetchall()]


def run_night(conn, schema: str = SCHEMA, *, budget_s: float = 3300, anytime: bool = False, today: dt.date = None,
              now=now_nz, log=print, **gate) -> dict:
    """The search walked month by month from the cursor (back to SEARCH_FROM on the first nights), the latest RECENT_DAYS
    again, both registers; then the details wanted; until the hours, the budget, or a failed read."""
    t0 = time.monotonic()
    today = today or now().date()
    ensure_ledger(conn, schema)
    counts = {"calls": 0, "search_pages": 0, "estates_seen": 0, "details": 0, "absent": 0}

    def stop():
        if not anytime and not off_peak(now()):
            return "off-peak ended"
        if time.monotonic() - t0 >= budget_s:
            return "budget spent"
        return ""

    def bad(a):
        conn.commit()
        return {**counts, "ok": False, "stopped": f"a failed read: {a.blocked or f'HTTP {a.status}'}"}

    for register in ("Insolvency", "DRO"):
        row = conn.execute(f"SELECT value FROM {schema}.cursor WHERE what = %s", (f"search/{register}",)).fetchone()
        walked_to = dt.date.fromisoformat(row[0]) if row else SEARCH_FROM - dt.timedelta(days=1)
        recent_from = today - dt.timedelta(days=RECENT_DAYS)
        back = [(f, min(l, recent_from - dt.timedelta(days=1)), True)
                for f, l in windows(walked_to + dt.timedelta(days=1), recent_from - dt.timedelta(days=1))]
        spans = back + [(max(f, recent_from), l, False) for f, l in windows(recent_from, today)]
        for first, last, walking_back in spans:
            page = 1
            while True:
                if (why := stop()):
                    conn.commit()
                    return {**counts, "ok": True, "stopped": why}
                a = call(conn, "/insolvencies", {"date-from": first.isoformat(), "date-to": last.isoformat(),
                         "register": register, "page": page, "page-size": SEARCH_PAGE}, "search", schema=schema, **gate)
                counts["calls"] += 1
                counts["search_pages"] += 1
                if failed(a):
                    return bad(a)
                results, total = read.search_results(a.body) if a.sha else ([], 0)
                for r in results:
                    conn.execute(f"INSERT INTO {schema}.search_seen (estate, register, call) VALUES (%s, %s, %s) "
                                 f"ON CONFLICT (estate) DO UPDATE SET call = EXCLUDED.call",
                                 (int(r["estateNumber"]), register, a.call))
                    counts["estates_seen"] += 1
                conn.commit()
                if not results or page * SEARCH_PAGE >= (total or 0):
                    break
                page += 1
            if walking_back:   # a month walked whole is not walked again; the latest days are, every night
                conn.execute(f"INSERT INTO {schema}.cursor (what, value) VALUES (%s, %s) ON CONFLICT (what) DO UPDATE SET "
                             f"value = GREATEST({schema}.cursor.value, EXCLUDED.value), at = now()",
                             (f"search/{register}", last.isoformat()))
                conn.commit()
    for estate in details_wanted(conn, schema, today):
        if (why := stop()):
            conn.commit()
            return {**counts, "ok": True, "stopped": why}
        a = call(conn, f"/insolvencies/{estate}", {}, "detail", estate=estate, schema=schema, **gate)
        counts["calls"] += 1
        counts["details" if a.sha else "absent"] += 1
        conn.commit()
        if failed(a):
            return bad(a)
    return {**counts, "ok": True, "stopped": "nothing wanted is left"}


def lookup(conn, estates: list, schema: str = SCHEMA, **gate) -> list:
    """On demand: at most LOOKUP_MAX estates' details, now. [(estate, status, landed sha or None)]."""
    if len(estates) > LOOKUP_MAX:
        raise ValueError(f"at most {LOOKUP_MAX}: a lookup is on demand, not a copy")
    ensure_ledger(conn, schema)
    out = []
    for e in estates:
        a = call(conn, f"/insolvencies/{int(e)}", {}, "lookup", estate=int(e), schema=schema, **gate)
        conn.commit()
        out.append((int(e), a.status, a.sha))
        if failed(a):
            break
    return out


def main(argv=None) -> int:
    from support import jobrun
    argv = argv if argv is not None else sys.argv[1:]
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '300s'")
        if "--removals" in argv:
            started = jobrun.now()
            out = run_removals(conn)
            jobrun.record(JOB_REMOVALS, out["ok"], ", ".join(f"{k} {v}" for k, v in out.items() if k != "ok"), started, {})
            return 0 if out["ok"] else 1
        if "--night" in argv:
            started = jobrun.now()
            budget = float(argv[argv.index("--budget-s") + 1]) if "--budget-s" in argv else 3300
            out = run_night(conn, budget_s=budget, anytime="--anytime" in argv)
            detail = ", ".join(f"{k} {v}" for k, v in out.items() if k != "ok")
            print("insolvency night: " + detail)
            jobrun.record(JOB_NIGHT, out["ok"], detail, started, {})
            return 0 if out["ok"] else 1
        if "--lookup" in argv:
            for e, status, sha in lookup(conn, argv[argv.index("--lookup") + 1:]):
                print(f"estate {e}: HTTP {status}" + (f", landed {sha[:12]}" if sha else ""))
            return 0
    print(__doc__.strip().splitlines()[-1].strip())
    return 2


if __name__ == "__main__":
    sys.exit(main())
