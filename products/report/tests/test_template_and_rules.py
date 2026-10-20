"""The template contract and the presentation rules, on fixtures: a template
that reads a view outside the catalogue, or a section outside the template's
reads, is refused; a flag keeps its contract; the rules check finds an
undated hop without the mark, a word of cause, an owner, a suppressed name,
a bare blank, a near link with no reason."""
import os
import tempfile

import pytest

from products.report import build, contract, rules, template as tpl


def write_template(folder, body):
    with open(os.path.join(folder, "template.toml"), "w", encoding="utf-8") as f:
        f.write(body)


GOOD = '''
name = "t"
title = "T"
version = "0.1"
owner = "test"
[[reads]]
view = "directors"
licence = "CC BY 4.0"
[[sections]]
name = "a"
heading = "A"
views = ["directors"]
'''


def test_the_shapes_own_template_loads_with_rules():
    t = tpl.by_name("subject")
    assert t.name == "subject" and len(t.rules) >= 2 and t.common_rules and len(contract.COMMON_RULES) == 3
    assert t.sections and t.views <= set(tpl.cat.BY_NAME)
    for s in t.sections:
        assert set(s.views) <= t.views


def test_a_template_may_read_only_views_the_catalogue_knows_and_sections_only_what_it_reads():
    d = tempfile.mkdtemp()
    write_template(d, GOOD)
    assert tpl.load(d).views == {"directors"}
    write_template(d, GOOD.replace('view = "directors"', 'view = "home_addresses"'))
    with pytest.raises(ValueError, match="catalogue does not know"):
        tpl.load(d)
    write_template(d, GOOD.replace('views = ["directors"]', 'views = ["directors", "shareholders"]'))
    with pytest.raises(ValueError, match="does not read"):
        tpl.load(d)
    write_template(d, GOOD.replace('licence = "CC BY 4.0"\n', ''))
    with pytest.raises(ValueError, match="licence"):
        tpl.load(d)


def test_a_flag_keeps_its_contract():
    with pytest.raises(ValueError, match="cite"):
        tpl.flag("r", "0.1", "fired", "red", "x")
    with pytest.raises(ValueError, match="sources"):
        tpl.flag("r", "0.1", "clear", "red", "x")
    with pytest.raises(ValueError, match="why"):
        tpl.flag("r", "0.1", "blocked", "red", "")
    f = tpl.flag("r", "0.1", "fired", "red", "x", citations=("a:b",))
    assert f["status"] == "fired" and f["citations"] == ("a:b",)


def item(**kw):
    it = {"ref": "companies:companies/1/director/a", "view": "directors", "register": "companies", "kind": "person", "title": "Jane DOE",
          "statement": "Jane DOE: Director of ACME LIMITED", "dates": {"undated": False, "text": "from 1 January 2020"},
          "citation": {"view": "directors", "key": "companies/1/director/a"}, "cite": 1, "grade": "confirmed", "reason": None,
          "suppressed": False, "row": {"full_name": "Jane DOE"}, "flags": []}
    it.update(kw)
    return it


def report(items, blank=None, flags=()):
    return {"found": True, "subject": item(), "members": [],
            "sections": [{"name": "a", "heading": "A", "items": items, "blank": blank}], "flags": list(flags)}


def test_the_rules_hold_on_a_sound_report_and_catch_each_breach():
    assert rules.problems(report([item(ref="x:1")])) == []
    assert any("rule 1" in p for p in rules.problems(report([item(ref="x:1", dates={"undated": True, "text": "in the files from a to b"})])))
    assert any("rule 2" in p for p in rules.problems(report([item(ref="x:1", cite=None)])))
    assert any("rule 3" in p for p in rules.problems(report([item(ref="x:1", statement="Jane DOE donated because she is a director")])))
    assert any("rule 4" in p for p in rules.problems(report([item(ref="x:1", statement="Jane DOE: owner of ACME")])))
    assert any("rule 5" in p for p in rules.problems(report([], blank="no connection: this person is clean")))
    assert rules.problems(report([], blank="none found in Companies, directors and shareholders; not held: Court judgments")) == []
    assert any("rule 6" in p for p in rules.problems(report([item(ref="x:1", suppressed=True, statement="Jane DOE: Director")])))
    assert any("rule 7" in p for p in rules.problems(report([item(ref="x:1", statement="Jane DOE: 12 Smith Street, Epsom 1051")])))
    assert any("rule 8" in p for p in rules.problems(report([item(ref="x:1", grade="near")])))
    bad_flag = {"rule": "r", "status": "fired", "severity": "red", "text": "x", "citations": (), "sources_held": ()}
    assert any("rule 9" in p for p in rules.problems(report([item(ref="x:1")], flags=[bad_flag])))


def test_a_registers_own_words_are_not_the_reports_and_a_planted_fault_still_is():
    """The recruitment checkpoint's two refusals: a donor surnamed Lane with a
    year in the line, a company named PEST CONTROL; and an owners' trust held
    of record. None is the report joining facts. The faults the rules exist
    for are still caught: a street address in a statement, a street in a
    name column (a value: hard limit 15 reads values too), 'because' in the
    report's wording, a fired flag with a word of cause."""
    lane = item(ref="party_returns:x/A/10", view="party_return_donors", kind="figure", title="Gary Rodney Lane · $100,000.00",
                statement="Gary Rodney Lane · $100,000.00 to The New Zealand National Party, in the party's return for 2022 (Part A); dates as printed: 31/3/2022",
                dates={"undated": False, "text": "2022 (the year the row is filed under)"}, row={"donor": "Gary Rodney Lane", "dates": "31/3/2022"})
    pest = item(ref="companies:companies/9", view="companies", kind="organisation", title="PEST CONTROL RESEARCH NZ LIMITED",
                statement="PEST CONTROL RESEARCH NZ LIMITED: Registered LTD, NZBN 9429030206168", row={"name": "PEST CONTROL RESEARCH NZ LIMITED"})
    pest_director = item(ref="companies:companies/9/director/a", statement="Jane DOE: DIRECTOR of PEST CONTROL RESEARCH NZ LIMITED",
                         entity_title="PEST CONTROL RESEARCH NZ LIMITED")
    owners = item(ref="companies:companies/9/shareholder/b", view="shareholders", title="HOME OWNERS TRUST LIMITED",
                  statement="HOME OWNERS TRUST LIMITED: shareholder of record in ACME LIMITED, 10 shares, active",
                  row={"name": "HOME OWNERS TRUST LIMITED"}, entity_title="ACME LIMITED",
                  note="a shareholding is shown as the register states it: a holder of record, never an owner")
    candidate = item(ref="house:ge-2023/x", view="candidates", title="Ann Lane · 2023", statement="Ann Lane · 2023: stood for Labour in Epsom",
                     row={"display_name": "Ann Lane", "election": "2023"})
    assert rules.problems(report([lane, pest, pest_director, owners, candidate])) == []
    assert any("rule 7" in p for p in rules.problems(report([item(ref="x:1", statement="Jane DOE: 12 Smith Street, Epsom 1051")])))
    assert any("rule 7" in p for p in rules.problems(report([item(ref="x:1", title="12 Smith Street", statement="12 Smith Street · $50.00 to Labour, return for 2022",
                                                                   row={"donor": "12 Smith Street"})])))
    assert any("rule 7" in p for p in rules.problems(report([item(ref="x:1", statement="Jane DOE: Queen Street, Auckland 1010")])))
    assert any("rule 3" in p for p in rules.problems(report([item(ref="x:1", statement="Jane DOE: Director of ACME LIMITED because she is the owner's wife",
                                                                   entity_title="ACME LIMITED")])))
    assert any("rule 3" in p for p in rules.problems(report([item(ref="x:1", grade="near", reason="near because the names match")])))
    assert any("rule 4" in p for p in rules.problems(report([item(ref="x:1", statement="Jane DOE: owner of ACME LIMITED", entity_title="ACME LIMITED")])))
    because = {"rule": "r", "status": "fired", "severity": "red", "text": "fired because of x", "citations": ("a:b",), "sources_held": ()}
    assert any("rule 3" in p for p in rules.problems(report([item(ref="x:1")], flags=[because])))
    assert rules.address_shaped("2020 Great North Road, Avondale") and not rules.address_shaped("Terrace Investments 2000 Limited")


RULES_ON_THE_CONTRACT = '''
flag = contract.flag          # bound by the loader; no import of products.report
def mine(report):
    return flag("mine", "0.1", "clear", "info", "nothing", sources_held=("pub.directors",))
def replaced_rows(report):
    return flag("replaced-return", "9", "blocked", "info", "the template's own, replacing the common one")
RULES = (mine, replaced_rows)
'''


def test_a_template_reaches_the_contract_by_name_and_the_common_rules_run_for_it():
    d = tempfile.mkdtemp()
    write_template(d, GOOD)
    with open(os.path.join(d, "rules.py"), "w", encoding="utf-8") as f:
        f.write(RULES_ON_THE_CONTRACT)
    t = tpl.load(d)
    assert len(t.rules) == 2 and t.common_rules
    r = report([item(ref="x:1")])
    r.update({"group": {"built": True, "size": 1, "contested": False}, "hubs": [], "flags": []})
    flags = {f["rule"]: f for f in build.apply_rules(r, t)}
    assert {"group-standing", "hubs-met", "replaced-return", "mine"} == set(flags)
    assert flags["replaced-return"]["version"] == "9" and flags["replaced-return"]["status"] == "blocked"
    assert flags["group-standing"]["status"] == "clear"
    write_template(d, GOOD.replace('owner = "test"\n', 'owner = "test"\ncommon_rules = false\n'))
    assert set(f["rule"] for f in build.apply_rules(r, tpl.load(d))) == {"mine", "replaced-return"}
    assert contract.presentation_problems is rules.problems and contract.address_shaped("12 Smith Street, Epsom")


def test_a_figure_start_with_an_adopted_group_says_so():
    r = report([item(ref="x:1")])
    r["subject"] = item(ref="party_returns:h/A/1", view="party_return_donors", kind="figure")
    r.update({"group": {"built": True, "size": 3, "contested": False, "via": "companies:companies/1/director/a", "via_groups": 1}, "hubs": []})
    f = contract.group_standing(r)
    assert f["status"] == "clear" and "filed row" in f["text"] and "companies:companies/1/director/a" in f["citations"]
    r["group"]["contested"] = True
    assert contract.group_standing(r)["status"] == "fired"


def test_the_stable_address_of_a_report_on_a_row():
    assert contract.report_url("companies:companies/9429037782269") == "/report/companies:companies/9429037782269"
    assert contract.report_url("party_returns:abc/A/3", "http://10.0.0.2:8440", "08-recruitment") == "http://10.0.0.2:8440/report/party_returns:abc/A/3?template=08-recruitment"
    assert contract.report_url("x:a b", "", "subject") == "/report/x:a%20b"
