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
    (positions / "specialist.md").write_text("# test\n\nhosts: determinations.era.govt.nz\n")
    for host in ("www.justice.govt.nz", "determinations.era.govt.nz"):
        monkeypatch.setitem(fetchgate._ROBOTS, host,
                            fetchgate.Robots(host, "", 404, False, 0.0, "2026-11-03T00:00:00+13:00", ""))
    store = {}

    def land(data, url, content_type):
        sha = hashlib.sha256(data).hexdigest()
        store[sha] = (url, data)
        return sha

    def walk(api, **kw):
        return own.Walk(conn, schema=S, mcp_schema=M, fetch=api, pacer=Pacer(), positions_dir=str(positions),
                        ledger_dir=str(tmp_path / "ledger"), now=lambda: NOW, log=lambda *a: None, land=land, **kw)

    def era_walk(api, **kw):
        return own.EraWalk(conn, schema=S, mcp_schema=M, fetch=api, pacer=Pacer(), positions_dir=str(positions),
                           ledger_dir=str(tmp_path / "ledger"), now=lambda: NOW, log=lambda *a: None, land=land, **kw)

    try:
        yield types.SimpleNamespace(conn=conn, walk=walk, era_walk=era_walk, store=store, ledger=str(tmp_path / "ledger"))
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
    # ruling 141: the challenge held the host in the gate; cleared, so the mutant is judged on the walk's own rule
    for host in list(fetchgate.refusals(env.ledger)):
        fetchgate.clear(host, by="test", ledger_dir=env.ledger)
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


# ── tranche 3: the Employment Relations Authority ─────────────────────────────────────────────────────────────────
def era_page(year: int, ids: list, page: int, pages: int) -> bytes:
    """A search page shaped like the Authority's (the survey's landed 2015 page): a record per determination with its
    PDF link, date and citation; one record (id 0) with no PDF; the "1 of N" pager. Every name invented."""
    recs = []
    for i in ids:
        pdf_li = ("" if i == 0 else f'<li class="p-0 m-0"><a target="_blank"  href="/assets/elawpdf/{year}/ab{i:04d}/'
                  f'{year}_NZERA_Auckland_{i}.pdf">{year}_NZERA_Auckland_{i}.pdf [PDF 99 KB]</a></li>')
        recs.append(f'<li class="search-results__record">\n<p class="search-results__record__title"><a href="/determination/'
                    f'view/{i}">Invented Worker {i} v Invented Employer Limited</a></p>\n<ul class="search-results__record'
                    f'__data m-0 p-0">\n{pdf_li}\n<li class="p-0 m-0"><p>1 March {year}</p></li>\n<li class="p-0 m-0">'
                    f'<p>[{year}] NZERA Auckland {i}</p></li>\n</ul>\n</li>\n')
    pager = f'<span class="page-link disabled">{page} of {pages}</span>' if pages else ""
    return (f'<html><body><div class="search-results"><ul>{"".join(recs)}</ul>{pager}</div></body></html>').encode()


class FakeERA:
    """2026: 23 determinations over three pages (id 0 has no PDF); 2015: 4 on one page; 2014: none. Determination 7 is
    the MCP's already; 9 answers 404."""

    def __init__(self, not_results=False):
        self.urls, self.not_results = [], not_results
        self.held = {2026: [0] + list(range(1, 23)), 2015: [501, 502, 503, 504]}

    def __call__(self, url, timeout):
        self.urls.append(url)
        u = urllib.parse.urlparse(url)
        if u.path == "/determinations/DeterminationSearchForm":
            if self.not_results:
                return 200, b"<html><body>Service unavailable</body></html>", url
            q = dict(urllib.parse.parse_qsl(u.query))
            if q["DateTo"] > NOW.date().isoformat():
                # the form refuses a date to come and sends the reader back to its landing page (seen 3 to 5 November 2026)
                return 200, b"<html><body><h1>Determinations</h1><form>search</form></body></html>", url
            year = int(q["DateFrom"][:4])
            ids = self.held.get(year, [])
            page = int(q.get("start", "0")) // own.ERA_PAGE + 1
            pages = -(-len(ids) // own.ERA_PAGE)
            return 200, era_page(year, ids[(page - 1) * own.ERA_PAGE: page * own.ERA_PAGE], page, pages), url
        n = int(u.path.rsplit("_", 1)[1].split(".")[0])
        if n == 9:
            return 404, b"", url
        return 200, pdf(n), url


def test_the_era_listing_reads_the_landed_page_shape():
    pages, hrefs = own.era_listing(era_page(2015, [501, 0, 502], 1, 74).decode())
    assert pages == 74 and hrefs == ["/assets/elawpdf/2015/ab0501/2015_NZERA_Auckland_501.pdf",
                                     "/assets/elawpdf/2015/ab0502/2015_NZERA_Auckland_502.pdf"]
    assert own.era_listing("<html><div class=\"search-results\"></div></html>") == (0, [])
    with pytest.raises(ValueError):
        own.era_listing("<html>no results here</html>")


def test_the_era_walk_lands_each_determination_once_and_skips_the_mcp_s(env):
    env.conn.execute(f"INSERT INTO {M}.files VALUES ('courts', %s)",
                     (own.ERA_BASE + "/assets/elawpdf/2026/ab0007/2026_NZERA_Auckland_7.pdf",))
    api = FakeERA()
    out = env.era_walk(api, years=[2026, 2015, 2014]).run()
    assert out["ok"] and out["stopped"] == "end", out
    assert out["skipped_mcp"] == 1 and out["absent"] == 1 and out["landed"] == 22 - 2 + 4
    assert not any(u.endswith("_7.pdf") for u in api.urls), "the MCP's file is never asked"
    rows = env.conn.execute(f"SELECT DISTINCT source, court FROM {S}.own_files").fetchall()
    assert rows == [(own.ERA_SOURCE, own.ERA_COURT)]
    assert len([u for u in api.urls if "DateFrom=2026" in u]) == 3
    api2 = FakeERA()
    out2 = env.era_walk(api2, years=[2026, 2015, 2014]).run()
    assert out2["ok"] and out2["landed"] == 0 and not any("/assets/elawpdf/" in u for u in api2.urls)
    assert not any("DateFrom=2015" in u for u in api2.urls), "a past year walked to its end is not asked again"
    entries = capture.own_records(env.conn, S)
    assert len(entries) == 24 and all(e["court_hint"] == own.ERA_COURT and "Employment Relations Authority" in e["note"]
                                      for e in entries)


def test_an_era_page_that_is_not_its_results_stops_the_run(env):
    out = env.era_walk(FakeERA(not_results=True), years=[2026]).run()
    assert not out["ok"] and "not the Authority's results page" in out["stopped"]


# ── tranche 2: the Ministry's decisions finder ────────────────────────────────────────────────────────────────────
def finder_page(ids: list, count: int, extra: str = "") -> bytes:
    """A finder page shaped like the landed one: the results header with its count, each result a link to its PDF and a
    commented-out copy of the same link; every name invented."""
    items = "".join(
        f'<li><article class="odd"><a href="https://www.justice.govt.nz/assets/Documents/Decisions/2099-NZXX-{i}-Invented-v-'
        f'Example.pdf"><header><span class="searchResultHeader">Invented v Example [2099] NZXX {i}</span></header></a>'
        f'<!--<a href="https://www.justice.govt.nz/assets/Documents/Decisions/2099-NZXX-{i}-Invented-v-Example.pdf">'
        f'<header>copy</header></a>--></article></li>' for i in ids)
    return (f'<html><body><form>options</form><div class="resultsHeader"><span class="heading">Search results</span>'
            f'<p><span>{count}</span> results found</p></div><ol id="SearchResults">{items}{extra}</ol></body></html>').encode()


class FakeFinder:
    """Employment Court (17): 60 decisions, newest first (ids 60 down to 1); decision 7 is the MCP's; 9 answers 404; a
    Word file is listed on page one. Disputes Tribunal (26): 3. Every other jurisdiction: none."""

    def __init__(self, newest=60):
        self.urls = []
        self.held = {17: list(range(newest, 0, -1)), 26: [503, 502, 501]}

    def __call__(self, url, timeout):
        self.urls.append(url)
        u = urllib.parse.urlparse(url)
        if u.path == own.FINDER_PATH:
            q = dict(urllib.parse.parse_qsl(u.query))
            ids = self.held.get(int(q["Filter_Jurisdiction"]), [])
            start = int(q.get("start", "0"))
            extra = ('<li><article><a href="https://www.justice.govt.nz/assets/Documents/Decisions/a-word-file.docx">x</a>'
                     '</article></li>') if start == 0 and ids else ""
            return 200, finder_page(ids[start: start + own.FINDER_PAGE], len(ids), extra), url
        n = int(u.path.split("-NZXX-")[1].split("-")[0])
        if n == 9:
            return 404, b"", url
        return 200, pdf(n), url


def test_the_finder_listing_drops_the_commented_copies_and_reads_the_count():
    count, pdfs, other = own.finder_listing(finder_page([3, 2, 1], 3, '<li><a href="https://x.nz/a.docx">x</a></li>').decode())
    assert count == 3 and len(pdfs) == 3 and other == ["https://x.nz/a.docx"]
    assert own.finder_listing('<div class="resultsHeader"></div><ol id="SearchResults"></ol>') == (0, [], [])
    with pytest.raises(ValueError):
        own.finder_listing("<html>a maintenance page</html>")


def test_the_finder_walk_lands_each_decision_once_and_then_reads_only_the_newest(env):
    env.conn.execute(f"INSERT INTO {M}.files VALUES ('courts', %s)",
                     ("https://www.justice.govt.nz/assets/Documents/Decisions/2099-NZXX-7-Invented-v-Example.pdf",))
    def walk(api, **kw):
        w = env.walk(api, **kw)
        f = own.FinderWalk.__new__(own.FinderWalk)
        f.__dict__.update(w.__dict__)
        f.counts = {**w.counts, "not_pdf": 0}
        return f
    api = FakeFinder()
    out = walk(api).run()
    assert out["ok"] and out["stopped"] == "end", out
    assert out["landed"] == 60 - 2 + 3 and out["skipped_mcp"] == 1 and out["absent"] == 1 and out["not_pdf"] == 2
    assert not any(u.endswith(".docx") for u in api.urls) and not any("-NZXX-7-" in u for u in api.urls)
    assert len([u for u in api.urls if "Filter_Jurisdiction=17" in u]) == 3            # 60 at 25 a page
    rows = dict(env.conn.execute(f"SELECT court, done FROM {S}.own_cursor WHERE source = %s", (own.FINDER_SOURCE,)).fetchall())
    assert rows["Employment Court"] and rows["Disputes Tribunal"]
    # the next night two new decisions sit at the top: page one is read, the two fetched, and the walk stops there
    api2 = FakeFinder(newest=62)
    out2 = walk(api2).run()
    assert out2["ok"] and out2["landed"] == 2
    assert len([u for u in api2.urls if "Filter_Jurisdiction=17" in u]) == 2           # page one, then page two holds nothing new
    sources = {r[0] for r in env.conn.execute(f"SELECT DISTINCT source FROM {S}.own_files").fetchall()}
    assert sources == {own.FINDER_SOURCE}


# ── from 9 November 2026: the ledger taken from the MCP's copy of the walks (own.take_from_mcp) ─────────────────────
C = "scratch_test_courts_own_copy"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Copy:
    """A scratch `files` table in the pull's shape and a store in memory: the MCP's copy of the walks, every name
    invented. JDO: one HIGH COURT 2019 listing page naming decisions 1 to 6 (an earlier copy of the page naming 1 only,
    as the court's listing first stood); 1 the MCP's courts corpus holds; 2 the ledger holds already; 3 in the copy
    twice (the newest taken); 4 whose bytes are not in the store yet; 5 not a PDF; 6 taken; 8, in no listing, taken
    as unlisted; 10 still waiting on the pull (not taken). ERA: one 2015 page naming two determinations."""

    def __init__(self, conn):
        self.conn, self.store, self.seq = conn, {}, 0
        conn.execute(f"DROP SCHEMA IF EXISTS {C} CASCADE")
        conn.execute(f"CREATE SCHEMA {C}")
        conn.execute(f"CREATE TABLE {C}.files (corpus text, seq bigint, record_sha256 text, record_id text, url text, "
                     f"content_type text, capture_sha256 text, state text)")

    def add(self, corpus, url, body, content_type="application/pdf", state="landed", in_store=True):
        self.seq += 1
        sha = _sha(body)
        rec = json.dumps({"capture": {"fetched_at": "2026-11-09 23:00:00+13:00", "sha256": sha}, "url": url}).encode()
        if in_store:
            self.store[sha] = body
        self.store[_sha(rec)] = rec
        self.conn.execute(f"INSERT INTO {C}.files VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                          (corpus, self.seq, _sha(rec), sha, url, content_type, sha, state))
        return sha

    def read(self, sha):
        if sha not in self.store:
            raise FileNotFoundError(sha)
        return self.store[sha]

    def take(self, source, conn=None):
        return own.take_from_mcp(conn or self.conn, source, schema=S, mcp_schema=C, read_bytes=self.read,
                                 exists=lambda s: s in self.store, log=lambda *a: None)


def jdo_url(n):
    return own.BASE + f"/jdo_documents/workspace___{n}.pdf"


def jdo_listing(ids):
    return json.dumps({"count": len(ids), "results": [{"caseName": f"Invented {i} v Other", "url": f"/jdo_documents/workspace___{i}.pdf"}
                                                      for i in ids]}).encode()


@pytest.fixture
def copy(env):
    cp = Copy(env.conn)
    jdo = own.MCP_CORPORA[own.SOURCE]
    page = own.search_url("HIGH COURT", dt.date(2019, 1, 1), dt.date(2019, 12, 31), 1)
    cp.add(jdo, own.TAXONOMY, json.dumps([{"Name": "HIGH COURT"}]).encode(), "application/json")
    cp.add(jdo, page, jdo_listing([1]), "application/json")
    cp.add(jdo, page, jdo_listing([1, 2, 3, 4, 5, 6]), "application/json")
    for n in (1, 2, 3, 6, 8):
        cp.add(jdo, jdo_url(n), pdf(n))
    cp.add(jdo, jdo_url(3), pdf(3) + b"% the court's corrected copy\n")
    cp.add(jdo, jdo_url(4), pdf(4), in_store=False)
    cp.add(jdo, jdo_url(5), b"<html>Just a moment...</html>")
    cp.add(jdo, jdo_url(10), pdf(10), state="waiting")
    env.conn.execute(f"INSERT INTO {C}.files (corpus, seq, url) VALUES ('courts', 1, %s)", (jdo_url(1),))
    env.conn.execute(f"INSERT INTO {S}.own_files (url, source, court, year, sha256, bytes, status) VALUES "
                     f"(%s, %s, 'HIGH COURT', 2019, %s, 1, 'landed')", (jdo_url(2), own.SOURCE, _sha(pdf(2))))
    era = own.MCP_CORPORA[own.ERA_SOURCE]
    cp.add(era, own.era_search_url(2015, 1), era_page(2015, [501, 502], 1, 1), "text/html")
    for i in (501, 502):
        cp.add(era, own.ERA_BASE + f"/assets/elawpdf/2015/ab{i:04d}/2015_NZERA_Auckland_{i}.pdf", pdf(i))
    return cp


def test_the_ledger_is_taken_from_the_mcp_s_copy_each_file_once_and_accounted_for(env, copy):
    out = copy.take(own.SOURCE)
    assert out["ok"], out
    assert (out["in_copy"], out["skipped_mcp"], out["skipped_held"], out["taken"], out["not_in_store"], out["not_pdf"],
            out["unlisted"]) == (7, 1, 1, 3, 1, 1, 1), out
    rows = {r[0].rsplit("___", 1)[1]: r[1:] for r in env.conn.execute(
        f"SELECT url, source, court, year, sha256, listing IS NOT NULL FROM {S}.own_files WHERE url LIKE '%%workspace%%'")}
    assert set(rows) == {"2.pdf", "3.pdf", "6.pdf", "8.pdf"}
    assert rows["6.pdf"] == (own.SOURCE, "HIGH COURT", 2019, _sha(pdf(6)), True)
    assert rows["3.pdf"][3] == _sha(pdf(3) + b"% the court's corrected copy\n"), "the newest copy of an address"
    assert rows["8.pdf"][1:3] == (own.UNLISTED[own.SOURCE], None)
    lines = env.conn.execute(f"SELECT url, corpus, provider_fetched_at IS NOT NULL FROM {S}.own_from_mcp").fetchall()
    assert len(lines) == 3 and all(c == "estate-courts-jdo" and f for _, c, f in lines)
    # the next run takes nothing again; the file whose bytes arrive is taken then
    copy.store[_sha(pdf(4))] = pdf(4)
    out2 = copy.take(own.SOURCE)
    assert out2["ok"] and out2["taken"] == 1 and out2["skipped_held"] == 4, out2
    # the ERA copy, the same way, its own source and court
    era = copy.take(own.ERA_SOURCE)
    assert era["ok"] and era["taken"] == 2 and era["unlisted"] == 0
    assert {tuple(r) for r in env.conn.execute(f"SELECT source, court, year FROM {S}.own_files WHERE url LIKE '%%elawpdf%%'")} \
        == {(own.ERA_SOURCE, own.ERA_COURT, 2015)}


def test_the_finder_s_copy_names_each_decision_s_jurisdiction_itself(env, copy):
    # 14 November 2026: estate-courts-finder's records carry `listed.jurisdiction`; its listing pages are not read
    fin = own.MCP_CORPORA[own.FINDER_SOURCE]
    url = "https://www.justice.govt.nz/assets/Documents/Decisions/2026-NZHRRT-1-Invented-v-Other.pdf"
    sha = copy.add(fin, url, pdf(901))
    seq = copy.seq
    rec = json.dumps({"capture": {"fetched_at": "2026-11-13T00:14:57+00:00", "sha256": sha}, "url": url,
                      "listed": {"jurisdiction": "Human Rights Review Tribunal", "title": "Invented v Other"}}).encode()
    copy.store[_sha(rec)] = rec
    env.conn.execute(f"UPDATE {C}.files SET record_sha256 = %s WHERE seq = %s", (_sha(rec), seq))
    nameless = "https://www.justice.govt.nz/assets/Documents/Decisions/no-listing.pdf"
    copy.add(fin, nameless, pdf(902))
    copy.add(fin, "https://www.justice.govt.nz/tribunals/human-rights/hrrt-decisions/?Filter_Jurisdiction=35",
             b"<html>a finder page</html>", "text/html")
    out = copy.take(own.FINDER_SOURCE)
    assert out["ok"] and out["taken"] == 2 and out["unlisted"] == 1 and out["listings_unread"] == 0, out
    rows = dict((u, (s, c, y)) for u, s, c, y in env.conn.execute(
        f"SELECT url, source, court, year FROM {S}.own_files WHERE url LIKE '%%Decisions%%'"))
    assert rows[url] == (own.FINDER_SOURCE, "Human Rights Review Tribunal", 0)
    assert rows[nameless] == (own.FINDER_SOURCE, own.UNLISTED[own.FINDER_SOURCE], None)
    assert {c for (c,) in env.conn.execute(f"SELECT corpus FROM {S}.own_from_mcp WHERE url LIKE '%%Decisions%%'")} == {fin}


def test_the_take_s_check_reads_the_tables_back_and_fails_on_a_lost_row(env, copy):
    class Drops:
        """A connection whose inserts into the ledger never arrive (the mutant)."""
        def __init__(self, c):
            self.c = c

        def execute(self, sql, params=None):
            if sql.startswith(f"INSERT INTO {S}.own_files"):
                return None
            return self.c.execute(sql, params)

        def commit(self):
            pass
    out = copy.take(own.SOURCE, conn=Drops(env.conn))
    assert not out["ok"] and "lacks 5" in out["stopped"], out


def test_the_take_s_check_fails_on_a_taken_row_holding_other_bytes(env, copy):
    env.conn.execute(f"INSERT INTO {S}.own_files (url, source, court, sha256, status) VALUES (%s, %s, 'X', %s, 'landed')",
                     (jdo_url(6), own.SOURCE, "f" * 64))
    env.conn.execute(f"INSERT INTO {S}.own_from_mcp (url, corpus, seq, record) VALUES (%s, 'estate-courts-jdo', 1, %s)",
                     (jdo_url(6), "e" * 64))
    out = copy.take(own.SOURCE)
    assert not out["ok"] and "1 rows taken from the copy hold other bytes" in out["stopped"], out
    # a row the boxes landed themselves that the provider's copy differs from is counted, never a failure
    env.conn.execute(f"DELETE FROM {S}.own_from_mcp")
    out2 = copy.take(own.SOURCE)
    assert out2["ok"] and out2["copy_differs_from_ours"] == 1, out2


def test_a_row_taken_from_the_copy_says_so_in_its_note_and_keeps_the_entry_shape(env, copy):
    copy.take(own.SOURCE)
    recs = {r["url"].rsplit("___", 1)[1]: r for r in capture.own_records(env.conn, S)}
    assert "fetched by the MCP's provider" in recs["6.pdf"]["note"] and "estate-courts-jdo" in recs["6.pdf"]["note"]
    assert "fetched itself" in recs["2.pdf"]["note"], "a file the boxes landed keeps its own note"
    shape = set(capture.entry("x", 1, "c" * 64, "u", "application/pdf", "d" * 64, "landed", 1, rec={}))
    assert all(set(r) == shape for r in recs.values())


def test_a_listing_of_the_copy_is_read_as_the_walk_read_it():
    page = own.search_url("COURT OF APPEAL", dt.date(2024, 1, 1), dt.date(2024, 12, 31), 3)
    assert own.listing_of(own.SOURCE, page, jdo_listing([7])) == ("COURT OF APPEAL", 2024, [jdo_url(7)])
    assert own.listing_of(own.SOURCE, own.TAXONOMY, b"[]") is None
    url = own.era_search_url(2026, 2, today=dt.date(2026, 11, 7))
    assert own.listing_of(own.ERA_SOURCE, url, era_page(2026, [3], 2, 3)) == (
        own.ERA_COURT, 2026, [own.ERA_BASE + "/assets/elawpdf/2026/ab0003/2026_NZERA_Auckland_3.pdf"])
    with pytest.raises(ValueError):
        own.listing_of(own.ERA_SOURCE, url, b"<html>a maintenance page</html>")


def test_the_page_reader_s_pieces_are_the_documents_the_load_left_waiting(env):
    from registers.courts import read as R
    Copy(env.conn)      # a fresh scratch schema of its own
    env.conn.execute(f"CREATE TABLE {C}.documents (document text, outcome text, fetched_at timestamptz)")
    env.conn.execute(f"INSERT INTO {C}.documents VALUES ('b', %s, '2026-11-02'), ('a', %s, '2026-11-01'), "
                     f"('a', %s, '2026-11-03'), ('c', 'read', '2026-11-01'), ('d', %s, NULL)",
                     (R.WAIT_PAGES, R.WAIT_PAGES, R.WAIT_PAGES, R.WAIT_TEXT))
    assert R.pages_waiting(env.conn, C) == ["a", "b"]
