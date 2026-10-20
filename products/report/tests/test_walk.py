"""The walk's pure parts, on fixtures: hub names, near grading, an item's
shape; and the design defaults are settings, not code."""
from products.report import catalogue as cat
from products.report import walk


def test_nominee_trustee_and_crown_names_are_hubs_and_plain_names_are_not():
    assert walk.name_hub("THOMSON O'NEIL NOMINEES LIMITED")["kind"] == "nominee"
    assert walk.name_hub("NEW ZEALAND TRUSTEE SERVICES LIMITED")["kind"] == "nominee"
    assert walk.name_hub("Her Majesty the Queen in right of New Zealand")["kind"] == "crown"
    assert walk.name_hub("Minister of Finance")["kind"] == "crown"
    assert walk.name_hub("RANK GROUP LIMITED") is None and walk.name_hub("Crowne Plaza Limited") is None
    assert "never as an owner" in walk.name_hub("ABC Nominees Ltd")["text"]


def test_an_item_carries_ref_dates_citation_and_grade():
    v = cat.BY_NAME["directors"]
    r = {"key": "companies/1/director/a", "entity_key": "companies/1", "full_name": "Jane DOE", "role_type": "Director",
         "appointed_on": None, "ended_on": None, "in_latest": True, "first_file": "f1", "last_file": "f2", "suppressed": False,
         "document": None}
    it = walk.item(v, r, "ACME LIMITED")
    assert it["ref"] == "companies:companies/1/director/a" and it["grade"] == "confirmed" and it["flags"] == []
    assert it["dates"]["undated"] and "in the files from f1 to f2" in it["dates"]["text"]
    assert it["citation"]["view"] == "directors" and it["statement"] == "Jane DOE: Director of ACME LIMITED"
    walk.near(it, walk.NEAR_THROUGH_PEOPLE, "x@1")
    assert it["grade"] == "near" and "more than one person" in it["reason"] and it["rule"] == "x@1"


def test_the_two_design_defaults_are_settings():
    assert walk.SETTINGS["through_people"] == "near"
    assert walk.SETTINGS["hub_roles"] == 50 and walk.SETTINGS["thousand_address"] == 1000 and walk.SETTINGS["busy_address"] == 50
    assert walk.LIMITS["members"] > 0 and walk.LIMITS["links"] > 0


def test_a_printed_name_is_matched_whole_or_by_first_and_last_word():
    assert walk.first_last("Tracey Lee McLELLAN") == "tracey mclellan" and walk.first_last("Hōne Pani Tamati Waka Nene HARAWIRA") == "hone harawira"
    assert walk.first_last("Hōne") == "hone" and walk.first_last("") == ""
    assert "near, never confirmed" in walk.NEAR_BY_NAME and walk.NAMED_ROWS["members"][0][3] == ("total", "outside")
