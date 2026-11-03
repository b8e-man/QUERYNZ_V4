"""A profile is never edited: a new version is a new line, one higher; the
newest version is current by version not position; the shipped file holds
the shipped profiles with no street address in it."""
import json
import os
import re

import pytest

import support.profiles as pr


def test_the_shipped_profiles_load_and_carry_no_address():
    cur = pr.current()
    assert len(cur) == 179 and "courts-maori-court-judgment" in cur and "lbp-register-search-page" in cur and "lbp-register-practitioner-page" in cur and "council-minutes-scanned" in cur and "council-minutes-standard" in cur and "council-minutes-text" in cur and "linz-wfs-page" in cur and "papers-past-archive-row" in cur and "insolvency-register-estate" in cur and "insolvency-register-removals" in cur and "gazette-jp-list" in cur and "gazette-board-intervention" in cur and cur["companies-monthly-package"]["version"] == 2 and cur["mfat-russia-sanctions-register-workbook"]["version"] == 2 and "rea-decision-abstract" in cur and "interests-register-pdf-text" in cur and "interests-register-html-text" in cur and "ec-party-return-text" in cur and "mcp-hansard-debates-record" in cur and "mcp-diary-entry" in cur and "mcp-parliament-wayback-page" in cur and "courts-case-page" in cur   # 153: hansard-2's two, the diary profile and the three parliament profiles (27 October); courts-2's seven (30 October); beehive-2's release body, hansard-3's day, parliament-2's two at version 2 replace theirs (31 October); courts-2's four new kinds, ten versions bumped (fix-registers-courts-2, 31 October); the companies monthly package, the REA decision abstract and the two councillor-interests readings, the Gazette's five office profiles, the two council-minutes readings, MFAT's workbook at version 2 (2 November); the Māori courts' judgment (ruling 140, 3 November)
    assert cur["ec-party-return-scan"]["version"] == 5 and cur["ec-party-return-scan"]["ocr"]["trial"]["ruling"] == 60   # the trial verdict, 19 October
    hist = pr.history("ec-party-return-scan")
    assert [h["version"] for h in hist] == [1, 2, 3, 4, 5]
    text = open(pr.PROFILES, encoding="utf-8").read()
    assert not re.search(r"\d+ [A-Z][a-z]+ (Road|Street|Avenue)", text)


def test_add_version_appends_and_never_edits(tmp_path):
    p = str(tmp_path / "profiles.jsonl")
    v1 = pr.add_version("ec-test-form", {"title": "a test form", "recognise": {"pages": 2}}, by="founding-2", path=p)
    v2 = pr.add_version("ec-test-form", {"title": "a test form, revised"}, by="founding-2", path=p)
    assert (v1["version"], v2["version"]) == (1, 2)
    lines = [json.loads(l) for l in open(p)]
    assert len(lines) == 2 and lines[0]["title"] == "a test form"      # the first line is untouched
    assert pr.profile("ec-test-form", p)["version"] == 2
    assert set(pr.FIELDS) <= set(lines[1])


def test_current_is_by_version_not_by_position(tmp_path):
    p = str(tmp_path / "profiles.jsonl")
    with open(p, "w") as f:
        f.write(json.dumps({"kind": "document-profile", "slug": "x", "version": 3, "title": "three"}) + "\n")
        f.write(json.dumps({"kind": "document-profile", "slug": "x", "version": 2, "title": "two"}) + "\n")
    assert pr.profile("x", p)["title"] == "three"
    assert pr.add_version("x", {"title": "four"}, "t", path=p)["version"] == 4


def test_refusals(tmp_path):
    p = str(tmp_path / "p.jsonl")
    with pytest.raises(ValueError):
        pr.add_version("Bad Slug", {}, "t", path=p)
    with pytest.raises(ValueError):
        pr.add_version("ok-slug", {}, "", path=p)
    assert not os.path.exists(p)


# --- what a profile extracts (Arthur, 3 November 2026) ---------------------------------------------------------------

def _it(field, n, by="model", private=False, ask="read it"):
    return {"field": field, "iteration": n, "by": by, "ask": ask, "private": private, "kinds": None}


def test_an_extract_list_grows_by_iteration_and_a_document_is_asked_only_what_it_lacks(tmp_path):
    p = str(tmp_path / "profiles.jsonl")
    one = [_it("people", 1)]
    pr.add_version("courts-test", {"title": "t", "extract": one}, by="t", path=p)
    two = one + [_it("identifiers", 2, by="pattern", private=True)]
    v2 = pr.add_version("courts-test", {"title": "t", "extract": two}, by="t", path=p)
    assert v2["iteration"] == 2 and pr.iteration(v2) == 2
    assert [i["field"] for i in pr.wanted(v2, {})] == ["identifiers", "people"]
    assert [i["field"] for i in pr.wanted(v2, {"people": 1})] == ["identifiers"]
    assert pr.wanted(v2, {"people": 1, "identifiers": 2}) == []
    # a changed instruction is a new iteration of the field: a document read at the old one asks for it again
    v3 = pr.add_version("courts-test", {"title": "t", "extract": two + [_it("people", 3, ask="read it, with roles")]},
                        by="t", path=p)
    assert [(i["field"], i["iteration"]) for i in pr.wanted(v3, {"people": 1, "identifiers": 2})] == [("people", 3)]


@pytest.mark.parametrize("bad, why", [
    ([_it("identifiers", 2, by="pattern", private=True)], "dropped"),               # people dropped
    ([{**_it("people", 1), "ask": "something else"}], "without a new iteration"),
    ([_it("people", 1), _it("x", 2, by="guess")], "`by`"),
    ([_it("people", 1), {**_it("x", 2), "private": None}], "`private`"),
    ([_it("people", 1), _it("x", 2, ask=" ")], "instruction"),
    ([], "drops the extract list"),
])
def test_an_extract_list_never_loses_or_quietly_changes_a_field(tmp_path, bad, why):
    p = str(tmp_path / "profiles.jsonl")
    pr.add_version("courts-test", {"title": "t", "extract": [_it("people", 1)]}, by="t", path=p)
    with pytest.raises(ValueError, match=re.escape(why)):
        pr.add_version("courts-test", {"title": "t", "extract": bad}, by="t", path=p)
    assert len(pr.history("courts-test", p)) == 1


def test_a_document_records_the_iteration_each_field_was_extracted_at(tmp_path, monkeypatch):
    """In the sample database, inside a transaction rolled back: record, done, never back an iteration, behind."""
    import support.db as db
    from support.docstore import landing
    from support.profiles import extraction
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
