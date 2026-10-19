"""Against the real published tables through the session reader (slow):
the outside check is green, a search is quick, and a four-pane walk renders."""
import time

import pytest

from products.board import check, db, search, server

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
    assert html.count('<section class="pane') == 3 and "Possible namesakes, apart" in html
