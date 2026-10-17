"""Repair-lane gate: completions are verbatim-evidenced or nothing;
merge-preferred under the register rule; renames audited and the old
surface stays findable."""
from testkit import fresh_graph, graph, seed_entity  # noqa: F401

from healer import mint_lane, repair
from reviewer import corroborate


def _flag(g, eid, name, etype="organisation"):
    g.execute("""
        INSERT INTO mint_review (entity_id, name, type, pattern, status)
        VALUES (%s,%s,%s,'trailing-particle','flagged-truncated')""",
        (eid, name, etype))
    g.commit()


def _texts(monkeypatch, texts):
    monkeypatch.setattr(repair, "_article_texts", lambda g, b, eid, cap=12: texts)
    monkeypatch.setattr(repair, "_backlog", lambda: object())
    monkeypatch.setattr(corroborate, "register_conn", lambda: None)


def test_rename_needs_two_articles(graph, tmp_path, monkeypatch):
    mint_lane.ensure_schema(graph)
    monkeypatch.setattr(mint_lane, "VERDICTS_PATH", str(tmp_path / "v.jsonl"))
    monkeypatch.setattr(repair, "VERDICTS_PATH", str(tmp_path / "v.jsonl"))
    eid = seed_entity(graph, "Greater Wellington Te", "organisation")
    graph.commit()
    _flag(graph, eid, "Greater Wellington Te")
    # one article only -> no action (register down, no register hit possible)
    _texts(monkeypatch, ["Greater Wellington Te Pane Matua Taiao met today."])
    stats = repair.run(graph)
    assert stats == {"merged": 0, "renamed": 0, "no_evidence": 1, "abstained": 0,
                     "requeued": 0}
    # re-flag; two independent articles -> rename through the gate
    graph.execute("UPDATE mint_review SET status='flagged-truncated' "
                  "WHERE entity_id=%s", (eid,))
    graph.commit()
    _texts(monkeypatch, ["Greater Wellington Te Pane Matua Taiao met today.",
                         "A Greater Wellington Te Pane Matua Taiao spokesperson said."])
    stats = repair.run(graph)
    assert stats["renamed"] == 1
    e = graph.execute("SELECT name FROM entities WHERE id=%s", (eid,)).fetchone()
    assert e["name"] == "Greater Wellington Te Pane Matua Taiao"
    a = graph.execute("""
        SELECT old_name, new_name FROM entity_renames WHERE entity_id=%s""",
        (eid,)).fetchone()
    assert a["old_name"] == "Greater Wellington Te"
    alias = graph.execute("""
        SELECT 1 FROM alias a JOIN alias_link l ON l.alias_id=a.id
        WHERE l.entity_id=%s AND a.normalised='greater wellington te'""",
        (eid,)).fetchone()
    assert alias, "the truncated surface stays findable as an alias"


def test_merge_preferred_when_completed_entity_exists(graph, tmp_path, monkeypatch):
    mint_lane.ensure_schema(graph)
    monkeypatch.setattr(mint_lane, "VERDICTS_PATH", str(tmp_path / "v.jsonl"))
    monkeypatch.setattr(repair, "VERDICTS_PATH", str(tmp_path / "v.jsonl"))
    full = seed_entity(graph, "Te Rūnanga o Ngāi Tahu", "organisation")
    stub = seed_entity(graph, "Te Rūnanga o", "organisation")
    graph.commit()
    _flag(graph, stub, "Te Rūnanga o")
    _texts(monkeypatch, ["Te Rūnanga o Ngāi Tahu welcomed the ruling.",
                         "Leaders of Te Rūnanga o Ngāi Tahu spoke."])
    # register down = strictest: without a corroborator the merge ABSTAINS
    stats = repair.run(graph)
    assert stats["abstained"] == 1 and stats["merged"] == 0
    # a shared article corroborates; re-flag and rerun -> merge
    graph.execute("""
        INSERT INTO mentions (article_id, entity_id, salience, n_mentions, first_char)
        SELECT a, e, 'passing', 1, 0 FROM (VALUES (gen_random_uuid())) v(a),
             unnest(ARRAY[%s::bigint, %s::bigint]) e""", (full, stub))
    graph.execute("UPDATE mint_review SET status='flagged-truncated' "
                  "WHERE entity_id=%s", (stub,))
    graph.commit()
    stats = repair.run(graph)
    assert stats["merged"] == 1 and stats["renamed"] == 0
    survivor = graph.execute("SELECT name FROM entities WHERE id=%s",
                             (full,)).fetchone()
    assert survivor["name"] == "Te Rūnanga o Ngāi Tahu"
