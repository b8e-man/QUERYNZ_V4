"""The three tables, the three verdicts, the two settings; decisions are
only ever added to. The DDL applies to a scratch schema of the sample
database (slow)."""
import os
import re

import pytest

import links


def test_verdicts_grades_and_settings_are_the_designs():
    assert links.VERDICTS == ("same", "not the same", "contested")
    assert links.GRADES == ("confirmed", "near", "related")
    assert links.SETTINGS["chain"] == "follow" and links.SETTINGS["steps"] == "near"


def test_pair_is_ordered_and_never_self():
    assert links.pair("b:2", "a:1") == ("a:1", "b:2")
    with pytest.raises(ValueError):
        links.pair("a:1", "a:1")


def test_a_decision_says_who_made_it_and_on_what():
    assert links.check_decision("same", "review-agent@2", {"rule": "full-name@1"}) == []
    assert links.check_decision("maybe", "", {}) == [
        "verdict must be one of ('same', 'not the same', 'contested')",
        "made_by names who or what made it: review-agent@N, correction:ID, suppression:ID, old-estate:ID or person:NAME",
        "made_on carries the evidence"]
    assert links.check_decision("contested", "old-estate:verdict-991", {"watch": "two regions"}) == []


def test_the_sql_defines_the_three_tables_and_the_copied_old_decisions():
    sql = links.tables_sql()
    for t in ("links.links", "links.decisions", "links.groups", "links.old_decisions"):
        assert re.search(rf"CREATE TABLE IF NOT EXISTS {re.escape(t)}\b", sql), t
    assert "CHECK (grade IN ('confirmed', 'near', 'related'))" in sql
    assert "CHECK (verdict IN ('same', 'not the same', 'contested'))" in sql
    assert "BEFORE UPDATE OR DELETE ON links.decisions" in sql


@pytest.mark.slow
def test_the_sql_applies_and_decisions_cannot_be_changed():
    import support.db as db
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    import psycopg
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(links.tables_sql())
        conn.execute("INSERT INTO links.decisions (row_a, row_b, verdict, made_by, made_on) VALUES ('a:1','b:2','same','person:test','{}')")
        with pytest.raises(psycopg.errors.RaiseException):
            conn.execute("UPDATE links.decisions SET verdict='contested' WHERE row_a='a:1'")
        conn.rollback()


def test_every_column_added_after_a_table_first_shipped_has_its_alter_line():
    """CREATE TABLE IF NOT EXISTS leaves an existing table as it was (card
    the-links-tables-do-not-migrate-an-existing-column)."""
    sql = links.tables_sql()
    for table, cols in (("old_decisions", ("source", "verdict", "mapped_how")), ("rows", ("part_of",)), ("links", ("relation",)),
                        ("readings", ("run_id", "pair_id", "kind", "truth", "band", "screen", "evidence", "citations", "model", "seconds"))):
        for col in cols:
            # added only where missing (24 November 2026: the unguarded form locked the table on every run)
            assert f"attname = '{col}' AND NOT attisdropped) THEN ALTER TABLE links.{table} ADD COLUMN {col} " in sql, (table, col)


class _NoCommit:
    """The real connection, held in one transaction the test rolls back: nothing it makes outlives it."""

    def __init__(self, conn):
        self.conn = conn

    def commit(self):
        pass

    def __getattr__(self, name):
        return getattr(self.conn, name)


@pytest.mark.slow
def test_the_groups_never_join_two_companies_through_a_relation():
    """Ruling 106 (2): a `successor-name@1` link is related, not an identity.
    On the real engine (a schema of the sample database, rolled back): a
    table made before the third grade takes it, a related link must name its
    relation, and two companies related by succession stay out of one group
    while the confirmed link between their two directors joins; so do two
    companies related as refiled (ruling 109)."""
    import support.db as db
    from links import build, rules
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    import psycopg
    s = "scratch_links_relation_test"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        conn = _NoCommit(raw)
        try:
            conn.execute(f"CREATE SCHEMA {s}")
            two_grades = (links.ddl(s).split(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = '{s}.links'::regclass AND attname = 'relation'")[0]
                          .replace("CONSTRAINT links_grade_check CHECK (grade IN ('confirmed', 'near', 'related'))", "CHECK (grade IN ('confirmed', 'near'))")
                          .replace("    relation     text,", "")
                          .replace("    CONSTRAINT links_relation_graded CHECK ((grade = 'related') = (relation IS NOT NULL)),", ""))
            assert "'related'" not in two_grades
            conn.execute(two_grades)
            conn.execute(links.ddl(s))               # the migration
            assert "'related'" in conn.execute(f"""SELECT pg_get_constraintdef(oid) FROM pg_constraint
                                                  WHERE conrelid = '{s}.links'::regclass AND conname = 'links_grade_check'""").fetchone()[0]
            conn.execute(f"""INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade, reason, relation) VALUES
                ('companies:companies/1', 'companies:companies/2', %s, '{{}}', 'related', NULL, 'succeeded by'),
                ('companies:companies/1/director/a', 'companies:companies/2/director/b', %s, '{{}}', 'confirmed', NULL, NULL),
                ('companies:companies/3', 'companies:companies/4', %s, '{{}}', 'related', NULL, %s),
                ('companies:companies/3/director/c', 'companies:companies/4/director/d', %s, '{{}}', 'confirmed', NULL, NULL)""",
                         (rules.RULE_SUCCESSOR, rules.RULE_FULL, rules.RULE_REFILED, rules.RELATION_REFILED, rules.RULE_FULL))
            with pytest.raises(psycopg.errors.CheckViolation):
                with raw.transaction():
                    conn.execute(f"INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade) VALUES ('x:1', 'x:2', %s, '{{}}', 'related')",
                                 (rules.RULE_SUCCESSOR,))
            build.build_groups(conn, s, log=lambda *_: None)
            g = dict(conn.execute(f"SELECT row_key, group_id FROM {s}.groups").fetchall())
            assert g["companies:companies/1/director/a"] == g["companies:companies/2/director/b"]
            assert "companies:companies/1" not in g and "companies:companies/2" not in g
            assert g["companies:companies/3/director/c"] == g["companies:companies/4/director/d"]
            assert "companies:companies/3" not in g and "companies:companies/4" not in g
        finally:
            raw.rollback()


def test_a_refill_writes_only_the_rows_that_changed():
    """24 November 2026: a refill wiped and rewrote its register's rows each time (541 million inserts into 17 million
    rows in 17 days). On the real engine (a schema of the sample database, rolled back): a row read the same stays
    where it is, a changed one is replaced, a vanished one goes, a new one comes, another register is untouched, and a
    whole refill drops a register gone from the sources."""
    import support.db as db
    from links import rows
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    s = "scratch_links_merge_test"
    cols = ", ".join(rows.ROW_COLUMNS)

    def row(ref, name):
        reg, key = ref.split(":", 1)
        return (ref, reg, "v", key, "person", name, None, None, None, name.lower(), None, None, False, None, None, None,
                None, None, False, None, None, False)

    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        conn = _NoCommit(raw)
        try:
            conn.execute(f"CREATE SCHEMA {s}")
            conn.execute(links.ddl(s))
            with conn.cursor() as w:
                with w.copy(f"COPY {s}.rows ({cols}) FROM STDIN") as cp:
                    for r in (row("a:1", "Same"), row("a:2", "Old"), row("a:3", "Gone"), row("b:1", "Other"), row("z:1", "Retired")):
                        cp.write_row(r)
            where = dict(conn.execute(f"SELECT ref, ctid::text FROM {s}.rows").fetchall())
            rows.stage_rows(conn, s)
            with conn.cursor() as w:
                with w.copy(f"COPY rows_new ({cols}) FROM STDIN") as cp:
                    for r in (row("a:1", "Same"), row("a:2", "New"), row("a:4", "Fresh")):
                        cp.write_row(r)
            assert rows.merge_rows(conn, s, {"a"}) == {"kept": 1, "deleted": 2, "inserted": 2}
            now = dict(conn.execute(f"SELECT ref, ctid::text FROM {s}.rows").fetchall())
            assert now["a:1"] == where["a:1"] and now["b:1"] == where["b:1"]          # not rewritten
            assert sorted(now) == ["a:1", "a:2", "a:4", "b:1", "z:1"]
            assert conn.execute(f"SELECT name_filed FROM {s}.rows WHERE ref = 'a:2'").fetchone()[0] == "New"
            rows.stage_rows(conn, s)
            with conn.cursor() as w:
                with w.copy(f"COPY rows_new ({cols}) FROM STDIN") as cp:
                    cp.write_row(row("a:1", "Same"))
            got = rows.merge_rows(conn, s, {"a", "b"}, stale_beyond={"a", "b"})
            assert got == {"kept": 1, "deleted": 4, "inserted": 0}
            assert [r[0] for r in conn.execute(f"SELECT ref FROM {s}.rows")] == ["a:1"]
        finally:
            raw.rollback()


def test_two_people_sitting_together_on_two_bodies_are_joined_and_a_different_middle_name_is_not():
    """shared-associate@1 (Arthur, 25 November 2026), on the real engine (a schema of the sample database, rolled back):
    Jane Smith and Tom Brown sit on Acme and on a trust; the two Jane Smith rows and the two Tom Brown rows are joined.
    A Jane Ann Smith beside Tom Brown on a third body with no middle-name agreement to "Jane Mary" is not; a pair on
    one body only is not; a body naming more than ASSOCIATE_BODY_PEOPLE people does not count."""
    import support.db as db
    from links import build, rules
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    s = "scratch_links_associate_test"
    rows = [  # ref, view, filed, given, middle, family, entity
        ("companies:d1", "directors", "Jane Mary SMITH", "jane", "Mary", "smith", "companies:acme"),
        ("companies:d2", "directors", "Tom BROWN", "tom", None, "brown", "companies:acme"),
        ("charities:o1", "charity_officers", "Jane Smith", "jane", None, "smith", "charities:trust"),
        ("charities:o2", "charity_officers", "Tom Brown", "tom", None, "brown", "charities:trust"),
        ("societies:o3", "society_officers", "Jane Ann SMITH", "jane", "Ann", "smith", "societies:club"),
        ("societies:o4", "society_officers", "Tom BROWN", "tom", None, "brown", "societies:club"),
        ("companies:d5", "directors", "Ann LEE", "ann", None, "lee", "companies:acme"),
        ("companies:d6", "directors", "Ann LEE", "ann", None, "lee", "companies:other"),
    ] + [(f"companies:big{i}", "directors", f"Person{i} X", f"person{i}", None, "x", "companies:big") for i in range(rules.ASSOCIATE_BODY_PEOPLE)] \
      + [("companies:big-jane", "directors", "Jane SMITH", "jane", None, "smith", "companies:big"),
         ("companies:big-tom", "directors", "Tom BROWN", "tom", None, "brown", "companies:big")]
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        conn = _NoCommit(raw)
        try:
            conn.execute(f"CREATE SCHEMA {s}")
            conn.execute(links.ddl(s))
            for ref, view, filed, g, mid, fam, ent in rows:
                full = " ".join(w for w in (g, (mid or "").lower(), fam) if w)
                conn.execute(f"""INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, given, middle, family, name_key,
                                   fl_key, full_key, has_middle, entity_ref)
                                 VALUES (%s, %s, %s, %s, 'person', %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                             (ref, ref.split(":")[0], view, ref, filed, g, mid, fam, full, f"{g} {fam}", full, bool(mid), ent))
            n = build.associate_links(conn, s)
            got = {(a, b) for a, b in conn.execute(f"SELECT row_a, row_b FROM {s}.links WHERE rule = %s",
                                                   (rules.RULE_SHARED_ASSOCIATE,)).fetchall()}
            assert ("charities:o1", "companies:d1") in got and ("charities:o2", "companies:d2") in got
            assert ("charities:o2", "societies:o4") in got or ("companies:d2", "societies:o4") in got
            assert not any("societies:o3" in p for p in got if "companies:d1" in p)      # Mary and Ann differ
            assert not any("companies:big" in x for p in got for x in p)                 # the big body does not count
            assert not any("companies:d5" in p or "companies:d6" in p for p in got)      # Ann Lee shares Acme with Jane, not a second body
            assert n == len(got)
        finally:
            raw.rollback()
