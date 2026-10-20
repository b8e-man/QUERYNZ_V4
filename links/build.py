"""Build the links, the groups and the watch from `links.rows` (plan 4.2).

    python -m links.build [--schema scratch_links] [--links] [--groups] [--watch]

Links are stored as a star inside each component a rule makes: every row
joined to the component's smallest key. Each stored pair satisfies the
rule on its own, and the table is bounded by the rows rather than by the
pairs (a name carried by 300 rows would otherwise be 44,850 links).

- `full-name@1` (rule 1): rows with the same full name key and a middle
  name, one star per full name.
- `name-and-address@1` (rule 2): rows with the same first and last name
  whose companies filed the same registered office, one star per name and
  address; a busy address (more than HUB_FLOOR companies) does not count.
- `source-identifier@1`: a lane's own join between two of its rows (a seat
  and the candidacy that won it; the filing candidate on a candidate return
  and on the amendment that replaces it).
- `official-number@1`: a company shareholder's NZBN to the company; a
  liquidation notice's company number to the company.
- `organisation-name@1`: a donation row's organisation name to the
  companies carrying it, near (the row has no official number).
- `name-only@1`: every other shared first and last name, near, with the
  reason; one star per name over the confirmed components.

Groups follow confirmed links and `same` decisions (setting `chain`);
a `not the same` or `contested` decision takes its pair's link out of the
walk; a group whose walk still joins two rows a decision says are not the
same contradicts itself and is contested as a whole (setting
`contested_group`), as is any group the watch flags.

Work tables (`address_counts`, `name_at_address`, `row_regions`,
`name_counts`) are regenerable and are emptied and refilled, never dropped.
"""
from __future__ import annotations

import json
import sys
import time

import links
from links import rules

RULE_SOURCE = "source-identifier@1"
WATCH_COMMON_FLOOR = 50       # a first-and-last name carried by more than this many director rows is very common

WORK_DDL = """
CREATE TABLE IF NOT EXISTS {s}.address_counts (address_key text PRIMARY KEY, n integer NOT NULL);
CREATE TABLE IF NOT EXISTS {s}.name_at_address (ref text, fl_key text, full_key text, has_middle boolean, name_filed text,
    register text, address_key text, companies_at integer);
CREATE INDEX IF NOT EXISTS name_at_address_keys ON {s}.name_at_address (fl_key, address_key);
CREATE INDEX IF NOT EXISTS name_at_address_ref ON {s}.name_at_address (ref);
CREATE TABLE IF NOT EXISTS {s}.row_regions (ref text PRIMARY KEY, regions text[]);
CREATE TABLE IF NOT EXISTS {s}.name_counts (fl_key text PRIMARY KEY, n integer NOT NULL);
"""


def work_tables(conn, s: str) -> None:
    conn.execute(WORK_DDL.format(s=s))


def hub_table(conn, s: str) -> None:
    conn.execute(f"DELETE FROM {s}.address_counts")
    conn.execute(f"""INSERT INTO {s}.address_counts (address_key, n)
                     SELECT address_key, count(DISTINCT entity_ref) FROM {s}.entity_addresses GROUP BY 1""")
    conn.execute(f"ANALYZE {s}.address_counts")


def build_links(conn, s: str, log=print, reader=None) -> dict:
    t0 = time.monotonic()
    out = {}
    work_tables(conn, s)
    conn.execute(f"DELETE FROM {s}.links")
    conn.execute(f"ALTER SEQUENCE {s}.links_link_id_seq RESTART WITH 1")
    hub_table(conn, s)
    # rule 1: the full name with a middle name
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least(m.ref, r.ref), greatest(m.ref, r.ref), %(rule)s,
               jsonb_build_object('full_name', r.full_key, 'middle', r.middle, 'as_filed', jsonb_build_array(m.name_filed, r.name_filed),
                                  'registers', jsonb_build_array(m.register, r.register)),
               'confirmed', NULL
        FROM {s}.rows r
        JOIN (SELECT full_key, min(ref) AS ref FROM {s}.rows
              WHERE kind = 'person' AND has_middle AND NOT politician GROUP BY full_key HAVING count(*) > 1) k ON k.full_key = r.full_key
        JOIN {s}.rows m ON m.ref = k.ref
        WHERE r.kind = 'person' AND r.has_middle AND NOT r.politician AND r.ref <> k.ref""", {"rule": rules.RULE_FULL})
    out[rules.RULE_FULL] = conn.execute(f"SELECT count(*) FROM {s}.links WHERE rule = %s", (rules.RULE_FULL,)).fetchone()[0]
    log(f"links.build: {rules.RULE_FULL}: {out[rules.RULE_FULL]} ({time.monotonic() - t0:.0f} s)")
    # rule 2: first and last name at the same quiet registered office; middle names must not differ
    conn.execute(f"DELETE FROM {s}.name_at_address")
    conn.execute(f"""
        INSERT INTO {s}.name_at_address
        SELECT r.ref, r.fl_key, r.full_key, r.has_middle, r.name_filed, r.register, a.address_key, c.n
        FROM {s}.rows r
        JOIN {s}.entity_addresses a ON a.entity_ref = r.entity_ref
        JOIN {s}.address_counts c ON c.address_key = a.address_key
        WHERE r.kind = 'person' AND NOT r.politician AND r.fl_key IS NOT NULL AND c.n <= {rules.HUB_FLOOR}""")
    conn.execute(f"ANALYZE {s}.name_at_address")
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT DISTINCT ON (least(m.ref, r.ref), greatest(m.ref, r.ref))
               least(m.ref, r.ref), greatest(m.ref, r.ref), %(rule)s,
               jsonb_build_object('first_last', r.fl_key, 'shared_address', r.address_key, 'companies_at_address', r.companies_at,
                                  'as_filed', jsonb_build_array(m.name_filed, r.name_filed), 'registers', jsonb_build_array(m.register, r.register)),
               'confirmed', NULL
        FROM {s}.name_at_address r
        JOIN (SELECT fl_key, address_key, min(ref) AS ref FROM {s}.name_at_address GROUP BY 1, 2 HAVING count(DISTINCT ref) > 1) k
             ON k.fl_key = r.fl_key AND k.address_key = r.address_key
        JOIN {s}.name_at_address m ON m.ref = k.ref AND m.address_key = k.address_key
        WHERE r.ref <> k.ref
          AND NOT (r.has_middle AND m.has_middle AND r.full_key <> m.full_key)
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_ADDRESS})
    out[rules.RULE_ADDRESS] = conn.execute(f"SELECT count(*) FROM {s}.links WHERE rule = %s", (rules.RULE_ADDRESS,)).fetchone()[0]
    log(f"links.build: {rules.RULE_ADDRESS}: {out[rules.RULE_ADDRESS]} ({time.monotonic() - t0:.0f} s)")
    # the lane's own join: a seat and the candidacy that won it
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least('house:' || m.key, 'house:' || m.candidate), greatest('house:' || m.key, 'house:' || m.candidate), %(rule)s,
               jsonb_build_object('join', 'pub.members.candidate', 'election', m.election, 'electorate', m.electorate),
               'confirmed', NULL
        FROM pub.members m JOIN pub.candidates c ON c.key = m.candidate
        ON CONFLICT DO NOTHING""", {"rule": RULE_SOURCE})
    # the lane's own join: the filing candidate on an original candidate return and on the amendment the Commission says replaces it
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least('candidate_returns:' || o.key, 'candidate_returns:' || n.key), greatest('candidate_returns:' || o.key, 'candidate_returns:' || n.key), %(rule)s,
               jsonb_build_object('join', 'pub.candidate_return_totals.replaced_by', 'year', o.year, 'electorate', o.electorate,
                                  'as_filed', jsonb_build_array(a.name_filed, b.name_filed), 'registers', jsonb_build_array('candidate_returns', 'candidate_returns')),
               'confirmed', NULL
        FROM pub.candidate_return_totals o JOIN pub.candidate_return_totals n ON n.key = o.replaced_by || '/declaration'
        JOIN {s}.rows a ON a.ref = 'candidate_returns:' || o.key JOIN {s}.rows b ON b.ref = 'candidate_returns:' || n.key
        WHERE o.replaced_by IS NOT NULL
        ON CONFLICT DO NOTHING""", {"rule": RULE_SOURCE})
    out[RULE_SOURCE] = conn.execute(f"SELECT count(*) FROM {s}.links WHERE rule = %s", (RULE_SOURCE,)).fetchone()[0]
    # the number is the link
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least('companies:' || sh.key, 'companies:' || c.key), greatest('companies:' || sh.key, 'companies:' || c.key), %(rule)s,
               jsonb_build_object('number', 'NZBN', 'value', sh.holder_nzbn, 'holder', sh.name, 'company', c.name), 'confirmed', NULL
        FROM pub.shareholders sh JOIN pub.companies c ON c.nzbn = sh.holder_nzbn
        WHERE sh.shareholder_type = 'company' AND sh.holder_nzbn IS NOT NULL AND sh.holder_nzbn <> ''
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_NUMBER})
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least('gazette:' || l.key, 'companies:' || c.key), greatest('gazette:' || l.key, 'companies:' || c.key), %(rule)s,
               jsonb_build_object('number', 'company number', 'value', l.company_number, 'notice', l.notice, 'company', c.name), 'confirmed', NULL
        FROM pub.gazette_liquidations l JOIN pub.companies c ON c.number = l.company_number AND c.register = 'companies'
        WHERE l.company_number IS NOT NULL AND l.company_number <> ''
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_NUMBER})
    out[rules.RULE_NUMBER] = conn.execute(f"SELECT count(*) FROM {s}.links WHERE rule = %s", (rules.RULE_NUMBER,)).fetchone()[0]
    log(f"links.build: {rules.RULE_NUMBER}: {out[rules.RULE_NUMBER]} ({time.monotonic() - t0:.0f} s)")
    # an organisation donor's name to the companies carrying it: near, with whether each was alive on the date
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least(r.ref, o.entity_ref), greatest(r.ref, o.entity_ref), %(rule)s,
               jsonb_build_object('name', r.name_filed, 'organisation_key', r.name_key, 'date', r.started_on,
                                  'alive_on_date', (o.registered_on IS NULL OR o.registered_on <= coalesce(r.ended_on, r.started_on, current_date))
                                                   AND (o.removed_on IS NULL OR o.removed_on >= coalesce(r.started_on, current_date)),
                                  'companies_of_that_name', o.n),
               'near', CASE WHEN o.n = 1 THEN %(one)s ELSE %(many)s END
        FROM {s}.rows r
        JOIN (SELECT n.org_key, n.entity_ref, n.registered_on, n.removed_on, count(*) OVER (PARTITION BY n.org_key) AS n
              FROM {s}.org_names n) o ON o.org_key = r.name_key
        WHERE r.kind = 'organisation' AND r.register IN ('party_returns', 'candidate_returns', 'disclosures', 'mp_interests')
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_ORG_NAME, "one": rules.NEAR_ORG_NAME + "; one company carries this name",
                                     "many": rules.NEAR_ORG_NAME + "; several companies carry this name"})
    out[rules.RULE_ORG_NAME] = conn.execute(f"SELECT count(*) FROM {s}.links WHERE rule = %s", (rules.RULE_ORG_NAME,)).fetchone()[0]
    log(f"links.build: {rules.RULE_ORG_NAME}: {out[rules.RULE_ORG_NAME]} ({time.monotonic() - t0:.0f} s)")
    conn.commit()
    # the rules of links-2: the House's own rows to their seats; declared interests to companies and the member's own directorships;
    # the donation registers' named circumstances; companies under one name; one candidate under two printings
    for name, step in ((rules.RULE_SEAT, seat_links), (rules.RULE_DECLARED, declared_links), ("donor rules", donor_links),
                       (rules.RULE_COMPANY_NAME, company_name_links), (rules.RULE_NAME_FORM, name_form_links)):
        out[name] = step(conn, s)
        log(f"links.build: {name}: {out[name]} ({time.monotonic() - t0:.0f} s)")
    out[rules.RULE_NUMBER] = conn.execute(f"SELECT count(*) FROM {s}.links WHERE rule = %s", (rules.RULE_NUMBER,)).fetchone()[0]
    # near: every other shared first and last name, one star per name over the confirmed components
    out[rules.RULE_NAME_ONLY] = near_links(conn, s, log, reader=reader)
    conn.commit()
    conn.execute(f"ANALYZE {s}.links")
    conn.commit()
    out["seconds"] = round(time.monotonic() - t0, 1)
    return out


#: an electorate name as the House and the Commission print it, folded for equality (macrons to plain letters, letters only)
_PLACE = "lower(regexp_replace(translate(coalesce({x}, ''), 'āēīōūĀĒĪŌŪ', 'aeiouAEIOU'), '[^A-Za-z]', '', 'g'))"


def _count(conn, s: str, rule: str) -> int:
    return conn.execute(f"SELECT count(*) FROM {s}.links WHERE rule = %s", (rule,)).fetchone()[0]


def seat_links(conn, s: str) -> dict:
    """`seat-and-window@1`: a row the House publishes about a sitting member
    (an interests return, an expense line) joined to the seat whose term
    covers the row's date, under the same first and last name, the
    electorate agreeing where the row prints one ('List' to a list seat).
    Confirmed when every seat that fits is one member: one party, and no
    two middle names (the seats before and after an election are one
    person's, under either printing of the name); near with the reason
    when two members of the name sat in the window. Middle names that
    differ on both rows take the pair out."""
    conn.execute(f"""
        CREATE TEMP TABLE seat_fit ON COMMIT DROP AS
        WITH seat AS (
            SELECT r.ref, r.fl_key, r.full_key, r.has_middle, r.name_key, m.key AS seat_key, m.from_on, coalesce(m.ended_on, m.to_by) AS to_on,
                   m.route, e.name AS electorate_name, m.party_registered, m.election
            FROM {s}.rows r JOIN pub.members m ON r.ref = 'house:' || m.key LEFT JOIN pub.electorates e ON e.key = m.electorate
            WHERE r.view = 'members' AND r.fl_key IS NOT NULL),
        published AS (
            SELECT r.ref, r.view, r.fl_key, r.full_key, r.has_middle, r.name_filed, r.started_on, coalesce(r.ended_on, r.started_on) AS ended_on,
                   x.electorate
            FROM {s}.rows r LEFT JOIN pub.mp_interest_returns x ON r.view = 'mp_interest_returns' AND r.ref = 'mp_interests:' || x.key
            WHERE r.view IN ('mp_interest_returns', 'mp_expenses', 'minister_expenses') AND r.fl_key IS NOT NULL AND r.started_on IS NOT NULL)
        SELECT p.ref AS row_ref, p.view, p.name_filed, p.started_on, p.ended_on, p.electorate AS printed_electorate,
               t.ref AS seat_ref, t.seat_key, t.name_key, t.full_key, t.has_middle, t.party_registered, t.route, t.electorate_name, t.from_on, t.to_on, t.election
        FROM published p JOIN seat t ON t.fl_key = p.fl_key
         AND p.started_on <= coalesce(t.to_on, 'infinity'::date) AND p.ended_on >= t.from_on
         AND NOT (t.has_middle AND p.has_middle AND t.full_key <> p.full_key)
         AND (p.electorate IS NULL OR (lower(p.electorate) = 'list' AND t.route = 'list')
              OR {_PLACE.format(x='p.electorate')} = {_PLACE.format(x='t.electorate_name')})""")
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least(f.row_ref, f.seat_ref), greatest(f.row_ref, f.seat_ref), %(rule)s,
               jsonb_build_object('seat', f.seat_key, 'election', f.election, 'route', f.route, 'electorate', f.electorate_name,
                                  'term', jsonb_build_array(f.from_on, f.to_on), 'row', f.view, 'dated', jsonb_build_array(f.started_on, f.ended_on),
                                  'printed_electorate', f.printed_electorate, 'as_filed', f.name_filed, 'members_fitting', u.members,
                                  'registers', jsonb_build_array(split_part(f.row_ref, ':', 1), 'house')),
               CASE WHEN u.members = 1 THEN 'confirmed' ELSE 'near' END,
               CASE WHEN u.members = 1 THEN NULL ELSE %(ambiguous)s END
        FROM seat_fit f
        JOIN (SELECT row_ref, count(DISTINCT party_registered) + (count(DISTINCT full_key) FILTER (WHERE has_middle) > 1)::int AS members
              FROM seat_fit GROUP BY 1) u ON u.row_ref = f.row_ref
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_SEAT, "ambiguous": rules.NEAR_SEAT_AMBIGUOUS})
    conn.commit()
    row = conn.execute(f"""SELECT count(*), count(*) FILTER (WHERE grade = 'confirmed'),
                                  count(DISTINCT row_a) FILTER (WHERE grade = 'confirmed' AND split_part(row_a, ':', 1) <> 'house')
                                  + count(DISTINCT row_b) FILTER (WHERE grade = 'confirmed' AND split_part(row_b, ':', 1) <> 'house')
                           FROM {s}.links WHERE rule = %s""", (rules.RULE_SEAT,)).fetchone()
    unjoined = conn.execute(f"""SELECT view, count(*) FROM {s}.rows r WHERE view IN ('mp_interest_returns', 'mp_expenses', 'minister_expenses')
                                AND NOT EXISTS (SELECT 1 FROM {s}.links l WHERE l.rule = %s AND (l.row_a = r.ref OR l.row_b = r.ref)) GROUP BY 1""",
                            (rules.RULE_SEAT,)).fetchall()
    return {"links": int(row[0]), "confirmed": int(row[1]), "near_ambiguous": int(row[0] - row[1]), "rows_joined": int(row[2]),
            "rows_no_seat_fits": {v: int(n) for v, n in unjoined}}


def declared_links(conn, s: str) -> dict:
    """A member's declared interests anchored to the companies register.
    `official-number@1` where the declaration prints the company number in
    brackets; otherwise `organisation-name@1` (near, with whether exactly
    one company of the name was alive on the declaration date) is made by
    the organisation-name step. Then `declared-directorship@1`: the member's
    return and a director row of the member's name on a company the member
    declared, confirmed (design: a politician's name on the director
    register counts with a company that person declared); near when two
    directors of that name sit on the declared company."""
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least(r.ref, 'companies:' || c.key), greatest(r.ref, 'companies:' || c.key), %(rule)s,
               jsonb_build_object('number', 'company number', 'value', c.number, 'declared', r.name_filed, 'company', c.name,
                                  'registers', jsonb_build_array('mp_interests', 'companies')), 'confirmed', NULL
        FROM {s}.rows r JOIN pub.mp_interests i ON r.ref = 'mp_interests:' || i.key
        JOIN pub.companies c ON c.number = substring(i.text FROM '\\((\\d{{5,8}})\\)') AND c.register = 'companies'
        WHERE r.view = 'mp_interests'
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_NUMBER})
    numbered = conn.execute(f"SELECT count(*) FROM {s}.links WHERE rule = %s AND evidence->>'declared' IS NOT NULL", (rules.RULE_NUMBER,)).fetchone()[0]
    conn.execute(f"""
        CREATE TEMP TABLE declared_company ON COMMIT DROP AS
        SELECT i.ref AS declared_ref, i.entity_ref AS return_ref, i.name_filed AS declared, i.started_on AS as_at, o.entity_ref AS company_ref,
               count(*) OVER (PARTITION BY i.ref) AS companies_alive
        FROM {s}.rows i JOIN {s}.org_names o ON o.org_key = i.name_key
        WHERE i.view = 'mp_interests' AND i.kind = 'organisation'
          AND (o.registered_on IS NULL OR o.registered_on <= i.started_on) AND (o.removed_on IS NULL OR o.removed_on >= i.started_on)
        UNION
        SELECT least(l.row_a, l.row_b), i.entity_ref, i.name_filed, i.started_on, greatest(l.row_a, l.row_b), 1
        FROM {s}.links l JOIN {s}.rows i ON i.ref = least(l.row_a, l.row_b) AND i.view = 'mp_interests'
        WHERE l.rule = %(number)s""", {"number": rules.RULE_NUMBER})
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT DISTINCT ON (least(m.ref, d.ref), greatest(m.ref, d.ref))
               least(m.ref, d.ref), greatest(m.ref, d.ref), %(rule)s,
               jsonb_build_object('declared', dc.declared, 'declaration', dc.declared_ref, 'as_at', dc.as_at, 'company', dc.company_ref,
                                  'directors_of_this_name_on_it', n.names, 'role', jsonb_build_array(d.started_on, d.ended_on),
                                  'as_filed', jsonb_build_array(m.name_filed, d.name_filed), 'registers', jsonb_build_array('mp_interests', 'companies')),
               CASE WHEN n.names = 1 THEN 'confirmed' ELSE 'near' END, CASE WHEN n.names = 1 THEN NULL ELSE %(two)s END
        FROM declared_company dc
        JOIN {s}.rows m ON m.ref = dc.return_ref AND m.fl_key IS NOT NULL
        JOIN {s}.rows d ON d.entity_ref = dc.company_ref AND d.view = 'directors' AND d.fl_key = m.fl_key
        JOIN (SELECT d2.entity_ref, d2.fl_key, count(DISTINCT CASE WHEN d2.has_middle THEN d2.full_key END) + (count(*) FILTER (WHERE NOT d2.has_middle) > 0)::int AS names
              FROM {s}.rows d2 WHERE d2.view = 'directors' GROUP BY 1, 2) n ON n.entity_ref = d.entity_ref AND n.fl_key = d.fl_key
        WHERE dc.companies_alive = 1 AND NOT (m.has_middle AND d.has_middle AND m.full_key <> d.full_key)
        ORDER BY least(m.ref, d.ref), greatest(m.ref, d.ref), d.started_on DESC NULLS LAST
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_DECLARED, "two": rules.NEAR_DECLARED_TWO})
    conn.commit()
    row = conn.execute(f"""SELECT count(*), count(*) FILTER (WHERE grade = 'confirmed'), count(DISTINCT least(row_a, row_b)) FILTER (WHERE grade = 'confirmed')
                           FROM {s}.links WHERE rule = %s""", (rules.RULE_DECLARED,)).fetchone()
    return {"declarations_with_a_company_number": int(numbered), "links": int(row[0]), "confirmed": int(row[1]), "near_two_directors": int(row[0] - row[1]),
            "returns_joined_to_a_directorship": int(row[2])}


def donor_links(conn, s: str) -> dict:
    """Three near rules on the donation registers, each naming its evidence.
    `filed-name@1`: donation rows filed under one organisation name, one
    star per name across party returns, candidate returns and declarations.
    `own-return@1`: a donor row on a candidate's own return in the
    candidate's name. `member-and-party-donor@1`: a member's name on a donor
    row (a party return's Part A, a declaration) to the member's own party,
    dated in the term. Every one is near: the rows name a circumstance,
    and whether any may confirm is Arthur's (the decision queue)."""
    out = {}
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least(m.ref, r.ref), greatest(m.ref, r.ref), %(rule)s,
               jsonb_build_object('name_key', r.name_key, 'as_filed', jsonb_build_array(m.name_filed, r.name_filed),
                                  'same_party', m.entity_ref = r.entity_ref, 'dated', jsonb_build_array(m.started_on, r.started_on),
                                  'registers', jsonb_build_array(m.register, r.register)),
               'near', %(reason)s
        FROM {s}.rows r
        JOIN (SELECT name_key, min(ref) AS ref FROM {s}.rows WHERE kind IN ('organisation', 'estate')
              AND register IN ('party_returns', 'candidate_returns', 'disclosures') GROUP BY 1 HAVING count(*) > 1) k ON k.name_key = r.name_key
        JOIN {s}.rows m ON m.ref = k.ref
        WHERE r.kind IN ('organisation', 'estate') AND r.register IN ('party_returns', 'candidate_returns', 'disclosures') AND r.ref <> k.ref
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_FILED_NAME, "reason": rules.NEAR_FILED_NAME})
    out[rules.RULE_FILED_NAME] = _count(conn, s, rules.RULE_FILED_NAME)
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least(d.ref, c.ref), greatest(d.ref, c.ref), %(rule)s,
               jsonb_build_object('return', c.ref, 'election', c.election, 'electorate', c.electorate,
                                  'as_filed', jsonb_build_array(d.name_filed, c.name_filed), 'registers', jsonb_build_array('candidate_returns', 'candidate_returns')),
               'near', %(reason)s
        FROM {s}.rows d JOIN {s}.rows c ON c.ref = d.entity_ref AND c.view = 'candidate_return_totals' AND c.fl_key = d.fl_key
        WHERE d.view = 'candidate_return_donors' AND d.kind = 'person' AND NOT (d.has_middle AND c.has_middle AND d.full_key <> c.full_key)
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_OWN_RETURN, "reason": rules.NEAR_OWN_RETURN})
    out[rules.RULE_OWN_RETURN] = _count(conn, s, rules.RULE_OWN_RETURN)
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT DISTINCT ON (least(d.ref, p.ref), greatest(d.ref, p.ref))
               least(d.ref, p.ref), greatest(d.ref, p.ref), %(rule)s,
               jsonb_build_object('party', coalesce(pr.party, ds.party), 'year', coalesce(pr.year, extract(year FROM ds.given_on)::int),
                                  'politician', p.view, 'election', p.election, 'term', jsonb_build_array(p.started_on, p.ended_on),
                                  'as_filed', jsonb_build_array(d.name_filed, p.name_filed), 'registers', jsonb_build_array(d.register, 'house')),
               'near', %(reason)s
        FROM {s}.rows d
        LEFT JOIN pub.party_return_donors pr ON d.ref = 'party_returns:' || pr.key
        LEFT JOIN pub.disclosures ds ON d.ref = 'disclosures:' || ds.key
        JOIN {s}.rows p ON p.view = 'members' AND p.fl_key = d.fl_key
        JOIN pub.members m ON p.ref = 'house:' || m.key AND m.party_registered = coalesce(pr.party, ds.party) AND m.party_registered <> ''
             AND d.started_on <= coalesce(m.ended_on, m.to_by, 'infinity'::date) AND coalesce(d.ended_on, d.started_on) >= m.from_on
        WHERE d.kind = 'person' AND d.register IN ('party_returns', 'disclosures') AND NOT (d.has_middle AND p.has_middle AND d.full_key <> p.full_key)
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_PARTY_DONOR, "reason": rules.NEAR_PARTY_DONOR})
    out[rules.RULE_PARTY_DONOR] = _count(conn, s, rules.RULE_PARTY_DONOR)
    conn.commit()
    return out


def company_name_links(conn, s: str) -> dict:
    """`company-name@1`, near: companies under one name, one star per name;
    and under one name apart from a year in brackets, one star per bare
    name. The number is the only confirmation of a company."""
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least(m.entity_ref, o.entity_ref), greatest(m.entity_ref, o.entity_ref), %(rule)s,
               jsonb_build_object('name_key', o.org_key, 'registered', jsonb_build_array(m.registered_on, o.registered_on),
                                  'removed', jsonb_build_array(m.removed_on, o.removed_on),
                                  'alive_together', coalesce(m.removed_on, 'infinity') >= coalesce(o.registered_on, '-infinity')
                                                AND coalesce(o.removed_on, 'infinity') >= coalesce(m.registered_on, '-infinity'),
                                  'companies_of_this_name', k.n, 'registers', jsonb_build_array('companies', 'companies')),
               'near', %(reason)s
        FROM {s}.org_names o
        JOIN (SELECT org_key, min(entity_ref) AS entity_ref, count(*) AS n FROM {s}.org_names GROUP BY 1 HAVING count(*) > 1) k ON k.org_key = o.org_key
        JOIN {s}.org_names m ON m.entity_ref = k.entity_ref AND m.org_key = k.org_key
        WHERE o.entity_ref <> k.entity_ref
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_COMPANY_NAME, "reason": rules.NEAR_COMPANY_SAME})
    same = _count(conn, s, rules.RULE_COMPANY_NAME)
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least(m.entity_ref, o.entity_ref), greatest(m.entity_ref, o.entity_ref), %(rule)s,
               jsonb_build_object('name_key', o.bare, 'as_keyed', jsonb_build_array(m.org_key, o.org_key),
                                  'registered', jsonb_build_array(m.registered_on, o.registered_on), 'removed', jsonb_build_array(m.removed_on, o.removed_on),
                                  'registers', jsonb_build_array('companies', 'companies')),
               'near', %(reason)s
        FROM (SELECT entity_ref, org_key, registered_on, removed_on, trim(regexp_replace(org_key, '\\s*\\(\\d{{4}}\\)\\s*', ' ', 'g')) AS bare
              FROM {s}.org_names WHERE org_key ~ '\\(\\d{{4}}\\)') o
        JOIN (SELECT org_key, min(entity_ref) AS entity_ref FROM {s}.org_names GROUP BY 1) k ON k.org_key = o.bare
        JOIN {s}.org_names m ON m.entity_ref = k.entity_ref AND m.org_key = k.org_key
        WHERE o.bare <> '' AND o.bare <> o.org_key
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_COMPANY_NAME, "reason": rules.NEAR_COMPANY_YEAR})
    conn.commit()
    total = _count(conn, s, rules.RULE_COMPANY_NAME)
    return {"same_name": int(same), "same_name_apart_from_a_year": int(total - same), "links": int(total)}


def name_form_links(conn, s: str) -> dict:
    """`candidate-name-form@1`, near: the House rows (candidacies, seats) of
    one first and last name for one party across different elections, where
    the printings differ (a middle name on one printing only, or none on
    either), one star per name and party. A pair whose two printings both
    carry middle names that differ is left out: those are two names."""
    conn.execute(f"""
        INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason)
        SELECT least(m.ref, r.ref), greatest(m.ref, r.ref), %(rule)s,
               jsonb_build_object('party', r.party, 'elections', jsonb_build_array(m.election, r.election),
                                  'electorates', jsonb_build_array(m.electorate, r.electorate), 'as_filed', jsonb_build_array(m.name_filed, r.name_filed),
                                  'same_printing', m.name_key = r.name_key, 'registers', jsonb_build_array('house', 'house'))
               , 'near', %(reason)s
        FROM (SELECT x.*, coalesce(c.party_registered, mm.party_registered) AS party FROM {s}.rows x
              LEFT JOIN pub.candidates c ON x.view = 'candidates' AND x.ref = 'house:' || c.key
              LEFT JOIN pub.members mm ON x.view = 'members' AND x.ref = 'house:' || mm.key
              WHERE x.view IN ('candidates', 'members') AND x.fl_key IS NOT NULL) r
        JOIN (SELECT fl_key, party, min(ref) AS ref FROM (SELECT x.fl_key, coalesce(c.party_registered, mm.party_registered) AS party, x.ref, x.election
                                                           FROM {s}.rows x
                                                           LEFT JOIN pub.candidates c ON x.view = 'candidates' AND x.ref = 'house:' || c.key
                                                           LEFT JOIN pub.members mm ON x.view = 'members' AND x.ref = 'house:' || mm.key
                                                           WHERE x.view IN ('candidates', 'members') AND x.fl_key IS NOT NULL) y
              WHERE party IS NOT NULL AND party <> '' GROUP BY 1, 2 HAVING count(DISTINCT election) > 1) k ON k.fl_key = r.fl_key AND k.party = r.party
        JOIN {s}.rows m ON m.ref = k.ref
        WHERE r.ref <> k.ref AND r.election <> m.election AND NOT (m.has_middle AND r.has_middle AND m.full_key <> r.full_key)
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_NAME_FORM, "reason": rules.NEAR_NAME_FORM})
    conn.commit()
    row = conn.execute(f"""SELECT count(*), count(*) FILTER (WHERE (evidence->>'same_printing')::boolean) FROM {s}.links WHERE rule = %s""",
                       (rules.RULE_NAME_FORM,)).fetchone()
    return {"links": int(row[0]), "same_printing": int(row[1]), "different_printing": int(row[0] - row[1])}


def components(conn, s: str) -> tuple:
    """(ref → component anchor (the smallest ref), the last decision per pair)
    over confirmed links and `same` decisions, minus the pairs a decision
    takes out. Union-find in memory."""
    parent: dict = {}

    def find(x):
        root = x
        while parent.get(root, root) != root:
            root = parent[root]
        while parent.get(x, x) != root:
            parent[x], x = root, parent[x]
        return root

    def union(a, b):
        parent.setdefault(a, a)      # every row seen is a node, the roots included
        parent.setdefault(b, b)
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if ra < rb:
            parent[rb] = ra
        else:
            parent[ra] = rb

    last: dict = {}     # the last decision on a pair is the verdict
    for a, b, v in conn.execute(f"SELECT row_a, row_b, verdict FROM {s}.decisions ORDER BY decision_id").fetchall():
        last[(a, b)] = v
    with conn.cursor(name="links_components") as cur:
        cur.itersize = 50000
        cur.execute(f"SELECT row_a, row_b FROM {s}.links WHERE grade = 'confirmed'")
        for a, b in cur:
            if last.get((a, b)) in ("not the same", "contested"):
                continue
            union(a, b)
    for (a, b), v in last.items():
        if v == "same":
            union(a, b)
    return {x: find(x) for x in list(parent)}, last


def near_links(conn, s: str, log=print, reader=None) -> int:
    """One star of near links per first-and-last name, between the confirmed
    components it spans (their anchors), with the reason for each pair. The
    names are read through `reader`, a second connection (lesson: a
    server-side cursor and writes should not share one connection)."""
    comp, _ = components(conn, s)
    n = 0
    t0 = time.monotonic()
    reader = reader or conn
    with reader.cursor(name="links_near_names") as cur:
        cur.itersize = 20000
        cur.execute(f"""SELECT fl_key, array_agg(ref ORDER BY ref), array_agg(full_key ORDER BY ref), array_agg(has_middle ORDER BY ref),
                               array_agg(middle ORDER BY ref), array_agg(politician ORDER BY ref), array_agg(name_filed ORDER BY ref),
                               array_agg(register ORDER BY ref)
                        FROM {s}.rows WHERE kind = 'person' AND fl_key IS NOT NULL GROUP BY fl_key HAVING count(*) > 1""")
        with conn.cursor() as w:
            batch = []
            for fl, refs, fulls, mids, middles, pols, filed, regs in cur:
                anchors: dict = {}
                for i, r in enumerate(refs):
                    c = comp.get(r, r)
                    if c not in anchors:
                        anchors[c] = {"ref": r, "fl_key": fl, "full_key": fulls[i], "has_middle": mids[i], "middle": middles[i],
                                      "politician": pols[i], "name_filed": filed[i], "register": regs[i]}
                if len(anchors) < 2:
                    continue
                order = sorted(anchors)
                head = anchors[order[0]]
                for c in order[1:]:
                    other = anchors[c]
                    j = rules.judge(head, other, set(), set(), {})
                    a, b = links.pair(head["ref"], other["ref"])
                    j["evidence"]["registers"] = [head["register"], other["register"]]
                    batch.append((a, b, rules.RULE_NAME_ONLY, json.dumps(j["evidence"]), "near", j["reason"]))
                if len(batch) >= 5000:
                    n += _insert_near(w, s, batch)
                    conn.commit()
                    batch = []
            if batch:
                n += _insert_near(w, s, batch)
                conn.commit()
    log(f"links.build: {rules.RULE_NAME_ONLY}: {n} ({time.monotonic() - t0:.0f} s)")
    return n


def _insert_near(w, s: str, batch: list) -> int:
    w.executemany(f"INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason) VALUES (%s, %s, %s, %s::jsonb, %s, %s) "
                  f"ON CONFLICT DO NOTHING", batch)
    return len(batch)


def build_groups(conn, s: str, log=print) -> dict:
    """Rebuild `<schema>.groups` whole from the confirmed links and the decisions."""
    t0 = time.monotonic()
    comp, last = components(conn, s)
    contradicted = set()
    for (a, b), v in last.items():
        if v == "not the same" and comp.get(a, a) == comp.get(b, b):
            contradicted.add(comp.get(a, a))
    flagged = {r[0] for r in conn.execute(f"""SELECT l.row_a FROM {s}.links l JOIN {s}.watch w ON w.link_id = l.link_id
                                              WHERE w.flags <> '[]'::jsonb""").fetchall()}
    flagged_groups = {comp.get(r, r) for r in flagged}
    contested = contradicted | (flagged_groups if links.SETTINGS["contested_group"] == "whole" else set())
    conn.execute(f"DELETE FROM {s}.groups")
    settings = json.dumps(links.SETTINGS)
    with conn.cursor() as w:
        with w.copy(f"COPY {s}.groups (group_id, row_key, contested, built_at, settings) FROM STDIN") as copy:
            for r, c in comp.items():
                copy.write_row((c, r, c in contested, "now()", settings))
    conn.execute(f"ANALYZE {s}.groups")
    conn.commit()
    sizes: dict = {}
    for c in comp.values():
        sizes[c] = sizes.get(c, 0) + 1
    out = {"rows": len(comp), "groups": len(sizes), "contested": len(contested), "contradicted": len(contradicted),
           "largest": max(sizes.values()) if sizes else 0, "seconds": round(time.monotonic() - t0, 1)}
    log(f"links.build: groups: {out}")
    return out


def build_watch(conn, s: str, log=print) -> dict:
    """The watch over every confirmed name link: regions apart (the current
    appointments' registered offices sit in different postcode regions), a
    very common name, and a bankruptcy on one row with a directorship taken
    up within three years on the other (an undischarged bankrupt may not
    manage a company). Donor addresses far apart wait: no donor address is
    published."""
    t0 = time.monotonic()
    work_tables(conn, s)
    conn.execute(f"DELETE FROM {s}.watch")
    conn.execute(f"DELETE FROM {s}.row_regions")
    conn.execute(f"""INSERT INTO {s}.row_regions (ref, regions)
        SELECT r.ref, array_agg(DISTINCT a.region)
        FROM {s}.rows r JOIN {s}.entity_addresses a ON a.entity_ref = r.entity_ref AND a.in_latest AND a.region IS NOT NULL
        WHERE r.kind = 'person' AND r.ended_on IS NULL GROUP BY r.ref""")
    conn.execute(f"DELETE FROM {s}.name_counts")
    conn.execute(f"""INSERT INTO {s}.name_counts (fl_key, n)
        SELECT fl_key, count(*) FROM {s}.rows WHERE view = 'directors' AND fl_key IS NOT NULL GROUP BY 1""")
    conn.execute(f"ANALYZE {s}.row_regions")
    conn.execute(f"ANALYZE {s}.name_counts")
    conn.execute(f"""
        INSERT INTO {s}.watch (link_id, flags)
        SELECT l.link_id,
               (CASE WHEN ra.regions IS NOT NULL AND rb.regions IS NOT NULL AND NOT (ra.regions && rb.regions)
                     THEN jsonb_build_array(jsonb_build_object('kind', 'regions-apart',
                          'text', 'current appointments sit in different postcode regions',
                          'evidence', jsonb_build_object('a', to_jsonb(ra.regions), 'b', to_jsonb(rb.regions))))
                     ELSE '[]'::jsonb END)
               ||
               (CASE WHEN nc.n > {WATCH_COMMON_FLOOR} AND NOT a.has_middle
                     THEN jsonb_build_array(jsonb_build_object('kind', 'very-common-name',
                          'text', 'a very common first and last name with no middle name filed',
                          'evidence', jsonb_build_object('director_rows_with_this_name', nc.n)))
                     ELSE '[]'::jsonb END)
               ||
               (CASE WHEN (a.view = 'gazette_bankruptcies' AND b.view = 'directors' AND b.started_on > a.started_on
                           AND b.started_on <= a.started_on + interval '3 years')
                        OR (b.view = 'gazette_bankruptcies' AND a.view = 'directors' AND a.started_on > b.started_on
                           AND a.started_on <= b.started_on + interval '3 years')
                     THEN jsonb_build_array(jsonb_build_object('kind', 'bankrupt-yet-appointing',
                          'text', 'a bankruptcy on one row and a directorship taken up within three years of it on the other',
                          'evidence', jsonb_build_object('bankruptcy_on', CASE WHEN a.view = 'gazette_bankruptcies' THEN a.started_on ELSE b.started_on END,
                                                         'appointed_on', CASE WHEN a.view = 'directors' THEN a.started_on ELSE b.started_on END)))
                     ELSE '[]'::jsonb END)
        FROM {s}.links l
        JOIN {s}.rows a ON a.ref = l.row_a
        JOIN {s}.rows b ON b.ref = l.row_b
        LEFT JOIN {s}.row_regions ra ON ra.ref = l.row_a
        LEFT JOIN {s}.row_regions rb ON rb.ref = l.row_b
        LEFT JOIN {s}.name_counts nc ON nc.fl_key = a.fl_key
        WHERE l.grade = 'confirmed' AND l.rule IN (%s, %s)""", (rules.RULE_FULL, rules.RULE_ADDRESS))
    conn.commit()
    row = conn.execute(f"""SELECT count(*), count(*) FILTER (WHERE flags <> '[]'::jsonb),
                                  count(*) FILTER (WHERE flags::text LIKE '%%regions-apart%%'),
                                  count(*) FILTER (WHERE flags::text LIKE '%%very-common-name%%'),
                                  count(*) FILTER (WHERE flags::text LIKE '%%bankrupt-yet-appointing%%') FROM {s}.watch""").fetchone()
    out = {"watched": row[0], "flagged": row[1], "regions_apart": row[2], "very_common_name": row[3], "bankrupt_yet_appointing": row[4],
           "not_available": ["donor-addresses-apart: no donor address is published"],
           "seconds": round(time.monotonic() - t0, 1)}
    log(f"links.build: watch: {out}")
    return out


def build_all(conn, s: str, log=print, reader=None) -> dict:
    out = {"links": build_links(conn, s, log, reader=reader)}
    out["watch"] = build_watch(conn, s, log)
    out["groups"] = build_groups(conn, s, log)
    return out


def main(argv=None) -> int:
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    s = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn, db.connect(db.OWNER_KEY, "querynz_v4") as reader:
        conn.execute("SET statement_timeout = 0")
        reader.execute("SET statement_timeout = 0")
        conn.execute(links.ddl(s))
        conn.commit()
        if "--near" in argv:      # only the near links, over the confirmed ones already built
            conn.execute(f"DELETE FROM {s}.links WHERE rule = %s", (rules.RULE_NAME_ONLY,))
            conn.commit()
            print(json.dumps({rules.RULE_NAME_ONLY: near_links(conn, s, reader=reader)}))
        elif not any(a in argv for a in ("--links", "--groups", "--watch")):
            print(json.dumps(build_all(conn, s, reader=reader)))
        else:
            if "--links" in argv:
                print(json.dumps(build_links(conn, s, reader=reader)))
            if "--watch" in argv:
                print(json.dumps(build_watch(conn, s)))
            if "--groups" in argv:
                print(json.dumps(build_groups(conn, s)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
