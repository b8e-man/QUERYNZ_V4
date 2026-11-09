"""The diagnostic subject report's own checks (Arthur, 9 November 2026; plan:
docs/research/diagnostic-report-plan-2026-11-09.md). Internal: it finds problems, it is no product's report.

For a built report (the `diagnostic` template, products/report/templates/diagnostic/):

    where_else(conn, report)   every register and table in the name index where the subject's name is filed, against
                               what the walk reached: [{register, view, rows, reached}]; counts, never rows
    checks(report, seconds)    the automatic problem lines: [(kind, text)]
    choose(conn)               the test set, chosen from the published tables at run time: [(case, ref)]

    python -m products.report.diagnose run OUT_DIR     build the test set's reports, write each memo and a summary
                                                       (OUT_DIR outside the repository: a memo carries names)

Reads `pub.*` only, on the product reader. A summary line carries a case, a ref, counts and kinds, never a name."""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter

from products.report import db

LIMIT_S = 60          # a report that takes longer is a problem of its own (plan: slow or cut short)
NAME_ONLY_RULES = ("name-only", "same-name")

KINDS = ("wrong link", "missing link", "register not reached", "register not catalogued", "wrong date", "missing date",
         "slow or cut short", "duplicate", "stale not held", "other")


def _items(report: dict) -> list:
    return [it for s in report.get("sections") or [] for it in s.get("items") or []]


def where_else(conn, report: dict) -> list:
    """Where the subject's name is filed (its full name key, else its first-and-last key) in every register of the
    name index, and how many of those rows the walk reached."""
    subj = report.get("subject") or {}
    ref = subj.get("ref") or report.get("ref")
    me = db.rows(conn, "select full_key, fl_key from pub.names where ref = %s limit 1", (ref,))
    if not me:
        return []
    col, key = ("full_key", me[0]["full_key"]) if me[0]["full_key"] else ("fl_key", me[0]["fl_key"])
    if not key:
        return []
    reached = {it["ref"] for it in _items(report)} | {ref}
    got = db.rows(conn, f"select register, view, ref from pub.names where {col} = %s limit 5000", (key,))
    out = {}
    for r in got:
        e = out.setdefault((r["register"], r["view"]), {"register": r["register"], "view": r["view"], "rows": 0, "reached": 0})
        e["rows"] += 1
        e["reached"] += r["ref"] in reached
    return sorted(out.values(), key=lambda e: (e["reached"] > 0, e["register"], e["view"]))


def checks(report: dict, seconds: float, elsewhere: list = ()) -> list:
    """[(kind, text)]: what the report shows that is wrong or missing, found without reading a name."""
    out = []
    items = _items(report)
    if not report.get("found"):
        return [("other", f"the start row was not found: {report.get('why')}")]
    if seconds > LIMIT_S:
        out.append(("slow or cut short", f"built in {seconds:.0f} s (limit {LIMIT_S} s)"))
    w = report.get("walk") or {}
    for k in ("links_omitted", "entities_omitted", "entities_not_expanded", "group_omitted", "officers_omitted"):
        if w.get(k):
            out.append(("slow or cut short", f"{k.replace('_', ' ')}: {w[k]}"))
    twice = Counter(it["ref"] for it in items)
    dup = [r for r, n in twice.items() if n > 1]
    if dup:
        out.append(("duplicate", f"{len(dup)} row(s) listed more than once, e.g. {dup[0]}"))
    for it in items:
        rule = str(it.get("rule") or "")
        if it.get("grade") == "confirmed" and rule.split("@")[0] in NAME_ONLY_RULES:
            out.append(("wrong link", f"a row confirmed by a name-only rule ({rule}): {it['ref']}"))
    undated = [it for it in items if (it.get("dates") or {}).get("undated")]
    if undated:
        by = Counter(it["view"] for it in undated)
        out.append(("missing date", f"{len(undated)} undated item(s): " + ", ".join(f"{v} {n}" for v, n in by.most_common(5))))
    for p in report.get("problems") or []:
        out.append(("other", str(p)))
    for x in report.get("superseded_not_held") or []:
        out.append(("stale not held", str(x)))
    for e in elsewhere:
        if e["rows"] and not e["reached"]:
            out.append(("register not reached", f"the name is filed {e['rows']} time(s) in pub.{e['view']} ({e['register']}); no link reached it"))
    from products.report import catalogue as cat
    for e in elsewhere:
        if e["view"] not in cat.BY_NAME and e["view"] not in cat.LINKS_VIEWS:
            out.append(("register not catalogued", f"the name index files the name in pub.{e['view']}, which the catalogue does not read"))
    return out


#: the test set (plan step 5): (case, SQL giving one ref), each chosen at run time so the set never goes stale
CASES = (
    ("a sitting MP", "select n.ref from pub.names n where n.view = 'members' and n.politician and n.full_key in "
                     "(select full_key from pub.names where register = 'hansard') order by n.ref limit 1"),
    ("a large donor to a party", "select 'party_returns:' || d.key from pub.party_return_donors d order by d.amount desc nulls last limit 1"),
    ("a director of liquidated companies", "select n.ref from pub.names n join pub.gazette_liquidations g on n.entity_ref = 'companies:' || g.register_key "
                                           "where n.view = 'directors' order by n.ref limit 1"),
    ("a professional director", "select ref from pub.names where view = 'directors' and full_key in (select full_key from pub.names "
                                "where view = 'directors' and full_key is not null group by 1 having count(*) between 50 and 80 limit 1) limit 1"),
    ("a very common name", "select ref from pub.names where view = 'directors' and full_key = (select full_key from pub.names where view = 'directors' "
                           "and full_key is not null group by 1 order by count(*) desc limit 1) limit 1"),
    ("a company with a holding chain", "select 'companies:' || s.entity_key from pub.shareholders s join pub.companies c on c.name = s.name "
                                       "where s.name ~* '(limited|ltd)$' order by s.entity_key limit 1"),
    ("a company named in a court judgment", "select row_a from pub.links where row_a like 'companies:%%' and row_b like 'courts:%%' and grade = 'confirmed' limit 1"),
    ("a supplier on a GETS award", "select n.ref from pub.names n where n.view = 'award_suppliers' order by n.ref limit 1"),
    ("a charity with officers", "select 'charities:' || o.charity_key from pub.charity_officers o order by o.charity_key limit 1"),
    ("an incorporated society", "select 'societies:' || o.society_key from pub.society_officers o order by o.society_key limit 1"),
    ("a councillor", "select ref from pub.names where view = 'councillor_interests' order by ref limit 1"),
    ("a council meeting attendee", "select ref from pub.names where view = 'council_meeting_attendance' order by ref limit 1"),
    ("a person in the Insolvency Register", "select ref from pub.names where view = 'insolvency_people' order by ref limit 1"),
    ("a licensed building practitioner confirmed to a company", "select row_a from pub.links where row_a like 'building_practitioners:%%/lbp/%%' "
                                                                "and row_b like 'companies:%%' and grade = 'confirmed' order by row_a limit 1"),
    ("a person named in a Building Practitioners Board decision", "select ref from pub.names where view = 'building_practitioner_decisions' order by ref limit 1"),
    ("a body on a sanctions list", "select ref from pub.names where view = 'sanctions_listings' and kind = 'organisation' order by ref limit 1"),
    ("a grant recipient", "select ref from pub.names where view = 'grant_recipients' order by ref limit 1"),
    ("an iwi entity", "select ref from pub.names where view = 'iwi_directory_entities' and ref like '%%/iwi/%%' order by ref limit 1"),
    ("a person on a ministerial diary", "select ref from pub.names where view = 'minister_diary_attendees' and kind = 'person' order by ref limit 1"),
    ("a party board member", "select ref from pub.names where view = 'party_board_roles' order by ref limit 1"),
    ("a Māori name with a macron", "select ref from pub.names where view = 'linz_title_owners' and kind = 'person' and name_filed ~ '[āēīōūĀĒĪŌŪ]' "
                                   "order by ref limit 1"),   # no director's name carries a macron (9 November 2026)
    ("a land title owner who is a company director", "select o.ref from pub.names o where o.view = 'linz_title_owners' and o.full_key in "
                                                    "(select full_key from pub.names where view = 'directors' and full_key is not null limit 2000) limit 1"),
)


def choose(conn) -> list:
    out = []
    for case, sql in CASES:
        try:
            got = conn.execute(sql).fetchone()
        except Exception as exc:   # a case whose query fails is a finding of its own
            conn.rollback()
            out.append((case, None, f"the case's query failed: {exc}".splitlines()[0]))
            continue
        out.append((case, got[0] if got else None, "" if got else "no row matches the case"))
    return out


def run(out_dir: str, log=print) -> list:
    from products.report import build as B, memo, template as T
    t = T.by_name("diagnostic")
    os.makedirs(out_dir, exist_ok=True)
    summary = []
    with db.read_connect() as conn:
        conn.execute("SET statement_timeout = '120s'")
        for i, (case, ref, why) in enumerate(choose(conn), 1):
            line = {"n": i, "case": case, "ref": ref, "problems": []}
            if not ref:
                line["problems"] = [("other", why)]
                summary.append(line)
                log(f"{i:2} {case}: {why}")
                continue
            t0 = time.time()
            try:
                report = B.build(conn, ref, t)
            except Exception as exc:
                conn.rollback()
                line["problems"] = [("other", f"the report failed to build: {type(exc).__name__}: {exc}".splitlines()[0])]
                summary.append(line)
                log(f"{i:2} {case}: FAILED {type(exc).__name__}")
                continue
            secs = time.time() - t0
            elsewhere = where_else(conn, report)
            items = _items(report)
            line.update(seconds=round(secs, 1), items=len(items), grades=dict(Counter(it.get("grade") for it in items)),
                        sections={s["name"]: len(s.get("items") or []) for s in report["sections"] if s.get("items")},
                        rules=dict(Counter(str(it.get("rule") or "").split("@")[0] for it in items)),
                        elsewhere=elsewhere, problems=checks(report, secs, elsewhere))
            with open(os.path.join(out_dir, f"{i:02d}.txt"), "w", encoding="utf-8") as f:
                f.write(memo.text(report))
            summary.append(line)
            log(f"{i:2} {case}: {len(items)} items in {secs:.1f} s, {len(line['problems'])} problem line(s)")
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=str, ensure_ascii=False)
    return summary


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if len(argv) != 2 or argv[0] != "run":
        print(__doc__)
        return 2
    run(argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
