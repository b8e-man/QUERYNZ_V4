"""B4 T3/T4 — the first queue (ruling 9) as gate tests on the fresh graph:
trailing-repeat doubles with the Māori-reduplication trap, Rt Hon twins,
conjunction persons (finder → tier-3 judge → SPLIT), and the claim-tier
re-subjecting rules (role-string subjects, surname-only subjects with a
same-document full-name co-mention). Written failing-first 2026-08-22."""
import json
import uuid

from testkit import fresh_graph, graph, seed_entity  # noqa: F401

from healer import crawler, mint_lane


def _mention(g, eid, article, form, n=1):
    g.execute("""INSERT INTO mentions (article_id, entity_id, salience, surface_form, n_mentions)
                 VALUES (%s, %s, 'participant', %s, %s)""", (article, eid, form, n))


def _claim(g, subj, obj, predicate, doc, evidence="evidence."):
    return g.execute("""
        INSERT INTO claims (class, predicate, subject_entity_id, object_entity_id, evidence_text,
                            document_id, extraction_method, extractor_version)
        VALUES ('ROLE', %s, %s, %s, %s, %s, 'test', 't1') RETURNING id""",
        (predicate, subj, obj, evidence, doc)).fetchone()["id"]


# ── trailing-repeat doubles ───────────────────────────────────────────────

def test_trailing_repeat_heals_but_refuses_maori_reduplication(graph):
    mint_lane.ensure_schema(graph)
    base = seed_entity(graph, "Justin Allen", "person")
    dbl = seed_entity(graph, "Justin Allen Allen", "person")          # fold into base
    lone = seed_entity(graph, "Pocket Whist Whist", "person")         # rename (no twin)
    trap = seed_entity(graph, "Georgina Te Heu Heu", "person")        # Māori reduplication: left
    two = seed_entity(graph, "Pago Pago", "place")                    # 2 tokens: not the shape
    graph.commit()
    n = crawler.heal_trailing_repeat(graph)
    assert n == 2
    assert graph.execute("SELECT kept_id FROM entity_merges WHERE merged_id=%s", (dbl,)).fetchone()["kept_id"] == base
    got = {r["id"]: r["name"] for r in graph.execute(
        "SELECT id, name FROM entities WHERE id = ANY(%s)", ([lone, trap, two],)).fetchall()}
    assert got[lone] == "Pocket Whist"
    assert got[trap] == "Georgina Te Heu Heu" and got[two] == "Pago Pago"
    assert crawler.heal_trailing_repeat(graph) == 0, "idempotent"
    assert crawler.TRAILING_REPEAT_REFUSED[-1] >= 1, "trap refusals are counted, not silent"


def test_maori_spellable():
    assert crawler._maori_spellable("Heu") and crawler._maori_spellable("Paki") and crawler._maori_spellable("Kiri")
    assert not crawler._maori_spellable("Allen") and not crawler._maori_spellable("Whist")
    assert crawler._maori_spellable("Whanganui") and not crawler._maori_spellable("George")


def test_role_string_entities_are_retyped_to_position(graph):
    mint_lane.ensure_schema(graph)
    nat = seed_entity(graph, "National MP", "organisation")
    lab = seed_entity(graph, "Labour MP", "person")
    real = seed_entity(graph, "Labour Party", "organisation")
    graph.commit()
    assert crawler.heal_role_string_entities(graph) == 2
    types = {r["id"]: r["type"] for r in graph.execute(
        "SELECT id, type FROM entities WHERE id = ANY(%s)", ([nat, lab, real],)).fetchall()}
    assert types == {nat: "position", lab: "position", real: "organisation"}
    chg = graph.execute("SELECT reason FROM entity_type_changes WHERE entity_id=%s", (nat,)).fetchone()
    assert chg and chg["reason"].startswith("crawler:role-string-position")
    assert crawler.heal_role_string_entities(graph) == 0, "idempotent"


# ── Rt Hon twins ──────────────────────────────────────────────────────────

def test_rt_hon_is_a_role_title(graph, monkeypatch):
    from reviewer import corroborate
    monkeypatch.setattr(corroborate, "register_conn", lambda: None)
    monkeypatch.setattr(corroborate, "register_namesakes", lambda reg, n: 1)
    mint_lane.ensure_schema(graph)
    bare = seed_entity(graph, "Winston Peters", "person")
    titled = seed_entity(graph, "Rt Hon Winston Peters", "person")
    hon = seed_entity(graph, "Hon Judith Collins", "person")
    graph.commit()
    assert crawler.heal_role_title_prefix(graph) == 2
    assert graph.execute("SELECT kept_id FROM entity_merges WHERE merged_id=%s", (titled,)).fetchone()["kept_id"] == bare
    assert graph.execute("SELECT name FROM entities WHERE id=%s", (hon,)).fetchone()["name"] == "Judith Collins"


# ── conjunction persons: finder → tier-3 judge → split ────────────────────

def test_conjunction_finder_queues_two_name_persons_only(graph):
    mint_lane.ensure_schema(graph)
    a = seed_entity(graph, "Jacinda Ardern and Grant Robertson", "person")
    b = seed_entity(graph, "Simon and Garfunkel", "person")            # single-token halves: skip
    c = seed_entity(graph, "Smith & Caughey", "organisation")          # not a person: skip
    graph.commit()
    assert crawler.find_conjunctions(graph) == 1
    rows = graph.execute("SELECT entity_id, pattern FROM mint_review").fetchall()
    assert [(r["entity_id"], r["pattern"]) for r in rows] == [(a, "crawler-conjunction")]
    assert crawler.find_conjunctions(graph) == 0


def test_conjunction_judge_uses_the_tier3_re_read(graph, monkeypatch):
    mint_lane.ensure_schema(graph)
    a = seed_entity(graph, "Jacinda Ardern and Grant Robertson", "person")
    graph.commit()
    crawler.find_conjunctions(graph)
    seen = {}

    def fake_re_read(case, labels, **kw):
        seen.update(case=case, labels=labels)
        return ({"verdict": "two-people", "confidence": 0.95, "reasoning": "both named in every sentence"}, {})
    monkeypatch.setattr(crawler, "_re_read", fake_re_read)
    monkeypatch.setattr(crawler, "_mirror", lambda row: None)
    import types
    # a "sibling" that reads through the fixture's connection but whose
    # close() is a no-op — the worker closes its sibling in `finally`
    monkeypatch.setattr(crawler, "_worker_connect",
                        lambda g: types.SimpleNamespace(execute=g.execute, close=lambda: None,
                                                        rollback=lambda: None))
    assert crawler.judge(graph, limit=5, concurrency=1) == 1
    assert seen["case"]["entity_id"] == a and seen["labels"] == ["two-people", "one-person", "not-a-person"]
    row = graph.execute("SELECT status, verdict, confidence FROM mint_review WHERE entity_id=%s", (a,)).fetchone()
    assert row["status"] == "judged" and row["verdict"] == "two-people" and abs(row["confidence"] - 0.95) < 1e-6


def test_conjunction_execute_splits_and_freezes_the_set(graph, monkeypatch, tmp_path):
    mint_lane.ensure_schema(graph)
    a = seed_entity(graph, "Jacinda Ardern and Grant Robertson", "person")
    org = seed_entity(graph, "Labour Party", "organisation")
    art = str(uuid.uuid4())
    _mention(graph, a, art, "Ardern and Robertson", 2)
    cid = _claim(graph, a, org, "is member of", art)
    one = seed_entity(graph, "Tom and Jerry", "person")
    graph.execute("""INSERT INTO mint_review (entity_id, name, type, pattern, status, verdict, confidence)
                     VALUES (%s, %s, 'person', 'crawler-conjunction', 'judged', 'two-people', 0.97),
                            (%s, %s, 'person', 'crawler-conjunction', 'judged', 'one-person', 0.9)""",
                  (a, "Jacinda Ardern and Grant Robertson", one, "Tom and Jerry"))
    graph.commit()
    frozen = tmp_path / "set.json"
    monkeypatch.setenv("B4_CONJUNCTION_SET", str(frozen))
    stats = crawler.execute(graph)
    assert stats.get("split") == 1 and stats["cleared"] == 1
    parts = graph.execute("SELECT name FROM entities WHERE name IN ('Jacinda Ardern','Grant Robertson') ORDER BY name").fetchall()
    assert [p["name"] for p in parts] == ["Grant Robertson", "Jacinda Ardern"]
    assert graph.execute("SELECT quarantined_at FROM entities WHERE id=%s", (a,)).fetchone()["quarantined_at"] is not None
    assert graph.execute("SELECT count(*) FROM claims WHERE predicate='is member of'").fetchone()["count"] == 2
    assert graph.execute("SELECT status FROM mint_review WHERE entity_id=%s", (a,)).fetchone()["status"] == "split"
    frozen_rows = json.loads(frozen.read_text())
    assert [r["entity_id"] for r in frozen_rows] == [a] and frozen_rows[0]["verdict"] == "two-people"


def test_re_read_refuses_a_non_loopback_endpoint(monkeypatch):
    """The healer calls the local model only — pinned in the unit AND here."""
    import pytest
    called = []
    import research.crawler_judge as cj
    monkeypatch.setattr(cj, "re_read", lambda *a, **k: called.append(1))
    # audit A30 (Muster 2 B5): the check judges the RESOLVED endpoint the
    # research loop posts to (query.agent.API), not the raw env — the loop
    # has defaulted to loopback since 211d32e, so "unset" is allowed
    import query.agent as qa
    monkeypatch.setattr(qa, "API", "https://inference-api.example.com/v1/chat/completions")
    with pytest.raises(RuntimeError, match="local-only"):
        crawler._re_read({"entity_id": 1}, ["x"])
    assert not called
    monkeypatch.delenv("LLM_API_URL", raising=False)
    monkeypatch.setattr(qa, "API", "http://127.0.0.1:8020/v1/chat/completions")
    crawler._re_read({"entity_id": 1}, ["x"])
    assert called == [1]


# ── claim-tier re-subjecting (R7 / R8) ────────────────────────────────────

def test_resubject_rules_are_evidence_gated_and_ledgered(graph):
    from healer import resubject
    mint_lane.ensure_schema(graph)
    nat_mp = seed_entity(graph, "National MP", "organisation")
    fleming = seed_entity(graph, "Greg Fleming", "person")
    party = seed_entity(graph, "National Party", "organisation")
    doc1, doc2, doc3 = (str(uuid.uuid4()) for _ in range(3))
    c_role = _claim(graph, nat_mp, party, "is member of", doc1,
                    "National MP Greg Fleming initially refused to speak to Stuff.")
    c_none = _claim(graph, nat_mp, party, "is member of", doc2,
                    "A National MP said it was not a good look.")          # no person named: stays
    ardern = seed_entity(graph, "Ardern", "people")
    jacinda = seed_entity(graph, "Jacinda Ardern", "person")
    cabinet = seed_entity(graph, "Cabinet", "organisation")
    _mention(graph, jacinda, doc1, "Jacinda Ardern")                     # co-mention in doc1
    c_sur = _claim(graph, ardern, cabinet, "leads", doc1, "Ardern said Cabinet would continue.")
    c_sur_alone = _claim(graph, ardern, cabinet, "leads", doc3, "Ardern said so.")   # no co-mention: stays
    graph.commit()

    plan = resubject.run(graph, apply=False)
    assert plan == {"R7-role-string-subject": 1, "R8-surname-co-mention": 1}
    assert graph.execute("SELECT subject_entity_id FROM claims WHERE id=%s", (c_role,)).fetchone()["subject_entity_id"] == nat_mp
    done = resubject.run(graph, apply=True)
    graph.commit()
    assert done == plan
    subj = {r["id"]: r["subject_entity_id"] for r in graph.execute(
        "SELECT id, subject_entity_id FROM claims").fetchall()}
    assert subj[c_role] == fleming and subj[c_sur] == jacinda
    assert subj[c_none] == nat_mp and subj[c_sur_alone] == ardern
    heals = graph.execute("SELECT claim_id, rule, old_subject_entity_id, new_subject_entity_id FROM claim_heals ORDER BY claim_id").fetchall()
    assert {(h["claim_id"], h["rule"], h["old_subject_entity_id"], h["new_subject_entity_id"]) for h in heals} == {
        (c_role, "R7-role-string-subject", nat_mp, fleming), (c_sur, "R8-surname-co-mention", ardern, jacinda)}
    assert resubject.run(graph, apply=True) == {"R7-role-string-subject": 0, "R8-surname-co-mention": 0}


def test_judge_picks_the_capped_conjunction_queue_before_the_old_backlog(graph, monkeypatch):
    """Found live 2026-08-22: judge() took the 1,000 OLDEST queued rows,
    so the 38 conjunctions (screened last, capped at 40/cycle) sat behind
    4,793 older acronym/type-multiplicity rows and would never reach the
    re-read. The capped queue is judged first; the backlog fills the rest."""
    mint_lane.ensure_schema(graph)
    old = seed_entity(graph, "ACC", "organisation")
    new = seed_entity(graph, "Jacinda Ardern and Grant Robertson", "person")
    graph.execute("""INSERT INTO mint_review (entity_id, name, type, pattern, status, screened_at)
                     VALUES (%s, 'ACC', 'organisation', 'crawler-acronym-org', 'queued', now() - interval '2 days')""", (old,))
    graph.execute("""INSERT INTO mint_review (entity_id, name, type, pattern, status, screened_at)
                     VALUES (%s, 'Jacinda Ardern and Grant Robertson', 'person', 'crawler-conjunction', 'queued', now())""", (new,))
    graph.commit()
    judged = []
    monkeypatch.setattr(crawler, "_re_read",
                        lambda case, labels, **kw: (judged.append(case["entity_id"]) or
                                                    ({"verdict": "two-people", "confidence": 0.9, "reasoning": "x"}, {})))
    monkeypatch.setattr(crawler.model, "judge",
                        lambda *a, **k: (judged.append("acronym") or {"verdict": "organisation", "confidence": 0.9, "reasoning": "x"}))
    monkeypatch.setattr(crawler, "_mirror", lambda row: None)
    import types
    monkeypatch.setattr(crawler, "_worker_connect",
                        lambda g: types.SimpleNamespace(execute=g.execute, close=lambda: None,
                                                        rollback=lambda: None))
    assert crawler.judge(graph, limit=1, concurrency=1) == 1
    assert judged == [new], judged


def test_conjunction_not_a_person_quarantines_at_the_band(graph, monkeypatch, tmp_path):
    """Live 2026-08-22: 24 of the first 31 conjunction verdicts were
    not-a-person at 0.95–1.0 ('Serge Suit and Extra Trousers', 'Duncan
    Grain and Manure Drill') and execute PARKED them — a paid verdict
    thrown away. Junk quarantines through the gate (reversible), as the
    acronym lane's debris already does; below the band still parks."""
    mint_lane.ensure_schema(graph)
    junk = seed_entity(graph, "Serge Suit and Extra Trousers", "person")
    weak = seed_entity(graph, "Bread and Butter Pudding", "person")
    for eid, name, conf in ((junk, "Serge Suit and Extra Trousers", 0.97), (weak, "Bread and Butter Pudding", 0.5)):
        graph.execute("""INSERT INTO mint_review (entity_id, name, type, pattern, status, verdict, confidence)
                         VALUES (%s, %s, 'person', 'crawler-conjunction', 'judged', 'not-a-person', %s)""", (eid, name, conf))
    graph.commit()
    monkeypatch.setenv("B4_CONJUNCTION_SET", str(tmp_path / "set.json"))
    stats = crawler.execute(graph)
    assert stats.get("quarantined") == 1 and stats["parked"] == 1, stats
    rows = {r["entity_id"]: r for r in graph.execute(
        "SELECT m.entity_id, m.status, e.quarantined_at FROM mint_review m JOIN entities e ON e.id=m.entity_id "
        "WHERE m.entity_id IN (%s,%s)", (junk, weak)).fetchall()}
    assert rows[junk]["status"] == "quarantined" and rows[junk]["quarantined_at"] is not None
    assert rows[weak]["status"] == "parked" and rows[weak]["quarantined_at"] is None
    assert graph.execute("SELECT reason FROM entity_quarantine WHERE entity_id=%s", (junk,)).fetchone()["reason"].startswith("crawler:conjunction-not-a-person")
    import json
    frozen = json.load(open(tmp_path / "set.json"))
    assert [x["status"] for x in frozen] == ["quarantined"]


def test_conjunction_split_needs_the_split_band_not_the_auto_band(graph, monkeypatch, tmp_path):
    """Hand-read of the first 36 live splits (2026-08-22): every 0.90
    verdict band held ~8/13 wrong halves ('Claire King Allen & Unwin Pea',
    'Shunhua Ding: Drugs and Human Health'); 0.95+ held. Splits mint
    entities, so they take the higher band; 0.90 two-people parks."""
    mint_lane.ensure_schema(graph)
    e = seed_entity(graph, "Claire King Allen and Unwin Pea", "person")
    graph.execute("""INSERT INTO mint_review (entity_id, name, type, pattern, status, verdict, confidence)
                     VALUES (%s, 'Claire King Allen and Unwin Pea', 'person', 'crawler-conjunction', 'judged', 'two-people', 0.90)""", (e,))
    graph.commit()
    monkeypatch.setenv("B4_CONJUNCTION_SET", str(tmp_path / "set.json"))
    assert crawler.CONJUNCTION_SPLIT_BAND >= 0.95 > crawler.AUTO_BAND
    stats = crawler.execute(graph)
    assert stats.get("split", 0) == 0 and stats["parked"] == 1, stats
    assert graph.execute("SELECT count(*) FROM entity_splits").fetchone()["count"] == 0
