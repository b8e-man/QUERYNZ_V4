import datetime as dt

from registers.news import load

D = dt.date


def test_a_site_the_provider_has_not_delivered_stays_old_only():
    assert load.judge(100, D(2026, 11, 16), 0, None, None, 0, False)[0] == "old only"


def test_a_site_is_ready_when_the_provider_is_current_and_reaches_back_to_the_old_copy():
    assert load.judge(100, D(2026, 11, 16), 40, D(2026, 11, 15), D(2026, 11, 17), 12, False)[0] == "ready"


def test_a_hole_between_the_old_copy_and_the_provider_is_a_gap():
    state, why = load.judge(100, D(2026, 11, 1), 40, D(2026, 11, 14), D(2026, 11, 17), 12, False)
    assert state == "providing, gap" and "13 days" in why


def test_a_provider_with_nothing_this_week_is_not_providing():
    assert load.judge(100, D(2026, 11, 1), 5, D(2026, 10, 1), D(2026, 11, 2), 0, False)[0] == "providing, gap"


def test_a_retired_site_says_so_whatever_else_holds():
    assert load.judge(100, D(2026, 11, 1), 0, None, None, 0, True)[0] == "retired"


def test_a_site_whose_provider_pages_are_stubs_is_never_ready():
    state, why = load.judge(100, D(2026, 11, 16), 40, D(2026, 11, 15), D(2026, 11, 17), 12, False, 40, 3)
    assert state == "providing, stubs" and "3 of" in why
    assert load.judge(100, D(2026, 11, 16), 40, D(2026, 11, 15), D(2026, 11, 17), 12, False, 40, 2)[0] == "ready"


def test_a_paywall_prompt_at_the_end_is_a_stub():
    assert load.is_stub("The council voted on Tuesday. " * 20 + "Already a subscriber? Sign in to continue reading")
    assert not load.is_stub("The council voted on Tuesday. " * 20)


def test_an_undated_site_is_ready_only_when_the_provider_holds_every_old_address():
    assert load.judge(87, None, 88, None, None, 0, False, 88, 0, 87)[0] == "ready"
    state, why = load.judge(2845, None, 75, None, None, 0, False, 75, 0, 73)
    assert state == "providing, gap" and "73 of" in why
    assert load.judge(87, None, 88, None, None, 0, False, 88, 9, 87)[0] == "providing, stubs"


def test_a_site_held_elsewhere_is_ready_only_when_every_old_address_is_there():
    # Arthur, 20 November 2026: "count as new copy but check it is the same as the copy it is replaceing"
    assert load.judge(137, None, 1999, None, None, 0, False, 0, 0, 137, "hansard")[0] == "ready"
    state, why = load.judge(53, None, 20106, None, None, 0, False, 0, 0, 3, "courts")
    assert state == "held elsewhere, gap" and "50 missing" in why
    assert load.judge(869, None, 0, None, None, 0, False, 0, 0, 0, "disclosure statements")[0] == "held elsewhere, gap"
    assert load.judge(16, None, 16, None, None, 0, True, 0, 0, 16, "courts")[0] == "retired"


def test_the_parser_is_the_sites_own_then_a_parent_domains_then_the_generic():
    assert load.parser_for("www.rnz.co.nz")[0] == "rnzscraper"
    assert load.parser_for("1news.co.nz")[0] == "onenews"
    assert load.parser_for("nowhere.example.nz")[0] == "genericrss"


def test_the_parsers_fetch_nothing():
    import pathlib
    here = pathlib.Path(load.__file__).parent / "extract"
    for f in here.glob("*.py"):
        src = f.read_text()
        assert "make_client(" not in src.replace("def make_client", "") or f.name == "base.py", f.name
    assert "httpx" not in (here / "base.py").read_text()


def test_only_a_ready_site_is_listed_and_logging_waits_for_the_old_registry(tmp_path):
    from registers.news import retire

    class Conn:
        def __init__(self):
            self.logged = []

        def execute(self, sql, args=None):
            conn = self

            class R:
                rowcount = 1

                def fetchall(self):
                    return [("scoop.co.nz",), ("stuff.co.nz",)]
            if sql.startswith("INSERT"):
                conn.logged.append(args[0])
            return R()

    path = str(tmp_path / "retired.txt")
    c = Conn()
    out = retire.retire(c, ["scoop.co.nz", "rnz.co.nz"], path=path, reads=False)
    assert out["listed"] == ["scoop.co.nz"] and out["not ready"] == ["rnz.co.nz"] and not c.logged
    out = retire.retire(c, None, path=path, reads=True)
    assert out["listed"] == ["stuff.co.nz"] and c.logged == ["scoop.co.nz", "stuff.co.nz"]


def test_the_stuff_mastheads_are_read_from_their_json():
    import json
    from registers.news.extract import stuffmasthead
    assert load.parser_for("www.thepress.co.nz")[0] == "stuffmasthead"
    page = json.dumps({"content": {"title": "A title", "contentBody": {"body": "<p>" + "The board met on Monday. " * 5
                                                                        + "</p><p>It voted to sell the land.</p>"}},
                       "author": [{"name": "A Writer"}], "publishedDate": "2026-11-15T23:08:35Z",
                       "metadata": {"section": "NZ news", "topic": ["Councils"]}})
    x = stuffmasthead.extract(page, "https://www.thepress.co.nz/nz-news/1/a")
    assert x.title == "A title" and "sell the land" in x.text and x.author == "A Writer"
    assert x.published_at.year == 2026 and x.categories == ["NZ news", "Councils"]
    assert stuffmasthead.extract("<html></html>", "u") is None


def test_a_ready_site_the_old_registry_does_not_hold_is_reported_not_retired(tmp_path):
    from registers.news import retire

    class Conn:
        def execute(self, sql, args=None):
            class R:
                rowcount = 1

                def fetchall(self):
                    return [("gazette.govt.nz",), ("beehive.govt.nz",)]
            return R()

    out = retire.retire(Conn(), None, path=str(tmp_path / "r.txt"), reads=False, registry={"beehive.govt.nz"})
    assert out["listed"] == ["beehive.govt.nz"] and out["outside the registry"] == ["gazette.govt.nz"]


def test_the_lanes_with_their_own_source_count_only_their_new_rows():
    sql = " ".join(q for _, q in load.OTHER_SOURCES)
    assert "origin = 'mcp'" in sql and "DigitalNZ" in sql


KIWIBLOG = """<ul><li class="comment-li"><article id="comment-11" class="jumplink">
<div class="comment byuser comment-author-ann even depth-1"><div class="comdiv-a">
<header class="comment-author"><h3><a href="https://example.org/ann">Ann</a></h3></header>
<div class="comment-content"><div><p>First point.</p></div></div>
<footer class="comment-meta"><ul><li class="voting"><span id="karma-11-up">4</span><span id="karma-11-down">1</span></li>
<li class="comdate"><a href="#comment-11">November 8, 2026 3:37am</a></li></ul></footer></div></div></article>
<ul class="children"><li class="comment-li"><article id="comment-12"><div class="comment odd depth-2"><div>
<header class="comment-author"><h3>Bob</h3></header><div class="comment-content"><p>A reply.</p></div>
<footer><ul><li class="comdate">November 8, 2026 6:55am</li></ul></footer></div></div></article></li></ul></li></ul>"""

STANDARD = """<ol><li id="li-comment-21" class="comment byuser comment-author-weka depth-1 parent"><article id="comment-21">
<footer class="comment-meta"><div class="comment-author vcard"><img src="https://a/1"><cite class="fn">weka</cite></div>
<time datetime="2026-11-07T19:03:21+13:00">7 Nov</time></footer><div class="comment-content"><p>Hello.</p></div></article>
<ol class="children"><li id="li-comment-22" class="comment depth-2"><article id="comment-22"><footer class="comment-meta">
<div class="comment-author vcard"><cite class="fn">phil</cite></div><time datetime="2026-11-07T19:10:49+13:00">x</time>
</footer><div class="comment-content"><p>Hi.</p></div></article></li></ol></li></ol>"""


def test_wordpress_comments_keep_the_reply_chain_the_site_user_and_the_time():
    from registers.news.extract import wpcomments
    k = {c.comment_id: c for c in wpcomments.extract(KIWIBLOG)}
    assert k["11"].parent_id is None and k["12"].parent_id == "11"
    assert k["11"].author_slug == "ann" and k["11"].author_url == "https://example.org/ann" and k["12"].author_slug is None
    assert (k["11"].votes_up, k["11"].votes_down) == (4, 1) and k["12"].posted_at.hour == 6
    s = {c.comment_id: c for c in wpcomments.extract(STANDARD)}
    assert s["22"].parent_id == "21" and s["21"].author_slug == "weka" and s["22"].author_name == "phil"
    assert s["21"].posted_at.isoformat() == "2026-11-07T19:03:21+13:00" and s["21"].text == "Hello."
    assert wpcomments.extract("<p>no comments</p>") == []


def test_the_commenter_key_is_the_sites_mark_then_the_profile_link_then_the_name():
    from registers.news import comments
    from registers.news.extract.wpcomments import Comment
    c = Comment("1", None, "Ann B", "ann", "https://x", None, None, "t")
    assert comments.commenter_key(c) == ("user:ann", "site user")
    c.author_slug = None
    assert comments.commenter_key(c) == ("link:https://x", "profile link")
    c.author_url = None
    assert comments.commenter_key(c) == ("name:ann b", "display name")



def test_an_address_too_long_for_the_index_keys_as_its_head_and_a_hash():
    """22 Nov 2026: a 4,279-character act.org.nz address broke every load (the btree limit is 2,704 bytes)."""
    import os
    sql = open(os.path.join(os.path.dirname(load.__file__), "tables.sql"), encoding="utf-8").read()
    fn = sql.split("FUNCTION news_private.url_key", 1)[1].split("$$;", 1)[0]
    assert "length(k) > 1000" in fn and "left(k, 1000)" in fn and "md5(k)" in fn
