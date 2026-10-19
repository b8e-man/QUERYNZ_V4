"""The six first measurements of plan 4.2, run on the real tables and
recorded in `links.measurements`. None had ever been run.

    python -m links.measure [--schema scratch_links] [--markdown]

1. How often a full name repeats, by how common the name is.
2. Addresses shared by many companies.
3. The error rate of the two confirming rules on the test pairs (links.pairs),
   by name band; and, beside it, the review agent's reading of 100 confirmed
   links (links.readings), reported as an agent's judgment.
4. How often each rule can fire at all, per register.
5. Company names to official numbers: the share of organisation donors that
   match exactly one company alive on the donation date.
6. The shape of the groups: sizes, and any group that contradicts itself.
"""
from __future__ import annotations

import json
import sys
import time

import links
from links import rules

BAND_SQL = "CASE WHEN n <= 5 THEN 'rare' WHEN n <= 50 THEN 'middling' ELSE 'common' END"


def m1_name_repeats(conn, s: str) -> dict:
    out = {"definition": "band by director rows carrying the first-and-last name: rare 1-5, middling 6-50, common over 50"}
    rows = conn.execute(f"""
        WITH n AS (SELECT fl_key, count(*) AS n, count(*) FILTER (WHERE has_middle) AS with_middle FROM {s}.rows
                   WHERE view = 'directors' AND fl_key IS NOT NULL GROUP BY 1)
        SELECT {BAND_SQL} AS band, count(*) AS names, sum(n) AS rows_, sum(with_middle) AS rows_with_middle,
               count(*) FILTER (WHERE n = 1) AS names_on_one_row
        FROM n GROUP BY 1 ORDER BY min(n)""").fetchall()
    out["first_and_last_name"] = [{"band": b, "names": int(a), "rows": int(r), "rows_with_middle": int(m), "names_on_one_row": int(o)}
                                  for b, a, r, m, o in rows]
    rows = conn.execute(f"""
        WITH f AS (SELECT full_key, count(*) AS n FROM {s}.rows WHERE view = 'directors' AND has_middle GROUP BY 1)
        SELECT count(*) AS names, sum(n) AS rows_, count(*) FILTER (WHERE n > 1) AS names_repeating, sum(n) FILTER (WHERE n > 1) AS rows_repeating,
               max(n) AS most
        FROM f""").fetchone()
    out["full_name_with_middle"] = {"names": int(rows[0]), "rows": int(rows[1]), "names_repeating": int(rows[2]),
                                    "rows_in_a_repeating_name": int(rows[3] or 0), "most_rows_one_name": int(rows[4])}
    rows = conn.execute(f"""
        WITH f AS (SELECT full_key, count(*) AS n FROM {s}.rows WHERE view = 'directors' AND NOT has_middle AND full_key IS NOT NULL GROUP BY 1)
        SELECT count(*), sum(n), count(*) FILTER (WHERE n > 1), sum(n) FILTER (WHERE n > 1), max(n) FROM f""").fetchone()
    out["full_name_without_middle"] = {"names": int(rows[0]), "rows": int(rows[1]), "names_repeating": int(rows[2]),
                                       "rows_in_a_repeating_name": int(rows[3] or 0), "most_rows_one_name": int(rows[4])}
    out["other_registers"] = [{"view": v, "rows": int(n), "rows_whose_first_and_last_is_on_the_director_register": int(d)}
                              for v, n, d in conn.execute(f"""
        SELECT r.view, count(*), count(*) FILTER (WHERE EXISTS (SELECT 1 FROM {s}.name_counts c WHERE c.fl_key = r.fl_key))
        FROM {s}.rows r WHERE r.kind = 'person' AND r.view <> 'directors' GROUP BY 1 ORDER BY 2 DESC""").fetchall()]
    return out


def m2_shared_addresses(conn, s: str) -> dict:
    rows = conn.execute(f"""
        SELECT CASE WHEN n = 1 THEN '1' WHEN n <= 5 THEN '2-5' WHEN n <= 50 THEN '6-50' WHEN n <= 200 THEN '51-200' ELSE 'over 200' END,
               count(*), sum(n) FROM {s}.address_counts GROUP BY 1 ORDER BY min(n)""").fetchall()
    out = {"companies_per_registered_office": [{"companies_at_the_address": b, "addresses": int(a), "companies": int(c)} for b, a, c in rows]}
    out["busy_floor"] = rules.HUB_FLOOR
    row = conn.execute(f"""SELECT count(*), sum(n) FROM {s}.address_counts WHERE n > {rules.HUB_FLOOR}""").fetchone()
    out["busy_addresses"] = {"addresses": int(row[0]), "companies": int(row[1] or 0)}
    out["busiest"] = [{"address_key": k, "companies": int(n)} for k, n in conn.execute(
        f"SELECT address_key, n FROM {s}.address_counts ORDER BY n DESC LIMIT 5").fetchall()]
    return out


def _addr_keys(conn, s: str, entity_ref: str) -> set:
    if not entity_ref:
        return set()
    return {r[0] for r in conn.execute(f"SELECT address_key FROM {s}.entity_addresses WHERE entity_ref = %s", (entity_ref,)).fetchall()}


def m3_rule_error(conn, s: str) -> dict:
    """Each test pair against the rules directly and against the groups as built."""
    hubs = {k: int(n) for k, n in conn.execute(f"SELECT address_key, n FROM {s}.address_counts WHERE n > {rules.HUB_FLOOR}").fetchall()}
    cols = "ref, fl_key, full_key, has_middle, middle, politician, name_filed, register, entity_ref"
    out: dict = {"by_kind_and_band": [], "note": "error on 'two people' pairs = the rules confirmed them; on 'one person' pairs = the rules did not. "
                 "Caveat: two director rows on one company with an identical full name and middle name may be the register listing one person "
                 "twice (a re-appointment), so that part of the 'two people' truth is not clean; the count is given beside"}
    for kind, truth, band in conn.execute(f"SELECT DISTINCT kind, truth, band FROM {s}.test_pairs ORDER BY 1, 3").fetchall():
        n = confirmed_direct = confirmed_group = identical_full = 0
        by_rule: dict = {}
        for a, b in conn.execute(f"SELECT row_a, row_b FROM {s}.test_pairs WHERE kind = %s AND band = %s", (kind, band)).fetchall():
            ra = conn.execute(f"SELECT {cols} FROM {s}.rows WHERE ref = %s", (a,)).fetchone()
            rb = conn.execute(f"SELECT {cols} FROM {s}.rows WHERE ref = %s", (b,)).fetchone()
            if not ra or not rb:
                continue
            da = dict(zip(cols.replace(" ", "").split(","), ra))
            db_ = dict(zip(cols.replace(" ", "").split(","), rb))
            j = rules.judge(da, db_, _addr_keys(conn, s, da["entity_ref"]), _addr_keys(conn, s, db_["entity_ref"]), hubs)
            n += 1
            if da["has_middle"] and db_["has_middle"] and da["full_key"] == db_["full_key"]:
                identical_full += 1
            if j["grade"] == "confirmed":
                confirmed_direct += 1
                by_rule[j["rule"]] = by_rule.get(j["rule"], 0) + 1
            g = conn.execute(f"""SELECT ga.group_id = gb.group_id FROM {s}.groups ga, {s}.groups gb
                                 WHERE ga.row_key = %s AND gb.row_key = %s""", (a, b)).fetchone()
            if g and g[0]:
                confirmed_group += 1
        if n:
            err_direct = confirmed_direct / n if truth == "two people" else (n - confirmed_direct) / n
            err_group = confirmed_group / n if truth == "two people" else (n - confirmed_group) / n
            out["by_kind_and_band"].append({"kind": kind, "truth": truth, "band": band, "pairs": n,
                                            "confirmed_by_the_rules_directly": confirmed_direct, "confirmed_by_rule": by_rule,
                                            "in_one_group_as_built": confirmed_group,
                                            "pairs_with_identical_full_name_and_middle": identical_full,
                                            "error_rate_direct": round(err_direct, 4), "error_rate_as_built": round(err_group, 4)})
    r = conn.execute(f"""SELECT agent, verdict, count(*), bool_or(web_searched) FROM {s}.readings GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()
    out["agent_reading_of_confirmed_links"] = {"note": "an agent's judgment of the evidence, not a measurement against a known answer",
                                               "verdicts": [{"agent": a, "verdict": v, "links": int(n), "web_searched": bool(w)} for a, v, n, w in r]}
    return out


def m4_rule_reach(conn, s: str) -> dict:
    rows = conn.execute(f"""
        SELECT r.register, r.view, count(*) AS rows_,
               count(*) FILTER (WHERE r.has_middle) AS with_middle,
               count(*) FILTER (WHERE EXISTS (SELECT 1 FROM {s}.entity_addresses a WHERE a.entity_ref = r.entity_ref)) AS with_office_address,
               count(*) FILTER (WHERE r.politician) AS politician
        FROM {s}.rows r WHERE r.kind = 'person' GROUP BY 1, 2 ORDER BY 3 DESC""").fetchall()
    out = {"rows_each_rule_could_read": [{"register": a, "view": b, "rows": int(n), "rule_1_can_compare_a_middle_name": int(m),
                                          "rule_2_has_a_company_address": int(ad), "politician_rows_never_confirmed_by_name": int(p)}
                                         for a, b, n, m, ad, p in rows]}
    rows = conn.execute(f"""
        SELECT l.rule, l.grade, ra.register, rb.register, count(*)
        FROM {s}.links l LEFT JOIN {s}.rows ra ON ra.ref = l.row_a LEFT JOIN {s}.rows rb ON rb.ref = l.row_b
        GROUP BY 1, 2, 3, 4 ORDER BY 5 DESC""").fetchall()
    out["links_made"] = [{"rule": r, "grade": g, "registers": [a or "companies", b or "companies"], "links": int(n)} for r, g, a, b, n in rows]
    return out


def m5_company_names(conn, s: str) -> dict:
    rows = conn.execute(f"""
        WITH d AS (
            SELECT r.ref, r.register,
                   count(o.entity_ref) AS any_time,
                   count(o.entity_ref) FILTER (WHERE (o.registered_on IS NULL OR o.registered_on <= coalesce(r.ended_on, r.started_on, current_date))
                                                 AND (o.removed_on IS NULL OR o.removed_on >= coalesce(r.started_on, current_date))) AS alive
            FROM {s}.rows r LEFT JOIN {s}.org_names o ON o.org_key = r.name_key
            WHERE r.kind = 'organisation' AND r.register IN ('party_returns', 'disclosures') GROUP BY 1, 2)
        SELECT register, count(*), count(*) FILTER (WHERE alive = 1), count(*) FILTER (WHERE alive > 1),
               count(*) FILTER (WHERE alive = 0 AND any_time > 0), count(*) FILTER (WHERE any_time = 0)
        FROM d GROUP BY 1 ORDER BY 1""").fetchall()
    out = {"organisation_donors": []}
    for reg, n, one, many, dead, none in rows:
        out["organisation_donors"].append({"register": reg, "rows": int(n), "exactly_one_company_alive_on_the_date": int(one),
                                           "share": round(one / n, 4) if n else None, "several_alive": int(many),
                                           "name_held_but_none_alive_on_the_date": int(dead), "no_company_of_that_name": int(none)})
    return out


def m6_groups(conn, s: str) -> dict:
    rows = conn.execute(f"""
        WITH g AS (SELECT group_id, count(*) AS n, bool_or(contested) AS contested, count(DISTINCT split_part(row_key, ':', 1)) AS registers
                   FROM {s}.groups GROUP BY 1)
        SELECT CASE WHEN n = 2 THEN '2' WHEN n <= 5 THEN '3-5' WHEN n <= 20 THEN '6-20' WHEN n <= 100 THEN '21-100' ELSE 'over 100' END,
               count(*), sum(n), count(*) FILTER (WHERE contested), count(*) FILTER (WHERE registers > 1)
        FROM g GROUP BY 1 ORDER BY min(n)""").fetchall()
    out = {"sizes": [{"rows_in_group": b, "groups": int(g), "rows": int(r), "contested": int(c), "spanning_registers": int(sp)}
                     for b, g, r, c, sp in rows]}
    row = conn.execute(f"SELECT count(DISTINCT group_id), count(*), max(c) FROM (SELECT group_id, count(*) AS c FROM {s}.groups GROUP BY 1) x").fetchone()
    out["groups"], out["rows_in_groups"], out["largest"] = int(row[0]), int(row[1]), int(row[2] or 0)
    # a group that contradicts itself: a `not the same` decision whose two rows the walk still joins
    row = conn.execute(f"""
        SELECT count(*) FROM {s}.decisions d JOIN {s}.groups ga ON ga.row_key = d.row_a JOIN {s}.groups gb ON gb.row_key = d.row_b
        WHERE d.verdict = 'not the same' AND ga.group_id = gb.group_id""").fetchone()
    out["contradicting_decisions_inside_one_group"] = int(row[0])
    row = conn.execute(f"""SELECT count(*), count(*) FILTER (WHERE flags <> '[]'::jsonb) FROM {s}.watch""").fetchone()
    out["watch"] = {"links_watched": int(row[0]), "flagged": int(row[1])}
    out["largest_five"] = [{"group_id": g, "rows": int(n), "registers": r} for g, n, r in conn.execute(f"""
        SELECT group_id, count(*), array_agg(DISTINCT split_part(row_key, ':', 1)) FROM {s}.groups GROUP BY 1 ORDER BY 2 DESC LIMIT 5""").fetchall()]
    return out


MEASURES = (("1 name repeats", m1_name_repeats), ("2 shared addresses", m2_shared_addresses), ("3 rule error", m3_rule_error),
            ("4 rule reach", m4_rule_reach), ("5 company names", m5_company_names), ("6 group shape", m6_groups))


def run(conn, s: str, log=print, only: str = None) -> dict:
    out = {}
    for name, fn in MEASURES:
        if only and not name.startswith(only):
            continue
        t0 = time.monotonic()
        figures = fn(conn, s)
        figures["seconds"] = round(time.monotonic() - t0, 1)
        conn.execute(f"INSERT INTO {s}.measurements (name, figures) VALUES (%s, %s::jsonb)", (name, json.dumps(figures, default=str)))
        conn.commit()
        out[name] = figures
        log(f"links.measure: {name}: {figures['seconds']} s")
    return out


def main(argv=None) -> int:
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    s = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = 0")
        print(json.dumps(run(conn, s, only=only), indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
