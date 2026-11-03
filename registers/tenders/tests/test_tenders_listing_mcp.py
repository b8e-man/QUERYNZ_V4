"""The GETS listing as the ingest MCP serves it (listing.py; rulings 96, 138, 142): records made in the recorded shape
(support/mcpsource/shapes.json, no database), then one load into a scratch schema of the sample database. Every
name and value is invented."""
import hashlib
import os

import pytest

from support import db
from support import mcpsource as M
from support.mcpsource.tests.fake import made_record
from registers.tenders import listing as L

SCRATCH = "scratch_tenders_listing_test"
REGIONS = "Regions: Auckland Bay of Plenty Hawke's Bay West Coast Exemption Reason"


def _rec(n, **kw):
    r = made_record("gets", n, M.shapes()["gets"])
    r.update({"id": f"https://www.gets.govt.nz/ExternalTenderDetails.htm?id={n}", "kind": "tender_notice",
              "case_slug": str(30000000 + n), "court": "gets"})
    r["page_fields"] = {"RFx ID": str(30000000 + n), "Tender Name": f"Tender {n}", "Overview": "Works.",
                        "Contact": "A Person, 021 000 000", "Agency Address": "1 Invented Street, Wellington",
                        REGIONS: "None", "Indicative Total Value": "$1m - $2m"}
    r.update(kw)
    return r


def _read(*recs):
    store = {hashlib.sha256(M.record_bytes(r)).hexdigest(): M.record_bytes(r) for r in recs}
    return L.read([(s, i, None) for i, s in enumerate(store)], store.__getitem__, loaded_at="2026-11-04T14:00:00+13:00")


def test_every_recorded_field_and_every_stable_page_label_has_a_column():
    """Ruling 96: their fields in our registers. A field the shapes record and the reading lacks fails here."""
    shape = M.shapes()["gets"]
    assert set(shape["fields"]) <= set(L.FIELDS) | set(L.PRIVATE_FIELDS) | {"seq"}, \
        set(shape["fields"]) - set(L.FIELDS) - set(L.PRIVATE_FIELDS)
    assert set(shape["items"]["page_fields"]) <= set(L.LABELS) | set(L.PRIVATE_LABELS)
    assert set(L.FIELDS.values()) | set(L.LABELS.values()) <= set(L.COLUMNS["listing"])
    sql = open(os.path.join(os.path.dirname(L.__file__), "listing.sql"), encoding="utf-8").read()
    for t, cols in list(L.COLUMNS.items()) + [("private", L.PRIVATE_COLUMNS["listing"])]:
        for c in cols:
            assert f"\n    {c} " in sql, (t, c)


def test_a_notice_is_read_with_its_page_s_labels_and_regions_and_the_contact_kept_private():
    res = _read(_rec(1))
    assert res.counts["notices"] == 1 and not res.set_aside
    row, priv = res.rows[0], res.private[0]
    assert (row["rfx_id"], row["provider_corpus"], row["page_tender_name"], row["indicative_total_value"]) == \
        ("30000001", "gets", "Tender 1", "$1m - $2m")
    assert row["regions"] == ["Auckland", "Bay of Plenty", "Hawke's Bay", "West Coast"]
    assert (row["regions_tail"], row["regions_tail_value"], row["regions_unread"]) == ("Exemption Reason", "None", None)
    assert row["fields_unread"] == [] and row["page_labels_unread"] == []
    assert "contact" not in row and "agency_address" not in row
    assert (priv["contact"], priv["agency_address"]) == ("A Person, 021 000 000", "1 Invented Street, Wellington")
    assert priv["page_fields"][REGIONS] == "None"


@pytest.mark.parametrize("label, want, printed", [
    ("Regions: New Zealand Required Pre-qualifications", ["New Zealand"], "New Zealand"),
    ("Regions: International Nelson Exemption Reason", ["International", "Nelson"], "International Nelson"),
    ("Regions: N/A Exemption Reason", [], "N/A"),
])
def test_the_regions_label_reads_every_form_gets_prints(label, want, printed):
    """Measured on the 8,547 records of 4 November: besides the region names, GETS prints New Zealand (2,184),
    International (642) and N/A (64)."""
    found, as_printed, unread, _ = L.regions_of(label)
    assert (found, as_printed, unread) == (want, printed, None)


def test_a_new_label_and_a_new_field_are_listed_never_dropped_and_the_last_version_is_read():
    old = _rec(2)
    new = _rec(2, page_fields={**_rec(2)["page_fields"], "Award Date": "1 May 2026"}, award_value="1")
    res = _read(old, new)
    assert res.counts["notices"] == 1 and res.counts["older versions"] == 1
    row = res.rows[0]
    assert row["versions"] == 2 and row["page_labels_unread"] == ["Award Date"] and row["fields_unread"] == ["award_value"]
    assert res.counts["records with a field unread"] == 1


def test_a_record_of_the_first_shape_without_the_page_s_fields_is_read_too():
    r = _rec(3)
    for f in ("page_fields", "open_date", "categories", "coverage", "prequalifications", "http_headers"):
        r.pop(f, None)
    row = _read(r).rows[0]
    assert row["regions"] == [] and row["regions_as_printed"] is None and row["overview"] is None
    assert row["fields_unread"] == []


def test_another_kind_is_set_aside_with_the_reason():
    res = _read(_rec(4, kind="award_notice"))
    assert not res.rows and res.set_aside[0]["stage"] == "recognise"


def test_the_load_fills_the_tables_and_reconciles():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here")
    recs = [_rec(5), _rec(6), _rec(6, tender_type="RFP"), _rec(7, kind="award_notice")]
    store = {hashlib.sha256(M.record_bytes(r)).hexdigest(): M.record_bytes(r) for r in recs}
    items = [(s, i, None) for i, s in enumerate(store)]
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        with conn.transaction():
            counts = L.load(conn, SCRATCH, items, store.__getitem__)
        rows = conn.execute(f"SELECT key, tender_type, regions, page_labels_unread FROM {SCRATCH}.listing ORDER BY key").fetchall()
        priv = conn.execute(f"SELECT count(*), count(contact), count(page_fields) FROM {SCRATCH}_private.listing").fetchone()
        aside = conn.execute(f"SELECT count(*) FROM {SCRATCH}.listing_set_aside").fetchone()[0]
    assert counts["notices"] == 2 and counts["older versions"] == 1 and aside == 1
    assert [r[1] for r in rows][1] == "RFP", "the version the pull saw last"
    assert rows[0][2] == ["Auckland", "Bay of Plenty", "Hawke's Bay", "West Coast"] and rows[0][3] == []
    assert tuple(priv) == (2, 2, 2)


def test_the_profile_the_reading_stamps_is_in_the_ledger():
    from support import profiles
    p = profiles.profile(L.PROFILE)
    assert p["version"] == L.PROFILE_VERSION and p["signals"]["name_prefix"] == "gets/"
