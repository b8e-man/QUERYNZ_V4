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
   match exactly one company alive on the donation date; and, beside them,
   the companies a member declared (`mp_interests`) on the return's date.
6. The shape of the groups: sizes, and any group that contradicts itself.
7. Ruling 106's three rules: what each confirmed or related, what it left
   near and why, and the groups they touch.
8. Ruling 107's rule: the donation rows whose name several companies carry,
   by how many of them were live in the year; what it confirmed, to how many
   companies, and the groups those rows sit in.
9. Ruling 109's rule: companies under one name key with no year in
   brackets, one removed, by whether the other was registered within twelve
   months of the removal, has people, and shares a confirmed person; what
   `refiled-name@1` related, every pair listed; and any relation beyond the
   twelve months or with no shared person, which must be none.
10. Ruling 114: the eight people views' rows, name keys, links and groups;
   the bodies on the four registers and how many fold onto another row; the
   organisation rules' links by the body's register, every confirmation to
   a body off the companies register listed; and the charities officer
   identifier's repeats (none: it keys a row, not a person).
12. Ruling 125: the organisation rules on every organisation-named row, by
   view: the rows, the dated, those with a body of the name, what the
   time-aware rule confirmed (sole, one live of several) and left near by
   outcome, and the rows by how many bodies carry the name (the queue
   item's figures: exactly one body; several with one live on the date).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time

import links
from links import rows as lrows
from links import rules
from links.pairs import COMPANY_KINDS, ORG_KINDS

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


def _org_judgment(conn, s: str, a: str, b: str):
    """What the build's rule (`rules.body_on_date`, rulings 114 and 125) says about an organisation-named row and one body of
    its name, from the facts the build reads: every body of the name on the four registers, with all its register rows. The
    row is whichever of the pair is an organisation-named row of `rows`; the other is the body."""
    found = conn.execute(f"""SELECT ref, register, view, name_filed, name_key, started_on, ended_on FROM {s}.rows
                             WHERE ref IN (%s, %s) AND kind = 'organisation' ORDER BY ref COLLATE "C" """, (a, b)).fetchall()
    if not found:
        return None
    row = found[0]
    body = b if row[0] == a else a
    rows_of: dict = {}
    for bd, ref, register, kind, number, name, reg, rem, undated, named in conn.execute(f"""
            SELECT b.body, b.entity_ref, b.register, b.kind, b.number, b.name, b.registered_on, b.removed_on, b.removal_undated, b.org_key = %s
            FROM {s}.bodies b WHERE b.body IN (SELECT body FROM {s}.bodies WHERE org_key = %s) ORDER BY 1, 2""", (row[4], row[4])).fetchall():
        rows_of.setdefault(bd, []).append({"entity_ref": ref, "register": register, "kind": kind, "number": number, "name": name,
                                           "registered_on": reg, "removed_on": rem, "removal_undated": undated, "named": named})
    judged = rules.body_on_date(dict(zip(("ref", "register", "view", "name_filed", "name_key", "started_on", "ended_on"), row)),
                                [{"body": bd, "rows": rs} for bd, rs in rows_of.items()])
    return next((j for j in judged if j["entity_ref"] == body), None)


def _company_judgment(conn, s: str, a: str, b: str):
    """(what `rules.refiled` says about two companies of one name, within the twelve months, a person shared) from the facts the
    build reads, the people's components read from the groups as built."""
    co = {e: {"entity_ref": e, "org_key": k, "registered_on": r, "removed_on": m} for e, k, r, m in conn.execute(
        f"SELECT entity_ref, org_key, registered_on, removed_on FROM {s}.org_names WHERE entity_ref IN (%s, %s)", (a, b)).fetchall()}
    if len(co) < 2:
        return None
    people: dict = {}
    for ref, entity, filed, g in conn.execute(f"""SELECT r.ref, r.entity_ref, r.name_filed, g.group_id FROM {s}.rows r JOIN {s}.groups g ON g.row_key = r.ref
                                                  WHERE r.entity_ref IN (%s, %s) AND r.view IN ('directors', 'shareholders') AND r.kind = 'person'""",
                                               (a, b)).fetchall():
        people.setdefault(entity, {}).setdefault(g, []).append((ref, filed))
    from links.build import shared_people
    shared = shared_people(people, a, b)
    first, then = sorted(co.values(), key=lambda c: (c["registered_on"] or dt.date.max, c["removed_on"] is None, c["entity_ref"]))
    return rules.refiled(co[a], co[b], shared), rules.within_months(first["removed_on"], then["registered_on"]), bool(shared)


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
        wrongly = {"related_by_relation": {}, "related_beyond_twelve_months": 0, "related_without_a_shared_person": 0}
        for a, b in conn.execute(f"SELECT row_a, row_b FROM {s}.test_pairs WHERE kind = %s AND band = %s", (kind, band)).fetchall():
            if kind in COMPANY_KINDS:     # two companies of one name: judged by ruling 109's rule; a relation is never an identity
                got = _company_judgment(conn, s, a, b)
                if got is None:
                    continue
                j, within, shared = got
                n += 1
                if j:
                    wrongly["related_by_relation"][j["relation"]] = wrongly["related_by_relation"].get(j["relation"], 0) + 1
                    wrongly["related_beyond_twelve_months"] += not within
                    wrongly["related_without_a_shared_person"] += not shared
                g = conn.execute(f"""SELECT ga.group_id = gb.group_id FROM {s}.groups ga, {s}.groups gb
                                     WHERE ga.row_key = %s AND gb.row_key = %s""", (a, b)).fetchone()
                confirmed_group += bool(g and g[0])
                continue
            if kind in ORG_KINDS:     # a donation row and a company: judged by ruling 106 and 107's rule, not the people rules
                j = _org_judgment(conn, s, a, b)
                if j is None:
                    continue
                n += 1
                if j["grade"] == "confirmed":
                    confirmed_direct += 1
                    by_rule[j["rule"]] = by_rule.get(j["rule"], 0) + 1
                g = conn.execute(f"""SELECT ga.group_id = gb.group_id FROM {s}.groups ga, {s}.groups gb
                                     WHERE ga.row_key = %s AND gb.row_key = %s""", (a, b)).fetchone()
                confirmed_group += bool(g and g[0])
                continue
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
                                            "error_rate_direct": round(err_direct, 4), "error_rate_as_built": round(err_group, 4),
                                            **(wrongly if kind in COMPANY_KINDS else {})})
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
            WHERE r.kind = 'organisation' AND r.register IN ('party_returns', 'candidate_returns', 'disclosures', 'mp_interests') GROUP BY 1, 2)
        SELECT register, count(*), count(*) FILTER (WHERE alive = 1), count(*) FILTER (WHERE alive > 1),
               count(*) FILTER (WHERE alive = 0 AND any_time > 0), count(*) FILTER (WHERE any_time = 0)
        FROM d GROUP BY 1 ORDER BY 1""").fetchall()
    out = {"organisation_donors": [], "note": "mp_interests rows are the companies a member declared, dated by the return, not donors"}
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
    row = conn.execute(f"SELECT count(*), sum(c), max(c) FROM (SELECT group_id, count(*) AS c FROM {s}.groups GROUP BY 1) x").fetchone()
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


def m7_ruling_106(conn, s: str) -> dict:
    out = {"links": [{"rule": r, "grade": g, "reason": why, "links": int(n)} for r, g, why, n in conn.execute(f"""
        SELECT rule, grade, reason, count(*) FROM {s}.links WHERE rule = ANY(%s) GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""",
        ([rules.RULE_SOLE_COMPANY, rules.RULE_ORG_NAME, rules.RULE_SUCCESSOR, rules.RULE_COMPANY_NAME, rules.RULE_SAME_PARTY, rules.RULE_NAME_FORM],)).fetchall()]}
    row = conn.execute(f"""SELECT count(DISTINCT r.ref) FROM {s}.links l JOIN {s}.rows r ON r.ref IN (l.row_a, l.row_b) AND r.kind = 'organisation'
                           WHERE l.rule = %s""", (rules.RULE_SOLE_COMPANY,)).fetchone()
    out["donation_rows_confirmed_to_a_company"] = int(row[0])
    row = conn.execute(f"""SELECT count(*), coalesce(sum((evidence->>'shared_people')::int), 0), count(*) FILTER (WHERE (evidence->>'shared_people')::int > 1),
                                  count(*) FILTER (WHERE evidence->>'order' <> 'by registration date')
                           FROM {s}.links WHERE rule = %s""", (rules.RULE_SUCCESSOR,)).fetchone()
    out["successions"] = {"related": int(row[0]), "shared_people": int(row[1]), "with_more_than_one_shared_person": int(row[2]),
                          "ordered_by_key_not_date": int(row[3])}
    row = conn.execute(f"""SELECT count(*), count(DISTINCT g.group_id) FROM {s}.links l JOIN {s}.groups g ON g.row_key IN (l.row_a, l.row_b)
                           WHERE l.rule = %s AND l.grade = 'confirmed'""", (rules.RULE_SAME_PARTY,)).fetchone()
    out["candidates"] = {"row_ends_of_confirmed_pairs": int(row[0]), "groups_they_sit_in": int(row[1])}
    return out


def m8_ruling_107(conn, s: str) -> dict:
    out = {"links": [{"rule": r, "grade": g, "reason": why, "links": int(n)} for r, g, why, n in conn.execute(f"""
        SELECT l.rule, l.grade, l.reason, count(*) FROM {s}.links l JOIN {s}.rows r ON r.ref IN (l.row_a, l.row_b)
        WHERE l.rule = ANY(%s) AND r.kind = 'organisation' AND r.register = ANY(%s) AND (l.evidence->>'companies_of_that_name')::int > 1
        GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""", ([rules.RULE_ONE_LIVE, rules.RULE_ORG_NAME], list(rules.DONATION_REGISTERS))).fetchall()]}
    out["donation_rows_by_companies_live_in_the_year"] = [{"live": int(k), "rows": int(n)} for k, n in conn.execute(f"""
        SELECT live, count(*) FROM (
            SELECT DISTINCT r.ref, (l.evidence->>'companies_alive_on_date')::int AS live FROM {s}.links l JOIN {s}.rows r ON r.ref IN (l.row_a, l.row_b)
            WHERE l.rule = ANY(%s) AND r.kind = 'organisation' AND r.register = ANY(%s) AND (l.evidence->>'companies_of_that_name')::int > 1) x
        GROUP BY 1 ORDER BY 1""", ([rules.RULE_ONE_LIVE, rules.RULE_ORG_NAME], list(rules.DONATION_REGISTERS))).fetchall()]
    row = conn.execute(f"""
        SELECT count(*), count(DISTINCT r.ref), count(DISTINCT CASE WHEN r.ref = l.row_a THEN l.row_b ELSE l.row_a END),
               count(DISTINCT g.group_id)
        FROM {s}.links l JOIN {s}.rows r ON r.ref IN (l.row_a, l.row_b) AND r.kind = 'organisation'
        LEFT JOIN {s}.groups g ON g.row_key = r.ref
        WHERE l.rule = %s AND l.grade = 'confirmed'""", (rules.RULE_ONE_LIVE,)).fetchone()
    out["confirmed"] = {"links": int(row[0]), "donation_rows": int(row[1]), "companies": int(row[2]), "groups_the_rows_sit_in": int(row[3])}
    return out


def m9_ruling_109(conn, s: str) -> dict:
    """Ruling 109: the gap and what `refiled-name@1` related, counted in SQL apart from the rule."""
    row = conn.execute(f"""
        WITH o AS (SELECT * FROM {s}.org_names WHERE org_key !~ '\\(\\d{{4}}\\)' AND org_key <> ''),
             p AS (SELECT a.entity_ref AS ea, b.entity_ref AS eb,
                          (a.removed_on IS NOT NULL AND b.registered_on BETWEEN a.removed_on - interval '12 months' AND a.removed_on + interval '12 months')
                          OR (b.removed_on IS NOT NULL AND a.registered_on BETWEEN b.removed_on - interval '12 months' AND b.removed_on + interval '12 months') AS within
                   FROM o a JOIN o b ON b.org_key = a.org_key AND b.entity_ref COLLATE "C" > a.entity_ref
                   WHERE a.removed_on IS NOT NULL OR b.removed_on IS NOT NULL),
             w AS (SELECT ea, eb FROM p WHERE within),
             pe AS (SELECT DISTINCT r.entity_ref, g.group_id FROM {s}.rows r LEFT JOIN {s}.groups g ON g.row_key = r.ref
                    WHERE r.entity_ref IN (SELECT ea FROM w UNION SELECT eb FROM w) AND r.view IN ('directors', 'shareholders') AND r.kind = 'person'),
             has AS (SELECT DISTINCT entity_ref FROM pe),
             sh AS (SELECT DISTINCT w.ea, w.eb FROM w JOIN pe x ON x.entity_ref = w.ea JOIN pe y ON y.entity_ref = w.eb AND y.group_id = x.group_id)
        SELECT (SELECT count(*) FROM p), (SELECT count(*) FROM w),
               (SELECT count(*) FROM w WHERE ea IN (SELECT entity_ref FROM has) AND eb IN (SELECT entity_ref FROM has)),
               (SELECT count(*) FROM w WHERE (ea IN (SELECT entity_ref FROM has)) <> (eb IN (SELECT entity_ref FROM has))),
               (SELECT count(*) FROM sh)""").fetchone()
    out = {"pairs_under_one_name_no_year_one_removed": int(row[0]), "removed_and_registered_within_twelve_months": int(row[1]),
           "within_with_people_on_both": int(row[2]), "within_with_people_on_one_only": int(row[3]),
           "within_sharing_a_confirmed_person": int(row[4])}
    out["removed_companies_with_a_person_row"] = [{"removed": bool(r), "companies": int(n), "with_a_person_row": int(w)} for r, n, w in conn.execute(f"""
        SELECT o.removed_on IS NOT NULL, count(*), count(*) FILTER (WHERE EXISTS (
            SELECT 1 FROM {s}.rows r WHERE r.entity_ref = o.entity_ref AND r.view IN ('directors', 'shareholders') AND r.kind = 'person'))
        FROM {s}.org_names o GROUP BY 1 ORDER BY 1""").fetchall()]
    out["related"] = [{"earlier": [en, enum, str(ereg), str(erem)], "later": [ln, lnum, str(lreg)], "gap_days": int(gap), "shared_people": int(sp)}
                      for en, enum, ereg, erem, ln, lnum, lreg, gap, sp in conn.execute(f"""
        SELECT ce.name, ce.number, e.registered_on, e.removed_on, ct.name, ct.number, t.registered_on, t.registered_on - e.removed_on,
               (l.evidence->>'shared_people')::int
        FROM {s}.links l JOIN {s}.org_names e ON e.entity_ref = l.evidence->>'earlier' JOIN {s}.org_names t ON t.entity_ref = l.evidence->>'later'
        LEFT JOIN pub.companies ce ON 'companies:' || ce.key = e.entity_ref LEFT JOIN pub.companies ct ON 'companies:' || ct.key = t.entity_ref
        WHERE l.rule = %s ORDER BY e.org_key, e.entity_ref COLLATE "C" """, (rules.RULE_REFILED,)).fetchall()]
    out["related_beyond_twelve_months"] = sum(1 for r in out["related"] if r["later"][2] == "None" or r["earlier"][3] == "None") + int(conn.execute(f"""
        SELECT count(*) FROM {s}.links l JOIN {s}.org_names e ON e.entity_ref = l.evidence->>'earlier' JOIN {s}.org_names t ON t.entity_ref = l.evidence->>'later'
        WHERE l.rule = %s AND (t.registered_on < e.removed_on - interval '12 months' OR t.registered_on > e.removed_on + interval '12 months')""",
        (rules.RULE_REFILED,)).fetchone()[0])
    out["related_without_a_shared_person"] = sum(1 for r in out["related"] if r["shared_people"] < 1)
    return out


NEW_PEOPLE_VIEWS = ("charity_officers", "gazette_celebrants", "gazette_practitioners", "limited_partnership_partners", "party_board_roles",
                    "local_election_returns", "building_practitioner_decisions", "councillor_interests")


def m10_ruling_114(conn, s: str) -> dict:
    """Ruling 114: what the eight people views brought (rows, name keys, the links that reach their rows) and what the
    organisation rules confirm on the four registers together, by the body's register; and whether the charities officer
    identifier repeats across rows (the one-person test pairs measurement 3 waited on)."""
    out = {"people_views": []}
    for view in NEW_PEOPLE_VIEWS:
        r = conn.execute(f"""SELECT count(*), count(DISTINCT name_key), count(*) FILTER (WHERE fl_key IS NOT NULL), count(*) FILTER (WHERE has_middle)
                             FROM {s}.rows WHERE view = %s""", (view,)).fetchone()
        c = conn.execute(f"SELECT read, written, set_aside, reasons FROM {s}.rows_catch WHERE view = %s", (view,)).fetchone()
        l = dict(((rule, grade), int(n)) for rule, grade, n in conn.execute(f"""
            SELECT l.rule, l.grade, count(DISTINCT l.link_id) FROM {s}.links l JOIN {s}.rows r ON r.ref IN (l.row_a, l.row_b)
            WHERE r.view = %s GROUP BY 1, 2""", (view,)).fetchall())
        g = conn.execute(f"""SELECT count(*), count(DISTINCT g.group_id) FROM {s}.rows r JOIN {s}.groups g ON g.row_key = r.ref
                             WHERE r.view = %s""", (view,)).fetchone()
        out["people_views"].append({"view": view, "rows": int(r[0]), "name_keys": int(r[1]), "first_and_last": int(r[2]), "with_middle": int(r[3]),
                                    "catch": {"read": c[0], "written": c[1], "set_aside": c[2], "reasons": c[3]} if c else None,
                                    "near_name_only_links": l.get((rules.RULE_NAME_ONLY, "near"), 0),
                                    "confirmed_full_name_links": l.get((rules.RULE_FULL, "confirmed"), 0),
                                    "rows_in_groups": int(g[0]), "groups": int(g[1])})
    out["rows"], out["name_keys"] = (int(x) for x in conn.execute(f"SELECT count(*), count(DISTINCT name_key) FROM {s}.rows").fetchone())
    out["bodies"] = [{"register": r, "rows": int(n), "folded_onto_another_row": int(f)} for r, n, f in conn.execute(f"""
        SELECT register, count(*), count(*) FILTER (WHERE body <> entity_ref) FROM {s}.bodies GROUP BY 1 ORDER BY 1""").fetchall()]
    out["organisation_links"] = [{"rule": r, "grade": g, "reason": why, "register": reg, "links": int(n)} for r, g, why, reg, n in conn.execute(f"""
        SELECT l.rule, l.grade, l.reason, l.evidence->>'register', count(*) FROM {s}.links l JOIN {s}.rows r ON r.ref IN (l.row_a, l.row_b)
        WHERE l.rule = ANY(%s) AND r.kind = 'organisation' AND r.register = ANY(%s) GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4""",
        ([rules.RULE_SOLE_BODY_DATED, rules.RULE_ONE_LIVE_BODY_DATED, rules.RULE_SOLE_BODY, rules.RULE_ONE_LIVE_BODY, rules.RULE_ORG_NAME,
          rules.RULE_SOLE_COMPANY, rules.RULE_ONE_LIVE], list(rules.DONATION_REGISTERS))).fetchall()]
    out["confirmed_off_the_companies_register"] = [
        {"donor": d, "body": b, "register": reg, "number": num, "year": y, "rule": r} for d, b, reg, num, y, r in conn.execute(f"""
        SELECT l.evidence->>'name', l.evidence->>'company', l.evidence->>'register', l.evidence->>'company_number',
               substr(l.evidence->>'date', 1, 4), l.rule
        FROM {s}.links l JOIN {s}.rows r ON r.ref IN (l.row_a, l.row_b) AND r.kind = 'organisation' AND r.register = ANY(%s)
        WHERE l.rule = ANY(%s) AND l.grade = 'confirmed'
          AND (l.evidence->>'register' <> 'companies' OR jsonb_path_exists(l.evidence, '$.registers[*] ? (@.register != "companies")'))
        ORDER BY 3, 1, 5""", (list(rules.DONATION_REGISTERS),
                              [rules.RULE_SOLE_BODY_DATED, rules.RULE_ONE_LIVE_BODY_DATED, rules.RULE_SOLE_BODY, rules.RULE_ONE_LIVE_BODY])).fetchall()]
    if conn.execute("SELECT to_regclass('pub.charity_officers')").fetchone()[0] is None:     # the sample database publishes no charities
        return out
    n, ids = conn.execute("SELECT count(*), count(DISTINCT key) FROM pub.charity_officers").fetchone()
    out["charity_officer_identifier"] = {"rows": int(n), "distinct_officer_ids": int(ids), "ids_on_more_than_one_row": int(n) - int(ids),
                                         "note": "the feed's OfficerId keys one officer row: one person on two charities, or across two "
                                                 "returns, carries two ids, so the identifier supplies no one-person pair"}
    return out


def m11_ruling_116(conn, s: str) -> dict:
    """Ruling 116: what each member view's rows came to under `member-on-the-day@1` (a written question's asker and minister
    apart): one member sitting, two or more, a member of the name at another time only, no member of the name, a day before
    the members view's first term; the twenty printed names that most often find no member on a day the view holds; ten
    confirmed pairs a view, named; and whether Parliament's member id, carried in the evidence, ever names two members."""
    held = conn.execute(f"SELECT min(started_on) FROM {s}.rows WHERE view = 'members'").fetchone()[0]
    conn.execute(f"""CREATE TEMP TABLE m11 ON COMMIT DROP AS
        WITH l AS (SELECT row_a AS ref, grade, reason FROM {s}.links WHERE rule = %(rule)s
                   UNION ALL SELECT row_b, grade, reason FROM {s}.links WHERE rule = %(rule)s),
             g AS (SELECT ref, bool_or(grade = 'confirmed') AS one, bool_or(reason = %(two)s) AS two, bool_or(reason = %(none)s) AS none
                   FROM l GROUP BY ref)
        SELECT r.ref, r.name_filed, r.started_on,
               r.view || CASE WHEN r.view = ANY(%(roles)s) THEN '#' || substring(r.ref from '#([a-z]+)$') ELSE '' END AS row_of,
               CASE WHEN g.one THEN %(d_one)s WHEN g.two THEN %(d_two)s WHEN g.none THEN %(d_none)s WHEN r.started_on IS NULL THEN %(d_undated)s
                    WHEN %(held)s::date IS NULL OR r.started_on < %(held)s::date THEN %(d_before)s
                    ELSE %(d_no)s END AS came_to
        FROM {s}.rows r LEFT JOIN g ON g.ref = r.ref
        WHERE r.view = ANY(%(views)s) AND r.part_of IS NULL""",
                 {"rule": rules.RULE_MEMBER_DAY, "two": rules.NEAR_DAY_TWO, "none": rules.NEAR_DAY_NONE, "held": held,
                  "d_one": rules.DAY_ONE, "d_two": rules.DAY_TWO, "d_none": rules.DAY_NONE, "d_undated": rules.DAY_UNDATED,
                  "d_before": rules.DAY_BEFORE, "d_no": rules.DAY_NO_MEMBER, "views": list(lrows.MEMBER_DAY_VIEWS),
                  "roles": sorted(lrows.ROLE_VIEWS)})
    out = {"held_from": str(held), "rows": {}, "finding_none": {}, "confirmed_pairs": {}}
    for row_of, came_to, n in conn.execute("SELECT row_of, came_to, count(*) FROM m11 GROUP BY 1, 2 ORDER BY 1, 2").fetchall():
        out["rows"].setdefault(row_of, {"rows": 0})[came_to] = int(n)
        out["rows"][row_of]["rows"] += int(n)
    for row_of, name, n in conn.execute("""
            SELECT row_of, name_filed, n FROM (SELECT row_of, name_filed, count(*) AS n,
                                                      row_number() OVER (PARTITION BY row_of ORDER BY count(*) DESC, name_filed) AS i
                                               FROM m11 WHERE came_to IN (%s, %s) GROUP BY 1, 2) t WHERE i <= 20 ORDER BY 1, 3 DESC, 2""",
                                        (rules.DAY_NONE, rules.DAY_NO_MEMBER)).fetchall():
        out["finding_none"].setdefault(row_of, []).append([name, int(n)])
    for row_of, name, member, key, day in conn.execute(f"""
            WITH t AS (SELECT * FROM (SELECT ref, row_of, name_filed, started_on,
                                             row_number() OVER (PARTITION BY row_of ORDER BY md5(ref)) AS i FROM m11 WHERE came_to = %s) a
                       WHERE i <= 10)
            SELECT t.row_of, t.name_filed, m.name_filed, m.key, t.started_on
            FROM t JOIN {s}.links l ON l.rule = %s AND l.grade = 'confirmed' AND t.ref IN (l.row_a, l.row_b)
            JOIN {s}.rows m ON m.ref IN (l.row_a, l.row_b) AND m.view = 'members' ORDER BY 1, 5, 2""",
                                                         (rules.DAY_ONE, rules.RULE_MEMBER_DAY)).fetchall():
        out["confirmed_pairs"].setdefault(row_of, []).append([name, member, key, str(day)])
    ids, two, keys_two = (int(x) for x in conn.execute(f"""
        WITH i AS (SELECT l.evidence->>'parliament_member_id' AS id, m.fl_key FROM {s}.links l
                   JOIN {s}.rows m ON m.ref IN (l.row_a, l.row_b) AND m.view = 'members'
                   WHERE l.rule = %s AND l.grade = 'confirmed' AND l.evidence->>'parliament_member_id' IS NOT NULL)
        SELECT count(DISTINCT id), (SELECT count(*) FROM (SELECT id FROM i GROUP BY 1 HAVING count(DISTINCT fl_key) > 1) a),
               (SELECT count(*) FROM (SELECT fl_key FROM i GROUP BY 1 HAVING count(DISTINCT id) > 1) b) FROM i""",
                                                          (rules.RULE_MEMBER_DAY,)).fetchone())
    out["parliament_member_ids"] = {"ids_on_confirmed_rows": ids, "ids_naming_two_members": two, "members_under_two_ids": keys_two}
    return out


def m12_ruling_125(conn, s: str) -> dict:
    """Ruling 125: every organisation-named row of every people view against the bodies of its name, judged on the row's own
    date: by view, the rows, the dated, those with a body of the name, what @3 confirmed (sole; one live of several) and left
    near by outcome (`evidence.outcome`), from the links as built; and the rows by how many bodies carry the name and how many
    of those were live on the row's date (the queue item's figures), from the rows and the bodies apart from the links."""
    out = {"by_view": []}
    links_by: dict = {}
    for view, rule, outcome, n in conn.execute(f"""
            SELECT r.view, l.rule, coalesce(l.evidence->>'outcome', l.reason), count(*)
            FROM {s}.links l JOIN {s}.rows r ON r.ref IN (l.row_a, l.row_b) AND r.kind = 'organisation'
            WHERE l.rule = ANY(%s) GROUP BY 1, 2, 3""",
            ([rules.RULE_SOLE_BODY_DATED, rules.RULE_ONE_LIVE_BODY_DATED, rules.RULE_ORG_NAME],)).fetchall():
        links_by.setdefault(view, {})[(rule, outcome)] = int(n)
    for view, register, n, dated, with_body, one, one_live, several_one, several_many, several_none in conn.execute(f"""
            WITH r AS (SELECT r.ref, r.view, r.register, r.name_key, r.started_on AS st, coalesce(r.ended_on, r.started_on) AS en,
                              count(DISTINCT b.body) AS bodies
                       FROM {s}.rows r LEFT JOIN {s}.bodies b ON b.org_key = r.name_key
                       WHERE r.kind = 'organisation' GROUP BY 1, 2, 3, 4, 5, 6),
                 k AS (SELECT DISTINCT b.org_key, b.body FROM {s}.bodies b WHERE b.org_key IN (SELECT name_key FROM r)),
                 {rules.body_dates_sql(s)},
                 live AS (SELECT r.ref, count(*) FILTER (WHERE (bd.reg IS NULL OR bd.reg <= r.en)
                                                           AND (NOT bd.removed OR (bd.removed_on IS NOT NULL AND bd.removed_on >= r.st))) AS n
                          FROM r JOIN k ON k.org_key = r.name_key JOIN bd ON bd.body = k.body WHERE r.st IS NOT NULL GROUP BY 1)
            SELECT r.view, r.register, count(*), count(*) FILTER (WHERE r.st IS NOT NULL), count(*) FILTER (WHERE r.bodies > 0),
                   count(*) FILTER (WHERE r.bodies = 1), count(*) FILTER (WHERE r.bodies = 1 AND live.n = 1),
                   count(*) FILTER (WHERE r.bodies > 1 AND live.n = 1), count(*) FILTER (WHERE r.bodies > 1 AND live.n > 1),
                   count(*) FILTER (WHERE r.bodies > 1 AND live.n = 0)
            FROM r LEFT JOIN live ON live.ref = r.ref GROUP BY 1, 2 ORDER BY 3 DESC, 1""").fetchall():
        lb = links_by.get(view, {})
        near = {outcome: k for (rule, outcome), k in lb.items() if rule == rules.RULE_ORG_NAME}
        out["by_view"].append({"view": view, "register": register, "rows": int(n), "dated": int(dated), "with_a_body_of_the_name": int(with_body),
                               "exactly_one_body_of_the_name": int(one), "of_which_live_on_the_date": int(one_live),
                               "several_bodies_one_live_on_the_date": int(several_one), "several_more_than_one_live": int(several_many),
                               "several_none_live": int(several_none),
                               "confirmed_sole": lb.get((rules.RULE_SOLE_BODY_DATED, "sole"), 0),
                               "confirmed_one_live_of_several": lb.get((rules.RULE_ONE_LIVE_BODY_DATED, "one_live"), 0),
                               "near_links_by_outcome": dict(sorted(near.items()))})
    out["note"] = ("live on the date: registered on or before the row's window's end and not removed before its start, by the body's own "
                   "register's dates (the formation registers' where it has any, else its charity row's); an undated row is never judged "
                   "live; the links' outcomes are the build's, the body counts are the rows' and the bodies' apart from the build")
    return out


#: step 8.2 (2 November 2026): the categories of a member's return the lane does not read for a body, and which side of the
#: entry's dash names it ("Te Karetu Farm Limited – agriculture": before; "Rugby World Cup tickets – HSBC": after). The real
#: property category is never read: its text is a place
DECLARED_SIDES = {"employment": "before", "seeking-government-funding": "before", "debts-owed-by-member": "before",
                  "debts-owed-to-member": "before", "trusts": "whole", "retirement-schemes": "whole",
                  "managed-investment-schemes": "both", "payments-for-activities": "both", "gifts": "after",
                  "directorships": "before", "business-interests": "before"}
READ_NOW = ("directorships", "business-interests")       # the lane's DECLARED reading today (links/rows.py ROW_SQL)


def declared_body(text: str, side: str) -> list:
    """The body names an entry's text offers on its side of the first dash, each with the side it came from."""
    t = " ".join((text or "").split())
    for sep in lrows._DASHES:
        if sep in t:
            before, after = t.split(sep, 1)
            break
    else:
        before, after = t, ""
    after = after.split(" – ")[0]
    out = []
    if side in ("before", "both", "whole"):
        out.append(("before", lrows._TRAILING_NOTE.sub("", before if side != "whole" else t).strip(" .,;:")))
    if side in ("after", "both") and after:
        out.append(("after", lrows._TRAILING_NOTE.sub("", after).strip(" .,;:")))
    return [(s, n) for s, n in out if n]


def m13_declared_bodies(conn, s: str = "links", sample: int = 20, seed: str = "8.2") -> dict:
    """Step 8.2's first rule: a member's declared interest to the body it names, by the one organisation key against
    `links.bodies`, judged on the return's date (`as_at`) as ruling 125's organisation rules judge a row: by category and side,
    the entries, those with a body of the name, exactly one, of which live on the date, several with one live, none live; for
    the two categories the lane reads today, what the build already did (confirmed to a company, near). Twenty entries matched
    to exactly one body live on the date, drawn by a fixed hash, from the categories not read today."""
    from keys import names as kn
    entries = conn.execute("SELECT key, member, category, text, as_at FROM pub.mp_interests WHERE category = ANY(%s) AND NOT withheld",
                           (list(DECLARED_SIDES),)).fetchall()
    keyed = []
    for key, member, cat, text, as_at in entries:
        for side, name in declared_body(text, DECLARED_SIDES[cat]):
            k = kn.organisation_key(name)
            if k:
                keyed.append((key, member, cat, side, name, k, as_at))
    bodies: dict = {}
    for body, org_key, register, number, bname, reg, rem, undated in conn.execute(
            "SELECT DISTINCT body, org_key, register, number, name, registered_on, removed_on, removal_undated FROM links.bodies "
            "WHERE org_key = ANY(%s)", (sorted({k[5] for k in keyed}),)).fetchall():
        bodies.setdefault(org_key, {}).setdefault(body, (register, number, bname, reg, rem, undated))

    def live(b, on):
        register, number, bname, reg, rem, undated = b
        # removed on no stated day is never live (the organisation rules' `NOT removed OR removed_on >= start`)
        return on is not None and (reg is None or reg <= on) and not undated and (rem is None or rem >= on)

    by: dict = {}
    hits = []
    for key, member, cat, side, name, k, as_at in keyed:
        bs = bodies.get(k, {})
        n_live = sum(1 for b in bs.values() if live(b, as_at))
        row = by.setdefault((cat, side), {"entries": 0, "with_a_body_of_the_name": 0, "exactly_one_body": 0, "of_which_live_on_the_date": 0,
                                          "several_one_live": 0, "several_more_live": 0, "none_live": 0, "by_register_of_the_one": {}})
        row["entries"] += 1
        if bs:
            row["with_a_body_of_the_name"] += 1
        if len(bs) == 1:
            row["exactly_one_body"] += 1
            if n_live == 1:
                row["of_which_live_on_the_date"] += 1
                reg = next(iter(bs.values()))[0]
                row["by_register_of_the_one"][reg] = row["by_register_of_the_one"].get(reg, 0) + 1
                if cat not in READ_NOW:
                    hits.append((key, member, cat, side, name, next(iter(bs.values()))))
        elif bs:
            row["several_one_live" if n_live == 1 else ("several_more_live" if n_live > 1 else "none_live")] += 1
    import hashlib
    hits.sort(key=lambda h: hashlib.sha256((seed + h[0] + h[3]).encode()).hexdigest())
    pairs = [{"member": h[1], "category": h[2], "side": h[3], "as_printed": h[4], "body_register": h[5][0], "body_number": h[5][1],
              "body_name": h[5][2], "entry": f"mp_interests:{h[0]}"} for h in hits[:sample]]
    done = dict(conn.execute("""
        SELECT x.category, count(DISTINCT x.key) FILTER (WHERE l.grade = 'confirmed') FROM pub.mp_interests x
        LEFT JOIN pub.links l ON ('mp_interests:' || x.key) IN (l.row_a, l.row_b) AND (l.row_a LIKE 'companies:%%' OR l.row_b LIKE 'companies:%%')
        WHERE x.category = ANY(%s) GROUP BY 1""", (list(READ_NOW),)).fetchall())
    return {"by_category_and_side": [{"category": c, "side": sd, "read_today": c in READ_NOW, **v} for (c, sd), v in sorted(by.items())],
            "confirmed_to_a_company_by_the_build_today": {c: int(n) for c, n in done.items()},
            "candidates_not_read_today": len(hits), "pairs": pairs,
            "note": "live on the date: registered on or before the return's date and not removed before it, by the body's register's "
                    "dates in links.bodies; entries the return withholds are not read; real property is never read"}


def m14_charity_officers(conn, s: str = "links", sample: int = 20, seed: str = "8.2") -> dict:
    """Step 8.2's second rule: a charity officer and a director (or a society officer) of the same body, the charity being
    that company or society by a shared business number (ruling 124: a charity is its company only by shared NZBN), with the
    same first and last name key: by register of the body, the officers, those on a body with officers in the other register,
    with exactly one same-name officer there, several, none; of the one, the full name equal or apart, and what pub.links holds
    between the two rows today. Twenty pairs drawn by a fixed hash."""
    zero = "9429000000000"
    rows = conn.execute(f"""
        WITH co AS (SELECT n.ref, n.name_filed, n.fl_key, n.full_key, n.has_middle, c.nzbn, c.number AS charity_number
                    FROM pub.names n JOIN pub.charity_officers o ON n.ref = 'charities:' || o.key
                    JOIN pub.charities c ON c.key = o.charity_key
                    WHERE n.view = 'charity_officers' AND n.kind = 'person' AND n.fl_key IS NOT NULL),
             other AS (SELECT n.ref, n.view, n.name_filed, n.fl_key, n.full_key, n.has_middle, split_part(n.ref, '/', 2) AS nzbn
                       FROM pub.names n WHERE n.view IN ('directors', 'society_officers') AND n.kind = 'person' AND n.fl_key IS NOT NULL
                       AND split_part(n.ref, '/', 2) IN (SELECT nzbn FROM co WHERE nzbn IS NOT NULL AND nzbn <> '{zero}')),
             body AS (SELECT DISTINCT nzbn, view FROM other),
             m AS (SELECT co.ref, co.name_filed, co.charity_number, co.nzbn, co.full_key, co.has_middle, o.view, o.ref AS oref,
                          o.name_filed AS oname, o.full_key AS ofull, o.has_middle AS omid,
                          count(*) OVER (PARTITION BY co.ref, o.view) AS same
                   FROM co JOIN other o ON o.nzbn = co.nzbn AND o.fl_key = co.fl_key)
        SELECT 'totals', NULL::text, (SELECT count(*) FROM co), (SELECT count(*) FROM co WHERE nzbn IS NOT NULL AND nzbn <> '{zero}'),
               NULL::bigint, NULL::bigint, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::text, NULL::bigint
        UNION ALL
        SELECT 'body', b.view, count(DISTINCT co.ref), NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
        FROM co JOIN body b ON b.nzbn = co.nzbn GROUP BY b.view
        UNION ALL
        SELECT 'pair', m.view, NULL, NULL, m.same, (SELECT count(*) FROM pub.links l WHERE (l.row_a = m.ref AND l.row_b = m.oref)
                                                    OR (l.row_a = m.oref AND l.row_b = m.ref)),
               (SELECT string_agg(DISTINCT l.grade || ':' || l.rule, ',') FROM pub.links l WHERE (l.row_a = m.ref AND l.row_b = m.oref)
                                                    OR (l.row_a = m.oref AND l.row_b = m.ref)),
               m.ref, m.oref, m.name_filed, m.oname, m.charity_number, m.nzbn,
               CASE WHEN m.full_key = m.ofull THEN 'equal' WHEN m.has_middle AND m.omid THEN 'middle names differ' ELSE 'one has no middle name' END,
               NULL
        FROM m""").fetchall()
    out = {"charity_officers": 0, "on_a_charity_with_a_business_number": 0, "on_a_body_with_officers_in": {}, "by_view": {}, "pairs": []}
    pairs = []
    for r in rows:
        if r[0] == "totals":
            out["charity_officers"], out["on_a_charity_with_a_business_number"] = int(r[2]), int(r[3])
        elif r[0] == "body":
            out["on_a_body_with_officers_in"][r[1]] = int(r[2])
        else:
            view, same, linked, grades, ref, oref, name, oname, cnum, nzbn, full = r[1], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13]
            v = out["by_view"].setdefault(view, {"officers_with_one_same_name_officer": set(), "officers_with_several": set(),
                                                  "of_the_one_full_name": {}, "of_the_one_linked_today": {}})
            if same == 1:
                v["officers_with_one_same_name_officer"].add(ref)
                v["of_the_one_full_name"][full] = v["of_the_one_full_name"].get(full, 0) + 1
                g = grades or "none"
                v["of_the_one_linked_today"][g] = v["of_the_one_linked_today"].get(g, 0) + 1
                pairs.append({"view": view, "charity_officer": name, "charity_number": cnum, "other_officer": oname, "body_nzbn": nzbn,
                              "full_name": full, "linked_today": g, "rows": [ref, oref]})
            else:
                v["officers_with_several"].add(ref)
    for v in out["by_view"].values():
        v["officers_with_one_same_name_officer"] = len(v["officers_with_one_same_name_officer"])
        v["officers_with_several"] = len(v["officers_with_several"])
    import hashlib
    pairs.sort(key=lambda p: hashlib.sha256((seed + p["rows"][0] + p["rows"][1]).encode()).hexdigest())
    unlinked = [p for p in pairs if p["linked_today"] == "none" or p["linked_today"].startswith("near")]
    out["unlinked_or_near_of_the_one"] = len(unlinked)
    out["pairs"] = unlinked[:sample]
    out["note"] = ("a charity is the company or society of the same business number (ruling 124); the all-zero number is no number "
                   "(fix-links-6); same name: the first-and-last key of pub.names; a pair already confirmed is counted and not drawn")
    return out


MEASURES = (("1 name repeats", m1_name_repeats), ("2 shared addresses", m2_shared_addresses), ("3 rule error", m3_rule_error),
            ("4 rule reach", m4_rule_reach), ("5 company names", m5_company_names), ("6 group shape", m6_groups),
            ("7 ruling 106", m7_ruling_106), ("8 ruling 107", m8_ruling_107), ("9 ruling 109", m9_ruling_109),
            ("10 ruling 114", m10_ruling_114), ("11 ruling 116", m11_ruling_116), ("12 ruling 125", m12_ruling_125),
            ("13 declared bodies", m13_declared_bodies), ("14 charity officers", m14_charity_officers))


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
