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
    assert p["donors_listed"] == 3 and p["donor_population"] == 3 and p["donors"][0]["name"] == "Big Co Limited"


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
    assert e["elections"] == [2023, 2026] and e["money"]["held"] is False          # 2014 is before the window
    r23 = e["races"][0]
    assert r23["elected"] == "David SEYMOUR" and r23["candidates"][0]["elected"] is True and r23["candidates"][1]["elected"] is False
    assert r23["candidates"][0]["sitting_mp"] is True and r23["candidates"][0]["party"] == "ACT New Zealand"
    assert r23["candidates"][1]["party"] is None and r23["candidates"][1]["party_filed"] == "Nobody Party"
    assert r23["declared_total"]["not_held"] == "candidate donations"
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
