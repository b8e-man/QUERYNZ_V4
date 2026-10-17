"""The gold set's one discipline: the two tiers are never mixed."""
import sys, pathlib, tempfile

import dataclasses
import pytest
from support.docread import gold, invariants as inv, queue as q
from support.docread.arbitrate import arbitrate, merge
from support.docread.rows import Document, Row


@pytest.fixture
def path():
    with tempfile.TemporaryDirectory() as td:
        yield pathlib.Path(td) / "gold.jsonl"


def d(rows, reader, **kw):
    kw.setdefault("year", 2024)
    return Document("doc", tuple(rows), reader=reader, **kw)


def r(n, amount=20000.0, donor="Acme Ltd 1 Queen St", date="2024-01-01",
      part="A"):
    return Row(n=n, donor=donor, date=date, amount=amount, part=part, page=1)


def test_a_row_both_readers_agreed_on_becomes_a_candidate():
    a = d([r(1), r(2, donor="Beta Ltd 2 High St")], "geometry")
    b = d([r(1), r(2, donor="Beta Ltd 2 High St")], "glm-ocr")
    doc, arb = merge(a, b)
    cands = gold.candidates(doc, inv.check(doc), arb)
    assert cands and all(c.tier == gold.AGREED for c in cands)
    assert {c.field for c in cands} == {"donor", "date", "amount"}


def test_a_disputed_row_is_never_a_candidate():
    a = d([r(1), r(2, donor="Beta Ltd 2 High St")], "geometry")
    b = d([r(1, amount=99.0), r(2, donor="Beta Ltd 2 High St")], "glm-ocr")
    arb = arbitrate([a, b])
    cands = gold.candidates(a, inv.check(a), arb)
    assert all(c.n != 1 for c in cands)


def test_a_row_any_finding_implicates_is_never_a_candidate():
    """Even a flag. A gold set whose rows are under suspicion is worse than
    no gold set, because it is quoted with the same confidence."""
    rows = [r(1), r(2, donor="Beta Ltd 2 High St"), r(4, donor="Cee Ltd 3 X")]
    a, b = d(rows, "geometry"), d(rows, "glm-ocr")
    rep = inv.check(a)
    assert any(f.rule == "row_numbers_complete" for f in rep.findings)
    doc, arb = merge(a, b)
    cands = gold.candidates(doc, inv.check(doc), arb)
    assert all(c.n != 3 for c in cands)


def test_a_candidate_is_agreed_and_that_is_not_ground_truth():
    """Both readers wrong in the same way produce a candidate. The tier is
    the honesty."""
    a = d([r(1, amount=111.0)], "geometry")
    b = d([r(1, amount=111.0)], "glm-ocr")
    doc, arb = merge(a, b)
    cands = gold.candidates(doc, inv.check(doc), arb)
    assert all(c.tier == gold.AGREED for c in cands)
    assert gold.CONFIRMED not in {c.tier for c in cands}


def test_a_confirmation_outranks_an_agreement_for_the_same_cell(path):
    gold.stage([gold.GoldRow("doc", "A", 1, "amount", 100.0, gold.AGREED)], path)
    gold.confirm("doc", "A", 1, "amount", 50000.0, path, by="arthur")
    g = gold.load(path)
    row = next(iter(g.values()))
    assert row.tier == gold.CONFIRMED and row.value == 50000.0


def test_an_agreement_never_overwrites_a_confirmation(path):
    gold.confirm("doc", "A", 1, "amount", 50000.0, path, by="arthur")
    gold.stage([gold.GoldRow("doc", "A", 1, "amount", 100.0, gold.AGREED)], path)
    row = next(iter(gold.load(path).values()))
    assert row.tier == gold.CONFIRMED and row.value == 50000.0


def test_staging_the_same_candidate_twice_adds_nothing(path):
    g = gold.GoldRow("doc", "A", 1, "amount", 100.0, gold.AGREED)
    assert gold.stage([g], path) == 1
    assert gold.stage([g], path) == 0


def test_scoring_must_name_its_tier(path):
    with pytest.raises(ValueError):
        gold.score(d([r(1)], "x"), gold.load(path), tier="both")
    with pytest.raises(TypeError):
        gold.score(d([r(1)], "x"), gold.load(path))


def test_a_reader_is_scored_only_against_the_tier_asked_for(path):
    gold.stage([gold.GoldRow("doc", "A", 1, "amount", 100.0, gold.AGREED),
                gold.GoldRow("doc", "A", 2, "amount", 200.0, gold.CONFIRMED)],
               path)
    g = gold.load(path)
    doc = d([r(1, amount=100.0), r(2, amount=999.0)], "reader")
    agreed = gold.score(doc, g, tier=gold.AGREED)
    confirmed = gold.score(doc, g, tier=gold.CONFIRMED)
    assert agreed["pins"] == 1 and agreed["accuracy"] == 1.0
    assert confirmed["pins"] == 1 and confirmed["accuracy"] == 0.0


def test_a_score_states_its_basis(path):
    gold.stage([gold.GoldRow("doc", "A", 1, "amount", 100.0, gold.CONFIRMED)],
               path)
    s = gold.score(d([r(1, amount=100.0)], "x"), gold.load(path),
                   tier=gold.CONFIRMED)
    assert "1 of 1 confirmed gold cell(s) for doc" in s["basis"]


def test_no_gold_gives_no_accuracy_rather_than_a_hundred_percent(path):
    s = gold.score(d([r(1)], "x"), gold.load(path), tier=gold.CONFIRMED)
    assert s["accuracy"] is None and s["pins"] == 0
    assert "no confirmed gold" in s["basis"]


def test_a_row_the_reader_missed_counts_against_it_not_as_absent(path):
    gold.stage([gold.GoldRow("doc", "A", 7, "amount", 100.0, gold.CONFIRMED)],
               path)
    s = gold.score(d([r(1)], "x"), gold.load(path), tier=gold.CONFIRMED)
    assert s["missing"] == 1 and s["accuracy"] == 0.0


def test_a_donor_is_compared_on_its_key_not_its_address(path):
    gold.stage([gold.GoldRow("doc", "A", 1, "donor",
                             "Hagaman, Lianna 10 Coldstream Court, Christchurch",
                             gold.CONFIRMED)], path)
    doc = d([r(1, donor="Hagaman, Lianna 10 Coldstream Court, Ilam, "
                         "Christchurch")], "x")
    assert gold.score(doc, gold.load(path), tier=gold.CONFIRMED)["correct"] == 1


def test_a_correction_in_the_queue_becomes_confirmed_gold(path):
    with tempfile.TemporaryDirectory() as td:
        qp = pathlib.Path(td) / "q.jsonl"
        it = q.Item(id="x1", stem="doc", kind="dispute", detail="d", part="A",
                    n=5, field="amount",
                    values=(("geometry", 88.0), ("glm-ocr", 10088.0)))
        q.enqueue([it], qp)
        q.resolve("x1", q.CORRECTED, qp, value=10088.0, by="arthur")
        assert gold.from_resolutions(qp, path) == 1
        row = next(iter(gold.load(path).values()))
        assert row.tier == gold.CONFIRMED and row.by == "arthur"


def test_an_accepted_invariant_item_pins_nothing(path):
    """Accepting 'the rows do not sum' says nothing about any one cell."""
    with tempfile.TemporaryDirectory() as td:
        qp = pathlib.Path(td) / "q.jsonl"
        q.enqueue([q.Item(id="x2", stem="doc", kind="invariant", detail="d",
                          part="A", n=5, field=None)], qp)
        q.resolve("x2", q.ACCEPTED, qp, by="arthur")
        assert gold.from_resolutions(qp, path) == 0


def test_unnumbered_rows_elsewhere_do_not_disqualify_the_numbered_ones():
    """2026-09-23: `rows_carry_printed_numbers` names no rows, so it was
    putting its whole part in doubt and every document yielded zero
    candidates. Gold only ever pins rows that HAVE a number."""
    rows = [r(1), r(2, donor="Beta Ltd 2 High St"),
            Row(n=None, donor="Cee Ltd 3 X", date="2024-01-01",
                amount=30000.0, part="A", page=2)]
    a, b = d(rows, "geometry"), d(rows, "glm-ocr")
    rep = inv.check(a)
    assert any(f.rule == "rows_carry_printed_numbers" for f in rep.findings)
    doc, arb = merge(a, b)
    cands = gold.candidates(doc, inv.check(doc), arb)
    assert cands, "rows both readers agreed on are gold"
    assert {c.n for c in cands} == {1, 2, None}
    # the numbered rows are addressed by their number, the third by its donor
    assert {c.addr for c in cands} == {"n=1", "n=2", "d=ceeltd#0"}


def test_a_part_whose_sum_is_wrong_yields_no_gold_at_all():
    """That rule says SOME row is wrong without saying which, so none of them
    can be pinned."""
    rows = [r(1, amount=100.0), r(2, amount=200.0, donor="Beta Ltd 2 High St")]
    a = d(rows, "geometry", stated_totals={"A": 999.0})
    b = d(rows, "glm-ocr", stated_totals={"A": 999.0})
    rep = inv.check(a)
    assert any(f.rule == "sum_matches_stated_total" for f in rep.fails)
    doc, arb = merge(a, b)
    assert gold.candidates(doc, inv.check(doc), arb) == []


def test_a_row_listed_as_both_agreed_and_disputed_is_not_gold():
    """Belt and braces: `Arbitration.agreed` already excludes disputed rows,
    so the dispute guard in `candidates` is redundant TODAY. It is kept
    because 'agreed' is a definition that could widen, and this pins it."""
    from support.docread.arbitrate import Arbitration, Dispute
    row = r(1)
    arb = Arbitration("doc", None, ("geometry", "glm-ocr"), (row,),
                      (Dispute("A", 1, "Acme Ltd", "amount",
                               (("geometry", 1.0), ("glm-ocr", 2.0))),))
    doc = d([row], "geometry")
    assert gold.candidates(doc, inv.check(doc), arb) == []


def test_an_unreadable_verdict_pins_nothing_even_on_a_field_item(path):
    """UNREADABLE means the person could not tell. That is the one verdict
    that must never become ground truth."""
    with tempfile.TemporaryDirectory() as td:
        qp = pathlib.Path(td) / "q.jsonl"
        q.enqueue([q.Item(id="x3", stem="doc", kind="dispute", detail="d",
                          part="A", n=5, field="amount",
                          values=(("geometry", 88.0), ("glm-ocr", 10088.0)))],
                  qp)
        q.resolve("x3", q.UNREADABLE, qp, by="arthur")
        assert gold.from_resolutions(qp, path) == 0
        assert gold.load(path) == {}


def test_a_row_with_no_printed_number_is_addressed_by_its_donor():
    """Every agreed row on the first six documents read whole had no number.
    Keyed on the number alone the gold set stays empty on most of the
    corpus."""
    rows = [Row(n=None, donor="Acme Ltd 1 Queen St", date="2024-01-01",
                amount=20000.0, part="A", page=1),
            Row(n=None, donor="Acme Ltd 1 Queen St", date="2024-02-01",
                amount=30000.0, part="A", page=1)]
    a, b = d(rows, "geometry"), d(rows, "glm-ocr")
    doc, arb = merge(a, b)
    cands = gold.candidates(doc, inv.check(doc), arb)
    addrs = {c.addr for c in cands}
    assert addrs == {"d=acmeltd#0", "d=acmeltd#1"}, \
        "two rows of one donor must not collide on the same address"


def test_a_donor_addressed_pin_survives_a_re_read_that_keeps_the_donor():
    """The address is stable as long as the donor reads the same way."""
    import tempfile as tf
    with tf.TemporaryDirectory() as td:
        gp = pathlib.Path(td) / "g.jsonl"
        rows = [Row(n=None, donor="Acme Ltd 1 Queen St", date="2024-01-01",
                    amount=20000.0, part="A", page=1)]
        a, b = d(rows, "geometry"), d(rows, "glm-ocr")
        doc, arb = merge(a, b)
        gold.stage(gold.candidates(doc, inv.check(doc), arb), gp)
        again = d([Row(n=None, donor="Acme Ltd, 1 Queen Street, Auckland",
                       date="2024-01-01", amount=20000.0, part="A", page=1)],
                  "reread")
        s = gold.score(again, gold.load(gp), tier=gold.AGREED)
        assert s["correct"] == s["pins"] and s["missing"] == 0


def test_a_re_read_that_loses_the_donor_reads_as_missing_not_wrong():
    """Under-claiming is the right failure: an unmatched pin is not evidence
    that the value was wrong."""
    import tempfile as tf
    with tf.TemporaryDirectory() as td:
        gp = pathlib.Path(td) / "g.jsonl"
        rows = [Row(n=None, donor="Acme Ltd 1 Queen St", date="2024-01-01",
                    amount=20000.0, part="A", page=1)]
        a, b = d(rows, "geometry"), d(rows, "glm-ocr")
        doc, arb = merge(a, b)
        gold.stage(gold.candidates(doc, inv.check(doc), arb), gp)
        garbled = d([Row(n=None, donor="Rcme Ltd 1 Queen St",
                         date="2024-01-01", amount=20000.0, part="A", page=1)],
                    "reread")
        s = gold.score(garbled, gold.load(gp), tier=gold.AGREED)
        assert s["missing"] == s["pins"] and s["wrong"] == 0


def test_a_finding_about_one_donor_does_not_condemn_the_whole_part():
    """2026-09-23, found twice: a finding that names no ROW was treated as
    naming the whole part. `donor_aggregate_above_threshold` is about one
    donor, and on a form printing no row numbers it can name no rows — so six
    whole documents yielded no gold at all."""
    rows = [Row(n=None, donor="Tiny Co 9 Small St", date="2024-01-01",
                amount=900.0, part="A", page=1),
            Row(n=None, donor="Big Co 1 Large Ave", date="2024-01-01",
                amount=50000.0, part="A", page=1)]
    a, b = d(rows, "geometry"), d(rows, "glm-ocr")
    rep = inv.check(a)
    hit = [f for f in rep.findings if f.rule == "donor_aggregate_above_threshold"]
    assert hit and hit[0].rows == () and hit[0].donors, \
        "the finding must name the donor it is about"
    doc, arb = merge(a, b)
    cands = gold.candidates(doc, inv.check(doc), arb)
    assert cands, "the donor above the threshold is still gold"
    assert all("tinyco" not in c.addr for c in cands)
    assert any("bigco" in c.addr for c in cands)


def test_a_dispute_on_an_unnumbered_row_does_not_condemn_its_part():
    """2026-09-23, the one that actually mattered. A dispute was recorded as
    (part, n); on an unnumbered row n is None, and the very next check read
    (part, None) as 'the whole part is in doubt'. Every document read whole
    produced zero gold. Two meanings of None is one too many."""
    ok = Row(n=None, donor="Clean Co 1 A St", date="2024-01-01",
             amount=50000.0, part="A", page=1)
    bad = Row(n=None, donor="Muddy Co 2 B St", date="2024-01-01",
              amount=40000.0, part="A", page=1)
    a = d([ok, bad], "geometry")
    b = d([ok, dataclasses.replace(bad, amount=99.0)], "glm-ocr")
    arb = arbitrate([a, b])
    assert any(x.n is None for x in arb.disputes), "the dispute has no number"
    doc2, _ = merge(a, b)
    cands = gold.candidates(doc2, inv.check(doc2), arb)
    assert any("cleanco" in c.addr for c in cands), \
        "the undisputed row in the same part is still gold"
    assert all("muddyco" not in c.addr for c in cands)


# ---------------------------------------------------------------------------
# THE SECOND CLASS (Arthur 2026-09-23: "do this — it is the change that makes
# your time worth more than the calibration").
#
# `candidates` offers only cells both readers agreed on with no rule against
# them, which is by construction the cells we were already right about.
# Measured on the live set the day this was written: 592 candidates, of which
# 359 sat in a part that already reconciled, 168 in a part with no stated
# total, and NONE in a part that failed. `contested` is the other two kinds.
# ---------------------------------------------------------------------------

def test_a_disputed_cell_is_offered_with_BOTH_readings():
    """The whole point: the person chooses, not transcribes. A dispute shown
    without both values is a worse question than no question."""
    a = d([r(1, amount=20000.0)], "geometry")
    b = d([r(1, amount=26000.0)], "glm-ocr")
    doc, arb = merge(a, b)
    con = gold.contested(doc, inv.check(doc), arb)
    amt = [c for c in con if c.field == "amount" and c.kind == gold.DISPUTED]
    assert amt, "a disputed amount must be offered"
    vals = {v for _, v in amt[0].options}
    assert vals == {20000.0, 26000.0}
    assert "disagree" in amt[0].why


def test_a_contested_cell_arrives_with_no_verdict_on_it():
    """It is a QUESTION, not gold. The tier is the verdict and these have had
    none, so they come back at the same tier a `candidates` row does."""
    a = d([r(1, amount=20000.0)], "geometry")
    b = d([r(1, amount=26000.0)], "glm-ocr")
    doc, arb = merge(a, b)
    con = gold.contested(doc, inv.check(doc), arb)
    assert con and all(c.tier == gold.AGREED for c in con)
    assert all(c.by == "" for c in con)


def test_the_rule_that_objected_travels_with_the_cell():
    """A person asked to look at a row must be told what is wrong with it
    first, or the question costs more than the answer is worth."""
    rows = [r(1), r(2, donor="Beta Ltd 2 High St")]
    a = d(rows, "geometry", stated_totals={"A": 999.0})
    b = d(rows, "glm-ocr")
    doc, arb = merge(a, b)
    rep = inv.check(doc)
    con = gold.contested(doc, rep, arb)
    imp = [c for c in con if c.kind == gold.IMPLICATED]
    assert imp, "an implicated row must be offered"
    assert any("sum_matches_stated_total" in c.why for c in imp)
    assert all(c.why for c in imp), "an implicated cell with no reason is a bare demand"


def test_a_rule_naming_a_row_that_was_never_READ_offers_nothing():
    """`row_numbers_complete` on a document holding 1, 2 and 4 names row 3 —
    which does not exist, so there is no cell to put in front of anyone. It
    must NOT fall back to condemning the part: that would offer rows 1, 2 and
    4, which `candidates` is already offering as agreed, and the person would
    be asked the same question twice with two different framings."""
    rows = [r(1), r(2, donor="Beta Ltd 2 High St"), r(4, donor="Cee Ltd 3 X")]
    a, b = d(rows, "geometry"), d(rows, "glm-ocr")
    doc, arb = merge(a, b)
    rep = inv.check(doc)
    assert any(f.rule == "row_numbers_complete" for f in rep.findings)
    assert not [c for c in gold.contested(doc, rep, arb) if c.kind == gold.IMPLICATED]
    assert gold.candidates(doc, rep, arb), "the readable rows stay in the agreed class"


def test_the_two_classes_never_offer_the_same_cell():
    """Agreed and contested must partition, or a person is asked to confirm a
    cell the machine has already flagged — which is the confusion the two
    classes exist to end."""
    rows = [r(1), r(2, donor="Beta Ltd 2 High St"), r(4, donor="Cee Ltd 3 X")]
    a, b = d(rows, "geometry"), d(rows, "glm-ocr")
    doc, arb = merge(a, b)
    rep = inv.check(doc)
    ids_agreed = {c.id for c in gold.candidates(doc, rep, arb)}
    ids_contested = {c.id for c in gold.contested(doc, rep, arb)}
    assert not (ids_agreed & ids_contested)


def test_one_finding_cannot_flood_the_queue_with_a_whole_part():
    """`sum_matches_stated_total` says 'some row in this part is wrong' and
    names none, so it implicates every row in it. Offering sixty rows is the
    same as offering none: the biggest money goes first, and the rest wait."""
    rows = [r(i, amount=1000.0 * i, donor=f"D{i} Ltd 1 X") for i in range(1, 30)]
    a, b = d(rows, "geometry", stated_totals={"A": 1.0}), d(rows, "glm-ocr")
    doc, arb = merge(a, b)
    rep = inv.check(doc)
    assert any(f.rule == "sum_matches_stated_total" for f in rep.fails)
    con = gold.contested(doc, rep, arb, per_finding=5)
    rows_offered = {(c.part, c.addr) for c in con if c.kind == gold.IMPLICATED}
    assert len(rows_offered) <= 5
    # and they are the biggest, because that is where being wrong costs most
    amounts = sorted((c.value for c in con
                      if c.kind == gold.IMPLICATED and c.field == "amount"),
                     reverse=True)
    assert amounts and amounts[0] == 29000.0


def test_a_donor_cell_is_never_offered_for_a_part_that_names_no_donors():
    """Part G is a banded aggregate — there is no donor to read, so asking
    about one is asking a person to invent it."""
    rows = [r(1, part="G", donor=None), r(2, part="G", donor=None)]
    a, b = d(rows, "geometry", stated_totals={"G": 1.0}), d(rows, "glm-ocr")
    doc, arb = merge(a, b)
    con = gold.contested(doc, inv.check(doc), arb)
    assert all(c.field != "donor" for c in con)


def test_a_dispute_the_trust_policy_already_settles_is_not_a_question():
    """`TRUSTED_FOR` sends donor to the transcriber and date to either; only
    AMOUNT is trusted to neither. Asking a person about a donor disagreement
    spends their attention on a decision the estate made on purpose — and on
    Green 2023, 132 disputed cells reduced to the amounts alone once this held."""
    # geometry is the one that returns an address fragment; the transcriber is
    # trusted for the donor precisely because it does not. (Written the other
    # way round at first, which made the merged donor a bare street address —
    # now a C423 finding, and rightly refused.)
    a = d([r(1, amount=20000.0, donor="1 Queen St", date="2024-01-01")], "geometry")
    b = d([r(1, amount=26000.0, donor="Acme Ltd 1 Queen St", date="2024-02-02")], "glm-ocr")
    doc, arb = merge(a, b)
    con = gold.contested(doc, inv.check(doc), arb)
    disputed = [c for c in con if c.kind == gold.DISPUTED]
    assert disputed, "the amount disagreement is a real question"
    assert {c.field for c in disputed} == {"amount"}


# --- C423: a row that did not parse is a finding, not a candidate ----------

def _doc_with_unparsed_rows():
    from support.docread.rows import Document, Row
    return Document("t", (
        Row(n=1, donor="Amount of contribution (including GST)", amount=0.0,
            date="2023-01-01", part="A", page=8, agreed=True),
        Row(n=2, donor="No", amount=20000.0, date="2023-02-01", part="A",
            page=2, agreed=True),
        Row(n=3, donor="", amount=31050.47, date="2023-03-01", part="A",
            page=7, agreed=True),
        Row(n=4, donor="Marama M Davidson C/O GPANZ", amount=31050.47,
            date="2023-04-01", part="A", page=7, agreed=True),
    ), year=2023)


def test_an_unparsed_row_is_never_offered_as_gold():
    """C423. Arthur was asked to confirm the amount on a row whose donor is the
    money column's own caption. A `confirmed` verdict there would make the
    reader's failure into ground truth, which is the one thing a gold set must
    not do."""
    from support.docread import gold as g
    from support.docread.invariants import check
    from support.docread.arbitrate import Arbitration
    doc = _doc_with_unparsed_rows()
    rep = check(doc)
    arb = Arbitration(stem="t", agreed=tuple(doc.rows), disputes=(), readers=("a", "b"))
    offered = list(g.candidates(doc, rep, arb)) + list(g.contested(doc, rep, arb))
    bad = [c for c in offered if c.addr in ("n=1", "n=2", "n=3")]
    assert not bad, f"unparsed rows were offered: {[(c.addr, c.field) for c in bad]}"


def test_the_row_that_did_parse_is_still_reachable():
    """The refusal is narrow: it removes the rows that provably did not parse
    and nothing else. A class that swallowed the good rows with the bad would
    be a worse bug than the one it fixes."""
    from support.docread import gold as g
    from support.docread.invariants import check
    from support.docread.arbitrate import Arbitration
    doc = _doc_with_unparsed_rows()
    rep = check(doc)
    arb = Arbitration(stem="t", agreed=tuple(doc.rows), disputes=(), readers=("a", "b"))
    offered = list(g.candidates(doc, rep, arb)) + list(g.contested(doc, rep, arb))
    assert any("davidson" in c.addr or c.addr == "n=4" for c in offered), \
        f"the one well-formed row vanished too: {[c.addr for c in offered]}"


def test_the_defect_is_named_so_the_reader_can_be_fixed():
    from support.docread.invariants import check
    rep = check(_doc_with_unparsed_rows())
    whys = {f.detail for f in rep.fails if f.rule == "rows_parse_cleanly"}
    assert any("column header" in w for w in whys)
    assert any("Yes/No" in w for w in whys)
    assert any("no donor was read" in w for w in whys)


def test_a_bare_street_address_is_not_a_donor():
    """C307/C423. Green 2023 p5 filed `11A Moody Avenue Whangarei` as a donor;
    the printed name is Nicholas R Karlovsky. The name was lost and the address
    kept, which is geometry's own failure mode — and the cell proves it, so it
    is a finding rather than an abstention."""
    from support.docread.rows import malformed, Row
    assert malformed(Row(donor="11A Moody Avenue Whangarei", part="A"))
    assert malformed(Row(donor="6 Cremorne Street Auckland", part="A"))


def test_a_company_whose_name_opens_with_a_number_is_left_alone():
    """The rule needs BOTH a house number and a street word, so a real donor
    is never lost to it. Losing `3M New Zealand` to a tidy-up would be a worse
    bug than the one the rule fixes."""
    from support.docread.rows import malformed, Row
    assert malformed(Row(donor="3M New Zealand Ltd", part="A")) is None
    assert malformed(Row(donor="2degrees Mobile Limited", part="A")) is None
    assert malformed(Row(donor="Stefan Sunde 24 Halston", part="A")) is None


# ---- the third answer (Arthur 2026-09-23) ---------------------------------
# "make sure you adjust the affected rejections to abstentions." All seven of
# his gold rejections carried a comment and every one said he could not judge
# the cell, not that the reader was wrong.

def _staged(tmp_path):
    p = tmp_path / "gold.jsonl"
    g = gold.GoldRow("Stem", "A", 1, "amount", 100.0, gold.AGREED,
                     addr="d=x#0", kind=gold.DISPUTED)
    gold.stage([g], p)
    return p, g


def test_an_abstention_is_a_verdict_a_person_can_give(tmp_path):
    p, g = _staged(tmp_path)
    out = gold.assess(g.id, gold.ABSTAINED, p, by="arthur",
                      note="too many dates on the page")
    assert out.tier == gold.ABSTAINED
    assert gold.load(p)[g.id].tier == gold.ABSTAINED


def test_an_abstention_says_which_verdict_it_replaced(tmp_path):
    """The ledger is append-only, so a changed mind is a new line — and a
    reader of the FILE ALONE has to be able to tell a first answer from a
    second. These seven lines were written by me on his instruction."""
    p, g = _staged(tmp_path)
    gold.assess(g.id, gold.REJECTED, p, by="arthur", note="blended cells")
    out = gold.assess(g.id, gold.ABSTAINED, p, by="arthur", note="blended cells")
    assert out.supersedes == gold.REJECTED
    # a first answer supersedes nothing
    p2, g2 = _staged(tmp_path / "second")
    assert gold.assess(g2.id, gold.ABSTAINED, p2).supersedes == ""


def test_an_abstention_keeps_the_readers_value_and_the_persons_words(tmp_path):
    p, g = _staged(tmp_path)
    out = gold.assess(g.id, gold.ABSTAINED, p, by="arthur", note="blended cells",
                      value=999.0)
    assert out.value == 100.0, "an abstention decides nothing, least of all the value"
    assert out.note == "blended cells" and out.by == "arthur"


def test_an_abstention_is_scored_neither_right_nor_wrong(tmp_path):
    """The whole point. Counted as errors, his seven put the implicated class
    at 13 of 19; set aside, 13 of 13. A person who could not tell has said
    nothing about whether the reader was right."""
    p, g = _staged(tmp_path)
    gold.assess(g.id, gold.ABSTAINED, p, by="arthur", note="cannot judge")
    pinned = [r for r in gold.load(p).values()
              if r.tier in (gold.AGREED, gold.CONFIRMED)]
    assert pinned == [], "an abstained cell must pin nothing under any tier"


def test_the_machine_still_cannot_write_a_human_verdict(tmp_path):
    p, g = _staged(tmp_path)
    for bad in ("agreed", "maybe", ""):
        try:
            gold.assess(g.id, bad, p)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} was accepted as a person's verdict")


# ---- C424: the donor cell holds the address column ------------------------
# Arthur's own words on the scans: "this runs on into the cell below it",
# "blended cells". Measured on the gold set the day it was fixed: 192
# address-shaped donor cells across EIGHT documents, 56 of them in Green 2023
# alone, and 171 of the 192 staged at tier AGREED — both readers returned the
# address, agreed with each other, and the cell was offered as CALIBRATION.

def _donor(v, part="A"):
    from support.docread.rows import Row, malformed
    return malformed(Row(part=part, n=1, donor=v, amount=1.0, date=None))


def test_an_address_is_refused_whatever_it_begins_with():
    """Four shapes, all from Green 2023, none of which the first guard caught
    because it required the cell to START with a bare house number."""
    assert _donor("Flat 1 86 McLauchlan Street Blenheim")
    assert _donor("|30 Findlay Street Mangawhai")
    assert _donor("2/21 Emmett Street Auckland")
    assert _donor("161 Barnard Street Wellington")


def test_a_blend_says_that_it_is_a_blend():
    """The stronger statement, and the one that explains where the money
    went: several rows' addresses in one cell."""
    for v in ("|30 Findlay Street Mangawhai |28 Landing Road Kerikeri",
              "C/O GPANZLS / 108 The Terrace 161 Barnard Street",
              "6 Cremorne Street Auckland _75 Godden Cresent Auckland "
              "348 Oriental Parade Wellington"):
        assert _donor(v) == "the donor cell has run several rows' addresses together", v


def test_a_real_donor_name_carrying_a_street_word_is_not_refused():
    """The measured cost, and it is zero: run over all 1,368 distinct filed
    donor names in the register, the widened guard refuses TWO, and both are
    genuinely addresses with no name. A company may carry one street word in
    its name; the blend rule needs two street words AND two house numbers."""
    for v in ("Queen Street Investments Limited", "Grove Road Holdings Ltd",
              "St John Ambulance", "Christopher Place", "Trevor Farmer",
              "Weft Knitting Company", "Rank Group Limited"):
        assert _donor(v) is None, v


def test_an_address_in_a_part_that_names_no_donors_is_left_alone():
    """Parts outside NAMED_DONOR_PARTS do not name their donors, so a cell
    there is not claiming to be one."""
    assert _donor("161 Barnard Street Wellington", part="G") is None


def test_a_confirmed_address_is_not_ground_truth(tmp_path):
    """The 15 that got through. A person was asked "is this what the form
    says" about text that IS on the form — just not in that column — and said
    yes. The verdict stands in the ledger (ruling 340: a person's word outlives
    our fixes); what is withdrawn is its use as ground truth, because a gold
    cell asserting a donor named `161 Barnard Street Wellington` would mark a
    correct reader wrong for ever after."""
    from support.docread.rows import Document, Row
    GoldRow = gold.GoldRow
    good = GoldRow("S", "A", 1, "donor", "Trevor Farmer", gold.CONFIRMED,
                   addr=gold.address(1, "Trevor Farmer", 0))
    bad = GoldRow("S", "A", 2, "donor", "161 Barnard Street Wellington",
                  gold.CONFIRMED,
                  addr=gold.address(2, "161 Barnard Street Wellington", 0))
    pins = {g.id: g for g in (good, bad)}
    doc = Document(stem="S", rows=[
        Row(part="A", n=1, donor="Trevor Farmer", amount=1.0, date=None),
        Row(part="A", n=2, donor="161 Barnard Street Wellington", amount=2.0, date=None)])
    out = gold.score(doc, pins, tier=gold.CONFIRMED)
    assert out["withdrawn_malformed"] == 1
    assert out["pins"] == 1 and out["correct"] == 1, out


def test_a_cell_that_names_its_donor_is_not_a_blend():
    """Corrected the same night it was written. The blend rule fired on
    `Julie Anne Genter, 16 Chatham Street, 16 Chatham Street, Wellington, 6`
    — two street words, two house numbers, and the donor's name right at the
    front — and refusing that loses a real donor, which is the opposite of
    what the guard is for. It is also C426's own premise: the form prints the
    address BESIDE the name, so what stands before the first digit is a name."""
    assert _donor("Julie Anne Genter, 16 Chatham Street, 16 Chatham Street, Wellington, 6") is None
    assert _donor("Robert John Wares, 10a Jollie Street, Marybank, Nelson") is None
    # one leading word is as likely to be a unit word as a given name
    assert _donor("Flat 1 86 McLauchlan Street Blenheim")
    # and a genuine blend, with no name in front, is still refused
    assert _donor("|30 Findlay Street Mangawhai |28 Landing Road Kerikeri")
