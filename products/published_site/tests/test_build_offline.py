"""The whole pipeline on fixture rows, no database: a listing pins the inputs, the ten kinds land by the path rule,
the gates run, the record says built, and a listing that lacks a document leaves its rows out."""
import json
import os

import pytest

from products.published_site import build as B
from products.published_site import paths, preview, read, version
from products.published_site.tests import fixtures as X
from products.published_site.tests.test_pin import write as write_listing


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(read, "Tables", X.FakeTables)
    monkeypatch.setattr(read, "product_connect", lambda: X.NoConn())
    monkeypatch.setattr(read, "read_connect", lambda: X.NoConn())
    monkeypatch.setattr(read, "document_names", lambda conn, hashes: {h: [f"{h[:6]}.pdf"] for h in hashes if h})


def listing(tmp_path, hashes, name="2026-10-20T0620"):
    rows = [{"path": f"ec-donations/{h[:4]}.pdf", "bytes": 1, "mtime": "x", "sha256": h} for h in hashes]
    write_listing(tmp_path / "listings", name, rows) if (tmp_path / "listings").exists() else None
    os.makedirs(tmp_path / "listings", exist_ok=True)
    return write_listing(tmp_path / "listings", name, rows)


def test_a_build_writes_the_kinds_runs_the_gates_and_stops(offline, tmp_path):
    listing(tmp_path, X.D.values())
    out = str(tmp_path / "out")
    ok, stamp, lines = B.build("2026-10-20T0620", out, stamp="2026-10-20T0800", listings_folder=str(tmp_path / "listings"), log=lambda s: None)
    assert ok, lines
    d = os.path.join(out, "v", stamp)
    m = version.manifest_of(d)
    assert m["listing"]["version"] == "2026-10-20T0620" and m["pinned"]["pub.party_return_donors"]["left_out"] == 0
    assert os.path.isfile(os.path.join(d, paths.path("subject", "party", "ACT New Zealand")))
    assert os.path.isfile(os.path.join(d, paths.path("donor", "Jane Q Donor")))
    home = json.load(open(os.path.join(d, "data", "home.json")))
    assert home["window_from"] == 2017 and len(home["headline_parties"]) == 2
    act = [p for p in home["parties"] if p["key"] == X.A][0]
    assert act["total_window"] == 51000.0 and act["named_window"] == 40600.0 and act["seats"]["total"] == 2
    assert home["recent_disclosures"]["total"] == 25000.0
    assert home["totals"]["electorate_spend"] == 500.0 and home["totals"]["electorate_declared"] == 1200.0
    rows = [json.loads(l) for l in open(os.path.join(out, "RELEASES.jsonl"))]
    assert rows[-1]["action"] == "built" and rows[-1]["gates"][0] == ["snapshot", True]
    assert not any("deploy" in l.lower() and "fail" in l for l in lines)


def test_a_listing_without_a_document_leaves_its_rows_out(offline, tmp_path):
    listing(tmp_path, [h for n, h in X.D.items() if n != "b"])   # ACT's 2023 return is not in the listing
    out = str(tmp_path / "out")
    ok, stamp, lines = B.build("2026-10-20T0620", out, stamp="2026-10-20T0801", listings_folder=str(tmp_path / "listings"), log=lambda s: None)
    assert ok, lines
    m = version.manifest_of(os.path.join(out, "v", stamp))
    assert m["pinned"]["pub.party_return_totals"]["left_out"] == 1 and m["pinned"]["pub.party_return_donors"]["left_out"] == 1
    home = json.load(open(os.path.join(out, "v", stamp, "data", "home.json")))
    act = [p for p in home["parties"] if p["key"] == X.A][0]
    assert act["declared_by_year"]["2023"] is None and act["total_window"] == 1000.0
    assert any("left out" in l for l in lines)


def test_no_listing_means_no_build(offline, tmp_path):
    ok, stamp, lines = B.build(None, str(tmp_path / "out"), listings_folder=str(tmp_path / "none"), log=lambda s: None)
    assert not ok and stamp is None and lines[0].startswith("fail")


def test_the_preview_renders_from_the_folder_and_refuses_the_frozen_ports(offline, tmp_path):
    listing(tmp_path, X.D.values())
    out = str(tmp_path / "out")
    ok, stamp, _ = B.build("2026-10-20T0620", out, stamp="2026-10-20T0802", listings_folder=str(tmp_path / "listings"), log=lambda s: None)
    d = os.path.join(out, "v", stamp)
    html = preview.index_html(d)
    assert "ACT New Zealand" in html and "nothing here is deployed" in html
    assert "$51,000.00" in preview.party_html(d, os.path.basename(paths.path("subject", "party", "ACT New Zealand")))
    assert "$600.00" in preview.donor_html(d, os.path.basename(paths.path("donor", "Jane Q Donor")))
    for port in (8300, 8301):
        with pytest.raises(ValueError, match="frozen product"):
            preview.check_port(port)
    preview.check_port(8430)
