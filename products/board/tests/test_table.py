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


def test_every_row_is_one_line_holding_its_whole_value_for_the_reader_to_clip_or_wrap():
    """Ruling 117 (3): the cell holds the whole value (cut only past CELL_MAX), one line by default, the browser clipping it."""
    v = cat.BY_NAME["directors"]
    html = panes.table_pane("", v, 100, rows(100), search.Boxes(table="directors"), {"directors"})
    trs = re.findall(r"<tr>(.*?)</tr>", html)
    assert len(trs) == 101                                                      # the heading and 100 rows
    assert re.findall(r'<th data-col="[^"]*"><div class="th"><a [^>]*>([^<]*)</a>', trs[0]) == ["title"] + [label for label, _ in v.fields]
    assert re.findall(r'<th data-col="([^"]*)"', trs[0]) == list(search.table_columns(v))
    assert '<table class="grid" data-view="directors" data-lines="1">' in html and 'id="table-lines"' in html
    for tr in trs[1:]:
        assert "<br" not in tr and "\n" not in tr
        cells = re.findall(r'<td title="([^"]*)"><div class="c">(.*?)</div></td>', tr)
        assert len(cells) == 1 + len(v.fields)
    long = re.search(r'<td title="(Person 0 [^"]*)"><div class="c"><a[^>]*>([^<]*)</a>', html)
    assert long.group(1) == long.group(2) and long.group(2).endswith("LONGSURNAME")          # whole, not cut at 40
    assert panes.whole("x" * 3000)[0].endswith("…") and len(panes.whole("x" * 3000)[1]) == 3000


def test_a_suppressed_name_reads_suppressed_and_a_key_column_reads_the_far_title():
    v = cat.BY_NAME["directors"]
    far = {("companies", "key", "companies/1"): {"key": "companies/1", "name": "ONE LIMITED"}}
    html = panes.table_pane("", v, 100, rows(5), search.Boxes(table="directors"), {"directors"}, far)
    assert "Person 3" not in html and panes.SUPPRESSED in html
    assert '<td title="companies/1"><div class="c"><a class="row" href="/?q=&amp;p=companies%3Acompanies%2F1' in html and "ONE LIMITED</a>" in html


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


# ── ruling 117 (3): every column sorts both ways from its heading, in SQL, the sort in the address ─────────

def test_the_sort_rides_the_address_and_only_a_column_of_the_table_reaches_it():
    assert search.boxes_of({"t": ["directors"], "ts": ["-appointed_on"]}).sort == ""            # a date column is not in the table
    assert search.boxes_of({"t": ["directors"], "ts": ["-role_type"]}).sort == "-role_type"
    assert search.boxes_of({"t": ["directors"], "ts": ["title"]}).sort == "title"
    for bad in ("role_type; select 1", "--role_type", "key", "suppressed", "-", "role_type desc"):
        assert search.boxes_of({"t": ["directors"], "ts": [bad]}).sort == "", bad
    assert search.boxes_of({"ts": ["title"]}).sort == ""                                        # no table, no sort
    b = search.Boxes(table="directors", sort="-role_type")
    assert ("ts", "-role_type") in b.params() and ("ts", "x") not in search.Boxes(sort="x").params()


def test_the_order_is_the_column_named_both_ways_the_key_last_and_the_view_order_otherwise():
    v = cat.BY_NAME["directors"]
    assert search.table_order(v, "role_type") == "role_type asc nulls last, key asc"
    assert search.table_order(v, "-role_type") == "role_type desc nulls last, key desc"
    assert search.table_order(v, "title") == "full_name asc nulls last, key asc"
    assert search.table_order(v, "appointed_on; x") == f"{v.default_order} nulls last, key"
    g = cat.BY_NAME["gazette_celebrants"]
    assert search.table_order(g, "-title") == "surname desc nulls last, given_names desc nulls last, key desc"


def test_the_table_is_sorted_in_sql_under_the_page_s_limit(monkeypatch):
    asked = []
    monkeypatch.setattr(search.db, "rows", lambda conn, sql, params=(): asked.append((sql, list(params))) or [{"n": 5, "hidden": 0}])
    search.table(None, cat.BY_NAME["directors"], 200, True, "-role_type")
    sql, params = asked[-1]
    assert sql.endswith("order by role_type desc nulls last, key desc limit %s") and params == [300]


def test_each_heading_sorts_its_column_both_ways_and_more_keeps_the_sort():
    v = cat.BY_NAME["directors"]
    boxes = search.Boxes(table="directors", sort="role_type")
    html = panes.table_pane("", v, 250, rows(100), boxes, {"directors", "companies"})
    head = re.search(r'<th data-col="role_type" aria-sort="ascending">(.*?)</th>', html).group(1)
    links = re.findall(r'href="([^"]*)"', head)
    assert [carried(h).sort for h in links] == ["-role_type", "role_type", "-role_type"]        # the label flips; up; down
    title = re.search(r'<th data-col="title">(.*?)</th>', html).group(1)
    assert [carried(h).sort for h in re.findall(r'href="([^"]*)"', title)] == ["title", "title", "-title"]
    assert carried(re.search(r'<a href="([^"]*)">more: the next 100</a>', html).group(1)).sort == "role_type"
    assert "sorted by role, ascending" in html and html.count("aria-sort=") == 1
    chooser = re.search(r'<p class="note">views: (.*?)</p>', html).group(1)
    assert all(carried(h).sort == "" for h in re.findall(r'href="([^"]*)"', chooser))          # another view starts in its own order


def test_the_reader_s_controls_are_a_listed_file_kept_in_the_session_and_ask_nothing():
    from products.board import assets
    js = assets.read("table.js")[0].decode()
    assert "sessionStorage" in js and "localStorage" not in js
    assert not re.search(r"fetch\(|XMLHttpRequest|sendBeacon|WebSocket|\.sort\(", js)           # nothing sent; no sort in the browser
    html = panes.table_pane("", cat.BY_NAME["directors"], 1, rows(1), search.Boxes(table="directors"), {"directors"})
    assert f'<script src="{panes.esc(assets.url("table.js"))}" defer></script>' in html
