"""Whitespace-hygiene gate (Muster 1 B4, T7.10 straggler class): an entity name
carrying an embedded newline/tab or untrimmed edges is normalised to its
whitespace-collapsed form through the audited rename gate — reversible, old
surface kept findable, deterministic, dry-run first. Skips on the read-only
standby, runs on the primary (like every gate test)."""
from testkit import fresh_graph, graph  # noqa: F401

from healer import hygiene


def _dirty(g, name, etype="organisation"):
    return g.execute(
        "INSERT INTO entities (name, type) VALUES (%s,%s) RETURNING id",
        (name, etype)).fetchone()["id"]


def test_clean_name_collapses_all_whitespace():
    assert hygiene.clean_name("St.\nJames' Gazette") == "St. James' Gazette"
    assert hygiene.clean_name("  trailing \t edges  ") == "trailing edges"
    assert hygiene.clean_name("already clean") == "already clean"


def test_dry_run_writes_nothing(graph):
    eid = _dirty(graph, "St.\nJames' Gazette")
    graph.commit()
    stats = hygiene.heal_whitespace_names(graph, apply=False)
    assert stats["dirty"] >= 1 and stats["renamed"] == 0
    name = graph.execute("SELECT name FROM entities WHERE id=%s", (eid,)).fetchone()["name"]
    assert "\n" in name                                   # untouched on a dry run


def test_apply_normalises_audits_and_keeps_alias(graph):
    from claim_graph.normalise import norm_form
    eid = _dirty(graph, "St.\nJames' Gazette")
    edge = _dirty(graph, "  Men s S. \nB  ")
    graph.commit()
    stats = hygiene.heal_whitespace_names(graph, apply=True)
    assert stats["renamed"] == 2

    # names normalised
    assert graph.execute("SELECT name FROM entities WHERE id=%s", (eid,)).fetchone()["name"] \
        == "St. James' Gazette"
    assert graph.execute("SELECT name FROM entities WHERE id=%s", (edge,)).fetchone()["name"] \
        == "Men s S. B"

    # audited (reversible) — entity_renames carries old + new
    ren = graph.execute(
        "SELECT old_name, new_name FROM entity_renames WHERE entity_id=%s", (eid,)).fetchone()
    assert "\n" in ren["old_name"] and ren["new_name"] == "St. James' Gazette"

    # old surface stays findable (alias on the normalised old form)
    hit = graph.execute("""
        SELECT 1 FROM alias a JOIN alias_link l ON l.alias_id=a.id
        WHERE l.entity_id=%s AND a.normalised=%s""",
        (eid, norm_form("St.\nJames' Gazette"))).fetchone()
    assert hit is not None

    # idempotent — nothing dirty remains
    again = hygiene.heal_whitespace_names(graph, apply=True)
    assert again["dirty"] == 0 and again["renamed"] == 0
