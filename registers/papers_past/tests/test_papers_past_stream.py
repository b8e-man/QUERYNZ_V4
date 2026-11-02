"""The streaming load's chunk commits and its resume (step 8.6, the full run), on fake dump lines against the sample
database and a store in a temporary folder: a run stopped after a chunk commits, or in the middle of a chunk with frames
already on the disk, resumes after its last committed chunk and ends with the same catalogue, the same catch log and
the same bytes in the same files as a run that never stopped; a second row of an article already held is set aside at
`once` by the catalogue's key; the whole batch reconciles; the stride keeps its phase across a resume."""
import os

import pytest

from registers.papers_past import capture, load, store
from registers.papers_past.tests.test_papers_past import PP, dump, row

pytestmark = pytest.mark.slow
DB = "querynz_v4_sample"
SOURCE = ("/nowhere/fake.sql.gz", "f" * 64, 1, "fake")


class Stop(Exception):
    pass


def lines():
    rows = [row(i, PP.format(i), f"the text of item {i} " * (i + 1)) for i in range(1, 11)]
    rows.insert(3, row(90, PP.format(90), None, "MIGRATION_ERROR"))
    rows.insert(6, row(91, "https://paperspast.natlib.govt.nz/newspapers/evening-post/1904"))
    rows.append(row(92, PP.format(2), "a second row of item 2"))
    rows.append(row(93, "https://paperspast.natlib.govt.nz/newspapers/TC19170911.2.30", "another paper, another year"))
    return dump(*rows)


def source_rows(stop_after=None, every=1):
    """rows_from for run(): the fake dump from the checkpoint; with stop_after, the stream stops after that many rows."""
    def rows_from(after, seen, n):
        for k, r in enumerate(capture.take(iter(lines()), n, after, every, None, seen), start=1):
            if stop_after is not None and k > stop_after:
                raise Stop()
            yield r
    return rows_from


@pytest.fixture
def conn():
    from support import db
    try:
        c = db.connect(db.OWNER_KEY, DB, connect_timeout=5)
    except Exception as exc:
        pytest.skip(f"no sample database: {type(exc).__name__}")
    yield c
    c.rollback()
    for s in ("scratch_test_pp_stream_a", "scratch_test_pp_stream_b"):
        c.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")
    c.commit()
    c.close()


def go(conn, schema, root, **kw):
    kw.setdefault("rows_from", source_rows())
    kw.setdefault("log", lambda *_: None)
    return load.run(conn, schema, database=DB, chunk=4, root=str(root), held=load.Held([5, 92]), source=SOURCE, **kw)


def died(conn):
    """The process stopped: what it had not committed is gone."""
    conn.rollback()


def picture(conn, schema, root):
    sdir = store.store_dir(DB, schema, str(root))
    items = conn.execute(f"SELECT key, upstream_id, sha256, chars, held_in_old, f.path, frame_at, at, i.bytes "
                         f"FROM {schema}.items i JOIN {schema}.files f USING (file) ORDER BY key").fetchall()
    catches = sorted(conn.execute(f"SELECT stage, item, reason FROM {schema}.catches").fetchall())
    stages = conn.execute(f"SELECT seq, stage, items_in, items_out, set_aside FROM {schema}.stages "
                          f"WHERE stage NOT LIKE '%%(measured)' ORDER BY seq").fetchall()
    return items, catches, stages, store.sizes(sdir)


def test_a_run_lands_in_chunks_reconciles_and_sets_a_second_row_aside_by_the_key(conn, tmp_path):
    out = go(conn, "scratch_test_pp_stream_a", tmp_path, fresh=True)
    assert (out["in"], out["landed"], out["set aside"], out["chunks"]) == (14, 11, 3, 4)
    assert out["reasons"] == {"article id: the URL is not a Papers Past article id": 1,
                              "text: the archive holds no text for it (MIGRATION_ERROR)": 1,
                              f"once: {load.TWICE}": 1}
    assert out["held in the old estate"] == 1, "92 is held but set aside; 5 is held and landed"
    items, catches, stages, sizes = picture(conn, "scratch_test_pp_stream_a", tmp_path)
    assert [s[1:] for s in stages] == [("in", 14, 14, 0), ("article id", 14, 13, 1), ("text", 13, 12, 1),
                                       ("once", 12, 11, 1), ("landed", 11, 11, 0)]
    assert {i[0] for i in items} >= {"EP19040730.2.115.2", "TC19170911.2.30"} and len(items) == 11
    assert ("once", "92", load.TWICE) in catches
    assert set(sizes) == {"text/EP/1904.zst", "text/TC/1917.zst"}
    sdir = store.store_dir(DB, "scratch_test_pp_stream_a", str(tmp_path))
    assert load.read_back(conn, "scratch_test_pp_stream_a", sdir, 100) == []


@pytest.mark.parametrize("stop_after", [8, 10])
def test_a_stopped_run_resumes_after_its_last_committed_chunk_and_ends_the_same(conn, tmp_path, monkeypatch, stop_after):
    """8 rows: stopped right after chunk 2 committed; 10: in the middle of chunk 3, with its frames already on the disk
    (one frame per item), which the resume must cut away."""
    monkeypatch.setattr(store, "FRAME", 1)
    go(conn, "scratch_test_pp_stream_a", tmp_path / "a", fresh=True)
    with pytest.raises(Stop):
        go(conn, "scratch_test_pp_stream_b", tmp_path / "b", fresh=True, rows_from=source_rows(stop_after))
    died(conn)
    sdir = store.store_dir(DB, "scratch_test_pp_stream_b", str(tmp_path / "b"))
    chunks = conn.execute("SELECT count(*), max(last_line) FROM scratch_test_pp_stream_b.chunks").fetchone()
    assert chunks[0] == 2
    committed = dict(conn.execute("SELECT path, bytes FROM scratch_test_pp_stream_b.files").fetchall())
    if stop_after == 10:
        assert store.sizes(sdir) != committed, "the stopped chunk left frames past the committed bytes"
    said = []
    out = go(conn, "scratch_test_pp_stream_b", tmp_path / "b", log=said.append)
    assert any(s.startswith("papers_past: resumed after chunk 2 ") for s in said), said[:2]
    assert [s.split(" committed:")[0] for s in said if " committed:" in s] == ["papers_past: chunk 3", "papers_past: chunk 4"], \
        "only chunks 3 and 4 are read again"
    assert (out["in"], out["landed"], out["set aside"], out["chunks"]) == (14, 11, 3, 4)
    a, b = picture(conn, "scratch_test_pp_stream_a", tmp_path / "a"), picture(conn, "scratch_test_pp_stream_b", tmp_path / "b")
    assert a == b, "a resumed run ends with the same catalogue, catches, stages and file bytes as one that never stopped"
    assert go(conn, "scratch_test_pp_stream_b", tmp_path / "b")["landed"] == 11, "a finished run is not run again"


def test_the_stride_keeps_its_phase_across_a_resume(conn, tmp_path):
    go(conn, "scratch_test_pp_stream_a", tmp_path / "a", fresh=True, every=3, rows_from=source_rows(every=3))
    with pytest.raises(Stop):
        go(conn, "scratch_test_pp_stream_b", tmp_path / "b", fresh=True, every=3, rows_from=source_rows(4, every=3))
    died(conn)
    go(conn, "scratch_test_pp_stream_b", tmp_path / "b", every=3, rows_from=source_rows(every=3))
    ka = [r[0] for r in conn.execute("SELECT upstream_id FROM scratch_test_pp_stream_a.items ORDER BY 1").fetchall()]
    kb = [r[0] for r in conn.execute("SELECT upstream_id FROM scratch_test_pp_stream_b.items ORDER BY 1").fetchall()]
    assert ka == kb and len(ka) >= 3


def test_a_resume_refuses_another_stride_and_a_store_that_lost_committed_text(conn, tmp_path):
    with pytest.raises(Stop):
        go(conn, "scratch_test_pp_stream_b", tmp_path, fresh=True, rows_from=source_rows(5))
    died(conn)
    with pytest.raises(RuntimeError, match="another dump, stride or store"):
        go(conn, "scratch_test_pp_stream_b", tmp_path, every=2)
    sdir = store.store_dir(DB, "scratch_test_pp_stream_b", str(tmp_path))
    f = os.path.join(sdir, "text/EP/1904.zst")
    committed = conn.execute("SELECT bytes FROM scratch_test_pp_stream_b.files WHERE path = 'text/EP/1904.zst'").fetchone()[0]
    assert os.path.getsize(f) > committed, "the stopped run's last rows were written past the committed bytes"
    os.truncate(f, committed - 1)
    with pytest.raises(RuntimeError, match="lost text"):
        go(conn, "scratch_test_pp_stream_b", tmp_path)


def test_the_held_ids_are_a_sorted_array_that_answers_membership():
    h = load.Held([30, 10, 20])
    assert 10 in h and 20 in h and 30 in h and 15 not in h and 31 not in h and 0 not in h and len(h) == 3
