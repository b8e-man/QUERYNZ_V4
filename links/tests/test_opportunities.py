"""The linking opportunities register (links/opportunities.py): every opportunity a profile declares is the links
lane's, by a rule it builds, the name sightings, or a measurement owed to Arthur."""
import pytest

from links import opportunities as O


def _prof(slug, field, links):
    return {slug: {"slug": slug, "version": 1, "extract": [
        {"field": field, "iteration": 1, "by": "rules", "ask": "read it", "private": False, "kinds": None,
         "lands": ["things.value"], "links": links}]}}


KNOWN = {"full-name@1", "official-number@1"}
NAME = {"key": "name", "to": "every row of pub.names", "rule": "full-name@1"}
NZBN = {"key": "nzbn", "to": "a company on the register", "rule": None}


def test_the_live_register_covers_every_declared_opportunity_and_names_only_rules_the_lane_builds():
    assert O.problems() == []
    for row in O.listing():
        assert row["status"] in O.STATUSES, row


def test_the_rule_ids_are_the_lane_s_own_and_never_a_retired_one():
    ids = O.rule_ids()
    assert {"full-name@1", "name-only@1", "organisation-name@1", "organisation-sole-company@3",
            "organisation-one-live-company@3"} <= ids
    assert "organisation-sole-company@1" not in ids and "organisation-sole-company@2" not in ids


@pytest.mark.parametrize("profiles, register, why", [
    (_prof("toy-a", "parties", [NAME]), (), "declares a name opportunity (every row of pub.names) the links register lacks"),
    (_prof("toy-a", "parties", [NAME]), (O.Entry("toy-*", "parties", "name", "rule", ("full-name@9",)),),
     "the rule full-name@9 is not one the links lane builds"),
    (_prof("toy-a", "parties", [NAME]), (O.Entry("toy-*", "parties", "name", "rule", ("official-number@1",)),),
     "names the rule full-name@1, which its register entry does not"),
    (_prof("toy-a", "ids", [NZBN]), (O.Entry("toy-*", "ids", "nzbn", "measure owed"),), "no decision named"),
    (_prof("toy-a", "ids", [NZBN]), (O.Entry("toy-*", "ids", "nzbn", "rule", ("official-number@1",)),), "the profile names none"),
    (_prof("toy-a", "ids", [NZBN]), (O.Entry("toy-*", "ids", "nzbn", "measure owed", decision="d"),
                                     O.Entry("toy-*", "ids", "email", "measure owed", decision="d")), "a register entry no profile declares"),
    (_prof("toy-a", "parties", [{**NAME, "rule": None}]), (O.Entry("toy-*", "parties", "name", "sighting"),),
     "the sightings do not scan the toy lane"),
    (_prof("toy-a", "ids", [NZBN]), (O.Entry("toy-*", "ids", "nzbn", "maybe", decision="d"),), "status 'maybe'"),
])
def test_each_gap_between_the_profiles_and_the_register_is_a_problem(profiles, register, why):
    got = O.problems(profiles, register, KNOWN)
    assert any(why in p for p in got), got


def test_a_well_kept_register_has_no_problem():
    profiles = {**_prof("toy-a", "parties", [NAME]), **_prof("toy-b", "ids", [NZBN])}
    register = (O.Entry("toy-*", "parties", "name", "rule", ("full-name@1",)),
                O.Entry("toy-b", "ids", "nzbn", "measure owed", decision="d"))
    assert O.problems(profiles, register, KNOWN) == []
    assert [r["status"] for r in O.listing(profiles, register)] == ["rule", "measure owed"]


# --- every published view that names a person or a body (3 November 2026) ---

CAT = {"toy_people": [("key", "text"), ("full_name", "text")], "toy_numbers": [("key", "text"), ("nzbn", "text")],
       "toy_flags": [("key", "text"), ("area_names_address", "boolean")], "toy_figures": [("key", "text"), ("amount", "numeric")]}


def test_a_view_naming_anybody_is_read_or_excluded_with_a_reason():
    assert O.view_problems(CAT, read={"toy_people"}, excluded={"toy_numbers": "the register's own number"}) == []
    got = O.view_problems(CAT, read={"toy_people"}, excluded={})
    assert len(got) == 1 and got[0].startswith("pub.toy_numbers names a person or a body (nzbn)")
    # a boolean flag column and a figures view name nobody
    assert O.view_problems(CAT, read=set(), excluded={"toy_people": "x", "toy_numbers": "y"}) == []


@pytest.mark.parametrize("read, excluded, why", [
    ({"toy_people", "toy_numbers"}, {"toy_numbers": "y"}, "is read and also excluded"),
    ({"toy_people"}, {"toy_numbers": " "}, "excluded with no reason"),
    ({"toy_people", "toy_numbers"}, {"toy_gone": "z"}, "no published view of that name carries a name or number column"),
    ({"toy_people", "toy_numbers"}, {"toy_figures": "z"}, "no published view of that name carries a name or number column"),
])
def test_an_exclusion_that_no_longer_holds_is_a_problem(read, excluded, why):
    got = O.view_problems(CAT, read=read, excluded=excluded)
    assert any(why in p for p in got), got


def test_the_lane_reads_the_views_arthur_named_on_3_november():
    read = O.views_read()
    for v in ("insolvency_companies", "company_insolvencies", "retirement_villages", "gazette_liquidations", "grant_recipients",
              "company_lookup_roles", "company_lookup_holdings", "insolvency_people", "rea_parties", "building_practitioners",
              "council_meeting_attendance", "minister_diary_attendees", "court_company_numbers", "court_documents"):
        assert v in read, v
    for v in ("award_notices",):                 # suppliers_named is a count; the suppliers are pub.award_suppliers, read
        assert v not in O.EXCLUDED
    assert O.EXCLUDED["linz_title_owners"].startswith("OWED")
    assert set(read) & set(O.EXCLUDED) == set()
