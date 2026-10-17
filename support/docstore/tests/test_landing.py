"""Landing writes the bytes first, then the row and the name in one
transaction; the same bytes again add a name and nothing more; a failure
leaves only a landing line. A fake connection for the fast tier, the
sample database for the slow one."""
import os

import pytest

import support.docstore as ds
from support.docstore import landing


class FakeConn:
    """Enough of psycopg for the wrapper: executes are recorded, SELECT on
    docs.documents answers from what was inserted, a transaction rolls back
    on an error."""

    def __init__(self, fail_on=None):
        self.docs, self.names, self.landings, self.fail_on = set(), [], [], fail_on
        self._tx = None

    def transaction(self):
        conn = self

        class Tx:
            def __enter__(s):
                conn._tx = {"docs": set(conn.docs), "names": list(conn.names), "landings": list(conn.landings)}

            def __exit__(s, et, ev, tb):
                if et is not None:
                    conn.docs, conn.names, conn.landings = conn._tx["docs"], conn._tx["names"], conn._tx["landings"]
                conn._tx = None
                return False
        return Tx()

    def execute(self, sql, params=()):
        if self.fail_on and self.fail_on in sql:
            raise RuntimeError("the database said no")
        s = " ".join(sql.split())
        if s.startswith("SELECT 1 FROM docs.documents"):
            return _Rows([(1,)] if params[0] in self.docs else [])
        if s.startswith("INSERT INTO docs.documents"):
            self.docs.add(params[0])
        elif s.startswith("INSERT INTO docs.names"):
            if (params[0], params[2], params[1]) not in self.names:
                self.names.append((params[0], params[2], params[1]))
        elif s.startswith("INSERT INTO docs.landings"):
            self.landings.append(params)
        elif s.startswith("SELECT name FROM docs.names"):
            return _Rows([(n,) for sha, k, n in self.names if sha == params[0]])
        elif s.startswith("SELECT DISTINCT sha256 FROM docs.names"):
            return _Rows([(sha,) for sha, k, n in self.names if n == params[0]])
        return _Rows([])


class _Rows:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def __iter__(self):
        return iter(self.rows)


def test_land_writes_bytes_then_row_and_name(tmp_path):
    conn = FakeConn()
    data = b"%PDF-1.4 a return"
    ref, new = landing.land(data, name="Act-2021.pdf", source="ec-donations", conn=conn, root=str(tmp_path))
    assert new and ref.sha256 == ds.sha256_bytes(data)
    p = landing.path_for(ref.sha256, str(tmp_path))
    assert open(p, "rb").read() == data and p.startswith(os.path.join(str(tmp_path), ref.sha256[:2]))
    assert ref.sha256 in conn.docs and conn.names == [(ref.sha256, "file", "Act-2021.pdf")]
    assert conn.landings[-1][3] is True          # new
    assert landing.read_bytes(ref, str(tmp_path)) == data


def test_the_same_bytes_again_add_a_name_and_nothing_more(tmp_path):
    conn = FakeConn()
    data = b"%PDF-1.4 a return"
    landing.land(data, name="Act-2021.pdf", source="ec-donations", conn=conn, root=str(tmp_path))
    ref, new = landing.land(data, name="dup-of-residue/ACT_2021.pdf", source="ec-donations", conn=conn, root=str(tmp_path))
    assert not new and len(conn.docs) == 1
    assert landing.names_of(ref.sha256, conn) == ["Act-2021.pdf", "dup-of-residue/ACT_2021.pdf"]
    assert landing.find_by_name("Act-2021.pdf", conn) == [ref.sha256]


def test_a_failed_landing_leaves_only_a_landing_line(tmp_path):
    conn = FakeConn(fail_on="INSERT INTO docs.names")
    with pytest.raises(RuntimeError):
        landing.land(b"bytes", name="x.pdf", source="s", conn=conn, root=str(tmp_path))
    assert conn.docs == set() and conn.names == []
    assert conn.landings and "the database said no" in conn.landings[-1][3]


def test_copy_from_old_keeps_the_old_path_as_a_name(tmp_path):
    old = tmp_path / "staging" / "ec-donations" / "archive" / "Green-2021.pdf"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"%PDF-1.4 green")
    conn = FakeConn()
    ref, new = landing.copy_from_old(str(old), "ec-donations", conn, root=str(tmp_path / "store"))
    assert new and old.read_bytes() == b"%PDF-1.4 green"      # the old file is untouched
    assert set(landing.names_of(ref.sha256, conn)) == {"Green-2021.pdf", str(old)}
    assert ref.fetched_at


@pytest.mark.slow
def test_the_tables_apply_and_a_landing_round_trips_in_the_sample_database(tmp_path):
    import support.db as db
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(landing.tables_sql())
        conn.commit()
        data = b"%PDF-1.4 slow-test " + os.urandom(8)
        ref, new = landing.land(data, name="slow-test.pdf", source="test", conn=conn, root=str(tmp_path))
        assert new
        ref2, new2 = landing.land(data, name="slow-test-again.pdf", source="test", conn=conn, root=str(tmp_path))
        assert not new2 and ref2.sha256 == ref.sha256
        assert sorted(landing.names_of(ref.sha256, conn)) == ["slow-test-again.pdf", "slow-test.pdf"]
        conn.execute("DELETE FROM docs.names WHERE sha256 = %s", (ref.sha256,))
        conn.execute("DELETE FROM docs.landings WHERE sha256 = %s", (ref.sha256,))
        conn.execute("DELETE FROM docs.documents WHERE sha256 = %s", (ref.sha256,))
        conn.commit()
