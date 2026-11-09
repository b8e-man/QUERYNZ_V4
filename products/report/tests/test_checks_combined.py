"""Step 9 (ruling 157): the one report's combined checks. The inventory is held
against the frozen templates (every retired check carried once); each check
runs on small reports built by hand, and the ones that read a register are
shown to move when the row they rest on is taken away."""
import copy
import os

import pytest

from products.report import checks_combined as cc
from products.report import contract, template as tpl

AS_OF = "2026-11-09"


def item(ref, view, grade="confirmed", kind="person", title=None, **kw):
    it = {"ref": ref, "view": view, "grade": grade, "kind": kind, "title": title or ref.rsplit("/", 1)[-1],
          "statement": f"{title or ref} ({view})", "dates": {"text": "1 January 2020"}, "row": kw.pop("row", {}),
          "flags": kw.pop("flags", []), "suppressed": False, "rule": None, "reason": "a reason" if grade == "near" else None, "via": None}
    it.update(kw)
    return it


def report(subject, items=(), walk=None, **kw):
    r = {"subject": subject, "members": [], "group": {}, "hubs": [], "as_of": AS_OF,
         "sections": [{"name": "all", "items": list(items), "omitted_views": []}],
         "walk": dict({"links_built": True, "links_omitted": 0, "entities_omitted": 0, "entities_not_expanded": 0}, **(walk or {}))}
    r.update(kw)
    return r


CO = "companies:companies/9429000000001"
CO2 = "companies:companies/9429000000002"
CO3 = "companies:companies/9429000000003"
PERSON = "companies:companies/9429000000001/director/aaaaaaaaaaaa"


def company(ref=CO, status="Registered", registered="2010-01-01", grade="confirmed", **kw):
    return item(ref, "companies", grade, "organisation", title=kw.pop("title", ref[-4:] + " LIMITED"),
                row=dict({"status": status, "registered_on": registered, "entity_type": "LTD"}, **kw.pop("row", {})), **kw)


def liquidation(ref, on, via, appointed="2024-03-01", grade="confirmed", **kw):
    return item(ref, "gazette_liquidations", grade, "figure", row={"register_key": on.split(":", 1)[1], "appointed_on": appointed,
                                                                    "published_on": appointed}, via=via, **kw)


# ── the inventory ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("folder", sorted(cc.RETIRED))
def test_retired_inventory_is_the_frozen_templates(folder):
    t = tpl.load(os.path.join(tpl.USE_CASE_TEMPLATES, folder))
    assert tuple(r.__name__ for r in t.rules) == cc.RETIRED[folder], f"{folder}: its RULES differ from the inventory held here"


def test_the_inventory_covers_every_retired_template():
    on_disk = sorted(d for d in os.listdir(tpl.USE_CASE_TEMPLATES) if d[:2].isdigit() and "-" in d)
    assert on_disk == sorted(cc.RETIRED)


def test_every_retired_check_is_carried_once():
    carried = [f for fs in list(cc.MERGED.values()) + list(cc.COMMON.values()) for f in fs]
    retired = {f for fs in cc.RETIRED.values() for f in fs}
    assert sorted(set(carried)) == sorted(retired), (set(carried) ^ retired)
    assert len(carried) == len(set(carried)), [f for f in carried if carried.count(f) > 1]


def test_every_check_is_named_in_merged_and_once():
    names = [f.__name__.replace("_", "-") for f in cc.CHECKS]
    assert len(names) == len(set(names))
    assert set(names) == set(cc.MERGED)
    assert not set(names) & {r.__name__.replace("_", "-") for r in contract.COMMON_RULES}, "a common rule is checked twice"


def test_the_one_template_carries_the_combined_checks():
    t = tpl.by_name("one")
    assert t.stage == 1 and t.rules == cc.CHECKS and t.common_rules
    assert "stage1" in t.buckets


def _all(r):
    out = cc.run(r)
    for f, c in zip(out, cc.CHECKS):
        assert f["rule"] == c.__name__.replace("_", "-"), (f["rule"], c.__name__)
    return {f["rule"]: f for f in out}


@pytest.mark.parametrize("shape", ["company", "person", "charity"])
def test_every_check_runs_on_each_start_and_keeps_the_contract(shape):
    if shape == "company":
        r = report(company())
    elif shape == "person":
        r = report(item(PERSON, "directors", row={"in_latest": True}), [company(CO2, via=PERSON)])
    else:
        r = report(item("charities:charities/CC1", "charities", kind="organisation", row={"status": "Registered"}))
    flags = _all(r)
    assert len(flags) == len(cc.CHECKS)
    assert flags["registers-not-held"]["status"] == "blocked"


# ── checks that must move with the rows ─────────────────────────────────────

def test_insolvency_notice_on_the_entity_fires_red_and_clears_without_it():
    n = liquidation("gazette:gazette/1", CO, CO)
    r = report(company(), [n])
    f = cc.insolvency_notices(r)
    assert (f["status"], f["severity"]) == ("fired", "red") and n["ref"] in f["citations"]
    r["sections"][0]["items"] = []
    assert cc.insolvency_notices(r)["status"] == "clear"
    r["subject"]["row"]["status"] = "In Liquidation"
    f = cc.insolvency_notices(r)
    assert f["status"] == "fired" and "undated" in f["text"]


def test_a_person_repeat_failure_needs_two_and_a_namesakes_never_reds():
    p = item(PERSON, "directors", row={"in_latest": True})
    cos = [company(CO2, status="In Liquidation", via=PERSON), company(CO3, status="In Liquidation", via=PERSON)]
    r = report(p, cos)
    assert (cc.repeat_failure(r)["status"], cc.repeat_failure(r)["severity"]) == ("fired", "red")
    r["sections"][0]["items"] = cos[:1]
    assert cc.repeat_failure(r)["status"] == "blocked"   # one, and past roles are not held: never a clear
    r["sections"][0]["items"] = [cos[0], dict(cos[1], grade="near")]
    assert cc.repeat_failure(r)["severity"] == "amber"


def test_phoenix_pair_is_found_and_lost_with_the_dates():
    p = item(PERSON, "directors", row={"in_latest": True})
    failed = company(CO2, status="In Liquidation", via=PERSON)
    going = company(CO3, registered="2024-06-01", via=PERSON)
    n = liquidation("gazette:gazette/2", CO2, CO2, appointed="2024-03-01")
    r = report(p, [failed, going, n])
    f = cc.phoenix_signature(r)
    assert f["status"] == "fired" and f["severity"] == "red" and going["ref"] in f["citations"]
    going["row"]["registered_on"] = "2027-06-01"
    assert cc.phoenix_signature(r)["status"] != "fired"


def test_prohibition_red_confirmed_amber_near_blocked_on_a_first_stage():
    p = item(PERSON, "directors", row={"in_latest": True})
    pro = item("gazette:gazette/9/prohibition/1", "gazette_prohibitions", row={"ends_on": "2030-01-01"})
    r = report(p, [pro])
    assert cc.prohibition(r)["severity"] == "red" and cc.prohibition(r)["status"] == "fired"
    pro["grade"] = "near"
    assert cc.prohibition(r)["severity"] == "amber"
    r["sections"][0]["items"] = []
    assert cc.prohibition(r)["status"] == "clear"
    r["walk"]["stage1"] = {"stage": 1, "near_set_aside": 7}
    f = cc.prohibition(r)
    assert f["status"] == "blocked" and "second stage" in f["text"]
    assert cc.bankruptcy(report(p, []))["status"] == "blocked"   # a bankruptcy blank is never a clear


def test_regulator_listings_and_court_judgments_never_clear():
    p = item(PERSON, "directors", row={"in_latest": True})
    r = report(p, [])
    assert cc.regulator_listings(r)["status"] == "blocked"
    assert cc.court_judgments(r)["status"] == "blocked"
    ws = item("worksafe:1", "worksafe_parties")
    r["sections"][0]["items"] = [ws]
    assert (cc.regulator_listings(r)["status"], cc.regulator_listings(r)["severity"]) == ("fired", "red")
    ws["view"] = "fma_parties"
    assert cc.regulator_listings(r)["severity"] == "amber"


def test_holders_named_as_trustee_fire_on_a_company_and_clear_without():
    h = item(CO + "/shareholder/1", "shareholders", via=CO, row={"shareholder_type": "individual", "name": "A TRUSTEES LIMITED"})
    r = report(company(), [h])
    f = cc.holders_of_record(r)
    assert f["status"] == "fired" and "nominee, trustee" in f["text"]
    h["row"]["name"] = "JANE PLAIN"
    assert cc.holders_of_record(r)["status"] == "clear"
    r["sections"][0]["items"] = []
    assert cc.holders_of_record(r)["status"] == "blocked"


def test_shared_office_compares_lines_and_never_quotes_them():
    p = item(PERSON, "directors", row={"in_latest": True})
    failed = company(CO2, status="In Liquidation", via=PERSON)
    going = company(CO3, via=PERSON)
    n = liquidation("gazette:gazette/3", CO2, CO2, appointed="2024-03-01")
    line = {"line_1": "12 Example Street", "postcode": "1010"}
    a1 = item(CO2 + "/address/1", "company_addresses", kind="figure", row=dict(line, entity_key=CO2.split(":")[1], started_on="2020-01-01",
                                                                               in_latest=False))
    a2 = item(CO3 + "/address/1", "company_addresses", kind="figure", row=dict(line, entity_key=CO3.split(":")[1], started_on="2024-05-01",
                                                                               in_latest=True))
    r = report(p, [failed, going, n, a1, a2])
    f = cc.shared_office(r)
    assert f["status"] == "fired" and "Example" not in f["text"] and "1010" not in f["text"]
    a2["row"]["line_1"] = "99 Other Road"
    assert cc.shared_office(r)["status"] == "blocked"


def test_a_late_charity_return_fires_and_a_filed_one_clears():
    c = item("charities:charities/CC9", "charities", kind="organisation", row={"status": "Registered", "year_end_month": 3, "year_end_day": 31})
    ret = item("charities:charities/returns/1", "charity_returns", kind="figure", row={"charity_key": "charities/CC9", "period_end": "2024-03-31"})
    r = report(c, [ret])
    f = cc.charity_return_filed(r)
    assert (f["status"], f["severity"]) == ("fired", "red")     # due for the year to 31 March 2026, newest held 2024
    ret["row"]["period_end"] = "2026-03-31"
    assert cc.charity_return_filed(r)["status"] == "clear"


def test_land_titles_list_a_company_never_a_person():
    t = item("linz:titles/owner/1", "linz_title_owners", kind="figure", row={"owner_type": "corporate", "status": "Live"})
    assert cc.land_titles(report(company(), [t]))["status"] == "fired"
    p = item(PERSON, "directors", row={"in_latest": True})
    f = cc.land_titles(report(p, [dict(t, row={"owner_type": "person", "status": "Live"})]))
    assert f["status"] == "blocked" and not f["citations"]


def test_namesake_exposure_counts_the_near_links_a_first_stage_set_aside():
    p = item(PERSON, "directors", row={"in_latest": True})
    r = report(p, [], walk={"stage1": {"stage": 1, "near_set_aside": 0}})
    assert cc.namesake_exposure(r)["status"] == "clear"
    r["walk"]["stage1"]["near_set_aside"] = 120
    f = cc.namesake_exposure(r)
    assert f["status"] == "fired" and "120" in f["text"] and "second stage" in f["text"]


def test_walk_coverage_says_the_next_hop_counted():
    r = report(company(), [], walk={"stage1": {"stage": 1, "depth": 2, "cut": True, "beyond_entities": 0, "beyond_people": 8,
                                               "hubs_not_expanded": 1, "hub_people": 50, "hub_entities": 50}})
    f = cc.walk_coverage(r)
    assert f["status"] == "fired" and "8 person(s)" in f["text"] and "1 hub(s)" in f["text"]
    r["walk"]["stage1"].update(cut=False, hubs_not_expanded=0)
    assert cc.walk_coverage(r)["status"] == "clear"


def test_same_name_failed_waits_for_the_second_stage():
    r = report(company(), [], walk={"stage1": {"stage": 1, "near_set_aside": 3}})
    assert cc.same_name_failed(r)["status"] == "blocked"
    r2 = copy.deepcopy(r)
    del r2["walk"]["stage1"]
    assert cc.same_name_failed(r2)["status"] == "clear"
