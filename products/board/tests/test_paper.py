"""The paper tab (paper.py): the newest read articles as a newspaper, pictures from the publishers' pages."""
from __future__ import annotations

import datetime as dt
import json

import pytest

from products.board import paper

T = dt.datetime(2026, 11, 26, 14, 8, tzinfo=dt.timezone.utc)
COLS = ["url_key", "url", "host", "title", "author", "published_at", "reading_key", "capture_sha256", "opening",
        "quotes_kept", "roles_kept"]


class Col:
    def __init__(self, n):
        self.name = n


class Conn:
    def __init__(self, n):
        self.rows = [(f"rnz.co.nz/{i}", f"https://www.rnz.co.nz/{i}", "rnz.co.nz", f"Story <{i}>", "A Writer",
                      T - dt.timedelta(hours=i), f"k/{i}", "", f"Story <{i}>. The first sentence is here. The second one.", 1, 0)
                     for i in range(n)]

    def execute(self, sql, params=None):
        rows = self.rows
        return type("C", (), {"description": [Col(c) for c in COLS], "fetchall": lambda _s: rows})()


class Store:
    def get(self, key):
        i = int(key.split("/")[1])
        th = [["business and finance"], ["crime and law"], ["Rugby union"], [], ["something odd"]][i % 5]
        ents = {"e1": {"name": "Fonterra", "kind": "organisation", "forms": ["Fonterra"]},
                "e2": {"name": "Miles Hurrell", "kind": "person", "forms": ["Miles Hurrell", "Hurrell"]},
                "e3": {"name": "$40m", "kind": "money", "forms": ["$40m"]}} if i % 2 == 0 else {}
        return type("R", (), {"text": json.dumps({"article": {"themes": th}, "entities": ents})})()


@pytest.fixture(autouse=True)
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(paper, "PICTURES", str(tmp_path / "pictures.jsonl"))
    monkeypatch.setattr(paper, "_FOUND", None)
    monkeypatch.setattr(paper, "_SHOWN", {})


def test_the_paper_sets_a_front_page_then_desks_each_story_opening_the_original():
    html = paper.render(Conn(20), Store())
    assert "The Daily Register" in html and 'data-tab="paper"' in html
    for d in ("front page", "business", "crime and justice", "sport", "more news"):
        assert f"<h2>{d}</h2>" in html, d
    assert html.index("<h2>business</h2>") < html.index("<h2>sport</h2>") < html.index("<h2>more news</h2>")
    assert 'href="https://www.rnz.co.nz/0" target="_blank"' in html and "Story &lt;0&gt;" in html
    assert html.count('class="pp-story') == 20 and 'class="pp-story lead"' in html
    assert "<p>The first sentence is here. The second one.</p>" in html, "the blurb leaves off the repeated headline"
    assert "/paper/picture?k=rnz.co.nz%2F0" in html


def test_a_picture_is_found_once_from_the_page_head_and_only_for_a_story_shown():
    calls = []

    class F:
        status, blocked, final_url = 200, "", "https://www.rnz.co.nz/0"
        body = b'<html><head><meta property="og:image" content="/img/a.jpg?w=1&amp;h=2"></head>'

    def open_url(url, **kw):
        calls.append(url)
        return F()
    assert paper.picture("rnz.co.nz/0", open_url=open_url) is None and not calls, "not shown: nothing fetched"
    paper.stories(Conn(1), Store())
    assert paper.picture("rnz.co.nz/0", open_url=open_url) == "https://www.rnz.co.nz/img/a.jpg?w=1&h=2"
    assert paper.picture("rnz.co.nz/0", open_url=open_url) == "https://www.rnz.co.nz/img/a.jpg?w=1&h=2"
    assert calls == ["https://www.rnz.co.nz/0"], "the page is read once"
    paper._FOUND = None
    assert paper.picture("rnz.co.nz/0", open_url=lambda *a, **k: 1 / 0) == "https://www.rnz.co.nz/img/a.jpg?w=1&h=2", "kept on disk"


def test_a_failed_read_or_a_page_with_no_picture_is_none_and_kept():
    paper.stories(Conn(2), Store())

    class Blocked:
        status, blocked, final_url, body = 403, "HTTP 403", "", b""

    def refused(url, **kw):
        raise RuntimeError("Refused: held")
    assert paper.picture("rnz.co.nz/0", open_url=lambda u, **k: Blocked()) is None
    assert paper.picture("rnz.co.nz/1", open_url=refused) is None
    lines = [json.loads(x) for x in open(paper.PICTURES)]
    assert [x["picture"][:5] for x in lines] == ["none:", "none:"]


def test_our_captured_copy_is_read_before_the_site():
    paper._SHOWN["rnz.co.nz/9"] = ("https://www.rnz.co.nz/9", "ab" * 32)
    got = paper.picture("rnz.co.nz/9", read_capture=lambda sha: b'<meta name="twitter:image" content="http://x.nz/p.png">',
                        open_url=lambda *a, **k: 1 / 0)
    assert got == "https://x.nz/p.png"


def test_a_story_carries_its_desk_site_and_names_and_a_tag_shows_only_those_stories():
    html = paper.render(Conn(20), Store())
    assert '<a class="desk" href="/paper?desk=business">business</a>' in html
    assert '<a class="site" href="/paper?site=rnz.co.nz">rnz.co.nz</a>' in html
    assert '<a href="/paper?name=Miles+Hurrell">Miles Hurrell</a><a href="/paper?name=Fonterra">Fonterra</a>' in html, \
        "the most often named first; a sum of money is not a tag"
    assert "$40m</a>" not in html and '<nav class="pp-nav">' in html
    one = paper.render(Conn(20), Store(), qs={"name": ["miles hurrell"]})
    assert one.count('class="pp-story') == 10 and "10 stories, name <b>miles hurrell</b> among the newest 800" in one
    assert "<h2>front page</h2>" not in one
    sport = paper.render(Conn(20), Store(), qs={"desk": ["sport"]})
    assert sport.count('class="pp-story') == 4 and '<a class="on" href="/paper?desk=sport">' in sport


def test_a_site_is_asked_of_the_database():
    c = Conn(3)
    seen = []
    ex = c.execute
    c.execute = lambda sql, params=None: (seen.append((sql, params)), ex(sql, params))[1]
    paper.render(c, Store(), qs={"site": ["RNZ.co.nz"]})
    assert "AND host = %s" in seen[0][0] and seen[0][1] == ["rnz.co.nz", paper.STORIES]


def test_the_live_paper_sets():
    from products.board import db
    with db.read_connect() as conn:
        html = paper.render(conn)
        biz = paper.render(conn, qs={"desk": ["business"]})
    assert "could not be set" not in html and html.count('class="pp-story') > 10
    assert "could not be set" not in biz and 'class="pp-tags"' in html
