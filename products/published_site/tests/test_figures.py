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
    jane = d["donor jane q"]
    assert jane.kind == "person" and sorted(jane.spellings) == ["Jane Q Donor", "Jane Q. Donor"] and jane.name == "Jane Q Donor"
    assert F.donor_totals(jane)["total"] == 600.0
    big = d["big co"]
    tt = F.donor_totals(big)
    assert tt["returns"] == 40000.0 and tt["disclosures_sighted"] == 40000.0 and tt["total"] == 40000.0
    assert F.donor_totals(d["giver open year"])["open_year_disclosures"] == 25000.0
    assert "Withdrawn Giver" not in {x.name for x in d.values()}


def test_dates_parse_as_the_forms_print_them():
    assert F.parse_dates("8/8/23, 1/6/23, 12/10/23") == [dt.date(2023, 8, 8), dt.date(2023, 6, 1), dt.date(2023, 10, 12)]
    assert F.parse_dates("07/09/2023") == [dt.date(2023, 9, 7)] and F.parse_dates("") == [] and F.parse_dates("31/02/2020") == []
