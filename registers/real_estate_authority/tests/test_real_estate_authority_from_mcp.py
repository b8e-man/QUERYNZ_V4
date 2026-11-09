"""The capture answered from the ingest MCP's copy (`--from-mcp`, 10 November 2026): the crawl is the MCP
provider's, so the walk asks the web nothing, runs at any hour, keeps the Committee's oldest first for what the copy
holds, and a listing page, abstract or PDF the copy lacks stays due (no line, no failure, no stop).
Every page here is invented; nothing is fetched."""
import datetime as dt
import os
import tomllib
import types

import support.fetchgate as fg
from registers.real_estate_authority import capture as C
from registers.real_estate_authority.tests.test_real_estate_authority_capture import FakeSite, FakeStore, FakeTables

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TODAY = dt.date(2026, 11, 10)
NOON = dt.datetime(2026, 11, 10, 12, 0, tzinfo=dt.timezone(dt.timedelta(hours=13)))
CHALLENGE = b"<html><head><title>Just a moment...</title></head></html>"
#: 2015 lists three Committee cases, oldest first 12, 10, 11; each has one PDF
YEARS = {2015: [(10, "02 Sep 2015"), (11, "03 Sep 2015"), (12, "01 Sep 2015")]}
SITE = FakeSite(YEARS)


def pdf(c):
    return f"https://{C.HOST}/reaa/pdfs/C{c}_Determination.pdf"


class Files:
    """mcpsource.files as the replay asks it: {url: [(corpus, seq, sha, state)]}."""

    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params):
        url, corpora = params
        hits = sorted((r for r in self.rows.get(url, ()) if r[0] in corpora and r[3] in ("landed", "held")),
                      key=lambda r: -r[1])
        return types.SimpleNamespace(fetchone=lambda: (hits[0][2],) if hits else None)


def _mcp(cases=(10, 11, 12), pdfs=(10, 11, 12), years=range(C.FIRST_YEAR, TODAY.year + 1),
         corpus="estate-real_estate_authority"):
    """The copy, its pages as the database serves them (the capture tests' FakeSite)."""
    urls = [C.listing_url(y) for y in years] + [C.abstract_url(c) for c in cases] + [pdf(c) for c in pdfs]
    store, rows = {}, {}
    for seq, u in enumerate(urls):
        sha = f"{seq:064x}"
        store[sha] = SITE(u).body
        rows[u] = [(corpus, seq, sha, "held")]
    return Files(rows), store


def _run(files, store, monkeypatch):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    monkeypatch.setattr(fg.time, "sleep", lambda s: (_ for _ in ()).throw(AssertionError(f"paced {s} s")))
    kw = C.from_mcp(files, read_bytes=lambda sha: store[sha])
    tables, landed = FakeTables(), FakeStore()
    out = C.Run(tables, land_fn=landed, clock=lambda: 0.0, now_local=lambda: NOON, log=lambda *_: None,
                anytime=kw.pop("anytime"), **kw).run(TODAY)     # as main passes it: the copy's hours, at noon
    return tables, landed, out


def test_the_walk_is_answered_from_the_mcp_by_day_and_never_asks_the_web(monkeypatch):
    assert C.from_mcp(None)["anytime"] is True          # the off-peak hours guard the web, not our store
    t, landed, out = _run(*_mcp(), monkeypatch)
    assert out["stopped"] == "" and out["listings"] == TODAY.year + 1 - C.FIRST_YEAR
    assert out["cases"] == 3 and out["landed"] == 3 and out["not_held"] == 0
    assert [n for n, *_ in landed.names if n.endswith(".pdf")] == [pdf(12), pdf(10), pdf(11)]   # oldest first


def test_a_case_the_copy_lacks_stays_due_and_fails_nothing(monkeypatch):
    t, landed, out = _run(*_mcp(cases=(10, 12)), monkeypatch)
    assert out["stopped"] == "" and out["cases"] == 2 and out["not_held"] == 1 and not t.asides
    assert t.pending(10) == [11]


def test_a_pdf_the_copy_lacks_leaves_its_case_due(monkeypatch):
    t, landed, out = _run(*_mcp(pdfs=(10, 11)), monkeypatch)
    assert out["stopped"] == "" and out["cases"] == 2 and out["not_held"] == 1 and not t.asides
    assert t.pending(10) == [12]


def test_three_not_held_in_a_row_do_not_stop_the_run(monkeypatch):
    t, landed, out = _run(*_mcp(cases=()), monkeypatch)
    assert out["stopped"] == "" and out["not_held"] == 3 and not t.asides and len(t.pending(10)) == 3


def test_a_year_the_copy_lacks_stays_to_be_listed(monkeypatch):
    t, landed, out = _run(*_mcp(years=[y for y in range(C.FIRST_YEAR, TODAY.year + 1) if y != 2012]), monkeypatch)
    assert out["stopped"] == "" and not t.asides and 2012 not in t.listed_years() and out["cases"] == 3


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    t, landed, out = _run(*_mcp(corpus="estate-fma"), monkeypatch)
    assert out["listings"] == 0 and out["cases"] == 0 and not t.cases


def test_a_copy_that_is_a_challenge_page_is_a_block(monkeypatch):
    files, store = _mcp()
    store[files.rows[C.abstract_url(10)][0][2]] = CHALLENGE
    t, landed, out = _run(files, store, monkeypatch)
    assert out["stopped"].startswith("stopped:") and "challenge" in out["stopped"]
    assert out["cases"] == 1 and t.pending(10) == [10, 11]          # case 12 first, then the block at 10
    assert t.asides[-1][1] == "fetch" and "challenge" in t.asides[-1][2]


def test_the_nightly_job_takes_the_mcp_copy_and_the_pull_brings_it():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    job = jobs[C.JOB]
    assert job.get("enabled", True) and "--from-mcp" in job["command"]
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(C.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}
