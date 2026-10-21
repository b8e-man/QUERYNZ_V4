"""The lane's check against the world outside it (contract: the lane).

The Companies Office publishes its own counts of the register
(https://www.companiesoffice.govt.nz/insights-and-articles/latest-company-statistics/,
"Last updated 5 October 2026", read 20 October 2026; the monthly series is
its file `monthly-company-statistics-since-2001.csv` on that page). Two kinds
are pinned below, as printed:

  QUARTERS   "There were N registered companies at <quarter end>"
  MONTHS     each calendar month's company incorporations and removals

Against them, the lane's own company rows (the five company types, register
`companies`), from the dates each row files:

  live on a day    registered on or before it, and not removed by it
  incorporated     registered in the month
  removed          removed in the month

Only days and months before the file's cut are compared (the cut is the
latest registration date the latest file holds). The check fails when the
last quarter end before the cut differs by more than LIVE_TOLERANCE, or a
month's incorporations by more than MONTH_TOLERANCE, or its removals by more
than REMOVAL_TOLERANCE. Earlier quarter ends are reported, never failed: a
company restored to the register files no removal date, so the live count
drifts above the Office's as the day goes back (0.02% at 30 June 2026,
0.27% at 30 September 2021).

The figures were read through a session's web reader, not the fetch gate:
no legal position yet covers companiesoffice.govt.nz (card
`the-companies-office-statistics-file-has-no-legal-position`). The old
estate's rows reproduce every month's incorporations to within one, which
is how the reading of the figures was checked.

    figures(live, months, cut)   the comparison, from the lane's counts
    failed(f)                    the reasons the check fails, empty when it passes
    python -m registers.companies.check [--schema companies | scratch_<session>] [--database querynz_v4]

The monitor (plan 5.5; monitor.py) is checked beside it, from its own
tables (`monitor_failed`): every change cites an answer the ledger shows
landed (HTTP 200, the document in the store's table); every request older
than the monitor's ANSWER_WITHIN is answered by a landed call or set aside
with its reason; no New Zealand day holds more calls than DAILY_LIMIT (the
interface states no limit; the limit is ours, docs/status/companies.md).

Read-only.
"""
import datetime as dt
import os
import sys

SOURCE = "https://www.companiesoffice.govt.nz/insights-and-articles/latest-company-statistics/"
LIVE_TOLERANCE = 0.001
MONTH_TOLERANCE = 0.005
REMOVAL_TOLERANCE = 0.02

QUARTERS = {
    "2021-09-30": 691500, "2021-12-31": 698163, "2022-03-31": 698546, "2022-06-30": 705936,
    "2022-09-30": 710364, "2022-12-31": 711599, "2023-03-31": 716503, "2023-06-30": 724244,
    "2023-09-30": 722997, "2023-12-31": 726359, "2024-03-31": 726727, "2024-06-30": 731314,
    "2024-09-30": 734808, "2024-12-31": 733219, "2025-03-31": 738687, "2025-06-30": 745169,
    "2025-09-30": 744728, "2025-12-31": 744378, "2026-03-31": 749895, "2026-06-30": 756821,
    "2026-09-30": 752292,
}
#: (year, month): (incorporations, removals)
MONTHS = {
    (2025, 4): (5309, 1223), (2025, 5): (5605, 3849), (2025, 6): (5045, 4433), (2025, 7): (5585, 1787),
    (2025, 8): (5167, 11635), (2025, 9): (5358, 3240), (2025, 10): (5251, 2343), (2025, 11): (4809, 4732),
    (2025, 12): (4106, 7559), (2026, 1): (4461, 4201), (2026, 2): (5139, 4709), (2026, 3): (6213, 1528),
    (2026, 4): (5325, 1497), (2026, 5): (5501, 3525), (2026, 6): (5527, 4529), (2026, 7): (5517, 3285),
    (2026, 8): (5047, 10523), (2026, 9): (5068, 3983),
}

_MONTHS_SQL = """
SELECT 'i', extract(year FROM registered_on)::int, extract(month FROM registered_on)::int, count(*)
  FROM {t} WHERE register = 'companies' AND registered_on >= %(since)s GROUP BY 2, 3
UNION ALL
SELECT 'r', extract(year FROM removed_on)::int, extract(month FROM removed_on)::int, count(*)
  FROM {t} WHERE register = 'companies' AND removed_on >= %(since)s GROUP BY 2, 3
"""


def _off(got: int, want: int) -> float:
    return abs(got - want) / want if want else float(got != 0)


def figures(live: dict, months: dict, cut: str) -> dict:
    """live: {quarter end: the lane's live count}; months: {(y, m): (incorporated, removed)};
    cut: the latest registration date in the latest file."""
    cut_d = dt.date.fromisoformat(cut)
    qs = [(d, live.get(d), want) for d, want in sorted(QUARTERS.items()) if dt.date.fromisoformat(d) <= cut_d]
    ms = []
    for (y, m), (inc, rem) in sorted(MONTHS.items()):
        if (y, m) < (cut_d.year, cut_d.month):
            got = months.get((y, m), (0, 0))
            ms.append(((y, m), got, (inc, rem)))
    return {"cut": cut, "quarters": qs, "months": ms}


def failed(f: dict) -> list:
    why = []
    if not f["quarters"]:
        why.append("no quarter end the Companies Office printed falls before the file's cut")
    else:
        d, got, want = f["quarters"][-1]
        if got is None or _off(got, want) > LIVE_TOLERANCE:
            why.append(f"live on {d}: the lane has {got}, the Companies Office {want:,}")
    if not f["months"]:
        why.append("no month the Companies Office printed falls before the file's cut")
    for (y, m), (inc, rem), (winc, wrem) in f["months"]:
        if _off(inc, winc) > MONTH_TOLERANCE:
            why.append(f"{y}-{m:02d}: {inc:,} incorporated in the lane, {winc:,} by the Companies Office")
        if _off(rem, wrem) > REMOVAL_TOLERANCE:
            why.append(f"{y}-{m:02d}: {rem:,} removed in the lane, {wrem:,} by the Companies Office")
    return why


def measure(conn, t: str) -> dict:
    """The lane's counts from its entities table `t`: one query each, inside the database."""
    live = ", ".join(f"count(*) FILTER (WHERE register = 'companies' AND registered_on <= DATE '{d}' AND "
                     f"(removed_on IS NULL OR removed_on > DATE '{d}'))" for d in QUARTERS)
    row = conn.execute(f"SELECT (SELECT max(registered_on) FROM {t} WHERE register = 'companies' AND in_latest), "
                       f"{live} FROM {t}").fetchone()
    since = dt.date(*min(MONTHS), 1)
    months = {}
    for kind, y, m, n in conn.execute(_MONTHS_SQL.format(t=t), {"since": since}).fetchall():
        inc, rem = months.get((y, m), (0, 0))
        months[(y, m)] = (n, rem) if kind == "i" else (inc, n)
    return figures(dict(zip(QUARTERS, row[1:])), months, row[0].isoformat() if row[0] else "1900-01-01")


def in_store(sha: str) -> bool:
    """The answer's bytes are in the document store (the store's own path; its tables are support's)."""
    from support.docstore.landing import path_for
    return os.path.exists(path_for(sha))


def monitor_failed(conn, t, now=None) -> list:
    """The monitor's three checks. `t(name)` is a table's full name."""
    from registers.companies import monitor as M
    now = now or M.now_nz()
    why = []
    n = conn.execute(f"SELECT count(*) FROM {t('changes')} ch WHERE NOT EXISTS (SELECT 1 FROM {t('calls')} c "
                     f"WHERE c.id = ch.call_id AND c.status = 200 AND c.document = ch.document)").fetchone()[0]
    n += sum(1 for (sha,) in conn.execute(f"SELECT DISTINCT document FROM {t('changes')}") if not in_store(sha))
    if n:
        why.append(f"{n} change(s) cite no answer the ledger shows landed")
    n = conn.execute(f"SELECT count(*) FROM {t('requests')} r WHERE (r.state = 'waiting' AND r.asked_at < %s) "
                     f"OR (r.state = 'answered' AND NOT EXISTS (SELECT 1 FROM {t('calls')} c WHERE c.id = r.call_id "
                     f"AND c.status = 200 AND c.document IS NOT NULL)) "
                     f"OR (r.state = 'set_aside' AND coalesce(btrim(r.reason), '') = '')",
                     (now - M.ANSWER_WITHIN,)).fetchone()[0]
    if n:
        why.append(f"{n} request(s) neither answered by a landed call nor set aside with a reason within "
                   f"{int(M.ANSWER_WITHIN.total_seconds() // 3600)} hours")
    for day, calls in conn.execute(f"SELECT day, count(*) FROM {t('calls')} GROUP BY day HAVING count(*) > %s "
                                   f"ORDER BY day", (M.DAILY_LIMIT,)).fetchall():
        why.append(f"{day}: {calls} calls to the interface, over the day's limit of {M.DAILY_LIMIT}")
    return why


def report(f: dict) -> list:
    out = [f"The latest file's cut: {f['cut']}. Live companies on a quarter end, the lane against the Companies Office:"]
    for d, got, want in f["quarters"]:
        out.append(f"  {d}: {got:,} against {want:,} ({100 * (got - want) / want:+.2f}%)")
    out.append("Each month, incorporated and removed, the lane against the Companies Office:")
    for (y, m), (inc, rem), (winc, wrem) in f["months"]:
        out.append(f"  {y}-{m:02d}: {inc:,} / {winc:,} incorporated, {rem:,} / {wrem:,} removed")
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "companies"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    from registers.companies.load import table
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        conn.execute("SET statement_timeout = '120s'")
        # the sample's shared schema names the lane's tables `companies_…`; a lane or staging schema does not
        shared = conn.execute("SELECT to_regclass(%s) IS NOT NULL", (table(schema, "entities", True),)).fetchone()[0]
        f = measure(conn, table(schema, "entities", shared))
        mon = monitor_failed(conn, lambda n: table(schema, n, shared))
    for line in report(f):
        print(line)
    why = failed(f) + mon
    for w in why:
        print("FAILS " + w)
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main())
