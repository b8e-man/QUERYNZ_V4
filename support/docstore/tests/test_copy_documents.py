"""copy_documents: the rows of documents already in the store copied from
one database's store tables to another's, with the bytes untouched. Two
scratch store schemas in the sample database stand for the two databases."""
import hashlib
import os

import pytest

from support.docstore import landing

SRC, DST = "scratch_test_docstore_copy_src", "scratch_test_docstore_copy_dst"


@pytest.fixture()
def pair():
    import support.db as db
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    with db.connect(db.OWNER_KEY, "querynz_v4_sample", autocommit=True) as c:
        for s in (SRC, DST):
            c.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")
            c.execute(f"CREATE SCHEMA {s}")
            c.execute(landing.tables_sql().replace("docs.", f"{s}.").replace("docs_", f"{s}_"))
        yield c
        for s in (SRC, DST):
            c.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")


def _put(c, schema, data, root, names, path=None):
    sha = hashlib.sha256(data).hexdigest()
    landing.write_bytes(data, sha, root)
    c.execute(f"INSERT INTO {schema}.documents (sha256, size, kind, source, fetched_at, path) "
              "VALUES (%s, %s, 'other', 'test', '2026-10-27T08:00:00+13:00', %s)",
              (sha, len(data), path or landing.path_for(sha, root)))
    for n, k in names:
        c.execute(f"INSERT INTO {schema}.names (sha256, name, kind) VALUES (%s, %s, %s)", (sha, n, k))
    return sha


def _n(c, schema, t):
    return c.execute(f"SELECT count(*) FROM {schema}.{t}").fetchone()[0]


def test_rows_are_copied_held_ones_skipped_and_a_rerun_copies_nothing(pair, tmp_path):
    c, root = pair, str(tmp_path)
    a = _put(c, SRC, b"a", root, [("c/1", "file"), ("https://x/1", "url")], path="/tmp/elsewhere")
    b = _put(c, SRC, b"b", root, [("c/2", "file")])
    held = _put(c, DST, b"b", root, [("c/2-old", "file")])     # the live store already holds b, under another name
    assert held == b
    before = c.execute(f"SELECT landed_at, path FROM {DST}.documents WHERE sha256 = %s", (b,)).fetchone()
    n = landing.copy_documents(c, c, [a, b, a], root=root, src_store=SRC, dst_store=DST)
    assert (n["asked"], n["copied"], n["held"], n["no bytes"], n["absent"]) == (2, 1, 1, 0, [])
    assert n["names"] == 3 and n["names copied"] == 3 and n["names live"] == 3
    # the copied row names the store's own place for the bytes, not the source row's
    assert c.execute(f"SELECT path FROM {DST}.documents WHERE sha256 = %s", (a,)).fetchone()[0] == landing.path_for(a, root)
    assert c.execute(f"SELECT landed_at, path FROM {DST}.documents WHERE sha256 = %s", (b,)).fetchone() == before
    assert sorted(r[0] for r in c.execute(f"SELECT name FROM {DST}.names WHERE sha256 = %s", (b,))) == ["c/2", "c/2-old"]
    assert c.execute(f"SELECT count(*) FROM {DST}.landings WHERE sha256 = %s AND ok AND new", (a,)).fetchone()[0] == 1
    rows = _n(c, DST, "documents"), _n(c, DST, "names"), _n(c, DST, "landings")
    again = landing.copy_documents(c, c, [a, b], root=root, src_store=SRC, dst_store=DST)
    assert (again["copied"], again["held"], again["names copied"], again["names live"]) == (0, 2, 0, 3)
    assert (_n(c, DST, "documents"), _n(c, DST, "names"), _n(c, DST, "landings")) == rows


def test_the_bytes_are_never_read_or_rewritten_and_missing_bytes_are_not_copied(pair, tmp_path):
    c, root = pair, str(tmp_path)
    a = _put(c, SRC, b"the bytes", root, [("c/1", "file")])
    p = landing.path_for(a, root)
    with open(p, "wb") as f:                       # what is on disk no longer hashes to its name
        f.write(b"other bytes")
    os.utime(p, (1_000_000_000, 1_000_000_000))
    gone = _put(c, SRC, b"gone", root, [("c/2", "file")])
    os.remove(landing.path_for(gone, root))
    n = landing.copy_documents(c, c, [a, gone, "f" * 64], root=root, src_store=SRC, dst_store=DST)
    assert (n["copied"], n["no bytes"], n["no source row"]) == (1, 1, 1)
    assert sorted(n["absent"]) == sorted([gone, "f" * 64])
    assert open(p, "rb").read() == b"other bytes" and os.stat(p).st_mtime == 1_000_000_000
    assert c.execute(f"SELECT count(*) FROM {DST}.names WHERE sha256 = %s", (gone,)).fetchone()[0] == 0
