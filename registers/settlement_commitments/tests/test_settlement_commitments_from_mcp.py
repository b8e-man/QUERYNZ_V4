"""The watch answered from the ingest MCP's copy (`--from-mcp`, 14 November 2026): the fetching is the MCP
provider's, so the watch asks the web for nothing, runs at any hour, and an address the copy lacks is set aside in
the watch's record without stopping it. Every page here is invented; nothing is fetched."""
import datetime as dt
import os
import tomllib
import types

import support.fetchgate as fg
from registers.settlement_commitments import capture
from registers.settlement_commitments.tests.test_settlement_commitments import WALL, FakeTables, Ref

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OPEN = b"<title>About | Te Haeata</title><p>About</p>"


class Files:
    """mcpsource.files as the replay asks it: each address the copy holds answers with itself as its hash."""

    def __init__(self, corpus="estate-settlement_commitments", lacks=()):
        self.corpus, self.lacks = corpus, set(lacks)

    def execute(self, sql, params):
        url, corpora = params
        held = self.corpus in corpora and url not in self.lacks
        return types.SimpleNamespace(fetchone=lambda: (url,) if held else None)


def _run(files, monkeypatch, pages=None):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    pages = {capture.RECORDS: WALL, **(pages or {})}
    t = FakeTables()
    kw = capture.from_mcp(files, read_bytes=lambda url: pages.get(url, OPEN))
    out = capture.Run(t, land_fn=lambda *a, **k: (Ref(), True), log=lambda *_: None,
                      now=lambda: dt.datetime(2026, 11, 14, 14, 0, tzinfo=capture.NZ), **kw).run()
    return t, out


def test_the_watch_is_answered_from_the_mcp_by_day_and_never_asks_the_web(monkeypatch):
    t, out = _run(Files(), monkeypatch)
    assert out["records"] == "wall" and out["stopped"] == "" and out["set_aside"] == 0
    assert [r[0] for r in t.rows] == [capture.RECORDS, *capture.DOCS]


def test_a_page_about_the_source_the_mcp_lacks_is_set_aside_and_the_rest_are_read(monkeypatch):
    t, out = _run(Files(lacks={capture.DOCS[1]}), monkeypatch)
    assert out["records"] == "wall" and out["stopped"] == "" and out["set_aside"] == 1
    lacked = [r for r in t.rows if r[0] == capture.DOCS[1]]
    assert lacked == [(capture.DOCS[1], "about the source", None, lacked[0][3])]
    assert lacked[0][3].startswith("set aside: not in the MCP's copy")
    assert len(t.rows) == 1 + len(capture.DOCS)


def test_the_records_address_the_mcp_lacks_leaves_the_watch_red(monkeypatch):
    t, out = _run(Files(lacks={capture.RECORDS}), monkeypatch)
    assert out["records"] == "" and out["set_aside"] == 1 and len(t.rows) == 1 + len(capture.DOCS)


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    t, out = _run(Files(corpus="estate-iwi_directory"), monkeypatch)
    assert out["records"] == "" and out["set_aside"] == 1 + len(capture.DOCS)


def test_a_copy_that_is_a_challenge_page_is_a_block(monkeypatch):
    t, out = _run(Files(), monkeypatch, {capture.RECORDS: b"<html><head><title>Just a moment...</title></head></html>"})
    assert out["stopped"].startswith("stopped:") and out["records"] == "" and len(t.rows) == 1


def test_the_pull_brings_the_copy_the_capture_reads():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(capture.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}
