"""The open gold queue: what is still a question, and why the rest is not.

These tests exist because the predicate moved out of a page (2026-09-28) so a
second consumer — the document review bridge — could measure through the same
one. A moved predicate that quietly stops withdrawing something does not fail
loudly: it puts unanswerable questions in front of a person and looks like it
is working. So every withdrawal rule is pinned HERE, at the predicate, not at
whichever surface happens to draw it.
"""
import json
import pathlib
import sys
import tempfile

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]

from support.docread import gold as G                   # noqa: E402
from support.docread import gold_queue as Q             # noqa: E402


@pytest.fixture
def paths():
    with tempfile.TemporaryDirectory() as td:
        yield pathlib.Path(td) / "gold.jsonl", pathlib.Path(td) / "corpus.jsonl"


def row(stem="Doc-2025", part="A", n=1, field="amount", value=100.0,
        tier=G.AGREED, kind=None, **kw):
    return G.GoldRow(stem, part, n, field, value, tier,
                     addr=kw.pop("addr", f"n={n}"), page=kw.pop("page", 2),
                     kind=kind, **kw)


def corpus(cpath, stem="Doc-2025", **kw):
    rec = {"stem": stem, "year": 2025, "kind": "party"}
    rec.update(kw)
    cpath.write_text(json.dumps(rec) + "\n")
    return Q.corpus_index(cpath)


# ---- the corpus index ---------------------------------------------------

def test_a_missing_corpus_file_is_an_empty_index_not_a_crash(paths):
    _, cpath = paths
    assert Q.corpus_index(cpath) == {}


def test_a_half_written_last_line_loses_itself_and_not_the_file(paths):
    """This file is appended to by a running job. A reader that throws on a
    truncated final line takes the whole surface down with it."""
    _, cpath = paths
    cpath.write_text(json.dumps({"stem": "A", "year": 2025}) + "\n{\"stem\": \"B\"")
    idx = Q.corpus_index(cpath)
    assert "A" in idx and "B" not in idx


def test_a_record_with_no_stem_is_not_indexed_under_nothing(paths):
    _, cpath = paths
    cpath.write_text(json.dumps({"year": 2025}) + "\n")
    assert Q.corpus_index(cpath) == {}


# ---- what is still a question -------------------------------------------

def test_an_unanswered_candidate_is_a_question(paths):
    gpath, cpath = paths
    G.stage([row()], gpath)
    q = Q.open_queue(gpath, corpus(cpath))
    assert len(q.rows) == 1 and q.counts["agreed"] == 1


def test_status_selects_the_verdict_axis(paths):
    gpath, cpath = paths
    G.stage([row(n=1), row(n=2)], gpath)
    rows = list(G.load(gpath).values())
    G.assess(rows[0].id, G.CONFIRMED, gpath, by="arthur")
    q = Q.open_queue(gpath, corpus(cpath), status=G.CONFIRMED)
    assert [r.tier for r in q.rows] == [G.CONFIRMED]
    assert q.counts["assessed"] == 1


def test_kind_selects_why_a_cell_was_offered(paths):
    """A cell offered because a rule objected and a cell offered because both
    readers agreed are different questions and must not share a queue."""
    gpath, cpath = paths
    G.stage([row(n=1), row(n=2, kind=G.IMPLICATED, why="a rule said so",
                           gen=G.CONTESTED_GEN)], gpath)
    q = Q.open_queue(gpath, corpus(cpath), kind=G.IMPLICATED)
    assert [r.n for r in q.rows] == [2]
    assert q.counts["open_implicated"] == 1 and q.counts["open_agreed"] == 1


def test_stem_narrows_to_one_document(paths):
    gpath, cpath = paths
    G.stage([row(stem="A-2025"), row(stem="B-2025")], gpath)
    q = Q.open_queue(gpath, corpus(cpath), stem="B-2025")
    assert {r.stem for r in q.rows} == {"B-2025"}


# ---- the withdrawals, each for its own reason ---------------------------

def test_a_part_that_reads_more_than_the_party_declared_is_withdrawn(paths):
    """Under-reading a part is honest. OVER-reading it is impossible, so the
    reading is wrong before the cell is and no answer could be right."""
    gpath, cpath = paths
    G.stage([row(kind=G.IMPLICATED, why="w", gen=G.CONTESTED_GEN)], gpath)
    idx = corpus(cpath, reconcile={"A": {"stated": 100.0, "read": 9000.0,
                                         "ok": False}})
    q = Q.open_queue(gpath, idx, kind=G.IMPLICATED)
    assert q.rows == [] and q.withdrawn_over_read == 1
    assert q.counts["withdrawn_over_read"] == 1


def test_an_under_read_part_is_still_a_question(paths):
    """The mirror of the rule above, and the reason it is not just 'ok is
    False': a part that reads LESS than declared is exactly the case a person
    can resolve."""
    gpath, cpath = paths
    G.stage([row(kind=G.IMPLICATED, why="w", gen=G.CONTESTED_GEN)], gpath)
    idx = corpus(cpath, reconcile={"A": {"stated": 9000.0, "read": 100.0,
                                         "ok": False}})
    q = Q.open_queue(gpath, idx, kind=G.IMPLICATED)
    assert len(q.rows) == 1 and q.withdrawn_over_read == 0


def test_an_agreed_cell_is_never_withdrawn_for_its_parts_arithmetic(paths):
    """The over-read rule is about CONTESTED classes. The agreed class is a
    rate estimator over cells no rule objected to; withdrawing from it by a
    part-level fault would bias the rate it exists to measure."""
    gpath, cpath = paths
    G.stage([row()], gpath)
    idx = corpus(cpath, reconcile={"A": {"stated": 100.0, "read": 9000.0,
                                         "ok": False}})
    q = Q.open_queue(gpath, idx)
    assert len(q.rows) == 1 and q.withdrawn_over_read == 0


def test_a_donor_cell_the_reader_malformed_is_not_a_question(paths):
    """C424: no answer to it can be right, so it is not asked."""
    gpath, cpath = paths
    G.stage([row(field="donor", value="12 Example Street, Auckland")], gpath)
    q = Q.open_queue(gpath, corpus(cpath))
    assert q.rows == [] and q.withdrawn_malformed == 1


def test_a_verdict_exempts_a_malformed_cell_from_withdrawal(paths):
    """A verdict is a person's word, not a generation of ours."""
    gpath, cpath = paths
    G.stage([row(field="donor", value="12 Example Street, Auckland")], gpath)
    rid = next(iter(G.load(gpath).values())).id
    G.assess(rid, G.CONFIRMED, gpath, by="arthur")
    q = Q.open_queue(gpath, corpus(cpath), status=G.CONFIRMED)
    assert len(q.rows) == 1 and q.withdrawn_malformed == 0


def test_a_contested_cell_from_a_reader_we_have_since_corrected_is_withdrawn(paths):
    """C422: the ledger is append-only, so the withdrawal happens at read
    time — an unanswered contested cell is served only if the code that made
    it is the code we still stand behind."""
    gpath, cpath = paths
    G.stage([row(kind=G.IMPLICATED, why="w", gen="older-generation")], gpath)
    q = Q.open_queue(gpath, corpus(cpath), kind=G.IMPLICATED)
    assert q.rows == []


def test_a_verdict_about_a_reading_expires_when_the_reading_moves(paths):
    """C430(a). An abstention is a sentence about the evidence; when the
    evidence changes it is a NEW question, counted as reopened so a question
    coming back never reads as the surface forgetting an answer."""
    gpath, cpath = paths
    G.stage([row(value=100.0)], gpath)
    rid = next(iter(G.load(gpath).values())).id
    G.assess(rid, G.ABSTAINED, gpath, by="arthur", note="cannot tell")
    G.stage([row(value=222.0)], gpath)          # the reader read it again
    q = Q.open_queue(gpath, corpus(cpath))
    assert q.reopened == 1 and q.counts["reopened"] == 1
    assert [r.tier for r in q.rows] == [G.AGREED]


def test_an_abstention_stands_while_the_reading_has_not_moved(paths):
    """The other half of C430(a), and the half that makes it a rule rather
    than a re-ask: a cell a person could not judge is not put back in front
    of them until something they were shown has actually changed."""
    gpath, cpath = paths
    G.stage([row(value=100.0)], gpath)
    rid = next(iter(G.load(gpath).values())).id
    G.assess(rid, G.ABSTAINED, gpath, by="arthur", note="cannot tell")
    q = Q.open_queue(gpath, corpus(cpath))
    assert q.reopened == 0
    assert q.rows == [], "an abstention withdraws the cell until the reading moves"


def test_a_confirmation_never_reopens(paths):
    """It says what THE PAGE says, which no re-read can make untrue — and it
    is the only tier a correctness claim may be made against."""
    gpath, cpath = paths
    G.stage([row(value=100.0)], gpath)
    rid = next(iter(G.load(gpath).values())).id
    G.assess(rid, G.CONFIRMED, gpath, by="arthur")
    G.stage([row(value=222.0)], gpath)
    q = Q.open_queue(gpath, corpus(cpath))
    assert q.reopened == 0


# ---- the counts a surface quotes ---------------------------------------

def test_the_counts_name_the_documents_not_the_cells(paths):
    gpath, cpath = paths
    G.stage([row(stem="A-2025", n=1), row(stem="A-2025", n=2),
             row(stem="B-2025", n=1)], gpath)
    q = Q.open_queue(gpath, corpus(cpath))
    assert q.counts["agreed"] == 3 and q.counts["documents"] == 2


def test_an_abstention_is_counted_but_never_assessed(paths):
    """An abstention says something about the QUESTION, not the READING, so
    it must never be folded into an accuracy figure."""
    gpath, cpath = paths
    G.stage([row()], gpath)
    rid = next(iter(G.load(gpath).values())).id
    G.assess(rid, G.ABSTAINED, gpath, by="arthur", note="blended cells")
    q = Q.open_queue(gpath, corpus(cpath))
    assert q.counts["abstained"] == 1 and q.counts["assessed"] == 0


# ---- what a cell is worth ----------------------------------------------

def test_a_cells_stake_is_its_rows_amount_not_its_own_value(paths):
    """'Is this the right donor' on a $9.4m row is worth more than the same
    question on a $2,000 one, and the fields of one line want answering
    together — the person is already looking at that line of the scan."""
    rows = [row(field="amount", value=9_400_000.0),
            row(field="donor", value="Someone")]
    table = Q.stakes(rows)
    assert Q.stake_of(table, rows[1]) == 9_400_000.0


def test_a_row_with_no_readable_amount_stakes_zero_and_is_kept(paths):
    """Zero is a real answer, not a missing one: a rule still named the cell,
    so it ranks last rather than being dropped."""
    r = row(field="donor", value="Someone")
    assert Q.stake_of(Q.stakes([r]), r) == 0.0


def test_a_non_numeric_amount_never_becomes_a_stake(paths):
    r = row(field="amount", value="see attached")
    assert Q.stakes([r]) == {}


def test_two_readings_of_one_row_stake_the_larger(paths):
    rows = [row(field="amount", value=100.0), row(field="amount", value=250.0)]
    assert max(Q.stakes(rows).values()) == 250.0


# ---- C463: one printed row, written twice (2026-09-28) -----------------

def _pair(gpath, stem="Doc-2025", donor="Brendan Lindsay", date="2025-06-23",
          amount=50000.0, n=10, occ=0):
    """The same donation as the reader wrote it twice: once by its printed
    number, once by a donor key because the margin number was not recovered."""
    rows = []
    for addr, num in ((f"n={n}", n),
                      (f"d={donor.lower().replace(' ','')}#{occ}", None)):
        for field, value in (("donor", donor), ("date", date), ("amount", amount)):
            rows.append(G.GoldRow(stem, "A", num, field, value, G.AGREED,
                                  addr=addr, page=3, kind=G.IMPLICATED,
                                  why="sum_matches_stated_total: part A is short",
                                  gen=G.CONTESTED_GEN))
    G.stage(rows, gpath)
    return rows


def test_the_numberless_copy_of_a_printed_row_is_withdrawn(paths):
    """Arthur counted 38 entries where the queue said 49, and 80 where it said
    88. Answering both copies would count one donation as two."""
    gpath, cpath = paths
    _pair(gpath)
    q = Q.open_queue(gpath, corpus(cpath), kind=G.IMPLICATED)
    assert {r.addr for r in q.rows} == {"n=10"}
    assert q.withdrawn_twin == 3 and q.counts["withdrawn_twin"] == 3


def test_the_numbered_copy_is_the_one_kept(paths):
    """The printed number is the better address, and it is the one a person
    can find on the page."""
    gpath, cpath = paths
    _pair(gpath)
    q = Q.open_queue(gpath, corpus(cpath), kind=G.IMPLICATED)
    assert all(r.addr.startswith("n=") for r in q.rows)


def test_two_genuine_donations_of_one_amount_stay_two_rows(paths):
    """A donor may give the same amount twice. The match is on every field of
    the line, so a different DATE is a different donation."""
    gpath, cpath = paths
    _pair(gpath, date="2025-06-23", n=10, occ=0)
    _pair(gpath, date="2025-09-01", n=11, occ=1)
    q = Q.open_queue(gpath, corpus(cpath), kind=G.IMPLICATED)
    assert {r.addr for r in q.rows} == {"n=10", "n=11"}
    assert q.withdrawn_twin == 6


def test_a_numberless_row_with_no_numbered_twin_is_still_a_question(paths):
    """Whole parts print no row numbers at all. Withdrawing every numberless
    row would empty them — which is the failure `gold.address`'s own fallback
    exists to prevent."""
    gpath, cpath = paths
    G.stage([G.GoldRow("Doc-2025", "G", None, f, v, G.AGREED,
                       addr="d=someone#0", page=12, kind=G.IMPLICATED,
                       why="sum_matches_stated_total: part G is short",
                       gen=G.CONTESTED_GEN)
             for f, v in (("donor", "Someone"), ("amount", 900.0))], gpath)
    q = Q.open_queue(gpath, corpus(cpath), kind=G.IMPLICATED)
    assert len(q.rows) == 2 and q.withdrawn_twin == 0


def test_a_verdict_on_a_duplicate_is_kept_and_counted(paths):
    """A person's word stands. But a verdict on a duplicate is not a second
    confirmation, and an accuracy figure counting it twice overstates its own
    denominator — so it is counted, not silently folded in."""
    gpath, cpath = paths
    _pair(gpath)
    twin = next(r for r in G.load(gpath).values()
                if r.addr.startswith("d=") and r.field == "amount")
    G.assess(twin.id, G.CONFIRMED, gpath, by="arthur")
    q = Q.open_queue(gpath, corpus(cpath), status=G.CONFIRMED)
    assert [r.addr for r in q.rows] == [twin.addr]
    assert q.answered_twin == 1


def test_the_twin_rule_never_crosses_documents_or_parts(paths):
    """Two parties can have a donor of the same name giving the same amount on
    the same day, and one party can list a donor in Part A and Part G."""
    gpath, cpath = paths
    _pair(gpath, stem="A-2025", n=10)
    G.stage([G.GoldRow("B-2025", "A", None, f, v, G.AGREED,
                       addr="d=brendanlindsay#0", page=3, kind=G.IMPLICATED,
                       why="sum_matches_stated_total: part A is short",
                       gen=G.CONTESTED_GEN)
             for f, v in (("donor", "Brendan Lindsay"), ("date", "2025-06-23"),
                          ("amount", 50000.0))], gpath)
    idx = {"A-2025": {"stem": "A-2025"}, "B-2025": {"stem": "B-2025"}}
    q = Q.open_queue(gpath, idx, kind=G.IMPLICATED)
    assert {(r.stem, r.addr) for r in q.rows} == {
        ("A-2025", "n=10"), ("B-2025", "d=brendanlindsay#0")}
