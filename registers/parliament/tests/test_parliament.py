"""registers/parliament: the reading of the MCP's parliament records, on
records made in the recorded shapes (no database), then on the filled
sample (real documents named by hash in sample.list): every field of the
API becomes a column, the version landed last is read, a withdrawn record
is marked, every text is published whole with its address flag beside it
(ruling 102), and each published row cites its document. The made-up
addresses here are "Sample" streets; no real value is printed."""
import datetime as dt
import hashlib
import os
import re

import pytest

from support import db, lane, rowcontract, sample
from support import mcpsource as M
from support.mcpsource.tests.fake import made_record
from registers.parliament import capture, check, read, shapes

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(LANE))
WQ, BILLS, SUBS, WAYBACK = ("parliament-written-questions", "parliament-bills", "parliament-sc-submissions",
                            "parliament-wayback")


def _rec(corpus, seq, **kw):
    r = made_record(corpus, seq, M.shapes()[corpus])
    if corpus == WAYBACK:
        r["id"] = r["url"] = f"http://www.parliament.nz:80/en-NZ/page-{seq}/"
        r["ts"] = "20061019014802"
    r.pop("seq", None)
    r.update(kw)
    return r


def _store(*recs):
    out = {}
    for r in recs:
        b = M.record_bytes(r)
        out[hashlib.sha256(b).hexdigest()] = b
    return out


def _read(corpus, *recs, served=True):
    store = _store(*recs)
    items = [(corpus, s, i, str(r["id"]), served) for i, (s, r) in enumerate(zip(store, recs))]
    return read.read(items, store.__getitem__, loaded_at="2026-10-27T09:00:00+13:00"), list(store)


def test_the_lane_folder_has_every_piece():
    assert lane.check_folder(LANE) == []


def test_every_recorded_field_of_every_corpus_has_a_column():
    """Ruling 96: their fields in our registers. A field the shapes record and the map lacks fails here."""
    for corpus in capture.CORPORA:
        shape = read.shape_of(corpus)
        known = set(read.SHAPE[shape]) | set(read.COMMON) | read.OWN[shape] | {"seq"}
        assert set(M.shapes()[corpus]["fields"]) <= known, (corpus, set(M.shapes()[corpus]["fields"]) - known)


def test_the_columns_are_the_tables():
    sql = open(os.path.join(LANE, "tables.sql"), encoding="utf-8").read()
    for shape, t in read.TABLE.items():
        body = sql.split(f"CREATE TABLE IF NOT EXISTS parliament.{t} (")[1].split("\n);")[0]
        cols = tuple(re.findall(r"^\s{4}([a-z_0-9]+)\s", body, re.M))
        assert cols == read.columns(shape), t


def test_a_written_question_is_read_field_by_field():
    r = _rec(WQ, 3, questionText="What is the plan?", replyText=" ", memberId="ab-12",
             questionReleasedDate="2025-03-04T00:00:00Z", text="a b c d")
    res, (sha,) = _read(WQ, r)
    (row,) = res.rows["written_questions"]
    assert (row["key"], row["question_number"], row["question_year"], row["member_id"]) == (r["id"], 3, 3, "ab-12")
    assert row["question_text"] == "What is the plan?" and row["reply_present"] is False
    assert row["question_released_on"] == "2025-03-04" and row["text_words"] == 4 and row["fields_unread"] == []
    assert row["question_text_names_address"] is False and row["reply_text_names_address"] is False and not res.flags
    assert row["document"] == sha and row["profile"] == read.PROFILE["wq"] and "text" not in row
    assert rowcontract.validate(row) == []


def test_an_api_item_is_keyed_by_its_corpus_and_cites_its_own_address():
    bill, sub = _rec(BILLS, 1, url=None), _rec(SUBS, 2, url="/en/pb/sc/make-a-submission/document/X/y")
    res, _ = _read(BILLS, bill)
    (row,) = res.rows["api_items"]
    assert row["key"] == f"{BILLS}/{bill['id']}" and row["corpus"] == BILLS and row["citation_url"] is None
    assert row["bill_number"] == bill["billNumber"] and row["capture"].startswith("{")
    res, _ = _read(SUBS, sub)
    assert res.rows["api_items"][0]["citation_url"] == "https://www.parliament.nz/en/pb/sc/make-a-submission/document/X/y"
    assert read.citation_url({"url": "https://example.test/x"}) is None             # never another host
    for r in res.rows["api_items"]:
        assert rowcontract.validate(r) == []


def test_a_wayback_page_carries_its_text_whole():
    r = _rec(WAYBACK, 4, text="one two three")
    res, _ = _read(WAYBACK, r)
    (row,) = res.rows["wayback_pages"]
    assert row["archived_at"] == "2006-10-19T01:48:02Z" and row["citation_url"] == r["url"]
    assert row["text_words"] == 3 and row["text"] == "one two three" and row["text_names_address"] is False


def test_a_text_naming_an_address_is_published_whole_and_flagged_by_key():
    q = _rec(WQ, 11, questionText="Who owns the house at 12 Sample Street?", replyText="Lot 2 DP 12345 is held.")
    res, _ = _read(WQ, q)
    (row,) = res.rows["written_questions"]
    assert row["question_text"] == q["questionText"] and row["reply_text"] == q["replyText"]       # nothing withheld
    assert row["question_text_names_address"] and row["reply_text_names_address"]
    assert sorted(res.flags) == [("written_questions", q["id"], "question_text", "numbered"),
                                 ("written_questions", q["id"], "reply_text", "legal")]
    assert res.counts["written_questions.question_text names an address"] == 1
    res, _ = _read(WAYBACK, _rec(WAYBACK, 12, text="Write to 2/14A Sample Road, Town."))
    assert res.rows["wayback_pages"][0]["text_names_address"] and res.flags[0][3] == "street"
    res, _ = _read(BILLS, _rec(BILLS, 13, text="Sample Road Bill 2024 at 3 readings"))
    assert res.rows["api_items"][0]["text_names_address"] is False and not res.flags


@pytest.mark.parametrize("text,want", [
    ("12 Sample Street", "street"), ("2/14A Sample Road", "street"), ("12-14 SAMPLE AVENUE", "street"),
    ("Lot 2 DP 12345", "legal"), ("Section 5 Block II", "legal"), ("Record of Title NA12/34", "legal"),
    ("CT 12A/345", "legal"), ("Unit 3, 45 Sample Road", "legal"),
    ("living at 12 Sample", "numbered"), ("the dwelling 7 Sample", "numbered"), ("Ms Sample, of 9 Sample", "numbered"),
    ("12 Sample Street Limited", None), ("State Highway 2 Sample Road", None), ("SH 1 Sample Highway", None),
    ("in 2019 Sample Road works", None), ("section 5 Sample Act", None), ("at 12 months", None), ("at 30 June", None),
    ("at 5 schools", None), ("at 10 am", None), ("question 12 Sample Road", None), ("unit 3 of the plan", None),
    ("Alert Level 4 Sample Way", None), ("", None), (None, None),
])
def test_the_three_shapes_and_what_is_not_an_address(text, want):
    assert shapes.shape(text) == want


def test_the_version_landed_last_is_read_not_the_highest_place():
    old = _rec(WQ, 4, replyText="")
    new = {**old, "replyText": "Answered."}
    store = _store(old, new)
    s_old, s_new = list(store)
    res = read.read([(WQ, s_old, 900, old["id"], True), (WQ, s_new, 654, old["id"], True)], store.__getitem__)
    (row,) = res.rows["written_questions"]
    assert row["reply_text"] == "Answered." and row["versions"] == 2 and row["seq"] == 654
    back = read.read([(WQ, s_old, 900, old["id"], True), (WQ, s_new, 654, old["id"], True),
                      (WQ, s_old, 900, old["id"], True)], store.__getitem__)
    assert back.rows["written_questions"][0]["reply_text"] == ""
    assert sorted(f[4] for f in res.files) == ["older version", "read"]
    c = res.counts
    assert c["records"] + c["older versions"] + c["set aside"] == c["documents"]


def test_a_withdrawn_record_is_kept_and_marked():
    res, _ = _read(WQ, _rec(WQ, 5), served=False)
    assert res.rows["written_questions"][0]["served"] is False and res.counts["withdrawn by the source"] == 1


def test_an_unknown_field_or_a_wrong_type_is_listed_not_dropped():
    res, _ = _read(WQ, _rec(WQ, 6, sentiment="warm", questionNumber="6"))
    assert res.set_aside[0][2] == "no `questionNumber`"
    res, _ = _read(WQ, _rec(WQ, 7, sentiment="warm", statusId="2"))
    assert res.rows["written_questions"][0]["fields_unread"] == ["sentiment", "statusId:str"]


def test_a_record_of_the_wrong_shape_is_set_aside():
    res, _ = _read(WAYBACK, _rec(WAYBACK, 8, url="https://example.test/x"))
    assert [w for _, _, w in res.set_aside] == ["its url is not a parliament.nz page"] and not res.rows["wayback_pages"]
    res, _ = _read(BILLS, _rec(BILLS, 9, documentType=""))
    assert [w for _, _, w in res.set_aside] == ["no `documentType`"]


def test_the_views_carry_every_text_whole_with_its_flag_beside_it():
    """Ruling 102: nothing withheld in a view; each text published whole has `<column>_names_address` next to it."""
    sql = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read().lower()
    views = dict(zip(("wq", "api", "wayback"), sql.split("create or replace view")[1:]))
    assert len(views) == 3
    for shape, v in views.items():
        body = v.split(" from ")[0]
        for col in read.FLAGGED[shape]:
            assert re.search(rf"\.{col}, \w\.{col}_names_address\b", body), (shape, col)
        assert "citation_url" in body and "document" in body and "_private" not in body
        for col in rowcontract.FORBIDDEN_COLUMNS:
            assert f" {col}," not in body


# ── the outside check's judgement ────────────────────────────────────────────

def _held(**kw):
    h = {c: {"cursor": 100, "arrivals": 100, "documents": 120, "caught": 0, "records": 100, "served": 100,
             "older versions": 20, "files set aside": 0, "set aside": 0, "fields unread": 0, "words": 5000}
         for c in capture.CORPORA}
    for c, v in kw.items():
        h[c].update(v)
    h["_wq"] = {"served": 100, "number repeated": 0, "replied": 99, "withdrawn": 0}
    return h


def test_the_check_on_the_views_names_a_street_with_its_flag_false_and_an_unflagged_column():
    ok = {"written_questions": {"rows": 9, "flagged": {"question_text": 2, "reply_text": 1},
                                "lines": {"question_text": 2, "reply_text": 1},
                                "street unflagged": {"question_text": 0, "reply_text": 0, "title": 0}}}
    assert check.judge_shown(ok) == []
    bad = {"written_questions": {**ok["written_questions"], "lines": {"question_text": 2},
                                 "street unflagged": {"question_text": 1, "reply_text": 0, "title": 3}}}
    fails = check.judge_shown(bad)
    assert len(fails) == 3 and any("`question_text_names_address` false" in f for f in fails)
    assert any("title: 3 rows hold a street address with no flag" in f for f in fails)
    assert check.judge_shown({"api_items": {"rows": 1, "flagged": {}, "lines": {}, "street unflagged": {}}})


def test_the_check_is_green_when_the_counts_agree_and_names_each_failure():
    o = {c: {"records": 100, "n_docs": 100, "corpus_words": 5010} for c in capture.CORPORA}
    assert check.judge(_held(), o) == []
    assert any("taken 80" in f for f in check.judge(_held(**{WAYBACK: {"cursor": 80, "arrivals": 80, "served": 80}}), o))
    assert any("older versions" in f for f in check.judge(_held(**{WQ: {"records": 90, "served": 90}}), o))
    assert any("still serves" in f for f in check.judge(_held(**{WQ: {"served": 99}}), o))
    assert any("words" in f for f in check.judge(_held(**{BILLS: {"words": 3000}}), o))
    assert check.judge(_held(**{SUBS: {"fields unread": 2}}), o) == [f"{SUBS}: 2 fields unread"]
    h = _held()
    h["_wq"].update({"number repeated": 3, "replied": 50})
    assert len(check.judge(h, o)) == 2


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
    return "scratch_gate_parliament"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    from registers.parliament import load as L, sample as S
    schema = _schema()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}_private")
        S.fill(conn, schema, items)
        conn.commit()

        def q(sql):
            cur = conn.execute(sql)
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.pub_"))
        conn.commit()
        out = {"items": items, "conn": conn, "schema": schema}
        for t in ("written_questions", "api_items", "wayback_pages", "files", "set_aside"):
            out[t] = q(f"SELECT * FROM {schema}.parliament_{t}")
        out["views"] = {v: q(f"SELECT * FROM {schema}.pub_parliament_{v}")
                        for v in ("written_questions", "api_items", "wayback_pages")}
        yield out


def test_every_sample_document_is_read_and_every_row_keeps_the_contract(filled):
    assert len(filled["files"]) == len(filled["items"]) and not filled["set_aside"]
    today = dt.date.today()
    for t in ("written_questions", "api_items", "wayback_pages"):
        for r in filled[t]:
            assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}, today) == [], (t, r["key"])
            assert r["fields_unread"] == [], (t, r["key"], r["fields_unread"])


def test_the_sample_holds_its_hard_cases(filled):
    wq, api, wb = filled["written_questions"], filled["api_items"], filled["wayback_pages"]
    assert any(r["reply_present"] for r in wq) and any(not r["reply_present"] for r in wq)
    assert any(r["attachment_name"] for r in wq)                                 # a reply with an attachment
    assert any(r["member_id"] is None for r in wq)                               # asked by no member id
    assert all(re.fullmatch(r"[0-9a-f-]{36}", r["member_id"]) for r in wq if r["member_id"])
    assert {r["corpus"] for r in api} == set(capture.API_CORPORA)
    assert {r["document_type"] for r in api} >= {"Bill", "SelectCommitteeReport", "AmendmentToBill",
                                                   "Submissions called for"}
    assert any(r["citation_url"] for r in api) and any(r["citation_url"] is None for r in api)
    assert {r["doc_type"] for r in wb} >= {"other", "features"} and all(r["text"] for r in wb)
    assert any(r["url"] and r["url"].split("/")[-2].endswith(" ") and not r["record_id"].endswith(" ")
               for r in api)                                                     # an id served with a trailing space, read


def test_every_published_row_cites_its_document(filled):
    v = filled["views"]
    for name, rows in v.items():
        assert len(rows) == len(filled[name]), name
        for r in rows:
            assert len(r["document"]) == 64, (name, r["key"])
            assert r["citation_url"] is None or r["citation_url"].startswith(("https://www.parliament.nz/",
                                                                              "http://www.parliament.nz")), r["key"]
    assert all(r["document_id"] for r in v["written_questions"])                 # Parliament's own id, where no address


def test_every_published_text_is_whole_and_its_flag_is_the_shapes(filled):
    """Counted, never printed: the flag equals shapes.names over the value, the value equals the lane's table."""
    for shape, name in read.TABLE.items():
        own = {r["key"]: r for r in filled[name]}
        for r in filled["views"][name]:
            for col in read.FLAGGED[shape]:
                assert r[col] == own[r["key"]][col], (name, r["key"], col)
                assert r[f"{col}_names_address"] == shapes.names(r[col]), (name, r["key"], col)
    assert any(r["question_text"] and r["reply_text"] for r in filled["views"]["written_questions"])


def test_postgres_s_street_pattern_reads_the_made_up_shapes_as_the_lane_does(filled):
    conn = filled["conn"]
    for text in ("12 Sample Street", "2/14A Sample Road", "12-14 SAMPLE AVENUE", "see 4 Sample Road.",
                 "State Highway 2 Sample Road", "in 2019 Sample Road works", "x123 Sample Road", "No. 4 Sample Road",
                 "Section 5 Sample Road", "at 5 schools", "12 Sample Street Limited"):
        pg = conn.execute("SELECT %s ~ %s", (text, check.STREET_SQL)).fetchone()[0]
        assert pg == (shapes.shape(text) == "street"), text


def test_the_check_fails_on_a_planted_street_whose_flag_is_false(filled):
    """The mutant: one question's text made a street address with its flag left false, in a rolled-back
    transaction. The check over the view must see it; the counts before must be clean."""
    conn, s = filled["conn"], filled["schema"]
    assert check.judge_shown(check.shown(conn, s, shared=True)) == []
    key = filled["written_questions"][0]["key"]
    conn.execute(f"UPDATE {s}.parliament_written_questions SET question_text = 'Visit 12 Sample Street.', "
                 "question_text_names_address = false WHERE key = %s", (key,))
    fails = check.judge_shown(check.shown(conn, s, shared=True))
    conn.rollback()
    assert fails == ["written_questions.question_text: 1 rows hold a street address with "
                     "`question_text_names_address` false"]


def test_arrivals_mark_a_record_that_holds_no_place_withdrawn(filled):
    """The MCP removed a record: the next one moved down a place and the re-walk landed it there. The removed
    record holds no place below the cursor any more."""
    conn, s = filled["conn"], filled["schema"] + "_mcp"
    conn.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")
    M.Tables(conn, s).create()
    a = "a" * 64
    rows = [(WQ, 0, "q0", a[:-1] + "0", "2026-10-26 20:00+13"), (WQ, 1, "gone", a[:-1] + "1", "2026-10-26 20:00+13"),
            (WQ, 2, "q2", a[:-1] + "2", "2026-10-26 20:00+13"), (WQ, 1, "q2", a[:-1] + "2", "2026-10-27 03:00+13")]
    for c, seq, rid, sha, at in rows:
        conn.execute(f"INSERT INTO {s}.arrivals (corpus, seq, record_id, sha256, new, landed_at) "
                     "VALUES (%s, %s, %s, %s, true, %s)", (c, seq, rid, sha, at))
    conn.execute(f"INSERT INTO {s}.cursors (corpus, cursor) VALUES (%s, 2)", (WQ,))
    got = capture.arrivals(conn, s)
    conn.rollback()
    assert {(rid, served) for _, _, _, rid, served in got} == {("q0", True), ("gone", False), ("q2", True)}
    assert [g[3] for g in got][-1] == "q2" and got[-1][2] == 1                    # landed last: its new place
