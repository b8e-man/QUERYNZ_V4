"""Electorate money (plan 4.4, tranche 2): the candidate-returns lane joined to the results, the Commission's
figure as the headline, unjoined returns counted apart, donor lines as filed, and the same money on the person
and donor pages."""
import json
import os

from products.published_site import candidate_money as CM
from products.published_site import gates, paths
from products.published_site.tests import fixtures as X
from products.published_site.tests.test_gates_can_fail import built, plant   # noqa: F401
from products.published_site.tests.test_kinds import load, vdir             # noqa: F401


def test_the_join_is_by_year_electorate_and_surname_and_never_guesses():
    assert CM.surname_of("MURALIDHAR, Mahesh") == "muralidhar" and CM.surname_of("Chlöe SWARBRICK") == "swarbrick" and CM.fold("Te Tai Hauāuru") == "te tai hauauru"
    t = X.FakeTables(__import__("products.published_site.site_template", fromlist=["load"]).load())
    from products.published_site import figures as F
    idx = F.PartyIndex(t.get("pub.parties"), t.get("pub.party_names"))
    cm = CM.candidate_money(t, idx, F.elections_in_window(t, list(range(2017, 2027))), list(range(2017, 2027)))
    assert cm.returns == 4 and cm.joined == 2                                  # the replaced return is not current; the 2018 by-election return joins nothing
    assert cm.of("ge-2023/seymour-david/epsom")["figures"]["declared"] == 1200.0  # the Commission's figure is the headline
    assert cm.of("ge-2023/seymour-david/epsom")["figures"]["declared_ours"] == 1000.0 and cm.of("ge-2023/seymour-david/epsom")["figures"]["declared_agrees"] is False
    assert "the return as read says $1,000.00" in cm.of("ge-2023/seymour-david/epsom")["figures"]["declared_basis"]
    assert cm.of("ge-2023/other-ann/epsom")["figures"]["nil"] is True and cm.of("ge-2023/other-ann/epsom")["figures"]["weaker"] is True
    u = cm.unjoined_for(2023, "Epsom")
    assert len(u) == 1 and u[0]["return"]["surname"] == "NOBODY" and "no candidate of this surname" in u[0]["why"]
    assert u[0]["figures"]["declared"] == 77.0 and "no figure" in u[0]["figures"]["declared_basis"]


def test_the_electorate_page_carries_the_money_and_the_unjoined_return_apart(vdir):
    e = load(vdir, paths.path("electorate", "Epsom"))
    r23 = e["races"][0]
    assert r23["declared_total"] == 1200.0 and r23["expenses_total"] == 500.0 and r23["returns_held"] == 2 and r23["declaring"] == 1 and r23["nil_returns"] == 1
    assert r23["returns_not_joined"]["n"] == 1 and r23["returns_not_joined"]["declared"] == 77.0 and r23["returns_not_joined"]["rows"][0]["candidate_as_filed"] == "Ghost NOBODY"
    sey = r23["candidates"][0]
    assert sey["declared"] == 1200.0 and sey["declared_ours"] == 1000.0 and sey["return_cite"]["document"] == X.D["c"] and sey["itemised_n"] == 3
    assert r23["top"]["display"] == "David SEYMOUR" and r23["parties"][0]["declared"] == 1200.0
    names = [d["name"] for d in r23["donors"]]
    assert names == ["Big Co Limited", "Local Giver", "ACT Epsom Electorate Committee"] and r23["donors"][1]["total"] == 477.0 and r23["donors"][1]["n"] == 2   # as filed, never folded; the unjoined return's line is here too
    assert r23["donors"][1]["to"][1]["candidate"] == "Ghost NOBODY" and r23["donors"][0]["to"][0]["candidate_key"] == "ge-2023/seymour-david/epsom"
    r26 = e["races"][1]
    assert r26["declared_total"] == 0.0 and r26["returns_held"] == 0 and r26["candidates"][0]["declared"]["held"] is False and "not a nil" in r26["candidates"][0]["declared_basis"]
    assert e["returns_for_contests_not_held"]["n"] == 1 and e["returns_for_contests_not_held"]["years"] == [2018] and e["returns_for_contests_not_held"]["rows"][0]["surname"] == "BYE"
    y = load(vdir, paths.path("electorates", "2023"))
    assert y["money"]["declared_total"] == 1200.0 and y["electorates"][0]["declared_total"] == 1200.0 and y["money"]["returns_not_joined"] == 1
    a = load(vdir, paths.path("electorates", "all"))
    assert a["money"]["by_year"]["2023"]["declared"] == 1200.0 and a["electorates"][0]["expenses_total"] == 500.0
    h = load(vdir, paths.path("home"))
    assert h["electorates"][0]["declared"] == 1200.0 and h["electorates"][0]["spend_by_year"] == {"2023": 500.0, "2026": 0.0} and h["electorates"][0]["winner"]["name"] == "David SEYMOUR"
    assert h["totals"]["electorate_declared"] == 1200.0 and h["totals"]["candidates_with_figure"] == 2 and h["totals"]["candidate_returns_not_joined"] == 1


def test_the_person_page_shows_the_candidacy_s_money_and_the_lines_received(vdir):
    p = load(vdir, paths.path("subject", "person", "David SEYMOUR"))
    c23 = next(c for c in p["candidacies"] if c["year"] == 2023)
    assert c23["declared"] == 1200.0 and c23["expenses"] == 500.0 and c23["return_held"] is True and c23["electorate_name"] == "Epsom"
    assert [r["donor"] for r in p["donations_received"]] == ["Big Co Limited", "Local Giver", "ACT Epsom Electorate Committee"] and p["donations_received_total"] == 1200.0
    assert p["donations_received_by_year"][0]["total"] == 1200.0 and p["donations_received_by_year"][0]["itemised_total"] == 1200.0
    assert p["donations_made"]["held"] is False                                   # still nothing joined by name


def test_candidate_donors_fold_only_by_the_shared_reading_of_the_exact_spelling(vdir):
    big = load(vdir, paths.path("donor", "Big Co Limited"))
    rows = {r["ref"]: r for r in big["history"]}
    assert "candidate_returns:cr-2023-epsom-seymour/A/1" in rows and rows["candidate_returns:cr-2023-epsom-seymour/A/1"]["receiver"] == "David SEYMOUR"
    assert big["totals"]["candidate_returns"] == 600.0 and big["totals"]["party_returns"] == 40000.0 and big["totals"]["total"] == 40600.0
    assert big["totals"]["by_receiver"] == {"ACT New Zealand": 40000.0, "David SEYMOUR": 600.0}
    local = load(vdir, paths.path("donor", "Local Giver"))
    assert local["name_key"] == "filed:local giver" and local["totals"]["total"] == 477.0 and len(local["history"]) == 2
    assert "not joined" in [r for r in local["history"] if r["receiver"] == "Ghost NOBODY"][0]["basis"]
    pk = load(vdir, paths.path("pickers"))
    assert "Local Giver" in [d["name"] for d in pk["donors"]]
    c = load(vdir, paths.path("cite", "candidate_returns:cr-2023-epsom-seymour"))
    assert c["document"] == X.D["c"] and "donations $1,000.00" in c["evidence_text"]


def test_the_candidate_money_gate_resums_the_commission_s_table_by_sql(built):
    out, vdir = built
    ctx = {"conn": X.NoConn(), "years": list(range(2017, 2027)), "candidate_returns_unjoined": 2}
    ok, line = gates.candidate_money(vdir, ctx)
    assert ok and "2 races equal" in line and "2 return(s) shown apart" in line, line
    plant(vdir, rel := paths.path("electorate", "Epsom"), lambda o: o["returns_for_contests_not_held"]["rows"].clear())
    ok, line = gates.candidate_money(vdir, ctx)
    assert not ok and "epsom 2018" in line and "no electorate page shows the race" in line, line
    plant(vdir, rel, lambda o: o["returns_for_contests_not_held"]["rows"].append({"year": 2018, "declared": 9.0}))
    rel = paths.path("electorate", "Epsom")
    plant(vdir, rel, lambda o: o["races"][0].update({"declared_total": 1199.0}))
    ok, line = gates.candidate_money(vdir, ctx)
    assert not ok and "epsom 2023" in line and "$1,276.00" in line, line
    plant(vdir, rel, lambda o: o["races"][0].update({"declared_total": 1200.0, "returns_held": 3}))
    assert not gates.candidate_money(vdir, ctx)[0]
    assert not gates.candidate_money(vdir, {"conn": None})[0]
