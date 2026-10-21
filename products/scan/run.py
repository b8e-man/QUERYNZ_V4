"""The runner: one scan, one query per start view, streamed through a
server-side cursor in pages so a scan over the whole companies register
holds no more than a page in memory; each page turned into lines, graded,
flagged for hubs, written to the scan's own schema; the citations numbered
across the whole run and written at the end; the freshness of every view
read recorded at the start (max loaded_at; the links' built_at), so the
stale rule can say when a view has loaded since; the time measured and
recorded. The presentation rules run over the lines as they pass; a run
with problems is kept, marked, and refused by the surface.

The stale rule: a scan is stale when any view its latest run read has a
later loaded_at now than the run recorded. `python -m products.scan run
--stale` re-runs those and nothing else."""
from __future__ import annotations

import time

from products.scan import db, hubs, lines as L, plan, rules, settings as cfg, state, template as tpl, views as cat

PAGE = 2000
FRESH_SQL = {"links": "select max(built_at) as at from pub.links", "groups": "select max(built_at) as at from pub.groups",
             "names": "select max(built_at) as at from pub.groups"}   # pub.names is rebuilt with the groups and carries no time of its own


def freshness(conn, views: list) -> list:
    """[{view, loaded_at}] for every view read, as ISO text or None."""
    out = []
    for v in views:
        sql = FRESH_SQL.get(v) or f"select max(loaded_at) as at from pub.{v}"
        at = db.rows(conn, sql)[0]["at"]
        out.append({"view": v, "loaded_at": at.isoformat(timespec="seconds") if at else None})
    return out


def blank_for(t: tpl.Template) -> str:
    regs = sorted({cat.REGISTER_NAME.get(cat.BY_NAME[v].register, v) for v in plan.views_read(t) if v in cat.BY_NAME})
    return "none found in " + ", ".join(regs)


def run(t: tpl.Template, limit: int = None, note: str = "", settings: dict = None, log=print) -> dict:
    """Runs the scan; returns the run record as a dict (run_id, lines,
    seconds, grades, hubs, problems, starts, views). A run that fails is
    closed with the failure named in its problems, so the page refuses it
    and the check fails on it; the exception is raised on."""
    settings = settings or cfg.in_force()
    views = plan.views_read(t)
    with db.pub_connect() as pub, db.state_connect() as st:
        pub.autocommit = True
        fresh = freshness(pub, views)
        have = {v: db.pub_columns(pub, v) for v in views if v in cat.BY_NAME}
        sql_text = "\n\n".join(plan.sql(t, settings, s, None, have)[0] for s in t.starts())
        run_id = state.open_run(st, t, settings, fresh, sql_text, note, limit)
        log(f"scan {t.name} {t.version}: run {run_id} started; reads {', '.join(views)}")
        busy = hubs.busy_addresses(pub) if any(s.view == "companies" for s in t.steps) or "companies" in t.starts() else set()
        c = {"n": 0, "hubs": 0, "starts": [], "grades": {g: 0 for g in L.GRADES}, "problems": rules.template_problems(t), "numbering": L.Numbering()}
        pub.autocommit = False
        t0 = time.monotonic()
        try:
            _scan(t, settings, limit, have, pub, st, run_id, busy, c, log)
        except Exception as exc:
            c["problems"].append(f"the run failed: {type(exc).__name__}: {str(exc)[:300]}")
            state.close_run(st, run_id, time.monotonic() - t0, c["n"], c["starts"], c["grades"], c["hubs"], c["problems"])
            raise
        seconds = time.monotonic() - t0
        state.write_citations(st, run_id, c["numbering"].citations)
        if c["n"] == 0:
            c["problems"] += rules.run_problems(t, [], blank_for(t))
        state.close_run(st, run_id, seconds, c["n"], c["starts"], c["grades"], c["hubs"], c["problems"])
    out = {"run_id": run_id, "scan": t.name, "lines": c["n"], "seconds": round(seconds, 3), "grades": c["grades"], "hubs": c["hubs"],
           "citations": len(c["numbering"].citations), "problems": c["problems"], "starts": c["starts"], "views": fresh, "limited": limit}
    log(f"scan {t.name}: run {run_id} finished: {c['n']:,} lines in {seconds:.1f} s; {c['grades']}; {c['hubs']} with a hub; "
        f"{len(c['numbering'].citations):,} citations; {len(c['problems'])} problems")
    return out


def _scan(t, settings, limit, have, pub, st, run_id, busy, c: dict, log) -> None:
    """One query per start view, streamed in pages; the counts in `c`."""
    for start in t.starts():
        text, params = plan.sql(t, settings, start, None, have)   # a limit is applied by stopping the fetch: a SQL limit changes the plan and runs slower
        t1, n_start = time.monotonic(), 0
        with pub.cursor(name=f"scan_{run_id}_{start}") as cur:
            cur.itersize = PAGE
            cur.execute(text, params)
            names = [d[0] for d in cur.description]
            while True:
                page = cur.fetchmany(min(PAGE, limit - n_start) if limit else PAGE)
                if not page:
                    break
                batch = [L.line_of(t, settings, start, dict(zip(names, r)), c["numbering"]) for r in page]
                c["hubs"] += hubs.flag(pub, batch, busy)
                for i, ln in enumerate(batch):
                    ln["n"] = c["n"] + i + 1
                    c["grades"][ln["grade"]] += 1
                    if len(c["problems"]) < 200:
                        c["problems"] += rules.line_problems(ln)
                state.write_lines(st, run_id, c["n"] + 1, batch)
                c["n"] += len(batch)
                n_start += len(batch)
                log(f"  {c['n']:,} lines…")
                if limit and n_start >= limit:
                    break
        pub.commit()
        c["starts"].append({"view": start, "lines": n_start, "seconds": round(time.monotonic() - t1, 3)})


def stale(pub, st) -> list:
    """[{scan, run_id, stale: [views], never_run: bool}] for every scan on disk."""
    out = []
    for name, folder in tpl.folders().items():
        t = tpl.load(folder)
        last = state.latest(st, name)
        if not last:
            out.append({"scan": name, "run_id": None, "stale": plan.views_read(t), "never_run": True})
            continue
        then = {x["view"]: x["loaded_at"] for x in (last.get("views") or [])}
        now = {x["view"]: x["loaded_at"] for x in freshness(pub, plan.views_read(t))}
        moved = sorted(v for v in now if (now[v] or "") != (then.get(v) or ""))
        out.append({"scan": name, "run_id": last["run_id"], "stale": moved, "never_run": False, "finished_at": last.get("finished_at")})
    return out
