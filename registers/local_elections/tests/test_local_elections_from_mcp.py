"""Both passes answered from the ingest MCP's copy (`--from-mcp`, 9 November 2026): the crawl is the MCP
provider's, so neither asks the web or the gate, both run by day (the listings' week guard still binds), an
address the copy lacks yet holds no host and stays wanted, and a challenge copy is blocked. Every page here is
invented; nothing is fetched."""
import datetime as dt
import os
import tomllib
import types

import support.fetchgate as fg
from registers.local_elections import capture
from registers.local_elections.tests.test_local_elections_reading import FOLDER, LISTING, NOON, FakeTables, Ref

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SEED = "https://www.example.govt.nz/elections/returns"
Y2025 = "https://www.example.govt.nz/elections/returns?path=Elections/Candidate%20Expenses/2025"
Y2022 = "https://www.example.govt.nz/elections/returns?path=Elections/Candidate%20Expenses/2022"
CHALLENGE = b"<html><head><title>Just a moment...</title></head></html>"


class Files:
    """mcpsource.files as the replay asks it: each address the copy holds answers with itself as its hash."""

    def __init__(self, held, corpus="estate-local_elections"):
        self.held, self.corpus = held, corpus

    def execute(self, sql, params):
        url, corpora = params
        ok = self.corpus in corpora and url in self.held
        return types.SimpleNamespace(fetchone=lambda: (url,) if ok else None)


def _run(held, monkeypatch, t, bodies=None, corpus="estate-local_elections"):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    monkeypatch.setattr(fg, "refused_by", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the gate")))
    bodies = {SEED: FOLDER, Y2025: LISTING, **(bodies or {})}
    page = lambda u: bodies.get(u, b"%PDF-1.4 " + u.encode())
    return capture.Run(t, land_fn=lambda *a, **k: (Ref, True), clock=NOON, log=lambda *a: None,
                       seed_list=[("Example District Council", [], SEED)],
                       **capture.from_mcp(Files(held, corpus), read_bytes=page))


def test_the_listings_are_answered_from_the_mcp_by_day_and_a_page_it_lacks_holds_nothing(monkeypatch):
    t = FakeTables([])
    run = _run({SEED, Y2025}, monkeypatch, t)
    out = run.listings()
    assert out["returns_new"] == 3 and (Y2022, capture.NOT_HELD) in t.pages and not run.bad_hosts


def test_the_week_guard_still_binds(monkeypatch):
    t = FakeTables([])
    t.days_since_listings = lambda: 2.0
    assert _run({SEED, Y2025}, monkeypatch, t).listings()["requests"] == 0


def test_files_are_answered_by_day_and_one_the_copy_lacks_stays_wanted(monkeypatch):
    a, b = "https://www.example.govt.nz/media/a.pdf", "https://www.example.govt.nz/media/b.pdf"
    t = FakeTables([(a, "A", 2019), (b, "A", 2022)])
    run = _run({b}, monkeypatch, t)
    out = run.files()
    assert out["landed"] == 1 and t.files == {b: "landed"} and [w[0] for w in t.wanted()] == [a]
    assert not run.bad_hosts                                        # the host is asked again: the next file landed


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    t = FakeTables([])
    assert _run({SEED, Y2025}, monkeypatch, t, corpus="estate-fma").listings()["returns_new"] == 0


def test_a_copy_that_is_a_challenge_page_is_blocked(monkeypatch):
    t = FakeTables([])
    run = _run({SEED}, monkeypatch, t, bodies={SEED: CHALLENGE})
    run.listings()
    assert t.pages == [(SEED, "blocked")] and "www.example.govt.nz" in run.bad_hosts


def test_both_nightly_jobs_take_the_mcp_copy_and_the_pull_brings_it():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    for name in (capture.JOB_LISTINGS, capture.JOB_FILES):
        assert jobs[name].get("enabled", True) and "--from-mcp" in jobs[name]["command"], name
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(capture.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}


def test_a_night_the_copy_holds_none_of_the_wanted_files_is_no_failure(monkeypatch):
    """10 November 2026: the first --from-mcp files run asked the copy for 97 wanted files it did not hold yet,
    counted each a request and a failure, and the job failed (the lane red) on a night nothing failed."""
    a, b = "https://www.example.govt.nz/media/a.pdf", "https://www.example.govt.nz/media/b.pdf"
    t = FakeTables([(a, "A", 2019), (b, "A", 2022)])
    out = _run(set(), monkeypatch, t).files()
    assert out["requests"] == 0 and out["failed"] == 0 and out["not_held"] == 2 and out["landed"] == 0
    assert [w[0] for w in t.wanted()] == [a, b]                     # both stay wanted, asked again next run
