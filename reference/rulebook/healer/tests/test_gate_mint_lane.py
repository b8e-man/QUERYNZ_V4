"""Post-mint healing lane gate: screen queues the right fresh mints,
verdicts execute REVERSIBLY under the calibration band, and the
register allowlist never even queues (the only path to a wrong
condemnation is closed at the screen)."""
import json

from testkit import fresh_graph, graph, seed_entity  # noqa: F401

from healer import mint_lane
from reviewer import fragments


def _mock_judge(monkeypatch, verdict, confidence=0.95):
    def fake(system, user, timeout=300.0, schema=None):
        return {"verdict": verdict, "confidence": confidence,
                "reasoning": "structural.", "model_reasoning": "…"}
    monkeypatch.setattr(fragments.model, "judge", fake)


def _lane_verdicts_to(monkeypatch, tmp_path):
    monkeypatch.setattr(mint_lane, "VERDICTS_PATH",
                        str(tmp_path / "mint_lane_verdicts.jsonl"))


def test_screen_queues_suspects_not_allowlist(graph, monkeypatch):
    mint_lane.ensure_schema(graph)
    seed_entity(graph, "Aoake Te", "person")
    seed_entity(graph, "Fonterra Co-operative Group", "organisation")
    seed_entity(graph, "Mandy Te", "person")     # register-allowlisted shape
    graph.commit()
    monkeypatch.setattr(mint_lane, "_register_allow", lambda: {"mandy te"})
    stats = mint_lane.screen(graph)
    assert stats["trailing-particle"] == 1, stats
    rows = graph.execute("SELECT name FROM mint_review").fetchall()
    names = {r["name"] for r in rows}
    assert names == {"Aoake Te"}, "allowlisted and clean names never queue"


def test_debris_verdict_quarantines_reversibly(graph, tmp_path, monkeypatch):
    mint_lane.ensure_schema(graph)
    eid = seed_entity(graph, "wāhine toa kaupapa", "organisation")
    graph.commit()
    monkeypatch.setattr(mint_lane, "_register_allow", lambda: set())
    _lane_verdicts_to(monkeypatch, tmp_path)
    _mock_judge(monkeypatch, "debris", 0.95)
    mint_lane.screen(graph)
    assert mint_lane.judge(graph) == 1
    stats = mint_lane.execute(graph)
    assert stats["quarantined"] == 1
    e = graph.execute("SELECT quarantined_at FROM entities WHERE id=%s",
                      (eid,)).fetchone()
    assert e["quarantined_at"] is not None
    q = graph.execute("SELECT reason, reverted_at FROM entity_quarantine "
                      "WHERE entity_id=%s", (eid,)).fetchone()
    assert q["reason"].startswith("mint-lane:") and q["reverted_at"] is None
    # the verdict mirrors to the Review tab's jsonl
    row = json.loads((tmp_path / "mint_lane_verdicts.jsonl").read_text()
                     .splitlines()[0])
    assert row["name"] == "wāhine toa kaupapa"
    assert row["tier"] == "mint-lane"
    # and the reversal is complete
    from claim_graph.remediate import unquarantine_entity
    unquarantine_entity(graph, eid)
    graph.commit()
    e = graph.execute("SELECT quarantined_at FROM entities WHERE id=%s",
                      (eid,)).fetchone()
    assert e["quarantined_at"] is None


def test_truncated_flags_never_quarantines(graph, tmp_path, monkeypatch):
    mint_lane.ensure_schema(graph)
    eid = seed_entity(graph, "Greater Wellington Te", "organisation")
    graph.commit()
    monkeypatch.setattr(mint_lane, "_register_allow", lambda: set())
    _lane_verdicts_to(monkeypatch, tmp_path)
    _mock_judge(monkeypatch, "truncated", 0.95)
    mint_lane.screen(graph)
    mint_lane.judge(graph)
    stats = mint_lane.execute(graph)
    assert stats["flagged_truncated"] == 1 and stats["quarantined"] == 0
    e = graph.execute("SELECT quarantined_at FROM entities WHERE id=%s",
                      (eid,)).fetchone()
    assert e["quarantined_at"] is None, "repaired, not deleted"


def test_low_confidence_parks_no_action(graph, tmp_path, monkeypatch):
    mint_lane.ensure_schema(graph)
    eid = seed_entity(graph, "kaimoana ki", "organisation")
    graph.commit()
    monkeypatch.setattr(mint_lane, "_register_allow", lambda: set())
    _lane_verdicts_to(monkeypatch, tmp_path)
    _mock_judge(monkeypatch, "debris", 0.6)       # below AUTO_BAND
    mint_lane.screen(graph)
    mint_lane.judge(graph)
    stats = mint_lane.execute(graph)
    assert stats["parked"] == 1 and stats["quarantined"] == 0
    e = graph.execute("SELECT quarantined_at FROM entities WHERE id=%s",
                      (eid,)).fetchone()
    assert e["quarantined_at"] is None, "below the band nothing executes"


def test_rescreen_is_idempotent(graph, monkeypatch):
    mint_lane.ensure_schema(graph)
    seed_entity(graph, "Aoake Te", "person")
    graph.commit()
    monkeypatch.setattr(mint_lane, "_register_allow", lambda: set())
    mint_lane.screen(graph)
    stats2 = mint_lane.screen(graph)   # overlap window re-reads; PK absorbs
    assert stats2["trailing-particle"] == 0
    n = graph.execute("SELECT count(*) c FROM mint_review").fetchone()["c"]
    assert n == 1
