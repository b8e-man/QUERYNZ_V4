"""B4b §5 c — merge_duplicates with a scripted refuter on the testkit graph:
refuted → no merge, a merge_refutations row, status 'refuted';
not-refuted → merged through the gate with the refuter named in the reason
and the ledger row linked to the merge; abstain → parked; a junk name parks
WITHOUT spending a refuter call. Watched to fail on the pre-B4b actuator
(no _refute, no ledger)."""
from healer import crawler, mint_lane
from testkit import fresh_graph, graph, seed_entity  # noqa: F401


def _queue(graph, name, keeper_type="person", loser_type="organisation", conf=0.95, keeper_mentions=9):
    """A judged mistyped-duplicate pair: the keeper side dominates mentions."""
    mint_lane.ensure_schema(graph)
    k = seed_entity(graph, name, keeper_type)
    l = seed_entity(graph, name, loser_type)
    for i in range(keeper_mentions):
        graph.execute("INSERT INTO mentions (entity_id, article_id, surface_form, n_mentions, salience) "
                      "VALUES (%s, gen_random_uuid(), %s, 1, 'participant')", (k, name))
    graph.execute("INSERT INTO mentions (entity_id, article_id, surface_form, n_mentions, salience) "
                  "VALUES (%s, gen_random_uuid(), %s, 1, 'participant')", (l, name))
    graph.execute("""INSERT INTO mint_review (entity_id, name, type, pattern, status, verdict, confidence)
                     VALUES (%s, %s, %s, 'crawler-type-multiplicity', 'observed', 'mistyped-duplicate', %s)""",
                  (l, name, loser_type, conf))
    graph.commit()
    return k, l


def _script(monkeypatch, verdict, reasoning="the graph evidence says so", urls=()):
    calls = []

    def fake(pair, **kw):
        calls.append(pair)
        return ({"verdict": verdict, "confidence": 0.9, "reasoning": reasoning,
                 "evidence": [{"kind": "web", "ref": u} for u in urls]}, {"urls": list(urls)})
    monkeypatch.setattr(crawler, "_refute", fake)
    monkeypatch.setattr(crawler, "_mirror", lambda row: None)
    return calls


def test_refuted_pair_is_not_merged_and_is_ledgered(graph, monkeypatch):
    k, l = _queue(graph, "Eric Hansen")
    calls = _script(monkeypatch, "refuted", "A is a 1950s councillor, B a 2020s plumbing firm",
                    urls=["https://example.org/eric-hansen-ltd"])
    stats = crawler.merge_duplicates(graph, cap=10)
    assert stats["refuted"] == 1 and stats["merged"] == 0, stats
    assert calls and {calls[0]["a_id"], calls[0]["b_id"]} == {k, l}
    assert graph.execute("SELECT count(*) FROM entity_merges WHERE merged_id IN (%s,%s)", (k, l)).fetchone()["count"] == 0
    row = graph.execute("SELECT verdict, urls, merge_id FROM merge_refutations WHERE loser_id=%s", (l,)).fetchone()
    assert row["verdict"] == "refuted" and row["urls"] == ["https://example.org/eric-hansen-ltd"] and row["merge_id"] is None
    assert graph.execute("SELECT status FROM mint_review WHERE entity_id=%s", (l,)).fetchone()["status"] == "refuted"


def test_not_refuted_pair_merges_with_the_refuter_in_the_reason(graph, monkeypatch):
    k, l = _queue(graph, "Eric Hansen")
    _script(monkeypatch, "not-refuted", "profiles, mentions and two searches found nothing separating them")
    stats = crawler.merge_duplicates(graph, cap=10)
    assert stats["merged"] == 1, stats
    m = graph.execute("SELECT id, kept_id, reason FROM entity_merges WHERE merged_id=%s", (l,)).fetchone()
    assert m["kept_id"] == k and "refuter:not-refuted" in m["reason"]
    row = graph.execute("SELECT merge_id FROM merge_refutations WHERE loser_id=%s", (l,)).fetchone()
    assert row["merge_id"] == m["id"]


def test_abstain_parks(graph, monkeypatch):
    k, l = _queue(graph, "Eric Hansen")
    _script(monkeypatch, "abstain", "evidence too thin either way")
    stats = crawler.merge_duplicates(graph, cap=10)
    assert stats["parked"] == 1 and stats["merged"] == 0
    assert graph.execute("SELECT status FROM mint_review WHERE entity_id=%s", (l,)).fetchone()["status"] == "parked"


def test_junk_name_parks_without_spending_the_refuter(graph, monkeypatch):
    k, l = _queue(graph, "2.20pm", keeper_type="place", loser_type="organisation")
    calls = _script(monkeypatch, "refuted")
    stats = crawler.merge_duplicates(graph, cap=10)
    assert stats["junk"] == 1 and not calls, (stats, calls)
    assert crawler._JUNK_NAME.match("4fd") and crawler._JUNK_NAME.match("7/u") and crawler._JUNK_NAME.match("18S4")
    assert not crawler._JUNK_NAME.match("Eric Hansen") and not crawler._JUNK_NAME.match("ACC")
