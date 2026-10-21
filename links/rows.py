"""Gather every person row of every published register into `links.rows`,
under the one shared reading of names (keys.names), and every company's
registered office under the one reading of addresses (keys.addresses).
Reads `pub.*` only. No home address: the address arm reads the office of
the company a role sits on, which a company publishes.

    python -m links.rows [--schema scratch_links] [--register gazette [--register house …]]

A register is named by its lane folder, as the board names it. The views
read, and what each row's entity is:

| register          | view                                  | person name              | entity (`<register>:<key>`) |
| companies         | directors                             | full_name                | entity_key          |
| companies         | shareholders                          | name (individuals)       | entity_key          |
| societies         | society_officers                      | full_name                | society_key         |
| house             | candidates, members                   | name (politician)        | -                   |
| party_returns     | party_return_donors                   | donor                    | party (as resolved) |
| candidate_returns | candidate_return_donors, _totals      | donor; the filing candidate | the return        |
| disclosures       | disclosures, items                    | donor_name, contributor  | party               |
| party_finance     | promoter_people                       | name                     | promoter_key        |
| gazette           | prohibitions, liquidators             | name                     | -                   |
| gazette           | gazette_bankruptcies                  | given_names, surname (a withheld name is no row) | - |
| gazette           | gazette_appointments                  | name                     | -                   |
| mp_interests      | mp_interest_returns                   | name (politician)        | -                   |
| mp_interests      | mp_interests (directorships, business interests) | the declared organisation | the member's return |
| expenses          | mp_expenses, minister_expenses        | member (politician)      | -                   |

An expense line is a figure under a member's name; it is a row here so a
product can reach the register through the one reading of names.

**A coupled donor name (ruling 73).** A donation row filed as two people
("Craig & Shayne Greenlees", "Mills, Phillip & Jackie"; `keys.names.is_joint_name`)
stays one row as the Commission filed it, with its name key, and is not
read as one person (no given, family or person keys). Beside it, one part
row per person it names (`keys.names.joint_parts`): ref `<donor ref>#<n>`,
the donor's register, view, key, entity and dates, `part_of` the donor's
ref, `name_filed` the person's name as the part reads it. The rules read a
part as any person row; `coupled-name@1` joins it to its donor row.

**Rebuild only what changed (register rule 10):** `--register` empties and
refills one register's rows and leaves the others; the registered offices
and company names are refilled only with `companies`. The links are still
built whole over the rows (`links.build`).
"""
from __future__ import annotations

import json
import re
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
    ("candidate_returns", "candidate_return_donors", """
        SELECT key, donor AS name, 'candidate_returns:' || return_key AS entity_key, make_date(year, 1, 1), make_date(year, 12, 31),
               year::text AS election, electorate, document, false, NULL, NULL, NULL
        FROM pub.candidate_return_donors WHERE donor IS NOT NULL AND donor <> ''"""),
    ("candidate_returns", "candidate_return_totals", """
        SELECT key, trim(coalesce(given_names, '') || ' ' || coalesce(surname, '')) AS name, NULL, make_date(year, 1, 1), NULL::date,
               year::text AS election, electorate, document, false, given_names, NULL, surname
        FROM pub.candidate_return_totals WHERE coalesce(surname, '') <> ''"""),
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
    # a Gazette bankruptcy names a person in two fields; a name the Gazette later withheld is blank and makes no row
    ("gazette", "gazette_bankruptcies", """
        SELECT key, trim(coalesce(given_names, '') || ' ' || coalesce(surname, '')) AS name, NULL, event_on, NULL::date, NULL, NULL,
               document, withheld_by IS NOT NULL, given_names, NULL, surname
        FROM pub.gazette_bankruptcies WHERE coalesce(surname, '') <> ''"""),
    ("gazette", "gazette_appointments", """
        SELECT key, name, NULL, starts_on, ends_on, NULL, NULL, document, false, NULL, NULL, NULL
        FROM pub.gazette_appointments WHERE name IS NOT NULL AND name <> ''"""),
    # a declared company directorship or business interest: the organisation named, read from the entry's text
    ("mp_interests", "mp_interests", """
        SELECT key, text AS name, 'mp_interests:' || member_return, as_at, NULL::date, NULL, NULL, document, withheld, NULL, NULL, NULL
        FROM pub.mp_interests WHERE category IN ('directorships', 'business-interests') AND text IS NOT NULL AND text <> ''"""),
    # an expense line is a figure under a member's name, for the period of the release
    ("expenses", "mp_expenses", """
        SELECT key, member AS name, NULL, period_start, period_end, NULL, NULL, document, false, NULL, NULL, NULL
        FROM pub.mp_expenses WHERE member IS NOT NULL AND member <> ''"""),
    ("expenses", "minister_expenses", """
        SELECT key, member AS name, NULL, period_start, period_end, NULL, NULL, document, false, NULL, NULL, NULL
        FROM pub.minister_expenses WHERE member IS NOT NULL AND member <> ''"""),
)
#: the filing candidate is a politician; a declared interest is the member's own (a sole trade in the member's name is not a director row)
POLITICIAN_VIEWS = {"candidates", "members", "mp_interest_returns", "candidate_return_totals", "mp_expenses", "minister_expenses", "mp_interests"}
DECLARED_VIEWS = {"mp_interests"}       # the name is read out of a declared entry's text
#: the donation views, where a coupled filed name is one donor joined to each person it names (ruling 73)
DONATION_VIEWS = {"party_return_donors", "candidate_return_donors", "disclosures", "disclosure_items"}
_DASHES = (" – ", " — ", " - ")
_TRAILING_NOTE = re.compile(r"\s*\([^()]*\)\s*$")      # "(not trading)", "(inactive, and in process of de-registration)"
_BRACKETED = re.compile(r"\s*\([^()]*\)")

ADDRESS_SQL = """
    SELECT key, entity_key, started_on, last_file, in_latest, care_of, line_1, line_2, line_3, line_4, postcode
    FROM pub.company_addresses"""
COMPANY_SQL = "SELECT key, name, registered_on, removed_on FROM pub.companies WHERE name IS NOT NULL"


def fold(s: str) -> str:
    return " ".join(kn.fold_diacritics(s or "").lower().replace("'", "").replace("’", "").split())


def declared_name(text: str) -> str:
    """The organisation a declared interest names: the entry's text up to
    its dash ("Spire Investments Limited – commercial property"), a trailing
    bracketed note off ("(not trading)")."""
    t = kn.squash(text or "")
    for sep in _DASHES:
        if sep in t:
            t = t.split(sep, 1)[0]
            break
    return _TRAILING_NOTE.sub("", t).strip(" .,;:")


def read_name(name: str, first: str = None, middle: str = None, last: str = None) -> dict:
    """The one reading: given, middle, family and the three keys. A lane
    that publishes the parts (directors, officers) is read from its parts,
    so a two-word surname stays a surname. The given name is the first of
    the given names and the rest are middle names, whichever field a lane
    put them in, as `keys.names.person_name` reads a one-line name: a lane
    that files every given name in one field ("Louise Claire", surname
    "UPSTON") would otherwise key the row apart from every other register's
    "Louise UPSTON". A nickname in brackets is no name."""
    if first or last:
        givens = kn.squash(_BRACKETED.sub("", f"{first or ''} {middle or ''}")).split()
        given, mid, family = (givens[0] if givens else ""), " ".join(givens[1:]), kn.squash(last or "")
    else:
        name = _BRACKETED.sub("", name)     # a footnote mark "(3)" or a nickname in brackets is no name
        n = kn.person_name(name)
        given, mid, family = n.given, n.middle, n.family
    fl = fold(f"{given} {family}") if given and family else None
    full = fold(" ".join(p for p in (given, mid, family) if p)) or None
    return {"given": given or None, "middle": mid or None, "family": family or None,
            "name_key": kn.person_key(name) if not (first or last) else kn.person_key(" ".join(p for p in (given, mid, family) if p)),
            "fl_key": fl, "full_key": full, "has_middle": bool(mid)}


def row_record(register: str, view: str, r: tuple, catch: dict = None) -> tuple | None:
    """The row to write, or None with the reason counted in `catch`."""
    key, name, entity, started, ended, election, electorate, document, suppressed, first, middle, last = r
    if view in DECLARED_VIEWS:
        name = declared_name(name)
    if suppressed or not name or name == "name suppressed":
        reason = "suppressed or withheld" if suppressed or name == "name suppressed" else "no name"
        if catch is not None:
            catch[reason] = catch.get(reason, 0) + 1
        return None
    kind = kn.name_kind(name)
    if kind == "person" and view in DONATION_VIEWS and kn.is_joint_name(name) is True:
        # one donor, two people: read as nobody alone; its part rows carry the people (part_records)
        read = {"given": None, "middle": None, "family": None, "name_key": kn.person_key(name),
                "fl_key": None, "full_key": None, "has_middle": False}
    elif kind == "person":
        read = read_name(name, first, middle, last)
    else:
        read = {"given": None, "middle": None, "family": None, "name_key": kn.organisation_key(name),
                "fl_key": None, "full_key": None, "has_middle": False}
    return (links.ref(register, key), register, view, key, kind, name, read["given"], read["middle"], read["family"],
            read["name_key"], read["fl_key"], read["full_key"], read["has_middle"], entity, started, ended, election, electorate,
            view in POLITICIAN_VIEWS, document, None)


def part_records(rec: tuple) -> list:
    """The part rows of a coupled donor row (ruling 73), one per person its
    filed name names; [] for any other row. Each is read as a one-line
    person name and carries the donor row's place: register, view, key,
    entity, dates, document, with `part_of` the donor's ref."""
    ref, register, view = rec[0], rec[1], rec[2]
    if view not in DONATION_VIEWS or rec[4] != "person" or rec[10] is not None:
        return []
    out = []
    for i, part in enumerate(kn.joint_parts(rec[5]), 1):
        r = read_name(part)
        out.append((f"{ref}#{i}", register, view, rec[3], "person", part, r["given"], r["middle"], r["family"], r["name_key"],
                    r["fl_key"], r["full_key"], r["has_middle"]) + tuple(rec[13:20]) + (ref,))
    return out


def address_record(r: tuple) -> tuple | None:
    key, entity_key, started_on, last_file, in_latest, care_of, l1, l2, l3, l4, postcode = r
    text = " ".join(p for p in (l1, l2, l3, l4, postcode) if p)
    k = ka.address_key(text)
    if not k:
        return None
    region = postcode[:1] if postcode and postcode[:1].isdigit() else None
    return (links.ref("companies", entity_key), k, "registered office", started_on, last_file, in_latest, region, key)


def gather(conn, schema: str, log=print, reader=None, registers=None) -> dict:
    """Wipe and refill `<schema>.rows`, `.entity_addresses`, `.org_names` from
    `pub`, in one transaction on `conn`. `reader` is a second connection the
    published rows are read through: a server-side cursor and a COPY cannot
    share one connection (the next fetch waits behind the open COPY).
    `registers`, when given, names the registers to refill (rule 10); the
    rest of the rows stand, and the offices and company names are refilled
    only when `companies` is among them."""
    reader = reader or conn
    t0 = time.monotonic()
    conn.execute(links.ddl(schema))
    counts = {}
    registers = set(registers) if registers else None
    unknown = (registers or set()) - {r for r, _, _ in SOURCES}
    if unknown:
        raise ValueError(f"no such register in links.rows: {sorted(unknown)}")
    companies_too = registers is None or "companies" in registers
    with conn.cursor() as w:
        if registers is None:
            conn.execute(f"DELETE FROM {schema}.rows")
        else:
            conn.execute(f"DELETE FROM {schema}.rows WHERE register = ANY(%s)", (sorted(registers),))
        if companies_too:
            for t in ("entity_addresses", "org_names"):
                conn.execute(f"DELETE FROM {schema}.{t}")
        for register, view, sql in SOURCES:
            if registers is not None and register not in registers:
                continue
            n = read = parts = 0
            catch: dict = {}
            with reader.cursor(name=f"links_rows_{view}") as cur:
                cur.itersize = 20000
                cur.execute(sql)
                with w.copy(f"COPY {schema}.rows (ref, register, view, key, kind, name_filed, given, middle, family, name_key, "
                            f"fl_key, full_key, has_middle, entity_ref, started_on, ended_on, election, electorate, politician, document, part_of) "
                            f"FROM STDIN") as copy:
                    for r in cur:
                        read += 1
                        rec = row_record(register, view, r, catch)
                        if rec:
                            copy.write_row(rec)
                            n += 1
                            for part in part_records(rec):
                                copy.write_row(part)
                                parts += 1
            assert read == n + sum(catch.values()), (view, read, n, catch)
            conn.execute(f"""INSERT INTO {schema}.rows_catch (view, register, read, written, set_aside, reasons, gathered_at)
                             VALUES (%s, %s, %s, %s, %s, %s::jsonb, now())
                             ON CONFLICT (view) DO UPDATE SET register = EXCLUDED.register, read = EXCLUDED.read, written = EXCLUDED.written,
                                 set_aside = EXCLUDED.set_aside, reasons = EXCLUDED.reasons, gathered_at = now()""",
                         (view, register, read, n, read - n, json.dumps(catch)))
            counts[f"{register}.{view}"] = n
            if parts:
                counts[f"{register}.{view}.parts"] = parts
            log(f"links.rows: {register}.{view}: {n} rows, {read - n} set aside {catch}, {parts} coupled-name parts ({time.monotonic() - t0:.0f} s)")
        if not companies_too:
            conn.execute(f"ANALYZE {schema}.rows")
            conn.commit()
            counts["seconds"] = round(time.monotonic() - t0, 1)
            counts["registers"] = sorted(registers)
            return counts
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
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    registers = [argv[i + 1] for i, a in enumerate(argv) if a == "--register"] or None
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn, db.connect(db.OWNER_KEY, "querynz_v4") as reader:
        conn.execute("SET statement_timeout = 0")
        reader.execute("SET statement_timeout = 0")
        links.ensure_schema(conn, schema)
        print(json.dumps(gather(conn, schema, reader=reader, registers=registers)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
