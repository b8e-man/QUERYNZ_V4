"""A part with no donor names cannot be aligned by name (C463, 2026-10-10).

Part G of a party return is three banded AGGREGATES and prints no donor, so
every donor key on both sides is the empty string and `SequenceMatcher` reports
one long `equal` block however the amounts line up. Measured consequences, both
on ACT 2025 page 3 when two readers still ran:

  * equal counts -> the rows pair BY POSITION, which is the chimera C422 fixed
    for named rows and left standing here because a replace block never forms;
  * different counts -> the remainder falls to insert/delete, `merge` keeps the
    unpaired character row, and ONE printed line is emitted TWICE — once
    addressed `n=10`, once `d=...#0`. That is C463's emission half, which
    `numberless_twins` has been withdrawing at READ time since 2026-09-28.

DORMANT, AND PINNED ANYWAY. One reader has run since 2026-09-25, so `arbitrate`
is reached only with a second reading — and a second OCR model brings this
straight back. Every test here fails against the alignment as it stood this
morning.
"""
import sys
from pathlib import Path

from support.docread import gold  # noqa: E402
from support.docread.arbitrate import _align, merge  # noqa: E402
from support.docread.rows import Document, Row  # noqa: E402


def _row(part="G", n=None, donor=None, amount=None, date=None, page=1):
    return Row(n=n, donor=donor, date=date, amount=amount, page=page, part=part)


def _doc(stem, rows, reader):
    return Document(stem=stem, rows=tuple(rows), reader=reader)


def test_a_donorless_part_pairs_on_the_amount_not_the_position():
    """THE CHIMERA. The structure reader found a row the transcriber missed;
    position pairs $100 with $200 and reports a dispute about a line neither
    reader disagreed on."""
    spine = [_row(n=1, amount=100.0), _row(n=2, amount=200.0), _row(n=3, amount=300.0)]
    other = [_row(amount=200.0), _row(amount=300.0)]
    pairs = dict((id(a) if a else None, b) for a, b in _align(spine, other))
    assert pairs[id(spine[1])] is not None and pairs[id(spine[1])].amount == 200.0
    assert pairs[id(spine[2])] is not None and pairs[id(spine[2])].amount == 300.0
    assert pairs[id(spine[0])] is None          # honestly unpaired, not chimera'd


def test_one_printed_line_becomes_ONE_merged_row():
    """C463's emission. The transcriber read the same three aggregates without
    their margin numbers; before the fix the third pair failed and `merge`
    emitted a fourth row for a line it had already emitted."""
    spine = _doc("x", [_row(n=1, amount=100.0), _row(n=2, amount=200.0),
                       _row(n=3, amount=300.0)], "structure")
    other = _doc("x", [_row(amount=200.0), _row(amount=300.0),
                       _row(amount=100.0)], "characters")
    doc, _arb = merge(spine, other)
    assert len(doc.part("G")) == 3, [r.amount for r in doc.part("G")]
    assert sorted(r.amount for r in doc.part("G")) == [100.0, 200.0, 300.0]


def test_one_printed_line_gets_ONE_gold_address():
    """The defect as Arthur met it: the queue said 49 where the page held 38.
    Two rows for one line address it twice — once by number, once by donor."""
    spine = _doc("x", [_row(n=1, amount=100.0), _row(n=2, amount=200.0)], "structure")
    other = _doc("x", [_row(amount=200.0), _row(amount=100.0)], "characters")
    doc, _arb = merge(spine, other)
    addrs = [gold.address(r.n, r.donor, i) for i, r in enumerate(doc.part("G"))]
    assert len(addrs) == len(set(addrs)) == 2, addrs
    assert not [a for a in addrs if a.startswith("d=")], \
        f"a numbered line addressed by donor key as well: {addrs}"


def test_a_row_that_corroborates_with_nothing_stays_unpaired():
    """Abstain is the design: `merge` then builds no row from two readings that
    never agreed, and the completeness checks see a row each reader saw alone."""
    spine = [_row(n=1, amount=100.0)]
    other = [_row(amount=999.0)]
    got = _align(spine, other)
    assert sorted((a is None, b is None) for a, b in got) == [(False, True), (True, False)]


def test_a_donorless_part_pairs_on_the_DATE_when_amounts_differ():
    """`_corroboration` takes n, amount or date — any positive agreement."""
    spine = [_row(n=1, amount=100.0, date="2024-05-01")]
    other = [_row(amount=None, date="2024-05-01")]
    (a, b), = _align(spine, other)
    assert a is spine[0] and b is other[0]


def test_a_part_WITH_donor_names_still_aligns_BY_NAME():
    """The fix is scoped to the case where names carry no information: the new
    branch runs only when EVERY key on both sides is empty.

    Pinned with the amounts SWAPPED, so the two paths would disagree: the name
    sequence pairs Atlas with Atlas, while pairing on evidence would prefer the
    row whose amount matches. The name must win — it is the stronger evidence
    and `TRUSTED_FOR` sends the donor to the transcriber for that reason.

    (A REORDERED pair is a different matter and is NOT fixed here: for
    `['a','h']` against `['h','a']` SequenceMatcher reports delete + equal +
    insert, so one row pairs and the other goes out unpaired without ever
    reaching `_pair_replace`. Pre-existing, measured 2026-10-10, left alone —
    one card, one job.)
    """
    spine = [_row(part="A", n=1, donor="Atlas Concrete Limited", amount=5000.0),
             _row(part="A", n=2, donor="Harbour Holdings Ltd", amount=7000.0)]
    other = [_row(part="A", donor="Atlas Concrete Limited", amount=7000.0),
             _row(part="A", donor="Harbour Holdings Ltd", amount=5000.0)]
    pairs = {id(a): b for a, b in _align(spine, other) if a}
    assert pairs[id(spine[0])].donor == "Atlas Concrete Limited"
    assert pairs[id(spine[1])].donor == "Harbour Holdings Ltd"


def test_one_side_donorless_already_took_the_evidence_path():
    """When only ONE reader lost the names the keys differ, a replace block
    forms, and `_pair_replace` was already reached — this pins that it stays
    so, because the new branch requires BOTH sides empty."""
    spine = [_row(part="A", n=1, donor="Atlas Concrete Limited", amount=5000.0)]
    other = [_row(part="A", donor=None, amount=5000.0)]
    (a, b), = _align(spine, other)
    assert a is spine[0] and b is other[0]
