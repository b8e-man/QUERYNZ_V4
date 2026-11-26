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


READING = {"article": {"type": "news", "themes": ["dairy"]}, "authors": [],
           "entities": {"e1": {"name": "Richard Allen", "kind": "person", "forms": ["Richard Allen", "Allen"]},
                        "e2": {"name": "Fonterra", "kind": "organisation", "forms": ["Fonterra"]}},
           "roles": [{"who": "e1", "role": "chief executive", "of": "e2"}],
           "quotes": [{"text": "we do not <comment>", "speaker": "e1", "form": "direct"}, {"text": "dropped one", "speaker": "e1"}],
           "events": [], "numbers": [{"text": "40-tonne", "measures": "weight"}], "sentiment": [], "later_section": [1]}


class Store:
    def __init__(self, reading=None):
        self.reading = reading

    def get(self, key):
        from support import reader as rd
        if self.reading is None:
            raise rd.MissingReading(f"no stored reading for {key}")
        return rd.Reading(document="a" * 64, page=1, reader="registers.news.read 5", model="qwen38-27b", settings={},
                          profile="news-article", profile_version=1, read_from="text",
                          text=__import__("json").dumps(self.reading), serving="a7a2b6080e776d68", commit="511a2627aa")


class InspConn:
    def __init__(self):
        self.calls = 0

    def execute(self, sql, params=None):
        if "FROM pub.news_read_items" in sql:
            rows = [("quotes", 0, True, False, "a speaker named and the words in the text"),
                    ("quotes", 1, False, False, "the words are not in the text"), ("roles", 0, True, False, "kept")]
            return type("C", (), {"fetchall": lambda _s: rows})()
        if "WHERE url_key = %s" in sql:
            cols = ["url_key", "url", "host", "title", "author", "published_at", "read_at", "outcome", "model", "reader",
                    "gates", "seconds", "reading_key", "skipped_why"]
            row = ("rnz.co.nz/a", "https://www.rnz.co.nz/a", "rnz.co.nz", "Fonterra says", "A Writer", T, T, "read",
                   "qwen38-27b", "registers.news.read 5", "registers.news.gates 2", 36.2, "k/1", None)
            return type("C", (), {"description": [Col(c) for c in cols], "fetchone": lambda _s: row})()
        return Conn([ROW]).execute(sql, params)


def test_a_headline_opens_the_inspector_with_every_section_names_for_numbers_and_the_gates():
    html = news.render(InspConn(), {"open": ["rnz.co.nz/a"]}, store=Store(READING))
    assert 'class="nw-split open"' in html and 'class="nw-insp"' in html
    assert "/news?sort=read&amp;dir=desc&amp;open=rnz.co.nz%2Fa" in html, "the headline in the list opens its inspector"
    pane = html[html.index('class="nw-insp"'):]
    for sec in ("article", "entities (2)", "roles (1)", "quotes (2)", "numbers (1)", "later_section (1)", "raw"):
        assert f"<h3>{sec}</h3>" in pane, sec
    assert "Richard Allen (person)" in pane and "Fonterra (organisation)" in pane, "entity numbers written as names"
    assert "forms in the article" in pane, "the entities table names its columns"
    assert "<q>we do not &lt;comment&gt;</q>" in pane
    assert "[kept: a speaker named and the words in the text]" in pane and "[dropped: the words are not in the text]" in pane
    assert "serving a7a2b6080e776d68" in pane and "36 s" in pane
    assert pane.index("<h3>quotes") < pane.index("<h3>later_section"), "the known sections first, a new one after"


def test_a_reading_missing_from_the_store_is_said():
    pane = news.inspector(InspConn(), "rnz.co.nz/a", news.args({}), Store(None))
    assert "the stored reading could not be opened: MissingReading" in pane and "Fonterra says" in pane


def test_the_live_inspector_opens_a_real_reading():
    from products.board import db
    with db.read_connect() as conn:
        key = conn.execute("SELECT url_key FROM pub.news_read WHERE outcome = 'read' ORDER BY read_at DESC LIMIT 1").fetchone()[0]
        html = news.render(conn, {"open": [key]})
    pane = html[html.index('class="nw-insp"'):]
    assert "could not be" not in pane and "<h3>entities" in pane and "<h3>quotes" in pane
