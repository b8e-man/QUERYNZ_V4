"""Against the real published tables through the session reader (slow):
the outside check is green, a search is quick, a four-pane walk renders,
the search tab marks a macron-folded word in the registers checked only,
and the graph tab draws a busy row quickly with every far end real."""
import time

import pytest

from products.board import check, db, graph, search, server

pytestmark = pytest.mark.slow


def test_the_outside_check_is_green():
    with db.read_connect() as conn:
        assert check.problems(conn) == []


def test_a_search_answers_within_two_seconds():
    with db.read_connect() as conn:
        t = time.time()
        res = search.search(conn, "Graeme Hart")
        assert time.time() - t < 2.0
        assert "party_returns" in res or "disclosures" in res


def test_a_person_pane_renders_with_namesakes_apart():
    with db.read_connect() as conn:
        d = db.rows(conn, "select key from pub.directors where not coalesce(suppressed, false) order by key limit 1")[0]["key"]
        html = server.render("", server.parse_path(f"directors:{d}|person:directors:{d}"), conn=conn)
    assert html.count('<section class="pane') == 4 and "Possible namesakes, apart" in html     # the left pane, the results, two panes


def test_the_search_tab_marks_maori_as_maori_in_the_registers_checked_only():
    with db.read_connect() as conn:
        html = server.render("Maori", [], conn=conn, boxes=search.Boxes(False, ("iwi_directory",)))
    results = html[html.index('id="results"'):]
    assert "<mark>Māori</mark>" in results                        # "Maori" typed marks "Māori" filed
    assert "<strong>iwi_directory_entities</strong>" in results
    assert "Registered political parties" not in results           # an unchecked register is not searched


def test_the_graph_of_a_busy_company_is_quick_and_every_far_end_is_a_row():
    with db.read_connect() as conn:
        c = db.rows(conn, "select entity_key from pub.directors group by 1 order by count(*) desc limit 1")[0]["entity_key"]
        t = time.time()
        g = graph.build(conn, "", centre=f"companies:{c}")
        assert time.time() - t < 5.0
        assert g["drawn"]["role"] >= 1 and len(g["nodes"]) <= graph.MAX_NODES
        for nid in g["nodes"]:
            view, _, key = nid.partition(":")
            assert search.row(conn, view, key) is not None, nid
