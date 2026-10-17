"""The return's own summary total, and the reconciliation it restores (C418).

The per-part totals came from the geometric reader, retired 2026-09-25. Fifteen
of the 107 party returns in scope lost EVERY stated total with it — Labour
2021, Te Pāti Māori 2025 and NZ First's amended return among them — so nothing
could be reconciled and an unchecked document looked exactly like a clean one.
106 of the 107 print `Total Party Donations (A + C + D + F + G) $N` on page 1.

Ten spellings were measured across those 107 documents on 2026-10-10 and each
one is a case below, because a pattern argued from one example is a pattern
that fits one example.
"""
import sys
from pathlib import Path

import pytest

from support.docread import invariants as inv, parse  # noqa: E402
from support.docread.rows import Document, Row  # noqa: E402


@pytest.mark.parametrize("line,amount,parts", [
    ("Total Party Donations (A + C + D + F + G) $1,500,307.55", 1500307.55, ("A","C","D","F","G")),
    ("Total (A + C + D + F + G) $ 207,385.96", 207385.96, ("A","C","D","F","G")),
    ("Total (A + C + D + F + G) $141,986.50", 141986.50, ("A","C","D","F","G")),
    ("Total Party Donations (A + C + D + F + G) 1877416.69", 1877416.69, ("A","C","D","F","G")),
    ("Total (A + C + D + F + G) 50000.00", 50000.00, ("A","C","D","F","G")),
    ("Total Party Donations (A + C + D + F + G) = 50.00", 50.00, ("A","C","D","F","G")),
    ("Total (A + C + D + F + G) NIL", 0.0, ("A","C","D","F","G")),
    ("TOTAL (A + C) $12,000.00", 12000.00, ("A","C")),
])
def test_every_measured_spelling(line, amount, parts):
    doc = parse.parse_document("x", {1: line})
    assert doc.declared_total == pytest.approx(amount)
    assert doc.declared_parts == parts


def test_an_unformatted_amount_is_not_truncated_to_its_first_three_digits():
    """THE LOOKAHEAD. The estate's other money patterns end in a mandatory
    `.NN`, which forces the alternation to backtrack onto the whole number.
    Cents are optional here, so without `(?![\\d,])` the first alternative
    matches "187" of "1877416" and this reads $187.00 for $1,877,416.69 — and
    NZ First's amended return prints its totals with no separators at all."""
    doc = parse.parse_document("x", {1: "Total Party Donations (A + C + D + F + G) 1877416.69"})
    assert doc.declared_total == pytest.approx(1877416.69)
    assert parse.parse_document("x", {1: "Total (A + C) 255000"}).declared_total == 255000.0


def test_the_party_LOANS_line_is_never_a_donations_total():
    """The same page prints `Total (H + I) $0.00`, which is loans. Reading it
    as the donations total would reconcile every return against zero."""
    doc = parse.parse_document("x", {1: "Total (H + I) $0.00"})
    assert doc.declared_total is None and doc.declared_parts == ()


def test_a_line_with_no_amount_declares_nothing():
    """Three of the 107 print the label and no figure. Abstain is the design:
    a declared total of 0.0 would fail every part in the document."""
    assert parse.parse_document("x", {1: "Total (A + C + D + F + G)"}).declared_total is None


def test_the_first_summary_wins():
    """The summary is on page 1; a later page repeating it is a continuation
    sheet, not a second declaration."""
    doc = parse.parse_document("x", {1: "Total (A + C) $100.00", 2: "Total (A + C) $999.00"})
    assert doc.declared_total == pytest.approx(100.00)


def _doc(**kw):
    return Document(stem="x", **kw)


def test_the_invariant_SKIPS_when_the_return_declares_nothing():
    rep = inv.check(_doc(rows=(Row(n=1, donor="A", date=None, amount=5.0, page=1, part="A"),)))
    skips = [s for s, _ in rep.skipped if s == "declared_total_matches_parts"]
    assert skips and not [f for f in rep.fails if f.rule == "declared_total_matches_parts"]


def test_the_invariant_PASSES_when_the_parts_add_up():
    rows = (Row(n=1, donor="A", date=None, amount=60.0, page=1, part="A"),
            Row(n=2, donor="B", date=None, amount=40.0, page=1, part="C"))
    rep = inv.check(_doc(rows=rows, declared_total=100.0, declared_parts=("A", "C")))
    assert not [f for f in rep.fails if f.rule == "declared_total_matches_parts"]


def test_the_invariant_FAILS_short_and_says_by_how_much():
    rows = (Row(n=1, donor="A", date=None, amount=60.0, page=1, part="A"),)
    rep = inv.check(_doc(rows=rows, declared_total=100.0, declared_parts=("A", "C")))
    f = next(f for f in rep.fails if f.rule == "declared_total_matches_parts")
    assert "short by $40.00" in f.detail and "$100.00" in f.detail


def test_a_read_OVER_the_declared_total_is_named_as_over():
    """Over-reading is the impossible direction (C433): a return itemises up to
    the total it declares, so money above it was made up."""
    rows = (Row(n=1, donor="A", date=None, amount=500.0, page=1, part="A"),)
    rep = inv.check(_doc(rows=rows, declared_total=100.0, declared_parts=("A",)))
    f = next(f for f in rep.fails if f.rule == "declared_total_matches_parts")
    assert "over by $400.00" in f.detail


def test_rows_with_no_part_are_NAMED_rather_than_counted_as_missing_money():
    """A shortfall that is really a part-header miss must read as one."""
    rows = (Row(n=1, donor="A", date=None, amount=60.0, page=1, part="A"),
            Row(n=2, donor="B", date=None, amount=40.0, page=1, part=None))
    rep = inv.check(_doc(rows=rows, declared_total=100.0, declared_parts=("A", "C")))
    f = next(f for f in rep.fails if f.rule == "declared_total_matches_parts")
    assert "1 row(s) carry no part at all, worth $40.00" in f.detail


def test_the_parts_are_the_ones_the_RETURN_declared():
    """A return declaring (A + B) is held to A+B, not to a set assumed here."""
    rows = (Row(n=1, donor="A", date=None, amount=60.0, page=1, part="A"),
            Row(n=2, donor="B", date=None, amount=40.0, page=1, part="B"),
            Row(n=3, donor="C", date=None, amount=99.0, page=1, part="G"))
    rep = inv.check(_doc(rows=rows, declared_total=100.0, declared_parts=("A", "B")))
    assert not [f for f in rep.fails if f.rule == "declared_total_matches_parts"]


def test_the_rule_is_registered():
    """An invariant not in RULES is a function nobody calls."""
    assert inv.declared_total_matches_parts in inv.RULES
