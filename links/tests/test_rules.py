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
