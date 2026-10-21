"""The shape's additions for the step-6.2 templates (scan-templates-1), on
fixtures: the name step (by business number when both rows carry one, else
by the folded name, near, namesakes marked when asked), the optional step
(a row with nothing there listed once, "none found in", uncited), a link
step of several rules, the award views in the catalogue; the refusals; the
parameters in the order their places stand; rule 10 with planted faults."""
import os
import re
import tempfile

import pytest

from products.scan import hubs, lines as L, out, plan, rules, template as tpl, views as cat

SET = {"chains": {"value": "follow", "status": "default in force"}, "through_people": {"value": "near", "status": "default in force"}}

HEAD = '''
name = "t"
title = "T"
question = "Which suppliers are companies?"
join = "a supplier; a company by number or name"
version = "0.1"
owner = "test"
[[reads]]
view = "award_notices"
licence = "CC BY 3.0 NZ"
[[reads]]
view = "award_suppliers"
licence = "CC BY 3.0 NZ"
[[reads]]
view = "companies"
licence = "CC BY 4.0"
[[reads]]
view = "party_return_donors"
licence = "public"
[[reads]]
view = "directors"
licence = "CC BY 4.0"
'''
AWARD = '[[steps]]\nview = "award_notices"\nlabel = "award"\n[[steps]]\nview = "award_suppliers"\nlabel = "supplier"\nby = "row"\non = ["key", "notice_key"]\n'
COMPANY = '[[steps]]\nview = "companies"\nlabel = "company"\nby = "name"\non = ["business_name", "name"]\n'


def write(body: str) -> str:
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "template.toml"), "w", encoding="utf-8") as f:
        f.write(HEAD + body)
    return d


def awards(extra: str = 'number = ["nzbn", "nzbn"]\noptional = true\nnamesakes = true\n'):
    return tpl.load(write(AWARD + COMPANY + extra))


def test_the_award_views_are_in_the_catalogue_titled_without_the_notice_s_own_title():
    n, s = cat.BY_NAME["award_notices"], cat.BY_NAME["award_suppliers"]
    assert n.register == s.register == "tenders" and "title" not in n.title and n.on == s.on == "awarded_on"
    assert s.names == ("business_name",) and cat.REGISTER_NAME["tenders"]


def test_an_optional_name_step_is_one_hash_join_per_route_in_a_subquery_left_joined_by_the_row():
    t = awards()
    s = t.steps[2]
    assert s.by == "name" and s.number == ("nzbn", "nzbn") and s.optional and s.namesakes and s.fold_note == "by business number or by name"
    text, params = plan.sql(t, SET, "award_notices")
    assert params == []
    assert re.search(r"\bor\b", text.lower()) is None   # a join on an `or` walks every pair
    assert "left join (select h.key as __hk, t.*\n  from pub.award_suppliers h" in text
    assert "values ('number', nullif(h.nzbn::text, '')), ('name', regexp_replace(" in text
    assert "t on t.__by = k.by and t.__val = k.val" in text and ") s2 on s2.__hk = s1.key" in text
    assert "and not (k.by = 'name' and nullif(h.nzbn::text, '') is not null and nullif(t.nzbn::text, '') is not null)" in text
    assert "count(*) over (partition by" in text and "s2.__by as s2__by" in text and "s2.__namesakes as s2__namesakes" in text


def test_an_inner_name_step_joins_in_the_line_s_own_query_and_counts_no_namesakes_unless_asked():
    t = awards("")
    text, _ = plan.sql(t, SET, "award_notices")
    assert "cross join lateral (values ('name', regexp_replace(" in text and "k2(by, val)" in text
    assert "join (select 'name'::text as __by," in text and "s2 on s2.__by = k2.by and s2.__val = k2.val and k2.val <> ''" in text
    assert "1 as __namesakes" in text and "count(*) over" not in text and "'number'" not in text and "left join" not in text


def test_the_fold_drops_the_legal_endings_the_check_s_fold_drops():
    from products.scan import check
    assert set(re.findall(r"[a-z]{2,}", plan.LEGAL_ENDING)) == set(re.findall(r"[a-z]{2,}", check.LEGAL.pattern))


def test_parameters_stand_in_the_order_of_their_places():
    t = tpl.load(write('[[steps]]\nview = "party_return_donors"\nlabel = "donor"\nwhere = { party = "x" }\n'
                       '[[steps]]\nview = "directors"\nlabel = "director"\nby = "link"\nrule = ["full-name@1", "name-only@1"]\n'
                       '[[steps]]\nview = "companies"\nlabel = "company"\nby = "row"\non = ["entity_key", "key"]\noptional = true\nwhere = { status = "y" }\n'))
    assert t.steps[1].rules == ("full-name@1", "name-only@1") and t.steps[1].rule == "full-name@1, name-only@1"
    text, params = plan.sql(t, SET, "party_return_donors", limit=5)
    assert "l1.rule = any(%s)" in text and "left join pub.companies s2 on s2.key = s1.entity_key and s2.status = %s" in text
    assert params == [["full-name@1", "name-only@1"], "y", "x", 5]
    places = [m.start() for m in re.finditer("%s", text)]
    assert places == sorted(places) and text.index("any(%s)") < text.index("s2.status = %s") < text.index("s0.party = %s")
    # one rule keeps the one-parameter form the proving scan compiles to
    one = tpl.by_name("donors-named-as-companies")
    assert plan.sql(one, SET, "disclosures")[1] == ["organisation-name@1"]


@pytest.mark.parametrize("body, why", [
    (AWARD + '[[steps]]\nview = "companies"\nlabel = "company"\nby = "name"\n', "on = [column here, column there]"),
    (AWARD + COMPANY + 'number = ["nzbn"]\n', "number = [column here, column there]"),
    (AWARD.replace('on = ["key", "notice_key"]\n', 'on = ["key", "notice_key"]\nnamesakes = true\n') + COMPANY, "only a name step"),
    (AWARD.replace('on = ["key", "notice_key"]\n', 'on = ["key", "notice_key"]\nnumber = ["a", "b"]\n') + COMPANY, "only a name step"),
    (AWARD + COMPANY + 'optional = "yes"\n', "optional is true or false"),
    (AWARD + COMPANY + 'namesakes = 1\n', "namesakes is true or false"),
    (AWARD.replace('label = "award"\n', 'label = "award"\noptional = true\n', 1) + COMPANY, "is not optional"),
    (AWARD.replace('on = ["key", "notice_key"]\n', 'on = ["key", "notice_key"]\noptional = true\n') + COMPANY, "optional too"),
    ('[[steps]]\nview = "party_return_donors"\nlabel = "donor"\n[[steps]]\nview = "directors"\nlabel = "director"\nby = "link"\n'
     'rule = ["full-name@1", "full-name@1"]\n', "names the rule"),
    ('[[steps]]\nview = "party_return_donors"\nlabel = "donor"\n[[steps]]\nview = "directors"\nlabel = "director"\nby = "link"\n'
     'rule = ["full-name"]\n', "names the rule"),
    ('[[steps]]\nview = "party_return_donors"\nlabel = "donor"\n[[steps]]\nview = "directors"\nlabel = "director"\nby = "link"\n'
     'rule = "full-name@1"\noptional = true\n', "only a row or name step may be optional"),
    (AWARD + COMPANY.replace('on = ["business_name", "name"]', 'on = ["street_address", "name"]'), "address-shaped"),
])
def test_a_step_outside_the_contract_is_refused(body, why):
    with pytest.raises(ValueError, match=re.escape(why)):
        tpl.load(write(body))


def rec(**kw):
    r = {"s0__key": "tenders/current/1", "s0__posting_agency": "Agency", "s0__rfx_id": "1", "s0__awarded_on": None, "s0__document": "a" * 64,
         "s0__page": 1, "s0__place": "record 1",
         "s1__key": "tenders/current/1/x", "s1__business_name": "Acme Ltd", "s1__awarded_on": None, "s1__document": "b" * 64, "s1__page": 1,
         "s1__place": "record 2",
         "s2__key": "companies/9", "s2__name": "ACME LIMITED", "s2__registered_on": None, "s2__removed_on": None, "s2__first_file": "f1",
         "s2__last_file": "f2", "s2__document": None, "s2__page": None, "s2__place": None, "s2__by": "name", "s2__namesakes": 1}
    r.update(kw)
    return r


def test_a_name_join_is_near_with_its_reason_a_number_join_confirmed_and_namesakes_marked():
    t = awards()
    ln = L.line_of(t, SET, "award_notices", rec(), L.Numbering())
    assert ln["grade"] == "near" and ln["reasons"] == [f"company: {L.NEAR_BY_NAME}"] and ln["cites"] == [1, 2, 3]
    ln = L.line_of(t, SET, "award_notices", rec(s2__by="number"), L.Numbering())
    assert ln["grade"] == "confirmed" and ln["reasons"] == []
    ln = L.line_of(t, SET, "award_notices", rec(s2__namesakes=3), L.Numbering())
    assert ln["grade"] == "near" and len(ln["reasons"]) == 2 and ln["reasons"][1].startswith("company: one of 3 rows of pub.companies")
    assert "the supplier" in ln["reasons"][1] and rules.line_problems(dict(ln, n=1)) == []


def test_an_optional_step_with_nothing_there_is_listed_once_uncited_as_none_found():
    t = awards()
    blank = {k: None for k in rec() if k.startswith("s2__")}
    num = L.Numbering()
    ln = L.line_of(t, SET, "award_notices", rec(**blank), num)
    s = ln["steps"][2]
    assert s["absent"] and s["cite"] is None and s["ref"] is None and s["values"] == {} and s["dates"] == ""
    assert s["title"] == "none found in pub.companies by business number or by name"
    assert ln["cites"] == [1, 2] and len(num.citations) == 2 and ln["grade"] == "confirmed" and ln["reasons"] == []
    ln["n"] = 1
    assert rules.line_problems(ln) == []
    assert hubs.flag(None, [ln], set()) == 0   # nothing to read for a step with no row
    assert s["title"] in out.csv_row(t, ln)
    html = out.table_html(t, [ln], 1, 1, 200, "/scan/t")
    assert "none found in pub.companies" in html and "[None]" not in html


def test_mutants_rule_10_catches_each_planted_fault_on_a_step_with_nothing_there():
    t = awards()
    blank = {k: None for k in rec() if k.startswith("s2__")}
    clean = dict(L.line_of(t, SET, "award_notices", rec(**blank), L.Numbering()), n=1)
    faults = {
        "a citation": {"cite": 7},
        "a ref": {"ref": "companies:companies/9"},
        "a value": {"values": {"status": "Registered"}},
        "a title that is not none found": {"title": "ACME LIMITED"},
        "a title that claims an absence": {"title": "no company is registered"},
    }
    for what, change in faults.items():
        bad = dict(clean, steps=[*clean["steps"][:2], dict(clean["steps"][2], **change)])
        assert any("rule 10" in p for p in rules.line_problems(bad)), what


def test_a_list_of_records_is_shown_as_their_values():
    assert L.fmt([{"code": "70000000", "description": "Farming"}, {"code": "1", "description": "B"}]) == "70000000 Farming; 1 B"
    assert L.fmt(["a", "b"]) == "a; b" and L.fmt([]) == L.NOT_STATED
