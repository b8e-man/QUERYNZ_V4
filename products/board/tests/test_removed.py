"""Ruling 93: "show removed companies", a check box under the register
ticks, unticked on the first view, riding every href like the ticks
(`removed=1` only when ticked). Unticked, a companies row whose folded
status is in catalogue.REMOVED_STATUS is left out in the SQL, before the
limit, and the count line says how many were hidden; ticked, the SQL is
the one the board wrote before. The same fixture rows against both
settings on a real database are in test_real.py (slow)."""
import re
import urllib.parse

from products.board import catalogue as cat
from products.board import db, panes, search, server

COMPANIES = cat.BY_NAME["companies"]


def boxes_back(link: str) -> search.Boxes:
    return search.boxes_of(urllib.parse.parse_qs(urllib.parse.urlsplit(link.replace("&amp;", "&")).query))


def test_the_status_words_are_data_folded():
    assert {"removed", "deregistered", "dissolved", "closed"} <= cat.REMOVED_STATUS
    assert all(w == w.strip().lower() for w in cat.REMOVED_STATUS)
    assert "registered" not in cat.REMOVED_STATUS and "in liquidation" not in cat.REMOVED_STATUS
    assert cat.REMOVED_OF == {"companies": "status"}


def test_ticked_writes_the_sql_as_before_and_unticked_leaves_removed_out_before_the_limit():
    before = search.view_sql(COMPANIES, ["fletcher"], None, 50)
    assert search.view_sql(COMPANIES, ["fletcher"], None, 50, removed=True) == before
    assert "_removed" not in before[0]
    sql, params = search.view_sql(COMPANIES, ["fletcher"], None, 50, removed=False)
    assert params[0] == sorted(cat.REMOVED_STATUS) and params[-1] == 50
    assert "where not _removed order by" in sql and sql.index("not _removed order by") < sql.rindex("limit %s")
    assert "count(*) filter (where _removed) as hidden" in sql
    assert search.view_sql(cat.BY_NAME["directors"], ["fletcher"], None, 50, removed=False) == \
        search.view_sql(cat.BY_NAME["directors"], ["fletcher"], None, 50)          # only the views REMOVED_OF names


def test_the_near_and_table_clause():
    assert search.removed_sql(COMPANIES, True) == ("", [])
    assert search.removed_sql(cat.BY_NAME["directors"], False) == ("", [])
    clause, params = search.removed_sql(COMPANIES, False)
    assert clause.startswith(" and not (") and "lower(btrim(status))" in clause and params == [sorted(cat.REMOVED_STATUS)]


def test_hrefs_carry_removed_only_when_ticked():
    off, on = search.Boxes(False, ("companies",)), search.Boxes(False, ("companies",), removed=True)
    assert "removed" not in panes.href("x", [], off) and "removed=1" in panes.href("x", [], on)
    assert boxes_back(panes.href("x", [], on)).removed and not boxes_back(panes.href("x", [], off)).removed
    assert not search.FIRST.removed and not search.boxes_of({}).removed
    assert boxes_back(panes.href("x", [], on._replace(table="companies", upto=100))).removed     # the table's "more" keeps it
    assert 'name="removed" value="1"' in panes.hidden_boxes(on) and "removed" not in panes.hidden_boxes(off)


def test_the_box_sits_under_the_register_ticks_unticked_on_the_first_view():
    for action in ("/", "/graph"):
        left = panes.left_pane("", ["companies"], search.FIRST, action=action)
        box = left.index('name="removed"')
        assert left.rindex('name="r"') < box and 'name="removed" value="1" checked' not in left
        assert "show removed companies" in left
    ticked = panes.left_pane("", ["companies"], search.Boxes(removed=True))
    assert 'name="removed" value="1" checked' in ticked


def row(key, name, status):
    return {"key": key, "name": name, "status": status, "entity_type": "NZ Limited Company", "nzbn": key,
            "number": key, "register": "companies", "document": None}


def test_the_count_line_says_how_many_were_hidden():
    held = {"companies"}
    hits = {"companies": [(COMPANIES, 2, [row("1", "ACME LIMITED", "Registered"), row("2", "ACME TWO LIMITED", "registered")])],
            "held": held, "hidden": {"companies": 3}}
    html = panes.results_pane("acme", hits, held, ("companies",), search.Boxes(False, ("companies",)), ["acme"])
    assert re.search(r'<span class="count">2</span> <span class="note">3 removed hidden</span></span>', html)
    shown = dict(hits, hidden={})
    html = panes.results_pane("acme", shown, held, ("companies",), search.Boxes(False, ("companies",), removed=True), ["acme"])
    assert "removed hidden" not in html
    none_left = {"held": held, "hidden": {"companies": 4}}                            # every match removed: the count still said
    html = panes.results_pane("acme", none_left, held, ("companies",), search.Boxes(False, ("companies",)), ["acme"])
    assert "4 removed hidden" in html and "none found" in html


def test_search_drops_the_counts_own_row_and_keeps_the_hidden_count(monkeypatch):
    answers = {"companies": [{"key": None, "total": 0, "hidden": 5}],
               "directors": [dict(row("d1", "JO FLETCHER", None), total=1)]}
    monkeypatch.setattr(db, "pub_views", lambda conn: {"companies", "directors"})
    monkeypatch.setattr(search, "_scan", lambda v, *a: (v, answers.get(v.name, [])))
    res = search.search(None, "fletcher", registers=("companies",), removed=False)
    assert [v.name for v, _, _ in res["companies"]] == ["directors"] and res["hidden"] == {"companies": 5}


def test_the_table_leaves_removed_out_and_counts_them(monkeypatch):
    asked = []

    def rows(conn, sql, params=()):
        asked.append((sql, list(params)))
        return [{"n": 7, "hidden": 4}] if "count(*)" in sql else []
    monkeypatch.setattr(db, "rows", rows)
    assert search.table(None, COMPANIES, 0, removed=False) == (7, [], 4)
    assert all("lower(btrim(status))" in sql for sql, _ in asked) and asked[1][1][-1] == search.TABLE_PAGE
    asked.clear()
    assert search.table(None, COMPANIES, 0) == (7, [], 0) and not any("status" in sql for sql, _ in asked)
    html = panes.table_pane("", COMPANIES, 7, [], search.Boxes(table="companies"), {"companies"}, hidden=4)
    assert "7 rows in companies</span> <span class=\"note\">4 removed hidden</span>" in html


def test_a_row_pane_by_its_own_link_reads_the_row_whatever_its_status():
    """search.row names the row: no status clause, so a removed company opens."""
    import inspect
    assert "status" not in inspect.getsource(search.row) and "removed" not in inspect.getsource(search.row)
    assert "removed" not in inspect.getsource(search.far_rows) and "removed" not in inspect.getsource(search.children)
    assert "removed=boxes.removed" in inspect.getsource(server.render)
