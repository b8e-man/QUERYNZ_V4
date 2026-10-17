"""Two readers, and what their disagreement is allowed to mean."""
import sys, pathlib

import pytest
from support.docread.arbitrate import arbitrate
from support.docread.rows import Document, Row

NAMES = ["Alpha Ltd 1 A St", "Beta Ltd 2 B St", "Gamma Ltd 3 C St",
         "Delta Ltd 4 D St", "Epsilon Ltd 5 E St", "Zeta Ltd 6 F St"]


def rows(amounts, names=None, part="A", start=1):
    names = names or NAMES
    return tuple(Row(n=start + i, donor=names[i], date="2017-01-01",
                     amount=a, part=part, page=1)
                 for i, a in enumerate(amounts))


def doc(amounts, reader, **kw):
    return Document(stem="t", rows=rows(amounts, **kw), reader=reader,
                    year=2017)


def test_two_readers_that_agree_dispute_nothing():
    a = doc([100.0, 200.0, 300.0], "geom")
    b = doc([100.0, 200.0, 300.0], "vlm")
    r = arbitrate([a, b])
    assert r.disputes == () and r.agreement == 1.0
    assert len(r.agreed) == 3


def test_one_wrong_amount_is_one_dispute():
    a = doc([100.0, 200.0, 300.0], "geom")
    b = doc([100.0, 250.0, 300.0], "vlm")
    r = arbitrate([a, b])
    assert len(r.disputes) == 1
    assert r.disputes[0].field == "amount" and r.disputes[0].n == 2


def test_a_rotation_is_caught_though_the_sum_is_unchanged():
    """The failure mode the stated-total gate is blind to, and the reason a
    second reader exists at all."""
    a = doc([100.0, 200.0, 300.0], "geom")
    b = doc([300.0, 100.0, 200.0], "vlm")
    r = arbitrate([a, b])
    assert sum(x.amount for x in a.rows) == sum(x.amount for x in b.rows)
    assert len(r.disputes) == 3
    assert r.agreement == 0.0


def test_a_dropped_row_does_not_cascade():
    """The 2026-09-22 defect that produced four false findings: comparing by
    POSITION after a dropped row reports every later row as wrong. Sequence
    alignment must localise it to the one gap."""
    a = doc([100.0, 200.0, 300.0, 400.0, 500.0, 600.0], "geom")
    b = Document(stem="t", reader="vlm", year=2017, rows=tuple(
        x for x in rows([100.0, 200.0, 300.0, 400.0, 500.0, 600.0])
        if x.n != 3))
    r = arbitrate([a, b])
    amount_disputes = [d for d in r.disputes if d.field == "amount"]
    assert amount_disputes == [], \
        f"a single gap produced {len(amount_disputes)} amount disputes"
    seen_by_one = [f for f in r.findings if f.rule == "seen_by_one_reader"]
    assert len(seen_by_one) == 1 and seen_by_one[0].rows == (3,)


def test_a_row_only_one_reader_saw_is_reported_not_silently_dropped():
    a = doc([100.0, 200.0], "geom")
    b = doc([100.0, 200.0, 300.0], "vlm")
    r = arbitrate([a, b])
    assert [f.rule for f in r.findings] == ["seen_by_one_reader"]
    assert "geom read no row" in r.findings[0].detail


def test_agreement_excludes_rows_that_were_never_compared():
    """A figure states its basis: a row one reader never saw was not agreed
    on, and it was not disagreed on either."""
    a = doc([100.0, 200.0], "geom")
    b = doc([100.0, 200.0, 300.0], "vlm")
    r = arbitrate([a, b])
    assert r.rows_compared == 2 and len(r.agreed) == 2
    assert r.agreement == 1.0, "the two compared rows did agree"
    assert len(r.uncompared) == 1
    assert r.coverage == pytest.approx(2 / 3), \
        "and the figure must carry the row that was never compared"
    assert "only one reader saw" in r.basis()


def test_a_different_donor_in_the_same_slot_is_a_donor_dispute():
    a = doc([100.0, 200.0], "geom")
    b = doc([100.0, 200.0], "vlm",
            names=["Alpha Ltd 1 A St", "Beta Holdings 2 B St"])
    r = arbitrate([a, b])
    fields = {d.field for d in r.disputes}
    assert "donor" in fields


def test_the_street_address_is_not_a_disagreement():
    a = Document("t", (Row(n=1, donor="Hagaman, Lianna 10 Coldstream Court, "
                                      "Christchurch", date="2017-01-01",
                           amount=100.0, part="A"),), reader="geom")
    b = Document("t", (Row(n=1, donor="Hagaman, Lianna 10 Coldstream Court, "
                                      "Ilam, Christchurch", date="2017-01-01",
                           amount=100.0, part="A"),), reader="vlm")
    assert arbitrate([a, b]).disputes == ()


def test_cents_are_compared_to_the_cent():
    a = doc([100.00], "geom")
    b = doc([100.004], "vlm")
    assert arbitrate([a, b]).disputes == ()
    c = doc([100.02], "vlm")
    assert arbitrate([a, c]).disputes != ()


def test_three_readers_dispute_when_any_one_differs():
    a, b = doc([100.0], "geom"), doc([100.0], "vlm")
    c = doc([999.0], "a-third-reader")
    r = arbitrate([a, b, c])
    assert len(r.disputes) == 1
    assert dict(r.disputes[0].values)["a-third-reader"] == 999.0


def test_one_reader_is_not_arbitration():
    with pytest.raises(ValueError):
        arbitrate([doc([100.0], "geom")])


def test_agreement_is_not_a_claim_of_correctness():
    """Both readers wrong in the same way agree. The partition is the product;
    truth is not."""
    a = doc([111.0], "geom")
    b = doc([111.0], "vlm")
    r = arbitrate([a, b])
    assert r.agreement == 1.0 and r.disputes == ()


def test_agreement_alone_can_flatter_and_coverage_is_what_says_so():
    """One row compared out of six reads as 100% agreement. That number is
    true and useless without its basis."""
    a = doc([100.0], "geom")
    b = doc([100.0, 200.0, 300.0, 400.0, 500.0, 600.0], "vlm")
    r = arbitrate([a, b])
    assert r.agreement == 1.0
    assert r.coverage == pytest.approx(1 / 6)
    assert "5 row(s) only one reader saw" in r.basis()


def test_a_row_the_leading_reader_never_saw_is_still_reported():
    """The alignment is led by whichever reader found most rows, so a row the
    OTHER reader found alone is easy to lose. It is a gap like any other: it
    must be reported and it must be outside the agreement denominator."""
    long_names = NAMES + ["Eta Ltd 7 G St"]
    a = Document("t", reader="geom", year=2017,
                 rows=rows([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0],
                           names=long_names))
    b_rows = list(rows([10.0, 20.0, 30.0], names=long_names))
    b_rows.append(Row(n=99, donor="Omega Ltd 9 Z St", date="2017-01-01",
                      amount=999.0, part="A", page=1))
    b_rows += [x for x in rows([10.0, 20.0, 30.0, 40.0, 50.0],
                               names=long_names) if x.n in (4, 5)]
    b = Document("t", reader="vlm", year=2017, rows=tuple(b_rows))

    r = arbitrate([a, b])
    lone = [f for f in r.findings if f.rule == "seen_by_one_reader"]
    assert any("only vlm read a row" in f.detail and "Omega" in f.detail
               for f in lone), f"Omega was never reported: {[f.detail for f in lone]}"
    assert any(x.donor and "Omega" in x.donor for x in r.uncompared), \
        "a row only one reader saw must sit outside the agreement denominator"


def test_a_dispute_on_one_unnumbered_row_does_not_blank_the_others():
    """2026-09-23, the bug that made the gold set empty and took seven wrong
    fixes to find. `merge` keyed disputed fields on (part, n); for rows with
    no printed number n is None, so one dispute anywhere in the part emptied
    the amount of EVERY unnumbered row in it — and the rows reaching the gold
    set had every field None while looking perfectly agreed."""
    from support.docread.arbitrate import merge
    clean = Row(n=None, donor="Clean Co 1 A St", date="2017-01-01",
                amount=100.0, part="G", page=1)
    messy = Row(n=None, donor="Messy Co 2 B St", date="2017-01-01",
                amount=200.0, part="G", page=1)
    a = Document("t", (clean, messy), reader="geometry", year=2017)
    b = Document("t", (clean, Row(n=None, donor="Messy Co 2 B St",
                                  date="2017-01-01", amount=999.0,
                                  part="G", page=1)),
                 reader="glm-ocr", year=2017)
    doc, arb = merge(a, b)
    rows = {r.donor: r for r in doc.rows if r.donor}
    assert rows["Clean Co 1 A St"].amount == 100.0, \
        "the undisputed row keeps its amount"
    assert rows["Clean Co 1 A St"].agreed
    assert rows["Messy Co 2 B St"].amount is None, \
        "the disputed row is still blanked and queued"


# --- C422: a pair the readers cannot corroborate is not a pair -------------
# Arthur, 2026-09-23, on the disputed gold tab: "I am having trouble finding
# the donor named in the dispute in the page displayed, I am not confident in
# my disputed rulings made so far." He was right not to be. Both of his
# rulings attached another row's amount to a donor printed on another page.

def _geom_vs_vlm(geom_rows, vlm_rows):
    from support.docread.arbitrate import merge
    a = Document("t", tuple(geom_rows), reader="geometry", year=2023)
    b = Document("t", tuple(vlm_rows), reader="glm-ocr", year=2023)
    return merge(a, b)


def test_a_merged_row_carries_the_page_of_the_donor_it_names():
    """THE bug, in the shape it reached Arthur.

    Geometry mangles the donor cell into an address fragment, so the whole part
    arrives as ONE replace block; and geometry also reads the form's column
    header as a row (`Amount of contribution (including GST)` is a donor name
    on National 2021). That one spurious row puts geometry one ahead, and
    paired by position every later row became a chimera: the transcriber's
    donor carried on another row's page with another row's amount. Arthur was
    served page 5 for `Allan D Johnson`, printed on page 4, and offered
    12,500.00 — a real amount on the page he was shown — against 11,000.00.
    """
    geom = [Row(donor="Amount of contribution (including GST)", amount=None, page=2, part="A"),
            Row(donor="|30 Findlay Street", amount=5040.0, page=2, part="A"),
            Row(donor="|32 Autumn Avenue", amount=11000.0, page=4, part="A"),
            Row(donor="|17 Dover Street", amount=12500.0, page=5, part="A")]
    vlm = [Row(donor="Glenys Mather 30 Findlay Street", amount=5040.0, page=2, part="A"),
           Row(donor="Allan D Johnson 32 Autumn Avenue", amount=11000.0, page=4, part="A"),
           Row(donor="Sue Morrison 17 Dover Street", amount=12500.0, page=5, part="A")]
    merged, _ = _geom_vs_vlm(geom, vlm)
    johnson = next(r for r in merged.rows if "Johnson" in (r.donor or ""))
    assert johnson.page == 4, "the donor's own page, not the page of whatever row paired with it"
    assert johnson.amount == 11000.0, "the donor's own amount, not the next row's"


def test_an_offset_reader_does_not_manufacture_a_page_of_disputes():
    """Geometry reading one row late produced 43 'disputes' on Green 2023, each
    offering the neighbouring row's amount as the alternative. They were never
    two readings of one cell, so they were never questions — and the wrong
    option was always a real number printed nearby, which is the one kind of
    wrong a person cannot catch by looking."""
    geom = [Row(donor="Does the donation contain contributions", amount=None, page=2, part="A"),
            Row(donor="|1 X St", amount=5300.0, page=2, part="A"),
            Row(donor="|2 Y St", amount=5350.0, page=2, part="A"),
            Row(donor="|3 Z St", amount=5480.0, page=2, part="A")]
    vlm = [Row(donor="Diane Baguley 1 X St", amount=5300.0, page=2, part="A"),
           Row(donor="James V Jenkins 2 Y St", amount=5350.0, page=2, part="A"),
           Row(donor="Rebecca M Scott 3 Z St", amount=5480.0, page=2, part="A")]
    _, arb = _geom_vs_vlm(geom, vlm)
    amounts = [d for d in arb.disputes if d.field == "amount"]
    assert not amounts, f"amounts agree row-for-row once paired on evidence: {amounts}"


def test_a_row_that_corroborates_with_nothing_is_left_unpaired():
    """Unpaired is the honest outcome. A merged row built from two readers that
    agreed on NOTHING is a chimera, and every question asked about it is
    unanswerable."""
    from support.docread.arbitrate import _pair_replace
    x = Row(n=1, donor="|a", amount=100.0, date="2023-01-01", part="A")
    y = Row(n=9, donor="Zeta Ltd", amount=999.0, date="2023-12-31", part="A")
    assert _pair_replace([x], [y]) == [(x, None), (None, y)]


def test_one_corroborating_field_is_enough_to_pair():
    from support.docread.arbitrate import _pair_replace
    x = Row(n=None, donor="|30 Findlay Street", amount=5040.0, part="A")
    y = Row(n=None, donor="Glenys Mather 30 Findlay Street", amount=5040.0, part="A")
    assert _pair_replace([x], [y]) == [(x, y)]


def test_a_repeated_amount_pairs_with_the_nearer_row():
    """Green 2023 page 7 carries 100,000.00 three times. Score ties must break
    on position or the merge shuffles identical amounts between donors."""
    from support.docread.arbitrate import _pair_replace
    xs = [Row(donor="|p", amount=100000.0, page=7, part="A"),
          Row(donor="|q", amount=100000.0, page=7, part="A")]
    ys = [Row(donor="Michael Lookman 63 G Rd", amount=100000.0, page=7, part="A"),
          Row(donor="Weft Knitting Company 61 O St", amount=100000.0, page=7, part="A")]
    assert _pair_replace(xs, ys) == [(xs[0], ys[0]), (xs[1], ys[1])]
