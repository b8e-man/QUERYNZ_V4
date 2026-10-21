"""The third tranche's pure parts, on fixtures: the catalogue knows the two
views and the not-held keys; a company's own name is not an address (rule
7) while a person's street-shaped name still is; a filed row with no group
is not called an organisation; a per-category expense line is never listed
however it is reached; a Crown body is a hub by its register name; a
template asks for the reaches by bucket and depth, and a section's own,
status and changed filters are parsed; the builder applies them and marks
what is new since a date, on a canned walk."""
import datetime as dt
import os
import tempfile

import pytest

from products.report import build, catalogue as cat, contract, rules, template as tpl, walk


def test_the_catalogue_knows_possessions_states_and_the_not_held_keys():
    p = cat.BY_NAME["gazette_possessions"]
    assert p.register == "gazette" and p.on == "entered_on" and p.published == "published_on" and set(p.names) == {"mortgagee", "mortgagor"}
    assert p.entity == ("companies", "mortgagor_register_key")
    assert {c for c, *_ in walk.POINTING_AT["companies"] if c == "gazette_possessions"} and \
        {col for v, col, *_ in walk.POINTING_AT["companies"] if v == "gazette_possessions"} == {"mortgagee_register_key", "mortgagor_register_key"}
    st = cat.BY_NAME["company_states"]
    assert st.register == "companies" and st.as_in == "file" and st.entity == ("companies", "entity_key") and "file" in cat.columns_read(st)
    assert ("company_states", "entity_key", "file") in walk.ROLES_ON["companies"]
    liq = cat.BY_NAME["gazette_liquidators"]
    assert liq.entity == ("gazette_liquidations", "notice") and liq.entity_col == "notice"
    assert walk.ROLES_ON["gazette_liquidations"][0][:2] == ("gazette_liquidators", "notice")
    for key in ("overseas", "trusts", "employment", "company_history", "worksafe", "regulators", "disputes", "fire", "unincorporated", "mpi",
                "credit_bureau", "nzbn_interface", "disciplinary", "tribunals", "limited_partnerships"):
        assert key in cat.NOT_HELD_NAME, key
    assert "partners" in cat.NOT_HELD_NAME["limited_partnerships"]
    assert not {r for r, _ in cat.REGISTERS} & set(cat.NOT_HELD_NAME)


def test_a_state_is_dated_by_its_file_and_a_practitioner_joins_its_notice_by_number():
    from products.report import rows
    d = rows.dates(cat.BY_NAME["company_states"], {"file": "companies-2026-07", "registered_on": None, "removed_on": None})
    assert not d["undated"] and "as in the file companies-2026-07" in d["text"]
    assert "entered" in rows.dates(cat.BY_NAME["gazette_possessions"], {"entered_on": dt.date(2026, 9, 15), "published_on": dt.date(2026, 9, 18)})["text"]


def item(**kw):
    it = {"ref": "companies:companies/1/director/a", "view": "directors", "register": "companies", "kind": "person", "title": "Jane DOE",
          "statement": "Jane DOE: Director of ACME LIMITED", "dates": {"undated": False, "text": "from 1 January 2020"},
          "citation": {"view": "directors", "key": "companies/1/director/a"}, "cite": 1, "grade": "confirmed", "reason": None,
          "suppressed": False, "row": {"full_name": "Jane DOE"}, "flags": [], "entity_title": "ACME LIMITED"}
    it.update(kw)
    return it


def report(items, flags=()):
    return {"found": True, "subject": item(), "members": [], "sections": [{"name": "a", "heading": "A", "items": items, "blank": None}], "flags": list(flags)}


def test_a_company_named_like_a_street_address_is_the_registers_own_name_and_a_persons_is_not():
    """The construction checkpoint's refusal: 1 SHEA TERRACE LIMITED on a
    director's walk. A company's name, as the register names it, is shown
    (hard limit 15 shows a company's registered address); a person named
    with a street, or an address in a statement, is still refused."""
    company = item(ref="companies:companies/9", view="companies", kind="organisation", title="1 SHEA TERRACE LIMITED",
                   statement="1 SHEA TERRACE LIMITED: Registered LTD, NZBN 9429047097209", row={"name": "1 SHEA TERRACE LIMITED"}, entity_title=None)
    director = item(ref="companies:companies/9/director/a", statement="Jane DOE: Director of 1 SHEA TERRACE LIMITED", entity_title="1 SHEA TERRACE LIMITED")
    holder = item(ref="companies:companies/2/shareholder/b", view="shareholders", title="1 SHEA TERRACE LIMITED",
                  statement="1 SHEA TERRACE LIMITED: shareholder of record in ACME LIMITED, 10 shares, active",
                  row={"name": "1 SHEA TERRACE LIMITED", "shareholder_type": "company"})
    assert rules.problems(report([company, director, holder])) == []
    assert any("rule 7" in p for p in rules.problems(report([item(ref="x:1", title="12 Smith Street", statement="12 Smith Street · $50.00 to Labour",
                                                                   row={"donor": "12 Smith Street"}, view="party_return_donors", entity_title=None)])))
    assert any("rule 7" in p for p in rules.problems(report([item(ref="x:1", statement="Jane DOE: Director of ACME LIMITED, 12 Smith Street, Epsom 1051")])))
    assert any("rule 7" in p for p in rules.problems(report([item(ref="x:1", statement="Jane DOE of 12 Smith Street: Director of 1 SHEA TERRACE LIMITED",
                                                                   entity_title="1 SHEA TERRACE LIMITED")])))
    assert set(rules.company_names(holder)) == {"1 SHEA TERRACE LIMITED", "ACME LIMITED"} and rules.company_names(item(row={"full_name": "12 Smith Street"}, entity_title=None)) == []


def test_a_filed_row_with_no_group_is_not_called_an_organisation():
    r = report([item(ref="x:1")])
    r["subject"] = item(ref="party_returns:h/A/1", view="party_return_donors", kind="figure")
    r.update({"group": {"built": True, "size": 1, "contested": False, "via": None, "why": walk.NO_GROUP_FOR_FILED.format(view="party_return_donors")}, "hubs": []})
    f = contract.group_standing(r)
    assert f["status"] == "clear" and "filed row" in f["text"] and "no group" in f["text"] and "organisation" not in f["text"]


def test_a_per_category_expense_line_is_never_listed_and_a_crown_body_is_a_hub():
    v = cat.BY_NAME["mp_expenses"]
    assert not walk.listable(v, {"role": "category"}) and walk.listable(v, {"role": "total"}) and walk.listable(v, {"role": "outside"})
    assert walk.listable(cat.BY_NAME["directors"], {"role_type": "Director"})
    assert walk.crown_body("HEALTH NEW ZEALAND") and walk.crown_body("Transpower New Zealand Limited") and walk.crown_body("Kāinga Ora–Homes and Communities")
    assert not walk.crown_body("RANK GROUP LIMITED") and not walk.crown_body("")
    assert walk.name_hub("HEALTH NEW ZEALAND")["kind"] == "crown" and walk.company_holder({"shareholder_type": "company"}) and not walk.company_holder({"shareholder_type": "individual"})
    assert walk.SETTINGS["hub_holdings"] == 50 and walk.LIMITS["chain"] == tpl.CHAIN_MAX and tuple(walk.BUCKETS) == tpl.BUCKETS


GOOD = '''
name = "t"
title = "T"
version = "0.1"
owner = "test"
chain_depth = 3
[[reads]]
view = "companies"
licence = "CC BY 4.0"
[[reads]]
view = "directors"
licence = "CC BY 4.0"
[[sections]]
name = "changed"
heading = "Changed"
views = ["directors"]
changed = true
[[sections]]
name = "own"
heading = "Own"
views = ["companies", "directors"]
sources = ["members", "roles", "officers", "office", "chain"]
own = true
statuses = ["In Liquidation", "removed"]
[[sections]]
name = "rest"
heading = "Rest"
views = ["companies", "directors"]
sources = ["members", "roles", "officers", "office", "chain"]
'''


def write(folder, body):
    with open(os.path.join(folder, "template.toml"), "w", encoding="utf-8") as f:
        f.write(body)


def test_a_template_asks_for_the_reaches_and_a_sections_filters_are_parsed_and_checked():
    d = tempfile.mkdtemp()
    write(d, GOOD)
    t = tpl.load(d)
    assert t.chain_depth == 3 and t.buckets >= {"officers", "office", "chain", "members", "roles"}
    changed, own, rest = t.sections
    assert own.own is True and own.statuses == ("in liquidation", "removed") and not own.changed
    assert changed.changed and changed.own is None and rest.own is None and "chain" in rest.sources
    write(d, GOOD.replace('"chain"]', '"chains"]'))
    with pytest.raises(ValueError, match="bucket"):
        tpl.load(d)
    write(d, GOOD.replace("chain_depth = 3", "chain_depth = 9"))
    with pytest.raises(ValueError, match="chain_depth"):
        tpl.load(d)
    write(d, GOOD.replace("own = true", 'own = "yes"'))
    with pytest.raises(ValueError, match="own"):
        tpl.load(d)
    write(d, GOOD.replace("chain_depth = 3\n", ""))
    assert tpl.load(d).chain_depth == 0 and tpl.by_name("subject").chain_depth == 2


def canned_walk():
    start = item(ref="companies:companies/1", view="companies", kind="organisation", title="ACME LIMITED", statement="ACME LIMITED: In Liquidation LTD",
                 row={"name": "ACME LIMITED", "status": "In Liquidation", "first_file": "companies-2026-07", "last_file": "companies-2026-08", "in_latest": True},
                 entity_title=None, dates={"undated": False, "text": "from 1 January 2020", "start": dt.date(2020, 1, 1)})
    d_old = item(ref="companies:companies/1/director/a", via="companies:companies/1", row={"full_name": "Jane DOE", "first_file": "companies-2026-07", "last_file": "companies-2026-08", "in_latest": True},
                 dates={"undated": False, "text": "from 1 January 2020", "start": dt.date(2020, 1, 1)})
    d_new = item(ref="companies:companies/1/director/b", via="companies:companies/1", row={"full_name": "Ann ROE", "first_file": "companies-2026-08", "last_file": "companies-2026-08", "in_latest": True},
                 dates={"undated": False, "text": "from 1 August 2026", "start": dt.date(2026, 8, 1)})
    d_gone = item(ref="companies:companies/1/director/c", via="companies:companies/1", row={"full_name": "Bob POE", "first_file": "companies-2026-07", "last_file": "companies-2026-07", "in_latest": False},
                  dates={"undated": True, "text": "undated; in the files from companies-2026-07 to companies-2026-07"})
    other = item(ref="companies:companies/2", view="companies", kind="organisation", title="OTHER LIMITED", statement="OTHER LIMITED: Registered LTD",
                 row={"name": "OTHER LIMITED", "status": "Registered"}, entity_title=None, grade="near", reason=walk.NEAR_THROUGH_OFFICER.format(who="Jane DOE"),
                 via="companies:companies/1/director/a", through="companies:companies/1/director/a", depth=1,
                 dates={"undated": False, "text": "from 2 February 2021", "start": dt.date(2021, 2, 2)})
    failed = item(ref="companies:companies/3", view="companies", kind="organisation", title="GONE LIMITED", statement="GONE LIMITED: Removed LTD",
                  row={"name": "GONE LIMITED", "status": "Removed"}, entity_title=None, grade="near", reason=walk.NEAR_SHARED_OFFICE,
                  via="companies:companies/1/registered-office/x", through="companies:companies/1", dates={"undated": False, "text": "from 3 March 2019", "start": dt.date(2019, 3, 3)})
    return {"found": True, "start": start, "settings": dict(walk.SETTINGS), "limits": dict(walk.LIMITS), "skipped": [], "group": {"built": True, "size": 1, "contested": False, "why": "an organisation"},
            "members": [start], "confirmed": [], "near": [], "entities": [start], "roles": [d_old, d_new, d_gone], "pointing": [], "second": [], "named": [],
            "officers": [other], "office": [failed], "chain": [], "hubs": [], "links_built": True, "links_omitted": 0}


def test_the_builder_applies_own_status_and_changed_filters_and_marks_what_is_new_since_a_date(monkeypatch):
    d = tempfile.mkdtemp()
    write(d, GOOD)
    t = tpl.load(d)
    seen = {}
    monkeypatch.setattr(build.walk, "walk", lambda conn, ref, allowed, depth=2, buckets=None, chain_depth=0: seen.update(buckets=buckets, chain_depth=chain_depth) or canned_walk())
    monkeypatch.setattr(build, "files_held", lambda conn: ("companies-2026-07", "companies-2026-08"))
    r = build.build(None, "companies:companies/1", t, held={"companies", "directors"}, since="2026-06-01")
    assert seen["buckets"] == t.buckets and seen["chain_depth"] == 3 and r["since"] == "2026-06-01"
    changed, own, rest = r["sections"]
    # changed, first: only the rows that arrived after the first file held or left before the latest, newest change first
    assert [it["ref"] for it in changed["items"]] == ["companies:companies/1/director/b", "companies:companies/1/director/c"]
    assert [it["changed_in"] for it in changed["items"]] == ["companies-2026-08", "companies-2026-07"]
    # own: the rows on the start the first section left (the subject itself is the header, never a section's row); a company
    # reached through an officer or the office is not the start's own, whatever its status
    assert [it["ref"] for it in own["items"]] == ["companies:companies/1/director/a"]
    # rest: what the first two left (the officer's and the office's companies, near), the start's own rows never twice
    assert {it["ref"] for it in rest["items"]} == {"companies:companies/2", "companies:companies/3"}
    # a status filter on a section drawing the office's companies keeps only the failed one
    write(d, GOOD.replace('name = "rest"', 'name = "rest"\nstatuses = ["removed"]'))
    r3 = build.build(None, "companies:companies/1", tpl.load(d), held={"companies", "directors"})
    assert {it["ref"] for it in r3["sections"][2]["items"]} == {"companies:companies/3"}
    # new since 1 June 2026: the director appointed in August; the undated one cannot say
    by_ref = {it["ref"]: it for s in r["sections"] for it in s["items"]}
    assert by_ref["companies:companies/1/director/b"]["new"] is True and by_ref["companies:companies/1/director/a"]["new"] is False
    assert by_ref["companies:companies/1/director/c"]["new"] is None and r["new"] == 1 and r["cannot_say"] == 1
    assert r["problems"] == [] and r["walk"]["chain_depth"] == 3
    r2 = build.build(None, "companies:companies/1", t, held={"companies", "directors"})
    assert r2["since"] is None and all(it["new"] is None for s in r2["sections"] for it in s["items"])


def test_the_memo_prints_the_since_line_and_marks_new_rows(monkeypatch):
    from products.report import memo
    d = tempfile.mkdtemp()
    write(d, GOOD)
    t = tpl.load(d)
    monkeypatch.setattr(build.walk, "walk", lambda *a, **k: canned_walk())
    monkeypatch.setattr(build, "files_held", lambda conn: ("companies-2026-07", "companies-2026-08"))
    r = build.build(None, "companies:companies/1", t, held={"companies", "directors"}, since="2026-06-01")
    text = memo.text(r)
    assert "since 2026-06-01: 1 row(s)" in text and "  - NEW [confirmed] " in text and "change first shown in the file companies-2026-08" in text
    assert "one step through companies:companies/1/director/a" in text
    html = memo.html_body(r)
    assert "since 2026-06-01" in html and ">new</span>" in html
