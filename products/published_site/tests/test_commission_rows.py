"""Step 4.5's two causes the template owns (site-4): a Commission row (`read_from` 'commission', no return read) cites
the spreadsheet under its own label with the Commission's figures; and a candidacy the official result prints no party
for shows the label as filed on its return or the Commission's row, said so, and stays blank with neither."""
import os

from products.published_site import build as B
from products.published_site import paths, read
from products.published_site.tests import fixtures as X
from products.published_site.tests.test_kinds import load
from products.published_site.tests.test_pin import write as write_listing


def _row(**kw):
    base = dict(X.tables()["pub.candidate_return_totals"][0])
    base.update({k: None for k in ("part_a", "part_c", "part_d", "donations_check", "part_f", "part_g", "expenses_check", "loans_check", "signed",
                                   "profile_version", "loaded_at", "donors_check", "sheet", "sheet_row")})
    base.update(kw)
    return base


def _candidate(key, name, display, votes):
    return {"key": key, "election": "ge-2023", "name": name, "display_name": display, "name_key": display.lower(), "party": None,
            "party_registered": None, "electorate": "ge-2023/epsom", "list_place": None, "votes": votes, "poll_cancelled": False,
            "document": X.D["g"], "page": 2}


def build(monkeypatch, tmp_path):
    data = X.tables()
    data["pub.candidates"] += [_candidate("ge-2023/free-fran/epsom", "FREE, Fran", "Fran FREE", 4),
                               _candidate("ge-2023/read-rae/epsom", "READ, Rae", "Rae READ", 3),
                               _candidate("ge-2023/blank-bea/epsom", "BLANK, Bea", "Bea BLANK", 2)]
    data["pub.candidate_return_totals"] += [
        _row(key=f"{X.D['h']}/7", document=X.D["h"], page=None, place="sheet Epsom, row 7", surname="FREE", given_names="Fran", party="Future Youth Party",
             placed_by="spreadsheet row", donations=None, expenses=None, loans=None, commission_donations=300.0, commission_expenses=50.0,
             commission_loans=None, commission_file=X.D["h"], commission_key=f"{X.D['h']}/7", read_from="commission", sheet="Epsom", sheet_row=7),
        _row(key="cr-2023-epsom-read", document=X.D["a"], surname="READ", given_names="Rae", party="Independent", donations=10.0, expenses=2.0,
             loans=0.0, commission_donations=None, commission_expenses=None, commission_loans=None, commission_file=None, commission_key=None)]
    answers = {"candidate_return_totals": [(2023, "Epsom", 1587.0, 5), (2018, "Epsom", 9.0, 1)]}
    monkeypatch.setattr(read, "Tables", lambda t, c, w: X.FakeTables(t, c, w, data=data))
    monkeypatch.setattr(read, "product_connect", lambda: X.NoConn(answers))
    monkeypatch.setattr(read, "read_connect", lambda: X.NoConn(answers))
    monkeypatch.setattr(read, "document_names", lambda conn, hashes: {h: [f"{h[:6]}.pdf"] for h in hashes if h})
    os.makedirs(tmp_path / "listings")
    write_listing(tmp_path / "listings", "2026-10-20T0620", [{"path": f"x/{h[:4]}", "bytes": 1, "mtime": "x", "sha256": h} for h in X.D.values()])
    ok, stamp, lines = B.build("2026-10-20T0620", str(tmp_path / "out"), stamp="2026-10-20T1000", listings_folder=str(tmp_path / "listings"), log=lambda s: None)
    assert ok, lines
    return os.path.join(str(tmp_path / "out"), "v", stamp)


def test_a_commission_row_cites_the_spreadsheet_with_the_commission_s_figures(monkeypatch, tmp_path):
    vdir = build(monkeypatch, tmp_path)
    c = load(vdir, paths.path("cite", f"candidate_returns:{X.D['h']}/7"))
    assert c["register"] != "EC candidate return (declaration)" and "no return read" in c["register"]
    assert c["evidence_text"] == "Fran FREE, Epsom 2023: the Commission's figures: donations $300.00, expenses $50.00"
    assert c["read_from"] == "commission" and c["document"] == X.D["h"] and c["place"] == "sheet Epsom, row 7"
    read_one = load(vdir, paths.path("cite", "candidate_returns:cr-2023-epsom-read"))
    assert read_one["register"] == "EC candidate return (declaration)" and "donations $10.00" in read_one["evidence_text"]   # a read return as before


def test_a_commission_row_with_no_figures_says_so_never_a_zero():
    from products.published_site import render
    assert render.commission_figures({"commission_donations": None, "commission_expenses": None, "commission_loans": None,
                                      "donations": None}) == "the Commission's row prints no figures"
    assert render.commission_figures({"commission_donations": 0.0, "commission_expenses": None, "commission_loans": 12.5}) == \
        "the Commission's figures: donations $0.00, loans $12.50"


def test_a_candidacy_with_no_party_in_the_result_shows_the_filed_label(monkeypatch, tmp_path):
    vdir = build(monkeypatch, tmp_path)
    race = next(r for r in load(vdir, paths.path("electorate", "Epsom"))["races"] if r["year"] == 2023)
    by = {c["display"]: c for c in race["candidates"]}
    assert by["Fran FREE"]["party"] is None and by["Fran FREE"]["party_filed"] == "Future Youth Party" and by["Fran FREE"]["party_filed_from"] == "commission"
    assert "the label as filed" in by["Fran FREE"]["party_filed_basis"] and "no return read" in by["Fran FREE"]["party_filed_basis"]
    assert by["Rae READ"]["party_filed"] == "Independent" and by["Rae READ"]["party_filed_from"] == "return"
    assert by["Bea BLANK"]["party"] is None and by["Bea BLANK"]["party_filed"] is None and by["Bea BLANK"]["party_filed_basis"] is None   # neither: blank
    assert by["David SEYMOUR"]["party_filed"] == "ACT" and by["David SEYMOUR"]["party_filed_from"] == "result"                      # the result's own label
    fran = load(vdir, paths.path("subject", "person", "Fran FREE"))
    cand = [c for c in fran["candidacies"] if c["year"] == 2023][0]
    assert cand["party_filed"] == "Future Youth Party" and "the label as filed" in cand["party_filed_basis"]
    bea = load(vdir, paths.path("subject", "person", "Bea BLANK"))
    assert [c["party_filed"] for c in bea["candidacies"]] == [None]


def test_a_filed_label_s_candidate_money_is_grouped_under_it_on_the_home_page(monkeypatch, tmp_path):
    vdir = build(monkeypatch, tmp_path)
    h = load(vdir, paths.path("home"))
    don = {p["name"]: p for p in h["race_donations"]}
    assert don["Future Youth Party"]["total"] == 300.0 and don["Future Youth Party"]["registered"] is False and don["Independent"]["total"] == 10.0
    pf = {p["party"]: p for p in h["party_funding"]}
    assert pf["Future Youth Party"]["key"] is None and pf["Future Youth Party"]["registered"] is False
    assert pf["Future Youth Party"]["parts"] == {"party": 0.0, "candidates": 300.0, "public": 0.0} and pf["Future Youth Party"]["by_year"] == {"2023": 300.0}
    assert pf["ACT New Zealand"]["registered"] is True and "no party listed" not in pf
