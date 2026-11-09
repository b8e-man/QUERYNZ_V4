"""The capture answered from the ingest MCP's copy (`--from-mcp`, 9 November 2026): the crawl is the MCP
provider's, so the walk asks the web for nothing and runs at any hour; an address the copy does not hold yet
holds no instance and fails no document (it is asked again next run); a challenge copy is a block. Every page
here is invented; nothing is fetched."""
import datetime as dt
import hashlib
import os
import tomllib
import types

import support.fetchgate as fg
from registers.council_minutes import capture, read
from registers.council_minutes.tests.test_council_minutes import BASE, PAGE, FakeTables, _with_store

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MINUTES = BASE + "/RedirectToDoc.aspx?URL=Open/2026/10/CO_20261021_MIN_3600.PDF"
OTHER = "https://other.infocouncil.biz"


class Files:
    """mcpsource.files as the replay asks it: each address the copy holds answers with itself as its hash."""

    def __init__(self, held, corpus="estate-council_minutes"):
        self.held, self.corpus = held, corpus

    def execute(self, sql, params):
        url, corpora = params
        ok = self.corpus in corpora and url in self.held
        return types.SimpleNamespace(fetchone=lambda: (url,) if ok else None)


def _run(held, monkeypatch, t=None, bodies=None, corpus="estate-council_minutes", store=None):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    store, t, bodies = {} if store is None else store, t or FakeTables(), bodies or {}
    _with_store(monkeypatch, store)

    def land_fn(data, *, name, content_type):
        sha = hashlib.sha256(data).hexdigest()
        new = sha not in store
        store[sha] = data
        return types.SimpleNamespace(sha256=sha), new

    page = lambda u: bodies.get(u, PAGE if u.endswith("/") else b"%PDF-1.4 " + u.encode())
    r = capture.Run(t, land_fn=land_fn, old={}, read_fn=read.recognise,
                    now=lambda: dt.datetime(2026, 11, 10, 14, 0, tzinfo=capture.NZ),
                    instances={BASE: "Invented District Council", OTHER: "Other"},
                    **capture.from_mcp(Files(held, corpus), read_bytes=page))
    return r.run(), t


def test_the_walk_is_answered_from_the_mcp_by_day_and_never_asks_the_web(monkeypatch):
    out, t = _run({BASE + "/", MINUTES}, monkeypatch)
    assert out["stopped"] == "" and (out["listings"], out["landed"]) == (1, 1) and t.docs[MINUTES][0] == "landed"


def test_what_the_copy_lacks_holds_nothing_fails_nothing_and_is_asked_again(monkeypatch):
    store = {}
    out, t = _run({BASE + "/"}, monkeypatch, store=store)         # the other listing and the minutes not held yet
    assert out["not_held"] == 2 and not t.held and MINUTES not in t.docs
    out2, t = _run({BASE + "/", MINUTES}, monkeypatch, t=t, store=store)   # the pull brought it: landed next run
    assert out2["landed"] == 1 and t.docs[MINUTES][0] == "landed"


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    out, t = _run({BASE + "/", MINUTES}, monkeypatch, corpus="estate-fma")
    assert (out["listings"], out["landed"]) == (0, 0)


def test_a_copy_that_is_a_challenge_page_is_a_block(monkeypatch):
    out, t = _run({BASE + "/"}, monkeypatch,
                  bodies={BASE + "/": b"<html><head><title>Just a moment...</title></head></html>"})
    assert out["listings"] == 0 and "invented.infocouncil.biz" in t.held


def test_the_nightly_job_takes_the_mcp_copy_and_the_pull_brings_it():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    job = jobs[capture.JOB]
    assert job.get("enabled", True) and "--from-mcp" in job["command"]
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(capture.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}
