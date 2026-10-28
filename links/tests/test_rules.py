"""The two confirming rules, exact (design: "How a link is made"), on rows
as `links.rows` reads them; the reading of names into the keys the rules
compare; the SQL defines every table and the publish text every view."""
import re

import pytest

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


@pytest.mark.parametrize("view, filed, parts", [
    # real filed strings from the published donor tables (ruling 73)
    ("party_return_donors", "Greenlees, Craig & Shayne", ["Craig Greenlees", "Shayne Greenlees"]),
    ("disclosures", "Craig & Shayne Greenlees", ["Craig Greenlees", "Shayne Greenlees"]),
    ("candidate_return_donors", "Stewart Menzies and Megan Jean Harrison", ["Stewart Menzies", "Megan Jean Harrison"]),
    ("party_return_donors", "Douglas, Jeffrey Graeme & Christine Elizabeth", ["Jeffrey Graeme Douglas", "Christine Elizabeth Douglas"]),
])
def test_a_coupled_donor_stays_one_row_and_names_each_person(view, filed, parts):
    register = {"party_return_donors": "party_returns", "disclosures": "disclosures", "candidate_return_donors": "candidate_returns"}[view]
    rec = rows.row_record(register, view, ("k1", filed, "parties:x", None, None, None, None, "doc", False, None, None, None))
    # the donor row: one row, the filed string, its own name key, read as no one person
    assert rec[0] == f"{register}:k1" and rec[4] == "person" and rec[5] == filed and rec[9]
    assert rec[6:9] == (None, None, None) and rec[10] is None and rec[11] is None and rec[12] is False and rec[20] is None
    got = rows.part_records(rec)
    assert [p[5] for p in got] == parts
    for i, p in enumerate(got, 1):
        assert len(p) == len(rec) and p[0] == f"{register}:k1#{i}" and p[20] == rec[0]
        assert p[1:4] == rec[1:4] and p[13:20] == rec[13:20] and p[4] == "person"
        assert p[10] == rows.read_name(parts[i - 1])["fl_key"] and p[9] == rows.read_name(parts[i - 1])["name_key"]


@pytest.mark.parametrize("register, view, filed", [
    ("party_returns", "party_return_donors", "Smith & Sons Limited"),           # an organisation is never cut on '&'
    ("party_returns", "party_return_donors", "Christopher & Banks"),
    ("party_returns", "party_return_donors", "M and J Patterson"),              # initials: not judged, read as filed
    ("disclosures", "disclosures", "Mr & Mrs McCabe"),                          # joint, but nobody named by a given name
    ("companies", "directors", "Craig & Shayne Greenlees"),                     # only donation rows are cut
])
def test_no_part_where_the_filed_name_names_no_two_people(register, view, filed):
    rec = rows.row_record(register, view, ("k1", filed, "x:y", None, None, None, None, "doc", False, None, None, None))
    assert rows.part_records(rec) == []


def test_the_coupled_rule_is_near_and_named():
    assert rules.RULE_COUPLED == "coupled-name@1" and "ruling 73" in rules.NEAR_COUPLED


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


# ruling 106 (links-3): each rule on rows shaped as the live tables filed them (28 October 2026)

def _co(ref, number, name, registered, removed=None):
    return {"entity_ref": f"companies:companies/{ref}", "number": number, "name": name, "registered_on": registered, "removed_on": removed}


def test_a_donation_name_confirms_to_the_one_company_live_in_its_year():
    gift = {"ref": "party_returns:x", "name_filed": "JBSR Limited", "name_key": "jbsr", "started_on": "2022-01-01", "ended_on": "2022-12-31"}
    [j] = rules.sole_company(gift, [_co("1", "7679857", "JBSR LIMITED", "2019-08-26")])
    assert (j["rule"], j["grade"], j["reason"]) == (rules.RULE_SOLE_COMPANY, "confirmed", None)
    assert (j["evidence"]["company_number"], j["evidence"]["date"], j["evidence"]["registered_on"], j["evidence"]["removed_on"]) == \
        ("7679857", "2022-01-01", "2019-08-26", None)
    # registered within the year counts: the return dates the gift by its year
    late = dict(gift, started_on="2025-01-01", ended_on="2025-12-31")
    assert rules.sole_company(late, [_co("2", "9320124", "RIVERSTONE INVESTMENTS (NZ) LIMITED", "2025-02-17")])[0]["grade"] == "confirmed"
    # a dated declaration is a year of one day
    dated = {"ref": "disclosures:y", "name_filed": "Atom Data NZ Limited", "started_on": "2026-09-07", "ended_on": None}
    assert rules.sole_company(dated, [_co("3", "9249560", "ATOM DATA NZ LIMITED", "2024-06-10")])[0]["grade"] == "confirmed"
    assert rules.sole_company(dated, [_co("3", "9249560", "ATOM DATA NZ LIMITED", "2026-09-08")])[0]["reason"] == rules.NEAR_ORG_NOT_YET


def test_a_donation_name_stays_near_where_the_one_company_was_gone_or_several_carry_it():
    # the live case: "NZ National Party" on a 2023 candidate return keys to a company removed in 2020
    gift = {"ref": "candidate_returns:z", "name_filed": "NZ National Party", "started_on": "2023-01-01", "ended_on": "2023-12-31"}
    [j] = rules.sole_company(gift, [_co("4", "1438536", "NEW ZEALAND NATIONAL PARTY LIMITED", "2003-11-04", "2020-01-28")])
    assert (j["rule"], j["grade"], j["reason"]) == (rules.RULE_ORG_NAME, "near", rules.NEAR_ORG_GONE)
    assert rules.NEAR_ORG_SEVERAL == "a name match to a company; the donation row carries no official number; several companies carry this name"


# ruling 107 (fix-links-1): several companies of the name, exactly one live in the donation's year (28 October 2026)

def test_one_of_several_companies_live_in_the_year_confirms_and_the_others_stay_near():
    gift = {"ref": "candidate_returns:z", "name_filed": "Porter Group", "name_key": "porter group",
            "started_on": "2023-01-01", "ended_on": "2023-12-31"}
    two = rules.sole_company(gift, [_co("5", "1", "PORTER GROUP LIMITED", "1954-02-22"),
                                    _co("6", "2", "PORTER GROUP LIMITED", "2001-01-01", "2010-01-01")])
    assert [(x["entity_ref"], x["rule"], x["grade"], x["reason"]) for x in two] == [
        ("companies:companies/5", rules.RULE_ONE_LIVE, "confirmed", None),
        ("companies:companies/6", rules.RULE_ORG_NAME, "near", rules.NEAR_ORG_OTHER_LIVE)]
    ev = two[0]["evidence"]
    assert (ev["date"], ev["year"], ev["live_in_year"], ev["companies_alive_on_date"], ev["companies_of_that_name"]) == \
        ("2023-01-01", ["2023-01-01", "2023-12-31"], "1", 1, 2)
    assert [(c["company_number"], c["registered_on"], c["removed_on"], c["live_in_year"]) for c in ev["companies_considered"]] == \
        [("1", "1954-02-22", None, True), ("2", "2001-01-01", "2010-01-01", False)]
    assert two[1]["evidence"]["companies_considered"] == ev["companies_considered"]
    # removed within the year was live in it; registered the day after a one-day declaration was not
    edge = rules.one_live_company({"started_on": "2026-04-08", "ended_on": None},
                                  [_co("7", "3", "X LIMITED", "2026-04-09"), _co("8", "4", "X LIMITED", "1990-01-01", "2026-04-08")])
    assert [(x["entity_ref"][-1], x["grade"]) for x in edge] == [("7", "near"), ("8", "confirmed")]


def test_none_or_more_than_one_live_stays_near_and_says_which():
    gift = {"ref": "party_returns:x", "name_filed": "Atlas Limited", "started_on": "2020-01-01", "ended_on": "2020-12-31"}
    none = rules.one_live_company(gift, [_co("1", "1", "ATLAS LIMITED", "1980-01-01", "2010-01-01"),
                                         _co("2", "2", "ATLAS LIMITED", "2021-03-01")])
    assert [(x["rule"], x["grade"], x["reason"]) for x in none] == [(rules.RULE_ORG_NAME, "near", rules.NEAR_ORG_NONE_LIVE)] * 2
    assert none[0]["evidence"]["live_in_year"] is None and none[0]["evidence"]["companies_alive_on_date"] == 0
    many = rules.one_live_company(gift, [_co("1", "1", "ATLAS LIMITED", "1980-01-01"), _co("2", "2", "ATLAS LIMITED", "2019-03-01"),
                                         _co("3", "3", "ATLAS LIMITED", "2021-03-01")])
    assert [(x["grade"], x["reason"]) for x in many] == [("near", rules.NEAR_ORG_MANY_LIVE)] * 3
    assert many[0]["evidence"]["companies_alive_on_date"] == 2
    assert not any(x["grade"] == "confirmed" for x in none + many)
    # one company of the name is still ruling 106's, never this rule's
    [one] = rules.sole_company(gift, [_co("4", "9", "ATLAS LIMITED", "1980-01-01")])
    assert one["rule"] == rules.RULE_SOLE_COMPANY


def _company(ref, key, registered, removed=None, name=None):
    return {"entity_ref": f"companies:companies/{ref}", "org_key": key, "name": name, "registered_on": registered, "removed_on": removed}


def test_a_successor_name_with_a_person_on_both_is_related_and_never_an_identity():
    old_ = _company("9429030000001", "speirs foods lp", "2009-03-02", "2019-06-30", "SPEIRS FOODS LP")
    new_ = _company("9429046968548", "speirs foods (2018) lp", "2018-08-15", None, "SPEIRS FOODS (2018) LP")
    shared = [{"a": "companies:companies/9429046968548/director/1", "b": "companies:companies/9429030000001/director/7", "group": "g1", "name": "x"}]
    j = rules.successor(new_, old_, shared)
    assert (j["rule"], j["grade"], j["relation"]) == (rules.RULE_SUCCESSOR, "related", "succeeded by")
    assert j["grade"] not in ("confirmed", "near") and "related" in links.GRADES
    # read from the earlier registered to the later, whichever came first in the call
    ev = j["evidence"]
    assert (ev["earlier"], ev["later"], ev["registered"]) == (old_["entity_ref"], new_["entity_ref"], ["2009-03-02", "2018-08-15"])
    assert ev["shared_rows"] == [{"earlier": shared[0]["b"], "later": shared[0]["a"], "group": "g1", "name": "x"}]
    assert rules.successor(old_, new_, [dict(a=shared[0]["b"], b=shared[0]["a"], group="g1", name="x")])["evidence"] == ev


def test_the_name_pattern_alone_stays_near_and_the_names_must_fit():
    old_ = _company("1", "ponsonby u3a", "2001-01-01")
    new_ = _company("2", "ponsonby u3a (2017)", "2018-01-24")
    assert rules.successor(old_, new_, []) is None                       # no person on both: company-name@1 keeps it near
    p = [{"a": "a", "b": "b", "group": "g", "name": "n"}]
    assert rules.successor(new_, _company("3", "ponsonby u3a (2019)", "2019-01-01"), p) is None   # both carry a year
    assert rules.successor(old_, _company("4", "ponsonby u3a", "2019-01-01"), p) is None           # neither does: one name, company-name@1
    assert rules.successor(_company("5", "onehunga club (2018)", "2018-05-30"), old_, p) is None   # another name
    assert rules.bare_name("speirs foods (2018) lp") == "speirs foods lp" and rules.bare_name("(2018)") == ""


def test_a_refiled_name_with_a_person_on_both_is_related_in_arthur_s_words():
    # Christopher & Banks Limited (ruling 109): 3482091 removed 2024-12-18, 9321019 registered 2025-03-06
    old_ = _company("9429031010443", "christopher & banks", "2011-07-28", "2024-12-18", "CHRISTOPHER & BANKS LIMITED")
    new_ = _company("9429052661174", "christopher & banks", "2025-03-06", None, "CHRISTOPHER & BANKS LIMITED")
    shared = [{"a": "companies:companies/9429052661174/director/1", "b": "companies:companies/9429031010443/director/7", "group": "g1", "name": "x"}]
    j = rules.refiled(new_, old_, shared)
    assert (j["rule"], j["grade"], j["relation"]) == (rules.RULE_REFILED, "related", "delisted/refiled same year")
    ev = j["evidence"]
    assert (ev["earlier"], ev["later"], ev["removed_on"], ev["refiled_on"], ev["gap_days"]) == (
        old_["entity_ref"], new_["entity_ref"], "2024-12-18", "2025-03-06", 78)
    assert ev["shared_rows"] == [{"earlier": shared[0]["b"], "later": shared[0]["a"], "group": "g1", "name": "x"}]
    assert ev["shared_people"] == 1 and ev["order"] == "by registration date"
    assert rules.refiled(old_, new_, [dict(a=shared[0]["b"], b=shared[0]["a"], group="g1", name="x")])["evidence"] == ev
    # either order: Pacific Hygiene Limited, 9444168 registered 2026-07-13 before 564741 was removed 2026-07-31
    a = _company("9429038920622", "pacific hygiene", "1992-11-10", "2026-07-31")
    b = _company("9429053809063", "pacific hygiene", "2026-07-13")
    assert rules.refiled(a, b, shared)["evidence"]["gap_days"] == -18
    # a successor's name is not this rule's, nor this one successor's
    assert rules.successor(old_, new_, shared) is None


def test_a_refiled_name_needs_a_person_on_both_and_the_twelve_months():
    old_ = _company("1", "harbour 5", "2001-01-01", "2024-02-29")
    p = [{"a": "a", "b": "b", "group": "g", "name": "n"}]
    assert rules.refiled(old_, _company("2", "harbour 5", "2025-02-28"), p) is not None          # the last day of the twelve months
    assert rules.refiled(old_, _company("2", "harbour 5", "2025-03-01"), p) is None              # a day past it
    assert rules.refiled(old_, _company("2", "harbour 5", "2023-02-28"), p) is not None          # twelve months before the removal
    assert rules.refiled(old_, _company("2", "harbour 5", "2023-02-27"), p) is None
    assert rules.refiled(old_, _company("2", "harbour 5", "2024-06-01"), []) is None             # no person on both: company-name@1 keeps it near
    assert rules.refiled(_company("1", "harbour 5", "2001-01-01"), _company("2", "harbour 5", "2024-06-01"), p) is None   # neither removed
    # the later registered removed and the earlier still live is no refiling
    assert rules.refiled(_company("1", "harbour 5", "2001-01-01"), _company("2", "harbour 5", "2024-01-01", "2024-06-01"), p) is None
    assert rules.refiled(old_, _company("2", "harbour 6", "2024-06-01"), p) is None             # another name
    assert rules.refiled(_company("1", "harbour 5 (2001)", "2001-01-01", "2024-02-29"),
                         _company("2", "harbour 5 (2001)", "2024-06-01"), p) is None             # a year in brackets: not this rule
    assert rules.refiled(old_, _company("2", "harbour 5", None), p) is None                     # a date unknown never relates
    # equal registration dates: the removed one is the earlier
    j = rules.refiled(_company("2", "harbour 5", "2020-01-01"), _company("1", "harbour 5", "2020-01-01", "2020-05-01"), p)
    assert j["evidence"]["earlier"] == "companies:companies/1" and j["evidence"]["order"].startswith("registration dates equal")


def test_the_tables_carry_the_third_grade_and_the_view_never_shows_it_confirmed():
    sql = links.tables_sql()
    assert "CHECK (grade IN ('confirmed', 'near', 'related'))" in sql and "ALTER TABLE links.links ADD COLUMN IF NOT EXISTS relation " in sql
    assert "links_relation_graded CHECK ((grade = 'related') = (relation IS NOT NULL))" in sql
    pub = links.publish_sql()
    assert "l.relation\nFROM links.links l" in pub                        # appended last: CREATE OR REPLACE VIEW keeps the columns before it
    import inspect
    from links import build
    assert "WHERE grade = 'confirmed'" in inspect.getsource(build.components)   # the groups walk confirmed links only


def _cand(ref, election, electorate=None, list_place=None, filed="UPSTON, Louise", party="National Party"):
    return {"ref": f"house:candidates/{ref}", "election": election, "electorate": electorate, "list_place": list_place,
            "name_filed": filed, "name_key": "louise upston", "party": party}


def test_one_candidate_name_for_one_party_in_two_elections_is_one_person():
    rows_ = [_cand("ge-2023/taupo/1", "ge-2023", "Taupō", 9), _cand("ge-2020/taupo/1", "ge-2020", "Taupō", 18)]
    [(a, b, j)] = rules.same_party_candidates(rows_)
    assert (j["rule"], j["grade"], j["reason"]) == (rules.RULE_SAME_PARTY, "confirmed", None)
    assert (a, b) == ("house:candidates/ge-2020/taupo/1", "house:candidates/ge-2023/taupo/1")
    ev = j["evidence"]
    assert (ev["party"], ev["elections"], ev["seats"]) == ("National Party", ["ge-2020", "ge-2023"], ["Taupō, list 18", "Taupō, list 9"])
    three = rules.same_party_candidates(rows_ + [_cand("ge-2026/x/1", "ge-2026", None, 12)])
    assert [j["grade"] for *_, j in three] == ["confirmed", "confirmed"] and three[1][2]["evidence"]["seats"][1] == "list 12"
    assert rules.same_party_candidates(rows_[:1]) == []


def test_two_of_the_name_for_the_party_in_one_election_and_no_pair_confirms():
    rows_ = [_cand("ge-2020/a/1", "ge-2020", "Ōhāriu"), _cand("ge-2023/a/1", "ge-2023", "Ōhāriu"), _cand("ge-2023/b/1", "ge-2023", "Rongotai")]
    out = rules.same_party_candidates(rows_)
    assert [(j["grade"], j["reason"]) for *_, j in out] == [("near", rules.NEAR_SAME_ELECTION)] * 2
    assert out[0][2]["evidence"]["elections_with_two_of_this_name"] == ["ge-2023"]
    # two in one election and never another: still near, still said
    assert [j["grade"] for *_, j in rules.same_party_candidates(rows_[1:])] == ["near"]
