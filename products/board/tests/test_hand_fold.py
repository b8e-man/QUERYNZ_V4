"""The fold by hand of ruling 119, on fixtures shaped like the Rank Group
search: every organisation entity carries a tick box and a person entity
none; the ticked fold into one entry named by the fullest name among them,
saying it is collapsed here by hand and not a link; the others stay apart;
the fold travels in the address (`hf=`) and reopens folded; the dossier
lists the members as the entities they are; the graph draws one node with
the same words; a person named in an address is never folded; and every
statement is a read."""
import re
import urllib.parse
from html import unescape

import pytest

from products.board import catalogue as cat
from products.board import collapse, dossier, panes, people, search

SHAREHOLDERS, COMPANIES, DIRECTORS = cat.BY_NAME["shareholders"], cat.BY_NAME["companies"], cat.BY_NAME["directors"]
COMCOM, DONORS, NOTICES = cat.BY_NAME["commerce_commission_parties"], cat.BY_NAME["party_return_donors"], cat.BY_NAME["gazette_notices"]
SAID = []
#: pub.names' kind by ref, for the lone rows of person views pub.names holds
KINDS = {"party_return_donors:d1": "organisation", "directors:p1": "person"}
GROUP = "companies:companies/9429037782269"


def holder(key, name, kind="company"):
    return {"key": f"companies/c{key}/shareholder/{key}", "name": name, "shareholder_type": kind, "entity_key": f"companies/c{key}",
            "suppressed": False}


def company(key, name):
    return {"key": f"companies/{key}", "name": name, "status": "Registered", "nzbn": None, "number": None}


def entry(v, r, group=None):
    return {"id": people.entity_id(group) if group else f"{v.name}:{r['key']}", "group": group, "in_hand": [(v, r)]}


@pytest.fixture(autouse=True)
def reads(monkeypatch):
    SAID.clear()

    def rows(conn, sql, params=()):
        SAID.append(sql)
        if "from pub.names" in sql:
            return [{"ref": r, "kind": k} for r, k in KINDS.items() if r in params[0]]
        raise AssertionError(sql)
    monkeypatch.setattr(collapse.db, "rows", rows)
    monkeypatch.setattr(collapse.links_view, "ref", lambda v, key: f"{v.name}:{key}")


def rank():
    """The group Rank Group Limited, five RANK GROUP LIMITED holder rows, the
    Commerce Commission party, two other Rank Group companies, a person holder, a director and a notice."""
    xs = [entry(DONORS, {"key": "g1", "donor": "Rank Group Limited"}, GROUP)]
    xs += [entry(SHAREHOLDERS, holder(i, "RANK GROUP LIMITED")) for i in range(1, 6)]
    xs += [entry(COMCOM, {"key": "commerce_commission/case/rank-group", "name": "Rank Group Ltd"}),
           entry(COMPANIES, company("9429031574990", "RANK GROUP HOLDINGS FINANCE (2010) LIMITED")),
           entry(COMPANIES, company("9429031575157", "RANK GROUP HOLDINGS (2010) LIMITED")),
           entry(SHAREHOLDERS, holder(9, "Jane RANK", "individual")),
           entry(DIRECTORS, {"key": "p1", "full_name": "Jane Rank", "entity_key": "companies/x", "suppressed": False}),
           entry(NOTICES, {"key": "gazette/2010-al6822", "title": "RANK GROUP CAPITAL LIMITED (in liquidation)"})]
    return xs


ENTS = {"group": {}, "named": {},
        "entity": {GROUP: {"group_id": GROUP, "label": "Rank Group Limited via Graeme Hart", "rows": 17, "registers": 3,
                           "count": "17 rows, 3 registers", "contested": False, "kinds": ["organisation"], "what": "donor",
                           "registers_named": ["Party donation and loan returns"], "centre": "party_return_donors:g1"},
                   "G2": {"group_id": "G2", "label": "Jane Rank", "rows": 2, "registers": 1, "count": "", "contested": False,
                          "kinds": ["person"], "what": "director", "registers_named": [], "centre": ""}}}
FOLD = (people.entity_id(GROUP),) + tuple(f"shareholders:companies/c{i}/shareholder/{i}" for i in range(1, 6)) \
    + ("commerce_commission_parties:commerce_commission/case/rank-group",)


def test_every_organisation_entity_is_offered_and_no_person_or_document():
    xs = rank() + [entry(DONORS, {"key": "d1", "donor": "Rank Group"}), entry(DIRECTORS, {"key": "p2", "full_name": "A B", "suppressed": True}),
                   {"id": "entity:G2", "group": "G2", "in_hand": []}]
    orgs = collapse.organisations(None, xs, ENTS)
    assert people.entity_id(GROUP) in orgs and "entity:G2" not in orgs                 # a group by the lane's kinds
    assert set(FOLD) <= orgs                                                            # holder type "company", an organisation view
    assert "companies:companies/9429031574990" in orgs and "party_return_donors:d1" in orgs     # pub.names' kind
    assert not {"shareholders:companies/c9/shareholder/9", "directors:p1", "directors:p2", "gazette_notices:gazette/2010-al6822"} & orgs
    assert len([s for s in SAID if "from pub.names" in s]) == 1                         # one query for the lone rows unsettled


def test_a_group_with_no_kinds_is_an_organisation_only_when_its_rows_are():
    assert collapse.organisation_group({"kinds": []}, [(COMPANIES, company("1", "ACME LIMITED"))])
    assert not collapse.organisation_group({"kinds": []}, [(DIRECTORS, {"key": "k", "full_name": "A B"})])
    assert not collapse.organisation_group({"kinds": ["organisation", "person"]}, [])
    assert not collapse.organisation_group(None, [(COMPANIES, company("1", "ACME LIMITED"))])


def test_the_ticked_fold_into_one_entry_and_the_rest_stay_apart():
    xs = rank()
    out = collapse.folder(None, (), (FOLD,), ENTS)(xs)
    (f,) = [x for x in out if x.get("fold")]
    assert out[0] is f and f["fold"][0] == ("hand",) and [m["id"] for m in f["fold"][1]] == list(FOLD)
    assert collapse.words(f["fold"][0]) == "collapsed here by hand; not a link"
    assert collapse.parse(f["id"]) == (("hand",), list(FOLD))
    assert len(out) == len(xs) - len(FOLD) + 1
    apart = {x["id"] for x in out if not x.get("fold")}
    assert {"companies:companies/9429031574990", "companies:companies/9429031575157"} <= apart     # not ticked, not folded
    assert all(x.get("org") for x in out if x["id"].startswith("companies:"))


def test_a_person_named_in_an_address_is_never_folded_by_hand():
    xs = rank()
    persons = ("shareholders:companies/c9/shareholder/9", "directors:p1")
    out = collapse.folder(None, (), (persons, ("directors:p1", people.entity_id(GROUP))), ENTS)(xs)
    assert not [x for x in out if x.get("fold")] and [x["id"] for x in out] == [x["id"] for x in xs]


def test_an_entity_is_in_one_fold_by_hand_and_criteria_leave_the_fold_as_made():
    xs = rank()
    two = ("companies:companies/9429031574990", FOLD[1])
    out = collapse.folder(None, ("number",), (FOLD, two), ENTS)(xs)
    folds = [x for x in out if x.get("fold")]
    assert len(folds) == 1 and len(folds[0]["fold"][1]) == len(FOLD)                  # the second fold kept one member: no fold


def test_the_address_carries_the_folds_and_the_ticked_join_it_as_one():
    ids = ("entity:a,b/c:d", "companies:companies/1", "shareholders:companies/2/shareholder/x")
    boxes = search.FIRST._replace(hand=(ids[:2],))
    qs = urllib.parse.parse_qs(urllib.parse.urlencode(boxes.params()))
    assert search.boxes_of(qs).hand == (ids[:2],)
    qs["hk"] = [ids[1], ids[2], ids[2]]
    again = search.boxes_of(qs)
    assert again.hand == (ids[:2], ids[1:]) and "hk" not in dict(again.params())
    assert search.boxes_of({"hf": ["companies%3A1"], "hk": ["nosuchview:1", "companies:2"]}).hand == ()     # fewer than two
    qs = urllib.parse.parse_qs(urllib.parse.urlencode(again.params()) + "&hk=" + urllib.parse.quote(ids[1]) + "&hk=" + urllib.parse.quote(ids[2]))
    assert search.boxes_of(qs).hand == again.hand                                     # a reload adds no fold twice


def test_the_results_pane_ticks_organisations_and_the_fold_reopens_from_its_address():
    xs = rank()
    rows = {}
    for x in xs:
        if x["group"] is None:
            v, r = x["in_hand"][0]
            rows.setdefault(v.register, {}).setdefault(v.name, (v, []))[1].append(r)
    res = {reg: [(v, len(rs), rs) for v, rs in views.values()] for reg, views in rows.items()}
    res.update({"hidden": {}, "tabs": None})
    ents = {**ENTS, "named": {GROUP: {"any"}}}
    regs = tuple(rows)
    plain = panes.results_pane("Rank Group", res, set(), regs, search.FIRST, ents=ents, fold=collapse.folder(None, (), (), ents))
    ticks = re.findall(r'<input type="checkbox" class="tick" name="hk" value="([^"]*)" form="handfold"', plain)
    assert set(map(unescape, ticks)) >= set(FOLD) and "directors:p1" not in map(unescape, ticks)
    assert "shareholders:companies/c9/shareholder/9" not in map(unescape, ticks) and len(ticks) == 9
    section = plain[plain.index('id="collapse"'):plain.index("</details>", plain.index('id="collapse"'))]
    assert '<form method="get" action="/" id="handfold">' in section and "collapse the ticked into one</button>" in section
    boxes = search.boxes_of(urllib.parse.parse_qs("all=1&" + urllib.parse.urlencode([("hk", m) for m in FOLD])))
    html = panes.results_pane("Rank Group", res, set(), regs, boxes, ents=ents, fold=collapse.folder(None, (), boxes.hand, ents))
    assert html.count('class="hit entity folded"') == 1 and "collapsed here by hand; not a link" in html
    assert re.search(r"<strong>Rank Group Limited via Graeme Hart</strong></a> <span class=\"meta\">collapsed here", html)
    assert 'name="hf" value="' in section or 'name="hf"' in html                         # the fold rides on every form and href
    unfold = unescape(re.search(r'<a class="unfold" href="([^"]*)"', html).group(1))
    assert "hf=" not in unfold and "q=Rank+Group" in unfold
    d = unescape(re.search(r'class="hit entity folded"[^>]* data-dossier="([^"]*)"', html).group(1))
    assert collapse.parse(d) == (("hand",), list(FOLD))
    assert all(s.lstrip().lower().startswith("select") for s in SAID)


def test_the_fold_s_dossier_lists_its_members_as_the_entities_they_are(monkeypatch):
    monkeypatch.setattr(people, "gather", lambda conn, hits, named=None: ENTS)
    found = {x["id"]: x["in_hand"][0][1] for x in rank() if x["group"] is None}
    monkeypatch.setattr(dossier.search, "row", lambda conn, v, k: found.get(f"{v}:{k}"))
    monkeypatch.setattr(dossier, "FOLD_GATHERED", 0)
    x = dossier.gather(None, collapse.fold_id(list(FOLD), {"hand"}))
    page = dossier.pane(x, "Rank Group")
    assert x["kind"] == "fold" and len(x["members"]) == len(FOLD) and x["label"] == "Rank Group Limited via Graeme Hart"
    assert "collapsed here by hand; not a link" in page and "never written" in page
    assert page.count('<a class="row" href="/?q=Rank+Group') == len(FOLD)


def rank_graph():
    """The graph beside the results: the group's node, the five holders, the
    Commerce Commission party, a Rank Group company not ticked, and a person holder, each a row node."""
    n = lambda v, r, order, **kw: {"v": v, "row": r, "matched": True, "centre": False, "order": order, "parent": None, **kw}
    e = ENTS["entity"][GROUP]
    nodes = {people.entity_id(GROUP): n(DONORS, {"key": "g1", "donor": "Rank Group Limited"}, 0, title=e["label"],
                                        entity={**e, "in_hand": ["party_return_donors:g1"]}, lone=False)}
    for i, x in enumerate(rank()[1:], 1):
        if x["group"] is None and x["in_hand"][0][0].name != "directors":
            v, r = x["in_hand"][0]
            nodes[x["id"]] = n(v, r, i, lone=True)
    target = "companies:companies/9429031575157"
    edges = [{"kind": "role", "a": f"shareholders:companies/c{i}/shareholder/{i}", "b": target, "label": "shareholder of",
              "cite": "x", "rule": None} for i in range(1, 6)]
    rows = {"party_return_donors:g1": {"v": DONORS, "row": {"key": "g1", "donor": "Rank Group Limited"}}}
    return {"nodes": nodes, "edges": edges, "people": True, "inside": 0, "decisions": {}, "lineage": []}, rows


def test_the_graph_draws_the_fold_by_hand_as_one_node_with_the_same_words():
    from products.board import graph
    g, rows = rank_graph()
    out = collapse.fold_graph(None, g, (), rows, (FOLD,))
    (fid,) = [k for k, x in out["nodes"].items() if x.get("fold")]
    f = out["nodes"][fid]["fold"]
    assert fid == "fold:" + people.entity_id(GROUP) and f["members"] == list(FOLD)
    assert f["words"] == "collapsed here by hand; not a link" and out["nodes"][fid]["title"] == "Rank Group Limited via Graeme Hart"
    assert "companies:companies/9429031575157" in out["nodes"] and "shareholders:companies/c9/shareholder/9" in out["nodes"]
    assert len(out["nodes"]) == len(g["nodes"]) - len(FOLD) + 1
    assert len(out["edges"]) == 1 and out["inside"] == 0                               # the five holders' edges, one line from the fold
    assert collapse.parse(f["dossier"]) == (("hand",), list(FOLD))
    out.update({"drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS}, "not_drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS},
                "matched_total": len(g["nodes"]), "unresolved": 0, "centre": ""})
    data = graph.answer(out, "Rank Group", search.FIRST._replace(hand=(FOLD,)))
    (node,) = [x for x in data["nodes"] if x.get("kind") == "fold"]
    assert node["words"] == "collapsed here by hand; not a link" and node["dossier"].startswith("fold:hand:")
    assert "collapsed here by hand; not a link" in graph.svg(out, "Rank Group", search.FIRST)
    persons = ("shareholders:companies/c9/shareholder/9", people.entity_id(GROUP))
    assert collapse.fold_graph(None, g, (), rows, (persons,)) is g                   # a person node is never folded by hand
    assert all(s.lstrip().lower().startswith("select") for s in SAID)


def test_a_saved_path_keeps_the_fold_and_one_saved_before_opens_as_it_did():
    from products.board import state
    boxes = search.FIRST._replace(hand=(FOLD,))
    saved = urllib.parse.urlencode(boxes.params())
    page = panes.paths_pane([{"name": "rank", "query": "Rank Group", "path": "companies:companies/1", "made_at": None, "boxes": saved},
                             {"name": "old", "query": "doe", "path": "directors:k", "made_at": None}])
    rank_href, old_href = (unescape(h) for h in re.findall(r'<a class="row" href="([^"]*)">', page))
    assert search.boxes_of(urllib.parse.parse_qs(urllib.parse.urlsplit(rank_href).query)).hand == (FOLD,)
    assert old_href == "/?q=doe&p=directors%3Ak"                                      # a path saved before: no boxes, as it was
    sql = state.tables_sql("board")
    assert "ADD COLUMN IF NOT EXISTS boxes text NOT NULL DEFAULT ''" in sql
    statements = re.sub(r"--[^\n]*", "", sql)
    assert not re.search(r"\b(delete|update|drop)\b", statements, re.I)                # only ever added to
