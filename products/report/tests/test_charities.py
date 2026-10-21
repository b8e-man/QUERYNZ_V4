"""The Charities Register in the report (cards the-report-shape-and-five-
templates-still-say-the-charities-register-is-not-published and
the-report-cannot-reach-the-charities-register), on fixtures: the catalogue
knows the three views and the register, and lists charities among the
registers held, not among those not held; a template that still names
`charities` as not held loads, the key is dropped from its blank and the
report says the register is published; a suppressed officer's name is
suppressed in title and statement, a name the lane withheld is the item's
note, and a return is dated 'period to'; a company's charity is joined by
business number as an entity with the company's grade, and a charity
officer that carries a person's name is listed near by name, with the
reason, on a canned database."""
import datetime as dt
import os
import tempfile

from products.report import build, catalogue as cat, memo, rows, template as tpl, walk
from products.report.tests.test_reaches import canned_walk, item, write


def test_the_catalogue_knows_the_three_charities_views_and_no_longer_says_the_register_is_not_held():
    ch, of, rt = cat.BY_NAME["charities"], cat.BY_NAME["charity_officers"], cat.BY_NAME["charity_returns"]
    assert ch.kind == "organisation" and ch.start == "registered_on" and ch.end == "deregistered_on" and "address_for_service" not in cat.columns_read(ch)
    assert of.kind == "person" and of.suppressed == "suppressed" and set(of.names) == {"full_name", "first_name", "middle_name", "last_name"}
    assert of.entity == ("charities", "charity_key") and of.role == "role" and of.row_note == "name_note" and "disqualified" in of.statement
    assert rt.kind == "figure" and rt.on == "period_end" and rt.on_label == "period to" and rt.amount == "total_gross_income" and rt.entity == ("charities", "charity_key")
    assert {c for c in ("total_gross_income", "total_expenditure", "net_surplus", "total_assets", "total_liabilities", "total_equity")} <= rows.MONEY
    assert cat.REGISTER_NAME["charities"].startswith("Charities register") and "charities" not in cat.NOT_HELD_NAME
    assert cat.SUPERSEDED_NOT_HELD == {"charities": "charities"}
    assert [c for c, *_ in walk.ROLES_ON["charities"]] == ["charity_officers", "charity_returns"]
    assert walk.NUMBER_JOINS["companies"] == (("charities", "nzbn", "nzbn"),) and walk.NAME_JOIN_TO[0][0] == "charity_officers"
    assert "charity_officers" in walk.OFFICER_VIEWS and "charity_officers" in walk.ROLE_VIEWS
    assert {r.view for r in tpl.by_name("subject").reads} >= {"charities", "charity_officers", "charity_returns"}
    for r in tpl.by_name("subject").reads:
        if r.view.startswith("charit"):
            assert "Creative Commons Attribution 3.0" in r.licence and "Charities Services" in r.attribution


def test_a_template_naming_charities_as_not_held_loads_and_the_report_says_the_register_is_published(monkeypatch):
    body = '''
name = "t"
title = "T"
version = "0.1"
owner = "test"
[[reads]]
view = "companies"
licence = "CC BY 4.0"
[[sections]]
name = "a"
heading = "A"
views = ["companies"]
not_held = ["charities", "courts"]
[[sections]]
name = "b"
heading = "B"
views = []
not_held = ["charities"]
'''
    d = tempfile.mkdtemp()
    write(d, body)
    t = tpl.load(d)
    assert t.superseded_not_held == (("charities", "charities"),)
    assert t.sections[0].not_held == ("courts",) and t.sections[1].not_held == ()
    monkeypatch.setattr(build.walk, "walk", lambda *a, **k: canned_walk())
    r = build.build(None, "companies:companies/1", t, held={"companies"})
    assert r["superseded_not_held"] == ["Charities register, officers and annual returns (named 'charities' in the template; published as pub.charities, pub.charity_officers, pub.charity_returns)"]
    assert r["sections"][0]["not_held"] == ["Court judgments"] and r["sections"][1]["blank"] == "none found"
    text = memo.text(r)
    assert "the template names as not held a register that is published and which it does not read: Charities register" in text
    assert "Charities register" not in text.split("NOT HELD (")[1].split("KNOWN LIMITS")[0]
    assert "published and which it does not read" in memo.html_body(r)
    write(d, body.replace('not_held = ["charities", "courts"]', 'not_held = ["charities", "nowhere"]'))
    import pytest
    with pytest.raises(ValueError, match="no such register"):
        tpl.load(d)


def test_an_officer_row_shows_as_the_register_states_it_and_a_return_is_dated_period_to():
    of, rt = cat.BY_NAME["charity_officers"], cat.BY_NAME["charity_returns"]
    r = {"key": "charities/officers/1", "charity_key": "charities/CC1", "kind": "person", "full_name": "Jane Doe", "first_name": "Jane", "middle_name": None,
         "last_name": "Doe", "name_note": None, "suppressed": False, "role": "Trustee", "started_on": dt.date(2020, 1, 2), "ended_on": None,
         "status": "Qualified", "disqualified": False, "document": "ab" * 32}
    it = walk.item(of, r, "ACME TRUST")
    assert it["statement"] == "Jane Doe: Trustee of ACME TRUST (Qualified; disqualified as the register states it: no)" and it["note"] == of.note
    assert it["dates"]["text"] == "from 2 January 2020; no end filed" and it["ref"] == "charities:charities/officers/1"
    it2 = walk.item(of, dict(r, suppressed=True, name_note="MiddleName withheld: holds a date", disqualified=True), "ACME TRUST")
    assert it2["title"] == rows.SUPPRESSED and it2["statement"].startswith("name suppressed: Trustee") and "disqualified as the register states it: yes" in it2["statement"]
    assert it2["suppressed"] and it2["note"] == "MiddleName withheld: holds a date"
    ret = {"key": "charities/returns/1", "charity_key": "charities/CC1", "period_end": dt.date(2025, 6, 30), "tier": "Tier3", "total_gross_income": 1234.5,
           "total_expenditure": None, "net_surplus": 10, "total_assets": 0, "total_liabilities": 0, "total_equity": 0, "audited": True, "opinion": None}
    it3 = walk.item(rt, ret, "ACME TRUST")
    assert it3["dates"]["text"] == "period to 30 June 2025" and not it3["dates"]["undated"]
    assert it3["statement"].startswith("ACME TRUST: annual return, Tier3: gross income $1,234.50, expenditure not stated, net surplus $10.00") and "audited yes" in it3["statement"]
    ch = walk.item(cat.BY_NAME["charities"], {"key": "charities/CC1", "name": "ACME TRUST", "number": "CC1", "status": "Registered",
                                              "legal_structure": "Trust", "registered_on": dt.date(2010, 1, 1), "deregistered_on": None, "address_for_service": "1 Smith Street"})
    assert ch["statement"] == "ACME TRUST: registered charity CC1, Registered; Trust" and "Smith" not in ch["statement"]


class FakeDB:
    """db.rows on a canned register: a charity for one business number, two
    officer rows for one folded name."""
    def __init__(self):
        self.sql = []

    def rows(self, conn, sql, params=()):
        self.sql.append(sql)
        if "from pub.charities where nzbn" in sql:
            return [{"key": "charities/CC9", "name": "ACME CHARITABLE TRUST", "number": "CC9", "status": "Registered", "legal_structure": "Trust",
                     "registered_on": dt.date(2010, 1, 1), "deregistered_on": None, "nzbn": "9429000000009"} for n in params[0] if n == "9429000000009"]
        if "from pub.charity_officers" in sql:
            names, firsts, limit = params
            out = []
            if "jane doe" in names:
                out.append({"key": "charities/officers/1", "charity_key": "charities/CC9", "full_name": "Jane Doe", "first_name": "Jane", "last_name": "Doe",
                            "middle_name": None, "name_note": None, "suppressed": False, "role": "Trustee", "started_on": dt.date(2021, 1, 1), "ended_on": None,
                            "status": "Qualified", "disqualified": False, "total": 2})
            if "jane doe" in firsts:
                out.append({"key": "charities/officers/2", "charity_key": "charities/CC9", "full_name": "Jane Ann Doe", "first_name": "Jane", "last_name": "Doe",
                            "middle_name": "Ann", "name_note": None, "suppressed": False, "role": "Chair", "started_on": dt.date(2019, 1, 1), "ended_on": None,
                            "status": "Qualified", "disqualified": True, "total": 2})
            return out
        if "from pub.charities where key" in sql:
            return [{"key": "charities/CC9", "name": "ACME CHARITABLE TRUST", "number": "CC9", "status": "Registered"}]
        raise AssertionError(sql)


def test_a_companys_charity_is_joined_by_business_number_and_an_officer_by_a_persons_name_is_near(monkeypatch):
    fake = FakeDB()
    monkeypatch.setattr(walk.db, "rows", fake.rows)
    company = item(ref="companies:companies/9", view="companies", kind="organisation", title="ACME LIMITED", row={"name": "ACME LIMITED", "nzbn": "9429000000009"})
    other = item(ref="companies:companies/8", view="companies", kind="organisation", title="OTHER LIMITED", row={"name": "OTHER LIMITED", "nzbn": "9429000000008"},
                 grade="near", reason="a name match")
    skipped = []
    got = walk.number_joined(None, [company, other, item()], {"companies", "charities"}, skipped)
    assert [it["ref"] for it in got] == ["charities:charities/CC9"] and got[0]["via"] == "companies:companies/9" and got[0]["grade"] == "confirmed"
    assert got[0]["rule"] == "official-number" and got[0]["kind"] == "organisation" and got[0]["hop"] == got[0]["dates"] and skipped == []
    near_company = walk.number_joined(None, [dict(other, row={"name": "OTHER LIMITED", "nzbn": "9429000000009"})], {"companies", "charities"}, skipped)
    assert near_company[0]["grade"] == "near" and near_company[0]["reason"] == "a name match"
    assert walk.number_joined(None, [company], {"companies"}, skipped) == [] and skipped == ["charities"]
    # the name join: a director named Jane Doe reaches both officer rows, near with the by-name reason; a suppressed person reaches nothing
    jane = item(ref="companies:companies/9/director/a", row={"full_name": "Jane DOE"})
    hidden = item(ref="companies:companies/9/director/b", row={"full_name": "Ann ROE"}, suppressed=True)
    joined, omitted = walk.name_joined(None, [jane, hidden, company], {"charity_officers", "charities"}, skipped)
    assert set(joined) == {jane["ref"]} and omitted == 0
    assert [it["ref"] for it in joined[jane["ref"]]] == ["charities:charities/officers/1", "charities:charities/officers/2"]
    for it in joined[jane["ref"]]:
        assert it["grade"] == "near" and it["reason"] == walk.NEAR_CHARITY_OFFICER_BY_NAME and it["rule"] == "same-name" and it["via"] == jane["ref"]
        assert "of ACME CHARITABLE TRUST" in it["statement"]
    assert walk.name_joined(None, [jane], {"companies"}, [])[0] == {}
    # the walk lists them: the charity as an entity, the officer rows in `named`, so a section naming the views carries them
    w = canned_walk()
    w["named"] = joined[jane["ref"]]
    w["entities"].append(got[0])
    monkeypatch.setattr(build.walk, "walk", lambda *a, **k: w)
    t = tpl.by_name("subject")
    r = build.build(None, "companies:companies/1", t, held={v.name for v in cat.VIEWS})
    sec = [s for s in r["sections"] if s["name"] == "charities"][0]
    assert [it["ref"] for it in sec["items"]][:1] == ["charities:charities/CC9"] and sec["confirmed"] == 1 and sec["near"] == 2
    assert r["problems"] == [] and "ACME CHARITABLE TRUST: registered charity CC9" in memo.text(r)
