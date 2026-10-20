"""The two confirming rules, exact (design: "How a link is made"), on rows
as `links.rows` reads them; the reading of names into the keys the rules
compare; the SQL defines every table and the publish text every view."""
import re

import links
from links import rows, rules


def row(filed, first=None, middle=None, last=None, politician=False, register="companies"):
    r = rows.read_name(filed, first, middle, last)
    r.update(name_filed=filed, politician=politician, register=register, ref=f"{register}:{filed}")
    return r


def test_the_reading_gives_the_three_keys():
    r = rows.read_name("Graeme Richard HART", "Graeme", "Richard", "HART")
    assert (r["fl_key"], r["full_key"], r["has_middle"]) == ("graeme hart", "graeme richard hart", True)
    s = rows.read_name("HART, Graeme")                      # a candidate as the Commission prints it
    assert (s["fl_key"], s["full_key"], s["has_middle"]) == ("graeme hart", "graeme hart", False)
    assert rows.read_name("Te Pāti Māori Officer", "Te", "", "Māori")["fl_key"] == "te maori"   # macrons decomposed, never deleted
    assert rows.read_name("Hone O'Brien", "Hone", "", "O'Brien")["fl_key"] == "hone obrien"


def test_rule_one_needs_the_same_middle_name_on_both():
    a, b = row("Graeme Richard HART", "Graeme", "Richard", "HART"), row("Graeme Richard HART", "Graeme", "Richard", "HART")
    assert rules.judge(a, b)["rule"] == rules.RULE_FULL and rules.judge(a, b)["grade"] == "confirmed"
    c = row("Graeme Eric HART", "Graeme", "Eric", "HART")
    j = rules.judge(a, c)
    assert (j["grade"], j["reason"]) == ("near", rules.NEAR_MIDDLE_DIFFERS)
    d = row("Graeme HART", "Graeme", "", "HART")
    assert rules.judge(a, d)["reason"] == rules.NEAR_ONE_MIDDLE
    assert rules.judge(d, row("Graeme HART", "Graeme", "", "HART"))["reason"] == rules.NEAR_NO_MIDDLE


def test_rule_two_needs_a_shared_quiet_address_and_never_address_alone():
    a, b = row("Graeme HART", "Graeme", "", "HART"), row("Graeme HART", "Graeme", "", "HART")
    j = rules.judge(a, b, {"2mortimertce"}, {"2mortimertce", "1queenst"}, {"2mortimertce": 3})
    assert (j["rule"], j["grade"]) == (rules.RULE_ADDRESS, "confirmed") and j["evidence"]["shared_addresses"] == ["2mortimertce"]
    busy = rules.judge(a, b, {"1queenst"}, {"1queenst"}, {"1queenst": 1060})
    assert (busy["grade"], busy["reason"]) == ("near", rules.NEAR_BUSY_ADDRESS)
    # a busy address counts when both rows carry the (same) middle name
    c, d = row("John Adam SMITH", "John", "Adam", "SMITH"), row("John Adam SMITH", "John", "Adam", "SMITH")
    ok, shared, reason = rules.same_name_and_address(c, d, {"1queenst"}, {"1queenst"}, {"1queenst": 1060})
    assert ok and shared == {"1queenst"}
    # a different name at the same address is nothing
    e = row("Jane HART", "Jane", "", "HART")
    assert rules.judge(a, e, {"2mortimertce"}, {"2mortimertce"}, {})["grade"] == "near"
    assert not rules.same_name_and_address(a, e, {"x"}, {"x"}, {})[0]


def test_a_politician_is_never_confirmed_by_name():
    mp = row("HART, Graeme Richard", politician=True, register="house")
    d = row("Graeme Richard HART", "Graeme", "Richard", "HART")
    j = rules.judge(mp, d, {"2mortimertce"}, {"2mortimertce"}, {})
    assert (j["grade"], j["reason"]) == ("near", rules.NEAR_POLITICIAN)


def test_organisations_are_read_apart_from_people():
    rec = rows.row_record("party_returns", "party_return_donors",
                          ("k1", "Rail & Maritime Transport Union", "parties:x", None, None, None, None, "doc", False, None, None, None))
    assert rec[4] == "organisation" and rec[9] == "rail & maritime transport union" and rec[10] is None
    rec = rows.row_record("companies", "directors", ("k2", "name suppressed", "companies:c", None, None, None, None, "doc", True, None, None, None))
    assert rec is None
    rec = rows.row_record("house", "candidates", ("k3", "HORN, Chrys", None, None, None, "ge-2020", "ge-2020/x", "doc", False, None, None, None))
    assert rec[0] == "house:k3" and rec[18] is True and rec[10] == "chrys horn"


def test_an_address_record_is_the_company_s_office_with_its_region():
    rec = rows.address_record(("ak", "companies/9429000000001", None, "companies-2026-08", True, None, "95 Waterside Drive", "Pyes Pa", "Tauranga", None, "3112"))
    assert rec[0] == "companies:companies/9429000000001" and rec[1] == "95watersidedrpyespatauranga3112" and rec[6] == "3"
    assert rows.address_record(("ak", "companies/1", None, None, True, None, None, None, None, None, None)) is None


def test_bands_follow_the_director_count():
    assert [links.band_of(n) for n in (1, 5, 6, 50, 51, 5000)] == ["rare", "rare", "middling", "middling", "common", "common"]


def test_refs_round_trip_and_the_ddl_targets_a_schema():
    assert links.split_ref(links.ref("companies", "companies/1/director/ab")) == ("companies", "companies/1/director/ab")
    ddl = links.ddl("scratch_links")
    assert "scratch_links.rows" in ddl and "links." not in ddl.replace("scratch_links.", "")
    for t in ("rows", "entity_addresses", "org_names", "watch", "test_pairs", "measurements", "readings"):
        assert re.search(rf"CREATE TABLE IF NOT EXISTS links\.{t}\b", links.tables_sql()), t
    pub = links.publish_sql()
    for v in ("pub.links", "pub.groups", "pub.decisions", "pub.names", "pub.old_decisions"):
        assert f"CREATE OR REPLACE VIEW {v}" in pub, v


def test_the_given_name_is_the_first_of_the_given_names_whichever_field_a_lane_put_them_in():
    """A lane that files every given name in one field (candidate returns,
    Gazette bankruptcies) keys the row as every other register does (links-2)."""
    r = rows.read_name("Louise Claire UPSTON", "Louise Claire", None, "UPSTON")
    assert (r["given"], r["middle"], r["fl_key"], r["full_key"], r["has_middle"]) == ("Louise", "Claire", "louise upston", "louise claire upston", True)
    assert r["fl_key"] == rows.read_name("UPSTON, Louise Claire")["fl_key"] == rows.read_name("Louise UPSTON", "Louise", "", "UPSTON")["fl_key"]
    assert rows.read_name("Romana (Marnz) MANNING", "Romana (Marnz)", None, "MANNING")["full_key"] == "romana manning"   # a nickname is no name
    assert rows.read_name("Mary Anne SMITH", "Mary Anne", "Louise", "SMITH")["middle"] == "Anne Louise"


def test_a_footnote_mark_in_an_expense_line_is_no_name():
    r = rows.read_name("Doyle, Benjamin (3)")
    assert (r["fl_key"], r["name_key"], r["has_middle"]) == ("benjamin doyle", "benjamin doyle", False)


def test_a_declared_interest_names_its_organisation_up_to_the_dash():
    assert rows.declared_name("Spire Investments Limited – commercial property") == "Spire Investments Limited"
    assert rows.declared_name("Cameron Brewer Communications Limited (inactive, and in process of de- registration)") == "Cameron Brewer Communications Limited"
    assert rows.declared_name("Animal Scanning Services (NZ) Limited – farming") == "Animal Scanning Services (NZ) Limited"
    assert rows.declared_name("Roxtene Holdings Limited (not trading)") == "Roxtene Holdings Limited"
    assert rows.declared_name("  ") == ""


def test_every_published_view_the_rows_read_is_named_once_and_the_politician_views_exist():
    views = [v for _, v, _ in rows.SOURCES]
    assert len(views) == len(set(views))
    for v in ("gazette_bankruptcies", "gazette_appointments", "mp_expenses", "minister_expenses", "mp_interests",
              "candidate_return_donors", "candidate_return_totals"):
        assert v in views, v
    assert rows.POLITICIAN_VIEWS <= set(views)
    assert rows.DECLARED_VIEWS <= set(views)


def test_every_rule_named_in_rules_is_built_and_the_tables_carry_the_catch_log():
    import os
    import links
    with open(os.path.join(links.HERE, "build.py"), encoding="utf-8") as f:
        build = f.read()
    for name in dir(rules):
        if name.startswith("RULE_"):
            assert f"rules.{name}" in build, name
    sql = links.tables_sql()
    assert "CREATE TABLE IF NOT EXISTS links.rows_catch" in sql
    assert "rows_register ON links.rows (register, view)" in sql
    with open(os.path.join(links.HERE, "check.py"), encoding="utf-8") as f:
        assert "check_rows_current" in f.read()


def test_a_scratch_schema_is_made_and_links_itself_never_is():
    import links

    class Conn:
        def __init__(self):
            self.sql = []

        def execute(self, q):
            self.sql.append(q)

        def commit(self):
            pass

    c = Conn()
    links.ensure_schema(c, "links")
    assert c.sql == []
    links.ensure_schema(c, "scratch_links_2")
    assert c.sql[0] == "CREATE SCHEMA IF NOT EXISTS scratch_links_2"
    import pytest
    with pytest.raises(ValueError):
        links.ensure_schema(c, "scratch; drop")
    assert "scratch_x_pub.links" in links.publish_ddl("scratch_x", "scratch_x_pub")
