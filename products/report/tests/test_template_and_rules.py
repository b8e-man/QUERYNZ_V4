"""The template contract and the presentation rules, on fixtures: a template
that reads a view outside the catalogue, or a section outside the template's
reads, is refused; a flag keeps its contract; the rules check finds an
undated hop without the mark, a word of cause, an owner, a suppressed name,
a bare blank, a near link with no reason."""
import os
import tempfile

import pytest

from products.report import rules, template as tpl


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
    assert t.name == "subject" and len(t.rules) >= 5 and t.sections and t.views <= set(tpl.cat.BY_NAME)
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
