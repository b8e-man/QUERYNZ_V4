"""support/mcpsource/gaps.py (ruling 160): the provider's gap list. An old item is held when the MCP holds its
address or its content hash; missing is counted by the old item's year; a source with no corpus is a gap in
itself; Papers Past, the NZME mastheads (the archive in the copy, ruling 169), the boxes' keyed APIs and derived tables are shown and never asked; fyi.org.nz is left out; a gap is
closed only when a measure finds nothing missing, never on an answer."""
import datetime as dt

from support.mcpsource import gaps as G

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 11, 10, 6, 0, tzinfo=UTC)
SHA_A, SHA_B = "a" * 64, "b" * 64


def held_of(*pairs):
    h = G.Held()
    for corpus, url, sha in pairs:
        h.add(corpus, url, sha)
    return h


def test_an_address_in_one_spelling():
    want = "beehive.govt.nz/release/x"
    for u in ("https://www.beehive.govt.nz/release/x", "http://beehive.govt.nz/release/x/",
              "https://WWW.Beehive.govt.nz:443/release/x#top", "www.beehive.govt.nz/release/x"):
        assert G.norm_url(u) == want, u
    assert G.norm_url("https://www.gets.govt.nz/ExternalTenderDetails.htm?id=5") == "gets.govt.nz/ExternalTenderDetails.htm?id=5"
    assert G.norm_url("https://www.gets.govt.nz/ExternalTenderDetails.htm?id=6") != G.norm_url(
        "https://www.gets.govt.nz/ExternalTenderDetails.htm?id=5")          # the query is the tender
    assert G.norm_url("https://x.nz/a%20b.pdf") == "x.nz/a b.pdf"
    for u in (None, "", "   ", 5):
        assert G.norm_url(u) is None


def test_a_parliament_path_is_parliaments_address():
    h = held_of(("parliament-sc-evidence", "/en/pb/sc/doc/1", None), ("courts", "/en/pb/sc/doc/2", None))
    assert "parliament.nz/en/pb/sc/doc/1" in h.urls
    assert "parliament.nz/en/pb/sc/doc/2" not in h.urls        # only the parliament corpora give paths


def test_only_a_real_hash_is_a_hash():
    h = held_of(("courts", None, SHA_A), ("courts", None, "not-a-hash"), ("courts", None, SHA_A.upper()))
    assert h.shas == {SHA_A}


def test_held_by_address_or_hash_by_year():
    h = held_of(("beehive", "https://www.beehive.govt.nz/release/a", None), ("courts", "https://c.nz/x.pdf", SHA_A))
    items = [("https://beehive.govt.nz/release/a/", None, "2020", "release"),       # held by address
             ("https://beehive.govt.nz/release/b", None, "2020", "release"),        # missing
             ("https://elsewhere.nz/y.pdf", SHA_A, "2021", "judgment"),             # held by hash
             ("https://elsewhere.nz/z.pdf", SHA_B, None, "judgment")]               # missing, undated
    t = G.tally(items, h, "url+sha")
    assert t == {"release": {"2020": [2, 1]}, "judgment": {"2021": [1, 0], G.UNDATED: [1, 1]}}
    assert G.tally(items, h, "url")["judgment"]["2021"] == [1, 1]                 # an address match only
    assert G.tally(items, h, "sha")["release"]["2020"] == [2, 2]                  # a hash match only


def test_a_sitting_day_is_held_by_its_daily_file():
    h = held_of(("parliament-hansard-debates",
                 "https://hansard.parliament.nz/api/resources/daily/related/2025-02-20/2025-02-20-daily.pdf", None),
                ("beehive", "https://beehive.govt.nz/2025-02-21/", None))
    src = next(s for s in G.SOURCES if s.id == "hansard-sittings")
    days = G.dates_held(h, src.corpus, src.date_pattern)
    assert days == {"2025-02-20"}                       # another corpus's date is not a sitting
    t = G.tally([("2025-02-20", None, "2025", "sitting day"), ("2025-02-21", None, "2025", "sitting day")],
                h, "date", days)
    assert t == {"sitting day": {"2025": [2, 1]}}


def test_a_gap_by_period_and_its_stable_id():
    src = G.Source("s", "S", "nzbn_canonical", "", "beehive", match="url")
    (g,) = G.gaps_of(src, {"release": {"2020": [3, 1], "2019": [2, 2], "2021": [1, 0]}})
    assert (g["old_count"], g["mcp_count"], g["missing"]) == (6, 3, 3)
    assert g["missing_by_period"] == {"2019": 2, "2020": 1}
    assert g["period"] == "2019–2020"
    assert g["gap_id"] == "s@beehive#release" == G.gap_id("s", "beehive", "Release")
    assert g["asked"] == G.ASKED
    (z,) = G.gaps_of(src, {"release": {"2020": [3, 0]}})
    assert z["missing"] == 0 and z["asked"] is None


def test_a_register_with_no_corpus_is_missing_whole():
    src = G.Source("leg", "Legislation", "nzbn_canonical", "", None, match="count")
    (g,) = G.gaps_of(src, G.tally_counts([("2020", "act", 5), ("2020", "bill", 2), ("undated", "act", 1)]))
    assert (g["old_count"], g["missing"]) == (8, 8)
    assert g["missing_by_period"] == {"2020": 7, G.UNDATED: 1}
    assert g["kinds"] == {"act": 6, "bill": 2}
    assert g["asked"] == G.ASKED


def test_a_count_beside_a_corpus_says_it_cannot_tell():
    """A corpus record is a captured page, not a row: no difference is reported, and the provider is asked."""
    src = G.Source("ch", "Charities", "nzbn_canonical", "", "estate-charities", match="count")
    (g,) = G.gaps_of(src, G.tally_counts([("2020", "registered", 900)]), corpus_records=1767)
    assert g["missing"] is None and g["mcp_count"] == 1767 and g["old_count"] == 900
    assert g["asked"] == G.ASKED
    fd = G.feed([g], NOW)
    assert [x["gap_id"] for x in fd["gaps"]] == [g["gap_id"]]


def test_articles_one_gap_per_host():
    h = held_of(("beehive", "https://www.beehive.govt.nz/release/a", None))
    counts = [("beehive.govt.nz", "2020", 2), ("odt.co.nz", "2019", 7), ("paperspast.natlib.govt.nz", "1900", 9),
              ("fyi.org.nz", "2020", 3), ("nzherald.co.nz", "2019", 4)]
    urls = {"beehive.govt.nz": [("https://beehive.govt.nz/release/a", "2020"), ("https://beehive.govt.nz/release/b", "2020")]}
    gs = {g["source_id"]: g for g in G.article_gaps(counts, urls, h, "")}
    assert gs["articles:beehive.govt.nz"]["missing"] == 1 and gs["articles:beehive.govt.nz"]["corpus"] == "beehive"
    assert gs["articles:odt.co.nz"]["missing"] == 7 and gs["articles:odt.co.nz"]["corpus"] is None
    assert gs["articles:odt.co.nz"]["category"] == "news and other sites"
    pp = gs["articles:paperspast.natlib.govt.nz"]
    assert pp["status"] == "searched" and pp["asked"] is None                     # hard limit 17
    assert "articles:fyi.org.nz" not in gs                                        # ruling 168: removed entirely
    nz = gs["articles:nzherald.co.nz"]
    assert nz["status"] == "held" and nz["asked"] is None and "ruling 169" in nz["caveats"]   # archive copied; new articles asked elsewhere
    ds = G.document_gaps([("https://fyi.org.nz/request/1/x.pdf", None, "2024", "fyi.org.nz")], h, "")
    assert ds == []


def test_an_out_tag_is_left_out(monkeypatch):
    monkeypatch.setattr(G, "OUT_TAGS", frozenset({"dump.example"}))
    gs = G.article_gaps([("dump.example", "2020", 5), ("odt.co.nz", "2020", 1)], {}, G.Held(), "")
    assert [g["source_id"] for g in gs] == ["articles:odt.co.nz"]
    ds = G.document_gaps([("https://dump.example/a", None, "2026", "dump.example")], G.Held(), "")
    assert ds == []


def test_categories():
    assert G.category_of("www.greens.org.nz") == "party site"
    assert G.category_of("assets.national.org.nz") == "party site"
    assert G.category_of("christchurch.infocouncil.biz") == "public record"
    assert G.category_of("justice.govt.nz/lcdt") == "public record"
    assert G.category_of("teachersdisciplinarytribunal.nz") == "public record"
    assert G.category_of("nzherald.co.nz") == "news and other sites"


def test_the_inventory_adds_what_is_not_measured_and_its_out_marks():
    inv = {"sources": [{"id": "gets-awards"}, {"id": "old-files:pdfs", "label": "PDF store", "count": 9},
                       {"id": "dump", "status": "OUT"}, {"id": "claims", "status": "derived"}, "junk", {"label": "no id"}]}
    extra, out = G.unmeasured(inv, {"gets-awards"})
    assert out == {"dump"}
    assert [(g["source_id"], g["status"], g["old_count"]) for g in extra] == [("inventory:old-files:pdfs", "unmeasured", 9)]
    assert G.unmeasured(None, set()) == ([], set())
    assert G.unmeasured([{"id": "x"}], set())[0][0]["source_id"] == "inventory:x"


def _gap(gid, missing, status="gap", old=10, corpus=None, category="public record"):
    return {"gap_id": gid, "source": gid, "source_id": gid, "status": status, "category": category, "corpus": corpus,
            "kind": "all", "old_count": old, "mcp_count": None, "missing": missing, "missing_by_period": {},
            "period": "", "kinds": None, "how_measured": "", "caveats": None, "asked": None}


def test_the_feed_asks_the_biggest_first_and_notes_the_rest():
    fd = G.feed([_gap("small", 2), _gap("big", 50), _gap("none-missing", 0), _gap("pp", 99, "searched"),
                 _gap("co", 999, "boxes")], NOW)
    assert [g["gap_id"] for g in fd["gaps"]] == ["big", "small"]
    assert {g["gap_id"] for g in fd["noted"]} == {"none-missing", "pp", "co"}
    assert fd["schema_version"] == 1 and fd["asked"] == G.ASKED and fd["closed"] == []


def test_a_gap_closes_only_when_measured_empty():
    prev = G.feed([_gap("landed", 5), _gap("answered", 5), _gap("unknown", None), _gap("gone", 5)], NOW)
    later = NOW + dt.timedelta(hours=6)
    fd = G.feed([_gap("landed", 0), _gap("answered", 5), _gap("unknown", None)], later, previous=prev)
    assert [c["gap_id"] for c in fd["closed"]] == ["landed"]               # not the one still missing, nor the
    assert fd["closed"][0]["closed_at"] == later.isoformat(timespec="seconds")   # unmeasurable, nor one unmeasured
    again = G.feed([_gap("landed", 0)], later + dt.timedelta(hours=6), previous=fd)
    assert [c["gap_id"] for c in again["closed"]] == ["landed"]            # kept
    assert again["closed"][0]["closed_at"] == fd["closed"][0]["closed_at"]
    reopened = G.feed([_gap("landed", 3)], later + dt.timedelta(hours=12), previous=again)
    assert reopened["closed"] == [] and [g["gap_id"] for g in reopened["gaps"]] == ["landed"]


def test_an_ask_we_drop_is_withdrawn_never_closed():
    """ruling 168: fyi.org.nz removed, GeoNames and the NZME archive no longer asked; the provider is told to stop, and nothing
    is said to have landed."""
    prev = G.feed([_gap("articles:nzherald.co.nz", 9), _gap("geonames", 5), _gap("kept", 3)], NOW)
    later = NOW + dt.timedelta(hours=6)
    nz = dict(_gap("articles:nzherald.co.nz", 9, "held"), caveats="an NZME masthead: ruling 169")
    fd = G.feed([nz, _gap("kept", 3)], later, previous=prev)
    assert fd["closed"] == []
    w = {x["gap_id"]: x for x in fd["withdrawn"]}
    assert set(w) == {"articles:nzherald.co.nz", "geonames"}
    assert "ruling 169" in w["articles:nzherald.co.nz"]["why"] and "out of scope" in w["geonames"]["why"]
    again = G.feed([nz, _gap("kept", 3)], later + dt.timedelta(hours=6), previous=fd)
    assert [x["gap_id"] for x in again["withdrawn"]] == ["articles:nzherald.co.nz", "geonames"]     # kept
    assert again["withdrawn"][0]["withdrawn_at"] == w["articles:nzherald.co.nz"]["withdrawn_at"]
    reasked = G.feed([_gap("geonames", 5)], later + dt.timedelta(hours=12), previous=again)
    assert "geonames" not in {x["gap_id"] for x in reasked["withdrawn"]}
    assert "Withdrawn (no longer asked" in G.page(fd, later)


def test_the_page():
    fd = G.feed([_gap("Gazette", 208914), _gap("odt", 7, category="news and other sites"),
                 _gap("Charities", None, corpus="estate-charities"), _gap("Papers Past", 9, "searched")], NOW)
    fd["gaps"][1]["mcp_count"] = 1767
    text = G.page(fd, NOW)
    assert "10 November 2026 19:00 NZ time" in text
    assert "| Gazette | **none** | all | 208,914 |" in text
    assert "## Public records: 2 gaps, 1 with no corpus" in text
    assert "## News and other sites: 1 gaps, 1 with no corpus" in text
    assert "? (corpus has 1,767 records)" in text
    assert "searched, never mined (hard limit 17): Papers Past" in text
    assert G.ASKED in text
    assert text.index("Gazette") < text.index("Charities")


class FakeConn:
    """An old or v4 connection: answers by a phrase of the query."""
    def __init__(self, answers):
        self.answers, self.asked, self.closed = answers, [], False

    def execute(self, sql, params=None):
        self.asked.append((sql, params))
        for phrase, rows in self.answers.items():
            if phrase in sql:
                return _Rows(rows(params) if callable(rows) else rows)
        return _Rows([])

    def cursor(self):
        return _Cursor(self)

    def close(self):
        self.closed = True


class _Rows(list):
    def fetchall(self):
        return list(self)

    def fetchone(self):
        return self[0] if self else None


class _Cursor:
    def __init__(self, conn):
        self.conn, self.rows = conn, []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.rows = self.conn.execute(sql, params)

    def __iter__(self):
        return iter(self.rows)


class FakeClient:
    def __init__(self, corpora, records):
        self.corpora, self.records, self.calls = corpora, records, []

    def call_retrying(self, tool, args, **kw):
        self.calls.append((tool, args))
        if tool == "corpora":
            return {"corpora": self.corpora}
        recs = self.records.get(args["corpus"], [])
        page = recs[args["cursor"]:args["cursor"] + args["limit"]]
        return {"records": page, "next_cursor": args["cursor"] + len(page)}


def test_measure_end_to_end_on_fakes():
    v4 = FakeConn({"mcpsource.arrivals": [("beehive", "https://www.beehive.govt.nz/release/a", None),
                                          ("gets", "https://www.gets.govt.nz/ExternalTenderDetails.htm?id=7", SHA_A)],
                   "mcpsource.cursors": [("beehive", 1), ("gets", 1)]})
    news = FakeConn({"from articles where sources": lambda p: [("beehive.govt.nz", "https://beehive.govt.nz/release/a", "2020"),
                                                              ("beehive.govt.nz", "https://beehive.govt.nz/release/z", "2021")],
                     "from (select unnest(sources) s, post_date": [("beehive.govt.nz", "2020", 1), ("beehive.govt.nz", "2021", 1),
                                                                  ("odt.co.nz", "2019", 4)],
                     "from documents": [("https://late.nz/x.pdf", SHA_B, "2026", "late.nz")]})
    old = FakeConn({"bulk.gets_award_notices": [("https://www.gets.govt.nz/ExternalTenderDetails.htm?id=7", None, "2015", "Awarded"),
                                                ("https://www.gets.govt.nz/ExternalTenderDetails.htm?id=8", None, "2015", "Awarded")],
                    "legislation.instruments": [("2020", "act", 3)]})
    client = FakeClient([{"name": "beehive", "records": 1}, {"name": "gets", "records": 1},
                         {"name": "estate-late", "records": 1}],
                        {"estate-late": [{"urls": ["https://late.nz/other"], "content_sha256": SHA_B}]})
    conns = {"incoming_news": news}
    gaps, mcp = G.measure(lambda name: conns.get(name, old), v4, client, inventory=None, log=lambda s: None)
    by = {g["gap_id"]: g for g in gaps}
    assert by["gets-awards@gets#awarded"]["missing"] == 1 and by["gets-awards@gets#awarded"]["missing_by_period"] == {"2015": 1}
    assert by["legislation@none#all"]["missing"] == 3
    assert by["articles:beehive.govt.nz@beehive#article"]["missing"] == 1          # matched by address
    assert by["articles:odt.co.nz@none#article"]["missing"] == 4                    # no host held: all missing
    assert by["documents:late.nz@none#document"]["missing"] == 0                    # held by hash past our cursor
    url_asks = [p for s, p in news.asked if "from articles where sources" in s]
    assert url_asks == [(["beehive.govt.nz"], ["beehive.govt.nz"])]                # only held hosts' addresses fetched
    assert ("records", {"corpus": "estate-late", "cursor": 0, "limit": 500, "include_text": False}) in client.calls
    assert not any(t == "records" and a["corpus"] == "beehive" for t, a in client.calls)   # nothing past our cursor
    assert mcp["tail_read"] == {"beehive": 0, "gets": 0, "estate-late": 1}
    assert old.closed and news.closed
