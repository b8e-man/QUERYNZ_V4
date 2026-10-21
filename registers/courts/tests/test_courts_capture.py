"""The capture job on fakes: no network, no database. The feed and page
shapes are invented in the form the old estate's scraper read."""
import datetime as dt
from dataclasses import dataclass

import pytest

import support.fetchgate as fg
from registers.courts import capture as C

RSS = """<rss><channel><title>Supreme Court</title><link>https://www.courtsofnz.govt.nz/judgments/supreme-court/</link>
<item><link>https://www.courtsofnz.govt.nz/cases/example-v-sample</link></item>
<item><link>https://www.courtsofnz.govt.nz/cases/test-v-r</link></item>
<item><link>https://www.courtsofnz.govt.nz/cases/example-v-sample</link></item></channel></rss>"""
PAGE = """<a href="/assets/cases/2099/2099-NZSC-7.pdf">Judgment</a>
<a href="/assets/cases/2099/MR-2099-NZSC-7.pdf">Media release</a>
<a href="/assets/cases/2099/2099-NZSC-7.pdf">again</a>"""


def test_the_feed_gives_each_case_page_once_in_order():
    assert C.case_links(RSS) == ["https://www.courtsofnz.govt.nz/cases/example-v-sample",
                                 "https://www.courtsofnz.govt.nz/cases/test-v-r"]


def test_a_case_page_gives_the_judgment_never_the_media_release():
    assert C.judgment_pdfs(PAGE) == [("[2099] NZSC 7", "https://www.courtsofnz.govt.nz/assets/cases/2099/2099-NZSC-7.pdf")]


def test_the_listed_judgments_whose_file_is_gone_are_queued_by_their_url():
    entries = [{"source": "courtsofnz.govt.nz", "url": "https://www.courtsofnz.govt.nz/assets/cases/2099/2099-NZHC-12.pdf",
                "old_path": "/nonexistent/x"},
               {"source": "waitangitribunal.govt.nz", "url": "https://forms.justice.govt.nz/x.pdf", "old_path": "/nonexistent/y"}]
    assert C.missing_from_listing(entries) == [("[2099] NZHC 12", entries[0]["url"])]


@dataclass
class Ref:
    sha256: str


class FakeTables:
    def __init__(self):
        self.caps, self.logs, self.feeds = {}, [], []

    def held(self, url):
        return bool(self.caps.get(url, {}).get("doc"))

    def found(self, citation, url, via):
        self.caps.setdefault(url, {"citation": citation, "via": via})

    def captured(self, url, sha):
        self.caps[url]["doc"] = sha

    def feed(self, court, url, sha, items):
        self.feeds.append((court, items))

    def pending(self):
        failed = {i for i, s, _ in self.logs if s == "fetch"}
        return [(u, c["citation"]) for u, c in self.caps.items() if not c.get("doc") and u not in failed]

    def log(self, item, stage, reason):
        self.logs.append((item, stage, reason))


def opener_for(answers):
    asked = []

    def opener(url, timeout=60):
        asked.append(url)
        status, body, final, blocked, *location = answers.get(url, (404, b"", url, ""))
        return fg.Fetched(url, status, body, final, blocked, *location)
    return opener, asked


def run_with(answers, **kw):
    t = FakeTables()
    opener, asked = opener_for(answers)
    landed = []

    def land_fn(data, *, name, source, name_kind, content_type):
        landed.append(name)
        return Ref(str(abs(hash(data)))), True
    r = C.Run(t, land_fn=land_fn, opener=opener, pacer=fg.Pacer(sleep=lambda s: None), anytime=True, **kw)
    return r, t, asked, landed


PDF = "https://www.courtsofnz.govt.nz/assets/cases/2099/2099-NZSC-7.pdf"
CASE = "https://www.courtsofnz.govt.nz/cases/example-v-sample"


def test_a_run_reads_the_feeds_then_fetches_each_judgment_once():
    answers = {C.RSS["NZSC"]: (200, RSS.encode(), C.RSS["NZSC"], ""), CASE: (200, PAGE.encode(), CASE, ""),
               PDF: (200, b"%PDF-1.7 x", PDF, "")}
    r, t, asked, landed = run_with(answers)
    out = r.run()
    assert out["stopped"] == "" and out["landed"] == 1 and out["found"] == 1 and out["feeds"] == 1
    assert asked.count(PDF) == 1 and PDF in landed and C.RSS["NZSC"] in landed
    again, *_ = run_with(answers)
    again.t = t
    assert again.run()["landed"] == 0, "a judgment held is never fetched again"


def test_a_challenge_stops_the_run_and_a_server_s_own_error_does_not():
    answers = {C.RSS["NZSC"]: (403, b"", C.RSS["NZSC"], "HTTP 403: a block or a challenge")}
    r, t, *_ = run_with(answers)
    assert r.run()["stopped"].startswith("stopped: HTTP 403")
    answers = {C.RSS["NZSC"]: (503, b"<html>Service Unavailable</html>", C.RSS["NZSC"], "HTTP 503: a block or a challenge"),
               C.RSS["NZCA"]: (200, b"<rss></rss>", C.RSS["NZCA"], "")}
    r, t, *_ = run_with(answers)
    out = r.run()
    assert not out["stopped"].startswith("stopped") and out["feeds"] == 1 and t.logs[0][1] == "fetch"
    answers[C.RSS["NZSC"]] = (503, b"<html>Just a moment...</html>", C.RSS["NZSC"], "HTTP 503: a block or a challenge")
    r, *_ = run_with(answers)
    assert r.run()["stopped"].startswith("stopped")


def test_a_redirect_off_the_host_stops_and_lands_nothing():
    # the gate returns a redirect off the host unfetched: the 3xx and its Location, final_url the URL asked
    answers = {C.RSS["NZSC"]: (302, b"", C.RSS["NZSC"], "", "https://elsewhere.example/rss")}
    r, t, asked, landed = run_with(answers)
    assert "redirected to elsewhere.example" in r.run()["stopped"] and landed == []
    assert t.logs == [(C.RSS["NZSC"], "fetch", "redirected to elsewhere.example: not landed, and the run stops")]


def test_the_back_catalogue_search_is_never_asked():
    r, t, asked, _ = run_with({})
    with pytest.raises(C.Stop):
        r.get("https://www.courtsofnz.govt.nz/search/SearchForm?Search=2020")
    assert asked == []


def test_off_peak_only_unless_asked():
    assert C.off_peak(dt.datetime(2026, 10, 21, 23, 0)) and C.off_peak(dt.datetime(2026, 10, 21, 3, 30))
    assert not C.off_peak(dt.datetime(2026, 10, 21, 12, 0))
    t = FakeTables()
    r = C.Run(t, land_fn=None, opener=lambda *a, **k: None, pacer=fg.Pacer(sleep=lambda s: None),
              now_local=lambda: dt.datetime(2026, 10, 21, 12, 0))
    assert r.run() == {**r.counts, "stopped": "off-peak is over"}


def test_the_pacer_keeps_five_seconds_between_requests():
    slept = []
    clock = [0.0]
    pacer = fg.Pacer(now=lambda: clock[0], sleep=lambda s: slept.append(s))
    pacer.wait(C.HOST, C.FLOOR_S)
    pacer.wait(C.HOST, C.FLOOR_S)
    assert slept == [C.FLOOR_S]
