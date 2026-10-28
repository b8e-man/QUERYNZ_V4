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
    assert re.findall(r'<h3 id="([\w-]+)"', html) == ["d-names", "d-rows", "d-money", "related", "d-near", "d-decided"]
    assert f'href="http://report/report/{ROWS[1][0]}"' in html                       # the group's own row, the report's path
    assert "No claims lane" in html


def test_the_rows_fold_into_facts_in_date_order_each_row_as_filed_under_its_fact(reads):
    """Ruling 117: one entry per thing the rows say, in date order, the row as filed closed under it."""
    html = dossier.pane(dossier.gather(None, "entity:" + ROWS[1][0]), "hart", search.FIRST)
    rows = section(html, "d-rows")
    says = re.findall(r'<div class="say">(.*?)</div>', rows)
    text = [re.sub(r"<[^>]+>", "", s) for s in says]
    assert text == ["Director of TWO LIMITED since 3 February 2001", "Director of ONE LIMITED since 1 May 2010",
                    "Donor to Party A, 2020 to 2021"]                                       # a return's rows and a disclosure say one thing
    assert rows.count('<li class="fact"') == 3 and rows.count('<li><span class="when">') == len(ROWS)   # every row once, as filed
    assert panes.href("hart", [f"directors:{D2}"], search.FIRST).replace("&", "&amp;") in rows
    assert '<span class="when">2020</span>' in rows                                   # a year filed alone is a year, not 1 January
    donor = rows[rows.index("Donor to Party A"):]
    assert "four donations in party returns" in donor and "large-donation disclosure" in donor


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


# ── many rows (ruling 116's ministers): counted in SQL, shown by view ───────

MANY_GID = "hansard:t/0"
MANY = [("hansard_speeches", 1800, "Brown, Hon Simeon", "sitting_on"),
        ("parliament_written_questions", 1000, "Hon Simeon Brown", "question_released_on"),
        ("beehive_release_ministers", 200, "Simeon Brown", "published_on")]


def many_rows():
    """3,000 rows over three views, a day apart, and one suppressed director (hard limit 16)."""
    out = {}
    for view, n, name, col in MANY:
        out[view] = [{"key": f"{view[0]}/{i}", col: dt.date(2000, 1, 1) + dt.timedelta(days=i), "member_name": name,
                      "name": name, "title": f"question {i}", "_name": name} for i in range(n)]
    out["directors"] = [{"key": "c/7/director/s", "full_name": "Hidden Person", "suppressed": True, "_name": "Hidden Person"}]
    return out


@pytest.fixture
def many(monkeypatch):
    held = many_rows()
    date = {view: col for view, _, _, col in MANY}

    def rows(conn, sql, params=()):
        if sql.startswith("select count(*) as n, bool_or(contested)"):
            return [{"n": sum(len(x) for x in held.values()), "contested": False}]
        if sql.startswith("select n.view, n.name_filed, count(*)"):
            return [{"view": v, "name_filed": x[0]["_name"], "n": len(x)} for v, x in held.items() if x]
        if sql.startswith("select n.view, count(*)"):                               # the check's count, apart
            return [{"view": v, "n": len(x)} for v, x in held.items()]
        if sql.startswith("select n.name_filed, count(*)") and "pub.directors r" in sql:
            return [{"name_filed": r["_name"], "n": 1} for r in held["directors"] if r["suppressed"]]
        hit = re.search(r"from pub\.(\w+) r\b", sql)
        if sql.startswith(("select r.*", "with k as")) and hit:
            limit, offset = params[-2:]
            got = sorted(held[hit.group(1)], key=lambda r: (r[date[hit.group(1)]], r["key"]), reverse=True)
            return [dict(r) for r in got[offset:offset + limit]]
        return []
    monkeypatch.setattr(dossier.db, "rows", rows)
    monkeypatch.setattr(dossier.document, "statuses", lambda conn, shas: {})
    monkeypatch.setattr(dossier.lineage, "related_of", lambda conn, refs: [])
    return held


def test_an_entity_of_3000_rows_over_three_views_is_shown_by_view_each_row_counted_once(many):
    from products.board import check
    x = dossier.gather(None, "entity:" + MANY_GID)
    page = dossier.pane(x, "brown", search.FIRST)
    order = [r for r, _ in cat.REGISTERS]
    want = sorted([(view, n) for view, n, _, _ in MANY], key=lambda vn: order.index(V[vn[0]].register))
    assert x["many"] and [(v.name, k) for v, k in x["views"]] == want                           # the catalogue's register order
    sections = re.findall(r'<details class="dview" data-view="(\w+)" data-count="(\d+)">', page)
    assert [(v, int(k)) for v, k in sections] == want
    assert "3,000 rows across 3 views" in page and sum(k for _, k in x["names"]) == 3000
    assert page.count('<li><span class="when">') == 3 * dossier.VIEW_ROWS < 3000                   # a page per view read, not 3,000
    assert page.count('<li class="newest">') == dossier.TIMELINE_ROWS and "and 2,960 more rows" in page
    newest = re.findall(r'<li class="newest"><span class="when">([\d-]+)</span>', page)
    assert newest == sorted(newest, reverse=True) and newest[0] == "2004-12-04"                # hansard's 1,800th day, the newest
    assert "Hidden Person" not in page and "suppressed" not in section(page, "d-rows")          # hard limit 16: unnamed and uncounted
    assert x["hidden_count"] == 1 and check.many_problems(None, MANY_GID, 3001, x, page) == []


def test_a_view_of_a_many_rows_dossier_pages_to_the_rest(many):
    x = dossier.gather(None, "entity:" + MANY_GID, "", "parliament_written_questions", 50)
    page = dossier.pane(x, "brown", search.FIRST)
    assert '<details class="dview" data-view="parliament_written_questions" data-count="1000" open>' in page
    assert "rows 51 to 100 of 1,000, newest first" in page and "the newer 50" in page and "the next 50 of 900 older" in page
    assert "dv=parliament_written_questions&amp;do=100" in page and "dv=hansard_speeches&amp;do=50" in page


def test_the_check_goes_red_when_a_view_drops_out_of_the_count(many, monkeypatch):
    from products.board import check
    real = dossier.counted
    monkeypatch.setattr(dossier, "counted", lambda conn, gid: dict(real(conn, gid), views=real(conn, gid)["views"][:-1]))
    x = dossier.gather(None, "entity:" + MANY_GID)
    gone, k = real(None, MANY_GID)["views"][-1]
    found = check.many_problems(None, MANY_GID, 3001, x, dossier.pane(x))
    assert any(f"counts {3000 - k:,} rows by view" in p for p in found)
    assert any(f"counts 0 rows of {gone.name} where the group holds {k:,}" in p for p in found)


def test_a_group_at_the_many_rows_line_is_shown_whole_as_before(many, monkeypatch):
    many["parliament_written_questions"][:] = many["parliament_written_questions"][:dossier.MANY_AT]
    for v in ("hansard_speeches", "beehive_release_ministers", "directors"):
        many[v].clear()
    asked = []
    monkeypatch.setattr(people, "entity", lambda conn, gid: asked.append(gid))
    assert dossier.gather(None, "entity:" + MANY_GID)["kind"] == "none" and asked == [MANY_GID]   # people.entity: the whole path
    many["directors"].append(many_rows()["directors"][0])                                           # one past the line
    assert dossier.gather(None, "entity:" + MANY_GID)["many"] and asked == [MANY_GID]


def test_a_view_s_page_is_read_from_the_address_and_a_bad_offset_is_the_first_page():
    assert server.dossier_page({"dv": ["hansard_speeches"], "do": ["50"]}) == ("hansard_speeches", 50)
    assert server.dossier_page({"do": ["-5"]}) == ("", 0) and server.dossier_page({"do": ["x"]}) == ("", 0)
    assert dossier.page_href("entity:g", "brown", search.FIRST, "hansard_speeches", 50).startswith("/?q=brown")
