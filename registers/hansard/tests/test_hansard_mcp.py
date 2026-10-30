"""The hansard lane's MCP half (hansard-2, rulings 96 and 97): the MCP's
`parliament-hansard-index` and `parliament-hansard-debates` records, read by
hash. The readers and the check are tested on records shaped like the
MCP's (every text invented); the filled sample against the row contract and
the published views. No model is called, nothing is fetched."""
import datetime as dt
import json
import os

import pytest

from support import db, rowcontract
from registers.hansard import check, read_mcp

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _pdf(day):
    return f"https://hansard.parliament.nz/api/resources/daily/related/{day}/{day}-daily.pdf"


def _day(day, text, **kw):
    rec = {"bytes": 10, "capture": {"bytes": 10, "fetched_at": "2026-10-26T07:21:17Z", "http_status": 200,
                                    "raw_file": f"raw/hansard_{day}.pdf", "sha256": "a" * 64, "url": _pdf(day)},
           "date": day, "fetched_at": "2026-10-26T07:21:17Z", "http_status": 200, "id": _pdf(day), "page_count": 3,
           "raw_file": f"raw/hansard_{day}.pdf", "sha256": "a" * 64, "sitting_date": day, "text": text,
           "title": f"Hansard {day}", "updated_at": "2026-10-26T07:21:17Z", "url": _pdf(day),
           "word_count": len(text.split())}
    rec.update(kw)
    return rec


def _index(url, lastmod="2026-10-01T10:00:00+00:00", **kw):
    rec = {"bytes": 1, "capture": {"bytes": 1, "fetched": "2026-10-19T14:31:26Z", "raw_file": "raw/x.html", "url": url},
           "date": lastmod[:10], "fetched": "2026-10-19T14:31:26Z", "id": url, "lastmod": lastmod,
           "raw_file": "raw/x.html", "text": url, "updated_at": "2026-10-19T14:31:26Z", "url": url}
    rec.update(kw)
    return rec


def _store(*recs):
    docs = {f"{i:064x}": json.dumps(r, sort_keys=True).encode() for i, r in enumerate(recs, 1)}
    return list(docs), docs.__getitem__


# --- the index -----------------------------------------------------------------------------

def test_an_index_record_is_read_from_the_version_the_pull_saw_last_and_a_foreign_url_is_set_aside():
    url = "https://www.parliament.nz/en/pb/sc/"
    shas, get = _store(_index(url, "2026-10-01T10:00:00+00:00"), _index(url, "2026-10-20T10:00:00+00:00"),
                       _index("https://example.com/x"))
    r = read_mcp.read_index([(shas[1], 5, url), (shas[0], 9, url), (shas[2], 6, "x")], get)
    assert [(p["url"], p["lastmod"][:10], p["versions"]) for p in r.index_pages] == [(url, "2026-10-01", 2)]
    assert r.index_pages[0]["document"] == shas[0]              # landed last, though its seq was higher: by order
    assert sorted(f[3] for f in r.files) == ["older version", "read", "set aside"]
    assert [why for _, _, why in r.set_aside] == ["parliament-hansard-index: its url is not a parliament.nz page"]


def test_an_index_record_with_a_field_the_lane_has_no_column_for_says_so():
    shas, get = _store(_index("https://www.parliament.nz/en/pb/sc/", newfield=1))
    assert read_mcp.read_index([(shas[0], 0, None)], get).index_pages[0]["fields_unread"] == ["newfield"]


# --- the days ------------------------------------------------------------------------------

TEXT_1 = ("  ORAL QUESTIONS—\n    Question No. 1—Prime\n   Minister ......... 10\n Example Amendment\n  Bill\n"
          "  Second Reading\n")
TEXT_2 = "  QUESTION NO. 4—HOUSING\n"


def test_each_day_is_one_row_its_text_goes_only_to_the_sink_and_each_old_subject_is_found_where_it_is():
    shas, get = _store(_day("2025-01-02", TEXT_1), _day("2025-01-03", TEXT_2), _day("2003-02-11", "Old words."))
    texts = {}
    subjects = {"2025-01-02": [("2025-01-02/1", "Question No. 1—Prime Minister"),
                               ("2025-01-02/2", "Example Amendment Bill"),
                               ("2025-01-02/3", "Question No. 4–Housing"),
                               ("2025-01-02/4", "(continued on Wednesday, 3 January 2025)"),
                               ("2025-01-02/5", "Third Reading"),
                               ("2025-01-02/6", None)]}
    r = read_mcp.read_days([(s, None, None) for s in shas], get, subjects, lambda k, t, sha: texts.__setitem__(k, t))
    assert sorted(texts) == ["2003-02-11", "2025-01-02", "2025-01-03"] and r.set_aside == []
    assert all("text" not in row for row in r.days)
    by = {s["key"]: (s["found"], s["neighbour"]) for s in r.day_subjects}
    assert by == {"2025-01-02/1": ("own day", None), "2025-01-02/2": ("own day", None),
                  "2025-01-02/3": ("neighbouring day", "2025-01-03"),
                  "2025-01-02/4": ("continuation note", None), "2025-01-02/5": ("not found", None),
                  "2025-01-02/6": ("no subject", None)}
    day = {d["key"]: d for d in r.days}
    assert (day["2025-01-02"]["old_sections"], day["2025-01-02"]["old_subjects"],
            day["2025-01-02"]["subjects_in_text"]) == (6, 4, 2)
    assert day["2003-02-11"]["old_sections"] is None
    assert r.counts["days both hold"] == 1 and r.counts["days only the MCP holds"] == 2
    d = day["2025-01-03"]
    assert (d["pdf_url"], d["text_words"], d["word_count"], d["captured_at"][:10]) == (_pdf("2025-01-03"), 3, 3,
                                                                                       "2026-10-26")


def test_a_record_whose_sitting_date_is_not_its_pdf_s_day_is_set_aside():
    shas, get = _store(_day("2025-01-02", "x", sitting_date="2025-01-03"))
    r = read_mcp.read_days([(shas[0], None, None)], get, {}, lambda k, t, sha: None)
    assert r.days == [] and "not the day its PDF's address names" in r.set_aside[0][2]


def test_an_old_day_the_mcp_lacks_is_counted():
    r = read_mcp.read_days([], lambda s: b"", {"2025-01-02": [("2025-01-02/1", "x")]}, lambda k, t, sha: None)
    assert r.counts["old days the MCP lacks"] == 1


# --- the check's MCP half --------------------------------------------------------------------

def _h(**kw):
    c = {"cursor": 100, "arrivals": 100, "documents": 100, "caught": 0, "files": 100, "older versions": 0,
         "files set aside": 0, "rows": 100}
    h = {"parliament-hansard-index": dict(c), "parliament-hansard-debates": dict(c), "fields unread": 0,
         "words": 1000, "word counts differ": 0, "subjects": 100, "in text": 95, "low days": [], "worst day": None,
         "found": {}, "both": 1, "mcp only": 1, "mcp only since the old first day": 0, "old only": 0,
         "sittings the index names": 0}
    h.update(kw)
    return h


O = {c: {"records": 100, "n_docs": 100, "corpus_words": 1000} for c in check.CORPORA}


def test_the_mcp_half_passes_when_every_figure_agrees():
    assert check.mcp_failed(_h(), O, recount=95) == []


@pytest.mark.parametrize("change, said", [
    (dict(subjects=100, **{"in text": 89}), "below 90%"),
    (dict(**{"low days": [("2025-01-02", 4, 10)]}), "below 50%"),
    (dict(words=1011), "words"),
    (dict(**{"word counts differ": 1}), "word_count"),
    (dict(**{"fields unread": 2}), "no column"),
])
def test_the_mcp_half_fails_on_each_figure(change, said):
    assert any(said in p for p in check.mcp_failed(_h(**change), O))


def test_the_mcp_half_fails_when_too_few_are_taken_a_document_is_unread_or_the_recount_differs():
    short = _h()
    short["parliament-hansard-debates"].update(cursor=98, arrivals=98)
    assert any("taken 98 of" in p for p in check.mcp_failed(short, O))
    unread = _h()
    unread["parliament-hansard-index"]["rows"] = 99
    assert any("99 read" in p for p in check.mcp_failed(unread, O))
    assert any("counted again" in p for p in check.mcp_failed(_h(), O, recount=94))


class _Recorder:
    """A connection that records the SQL it is sent and answers zeros."""
    def __init__(self):
        self.sent = []

    def execute(self, sql, args=None):
        self.sent.append(sql)
        return self

    def fetchone(self):
        return (0, 0)

    def fetchall(self):
        return []


def test_the_reader_s_figures_never_read_the_private_twin():
    rec = _Recorder()
    check.mcp_held(rec, "hansard", "mcpsource")
    assert rec.sent and not any("_private." in s for s in rec.sent)
    rec = _Recorder()
    check.owner_recount(rec, "hansard")
    assert any("hansard_private.day_texts" in s for s in rec.sent)      # the owner's recount does, and is the only one


# --- the filled sample --------------------------------------------------------------------

@pytest.fixture(scope="module")
def filled(sample_schema):
    schema = sample_schema
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        cur = conn.execute(f"SELECT * FROM {schema}.hansard_days ORDER BY key")
        days = [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        yield {"schema": schema, "conn": conn, "days": days}


def test_the_sample_s_days_read_as_their_comments_say(filled):
    by = {d["key"]: d for d in filled["days"]}
    assert sorted(by) == ["2003-02-11", "2024-11-20", "2025-12-09", "2026-07-30", "2026-09-23"]
    assert by["2003-02-11"]["old_sections"] is None and by["2026-07-30"]["old_sections"] is None
    assert by["2024-11-20"]["subjects_in_text"] >= 0.9 * by["2024-11-20"]["old_subjects"]
    assert by["2025-12-09"]["subjects_in_text"] < 0.9 * by["2025-12-09"]["old_subjects"]
    assert all(d["word_count"] == d["text_words"] and d["pdf_url"].endswith(f"{d['key']}-daily.pdf") for d in by.values())
    conn, schema = filled["conn"], filled["schema"]
    n = conn.execute(f"SELECT count(*), min(length(text)) FROM {schema}_private.hansard_day_texts").fetchone()
    assert n[0] == 5 and n[1] > 0
    assert conn.execute(f"SELECT count(*) FROM {schema}.hansard_index_pages").fetchone()[0] == 2


def test_every_day_keeps_the_row_contract(filled):
    today = dt.date.today()
    for r in filled["days"]:
        row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from")}
        row["loaded_at"] = r["loaded_at"].isoformat()
        row["filed"] = {"sitting_on": r["sitting_on"].isoformat()}
        assert rowcontract.validate(row, today) == [], r["key"]


def test_the_days_view_carries_no_text_and_both_views_say_where_the_day_is_also_held(filled):
    from registers.hansard import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.hansard_pub_"))
    cur = conn.execute(f"SELECT * FROM {schema}.hansard_pub_hansard_days LIMIT 0")
    cols = [d[0] for d in cur.description]
    notes = dict(conn.execute(f"SELECT key, old_note FROM {schema}.hansard_pub_hansard_days").fetchall())
    sit = dict(conn.execute(f"SELECT key, day_note FROM {schema}.hansard_pub_hansard_sittings").fetchall())
    conn.rollback()
    assert "text" not in cols and "citation_url" in cols and "document" in cols
    assert notes["2024-11-20"] == "also held as the old transcript's sections"
    assert notes["2003-02-11"] == "not held as the old transcript's sections"
    assert sit["2024-11-20"] == "also held as the daily PDF's text (the MCP)"
