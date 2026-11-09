"""The old-estate copy (ruling 160): the inventory's NEW and PARTLY entries only; a fake old table in a scratch schema
of the sample database copied verbatim in checked batches, resumed after a stop, a row changed on the way caught by
the md5 and rolled back, a table with no key or an old type refused; the file copier landing PDFs and images by
their bytes and resuming its walk. The data is made up here (generate_series), never a real row."""
import datetime as dt
import os

import pytest

from support import db, sample
from support.oldcopy import ensure_ledger, inventory, off_peak
from support.oldcopy import files as F
from support.oldcopy import tables as T

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ── the inventory, pure ──────────────────────────────────────────────────────

INV = {"tables": [
    {"database": "incoming_news", "schema": "public", "table": "a_new", "status": "NEW"},
    {"database": "incoming_news", "schema": "public", "table": "a_held", "status": "HELD"},
    {"database": "incoming_news", "schema": "public", "table": "a_derived", "verdict": "derived"},
    {"database": "incoming_news", "schema": "public", "table": "an_out", "status": "OUT"},
    {"database": "incoming_news", "schema": "public", "table": "a_strange", "status": "MAYBE"},
    {"database": "extractions", "schema": "v3", "table": "a_part", "status": "PARTLY",
     "missing": [{"after": 10, "through": 20}, {"after": [50], "through": None}]},
    {"database": "extractions", "schema": "v3", "table": "a_part_unnamed", "status": "PARTLY"},
    {"database": "querynz_v4", "schema": "public", "table": "not_old", "status": "NEW"},
], "stores": {
    "v3-staging": {"root": "/x/staging", "status": "NEW"},
    "v3-held": {"root": "/x/held", "status": "HELD"},
    "v3-pages": {"root": "/x/pages", "status": "PARTLY", "html": True},
}}


def test_only_new_and_partly_tables_are_copied_and_the_rest_said_why():
    todo, skipped = inventory.tables(INV, ("incoming_news", "extractions"))
    assert [t.piece for t in todo] == ["incoming_news:public.a_new", "extractions:v3.a_part"]
    why = {n: w for n, _, w in skipped}
    assert set(why) == {"incoming_news:public.a_held", "incoming_news:public.a_derived", "incoming_news:public.an_out",
                        "incoming_news:public.a_strange", "extractions:v3.a_part_unnamed", "querynz_v4:public.not_old"}
    assert "not guessed" in why["extractions:v3.a_part_unnamed"]
    assert todo[1].ranges == ((["10"], ["20"]), (["50"], None))
    assert todo[0].ranges == ((None, None),)


def test_only_new_and_partly_stores_are_walked():
    todo, skipped = inventory.stores(INV)
    assert [(s.name, s.html) for s in todo] == [("v3-staging", False), ("v3-pages", True)]
    assert [n for n, _, _ in skipped] == ["v3-held"]


def test_a_piece_key_is_database_schema_table():
    assert inventory.parse_piece("nzbn_canonical:bulk.x_y") == ("nzbn_canonical", "bulk", "x_y")
    with pytest.raises(ValueError):
        inventory.parse_piece("nzbn_canonical:x; drop")


def test_off_peak_is_the_night_hours_in_new_zealand():
    utc = dt.timezone.utc
    assert off_peak(dt.datetime(2026, 11, 10, 10, 30, tzinfo=utc))      # 23:30 NZDT
    assert off_peak(dt.datetime(2026, 11, 10, 16, 30, tzinfo=utc))      # 05:30 NZDT
    assert not off_peak(dt.datetime(2026, 11, 10, 17, 0, tzinfo=utc))   # 06:00 NZDT
    assert not off_peak(dt.datetime(2026, 11, 10, 1, 0, tzinfo=utc))    # 14:00 NZDT


def test_the_destination_is_private_and_names_its_old_schema():
    assert T.dest_schema("nzbn_canonical") == "old_nzbn_canonical_private" and db.is_private(T.dest_schema("x"))
    assert T.dest_table("public", "t") == "t" and T.dest_table("bulk", "t") == "bulk__t"


# ── the walk, pure ───────────────────────────────────────────────────────────

def test_the_walk_resumes_past_its_cursor_in_its_own_order(tmp_path):
    for rel in ("a/b.pdf", "a-c.pdf", "a/d/e.png", "b.pdf", "z/y/x.pdf"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"%PDF-1.4 " + rel.encode())
    every = list(F.walk(str(tmp_path)))
    assert sorted(every) == sorted(["a/b.pdf", "a-c.pdf", "a/d/e.png", "b.pdf", "z/y/x.pdf"])
    for i, cur in enumerate(every):
        assert list(F.walk(str(tmp_path), cur)) == every[i + 1:], cur
    assert list(F.walk(str(tmp_path), None, ("a",))) == [r for r in every if not r.startswith("a/")]
    seen, real = [], os.scandir

    def scandir(p):
        seen.append(os.path.relpath(p, tmp_path))
        return real(p)
    F.os.scandir = scandir
    try:
        assert list(F.walk(str(tmp_path), "b.pdf")) == ["z/y/x.pdf"]
    finally:
        F.os.scandir = real
    assert seen == [".", "z", os.path.join("z", "y")]          # the folders walked before the cursor are not opened


def test_a_file_is_known_by_its_name_or_its_first_bytes(tmp_path):
    (tmp_path / "noname").write_bytes(b"%PDF-1.7 x")
    (tmp_path / "img").write_bytes(b"\x89PNG\r\n\x1a\n...")
    (tmp_path / "t.html").write_bytes(b"<html>")
    (tmp_path / "blob").write_bytes(b"hello")
    assert F.sniff(str(tmp_path / "noname"), "noname") == ("pdf", "application/pdf")
    assert F.sniff(str(tmp_path / "img"), "img")[0] == "image"
    assert F.sniff(str(tmp_path / "t.html"), "t.html")[0] == "web-page"
    assert F.sniff(str(tmp_path / "blob"), "blob")[0] == "other"
    assert F.wanted("pdf", False) and F.wanted("image", False) and not F.wanted("web-page", False)
    assert F.wanted("web-page", True) and not F.wanted("other", True) and not F.wanted("text", True)


# ── on the sample database ───────────────────────────────────────────────────

def _scratch() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_oldcopy"


@pytest.fixture()
def env():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    s = _scratch()
    src_s, dst_s, led = f"{s}_ocsrc", f"{s}_ocdst_private", f"{s}_ocledger_private"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as c:
        for x in (src_s, dst_s, led):
            c.execute(f"DROP SCHEMA IF EXISTS {x} CASCADE")
        c.execute(f"CREATE SCHEMA {src_s}")
        c.execute(f"CREATE TYPE {src_s}.mood AS ENUM ('a', 'b')")
        c.execute(f"""CREATE TABLE {src_s}.t (id bigint PRIMARY KEY, label text, amount numeric(12,2), at timestamptz,
                      f float8, tags text[], blob bytea, j jsonb, maybe int)""")
        c.execute(f"""INSERT INTO {src_s}.t SELECT g, 'label ' || g || CASE WHEN g % 7 = 0 THEN E'\\ttab\\nline' ELSE '' END,
                      g * 1.25, timestamptz '2020-01-01 00:00+13' + g * interval '1 hour 1 second', g / 3.0::float8,
                      ARRAY['x' || g, NULL], decode(md5(g::text), 'hex'), jsonb_build_object('g', g, 'h', 'é'),
                      CASE WHEN g % 3 = 0 THEN NULL ELSE g END FROM generate_series(1, 1234) g""")
        c.execute(f"CREATE TABLE {src_s}.nokey (a int, b text)")
        c.execute(f"INSERT INTO {src_s}.nokey VALUES (1, 'x')")
        c.execute(f"CREATE TABLE {src_s}.oldtype (id int PRIMARY KEY, m {src_s}.mood)")
        c.execute(f"CREATE TYPE {src_s}.span AS RANGE (subtype = float8)")
        c.execute(f"CREATE TABLE {src_s}.oldrange (id int PRIMARY KEY, r {src_s}.span)")
        c.execute(f"CREATE TABLE {src_s}.nullkey (a int UNIQUE, b text)")
        c.execute(f"CREATE TABLE {src_s}.exprkey (a text NOT NULL, b text)")
        c.execute(f"CREATE UNIQUE INDEX ON {src_s}.exprkey (lower(a))")
        c.execute(f"CREATE TABLE {src_s}.pair (a text NOT NULL, b int NOT NULL, v text, UNIQUE (a, b))")
        c.execute(f"INSERT INTO {src_s}.pair SELECT chr(97 + g % 5), g, 'v' || g FROM generate_series(1, 300) g")
        c.commit()
    src = T.prepare_source(db.connect(db.OWNER_KEY, "querynz_v4_sample"))
    dst = T.prepare_dest(db.connect(db.OWNER_KEY, "querynz_v4_sample"))
    ensure_ledger(dst, led)
    dst.commit()
    yield {"src": src, "dst": dst, "src_s": src_s, "dst_s": dst_s, "led": led}
    src.close()
    dst.close()


def test_the_source_connection_cannot_write_and_each_batch_is_one_snapshot(env):
    import psycopg
    with env["src"].transaction():
        assert env["src"].execute("SHOW transaction_isolation").fetchone()[0] == "repeatable read"
    with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
        with env["src"].transaction():
            env["src"].execute(f"CREATE TABLE {env['src_s']}.written (a int)")
    with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
        env["src"].execute(f"INSERT INTO {env['src_s']}.nokey VALUES (2, 'y')")      # outside a snapshot too


def _spec(src_s, table, status="NEW", ranges=((None, None),), key=()):
    return inventory.Table("querynz_v4_sample", src_s, table, status, key, ranges)


def _whole(conn, rel, order="id"):
    with conn.transaction() if conn.autocommit else _noop():
        return conn.execute(f"SELECT count(*), md5(string_agg(md5(s::text), '' ORDER BY {order})) FROM {rel} s").fetchone()


class _noop:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _copy(e, spec, **kw):
    return T.copy_table(e["src"], e["dst"], spec, schema=e["dst_s"], ledger=e["led"], log=lambda *_: None, **kw)


def test_a_table_is_copied_verbatim_in_checked_batches(env):
    e = env
    out = _copy(e, _spec(e["src_s"], "t"), rows=100)
    assert out == {"batches": 13, "rows": 1234, "caught_up": True, "stopped": ""}
    dst_rel = f"{e['dst_s']}.{e['src_s']}__t"
    assert _whole(e["dst"], dst_rel) == _whole(e["src"], f"{e['src_s']}.t")
    d = e["dst"]
    types = d.execute("SELECT string_agg(format_type(atttypid, atttypmod), ',' ORDER BY attnum) FROM pg_attribute "
                      "WHERE attrelid = %s::regclass AND attnum > 0", (dst_rel,)).fetchone()[0]
    assert types == "bigint,text,numeric(12,2),timestamp with time zone,double precision,text[],bytea,jsonb,integer"
    led = d.execute(f"SELECT count(*), bool_and(ok), sum(rows_landed), bool_and(md5_source = md5_landed) "
                    f"FROM {e['led']}.batches").fetchone()
    assert led == (13, True, 1234, True)
    assert d.execute("SELECT has_schema_privilege('qv4_read', %s, 'USAGE')", (e["dst_s"],)).fetchone()[0] is False
    d.rollback()


def test_a_stopped_copy_resumes_from_its_cursor_without_a_row_twice(env):
    e = env
    calls = {"n": 0}

    def stop():
        calls["n"] += 1
        return calls["n"] > 3                     # dawn after three batches

    first = _copy(e, _spec(e["src_s"], "t"), rows=200, stop=stop)
    assert first == {"batches": 3, "rows": 600, "caught_up": False, "stopped": "window"}
    second = _copy(e, _spec(e["src_s"], "t"), rows=200)
    assert second["rows"] == 634 and second["caught_up"]
    assert _whole(e["dst"], f"{e['dst_s']}.{e['src_s']}__t") == _whole(e["src"], f"{e['src_s']}.t")
    assert _copy(e, _spec(e["src_s"], "t"), rows=200)["batches"] == 0     # caught up: nothing more
    e["dst"].rollback()


def test_a_row_changed_on_the_way_is_caught_and_its_batch_rolled_back(env):
    e = env
    d = e["dst"]
    _copy(e, _spec(e["src_s"], "t"), rows=500, stop=iter([False, True]).__next__)   # one batch lands: ids 1..500
    rel = f"{e['dst_s']}.{e['src_s']}__t"
    d.execute(f"CREATE FUNCTION {e['dst_s']}.tamper() RETURNS trigger LANGUAGE plpgsql AS "
              f"$$ BEGIN IF NEW.id = 777 THEN NEW.label := NEW.label || '.'; END IF; RETURN NEW; END $$")
    d.execute(f"CREATE TRIGGER tamper BEFORE INSERT ON {rel} FOR EACH ROW EXECUTE FUNCTION {e['dst_s']}.tamper()")
    d.commit()
    with pytest.raises(T.Mismatch):
        _copy(e, _spec(e["src_s"], "t"), rows=500)
    assert d.execute(f"SELECT count(*), max(id) FROM {rel}").fetchone() == (500, 500)     # the bad batch is not there
    bad = d.execute(f"SELECT rows_source, rows_landed, md5_source <> md5_landed, ok FROM {e['led']}.batches "
                    f"ORDER BY batch_id DESC LIMIT 1").fetchone()
    assert bad == (500, 500, True, False)
    d.rollback()


def test_a_table_with_no_key_or_an_old_type_is_refused_and_recorded(env):
    e = env
    for table, why in (("nokey", "no usable key"), ("nullkey", "no usable key"), ("exprkey", "no usable key"), ("oldtype", "not carried"),
                       ("oldrange", "not carried")):
        with pytest.raises(T.Refused, match=why):
            _copy(e, _spec(e["src_s"], table))
    got = e["dst"].execute(f"SELECT piece FROM {e['led']}.refusals ORDER BY refusal_id").fetchall()
    assert [g[0].rsplit(".", 1)[1] for g in got] == ["nokey", "nullkey", "exprkey", "oldtype", "oldrange"]
    e["dst"].rollback()


def test_a_partly_table_copies_only_its_missing_ranges_and_a_two_column_key_works(env):
    e = env
    out = _copy(e, _spec(e["src_s"], "t", "PARTLY", ((["100"], ["250"]), (["1200"], None))), rows=40)
    ids = e["dst"].execute(f"SELECT min(id), max(id), count(*) FROM {e['dst_s']}.{e['src_s']}__t WHERE id <= 250").fetchone()
    assert ids == (101, 250, 150) and out["rows"] == 150 + 34
    e["dst"].rollback()
    _copy(e, _spec(e["src_s"], "pair"), rows=37)
    assert _whole(e["dst"], f"{e['dst_s']}.{e['src_s']}__pair", "a, b") == _whole(e["src"], f"{e['src_s']}.pair", "a, b")
    e["dst"].rollback()


def test_the_dry_run_measures_the_source_and_writes_nothing(env):
    e = env
    dry = T.dry_run(e["src"], _spec(e["src_s"], "t"), rows=100, log=lambda *_: None)
    assert (dry["rows"], dry["batches"], dry["key"]) == (1234, 13, ["id"])
    assert e["dst"].execute("SELECT to_regclass(%s)", (f"{e['dst_s']}.{e['src_s']}__t",)).fetchone()[0] is None
    _copy(e, _spec(e["src_s"], "t"), rows=100)
    import hashlib
    md5s = [r[0] for r in e["dst"].execute(f"SELECT md5_source FROM {e['led']}.batches ORDER BY batch_id")]
    assert hashlib.md5("".join(md5s).encode()).hexdigest() == dry["md5"]
    e["dst"].rollback()


class _Held:
    """The connection, its commits held, so the sample's docs tables are left as they were (rolled back at the end)."""
    def __init__(self, conn):
        self._c = conn

    def commit(self):
        pass

    def __getattr__(self, k):
        return getattr(self._c, k)


def test_old_files_land_by_their_bytes_and_the_walk_resumes(env, tmp_path):
    e = env
    tree, store_root = tmp_path / "old", tmp_path / "store"
    files = {"a/one.pdf": b"%PDF-1.4 one", "a/two.png": b"\x89PNG\r\n\x1a\n two", "a/page.html": b"<html>x",
             "b/noext": b"%PDF-1.4 three", "b/copy-of-one.pdf": b"%PDF-1.4 one", "c/notes.txt": b"x"}
    for rel, data in files.items():
        p = tree / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    store = inventory.Store("test-old", str(tree), "NEW", "test-old")
    conn = _Held(e["dst"])
    try:
        calls = {"n": 0}

        def stop():
            calls["n"] += 1
            return calls["n"] > 1

        first = F.copy_store(conn, store, root=str(store_root), ledger=e["led"], batch=2, stop=stop, log=lambda *_: None)
        assert first["stopped"] == "window" and sum(first["counts"].values()) == 2
        F.copy_store(conn, store, root=str(store_root), ledger=e["led"], batch=2, log=lambda *_: None)
        got = dict(conn.execute(f"SELECT old_path, outcome FROM {e['led']}.files WHERE store = 'test-old'").fetchall())
        assert got == {"a/one.pdf": "landed-new", "a/two.png": "landed-new", "b/noext": "landed-new",
                       "b/copy-of-one.pdf": "landed-held"}
        assert len([p for p in store_root.rglob("*") if p.is_file()]) == 3      # three distinct contents, no second copy
        from support.docstore import landing
        shas = landing.find_by_name(str(tree / "b/noext"), conn)
        assert [d["kind"] for d in landing.documents_of(shas, conn).values()] == ["pdf"]
        conn.execute(f"DELETE FROM {e['led']}.file_cursors WHERE store = 'test-old'")   # the walk again from the start
        again = F.copy_store(conn, store, root=str(store_root), ledger=e["led"], log=lambda *_: None)
        assert again["counts"] == {"held-by-path": 4, "not-wanted": 2}
    finally:
        e["dst"].rollback()
