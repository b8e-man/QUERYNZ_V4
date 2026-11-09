"""The capture answered from the ingest MCP's copy (`--from-mcp`, 9 November 2026): the crawl is the MCP
provider's, so the walk asks neither the web nor the gate, runs at any hour, an address the MCP lacks is a failed
read with no host held for it, a challenge copy is a block, and a host the lane holds stays held. Every page here
is invented; nothing is fetched."""
import datetime as dt
import hashlib
import os
import tomllib
import types

import support.fetchgate as fg
from registers.councillor_interests import capture
from registers.councillor_interests.tests.test_councillor_interests import LANDING, FakeTables

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REGS = {"Invented District Council": ("www.invented.govt.nz", "https://www.invented.govt.nz/council/", None),
        "Other District Council": ("www.other.govt.nz", "https://www.other.govt.nz/council/", None)}
DOC = "https://www.invented.govt.nz/files/register-of-pecuniary-interests-2026.pdf"


class Files:
    """mcpsource.files as the replay asks it: each address the copy holds answers with itself as its hash."""

    def __init__(self, held, corpus="estate-councillor_interests"):
        self.held, self.corpus = held, corpus

    def execute(self, sql, params):
        url, corpora = params
        ok = self.corpus in corpora and url in self.held
        return types.SimpleNamespace(fetchone=lambda: (url,) if ok else None)


def _run(held, monkeypatch, bodies=None, t=None, corpus="estate-councillor_interests"):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    monkeypatch.setattr(fg, "refused_by", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the gate")))
    bodies = bodies or {}
    t, store = t or FakeTables(), {}

    def land_fn(data, *, name, content_type):
        sha = hashlib.sha256(data).hexdigest()
        new = sha not in store
        store[sha] = data
        return types.SimpleNamespace(sha256=sha), new

    page = lambda u: bodies.get(u, b"%PDF-1.4 x" if u.endswith(".pdf") else LANDING)
    r = capture.Run(t, land_fn=land_fn, registers=REGS, now=lambda: dt.datetime(2026, 11, 10, 14, 0, tzinfo=capture.NZ),
                    **capture.from_mcp(Files(held, corpus), read_bytes=page))
    return r.run(), t


def test_the_walk_is_answered_from_the_mcp_by_day_and_asks_neither_web_nor_gate(monkeypatch):
    out, t = _run({REGS["Invented District Council"][1], DOC}, monkeypatch)
    assert out["stopped"] == "" and (out["pages"], out["documents"]) == (1, 1)
    assert out["failed"] == 1 and not t.held                       # the other council's page: not held, no hold


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    out, t = _run({REGS["Invented District Council"][1], DOC}, monkeypatch, corpus="estate-fma")
    assert (out["pages"], out["documents"]) == (0, 0)


def test_a_copy_that_is_a_challenge_page_is_a_block(monkeypatch):
    url = REGS["Invented District Council"][1]
    out, t = _run({url}, monkeypatch, bodies={url: b"<html><head><title>Just a moment...</title></head></html>"})
    assert out["pages"] == 0 and "www.invented.govt.nz" in t.held


def test_a_host_the_lane_holds_stays_held(monkeypatch):
    t = FakeTables()
    t.hold("www.invented.govt.nz", "HTTP 403: a block")
    out, t = _run({REGS["Invented District Council"][1], DOC}, monkeypatch, t=t)
    assert (out["pages"], out["documents"]) == (0, 0)


def test_the_nightly_job_takes_the_mcp_copy_and_the_pull_brings_it():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    job = jobs[capture.JOB]
    assert job.get("enabled", True) and "--from-mcp" in job["command"]
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(capture.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}
