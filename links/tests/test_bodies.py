"""Ruling 114 (28 October 2026): a donor's organisation name looked up on the
companies, societies, limited partnerships and charities registers together
(`organisation-sole-company@2`, `organisation-one-live-company@2`), a body
on two registers counted once; and ruling 125 (30 October 2026): the same
two rules, as @3, on every organisation-named row of every people view,
"live" judged on the row's own date, an undated row near. Pure tests on
shapes the registers file; a slow test builds and checks on the real engine
(a sample-database schema, rolled back) and turns check item 9 red on
planted faults."""
import os
import re

import pytest

import links
from links import rules

GIFT = {"ref": "party_returns:x", "name_filed": "Hart Foundation", "name_key": "hart foundation",
        "started_on": "2023-01-01", "ended_on": "2023-12-31"}


def _r(ref, register, registered, removed=None, number=None, name="HART FOUNDATION", kind=None, undated=False, named=True):
    return {"entity_ref": ref, "register": register, "kind": kind, "number": number, "name": name, "registered_on": registered,
            "removed_on": removed, "removal_undated": undated, "named": named}


def test_one_charity_of_the_name_live_in_the_year_confirms_under_version_two():
    [j] = rules.sole_body(GIFT, [{"body": "charities:charities/CC1", "rows": [_r("charities:charities/CC1", "charities", "2009-05-01",
                                                                                   number="CC1")]}])
    assert (j["entity_ref"], j["rule"], j["grade"], j["reason"]) == ("charities:charities/CC1", "organisation-sole-company@2", "confirmed", None)
    ev = j["evidence"]
    assert (ev["company"], ev["company_number"], ev["register"], ev["companies_of_that_name"], ev["registers_holding_the_name"]) == \
        ("HART FOUNDATION", "CC1", "charities", 1, ["charities"])
    assert rules.RULE_SOLE_COMPANY == "organisation-sole-company@1" and rules.RULE_SOLE_COMPANY in rules.RETIRED   # @1 keeps its meaning


def test_a_charity_that_is_a_company_is_one_body_and_live_by_its_company():
    """The charity was deregistered in 2015; the company it is stands: the body was live in 2023."""
    body = {"body": "companies:companies/7", "rows": [
        _r("companies:companies/7", "companies", "1990-02-01", number="400123", kind="companies", name="HART FOUNDATION LIMITED", named=False),
        _r("charities:charities/CC2", "charities", "2008-06-30", "2015-01-01", number="CC2")]}
    [j] = rules.sole_body(GIFT, [body])
    assert (j["entity_ref"], j["rule"], j["evidence"]["company_number"], j["evidence"]["company"]) == \
        ("companies:companies/7", rules.RULE_SOLE_BODY, "400123", "HART FOUNDATION")
    assert [x["register"] for x in j["evidence"]["registers"]] == ["charities", "companies"]
    assert j["evidence"]["registers_holding_the_name"] == ["charities"]
    # a charity alone is ended by its deregistration
    [k] = rules.sole_body(GIFT, [{"body": "charities:charities/CC2", "rows": [body["rows"][1]]}])
    assert (k["grade"], k["reason"]) == ("near", rules.body_reason(["charities"], rules.NEAR_BODY_GONE))


def test_a_company_and_a_charity_of_one_name_both_live_stay_near_and_name_both_registers():
    two = rules.sole_body(GIFT, [
        {"body": "companies:companies/8", "rows": [_r("companies:companies/8", "companies", "2001-01-01", kind="companies")]},
        {"body": "charities:charities/CC3", "rows": [_r("charities:charities/CC3", "charities", "2010-01-01")]}])
    assert [(x["rule"], x["grade"]) for x in two] == [(rules.RULE_ORG_NAME, "near")] * 2
    assert two[0]["reason"] == ("a name match on the companies and charities registers; the donation row carries no official number; "
                                "several bodies carry this name, and more than one of them was live in the donation's year")
    assert two[0]["evidence"]["companies_alive_on_date"] == 2 and two[0]["evidence"]["live_in_year"] is None


def test_one_of_a_company_and_a_charity_live_confirms_the_live_one():
    two = rules.sole_body(GIFT, [
        {"body": "companies:companies/9", "rows": [_r("companies:companies/9", "companies", "1980-01-01", "2010-03-01", kind="companies")]},
        {"body": "charities:charities/CC4", "rows": [_r("charities:charities/CC4", "charities", "2011-01-01", number="CC4")]}])
    assert [(x["entity_ref"][-3:], x["rule"], x["grade"]) for x in two] == [
        ("CC4", rules.RULE_ONE_LIVE_BODY, "confirmed"), ("s/9", rules.RULE_ORG_NAME, "near")]
    assert two[1]["reason"].endswith(rules.NEAR_BODY_OTHER_LIVE) and two[0]["evidence"]["live_in_year"] == "CC4"


def test_a_removal_with_no_published_date_is_not_known_and_never_confirms():
    """A limited partnership the register lists as Removed, with no date, beside its Companies Office twin that says registered."""
    lp = {"body": "companies:companies/10", "rows": [
        _r("companies:companies/10", "companies", "2012-01-01", kind="other_incorporated", name="HART FOUNDATION LP"),
        _r("limited_partnerships:lp/1", "limited_partnerships", "2012-01-01", undated=True, name="HART FOUNDATION LP")]}
    [j] = rules.sole_body(GIFT, [lp])
    assert (j["grade"], j["evidence"]["alive_on_date"], j["evidence"]["register"]) == ("near", None, "limited partnerships")
    assert [x["register"] for x in j["evidence"]["registers"]] == ["other incorporated bodies", "limited partnerships"]   # each row its own
    assert j["reason"] == rules.body_reason(["limited partnerships"], rules.NEAR_BODY_UNDATED)
    other = {"body": "charities:charities/CC5", "rows": [_r("charities:charities/CC5", "charities", "2000-01-01")]}
    both = rules.sole_body(GIFT, [lp, other])
    assert all(x["grade"] == "near" and x["reason"].endswith(rules.NEAR_BODY_UNDATED_SEVERAL) for x in both)
    # registered after the year is not live whatever its removal
    late = dict(lp, rows=[dict(r, registered_on="2024-02-01") for r in lp["rows"]])
    assert rules.sole_body(GIFT, [late])[0]["reason"].endswith(rules.NEAR_BODY_NOT_YET)


def test_the_body_dates_take_the_formation_registers_over_the_charity():
    rows = [_r("companies:c", "companies", "1995-01-01", kind="companies"), _r("charities:x", "charities", "2009-01-01", "2014-01-01")]
    assert rules.body_dates(rows) == {"registered_on": rules._d("1995-01-01"), "removed": False, "removed_on": None, "removal_undated": False}
    assert rules.body_dates(rows[1:])["removed_on"] == rules._d("2014-01-01")


def test_the_charities_of_one_nzbn_are_one_body_removed_only_where_the_last_registered_is():
    """One NZBN under two charity numbers (fix-links-6): deregistered in February 2023, registered again in July 2023 under
    a new name and number. The body's charities rows are its registrations in turn, so it is removed only where the last
    registered says so; a 2024 row naming the new name confirms to the body, which is the earliest row."""
    rows = [_r("charities:charities/CC1", "charities", "2020-11-09", "2023-02-20", number="CC1", name="TAMA ACADEMY", named=False),
            _r("charities:charities/CC2", "charities", "2023-07-12", number="CC2", name="TAGATA ACADEMY")]
    assert rules.body_dates(rows) == {"registered_on": rules._d("2020-11-09"), "removed": False, "removed_on": None, "removal_undated": False}
    assert rules.body_dates(rows[::-1]) == rules.body_dates(rows)                                     # whichever order the rows come
    assert rules.body_dates([rows[0], dict(rows[1], removed_on="2025-01-01")]) == \
        {"registered_on": rules._d("2020-11-09"), "removed": True, "removed_on": rules._d("2025-01-01"), "removal_undated": False}
    assert rules.body_dates([rows[0], dict(rows[1], removal_undated=True)])["removal_undated"] is True
    # the last registered: the latest date, a row with no date counting earliest, then the largest ref by bytes
    assert rules.body_dates([rows[0], dict(rows[1], registered_on=None)]) == \
        {"registered_on": rules._d("2020-11-09"), "removed": True, "removed_on": rules._d("2023-02-20"), "removal_undated": False}
    assert rules.body_dates([dict(rows[0], registered_on="2023-07-12"), rows[1]])["removed"] is False
    assert rules.body_dates([dict(rows[0], entity_ref="charities:charities/CC3", registered_on="2023-07-12"), rows[1]])["removed"] is True
    # a formation row still decides over every charities row
    formed = [_r("companies:c", "companies", "1995-01-01", "2000-01-01", kind="companies")] + rows
    assert rules.body_dates(formed)["removed_on"] == rules._d("2000-01-01")
    body = {"body": "charities:charities/CC1", "rows": rows}
    row = dict(DECLARED, name_filed="Tagata Academy", name_key="tagata academy", started_on="2024-03-31")
    [j] = rules.body_on_date(row, [body])
    assert (j["entity_ref"], j["rule"], j["grade"], j["evidence"]["outcome"]) == \
        ("charities:charities/CC1", rules.RULE_SOLE_BODY_DATED, "confirmed", "sole")
    assert (j["evidence"]["company"], j["evidence"]["company_number"], j["evidence"]["registered_on"], j["evidence"]["removed_on"]) == \
        ("TAGATA ACADEMY", "CC1", "2020-11-09", None)
    assert [x["entity_ref"] for x in j["evidence"]["registers"]] == ["charities:charities/CC1", "charities:charities/CC2"]
    # before the first registration: not yet; between the two: the earlier registration stood
    assert rules.body_on_date(dict(row, started_on="2019-06-30"), [body])[0]["evidence"]["outcome"] == "not_yet"
    assert rules.body_on_date(dict(row, started_on="2023-04-30"), [body])[0]["grade"] == "confirmed"


# ── ruling 125 (links-5): the rules on every organisation-named row, judged on the row's own date ──────────────────

HOLDING = {"ref": "companies:companies/1/shareholder/1", "register": "companies", "view": "shareholders", "name_filed": "Hart Foundation",
           "name_key": "hart foundation", "started_on": None, "ended_on": None}
DECLARED = {"ref": "mp_interests:2021/hart/3", "register": "mp_interests", "view": "mp_interests", "name_filed": "Hart Foundation Limited",
            "name_key": "hart foundation", "started_on": "2021-01-31", "ended_on": None}


def test_the_one_live_body_today_was_not_alive_on_the_row_s_date_and_the_one_that_was_is_confirmed():
    """Two companies of the name: the one live today was registered in 2023, after a 2021 interests return; the other was
    removed in 2022, so on the return's date it was the only one alive. Today's answer would be the wrong company."""
    two = rules.body_on_date(DECLARED, [
        {"body": "companies:companies/new", "rows": [_r("companies:companies/new", "companies", "2023-05-01", number="9000001", kind="companies")]},
        {"body": "companies:companies/old", "rows": [_r("companies:companies/old", "companies", "2010-01-01", "2022-06-30", number="1000001", kind="companies")]}])
    assert [(x["entity_ref"][-3:], x["rule"], x["grade"]) for x in two] == [
        ("new", rules.RULE_ORG_NAME, "near"), ("old", rules.RULE_ONE_LIVE_BODY_DATED, "confirmed")]
    assert two[1]["evidence"]["live_in_year"] == "1000001" and two[1]["evidence"]["outcome"] == "one_live"
    assert two[1]["evidence"]["date_is"] == "the interests return's date" and two[1]["evidence"]["dated"] is True
    assert two[0]["reason"] == ("a name match on the companies register; the row carries no official number; several bodies carry this "
                                "name; this one was not live on the row's date, and the one that was is confirmed")
    # the same two bodies against a row dated today: the new company is the one live, the removed one is not
    today = dict(DECLARED, started_on="2026-10-30")
    now = rules.body_on_date(today, [
        {"body": "companies:companies/new", "rows": [_r("companies:companies/new", "companies", "2023-05-01", number="9000001", kind="companies")]},
        {"body": "companies:companies/old", "rows": [_r("companies:companies/old", "companies", "2010-01-01", "2022-06-30", number="1000001", kind="companies")]}])
    assert [(x["entity_ref"][-3:], x["grade"]) for x in now] == [("new", "confirmed"), ("old", "near")]


def test_one_body_of_the_name_live_today_but_registered_after_the_row_s_date_stays_near():
    [j] = rules.body_on_date(DECLARED, [{"body": "companies:companies/new", "rows": [
        _r("companies:companies/new", "companies", "2023-05-01", number="9000001", kind="companies")]}])
    assert (j["rule"], j["grade"], j["evidence"]["outcome"], j["evidence"]["alive_on_date"]) == (rules.RULE_ORG_NAME, "near", "not_yet", False)
    assert j["reason"].endswith("one body carries this name, but it was registered after the row's date")
    # registered before and never removed: confirmed, sole, on the row's date
    [k] = rules.body_on_date(DECLARED, [{"body": "companies:companies/old", "rows": [
        _r("companies:companies/old", "companies", "2010-01-01", number="1000001", kind="companies")]}])
    assert (k["rule"], k["grade"], k["evidence"]["outcome"]) == (rules.RULE_SOLE_BODY_DATED, "confirmed", "sole")
    # removed before the date: near, "removed before the row's date"
    [m] = rules.body_on_date(DECLARED, [{"body": "companies:companies/old", "rows": [
        _r("companies:companies/old", "companies", "2010-01-01", "2020-12-31", number="1000001", kind="companies")]}])
    assert (m["grade"], m["evidence"]["outcome"]) == ("near", "gone") and m["reason"].endswith("removed before the row's date")
    # removed on the day itself was live on it; registered on the day itself was live on it
    for body in (_r("companies:companies/x", "companies", "2010-01-01", "2021-01-31", kind="companies"),
                 _r("companies:companies/x", "companies", "2021-01-31", kind="companies")):
        assert rules.body_on_date(DECLARED, [{"body": "companies:companies/x", "rows": [body]}])[0]["grade"] == "confirmed"


def test_an_undated_row_stays_near_as_undated_whatever_the_bodies_say():
    """A shareholding (`pub.shareholders` publishes no filing date today): the one company of the name, live since 1990, would
    confirm under @2, where an unknown date does not count against; under @3 the row is undated and stays near."""
    body = {"body": "companies:companies/7", "rows": [_r("companies:companies/7", "companies", "1990-02-01", number="400123", kind="companies")]}
    [j] = rules.body_on_date(HOLDING, [body])
    assert (j["rule"], j["grade"], j["evidence"]["outcome"], j["evidence"]["alive_on_date"], j["evidence"]["dated"]) == \
        (rules.RULE_ORG_NAME, "near", "undated_row", None, False)
    assert j["reason"] == "a name match on the companies register; the row carries no official number; " + rules.NEAR_BODY_UNDATED_ROW
    assert j["reason"].split("; ")[-1].startswith("undated")
    assert j["evidence"]["date_is"] == "the shareholding's filing (not published today)"
    assert rules.sole_body(dict(HOLDING, register="party_returns"), [body])[0]["grade"] == "confirmed"      # @2, as it was
    several = rules.body_on_date(HOLDING, [body, {"body": "charities:charities/CC9", "rows": [_r("charities:charities/CC9", "charities", "2001-01-01")]}])
    assert all(x["grade"] == "near" and x["evidence"]["outcome"] == "undated_row" for x in several)
    assert several[0]["evidence"]["companies_alive_on_date"] == 0 and several[0]["evidence"]["live_in_year"] is None


def test_a_donation_row_keeps_ruling_114_s_words_under_version_three():
    """The grades and reasons are @2's: a donor row's reason is byte for byte what ruling 114 stored; only the rule name moves."""
    gift = dict(GIFT, register="party_returns", view="party_return_donors")
    old = rules.sole_body(gift, [{"body": "charities:charities/CC2", "rows": [_r("charities:charities/CC2", "charities", "2008-06-30", "2015-01-01")]}])
    new = rules.body_on_date(gift, [{"body": "charities:charities/CC2", "rows": [_r("charities:charities/CC2", "charities", "2008-06-30", "2015-01-01")]}])
    assert old[0]["reason"] == new[0]["reason"] == rules.body_reason(["charities"], rules.NEAR_BODY_GONE)
    assert (old[0]["rule"], new[0]["rule"]) == (rules.RULE_ORG_NAME, rules.RULE_ORG_NAME)
    live = rules.body_on_date(gift, [{"body": "charities:charities/CC1", "rows": [_r("charities:charities/CC1", "charities", "2009-05-01", number="CC1")]}])
    assert (live[0]["rule"], live[0]["evidence"]["date_is"]) == (rules.RULE_SOLE_BODY_DATED, "the return's year")
    assert {rules.RULE_SOLE_BODY, rules.RULE_ONE_LIVE_BODY} <= rules.RETIRED and rules.RULE_SOLE_BODY_DATED not in rules.RETIRED
    for tail, template in ((rules.NEAR_BODY_NOT_YET, "not_yet"), (rules.NEAR_BODY_MANY_LIVE, "many_live")):
        assert tail == rules.BODY_TAILS[template].format(**rules.WHEN_DONATION)


# ── the build and check item 9 on the real engine ──────────────────────────

class _NoCommit:
    def __init__(self, conn):
        self.conn = conn

    def commit(self):
        pass

    def __getattr__(self, name):
        return getattr(self.conn, name)


@pytest.mark.slow
def test_the_build_confirms_by_body_and_check_nine_goes_red_on_planted_faults():
    import support.db as db
    from links import build, check
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    s = "scratch_links_bodies_test"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        conn = _NoCommit(raw)
        try:
            conn.execute(f"CREATE SCHEMA {s}")
            conn.execute(links.ddl(s))
            conn.execute(f"""INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, name_key, started_on, ended_on) VALUES
                ('party_returns:d1', 'party_returns', 'party_return_donors', 'd1', 'organisation', 'Hart Foundation', 'hart foundation', '2023-01-01', '2023-12-31'),
                ('party_returns:d2', 'party_returns', 'party_return_donors', 'd2', 'organisation', 'Kea Trust', 'kea', '2023-01-01', '2023-12-31'),
                ('party_returns:d3', 'party_returns', 'party_return_donors', 'd3', 'organisation', 'Moa Society', 'moa', '2023-01-01', '2023-12-31'),
                ('companies:h1', 'companies', 'shareholders', 'h1', 'organisation', 'Hart Foundation', 'hart foundation', NULL, NULL),
                ('mp_interests:i1', 'mp_interests', 'mp_interests', 'i1', 'organisation', 'Kea Trust', 'kea', '1995-01-31', NULL),
                ('societies:o1', 'societies', 'society_officers', 'o1', 'organisation', 'Moa Society', 'moa', '2024-01-01', '2024-06-01')""")
            conn.execute(f"""INSERT INTO {s}.bodies (entity_ref, org_key, register, kind, number, nzbn, name, registered_on, removed_on, removal_undated, body) VALUES
                ('companies:c7', 'hart foundation', 'companies', 'companies', '400123', '9429000000007', 'HART FOUNDATION LIMITED', '1990-02-01', NULL, false, 'companies:c7'),
                ('charities:CC2', 'hart foundation', 'charities', NULL, 'CC2', '9429000000007', 'HART FOUNDATION', '2008-06-30', '2015-01-01', false, 'companies:c7'),
                ('charities:CC3', 'kea', 'charities', NULL, 'CC3', NULL, 'KEA TRUST', '2001-01-01', NULL, false, 'charities:CC3'),
                ('companies:c9', 'kea', 'companies', 'companies', '500', NULL, 'KEA LIMITED', '1980-01-01', '2010-01-01', false, 'companies:c9'),
                ('companies:c11', 'moa', 'companies', 'other_incorporated', '600', '9429000000011', 'MOA SOCIETY INCORPORATED', '1970-01-01', NULL, false, 'companies:c11'),
                ('societies:s1', 'moa', 'societies', NULL, '600', '9429000000011', 'MOA SOCIETY INCORPORATED', '1970-01-01', NULL, false, 'companies:c11')""")
            got = build.body_links(conn, s)
            assert (got["confirmed"], got["confirmed_one_live_of_several"], got["confirmed_by_register"], got["undated_rows"]) == \
                (3, 2, {"companies": 2, "charities": 1, "incorporated societies": 2}, 1)
            links_ = {(a, b): (r, g, o) for a, b, r, g, o in conn.execute(f"SELECT row_a, row_b, rule, grade, evidence->>'outcome' FROM {s}.links").fetchall()}
            assert links_[("companies:c7", "party_returns:d1")] == (rules.RULE_SOLE_BODY_DATED, "confirmed", "sole")   # one body on two registers
            assert links_[("charities:CC3", "party_returns:d2")] == (rules.RULE_ONE_LIVE_BODY_DATED, "confirmed", "one_live")
            assert links_[("companies:c9", "party_returns:d2")] == (rules.RULE_ORG_NAME, "near", "other_live")
            assert ("charities:CC2", "party_returns:d1") not in links_ and ("party_returns:d3", "societies:s1") not in links_
            # ruling 125: a shareholding with no date stays near, undated, though the one company of its name has stood since 1990
            assert links_[("companies:c7", "companies:h1")] == (rules.RULE_ORG_NAME, "near", "undated_row")
            assert got["by_view"]["shareholders"] == {"rows_with_a_body_of_the_name": 1, "undated_rows": 1, "confirmed": 0,
                                                      "confirmed_one_live_of_several": 0, "near": {"undated_row": 1}}
            # a 1995 interests return naming Kea: the charity live today was not registered until 2001; the company, removed in
            # 2010, was the one alive on the return's date, and is confirmed
            assert links_[("companies:c9", "mp_interests:i1")] == (rules.RULE_ONE_LIVE_BODY_DATED, "confirmed", "one_live")
            assert links_[("charities:CC3", "mp_interests:i1")] == (rules.RULE_ORG_NAME, "near", "other_live")
            assert links_[("companies:c11", "societies:o1")] == (rules.RULE_SOLE_BODY_DATED, "confirmed", "sole")   # an officer's appointment
            assert all(r["ok"] for r in check.check_ruling_114(conn, s)), check.check_ruling_114(conn, s)
            assert check.check_ruling_114(conn, s)[0]["confirmed"] == 5 and check.check_ruling_114(conn, s)[0]["undated_row"] == 0
            # planted: the interests row loses its date (its confirmed link is then an undated row's); and dated after the
            # company's removal (the linked body was not live on the row's date)
            conn.execute(f"UPDATE {s}.rows SET started_on = NULL WHERE ref = 'mp_interests:i1'")
            assert check.check_ruling_114(conn, s)[0]["undated_row"] == 1 and not check.check_ruling_114(conn, s)[0]["ok"]
            conn.execute(f"UPDATE {s}.rows SET started_on = '2015-01-31' WHERE ref = 'mp_interests:i1'")
            assert check.check_ruling_114(conn, s)[0]["linked_body_not_live_or_not_of_the_name"] == 1
            conn.execute(f"UPDATE {s}.rows SET started_on = '1995-01-31' WHERE ref = 'mp_interests:i1'")
            assert check.check_ruling_114(conn, s)[0]["ok"]
            # measurement 12 counts the same by view, apart from the links
            from links import measure as _m
            m12 = {x["view"]: x for x in _m.m12_ruling_125(conn, s)["by_view"]}
            assert (m12["mp_interests"]["exactly_one_body_of_the_name"], m12["mp_interests"]["several_bodies_one_live_on_the_date"],
                    m12["mp_interests"]["confirmed_one_live_of_several"], m12["shareholders"]["dated"],
                    m12["shareholders"]["near_links_by_outcome"]) == (0, 1, 1, 0, {"undated_row": 1})
            # measurement 3 judges a donor pair by the build's rule; measurement 10 lists the confirmations off the companies register
            from links import measure
            assert measure._org_judgment(conn, s, "party_returns:d2", "companies:c9")["reason"].endswith(rules.NEAR_BODY_OTHER_LIVE)
            m = measure.m10_ruling_114(conn, s)
            assert sorted((x["donor"], x["register"]) for x in m["confirmed_off_the_companies_register"]) == [
                ("Hart Foundation", "companies"), ("Kea Trust", "charities"), ("Moa Society", "incorporated societies")]
            assert m["bodies"] == [{"register": "charities", "rows": 2, "folded_onto_another_row": 1},
                                   {"register": "companies", "rows": 3, "folded_onto_another_row": 0},
                                   {"register": "societies", "rows": 1, "folded_onto_another_row": 1}]
            # planted: the other Kea body made live in the year (two live for the donor; and for the 1995 return the charity is still not)
            conn.execute(f"UPDATE {s}.bodies SET removed_on = NULL WHERE entity_ref = 'companies:c9'")
            assert not check.check_ruling_114(conn, s)[0]["ok"] and check.check_ruling_114(conn, s)[0]["another_body_live_or_undated"] == 1
            conn.execute(f"UPDATE {s}.bodies SET removed_on = '2010-01-01' WHERE entity_ref = 'companies:c9'")
            assert check.check_ruling_114(conn, s)[0]["ok"]
            # planted: the Hart company removed before the year (its charity row's later date does not keep it live)
            conn.execute(f"UPDATE {s}.bodies SET removed_on = '2020-01-01' WHERE entity_ref = 'companies:c7'")
            assert not check.check_ruling_114(conn, s)[0]["ok"]
            conn.execute(f"UPDATE {s}.bodies SET removed_on = NULL WHERE entity_ref = 'companies:c7'")
            # planted: the society row folded apart from its Companies Office twin (two bodies, one NZBN)
            conn.execute(f"UPDATE {s}.bodies SET body = 'societies:s1' WHERE entity_ref = 'societies:s1'")
            assert [r["ok"] for r in check.check_ruling_114(conn, s)] == [False, False]
        finally:
            raw.rollback()


# ── the bodies' NZBNs on the real engine (fix-links-6) ─────────────────────

#: the four registers `rows.BODY_SQL` reads, as stubs with the columns it reads
BODY_STUBS = {
    "companies": "key text, nzbn text, number text, register text, name text, registered_on date, removed_on date, status text",
    "societies": "key text, nzbn text, number text, name text, registered_on date, removed_on date, status text",
    "limited_partnerships": "key text, nzbn text, number text, name text, registered_on date, status text, name_withheld boolean",
    "charities": ("key text, nzbn text, number text, name text, registered_on date, deregistered_on date, status text, legal_structure text, "
                  "incorporation_number text"),
}
TRUST_ACT = "Charitable Trusts incorporated under the Charitable Trusts Act"
ZERO = "0000000000000"


class _PubCur:
    """A client-side cursor (the build's server-side one cannot fetch behind the COPY on the one connection the test has)."""

    def __init__(self, cur, fix):
        self._c, self._f, self.itersize = cur, fix, None

    def execute(self, q, *a, **k):
        self._c.execute(self._f(q), *a, **k)
        return self

    def executemany(self, q, *a, **k):
        return self._c.executemany(self._f(q), *a, **k)

    def __iter__(self):
        return iter(self._c)

    def __enter__(self):
        return self

    def __exit__(self, *e):
        self._c.close()

    def __getattr__(self, n):
        return getattr(self._c, n)


class _Pub:
    """The real connection in one transaction the test rolls back, `pub.` read from the scratch stubs."""

    def __init__(self, conn, pub):
        self.conn, self.pub = conn, pub

    def fix(self, q):
        return re.sub(r"\bpub\.", f"{self.pub}.", q)

    def execute(self, q, *a, **k):
        return self.conn.execute(self.fix(q), *a, **k)

    def cursor(self, *a, name=None, **k):
        return _PubCur(self.conn.cursor(*a, **k), self.fix)

    def commit(self):
        pass

    def __getattr__(self, n):
        return getattr(self.conn, n)


@pytest.mark.slow
def test_an_all_zero_nzbn_is_none_and_the_charities_of_one_nzbn_are_one_body_on_the_engine():
    """`rows.gather_bodies` over stub registers shaped like the live fault (30 October 2026): three charities carrying the
    placeholder `0000000000000` (one a trust board by its number), one NZBN under two charity numbers with no Companies
    Office row, one under two charity numbers that is a company, and one that is a society. Then the build confirms a
    2024 row naming the re-registered charity's new name to the one body, check item 9 is green on both lines, and goes
    red when the body is split or the placeholder put back."""
    import support.db as db
    from links import build, check, rows
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    s, p = "scratch_links_bodies_nzbn_test", "scratch_links_bodies_nzbn_pub"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        conn = _Pub(_NoCommit(raw), p)
        try:
            conn.execute(f"CREATE SCHEMA {s}")
            conn.execute(f"CREATE SCHEMA {p}")
            conn.execute(links.ddl(s))
            for table, cols in BODY_STUBS.items():
                conn.execute(f"CREATE TABLE {p}.{table} ({cols})")
            conn.execute(f"""INSERT INTO {p}.companies VALUES
                ('companies/9429000000001', '9429000000001', '2731452', 'charitable_trust_board', 'KOWHAI TRUST BOARD', '2010-01-01', NULL, 'Registered'),
                ('companies/9429000000002', '9429000000002', '700', 'companies', 'RATA HOLDINGS LIMITED', '2000-01-01', NULL, 'Registered')""")
            conn.execute(f"""INSERT INTO {p}.societies VALUES
                ('societies/600', '9429000000040', '600', 'MOA SOCIETY INCORPORATED', '1970-01-01', NULL, 'Registered')""")
            conn.execute(f"""INSERT INTO {p}.limited_partnerships VALUES
                ('lp/1', '9429000000050', 'LP1', 'KAURI LP', '2012-01-01', 'Registered', false)""")
            conn.execute(f"""INSERT INTO {p}.charities VALUES
                ('charities/CC20', %(z)s, 'CC20', 'KOWHAI TRUST', '2015-01-01', NULL, 'Registered', %(t)s, '2731452'),
                ('charities/CC21', %(z)s, 'CC21', 'NIKAU SOCIETY', '2016-01-01', NULL, 'Registered', NULL, NULL),
                ('charities/CC22', %(z)s, 'CC22', 'PUKA SOCIETY', '2017-01-01', NULL, 'Registered', NULL, NULL),
                ('charities/CC30', '9429000000030', 'CC30', 'TAMA ACADEMY', '2020-11-09', '2023-02-20', 'Deregistered', NULL, NULL),
                ('charities/CC31', '9429000000030', 'CC31', 'TAGATA ACADEMY', '2023-07-12', NULL, 'Registered', %(t)s, NULL),
                ('charities/CC10', '9429000000002', 'CC10', 'RATA FOUNDATION', '2005-01-01', '2008-06-30', 'Deregistered', NULL, NULL),
                ('charities/CC11', '9429000000002', 'CC11', 'RATA FOUNDATION', '2010-01-01', NULL, 'Registered', 'Company', '700'),
                ('charities/CC40', '9429000000040', 'CC40', 'MOA SOCIETY', '2009-01-01', '2012-01-01', 'Deregistered', NULL, NULL),
                ('charities/CC41', '9429000000040', 'CC41', 'MOA SOCIETY', NULL, NULL, 'Registered', NULL, NULL)""", {"z": ZERO, "t": TRUST_ACT})
            with raw.cursor() as w:
                assert rows.gather_bodies(conn, conn, w, s) == 13
            bodies = {ref: (nzbn, body) for ref, nzbn, body in conn.execute(f"SELECT entity_ref, nzbn, body FROM {s}.bodies").fetchall()}
            assert len(bodies) == 13
            # line 1: the placeholder is no NZBN; the rows stand, each its own body unless its number joins a Companies Office row
            assert {bodies[f"charities:charities/CC2{i}"] for i in (0, 1, 2)} == \
                {(None, "companies:companies/9429000000001"), (None, "charities:charities/CC21"), (None, "charities:charities/CC22")}
            assert conn.execute(f"SELECT count(*) FROM {s}.bodies WHERE nzbn ~ '^0+$'").fetchone()[0] == 0
            # line 2: the charities of one NZBN are one body: the earliest charities row, else the company, else the society
            assert bodies["charities:charities/CC30"] == bodies["charities:charities/CC31"] == ("9429000000030", "charities:charities/CC30")
            assert bodies["charities:charities/CC10"] == bodies["charities:charities/CC11"] == ("9429000000002", "companies:companies/9429000000002")
            assert bodies["charities:charities/CC40"] == bodies["charities:charities/CC41"] == ("9429000000040", "societies:societies/600")
            assert bodies["societies:societies/600"] == ("9429000000040", "societies:societies/600")
            assert bodies["limited_partnerships:lp/1"] == ("9429000000050", "limited_partnerships:lp/1")
            assert conn.execute(f"SELECT count(*) FROM (SELECT nzbn FROM {s}.bodies WHERE nzbn IS NOT NULL GROUP BY nzbn HAVING count(DISTINCT body) > 1) d"
                                ).fetchone()[0] == 0
            # the build: a 2024 return naming the new name, a 2022 one naming the old, confirm to the one body; the company
            # under two charity numbers and the trust board behind a placeholder confirm as before
            conn.execute(f"""INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, name_key, started_on, ended_on) VALUES
                ('mp_interests:i2', 'mp_interests', 'mp_interests', 'i2', 'organisation', 'Tagata Academy', 'tagata academy', '2024-03-31', NULL),
                ('mp_interests:i3', 'mp_interests', 'mp_interests', 'i3', 'organisation', 'Tama Academy', 'tama academy', '2022-01-31', NULL),
                ('mp_interests:i4', 'mp_interests', 'mp_interests', 'i4', 'organisation', 'Tagata Academy', 'tagata academy', '2019-06-30', NULL),
                ('party_returns:d4', 'party_returns', 'party_return_donors', 'd4', 'organisation', 'Rata Foundation', 'rata foundation', '2023-01-01', '2023-12-31'),
                ('mp_interests:i5', 'mp_interests', 'mp_interests', 'i5', 'organisation', 'Kowhai Trust', 'kowhai trust', '2024-01-31', NULL)""")
            got = build.body_links(conn, s)
            assert (got["confirmed"], got["confirmed_one_live_of_several"], got["near"]) == (4, 0, {"not_yet": 1})
            links_ = {(a, b): (r, g, o) for a, b, r, g, o in conn.execute(f"SELECT row_a, row_b, rule, grade, evidence->>'outcome' FROM {s}.links").fetchall()}
            assert links_[("charities:charities/CC30", "mp_interests:i2")] == (rules.RULE_SOLE_BODY_DATED, "confirmed", "sole")
            assert links_[("charities:charities/CC30", "mp_interests:i3")] == (rules.RULE_SOLE_BODY_DATED, "confirmed", "sole")
            assert links_[("charities:charities/CC30", "mp_interests:i4")] == (rules.RULE_ORG_NAME, "near", "not_yet")
            assert links_[("companies:companies/9429000000002", "party_returns:d4")] == (rules.RULE_SOLE_BODY_DATED, "confirmed", "sole")
            assert links_[("companies:companies/9429000000001", "mp_interests:i5")] == (rules.RULE_SOLE_BODY_DATED, "confirmed", "sole")
            assert not any("charities:charities/CC31" in k for k in links_)
            item = check.check_ruling_114(conn, s)
            assert [r["ok"] for r in item] == [True, True] and item[0]["confirmed"] == 4 and item[1]["nzbns_on_two_bodies"] == 0, item
            # the check reads the body's registrations in turn as the build does: a removal of the last registered after
            # the row's date keeps the row live; before it, the linked body was not live
            conn.execute(f"UPDATE {s}.bodies SET removed_on = '2025-01-01' WHERE entity_ref = 'charities:charities/CC31'")
            assert check.check_ruling_114(conn, s)[0]["ok"]
            conn.execute(f"UPDATE {s}.bodies SET removed_on = '2024-01-01' WHERE entity_ref = 'charities:charities/CC31'")
            assert check.check_ruling_114(conn, s)[0]["linked_body_not_live_or_not_of_the_name"] == 1
            conn.execute(f"UPDATE {s}.bodies SET removed_on = NULL WHERE entity_ref = 'charities:charities/CC31'")
            # planted: the later charity number its own body again (one NZBN, two bodies)
            conn.execute(f"UPDATE {s}.bodies SET body = entity_ref WHERE entity_ref = 'charities:charities/CC31'")
            assert check.check_ruling_114(conn, s)[1] == {"check": "a body on two registers is one body: no NZBN names two bodies",
                                                          "nzbns_on_two_bodies": 1, "ok": False}
            conn.execute(f"UPDATE {s}.bodies SET body = 'charities:charities/CC30' WHERE entity_ref = 'charities:charities/CC31'")
            # planted: the placeholder put back on its three rows (one "NZBN", three bodies)
            conn.execute(f"UPDATE {s}.bodies SET nzbn = %s WHERE register = 'charities' AND nzbn IS NULL", (ZERO,))
            assert check.check_ruling_114(conn, s)[1]["nzbns_on_two_bodies"] == 1
        finally:
            raw.rollback()
