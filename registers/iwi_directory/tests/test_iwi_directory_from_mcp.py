"""The walk answered from the ingest MCP's copy (`--from-mcp`, 14 November 2026): the crawl is the MCP provider's,
so the walk asks the web for nothing, runs at any hour, and an address the copy lacks is set aside in the frontier
without stopping the walk. Every page here is invented; nothing is fetched."""
import datetime as dt
import os
import tomllib
import types

import support.fetchgate as fg
from registers.iwi_directory import capture
from registers.iwi_directory.tests.test_iwi_directory_reading import FakeTables, Ref, _site

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class Files:
    """mcpsource.files as the replay asks it: each address the copy holds answers with itself as its hash."""

    def __init__(self, site, corpus="estate-iwi_directory", lacks=()):
        self.site, self.corpus, self.lacks = site, corpus, set(lacks)

    def execute(self, sql, params):
        url, corpora = params
        held = self.corpus in corpora and url in self.site and url not in self.lacks
        return types.SimpleNamespace(fetchone=lambda: (url,) if held else None)


def _run(files, monkeypatch, site):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    t = FakeTables()
    kw = capture.from_mcp(files, read_bytes=lambda sha: site[sha])
    run = capture.Run(t, land_fn=lambda data, **k: (Ref(str(abs(hash(data)))), True), seeds=("/",), log=lambda *_: None,
                      now=lambda: dt.datetime(2026, 11, 14, 14, 0, tzinfo=capture.NZ), **kw)
    return t, run.run()


def test_the_walk_is_answered_from_the_mcp_by_day_and_never_asks_the_web(monkeypatch):
    site = _site()
    t, out = _run(Files(site), monkeypatch, site)
    assert out["landed"] == 5 and out["stopped"] == "" and t.finished
    # the one address the pages link and the copy lacks (/region/tainui/, linked from the iwi pages) is set aside
    assert [a[0] for a in t.asides] == ["https://www.tkm.govt.nz/region/tainui/"]
    assert "not in the MCP's copy" in t.asides[0][2]


def test_an_address_the_mcp_lacks_is_set_aside_and_the_rest_land(monkeypatch):
    site = _site()
    t, out = _run(Files(site, lacks={"https://www.tkm.govt.nz/iwi/a/"}), monkeypatch, site)
    assert out["landed"] == 4 and t.finished and out["stopped"] == ""
    assert t.frontier["https://www.tkm.govt.nz/iwi/a/"]["state"] == "set aside"


def test_addresses_the_mcp_lacks_never_stop_the_walk_however_many_in_a_row(monkeypatch):
    site = _site()
    gone = {"https://www.tkm.govt.nz/region/r/", "https://www.tkm.govt.nz/iwi/a/", "https://www.tkm.govt.nz/iwi/b/"}
    site = {**site, "https://www.tkm.govt.nz/map/": site["https://www.tkm.govt.nz/map/"]
            + b"<a href='/iwi/a/'>a</a><a href='/iwi/b/'>b</a>"}
    t, out = _run(Files(site, lacks=gone), monkeypatch, site)
    assert out["stopped"] == "" and t.finished and out["landed"] == 2 and out["set_aside"] == 3
    assert capture.outcome(out)[0]


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    site = _site()
    t, out = _run(Files(site, corpus="estate-worksafe"), monkeypatch, site)
    assert out["landed"] == 0 and out["set_aside"] == 1 and t.finished


def test_a_copy_that_is_a_challenge_page_is_a_block(monkeypatch):
    site = {**_site(), "https://www.tkm.govt.nz/": b"<html><head><title>Just a moment...</title></head></html>"}
    t, out = _run(Files(site), monkeypatch, site)
    assert out["stopped"].startswith("stopped:") and out["landed"] == 0 and not t.finished
    assert t.asides[0][1] == "fetch" and "challenge" in t.asides[0][2]


def test_the_pull_brings_the_copy_the_capture_reads():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(capture.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}
