"""The queue's arithmetic, its append-only discipline, and Arthur's priority."""
import sys, pathlib, tempfile

import pytest
from support.docread import queue as q
from support.docread import invariants as inv
from support.docread.arbitrate import arbitrate
from support.docread.rows import Document, Row


@pytest.fixture
def path():
    with tempfile.TemporaryDirectory() as td:
        yield pathlib.Path(td) / "queue.jsonl"


def item(**kw):
    kw.setdefault("id", q.item_id("s", "invariant", "A", 1, "r", "d"))
    kw.setdefault("stem", "s"); kw.setdefault("kind", "invariant")
    kw.setdefault("detail", "d")
    return q.Item(**kw)


def test_recent_years_outrank_older_ones():
    """Arthur, 2026-09-23: focus on recent years, deprioritise pre-2010."""
    now = item(year=2024, amount=1000.0)
    old = item(year=2005, amount=1000.0, id="b")
    assert q.priority(now) > q.priority(old)


def test_a_contradiction_outranks_a_doubt_at_the_same_age():
    hard = item(year=2024, severity="fail", amount=100.0)
    soft = item(year=2024, severity="flag", amount=100.0, id="b")
    assert q.priority(hard) > q.priority(soft)


def test_more_money_outranks_less_but_not_linearly():
    big = item(year=2024, amount=1_000_000.0)
    small = item(year=2024, amount=1_000.0, id="b")
    assert q.priority(big) > q.priority(small)
    assert q.priority(big) < 3 * q.priority(small)


def test_a_pre_2010_failure_still_outranks_a_recent_trifle_only_if_it_should():
    """The policy is a weighting, not a cutoff: old documents are still in the
    queue, they simply sort last."""
    old = item(year=2005, severity="fail", amount=1_000_000.0)
    assert q.priority(old) > 0


def test_an_item_id_is_stable_across_reads():
    a = q.item_id("stem", "invariant", "A", 7, "rule", "detail")
    b = q.item_id("stem", "invariant", "A", 7, "rule", "detail")
    assert a == b and len(a) == 16


def test_re_reading_a_document_does_not_re_queue_what_is_resolved(path):
    it = item(year=2024)
    assert q.enqueue([it], path) == 1
    q.resolve(it.id, q.ACCEPTED, path, by="arthur")
    assert q.enqueue([it], path) == 0
    assert q.open_items(path) == []


def test_a_resolution_never_edits_the_item(path):
    it = item(year=2024)
    q.enqueue([it], path)
    q.resolve(it.id, q.CORRECTED, path, value=50000.0, by="arthur")
    assert len(q.load_items(path)) == 1, "the item row is untouched"
    assert q.resolutions(path)[it.id].value == 50000.0


def test_a_later_resolution_corrects_an_earlier_one(path):
    it = item(year=2024)
    q.enqueue([it], path)
    q.resolve(it.id, q.ACCEPTED, path, by="a")
    q.resolve(it.id, q.CORRECTED, path, value=1.0, by="b")
    r = q.resolutions(path)[it.id]
    assert r.verdict == q.CORRECTED and r.by == "b"
    assert len(list(q._rows(path))) == 3, "nothing was overwritten"


def test_an_invented_verdict_is_refused(path):
    with pytest.raises(ValueError):
        q.resolve("x", "probably fine", path)


def test_open_items_come_back_most_urgent_first(path):
    """Both years are inside the 2019 window — a pre-window item is not
    ordered last, it is not asked at all (see `withheld` below)."""
    q.enqueue([item(year=2019, id="old"), item(year=2024, id="new")], path)
    assert [i.id for i in q.open_items(path)] == ["new", "old"]


def test_a_finding_becomes_an_item_carrying_its_rule(path):
    doc = Document("s", (Row(n=1, part="A", amount=None, donor="X Ltd 1 A"),),
                   year=2024)
    items = q.from_report(doc, inv.check(doc))
    assert any(i.rule == "every_row_has_an_amount" and i.severity == "fail"
               for i in items)


def test_a_dispute_becomes_an_item_carrying_both_readings():
    a = Document("s", (Row(n=1, part="A", donor="X Ltd 1 A", amount=100.0,
                           bbox=(0, 10, 100, 40), dpi=300, page=3),),
                 reader="geometry")
    b = Document("s", (Row(n=1, part="A", donor="X Ltd 1 A", amount=900.0),),
                 reader="glm-ocr")
    items = q.from_arbitration(arbitrate([a, b]), year=2024)
    vals = dict(items[0].values)
    assert vals == {"geometry": 100.0, "glm-ocr": 900.0}
    assert items[0].bbox == (0, 10, 100, 40) and items[0].page == 3, \
        "a reviewer must be shown the pixels, not sent hunting for the page"


def test_a_corrupt_line_does_not_take_the_queue_down(path):
    q.enqueue([item(year=2024)], path)
    with path.open("a") as fh:
        fh.write("{not json at all\n\n")
    assert len(q.load_items(path)) == 1


def test_the_summary_counts_documents_not_only_items(path):
    q.enqueue([item(stem="a", id="1"), item(stem="b", id="2")], path)
    assert q.summary(path)["documents"] == 2


# --- what is no longer asked (2026-09-26) -----------------------------------

def test_an_item_before_the_window_is_not_asked_and_says_why():
    """Ruling 347: for Follow the Money, nothing before 2019 exists. The item
    is still written — it is a question that is never PUT."""
    assert q.withheld(item(year=2014, amount=9e6)) == "before 2019 (ruling 347)"
    assert q.withheld(item(year=2019)) is None


def test_a_disagreement_with_a_retired_reader_is_not_asked():
    """The question a dispute asks is which of two readers is right. One of
    them was retired on 2026-09-25, so it has no answer to give."""
    dead = item(kind="dispute", rule="reader_disagreement", year=2023,
                values=(("geometry", "A"), ("glm-ocr", "B")))
    live = item(kind="dispute", rule="reader_disagreement", year=2023, id="b",
                values=(("glm-ocr", "A"), ("glm-ocr-2", "B")))
    assert q.withheld(dead) == "disagreement with a retired reader (geometry)"
    assert q.withheld(live) is None


def test_a_rule_that_needs_two_readers_is_not_asked_when_there_is_one():
    held = item(kind="dispute", rule="seen_by_one_reader", year=2023)
    assert q.withheld(held) == "seen_by_one_reader needs two readers, and there is one"


def test_withholding_hides_the_question_and_keeps_the_row(path):
    """Quarantine, never delete: `everything=True` brings it straight back, so
    lifting the window or re-hiring a reader costs nothing."""
    q.enqueue([item(year=2014, id="old"), item(year=2023, id="new")], path)
    assert [i.id for i in q.open_items(path)] == ["new"]
    assert {i.id for i in q.open_items(path, everything=True)} == {"old", "new"}
    assert {i.id for i in q.load_items(path)} == {"old", "new"}


def test_summary_says_how_much_it_is_holding_back_and_under_which_rule(path):
    q.enqueue([item(year=2014, id="a"), item(year=2013, id="b"),
               item(year=2023, id="c")], path)
    s = q.summary(path)
    assert s["open"] == 1 and s["withheld_total"] == 2
    assert s["withheld"] == {"before 2019 (ruling 347)": 2}
    assert s["documents_asked"] == 1


def test_one_question_written_twice_is_one_question(path):
    """The id is keyed on what is being asked, so a second run over the same
    corpus re-states rather than adds. The live queue held 29,528 rows for
    15,230 questions and the review page would have shown each one twice."""
    q.append(path, [{"row": "item", **item(year=2023, id="x", detail="first").to_json()}])
    q.append(path, [{"row": "item", **item(year=2023, id="x", detail="second").to_json()}])
    got = q.load_items(path)
    assert len(got) == 1 and got[0].detail == "second"


def test_a_question_asked_under_a_repealed_threshold_is_not_put():
    """The detail quotes the number it judged against, so the queue can tell
    without re-reading the document. 1,150 items in the live queue accused
    donors of sitting below a threshold that stopped applying on
    1 January 2023."""
    stale = item(rule="donor_aggregate_above_threshold", year=2023,
                 detail="part A: 'Alpha' aggregates to $6,000.00, at or below "
                        "the $15,000 threshold that requires the disclosure")
    live = item(rule="donor_aggregate_above_threshold", year=2023, id="b",
                detail="part A: 'Alpha' aggregates to $900.00, at or below "
                       "the $5,000 threshold that requires the disclosure")
    assert q.withheld(stale) == ("raised under a superseded threshold "
                                 "($15,000; 2023's is $5,000)")
    assert q.withheld(live) is None
