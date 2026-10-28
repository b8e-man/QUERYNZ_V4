"""The links lane's third grade, `related` (ruling 106 (2)), on a fixture
walk: two companies under one name, one with a year in brackets, a person
confirmed on both. The report states the relation in words, "succeeded by",
the two companies in the evidence's date order and the people on both, under
its own heading; it never walks the two into one (the later company is no
entity of the walk and its rows are not read) and never words them as near.
Also: the links rules ruling 106 and 107 added are named in words where the
report names a rule, held equal to the board's words."""
import ast
import datetime as dt
import pathlib

import pytest

from products.report import build, catalogue as cat, memo, rules, template as tpl, walk

A, B = "companies:companies/1", "companies:companies/2"
COMPANIES = {
    A: {"key": "companies/1", "name": "SPEIRS FOODS LIMITED", "status": "Registered", "entity_type": "LTD", "nzbn": "9429000000001",
        "registered_on": dt.date(1987, 3, 1), "removed_on": None, "in_latest": True, "first_file": "f1", "last_file": "f9"},
    B: {"key": "companies/2", "name": "SPEIRS FOODS (2011) LIMITED", "status": "Registered", "entity_type": "LTD", "nzbn": "9429000000002",
        "registered_on": dt.date(2011, 6, 15), "removed_on": None, "in_latest": True, "first_file": "f1", "last_file": "f9"},
}
SECRET = "Withheld PERSONNAME"


def director(company: str, tag: str, name: str, suppressed: bool = False) -> dict:
    return {"key": f"{COMPANIES[company]['key']}/director/{tag}", "entity_key": COMPANIES[company]["key"], "full_name": name,
            "role_type": "Director", "appointed_on": dt.date(2011, 6, 15), "ended_on": None, "in_latest": True,
            "first_file": "f1", "last_file": "f9", "suppressed": suppressed, "document": None}


DIRECTORS = [director(A, "a", "Jane DOE"), director(A, "s", SECRET, True), director(B, "b", "Jane DOE"), director(B, "s2", SECRET, True)]
# the link as links publishes it, row_a the later company, so the order can only come from the evidence
LINK = {"link_id": 1, "row_a": B, "row_b": A, "rule": "successor-name@1", "grade": "related", "reason": None, "relation": "succeeded by",
        "watch": [], "decision": None,
        "evidence": {"earlier": A, "later": B, "relation": "succeeded by", "order": "by registration date", "shared_people": 2,
                     "shared_rows": [{"earlier": f"companies:{DIRECTORS[0]['key']}", "later": f"companies:{DIRECTORS[2]['key']}", "group": "g1", "name": "x"},
                                     {"earlier": f"companies:{DIRECTORS[1]['key']}", "later": f"companies:{DIRECTORS[3]['key']}", "group": "g2", "name": "x"}]}}


@pytest.fixture
def fake(monkeypatch):
    """The walk's reads answered from the fixture; `seen` records which
    companies' own rows the walk read."""
    seen = []
    by_ref = {**{ref: (cat.BY_NAME["companies"], r) for ref, r in COMPANIES.items()},
              **{f"companies:{d['key']}": (cat.BY_NAME["directors"], d) for d in DIRECTORS}}

    def db_rows(conn, sql, params=()):
        if "from pub.links" in sql:
            refs = set(params[0])
            got = [dict(LINK)] if LINK["row_a"] in refs or LINK["row_b"] in refs else []
            return [dict(l, total=len(got)) for l in got]
        return []

    def rows_where(conn, view, column, value, order):
        if view == "directors" and column == "entity_key":
            seen.append(value)
            got = [d for d in DIRECTORS if d["entity_key"] == value]
            return len(got), got
        return 0, []

    def entity_of(conn, v, r):
        if v.name == "directors":
            return by_ref[f"companies:{r['entity_key']}"]
        return None, None

    def group_of(conn, ref):
        rows_ = [f"companies:{DIRECTORS[0]['key']}", f"companies:{DIRECTORS[2]['key']}"] if ref in (f"companies:{DIRECTORS[0]['key']}",) else [ref]
        return {"built": True, "why": "", "group_id": "g1", "contested": False, "settings": None, "rows": rows_, "size": len(rows_), "omitted": 0}

    monkeypatch.setattr(walk.db, "rows", db_rows)
    monkeypatch.setattr(walk.db, "has_relation", lambda conn, schema, name: True)
    monkeypatch.setattr(walk.rows, "locate", lambda conn, ref: by_ref.get(ref, (None, None)))
    monkeypatch.setattr(walk.rows, "entity_of", entity_of)
    monkeypatch.setattr(walk.rows, "rows_where", lambda *a, **k: (0, []))
    monkeypatch.setattr(walk, "rows_where", rows_where)
    monkeypatch.setattr(walk, "group_of", group_of)
    monkeypatch.setattr(walk, "flag_people", lambda conn, items: None)
    monkeypatch.setattr(walk, "number_joined", lambda conn, entities, allowed, skipped: [])
    monkeypatch.setattr(walk, "name_joined", lambda conn, people, allowed, skipped: ({}, 0))
    return seen


def report(ref):
    t = tpl.by_name("subject")
    return build.build(None, ref, t, held=set(t.views))


def items(r, name=None):
    return [it for s in r["sections"] if name is None or s["name"] == name for it in s["items"]]


@pytest.mark.parametrize("start", [A, B])
def test_a_succession_reads_as_succeeded_by_in_date_order_never_one_and_never_near(fake, start):
    r = report(start)
    assert r["found"] and r["problems"] == [], r["problems"]
    other = B if start == A else A
    rel = items(r, "related")
    assert [s["heading"] for s in r["sections"] if s["name"] == "related"] == [build.RELATED_SECTION["heading"]]
    assert len(rel) == 1 and rel[0]["ref"] == other and rel[0]["grade"] == "related" and rel[0]["reason"] is None
    assert rel[0]["statement"] == "SPEIRS FOODS LIMITED (registered 1 March 1987) succeeded by SPEIRS FOODS (2011) LIMITED (registered 15 June 2011)"
    assert (rel[0]["earlier"], rel[0]["later"]) == (A, B)
    # never walked into one: the other company is no entity of the walk, its rows are not read, and it is in no other section
    w = walk.walk(None, start, set(tpl.by_name("subject").views))
    assert other not in {e["ref"] for e in w["entities"]} and other not in {it["ref"] for it in w["confirmed"] + w["near"]}
    assert COMPANIES[other]["key"] not in fake
    # the successor link makes no item but the related one; the other company may still be met through a person on both
    # (the officers reach: the officer's other role, near through the officer, never by the link)
    assert [it for it in items(r) if it.get("rule") == LINK["rule"] and it["grade"] != "related"] == []
    assert {it.get("rule") for it in items(r) if it["ref"] == other and it["grade"] != "related"} <= {"through-officer"}
    # never near: no item, section count or memo line words the pair as perhaps one
    assert not [it for it in items(r) if it["grade"] == "near" and it.get("rule") != "through-officer"]
    text = memo.text(r)
    line = next(x for x in text.splitlines() if "[related]" in x)
    assert line.strip().startswith("- [related] SPEIRS FOODS LIMITED") and "succeeded by SPEIRS FOODS (2011) LIMITED" in line and "near" not in line and "may be" not in text
    assert "RELATED COMPANIES: ONE SUCCEEDED BY ANOTHER  (1 related)" in text
    assert cat.RULE_WORDS["successor-name"] in text and "links rule successor-name, version 1" in text
    # the people on both: this side's row, cited; the suppressed counted, never named
    people = rel[0]["people"]
    side = DIRECTORS[0] if start == A else DIRECTORS[2]
    assert [p["ref"] for p in people] == [f"companies:{side['key']}"] and people[0].get("cite")
    assert rel[0]["shared_people"] == 2 and rel[0]["people_hidden"] == 1
    assert f"2 people on both: Jane DOE [{people[0]['cite']}]; 1 whose name is suppressed or whose row is not found, not named" in text
    assert SECRET not in text and SECRET not in memo.html_body(r)
    assert f"[{people[0]['cite']}] " in text.split("CITATIONS")[1]
    html = memo.html_body(r)
    assert '<span class="grade related">related</span>' in html and "1 related</span></h3>" in html


def test_from_a_person_on_both_the_two_companies_stay_two_and_the_relation_is_stated_once(fake):
    start = f"companies:{DIRECTORS[0]['key']}"
    r = report(start)
    assert r["found"] and r["problems"] == [], r["problems"]
    companies = [it for it in items(r, "companies") if it["view"] == "companies"]
    assert sorted(it["ref"] for it in companies) == [A, B] and all(it["grade"] == "confirmed" for it in companies)
    rel = items(r, "related")
    assert len(rel) == 1 and (rel[0]["earlier"], rel[0]["later"]) == (A, B)


def test_the_rules_refuse_a_related_link_worded_near_or_listed_with_the_companies():
    def it(**kw):
        x = {"ref": B, "view": "companies", "kind": "organisation", "title": "SPEIRS FOODS (2011) LIMITED", "entity_title": "SPEIRS FOODS LIMITED",
             "statement": "SPEIRS FOODS LIMITED (registered 1 March 1987) succeeded by SPEIRS FOODS (2011) LIMITED (registered 15 June 2011)",
             "dates": {"undated": False, "text": "registered 15 June 2011"}, "citation": {"view": "companies", "key": "companies/2"}, "cite": 1,
             "grade": "related", "reason": None, "relation": "succeeded by", "earlier": A, "later": B, "suppressed": False, "row": {}, "flags": [], "people": []}
        x.update(kw)
        return x

    def rep(item, section="related"):
        return {"found": True, "subject": None, "members": [], "flags": [], "sections": [{"name": section, "heading": "H", "items": [item], "blank": None}]}
    assert rules.problems(rep(it())) == []
    assert any("rule 10" in p for p in rules.problems(rep(it(reason="two companies under one name: may be the same"))))
    assert any("rule 10" in p for p in rules.problems(rep(it(), section="companies")))
    assert any("rule 10" in p for p in rules.problems(rep(it(relation=None))))
    assert any("rule 10" in p for p in rules.problems(rep(it(later=A))))
    assert any("rule 6" in p for p in rules.problems(rep(it(people=[it(ref="p:1", view="directors", title=SECRET, statement=f"{SECRET}: Director",
                                                                        grade="confirmed", relation=None, suppressed=True, row={"full_name": SECRET})]))))


def test_a_related_link_is_kept_apart_from_the_near_by_links_of(monkeypatch):
    monkeypatch.setattr(walk.db, "has_relation", lambda conn, schema, name: True)
    monkeypatch.setattr(walk.db, "rows", lambda conn, sql, params=(): [dict(LINK, relation=None, total=3), dict(LINK, row_a="x:1", grade="near", total=3),
                                                                     dict(LINK, row_a="x:2", grade="mystery", total=3)])
    L = walk.links_of(None, [A])
    assert [l["other"] for l in L["related"]] == [B] and L["related"][0]["relation"] == "succeeded by"   # the evidence's copy when the column is empty
    assert [l["other"] for l in L["near"]] == ["x:1", "x:2"] and not L["confirmed"]


def test_the_rules_106_and_107_added_are_named_in_words_as_the_board_names_them():
    for rid in ("organisation-sole-company", "successor-name", "candidate-same-party", "organisation-one-live-company"):
        assert cat.RULE_WORDS[rid] and cat.rule_text(f"{rid}@1") == f"{cat.RULE_WORDS[rid]} (links rule {rid}, version 1)"
    assert cat.rule_text("same-name") == "same-name" and cat.rule_text("official-number") == "official-number"   # the walk's own rules
    src = pathlib.Path(__file__).resolve().parents[2] / "board" / "catalogue.py"
    tree = ast.parse(src.read_text())
    board = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "RULE_WORDS" for t in n.targets))
    for rid in set(board) & set(cat.RULE_WORDS):
        assert cat.RULE_WORDS[rid] == board[rid], rid
    assert set(board) <= set(cat.RULE_WORDS), sorted(set(board) - set(cat.RULE_WORDS))
