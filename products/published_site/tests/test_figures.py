"""The shared figures follow the template's rules on fixture rows."""
import datetime as dt

from products.published_site import figures as F
from products.published_site.tests import fixtures as X
from products.published_site import site_template as ftm

YEARS = list(range(2017, 2027))


def setup():
    t = ftm.load()
    T = X.FakeTables(t)
    idx = F.PartyIndex(T.get("pub.parties"), T.get("pub.party_names"))
    ser = F.party_series(T, t.settings, idx, YEARS)
    return t, T, idx, ser


def test_party_values_in_any_form_come_back_to_the_key():
    _, _, idx, _ = setup()
    assert idx.key(X.A) == X.A and idx.key("ACT New Zealand") == X.A and idx.key("The New Zealand National Party") == X.B
    assert idx.key("Nobody Party") is None and idx.key(None) is None


def test_one_figure_per_party_year_with_its_basis():
    _, _, _, ser = setup()
    act = ser[X.A]
    d = act.declared(2023)
    assert d["total"] == 50000.0 and "pixels" in d["basis"] and d["documents"][0]["document"] == X.D["b"]
    assert act.declared(2019)["total"] is None and act.declared(2019)["basis"] == "no return held"
    nat = ser[X.B]
    two = nat.declared(2022)
    assert two["total"] is None and "2 returns held" in two["basis"] and two["held"] == [100.0, 120.0]
    assert nat.declared(2020)["total"] is None   # replaced return is not current
    w = nat.window()
    assert w["total"] == 0.0 and w["years_left_out"] == [2022]


def test_named_rows_of_two_unreplaced_returns_are_never_summed():
    _, _, _, ser = setup()
    nat = ser[X.B]
    n = nat.named(2022)
    assert n["total"] is None and n["rows"] == 2 and "neither are counted" in n["basis"]
    assert nat.window()["named"] == 0.0
    assert nat.race(2023, [2021, 2022, 2023])["named"] == 0.0


def test_the_2020_race_takes_2017_rows_by_their_own_date():
    t, _, _, ser = setup()
    act = ser[X.A]
    r = act.race(2020, [2018, 2019, 2020])
    assert r["named"] == 500.0 and r["named_rows"] == 1          # 30/09/2017 is after 24 September; 01/03/2017 is not
    assert act.named(2017)["total"] == 600.0                      # the whole window keeps both
    assert ftm.race_of(2017, t.settings) is None
    r23 = act.race(2023, [2021, 2022, 2023])
    assert r23["total"] == 50000.0 and r23["named"] == 40000.0 and r23["over_line"] == 40000.0


def test_a_disclosure_the_return_covers_is_sighted_and_the_open_year_counts():
    _, T, idx, ser = setup()
    act = ser[X.A]
    assert act.disclosed(2023) == {"year": 2023, "total": 40000.0, "n": 1, "covered_by_return": True,
                                   "basis": "sighted beside the return, never added"}
    assert act.disclosed(2026)["covered_by_return"] is False and act.disclosed(2026)["total"] == 25000.0   # the withdrawn one is out
    w = act.window()
    assert w["disclosed_sighted"] == 40000.0 and w["disclosed_open_years"] == 25000.0 and w["total"] == 51000.0


def test_public_money_and_seats():
    _, _, _, ser = setup()
    act = ser[X.A]
    pm = act.public_money()
    assert pm["allocated"] == 500.0 and pm["spent"] == 400.0 and pm["expenses_by_year"] == {"2023": 1000.0}
    assert act.seats == {"total": 2, "electorate": 1, "list": 1}


def test_donors_fold_under_the_shared_reading_and_never_add_a_sighted_disclosure():
    t, T, idx, ser = setup()
    d = F.donors(T, t.settings, idx, ser, YEARS)
    jane = d["jane q donor"]
    assert jane.kind == "person" and sorted(jane.spellings) == ["Jane Q Donor", "Jane Q. Donor"] and jane.name == "Jane Q Donor"
    assert F.donor_totals(jane)["total"] == 600.0
    big = d["big co limited"]
    tt = F.donor_totals(big)
    assert tt["returns"] == 40000.0 and tt["disclosures_sighted"] == 40000.0 and tt["total"] == 40000.0
    assert F.donor_totals(d["open year giver"])["open_year_disclosures"] == 25000.0
    assert "Withdrawn Giver" not in {x.name for x in d.values()}


def test_dates_parse_as_the_forms_print_them():
    assert F.parse_dates("8/8/23, 1/6/23, 12/10/23") == [dt.date(2023, 8, 8), dt.date(2023, 6, 1), dt.date(2023, 10, 12)]
    assert F.parse_dates("07/09/2023") == [dt.date(2023, 9, 7)] and F.parse_dates("") == [] and F.parse_dates("31/02/2020") == []


def test_a_declaration_s_year_is_the_gift_s_never_the_commission_s():
    assert F.disclosure_year({"received_on": "2024-05-23", "given_on": "2023-08-25"}) == 2023
    assert F.disclosure_year({"received_on": "2024-05-23", "given_on": None}) == 2024
    assert "gift" in F.disclosure_year_basis({"given_on": "2023-08-25"}) and "no gift date" in F.disclosure_year_basis({"given_on": None})
    t, T, idx, _ = setup()
    data = X.tables()
    data["pub.disclosures"].append({"key": "d4", "document": X.D["e"], "page": 1, "place": None, "regime": "over-20000-from-2023", "party": "ACT New Zealand",
                                    "party_label": "ACT", "donor_name": "Late Declarer", "amount": 30000.0, "received_on": "2024-01-15", "given_on": "2023-12-20",
                                    "amendment": "none", "withdrawn_on": None, "href": None, "declaration_document": None})
    T2 = X.FakeTables(t, data=data)
    ser = F.party_series(T2, t.settings, idx, YEARS)
    act = ser[X.A]
    assert act.disclosed(2023)["total"] == 70000.0 and act.disclosed(2023)["covered_by_return"] is True and act.disclosed(2024)["n"] == 0
    d = F.donors(T2, t.settings, idx, ser, YEARS)
    row = d["late declarer"].rows[0]
    assert row["year"] == 2023 and row["given_on"] == "2023-12-20" and row["received_on"] == "2024-01-15" and row["counts"] is False


def test_one_display_name_is_one_donor_and_the_published_key_is_its_own_form():
    t, T, idx, ser = setup()
    data = X.tables()
    # a Part A row the links have not read: its exact filed spelling is read elsewhere, so it joins that donor
    data["pub.party_return_donors"].append({"key": "r2/A/2", "return_key": "r2", "document": X.D["b"], "page": 2, "ordinal": 2, "party": "ACT New Zealand", "party_key": X.A,
                                            "party_label": "ACT", "year": 2023, "donor": "Big Co Limited", "amount": 5.0, "dates": "", "read_from": "text", "replaced_by": None})
    # a row the links read under a second key for an identical spelling (the links' half, carded): one page all the same
    data["pub.party_return_donors"].append({"key": "r2/A/3", "return_key": "r2", "document": X.D["b"], "page": 2, "ordinal": 3, "party": "ACT New Zealand", "party_key": X.A,
                                            "party_label": "ACT", "year": 2023, "donor": "Jane Q Donor", "amount": 7.0, "dates": "", "read_from": "text", "replaced_by": None})
    data["pub.names"].append({"ref": "party_returns:r2/A/3", "register": "party_returns", "view": "party_return_donors", "key": "r2/A/3", "name_filed": "Jane Q Donor",
                              "kind": "person", "name_key": "donor jane q village road"})
    # a row read by nobody under a spelling read nowhere: its own page under the spelling
    data["pub.party_return_donors"].append({"key": "r2/A/4", "return_key": "r2", "document": X.D["b"], "page": 2, "ordinal": 4, "party": "ACT New Zealand", "party_key": X.A,
                                            "party_label": "ACT", "year": 2023, "donor": "Nobody Read Me", "amount": 9.0, "dates": "", "read_from": "text", "replaced_by": None})
    T2 = X.FakeTables(t, data=data)
    ser = F.party_series(T2, t.settings, idx, YEARS)
    d = F.donors(T2, t.settings, idx, ser, YEARS)
    big = d["big co limited"]
    assert big.name_key == "big co limited" and len(big.readings) == 1 and "party_returns:r2/A/2" in big.refs and F.donor_totals(big)["party_returns"] == 40005.0
    jane = d["jane q donor"]
    assert len(jane.readings) == 2 and len(jane.rows) == 3 and F.donor_totals(jane)["total"] == 607.0 and jane.kind == "person"
    assert d["nobody read me"].readings == ["filed:nobody read me"] and d["nobody read me"].kind == "unreadable"
    assert len({x.name_key for x in d.values()}) == len(d)
    for x in d.values():
        assert not (set(x.name_key.split()) - set(F.paths.name_key(x.name).split())), x.name_key
