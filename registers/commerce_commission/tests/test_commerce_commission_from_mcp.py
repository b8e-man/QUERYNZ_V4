"""The capture answered from the ingest MCP's copy (`--from-mcp`, 9 November 2026): the crawl is the MCP
provider's, so the walk asks the web for nothing, runs at any hour, and an address the MCP lacks is a failed read.
Every page here is invented; nothing is fetched."""
import datetime as dt
import os
import tomllib
import types

import support.fetchgate as fg
from registers.commerce_commission import capture
from registers.commerce_commission.tests.test_commerce_commission_reading import FakeTables, _entry, _listing

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PAGE1 = capture.LISTS[0].page_url(1)
ENTRY = capture.BASE + "/case-register/case-register-entries/{}/"


class Files:
    """mcpsource.files as the replay asks it: {url: [(corpus, seq, sha, state)]}."""

    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params):
        url, corpora = params
        hits = sorted((r for r in self.rows.get(url, ()) if r[0] in corpora and r[3] in ("landed", "held")),
                      key=lambda r: -r[1])
        return types.SimpleNamespace(fetchone=lambda: (hits[0][2],) if hits else None)


def _mcp(slugs_held, corpus="estate-commerce_commission"):
    store = {"l" * 64: _listing([(s, s, "closed", "Warning") for s in ("a", "b", "c")], total=3)}
    rows = {PAGE1: [(corpus, 1, "l" * 64, "landed")]}
    for i, s in enumerate(slugs_held):
        store[s * 64] = _entry("Invented Limited")
        rows[ENTRY.format(s)] = [(corpus, 10 + i, s * 64, "held")]
    return Files(rows), store


def _run(files, store, monkeypatch):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    t = FakeTables()
    kw = capture.from_mcp(files, read_bytes=lambda sha: store[sha])
    kw.pop("anytime")
    run = capture.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256="a" * 64), True), docs={},
                      now=lambda: dt.datetime(2026, 11, 10, 14, 0, tzinfo=capture.NZ), anytime=True, **kw)
    return t, run.run()


def test_the_walk_is_answered_from_the_mcp_by_day_and_never_asks_the_web(monkeypatch):
    t, out = _run(*_mcp("abc"), monkeypatch)
    assert out["stopped"] == "" and out["pages"] == 1 and set(t.items) == {"a", "b", "c"}
    assert capture.from_mcp(None)["anytime"] is True          # the off-peak hours guard the web, not our store


def test_an_address_the_mcp_lacks_is_a_failed_read_and_the_rest_land(monkeypatch):
    t, out = _run(*_mcp("ac"), monkeypatch)
    assert set(t.items) == {"a", "c"} and [s for s, _ in t.asides] == ["fetch"]


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    t, out = _run(*_mcp("abc", corpus="estate-fma"), monkeypatch)
    assert out["pages"] == 0 and not t.items


def test_the_nightly_job_takes_the_mcp_copy_and_the_pull_brings_it():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    job = jobs[capture.JOB]
    assert job.get("enabled", True) and "--from-mcp" in job["command"]
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(capture.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}


def test_a_copy_that_is_a_challenge_page_is_a_block(monkeypatch):
    files, store = _mcp("abc")
    store["l" * 64] = b"<html><head><title>Just a moment...</title></head></html>"
    t, out = _run(files, store, monkeypatch)
    assert out["stopped"].startswith("stopped:") and out["pages"] == 0 and not t.items
    assert t.asides[0][0] == "fetch" and "challenge" in t.asides[0][1]     # a block, before any reading of it
