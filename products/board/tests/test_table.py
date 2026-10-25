"""Ruling 92 (5): a register's name opens its table: 100 rows a page in the
view's order, each one line, "more" appends the next 100 (the href carries
the offset), the count of all rows at the top, the table kept while a search
runs; a suppressed name reads name suppressed."""
import re
import urllib.parse

from products.board import catalogue as cat
from products.board import panes, search
from products.board.tests.test_panes import director


def carried(link: str) -> search.Boxes:
    return search.boxes_of(urllib.parse.parse_qs(urllib.parse.urlsplit(link.replace("&amp;", "&")).query))


def rows(n):
    return [director(key=f"companies/1/director/{i:04d}", full_name=f"Person {i} " + "LONGSURNAME" * 6,
                     role_type="Director", suppressed=(i == 3)) for i in range(n)]


def test_the_register_name_is_a_link_to_its_table_and_the_form_keeps_an_open_table():
    left = panes.left_pane("doe", ["companies", "parties"], search.Boxes(False, ("parties",)))
    link = re.search(r'<a class="row" href="([^"]*)" title="open the register as a table">Companies, directors', left).group(1)
    b = carried(link)
    assert b.table == "companies" and b.upto == 0 and b.ticked == ("parties",) and not b.all and link.endswith("#table")
    assert urllib.parse.parse_qs(urllib.parse.urlsplit(link.replace("&amp;", "&")).query)["q"] == ["doe"]
    open_ = panes.left_pane("doe", ["companies"], search.Boxes(table="directors", upto=200))
    assert '<input type="hidden" name="t" value="directors"><input type="hidden" name="o" value="200">' in open_
    assert "open the register as a table" not in panes.left_pane("doe", ["companies"], search.FIRST, action="/graph")


def test_paging_hrefs_carry_the_offset_and_stop_at_the_cap():
    v = cat.BY_NAME["directors"]
    boxes = search.Boxes(table="directors")
    html = panes.table_pane("", v, 250, rows(100), boxes, {"directors", "companies"})
    assert '1,185' not in html and "250 rows in directors" in html and "rows 1 to 100 of 250" in html
    more = re.search(r'<a href="([^"]*)">more: the next 100</a>', html).group(1)
    assert carried(more) == boxes._replace(upto=100)
    html = panes.table_pane("", v, 250, rows(200), boxes._replace(upto=100), {"directors"})
    assert carried(re.search(r'<a href="([^"]*)">more', html).group(1)).upto == 200
    assert "more:" not in panes.table_pane("", v, 250, rows(250), boxes._replace(upto=200), {"directors"})
    capped = panes.table_pane("", v, 5000, rows(search.TABLE_MAX), boxes._replace(upto=search.TABLE_MAX - 100), {"directors"})
    assert "more:" not in capped and "1,000 rows at most" in capped
    q = {"t": ["directors"], "o": ["99999"]}
    assert search.boxes_of(q).upto == search.TABLE_MAX - 100
    assert search.boxes_of({"t": ["pub.secret"], "o": ["100"]}) == search.Boxes()          # an unknown view opens no table


def test_every_row_is_one_line_cut_with_the_whole_value_on_hover():
    v = cat.BY_NAME["directors"]
    html = panes.table_pane("", v, 100, rows(100), search.Boxes(table="directors"), {"directors"})
    trs = re.findall(r"<tr>(.*?)</tr>", html)
    assert len(trs) == 101                                                      # the heading and 100 rows
    assert re.findall(r"<th>(.*?)</th>", trs[0]) == ["title"] + [label for label, _ in v.fields]
    for tr in trs[1:]:
        assert "<br" not in tr and "\n" not in tr
        cells = re.findall(r'<td title="([^"]*)">(.*?)</td>', tr)
        assert len(cells) == 1 + len(v.fields)
        for full, shown in cells:
            text = re.sub(r"<[^>]+>", "", shown)
            assert len(panes.html.unescape(text)) <= panes.CELL_CHARS
    long = re.search(r'<td title="(Person 0 [^"]*)"><a[^>]*>([^<]*)</a>', html)
    assert long.group(1).endswith("LONGSURNAME") and long.group(2).endswith("…")


def test_a_suppressed_name_reads_suppressed_and_a_key_column_reads_the_far_title():
    v = cat.BY_NAME["directors"]
    far = {("companies", "key", "companies/1"): {"key": "companies/1", "name": "ONE LIMITED"}}
    html = panes.table_pane("", v, 100, rows(5), search.Boxes(table="directors"), {"directors"}, far)
    assert "Person 3" not in html and panes.SUPPRESSED in html
    assert '<td title="companies/1"><a class="row" href="/?q=&amp;p=companies%3Acompanies%2F1' in html and "ONE LIMITED</a>" in html


def test_the_view_chooser_offers_the_registers_other_held_views():
    v = cat.BY_NAME["directors"]
    html = panes.table_pane("", v, 1, rows(1), search.Boxes(table="directors"), {"directors", "companies", "shareholders"})
    chooser = re.search(r'<p class="note">views: (.*?)</p>', html).group(1)
    assert "<strong>directors</strong>" in chooser
    assert [carried(h).table for h in re.findall(r'href="([^"]*)"', chooser)] == ["companies", "shareholders"]


def test_every_main_view_is_a_view_of_its_register():
    for register, _ in cat.REGISTERS:
        assert cat.BY_NAME[cat.main_view_of(register)].register == register
    assert cat.main_view_of("parties") == "parties" and cat.main_view_of("companies") == "companies"
