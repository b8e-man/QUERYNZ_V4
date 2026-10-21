"""The lane's checks (contract: the lane, "its one figure checked against the
outside world"). Exit 1 on any problem; every line printed is a count.

  outside   the held count of the newest finished full pass against the
            interface's own figure, probed by offset at the pass's start;
            and the figure probed now, beside it (cases added since)
  reading   every record of every page is a case row, superseded or in the
            catch log (the ledger); parties per case; suppression counts;
            no withheld name and no suppressed case's title on a view; no
            party row without its private name; the catch log's reasons

    python -m registers.openlaw.check [--schema openlaw] [--views pub] [--database querynz_v4]
    python -m registers.openlaw.check --probe-only      # the interface's figure now; nothing kept

Until OpenLaw authorises copies (API terms 3.6(a)) nothing is held, and the
outside check says so and is red: a lane fed by nothing is not green.
"""
import argparse
import json
import sys

from registers.openlaw import capture, load


def _one(conn, sql, args=()):
    return conn.execute(sql, args).fetchone()


def reading(conn, schema: str = load.SCHEMA, views: str = "pub", shared: bool = False) -> dict:
    T = lambda t: load.table(schema, t, shared)
    problems, figures = [], {}
    pages = conn.execute(f"SELECT count(*), coalesce(sum(cases), 0), coalesce(sum(typed), 0), coalesce(sum(set_aside), 0), "
                         f"coalesce(sum(superseded), 0), count(*) FILTER (WHERE skipped <> 0) FROM {T('read_pages')}").fetchone()
    figures.update(dict(zip(("pages", "records", "typed", "set_aside", "superseded", "pages_not_reconciled"), pages)))
    if pages[5]:
        problems.append(f"{pages[5]} page(s) do not reconcile: records in ≠ typed + superseded + set aside")
    n_cases = _one(conn, f"SELECT count(*) FROM {T('cases')}")[0]
    if n_cases != pages[2]:
        problems.append(f"{n_cases} case rows against {pages[2]} typed in the ledger")
    figures["cases"] = n_cases
    per = conn.execute(f"SELECT n, count(*) FROM (SELECT c.key, count(p.key) AS n FROM {T('cases')} c "
                       f"LEFT JOIN {T('parties')} p ON p.case_key = c.key GROUP BY c.key) x GROUP BY n ORDER BY n").fetchall()
    figures["parties_per_case"] = {int(n): k for n, k in per}
    figures["parties_from"] = dict(conn.execute(f"SELECT parties_from, count(*) FROM {T('cases')} GROUP BY 1 ORDER BY 1").fetchall())
    s = _one(conn, f"SELECT count(*) FILTER (WHERE suppressed), count(*) FILTER (WHERE 'anonymised-party' = ANY(suppression_marks)) "
                   f"FROM {T('cases')}")
    w = _one(conn, f"SELECT count(*) FILTER (WHERE withheld), count(*) FILTER (WHERE anonymised), count(*) FROM {T('parties')}")
    figures.update({"cases_suppressed": s[0], "cases_with_an_anonymised_party": s[1], "parties": w[2],
                    "parties_withheld": w[0], "parties_anonymised": w[1]})
    orphan = _one(conn, f"SELECT count(*) FROM {T('parties')} p LEFT JOIN {T('party_names')} n USING (key) WHERE n.key IS NULL")[0]
    if orphan:
        problems.append(f"{orphan} party row(s) with no name held")
    bad = _one(conn, f"SELECT count(*) FROM {T('parties')} p JOIN {T('cases')} c ON c.key = p.case_key "
                     f"WHERE c.suppressed AND NOT p.crown AND NOT p.withheld")[0]
    if bad:
        problems.append(f"{bad} non-Crown party row(s) of a suppressed case not withheld")
    if views:
        leak = _one(conn, f"SELECT count(*) FROM {views}.court_case_parties WHERE name_withheld AND name IS NOT NULL")[0]
        if leak:
            problems.append(f"{leak} withheld name(s) shown on court_case_parties")
        leak = _one(conn, f"SELECT count(*) FROM {views}.court_cases WHERE suppressed AND title IS NOT NULL")[0]
        if leak:
            problems.append(f"{leak} suppressed case title(s) shown on court_cases")
        for v in ("court_cases", "court_case_parties", "court_case_citations", "court_case_statutes"):
            cols = {r[0] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = %s "
                                               "AND table_name = %s", (views, v))}
            if not cols:
                problems.append(f"no view {views}.{v}")
            if cols & {"address", "home_address", "residential_address", "street_address", "case_text", "appearance"}:
                problems.append(f"{views}.{v} carries a column it must not")
    figures["set_aside_reasons"] = dict(conn.execute(f"SELECT stage || ': ' || reason, count(*) FROM {T('read_set_aside')} "
                                                     "GROUP BY 1 ORDER BY 2 DESC LIMIT 20").fetchall())
    for t in ("citations", "statutes"):
        figures[t] = _one(conn, f"SELECT count(*) FROM {T(t)}")[0]
    return {"ok": not problems, "problems": problems, "figures": figures}


def outside(conn, schema: str = load.SCHEMA, probe=None) -> dict:
    """The newest finished full pass's distinct cases against the figure
    probed at its start; the figure now beside it."""
    if not capture.authorisation():
        return {"ok": False, "detail": "held: OpenLaw has not authorised copies (API terms 3.6(a)); no case is held"}
    if conn.execute("SELECT to_regclass(%s)", (f"{schema}.capture_passes",)).fetchone()[0] is None:
        return {"ok": False, "detail": "no capture tables"}
    r = _one(conn, f"SELECT pass_id, probed_total, started_at FROM {schema}.capture_passes WHERE mode = 'full' "
                   "AND finished_at IS NOT NULL ORDER BY finished_at DESC LIMIT 1")
    if r is None:
        return {"ok": False, "detail": "no finished full pass is held"}
    pass_id, stated, started = r
    held = _one(conn, f"SELECT count(DISTINCT i) FROM {schema}.capture_pages, unnest(ids) i WHERE pass_id = %s", (pass_id,))[0]
    now = probe() if probe else None
    return {"ok": held == stated, "pass_id": pass_id, "pass_started": started.isoformat(timespec="minutes"),
            "probed_at_start": stated, "held": held, "difference": held - (stated or 0), "probed_now": now}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m registers.openlaw.check")
    ap.add_argument("--schema", default=load.SCHEMA)
    ap.add_argument("--views", default="pub")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--probe-only", action="store_true")
    a = ap.parse_args(argv)
    if a.probe_only:
        return capture.main(["--probe"])
    from support import db
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '300s'")
        o = outside(conn, a.schema, probe=lambda: capture.Run(None, land_fn=None, anytime=True).probe())
        print("openlaw: outside: " + json.dumps(o, default=str))
        if conn.execute("SELECT to_regclass(%s)", (f"{a.schema}.read_pages",)).fetchone()[0] is None:
            print("openlaw: reading: no reading is held")
            return 1
        r = reading(conn, a.schema, a.views)
        print("openlaw: reading: " + json.dumps(r, default=str))
    return 0 if o["ok"] and r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
