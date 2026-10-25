"""Against the real published tables through the session reader (slow):
the outside check is green, a search is quick, a four-pane walk renders,
the search tab marks a macron-folded word in the registers checked only,
and the graph tab draws a busy row quickly with every far end real."""
import time

import pytest

from products.board import catalogue as cat
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


def test_the_field_search_is_quick_and_a_last_name_is_a_whole_word():
    with db.read_connect() as conn:
        t = time.time()
        res = search.search(conn, "", limit=search.RESULTS_LIMIT, fields={"first": "Graeme", "last": "Hart"})
        assert time.time() - t < 3.0
        names = [n for reg, hits in res.items() if reg != "held" for v, _, rows in hits for r in rows for n in check._names(v, r)]
    assert names and all("hart" in cat.fold_term(n).replace(",", " ").split() for n in names)


def test_near_matches_render_closed_below_the_results_within_three_seconds():
    with db.read_connect() as conn:
        t = time.time()
        html = server.render("", [], conn=conn, boxes=search.Boxes(True, (), (("first", "Phillip"), ("last", "Mills"))))
        assert time.time() - t < 3.0
    exact, below = html.split('<details class="near" id="near">')
    assert "party_return_donors" in exact and "near: given name and surname reversed" in below
    assert "narrowed by: first name" in exact and "<script" not in html


def test_every_links_rule_in_pub_links_has_its_words():
    """Ruling 84: each rule id pub.links carries is in catalogue.RULE_WORDS,
    so no edge falls back to "links rule <id>" on the live data."""
    with db.read_connect() as conn:
        rules = {r["rule"] for r in db.rows(conn, "select distinct rule from pub.links")}
    assert rules
    lacking = sorted(r for r in rules if r.partition("@")[0] not in cat.RULE_WORDS)
    assert not lacking, lacking
