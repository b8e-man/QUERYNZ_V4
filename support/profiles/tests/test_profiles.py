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
    return {"field": field, "iteration": n, "by": by, "ask": ask, "private": private, "kinds": None,
            "lands": ["lane_private.details.value" if private else "people.name"], "links": []}


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



# --- where a field lands and what it can link (contract item 9) ---------------------------------------------------

_LINK = {"key": "nzbn", "to": "a company on the register", "rule": None}


@pytest.mark.parametrize("bad, why", [
    ({"lands": []}, "`lands` lists"),
    ({"lands": None}, "`lands` lists"),
    ({"lands": ["name"]}, "table.column"),
    ({"lands": ["People.name"]}, "table.column"),
    ({"lands": ["people.name", "people.name"]}, "listed twice"),
    ({"links": None}, "`links` is a list"),
    ({"links": [{"key": "nzbn", "to": "x"}]}, "{key, to, rule}"),
    ({"links": [{**_LINK, "key": "shoe size"}]}, "`links` key"),
    ({"links": [{**_LINK, "to": " "}]}, "`to`"),
    ({"links": [{**_LINK, "rule": "full name"}]}, "rule id"),
    ({"links": [_LINK, dict(_LINK)]}, "listed twice"),
])
def test_an_extract_item_says_where_it_lands_and_what_it_links(tmp_path, bad, why):
    p = str(tmp_path / "profiles.jsonl")
    with pytest.raises(ValueError, match=re.escape(why)):
        pr.add_version("courts-test", {"title": "t", "extract": [{**_it("people", 1), **bad}]}, by="t", path=p)
    assert pr.history("courts-test", p) == []


def test_a_private_field_lands_only_in_a_private_table(tmp_path):
    p = str(tmp_path / "profiles.jsonl")
    with pytest.raises(ValueError, match="is private"):
        pr.add_version("courts-test", {"title": "t", "extract": [{**_it("ids", 1, private=True), "lands": ["people.value"]}]},
                       by="t", path=p)
    ok = {**_it("ids", 1, private=True), "links": [_LINK, {"key": "name", "to": "every row of pub.names", "rule": "full-name@1"}]}
    assert pr.add_version("courts-test", {"title": "t", "extract": [ok]}, by="t", path=p)["iteration"] == 1


def test_a_version_that_only_adds_to_the_extract_list_keeps_the_reading_version(tmp_path):
    """The stored readings are keyed by the profile's version: a version adding only an extract list must not orphan them."""
    p = str(tmp_path / "profiles.jsonl")
    pr.add_version("courts-test", {"title": "t", "prompt": "a", "reading": {"split": "whole"}}, by="t", path=p)
    pr.add_version("courts-test", {"title": "t", "prompt": "b", "reading": {"split": "whole"}}, by="t", path=p)
    assert pr.reading_version("courts-test", p) == 2
    pr.add_version("courts-test", {"title": "t", "prompt": "b", "reading": {"split": "whole"}, "extract": [_it("people", 1)]},
                   by="u", path=p)
    pr.add_version("courts-test", {"title": "t", "prompt": "b", "reading": {"split": "whole"},
                                   "extract": [_it("people", 1), _it("ids", 2, private=True)]}, by="u", path=p)
    assert pr.profile("courts-test", p)["version"] == 4 and pr.reading_version("courts-test", p) == 2
    pr.add_version("courts-test", {"title": "t", "prompt": "c", "reading": {"split": "whole"},
                                   "extract": [_it("people", 1), _it("ids", 2, private=True)]}, by="u", path=p)
    assert pr.reading_version("courts-test", p) == 5, "a changed prompt is a new reading"
    assert pr.reading_version("no-such", p) is None


def test_every_extract_list_in_the_ledger_is_well_formed():
    for slug, prof in pr.current().items():
        if prof.get("extract"):
            pr.check_extract(prof["extract"])
            assert prof["iteration"] == pr.iteration(prof), slug
            for older, newer in zip(pr.history(slug), pr.history(slug)[1:]):
                pr.check_extract(newer.get("extract"), older.get("extract"))
