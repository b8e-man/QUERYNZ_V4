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


def test_a_citation_names_the_row_it_read_and_a_planted_document_is_caught():
    """A settlement the iwi directory names on several bodies' pages (a collective,
    one row per body, each row under its own key) is cited row by row, and the check reads back the
    document, page and place as well as the key."""
    with pub() as c:
        shared = db.rows(c, "select settlement_key from pub.iwi_directory_settlements group by settlement_key having count(*) > 1 "
                            "order by settlement_key limit 1")   # since fix-registers-iwi-directory-1 (second sitting) a row's key is its own
        if not shared:
            pytest.skip("no settlement is named by more than one body today")
        rows = db.rows(c, "select key, document, page, place from pub.iwi_directory_settlements where settlement_key = %s order by entity_key",
                       (shared[0]["settlement_key"],))
        cites = [{"view": "iwi_directory_settlements", "key": r["key"], "document": r["document"], "page": r["page"], "place": r["place"]}
                 for r in rows]
        assert check.citations_resolve(c, cites) == []
        wrong = [dict(cites[0], document=cites[0]["document"][::-1])]
        assert any("cited document" in p for p in check.citations_resolve(c, wrong))


@pytest.mark.parametrize("name", check.TEMPLATES_CHAINED)
def test_the_settlement_map_read_back_holds_and_catches_each_planted_fault(name):
    lines = latest_lines(name)
    if not lines:
        R.run(tpl.by_name(name), note="test", log=lambda s: None)
        lines = latest_lines(name)
    t = tpl.by_name(name)
    with pub() as c:
        assert check.chain_readback(c, t, lines) == []
        caught = lambda bad: check.chain_readback(c, t, [bad] + [ln for ln in lines if ln["steps"][0]["ref"] != bad["steps"][0]["ref"]])
        dropped = [ln for ln in lines if ln["steps"][0]["ref"] != lines[0]["steps"][0]["ref"]]
        assert any("rows listed" in p for p in check.chain_readback(c, t, dropped))
        found = next(ln for ln in lines if not ln["steps"][1].get("absent"))
        other = next(ln for ln in lines if not ln["steps"][1].get("absent") and ln["steps"][0]["ref"] != found["steps"][0]["ref"]
                     and ln["steps"][1]["ref"] != found["steps"][1]["ref"])
        swapped = copy.deepcopy(found)
        swapped["steps"][1]["ref"] = other["steps"][1]["ref"]
        assert any(("differ" in p or "equal to" in p or "do not fold alike" in p) for p in caught(swapped)), name
        regraded = copy.deepcopy(found)
        regraded["grade"] = "contested"
        assert any("graded contested" in p for p in caught(regraded))
        absent = next((ln for ln in lines if ln["steps"][1].get("absent")), None)
        if absent:
            blanked = copy.deepcopy(found)
            for s in blanked["steps"][1:]:
                s.update(absent=True, ref=None, cite=None, values={}, title="none found in pub." + s["view"])
            blanked["reasons"] = []
            blanked["grade"] = "confirmed"
            assert any("shown as none found" in p for p in caught(blanked)), name


def test_a_near_link_between_two_group_ids_is_found_from_two_other_rows_and_the_row_lookup_would_miss_it(monkeypatch):
    """The links lane stores name-only@1 as a star between groups and moves
    its centre when it rebuilds (links/spec.md, "contract for readers"). A
    live link between two group ids is read from a director row of each
    group that is neither end: the check finds it, the walk reaches the
    other group's row by it with the link's own reason, and the lookup by
    the two rows themselves (the mutation) finds nothing."""
    with pub() as c:
        got = db.rows(c, """select l.reason, x.key as x, y.ref as y from pub.links l
                              join pub.groups ga on ga.row_key = l.row_a and ga.group_id = l.row_a
                              join pub.groups gb on gb.row_key = l.row_b and gb.group_id = l.row_b
                              cross join lateral (select n.key from pub.groups m join pub.names n on n.ref = m.row_key and n.view = 'directors'
                                                  where m.group_id = l.row_a and m.row_key <> l.row_a limit 1) x
                              cross join lateral (select m.row_key as ref from pub.groups m join pub.names n on n.ref = m.row_key and n.view = 'directors'
                                                  where m.group_id = l.row_b and m.row_key <> l.row_b limit 1) y
                             where l.rule = 'name-only@1' limit 1""")
        if not got:
            pytest.skip("no name-only link joins two groups with a director row beside each end today")
        f = got[0]
        x = db.rows(c, "select ref from pub.names where view = 'directors' and key = %s", (f["x"],))[0]["ref"]
        assert check.link_between(c, ["name-only@1"], x, f["y"])[0]["grade"] == "near"
        assert check.link_between(c, ["name-only@1"], f["y"], x)[0]["reason"] == f["reason"]
        import os
        import tempfile
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "template.toml"), "w", encoding="utf-8") as fh:
            fh.write('name = "t"\ntitle = "T"\nquestion = "Which?"\njoin = "j"\nversion = "0"\nowner = "test"\n'
                     '[[reads]]\nview = "directors"\nlicence = "CC BY 4.0"\n'
                     '[[steps]]\nview = "directors"\nlabel = "director"\nwhere = { key = ["' + f["x"] + '"] }\n'
                     '[[steps]]\nview = "directors"\nlabel = "namesake"\nby = "link"\nrule = "name-only@1"\n')
        t = tpl.load(d)
        have = {"directors": db.pub_columns(c, "directors")}

        def reached() -> dict:
            text, params = plan.sql(t, SET, "directors", None, have)
            return {"companies:" + r["s1__key"]: r for r in db.rows(c, text, params)}

        walk = reached()
        assert f["y"] in walk and walk[f["y"]]["s1__grade"] == "near" and walk[f["y"]]["s1__reason"] == f["reason"]
        monkeypatch.setattr(plan, "MEMBERS", "(select {ref} as k)")    # the mutation: back to the two rows themselves
        monkeypatch.setattr(plan, "GROUP_ROWS", "select {ref} as k, true as own")
        assert check.link_between(c, ["name-only@1"], x, f["y"]) == []
        assert f["y"] not in reached()
