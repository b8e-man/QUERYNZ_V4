"""The own capture (ruling 140, own.py) on a fake JDO shaped like the answers the survey landed on 3 November 2026
(`{"count": n, "results": [{"caseName", "url"}]}`, the taxonomy's `[{"Name", "TeReoName", ...}]`), every case name
invented; the ledger in a scratch schema of the sample database, rolled back at the end; nothing is fetched. Then the
join (capture.for_load) and the suppression of own entries, measured on the sample's real files read as own ones."""
import datetime as dt
import hashlib
import json
import os
import types
import urllib.parse

import pytest

from support import db, fetchgate
from registers.courts import capture, load as L, own, read, sample

S = "scratch_test_courts_own"
M = "scratch_test_courts_own_mcp"
NOW = dt.datetime(2026, 11, 3, 23, 0, tzinfo=own.NZ)
HERE = os.path.dirname(os.path.abspath(__file__))
LANE = os.path.dirname(HERE)


def pdf(n: int) -> bytes:
    return b"%PDF-1.4\n% invented decision " + str(n).encode() + b"\n%%EOF\n"


class FakeJDO:
    """Two courts; HIGH COURT holds 120 decisions in 2026 and 3 in 2024, COURT OF APPEAL 2 in 2026. Decision 7 is the
    MCP's already, 9 answers 404, `challenge` names decisions that answer a challenge page, `reset` one that resets."""

    def __init__(self, challenge=(), reset=()):
        self.urls, self.challenge, self.reset = [], set(challenge), set(reset)
        self.held = {("HIGH COURT", 2026): list(range(1, 121)), ("HIGH COURT", 2024): [501, 502, 503],
                     ("COURT OF APPEAL", 2026): [901, 902]}

    def __call__(self, url, timeout):
        self.urls.append(url)
        u = urllib.parse.urlparse(url)
        if u.path == "/jdo-taxonomy-api/courts":
            return 200, json.dumps([{"Name": "COURT OF APPEAL", "TeReoName": "x", "HasMinuteBookReference": 0},
                                    {"Name": "HIGH COURT", "TeReoName": "y", "HasMinuteBookReference": 0}]).encode(), url
        if u.path == "/jdo-search-api":
            q = dict(urllib.parse.parse_qsl(u.query))
            year = int(q["judgmentDate"][2:6])
            ids = self.held.get((q["court"], year), [])
            page = int(q["page"])
            rows = [{"caseName": f"Invented Party {i} v Invented Other", "url": f"/jdo_documents/workspace___{i}.pdf"}
                    for i in ids[(page - 1) * own.PAGE_SIZE: page * own.PAGE_SIZE]]
            return 200, json.dumps({"count": len(ids), "results": rows}).encode(), url
        n = int(u.path.rsplit("___", 1)[1].split(".")[0])
        if n in self.reset:
            raise ConnectionResetError("reset by peer")
        if n in self.challenge:
            return 200, b"<html><head><title>Just a moment...</title></head><body>checking</body></html>", url
        if n == 9:
            return 404, b"", url
        return 200, pdf(n), url


class Pacer:
    def wait(self, host, floor):
        return 0.0


class NoCommit:
    def __init__(self, c):
        self.c = c

    def execute(self, *a, **k):
        return self.c.execute(*a, **k)

    def cursor(self, *a, **k):
        return self.c.cursor(*a, **k)

    def transaction(self):
        return self.c.transaction()

    def commit(self):
        pass

    def rollback(self):
        pass


@pytest.fixture
def env(monkeypatch, tmp_path):
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    raw = db.connect(db.OWNER_KEY, "querynz_v4_sample")
    conn = NoCommit(raw)
    for s in (S, M):
        conn.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")
    conn.execute(f"CREATE SCHEMA {S}")
    conn.execute(L.sql("tables.sql", S).replace(f"{L.private_of(S)}.", f"{S}."))
    conn.execute(f"CREATE SCHEMA {M}")
    conn.execute(f"CREATE TABLE {M}.files (corpus text, url text)")
    conn.execute(f"INSERT INTO {M}.files VALUES ('courts', %s)", (own.BASE + "/jdo_documents/workspace___7.pdf",))
    positions = tmp_path / "positions"
    positions.mkdir()
    (positions / "court-judgments.md").write_text("# test\n\nhosts: www.justice.govt.nz\n")
    monkeypatch.setitem(fetchgate._ROBOTS, "www.justice.govt.nz",
                        fetchgate.Robots("www.justice.govt.nz", "", 404, False, 0.0, "2026-11-03T00:00:00+13:00", ""))
    store = {}

    def land(data, url, content_type):
        sha = hashlib.sha256(data).hexdigest()
        store[sha] = (url, data)
        return sha

    def walk(api, **kw):
        return own.Walk(conn, schema=S, mcp_schema=M, fetch=api, pacer=Pacer(), positions_dir=str(positions),
                        ledger_dir=str(tmp_path / "ledger"), now=lambda: NOW, log=lambda *a: None, land=land, **kw)

    try:
        yield types.SimpleNamespace(conn=conn, walk=walk, store=store)
    finally:
        raw.rollback()
        raw.close()


def _ledger(env):
    return {r[0].rsplit("___", 1)[1]: r[1] for r in env.conn.execute(f"SELECT url, status FROM {S}.own_files").fetchall()}


def test_the_walk_lands_each_decision_once_skips_the_mcp_s_and_records_a_404(env):
    api = FakeJDO()
    out = env.walk(api, years=[2026, 2024]).run()
    assert out["ok"] and out["stopped"] == "end", out
    led = _ledger(env)
    assert led["9.pdf"] == "absent" and "7.pdf" not in led
    assert out["skipped_mcp"] == 1 and out["absent"] == 1
    assert out["landed"] == 120 - 2 + 3 + 2
    assert not any(u.endswith("___7.pdf") for u in api.urls), "the MCP's file is never asked"
    # the year of 120 is three pages; a recent year is walked from page one while pages hold something new
    pages = [u for u in api.urls if "jdo-search-api" in u and "HIGH%20COURT" in u and "2026-1-1" in u]
    assert len(pages) == 3
    # a second night: the recent years' first pages are asked again, nothing is fetched again, the past year not at all
    api2 = FakeJDO()
    out2 = env.walk(api2, years=[2026, 2024]).run()
    assert out2["ok"] and out2["landed"] == 0 and out2["new_files"] == 0
    assert not any("/jdo_documents/" in u for u in api2.urls)
    assert not any("2024-1-1" in u for u in api2.urls), "a past year walked to its end is not asked again"


def _skips_the_mcp(env) -> bool:
    api = FakeJDO()
    out = env.walk(api, years=[2026]).run()
    return out["ok"] and out["skipped_mcp"] == 1 and not any(u.endswith("___7.pdf") for u in api.urls)


def _stops_at_the_challenge(env) -> bool:
    api = FakeJDO(challenge={4})
    out = env.walk(api, years=[2026]).run()
    return (not out["ok"] and "challenge" in out["stopped"] and api.urls[-1].endswith("___4.pdf")
            and "4.pdf" not in _ledger(env))


def _fresh(env):
    env.conn.execute(f"DELETE FROM {S}.own_files")
    env.conn.execute(f"DELETE FROM {S}.own_cursor")


def test_the_skip_if_the_mcp_holds_it_rule_and_its_mutant(env, monkeypatch):
    assert _skips_the_mcp(env)
    _fresh(env)
    monkeypatch.setattr(own.Walk, "_mcp_urls", lambda self: set())     # the mutant: the MCP's addresses forgotten
    assert not _skips_the_mcp(env)


def test_a_challenge_stops_the_run_and_its_mutant(env, monkeypatch):
    assert _stops_at_the_challenge(env)
    _fresh(env)
    src = open(own.__file__, encoding="utf-8").read()
    rule = "        if got.blocked:\n            raise Stop(got.blocked)\n"
    assert rule in src
    mutant = types.ModuleType("own_mutant")
    exec(compile(src.replace(rule, ""), own.__file__, "exec"), mutant.__dict__)   # the mutant: a blocked read let through
    monkeypatch.setattr(own, "Walk", mutant.Walk)
    assert not _stops_at_the_challenge(env)


def test_a_reset_connection_is_a_failed_read(env):
    api = FakeJDO(reset={3})
    out = env.walk(api, years=[2026]).run()
    assert not out["ok"] and "ConnectionResetError" in out["stopped"]


def test_a_request_budget_stops_cleanly_and_the_next_run_resumes(env):
    api = FakeJDO()
    out = env.walk(api, years=[2024], max_requests=3).run()
    assert out["ok"] and out["stopped"] == "the run's request budget spent" and out["requests"] == 3
    api2 = FakeJDO()
    out2 = env.walk(api2, years=[2024]).run()
    assert out2["ok"] and out2["landed"] == 3 - out["landed"]
    assert len(_ledger(env)) == 3


def test_outside_the_hours_nothing_is_asked(env):
    api = FakeJDO()
    w = env.walk(api, years=[2026])
    w.now = lambda: dt.datetime(2026, 11, 3, 14, 0, tzinfo=own.NZ)
    out = w.run()
    assert out["ok"] and "outside 22:00" in out["stopped"] and api.urls == []


def test_the_search_address_is_the_form_s_own():
    u = own.search_url("HIGH COURT", dt.date(2020, 1, 1), dt.date(2020, 12, 31), 2)
    assert u.startswith(own.SEARCH + "?court=HIGH%20COURT&location=&judge=")
    assert "judgmentDate=%5B%272020-1-1T00:00:00Z%27,%272020-12-31T23:59:59Z%27%5D" in u and u.endswith("&page=2&sort=judgmentdate%20desc")
    assert own.spans(2020, 50) == [(dt.date(2020, 1, 1), dt.date(2020, 12, 31))]
    assert len(own.spans(2020, own.CAP)) == 12 and own.spans(2020, own.CAP)[-1] == (dt.date(2020, 12, 1), dt.date(2020, 12, 31))


def test_the_mcp_stays_first_by_hash():
    mcp = [{"record_id": "courts/1", "capture": "a" * 64}, {"record_id": "courts/2", "capture": None}]
    own_ = [{"record_id": "own/" + "a" * 64, "capture": "a" * 64}, {"record_id": "own/" + "b" * 64, "capture": "b" * 64}]
    out = capture.for_load(mcp, own_)
    assert [e["record_id"] for e in out] == ["courts/1", "courts/2", "own/" + "b" * 64]


def test_own_records_are_one_entry_per_file_in_the_mcp_s_shape(env):
    env.walk(FakeJDO(), years=[2024]).run()
    recs = capture.own_records(env.conn, S)
    assert len(recs) == 3 and all(r["record_id"] == "own/" + r["capture"] and r["source"] == own.SOURCE for r in recs)
    shape = set(capture.entry("x", 1, "c" * 64, "u", "application/pdf", "d" * 64, "landed", 1, rec={}))
    assert all(set(r) == shape for r in recs)


def _sample_entries():
    with open(os.path.join(LANE, "sample.list"), encoding="utf-8") as f:
        items = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    hashes = [i.split()[0] for i in items if not i.startswith("key:")][1:]
    return sample.entries_of(hashes)


def test_an_own_entry_is_suppressed_exactly_as_the_mcp_s_entry_of_the_same_file():
    """The sample's real judgment files read once as the MCP's entries and once as own entries (the shape own_records
    gives): the same judgments carry a suppression, the same parties are withheld, and no withheld name is published."""
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample store here")
    try:
        mcp = [e for e in _sample_entries() if e.get("state") == "landed" and e.get("capture")]
    except LookupError as exc:
        pytest.skip(str(exc))
    as_own = [{**e, "record_id": capture.OWN_PREFIX + e["capture"], "seq": None, "case_slug": None,
               "source": own.SOURCE, "note": capture.OWN_NOTE[own.SOURCE]} for e in mcp if e.get("kind") == "judgment_pdf"]
    pdfs = {e["capture"] for e in as_own}
    a = read.read([e for e in mcp if e["capture"] in pdfs])
    b = read.read(as_own)
    sup = lambda r: sorted((j["document"], j["suppression"]) for j in r.judgments)  # noqa: E731
    assert sup(a) == sup(b) and any(s for _, s in sup(b)), "the sample holds suppressed judgments, read the same way"
    withheld = lambda r: sorted(p["key"] for p in r.parties if p["withheld"])  # noqa: E731
    assert withheld(a) == withheld(b)
    suppressed = {j["key"] for j in b.judgments if j["suppression"]}
    for p in b.parties:
        if p["judgment"] in suppressed and not p["crown"] and not p["anonymised"]:
            assert p["withheld"] and p["name"] is None
