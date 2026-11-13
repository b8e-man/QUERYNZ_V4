"""The capture answered from the ingest MCP's copy (`--from-mcp`, 10 November 2026): the crawl is the MCP
provider's, so the walk asks the web and the gate nothing, runs at any hour, keeps the soonest-to-be-taken-down
order for what the copy holds, and an order or a month the copy lacks stays due (no line, no failure, no stop).
Every page here is invented; nothing is fetched."""
import datetime as dt
import gzip
import os
import tomllib
import types

import support.fetchgate as fg
from registers.tenancy_tribunal import capture as C
from registers.tenancy_tribunal.tests.test_tenancy_tribunal_capture import FakeStore, FakeTables, listing_bytes, solr_doc

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TODAY = dt.date(2026, 11, 10)
NOON = dt.datetime(2026, 11, 10, 12, 0, tzinfo=dt.timezone(dt.timedelta(hours=13)))
CHALLENGE = b"<html><head><title>Just a moment...</title></head></html>"


class Files:
    """mcpsource.files as the replay asks it: {url: [(corpus, seq, sha, state)]}."""

    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params):
        url, corpora = params
        hits = sorted((r for r in self.rows.get(url, ()) if r[0] in corpora and r[3] in ("landed", "held")),
                      key=lambda r: -r[1])
        return types.SimpleNamespace(fetchone=lambda: (hits[0][2],) if hits else None)


def _doc(order, takedown):
    d = solr_doc([order])
    d["unpublishedDate_s"] = [f"{takedown} 00:00:00.0"]
    return d


#: three orders in October 2026, taken down in this order: c, a, b
ORDERS = {"a": "2029-10-02", "b": "2029-10-03", "c": "2029-10-01"}


def pdf(o):
    return C.DOCUMENTS + f"PDF/{o}-Tribunal_Order.pdf"


def _mcp(held=("a", "b", "c"), corpus="estate-tenancy_tribunal", months=None):
    """The copy: every month of the window listed whole (October 2026 names the three orders), and the PDFs of
    `held`."""
    store, rows, seq = {}, {}, 0
    for m in (C.window(TODAY) if months is None else months):
        docs = [_doc(o, t) for o, t in ORDERS.items()] if m == dt.date(2026, 10, 1) else []
        sha = f"{seq:064x}"
        store[sha] = listing_bytes(docs)
        rows[C.listing_url(m)] = [(corpus, seq, sha, "landed")]
        seq += 1
    for o in held:
        sha = o * 64
        store[sha] = b"%PDF-1.7 order " + o.encode()
        rows[pdf(o)] = [(corpus, 1000 + seq, sha, "held")]
        seq += 1
    return Files(rows), store


def _run(files, store, monkeypatch, tables=None):
    monkeypatch.setattr(fg, "open_url", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the web")))
    monkeypatch.setattr(fg, "refused_by", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked the gate")))
    monkeypatch.setattr(fg.time, "sleep", lambda s: (_ for _ in ()).throw(AssertionError(f"paced {s} s")))
    asked = []
    kw = C.from_mcp(files, read_bytes=lambda sha: (asked.append(sha), store[sha])[1])
    tables, landed = tables or FakeTables(), FakeStore()
    out = C.Run(tables, land_fn=landed, clock=lambda: 0.0, now_local=lambda: NOON, log=lambda *_: None,
                anytime=kw.pop("anytime"), **kw).run(TODAY)     # as main passes it: the copy's hours, at noon
    return tables, landed, out, asked


def test_the_walk_is_answered_from_the_mcp_by_day_never_asking_the_web_or_the_gate(monkeypatch):
    kw = C.from_mcp(None)
    assert kw["anytime"] is True                    # the off-peak hours guard the web, not our store
    t, landed, out, asked = _run(*_mcp(), monkeypatch)
    assert out["stopped"] == "" and out["listings"] == C.WINDOW_MONTHS and out["landed"] == 3
    assert {o for o, r in t.orders.items() if r["document"]} == {"a", "b", "c"}
    assert [n for n, *_ in landed.names if n.endswith(".pdf")] == [pdf("c"), pdf("a"), pdf("b")]   # soonest first


def test_an_order_the_copy_lacks_stays_due_and_fails_nothing(monkeypatch):
    t, landed, out, _ = _run(*_mcp(held=("b",)), monkeypatch)
    assert out["stopped"] == "" and out["not_held"] == 2 and out["landed"] == 1 and out["set_aside"] == 0
    assert not t.aside and [o for o, _ in t.pending(10)] == ["c", "a"]       # still due, in the same order


def test_a_month_the_copy_lacks_stays_to_be_listed(monkeypatch):
    t, landed, out, _ = _run(*_mcp(months=C.window(TODAY)[:-1]), monkeypatch)
    assert out["stopped"] == "" and out["not_held"] == 1 and not t.aside
    assert dt.date(2026, 11, 1) not in t.listed_months() and len(t.listed_months()) == C.WINDOW_MONTHS - 1


def test_three_not_held_in_a_row_do_not_stop_the_run(monkeypatch):
    t, landed, out, _ = _run(*_mcp(held=()), monkeypatch)
    assert out["stopped"] == "" and out["not_held"] == 3 and len(t.pending(10)) == 3


def test_another_corpus_s_copy_does_not_answer(monkeypatch):
    t, landed, out, _ = _run(*_mcp(corpus="estate-fma"), monkeypatch)
    assert out["listings"] == 0 and out["landed"] == 0 and out["not_held"] == C.WINDOW_MONTHS


def test_a_copy_that_is_a_challenge_page_is_a_block(monkeypatch):
    files, store = _mcp()
    store["a" * 64] = CHALLENGE
    t, landed, out, _ = _run(files, store, monkeypatch)
    assert out["stopped"].startswith("stopped:") and "challenge" in out["stopped"]
    assert [n for n, *_ in landed.names if n.endswith(".pdf")] == [pdf("c")]    # the run stopped at a
    assert t.aside[-1][1] == "fetch" and "challenge" in t.aside[-1][2]


def test_a_gzip_challenge_listing_is_a_block_too(monkeypatch):
    files, store = _mcp()
    store[f"{0:064x}"] = gzip.compress(CHALLENGE)
    t, landed, out, _ = _run(files, store, monkeypatch)
    assert out["stopped"].startswith("stopped:") and out["listings"] == 0


def test_the_nightly_job_takes_the_mcp_copy_and_the_pull_brings_it():
    with open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb") as f:
        jobs = tomllib.load(f)["jobs"]
    job = jobs[C.JOB]
    assert job.get("enabled", True) and "--from-mcp" in job["command"]
    pulled = jobs["qv4-mcp-pull"]["command"]
    assert set(C.MCP_CORPORA) <= {pulled[i + 1] for i, a in enumerate(pulled) if a == "--corpus"}
    assert "courts" in C.MCP_CORPORA, "the provider files Tenancy Tribunal orders in its courts corpus too (13 November 2026)"


def test_the_request_names_what_neither_copy_holds_soonest_first(tmp_path):
    import datetime as dt
    import json
    from registers.tenancy_tribunal import asks

    class Conn:
        def execute(self, q):
            class R:
                def __init__(self, rows):
                    self.rows = rows

                def fetchall(self):
                    return self.rows

                def fetchone(self):
                    return self.rows[0]
            if "count(*)" in q:
                return R([(5,)])
            assert "document IS NULL" in q and "ORDER BY unpublished_date" in q
            return R([("b", dt.date(2028, 6, 23)), ("a", dt.date(2028, 9, 1)), ("c", dt.date(2028, 9, 2)), ("d", None)])

    out = asks.write(Conn(), path=str(tmp_path / "t.json"))
    assert out == {"missing": 4, "earliest_take_down": "2028-06-23",
                   "request_id": "estate-tenancy_tribunal@short-4-2028-06-23"}
    s = json.loads((tmp_path / "t.json").read_text())
    assert s["listed"] == 5 and [o["order_id"] for o in s["orders"]] == ["b", "a", "c", "d"]
    assert s["by_take_down_month"] == [{"month": "2028-06", "orders": 1}, {"month": "2028-09", "orders": 2},
                                       {"month": "undated", "orders": 1}]
