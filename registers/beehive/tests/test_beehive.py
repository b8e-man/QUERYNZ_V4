"""registers/beehive: the reading of the MCP's beehive records, on records
made in the recorded shape (no database), then on the filled sample (real
documents named by hash in sample.list): every row keeps the row contract,
the model-made annotation is marked as the source's, the body stays
private, and each published row cites its document and its page."""
import datetime as dt
import json
import os

import pytest

from support import db, lane, rowcontract, sample
from support import mcpsource as M
from support.mcpsource.tests.fake import made_record
from registers.beehive import read

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(LANE))


def _rec(seq, **kw):
    r = made_record("beehive", seq, M.shapes()["beehive"])
    r["id"] = r["url"] = f"https://www.beehive.govt.nz/release/made-{seq}"
    r["date"], r["published_at"] = "2025-03-04", "2025-03-04T00:00:00Z"
    r["ministers"] = [{"name": "Minister A", "slug": "minister-a"}, {"name": "Minister B", "slug": "minister-b"}]
    r.update(kw)
    return r


def _docs(*recs):
    store = {}
    for r in recs:
        b = M.record_bytes(r)
        store[__import__("hashlib").sha256(b).hexdigest()] = b
    return store


def test_the_lane_folder_has_every_piece():
    assert lane.check_folder(LANE) == []


def test_a_record_is_read_field_by_field_and_its_annotation_marked_the_sources():
    r = _rec(3)
    store = _docs(r)
    sha = next(iter(store))
    res = read.read([(sha, 3, r["id"])], store.__getitem__, loaded_at="2026-10-26T19:00:00+13:00")
    assert res.counts["releases"] == 1 and not res.set_aside
    rel = res.releases[0]
    assert (rel["key"], rel["url"], rel["published_on"], rel["seq"], rel["document"]) == (r["id"], r["url"], "2025-03-04", 3, sha)
    assert rel["ministers"] == 2 and [m["name"] for m in res.ministers] == ["Minister A", "Minister B"]
    assert rel["portfolios"] == r["portfolios"] and rel["fields_unread"] == []
    assert res.topics and all(t["model_made"] and "outside the estate" in t["made_by"] for t in res.topics + res.quotes)
    assert res.texts == [(r["id"], r["body_text"], r["text"])]
    assert "body_text" not in rel and "text" not in rel
    for row in res.releases + res.ministers + res.portfolios + res.topics + res.quotes:
        assert rowcontract.validate(row) == [], row["key"]


def test_the_newest_version_is_read_and_the_older_kept():
    old = _rec(4, title="First title")
    new = {**old, "title": "Amended title"}
    store = _docs(old, new)
    (s_old, s_new) = list(store)
    # seen first at place 9, then re-rendered and seen at place 4 (the MCP removed records before it): the later is current
    res = read.read([(s_old, 9, old["id"]), (s_new, 4, new["id"])], store.__getitem__)
    assert [r["title"] for r in res.releases] == ["Amended title"] and res.releases[0]["versions"] == 2
    back = read.read([(s_old, 9, old["id"]), (s_new, 4, new["id"]), (s_old, 9, old["id"])], store.__getitem__)
    assert [r["title"] for r in back.releases] == ["First title"]          # seen again last: the MCP went back to it
    assert sorted(f[3] for f in res.files) == ["older version", "read"]
    assert res.counts["releases"] + res.counts["older versions"] + res.counts["set aside"] == res.counts["documents"]


def test_a_record_that_is_not_a_beehive_page_is_set_aside_and_an_untitled_one_read():
    good, foreign, untitled = _rec(1), _rec(2, url="https://example.test/x"), _rec(3, title="")
    store = _docs(good, foreign, untitled)
    res = read.read([(s, None, None) for s in store], store.__getitem__)
    assert res.counts["releases"] == 2 and res.counts["untitled"] == 1      # an empty title is still the record
    assert [w for _, _, w in res.set_aside] == ["its url is not a beehive.govt.nz page"]


def test_a_field_the_lane_does_not_know_is_listed_not_dropped():
    r = _rec(5, sentiment="warm")
    store = _docs(r)
    res = read.read([(next(iter(store)), 5, r["id"])], store.__getitem__)
    assert res.releases[0]["fields_unread"] == ["sentiment"]


def test_the_published_views_never_carry_the_body_or_an_address_column():
    sql = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read().lower()
    views = sql.split("create or replace view")[1:]
    assert len(views) == 3
    for v in views:
        assert "body_text" not in v and "beehive_private" not in v and " text," not in v
        assert "citation_url" in v and "document" in v
        for col in rowcontract.FORBIDDEN_COLUMNS:
            assert f" {col}," not in v


# ── the filled sample ────────────────────────────────────────────────────────

def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_beehive"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    from registers.beehive import sample as S
    schema = _schema()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}_private")
        S.fill(conn, schema, items)
        conn.commit()

        def q(t, s=schema):
            cur = conn.execute(f"SELECT * FROM {s}.beehive_{t}")
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        from registers.beehive import load as L
        conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.pub_"))
        conn.commit()
        views = {}
        for v in ("beehive_releases", "beehive_release_ministers", "beehive_release_annotations"):
            cur = conn.execute(f"SELECT * FROM {schema}.pub_{v}")
            views[v] = [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        yield {"items": items, "views": views, **{t: q(t) for t in ("releases", "release_ministers", "release_portfolios",
                                                    "release_topics", "release_quotes", "files", "set_aside")},
               "texts": q("texts", schema + "_private")}


def test_every_sample_document_is_read_and_every_row_keeps_the_contract(filled):
    assert len(filled["files"]) == len(filled["items"]) and not filled["set_aside"]
    today = dt.date.today()
    for t in ("releases", "release_ministers", "release_portfolios", "release_topics", "release_quotes"):
        for r in filled[t]:
            row = {**r, "loaded_at": r["loaded_at"].isoformat()}
            assert rowcontract.validate(row, today) == [], (t, r["key"])
    assert all(r["url"].startswith(read.HOST) and r["key"] == r["url"] for r in filled["releases"])


def test_the_sample_holds_its_hard_cases(filled):
    rel = filled["releases"]
    types = {r["type"] for r in rel}
    assert {"release", "speech"} <= types, types
    assert any(r["ministers"] == 0 for r in rel) and any(r["ministers"] >= 2 for r in rel)
    assert any(r["published_on"] is None for r in rel)                      # a record served with no date
    assert any(r["kind"] or r["final_url"] or r["http_status"] for r in rel)   # a later arrival's fields
    assert any(r["quotes"] for r in rel) and any(r["topics"] for r in rel)
    assert all(not r["fields_unread"] for r in rel)


def test_the_annotation_rows_agree_with_their_release_and_are_the_sources(filled):
    by = {r["key"]: r for r in filled["releases"]}
    for t, col in (("release_topics", "topics"), ("release_quotes", "quotes")):
        n = {}
        for a in filled[t]:
            rel = by[a["release"]]
            assert a["model_made"] and a["made_by"].startswith(read.MADE_BY) and a["document"] == rel["document"]
            assert (rel["annotation_generator"] or rel["model"] or read.MADE_BY) in a["made_by"]
            n[a["release"]] = n.get(a["release"], 0) + 1
        assert all(by[k][col] == n.get(k, 0) for k in by), t
    names = {}
    for m in filled["release_ministers"]:
        names.setdefault(m["release"], []).append(m["ordinal"])
    assert all(by[k]["ministers"] == len(v) and sorted(v) == list(range(1, len(v) + 1)) for k, v in names.items())


def test_each_word_count_is_the_records_own_body_count(filled):
    """The MCP's word_count is the body's whitespace words (true on every
    record of the first pull); a drift here means the field changed meaning."""
    texts = {k: b for k, b, _ in ((t["key"], t["body_text"], t["text"]) for t in filled["texts"])}
    for r in filled["releases"]:
        if r["word_count"] is not None and texts.get(r["key"]):
            assert r["word_count"] == len(texts[r["key"]].split()), r["key"]


# ── the outside check's judgement ────────────────────────────────────────────

def _held(**kw):
    from registers.beehive import check  # noqa: F401
    h = {"cursor": 1000, "arrivals": 1000, "documents": 1000, "caught": 0, "releases": 998, "old estate releases": 5,
         "older versions": 2, "set aside": 0, "files set aside": 0, "fields unread": 0, "annotated outside": 0,
         "words": 500000}
    h.update(kw)
    return h


def test_the_check_is_green_when_the_counts_agree_and_names_each_failure():
    from registers.beehive import check
    o = {"records": 1000, "n_docs": 1000, "corpus_words": 501000}
    assert check.judge(_held(), o) == []
    assert any("taken" in f for f in check.judge(_held(cursor=900, arrivals=900), o))
    assert any("read:" in f for f in check.judge(_held(releases=990), o))
    assert any("words" in f for f in check.judge(_held(words=400000), o))
    assert check.judge(_held(caught=1, arrivals=999), o) == ["clean: 1 caught"]
    assert check.judge(_held(**{"fields unread": 3}), o) == ["clean: 3 fields unread"]


def test_every_published_row_cites_its_document_and_its_page(filled):
    v = filled["views"]
    assert len(v["beehive_releases"]) == len(filled["releases"])
    assert len(v["beehive_release_ministers"]) == len(filled["release_ministers"])
    assert len(v["beehive_release_annotations"]) == len(filled["release_topics"]) + len(filled["release_quotes"])
    for name, rows in v.items():
        for r in rows:
            assert len(r["document"]) == 64 and r["citation_url"].startswith(read.HOST), (name, r["key"])
            assert not {"body_text", "text", "address"} & set(r), name
    assert all(r["model_made"] for r in v["beehive_release_annotations"])


def test_the_old_estate_reads_a_page_the_mcp_lacks_or_holds_only_as_a_capture():
    read_rec = _rec(1)
    stub = {"id": "https://www.beehive.govt.nz/release/stub-2", "url": "https://www.beehive.govt.nz/release/stub-2",
            "text": "Menu Home the whole page as rendered", "updated_at": "2026-10-26T05:00:00Z",
            "capture": {"status": "ok", "fetched_at": "2026-10-26T04:00:00Z", "sha256": "ab" * 32}}
    store = _docs(read_rec, stub)
    (s_read, s_stub) = list(store)
    lines = [{"url": read_rec["url"], "title": "old title", "text": "old body", "posted_nz": "2020-01-02 10:00:00+13"},
             {"url": stub["url"], "title": "Stub page", "text": "four words of body", "posted_nz": "2021-05-06 09:00:00+12"},
             {"url": "https://www.beehive.govt.nz/release/old-only-3", "title": "Old only", "text": "a b",
              "posted_nz": "2019-07-08 08:00:00+12"}]
    export = ("\n".join(json.dumps(l, ensure_ascii=False) for l in lines) + "\n").encode()
    export = export.replace(b"four words", "four words".encode())       # a raw line separator inside a text
    res = read.read([(s_read, 1, read_rec["id"]), (s_stub, 2, stub["id"])], store.__getitem__)
    read.read_old(export, "cd" * 32, res)
    by = {r["key"]: r for r in res.releases}
    assert len(by) == 3 and res.counts["old estate lines"] == 3 and not res.set_aside
    assert by[read_rec["url"]]["origin"] == "mcp" and by[read_rec["url"]]["title"] == read_rec["title"]
    s = by[stub["url"]]
    assert (s["origin"], s["mcp_state"], s["mcp_document"], s["title"], s["published_on"]) == \
        ("old estate", "captured only", s_stub, "Stub page", "2021-05-06")
    assert s["captured_at"] == "2026-10-26T04:00:00Z" and s["document"] == "cd" * 32 and s["place"] == "line 2"
    o = by["https://www.beehive.govt.nz/release/old-only-3"]
    assert (o["origin"], o["mcp_state"], o["mcp_document"]) == ("old estate", None, None)
    for row in res.releases:
        assert rowcontract.validate(row) == [], row["key"]
