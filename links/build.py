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
  and the candidacy that won it).
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
        WHERE r.kind = 'organisation' AND r.register IN ('party_returns', 'disclosures')
        ON CONFLICT DO NOTHING""", {"rule": rules.RULE_ORG_NAME, "one": rules.NEAR_ORG_NAME + "; one company carries this name",
                                     "many": rules.NEAR_ORG_NAME + "; several companies carry this name"})
    out[rules.RULE_ORG_NAME] = conn.execute(f"SELECT count(*) FROM {s}.links WHERE rule = %s", (rules.RULE_ORG_NAME,)).fetchone()[0]
    log(f"links.build: {rules.RULE_ORG_NAME}: {out[rules.RULE_ORG_NAME]} ({time.monotonic() - t0:.0f} s)")
    conn.commit()
    # near: every other shared first and last name, one star per name over the confirmed components
    out[rules.RULE_NAME_ONLY] = near_links(conn, s, log, reader=reader)
    conn.commit()
    conn.execute(f"ANALYZE {s}.links")
    conn.commit()
    out["seconds"] = round(time.monotonic() - t0, 1)
    return out


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
    appointments' registered offices sit in different postcode regions) and
    a very common name. A bankruptcy on one row, and donor addresses far
    apart, wait on registers not yet published."""
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
        FROM {s}.links l
        JOIN {s}.rows a ON a.ref = l.row_a
        LEFT JOIN {s}.row_regions ra ON ra.ref = l.row_a
        LEFT JOIN {s}.row_regions rb ON rb.ref = l.row_b
        LEFT JOIN {s}.name_counts nc ON nc.fl_key = a.fl_key
        WHERE l.grade = 'confirmed' AND l.rule IN (%s, %s)""", (rules.RULE_FULL, rules.RULE_ADDRESS))
    conn.commit()
    row = conn.execute(f"""SELECT count(*), count(*) FILTER (WHERE flags <> '[]'::jsonb),
                                  count(*) FILTER (WHERE flags::text LIKE '%%regions-apart%%'),
                                  count(*) FILTER (WHERE flags::text LIKE '%%very-common-name%%') FROM {s}.watch""").fetchone()
    out = {"watched": row[0], "flagged": row[1], "regions_apart": row[2], "very_common_name": row[3],
           "not_available": ["bankruptcy-conflict: no bankruptcy register is published yet",
                             "donor-addresses-apart: no donor address is published"],
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
