"""Stage 2 of the one report, near links on request (ruling 151): fast tests on
made-up rows; the real tables are in test_near_real.py (slow)."""
import copy

import pytest

from products.report import db, near, rules, walk
from products.report import near_server
from products.report import template as tpl


def _it(ref, grade="confirmed", reason=None, view="directors", **extra):
    reg, _, key = ref.partition(":")
    it = {"ref": ref, "view": view, "register": reg, "kind": "person", "title": f"row {key}", "statement": f"a director, row {key}",
          "dates": {"text": "undated", "undated": True}, "citation": {"view": view, "key": key}, "grade": grade, "reason": reason,
          "rule": None, "via": None, "flags": [], "row": {}, "suppressed": False, "note": ""}
    it.update(extra)
    return it


def _report():
    subject = _it("companies:s1", cite=1)
    sec = {"name": "companies", "heading": "Companies", "text": "", "views": ["directors"], "items": [
        _it("companies:c1", cite=2, people=[_it("companies:p1", cite=3), _it("companies:p2", "near", "a namesake", cite=4)]),
        _it("companies:n1", "near", "through two people", cite=5)], "confirmed": 1, "near": 1, "omitted": 0, "omitted_views": [],
        "blank": None, "not_held": []}
    return {"found": True, "ref": "companies:s1", "template": {"name": "diagnostic", "reads": [{"view": "directors"}]},
            "subject": subject, "members": [_it("companies:m1", cite=6), _it("companies:m2", "near", "contested", cite=7)],
            "sections": [sec], "citations": [{"n": i, "view": "directors", "key": k} for i, k in
                                             enumerate(["s1", "c1", "p1", "p2", "n1", "m1", "m2"], 1)],
            "problems": [], "flags": [], "hubs": []}


def test_the_stage_1_records_are_the_confirmed_refs_only():
    assert near.confirmed_refs(_report()) == ["companies:c1", "companies:m1", "companies:p1", "companies:s1"]
    assert near.listed_refs(_report()) >= {"companies:p2", "companies:n1", "companies:m2"}


def test_a_near_line_always_has_a_reason():
    assert near.reason_for({"rule": walk.NAME_ONLY, "reason": ""}).startswith("the two rows share a first and last name")
    assert near.reason_for({"rule": "anything@1", "reason": None}) == near.NO_REASON_DEFAULT
    assert near.reason_for({"rule": walk.NAME_ONLY, "reason": None, "evidence": {"full_name": "a b c", "middle": "b"}}) == near.NO_REASON_FULL
    lbp = "the licence number matches but the names are not a full match; the lack of one may indicate another rendering of the name"
    assert near.reason_for({"rule": "lbp-number@1", "reason": lbp}) == lbp


class FakeLinks:
    """db.rows answering the near query with given pub.links rows."""

    def __init__(self, links):
        self.links, self.sql = links, []

    def __call__(self, conn, sql, params=()):
        self.sql.append(sql)
        got = [dict(l, total=len(self.links)) for l in self.links]
        return got


def _link(a, b, rule, grade="near", reason="r"):
    return {"row_a": a, "row_b": b, "rule": rule, "grade": grade, "reason": reason, "evidence": {}, "watch": [], "decision": None}


def test_near_links_reads_near_only_drops_what_is_listed_and_orders_by_rule_then_ref(monkeypatch):
    fake = FakeLinks([_link("companies:s1", "x:zz", "organisation-name@1"), _link("x:aa", "companies:s1", "company-name@1"),
                      _link("companies:s1", "companies:m1", "name-only@1"), _link("companies:s1", "x:bb", "full-name@1", grade="confirmed"),
                      _link("companies:c1", "x:aa", "organisation-name@1")])
    monkeypatch.setattr(db, "rows", fake)
    monkeypatch.setattr(walk, "links_built", lambda conn: True)
    monkeypatch.setattr(walk, "star_links", lambda conn, spokes, seen: ([], 0))
    got = near.near_links(None, ["companies:s1", "companies:c1"], {"companies:m1"})
    assert "grade = 'near'" in fake.sql[0]
    assert [(l["rule"], l["other"]) for l in got["links"]] == [("company-name@1", "x:aa"), ("organisation-name@1", "x:zz")]
    assert all(l["grade"] == "near" and l["reason"] for l in got["links"])
    assert got["already"] == 1   # the link to a listed member


def _patch_items(monkeypatch, made):
    """stage2_items over made-up links: walk.link_item returns `made`'s items,
    as confirmed as the walk's helper would make them, entity and all."""
    monkeypatch.setattr(near, "near_links", lambda conn, refs, listed: {"links": [
        {"this": "companies:s1", "other": it["ref"], "rule": "name-only@1", "reason": "shares a first and last name", "grade": "near"}
        for it in made], "omitted": 3, "already": 2})
    by_ref = {it["ref"]: it for it in made}
    monkeypatch.setattr(walk, "link_item", lambda conn, l, cache, allowed, skipped, via=None: copy.deepcopy(by_ref[l["other"]]))
    monkeypatch.setattr(walk, "name_joined", lambda conn, people, allowed, skipped: ({}, 0))
    monkeypatch.setattr(walk, "named_rows", lambda *a, **k: [])
    monkeypatch.setattr(walk, "resolve", lambda conn, ref, cache: None)


def test_a_near_link_never_enters_the_confirmed_set(monkeypatch):
    made = [_it("x:far1", entity=_it("x:co1")), _it("x:far2")]   # confirmed as the helper hands them over, the entity too
    _patch_items(monkeypatch, made)
    r1 = _report()
    before = copy.deepcopy(r1)
    r2 = near.stage2(None, r1)
    assert near.confirmed_refs(r2, stage1_only=False) == near.confirmed_refs(r1)
    sec = r2["sections"][-1]
    assert sec["name"] == near.SECTION["name"] and sec["confirmed"] == 0 and sec["near"] == 2
    for it in sec["items"]:
        assert it["grade"] == "near" and it["reason"] and it["near"] and it["stage"] == 2
        assert it.get("entity") is None or it["entity"]["grade"] == "near"
    assert r1 == before   # the first report is not changed
    assert r2["stage"] == 2 and r2["stage2"]["omitted"] == 3 and r2["stage2"]["already_listed"] == 2
    assert [c["n"] for c in r2["citations"]] == list(range(1, 10)) and {it["cite"] for it in sec["items"]} == {8, 9}
    assert r2["problems"] == rules.problems(r2) == []


def test_the_guard_refuses_a_confirmed_item_in_the_second_pass(monkeypatch):
    monkeypatch.setattr(near, "stage2_items", lambda conn, report: {"items": [_it("x:sneaked")], "by_kind": {}, "omitted": 0, "already": 0,
                                                                    "skipped": [], "from": 4})
    with pytest.raises(AssertionError, match="confirmed set"):
        near.stage2(None, _report())


def test_a_row_the_first_report_lists_is_not_listed_again(monkeypatch):
    _patch_items(monkeypatch, [_it("companies:n1"), _it("x:new")])
    r2 = near.stage2(None, _report())
    assert [it["ref"] for it in r2["sections"][-1]["items"]] == ["x:new"]


def test_the_limit_is_counted_never_silent(monkeypatch):
    monkeypatch.setitem(near.LIMITS, "items", 2)
    _patch_items(monkeypatch, [_it(f"x:r{i}") for i in range(5)])
    r2 = near.stage2(None, _report())
    assert len(r2["sections"][-1]["items"]) == 2 and r2["stage2"]["omitted"] == 3 + 3
    assert "more near link(s) past the limits" in near.summary(r2)


def test_rerunning_the_second_pass_replaces_its_section(monkeypatch):
    _patch_items(monkeypatch, [_it("x:new")])
    r2 = near.stage2(None, near.stage2(None, _report()))
    assert [s["name"] for s in r2["sections"]].count(near.SECTION["name"]) == 1


def test_nothing_found_says_so_and_a_report_not_found_is_returned_as_it_is(monkeypatch):
    _patch_items(monkeypatch, [])
    r2 = near.stage2(None, _report())
    assert r2["sections"][-1]["blank"] == near.BLANK and rules.problems(r2) == []
    assert near.stage2(None, {"found": False, "sections": []})["found"] is False


def test_the_hook_asks_by_its_own_query_name_never_a_template_parameter():
    assert near_server.asked({"near": ["1"]}) and not near_server.asked({}) and not near_server.asked({"near": ["0"]})
    h = near_server.href("companies:s1", "diagnostic")
    assert h.startswith("/report/companies:s1?") and "near=1" in h
    for name in tpl.folders():
        assert near_server.QUERY_NAME not in {p.name for p in tpl.by_name(name).params}, name
    assert near_server.offer({"found": True, "ref": "companies:s1"}).count("follow the near links") == 1
    assert near_server.offer({"found": True, "ref": "companies:s1", "stage": 2}) == ""
