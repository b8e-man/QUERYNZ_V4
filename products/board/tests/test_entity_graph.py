"""Ruling 117 (4), on a fixture shaped as Lloyd Budd's rows: the entity
graph draws one entity with the same connections whichever of its rows it
is opened from (a charity officer's row named the charity, a director's row
the company, and the entity's one connection swapped between them), its
node stands for its group by the group's first row in byte order, and the
name fold draws the same entity with the same connections, named by its
member, never by its place in the answer."""
import pytest

from products.board import catalogue as cat
from products.board import collapse, graph, people

V = cat.BY_NAME
G = "charities:charities/officers/1"
OFFICER = {"key": "charities/officers/1", "charity_key": "charities/1", "full_name": "Lloyd Budd", "role": "Trustee"}
DIRECTOR = {"key": "companies/9/director/a", "entity_key": "companies/9", "full_name": "Lloyd Sam BUDD", "suppressed": False}
SHARE = {"key": "companies/9/shareholder/b", "entity_key": "companies/9", "name": "Lloyd Sam BUDD", "suppressed": False}
CELEBRANT = {"key": "gazette/2020-go1/celebrant/c", "surname": "Budd", "given_names": "Lloyd"}
FAR = {("charities", "key", "charities/1"): {"key": "charities/1", "name": "Keystone Trust"},
       ("companies", "key", "companies/9"): {"key": "companies/9", "name": "BUDD CONSULTANCY LIMITED"}}
ROWS = {("charity_officers", OFFICER["key"]): OFFICER, ("directors", DIRECTOR["key"]): DIRECTOR,
        ("shareholders", SHARE["key"]): SHARE, ("gazette_celebrants", CELEBRANT["key"]): CELEBRANT}
MEMBERS = [{"ref": f"charities:{OFFICER['key']}", "view": "charity_officers", "key": OFFICER["key"], "register": "charities",
            "name": "Lloyd Budd", "kind": "person"},
           {"ref": f"companies:{DIRECTOR['key']}", "view": "directors", "key": DIRECTOR["key"], "register": "companies",
            "name": "Lloyd Sam BUDD", "kind": "person"},
           {"ref": f"companies:{SHARE['key']}", "view": "shareholders", "key": SHARE["key"], "register": "companies",
            "name": "Lloyd Sam BUDD", "kind": "person"}]
NEAR = f"gazette:{CELEBRANT['key']}"


@pytest.fixture
def reads(monkeypatch):
    by_ref = {m["ref"]: m for m in MEMBERS}
    monkeypatch.setattr(graph.db, "pub_views", lambda conn: {v.name for v in cat.VIEWS})
    monkeypatch.setattr(graph.search, "row", lambda conn, view, key: ROWS.get((view, key)))
    monkeypatch.setattr(graph, "_rows", lambda conn, v, col, value, limit: (1, [FAR[(v.name, col, value)]]) if (v.name, col, value) in FAR else (0, []))
    monkeypatch.setattr(graph, "INCOMING", {})
    monkeypatch.setattr(graph.lineage, "draw", lambda *a, **k: None)
    monkeypatch.setattr(people, "groups_of", lambda conn, refs: {r: (G, False) for r in refs if r in by_ref})
    monkeypatch.setattr(people, "members_of", lambda conn, gids: {g: list(MEMBERS) for g in gids})
    monkeypatch.setattr(people, "suppressed_refs", lambda conn, ms: set())
    monkeypatch.setattr(people, "resolve_refs", lambda conn, refs, m=None: {
        r: (V[by_ref[r]["view"]], ROWS[(by_ref[r]["view"], by_ref[r]["key"])]) if r in by_ref else (V["gazette_celebrants"], CELEBRANT)
        for r in refs if r in by_ref or r == NEAR})
    monkeypatch.setattr(people, "rows_by_key", lambda conn, view, keys: {k: ROWS[(view, k)] for k in keys if (view, k) in ROWS})
    monkeypatch.setattr(people, "near_of", lambda conn, refs: [
        {"mine": MEMBERS[0]["ref"], "row_a": MEMBERS[0]["ref"], "row_b": NEAR, "rule": "name-only@1", "reason": "same name",
         "decision": "", "total": 1}] if MEMBERS[0]["ref"] in refs else [])
    monkeypatch.setattr(people, "decisions_of", lambda conn, refs: [])
    monkeypatch.setattr(collapse, "keys", lambda conn, units, criteria: {
        u["id"]: {"name": {"lloyd budd"}} for u in units if u["group"] == G or u["id"].startswith("gazette_celebrants:")})


def drawn(g):
    """(nodes {id: the view that stands for it}, edges {(a, b, kind)})."""
    return ({nid: n["v"].name for nid, n in g["nodes"].items()},
            {(e["a"], e["b"], e["kind"]) for e in g["edges"]})


CENTRES = ["charity_officers:" + OFFICER["key"], "directors:" + DIRECTOR["key"], "shareholders:" + SHARE["key"]]


def test_every_row_of_the_entity_opens_the_same_entity_with_the_same_connections(reads):
    seen = [drawn(graph.build(None, "", centre=c, people=True)) for c in CENTRES]
    assert seen[0] == seen[1] == seen[2]
    nodes, edges = seen[0]
    e = people.entity_id(G)
    assert nodes[e] == "charity_officers"                      # the group's first row by ref: charities: before companies:
    assert {(e, "charities:charities/1", "role"), (e, "companies:companies/9", "role")} <= edges


def test_the_rows_state_still_draws_one_row_s_hop():
    """The fix is the entity state's: a row opened in the rows state draws its own hop, as before."""
    assert graph.group_rows.__doc__ and "entity state" in graph.group_rows.__doc__


def test_the_name_fold_draws_the_same_entity_with_the_same_connections(reads):
    for c in CENTRES:
        plain = graph.build(None, "", centre=c, people=True)
        folded = graph.build(None, "", centre=c, people=True, collapse=("name",))
        pn, pe = drawn(plain)
        fn, fe = drawn(folded)
        fid = collapse.PREFIX + people.entity_id(G)
        assert fid in fn and fn[fid] == pn[people.entity_id(G)]                # named by its entity, the same row standing for it
        members = set(folded["nodes"][fid]["fold"]["members"])
        to = {nid: (fid if nid in members else nid) for nid in pn}
        assert set(to.values()) == set(fn)                                      # every node drawn, folded or as it was
        assert {(to[a], to[b], k) for a, b, k in pe if to[a] != to[b]} == fe   # every connection, lifted to its folded ends
        assert members == {people.entity_id(G), "gazette_celebrants:" + CELEBRANT["key"]}


def test_a_fold_is_named_by_the_member_that_stands_for_it_never_by_its_place():
    assert collapse.stands_for(["gazette_celebrants:x", "entity:b", "entity:a"]) == "entity:a"
    assert collapse.stands_for(["gazette_celebrants:y", "candidates:z"]) == "candidates:z"


def test_a_search_drawing_his_rows_in_any_order_stands_the_entity_for_its_first_row_by_ref(reads, monkeypatch):
    """The search's own order (the companies before the charities in the catalogue) never picks the entity's row."""
    for order in ([("directors", DIRECTOR), ("charity_officers", OFFICER)], [("shareholders", SHARE)]):
        monkeypatch.setattr(graph.search, "search", lambda conn, q, **kw: {V[v].register: [(V[v], 1, [r])] for v, r in order})
        g = graph.build(None, "lloyd budd", people=True)
        assert g["nodes"][people.entity_id(G)]["v"].name == "charity_officers", order
