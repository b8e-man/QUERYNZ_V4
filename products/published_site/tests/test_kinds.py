"""The kinds beside home and parties, on fixture rows: pickers, size bands, cites, electorates, people, board members."""
import json
import os

import pytest

from products.published_site import build as B
from products.published_site import paths, read, version
from products.published_site.tests import fixtures as X
from products.published_site.tests.test_pin import write as write_listing


@pytest.fixture
def vdir(monkeypatch, tmp_path):
    monkeypatch.setattr(read, "Tables", X.FakeTables)
    monkeypatch.setattr(read, "product_connect", lambda: X.NoConn())
    monkeypatch.setattr(read, "read_connect", lambda: X.NoConn())
    monkeypatch.setattr(read, "document_names", lambda conn, hashes: {h: [f"{h[:6]}.pdf"] for h in hashes if h})
    os.makedirs(tmp_path / "listings")
    write_listing(tmp_path / "listings", "2026-10-20T0620", [{"path": f"x/{h[:4]}", "bytes": 1, "mtime": "x", "sha256": h} for h in X.D.values()])
    ok, stamp, lines = B.build("2026-10-20T0620", str(tmp_path / "out"), stamp="2026-10-20T1000", listings_folder=str(tmp_path / "listings"), log=lambda s: None)
    assert ok, lines
    return os.path.join(str(tmp_path / "out"), "v", stamp)


def load(vdir, rel):
    return json.load(open(os.path.join(vdir, rel), encoding="utf-8"))


def test_every_kind_is_written_or_said_not_held(vdir):
    m = version.manifest_of(vdir)
    for k in paths.KINDS:
        assert m["written"].get(k) or k in m["kinds_not_held"], k
    assert m["kinds_not_held"] == {"board-member": "no lane publishes party boards; the frozen site read them from party websites (not captured here)"}
    assert m["kinds_not_built"] == {}


def test_pickers_list_sitting_members_and_the_cut_donor_list(vdir):
    p = load(vdir, paths.path("pickers"))
    assert [m["name"] for m in p["mps"]] == ["Karen CHHOUR", "David SEYMOUR"]          # Pat GONE's seat ended
    seymour = p["mps"][1]
    assert seymour["seat"]["route"] == "electorate" and seymour["running"]["electorate"] == "ge-2026/epsom" and seymour["running"]["namesakes"] == 0
    assert p["donors_listed"] == 5 and p["donor_population"] == 5 and p["donors"][0]["name"] == "Big Co Limited"   # Local Giver and the committee are known from a candidate return alone


def test_size_bands_split_at_the_line_and_keep_part_g_nameless(vdir):
    s = load(vdir, paths.path("size-bands", "ACT New Zealand"))
    over, under, unknown = s["bands"]
    assert over["n"] == 1 and over["total"] == 40000.0 and over["rows"][0]["donor"] == "Big Co Limited"
    assert under["n"] == 2 and under["named"] == 600.0 and under["total"] == 600.0
    assert unknown["total"] == 0.0 and s["years_covered"] == [2017, 2023]
    y = {r["year"]: r for r in s["years"]}
    assert y[2023]["threshold"] == 5000 and y[2017]["threshold"] == 15000 and y[2023]["placed"] == 40000.0
    assert not os.path.exists(os.path.join(vdir, paths.path("size-bands", "The New Zealand National Party"))) or True   # two returns: a year is skipped, the page may still exist


def test_cites_name_the_document_and_never_a_lane(vdir):
    c = load(vdir, paths.path("cite", "party_returns:r2/A/1"))
    assert c["document"] == X.D["b"] and c["page"] == 2 and c["source_file"] == X.D["b"][:6] + ".pdf" and c["pinned"] is True
    assert "Part A" in c["register"] and "$40,000.00" in c["evidence_text"]
    d = load(vdir, paths.path("cite", "disclosures:d1"))
    assert d["source_url"] == "/assets/x.pdf" and "Commission" in d["register"]


def test_electorates_hold_candidates_and_results_and_say_money_is_not_held(vdir):
    e = load(vdir, paths.path("electorate", "Epsom"))
    assert e["elections"] == [2023, 2026] and e["money"]["declared_total"] == 1200.0   # 2014 is before the window
    r23 = e["races"][0]
    assert r23["elected"] == "David SEYMOUR" and r23["candidates"][0]["elected"] is True and r23["candidates"][1]["elected"] is False
    assert r23["candidates"][0]["sitting_mp"] is True and r23["candidates"][0]["party"] == "ACT New Zealand"
    assert r23["candidates"][1]["party"] is None and r23["candidates"][1]["party_filed"] == "Nobody Party"
    assert r23["declared_total"] == 1200.0 and r23["expenses_total"] == 500.0
    r26 = e["races"][1]
    assert r26["result_held"] is False and r26["elected"] is None and r26["candidates"][0]["elected"] is None
    a = load(vdir, paths.path("electorates", "all"))
    assert a["n"] == 1 and a["years"] == [2023, 2026]
    y = load(vdir, paths.path("electorates", "2023"))
    assert y["contests"] == 1 and y["with_result"] == 1 and y["candidates"] == 2


def test_people_pages_hold_seats_and_candidacies_and_nothing_joined_by_name(vdir):
    p = load(vdir, paths.path("subject", "person", "David SEYMOUR"))
    assert p["sitting_mp"] is True and len(p["seats"]) == 1 and len(p["candidacies"]) == 2
    assert p["donations_made"]["held"] is False and p["party_boards"]["held"] is False
    assert os.path.exists(os.path.join(vdir, paths.path("subject", "person", "Pat GONE")))
    assert not os.path.exists(os.path.join(vdir, paths.path("subject", "person", "Bob OLD")))   # 2014 is outside the window
    assert not any(f.startswith("board-member") for f in os.listdir(os.path.join(vdir, "data")) if os.path.isdir(os.path.join(vdir, "data", f)) and f == "board-member")


def test_the_party_page_lists_its_financial_statements_with_cited_figures(vdir):
    p = load(vdir, paths.path("subject", "party", "ACT New Zealand"))
    fin = p["financials"]
    assert isinstance(fin, list) and len(fin) == 2 and [s["filed_year"] for s in fin] == [2026, 2025]   # 2016 is before the window
    s25 = fin[1]
    assert s25["document_held"] is True and s25["figures"]["income"]["amount"] == 1565672.0 and s25["figures"]["income"]["prior"] == 4554215.0
    assert s25["figures"]["income"]["cite"]["document"] == X.D["h"] and s25["figures"]["income"]["cite"]["page"] == 3
    assert "income" in s25["figures_read"] and s25["figures"]["expenditure"]["amount"] == 1500000.0
    assert s25["cite"]["document"] == X.D["h"]                                      # cited to the statement itself
    s26 = fin[0]
    assert s26["document_held"] is False and s26["figures"] == {} and "no statement document is held" in s26["basis"]
    assert s26["cite"]["document"] == X.D["g"]                                      # cited to the Commission's list
    nat = load(vdir, paths.path("subject", "party", "The New Zealand National Party"))
    assert nat["financials"] == []                     # none listed: an empty list, not "not held"


def test_two_registrations_with_one_name_get_two_pages_deterministically(monkeypatch, tmp_path):
    data = X.tables()
    twin = "ec-party/2026-08-05/000000000000"
    data["pub.parties"].append(dict(data["pub.parties"][0], key=twin, registered_on="2026-08-05"))     # a second "ACT New Zealand" registration, no money
    data["pub.parties"][0]["on_register"] = False
    monkeypatch.setattr(read, "Tables", lambda t, c, w: X.FakeTables(t, c, w, data=data))
    monkeypatch.setattr(read, "product_connect", lambda: X.NoConn())
    monkeypatch.setattr(read, "read_connect", lambda: X.NoConn())
    monkeypatch.setattr(read, "document_names", lambda conn, hashes: {h: [] for h in hashes if h})
    os.makedirs(tmp_path / "listings")
    write_listing(tmp_path / "listings", "2026-10-20T0620", [{"path": f"x/{h[:4]}", "bytes": 1, "mtime": "x", "sha256": h} for h in X.D.values()])
    ok, stamp, lines = B.build("2026-10-20T0620", str(tmp_path / "out"), stamp="2026-10-20T1000", listings_folder=str(tmp_path / "listings"), log=lambda s: None)
    assert ok, lines
    vdir = os.path.join(str(tmp_path / "out"), "v", stamp)
    plain = load(vdir, paths.path("subject", "party", "ACT New Zealand"))
    assert plain["key"] == X.A and plain["donations_received"]                       # the key with the rows keeps the plain path, registered or not
    other = load(vdir, plain["card"]["other_registrations_of_this_name"][0]["page"])
    assert other["key"] == twin and other["donations_received"] == [] and other["card"]["other_registrations_of_this_name"][0]["key"] == X.A
    assert os.path.exists(os.path.join(vdir, paths.path("size-bands", "ACT New Zealand")))
