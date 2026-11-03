"""Ruling 142 (4 November 2026): the rules that read a private value (links/identifiers.py, links/rules.py), on made-up
rows. Each fails against the code before them (no such rule, no such sorting)."""
from links import identifiers as li
from links import rules

PLACE, STREET = rules.PLACE_LEVELS[1], "number and street"
P = {"ref": "courts:p1", "kind": "person", "how": "nearest name on the page"}
B = {"ref": "courts:b1", "kind": "organisation", "how": "nearest name on the page"}


def grades(out):
    return sorted((a, b, j["rule"], j["grade"]) for a, b, j in out)


def test_title_confirmed_by_a_name_at_a_place_near_at_street_only_and_near_without_a_name():
    owners = [{"ref": "linz:o1", "kind": "person"}, {"ref": "linz:o2", "kind": "organisation"}]
    named = [("courts:p1", "linz:o1")]
    assert grades(rules.judge_address_title({"level": PLACE, "named": named, "tie": P, "owners": owners})) == [
        ("courts:p1", "linz:o1", rules.RULE_ADDRESS_TITLE, "confirmed")]
    assert grades(rules.judge_address_title({"level": STREET, "named": named, "tie": P, "owners": owners})) == [
        ("courts:p1", "linz:o1", rules.RULE_ADDRESS_TITLE, "near")]
    # no name: the tie to each owner of its kind, at a place level only
    assert grades(rules.judge_address_title({"level": PLACE, "named": [], "tie": P, "owners": owners})) == [
        ("courts:p1", "linz:o1", rules.RULE_ADDRESS_TITLE, "near")]
    assert rules.judge_address_title({"level": STREET, "named": [], "tie": P, "owners": owners}) == []
    assert rules.judge_address_title({"level": PLACE, "named": [], "tie": None, "owners": owners}) == []


def test_judgment_to_judgment():
    shared = [("courts:a", "courts:b")]
    assert grades(rules.judge_address_judgment({"level": PLACE, "shared": shared})) == [
        ("courts:a", "courts:b", rules.RULE_ADDRESS_JUDGMENT, "confirmed")]
    assert grades(rules.judge_address_judgment({"level": STREET, "shared": shared}))[0][3] == "near"
    ta, tb = {**P, "ref": "courts:x"}, {**P, "ref": "courts:y"}
    assert grades(rules.judge_address_judgment({"level": PLACE, "shared": [], "tie_a": ta, "tie_b": tb}))[0][3] == "near"
    assert rules.judge_address_judgment({"level": STREET, "shared": [], "tie_a": ta, "tie_b": tb}) == []
    assert rules.judge_address_judgment({"level": PLACE, "shared": [], "tie_a": ta, "tie_b": {**B, "ref": "courts:z"}}) == []


def test_insolvency_at_a_place_only():
    est = [{"ref": "insolvency:e", "kind": "person"}]
    assert grades(rules.judge_address_insolvency({"level": PLACE, "named": [("courts:p1", "insolvency:e")], "tie": P,
                                                  "estates": est}))[0][3] == "confirmed"
    assert grades(rules.judge_address_insolvency({"level": PLACE, "named": [], "tie": P, "estates": est}))[0][3] == "near"
    assert rules.judge_address_insolvency({"level": STREET, "named": [("courts:p1", "insolvency:e")], "tie": P,
                                           "estates": est}) == []


def test_office_named_busy_and_one_company():
    one = {"companies:c": PLACE}
    assert grades(rules.judge_address_office({"companies": one, "named": [("courts:b1", "companies:c")], "tie": B}))[0][3] == "confirmed"
    busy = {f"companies:c{i}": PLACE for i in range(rules.OFFICE_BUSY + 1)}
    out = rules.judge_address_office({"companies": busy, "named": [("courts:b1", "companies:c0")], "tie": B})
    assert [j["grade"] for *_, j in out] == ["near"] and out[0][2]["reason"] == rules.NEAR_OFFICE_BUSY
    assert rules.judge_address_office({"companies": busy, "named": [], "tie": B}) == []
    assert grades(rules.judge_address_office({"companies": one, "named": [], "tie": B}))[0][3] == "near"
    # a person printed nearest is not a company; two companies at the street and town without a name is none
    assert rules.judge_address_office({"companies": one, "named": [], "tie": P}) == []
    assert rules.judge_address_office({"companies": {"companies:c": PLACE, "companies:d": PLACE}, "named": [], "tie": B}) == []
    assert rules.judge_address_office({"companies": {"companies:c": STREET}, "named": [], "tie": B}) == []


def test_shared_contact_confirmed_where_the_names_agree_near_where_they_differ():
    t = lambda d, ref, name: {"document": d, "ref": ref, "kind": "person", "name": name, "how": "person field"}  # noqa: E731
    out = rules.judge_shared_contact("email", [t("d1", "courts:a", "jo bloggs"), t("d2", "courts:b", "jo bloggs"),
                                               t("d3", "courts:c", "ann other")])
    g = {(a, b): j["grade"] for a, b, j in out}
    assert g == {("courts:a", "courts:b"): "confirmed", ("courts:a", "courts:c"): "near", ("courts:b", "courts:c"): "near"}
    assert all("@" not in str(j["evidence"]) for *_, j in out), "a value never in a link's evidence"


def test_the_sorting_sets_offices_apart():
    assert li.category("email", "registry@justice.govt.nz", [], 1) == "courts, tribunals, government"
    assert li.category("email", "jo@smithlaw.co.nz", [], 1) == "law firms"
    assert li.category("email", "jo@gmail.com", [], 1) == "personal webmail"
    assert li.category("email", "jo@gmail.com", [], li.RECUR_CASES) in li.OFFICE
    assert li.category("email", "jo@acmeplumbing.co.nz", [], 1, company_stems={"acmeplumbing"}) == "companies"
    assert li.category("phone", "0800123456", [""], 1) in li.OFFICE
    assert li.category("phone", "093001234", ["the Registry, High Court at Auckland"], 1) in li.OFFICE
    assert li.category("phone", "021555666", ["his phone"], 1) == "other"
    assert li.category("address", "x", ["solicitors for the applicant"], 1) in li.OFFICE
    assert li.category("address", "x", [""], 1, office_town=True) in li.OFFICE_CATS - li.ADDRESS_CATS
    assert li.category("address", "x", [""], 1) in li.ADDRESS_CATS


def test_the_tie_is_the_name_printed_nearest():
    text = "The applicant Jane Roe lives at 12 Example Street, Sometown. The respondent, Acme Limited, ... " + "x" * 50
    cands = [{"key": "k1", "ref": "courts:k1", "kind": "person", "name_filed": "Jane Roe"},
             {"key": "k2", "ref": "courts:k2", "kind": "organisation", "name_filed": "Acme Limited"}]
    r, d = li.nearest(text, "12 Example Street, Sometown", cands)
    assert r["key"] == "k1" and d == len(" lives at ")
    r, d = li.nearest(text, "12 Example Street, Sometown", cands[1:])
    assert r["key"] == "k2"
    far = "Jane Roe " + "y" * (li.TIE_WINDOW + 10) + " 12 Example Street"
    assert li.nearest(far, "12 Example Street", cands) == (None, None)
    assert li.nearest(text, "not on the page", cands) == (None, None)


def test_phone_key_and_value_key():
    assert li.phone_key("+64 9 300 1234") == "093001234"
    assert li.value_key("email", " Jo@Example.CO.NZ ") == "jo@example.co.nz"


def test_linz_owners_are_rows_read_from_their_parts():
    from links import rows
    src = [x for x in rows.SOURCES if x[1] == "linz_title_owners"]
    assert src and src[0][0] == "linz"
    rec = rows.row_record("linz", "linz_title_owners", ("linz/owners/1", "John Fitzgerald SMITH", None, None, None, None,
                                                         None, "sha", False, "John Fitzgerald", None, "SMITH"))
    assert rec[4] == "person" and rec[10] == "john smith" and rec[12] is True


def test_every_judged_evidence_key_is_one_the_check_allows():
    from links.check import IDENTIFIER_EVIDENCE
    t = {"document": "d1", "ref": "courts:a", "kind": "person", "name": "x", "how": "person field"}
    outs = (rules.judge_address_title({"level": PLACE, "named": [], "tie": P, "owners": [{"ref": "linz:o", "kind": "person"}]})
            + rules.judge_address_judgment({"level": PLACE, "shared": [("courts:a", "courts:b")]})
            + rules.judge_address_insolvency({"level": PLACE, "named": [], "tie": P, "estates": [{"ref": "insolvency:e", "kind": "person"}]})
            + rules.judge_address_office({"companies": {"companies:c": PLACE}, "named": [], "tie": B})
            + rules.judge_shared_contact("phone", [t, {**t, "document": "d2", "ref": "courts:b"}]))
    assert len(outs) == 5
    for *_, j in outs:
        assert set(j["evidence"]) <= IDENTIFIER_EVIDENCE, j["evidence"]
