"""The three tables, the three verdicts, the two settings; decisions are
only ever added to. The DDL applies to a scratch schema of the sample
database (slow)."""
import os
import re

import pytest

import links


def test_verdicts_grades_and_settings_are_the_designs():
    assert links.VERDICTS == ("same", "not the same", "contested")
    assert links.GRADES == ("confirmed", "near")
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
    assert "CHECK (grade IN ('confirmed', 'near'))" in sql
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
    for table, cols in (("old_decisions", ("source", "verdict", "mapped_how")),
                        ("readings", ("run_id", "pair_id", "kind", "truth", "band", "screen", "evidence", "citations", "model", "seconds"))):
        for col in cols:
            assert f"ALTER TABLE links.{table} ADD COLUMN IF NOT EXISTS {col} " in sql, (table, col)
