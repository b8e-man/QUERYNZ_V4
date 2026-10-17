"""The parser reads BOTH shapes the transcriber emits for one document.

The fixtures are verbatim lines from GLM-OCR's read of National 2017 on
2026-09-23: page 3 carried the form's row-number column, page 2 did not.
"""
import sys, pathlib

from support.docread import parse
from support.docread.rows import donor_key, donor_name, money, date as read_date

NUMBERED = """PART A: PARTY DONATIONS OF MORE THAN $15,000

21 Shi, Di Yi L3, 139 Quay Street, Auckland | 01/03/2017 | No | $50,000.00

22 Lane Capital Group L2, 16 Viaduct Harbour Avenue, Auckland | 04/09/2017 | No | $50,000.00

25 Heartland Bank Limited L3, Heartland House, 35 Teed Street, Newmarket, Auckland | 11/08/2017 | No | $12,950.00
"""

UNNUMBERED = """PART A: PARTY DONATIONS OF MORE THAN $15,000

| Donor's name and street address | Date donation or aggregated donations received | Does the donation contain contributions from another person of more than $15,000? Enter YES or NO | Amount of donation or total aggregated donations (including GST) |
| :--- | :--- | :--- | :--- |
| Inner Mongolia Rider Horse Industry (NZ) Limited L7, PWC Tower, 188 Quay Street, Auckland | 15/05/2017 | No | $150,000.00 |
| Alpha Laboratories (NZ) Limited 48 Crooks Rd, East Tamaki, Auckland | 28/07/2017 | No | $100,000.00 |
| Hagaman, Lianna 10 Coldstream Court, Christchurch | 31/01/2017 | No | $1,150.00 |
"""


def test_a_numbered_page_keeps_the_printed_number():
    rows, part, _, _ = parse.parse_page(NUMBERED, 3)
    assert [r.n for r in rows] == [21, 22, 25]
    assert part == "A" and all(r.part == "A" for r in rows)
    assert rows[0].amount == 50000.0 and rows[2].amount == 12950.0
    assert rows[0].date == "2017-03-01"


def test_an_unnumbered_page_still_yields_its_rows():
    """The failure this parser was written for: three correctly-read rows that
    the number-anchored parser discarded."""
    rows, _, _, _ = parse.parse_page(UNNUMBERED, 2)
    assert len(rows) == 3
    assert [r.n for r in rows] == [None, None, None]
    assert rows[0].amount == 150000.0
    assert rows[2].donor.startswith("Hagaman")


def test_the_header_row_is_not_a_donation():
    rows, _, _, _ = parse.parse_page(UNNUMBERED, 2)
    assert not any("Donor's name" in (r.donor or "") for r in rows)
    assert not any(r.amount == 15000.0 for r in rows), \
        "the header's '$15,000' must not be read as an amount"


def test_the_markdown_rule_is_not_a_row():
    rows, _, _, _ = parse.parse_page("| :--- | :--- |\n", 1)
    assert rows == []


def test_a_number_is_never_invented():
    """An inferred row number would defeat the invariant that exists to notice
    the column's absence, so the parser must leave it None."""
    rows, _, _, _ = parse.parse_page(UNNUMBERED, 2)
    assert all(r.n is None for r in rows)


def test_the_part_carries_across_pages():
    doc = parse.parse_document("t", {2: UNNUMBERED, 3: NUMBERED.split("\n", 1)[1]})
    assert all(r.part == "A" for r in doc.rows)
    assert len(doc.rows) == 6


def test_a_printed_total_is_read_as_the_form_s_own():
    rows, _, totals, _ = parse.parse_page(
        "| TOTAL FOR PART A | $ 1,002,516.53 |\n", 2)
    assert totals == {"A": 1002516.53}
    assert rows == [], "a total is not a donation row"


def test_a_total_is_never_counted_as_a_row():
    doc = parse.parse_document("t", {1: NUMBERED + "\nTOTAL FOR PART A $113,000.00\n"})
    assert len(doc.rows) == 3
    assert doc.stated_totals["A"] == 113000.0


def test_a_row_with_no_money_is_not_a_row():
    rows, _, _, _ = parse.parse_page("| Some Donor | 01/01/2017 | No |\n", 1)
    assert rows == []


def test_money_and_date_readers_refuse_rather_than_guess():
    assert money("no money at all") is None
    assert read_date("32/01/2017") is None
    assert read_date("01/13/2017") is None


def test_the_donor_key_drops_the_street_address():
    a = "Hagaman, Lianna 10 Coldstream Court, Christchurch"
    b = "Hagaman, Lianna 10 Coldstream Court, Ilam, Christchurch"
    assert donor_key(a) == donor_key(b)
    assert donor_name(a) == "Hagaman, Lianna"


def test_a_donor_whose_name_starts_with_a_digit_keeps_its_name():
    assert donor_key("3M New Zealand 5 High St") == donor_key("3M New Zealand 5 High St")
    assert len(donor_key("3M New Zealand 5 High St")) > 3
