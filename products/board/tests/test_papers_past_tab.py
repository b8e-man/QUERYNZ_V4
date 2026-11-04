"""The papers past tab (Arthur, 5 November 2026), on the lane's search faked: the bar carries the tab, the tab's page carries
the query box, the hit count and the seconds, each hit's title, paper, date, window of text with the words marked, its
link to Papers Past and to the text held, and the pages; a failed search and an unknown article are said; every value is
escaped; the routes answer on the server and nothing is written."""
import contextlib
import datetime as dt
import http.client
import threading

import pytest

from products.board import db, panes, papers_past, server

HIT = {"key": "OW18620801.2.5", "paper": "OW", "published_on": dt.date(1862, 8, 1), "title": "The Gold <Escort>",
       "url": "https://paperspast.natlib.govt.nz/newspapers/OW18620801.2.5", "chars": 1234,
       "snippet": "… the gold escort left Dunedin …"}


def found(n=45, offset=0, hits=None):
    return {"query": "gold escort", "count": n, "hits": [HIT] * 20 if hits is None else hits, "seconds": 1.234,
            "index seconds": 1.1, "error": "", "limit": 20, "offset": offset}


def test_every_page_s_bar_carries_the_papers_past_tab():
    for tab in ("search", "uses", papers_past.TAB):
        page = panes.page("", [], [], tab=tab)
        assert 'href="/papers-past">papers past</a>' in page
        assert ('class="on" href="/papers-past"' in page) == (tab == papers_past.TAB)


def test_the_tab_shows_the_count_the_time_and_each_hit_with_its_links():
    html = papers_past.search_pane("gold escort", found())
    assert "1–20 of 45 articles" in html and "1.23 s" in html
    assert 'name="q" value="gold escort"' in html and f'action="{papers_past.PATH}"' in html
    assert 'href="https://paperspast.natlib.govt.nz/newspapers/OW18620801.2.5" target="_blank"' in html
    assert 'href="/papers-past/text?k=OW18620801.2.5&amp;q=gold+escort"' in html
    assert "The <mark>Gold</mark> &lt;<mark>Escort</mark>&gt;" in html, "the title escaped, the words asked marked"
    assert "<mark>gold</mark> <mark>escort</mark> left" in html and "OW, 1862-08-01, 1,234 characters" in html
    assert 'href="/papers-past?q=gold+escort&amp;o=20">next 20</a>' in html and "previous" not in html


def test_the_last_page_has_no_next_and_none_found_is_said():
    html = papers_past.search_pane("gold escort", found(n=45, offset=40, hits=[HIT] * 5))
    assert "41–45 of 45" in html and "previous 20" in html and "next 20" not in html
    assert "none found" in papers_past.search_pane("zzz", found(n=0, hits=[]))
    assert "the search could not answer: FileNotFoundError" in papers_past.search_pane("x", failed="FileNotFoundError: no index")


def test_one_article_s_text_is_shown_whole_with_the_words_marked():
    item = dict(HIT, text="Line one.\nThe gold escort <left>.")
    html = papers_past.text_pane(item, "escort")
    assert "<mark>escort</mark> &lt;left&gt;." in html and "on Papers Past" in html and 'class="text"' in html
    assert "no article by that id" in papers_past.text_pane(None)


class FakeConn:
    def close(self):
        pass


@pytest.fixture
def served(monkeypatch):
    asked = []
    monkeypatch.setattr(db, "read_connect", lambda: contextlib.nullcontext(FakeConn()))
    monkeypatch.setattr(server, "counter", lambda conn=None: None)
    monkeypatch.setattr(papers_past.pp, "search", lambda conn, q, limit, offset: asked.append((q, limit, offset)) or found(offset=offset))
    monkeypatch.setattr(papers_past.pp, "article", lambda conn, key: dict(HIT, text="whole text") if key == HIT["key"] else None)
    httpd = server.Server(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd.server_address[1], asked
    httpd.shutdown()
    httpd.server_close()


def get(port, path):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    c.request("GET", path)
    r = c.getresponse()
    return r.status, r.read().decode("utf-8")


def test_the_routes_answer_and_page_by_offset(served):
    port, asked = served
    status, body = get(port, "/papers-past?q=gold+escort&o=20")
    assert status == 200 and "21–40 of 45 articles" in body and asked == [("gold escort", 20, 20)]
    status, body = get(port, "/papers-past")
    assert status == 200 and "Search Papers Past" in body and len(asked) == 1, "no query, no search"
    assert get(port, "/papers-past/text?k=OW18620801.2.5")[1].count("whole text") == 1
    assert "no article by that id" in get(port, "/papers-past/text?k=XX1")[1]
    assert get(port, "/papers-past/text")[0] == 404
