"""The adopt (`--adopt`): a session's pull record and the store rows of its
documents carried from one database to another, in batches, resumable.
A fake pair in the sample database: a source pull schema with its own
scratch store schema, and a live pull schema with another; two
connections, as the job has. The bytes go to a temporary store root."""
import hashlib
import os

import pytest

from support import db
from support import mcpsource as M
from support.docstore import landing
from support.mcpsource.tests.fake import FakeServer, client_for, corpus_of

SRC, DST = "scratch_test_adopt_src", "scratch_test_adopt_dst"
SRC_STORE, DST_STORE = "scratch_test_adopt_srcstore", "scratch_test_adopt_dststore"
SCHEMAS = (SRC, DST, SRC_STORE, DST_STORE, SRC + "_mcpsource_named")


def no_sleep(_s):
    return None


class StoreLand:
    """The landing wrapper's effect on a scratch store schema: the bytes on
    disk under `root`, a document row and its names."""

    def __init__(self, store, root):
        self.store, self.root = store, root

    def __call__(self, data, *, name, source, conn, name_kind="file", content_type="", fetched_at=None, root=None,
                 kind_hint=""):
        sha = hashlib.sha256(data).hexdigest()
        landing.write_bytes(data, sha, self.root)
        new = conn.execute(f"INSERT INTO {self.store}.documents (sha256, size, kind, source, fetched_at, path) "
                           "VALUES (%s, %s, 'other', %s, %s, %s) ON CONFLICT DO NOTHING",
                           (sha, len(data), source, fetched_at, landing.path_for(sha, self.root))).rowcount == 1
        conn.execute(f"INSERT INTO {self.store}.names (sha256, name, kind) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                     (sha, name, name_kind))
        return type("Ref", (), {"sha256": sha})(), new


@pytest.fixture()
def pair(tmp_path):
    """(src, dst, root): the source pull filled from a fake server (three
    corpora, a changed record that is a second document, a field new to
    us), the live record empty."""
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    with db.connect(db.OWNER_KEY, "querynz_v4_sample", autocommit=True) as src, \
            db.connect(db.OWNER_KEY, "querynz_v4_sample", autocommit=True) as dst:
        for s in SCHEMAS:
            src.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")
        for s in (SRC_STORE, DST_STORE):
            src.execute(f"CREATE SCHEMA {s}")
            src.execute(landing.tables_sql().replace("docs.", f"{s}.").replace("docs_", f"{s}_"))
        M.Tables(src, SRC).create()
        served = {"beehive": corpus_of("beehive", 23), "parliament-bills": corpus_of("parliament-bills", 7),
                  "parliament-wayback": corpus_of("parliament-wayback", 4)}
        served["beehive"][3]["sentiment"] = "warm"
        server, land = FakeServer(served), StoreLand(SRC_STORE, str(tmp_path))
        for c in served:
            M.pull(src, client_for(server), c, SRC, land=land, sleep=no_sleep)
        served["beehive"][2]["title"] = "changed in place"
        M.pull(src, client_for(server), "beehive", SRC, land=land, sleep=no_sleep, rewalk=True)
        yield src, dst, str(tmp_path)
        for s in SCHEMAS:
            src.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")


def _adopt(src, dst, root, **kw):
    return M.adopt(src, dst, SRC, DST, log=lambda _l: None, root=root, src_store=SRC_STORE, dst_store=DST_STORE,
                   **{"batch": 5, **kw})


def _n(conn, table):
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_the_record_and_its_documents_are_carried_whole_and_a_rerun_adds_nothing(pair):
    src, dst, root = pair
    assert _n(src, f"{SRC}.arrivals") == 35 and _n(src, f"{SRC_STORE}.documents") == 35 and _n(src, f"{SRC}.drift") == 1
    names = _n(src, f"{SRC_STORE}.names")
    res = _adopt(src, dst, root)
    assert res["ok"], res["red"]
    assert {x: v["added"] for x, v in res["tables"].items()} == {"cursors": 3, "arrivals": 35, "catch": 0, "drift": 1}
    assert res["per corpus"] == {"beehive": [24, 24], "parliament-bills": [7, 7], "parliament-wayback": [4, 4]}
    d = res["documents"]
    assert (d["asked"], d["copied"], d["held"], d["names"], d["names live"]) == (35, 35, 0, names, names)
    assert _n(dst, f"{DST_STORE}.documents") == 35 and _n(dst, f"{DST_STORE}.names") == names
    assert M.Tables(dst, DST).cursors() == M.Tables(src, SRC).cursors()
    again = _adopt(src, dst, root)
    assert again["ok"] and all(v["added"] == 0 for v in again["tables"].values())
    assert (again["documents"]["copied"], again["documents"]["held"], again["documents"]["names copied"]) == (0, 35, 0)
    assert _n(dst, f"{DST_STORE}.documents") == 35 and _n(dst, f"{DST}.arrivals") == 35


def test_a_killed_adopt_is_finished_by_its_rerun(pair):
    src, dst, root = pair
    calls = []

    def dies_on_the_third_batch(*a, **kw):
        calls.append(1)
        if len(calls) == 3:
            raise KeyboardInterrupt("killed at the deadline")
        return landing.copy_documents(*a, **kw)

    with pytest.raises(KeyboardInterrupt):
        _adopt(src, dst, root, copy=dies_on_the_third_batch)
    assert _n(dst, f"{DST_STORE}.documents") == 10          # two batches of five landed, the third rolled back
    # a table part-copied (as by an older adopt): the rerun adds only what the live one lacks
    dst.execute(f"DELETE FROM {DST}.arrivals WHERE corpus = 'beehive' AND seq >= 10")
    res = _adopt(src, dst, root)
    assert res["ok"], res["red"]
    assert res["tables"]["arrivals"]["live before"] == 22 and res["tables"]["arrivals"]["added"] == 13
    assert res["tables"]["cursors"]["added"] == 0
    assert (res["documents"]["held"], res["documents"]["copied"]) == (10, 25)
    assert _n(dst, f"{DST_STORE}.documents") == 35 and _n(dst, f"{DST}.arrivals") == 35


def test_a_document_the_live_store_holds_is_skipped_and_left_as_it_is(pair):
    src, dst, root = pair
    sha, path, fetched = src.execute(f"SELECT sha256, path, fetched_at FROM {SRC_STORE}.documents "
                                     "ORDER BY sha256 LIMIT 1").fetchone()
    dst.execute(f"INSERT INTO {DST_STORE}.documents (sha256, size, kind, source, fetched_at, path, landed_at) "
                "VALUES (%s, 1, 'other', 'query-nz', %s, %s, '2026-10-27T08:21:00+13:00')", (sha, fetched, path))
    before = dst.execute(f"SELECT * FROM {DST_STORE}.documents WHERE sha256 = %s", (sha,)).fetchone()
    res = _adopt(src, dst, root)
    assert res["ok"], res["red"]
    assert (res["documents"]["held"], res["documents"]["copied"]) == (1, 34)
    assert dst.execute(f"SELECT * FROM {DST_STORE}.documents WHERE sha256 = %s", (sha,)).fetchone() == before
    assert _n(dst, f"{DST_STORE}.names") == _n(src, f"{SRC_STORE}.names")     # its names were added all the same


def test_a_count_that_differs_or_a_document_without_its_bytes_is_red(pair):
    src, dst, root = pair
    gone = src.execute(f"SELECT sha256 FROM {SRC}.arrivals WHERE corpus = 'parliament-bills' LIMIT 1").fetchone()[0]
    os.remove(landing.path_for(gone, root))
    res = _adopt(src, dst, root)
    assert not res["ok"]
    assert "documents parliament-bills: 7 in the source, 6 live" in res["red"]
    assert "documents: 1 with no bytes" in res["red"]
    dst.execute(f"INSERT INTO {DST}.arrivals (corpus, seq, record_id, sha256, new) "
                f"VALUES ('parliament-wayback', 99, 'x', '{'0' * 64}', true)")
    res = _adopt(src, dst, root)
    assert "arrivals parliament-wayback: 4 in the source, 5 live" in res["red"]


def test_a_schema_whose_name_holds_the_module_s_name_is_made_as_named(pair):
    src = pair[0]
    s = SRC + "_mcpsource_named"
    M.Tables(src, s).create()
    assert _n(src, f"{s}.arrivals") == 0
    assert src.execute("SELECT count(*) FROM pg_indexes WHERE schemaname = %s AND indexname LIKE %s",
                       (s, f"{s}_arrivals_%")).fetchone()[0] == 2
