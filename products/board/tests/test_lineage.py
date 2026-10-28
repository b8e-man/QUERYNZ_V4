"""The links lane's related grade drawn as a lineage frame (ruling 106 (2)),
on a fixture: a chain of three companies is one frame in date order, each
company its own node in both states, never one entity; the people on both
drawn once inside the frame, joined to both by their own rows' relation; a
suppressed person counted and never named (hard limit 16); the near colour
and dash kept for near alone; the row's and the entity's panes list the
relation and the people under their own heading."""
import pytest

from products.board import catalogue as cat
from products.board import graph, lineage, links_view, panes, people, search

A, B, C = "companies/1", "companies/2", "companies/3"          # registered 1987, 2013, 2020
RA, RB, RC = (f"companies:{k}" for k in (A, B, C))
DA, DB, DC = "companies/1/director/p", "companies/2/director/q", "companies/3/director/r"     # one person on all three
SA, SB = "companies/1/director/s", "companies/2/director/t"                                  # a suppressed one on A and B
G_PERSON, G_HIDDEN = "companies:companies/9/director/g", "companies:companies/9/director/h"


def link(earlier, later, dates, shared, n=None):
    a, b = sorted((earlier, later))
    return {"row_a": a, "row_b": b, "rule": "successor-name@1", "grade": "related", "relation": "succeeded by",
            "reason": None, "decision": None,
            "evidence": {"earlier": earlier, "later": later, "relation": "succeeded by", "registered": dates,
                         "order": "by registration date", "shared_people": n or len(shared),
                         "shared_rows": [{"earlier": e, "later": l, "group": g, "name": "NOT FROM HERE"} for e, l, g in shared]}}


LINKS = [link(RB, RC, ["2013-05-01", "2020-02-02"], [(f"companies:{DB}", f"companies:{DC}", G_PERSON)]),
         link(RA, RB, ["1987-01-01", "2013-05-01"], [(f"companies:{DA}", f"companies:{DB}", G_PERSON),
                                                     (f"companies:{SA}", f"companies:{SB}", G_HIDDEN)])]
ROWS = {RA: ("companies", {"key": A, "name": "ANDERSON TRUSTEE COMPANY LIMITED", "registered_on": "1987-01-01"}),
        RB: ("companies", {"key": B, "name": "ANDERSON TRUSTEE COMPANY (2013) LIMITED", "registered_on": "2013-05-01"}),
        RC: ("companies", {"key": C, "name": "ANDERSON TRUSTEE COMPANY (2020) LIMITED", "registered_on": "2020-02-02"}),
        f"companies:{DA}": ("directors", {"key": DA, "full_name": "Pat Lane", "entity_key": A}),
        f"companies:{DB}": ("directors", {"key": DB, "full_name": "Pat Lane", "entity_key": B}),
        f"companies:{DC}": ("directors", {"key": DC, "full_name": "Pat Lane", "entity_key": C}),
        f"companies:{SA}": ("directors", {"key": SA, "full_name": "Sealed Person", "entity_key": A, "suppressed": True}),
        f"companies:{SB}": ("directors", {"key": SB, "full_name": "Sealed Person", "entity_key": B, "suppressed": True})}


def resolve_refs(conn, refs, members=None):
    return {r: (cat.BY_NAME[ROWS[r][0]], ROWS[r][1]) for r in refs if r in ROWS}


@pytest.fixture
def reads(monkeypatch):
    asked = []

    def related_of(conn, refs):
        asked.append(sorted(refs))
        return [l for l in LINKS if l["row_a"] in refs or l["row_b"] in refs]
    monkeypatch.setattr(lineage, "related_of", related_of)
    return asked


def rows_graph(matched=RB, with_director=True):
    """graph.build's rows graph by hand: one matched company, and the shared person's row on it already drawn."""
    g = {"nodes": {}, "edges": [], "drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS},
         "not_drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS}, "matched_total": 1, "unresolved": 0, "centre": ""}
    view, row = ROWS[matched]
    g["nodes"][f"{view}:{row['key']}"] = {"v": cat.BY_NAME[view], "row": row, "matched": True, "centre": False, "order": 0, "parent": None}
    seen = set()

    def add_node(v, r, parent):
        nid = f"{v.name}:{r['key']}"
        if nid not in g["nodes"]:
            g["nodes"][nid] = {"v": v, "row": r, "matched": False, "centre": False, "order": len(g["nodes"]), "parent": parent}
        return nid

    def add_edge(kind, a, b, label, cite, rule=None, **extra):
        k = (kind, min(a, b), max(a, b), label, rule)
        if k not in seen:
            seen.add(k)
            g["edges"].append({"kind": kind, "a": a, "b": b, "label": label, "cite": cite, "rule": rule, **extra})
            g["drawn"][kind] += 1
    if with_director:
        v, r = ROWS[f"companies:{DB}"]
        add_edge("role", add_node(cat.BY_NAME[v], r, f"companies:{B}"), f"companies:{B}", "director of", f"directors:{DB}")
    return g, add_node, add_edge


def drawn(matched=RB):
    g, add_node, add_edge = rows_graph(matched)
    lineage.draw(None, g, add_node, add_edge, resolve_refs)
    return g


def test_a_chain_is_one_frame_in_date_order_labelled_with_the_relation_and_years(reads):
    g = drawn()
    assert len(g["lineage"]) == 1
    f = g["lineage"][0]
    assert f["companies"] == [f"companies:{A}", f"companies:{B}", f"companies:{C}"]          # 1987, 2013, 2020
    assert f["label"] == "succeeded by · 1987 → 2013 → 2020" and f["id"] == lineage.FRAME + RA
    assert len(reads) == 2 and reads[1] == [RA, RC]           # the rows in hand at once, then the chain's two new ends
    lines = [(e["a"], e["b"], e["label"]) for e in g["edges"] if e["kind"] == lineage.KIND]
    assert sorted(lines) == [(f"companies:{A}", f"companies:{B}", "succeeded by"), (f"companies:{B}", f"companies:{C}", "succeeded by")]


def test_the_frame_order_is_the_evidence_s_not_the_row_order():
    flipped = link(RC, RA, ["1999-01-01", "2001-01-01"], [])            # row_a is the later here
    f = lineage.frames([flipped])[0]
    assert f["companies"] == [RC, RA] and lineage.ends(flipped) == (RC, RA)


def test_the_shared_person_is_one_node_joined_to_every_company_by_its_own_rows(reads):
    g = drawn()
    f = g["lineage"][0]
    assert f["people"] == [f"directors:{DA}"]                 # the row on the earliest company stands for all three,
    assert f"directors:{DB}" not in g["nodes"] and f"directors:{DC}" not in g["nodes"]     # the one drawn before merged in
    assert g["nodes"][f"directors:{DA}"]["stands_for"] == [f"directors:{DA}", f"directors:{DB}", f"directors:{DC}"]
    roles = sorted((e["b"], e["cite"]) for e in g["edges"] if e["kind"] == "role")
    assert roles == [(f"companies:{A}", f"directors:{DA}"), (f"companies:{B}", f"directors:{DB}"), (f"companies:{C}", f"directors:{DC}")]
    assert all(e["a"] == f"directors:{DA}" for e in g["edges"] if e["kind"] == "role")


def test_a_grown_hop_draws_the_shared_person_as_the_node_the_first_answer_drew(reads):
    first = drawn(RB)["lineage"][0]["people"]
    g, add_node, add_edge = rows_graph(RC, with_director=False)       # the hop of the latest company, its own row drawn first
    v, r = ROWS[f"companies:{DC}"]
    add_edge("role", add_node(cat.BY_NAME[v], r, RC), RC, "director of", f"directors:{DC}")
    lineage.draw(None, g, add_node, add_edge, resolve_refs)
    assert g["lineage"][0]["people"] == first and f"directors:{DC}" not in g["nodes"]


def test_a_suppressed_person_is_counted_and_never_named(reads):
    g = drawn()
    f = g["lineage"][0]
    assert f["hidden"] == 1
    assert "Sealed Person" not in repr(g) and "NOT FROM HERE" not in repr(g)      # nor any name from the evidence
    data = graph.answer(g, "anderson")
    assert "Sealed Person" not in graph.to_json(data) and "NOT FROM HERE" not in graph.to_json(data)


def test_the_answer_draws_a_frame_parent_with_the_companies_left_to_right_and_the_people_below(reads):
    data = graph.answer(drawn(), "anderson")
    frame = next(n for n in data["nodes"] if n["kind"] == "lineage")
    assert data["nodes"][0] is frame                                  # a parent before its children
    kids = {n["id"]: n for n in data["nodes"] if n.get("parent") == frame["id"]}
    assert set(kids) == {f"companies:{A}", f"companies:{B}", f"companies:{C}", f"directors:{DA}"}
    xs = [kids[f"companies:{k}"]["x"] for k in (A, B, C)]
    assert xs == sorted(xs) and len(set(xs)) == 3
    assert len({kids[f"companies:{k}"]["y"] for k in (A, B, C)}) == 1 and kids[f"directors:{DA}"]["y"] > kids[f"companies:{A}"]["y"]
    assert frame["title"].startswith("succeeded by") and frame["colour"] == lineage.COLOUR
    assert kids[f"directors:{DA}"]["stands_for"] == 3
    edge = next(e for e in data["edges"] if e["kind"] == lineage.KIND)
    assert not edge["dashed"] and edge["colour"] != graph.KIND[graph.NEAR][0]


def test_the_svg_picture_still_lays_out_a_line_between_two_far_rows(reads):
    g = drawn()
    html = graph.pane(g, "anderson")                                  # the A-to-B line joins no matched row when B is not matched
    assert "<svg" in html and "lineage" in html


def test_the_entity_state_keeps_each_company_its_own_node_and_the_person_once(reads, monkeypatch):
    grp = {RA: ("GA", False), RB: ("GB", False), f"companies:{DA}": ("GP", False), f"companies:{DB}": ("GP", False),
           f"companies:{DC}": ("GP", False)}
    members = {"GA": [{"ref": RA, "view": "companies", "key": A, "register": "companies", "name": ROWS[RA][1]["name"], "kind": "organisation"}],
               "GB": [{"ref": RB, "view": "companies", "key": B, "register": "companies", "name": ROWS[RB][1]["name"], "kind": "organisation"}],
               "GP": [{"ref": f"companies:{k}", "view": "directors", "key": k, "register": "companies", "name": "Pat Lane", "kind": "person"}
                      for k in (DA, DB, DC)]}
    monkeypatch.setattr(people, "groups_of", lambda conn, refs: {r: grp[r] for r in refs if r in grp})
    monkeypatch.setattr(people, "members_of", lambda conn, gids: {x: members[x] for x in gids})
    monkeypatch.setattr(people, "suppressed_refs", lambda conn, ms: set())
    monkeypatch.setattr(people, "near_of", lambda conn, refs: [])
    monkeypatch.setattr(people, "decisions_of", lambda conn, refs: [])
    p = people.fold(None, drawn())
    f = p["lineage"][0]
    assert f["companies"] == ["entity:GA", "entity:GB", f"companies:{C}"]     # two entities and a lone row, never one node
    assert len(set(f["companies"])) == 3 and f["people"] == ["entity:GP"]
    data = graph.answer(p, "anderson")
    kids = [n["id"] for n in data["nodes"] if n.get("parent") == f["id"]]
    assert sorted(kids) == sorted(f["companies"] + ["entity:GP"])
    assert sum(1 for e in data["edges"] if e["kind"] == lineage.KIND) == 2


def test_the_near_style_is_near_s_alone_and_the_frame_passes_the_floor():
    colour, dash = graph.KIND[lineage.KIND]
    assert not dash and colour != graph.KIND[graph.NEAR][0]
    assert all(panes.apart(colour, c) >= panes.EDGE_APART for k, c, _ in cat.EDGE_KINDS if k != lineage.KIND)
    assert panes.contrast(colour, "#161a20") >= panes.EDGE_FLOOR
    fill = panes.over(colour, "#161a20", lineage.FILL_OPACITY)        # the frame's fill, where the labels inside it sit
    assert panes.contrast("#e8eaed", fill) >= panes.TEXT_FLOOR


def test_links_of_keeps_related_apart_from_near(monkeypatch):
    rows = [dict(LINKS[1], link_id=1), {"row_a": RA, "row_b": "companies:companies/8", "rule": "company-name@1", "grade": "near",
                                        "relation": None, "evidence": {}, "reason": "two companies under one name", "decision": None},
            {"row_a": RA, "row_b": "companies:companies/7", "rule": "x@1", "grade": "odd", "evidence": {}, "reason": None}]
    monkeypatch.setattr(links_view, "built", lambda conn: True)
    monkeypatch.setattr(links_view.db, "rows", lambda conn, sql, params=None: rows if "from pub.links" in sql else [])
    monkeypatch.setattr(links_view.db, "has_relation", lambda conn, s, t: False)
    got = links_view.links_of(None, RA)
    assert [l["other"] for l in got["related"]] == [RB] and got["related"][0]["relation"] == "succeeded by"
    assert [l["other"] for l in got["near"]] == ["companies:companies/8", "companies:companies/7"] and not got["confirmed"]


def test_the_results_pane_says_related_in_a_word_for_an_entity_with_a_related_link(monkeypatch):
    members = {"GA": [{"ref": RA, "view": "companies", "key": A, "register": "companies", "name": ROWS[RA][1]["name"], "kind": "organisation"}],
               "GC": [{"ref": RC, "view": "companies", "key": C, "register": "companies", "name": ROWS[RC][1]["name"], "kind": "organisation"}]}
    monkeypatch.setattr(people, "groups_of", lambda conn, refs: {r: {RA: ("GA", False), RC: ("GC", False)}[r] for r in refs if r in (RA, RC)})
    monkeypatch.setattr(people, "members_of", lambda conn, gids: {x: members[x] for x in gids})
    monkeypatch.setattr(people, "suppressed_refs", lambda conn, ms: set())
    asked = []
    monkeypatch.setattr(lineage, "related_refs", lambda conn, refs: asked.append(sorted(refs)) or {RA: "succeeded by"})
    companies = cat.BY_NAME["companies"]
    ents = people.gather(None, [(companies, ROWS[RA][1]), (companies, ROWS[RC][1])])
    assert asked == [[RA, RC]]                                            # one query for every entity's rows
    assert ents["entity"]["GA"]["related"] == ["succeeded by"] and ents["entity"]["GC"]["related"] == []
    a = panes.entity_hit("anderson", ents["entity"]["GA"], [], ())
    c = panes.entity_hit("anderson", ents["entity"]["GC"], [], ())
    assert '<span class="lineage"' in a and ">related</span>" in a and "succeeded by" in a
    assert "related" not in c


def test_the_row_pane_and_the_entity_pane_list_related_links_under_their_own_heading():
    resolve = lambda ref: (cat.BY_NAME[ROWS[ref][0]], ROWS[ref][1]) if ref in ROWS else None
    html = panes.related_section([LINKS[1]], {RB}, "anderson", [], resolve)
    assert "Related companies" in html and "<strong>succeeded by</strong> this company (2013)" in html
    assert "ANDERSON TRUSTEE COMPANY LIMITED</a> (1987)" in html
    assert "Pat Lane" in html and "1 whose name is suppressed" in html and "Sealed Person" not in html and "NOT FROM HERE" not in html
    earlier = panes.related_section([LINKS[1]], {RA}, "anderson", [], resolve)
    assert "this company (1987) <strong>succeeded by</strong>" in earlier
    links = {"built": True, "confirmed": [], "near": [], "related": [{"other": RB, "register": "companies", "rule": "successor-name@1",
                                                                       "link": LINKS[1], "decisions": []}]}
    pane = panes.links_section(links, {}, "anderson", [], resolve)
    assert "Related companies" in pane and "none found" not in pane and "<strong>near</strong>" not in pane


def test_a_person_whose_two_rows_are_both_drawn_is_merged_into_the_matched_one(reads):
    g, add_node, add_edge = rows_graph()
    v, r = ROWS[f"companies:{DA}"]
    g["nodes"][f"directors:{DA}"] = {"v": cat.BY_NAME[v], "row": r, "matched": True, "centre": False, "order": 9, "parent": None}
    g["edges"].append({"kind": "role", "a": f"directors:{DA}", "b": "companies:x", "label": "x", "cite": f"directors:{DA}", "rule": None})
    lineage.draw(None, g, add_node, add_edge, resolve_refs)
    assert f"directors:{DA}" in g["nodes"] and f"directors:{DB}" not in g["nodes"]           # the earliest row stands for both
    assert g["nodes"][f"directors:{DA}"]["matched"]
    assert g["lineage"][0]["people"] == [f"directors:{DA}"]
    assert not any(f"directors:{DB}" in (e["a"], e["b"]) for e in g["edges"])


def test_one_company_succeeded_by_two_is_not_labelled_a_chain(reads, monkeypatch):
    two = [link(RA, RB, ["1987-01-01", "2011-02-08"], [(f"companies:{DA}", f"companies:{DB}", G_PERSON)]),
           link(RA, RC, ["1987-01-01", "2013-04-15"], [(f"companies:{DA}", f"companies:{DC}", G_PERSON)])]
    monkeypatch.setattr(lineage, "related_of", lambda conn, refs: [l for l in two if l["row_a"] in refs or l["row_b"] in refs])
    f = drawn(RA)["lineage"][0]
    assert f["companies"] == [RA, RB, RC]                    # a company ref and its node id are one string in this view
    assert f["label"] == "succeeded by \u00b7 1987 \u2192 2011, 2013"


def test_a_result_row_with_a_related_link_says_so_in_a_word_and_one_without_does_not():
    v = cat.BY_NAME["companies"]
    marked = panes.hit("anderson", v, dict(ROWS[RA][1], _related="succeeded by"), ())
    plain = panes.hit("anderson", v, dict(ROWS[RC][1]), ())
    assert ">related</span>" in marked and "a related company: succeeded by" in marked
    assert "related" not in plain


def test_many_people_wrap_into_rows_whose_labels_never_meet():
    f = {"companies": ["a", "b"], "people": [f"p{i}" for i in range(12)]}
    at = lineage.places([f, {"companies": ["c", "d"], "people": []}], 500, 1000)
    rows = {}
    for p in f["people"]:
        rows.setdefault(at[p][1], []).append(at[p][0])
    assert len(rows) == 3 and all(len(r) <= lineage.PER_ROW for r in rows.values())
    assert all(b - a >= 96 + 8 for r in rows.values() for a, b in zip(sorted(r), sorted(r)[1:]))     # a label's width and a margin
    assert at["c"][1] > max(y for y in rows)                                                           # the next frame below the last row
    assert at["a"][0] < at["b"][0] and min(rows) > at["a"][1]
