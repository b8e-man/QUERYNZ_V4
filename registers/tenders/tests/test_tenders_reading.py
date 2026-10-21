"""The lane's reading: its rules on invented files in the ministry's layouts
(tests/fixtures.py), then the filled sample (the real files, sample.list's
RFx IDs) against the row contract, the catch log, the ledger and the views,
and, marked slow, a full build from every listed file against the files'
own counts and the old estate's 29,874, built twice to show the keys do not
move. No model is called and nothing is fetched."""
import datetime as dt
import os

import psycopg
import pytest

from support import db, rowcontract, sample
from registers.tenders import check, load, read
from registers.tenders import sample as S
from registers.tenders.tests import fixtures

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_SCHEMA = "scratch_tenders_lane"
FULL_SCHEMA = "scratch_tenders_slow"


# ── the rules, on invented files ──────────────────────────────────────────────

def test_each_field_is_decoded_on_its_own():
    import collections
    notes = collections.Counter()
    header, recs = read.records(b"A,B\r\nCaf\xe9,\xc4\x81 macron\r\n", notes)
    assert header == ["A", "B"] and recs == [(1, ["Café", "ā macron"])]
    assert notes == {"a field read as Windows-1252": 1}


def test_dates_are_read_as_each_file_writes_them():
    import collections
    n = collections.Counter()
    assert read.date_of("5/03/2024", "current", n, "x") == "2024-03-05"
    assert read.date_of("20180412", "historic", n, "x") == "2018-04-12"
    assert read.date_of("31/02/2024", "current", n, "x") is None
    assert read.date_of("20181301", "historic", n, "x") is None
    assert read.date_of("2024-03-05", "current", n, "x") is None        # not the file's shape
    assert sum(n.values()) == 3


def test_an_amount_of_0_is_kept_as_published_and_is_not_a_value():
    assert read.value_of("0", "current") == ("0", None, "0 as published: no value given")
    assert read.value_of("190572", "current") == ("190572", 190572, "published")
    assert read.value_of("", "current")[1] is None
    assert read.value_of("$1,000", "current")[1] is None
    assert read.value_of(None, "historic")[2] == "the historic file has no amount column"


def test_the_business_number_field_is_kept_and_an_nzbn_taken_only_when_it_is_one():
    assert read.nzbn_form("9.42904E+12") == (None, "exponent form: digits lost")
    assert read.nzbn_form(fixtures.VALID_NZBN) == (fixtures.VALID_NZBN, "nzbn")
    assert read.nzbn_form("9429000000018") == (None, "13 digits, check digit fails")
    assert read.nzbn_form("NULL") == (None, "NULL") and read.nzbn_form("") == (None, "empty")
    assert read.nzbn_form("1234567") == (None, "7 digits")
    assert read.nzbn_form("GST 12-345-678") == (None, "other")


def test_a_file_is_recognised_by_its_header_and_nothing_else():
    f = fixtures.files()
    assert read.recognise(f[("notices", "current")][1]) == "gets-award-notices-current"
    assert read.recognise(f[("notices", "historic")][1]) == "gets-award-notices-historic"
    assert read.recognise(f[("suppliers", "historic")][1]) == "gets-supplier-data"
    assert read.recognise(fixtures.CHALLENGE) is None
    assert read.recognise(b"") is None


def test_a_file_its_profile_does_not_recognise_is_set_aside_whole():
    f = fixtures.files()
    f[("regions", "current")] = (f[("regions", "current")][0], fixtures.CHALLENGE)
    r = read.read(f)
    assert [(a["set_name"], a["stage"], a["place"]) for a in r.set_aside if a["stage"] == "recognise"] == [
        ("regions", "recognise", "whole file")]
    assert not any(n["regions"] for n in r.notices if n["era"] == "current")


def test_every_property_holds_on_the_fixtures():
    assert fixtures.properties(read) == []


def test_the_profiles_name_every_layout_the_reading_asks_for():
    for slug in set(read.PROFILE_OF.values()) | {"gets-schema-and-documentation"}:
        p = read.profile(slug)
        assert p["version"] >= 1 and p["by"] and p["recognise"], slug
        assert "address" not in (p.get("tables") or {}).get("read", []), slug


# ── the filled sample: the real files ─────────────────────────────────────────

def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


def _rows(conn, sql):
    cur = conn.execute(sql)
    cols = [c.name for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


@pytest.fixture(scope="module")
def filled():
    _db_or_skip()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SAMPLE_SCHEMA}")
        S.fill(conn, SAMPLE_SCHEMA, items)
        conn.commit()
        T = lambda t: load.table(SAMPLE_SCHEMA, t, True)
        yield {"conn": conn, "items": items, "notices": _rows(conn, f"SELECT * FROM {T('notices')}"),
               "suppliers": _rows(conn, f"SELECT * FROM {T('suppliers')}"),
               "ledger": _rows(conn, f"SELECT * FROM {T('read_files')}"),
               "asides": _rows(conn, f"SELECT * FROM {T('read_set_aside')}")}


def test_every_sample_row_meets_the_row_contract(filled):
    for row in filled["notices"] + filled["suppliers"]:
        assert rowcontract.validate({**row, "loaded_at": row["loaded_at"].isoformat(),
                                     "filed": {"opened_on": row.get("opened_on") and row["opened_on"].isoformat()}},
                                    dt.date.today()) == [], row["key"]
        assert row["read_from"] == "text" and row["place"].startswith("record ")


def test_the_sample_reads_exactly_the_notices_its_keys_name(filled):
    want = {f"tenders/{era}/{rfx}" for era, ids in S.keys_of(filled["items"]).items() for rfx in ids}
    want.discard("tenders/historic/18184651")                            # the RFx ID the notices file lacks
    assert {n["key"] for n in filled["notices"]} == want
    for led in filled["ledger"]:
        assert led["typed"] + led["set_aside"] + led["skipped"] == led["records"]
        assert led["records"] == check.count_records(open_doc(led["document"]))


def open_doc(sha):
    from support.docstore.landing import read_bytes
    return read_bytes(sha)


def test_the_real_hard_cases_read_as_published(filled):
    n = {x["key"]: x for x in filled["notices"]}
    a, b = n["tenders/historic/12994431"], n["tenders/current/12994431"]
    assert a["awarded_on"] != b["awarded_on"] and a["document"] != b["document"]
    assert n["tenders/current/11121012"]["awarded_amount_as_published"] == "0"
    assert n["tenders/current/11121012"]["value_nzd"] is None
    assert n["tenders/current/10199365"]["value_nzd"] > 0
    assert n["tenders/historic/10007376"]["award_type"] == "Not Awarded"
    assert n["tenders/historic/10007376"]["suppliers_named"] == 0
    assert n["tenders/historic/12994431"]["value_note"] == "the historic file has no amount column"
    assert n["tenders/historic/17435225"]["regions"] == []
    assert n["tenders/current/25011835"]["awarded_on"] > n["tenders/current/25011835"]["report_date"]
    assert all(x["categories"] for x in filled["notices"])
    s = filled["suppliers"]
    forms = {(x["rfx_id"], x["era"], x["nzbn_form"]) for x in s}
    assert {("16912433", "current", "exponent form: digits lost"), ("10096289", "historic", "exponent form: digits lost"),
            ("10058111", "historic", "7 digits")} <= forms
    assert any(x["rfx_id"] == "10199365" and x["nzbn_form"] == "NULL" for x in s)
    assert any(x["rfx_id"] == "10002541" and x["business_name"] is None for x in s)
    assert len([x for x in s if x["notice_key"] == "tenders/historic/10255554"]) >= 3
    twice = [x["key"] for x in s if x["notice_key"] == "tenders/current/19834916"]
    assert len(twice) == len(set(twice)) and any(k.endswith("/2") for k in twice)
    assert sorted((x["set_name"], x["stage"]) for x in filled["asides"]) == [
        ("categories", "join"), ("regions", "join"), ("suppliers", "join")]


def test_no_sample_row_carries_an_address_or_a_website(filled):
    for row in filled["notices"] + filled["suppliers"]:
        assert not [k for k in row if any(w in k for w in check.FORBIDDEN)], row["key"]


def test_the_views_carry_the_licence_and_no_address(filled):
    conn = filled["conn"]
    with conn.transaction() as tx:
        conn.execute(load.sql("publish.sql", SAMPLE_SCHEMA, True).replace("pub.", f"{SAMPLE_SCHEMA}.tenders_pub_"))
        problems = check.columns_problems(conn, SAMPLE_SCHEMA, "tenders_pub_")
        rows = _rows(conn, f"SELECT licence, attribution FROM {SAMPLE_SCHEMA}.tenders_pub_award_suppliers")
        raise psycopg.Rollback(tx)
    assert problems == []
    assert rows and {r["licence"] for r in rows} == {"CC BY 3.0 NZ"}
    assert all("Ministry of Business, Innovation and Employment" in r["attribution"] for r in rows)


# ── the full build, marked slow ───────────────────────────────────────────────

@pytest.fixture(scope="module")
def full():
    _db_or_skip()
    with db.connect(db.READ_KEY, "querynz_v4") as src, db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        src.execute("SET statement_timeout = '60s'")
        listed = load.listings(src)
        if len(listed) != 8:
            pytest.skip("the capture lists no full release of both eras")
        with conn.transaction():
            counts = load.build(conn, FULL_SCHEMA, listed)
        yield {"src": src, "conn": conn, "listed": listed, "counts": counts}


@pytest.mark.slow
def test_the_full_build_meets_the_files_own_counts_and_the_old_estate_s_29874(full):
    assert check.reading(full["conn"], FULL_SCHEMA, full["listed"]) == []
    assert full["counts"]["notices"] == 29874
    assert check.catalogue(full["src"]) == []


@pytest.mark.slow
def test_the_check_fails_when_a_notice_goes_missing(full):
    conn = full["conn"]
    with conn.transaction() as tx:
        conn.execute(f"DELETE FROM {FULL_SCHEMA}.notices WHERE key = 'tenders/current/11121012'")
        problems = check.reading(conn, FULL_SCHEMA, full["listed"])
        raise psycopg.Rollback(tx)
    assert any("notices current: 22559 rows" in p for p in problems), problems


@pytest.mark.slow
def test_a_second_full_build_gives_the_same_rows_under_the_same_keys(full):
    conn = full["conn"]
    q = (f"SELECT md5(string_agg(key || coalesce(awarded_on::text, '') || coalesce(value_nzd::text, ''), ',' "
         f"ORDER BY key)) FROM {FULL_SCHEMA}.notices")
    before = conn.execute(q).fetchone()[0]
    with conn.transaction():
        load.build(conn, FULL_SCHEMA, full["listed"])
    assert conn.execute(q).fetchone()[0] == before
