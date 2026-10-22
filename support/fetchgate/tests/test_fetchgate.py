"""The gate under hard limits 4 to 9: held hosts refused before any knock,
no position on file refused, a publisher's stop honoured, robots read for a
crawl delay only (never a permission), the slowest floor binds, the pacer
blocks per host, one User-Agent, a challenge is a failed read, every
decision recorded. The old gate's floor, pacing and one-agent cases are
carried."""
import json
import os

import pytest

import support.fetchgate as fg


@pytest.fixture
def positions(tmp_path):
    d = tmp_path / "positions"
    d.mkdir()
    (d / "README.md").write_text("# positions\n")
    (d / "electoral-commission.md").write_text("# Electoral Commission filings\nhosts: elections.nz, www.elections.nz\n\nOpen; public filings...\n")
    (d / "gazette.md").write_text("# The Gazette\nclass: gazette\nhosts: gazette.govt.nz\n")
    return str(d)


def robots(host="example.org", text="", unreadable=False, delay=None):
    return fg.Robots(host, text, 0 if unreadable else 200, unreadable,
                     fg.crawl_delay_of(text) if delay is None else delay, "2026-10-18T02:00:00+13:00", "")


# ── refusals ──────────────────────────────────────────────────────────────────

def test_a_held_host_is_refused_whatever_else_is_true():
    d = fg.decide("https://www.nzherald.co.nz/nz/x", robots("www.nzherald.co.nz"), position="news")
    assert not d.allowed and "ruling 12" in d.reason
    assert not fg.decide("https://fyi.org.nz/request/1", None, "oia").allowed
    assert not fg.decide("https://cdn.oneroof.co.nz/a", None, "x").allowed       # a subdomain is not the way back in


def test_a_held_host_is_not_even_sent_a_robots_request(tmp_path):
    knocked = []
    with pytest.raises(fg.Refused):
        fg.check("https://www.nzherald.co.nz/x", fetch=lambda u, t: knocked.append(u) or (200, b""),
                 positions_dir=str(tmp_path), ledger_dir=str(tmp_path / "l"))
    assert knocked == []


def test_no_position_on_file_is_refused(positions, tmp_path):
    d = fg.decide("https://unknown.example/x", robots("unknown.example"), fg.position_for("unknown.example", positions))
    assert not d.allowed and "hard limit 9" in d.reason and "docs/legal/positions" in d.reason
    knocked = []
    with pytest.raises(fg.Refused):
        fg.check("https://unknown.example/x", fetch=lambda u, t: knocked.append(u) or (200, b""), positions_dir=positions,
                 ledger_dir=str(tmp_path / "l"))
    assert knocked == []                      # no position, no knock


def test_a_position_covers_its_hosts_and_their_subdomains(positions):
    assert fg.position_for("www.elections.nz", positions) == "electoral-commission"
    assert fg.position_for("elections.nz", positions) == "electoral-commission"
    assert fg.position_for("api.gazette.govt.nz", positions) == "gazette"
    assert fg.position_for("stuff.co.nz", positions) is None


def test_a_publishers_request_to_stop_is_honoured(monkeypatch):
    monkeypatch.setitem(fg.STOP_REQUESTS, "example.org", "email of 2026-10-01")
    d = fg.decide("https://example.org/x", robots(), "news")
    assert not d.allowed and "asked us to stop" in d.reason
    assert not fg.decide("https://sub.example.org/x", robots(), "news").allowed


# ── robots: a record and a crawl delay, never a permission ───────────────────

def test_a_disallow_is_not_a_refusal_but_a_crawl_delay_binds():
    r = robots(text="User-agent: *\nDisallow: /\nCrawl-delay: 30\n")
    d = fg.decide("https://example.org/private/x", r, "news")
    assert d.allowed and d.floor == 30.0 and "crawl delay 30s honoured" in d.reason


def test_an_unreadable_robots_is_not_a_refusal_but_the_polite_floor_applies():
    d = fg.decide("https://example.org/x", robots(unreadable=True), "news")
    assert d.allowed and d.floor == fg.POLITE_FLOOR_S and "could not be read" in d.reason


def test_read_robots_archives_the_file_and_reads_its_delay(tmp_path):
    r = fg.read_robots("example.org", fetch=lambda u, t: (200, b"User-agent: QueryNZ\nCrawl-delay: 7\nUser-agent: *\nCrawl-delay: 2\n"),
                       archive_dir=str(tmp_path))
    assert r.crawl_delay == 7.0 and r.sha256 and os.listdir(str(tmp_path))[0].startswith("example.org.")
    assert fg.read_robots("example.org", fetch=lambda u, t: (404, b""), archive_dir=str(tmp_path)).crawl_delay == 0.0
    assert fg.read_robots("example.org", fetch=lambda u, t: (503, b""), archive_dir=str(tmp_path)).unreadable
    assert fg.read_robots("example.org", fetch=lambda u, t: (_ for _ in ()).throw(TimeoutError()), archive_dir=str(tmp_path)).unreadable


# ── floors and pacing (carried) ──────────────────────────────────────────────

def test_a_stated_floor_binds_and_beats_a_faster_default():
    assert fg.floor_for("greaterauckland.org.nz") >= 30.0
    assert fg.floor_for("www.greaterauckland.org.nz") >= 30.0


def test_the_slowest_of_the_stated_floor_and_the_crawl_delay_wins():
    assert fg.floor_for("example.org", robots(delay=30.0)) >= 30.0
    assert fg.floor_for("greaterauckland.org.nz", robots("greaterauckland.org.nz", delay=2.0)) >= 30.0
    assert fg.floor_for("example.org", robots(delay=100000.0)) == fg.MAX_FLOOR_S


def test_every_host_has_a_floor_even_with_no_robots_and_no_table_row():
    assert fg.floor_for("unknown.example") > 0


def test_pacing_blocks_rather_than_logs():
    clock = {"t": 1000.0}
    slept = []

    def sleep(s):
        slept.append(s)
        clock["t"] += s
    g = fg.Pacer(now=lambda: clock["t"], sleep=sleep)
    g.wait("example.org", 120.0)
    clock["t"] += 1.5
    g.wait("example.org", 120.0)
    assert slept and slept[-1] >= 118.0


def test_pacing_is_per_host_and_rotation_never_resets_it():
    clock = {"t": 0.0}
    g = fg.Pacer(now=lambda: clock["t"], sleep=lambda s: clock.__setitem__("t", clock["t"] + s))
    g.wait("a.example", 60.0)
    g.wait("b.example", 60.0)
    assert clock["t"] == 0.0
    for _ in range(4):
        g.wait("example.org", 120.0)
    assert clock["t"] >= 360.0


def test_one_user_agent():
    assert fg.UA.startswith("QueryNZ/1.0") and fg.OUR_TOKEN in fg.UA


# ── the read itself ──────────────────────────────────────────────────────────

def test_a_challenge_or_block_is_a_failed_read_and_a_404_is_an_answer(positions, tmp_path):
    pacer = fg.Pacer(now=lambda: 0.0, sleep=lambda s: None)
    kw = dict(positions_dir=positions, ledger_dir=str(tmp_path / "l"), pacer=pacer)
    fg._ROBOTS["www.elections.nz"] = robots("www.elections.nz")
    got = fg.open_url("https://www.elections.nz/x", fetch=lambda u, t: (403, b"", u), **kw)
    assert got.blocked.startswith("HTTP 403")
    got = fg.open_url("https://www.elections.nz/x", fetch=lambda u, t: (200, b"<html><title>Just a moment...</title>cf-chl", u), **kw)
    assert "challenge page" in got.blocked
    got = fg.open_url("https://www.elections.nz/gone", fetch=lambda u, t: (404, b"", u), **kw)
    assert got.status == 404 and got.blocked == ""
    got = fg.open_url("https://www.elections.nz/ok", fetch=lambda u, t: (200, b"<html>a page</html>", u), **kw)
    assert got.status == 200 and got.body and got.blocked == ""
    rows = [json.loads(l) for f in os.listdir(tmp_path / "l") for l in open(tmp_path / "l" / f)]
    assert len(rows) == 4 and all(r["allowed"] and r["position"] == "electoral-commission" for r in rows)


def test_every_decision_carries_what_it_decided_and_why(tmp_path):
    d = fg.decide("https://www.elections.nz/x", robots("www.elections.nz"), "electoral-commission")
    fg.record(d, str(tmp_path))
    row = json.loads(open(os.path.join(str(tmp_path), os.listdir(str(tmp_path))[0])).read())
    assert row["allowed"] and row["reason"] and row["host"] == "www.elections.nz" and row["at"]


# ── Imperva's interstitial and redirects (grants-1, 21 October) ─────────────

INTERSTITIAL = (b"<!DOCTYPE html><html><head><title>Pardon Our Interruption</title>"
                b"<script>window.reeseSkipExpirationCheck = true;</script>"
                b"<script src=\"/Ifed-the-Swoud-Sath-on-the-Goule-of-Ile\" async></script></head>"
                b"<body><h1>Pardon Our Interruption</h1><p>As you were browsing something about your browser "
                b"made us think you were a bot.</p></body></html>")


@pytest.fixture
def gated(positions, tmp_path, monkeypatch):
    for h in ("www.elections.nz", "elections.nz", "gazette.govt.nz", "127.0.0.1", "localhost"):
        monkeypatch.setitem(fg._ROBOTS, h, robots(h))
    return dict(positions_dir=positions, ledger_dir=str(tmp_path / "l"), pacer=fg.Pacer(now=lambda: 0.0, sleep=lambda s: None))


def test_an_imperva_interstitial_answered_200_is_a_failed_read(gated):
    got = fg.open_url("https://www.elections.nz/x", fetch=lambda u, t: (200, INTERSTITIAL, u, {"X-SPA-INTERSTITIAL": "1"}), **gated)
    assert got.status == 200 and got.blocked
    assert "pardon our interruption" in fg.looks_challenged(200, INTERSTITIAL)          # the page alone
    assert "X-SPA-INTERSTITIAL" in fg.looks_challenged(200, b"<html></html>", {"X-SPA-INTERSTITIAL": "1"})  # the header alone


def test_a_real_page_carrying_the_imperva_script_is_not_a_challenge():
    page = b"<html><head><title>Datasets</title><script src=\"/reese84.js?d=x\"></script></head><body>rows</body></html>"
    assert fg.looks_challenged(200, page, {"Content-Type": "text/html"}) == ""


def test_a_redirect_is_returned_not_followed_and_the_other_host_is_never_asked(gated):
    asked = []

    def fetch(u, t):
        asked.append(u)
        return (302, b"", u, {"Location": "https://unnamed.example/elsewhere"})
    got = fg.open_url("https://www.elections.nz/x", fetch=fetch, **gated)
    assert asked == ["https://www.elections.nz/x"]
    assert got.status == 302 and got.location == "https://unnamed.example/elsewhere"
    assert got.final_url == "https://www.elections.nz/x" and got.blocked == ""


def test_following_is_asked_for_and_every_hop_is_judged(gated, tmp_path):
    hops = {"https://www.elections.nz/a": (301, b"", "https://www.elections.nz/a", {"location": "/b"}),
            "https://www.elections.nz/b": (302, b"", "https://www.elections.nz/b", {"Location": "https://unnamed.example/c"})}
    asked = []

    def fetch(u, t):
        asked.append(u)
        return hops.get(u, (200, b"<html>ok</html>", u, {}))
    with pytest.raises(fg.Refused, match="unnamed.example"):
        fg.open_url("https://www.elections.nz/a", fetch=fetch, follow=5, **gated)
    assert asked == ["https://www.elections.nz/a", "https://www.elections.nz/b"]      # no knock on the unnamed host
    hops["https://www.elections.nz/b"] = (302, b"", "", {"Location": "https://gazette.govt.nz/c"})
    got = fg.open_url("https://www.elections.nz/a", fetch=fetch, follow=5, **gated)
    assert got.status == 200 and got.final_url == "https://gazette.govt.nz/c" and got.url == "https://www.elections.nz/a"
    got = fg.open_url("https://www.elections.nz/a", fetch=fetch, follow=1, **gated)
    assert got.status == 302 and got.location == "https://gazette.govt.nz/c"         # out of hops: returned, not taken
    rows = [json.loads(l) for f in os.listdir(tmp_path / "l") for l in open(tmp_path / "l" / f)]
    assert [r["host"] for r in rows][-2:] == ["www.elections.nz", "www.elections.nz"]
    assert any(r["host"] == "unnamed.example" and not r["allowed"] for r in rows)


def test_urllib_itself_does_not_follow_a_redirect(gated, positions):
    """The real transport, on loopback: the answer from 127.0.0.1 points at
    localhost, which no position names. The old open_url let urllib go there."""
    import http.server
    import threading
    with open(os.path.join(positions, "loopback.md"), "w") as f:
        f.write("# loopback\nhosts: 127.0.0.1\n")
    went = []

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            went.append(self.headers.get("Host"))
            if self.path == "/x":
                self.send_response(302)
                self.send_header("Location", f"http://localhost:{self.server.server_port}/landed")
                self.end_headers()
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"from another host")

        def log_message(self, *a):
            pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        got = fg.open_url(f"http://127.0.0.1:{srv.server_port}/x", timeout=5, **gated)
        assert got.status == 302 and got.location.endswith("/landed") and got.body == b""
        assert len(went) == 1
        with pytest.raises(fg.Refused, match="localhost"):
            fg.open_url(f"http://127.0.0.1:{srv.server_port}/x", timeout=5, follow=3, **gated)
        assert len(went) == 2
    finally:
        srv.shutdown()


def test_a_redirect_within_the_host_is_followed_by_default_and_a_fourth_hop_is_not(gated):
    """Integrator, at the merge of fix-support-fetchgate-1: the host asked was judged, so http to https or a trailing slash on
    the same host is followed (each hop paced and recorded); another host is still returned unfollowed."""
    asked = []

    def fetch(u, t):
        asked.append(u)
        if u.endswith("/x"):
            return (301, b"", u, {"Location": "https://www.elections.nz/x/"})
        return (200, b"<html>page</html>", u, {})
    got = fg.open_url("https://www.elections.nz/x", fetch=fetch, **gated)
    assert asked == ["https://www.elections.nz/x", "https://www.elections.nz/x/"]
    assert got.status == 200 and got.location == "" and got.blocked == ""

    def loop(u, t):
        return (302, b"", u, {"Location": "https://www.elections.nz/again"})
    got = fg.open_url("https://www.elections.nz/x", fetch=loop, **gated)
    assert got.status == 302 and got.location == "https://www.elections.nz/again"

    def away(u, t):
        return (302, b"", u, {"Location": "https://unnamed.example/elsewhere"})
    got = fg.open_url("https://www.elections.nz/x", fetch=away, **gated)
    assert got.status == 302 and got.location == "https://unnamed.example/elsewhere"


# ── a block is known by its own page, not a word on a page of content (councils-1, 22 October) ──

def listing_like_christchurch():
    """The shape of christchurch.infocouncil.biz on 22 October, not its bytes: a 200 of about 795,737 bytes, the
    word `captcha` in a form's script inside the first 4,096 bytes, and 237 minutes links."""
    head = (b"<!DOCTYPE html><html><head><title>Christchurch City Council - Meetings</title>"
            b"<script src=\"/scripts/contact-form-captcha.js\"></script>"
            b"<script>var captchaKey = 'form';</script></head><body><table>")
    rows = b"".join(b"<tr><td>Council %d</td><td><a href=\"/Open/2026/10/CNCL_2026%04d_MIN_%d.PDF\">Minutes</a></td></tr>"
                    % (i, i, i) for i in range(237))
    page, tail = head + rows + b"<!-- ", b" --></table></body></html>"
    return page + b"x" * (795_737 - len(page) - len(tail)) + tail


def test_a_listing_carrying_the_content_asked_for_is_not_a_challenge_for_a_word_in_its_script(gated):
    page = listing_like_christchurch()
    assert len(page) == 795_737 and page.count(b"_MIN_") == 237 and b"captcha" in page[:4096]
    assert fg.looks_challenged(200, page, {"Content-Type": "text/html"}) == ""
    got = fg.open_url("https://www.elections.nz/listing", fetch=lambda u, t: (200, page, u, {}), **gated)
    assert got.status == 200 and got.blocked == "" and got.body == page


def test_every_block_page_the_gate_knows_is_still_a_failed_read():
    pages = {
        "cloudflare challenge": b"<!DOCTYPE html><html><head><title>Just a moment...</title><style>"
                                + b"b{}" * 9000 + b"</style></head><body><script>window._cf_chl_opt={}</script></body></html>",
        "cloudflare block": b"<html><head><title>Attention Required! | Cloudflare</title></head>"
                            b"<body><div id=\"cf-error-details\">Sorry, you have been blocked</div></body></html>",
        "incapsula": b"<html style=\"height:100%\"><head><META NAME=\"ROBOTS\" CONTENT=\"NOINDEX, NOFOLLOW\"></head>"
                     b"<body><iframe id=\"main-iframe\" src=\"/_Incapsula_Resource?CWUDNSAI=9&xinfo=1\">"
                     b"Request unsuccessful. Incapsula incident ID: 1-2</iframe></body></html>",
        "imperva": INTERSTITIAL,
        "radware": b"<html><head><title>Radware Captcha Page</title></head><body><form>"
                   b"<div class=\"g-recaptcha\"></div></form></body></html>",
    }
    for name, page in pages.items():
        assert fg.looks_challenged(200, page), name
    assert len(pages["cloudflare challenge"]) > 4096                  # the title is found past the first 4,096 bytes
    # the title is the block page's own landmark, whatever the page weighs
    big = b"<html><head><title>Just a moment...</title></head><body>" + b"x" * 900_000 + b"</body></html>"
    assert "title" in fg.looks_challenged(200, big)
    # and a small page with a block's mark near its top is still a challenge, as before
    assert fg.looks_challenged(200, b"<html><body>Are you a human? captcha</body></html>")


# ── response headers, and 304 is "unchanged" (societies, 20 October) ─────────

def test_fetched_carries_the_headers_as_sent_and_old_callers_still_build_it(gated):
    assert fg.Fetched("u", 200, b"", "u", "", "").headers == {}                # a field with a default
    got = fg.open_url("https://www.elections.nz/e", fetch=lambda u, t: (200, b"<html>x</html>", u, {"ETag": "\"v1\""}), **gated)
    assert got.headers == {"ETag": "\"v1\""} and not got.unchanged


def test_a_304_is_unchanged_with_no_body_and_not_a_block_on_the_real_transport(gated, positions):
    import http.server
    import threading
    with open(os.path.join(positions, "loopback.md"), "w") as f:
        f.write("# loopback\nhosts: 127.0.0.1\n")
    seen = []

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.headers.get("If-None-Match"))
            if self.headers.get("If-None-Match") == "\"v1\"":
                self.send_response(304)
                self.send_header("ETag", "\"v1\"")
                self.end_headers()
                return
            body = b"{\"entity\": 1}"
            self.send_response(200)
            self.send_header("ETag", "\"v1\"")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{srv.server_port}/entity"
        first = fg.open_url(url, timeout=5, **gated)
        assert first.status == 200 and first.headers.get("ETag") == "\"v1\"" and not first.unchanged
        again = fg.open_url(url, timeout=5, headers={"If-None-Match": first.headers["ETag"]}, **gated)
        assert again.status == 304 and again.unchanged and again.body == b"" and again.blocked == ""
        assert again.headers.get("ETag") == "\"v1\"" and seen == [None, "\"v1\""]
    finally:
        srv.shutdown()
