"""The views the links never read, first tranche (Arthur, 3 November 2026: "the views the links never read, yes ... exact
number joins come first"): the views that print a body's official number are rows, each with its number in
`row_numbers`, and `official-number@1` joins a row to the one body that holds the number. Fast tests on the reading;
a slow test builds the number links on the real engine in a rolled-back schema of the sample database, with invented
rows, and fails when a number joins two bodies, a row not written, or the wrong register's number."""
import os

import pytest

from links import build, rows, rules

NUMBER_VIEWS = {"gazette_liquidations": "gazette", "insolvency_companies": "insolvency", "company_insolvencies": "companies",
                "retirement_villages": "companies", "grant_recipients": "grants", "company_lookup_roles": "companies",
                "company_lookup_holdings": "companies"}


def _source(view):
    return next((reg, sql) for reg, v, sql in rows.SOURCES if v == view)


def test_each_number_view_is_read_once_under_its_lane_folder_and_prints_its_number():
    regs = {v: r for r, v, _ in rows.SOURCES}
    assert {v: regs.get(v) for v in NUMBER_VIEWS} == NUMBER_VIEWS
    assert len([v for _, v, _ in rows.SOURCES]) == len({v for _, v, _ in rows.SOURCES})
    numbered = {(v, r) for r, v, _ in rows.NUMBERS}
    for v, r in NUMBER_VIEWS.items():
        assert (v, r) in numbered, v
    for r, v, _ in rows.NUMBERS:
        assert regs.get(v) == r, v                       # a number is only ever a row's that the gather writes
    kinds = {v: sql for _, v, sql in rows.NUMBERS}
    assert "'charity_number', charity_number" in kinds["grant_recipients"]
    assert "nzbn" not in kinds["grant_recipients"]       # the funders' printed NZBN names another body (measurements.md §15)
    assert "'operator', 'nzbn', operator_nzbn" in kinds["retirement_villages"]
    assert "'company', 'nzbn', nzbn" in kinds["company_insolvencies"]
    for v in ("award_suppliers", "iwi_directory_entities", "commerce_commission_parties", "fma_parties", "worksafe_parties",
              "overseas_investment_parties"):
        assert v in kinds, v                             # the views already read print numbers too


def test_an_insolvency_is_the_company_and_its_appointee_each_its_own_ref():
    assert {"company_insolvencies", "retirement_villages"} <= rows.ROLE_VIEWS
    sql = _source("company_insolvencies")[1]
    assert "'company' AS role" in sql and "'appointee'" in sql
    co = rows.row_record("companies", "company_insolvencies",
                         ("companies/1/insolvency/2", "Acme Widgets Limited", "companies:companies/1", None, None, None, None, "d", False,
                          None, None, None, "company"))
    ap = rows.row_record("companies", "company_insolvencies",
                         ("companies/1/insolvency/2", "Hemi Ruru Tane", "companies:companies/1", None, None, None, None, "d", False,
                          "Hemi Ruru", None, "Tane", "appointee"))
    assert (co[0], co[4], co[13]) == ("companies:companies/1/insolvency/2#company", "organisation", "companies:companies/1")
    assert (ap[0], ap[4], ap[10], ap[11]) == ("companies:companies/1/insolvency/2#appointee", "person", "hemi tane", "hemi ruru tane")


def test_a_village_s_operator_and_supervisor_sit_on_the_village_and_a_grant_recipient_is_dated_by_its_periods():
    sql = _source("retirement_villages")[1]
    assert "'companies:' || key" in sql and "'operator' AS role" in sql and "'supervisor'" in sql
    g = _source("grant_recipients")[1]
    assert "first_period" in g and "last_period" in g
    assert "suppressed" in _source("company_lookup_roles")[1] and "suppressed" in _source("company_lookup_holdings")[1]


PUB_STUBS = {
    "members": "key text, candidate text, election text, electorate text, from_on date, ended_on date, to_by date, party_registered text, route text",
    "candidates": "key text, party_registered text, election text, electorate text, list_place int",
    "candidate_return_totals": "key text, replaced_by text, year int, electorate text",
    "shareholders": "key text, holder_nzbn text, shareholder_type text, name text",
    "companies": "key text, nzbn text, number text, register text, name text",
    "company_lookup_roles": "key text, held_key text",
    "electorates": "key text, name text",
    "mp_interest_returns": "key text, electorate text",
    "mp_interests": "key text, text text",
    "party_return_donors": "key text, party text, year int",
    "disclosures": "key text, party text, given_on date",
    "rea_parties": "key text, licence_number text",
    "building_practitioner_decisions": "key text, lbp_number text",
    "building_practitioners": "key text, licence_number text",
}


class _Pub:
    """The sample connection with `pub.` read from the scratch stubs."""

    def __init__(self, conn, pub):
        self.conn, self.pub = conn, pub

    def execute(self, q, *a, **k):
        return self.conn.execute(q.replace("pub.", f"{self.pub}."), *a, **k)

    def commit(self):
        pass

    def __getattr__(self, n):
        return getattr(self.conn, n)


def _row(ref, view, name):
    return (ref, ref.split(":", 1)[0], view, ref.split(":", 1)[1], "organisation", name, None, None, None, name.lower(), None, None, False)


@pytest.mark.slow
def test_a_printed_number_confirms_the_row_to_the_one_body_that_holds_it():
    import support.db as db
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    s, p = "scratch_links_numbers_test", "scratch_links_numbers_test_pub"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        try:
            raw.execute(f"CREATE SCHEMA {s}")
            raw.execute(f"CREATE SCHEMA {p}")
            raw.execute(__import__("links").ddl(s))
            for v, cols in PUB_STUBS.items():
                raw.execute(f"CREATE TABLE {p}.{v} ({cols})")
            with raw.cursor() as w:
                w.executemany(f"""INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, given, middle, family, name_key, fl_key,
                                  full_key, has_middle) VALUES ({', '.join(['%s'] * 13)})""",
                              [_row("gazette:n/1", "gazette_liquidations", "Acme Widgets Limited"),
                               _row("gazette:n/2", "gazette_liquidations", "Acme Widgets Limited"),
                               _row("grants:r/1", "grant_recipients", "Kauri Trust"),
                               _row("grants:r/2", "grant_recipients", "Kauri Trust"),
                               _row("companies:c/9#company", "company_insolvencies", "Twin Limited")])
                # bodies: a company; a charity whose NZBN is the company's (one body); a second company of another number
                w.executemany(f"""INSERT INTO {s}.bodies (entity_ref, org_key, register, kind, number, nzbn, name, body)
                                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                              [("companies:c/1", "acme widgets", "companies", "companies", "1001", "9429000000011", "Acme Widgets Limited", "companies:c/1"),
                               ("charities:h/1", "kauri", "charities", None, "CC10001", "9429000000011", "Kauri Trust", "companies:c/1"),
                               ("companies:c/2", "kauri", "companies", "other_incorporated", "1001", "9429000000022", "Kauri Trust Board", "companies:c/2"),
                               ("companies:c/3", "twin", "companies", "companies", "3003", "9429000000033", "Twin Limited", "companies:c/3"),
                               ("companies:c/4", "twin", "companies", "companies", "4004", "9429000000033", "Twin Two Limited", "companies:c/4")])
                w.executemany(f"INSERT INTO {s}.row_numbers (ref, register, view, kind, value) VALUES (%s, %s, %s, %s, %s)",
                              [("gazette:n/1", "gazette", "gazette_liquidations", "company_number", "1001"),     # the companies register's 1001
                               ("gazette:n/3", "gazette", "gazette_liquidations", "company_number", "1001"),     # a row not written
                               ("grants:r/1", "grants", "grant_recipients", "charity_number", "CC10001"),       # the charity: its body
                               ("grants:r/2", "grants", "grant_recipients", "nzbn", "9429000000099"),           # no body holds it
                               ("companies:c/9#company", "companies", "company_insolvencies", "nzbn", "9429000000033")])   # two bodies
            out = build.number_links(_Pub(raw, p), s)
            got = sorted(raw.execute(f"SELECT row_a, row_b, grade, evidence->>'number', evidence->>'value' FROM {s}.links").fetchall())
            assert got == [("companies:c/1", "gazette:n/1", "confirmed", "company number", "1001"),
                           ("companies:c/1", "grants:r/1", "confirmed", "charity number", "CC10001")]
            assert out["grant_recipients"] == {"printed": 2, "one_body": 1, "several_bodies": 0, "not_held": 1}
            assert out["company_insolvencies"]["several_bodies"] == 1
            # a name never outweighs a number: the row's name link to another body turns near; to its own body it stands
            raw.execute(f"""INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade) VALUES
                            ('companies:c/2', 'grants:r/1', 'organisation-sole-company@3', '{{}}', 'confirmed'),
                            ('companies:c/1', 'gazette:n/1', 'organisation-sole-company@3', '{{}}', 'confirmed'),
                            ('companies:c/3', 'gazette:n/2', 'organisation-sole-company@3', '{{}}', 'confirmed')""")
            assert build.number_over_name(_Pub(raw, p), s) == 1
            graded = dict(((a, b), (g, r)) for a, b, g, r in raw.execute(
                f"SELECT row_a, row_b, grade, reason FROM {s}.links WHERE rule = 'organisation-sole-company@3'").fetchall())
            assert graded[("companies:c/2", "grants:r/1")] == ("near", rules.NEAR_NUMBER_ELSEWHERE)
            assert graded[("companies:c/1", "gazette:n/1")][0] == "confirmed" and graded[("companies:c/3", "gazette:n/2")][0] == "confirmed"
        finally:
            raw.rollback()


def _person(ref, view, given, family):
    full = f"{given} {family}".lower()
    return (ref, ref.split(":", 1)[0], view, ref.split(":", 1)[1], "person", f"{given} {family}", given, None, family, full, full, full, False)


@pytest.mark.slow
def test_a_licence_number_confirms_two_rows_only_of_one_kind_and_agreeing_names():
    import support.db as db
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    s, p = "scratch_links_licence_test", "scratch_links_licence_test_pub"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        try:
            raw.execute(f"CREATE SCHEMA {s}")
            raw.execute(f"CREATE SCHEMA {p}")
            raw.execute(__import__("links").ddl(s))
            raw.execute(f"CREATE TABLE {p}.rea_parties (key text, licence_number text)")
            raw.execute(f"""INSERT INTO {p}.rea_parties VALUES ('a/1', '10001'), ('a/2', ' 10001 '), ('a/3', '10001'),
                            ('a/4', '20002'), ('a/5', '20002'), ('a/6', '30003'), ('a/7', ''), ('a/8', ' ')""")
            with raw.cursor() as w:
                w.executemany(f"""INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, given, middle, family, name_key, fl_key,
                                  full_key, has_middle) VALUES ({', '.join(['%s'] * 13)})""",
                              [_person("real_estate_authority:a/1", "rea_parties", "Hemi", "Tane"),
                               _person("real_estate_authority:a/2", "rea_parties", "Hemi", "Tane"),
                               _person("real_estate_authority:a/3", "rea_parties", "Mere", "Kauri"),
                               _person("real_estate_authority:a/4", "rea_parties", "Hemi", "Tane"),
                               _row("real_estate_authority:a/5", "rea_parties", "Tane Realty Limited"),
                               _person("real_estate_authority:a/6", "rea_parties", "Hemi", "Tane"),
                               _person("real_estate_authority:a/7", "rea_parties", "Hemi", "Tane"),
                               _person("real_estate_authority:a/8", "rea_parties", "Hemi", "Tane")])
            out = build.licence_links(_Pub(raw, p), s)
            got = sorted(raw.execute(f"SELECT row_a, row_b, grade, reason FROM {s}.links").fetchall())
            assert got == [("real_estate_authority:a/1", "real_estate_authority:a/2", "confirmed", None),
                           ("real_estate_authority:a/1", "real_estate_authority:a/3", "near", rules.NEAR_LICENCE_NAMES),
                           ("real_estate_authority:a/4", "real_estate_authority:a/5", "near", rules.NEAR_LICENCE_KINDS)]
            assert out == {"links": 3, "confirmed": 1, "names_differ": 2}
        finally:
            raw.rollback()


def _surname(ref, view, family):
    return (ref, ref.split(":", 1)[0], view, ref.split(":", 1)[1], "person", f"Mr {family}", None, None, family, family.lower(), None,
            family.lower(), False)


@pytest.mark.slow
def test_a_board_decision_confirms_to_its_licensee_only_on_a_full_match_and_is_near_otherwise():
    """Arthur, 9 November 2026: the licence number joins a decision to the licence register; less than a full match is near,
    the lack of one perhaps another rendering of the name."""
    import support.db as db
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    s, p = "scratch_links_lbp_test", "scratch_links_lbp_test_pub"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        try:
            raw.execute(f"CREATE SCHEMA {s}")
            raw.execute(f"CREATE SCHEMA {p}")
            raw.execute(__import__("links").ddl(s))
            raw.execute(f"CREATE TABLE {p}.building_practitioner_decisions (key text, lbp_number text)")
            raw.execute(f"CREATE TABLE {p}.building_practitioners (key text, licence_number text)")
            raw.execute(f"""INSERT INTO {p}.building_practitioner_decisions VALUES ('d/1', 'BP100001'), ('d/2', 'BP 100002'),
                            ('d/3', 'bp100003'), ('d/4', 'BP100004'), ('d/5', ''), ('d/6', 'BP999999')""")
            raw.execute(f"""INSERT INTO {p}.building_practitioners VALUES ('l/1', 'BP100001'), ('l/2', 'BP100002'), ('l/3', 'BP100003'),
                            ('l/4', 'BP100004'), ('l/4b', 'BP100004'), ('l/5', 'BP100005')""")
            B = "building_practitioners"
            with raw.cursor() as w:
                w.executemany(f"""INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, given, middle, family, name_key, fl_key,
                                  full_key, has_middle) VALUES ({', '.join(['%s'] * 13)})""",
                              [_person(f"{B}:d/1", "building_practitioner_decisions", "Hemi", "Tane"),
                               _surname(f"{B}:d/2", "building_practitioner_decisions", "Kauri"),
                               _person(f"{B}:d/3", "building_practitioner_decisions", "Mere", "Kauri"),
                               _person(f"{B}:d/4", "building_practitioner_decisions", "Hemi", "Tane"),
                               _person(f"{B}:d/5", "building_practitioner_decisions", "Hemi", "Tane"),
                               _person(f"{B}:d/6", "building_practitioner_decisions", "Hemi", "Tane"),
                               _person(f"{B}:l/1", B, "Hemi", "Tane"), _person(f"{B}:l/2", B, "Aroha", "Kauri"),
                               _person(f"{B}:l/3", B, "Merenia", "Kauri"), _person(f"{B}:l/4", B, "Hemi", "Tane"),
                               _person(f"{B}:l/4b", B, "Hemi", "Tane"), _person(f"{B}:l/5", B, "Hemi", "Tane")])
            out = build.lbp_links(_Pub(raw, p), s)
            got = sorted(raw.execute(f"SELECT row_a, row_b, grade, reason FROM {s}.links").fetchall())
            assert got == [(f"{B}:d/1", f"{B}:l/1", "confirmed", None),
                           (f"{B}:d/2", f"{B}:l/2", "near", rules.NEAR_LBP_SURNAME),        # the surname alone, the licensee's
                           (f"{B}:d/3", f"{B}:l/3", "near", rules.NEAR_LBP_NAMES)]          # Mere and Merenia: perhaps one name rendered two ways
            assert out == {"links": 3, "confirmed": 1, "surname_only": 1, "names_differ": 1}
            assert "another rendering" in rules.NEAR_LBP_NAMES and "another rendering" in rules.NEAR_LBP_SURNAME
        finally:
            raw.rollback()
