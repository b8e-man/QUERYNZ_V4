"""The rows stage and the level comparison: pure functions over the text
reader's rows and the keys; no model, no file."""
from support.trials import score

KEY_REC = {"declaration": {"total": 41500.50, "parts": {"A": 41500.50, "B": 0.0}, "nil": False}, "frozen": {"total": 41500.50},
           "ec_table": {"total_donations": 99.0, "excepted": True}}


def _reader(family, rows, declared=41500.50, parts_named=("A", "B")):
    return {"family": family, "pages": [{"page": 1, "parts_named": list(parts_named), "declared_total": declared, "rows": rows,
                                         "unparsed": False}]}


ROWS = [{"part": "A", "n": 1, "amount": 25000.0, "donor": "A Donor Trust", "is_total": False},
        {"part": "A", "n": 2, "amount": 16500.5, "donor": "Another Giver", "is_total": False},
        {"part": "A", "n": None, "amount": 41500.5, "donor": None, "is_total": True}]


def test_the_key_total_prefers_the_declaration_then_the_frozen_site_then_the_commission():
    assert score.key_total(KEY_REC) == (4150050, "declaration")
    assert score.key_total({"frozen": {"total": 12.0}}) == (1200, "frozen")
    assert score.key_total({"ec_table": {"total_donations": 12.0, "excepted": False}}) == (1200, "commission")
    assert score.key_total({"ec_table": {"total_donations": 12.0, "excepted": True}}) == (None, None)
    assert score.key_total({"declaration": {"total": None, "nil": True}}) == (0, "declaration")


def test_a_faithful_set_of_rows_matches_the_declaration_and_its_parts():
    s = score.document_score({("glm-ocr", "q8_0", 300, "two"): _reader("zhipu", ROWS)}, KEY_REC)[0]
    assert s["declared_match"] and s["parts_exact"] == 2 and s["parts_compared"] == 2
    assert s["rows"] == 2 and s["total_rows"] == 1 and s["lone_rows"] is None     # one family: nothing to be lone against


def test_a_row_only_one_family_produces_that_breaks_the_printed_total():
    extra = ROWS + [{"part": "A", "n": 3, "amount": 999.99, "donor": "Nobody", "is_total": False}]
    by = {("glm-ocr", "q8_0", 300, "two"): _reader("zhipu", ROWS), ("ovisocr2", "q8_0", 300, "two"): _reader("qwen", extra)}
    out = {s["reader"]: s for s in score.document_score(by, KEY_REC)}
    assert out["glm-ocr"]["lone_rows"] == 0 and out["glm-ocr"]["parts_exact"] == 2
    assert out["ovisocr2"]["lone_rows"] == 1 and out["ovisocr2"]["lone_breaking"] == 1 and out["ovisocr2"]["parts_exact"] == 1


def test_two_readers_of_one_family_do_not_vouch_for_each_other():
    extra = ROWS + [{"part": "A", "n": 3, "amount": 999.99, "donor": "Nobody", "is_total": False}]
    by = {("ovisocr2", "q8_0", 300, "two"): _reader("qwen", extra), ("chandra-ocr-2", "q8_0", 300, "two"): _reader("qwen", extra)}
    out = {s["reader"]: s for s in score.document_score(by, KEY_REC)}
    assert out["ovisocr2"]["lone_rows"] is None           # no other family read the document


def test_example_donors_and_gold_cells():
    ex = ROWS + [{"part": "A", "n": 3, "amount": 1500.0, "donor": "John Smith, 1 Example St", "is_total": False}]
    gold = [{"part": "A", "n": 1, "field": "amount", "value": 25000.0}, {"part": "A", "n": 9, "field": "amount", "value": 7.0}]
    s = score.document_score({("glm-ocr", "q8_0", 300, "two"): _reader("zhipu", ex)}, KEY_REC, gold)[0]
    assert s["example_rows"] == 1 and s["gold_cells"] == 2 and s["gold_hits"] == 1


def test_levels_compare_texts():
    assert score.compare_texts("a  b\nc", "a b c") == (True, 1.0)
    eq, ratio = score.compare_texts("TOTAL $1.00", "TOTAL $1.01")
    assert not eq and 0.8 < ratio < 1.0
