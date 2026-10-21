"""The shape's step-6.2 additions against the real published tables (slow):
the SQL fold is the check's fold on real names; a name step with a number
joins by the number alone where both rows carry one; and the templates'
read-back in the check catches each planted fault on real lines."""
import copy
import re

import pytest

from products.scan import check, db, plan, run as R, settings as cfg, state, template as tpl

pytestmark = pytest.mark.slow
SET = cfg.in_force()


def pub():
    c = db.pub_connect()
    c.autocommit = True
    return c


def test_the_sql_fold_is_the_check_s_fold_on_real_names():
    with pub() as c:
        names = [r[0] for r in c.execute("(select business_name from pub.award_suppliers where business_name is not null order by key limit 400) "
                                         "union all (select distinct posting_agency from pub.award_notices where posting_agency ~ '[āēīōūĀĒĪŌŪ]')")]
        folded = [r[0] for r in c.execute(f"select {plan.fold_sql('x')} from unnest(%s::text[]) with ordinality as u(x, i) order by i", (names,))]
    assert len(folded) == len(names) > 400 and any("ō" in n.lower() for n in names)
    assert [check.loose(n) for n in names] == folded


def test_a_name_step_with_a_number_joins_by_the_number_alone_where_both_rows_carry_one():
    """Directors to companies by full name, with the company's number on
    both sides: every director row meets its own company by the number,
    and never a company that merely carries the name."""
    import os
    import tempfile
    d = tempfile.mkdtemp()
    with pub() as c:
        keys = [r[0] for r in c.execute("select key from pub.directors where nzbn is not null and nzbn <> '' order by key limit 40")]
    with open(os.path.join(d, "template.toml"), "w", encoding="utf-8") as f:
        f.write('name = "t"\ntitle = "T"\nquestion = "Which?"\njoin = "j"\nversion = "0"\nowner = "test"\n'
                '[[reads]]\nview = "directors"\nlicence = "CC BY 4.0"\n[[reads]]\nview = "companies"\nlicence = "CC BY 4.0"\n'
                '[[steps]]\nview = "directors"\nlabel = "director"\ncolumns = ["entity_key"]\nwhere = { key = ' + str(keys).replace("'", '"') + ' }\n'
                '[[steps]]\nview = "companies"\nlabel = "company"\nby = "name"\non = ["full_name", "name"]\nnumber = ["nzbn", "nzbn"]\nnamesakes = true\n')
    t = tpl.load(d)
    with pub() as c:
        have = {v: db.pub_columns(c, v) for v in ("directors", "companies")}
        text, params = plan.sql(t, SET, "directors", None, have)
        rows = db.rows(c, text, params)
    assert len(rows) == len(keys)
    assert all(r["s1__by"] == "number" and r["s1__key"] == r["s0__entity_key"] and r["s1__namesakes"] == 1 for r in rows)


def latest_lines(name: str) -> list:
    with db.state_read_connect() as st:
        r = state.latest(st, name)
        return list(state.all_lines(st, r["run_id"])) if r else []


@pytest.fixture(scope="module")
def award_lines():
    if not latest_lines("tender-awards"):
        R.run(tpl.by_name("tender-awards"), note="test", log=lambda s: None)
    return latest_lines("tender-awards")


def test_the_award_read_back_holds_and_catches_each_planted_fault(award_lines):
    lines = award_lines
    with pub() as c:
        assert check.templates_proving(c, "tender-awards", lines) == []
        by_name = next(ln for ln in lines if not ln["steps"][2].get("absent") and len(ln["reasons"]) == 1)
        other = next(ln for ln in lines if ln["steps"][0]["ref"] != by_name["steps"][0]["ref"] and not ln["steps"][2].get("absent")
                     and ln["steps"][2]["title"] != by_name["steps"][2]["title"])
        namesake = next(ln for ln in lines if len(ln["reasons"]) == 2)
        absent = next(ln for ln in lines if ln["steps"][2].get("absent"))

        def caught(bad: dict) -> list:
            return check.templates_proving(c, "tender-awards", [bad])

        swap_supplier = copy.deepcopy(by_name)
        swap_supplier["steps"][1]["ref"] = other["steps"][1]["ref"]
        assert any("not named on the award" in p for p in caught(swap_supplier))
        swap_company = copy.deepcopy(by_name)
        swap_company["steps"][2]["ref"] = other["steps"][2]["ref"]
        assert any("do not fold alike" in p for p in caught(swap_company))
        miscount = copy.deepcopy(namesake)
        miscount["reasons"][1] = re.sub(r"one of [\d,]+ ", "one of 999 ", miscount["reasons"][1], count=1)
        assert any("namesakes" in p for p in caught(miscount))
        graded = copy.deepcopy(absent)
        graded["grade"] = "near"
        assert any("no company joined" in p for p in caught(graded))
        confirmed = copy.deepcopy(by_name)
        confirmed["grade"], confirmed["reasons"] = "confirmed", []
        assert any("business number" in p for p in caught(confirmed))
        dropped = [ln for ln in lines if ln["steps"][1]["ref"] != by_name["steps"][1]["ref"]]
        assert any("suppliers listed" in p for p in check.templates_proving(c, "tender-awards", dropped))


def test_the_procurement_read_back_holds_and_catches_a_planted_person():
    for name in ("procurement-directors-donors", "procurement-shareholders-donors"):
        lines = latest_lines(name) or [None]
        if lines == [None]:
            R.run(tpl.by_name(name), note="test", log=lambda s: None)
            lines = latest_lines(name)
        with pub() as c:
            assert check.templates_proving(c, name, lines) == []
            if not lines:
                continue
            bad = copy.deepcopy(lines[0])
            other = next((ln for ln in lines if ln["steps"][1]["ref"] != bad["steps"][1]["ref"]), None)
            bad["steps"][1]["ref"] = other["steps"][1]["ref"] if other else bad["steps"][1]["ref"] + "-not-a-row"
            got = check.templates_proving(c, name, [bad])
            assert any("link joins" in p or "not on the company" in p for p in got)
