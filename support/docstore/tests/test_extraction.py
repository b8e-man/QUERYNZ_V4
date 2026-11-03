"""docs.extractions: what each document has had extracted, by profile and field (Arthur, 3 November 2026)."""
import os

import pytest

import support.profiles as pr


def _it(field, n, by="model", private=False, ask="read it"):
    return {"field": field, "iteration": n, "by": by, "ask": ask, "private": private, "kinds": None,
            "lands": ["lane_private.details.value" if private else "people.name"], "links": []}


def test_a_document_records_the_iteration_each_field_was_extracted_at(tmp_path, monkeypatch):
    """In the sample database, inside a transaction rolled back: record, done, never back an iteration, behind."""
    import support.db as db
    from support.docstore import landing
    from support.docstore import extraction
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here")
    p = str(tmp_path / "profiles.jsonl")
    prof = pr.add_version("courts-test", {"title": "t", "extract": [_it("people", 1), _it("identifiers", 2, private=True)]},
                          by="t", path=p)
    monkeypatch.setattr(pr, "PROFILES", p)
    conn = db.connect(db.OWNER_KEY, "querynz_v4_sample")
    try:
        conn.execute(landing.tables_sql())
        sha = "e" * 64
        conn.execute("INSERT INTO docs.documents (sha256, size, kind, source, path) VALUES (%s, 1, 'text', 'test', 'x') "
                     "ON CONFLICT DO NOTHING", (sha,))
        assert extraction.done(conn, sha, "courts-test") == {}
        assert extraction.behind(conn, "courts-test", [sha]) == {"people": 1, "identifiers": 1}
        extraction.record(conn, sha, "courts-test", pr.wanted(prof, {})[1:], reader="test 1", model="m")   # people only
        assert extraction.done(conn, sha, "courts-test") == {"people": 1}
        assert [i["field"] for i in pr.wanted(prof, extraction.done(conn, sha, "courts-test"))] == ["identifiers"]
        extraction.record(conn, sha, "courts-test", [{"field": "people", "iteration": 3}], reader="test 1")
        extraction.record(conn, sha, "courts-test", [{"field": "people", "iteration": 1}], reader="test 1")
        assert extraction.done(conn, sha, "courts-test")["people"] == 3, "a row never moves back an iteration"
        assert extraction.behind(conn, "courts-test", [sha]) == {"people": 0, "identifiers": 1}
    finally:
        conn.rollback()
        conn.close()
