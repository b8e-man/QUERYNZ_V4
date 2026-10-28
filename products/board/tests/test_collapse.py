"""The collapse section of ruling 112, on fixtures: each criterion folds the
entities that share its key and no others; the links lane's groups are
always on; a fold says it is collapsed here and not a link, carries its
members as the entities they are to its dossier, folds the graph the same
way, and only ever reads (every statement a select, never pub.links or
pub.groups written)."""
import re
import urllib.parse

import pytest

from products.board import catalogue as cat
from products.board import collapse, dossier, panes, people, search

DIRECTORS, COMPANIES, SHAREHOLDERS = cat.BY_NAME["directors"], cat.BY_NAME["companies"], cat.BY_NAME["shareholders"]
SAID = []


def person(key, name, **kw):
    return {"key": key, "entity_key": "companies/1", "full_name": name, "role_type": "Director", "suppressed": False, **kw}


def company(key, name, **kw):
    return {"key": key, "name": name, "status": "Registered", "nzbn": None, "number": None, **kw}


#: pub.names by ref: (kind, fl_key, full_key, has_middle)
NAMES = {"companies:g1a": ("person", "jane hart", "jane mary hart", True),
         "companies:g2a": ("person", "jane hart", "jane hart", False),
         "companies:g3a": ("person", "jane hart", "jane mary hart", True),
         "companies:d4": ("person", "joe bloggs", "joe bloggs", False),
         "companies:d5": ("person", "joe bloggs", "joe bloggs", False),
         "companies:s6": ("person", "joe bloggs", "joe bloggs", False)}
MEMBERS = {g: [{"ref": f"companies:{k}", "view": "directors", "key": k, "register": "companies", "name": "x", "kind": "person"}]
           for g, k in (("G1", "g1a"), ("G2", "g2a"), ("G3", "g3a"))}
#: pub.company_addresses by entity_key; a person's row's entity_key names its company and must never be asked
OFFICES = {"companies/c1": {"line_1": "Level 2, 10 Queen St", "line_2": "Auckland", "postcode": "1010"},
           "companies/c2": {"line_1": "LEVEL 2 10 QUEEN ST.", "line_2": "AUCKLAND", "postcode": "1010"},
           "companies/c3": {"line_1": "1 Other Road", "line_2": "Wellington", "postcode": "6011"},
           "companies/1": {"line_1": "Level 2, 10 Queen St", "line_2": "Auckland", "postcode": "1010"}}


@pytest.fixture(autouse=True)
def reads(monkeypatch):
    SAID.clear()

    def rows(conn, sql, params=()):
        SAID.append(sql)
        if "from pub.names" in sql:
            return [{"ref": r, "kind": k, "fl_key": fl, "full_key": full, "has_middle": mid}
                    for r, (k, fl, full, mid) in NAMES.items() if r in params[0]]
        if "from pub.company_addresses" in sql:
            return [{"entity_key": k, "line_3": None, "line_4": None, **o} for k, o in OFFICES.items() if k in params[0]]
        raise AssertionError(sql)
    monkeypatch.setattr(collapse.db, "rows", rows)
    monkeypatch.setattr(people, "members_of", lambda conn, gids: {g: MEMBERS[g] for g in gids})
    monkeypatch.setattr(people, "suppressed_refs", lambda conn, ms: set())


def entry(i, v=None, r=None, group=None):
    return {"id": f"entity:{group}" if group else f"{v.name}:{r['key']}", "group": group, "in_hand": [(v, r)] if v else []}


GROUPS = [entry(0, DIRECTORS, person("g1a", "Jane Mary Hart"), "G1"), entry(1, DIRECTORS, person("g2a", "Jane Hart"), "G2"),
          entry(2, DIRECTORS, person("g3a", "Jane Mary Hart"), "G3")]


def folded(xs, criteria):
    return [x for x in collapse.fold_entries(None, xs, criteria) if x.get("fold")]


def test_the_order_of_the_address_is_the_section_s():
    assert collapse.CHOICES == tuple(c for c, _, _ in collapse.CRITERIA if c != "groups") == search.COLLAPSE_CHOICES
    assert collapse.CRITERIA[0][0] == "groups"


def test_nothing_ticked_leaves_the_links_lane_s_groups_as_they_are():
    assert collapse.fold_entries(None, GROUPS, ()) == GROUPS and not SAID


def test_a_shared_first_and_last_name_folds_the_groups_that_share_it():
    (f,) = folded(GROUPS, ("name",))
    by, members = f["fold"]
    assert by == {"name"} and [m["id"] for m in members] == ["entity:G1", "entity:G2", "entity:G3"]
    assert collapse.words(by) == "collapsed here by shared name; not a link"


def test_a_shared_full_name_folds_only_names_with_middle_names():
    (f,) = folded(GROUPS, ("full",))
    assert [m["id"] for m in f["fold"][1]] == ["entity:G1", "entity:G3"]                 # G2's full key has no middle name
    bloggs = [entry(0, DIRECTORS, person("d4", "Joe Bloggs")), entry(1, DIRECTORS, person("d5", "Joe Bloggs"))]
    assert len(folded(bloggs, ("name",))) == 1 and folded(bloggs, ("full",)) == []        # one full key, but no middle name
    assert collapse.words(f["fold"][0]) == "collapsed here by shared full name; not a link"


def test_a_shared_registered_address_folds_companies_and_never_asks_for_a_person_s():
    xs = [entry(0, COMPANIES, company("companies/c1", "ACME LIMITED")), entry(1, COMPANIES, company("companies/c2", "ACME HOLDINGS")),
          entry(2, COMPANIES, company("companies/c3", "OTHER LIMITED")), entry(3, DIRECTORS, person("d4", "Joe Bloggs"))]
    (f,) = folded(xs, ("address",))
    assert [m["id"] for m in f["fold"][1]] == ["companies:companies/c1", "companies:companies/c2"]   # case and punctuation off
    asked = [s for s in SAID if "company_addresses" in s]
    assert len(asked) == 1 and "registered" not in collapse.words(f["fold"][0]).replace("registered address", "")
    keys = collapse.address_keys(None, [{"id": "d", "group": None, "rows": [(DIRECTORS, person("d4", "Joe Bloggs"))]}])
    assert keys == {}                                                                    # a director's company's office is not his


def test_a_shared_official_number_folds_an_organisation_s_own_number_only():
    xs = [entry(0, COMPANIES, company("companies/c1", "ACME LIMITED", nzbn="9429000000001")),
          entry(1, COMPANIES, company("companies/c3", "ACME (2011) LIMITED", nzbn="9429000000001")),
          entry(2, SHAREHOLDERS, {"key": "s6", "name": "ACME LIMITED", "holder_nzbn": "9429000000001", "suppressed": False})]
    (f,) = folded(xs, ("number",))
    assert [m["id"] for m in f["fold"][1]] == ["companies:companies/c1", "companies:companies/c3"]   # a holder's NZBN names someone else
    assert collapse.number_keys(COMPANIES, company("x", "X", number="123456")) == {"company number:123456"}
    assert collapse.number_keys(DIRECTORS, person("d", "D", nzbn="9429000000001", company_number="1")) == set()
    holders = [entry(i, SHAREHOLDERS, {"key": f"s{i}", "name": "ACME LIMITED", "holder_nzbn": "9429000000001", "suppressed": False})
               for i in (1, 2)]
    assert collapse.number_keys(*holders[0]["in_hand"][0]) == set() and folded(holders, ("number",)) == []
    award = cat.BY_NAME["award_suppliers"]                                                # one tender, two suppliers: an rfx id is no one's own
    tender = [entry(i, award, {"key": f"a{i}", "business_name": f"SUPPLIER {i}", "nzbn": f"94290000000{i}", "rfx_id": "778899"})
              for i in (1, 2)]
    assert folded(tender, ("number",)) == []


def test_a_suppressed_row_carries_no_key_and_is_never_folded():
    xs = [entry(0, DIRECTORS, person("d4", "Joe Bloggs")), entry(1, DIRECTORS, person("d5", "Hidden", suppressed=True))]
    assert folded(xs, ("name",)) == []


def test_criteria_join_through_a_chain_and_say_each_that_joined():
    xs = GROUPS[:1] + [entry(1, COMPANIES, company("companies/c1", "ACME", nzbn="1")),
                       entry(2, COMPANIES, company("companies/c2", "ACME TWO", nzbn="1"))]
    sets = collapse.union(["a", "b", "c", "d"], {"a": {"name": {"x"}}, "b": {"name": {"x"}, "number": {"1"}},
                                                 "c": {"number": {"1"}}, "d": {"name": {"y"}}}, ("name", "number"))
    assert sets == [(["a", "b", "c"], {"name", "number"})]
    assert collapse.words({"name", "number"}) == "collapsed here by shared name and shared official number; not a link"
    assert len(folded(xs, ("number",))) == 1


def test_every_statement_is_a_read_and_none_touches_links_or_groups():
    for c in collapse.CHOICES:
        collapse.fold_entries(None, GROUPS + [entry(3, COMPANIES, company("companies/c1", "ACME", nzbn="1"))], (c,))
    assert SAID and all(re.match(r"\s*select\b", s, re.I) for s in SAID)
    assert not any(re.search(r"\b(insert|update|delete|create|alter|drop|truncate|copy)\b", s, re.I) for s in SAID)
    assert not any("pub.links" in s or "pub.groups" in s for s in SAID)


def test_a_fold_s_dossier_address_round_trips_keys_with_any_character():
    ids = ["entity:G1", "local_election_returns:Council|https://x.nz/a,b:c.pdf"]
    d = collapse.fold_id(ids, {"name", "address"})
    assert d.startswith("fold:name+address:") and collapse.parse(d) == (("name", "address"), ids)
    assert dossier.parse(d) == d and dossier.parse("fold:name:only-one") == "" and dossier.parse("fold:bogus:a,b") == ""


def ents_of(xs):
    return {"group": {}, "entity": {g: {"group_id": g, "label": l, "rows": n, "count": people.count_words(n, 1), "contested": False,
                                         "registers_named": ["Companies, directors and shareholders"], "centre": c}
                                     for g, l, n, c in (("G1", "Jane Mary Hart", 3, "directors:g1a"),
                                                        ("G2", "Jane Hart", 1, "directors:g2a"),
                                                        ("G3", "Jane Mary Hart", 2, "directors:g3a"))}, "named": {}}


def test_the_results_pane_holds_the_section_closed_and_the_folded_entry_says_so(monkeypatch):
    ents = ents_of(GROUPS)
    ents["group"] = {f"directors:{k}": g for g, k in (("G1", "g1a"), ("G2", "g2a"), ("G3", "g3a"))}
    rows = [r for x in GROUPS for _, r in x["in_hand"]]
    res = {"companies": [(DIRECTORS, 3, rows)], "held": {"directors"}, "hidden": {}, "tabs": None}
    boxes = search.FIRST._replace(collapse=("name",), people=True)
    plain = panes.results_pane("hart", res, {"directors"}, ("companies",), boxes._replace(collapse=()), ents=ents)
    html = panes.results_pane("hart", res, {"directors"}, ("companies",), boxes, ents=ents,
                              fold=collapse.folder(None, boxes.collapse))
    assert '<details class="collapse" id="collapse"><summary>collapse' in html and "<details class=\"collapse\" id=\"collapse\" open" not in html
    section = html[html.index('id="collapse"'):html.index("</details>", html.index('id="collapse"'))]
    assert 'checked disabled> the links lane' in section and 'name="cl" value="name" checked' in section
    assert 'name="cl" value="number">' in section and 'name="g" value="entities"' in section and 'name="cl" value="name"' in section
    assert section.count('type="hidden" name="cl"') == 0                                  # the boxes themselves carry cl
    assert html.index('id="collapse"') < html.index("<h3>Entities")
    assert plain.count('class="hit entity"') == 3 and html.count('class="hit entity folded"') == 1
    assert "collapsed here by shared name; not a link" in html and ">3 entities, from " in html and "6 rows" not in html
    assert '<span class="count">1</span></h3>' in html                                    # the entities counted after the fold
    d = re.search(r'class="hit entity folded"[^>]* data-dossier="([^"]*)"', html).group(1)
    assert collapse.parse(panes.html.unescape(d)) == (("name",), ["entity:G1", "entity:G3", "entity:G2"])     # most rows first


def test_the_fold_s_dossier_lists_its_members_as_the_entities_they_are(monkeypatch):
    monkeypatch.setattr(people, "gather", lambda conn, hits, named=None: ents_of(GROUPS))
    monkeypatch.setattr(dossier.search, "row", lambda conn, v, k: company(k, "ACME LIMITED") if v == "companies" else None)
    monkeypatch.setattr(dossier, "FOLD_GATHERED", 0)          # the listing alone; test_dossier covers the members' records
    d = collapse.fold_id(["entity:G1", "entity:G2", "companies:companies/c1"], {"name"})
    x = dossier.gather(None, d)
    page = dossier.pane(x, "hart")
    assert x["kind"] == "fold" and x["centre"] == "directors:g1a" and len(x["members"]) == 3
    assert "collapsed here by shared name; not a link" in page and "never written" in page
    assert page.count('<a class="row" href="/?q=hart') == 3 and "d=entity%3AG1" in page and "d=companies%3Acompanies%2Fc1" in page
    assert "single-row entity" not in page and "rows, " not in page


def graph_of():
    n = lambda v, r, order, **kw: {"v": v, "row": r, "matched": True, "centre": False, "order": order, "parent": None, **kw}
    ent = lambda g, k, name, order: n(DIRECTORS, person(k, name), order, title=name, entity={"group_id": g, "in_hand": [f"directors:{k}"],
                                                                                         "rows": 2, "count": "2 rows, 1 register"})
    nodes = {"entity:G1": ent("G1", "g1a", "Jane Mary Hart", 0), "entity:G2": ent("G2", "g2a", "Jane Hart", 1),
             "companies:companies/c3": n(COMPANIES, company("companies/c3", "OTHER LIMITED"), 2, lone=True)}
    edges = [{"kind": "role", "a": "entity:G1", "b": "companies:companies/c3", "label": "director of", "cite": "x", "rule": None},
             {"kind": "role", "a": "entity:G2", "b": "companies:companies/c3", "label": "director of", "cite": "y", "rule": None},
             {"kind": "same person, near", "a": "entity:G1", "b": "entity:G2", "label": "near", "cite": "x", "rule": "r@1"}]
    rows = {f"directors:{k}": {"v": DIRECTORS, "row": person(k, nm)} for k, nm in (("g1a", "Jane Mary Hart"), ("g2a", "Jane Hart"))}
    return {"nodes": nodes, "edges": edges, "people": True, "inside": 0, "decisions": {}, "lineage": []}, rows


def test_the_graph_folds_the_same_way_with_the_same_words_on_the_node():
    g, rows = graph_of()
    out = collapse.fold_graph(None, g, ("name",), rows)
    (fid,) = [k for k, x in out["nodes"].items() if x.get("fold")]
    f = out["nodes"][fid]["fold"]
    assert f["words"] == "collapsed here by shared name; not a link" and f["members"] == ["entity:G1", "entity:G2"]
    assert f["count"] == "2 entities, 4 rows" and out["nodes"][fid]["title"] == "Jane Mary Hart"
    assert set(out["nodes"]) == {fid, "companies:companies/c3"} and out["inside"] == 1          # the near line fell inside
    assert len(out["edges"]) == 1 and {out["edges"][0]["a"], out["edges"][0]["b"]} == {fid, "companies:companies/c3"}
    assert collapse.parse(f["dossier"]) == (("name",), ["entity:G1", "entity:G2"])
    assert collapse.fold_graph(None, g, (), rows) is g


def test_the_graph_answer_carries_the_fold_s_words_and_its_dossier():
    from products.board import graph
    g, rows = graph_of()
    out = collapse.fold_graph(None, g, ("name",), rows)
    out.update({"drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS}, "not_drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS},
                "matched_total": 3, "unresolved": 0, "centre": ""})
    data = graph.answer(out, "hart", search.FIRST._replace(people=True, collapse=("name",)))
    (n,) = [n for n in data["nodes"] if n.get("kind") == "fold"]
    assert n["words"] == "collapsed here by shared name; not a link" and n["dossier"].startswith("fold:name:")
    assert "d=fold%3Aname%3A" in n["pane"] and n["grow"] == ""
    picture = graph.svg(out, "hart", search.FIRST)
    assert "collapsed here by shared name; not a link" in picture


def test_a_fold_is_named_by_its_groups_before_a_row_s_title_with_its_year():
    assert collapse.label(["John Clive Smith"], ["John Smith · ge-2020 · Hauraki"]) == "John Clive Smith"
    assert collapse.label([], ["ACME LIMITED", "ACME HOLDINGS LIMITED"]) == "ACME HOLDINGS LIMITED"


OFFICERS, CELEBRANTS = cat.BY_NAME["charity_officers"], cat.BY_NAME["gazette_celebrants"]


def test_a_row_pub_names_does_not_hold_is_keyed_from_its_own_name_columns():
    """charity_officers and gazette_celebrants are no view of the links lane: pub.names holds none of their rows,
    so each is keyed from its declared Name (parts, ruling 85) in pub.names' own shape and folds with the entity."""
    officer = {"key": "o1", "full_name": "Jane Mary HART", "first_name": "Jane", "middle_name": "Mary", "last_name": "HART",
               "suppressed": False}
    celebrant = {"key": "c1", "surname": "HART", "given_names": "Jāne Mary", "organisation": None}
    other = {"key": "c2", "surname": "Jane", "given_names": "Hart", "organisation": None}        # family-given read right: not Jane Hart
    hidden = {**officer, "key": "o2", "suppressed": True}
    xs = GROUPS[:2] + [entry(2, OFFICERS, officer), entry(3, CELEBRANTS, celebrant), entry(4, CELEBRANTS, other),
                       entry(5, OFFICERS, hidden)]
    (f,) = folded(xs, ("name",))
    assert [m["id"] for m in f["fold"][1]] == ["entity:G1", "entity:G2", "charity_officers:o1", "gazette_celebrants:c1"]
    (f,) = folded(xs, ("full",))
    assert [m["id"] for m in f["fold"][1]] == ["entity:G1", "charity_officers:o1", "gazette_celebrants:c1"]
    assert collapse.row_name_keys(CELEBRANTS, celebrant) == ("jane hart", "jane mary hart", True) == NAMES["companies:g1a"][1:]
    assert collapse.row_name_keys(OFFICERS, hidden) is None
    assert collapse.row_name_keys(CELEBRANTS, {**celebrant, "surname": "HART TRUST"}) is None     # an organisation word abstains
    assert collapse.row_name_keys(OFFICERS, {**officer, "first_name": "Jane (Janey)"})[0] == "jane hart"


def test_a_row_pub_names_holds_is_never_re_read_from_its_columns():
    """A directors row pub.names keys as Jane Hart keeps that key even where its columns would say otherwise."""
    xs = [GROUPS[1], entry(1, DIRECTORS, person("d4", "Jane Hart", first_name="Jane", last_name="Hart")),
          entry(2, OFFICERS, {"key": "o1", "first_name": "Joe", "last_name": "Bloggs", "full_name": "Joe Bloggs", "suppressed": False})]
    (f,) = folded(xs, ("name",))                                                          # d4 is Joe Bloggs in pub.names, not Jane Hart
    assert [m["id"] for m in f["fold"][1]] == ["directors:d4", "charity_officers:o1"]
