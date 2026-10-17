"""C246: `repair-no-evidence` was a terminal state nothing ever re-read.

The repair lane needs VERBATIM evidence in the entity's own sighting articles.
When it finds none it writes `repair-no-evidence` — and the select asked only for
`flagged-truncated`, so that row was never looked at again. The corpus grows
every night; the article that completes "Greater Wellington Te" may well be
ingested a week after the row was judged. MEASURED 2026-10-07: **7,001 rows in
`repair-no-evidence`, 5,220 of them judged more than 30 days ago**, against
2,298 live `flagged-truncated` rows and a cap of 300 a run.

WHY SPARE CAPACITY AND NOT A SHARED ORDER BY, which is the whole of the card.
5,220 aged rows into one `ORDER BY` with 2,298 new ones would starve genuinely
new work for weeks — the lane would spend every night re-asking questions it has
already answered while fresh truncations sat unexamined. So the re-queue only
TOPS UP a batch the new work has not filled, which self-regulates: the backlog
drains first, and the aged rows get re-asked out of whatever is left.

AND IT MUST NOT BECOME A TREADMILL. A re-queued row that still finds no evidence
has its `actioned_at` refreshed, so it waits another full window rather than
being re-asked every night for ever.
"""
from testkit import graph, seed_entity  # noqa: F401

from healer import mint_lane, repair
from reviewer import corroborate


def _row(g, name, status, age_days=None, etype="organisation", quarantined=False):
    """Seed an entity and its mint_review row at a chosen age."""
    eid = seed_entity(g, name, etype)
    if quarantined:
        g.execute("UPDATE entities SET quarantined_at=now() WHERE id=%s", (eid,))
    g.execute("""
        INSERT INTO mint_review (entity_id, name, type, pattern, status, actioned_at)
        VALUES (%s,%s,%s,'trailing-particle',%s,
                CASE WHEN %s::int IS NULL THEN NULL
                     ELSE now() - make_interval(days => %s::int) END)""",
        (eid, name, etype, status, age_days, age_days))
    g.commit()
    return eid


def _names(rows):
    return [r["name"] for r in rows]


def test_an_AGED_no_evidence_row_is_re_queued(graph):
    mint_lane.ensure_schema(graph)
    _row(graph, "Te Rūnanga o", "repair-no-evidence", age_days=40)
    rows, requeued = repair.select_batch(graph)
    assert requeued == 1, "a row judged 40 days ago was never looked at again"
    assert _names(rows) == ["Te Rūnanga o"]


def test_a_RECENT_no_evidence_row_is_LEFT_ALONE(graph):
    """Re-asking a row judged yesterday spends the lane's budget on a corpus that
    has barely moved."""
    mint_lane.ensure_schema(graph)
    _row(graph, "Greater Wellington Te", "repair-no-evidence", age_days=3)
    rows, requeued = repair.select_batch(graph)
    assert (rows, requeued) == ([], 0)


def test_NEW_WORK_IS_NEVER_DISPLACED(graph, monkeypatch):
    """The assertion the card exists for. With the cap filled by new rows, not one
    aged row is re-queued — whatever the size of the aged backlog."""
    mint_lane.ensure_schema(graph)
    monkeypatch.setattr(repair, "REPAIR_CAP", 4)
    for i in range(6):
        _row(graph, f"New Truncation {i} Te", "flagged-truncated")
    for i in range(20):
        _row(graph, f"Old Stub {i} o", "repair-no-evidence", age_days=99)
    rows, requeued = repair.select_batch(graph)
    assert requeued == 0, (
        f"{requeued} aged rows took places from new work: the lane would spend "
        f"its nights re-asking answered questions")
    assert len(rows) == 4
    assert all(r["name"].startswith("New Truncation") for r in rows)


def test_the_TOP_UP_respects_the_cap(graph, monkeypatch):
    """Spare capacity, not extra capacity — the cap is what keeps a run bounded."""
    mint_lane.ensure_schema(graph)
    monkeypatch.setattr(repair, "REPAIR_CAP", 5)
    for i in range(2):
        _row(graph, f"New {i} Te", "flagged-truncated")
    for i in range(20):
        _row(graph, f"Old {i} o", "repair-no-evidence", age_days=99)
    rows, requeued = repair.select_batch(graph)
    assert len(rows) == 5 and requeued == 3, (
        f"{len(rows)} rows for a cap of 5")


def test_the_OLDEST_aged_rows_come_first(graph, monkeypatch):
    """So a row does not sit at the back of the queue indefinitely because newer
    no-evidence rows keep arriving."""
    mint_lane.ensure_schema(graph)
    monkeypatch.setattr(repair, "REPAIR_CAP", 2)
    _row(graph, "Middle o", "repair-no-evidence", age_days=60)
    _row(graph, "Oldest o", "repair-no-evidence", age_days=400)
    _row(graph, "Newest o", "repair-no-evidence", age_days=31)
    rows, _ = repair.select_batch(graph)
    assert _names(rows) == ["Oldest o", "Middle o"]


def test_a_QUARANTINED_entity_is_not_re_queued(graph):
    """Quarantine is the estate's "do not touch"; the re-queue must honour the
    same join the new-work select does."""
    mint_lane.ensure_schema(graph)
    _row(graph, "Quarantined Te", "repair-no-evidence", age_days=99,
         quarantined=True)
    assert repair.select_batch(graph) == ([], 0)


def test_OTHER_statuses_are_not_swept_in(graph):
    """`renamed`, `merged` and `judging` are settled or in flight. Re-queueing a
    settled row would re-open a decision; re-queueing `judging` would race."""
    mint_lane.ensure_schema(graph)
    for st in ("renamed", "merged", "judging", "pending"):
        _row(graph, f"Settled {st} o", st, age_days=99)
    assert repair.select_batch(graph) == ([], 0)


def test_a_re_queued_row_that_STILL_finds_nothing_waits_another_window(graph,
                                                                      tmp_path,
                                                                      monkeypatch):
    """Not a treadmill. Without refreshing `actioned_at` the same 5,220 rows
    would be re-asked every single night for ever."""
    mint_lane.ensure_schema(graph)
    monkeypatch.setattr(mint_lane, "VERDICTS_PATH", str(tmp_path / "v.jsonl"))
    monkeypatch.setattr(repair, "VERDICTS_PATH", str(tmp_path / "v.jsonl"))
    monkeypatch.setattr(repair, "_article_texts", lambda g, b, eid, cap=12: [])
    monkeypatch.setattr(repair, "_backlog", lambda: object())
    monkeypatch.setattr(corroborate, "register_conn", lambda: None)
    eid = _row(graph, "Still Nothing Te", "repair-no-evidence", age_days=99)

    stats = repair.run(graph)
    assert stats["requeued"] == 1 and stats["no_evidence"] == 1
    age = graph.execute("""
        SELECT extract(epoch from (now() - actioned_at)) AS secs
        FROM mint_review WHERE entity_id=%s""", (eid,)).fetchone()["secs"]
    assert age < 60, f"actioned_at was not refreshed ({age:.0f}s old)"
    assert repair.select_batch(graph) == ([], 0), (
        "the row is immediately re-queueable again, so the lane re-asks it nightly")


def test_the_run_REPORTS_the_re_queue(graph, tmp_path, monkeypatch):
    """A lane doing invisible extra work is a lane nobody can size. `requeued` is
    how the night's log says how much of the batch was a second ask."""
    mint_lane.ensure_schema(graph)
    monkeypatch.setattr(repair, "_backlog", lambda: None)
    assert "requeued" in repair.run(graph)
