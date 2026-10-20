"""Every gate beside the snapshot gate is shown failing on a planted defect, so a green gate means something."""
import json
import os

import pytest

from products.published_site import build as B
from products.published_site import gates, paths, read, redact, version
from products.published_site.tests import fixtures as X
from products.published_site.tests.test_pin import write as write_listing


@pytest.fixture
def built(monkeypatch, tmp_path):
    monkeypatch.setattr(read, "Tables", X.FakeTables)
    monkeypatch.setattr(read, "product_connect", lambda: X.NoConn())
    monkeypatch.setattr(read, "read_connect", lambda: X.NoConn())
    monkeypatch.setattr(read, "document_names", lambda conn, hashes: {h: [f"{h[:6]}.pdf"] for h in hashes if h})
    monkeypatch.setattr(gates, "GATES", [g for g in gates.GATES if g[0] not in ("commission",)])
    os.makedirs(tmp_path / "listings")
    rows = [{"path": f"ec-donations/{h[:4]}.pdf", "bytes": 1, "mtime": "x", "sha256": h} for h in X.D.values()]
    write_listing(tmp_path / "listings", "2026-10-20T0620", rows)
    out = str(tmp_path / "out")
    ok, stamp, lines = B.build("2026-10-20T0620", out, stamp="2026-10-20T0900", listings_folder=str(tmp_path / "listings"), log=lambda s: None)
    assert ok, lines
    return out, os.path.join(out, "v", stamp)


def plant(vdir, rel, change):
    p = os.path.join(vdir, rel)
    with open(p, encoding="utf-8") as f:
        obj = json.load(f)
    change(obj)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def test_the_address_gate_sees_a_street_a_box_and_a_rural_delivery(built):
    out, vdir = built
    assert gates.addresses(vdir)[0]
    for text in ("12 Queen Street, Auckland 1010", "PO Box 1234, Wellington", "RD 3 Kaiapoi", "4/18 Kōwhai Rd"):
        plant(vdir, paths.path("home"), lambda o, t=text: o.update({"basis": {"parties": t}}))
        ok, line = gates.addresses(vdir)
        assert not ok and "data/home.json at basis.parties" in line and text not in line, (text, line)
    plant(vdir, paths.path("home"), lambda o: o.update({"basis": {"parties": "one figure per year"}}))
    assert gates.addresses(vdir)[0]


def test_the_suppression_gate_and_the_redaction(built):
    out, vdir = built
    forms = [redact.form_key("Jane Q Donor")]
    ok, line = gates.suppressed(vdir, {"suppressed_forms": forms})
    assert not ok and "still carry a suppressed form" in line
    page = json.load(open(os.path.join(vdir, paths.path("donor", "Jane Q Donor"))))
    red, n = redact.redact(page, forms)
    assert n >= 2 and red["name"] == redact.MARK and red["history"][0]["donor_filed"] == redact.MARK
    assert red["history"][0]["amount"] == page["history"][0]["amount"] and red["totals"] == page["totals"]
    assert redact.find(red, forms) == 0
    assert gates.suppressed(vdir, {"suppressed_forms": []})[0]


def test_the_donor_fold_gate_misses_a_page_and_a_shared_key(built):
    out, vdir = built
    assert gates.donor_fold(vdir)[0]
    os.remove(os.path.join(vdir, paths.path("donor", "Jane Q Donor")))
    ok, line = gates.donor_fold(vdir)
    assert not ok and "has no donor page" in line
    plant(vdir, paths.path("donor", "Big Co Limited"), lambda o: o.update({"name_key": "giver open year"}))
    ok, line = gates.donor_fold(vdir)
    assert "share the name key" in line


class FakeConn:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params=()):
        return iter(self.rows)


def test_the_commission_gate_reads_the_table_again_and_sees_a_wrong_figure(built):
    out, vdir = built
    table = [("ACT New Zealand", 2023, 40000.0, 1), ("ACT New Zealand", 2026, 25000.0, 1), (None, 2026, 5.0, 1)]
    ok, line = gates.commission(vdir, {"conn": FakeConn(table), "years": list(range(2017, 2027))})
    assert ok and "2 party-years" in line and "unresolved" in line, line
    plant(vdir, paths.path("home"), lambda o: [p.update({"disclosed_by_year": {"2023": 1.0, "2026": 25000.0}}) for p in o["parties"] if p["key"] == X.A])
    ok, line = gates.commission(vdir, {"conn": FakeConn(table), "years": list(range(2017, 2027))})
    assert not ok and "ACT New Zealand 2023: version $1.00, the Commission's table $40,000.00" in line
    assert not gates.commission(vdir, {"years": [2017]})[0]


def test_the_compare_gate_refuses_a_fall_unless_allowed(built, tmp_path):
    out, vdir = built
    prev = str(tmp_path / "prev")
    import shutil
    shutil.copytree(vdir, prev)
    assert gates.compare(vdir, {"previous": prev})[0]
    plant(prev, paths.path("donor", "Jane Q Donor"), lambda o: o["totals"].update({"total": 99999.0}))
    ok, line = gates.compare(vdir, {"previous": prev})
    assert not ok and "1 total(s) fell ($99,399.00)" in line
    ok, line = gates.compare(vdir, {"previous": prev, "allow_drop": True})
    assert ok and "(--allow-drop)" in line
    assert gates.compare(vdir, {})[0]


def test_a_second_build_compares_against_the_first(built, monkeypatch):
    out, vdir = built
    plant(vdir, paths.path("donor", "Jane Q Donor"), lambda o: o["totals"].update({"total": 99999.0}))
    ok, stamp, lines = B.build("2026-10-20T0620", out, stamp="2026-10-20T0901", listings_folder=os.path.join(os.path.dirname(out), "listings"), log=lambda s: None)
    assert not ok and any("FAIL  compare" in l for l in lines)
    rows = [json.loads(l) for l in open(os.path.join(out, "RELEASES.jsonl"))]
    assert rows[-1]["action"] == "refused"
    ok, stamp, lines = B.build("2026-10-20T0620", out, stamp="2026-10-20T0902", listings_folder=os.path.join(os.path.dirname(out), "listings"),
                               log=lambda s: None, allow_drop=True)
    assert ok


def test_the_statements_gate_recounts_the_lane_by_sql(built):
    out, vdir = built
    ctx = {"conn": X.NoConn(), "years": list(range(2017, 2027))}
    ok, line = gates.statements(vdir, ctx)
    assert ok and "1 parties' statements" in line, line
    rel = paths.path("subject", "party", "ACT New Zealand")
    plant(vdir, rel, lambda o: o["financials"].pop())
    ok, line = gates.statements(vdir, ctx)
    assert not ok and "page lists 1 statement(s)" in line, line
    plant(vdir, rel, lambda o: o["financials"].append({"filed_year": 2025, "figures": {"income": {"amount": 1.0}}}))
    ok, line = gates.statements(vdir, ctx)
    assert not ok and "income" in line
    assert not gates.statements(vdir, {"conn": None, "years": [2017]})[0]
