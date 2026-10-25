"""Ruling 92 (6): the field search's selector, "all fields must match" (the
default, as before) or "any field may match": radio inputs in the details
element, carried in the hrefs like the fields; under "any" a row matches on
any filled field and the results say which. The same fixture rows against
both modes on a real database are in test_real.py (slow)."""
import re
import urllib.parse

from products.board import catalogue as cat
from products.board import panes, search
from products.board.tests.test_panes import director

FIELDS = {"first": "Garry", "last": "Payinda", "year": "2020"}


def test_all_ands_the_fields_and_any_ors_them():
    v = cat.BY_NAME["directors"]
    all_parts = search.field_clauses(v, FIELDS)
    any_parts = search.field_clauses(v, FIELDS, search.ANY)
    assert [f for f, _, _ in all_parts] == [("first", "last"), ("year",)]          # all: one person's first and last name
    assert [f for f, _, _ in any_parts] == [("first",), ("last",), ("year",)]
    assert search.fields_sql(v, FIELDS) == (" and ".join(c for _, c, _ in all_parts), [p for _, _, ps in all_parts for p in ps])
    assert search.fields_sql(v, FIELDS, search.ANY) == ("(" + " or ".join(c for _, c, _ in any_parts) + ")",
                                                       [p for _, _, ps in any_parts for p in ps])


def test_a_field_a_view_cannot_hold_drops_the_view_under_all_and_is_skipped_under_any():
    v = cat.BY_NAME["directors"]                   # no address column
    asked = {"last": "Payinda", "address": "1 Queen Street"}
    assert search.fields_sql(v, asked) is None and search.match_sql(v, [], None, False, asked) is None
    clause, _ = search.fields_sql(v, asked, search.ANY)
    assert clause and "line_1" not in clause
    assert search.fields_sql(v, {"address": "1 Queen Street"}, search.ANY) is None
    assert search.fields_sql(v, {"last": "x", "year": "20"}, search.ANY)[0]          # a bad year is skipped, not fatal


def test_any_selects_which_field_each_row_matched():
    sql, params = search.view_sql(cat.BY_NAME["directors"], [], None, 50, fields=FIELDS, mode=search.ANY)
    assert sql.count(" as _matched_") == 3 and "_matched_first" in sql and "_matched_year" in sql
    assert sql.index(" as _matched_") < sql.index(" where ") and params[-1] == 50
    assert sql.count("%s") == len(params)
    plain, pp = search.view_sql(cat.BY_NAME["directors"], [], None, 50, fields=FIELDS)
    assert "_matched_" not in plain and plain.count("%s") == len(pp)


def test_the_selector_defaults_to_all_and_rides_the_hrefs_only_when_any():
    left = panes.left_pane("", ["companies"], search.FIRST)
    assert re.search(r'<input type="radio" name="mode" value="all" checked> all fields must match', left)
    assert re.search(r'<input type="radio" name="mode" value="any"> any field may match', left)
    any_ = search.Boxes(True, (), (("last", "Payinda"),), mode=search.ANY)
    assert 'value="any" checked' in panes.left_pane("", ["companies"], any_)
    link = panes.href("x", [], any_)
    assert search.boxes_of(urllib.parse.parse_qs(urllib.parse.urlsplit(link).query)).mode == search.ANY
    assert "mode=" not in panes.href("x", [], search.Boxes(True, (), (("last", "Payinda"),)))     # all: the address as before
    assert search.boxes_of({"mode": ["drop table"]}).mode == search.ALL


def test_the_results_say_which_field_a_row_matched():
    r = director(_matched_first=False, _matched_last=True, _matched_year=True)
    html = panes.hit("", cat.BY_NAME["directors"], r, [], search.Boxes(mode=search.ANY))
    assert "matched: last name, year" in html
    assert "matched:" not in panes.hit("", cat.BY_NAME["directors"], director(), [])
    line = panes.narrowed_line(search.Boxes(True, (), (("first", "Garry"), ("last", "Payinda")), mode=search.ANY))
    assert "(any field may match)" in line
