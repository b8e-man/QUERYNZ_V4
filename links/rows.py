"""Gather every person row of every published register into `links.rows`,
under the one shared reading of names (keys.names), and every company's
registered office under the one reading of addresses (keys.addresses).
Reads `pub.*` only. No home address: the address arm reads the office of
the company a role sits on, which a company publishes.

    python -m links.rows [--schema scratch_links]

A register is named by its lane folder, as the board names it. The views
read, and what each row's entity is:

| register      | view                 | person name          | entity (`<register>:<key>`) |
| companies     | directors            | full_name            | entity_key          |
| companies     | shareholders         | name (individuals)   | entity_key          |
| societies     | society_officers     | full_name            | society_key         |
| house         | candidates, members  | name (politician)    | -                   |
| party_returns | party_return_donors  | donor                | party (as resolved) |
| disclosures   | disclosures, items   | donor_name, contributor | party            |
| party_finance | promoter_people      | name                 | promoter_key        |
| gazette       | prohibitions, liquidators | name            | -                   |
| mp_interests  | mp_interest_returns  | name (politician)    | -                   |

Expenses are figures under a member's name, not roles; they are not rows here.
"""
from __future__ import annotations

import sys
import time

from keys import addresses as ka
from keys import names as kn

import links

#: (register, view, sql) — each query yields: key, name, entity_key, started_on, ended_on, election, electorate, document, suppressed
SOURCES = (
    ("companies", "directors", """
        SELECT key, full_name AS name, 'companies:' || entity_key, appointed_on AS started_on, ended_on, NULL AS election, NULL AS electorate,
               document, suppressed, first_name, middle_names, last_name
        FROM pub.directors"""),
    ("companies", "shareholders", """
        SELECT key, name, 'companies:' || entity_key, NULL::date AS started_on, NULL::date AS ended_on, NULL, NULL, document, suppressed,
               NULL, NULL, NULL
        FROM pub.shareholders WHERE shareholder_type = 'individual'"""),
    ("societies", "society_officers", """
        SELECT key, full_name AS name, 'societies:' || society_key, started_on, ended_on, NULL, NULL, document, suppressed,
               first_name, middle_names, last_name
        FROM pub.society_officers"""),
    ("house", "candidates", """
        SELECT key, name, NULL, NULL::date, NULL::date, election, electorate, document, false, NULL, NULL, NULL
        FROM pub.candidates"""),
    ("house", "members", """
        SELECT key, name, NULL, from_on, ended_on, election, electorate, document, false, NULL, NULL, NULL
        FROM pub.members"""),
    ("party_returns", "party_return_donors", """
        SELECT key, donor AS name, 'parties:' || party AS entity_key, make_date(year, 1, 1), make_date(year, 12, 31), NULL, NULL,
               document, false, NULL, NULL, NULL
        FROM pub.party_return_donors WHERE donor IS NOT NULL AND donor <> ''"""),
    ("disclosures", "disclosures", """
        SELECT key, donor_name AS name, 'parties:' || party AS entity_key, coalesce(given_on, received_on), NULL::date, NULL, NULL,
               document, false, NULL, NULL, NULL
        FROM pub.disclosures WHERE donor_name IS NOT NULL AND donor_name <> ''"""),
    ("disclosures", "disclosure_items", """
        SELECT i.key, i.contributor AS name, 'disclosures:' || i.declaration AS entity_key, i.first_date, NULL::date, NULL, NULL,
               d.document, false, NULL, NULL, NULL
        FROM pub.disclosure_items i JOIN pub.disclosures d ON d.key = i.declaration
        WHERE i.contributor IS NOT NULL AND i.contributor <> ''"""),
    ("party_finance", "promoter_people", """
        SELECT key, name, 'party_finance:' || promoter_key, make_date(year, 1, 1), NULL::date, NULL, NULL, document, false, NULL, NULL, NULL
        FROM pub.promoter_people WHERE name IS NOT NULL AND name <> ''"""),
    ("gazette", "gazette_prohibitions", """
        SELECT key, name, NULL, starts_on, ends_on, NULL, NULL, document, false, NULL, NULL, NULL
        FROM pub.gazette_prohibitions WHERE name IS NOT NULL AND name <> '' AND coalesce(superseded_how, '') NOT LIKE 'revoked%'"""),
    ("gazette", "gazette_liquidators", """
        SELECT key, name, NULL, published_on, NULL::date, NULL, NULL, document, false, NULL, NULL, NULL
        FROM pub.gazette_liquidators WHERE name IS NOT NULL AND name <> ''"""),
    ("mp_interests", "mp_interest_returns", """
        SELECT key, name, NULL, as_at, NULL::date, NULL, NULL, document, false, NULL, NULL, NULL
        FROM pub.mp_interest_returns WHERE name IS NOT NULL AND name <> ''"""),
)
POLITICIAN_VIEWS = {"candidates", "members", "mp_interest_returns"}

ADDRESS_SQL = """
    SELECT key, entity_key, started_on, last_file, in_latest, care_of, line_1, line_2, line_3, line_4, postcode
    FROM pub.company_addresses"""
COMPANY_SQL = "SELECT key, name, registered_on, removed_on FROM pub.companies WHERE name IS NOT NULL"


def fold(s: str) -> str:
    return " ".join(kn.fold_diacritics(s or "").lower().replace("'", "").replace("’", "").split())


def read_name(name: str, first: str = None, middle: str = None, last: str = None) -> dict:
    """The one reading: given, middle, family and the three keys. A lane
    that publishes the parts (directors, officers) is read from its parts,
    so a two-word surname stays a surname."""
    if first or last:
        given, mid, family = kn.squash(first or ""), kn.squash(middle or ""), kn.squash(last or "")
    else:
        n = kn.person_name(name)
        given, mid, family = n.given, n.middle, n.family
    fl = fold(f"{given} {family}") if given and family else None
    full = fold(" ".join(p for p in (given, mid, family) if p)) or None
    return {"given": given or None, "middle": mid or None, "family": family or None,
            "name_key": kn.person_key(name) if not (first or last) else kn.person_key(" ".join(p for p in (given, mid, family) if p)),
            "fl_key": fl, "full_key": full, "has_middle": bool(mid)}


def row_record(register: str, view: str, r: tuple) -> tuple | None:
    key, name, entity, started, ended, election, electorate, document, suppressed, first, middle, last = r
    if suppressed or not name or name == "name suppressed":
        return None
    kind = kn.name_kind(name)
    if kind == "person":
        read = read_name(name, first, middle, last)
    else:
        read = {"given": None, "middle": None, "family": None, "name_key": kn.organisation_key(name),
                "fl_key": None, "full_key": None, "has_middle": False}
    return (links.ref(register, key), register, view, key, kind, name, read["given"], read["middle"], read["family"],
            read["name_key"], read["fl_key"], read["full_key"], read["has_middle"], entity, started, ended, election, electorate,
            view in POLITICIAN_VIEWS, document)


def address_record(r: tuple) -> tuple | None:
    key, entity_key, started_on, last_file, in_latest, care_of, l1, l2, l3, l4, postcode = r
    text = " ".join(p for p in (l1, l2, l3, l4, postcode) if p)
    k = ka.address_key(text)
    if not k:
        return None
    region = postcode[:1] if postcode and postcode[:1].isdigit() else None
    return (links.ref("companies", entity_key), k, "registered office", started_on, last_file, in_latest, region, key)


def gather(conn, schema: str, log=print, reader=None) -> dict:
    """Wipe and refill `<schema>.rows`, `.entity_addresses`, `.org_names` from
    `pub`, in one transaction on `conn`. `reader` is a second connection the
    published rows are read through: a server-side cursor and a COPY cannot
    share one connection (the next fetch waits behind the open COPY)."""
    reader = reader or conn
    t0 = time.monotonic()
    conn.execute(links.ddl(schema))
    counts = {}
    with conn.cursor() as w:
        for t in ("rows", "entity_addresses", "org_names"):
            conn.execute(f"DELETE FROM {schema}.{t}")
        for register, view, sql in SOURCES:
            n = 0
            with reader.cursor(name=f"links_rows_{view}") as cur:
                cur.itersize = 20000
                cur.execute(sql)
                with w.copy(f"COPY {schema}.rows (ref, register, view, key, kind, name_filed, given, middle, family, name_key, "
                            f"fl_key, full_key, has_middle, entity_ref, started_on, ended_on, election, electorate, politician, document) "
                            f"FROM STDIN") as copy:
                    for r in cur:
                        rec = row_record(register, view, r)
                        if rec:
                            copy.write_row(rec)
                            n += 1
            counts[f"{register}.{view}"] = n
            log(f"links.rows: {register}.{view}: {n} rows ({time.monotonic() - t0:.0f} s)")
        n = 0
        seen = set()
        with reader.cursor(name="links_addresses") as cur:
            cur.itersize = 20000
            cur.execute(ADDRESS_SQL)
            with w.copy(f"COPY {schema}.entity_addresses (entity_ref, address_key, kind, started_on, last_file, in_latest, region, source_key) FROM STDIN") as copy:
                for r in cur:
                    rec = address_record(r)
                    if rec and (rec[0], rec[1], rec[7]) not in seen:
                        seen.add((rec[0], rec[1], rec[7]))
                        copy.write_row(rec)
                        n += 1
        counts["entity_addresses"] = n
        log(f"links.rows: entity_addresses: {n} ({time.monotonic() - t0:.0f} s)")
        n = 0
        seen = set()
        with reader.cursor(name="links_orgs") as cur:
            cur.itersize = 20000
            cur.execute(COMPANY_SQL)
            with w.copy(f"COPY {schema}.org_names (entity_ref, org_key, registered_on, removed_on) FROM STDIN") as copy:
                for key, name, reg, rem in cur:
                    k = kn.organisation_key(name)
                    if k and (key, k) not in seen:
                        seen.add((key, k))
                        copy.write_row((links.ref("companies", key), k, reg, rem))
                        n += 1
        counts["org_names"] = n
        log(f"links.rows: org_names: {n} ({time.monotonic() - t0:.0f} s)")
    conn.execute(f"ANALYZE {schema}.rows")
    conn.execute(f"ANALYZE {schema}.entity_addresses")
    conn.execute(f"ANALYZE {schema}.org_names")
    conn.commit()
    counts["seconds"] = round(time.monotonic() - t0, 1)
    return counts


def main(argv=None) -> int:
    import json
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn, db.connect(db.OWNER_KEY, "querynz_v4") as reader:
        conn.execute("SET statement_timeout = 0")
        reader.execute("SET statement_timeout = 0")
        print(json.dumps(gather(conn, schema, reader=reader)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
