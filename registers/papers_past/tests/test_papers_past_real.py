"""The lane against the real dump and the real disk (step 8.6; slow): batch 1 re-landed as a catalogue with its text in the
store's files on /mnt/hdd2 must reconcile to the research file's figures (10,000 = 9,031 + 969); every item read back
from the files must match its sha256; the 1-million spread sample, where it has been built, must span the dump and
reconcile; and the keyword index must find what a plain scan of the same texts finds."""
import os
import re

import pytest

from registers.papers_past import capture, index, load, store

pytestmark = pytest.mark.slow
DB, SCHEMA, SAMPLE = "querynz_v4_sample", "scratch_test_papers_past", "scratch_papers_past_s1m"


@pytest.fixture(scope="module")
def conn():
    if not os.path.exists(os.path.join(capture.FOLDER, capture.DUMP)) or not os.path.isdir(os.path.dirname(store.ROOT)):
        pytest.skip("not node2: the dump or the 4 TB disk is not here")
    from support import db
    try:
        c = db.connect(db.OWNER_KEY, DB, connect_timeout=5)
    except Exception as exc:
        pytest.skip(f"no sample database: {type(exc).__name__}")
    with c:
        c.execute("SET statement_timeout = '1800s'")
        yield c


@pytest.fixture(scope="module")
def batch1(conn):
    out = load.build(conn, SCHEMA, 1, 10_000, database=DB, log=lambda *_: None)
    conn.commit()
    return out


def test_batch_one_reconciles_to_the_research_figures(batch1, conn):
    assert (batch1["in"], batch1["landed"], batch1["set aside"]) == (10_000, 9_031, 969)
    assert batch1["reasons"] == {"text: the archive holds no text for it (MIGRATION_ERROR)": 952,
                                 "text: the archive holds no text for it (CONTENT_COMPLETE)": 17}
    assert batch1["held in the old estate"] == 1_995 and batch1["text chars per item"] == 3_638
    cols = {r[0] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = %s "
                                       "AND table_name = 'items'", (SCHEMA,)).fetchall()}
    assert cols and "text" not in cols, "the database keeps the catalogue only"
    assert batch1["catalogue bytes per item"] < 400
    assert batch1["disk bytes per item"] < batch1["text bytes per item"], "the files are compressed"
    assert batch1["store"].startswith("/mnt/hdd2/qv4-papers-past/")


def test_every_item_of_batch_one_reads_back_from_the_files(batch1, conn):
    n = conn.execute(f"SELECT count(*) FROM {SCHEMA}.items").fetchone()[0]
    assert n == 9_031 and load.read_back(conn, SCHEMA, batch1["store"], n) == []


def test_the_keyword_index_finds_what_a_plain_scan_finds(batch1, conn, tmp_path):
    with conn.transaction():
        docs = list(index.documents(conn, SCHEMA, batch1["store"]))
    assert len(docs) == 9_031
    out = index.fts5(iter(docs), str(tmp_path / "fts5.sqlite"))
    word = re.compile(r"(?<![^\W_])kauri(?![^\W_])", re.I)
    assert out["queries"]["a rarer word"]["hits"] == sum(1 for _, t, x in docs if word.search(t) or word.search(x))
    try:
        import tantivy  # noqa: F401
    except ImportError:
        return
    tv = index.tantivy_index(iter(docs), str(tmp_path / "tantivy"))
    for label, q in tv["queries"].items():
        assert q["hits"] == out["queries"][label]["hits"], f"the two engines disagree on {label}"


def test_the_spread_sample_spans_the_dump_and_reconciles(conn):
    if not conn.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", (SAMPLE,)).fetchone():
        pytest.skip(f"{SAMPLE} not built here (python -m registers.papers_past.load --every 90 --items 1000000)")
    every, sdir = conn.execute(f"SELECT every, store FROM {SAMPLE}.batches").fetchone()
    stages = {r[0]: r[1:] for r in conn.execute(f"SELECT stage, items_in, items_out, set_aside FROM {SAMPLE}.stages")}
    assert every == 90 and stages["in"][0] == 1_000_000
    assert stages["in"][0] == stages["landed"][1] + sum(v[2] for k, v in stages.items() if not k.endswith("(measured)"))
    lo, hi, years = conn.execute(f"SELECT min(line), max(line), count(DISTINCT extract(year FROM published_on)) "
                                 f"FROM {SAMPLE}.items").fetchone()
    assert hi - lo > 50_000_000 and years > 80, "spread over the dump, not its first rows"
    assert load.read_back(conn, SAMPLE, sdir, 2_000) == []


def test_the_streamed_run_s_chunks_join_end_to_end_and_its_files_are_the_committed_ones(conn):
    """The 1,000,000-row streaming run resumed for 50,000 more (scratch_papers_past_st1m): the chunks follow one another
    in the dump, their sums are the stages, the store holds exactly the committed bytes, and items read back."""
    s = "scratch_papers_past_st1m"
    if not conn.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", (s,)).fetchone():
        pytest.skip(f"{s} not built here (python -m registers.papers_past.load --items 1000000, then --items 1050000)")
    chunks = conn.execute(f"SELECT chunk, first_line, last_line, rows_in, no_article + no_text + twice, landed "
                          f"FROM {s}.chunks ORDER BY chunk").fetchall()
    assert len(chunks) >= 2 and [c[0] for c in chunks] == list(range(1, len(chunks) + 1))
    assert all(b[1] > a[2] for a, b in zip(chunks, chunks[1:])), "a resumed chunk starts after the last committed line"
    stages = {r[0]: r[1:] for r in conn.execute(f"SELECT stage, items_in, items_out, set_aside FROM {s}.stages")}
    assert stages["in"][0] == sum(c[3] for c in chunks) == sum(c[4] + c[5] for c in chunks)
    n = conn.execute(f"SELECT count(*) FROM {s}.items").fetchone()[0]
    assert stages["landed"][1] == sum(c[5] for c in chunks) == n
    sdir = conn.execute(f"SELECT store FROM {s}.batches").fetchone()[0]
    assert store.sizes(sdir) == dict(conn.execute(f"SELECT path, bytes FROM {s}.files").fetchall())
    assert load.read_back(conn, s, sdir, 500) == []
