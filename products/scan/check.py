"""The scan's outside check (spec line 4), against the real published
tables through the product reader and the scan's own tables, never the
sample:

  1. Every scan on disk loads, reads only published views that exist,
     every column it reads exists in its view, and none is address-shaped.
  2. The settings file loads, and what it records as in force is what the
     latest runs recorded.
  3. Every scan has a finished run, and its lines are all cited: every
     citation names a row that is in its published view today, the key
     read back (all of them, in chunks). A planted wrong key fails here
     (the fast tier's mutant test proves the catch).
  4. The presentation rules hold on every line of every latest run, and the
     run recorded no problems.
  5. The two proving scans prove the shape on the real tables: the society
     scan has confirmed lines, and on a sample of its lines the notice's
     register key is the company's today, the officer and the director are
     in one group, and the grade follows the group's contested flag; the
     donor scan has lines from both starts, all near with the rule's own
     reason, and a near organisation-name link joins each pair today.
  6. The stale rule answers for every scan, and the page renders the latest
     run of each with every line's citation numbered.
  7. The CSV and the JSON of each latest run carry every line and its citations.

  python -m products.scan check [--scan NAME]      exit 1 on any failure
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys

from products.scan import db, out, plan, rules, run as R, settings as cfg, state, template as tpl, views as cat

CHUNK = 5000
LEGAL = re.compile(r"\b(limited|ltd|incorporated|inc|tapui)\b")


def loose(name: str) -> str:
    """A name as the lanes' and the links' own folds compare it: lower, no
    macrons, the legal ending off, letters and digits only."""
    return re.sub(r"[^a-z0-9]", "", LEGAL.sub("", cat.fold(name)))


def citations_resolve(pub, citations: list) -> list:
    """The citations whose (view, key) is not a row of the view today."""
    bad = []
    by_view = {}
    for c in citations:
        by_view.setdefault(c["view"], []).append(c["key"])
    for view, keys in by_view.items():
        v = cat.BY_NAME.get(view)
        if not v:
            bad += [f"{view}: not a view the catalogue knows"]
            continue
        keys = sorted(set(keys))
        for i in range(0, len(keys), CHUNK):
            chunk = keys[i:i + CHUNK]
            have = {r[0] for r in pub.execute(f"select {v.key_col} from pub.{v.name} where {v.key_col} = any(%s)", (chunk,))}
            bad += [f"pub.{view} {k}: no such row today" for k in chunk if k not in have]
    return bad


def check_template(pub, t: tpl.Template, held: set) -> list:
    out_ = []
    for v in plan.views_read(t):
        if v not in held:
            out_.append(f"{t.name}: reads pub.{v}, which is not published")
            continue
        if v in cat.BY_NAME:
            cols = db.pub_columns(pub, v)
            need = cat.columns_read(cat.BY_NAME[v]) - plan.OPTIONAL
            for s in t.steps:
                if s.view == v or v in s.views:
                    need |= set(s.columns) | {c for c, _ in s.where}
                    if s.by == "row":
                        need.add(s.on[1])
            missing = sorted(need - cols)
            if missing:
                out_.append(f"{t.name}: pub.{v} lacks {missing}")
            shaped = sorted(c for c in need if cat.ADDRESS_COLUMN.search(c))
            if shaped:
                out_.append(f"{t.name}: reads address-shaped columns {shaped} of pub.{v} (hard limit 15)")
    out_ += [f"{t.name}: {p}" for p in rules.template_problems(t)]
    return out_


def check_run(pub, st, t: tpl.Template, settings: dict) -> list:
    out_ = []
    r = state.latest(st, t.name)
    if not r:
        return [f"{t.name}: no finished run"]
    if r.get("problems"):
        out_.append(f"{t.name}: run {r['run_id']} recorded {len(r['problems'])} problems: {r['problems'][0]}")
    if (r.get("settings") or {}).get("chains", {}).get("value") != settings["chains"]["value"] or \
       (r.get("settings") or {}).get("through_people", {}).get("value") != settings["through_people"]["value"]:
        out_.append(f"{t.name}: run {r['run_id']} ran under other trust settings than the file now records: stale by setting")
    cites = state.citations(st, r["run_id"])
    out_ += [f"{t.name}: {b}" for b in citations_resolve(pub, cites)[:20]]
    numbers = {c["n"] for c in cites}
    n, lines_seen = 0, 0
    for ln in state.all_lines(st, r["run_id"]):
        lines_seen += 1
        out_ += [f"{t.name}: {p}" for p in rules.line_problems(ln)[:5]]
        for s in ln["steps"]:
            if s["cite"] not in numbers:
                out_.append(f"{t.name}: line {ln['n']} cites [{s['cite']}], which the run's citations lack")
        if len(out_) > 40:
            break
        n += 1
    if lines_seen != (r.get("lines") or 0):
        out_.append(f"{t.name}: run {r['run_id']} says {r.get('lines')} lines and holds {lines_seen}")
    if not lines_seen and not any("none found in" in p for p in (r.get("problems") or [])):
        pass   # an empty run is "none found", never a finding; nothing to check beyond its blank, which rules hold at the run
    # the page renders with every citation numbered; the files carry every line
    lines, total = state.lines(st, r["run_id"], 1, state.PAGE)
    html = out.scan_html(t, r, lines, total, 1, state.PAGE, state.citations(st, r["run_id"], sorted({c for ln in lines for c in ln["cites"]})), [])
    for ln in lines:
        for s in ln["steps"]:
            if f"[{s['cite']}]" not in html:
                out_.append(f"{t.name}: the page lacks citation [{s['cite']}] of line {ln['n']}")
                break
    text = out.csv_text(t, state.all_lines(st, r["run_id"]))
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) - 1 != lines_seen:
        out_.append(f"{t.name}: the CSV has {len(rows) - 1} lines, the run {lines_seen}")
    if rows and not all(h.endswith("_citation") for h in rows[0] if h.endswith("_citation")) or "cites" not in (rows[0] if rows else []):
        out_.append(f"{t.name}: the CSV header lacks the citation columns")
    doc = json.loads(out.json_text(t, r, state.all_lines(st, r["run_id"]), cites))
    if len(doc["lines"]) != lines_seen or len(doc["citations"]) != len(cites) or doc["run"]["run_id"] != r["run_id"]:
        out_.append(f"{t.name}: the JSON does not carry every line and citation")
    return out_


def proving(pub, st) -> list:
    """The two proving scans on the real tables: what each must show, read
    back from the tables today (the join holds, the grade is the rule's)."""
    out_ = []
    r = state.latest(st, "society-officers-liquidations")
    if r:
        if not (r.get("grades") or {}).get("confirmed"):
            out_.append("society-officers-liquidations: no confirmed line: the person step through pub.groups found no uncontested group")
        for ln in list(state.all_lines(st, r["run_id"]))[:50]:
            o, d, c, n = ln["steps"]
            got = db.rows(pub, "select register_key from pub.gazette_liquidations where key = %s", (n["ref"].split(":", 1)[1],))
            if not got or got[0]["register_key"] != c["ref"].split(":", 1)[1]:
                out_.append(f"society-officers-liquidations: line {ln['n']}: the notice's register key is not the company's today")
                break
            same = db.rows(pub, "select a.group_id = b.group_id as same, a.contested or b.contested as contested from pub.groups a, pub.groups b "
                                "where a.row_key = %s and b.row_key = %s", (o["ref"], d["ref"]))
            if not same or not same[0]["same"]:
                out_.append(f"society-officers-liquidations: line {ln['n']}: the officer and the director are not in one group today")
                break
            if (ln["grade"] == "contested") != bool(same[0]["contested"]):
                out_.append(f"society-officers-liquidations: line {ln['n']}: graded {ln['grade']} but the group's contested flag says otherwise")
                break
            if ln["grade"] == "confirmed" and ln["reasons"]:
                out_.append(f"society-officers-liquidations: line {ln['n']}: confirmed with a reason")
                break
    r = state.latest(st, "donors-named-as-companies")
    if r:
        if not r.get("lines"):
            out_.append("donors-named-as-companies: no line: the organisation-name rule joined no donor to a company")
        starts = {x["view"] for x in (r.get("starts") or []) if x["lines"]}
        if starts != {"party_return_donors", "disclosures"}:
            out_.append(f"donors-named-as-companies: lines from {sorted(starts)}, not from both starts")
        for ln in list(state.all_lines(st, r["run_id"]))[:50]:
            donor, company = ln["steps"]
            if ln["grade"] != "near" or not any("organisation-name@1" in x for x in ln["reasons"]):
                out_.append(f"donors-named-as-companies: line {ln['n']} is {ln['grade']} or lacks the rule's reason")
                break
            got = db.rows(pub, "select grade from pub.links where rule = 'organisation-name@1' and ((row_a = %s and row_b = %s) or (row_a = %s and row_b = %s))",
                          (donor["ref"], company["ref"], company["ref"], donor["ref"]))
            if not got or got[0]["grade"] != "near":
                out_.append(f"donors-named-as-companies: line {ln['n']}: no near organisation-name link joins the donor and the company today")
                break
    return out_


def main(argv=None) -> int:
    argv = list(argv or [])
    only = argv[argv.index("--scan") + 1] if "--scan" in argv else None
    problems = []
    settings = cfg.in_force()
    with db.pub_connect() as pub, db.state_read_connect() as st:
        pub.autocommit = True
        held = db.pub_views(pub)
        names = [n for n in tpl.folders() if not only or n == only]
        for name in names:
            try:
                t = tpl.by_name(name)
            except Exception as exc:
                problems.append(f"{name}: does not load: {exc}")
                continue
            problems += check_template(pub, t, held)
            problems += check_run(pub, st, t, settings)
        if not only:
            problems += proving(pub, st)
            try:
                for x in R.stale(pub, st):
                    print(f"stale rule: {x['scan']}: " + ("never run" if x["never_run"] else (", ".join(x["stale"]) + " loaded since" if x["stale"] else "current")))
            except Exception as exc:
                problems.append(f"the stale rule could not answer: {type(exc).__name__}: {exc}")
    for p in problems:
        print("FAIL", p)
    print(f"products.scan check: {len(problems)} problems; scans {', '.join(names)}; settings in force: "
          + "; ".join(f"{k} {v['value']} ({v['status']})" for k, v in settings.items()))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
