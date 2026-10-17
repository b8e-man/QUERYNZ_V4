"""C261: a count nobody can resolve back to rows can only be repeated.

The 2026-08-23 R3a artifact recorded `dissent` row by row and `abstain_one_side`
as a SCALAR: 110 of 300. The card raised off that number asked how much of the 110
was the 1,024 reasoning budget — a question the artifact it came from could not
answer, because it never said which rows abstained. Measured 2026-10-07 while
closing the card: of the 54 dissent rows the artifact DOES name, **zero** are
still in a fresh `sample(n=300, seed=20260822)`, so the rows could not be
recovered from the draw either. The one thing that would have settled it was the
only thing not written down.

So the abstaining rows are now listed the same way the dissenting ones are, with
`which` naming the side that abstained — the fleet or the dense model — because
"one side abstained" is two different findings and the count conflates them.
"""
import sys

import pytest

from healer import dense_validation as dv


def _row(eid, pattern, fleet, dense, fleet_conf=0.9, dense_conf=0.8):
    return {"entity_id": eid, "name": f"E{eid}", "type": "organisation",
            "pattern": pattern, "verdict": fleet, "confidence": fleet_conf,
            "reasoning": "fleet said so",
            "dense": {"verdict": dense, "confidence": dense_conf,
                      "reasoning": "dense said so", "model": "m"}}


def test_an_abstaining_row_is_NAMED_not_just_counted():
    rep = dv.report([_row(1, "p", "conflated", "abstain")])
    assert rep["abstain_one_side"] == 1
    assert [r["entity_id"] for r in rep["abstain"]] == [1], (
        "the count is there and the row is not — which is the defect")


def test_the_report_says_WHICH_SIDE_abstained():
    """Two different findings. The dense model abstaining means the second opinion
    could not decide; the FLEET abstaining means the verdict under test was an
    abstention in the first place."""
    rep = dv.report([_row(1, "p", "conflated", "abstain"),
                     _row(2, "p", "abstain", "conflated")])
    which = {r["entity_id"]: r["which"] for r in rep["abstain"]}
    assert which == {1: "dense", 2: "fleet"}


def test_BOTH_abstaining_counts_once_and_is_not_a_dissent():
    rep = dv.report([_row(1, "p", "abstain", "abstain")])
    assert rep["abstain_one_side"] == 0, (
        "both sides abstaining is AGREEMENT on abstention, not one-sided")
    assert rep["abstain"] == [] and rep["dissent"] == []
    assert rep["agreement"] == 1.0


def test_a_real_dissent_is_still_a_dissent_and_not_an_abstain():
    rep = dv.report([_row(1, "p", "conflated", "mistyped-duplicate")])
    assert rep["abstain_one_side"] == 0 and rep["abstain"] == []
    assert [r["entity_id"] for r in rep["dissent"]] == [1]


def test_an_ERROR_row_is_neither():
    rep = dv.report([_row(1, "p", "conflated", "error")])
    assert rep["errors"] == 1
    assert rep["abstain"] == [] and rep["dissent"] == []
    assert rep["agreement"] is None, "an all-error pass has no agreement to report"


def test_the_counts_and_the_lists_CANNOT_disagree():
    """The whole point: the scalar and the rows come from one pass, so a future
    edit cannot leave them out of step."""
    rows = [_row(1, "a", "conflated", "abstain"),
            _row(2, "a", "abstain", "conflated"),
            _row(3, "a", "conflated", "conflated"),
            _row(4, "b", "conflated", "mistyped-duplicate"),
            _row(5, "b", "abstain", "abstain")]
    rep = dv.report(rows)
    assert len(rep["abstain"]) == rep["abstain_one_side"] == 2
    assert len(rep["dissent"]) == 1
    per = sum(c["abstain_one_side"] for c in rep["per_pattern"].values())
    assert per == rep["abstain_one_side"], "per-pattern and total disagree"
