"""The people state (ruling 105), on a fixture: rows in one group become one
node, edges are lifted to their group ends with duplicates dropped and their
rows kept, a row in no group is a lone row, a near link is one hop and
dashed with its reason, a contested group is marked, a decision shows on its
line, and a suppressed row is never gathered (hard limit 16)."""
import pytest

from products.board import catalogue as cat
from products.board import graph, people


def node(view, key, matched, order, **row):
    return {"v": cat.BY_NAME[view], "row": {"key": key, **row}, "matched": matched, "centre": False, "order": order, "parent": None}


def ref(view, key):
    return f"{cat.BY_NAME[view].register}:{key}"


D1, D2, D3, S1 = "c/1/director/a", "c/2/director/b", "c/3/director/c", "c/4/director/s"


def rows_graph():
    g = {"nodes": {}, "edges": [], "drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS}, "not_drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS},
         "matched_total": 4, "unresolved": 0, "centre": ""}
    g["nodes"]["directors:" + D1] = node("directors", D1, True, 0, full_name="Jane Mary Hart")
    g["nodes"]["directors:" + D2] = node("directors", D2, True, 1, full_name="Jane Hart")
    g["nodes"]["directors:" + D3] = node("directors", D3, True, 2, full_name="Joe Hart")
    g["nodes"]["directors:" + S1] = node("directors", S1, True, 3, full_name="Hidden Hart", suppressed=True)
    g["nodes"]["companies:c/9"] = node("companies", "c/9", False, 4, name="ACME LIMITED")
    for d in (D1, D2, D3, S1):
        g["edges"].append({"kind": "role", "a": "directors:" + d, "b": "companies:c/9", "label": "director of", "cite": "directors:" + d, "rule": None})
    g["drawn"]["role"] = 4
    return g


@pytest.fixture
def reads(monkeypatch):
    grp = {ref("directors", D1): ("G1", True), ref("directors", D2): ("G1", True), ref("directors", S1): ("G1", True)}
    members = {"G1": [{"ref": ref("directors", k), "view": "directors", "key": k, "register": "companies", "name": n, "kind": "person"}
                      for k, n in ((D1, "Jane Mary Hart"), (D2, "Jane Hart"), (S1, "Hidden Hart"))]
                     + [{"ref": "mp_interests:x", "view": "mp_interests", "key": "x", "register": "mp_interests", "name": "Jane M Hart", "kind": "person"}]}
    far = ref("directors", "c/8/director/f")
    nears = [{"mine": ref("directors", D3), "row_a": ref("directors", D3), "row_b": far, "rule": "name-only@1",
              "reason": "same first and last name, no middle", "decision": "", "total": 12}]
    monkeypatch.setattr(people, "groups_of", lambda conn, refs: {r: grp[r] for r in refs if r in grp})
    monkeypatch.setattr(people, "members_of", lambda conn, gids: {g: members[g] for g in gids})
    monkeypatch.setattr(people, "suppressed_refs", lambda conn, ms: {m["ref"] for m in ms if m["name"] == "Hidden Hart"})
    monkeypatch.setattr(people, "near_of", lambda conn, refs: [l for l in nears if l["mine"] in refs])
    monkeypatch.setattr(people, "resolve_refs", lambda conn, refs, m=None: {
        far: (cat.BY_NAME["directors"], {"key": "c/8/director/f", "full_name": "Joseph Hart"})} if far in refs else {})
    monkeypatch.setattr(people, "decisions_of", lambda conn, refs: [
        {"row_a": ref("directors", D3), "row_b": far, "verdict": "not the same", "made_by": "review-agent@2", "made_at": None}])
    return grp


def test_rows_in_one_group_are_one_node_labelled_by_the_fullest_shown_name(reads):
    p = people.fold(None, rows_graph())
    e = p["nodes"]["entity:G1"]
    assert e["entity"]["in_hand"] == ["directors:" + D1, "directors:" + D2]
    assert e["title"] == "Jane Mary Hart"                    # three words beat two; the suppressed row's name never counts
    assert e["entity"]["count"] == "3 rows, 2 registers" and e["entity"]["contested"]
    assert "directors:" + D1 not in p["nodes"] and "directors:" + D2 not in p["nodes"]


def test_a_row_in_no_group_is_a_lone_row_and_a_suppressed_row_is_kept_apart(reads):
    p = people.fold(None, rows_graph())
    assert p["nodes"]["directors:" + D3]["lone"] and not p["nodes"]["directors:" + D3].get("entity")
    s = p["nodes"]["directors:" + S1]
    assert s["apart"] and not s["lone"] and not s.get("entity")
    assert "Hidden Hart" not in repr({k: v for k, v in p["nodes"].items() if k != "directors:" + S1})


def test_edges_are_lifted_to_their_group_ends_duplicates_dropped_rows_kept(reads):
    p = people.fold(None, rows_graph())
    roles = [e for e in p["edges"] if e["kind"] == "role"]
    ends = sorted((e["a"], e["b"]) for e in roles)
    assert ends == sorted([("entity:G1", "companies:c/9"), ("directors:" + D3, "companies:c/9"), ("directors:" + S1, "companies:c/9")])
    lifted = next(e for e in roles if e["a"] == "entity:G1")
    assert [r[2] for r in lifted["rows"]] == ["directors:" + D1, "directors:" + D2]     # which rows: its pane lists them
    assert p["drawn"]["role"] == 3


def test_near_is_one_hop_dashed_with_its_reason_and_never_merged(reads):
    p = people.fold(None, rows_graph())
    near = [e for e in p["edges"] if e["kind"] == people.NEAR]
    assert len(near) == 1 and near[0]["label"] == "same first and last name, no middle"
    assert near[0]["a"] == "directors:" + D3 and near[0]["b"] == "directors:c/8/director/f"
    assert p["nodes"]["directors:c/8/director/f"]["lone"]          # pulled in as its own node
    assert p["not_drawn"][people.NEAR] == 2                         # 12 near links, 10 drawn per row
    assert p["decisions"][tuple(sorted(("directors:" + D3, "directors:c/8/director/f")))][0]["verdict"] == "not the same"
    lns = graph.lines(p)
    data = graph.answer(p, "hart")
    e = next(x for x in data["edges"] if x["kind"] == people.NEAR)
    assert e["dashed"] and "not the same" in e["title"]
    assert not any(x["kind"] == people.CONFIRMED for x in data["edges"])     # confirmed links live inside an entity
    assert len(lns) == len(data["edges"])


def test_without_groups_every_row_is_lone_and_the_rows_graph_is_unchanged(monkeypatch):
    for f in ("groups_of", "near_of", "decisions_of", "resolve_refs"):
        monkeypatch.setattr(people, f, lambda *a, **k: {} if f in ("groups_of", "resolve_refs") else [])
    monkeypatch.setattr(people, "members_of", lambda conn, gids: {})
    monkeypatch.setattr(people, "suppressed_refs", lambda conn, ms: set())
    g = rows_graph()
    p = people.fold(None, g)
    assert set(p["nodes"]) == set(g["nodes"]) and len(p["edges"]) == len(g["edges"])
    assert g["nodes"]["directors:" + D1].get("lone") is None              # the rows graph itself is never written


def test_the_fullest_name_is_most_words_then_most_letters_then_first():
    assert people.fullest(["Jane Hart", "Jane Mary Hart", "Jane Marie Hart", ""]) == "Jane Marie Hart"
    assert people.fullest(["A B", "A B"]) == "A B" and people.fullest([]) == ""
