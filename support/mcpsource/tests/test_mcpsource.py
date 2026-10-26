"""support/mcpsource: the client's handshake and answers, the pull's
cursor, its documents and its catch log, against a fake server serving
each corpus in its recorded shape (tests/fake.py). The pull's own tables
are made in a scratch schema of the sample database; the documents land
through the real landing wrapper into a temporary store root (one test)
or a recording stand-in (the rest). The live shape test is slow (the
network)."""
import json
import os
import urllib.error

import pytest

from support import db
from support import mcpsource as M
from support.mcpsource import client as C
from support.mcpsource.tests.fake import FakeServer, client_for, corpus_of, made_record

CORPORA = ("beehive", "parliament-bills", "parliament-bills-historical", "parliament-diaries",
           "parliament-hansard-debates", "parliament-hansard-index", "parliament-sc-reports", "parliament-sc-submissions",
           "parliament-sops", "parliament-wayback",
           "parliament-written-questions")
TEST_SCHEMA = "scratch_test_mcpsource"


def no_sleep(_s):
    return None


class Lands:
    """A stand-in for the landing wrapper: {sha: bytes}, {name: [sha]}."""

    def __init__(self, fail_names=()):
        self.docs, self.names, self.calls, self.fail_names = {}, {}, 0, set(fail_names)

    def __call__(self, data, *, name, source, conn, name_kind="file", content_type="", fetched_at=None, root=None,
                 kind_hint=""):
        import hashlib
        self.calls += 1
        assert source == "query-nz" and content_type == "application/json"
        if name in self.fail_names:
            raise OSError("the store said no")
        sha = hashlib.sha256(data).hexdigest()
        new = sha not in self.docs
        self.docs[sha] = data
        if sha not in self.names.setdefault(name, []):
            self.names[name].append(sha)
        return type("Ref", (), {"sha256": sha})(), new


# ── without a database ───────────────────────────────────────────────────────

def test_an_event_stream_answer_is_read_past_its_pings_and_a_json_answer_too():
    msg = {"jsonrpc": "2.0", "id": 3, "result": {"ok": 1}}
    sse = f": ping\n\n: ping\n\nevent: message\ndata: {json.dumps(msg)}\n\n"
    assert C.messages_of(sse, "text/event-stream") == [msg]
    assert C.messages_of(json.dumps(msg), "application/json") == [msg]
    assert C.messages_of("", "application/json") == []
    odd = {"jsonrpc": "2.0", "id": 4, "result": {"text": "a\u2028b\x0cc\x1cd\u0085e"}}   # raw separators in a text
    body = "event: message\r\ndata: " + json.dumps(odd, ensure_ascii=False) + "\r\n\r\n"
    assert C.messages_of(body, "text/event-stream") == [odd]


def test_the_handshake_keeps_the_session_id_and_says_initialized():
    server = FakeServer({"beehive": corpus_of("beehive", 3)})
    c = client_for(server)
    got = c.call("corpora", {})
    assert [m for m, _ in server.requests] == ["initialize", "notifications/initialized", "tools/call"]
    assert c.session == server.session and got["corpora"][0]["ingest_cursor"] == 3


def test_a_tool_error_and_an_http_error_keep_the_servers_words():
    server = FakeServer({"beehive": []})
    c = client_for(server)
    with pytest.raises(C.McpError, match="no tool nosuch"):
        c.call("nosuch", {})
    err = urllib.error.HTTPError("http://fake.test/mcp", 503, "Service Unavailable", {}, None)
    server.fail_next = [err]
    with pytest.raises(C.McpError, match="HTTP 503") as e:
        c.call("corpora", {})
    assert e.value.transient


def test_a_slow_server_is_waited_for_and_asked_again():
    server = FakeServer({"beehive": corpus_of("beehive", 2)})
    c = client_for(server)
    c.connect()
    import http.client
    server.fail_next = [TimeoutError("timed out"), urllib.error.URLError("Connection refused"),
                        http.client.IncompleteRead(b"")]          # an answer cut off mid-stream (26 October, 23:12)
    waits = []
    got = c.call_retrying("corpora", {}, sleep=waits.append)
    assert got["corpora"][0]["records"] == 2 and waits == [30.0, 60.0, 120.0]


def test_the_bytes_are_the_record_sorted_and_compact_without_its_place():
    rec = {"title": "Ā release", "seq": 9, "id": "x", "ministers": [{"slug": "a", "name": "A"}]}
    assert M.record_bytes(rec) == '{"id":"x","ministers":[{"name":"A","slug":"a"}],"title":"Ā release"}'.encode("utf-8")
    assert M.record_bytes({**rec, "seq": 10}) == M.record_bytes(rec)


@pytest.mark.parametrize("corpus", CORPORA)
def test_each_corpus_s_recorded_shape_is_no_drift_and_a_new_field_is(corpus):
    shape = M.shapes()[corpus]
    rec = made_record(corpus, 0, shape)
    assert M.drift_of(rec, shape) == []
    assert M.drift_of({**rec, "sentiment": 0.5}, shape) == [("sentiment", "float")]
    if corpus == "beehive":
        changed = {**rec, "quotes": [{"text": "q", "speaker": "s", "stance": "for"}]}
        assert M.drift_of(changed, shape) == [("quotes.stance", "str")]
        assert M.drift_of({**rec, "word_count": "312"}, shape) == [("word_count", "str")]


def test_a_page_out_of_place_is_refused():
    recs = corpus_of("parliament-bills", 4)
    page = {"records": recs[1:3], "cursor": 1, "next_cursor": 3, "total": 4}
    assert M.check_page(page, "parliament-bills", 1) == recs[1:3]
    with pytest.raises(M.ShapeError, match="asked for 2"):
        M.check_page(page, "parliament-bills", 2)
    with pytest.raises(M.ShapeError, match="next_cursor"):
        M.check_page({**page, "next_cursor": 4}, "parliament-bills", 1)
    with pytest.raises(M.ShapeError, match="seq"):
        M.check_page({**page, "records": [recs[2], recs[1]]}, "parliament-bills", 1)
    with pytest.raises(M.ShapeError, match="not the MCP's shape"):
        M.check_page({"items": recs}, "parliament-bills", 0)


# ── with the sample database ─────────────────────────────────────────────────

@pytest.fixture()
def conn():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    with db.connect(db.OWNER_KEY, "querynz_v4_sample", autocommit=True) as c:
        c.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
        M.Tables(c, TEST_SCHEMA).create()
        yield c
        c.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")


def _count(conn, t, where=""):
    return conn.execute(f"SELECT count(*) FROM {TEST_SCHEMA}.{t} {where}").fetchone()[0]


def test_every_corpus_is_pulled_whole_and_a_second_run_lands_nothing(conn):
    served = {c: corpus_of(c, n) for c, n in zip(CORPORA, (450, 7, 6, 30, 5, 12, 4, 3, 2, 9, 401))}
    server, lands = FakeServer(served), Lands()
    res = M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert M.outcome(res), M.summary(res)
    assert {c: r["landed"] for c, r in res.items()} == {c: len(v) for c, v in served.items()}
    assert M.Tables(conn, TEST_SCHEMA).cursors() == {c: len(v) for c, v in served.items()}
    assert _count(conn, "arrivals") == sum(len(v) for v in served.values())
    pages = [a for m, a in server.requests if m == "tools/call" and a.get("corpus") == "beehive" and "since" not in a]
    assert [(p["cursor"], p["limit"]) for p in pages] == [(0, 200), (200, 200), (400, 200)]
    # named by corpus and id, and by the page's own address
    rec = served["beehive"][5]
    sha = lands.names[f"beehive/{rec['id']}"]
    assert sha == lands.names[rec["url"]] and lands.docs[sha[0]] == M.record_bytes(rec)
    assert "parliament-bills/" + served["parliament-bills"][0]["id"] in lands.names
    before, asked = lands.calls, len(server.requests)
    res2 = M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert lands.calls == before and all(r["stopped"] == "nothing new" for r in res2.values())
    calls = [a for m, a in server.requests[asked:] if m == "tools/call"]
    assert len(calls) == 1 + len(CORPORA) and all("since" in a for a in calls[1:])   # `corpora`, then one feed each
    assert all(r["changes"]["changed"] == 0 and r["changes"]["stopped"] == "end" for r in res2.values())
    assert M.Tables(conn, TEST_SCHEMA).cursors() == {c: len(v) for c, v in served.items()}


def test_new_arrivals_are_taken_from_the_cursor_and_a_changed_record_is_a_second_document(conn):
    served = {"beehive": corpus_of("beehive", 5)}
    server, lands = FakeServer(served), Lands()
    M.pull(conn, client_for(server), "beehive", TEST_SCHEMA, land=lands, sleep=no_sleep)
    first = dict(served["beehive"][2])
    again = {**first, "seq": 5}                                   # the same record arriving again, unchanged
    changed = {**first, "seq": 6, "title": first["title"] + " (amended)"}
    served["beehive"] += [again, changed]
    res = M.pull(conn, client_for(server), "beehive", TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert (res["from"], res["to"], res["landed"], res["held"]) == (5, 7, 1, 1)
    shas = lands.names[f"beehive/{first['id']}"]
    assert len(shas) == 2 and lands.docs[shas[0]] == M.record_bytes(first)          # the first is never overwritten
    rows = conn.execute(f"SELECT seq, sha256, new FROM {TEST_SCHEMA}.arrivals WHERE record_id = %s ORDER BY seq",
                        (first["id"],)).fetchall()
    assert [(s, n) for s, _, n in rows] == [(2, True), (5, False), (6, True)] and rows[0][1] == rows[1][1]


def test_a_rewalk_finds_a_record_changed_in_place_and_leaves_the_cursor(conn):
    served = {"parliament-written-questions": corpus_of("parliament-written-questions", 250)}
    server, lands = FakeServer(served), Lands()
    M.pull(conn, client_for(server), "parliament-written-questions", TEST_SCHEMA, land=lands, sleep=no_sleep)
    rec = served["parliament-written-questions"][7]
    rec["replyText"], rec["updated_at"] = "a later reply", "2026-10-27T01:00:00Z"   # changed where it stood
    served["parliament-written-questions"].append(made_record("parliament-written-questions", 250,
                                                              M.shapes()["parliament-written-questions"]))
    res = M.pull(conn, client_for(server), "parliament-written-questions", TEST_SCHEMA, land=lands, sleep=no_sleep,
                 rewalk=True)
    assert (res["from"], res["to"], res["landed"], res["held"]) == (0, 250, 1, 249) and M.outcome(
        {"x": {**res, "source_cursor": 251}})
    assert M.Tables(conn, TEST_SCHEMA).cursor_of("parliament-written-questions") == 250     # the new arrival waits
    assert len(lands.names[f"parliament-written-questions/{rec['id']}"]) == 2
    assert _count(conn, "arrivals", "WHERE seq = 7") == 2


def test_the_change_feed_lands_a_record_changed_in_place_and_moves_its_stamp(conn):
    served = {"parliament-diaries": corpus_of("parliament-diaries", 30)}
    server, lands = FakeServer(served), Lands()
    first = M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert first["parliament-diaries"]["changes"]["changed"] == 0 and M.outcome(first)
    t = M.Tables(conn, TEST_SCHEMA)
    stamp = t.changes_since("parliament-diaries")
    assert stamp is not None
    rec = served["parliament-diaries"][12]
    rec["meeting"], rec["updated_at"] = "a corrected meeting", "2099-01-01T00:00:00Z"   # re-processed where it stood
    res = M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    ch = res["parliament-diaries"]["changes"]
    assert (res["parliament-diaries"]["stopped"], ch["changed"], ch["stopped"]) == ("nothing new", 1, "end")
    assert len(lands.names[f"parliament-diaries/{rec['id']}"]) == 2 and _count(conn, "arrivals", "WHERE seq = 12") == 2
    assert t.changes_since("parliament-diaries") == "2099-01-01T00:00:00Z"
    again = M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert again["parliament-diaries"]["changes"]["changed"] == 0


def test_a_source_that_counts_fewer_records_than_taken_is_red_and_named(conn):
    served = {"parliament-bills": corpus_of("parliament-bills", 10)}
    server, lands = FakeServer(served), Lands()
    M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    del served["parliament-bills"][3:5]                          # the MCP removed two (26 October: 246 written questions)
    for i, r in enumerate(served["parliament-bills"]):
        r["seq"] = i
    res = M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert not M.outcome(res) and "fewer than the 10 taken" in res["parliament-bills"]["error"]
    assert M.Tables(conn, TEST_SCHEMA).cursor_of("parliament-bills") == 10
    walk = M.pull(conn, client_for(server), "parliament-bills", TEST_SCHEMA, land=lands, sleep=no_sleep, rewalk=True)
    assert (walk["landed"], walk["held"], walk["cursor reset"]) == (0, 8, "10 to 8")
    fresh = made_record("parliament-bills", 8, M.shapes()["parliament-bills"])
    fresh["id"] = "parliament-bills-fresh"
    served["parliament-bills"].append(fresh)
    after = M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert after["parliament-bills"]["landed"] == 1 and M.outcome(after)          # the next arrival is not passed over


def test_a_changed_page_shape_stops_the_run_and_the_cursor_holds(conn):
    served = {"parliament-diaries": corpus_of("parliament-diaries", 450)}
    server, lands = FakeServer(served), Lands()
    calls = {"n": 0}

    def hook(page):
        calls["n"] += 1
        if calls["n"] == 2:                                       # the second page comes back renamed
            page = {"items": page.pop("records"), **page}
        return page
    server.page_hook = hook
    with pytest.raises(M.ShapeError):
        M.pull(conn, client_for(server), "parliament-diaries", TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert M.Tables(conn, TEST_SCHEMA).cursor_of("parliament-diaries") == 200
    assert _count(conn, "arrivals") == 200
    server.page_hook = None
    res = M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert res["parliament-diaries"]["from"] == 200 and res["parliament-diaries"]["to"] == 450


def test_a_field_new_to_us_lands_whole_and_turns_the_run_red(conn):
    recs = corpus_of("beehive", 3)
    recs[1]["sentiment"] = "warm"
    server, lands = FakeServer({"beehive": recs}), Lands()
    res = M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert res["beehive"]["landed"] == 3 and res["beehive"]["drift"] == 1 and not M.outcome(res)
    assert b'"sentiment":"warm"' in lands.docs[lands.names[f"beehive/{recs[1]['id']}"][0]]
    assert conn.execute(f"SELECT field, type, first_seq FROM {TEST_SCHEMA}.drift").fetchall() == [("sentiment", "str", 1)]


def test_a_record_that_will_not_land_is_a_catch_line_and_a_later_run_lands_it(conn):
    recs = corpus_of("parliament-wayback", 6)
    del recs[4]["id"]
    bad = f"parliament-wayback/{recs[2]['id']}"
    server, lands = FakeServer({"parliament-wayback": recs}), Lands(fail_names=[bad])
    res = M.pull_all(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    r = res["parliament-wayback"]
    assert (r["landed"], r["caught"], r["to"]) == (4, 2, 6) and not M.outcome(res)
    assert r["landed"] + r["caught"] == r["to"] - r["from"]                              # items in = out + aside
    caught = conn.execute(f"SELECT seq, stage FROM {TEST_SCHEMA}.catch ORDER BY seq").fetchall()
    assert caught == [(2, "land"), (4, "shape")]
    lands.fail_names.clear()
    n = M.retry_caught(conn, client_for(server), TEST_SCHEMA, land=lands, sleep=no_sleep)
    assert n == {"asked": 2, "landed": 1}
    assert _count(conn, "catch", "WHERE resolved_at IS NULL") == 1 and _count(conn, "arrivals") == 5


def test_the_real_landing_wrapper_keeps_one_document_per_bytes(conn, tmp_path):
    from support.docstore.landing import find_by_name, read_bytes
    recs = corpus_of("parliament-hansard-index", 2)
    tag = os.urandom(4).hex()                                     # names this test's documents apart from any other
    for r in recs:
        r["id"], r["url"] = f"{r['id']}-{tag}", f"{r['url']}-{tag}"
    server = FakeServer({"parliament-hansard-index": recs})
    res = M.pull(conn, client_for(server), "parliament-hansard-index", TEST_SCHEMA, root=str(tmp_path), sleep=no_sleep)
    assert res["landed"] == 2
    shas = find_by_name(f"parliament-hansard-index/{recs[0]['id']}", conn)
    assert shas == find_by_name(recs[0]["url"], conn) and len(shas) == 1
    assert read_bytes(shas[0], root=str(tmp_path)) == M.record_bytes(recs[0])


# ── the live server's shape (the network: slow) ──────────────────────────────

@pytest.mark.slow
@pytest.mark.parametrize("corpus", CORPORA)
def test_the_live_server_still_serves_the_recorded_shape(corpus):
    """Reads one page of 200 from the start and one from the newest end of
    each corpus and holds every record to the recorded shape: a field
    renamed, added or retyped on the server fails here by name."""
    c = M.Client(timeout=120)
    try:
        listing = c.call_retrying("corpora", {}, tries=3, wait_s=10)
    except C.McpError as e:
        pytest.skip(f"the MCP is not reachable through the tunnel: {e.why[:120]}")
    total = next(x["ingest_cursor"] for x in listing["corpora"] if x["name"] == corpus)
    shape = M.shapes()[corpus]
    drift = set()
    for cur in sorted({0, max(0, total - 200)}):
        page = c.call_retrying("records", {"corpus": corpus, "cursor": cur, "limit": 200, "include_text": True},
                               tries=3, wait_s=10)
        for r in M.check_page(page, corpus, cur):
            assert isinstance(r.get("id"), str) and r["id"], f"{corpus} seq {r['seq']} has no id"
            drift |= set(M.drift_of(r, shape))
    assert not drift, f"{corpus}: fields the recorded shape does not hold: {sorted(drift)}"
