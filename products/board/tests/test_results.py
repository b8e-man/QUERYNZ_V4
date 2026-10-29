"""The results pane of ruling 108, on fixtures: entities alone (ruling 111;
the graph's one state, ruling 120: groups first, then the rows in no group, a
suppressed row never gathered); tabs by the field a hit matched, for the search box and for "any
field may match", each register closed to its name and count, none for "all
fields must match"; every result carries the graph it opens beside the pane."""
import re
import urllib.parse

import pytest

from products.board import catalogue as cat
from products.board import graph, panes, people, search

D1, D2, D3, S1 = "c/1/director/a", "c/2/director/b", "c/3/director/c", "c/4/director/s"
DIRECTORS = cat.BY_NAME["directors"]


def row(key, name, **kw):
    return {"key": key, "entity_key": "c/1", "full_name": name, "role_type": "Director", "suppressed": False, **kw}


def ref(key):
    return f"{DIRECTORS.register}:{key}"


@pytest.fixture
def reads(monkeypatch):
    grp = {ref(D1): ("G1", False), ref(D2): ("G1", False), ref(S1): ("G1", False)}
    members = {"G1": [{"ref": ref(k), "view": "directors", "key": k, "register": "companies", "name": n, "kind": "person"}
                      for k, n in ((D1, "Jane Hart"), (D2, "Jane Mary Hart"), (S1, "Hidden Hart"))]
               + [{"ref": "mp_interests:x", "view": "mp_interests", "key": "x", "register": "mp_interests", "name": "J Hart", "kind": "person"}],
               "G2": [{"ref": "house:c9", "view": "candidates", "key": "c9", "register": "house", "name": "Joe Hart", "kind": "person"}]}
    monkeypatch.setattr(people, "groups_of", lambda conn, refs: {r: grp[r] for r in refs if r in grp})
    monkeypatch.setattr(people, "members_of", lambda conn, gids: {g: members[g] for g in gids})
    monkeypatch.setattr(people, "suppressed_refs", lambda conn, ms: {m["ref"] for m in ms if m["name"] == "Hidden Hart"})
    monkeypatch.setattr(people.db, "rows", lambda conn, sql, params=(): [{"group_id": "G2", "c": True}])
    monkeypatch.setattr(people.lineage, "related_refs", lambda conn, refs: {})
    return grp


def hits():
    return [(DIRECTORS, row(D1, "Jane Hart")), (DIRECTORS, row(D2, "Jane Mary Hart")), (DIRECTORS, row(D3, "Joe Hart")),
            (DIRECTORS, row(S1, "Hidden Hart", suppressed=True))]


def results_of(rs, **counts):
    rows = [dict(r, **{f"_n_{t}": n for t, n in counts.items()}) for r in rs]
    return {"companies": [(DIRECTORS, len(rows), rows)], "held": {"directors"}, "hidden": {}, "tabs": None}


def test_the_rows_in_one_group_are_one_entity_and_a_suppressed_row_is_never_gathered(reads):
    ents = people.gather(None, hits())
    assert ents["group"] == {f"directors:{D1}": "G1", f"directors:{D2}": "G1"}          # S1 is in G1 and never gathered
    e = ents["entity"]["G1"]
    assert e["label"] == "Jane Mary Hart" and e["rows"] == 3 and e["registers"] == 2       # the hidden row is not counted
    assert e["registers_named"] == [panes.REGISTER_NAME["mp_interests"], panes.REGISTER_NAME["companies"]]
    assert "Hidden" not in repr(ents)


ROW_CARD = re.compile(r'<article class="hit"|<table class="f">|class="cite')     # a row's own card: its fields, its citation


def test_the_results_list_entities_alone(reads):
    """Ruling 111: groups first, then each row in no group as an entity of one
    row; no row's card anywhere in the pane."""
    ents = people.gather(None, hits())
    boxes = search.FIRST
    html = panes.results_pane("hart", results_of([r for _, r in hits()]), {"directors"}, ("companies",), boxes, ents=ents)
    entities, lone = html.index("<h3>Entities"), html.index("<h4>Single-row entities")
    assert '<span class="count">3</span></h3>' in html                                     # G1, then Joe Hart and the suppressed row
    assert entities < html.index('class="hit entity"') < lone
    assert html.count('class="hit entity') == 3 and html.count('class="hit entity lone"') == 2 and "2 registers" not in html
    assert 'class="what">declares interests, director</div>' in html                      # ruling 117 (2): what it is, not its counts
    assert not ROW_CARD.search(html) and "Rows in no group" not in html
    assert "matching here" not in html and html[:lone].count("Jane Hart") == 0                 # ruling 110 (1): no list of the rows' names
    after = html[lone:]
    assert "Joe Hart" in after and panes.SUPPRESSED in after and after.count('class="what">director</div>') == 1
    assert "1 row, 1 register" not in html and "single-row entity" not in html and "· directors</div>" not in html
    assert "Jane Mary Hart" not in after and "Hidden" not in html
    assert f'data-dossier="directors:{D3}"' in after and 'data-dossier="entity:G1"' in html[:lone]
    assert 'id="state"' not in html                                                       # no switch anywhere (ruling 120)


def test_an_entity_the_name_search_found_is_listed_after_those_in_hand_and_under_its_tab(reads):
    ents = people.gather(None, hits()[:1], named={"G2": {"first", "last"}})
    assert ents["entity"]["G2"]["contested"] and ents["named"] == {"G2": {"first", "last"}}
    res = results_of([row(D1, "Jane Hart", _tab_last=True, _tab_first=True)], last=1, first=1)
    res["tabs"] = search.BOX
    html = panes.results_pane("hart", res, {"directors"}, ("companies",), search.FIRST, ents=ents)
    for t in ("first", "last"):
        tab = html[html.index(f'id="ftab-{t}"'):]
        tab = tab[:tab.index("</div>\n<div") if "</div>\n<div" in tab else len(tab)]
        assert tab.index("Jane Mary Hart") < tab.index("Joe Hart") and "no row heading this list" in tab and "contested" in tab


def test_tabs_hold_entities_and_count_them(reads):
    """Ruling 111: each tab holds the entities one of whose rows matched its
    field, its count those entities, "+" where rows matched past those read."""
    rs = [row(D1, "Jane Hart", _tab_last=True), row(D2, "Hart Jane", _tab_first=True, _tab_last=True), row(D3, "Elsewhere", _tab_other=True)]
    res = results_of(rs, last=120, first=1, other=1)
    res["tabs"] = search.BOX
    lone = panes.results_pane("hart", res, {"directors"}, ("companies",), search.FIRST)          # nothing gathered: three of one row
    labels = re.findall(r'<label for="ft-(\w+)">([^<]*)<span class="count">([\d,+]+)</span>', lone)
    assert labels == [("first", "first name ", "1"), ("last", "last name ", "2+"), ("other", "elsewhere in the row ", "1")]
    ents = people.gather(None, [(DIRECTORS, r) for r in rs])
    html = panes.results_pane("hart", res, {"directors"}, ("companies",), search.FIRST, ents=ents)
    labels = re.findall(r'<label for="ft-(\w+)">([^<]*)<span class="count">([\d,+]+)</span>', html)
    assert labels == [("first", "first name ", "1"), ("last", "last name ", "1+"), ("other", "elsewhere in the row ", "1")]
    assert html.count('type="radio" class="ft"') == 3 and html.count(" checked>") == 1
    last = html[html.index('id="ftab-last"'):html.index('id="ftab-other"')]
    assert last.count('data-dossier="entity:G1"') == 1 and "Elsewhere" not in last              # D1 and D2: one entity
    assert "118 more matching rows were not read" in last and not ROW_CARD.search(html)
    first = html[html.index('id="ftab-first"'):html.index('id="ftab-last"')]
    assert 'data-dossier="entity:G1"' in first                                                 # under every field one of its rows matched
    for t in ("first", "last", "other"):                                                      # the sheet shows the checked tab's alone
        assert f"#ft-{t}:checked~#ftab-{t}{{display:block}}" in panes.CSS


def test_all_fields_must_match_has_no_tabs_and_any_field_has_one_per_filled_field():
    both = {"first": "jane", "last": "hart"}
    assert search.tab_mode("", both, search.ALL) is None and search.tab_mode("hart", both, search.ALL) is None
    assert search.tab_mode("", both, search.ANY) == search.BY_FIELD
    assert search.tab_mode("hart", {}, search.ALL) == search.BOX and search.tab_mode("", {}, search.ANY) is None
    res = results_of([row(D1, "Jane Hart")])
    html = panes.results_pane("", res, {"directors"}, ("companies",), search.FIRST._replace(fields=tuple(both.items())))
    assert 'class="ftabs"' not in html and "<h3>Entities" in html and not ROW_CARD.search(html)


@pytest.mark.parametrize("tabs", [search.BOX, search.BY_FIELD])
def test_the_tab_query_has_a_parameter_for_every_placeholder_in_every_view(tabs):
    fields = {"first": "jane", "last": "hart", "org": "acme", "address": "queen", "year": "2020"}
    for v in cat.VIEWS:
        for removed in (True, False):
            got = search.view_sql(v, ["hart", "2020"], "2020", 50, fields=fields if tabs == search.BY_FIELD else None,
                                  mode=search.ANY, removed=removed, tabs=tabs)
            if got is None:
                continue
            sql, params = got
            assert sql.count("%s") == len(params), v.name
            assert "_n_" in sql and "_r_" in sql and (tabs == search.BY_FIELD or "_tab_other" in sql)


def py(pattern: str) -> str:
    """The database's word edges in Python's dialect."""
    return pattern.replace(r"\m", r"\b").replace(r"\M", r"\b")


def test_a_box_word_need_only_begin_a_name_word_in_its_place():
    plain, comma, one = (py(x) for x in search.name_patterns("last", "hart", cat.GIVEN_FAMILY, prefix=True))
    assert re.search(plain, "jane hartley") and not re.search(plain, "hartley jane")
    plain = py(search.name_patterns("last", "hart", cat.GIVEN_FAMILY)[0])
    assert not re.search(plain, "jane hartley") and re.search(plain, "jane hart")


def test_every_result_carries_the_graph_it_opens_with_the_boxes_and_no_state():
    boxes = search.FIRST._replace(collapse=("name",))
    html = panes.lone_hit("hart", DIRECTORS, row(D1, "Jane Hart"), ["hart"], boxes)
    url = re.search(r'data-graph="([^"]*)"', html).group(1).replace("&amp;", "&")
    qs = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    assert url.startswith("/graph.json?") and qs["c"] == [f"directors:{D1}"] and qs["cl"] == ["name"] and "g" not in qs


def test_the_side_pane_is_the_canvas_empty_hidden_and_in_the_entities_state():
    side = graph.side_pane(search.FIRST)
    assert 'class="pane side"' in side and 'id="cy"' in side and 'id="graph-data"' in side and "entities" in side
    data = side[side.index('id="graph-data">') + len('id="graph-data">'):side.index("</script>")]
    assert '"nodes":[]' in data and '"mode":"entities"' in data
    assert "div.duo{flex-direction:column}" in panes.CSS                                       # a narrow window stacks it under the results


def test_the_name_keys_are_read_as_the_links_lane_reads_a_filed_name():
    assert people.name_keys("Rt Hon Hart, Graeme Richard") == {"fl": "graeme hart", "full": "graeme richard hart",
                                                              "person": "graeme hart richard", "org": "rt hon hart, graeme richard"}
    assert people.name_keys("Māori|maori") == {"person": "maori", "org": "maori"}            # one word: a family name, no fl key
    assert people.name_keys("12345") == {}
    assert people.name_keys("ignored", {"first": "Jane", "middle": "Mary", "last": "O'Hart", "org": "Acme Ltd"}) == {
        "fl": "jane ohart", "full": "jane mary ohart", "org": "acme"}
    assert people.name_keys("", {"last": "hart"}) == {}                                        # a last name alone is on no index


def test_an_entity_is_found_by_the_key_it_matched_under_that_field_and_never_by_a_suppressed_row(monkeypatch):
    seen = {}

    def rows(conn, sql, params=()):
        seen["sql"], seen["params"] = sql, params
        base = {"view": "directors", "register": "companies", "kind": "person", "has_middle": False,
                "by_fl": False, "by_full": False, "by_person": False, "by_org": False}
        return [dict(base, ref="a", key="a", group_id="G1", name_filed="Jane Hart", by_fl=True),
                dict(base, ref="b", key="b", group_id="G2", name_filed="Jane Mary Hart", has_middle=True, by_full=True),
                dict(base, ref="c", key="c", group_id="G3", name_filed="Acme", kind="organisation", by_org=True),
                dict(base, ref="s", key="s", group_id="G4", name_filed="Jane Hart", by_fl=True)]
    monkeypatch.setattr(people.db, "rows", rows)
    monkeypatch.setattr(people, "suppressed_refs", lambda conn, ms: {"s"})
    got = people.named_groups(None, "Jane Mary Hart", registers=("companies",))
    assert got == {"G1": {"first", "last"}, "G2": {"first", "middle", "last"}, "G3": {"org"}}     # G4 only by a suppressed row
    assert "pub.names n join pub.groups g on g.row_key = n.ref" in seen["sql"] and seen["params"]["regs"] == ["companies"]
    assert "like" not in seen["sql"] and "~" not in seen["sql"]                                  # equality on the indexed keys only
    with_box = people.named_groups(None, "mary", {"first": "jane", "last": "hart"})
    assert set(with_box) == {"G2"}                                                               # fields and the box: the box's words too


def test_the_graph_has_one_state_entities_and_no_switch():
    """Ruling 120: the rows mode, its switch and its address value leave; an
    address naming either state (`g=rows`, `g=entities`) opens the entities
    graph, the boxes read as without it and no href carries `g=`."""
    side = graph.side_pane(search.FIRST, "directors:a", q="hart", chosen="entity:G1")
    opened = graph.side_pane(search.FIRST, g=graph_sample(), q="hart", chosen="")
    for pane in (side, opened):
        assert 'id="state"' not in pane and "aria-current" not in pane and ">rows</a>" not in pane and "g=" not in pane
        assert "graph beside the results · entities" in pane
    assert 'data-inline="1"' in opened and 'class="pane side on"' in opened and "<svg" in opened
    assert "the switch" not in side and "on the graph tab" not in side and "/graph?" not in side + opened
    for g in (["rows"], ["entities"]):
        assert search.boxes_of({"q": ["hart"], "cl": ["name"], "g": g}) == search.boxes_of({"q": ["hart"], "cl": ["name"]})
    assert "people" not in search.Boxes._fields and "g" not in dict(search.FIRST._replace(collapse=("name",)).params())
    assert "people" not in graph.build.__code__.co_varnames[:graph.build.__code__.co_argcount] and not hasattr(graph, "switch")


def graph_sample():
    v = DIRECTORS
    return {"nodes": {f"directors:{D1}": {"v": v, "row": row(D1, "Jane Hart"), "matched": True, "centre": False, "order": 0,
                                          "parent": None}},
            "edges": [], "drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS}, "not_drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS},
            "matched_total": 1, "unresolved": 0, "centre": ""}


def test_the_bar_has_no_graph_tab_and_the_old_address_answers_with_the_search_page_and_the_graph_open():
    from products.board import server
    page = panes.page("hart", [], [], "", search.FIRST)
    assert ">search</a>" in page and ">use cases</a>" in page and ">graph</a>" not in page and 'href="/graph' not in page
    old = urllib.parse.parse_qs("q=Graeme+Hart&all=0&r=companies&r=party_returns&g=entities&c=directors%3Ac%2F1%2Fdirector%2Fa")
    to = server.graph_redirect(old)
    qs = urllib.parse.parse_qs(urllib.parse.urlsplit(to).query)
    assert to.startswith("/?") and qs["q"] == ["Graeme Hart"] and qs["r"] == ["companies", "party_returns"]
    assert qs["all"] == ["0"] and "g" not in qs and qs["d"] == [f"directors:{D1}"] and qs["gv"] == ["1"]
    assert search.boxes_of(qs) == search.boxes_of(old)                                           # the same boxes; the state is one
    plain = urllib.parse.parse_qs(urllib.parse.urlsplit(server.graph_redirect({"q": ["hart"], "tab": ["graph"]})).query)
    assert plain == {"q": ["hart"], "all": ["1"], "gv": ["1"]}                                  # the whole search, no centre
    assert "d" not in urllib.parse.parse_qs(server.graph_redirect({"c": ["nosuchview:1"]}).split("?")[1])
