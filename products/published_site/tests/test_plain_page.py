"""The plain page renders every row with its document and marks pixels."""
import datetime as dt

from products.published_site import render_party_totals, template


def rows():
    return [{"party": "Example Party", "party_label": "Example", "year": 2023, "declared_total": 219964.7, "declared_parts": "A+C+D+F+G",
             "total_check": "parts-sum", "read_from": "text", "document": "a" * 64, "page": 1},
            {"party": "Example Party", "party_label": "Example", "year": 2023, "declared_total": 219000.0, "declared_parts": "A+C+D+F+G",
             "total_check": "parts-sum", "read_from": "pixels", "document": "b" * 64, "page": 1},
            {"party": None, "party_label": "Nobody Party", "year": 2022, "declared_total": 0, "declared_parts": "",
             "total_check": "declared-nil", "read_from": "text", "document": "c" * 64, "page": 1}]


def test_every_figure_names_its_document_and_pixels_are_marked():
    t = template()
    assert t.reads[0].table == "pub.party_return_totals"
    page = render_party_totals(rows(), t, now=dt.datetime(2026, 10, 18, 12, 0))
    assert "$219,964.70" in page and "document " + "a" * 64 in page
    assert "READ FROM PIXELS" in page and "2 returns held for this year; none chosen" in page
    assert "(unresolved: Nobody Party)" in page and "declared NIL" in page
    assert "Known limits: Only returns with a text layer" in page
    assert "3 returns read" in page


def test_an_empty_table_says_so():
    page = render_party_totals([], template())
    assert "No returns read yet" in page
