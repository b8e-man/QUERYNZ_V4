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
  5. The step-6.2 templates, read back on a spread of each run's lines
     (template 3's six scans by `chain_readback`, from their own steps):
     every join on the line holds today (the link, the register keys, the
     names folding alike, the namesake count, the business number), the
     grade says how each was made, and every supplier the notices name is on
     the award list.
     The two proving scans prove the shape on the real tables: the society
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
    """The citations whose (view, key) is not a row of the view today, and
    those whose document, page and place are not that row's (a key can name
    several rows, each read from its own page: the citation must name the one
    the line read)."""
    bad = []
    by_view = {}
    for c in citations:
        by_view.setdefault(c["view"], []).append(c)
    for view, cs in by_view.items():
        v = cat.BY_NAME.get(view)
        if not v:
            bad += [f"{view}: not a view the catalogue knows"]
            continue
        cols = db.pub_columns(pub, view)
        where = [x for x in ("document", "page", "place") if x in cols]
        keys = sorted({c["key"] for c in cs})
        have = {}
        for i in range(0, len(keys), CHUNK):
            chunk = keys[i:i + CHUNK]
            for r in pub.execute(f"select {', '.join([v.key_col] + where)} from pub.{v.name} where {v.key_col} = any(%s)", (chunk,)):
                have.setdefault(r[0], set()).add(tuple(None if x is None else str(x) for x in r[1:]))
        for c in cs:
            if c["key"] not in have:
                bad.append(f"pub.{view} {c['key']}: no such row today")
            elif where and tuple(None if c.get(x) is None else str(c.get(x)) for x in where) not in have[c["key"]]:
                bad.append(f"pub.{view} {c['key']}: no row under this key was read from the cited document, page and place today")
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
                    if s.by in ("row", "name"):
                        need.add(s.on[1])
                    need |= set(s.number[1:])
                    i = t.steps.index(s)
                    if i + 1 < len(t.steps) and t.steps[i + 1].by in ("row", "name"):
                        need.add(t.steps[i + 1].on[0])
                        need |= set(t.steps[i + 1].number[:1])
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
            if s.get("absent"):
                continue
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
            if not s.get("absent") and f"[{s['cite']}]" not in html:
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


TEMPLATES_PROVED = ("tender-awards", "procurement-directors-donors", "procurement-shareholders-donors")
SAMPLE = 60          # lines read back per step-6.2 template, spread across the run
FOLD_READS = 5       # namesake counts read back (each folds the whole view)


def spread(lines: list, k: int = SAMPLE) -> list:
    step = max(1, len(lines) // k)
    return lines[::step][:k]


def _row(pub, view: str, key: str, cols: str) -> dict:
    got = db.rows(pub, f"select {cols} from pub.{view} where key = %s", (key,))
    return got[0] if got else {}


def _key(step: dict) -> str:
    return step["ref"].split(":", 1)[1]


def _by_name(pub, name: str, scan: str, n, ln: dict, here: dict, there: dict, here_col: str, there_col: str,
             here_view: str, there_view: str, folds: list) -> list:
    """A name step read back: by name, the two names fold alike; marked as
    one of N namesakes, N rows there carry the folded name today."""
    out_ = []
    a, b = _row(pub, here_view, _key(here), f"{here_col} as name"), _row(pub, there_view, _key(there), f"{there_col} as name")
    if not a or not b:
        return [f"{scan}: line {n}: {name}: a row is not in its view today"]
    if any(name + ": joined by name alone" in x for x in ln["reasons"]):
        if loose(a["name"]) != loose(b["name"]) or not loose(a["name"]):
            out_.append(f"{scan}: line {n}: {name}: joined by name, but the names do not fold alike today")
    m = next((x for x in ln["reasons"] if x.startswith(f"{name}: one of ")), None)
    if m and folds[0] < FOLD_READS:
        folds[0] += 1
        want = int(m.split()[3].replace(",", ""))
        got = db.rows(pub, f"select count(*) as n from pub.{there_view} x where {plan.fold_sql(f'x.{there_col}')} = {plan.fold_sql('%s')}",
                      (b["name"],))[0]["n"]
        if got != want:
            out_.append(f"{scan}: line {n}: {name}: marked one of {want} namesakes; pub.{there_view} has {got} under that name today")
    return out_


def templates_proving(pub, scan: str, lines: list) -> list:
    """The step-6.2 templates on the real tables, read back line by line
    (a spread of each run): every join on the line holds today and the
    grade says how it was made. `lines` is passed in so a test can plant a
    fault and see it caught."""
    out_, folds = [], [0]
    if scan == "tender-awards":   # every supplier the notices name is on the list, matched or not
        held = db.rows(pub, "select count(*) as n from pub.award_suppliers s join pub.award_notices a on a.key = s.notice_key")[0]["n"]
        listed = len({ln["steps"][1]["ref"] for ln in lines})
        if listed != held:
            out_.append(f"{scan}: {listed:,} suppliers listed; the notices name {held:,} today")
    for ln in spread(lines):
        n = ln["n"]
        if scan == "tender-awards":
            aw, su, co = ln["steps"]
            if _row(pub, "award_suppliers", _key(su), "notice_key").get("notice_key") != _key(aw):
                out_.append(f"{scan}: line {n}: the supplier is not named on the award today")
            if co.get("absent"):
                if ln["grade"] != "confirmed" or ln["reasons"]:
                    out_.append(f"{scan}: line {n}: no company joined, but graded {ln['grade']} with reasons")
                continue
            if ln["grade"] == "confirmed":
                a, b = _row(pub, "award_suppliers", _key(su), "nzbn"), _row(pub, "companies", _key(co), "nzbn")
                if not a.get("nzbn") or a.get("nzbn") != b.get("nzbn"):
                    out_.append(f"{scan}: line {n}: confirmed, but the supplier and the company do not share a business number")
            elif not any("company: joined by name alone" in x for x in ln["reasons"]):
                out_.append(f"{scan}: line {n}: near without the name join's reason")
            out_ += _by_name(pub, "company", scan, n, ln, su, co, "business_name", "name", "award_suppliers", "companies", folds)
        elif scan in ("procurement-directors-donors", "procurement-shareholders-donors"):
            donor, person, co, su, aw = ln["steps"]
            pview = person["view"]
            link = db.rows(pub, "select grade from pub.links where rule = any(%s) and ((row_a = %s and row_b = %s) or (row_a = %s and row_b = %s))",
                           (["full-name@1", "name-only@1"], donor["ref"], person["ref"], person["ref"], donor["ref"]))
            if not link:
                out_.append(f"{scan}: line {n}: no full-name or name-only link joins the donor and the {person['label']} today")
            elif link[0]["grade"] != "confirmed" and not any(x.startswith(person["label"] + ":") for x in ln["reasons"]):
                out_.append(f"{scan}: line {n}: a near link without its reason")
            if _row(pub, pview, _key(person), "entity_key").get("entity_key") != _key(co):
                out_.append(f"{scan}: line {n}: the {person['label']} row is not on the company today")
            if _row(pub, "award_suppliers", _key(su), "notice_key").get("notice_key") != _key(aw):
                out_.append(f"{scan}: line {n}: the supplier is not named on the award today")
            if any("supplier: joined by name alone" in x for x in ln["reasons"]):
                if ln["grade"] != "near":
                    out_.append(f"{scan}: line {n}: graded {ln['grade']}; a supplier joined by name is near")
            else:
                a, b = _row(pub, "companies", _key(co), "nzbn"), _row(pub, "award_suppliers", _key(su), "nzbn")
                if not b.get("nzbn") or a.get("nzbn") != b.get("nzbn"):
                    out_.append(f"{scan}: line {n}: the supplier is joined without the name join's reason and without a shared business number")
            out_ += _by_name(pub, "supplier", scan, n, ln, co, su, "name", "business_name", "companies", "award_suppliers", folds)
        if len(out_) > 10:
            break
    return out_


#: the step-6.2 template 3 scans (use case 14), read back step by step from their own template (`chain_readback`)
TEMPLATES_CHAINED = ("settlement-map-iwi", "settlement-map-settlements", "settlement-map-charities", "settlement-map-companies",
                     "settlement-map-societies", "settlement-map-shareholdings")


def _holds(row: dict, where: tuple) -> bool:
    for col, val in where:
        got = row.get(col)
        if isinstance(val, tuple):
            if got not in val:
                return False
        elif got != val and not (val is None and got is None):
            return False
    return True


def _where_sql(where: tuple) -> tuple:
    text, params = [], []
    for col, val in where:
        if val is None:
            text.append(f"{col} is null")
        elif isinstance(val, bool):
            text.append(f"{col} is {'true' if val else 'false'}")
        elif isinstance(val, tuple):
            text.append(f"{col} = any(%s)")
            params.append(list(val))
        else:
            text.append(f"{col} = %s")
            params.append(val)
    return "".join(f" and {x}" for x in text), params


def chain_readback(pub, t: tpl.Template, lines: list) -> list:
    """A scan of row and name steps read back from its own template on the
    real tables: every row the first step's filter selects is listed; on a
    spread of lines each row still meets its filter, each row step's columns
    are equal today, each name step joined by name folds alike (or, joined
    by number, the two numbers are equal), the namesake count holds, a step
    shown as 'none found in' has nothing there today, and the grade says how
    each join was made. `lines` is passed in so a test can plant a fault."""
    name, out_, folds = t.name, [], [0]
    first = t.steps[0]
    w, p = _where_sql(first.where)
    v0 = cat.BY_NAME[first.view]
    held = db.rows(pub, f"select count(*) as n from pub.{v0.name} where true{w}", p)[0]["n"]
    listed = len({ln["steps"][0]["ref"] for ln in lines})
    if listed != held:
        out_.append(f"{name}: {listed:,} {first.label} rows listed; pub.{v0.name} holds {held:,} under the scan's filter today")
    for ln in spread(lines):
        n, near = ln["n"], False
        rows = []
        for i, (s, st) in enumerate(zip(t.steps, ln["steps"])):
            v = cat.BY_NAME[st["view"]]
            if st.get("absent"):
                rows.append(None)
                prev = rows[i - 1] if i else None
                if prev is None:
                    continue
                if s.by == "row":
                    w, p = _where_sql(s.where)
                    got = db.rows(pub, f"select count(*) as n from pub.{v.name} where {s.on[1]} = %s{w}", [prev.get(s.on[0])] + p)[0]["n"]
                    if got:
                        out_.append(f"{name}: line {n}: {s.label} shown as none found, but pub.{v.name} has {got} such rows today")
                elif s.by == "name" and folds[0] < FOLD_READS:
                    folds[0] += 1
                    w, p = _where_sql(s.where)
                    got = db.rows(pub, f"select count(*) as n from pub.{v.name} x where {plan.fold_sql(f'x.{s.on[1]}')} = {plan.fold_sql('%s')}{w}",
                                  [prev.get(s.on[0])] + p)[0]["n"]
                    if got and loose(prev.get(s.on[0]) or ""):
                        out_.append(f"{name}: line {n}: {s.label} shown as none found, but {got} rows of pub.{v.name} carry the name today")
                continue
            want = sorted(set(cat.columns_read(v)) - plan.OPTIONAL | set(s.columns) | {c for c, _ in s.where} | set(s.on[1:]) | set(s.number[1:])
                          | ({t.steps[i + 1].on[0]} | set(t.steps[i + 1].number[:1]) if i + 1 < len(t.steps) else set()))
            prev = rows[i - 1] if i else None
            if s.by == "row" and prev is not None:   # a key may name several rows (a settlement's): the one this join reaches
                got = db.rows(pub, f"select {', '.join(want)} from pub.{v.name} where {v.key_col} = %s and {s.on[1]}::text = %s::text",
                              (_key(st), str(prev.get(s.on[0]))))
                row = got[0] if got else {}
                if not row:
                    out_.append(f"{name}: line {n}: {s.label}: no row {st['ref']} of pub.{v.name} has {s.on[1]} equal to the {t.steps[i - 1].label}'s {s.on[0]} today")
                    rows.append(None)
                    continue
            else:
                row = _row(pub, v.name, _key(st), ", ".join(want))
            rows.append(row)
            if not row:
                out_.append(f"{name}: line {n}: {s.label} {st['ref']} is not in pub.{v.name} today")
                continue
            if not _holds(row, s.where):
                out_.append(f"{name}: line {n}: {s.label} no longer meets the scan's filter today")
            if not i or prev is None:
                continue
            if s.by == "name":
                by_name = any(x.startswith(f"{s.label}: joined by name alone") for x in ln["reasons"])
                if by_name:
                    near = True
                    if loose(prev.get(s.on[0]) or "") != loose(row.get(s.on[1]) or "") or not loose(prev.get(s.on[0]) or ""):
                        out_.append(f"{name}: line {n}: {s.label}: joined by name, but the names do not fold alike today")
                elif not s.number or not prev.get(s.number[0]) or str(prev.get(s.number[0])) != str(row.get(s.number[1])):
                    out_.append(f"{name}: line {n}: {s.label}: joined without the name join's reason and without a shared number")
                m = next((x for x in ln["reasons"] if x.startswith(f"{s.label}: one of ")), None)
                if m:
                    near = True
                    if folds[0] < FOLD_READS:
                        folds[0] += 1
                        want_n = int(m.split()[3].replace(",", ""))
                        got = db.rows(pub, f"select count(*) as n from pub.{v.name} x where {plan.fold_sql(f'x.{s.on[1]}')} = {plan.fold_sql('%s')}",
                                      (row.get(s.on[1]),))[0]["n"]
                        if got != want_n:
                            out_.append(f"{name}: line {n}: {s.label}: marked one of {want_n} namesakes; pub.{v.name} has {got} under that name today")
                elif s.namesakes and by_name and folds[0] < FOLD_READS:
                    folds[0] += 1
                    got = db.rows(pub, f"select count(*) as n from pub.{v.name} x where {plan.fold_sql(f'x.{s.on[1]}')} = {plan.fold_sql('%s')}",
                                  (row.get(s.on[1]),))[0]["n"]
                    if got != 1:
                        out_.append(f"{name}: line {n}: {s.label}: not marked as a namesake; pub.{v.name} has {got} under that name today")
        if ln["grade"] != ("near" if near else "confirmed"):
            out_.append(f"{name}: line {n}: graded {ln['grade']}; its joins make it {'near' if near else 'confirmed'}")
        if len(out_) > 10:
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
        for name in names:
            r = state.latest(st, name) if name in TEMPLATES_PROVED + TEMPLATES_CHAINED else None
            if r and name in TEMPLATES_PROVED:
                problems += templates_proving(pub, name, list(state.all_lines(st, r["run_id"])))
            elif r:
                problems += chain_readback(pub, tpl.by_name(name), list(state.all_lines(st, r["run_id"])))
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
