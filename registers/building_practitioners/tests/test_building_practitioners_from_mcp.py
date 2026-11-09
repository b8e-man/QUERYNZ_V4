"""Both captures answered from the ingest MCP's copy (`--from-mcp`, 9 November 2026): the crawl is the MCP
provider's, so neither walk asks the web, both run at any hour, an address the copy lacks yet is set aside and
asked again next run without stopping the run, and a challenge copy is a block. Every page here is invented;
nothing is fetched."""
import datetime as dt
import os
import tomllib
import types

import support.fetchgate as fg
from registers.building_practitioners import capture, register as R
from registers.building_practitioners.tests.test_building_practitioners_reading import PassTables, _item, _page
from registers.building_practitioners.tests.test_building_practitioners_register import G1, G2, RegTables, _bodies

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
G3 = "0000000a-0000-0000-0000-000000000003"
CHALLENGE = b"<html><head><title>Just a moment...</title></head></html>"


class Files:
    """mcpsource.files as the replay asks it: each address the copy holds answers with itself as its hash."""

    def __init__(self, held, corpus="estate-building_practitioners"):
        self.held, self.corpus = held, corpus

    def execute(self, sql, params):
        url, corpora = params
        ok = self.corpus in corpora and url in self.held
        return types.SimpleNamespace(fetchone=lambda: (url,) if ok else None)


def _no_web(monkeypatch):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))


DAY = dt.datetime(2026, 11, 10, 14, 0, tzinfo=capture.NZ)
LIST = _page([_item(f"Invented [2026] BPB {i} – final decision", number=f"CB{i}") for i in range(3)], total=3)


def _decisions(held, monkeypatch, bodies=None, corpus="estate-building_practitioners"):
    _no_web(monkeypatch)
    bodies = bodies or {capture.page_url(0): LIST}
    t = PassTables()
    run = capture.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256="a" * 64), True), clock=lambda: 0.0,
                      now=lambda: DAY, **capture.from_mcp(Files(held, corpus), read_bytes=lambda u: bodies.get(u, b"")))
    return t, run.run()


def test_the_decisions_are_answered_from_the_mcp_by_day(monkeypatch):
    t, out = _decisions({capture.page_url(0)}, monkeypatch)
    assert out["stopped"] == "" and out["passes_finished"] == 1 and t.pages == [0]
    assert out["not_held"] == len(capture.DOCS)                    # the copy holds no document about the source here


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    t, out = _decisions({capture.page_url(0)}, monkeypatch, corpus="estate-fma")
    assert out["pages"] == 0 and out["stopped"].startswith("stopped:")


def test_a_decisions_copy_that_is_a_challenge_page_is_a_block(monkeypatch):
    t, out = _decisions({capture.page_url(0)}, monkeypatch, bodies={capture.page_url(0): CHALLENGE})
    assert out["stopped"].startswith("stopped:") and t.pages == [] and any("challenge" in a for a in t.asides)


def _register(held, monkeypatch, t=None):
    _no_web(monkeypatch)
    bodies = _bodies()
    t = t or RegTables()
    run = R.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256=k["name"]), True), clock=lambda: 0.0,
                now=lambda: DAY, read_bytes=lambda sha: bodies[sha], adopt=False,
                **capture.from_mcp(Files(held), read_bytes=lambda u: bodies[u]))
    return t, run.run()


def test_the_register_is_answered_from_the_mcp_and_a_page_it_lacks_waits_without_stopping(monkeypatch):
    searches = {R.search_url(f, v) for f, v in R.QUERIES}
    t, out = _register(searches | {R.detail_url(G2)}, monkeypatch)
    assert out["stopped"] == "" and out["searches"] == len(R.QUERIES) and list(t.details) == [G2]
    assert out["not_held"] == 1
    t, out = _register(searches | {R.detail_url(G1), R.detail_url(G2)}, monkeypatch, t=t)   # the pull brought it
    assert set(t.details) == {G1, G2}


def test_pages_the_copy_lacks_in_a_row_do_not_stop_the_register(monkeypatch):
    bodies = _bodies()
    rows = [(g, "A", "B", "C") for g in (G1, G2, G3)]
    from registers.building_practitioners.tests.test_building_practitioners_register import _list
    bodies[R.search_url("lclass", "Site")] = _list(rows, field="lclass", value="Site")
    _no_web(monkeypatch)
    t = RegTables()
    out = R.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256=k["name"]), True), clock=lambda: 0.0,
                now=lambda: DAY, read_bytes=lambda sha: bodies[sha], adopt=False,
                **capture.from_mcp(Files({R.search_url(f, v) for f, v in R.QUERIES}), read_bytes=lambda u: bodies[u])).run()
    assert out["stopped"] == "" and out["not_held"] == 3 and not t.details


def test_both_nightly_jobs_take_the_mcp_copy_and_the_pull_brings_it():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    for name in (capture.JOB, R.JOB):
        assert jobs[name].get("enabled", True) and "--from-mcp" in jobs[name]["command"], name
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(capture.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}
