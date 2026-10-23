"""A restored database carries its source's collation: the copy records the
encoding, provider, collation and ctype from pg_database, the restore's
initdb and CREATE DATABASE use them, and a manifest without them takes the
live server's and says so. Fakes only: no database, no server started."""
import json
import types

from support.offsite import copy as C
from support.offsite import restore as R

NZ = {"encoding": "UTF8", "provider": "libc", "collate": "en_NZ.UTF-8", "ctype": "en_NZ.UTF-8",
      "locale": None, "icu_rules": None}


class FakeCursor:
    def __init__(self, row):
        self.row, self.sql = row, []

    def execute(self, sql, *a):
        self.sql.append(sql)

    def fetchone(self):
        return self.row


class FakeRunner:
    """Every command succeeds; the server answers at once."""

    def __init__(self):
        self.calls = []

    def __call__(self, argv, **kw):
        self.calls.append(argv)
        return types.SimpleNamespace(returncode=0, stderr=b"")

    def initdb(self):
        return next(c for c in self.calls if c[0] == "initdb")


class FakeConnection:
    def __init__(self, executed):
        self.executed = executed

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql):
        self.executed.append(sql)


def no_live(database):
    raise AssertionError("the live server was read though the manifest has the locale")


def test_the_copy_reads_the_locale_from_pg_database():
    cur = FakeCursor(("UTF8", "c", "en_NZ.UTF-8", "en_NZ.UTF-8", None, None))
    assert C.database_locale(cur) == NZ
    assert "pg_database" in cur.sql[0] and "current_database()" in cur.sql[0]
    icu = C.database_locale(FakeCursor(("UTF8", "i", "en_NZ.UTF-8", "en_NZ.UTF-8", "en-NZ", None)))
    assert icu["provider"] == "icu" and icu["locale"] == "en-NZ"


def test_initdb_and_create_database_carry_the_manifest_collation(tmp_path):
    man = {"databases": {"querynz_v4": {"stamp": "S", "schema": "x", "locale": NZ}}}
    loc = R.database_locales(man, ["querynz_v4"], live=no_live)["querynz_v4"]
    assert loc == {**NZ, "from": "manifest"}

    run = FakeRunner()
    R.start_server(str(tmp_path), loc, run=run)
    argv = run.initdb()
    assert {"--locale-provider=libc", "--lc-collate=en_NZ.UTF-8", "--lc-ctype=en_NZ.UTF-8"} <= set(argv)
    assert argv[argv.index("-E") + 1] == "UTF8"
    assert not any("C.UTF-8" in a for a in argv)

    executed = []
    R.create_database(str(tmp_path), "querynz_v4", loc, connect=lambda *a, **kw: FakeConnection(executed))
    create = executed[-1]
    assert create.startswith('CREATE DATABASE "querynz_v4" TEMPLATE template0 ')
    for part in ("ENCODING 'UTF8'", "LOCALE_PROVIDER libc", "LC_COLLATE 'en_NZ.UTF-8'", "LC_CTYPE 'en_NZ.UTF-8'"):
        assert part in create


def test_icu_and_builtin_name_their_own_locale():
    icu = {**NZ, "provider": "icu", "locale": "en-NZ", "icu_rules": "&a<b"}
    assert R.create_database_sql("d", icu).endswith("ICU_LOCALE 'en-NZ' ICU_RULES '&a<b'")
    assert {"--icu-locale=en-NZ", "--icu-rules=&a<b"} <= set(R.initdb_locale_args(icu))
    built = {**NZ, "provider": "builtin", "collate": "C", "ctype": "C", "locale": "C.UTF-8"}
    assert R.create_database_sql("d", built).endswith("BUILTIN_LOCALE 'C.UTF-8'")
    assert "--builtin-locale=C.UTF-8" in R.initdb_locale_args(built)


def test_a_manifest_without_the_locale_falls_back_to_the_live_server_and_records_it(tmp_path, monkeypatch):
    stamp, spool = "20261021T210010", tmp_path / "spool"
    man = {"stamp": stamp, "kind": "nightly", "pieces": {}, "trees": {},
           "databases": {"querynz_v4": {"stamp": stamp, "schema": "querynz_v4--_schema.dump.gpg"}}}
    (spool / "objects" / stamp).mkdir(parents=True)
    C.write_json(str(spool / "manifest.json"), {"stamp": stamp})
    out = C.Sealed(str(spool / "objects" / stamp / "manifest.json.gpg"), "test-pass")
    out.write(json.dumps(man).encode())
    out.close()

    record = tmp_path / "offsite-restore-last.json"
    monkeypatch.setattr(R, "RECORD", str(record))
    monkeypatch.setattr(R, "read_env", lambda path: {"OFFSITE_PASSPHRASE": "test-pass"})
    given = {}

    def restore_database(database, man, src, passphrase, root, jobs, locale, log):
        given[database] = locale
        return {"tables": 0, "equal": 0, "locale": locale}
    monkeypatch.setattr(R, "restore_database", restore_database)
    asked, run = [], FakeRunner()

    def live(database):
        asked.append(database)
        return NZ

    rec = R.rehearse("local", root=str(tmp_path / "restore"), spool=str(spool), log=lambda *a: None,
                     live=live, run=run)
    assert asked == ["querynz_v4"]
    assert given["querynz_v4"] == {**NZ, "from": "live server"}
    assert "--lc-collate=en_NZ.UTF-8" in run.initdb()
    back = C.load_json(str(record))
    assert back["server_locale"]["from"] == "live server"
    assert back["databases"]["querynz_v4"]["locale"] == {**NZ, "from": "live server"}
    assert rec["equal"] is True
    assert ["systemctl", "--user", "stop", R.UNIT] in run.calls      # the fake's, never the real unit
