"""Template parameters (card the-report-carries-no-template-parameters): a
template declares the reader's settings its rules read, the builder puts
each under its name in report["params"] and on the report itself, read as
its kind or passed as given when it does not read, a name the template does
not declare is refused, the command line's --set and the page's query carry
them, and the memo and the form show them."""
import os
import tempfile

import pytest

from products.report import build, memo, server, template as tpl, walk
from products.report.tests.test_reaches import canned_walk

WINDOWED = '''
name = "windowed"
title = "Windowed"
version = "0.1"
owner = "test"
[[params]]
name = "window_days"
kind = "integer"
means = "days either side of a failure's Gazette date within which a going company is set beside it; none: every gap is shown"
[[params]]
name = "note"
kind = "text"
default = "none"
means = "a word the reader wants printed"
[[reads]]
view = "companies"
licence = "CC BY 4.0"
[[reads]]
view = "directors"
licence = "CC BY 4.0"
[[sections]]
name = "a"
heading = "A"
views = ["companies", "directors"]
'''

RULES = '''
flag = contract.flag
def window(report):
    w = report.get("window_days")
    p = report["params"]["window_days"]
    assert w == p
    try:
        days = int(str(w).strip()) if w not in (None, "") else None
    except ValueError:
        days = "bad"
    return flag("window", "0.1", "clear", "info", f"window {days}; note {report['note']}", sources_held=("pub.companies",))
RULES = (window,)
'''


def write(folder, body, rules=RULES):
    with open(os.path.join(folder, "template.toml"), "w", encoding="utf-8") as f:
        f.write(body)
    with open(os.path.join(folder, "rules.py"), "w", encoding="utf-8") as f:
        f.write(rules)


def test_a_template_declares_its_parameters_and_a_bad_declaration_is_refused():
    d = tempfile.mkdtemp()
    write(d, WINDOWED)
    t = tpl.load(d)
    assert t.param_names == ("window_days", "note")
    assert t.params[0].kind == "integer" and t.params[0].default is None and "Gazette" in t.params[0].means and t.params[1].default == "none"
    assert tpl.by_name("subject").params == ()
    for bad, why in ((WINDOWED.replace('name = "window_days"', 'name = "since"'), "report's own keys"),
                     (WINDOWED.replace('name = "window_days"', 'name = "Window Days"'), "lower-case"),
                     (WINDOWED.replace('kind = "integer"', 'kind = "days"'), "kind"),
                     (WINDOWED.replace('name = "note"', 'name = "window_days"'), "twice"),
                     (WINDOWED.replace('default = "none"', 'default = "x"\n').replace('kind = "text"', 'kind = "integer"'), "not a integer"),
                     (WINDOWED.replace('means = "a word the reader wants printed"\n', ""), "means")):
        write(d, bad)
        with pytest.raises(ValueError, match=why):
            tpl.load(d)


def test_the_builder_sets_each_parameter_under_its_name_and_refuses_an_undeclared_one(monkeypatch):
    d = tempfile.mkdtemp()
    write(d, WINDOWED)
    t = tpl.load(d)
    monkeypatch.setattr(build.walk, "walk", lambda *a, **k: canned_walk())
    held = {"companies", "directors"}
    r = build.build(None, "companies:companies/1", t, held=held, params={"window_days": "365"})
    assert r["window_days"] == 365 and r["params"] == {"window_days": 365, "note": "none"} and r["note"] == "none"
    assert [f for f in r["flags"] if f["rule"] == "window"][0]["text"] == "window 365; note none"
    declared = {p["name"]: p for p in r["params_declared"]}
    assert declared["window_days"]["source"] == "given" and declared["window_days"]["read"] and declared["note"]["source"] == "default"
    # not given: None, so the rule applies no cut; a value that does not read as an integer is passed as given, for the rule to say so
    r0 = build.build(None, "companies:companies/1", t, held=held)
    assert r0["window_days"] is None and r0["params"]["window_days"] is None and "window None" in [f for f in r0["flags"] if f["rule"] == "window"][0]["text"]
    rb = build.build(None, "companies:companies/1", t, held=held, params={"window_days": "a year", "note": "hello"})
    assert rb["window_days"] == "a year" and rb["note"] == "hello" and not {p["name"]: p for p in rb["params_declared"]}["window_days"]["read"]
    assert "window bad" in [f for f in rb["flags"] if f["rule"] == "window"][0]["text"]
    # an empty value is not given
    assert build.build(None, "companies:companies/1", t, held=held, params={"window_days": ""})["window_days"] is None
    with pytest.raises(KeyError, match="declares no parameter named window"):
        build.build(None, "companies:companies/1", t, held=held, params={"window": "365"})
    with pytest.raises(KeyError, match="declares no parameter"):
        build.build(None, "companies:companies/1", tpl.by_name("subject"), held=held, params={"window_days": "365"})
    # the memo prints what was set, what stands by default, and what did not read; the public report keeps them
    text = memo.text(rb)
    assert "parameters: window_days = 'a year': not read as an integer" in text and "note = hello" in text
    assert "window_days = 365 (days either side" in memo.text(r) and "note not set; the template's default none stands" in memo.text(r)
    assert "parameters:" in memo.html_body(r) and build.public(r)["params"] == {"window_days": 365, "note": "none"}
    assert "parameters:" not in memo.text(build.build(None, "companies:companies/1", tpl.by_name("subject"), held=held))


def test_the_command_line_and_the_page_carry_a_parameter(monkeypatch, capsys):
    from products.report import __main__ as main
    d = tempfile.mkdtemp()
    write(d, WINDOWED)
    t = tpl.load(d)
    monkeypatch.setattr(tpl, "by_name", lambda name: t if name == "windowed" else tpl.load(tpl.folders()[name]))
    monkeypatch.setattr(build.walk, "walk", lambda *a, **k: canned_walk())
    from products.report import db as rdb
    monkeypatch.setattr(rdb, "pub_views", lambda conn: {"companies", "directors"})
    monkeypatch.setattr(server.db, "scan_connect", lambda: __import__("contextlib").nullcontext(None))
    assert main.main(["render", "companies:companies/1", "--template", "windowed", "--set", "window_days=365", "--set", "note=hi"]) == 0
    out = capsys.readouterr().out
    assert "window_days = 365" in out and "note = hi" in out and "window 365; note hi" in out
    assert main.main(["render", "companies:companies/1", "--template", "windowed", "--set", "window=365"]) == 2
    refused = capsys.readouterr().out
    assert refused.startswith("refused:") and "declares no parameter named window" in refused
    # the page: a query parameter the template declares is read; the form offers each declared parameter with what was given
    assert server.query_params({"ref": ["x"], "template": ["windowed"], "window_days": ["90"], "since": ["2026-01-01"]}) == {"window_days": "90"}
    ctype, body = server.render("companies:companies/1", "windowed", "html", params={"window_days": "90"})
    assert 'name="window_days" value="90"' in body and "window_days = 90" in body and 'name="since"' in body
    assert [p["name"] for p in server.declared_params("windowed")] == ["window_days", "note"] and server.declared_params("subject") == []
    with pytest.raises(KeyError):
        server.render("companies:companies/1", "windowed", "text", params={"window": "90"})
