"""The dossier of ruling 110, on fixtures: an entity's name and the note that
it is no link, its names as filed with their counts, its rows by register in
date order with their roles and citations, the companies it holds a role
on in date order, its money summed by year from the filed amounts the view
lets be added (a disclosure, a replaced row and a row with no amount listed
and not added), its near links with their reasons, contested and every
decision said; a lone row's own dossier; a row in a group opens the group's;
a suppressed row is never gathered or named; a flagged column carries its flag."""
import datetime as dt
import decimal
import re

import pytest

from products.board import catalogue as cat
from products.board import dossier, panes, people, search, server

V = cat.BY_NAME
D1, D2 = "c/1/director/a", "c/2/director/b"


def ref(view, key):
    return f"{V[view].register}:{key}"


def director(key, name, company, on):
    return {"key": key, "entity_key": company, "full_name": name, "role_type": "DIRECTOR", "appointed_on": on,
            "suppressed": False, "document": None}


def donor(key, year, amount, replaced=None):
    return {"key": key, "return_key": "R1", "donor": "Jane Hart", "year": year, "amount": amount, "party": "Party A",
            "replaced_by": replaced, "document": None}


ROWS = [(ref("directors", D1), V["directors"], director(D1, "Jane Hart", "c/1", dt.date(2010, 5, 1))),
        (ref("directors", D2), V["directors"], director(D2, "Jane Mary Hart", "c/2", dt.date(2001, 2, 3))),
        (ref("party_return_donors", "p1"), V["party_return_donors"], donor("p1", 2020, decimal.Decimal("1000.00"))),
        (ref("party_return_donors", "p2"), V["party_return_donors"], donor("p2", 2020, decimal.Decimal("500.00"))),
        (ref("party_return_donors", "p3"), V["party_return_donors"], donor("p3", 2020, decimal.Decimal("700.00"), replaced="p9")),
        (ref("party_return_donors", "p4"), V["party_return_donors"], donor("p4", 2021, None)),
        (ref("disclosures", "x1"), V["disclosures"], {"key": "x1", "donor_name": "Jane Hart", "party": "Party A", "amount": decimal.Decimal("30000"),
                                                       "given_on": dt.date(2020, 5, 1), "document": None})]
NAMES = {ROWS[0][0]: "Jane Hart", ROWS[1][0]: "Jane Mary Hart"} | {r: "Jane Hart" for r, _, _ in ROWS[2:]}
COMPANY = {"c/1": {"key": "c/1", "name": "ONE LIMITED", "registered_on": dt.date(1990, 1, 1)},
           "c/2": {"key": "c/2", "name": "TWO LIMITED", "registered_on": dt.date(1995, 1, 1)}}
FAR = (V["candidates"], {"key": "c9", "display_name": "Jane Hartley", "election": 2023})
HIDDEN = (V["directors"], {"key": "c/7/director/s", "full_name": "Hidden Person", "suppressed": True})


@pytest.fixture
def reads(monkeypatch):
    ent = {"group_id": ROWS[1][0], "rows": ROWS, "links": [], "hidden": {"companies:c/4/director/s"},
           "describe": {"label": "Jane Mary Hart", "count": "7 rows, 3 registers", "contested": True, "number": ""},
           "near": [{"row_a": ROWS[0][0], "row_b": "house:c9", "mine": ROWS[0][0], "rule": "name-only@1", "reason": "the two rows share a name"},
                    {"row_a": ROWS[0][0], "row_b": "companies:c/7/director/s", "mine": ROWS[0][0], "rule": "name-only@1", "reason": "same"}],
           "near_total": 2, "related": [], "names": NAMES,
           "decisions": [{"row_a": ROWS[0][0], "row_b": "house:c9", "verdict": "not the same", "made_by": "review-agent@2", "made_at": None},
                         {"row_a": ROWS[0][0], "row_b": "companies:c/7/director/s", "verdict": "not the same", "made_by": "r", "made_at": None}]}
    monkeypatch.setattr(people, "entity", lambda conn, gid: ent if gid == ROWS[1][0] else None)
    monkeypatch.setattr(people, "resolve_refs", lambda conn, refs, members=None: {r: x for r, x in
                                                                                 {"house:c9": FAR, "companies:c/7/director/s": HIDDEN}.items() if r in refs})

    def rows(conn, sql, params=()):
        if "from pub.companies" in sql:
            return [COMPANY[k] for k in params[0] if k in COMPANY]
        if "from pub.party_return_totals" in sql:
            return [{"key": "R1", "party": "Party A", "year": 2020}]
        if "from pub.parties" in sql:
            return [{"key": "party-a", "name": "Party A"}]
        if "from pub.names" in sql:
            return [{"name_filed": "Lone Donor"}]
        return []
    monkeypatch.setattr(dossier.db, "rows", rows)
    monkeypatch.setattr(dossier.document, "statuses", lambda conn, shas: {})
    rowsof = {("directors", D1): ROWS[0][2], ("party_return_donors", "lone"): donor("lone", 2019, decimal.Decimal("250")),
              ("directors", "c/7/director/s"): HIDDEN[1]}
    monkeypatch.setattr(dossier.search, "row", lambda conn, view, key: rowsof.get((view, key)))
    monkeypatch.setattr(people, "groups_of", lambda conn, refs: {r: (ROWS[1][0], True) for r in refs if r == ROWS[0][0]})
    monkeypatch.setattr(people, "near_of", lambda conn, refs: [])
    monkeypatch.setattr(people, "decisions_of", lambda conn, refs: [])
    monkeypatch.setattr(dossier.lineage, "related_of", lambda conn, refs: [])
    return ent


def section(html, sid):
    at = html.index(f'id="{sid}"')
    nxt = html.find("<h3 id=", at + 1)
    return html[at:nxt if nxt > 0 else len(html)]


def test_parse_takes_an_entity_or_a_catalogued_row_and_nothing_else():
    assert dossier.parse("entity:companies:c/1") == "entity:companies:c/1"
    assert dossier.parse("directors:c/1/director/a") == "directors:c/1/director/a"
    for bad in ("", "entity:", "nosuchview:1", "directors:", "<script>"):
        assert dossier.parse(bad) == ""


def test_an_entity_s_dossier_has_its_name_its_names_as_filed_and_every_section(reads):
    x = dossier.gather(None, "entity:" + ROWS[1][0], "http://report")
    html = dossier.pane(x, "hart", search.FIRST)
    assert "<h2>Jane Mary Hart</h2>" in html and panes.esc(panes.ENTITY_LABEL_NOTE) in html and "contested" in html
    assert x["names"] == [("Jane Hart", 6), ("Jane Mary Hart", 1)]                     # a row counted once, most rows first
    assert re.findall(r'<h3 id="([\w-]+)"', html) == ["d-names", "d-rows", "d-roles", "d-money", "related", "d-near", "d-decided"]
    assert f'href="http://report/report/{ROWS[1][0]}"' in html                       # the group's own row, the report's path
    assert "No claims lane" in html


def test_the_rows_run_by_register_in_date_order_each_with_its_role_its_company_and_its_pane(reads):
    html = dossier.pane(dossier.gather(None, "entity:" + ROWS[1][0]), "hart", search.FIRST)
    rows = section(html, "d-rows")
    assert rows.index("Party donation and loan returns") < rows.index("Large-donation disclosures") < rows.index("Companies, directors")
    co = rows[rows.index("Companies, directors"):]
    assert co.index("2001-02-03") < co.index("TWO LIMITED") < co.index("2010-05-01") < co.index("ONE LIMITED")
    assert "director of" in co and panes.href("hart", [f"directors:{D2}"], search.FIRST).replace("&", "&amp;") in co
    assert '<span class="when">2020</span>' in rows                                   # a year filed alone is a year, not 1 January
    roles = section(html, "d-roles")
    assert roles.index("TWO LIMITED") < roles.index("ONE LIMITED") and roles.count("<li>") == 2


def test_money_sums_by_year_only_the_filed_amounts_the_view_lets_be_added(reads):
    x = dossier.gather(None, "entity:" + ROWS[1][0])
    years = {y: (total, n, len(items)) for y, items, total, n in dossier.by_year(dossier.addends(x))}
    assert years == {2020: (decimal.Decimal("1500.00"), 2, 4), 2021: (decimal.Decimal(0), 0, 1)}   # p3 replaced, x1 a disclosure, p4 no amount
    money = section(dossier.pane(x), "d-money")
    assert "$1,500.00, the sum of 2 filed amounts" in money and "none added" in money
    assert "replaced by an amendment, not added" in money and "a disclosure: its gift is also in the year" in money
    assert "no amount filed, not added" in money and "$31" not in money and "$2,200" not in money


def test_near_links_carry_their_reasons_and_a_suppressed_far_row_is_never_named(reads):
    html = dossier.pane(dossier.gather(None, "entity:" + ROWS[1][0]), "hart", search.FIRST)
    near = section(html, "d-near")
    assert "Jane Hartley" in near and "because the two rows share a name" in near
    decided = section(html, "d-decided")
    assert "not the same" in decided and "1 decision on a pair" in decided and "contested" in decided
    assert "Hidden Person" not in html


def test_a_row_in_a_group_opens_its_group_and_a_lone_row_its_own(reads):
    x = dossier.gather(None, f"directors:{D1}")
    assert x["kind"] == "entity" and x["via"] == "Jane Hart" and len(x["rows"]) == len(ROWS)
    lone = dossier.gather(None, "party_return_donors:lone", "http://report")
    html = dossier.pane(lone)
    assert lone["kind"] == "row" and "a lone row: in no group" in html and "<h2>Lone Donor</h2>" in html
    assert "$250.00, the sum of 1 filed amount" in html and "http://report/report/party_returns:lone" in html


def test_a_chosen_suppressed_row_is_never_gathered_or_named(reads):
    x = dossier.gather(None, "directors:c/7/director/s")
    html = dossier.pane(x)
    assert x["kind"] == "suppressed" and "rows" not in x and "Hidden" not in html and "hard limit 16" in html


def test_a_flagged_column_carries_its_flag_and_its_text_whole():
    v = V["minister_diary_entries"]
    r = {"key": "e1", "location": "12 Some Street, Town", "location_names_home": True, "meeting": "x" * 900}
    text = dossier.fields_text(v, r)
    assert "names a home" in text and "x" * 900 in text


def test_the_page_carries_the_dossier_under_the_graph_and_the_results_a_plain_link_to_it(reads):
    hits = [(V["directors"], ROWS[0][2])]
    html = panes.results_pane("hart", {"companies": [(V["directors"], 1, [ROWS[0][2]])], "tabs": None}, {"directors"},
                              ("companies",), search.FIRST)
    assert f'data-dossier="directors:{D1}"' in html and 'class="dos"' in html
    assert "d=directors%3A" + D1.replace("/", "%2F") in html
    assert 'id="dossier"' in dossier.placeholder("hart", search.FIRST) and "hidden" in dossier.placeholder()
    assert dossier.base("hart", search.FIRST).startswith("/dossier?q=hart")
