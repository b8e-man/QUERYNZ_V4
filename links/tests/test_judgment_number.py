"""Ruling 1 (Arthur, 3 November 2026): a court party is confirmed to the company whose NZBN or company number its
judgment prints, `official-number@1`'s kind of join; the number is tied to a party, not only to the document, by the
party's name (`judgment-number@1`). Invented values throughout."""
from links import build, opportunities, rules


def _c(ref, body, matches, doc="d1", kind="nzbn", value="9429000000011", view="court_judgment_parties", key="acme widgets"):
    return {"document": doc, "kind": kind, "value": value, "page": 1, "body": body, "company": "Acme Widgets Limited", "ref": ref,
            "view": view, "name_key": key, "name_filed": "Acme Widgets Ltd", "name_matches": matches}


def test_the_party_of_the_body_s_name_is_confirmed_and_another_party_of_the_document_is_not():
    counts, out = rules.judgment_numbers([_c("courts:p1", "companies:c/1", True),
                                          _c("courts:p2", "companies:c/1", False, key="kauri holdings")])
    assert [(r, b, j["grade"]) for r, b, j in out] == [("courts:p1", "companies:c/1", "confirmed")]
    assert out[0][2]["rule"] == "judgment-number@1" and out[0][2]["evidence"]["number"] == "NZBN"
    assert counts == {rules.JN_CONFIRMED: 1}


def test_a_number_is_never_a_link_to_the_document_alone():
    # two body parties, neither of the body's name: the number is tied to no party
    counts, out = rules.judgment_numbers([_c("courts:p1", "companies:c/1", False, key="kauri holdings"),
                                          _c("courts:p2", "companies:c/1", False, key="totara farms")])
    assert out == [] and counts == {rules.JN_UNTIED: 1}


def test_one_body_party_under_another_name_is_near_with_its_reason():
    counts, out = rules.judgment_numbers([_c("courts:p1", "companies:c/1", False, key="acme trading")])
    assert [(r, b, j["grade"], j["reason"]) for r, b, j in out] == [("courts:p1", "companies:c/1", "near", rules.NEAR_JN_OTHER_NAME)]
    assert counts == {rules.JN_OTHER_NAME: 1}
    # a text reader's row alone is never the one body party: no link
    assert rules.judgment_numbers([_c("courts:x", "companies:c/1", False, view="court_people")])[1] == []


def test_two_numbers_naming_two_bodies_of_the_party_s_name_are_near_to_each():
    counts, out = rules.judgment_numbers([_c("courts:p1", "companies:c/1", True),
                                          _c("courts:p1", "companies:c/2", True, kind="company_number", value="1001")])
    assert sorted((b, j["grade"], j["reason"]) for _, b, j in out) == [("companies:c/1", "near", rules.NEAR_JN_TWO_BODIES),
                                                                         ("companies:c/2", "near", rules.NEAR_JN_TWO_BODIES)]
    assert counts == {rules.JN_TWO: 2}


def test_documents_are_judged_apart():
    counts, out = rules.judgment_numbers([_c("courts:p1", "companies:c/1", True, doc="d1"),
                                          _c("courts:p9", "companies:c/1", False, doc="d2", key="kauri holdings"),
                                          _c("courts:p8", "companies:c/1", False, doc="d2", key="totara farms")])
    assert [(r, j["grade"]) for r, _, j in out] == [("courts:p1", "confirmed")]
    assert counts == {rules.JN_CONFIRMED: 1, rules.JN_UNTIED: 1}


def test_the_rule_is_built_and_the_register_names_it_for_the_court_identifiers():
    assert rules.RULE_JUDGMENT_NUMBER in opportunities.rule_ids()
    assert build.COURT_NUMBERS_VIEW == "pub.court_company_numbers"
    for key in ("nzbn", "company_number"):
        e = opportunities.entry_for("courts-judgment", "identifiers", key)
        assert e.status == "rule" and rules.RULE_JUDGMENT_NUMBER in e.rules, key
