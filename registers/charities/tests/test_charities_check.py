"""Where the lane's check looks. Run bare, as the board's module-checks run
it, it reads the lane's live tables in querynz_v4 with the read-only login;
`--schema` names a session's scratch proof in the sample with the owner's.
The connection is a stand-in: nothing is opened and nothing is read."""
from support import db
from registers.charities import check, load


class _Conn:
    """Answers every query with no row: to_regclass finds nothing, so main
    stops at its first look and says so."""

    def __init__(self, key, database, opened):
        self.key, self.database, self.queries = key, database, []
        opened.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, q, args=None):
        self.queries.append((q, args))
        return self

    def fetchone(self):
        return (None,)


def _run(monkeypatch, capsys, argv):
    opened = []
    monkeypatch.setattr(db, "connect", lambda key, database=None, **kw: _Conn(key, database, opened))
    rc = check.main(argv)
    return rc, opened, capsys.readouterr().out


def test_the_bare_run_reads_the_live_schema_with_the_reader(monkeypatch, capsys):
    rc, opened, out = _run(monkeypatch, capsys, [])
    assert [(c.key, c.database) for c in opened] == [(db.READ_KEY, "querynz_v4")]
    assert opened[0].queries[-1][1] == ("charities.read_pages",)
    assert "querynz_v4.charities" in out and rc == 1


def test_the_scratch_switch_reads_the_sample_with_the_owner(monkeypatch, capsys):
    rc, opened, out = _run(monkeypatch, capsys, ["--schema", load.SCRATCH, "--offline"])
    assert [(c.key, c.database) for c in opened] == [(db.READ_KEY, "querynz_v4"), (db.OWNER_KEY, "querynz_v4_sample")]
    assert opened[1].queries[-1][1] == (f"{load.SCRATCH}.read_pages",)
    assert f"querynz_v4_sample.{load.SCRATCH}" in out and rc == 1


def test_the_database_switch_still_names_the_database():
    assert check.target(load.SCRATCH, "querynz_v4_other") == (db.OWNER_KEY, "querynz_v4_other")
    assert check.target(load.SCHEMA, "querynz_v4") == (db.READ_KEY, "querynz_v4")
    assert check.target(load.SCHEMA) == (db.READ_KEY, "querynz_v4")


def test_no_check_names_the_private_twin():
    """The reader has no grant on charities_private by design; every table a
    check reads is in the lane's own schema or pub."""
    names = [load.table(load.SCHEMA, t) for t in ("read_pages", "read_set_aside", "codes", "officers")]
    names += [load.table(load.SCHEMA, t) for t in check.TABLE_OF.values()] + list(check.VIEWS)
    assert names and not any(n.startswith(load.PRIVATE) for n in names)
