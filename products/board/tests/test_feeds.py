"""The feeds tab (feeds.py): a feed made from an entity, kept as lines, narrowed by its form; and live."""
from __future__ import annotations

import json

from products.board import feeds

F = {"feed": "ab12", "name": "Fonterra", "entity_id": "companies:companies/9429037784669", "kind": "organisation",
     "relations": ["named", "central", "role", "connected"], "subjects_on": True,
     "subjects": [{"name": "dairy", "signifiers": ["dairy"], "on": True, "here": 27}],
     "types_out": [], "sources_out": [], "forms_out": [], "withdrawn": False}


def test_a_feed_is_its_newest_line_and_nothing_is_erased(tmp_path):
    p = str(tmp_path / "feeds.jsonl")
    feeds.save(F, p)
    to = feeds.take({"f": ["ab12"], "name": ["Fonterra watch"], "rel": ["named", "role"], "subj_0": [json.dumps(F["subjects"][0])],
                     "sig_0": ["milk"], "subj_new": ["3D printing"], "type": ["news"],
                     "src_all": ["rnz.co.nz", "nzherald.co.nz"], "src": ["rnz.co.nz"],
                     "form_all": ["news", "opinion"], "form": ["news"]}, p)
    assert to == "/feeds?f=ab12"
    lines = open(p).read().splitlines()
    assert len(lines) == 2, "a save is a line"
    f = feeds.feeds(p)["ab12"]
    assert f["name"] == "Fonterra watch" and f["relations"] == ["named", "role"] and f["subjects_on"] is False
    assert f["subjects"][0]["on"] is False and f["subjects"][0]["signifiers"] == ["dairy", "milk"], "one subject, two signifiers"
    assert f["subjects"][1] == {"name": "3D printing", "signifiers": ["3D printing"], "on": True, "typed": True}
    assert f["sources_out"] == ["nzherald.co.nz"] and f["forms_out"] == ["opinion"] and f["types_out"] == []
    assert feeds.take({"f": ["ab12"], "withdraw": ["1"]}, p) == "/feeds" and feeds.feeds(p)["ab12"]["withdrawn"]


def test_the_controls_name_every_relation_and_the_types_not_yet_joined():
    h = feeds.controls(F, {"connected": 3, "sources": {"rnz.co.nz": 4}, "forms": {"news": 3}})
    for _, label in feeds.RELATIONS:
        assert label in h
    assert "Hansard (not joined yet)" in h and "3 entities one step away" in h and 'value="rnz.co.nz" checked' in h


def test_a_typed_subject_catches_its_other_forms_a_suggested_one_only_itself():
    class C:
        def execute(self, sql, params=None):
            return type("R", (), {"fetchall": lambda _s: [("3d printed firearms",), ("money and banking",), ("banking",)]})()
    assert feeds.subject_keys(C(), [{"name": "banking", "signifiers": ["banking"], "on": True}]) == {"banking"}
    assert feeds.subject_keys(C(), [{"name": "3D printing", "signifiers": ["3D printing"], "on": True, "typed": True}]) == {"3d printed firearms"}


def test_the_live_feed_of_a_company_is_set_newest_first(tmp_path):
    from products.board import db
    p = str(tmp_path / "feeds.jsonl")
    with db.read_connect() as conn:
        assert "make a feed" in feeds.finder(conn, "fonterra")
        to = feeds.create(conn, {"entity_id": [F["entity_id"]]}, p)
        fid = to.split("=")[1]
        html = feeds.render(conn, {"f": [fid]}, p)
        rows, facts = feeds.items(conn, feeds.feeds(p)[fid])
    assert "the feed could not be read" not in html and 'class="fd-story' in html and "narrow" in html
    dates = [r["published_at"] for r in rows if r["published_at"]]
    assert dates == sorted(dates, reverse=True), "newest first"
