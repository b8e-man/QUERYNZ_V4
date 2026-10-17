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
