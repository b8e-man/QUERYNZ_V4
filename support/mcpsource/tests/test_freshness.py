"""support/mcpsource/freshness.py (ruling 159): the MCP's four spellings of a time, a reading of `corpora` and
`pipeline` as rows, the never-wiped history in a scratch schema of the sample database (a corpus that stops growing
is seen), and the pull calling it with every corpus of the listing, `--corpus` or not."""
import datetime as dt
import os

import pytest

from support import db
from support import mcpsource as M
from support.mcpsource import freshness as F
from support.mcpsource.tests.fake import FakeServer, client_for, corpus_of

UTC = dt.timezone.utc
AT = dt.datetime(2026, 11, 9, 16, 7, 30, tzinfo=UTC)
TEST_SCHEMA = "scratch_test_mcpfresh"


def test_the_four_spellings_of_a_time():
    want = dt.datetime(2026, 11, 7, 11, 15, 1, tzinfo=UTC)
    for s in ("2026-11-07T11:15:01+00:00", "2026-11-07T11:15:01Z", "2026-11-07 11:15:01+00:00",
              "2026-11-08 00:15:01+13:00", "2026-11-07 11:15:01"):
        assert F.parse_time(s) == want, s
    for s in (None, "", "yesterday", 5):
        assert F.parse_time(s) is None


LISTING = [{"name": "estate-worksafe", "records": 1439, "ingest_cursor": 1439, "arrivals_last_24h": 0,
            "newest_arrival": "2026-11-07 12:02:47+00:00", "date_to": "2026-11-07"},
           {"name": "courts", "records": 68967, "ingest_cursor": 68967, "arrivals_last_24h": 6183,
            "newest_arrival": "2026-11-09T16:06:56+00:00"},
           {"name": "odd", "records": "many", "newest_arrival": "not a time"}, {"label": "no name"}]
PIPELINE = {"lanes": [{"name": "courts-capture", "status": "active", "corpus": "courts"},
                      {"name": "parliament-doc-bytes", "status": "active"}, {"name": "mbie-bulk-csv", "status": "blocked"}]}


def test_a_reading_as_rows():
    rows = {r[1]: dict(zip(F.COLUMNS, r)) for r in F.rows_of(LISTING, PIPELINE, AT)}
    assert set(rows) == {"estate-worksafe", "courts", "odd"}                    # a listing entry with no name is no row
    w, c, o = rows["estate-worksafe"], rows["courts"], rows["odd"]
    assert w["newest_arrival"] == dt.datetime(2026, 11, 7, 12, 2, 47, tzinfo=UTC) and w["arrivals_last_24h"] == 0
    assert (w["pipeline_lane"], w["pipeline_read"]) == (None, True)            # read, and no lane names it
    assert (c["pipeline_lane"], c["pipeline_status"], c["records"]) == ("courts-capture", "active", 68967)
    assert o["records"] is None and o["newest_arrival"] is None
    unread = {r[1]: dict(zip(F.COLUMNS, r)) for r in F.rows_of(LISTING, None, AT)}
    assert (unread["courts"]["pipeline_lane"], unread["courts"]["pipeline_read"]) == (None, False)


def test_pipeline_not_answering_is_none_not_a_failed_pull():
    server = FakeServer({"beehive": corpus_of("beehive", 2)})                  # the fake has no `pipeline` tool
    assert F.poll_pipeline(client_for(server), log=lambda _l: None) is None


def test_the_pull_hands_on_every_corpus_of_the_listing_before_it_pulls():
    served = {"beehive": corpus_of("beehive", 3), "parliament-bills": corpus_of("parliament-bills", 2)}
    server, seen = FakeServer(served), []

    class NoTables(M.Tables):
        def cursors(self):
            raise RuntimeError("stop: the listing was handed on first")

    real = M.Tables
    M.Tables = NoTables
    try:
        with pytest.raises(RuntimeError):
            M.pull_all(None, client_for(server), "x", only=["beehive"], on_listing=seen.append, sleep=lambda _s: None)
    finally:
        M.Tables = real
    assert [[c["name"] for c in got] for got in seen] == [["beehive", "parliament-bills"]]   # `only` or not


@pytest.fixture()
def conn():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    with db.connect(db.OWNER_KEY, "querynz_v4_sample", autocommit=True) as c:
        c.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
        assert F.latest(c, TEST_SCHEMA) == {}                                  # no table yet: nothing, no error
        M.Tables(c, TEST_SCHEMA).create()
        yield c
        c.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")


def test_the_history_is_kept_and_a_corpus_that_stops_growing_is_seen(conn):
    day = dt.timedelta(days=1)
    grow = [dict(LISTING[1], records=100 + i) for i in range(3)]
    for i, c in enumerate(grow):                                               # courts grows three days running
        F.record(conn, TEST_SCHEMA, [LISTING[0], c], PIPELINE, at=AT + i * day)
    F.record(conn, TEST_SCHEMA, [LISTING[0], grow[-1]], None, at=AT + 3 * day)  # then stops; pipeline silent
    assert conn.execute(f"SELECT count(*) FROM {TEST_SCHEMA}.freshness").fetchone()[0] == 8   # every reading kept
    got = F.latest(conn, TEST_SCHEMA)
    assert got["courts"]["at"] == AT + 3 * day and got["courts"]["records"] == 102
    assert got["courts"]["grew_at"] == AT + 2 * day                            # it last grew on the third reading
    assert got["courts"]["pipeline_read"] is False and got["courts"]["pipeline_lane"] is None
    assert got["estate-worksafe"]["grew_at"] is None                           # never grew inside what we hold
    assert F.record(conn, TEST_SCHEMA, [LISTING[0]], None, at=AT) == 1          # the same reading again: no second row
    assert conn.execute(f"SELECT count(*) FROM {TEST_SCHEMA}.freshness").fetchone()[0] == 8
