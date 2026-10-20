"""The frozen site's money sections on the home, parties and party pages (plan 4.4, tranche 3), on fixture rows."""
from products.published_site import money_sections as M
from products.published_site import paths
from products.published_site.tests import fixtures as X
from products.published_site.tests.test_kinds import load, vdir   # noqa: F401


def test_a_filed_name_is_a_party_only_by_its_names_or_a_committee_of_it():
    from products.published_site import figures as F
    t = X.tables()
    idx = F.PartyIndex(t["pub.parties"], t["pub.party_names"])
    pn = M.PartyNames(idx, t["pub.party_names"])
    assert pn.of("ACT New Zealand") == (X.A, "party") and pn.of("The ACT Party") == (X.A, "party") and pn.of("NZ National Party") == (X.B, "party")
    assert pn.of("ACT Epsom Electorate Committee") == (X.A, "committee") and pn.of("National Party Botany Electorate") == (X.B, "committee")
    assert pn.of("Big Co Limited") == (None, None) and pn.of("Epsom Electorate Committee") == (None, None)      # no party token: nobody's
    assert pn.of("ACT National Party Electorate Committee") == (None, None)                                       # two parties' words: ambiguous, nobody's


def test_the_home_page_carries_the_money_sections_with_their_bases(vdir):
    h = load(vdir, paths.path("home"))
    pt = h["party_transfers"]
    assert len(pt) == 1 and pt[0]["key"] == X.A and pt[0]["total"] == 200.0 and pt[0]["committees"]["rows"] == 1 and pt[0]["direct"]["rows"] == 0
    assert pt[0]["spellings"] == ["ACT Epsom Electorate Committee"] and pt[0]["to_own_candidates"] == 1 and "rows_detail" not in pt[0]
    rd = h["race_donations"]
    assert rd[0]["name"] == "ACT New Zealand" and rd[0]["total"] == 1200.0 and rd[0]["by_year"] == {"2023": 1200.0} and rd[0]["registered"] is True
    assert any(p["name"] == "Nobody Party" and p["registered"] is False and p["total"] == 0.0 for p in rd)
    rs = h["race_spend"]
    assert rs[0]["party"] == "ACT New Zealand" and rs[0]["spend"] == 500.0 and rs[0]["candidates"] == 2 and rs[0]["with_figure"] == 1   # 2023 and 2026 candidacies, one return
    assert h["race_spend_total"] == 500.0
    pf = {p["key"]: p for p in h["party_funding"]}
    assert pf[X.A]["parts"] == {"party": 51000.0, "candidates": 1200.0, "public": 500.0} and pf[X.A]["by_year"]["2023"] == 51700.0 and pf[X.A]["total"] == 52700.0
    dc = h["donor_categories"]
    assert dc["named"] == 40600.0 and dc["party_years"] == 2 and dc["years"] == [2017, 2023]                   # National 2022 has two returns and is left out
    assert h["party_spend"]["by_year"]["2023"]["spend"] == 1000.0 and h["party_spend"]["returns"] == 1
    assert h["race_public"][0]["total"] == 500.0 and h["public_money"]["allocated"] == 500.0 and h["public_money"]["parties"] == 1
    ps = h["promoter_spend"]
    assert ps["total"] == 300000.0 and ps["referendum_2020"] == 75000.0 and ps["cannabis_2020"] == 50000.0 and ps["returns"] == 2 and ps["promoters"] == 1
    assert ps["named"][0]["name"] == "Vote Loud Limited" and ps["named"][0]["people"] == [{"role": "authorised representative", "name": "Loud Person"}]
    assert ps["read_from_the_return"] == 1 and ps["agree"] == 1 and ps["nil_returns"] == 0
    assert h["donors_sighted"]["n"] == 0 and h["totals"]["promoter_spend"] == 300000.0 and h["totals"]["public_allocated"] == 500.0
    assert set(h["sections_basis"]) >= {"party_transfers", "race_donations", "party_funding", "donor_categories"}


def test_the_parties_page_counts_what_resolves_to_nobody(vdir):
    p = load(vdir, paths.path("parties"))
    assert p["unaffiliated_sitting"] == 0 and p["junk_labels"] == {"rows": 0, "total": 0.0, "basis": p["junk_labels"]["basis"]}
    assert p["unmatched_disclosures"]["rows"] == 0 and p["unmatched_disclosures"]["labels"] == []


def test_the_party_page_lists_top_donors_donations_made_and_sitting_members(vdir):
    p = load(vdir, paths.path("subject", "party", "ACT New Zealand"))
    top = p["top_donors"]
    assert [d["name"] for d in top] == ["Big Co Limited", "Open Year Giver", "Jane Q Donor"] and top[0]["total"] == 40000.0 and top[1]["open_year_disclosures"] == 25000.0
    assert top[2]["total"] == 600.0 and top[2]["n"] == 2 and top[2]["first_year"] == 2017 and top[2]["page"] == paths.path("donor", "Jane Q Donor")
    assert [d["name"] for d in p["top_donors_by_race"]["2023"]] == ["Big Co Limited"] and p["top_donors_by_race"]["2020"] == []
    made = p["donations_made"]
    assert len(made) == 1 and made[0]["receiver"] == "David SEYMOUR" and made[0]["tier"] == "committee" and made[0]["donor_filed"] == "ACT Epsom Electorate Committee"
    assert p["donations_made_total"] == 200.0 and made[0]["cite"]["document"] == X.D["c"]
    mps = p["mps"]["members"]
    assert [m["name"] for m in mps] == ["David SEYMOUR", "Karen CHHOUR"] and mps[0]["receipts"] == 1200.0 and mps[1]["receipts"] == 0.0
    assert p["leaders"]["held"] is False and p["rules"]["held"] is False and p["industries"]["held"] is False
