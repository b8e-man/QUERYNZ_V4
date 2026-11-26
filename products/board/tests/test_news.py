"""The news tab (news.py): the read articles, sorted by published or read date, searched in title, author and site."""
from __future__ import annotations

import datetime as dt

from products.board import news

T = dt.datetime(2026, 11, 26, 14, 8, tzinfo=dt.timezone.utc)
ROW = {"url_key": "rnz.co.nz/a", "url": "https://www.rnz.co.nz/a", "host": "rnz.co.nz", "title": "A <bold> claim",
       "author": "A Writer", "published_at": T - dt.timedelta(days=2), "read_at": T, "outcome": "read", "model": "qwen38-27b",
       "quotes_kept": 3, "roles_kept": 1, "tones_kept": 0, "skipped_why": None}


class Col:
    def __init__(self, name):
        self.name = name


class Conn:
    def __init__(self, rows):
        self.rows, self.sql = rows, []

    def execute(self, sql, params=None):
        self.sql.append((sql, params))
        rows = self.rows
        return type("C", (), {"description": [Col(k) for k in ROW], "fetchall": lambda _s: [tuple(r[k] for k in ROW) for r in rows]})()


def test_the_sort_is_read_or_published_and_anything_else_falls_back():
    assert news.args({})["sort"] == "read" and news.args({})["dir"] == "desc"
    a = news.args({"sort": ["published"], "dir": ["asc"], "page": ["2"]})
    sql, _ = news.query(a)
    assert "ORDER BY published_at ASC NULLS LAST" in sql and "OFFSET 200" in sql
    sql, _ = news.query(news.args({"sort": ["read_at; DELETE"], "dir": ["sideways"]}))
    assert "ORDER BY read_at DESC" in sql and "DELETE" not in sql, "only the two sorts ever reach the SQL"


def test_the_search_is_one_parameter_in_title_author_and_site_its_wildcards_escaped():
    sql, params = news.query(news.args({"q": ["50%_off"]}))
    assert "(title ILIKE %s OR author ILIKE %s OR host ILIKE %s)" in sql
    assert params[-3:] == ["%50\\%\\_off%"] * 3 and params[0] == ["read", "replayed"]
    sql, params = news.query(news.args({"all": ["1"]}))
    assert "WHERE" not in sql and params == []


def test_the_page_escapes_the_title_links_the_article_and_sorts_by_its_headers():
    conn = Conn([ROW])
    html = news.render(conn, {"q": ["claim"]})
    assert "A &lt;bold&gt; claim" in html and 'href="https://www.rnz.co.nz/a"' in html
    assert "/news?q=claim&amp;sort=published&amp;dir=desc" in html, "the published header sorts by it"
    assert "read ↓" in html and 'data-tab="news"' in html and "next page" not in html


def test_a_page_full_offers_the_next_and_a_failure_is_said():
    html = news.render(Conn([ROW] * (news.PAGE + 1)), {})
    assert "next page" in html and html.count("<tr>") == news.PAGE + 1

    class Broken:
        def execute(self, *a):
            raise RuntimeError("canceling statement due to statement timeout")
    assert "the list could not be read: RuntimeError: canceling statement" in news.render(Broken(), {})


def test_the_live_view_reads_as_the_board_reads_it():
    from products.board import db
    with db.read_connect() as conn:
        html = news.render(conn, {"sort": ["published"]})
        searched = news.render(conn, {"q": ["the"]})
    assert "the list could not be read" not in html and "the list could not be read" not in searched
    assert "<table" in html
