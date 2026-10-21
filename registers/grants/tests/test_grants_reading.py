"""The reading on invented documents (fixtures.py), and the filled sample (the
Department's real file at the records sample.list names, and a real Lottery
record of grants) against the row contract, the ledger, the views and the
check. No model is called and nothing is fetched."""
import os

import pytest

from support import db, rowcontract, sample
from registers.grants import check, load, read
from registers.grants import sample as S
from registers.grants.tests import fixtures

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_SCHEMA = "scratch_test_grants"
DIA_FILE = "a1da8259821c41dd8243aa90f6a4ac1d03e19c4026dc53bce8214505c3832083"
LOTTERY_NATIONAL = "16bd7a0b3d0e3494bb57419ace762082f9b2694f37bad15b6d2f413076399905"
INTERSTITIAL = "fe3dcaa5d2872d504b93e3708fb93df3c6f6f0db37d6f9b4529606d9f8d0e199"
CM_HOME = "9d579b4c2b1c8e7aadd0ce52ff93a97c3b26b87d3d26d7bb24f76b26c727d8a6"


def test_the_reading_as_written_holds_every_property():
    assert fixtures.properties(read) == []


def test_every_society_form_maps_to_a_publisher_row():
    keys = {p["key"] for p in read.publishers()}
    assert set(read.NAME_FORMS.values()) <= keys
    assert read.society_key("THE BENDIGO VALLEY SPORTS AND CHARITY FOUNDATION") == "bendigo-valley"
    assert read.society_key("Trillian Trust Limited") == read.society_key("Trillian Trust") == "trillian-trust"
    assert read.society_key("An Invented Trust") is None


def test_a_heading_gives_its_year_round_and_committee():
    assert read.heading_parts("2024-25 round one Lottery Community Auckland record of grants") == (
        "2024/25", "round one", "Community Auckland")
    assert read.heading_parts("Lottery Community Sector Research Fund 2021/22 record of grants") == (
        "2021/22", None, "Community Sector Research Fund")
    assert read.heading_parts("2024/25 Lottery Canterbury Kaikoura round two record of grants") == (
        "2024/25", "round two", "Canterbury Kaikoura")


def test_the_check_counts_records_without_the_reader():
    assert check.records_in_bytes(fixtures.dia_csv()) == 8
    assert check.records_in_bytes(b'a,b\n"x\ny",1\n"z",2') == 2


# ── the filled sample: real documents ─────────────────────────────────────────

def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


def _rows(conn, q, args=()):
    cur = conn.execute(q, args)
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


@pytest.fixture(scope="module")
def filled():
    _db_or_skip()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        S.fill(conn, SAMPLE_SCHEMA, items)
        conn.execute(load.sql("publish.sql", SAMPLE_SCHEMA).replace("pub.", f"{SAMPLE_SCHEMA}.v_"))
        conn.commit()
        T = lambda t: load.table(SAMPLE_SCHEMA, t)
        yield {"conn": conn, "items": items, **{t: _rows(conn, f"SELECT * FROM {T(t)}") for t in load.TABLES},
               "view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_grants")}


def test_the_sample_reads_what_it_names(filled):
    keyed = {int(i.split()[2]) for i in filled["items"] if i.startswith("key: dia ")}
    dia = [g for g in filled["grants"] if g["document"] == DIA_FILE]
    assert len(dia) + sum(1 for a in filled["read_set_aside"] if a["document"] == DIA_FILE) == len(keyed)
    assert [(a["place"], a["reason"]) for a in filled["read_set_aside"] if a["document"] == DIA_FILE] == [
        ("record 583", "no recipient named")]
    profiles = {d["document"]: d["profile"] for d in filled["read_documents"]}
    assert profiles[DIA_FILE] == read.DIA_CSV and profiles[LOTTERY_NATIONAL] == read.LOTTERY_PAGE
    assert {d["list"] for d in filled["read_documents"]} == {"dia-file", "lottery-page", "society-file"}


def test_every_row_meets_the_row_contract(filled):
    for r in filled["grants"] + filled["recipients"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]


def test_the_hard_cases_read_as_the_file_says(filled):
    g = {int(x["place"].split()[1]): x for x in filled["grants"] if x["document"] == DIA_FILE}
    assert g[3]["status"] == "Declined" and g[3]["amount_nzd"] is None and g[3]["decided_on"] is not None
    assert g[3]["recipient_final_as_published"] != g[3]["recipient_as_published"]
    assert g[2]["recipient_kind"] == "not shown to be an organisation"
    assert g[5]["amount_nzd"] % 1 != 0
    assert g[3241]["decided_on"] is None and g[3241]["period"].isdigit()
    assert g[12328]["nzbn"] == g[12328]["nzbn_as_published"] and len(g[12328]["nzbn"]) == 13
    assert g[18583]["nzbn"] is None and len(g[18583]["nzbn_as_published"]) == 12
    assert (g[11244]["grantor_key"], g[22538]["grantor_key"], g[88866]["grantor_key"]) == (
        "lion-foundation", "bendigo-valley", "tab-new-zealand")
    assert g[58811]["amount_granted_as_published"] is None
    assert g[115239]["refunded_on"] is None and g[120451]["refunded_on"] is not None
    assert g[136422]["charity_number"].startswith("CC") and g[141130]["charity_number"] is None
    assert g[178732]["status"] == "Refunded" and g[178732]["amount_nzd"] is None
    assert all(x["period"] >= "2017" for x in g.values())


def test_the_lottery_record_reads_whole(filled):
    rows = [x for x in filled["grants"] if x["document"] == LOTTERY_NATIONAL]
    assert len(rows) == 156 and sum(x["amount_nzd"] for x in rows) == 14710725
    assert sum(1 for x in rows if x["multi_year"]) == 61
    assert {(x["period"], x["round"], x["committee"]) for x in rows} == {("2024/25", "round two", "Community National")}
    assert {x["multi_year"] for x in rows if x["multi_year"]} == {"*2 year multi-year grant (no 3 year grants awarded)"}


def test_pages_that_are_no_record_are_not_recognised():
    from support.docstore.landing import path_for, read_bytes
    for sha in (INTERSTITIAL, CM_HOME):
        if not os.path.exists(path_for(sha)):
            pytest.skip("the document store is not here")
        assert read.recognise(read_bytes(sha)) is None
    from registers.grants import capture
    assert capture.challenged(200, read_bytes(INTERSTITIAL)) and not capture.challenged(200, read_bytes(CM_HOME))


def test_the_views_carry_the_licence_and_the_check_is_clean(filled):
    assert filled["view"] and all(r["attribution"] for r in filled["view"])
    assert all(r["licence"] == ("CC BY 4.0" if r["publisher_key"] == "dia" else read.SOCIETY_LICENCE)
               for r in filled["view"])
    assert {r["grantor_key"] for r in filled["view"] if r["publisher_key"] != "dia"} == {
        r["publisher_key"] for r in filled["view"] if r["publisher_key"] != "dia"}
    assert check.views(filled["conn"], f"{SAMPLE_SCHEMA}.v_") == []
    assert check.reading(filled["conn"], SAMPLE_SCHEMA) == []


def test_the_check_goes_red_on_a_broken_ledger_or_an_address(filled):
    conn = filled["conn"]
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    conn.execute(f"UPDATE {T('read_documents')} SET grants = grants + 1 WHERE document = %s", (LOTTERY_NATIONAL,))
    try:
        assert check.reading(conn, SAMPLE_SCHEMA) != []
    finally:
        conn.rollback()
    conn.execute(f"UPDATE {T('grants')} SET status = 'Declined' WHERE document = %s AND place = 'table row 1'",
                 (LOTTERY_NATIONAL,))
    try:
        assert any("not accepted carry an amount" in p for p in check.reading(conn, SAMPLE_SCHEMA))
    finally:
        conn.rollback()
    conn.execute(f"UPDATE {T('grants')} SET recipient_as_published = '12 Invented Street' "
                 "WHERE document = %s AND place = 'table row 2'", (LOTTERY_NATIONAL,))
    try:
        assert any("street address" in p for p in check.views(conn, f"{SAMPLE_SCHEMA}.v_"))
    finally:
        conn.rollback()
    conn.execute(f"UPDATE {T('publishers')} SET attribution = '' WHERE key = 'dia'")
    try:
        assert any("no licence or attribution" in p for p in check.views(conn, f"{SAMPLE_SCHEMA}.v_"))
    finally:
        conn.rollback()
    assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") == []


def test_the_outside_check_sees_a_society_missing_and_a_short_count(filled):
    """On the sample the Department's list cannot be met (18 records), so the check is red, naming societies."""
    out = check.outside(filled["conn"], SAMPLE_SCHEMA)
    assert not out["ok"] and any("societies on the Department's list have no grant" in p for p in out["problems"])
    assert any("records in its bytes" in p for p in out["problems"])


CHECK_MUTANTS = {
    "the bytes counted by the reader's rule": ("        elif b == 0x0A and not quoted:", "        elif b == 0x0A:"),
    "a street address missed": ("if r[1] and STREET.search(r[1])]", "if False]"),
    "a row with no attribution let through": ("WHERE coalesce(licence, '') = '' OR coalesce(attribution, '') = ''",
                                              "WHERE false"),
    "a declined amount let through": ("WHERE amount_nzd IS NOT NULL AND status <> 'Accepted'", "WHERE false"),
}


def check_properties(mod, conn) -> list:
    """The rules the check keeps, on the filled sample; the names of the ones `mod` breaks."""
    T = lambda t: load.table(SAMPLE_SCHEMA, t)
    broken = []
    if mod.records_in_bytes(b'a,b\n"x\ny",1\n"z",2') != 2:
        broken.append("a line break inside quotes is no record")
    for sql, finder, what in (
            (f"UPDATE {T('grants')} SET recipient_as_published = '12 Invented Street' WHERE place = 'table row 2'",
             lambda: mod.views(conn, f"{SAMPLE_SCHEMA}.v_"), "a street-shaped name"),
            (f"UPDATE {T('publishers')} SET attribution = ''", lambda: mod.views(conn, f"{SAMPLE_SCHEMA}.v_"),
             "a row with no attribution"),
            (f"UPDATE {T('grants')} SET status = 'Declined' WHERE place = 'table row 1'",
             lambda: mod.reading(conn, SAMPLE_SCHEMA), "a declined grant with an amount")):
        conn.execute(sql)
        try:
            if not finder():
                broken.append(what)
        finally:
            conn.rollback()
    return broken


def test_the_check_as_written_holds_every_property(filled):
    assert check_properties(check, filled["conn"]) == []


@pytest.mark.parametrize("name", sorted(CHECK_MUTANTS))
def test_each_broken_check_is_caught(name, filled):
    from registers.grants.tests.test_grants_mutants import mutant
    mod = mutant(os.path.join(LANE, "check.py"), name, *CHECK_MUTANTS[name])
    assert check_properties(mod, filled["conn"]), f"the mutant {name!r} passed every property"


@pytest.mark.slow
def test_the_whole_file_reads_and_reconciles():
    """The full tier: every record of the Department's file of 21 October 2026."""
    from support.docstore.landing import path_for, read_bytes
    if not os.path.exists(path_for(DIA_FILE)):
        pytest.skip("the document store is not here")
    data = read_bytes(DIA_FILE)
    r = read.read_dia_csv(data, DIA_FILE)
    assert r.records == check.records_in_bytes(data) == 178739
    assert len(r.grants) == 178729 and len(r.set_aside) == 10
    assert {g["grantor_key"] for g in r.grants} >= {k for k, (_, _, on) in read.SOCIETIES.items() if on}
