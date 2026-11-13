"""The capture answered from the ingest MCP's copy (`--from-mcp`, 9 November 2026): the crawl is the MCP
provider's, so the walk asks the web for nothing, runs at any hour, and an address the MCP lacks is a failed read.
Every page here is invented; nothing is fetched."""
import datetime as dt
import os
import tomllib
import types

import support.fetchgate as fg
from registers.worksafe import capture, read
from registers.worksafe.tests.test_worksafe_reading import FakeTables, _listing, _summary, _undertaking

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PAGES = {"prosecutions": _listing("prosecutions", ["a", "b"], total=2),
         "undertakings": _listing("undertakings", ["c"], total=1)}


def body(url):
    name = next((n for n, p in read.PATHS.items() if url.endswith(p)), None)
    return PAGES[name] if name else (_summary("Invented Limited") if "/prosecutions/" in url
                                     else _undertaking("Invented Limited"))


class Files:
    """mcpsource.files as the replay asks it: each address the copy holds answers with itself as its hash."""

    def __init__(self, corpus="estate-worksafe", lacks=()):
        self.corpus, self.lacks = corpus, lacks

    def execute(self, sql, params):
        url, corpora = params
        held = self.corpus in corpora and not any(url.rstrip("/").endswith("/" + s) for s in self.lacks)
        return types.SimpleNamespace(fetchone=lambda: (url,) if held else None)


def _run(files, monkeypatch):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    t = FakeTables()
    kw = capture.from_mcp(files, read_bytes=body)
    run = capture.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256="a" * 64), True), docs={},
                      now=lambda: dt.datetime(2026, 11, 10, 14, 0, tzinfo=capture.NZ), **kw)
    return t, run.run()


def test_the_walk_is_answered_from_the_mcp_by_day_and_never_asks_the_web(monkeypatch):
    t, out = _run(Files(), monkeypatch)
    assert out["stopped"] == "" and out["pages"] == 2 and out["landed"] == 3 and not t.asides


def test_an_address_the_mcp_lacks_is_a_failed_read_and_the_rest_land(monkeypatch):
    t, out = _run(Files(lacks=("b",)), monkeypatch)
    assert out["landed"] == 2 and [s for s, _ in t.asides] == ["fetch"]


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    t, out = _run(Files(corpus="estate-fma"), monkeypatch)
    assert out["pages"] == 0 and out["landed"] == 0


def test_the_pull_brings_the_copy_the_capture_reads():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(capture.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}
    job = jobs[capture.JOB]
    assert not job.get("enabled", True) or "--from-mcp" in job["command"]   # on again only from the MCP's copy


def test_a_copy_that_is_a_challenge_page_is_a_block(monkeypatch):
    monkeypatch.setitem(PAGES, "prosecutions", b"<html><head><title>Just a moment...</title></head></html>")
    t, out = _run(Files(), monkeypatch)
    assert out["stopped"].startswith("stopped:") and out["pages"] == 0 and out["landed"] == 0
    assert t.asides[0][0] == "fetch" and "challenge" in t.asides[0][1]     # a block, before any reading of it


def test_addresses_the_mcp_lacks_never_stop_the_run_however_many_in_a_row(monkeypatch):
    # 13 November 2026: three items the copy lacked, one after another, stopped the night as "the host may be in
    # trouble"; a gap in the copy is set aside and the run goes on
    t, out = _run(Files(lacks=("a", "b", "c")), monkeypatch)
    assert out["stopped"] == "" and out["landed"] == 0 and len(t.asides) == 3
    assert capture.outcome(out)[0]
