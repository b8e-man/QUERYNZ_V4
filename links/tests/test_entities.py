"""Ruling 123: `pub.entities`, one row per entity, a group or a row in no
group, named by the one ordering every reader shares (links/pane.md). The
build on the real engine is a slow test (a scratch schema of the sample
database, rolled back)."""
import inspect
import os
import re

import pytest

import links
from links import build, build_all, check

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLUMNS = ("entity_id", "kind", "display_name", "rows", "registers", "contested", "politician", "built_at")


def test_the_sql_defines_the_entities_table_with_its_columns():
    sql = links.tables_sql()
    assert re.search(r"CREATE TABLE IF NOT EXISTS links\.entities\b", sql)
    body = sql.split("CREATE TABLE IF NOT EXISTS links.entities")[1].split(");")[0]
    for col in COLUMNS:
        assert re.search(rf"^\s+{col}\s", body, re.M), col
    assert "CHECK (kind IN ('person', 'organisation', 'estate'))" in body
    assert "entity_id    text PRIMARY KEY" in body


def test_the_view_is_published_with_every_column_of_the_ruling():
    sql = links.publish_sql()
    assert "CREATE OR REPLACE VIEW pub.entities AS" in sql
    select = sql.split("CREATE OR REPLACE VIEW pub.entities AS")[1].split(";")[0]
    for col in COLUMNS:
        assert re.search(rf"\b{col}\b", select), col
    assert "FROM links.entities" in select
    ddl = links.publish_ddl("scratch_x", "scratch_x_pub")
    assert "CREATE OR REPLACE VIEW scratch_x_pub.entities AS" in ddl and "FROM scratch_x.entities" in ddl


def test_the_spec_and_the_pane_name_the_view_and_its_ordering():
    with open(os.path.join(HERE, "spec.md"), encoding="utf-8") as f:
        spec = f.read()
    publishes = [l for l in spec.splitlines() if l.startswith("publishes:")][0]
    assert "`pub.entities`" in publishes and "ruling 123" in publishes
    owns = [l for l in spec.splitlines() if l.startswith("owns:")][0]
    assert "`entities`" in owns
    assert "entities" in [l for l in spec.splitlines() if l.startswith("jobs:")][0]
    with open(os.path.join(HERE, "pane.md"), encoding="utf-8") as f:
        pane = f.read()
    assert "`pub.entities`" in pane
    for col in COLUMNS:
        assert f"`{col}`" in pane, col
    assert "the most words" in pane and "the most characters" in pane and 'COLLATE "C"' in pane


def test_the_build_makes_the_entities_after_the_groups_in_the_job_and_the_module():
    for fn in (build_all.run, build.build_all):
        src = inspect.getsource(fn)
        assert src.index("build_groups(") < src.index("build_entities("), fn.__name__
    src = inspect.getsource(build.build_entities)
    assert "DELETE FROM {s}.entities" in src and "DISTINCT ON (entity_id)" in src
    assert "array_length(string_to_array(name, ' '), 1) DESC NULLS LAST, length(name) DESC" in src   # the most words, then the most characters
    assert "ref {links.ORDER}" in src                                                              # then the smallest ref, bytes
    assert "array_agg(DISTINCT register ORDER BY register)" in src                                 # the registers sorted


class _Conn:
    """A connection that answers each count from a script keyed by a phrase of the query."""

    def __init__(self, answers: dict):
        self.answers = answers

    def execute(self, sql, params=None):
        for phrase, value in self.answers.items():
            if phrase in sql:
                return _Res(value)
        raise AssertionError(sql)


class _Res:
    def __init__(self, v):
        self.v = v

    def fetchone(self):
        return self.v


def test_the_check_counts_the_published_entities_against_the_groups_and_the_lone_rows():
    conn = _Conn({"information_schema.views": (1,), "FROM pub.entities": (7,), "FROM links.entities": (7,),
                  "FROM pub.links": (1,), "FROM links.links": (1,), "FROM pub.groups": (2,), "FROM links.groups": (2,),
                  "FROM pub.decisions": (0,), "FROM links.decisions": (0,)})
    published = check.check_published(conn, "links")
    assert [r["check"] for r in published][-1] == "pub.entities answers with the table's count" and all(r["ok"] for r in published)
    good = (7, 3, 4, 0, 0, 0, 10, 6, 0, 0)       # 7 entities = 3 groups + 4 lone rows; 10 rows = 6 grouped + 4 lone
    out = check.check_entities(_Conn({"information_schema.views": (1,), "WITH g AS": good}), "links")
    assert out[0]["ok"] and out[0]["entities"] == 7 and out[0]["rows_grouped_plus_lone"] == 10
    for bad in ((8, 3, 4, 0, 0, 1, 10, 6, 0, 0), (7, 3, 4, 1, 0, 0, 10, 6, 0, 0), (7, 3, 4, 0, 0, 0, 11, 6, 0, 0),
                (7, 3, 4, 0, 0, 0, 10, 6, 1, 0), (7, 3, 4, 0, 0, 0, 10, 6, 0, 1)):
        assert not check.check_entities(_Conn({"information_schema.views": (1,), "WITH g AS": bad}), "links")[0]["ok"], bad
    assert check.check_entities(_Conn({"information_schema.views": None}), "links")[0] == {
        "check": "pub.entities is the groups plus the lone rows", "ok": False, "note": "view missing"}
    assert "check_entities(conn, s, pub)" in inspect.getsource(check.run)


class _NoCommit:
    """The real connection, held in one transaction the test rolls back."""

    def __init__(self, conn):
        self.conn = conn

    def commit(self):
        pass

    def __getattr__(self, name):
        return getattr(self.conn, name)


@pytest.mark.slow
def test_the_entities_are_the_groups_and_the_lone_rows_named_by_the_shared_ordering():
    """On the real engine: a group takes the fullest filed name (the most
    words, then the most characters), a tie takes the smallest ref by bytes
    (where the database's own collation would pick the other), a lone row is
    a single-row entity, a group of bodies alone is an organisation named
    from the bodies, a contradicted group is contested, the registers are
    sorted, and the published view answers with the table."""
    import support.db as db
    from links import rules
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    s = "scratch_links_entities_test"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        conn = _NoCommit(raw)
        try:
            conn.execute(f"CREATE SCHEMA {s}")
            conn.execute(f"CREATE SCHEMA {s}_pub")
            conn.execute(links.ddl(s))
            conn.execute(links.publish_ddl(s, f"{s}_pub"))
            rows = [    # ref, register, view, key, kind, name_filed, politician
                ("companies:c/1", "companies", "directors", "c/1", "person", "J Smith", False),
                ("companies:c/2", "companies", "directors", "c/2", "person", "John   Smith ", False),   # whitespace folds
                ("house:m/1", "house", "members", "m/1", "person", "John Andrew Smith", True),
                ("x:B", "x", "v", "B", "person", "Ann Lee", False),       # bytes: 'x:B' < 'x:a'; en_NZ says the other way round
                ("x:a", "x", "v", "a", "person", "Ann Lee", False),
                ("gazette:lone/1", "gazette", "v", "lone/1", "estate", "Estate of Kim Roe", False),
                ("societies:s/1", "societies", "officers", "s/1", "person", "Pat Doe", False),
                ("societies:s/2", "societies", "officers", "s/2", "person", "Pat Doe", False),
                ("societies:s/3", "societies", "officers", "s/3", "person", "Pat Doe", False),
            ]
            for ref, reg, view, key, kind, name, pol in rows:
                conn.execute(f"""INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, name_key, politician)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (ref, reg, view, key, kind, name, name.lower(), pol))
            conn.execute(f"""INSERT INTO {s}.bodies (entity_ref, org_key, register, name, body) VALUES
                             ('companies:companies/9', 'sanford', 'companies', 'SANFORD LIMITED', 'companies:companies/9')""")
            for a, b, rule in (("companies:c/1", "companies:c/2", rules.RULE_FULL), ("companies:c/2", "house:m/1", rules.RULE_FULL),
                               ("x:B", "x:a", rules.RULE_FULL), ("companies:companies/9", "gazette:liq/9", rules.RULE_NUMBER),
                               ("societies:s/1", "societies:s/2", rules.RULE_FULL), ("societies:s/2", "societies:s/3", rules.RULE_FULL)):
                a, b = links.pair(a, b)
                conn.execute(f"INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade) VALUES (%s, %s, %s, '{{}}', 'confirmed')", (a, b, rule))
            a, b = links.pair("societies:s/1", "societies:s/3")
            conn.execute(f"INSERT INTO {s}.decisions (row_a, row_b, verdict, made_by, made_on) VALUES (%s, %s, 'not the same', 'person:test', '{{}}')", (a, b))
            quiet = lambda *_: None
            build.build_groups(conn, s, log=quiet)
            out = build.build_entities(conn, s, log=quiet)
            assert out["entities"] == 5 and out["groups"] == 4 and out["lone_rows"] == 1 and out["rows"] == 11   # 9 named rows and the two bodies
            assert out["person"] == 3 and out["organisation"] == 1 and out["estate"] == 1 and out["contested"] == 1 and out["politician"] == 1
            e = {r[0]: r[1:] for r in conn.execute(f"""SELECT entity_id, kind, display_name, rows, registers, contested, politician
                                                        FROM {s}_pub.entities""").fetchall()}
            assert set(e) == {"companies:c/1", "x:B", "gazette:lone/1", "companies:companies/9", "societies:s/1"}
            assert e["companies:c/1"] == ("person", "John Andrew Smith", 3, ["companies", "house"], False, True)   # the most words
            assert e["x:B"] == ("person", "Ann Lee", 2, ["x"], False, False)
            assert e["gazette:lone/1"] == ("estate", "Estate of Kim Roe", 1, ["gazette"], False, False)            # a lone row
            assert e["companies:companies/9"] == ("organisation", "SANFORD LIMITED", 2, ["companies", "gazette"], False, False)
            assert e["societies:s/1"] == ("person", "Pat Doe", 3, ["societies"], True, False)                      # contradicted: contested
            # the tie: two rows filed "Ann Lee"; the name is taken from 'x:B', the smaller ref by bytes
            chosen = conn.execute(f"""SELECT ref FROM {s}.rows WHERE name_filed = 'Ann Lee' ORDER BY ref {links.ORDER} LIMIT 1""").fetchone()[0]
            assert chosen == "x:B"
            assert conn.execute(f"SELECT ref FROM {s}.rows WHERE name_filed = 'Ann Lee' ORDER BY ref LIMIT 1").fetchone()[0] == "x:a"
            # the most characters, among names of one word count: "John Smith" over "J Smith" (c/2's whitespace folded)
            conn.execute(f"DELETE FROM {s}.groups WHERE row_key = 'house:m/1'")
            build.build_entities(conn, s, log=quiet)
            assert conn.execute(f"SELECT display_name, rows FROM {s}.entities WHERE entity_id = 'companies:c/1'").fetchone() == ("John Smith", 2)
            # the check agrees with the build
            published = [r for r in check.check_published(conn, s, f"{s}_pub") if r["check"].endswith("entities answers with the table's count")]
            assert published and published[0]["ok"] and published[0]["view"] == 6
            ok = check.check_entities(conn, s, f"{s}_pub")[0]
            assert ok["ok"] and ok["entities"] == 6 and ok["groups"] == 4 and ok["lone_rows"] == 2, ok
            conn.execute(f"DELETE FROM {s}.entities WHERE entity_id = 'x:B'")
            assert not check.check_entities(conn, s, f"{s}_pub")[0]["ok"]
        finally:
            raw.rollback()
