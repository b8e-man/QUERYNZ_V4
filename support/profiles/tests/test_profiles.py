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
    assert len(cur) == 154 and "ec-party-return-text" in cur and "mcp-hansard-debates-record" in cur and "mcp-diary-entry" in cur and "mcp-parliament-wayback-page" in cur and "courts-case-page" in cur   # 153: hansard-2's two, the diary profile and the three parliament profiles (27 October); courts-2's seven (30 October); beehive-2's release body (31 October)
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
