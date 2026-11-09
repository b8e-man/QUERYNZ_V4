"""Stage 2 against the real published tables (slow): a director row that is
a spoke of a name-only star, taken from the tables at run time."""
import pytest

from products.report import build, db, near, rules
from products.report import template as tpl

pytestmark = pytest.mark.slow


def _confirmed_only(report: dict) -> dict:
    """The first report as ruling 151 has it, whatever stage 1 builds today:
    confirmed items only, a section left empty saying so."""
    report["members"] = [m for m in report["members"] if m["grade"] == "confirmed"]
    for s in report["sections"]:
        s["items"] = [it for it in s["items"] if it["grade"] == "confirmed"]
        s["near"] = 0
        if not s["items"]:
            s["blank"] = s.get("blank") or "none found in the registers held"
    return report


def test_the_second_pass_on_a_real_director_is_near_only_and_leaves_the_first_report_alone():
    with db.read_connect() as conn:
        got = db.rows(conn, "select row_a, row_b from pub.links where rule = 'name-only@1' and grade = 'near' "
                            "and row_a like 'companies:companies/%%/director/%%' order by row_a limit 1")
        assert got, "no director row carries a name-only link"
        ref = got[0]["row_a"]
        r1 = _confirmed_only(build.build(conn, ref, tpl.by_name("diagnostic")))
        assert r1["found"]
        before = near.confirmed_refs(r1)
        r2 = near.stage2(conn, r1)
    sec = r2["sections"][-1]
    assert sec["name"] == near.SECTION["name"]
    assert near.confirmed_refs(r2, stage1_only=False) == before
    assert sec["items"] or r2["stage2"]["already_listed"], "the name-only link the row carries was neither listed nor counted"
    for it in sec["items"]:
        assert it["grade"] == "near" and it["reason"] and it["cite"]
    reached = {it["ref"] for it in sec["items"]} | near.listed_refs(r1)
    assert got[0]["row_b"] in reached or r2["stage2"]["omitted"]
    assert rules.problems(r2) == [] and r2["problems"] == []
