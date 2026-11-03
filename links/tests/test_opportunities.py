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
