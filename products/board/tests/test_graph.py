"""The graph tab, pure: relations are catalogue data and never an address;
the layout is deterministic; the picture is SVG with no script, every node an
href that re-centres and every edge label an href to the asserting row; the
key names each colour and counts its edges; a suppressed name never shows."""
import re

from products.board import catalogue as cat
from products.board import graph, search

ADDRESSISH = ("address", "street", "suburb", "residential", "postal")


def test_every_relation_is_typed_and_names_a_catalogued_view_and_never_an_address():
    assert not any("address" in k for k, _, _ in cat.EDGE_KINDS)
    assert set(cat.RELATION_KINDS) < {k for k, _, _ in cat.EDGE_KINDS}
    n = 0
    for v in cat.VIEWS:
        for rel in v.relations:
            n += 1
            assert rel.kind in cat.RELATION_KINDS, (v.name, rel)
            assert rel.view in cat.BY_NAME and rel.view != "company_addresses", (v.name, rel)
            assert not any(w in c for c in (rel.column, rel.to_column) for w in ADDRESSISH), (v.name, rel)
            assert rel.label, (v.name, rel)
    assert not cat.BY_NAME["company_addresses"].relations
    assert n >= 20
    kinds = {rel.kind for v in cat.VIEWS for rel in v.relations}
    assert kinds == set(cat.RELATION_KINDS)          # every type the brief names has at least one line


def test_the_relations_the_ruling_names_are_declared():
    def has(view, kind, far):
        return any(r.kind == kind and r.view == far for r in cat.BY_NAME[view].relations)
    assert has("party_return_donors", "money", "party_return_totals") and has("candidate_return_donors", "money", "candidate_return_totals")
    assert has("disclosures", "money", "parties")
    assert has("directors", "role", "companies") and has("shareholders", "role", "companies")
    assert has("charity_officers", "role", "charities") and has("society_officers", "role", "societies")
    assert has("party_board_roles", "role", "parties")
    assert has("candidates", "candidacy", "parties") and has("candidates", "candidacy", "electorates")
    assert has("mp_interests", "declaration", "mp_interest_returns")
    assert has("overseas_investment_parties", "dealing", "overseas_investment_decisions")
    assert has("award_suppliers", "dealing", "award_notices") and has("grants", "dealing", "grant_recipients")
    assert (cat.BY_NAME["directors"], cat.BY_NAME["directors"].relations[0]) in graph.INCOMING["companies"]


def node(v, key, matched, order, parent=None, **row):
    r = {"key": key, **row}
    return {"v": cat.BY_NAME[v], "row": r, "matched": matched, "centre": False, "order": order, "parent": parent}


def sample():
    g = {"nodes": {}, "edges": [], "drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS}, "not_drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS},
         "matched_total": 3, "unresolved": 0, "centre": ""}
    g["nodes"]["party_return_donors:d1"] = node("party_return_donors", "d1", True, 0, donor="Jane DOE", amount=5)
    g["nodes"]["directors:x1"] = node("directors", "x1", True, 1, full_name="Secret Person", suppressed=True)
    g["nodes"]["party_return_totals:t1"] = node("party_return_totals", "t1", False, 2, "party_return_donors:d1", party="A Party", year=2023)
    g["nodes"]["companies:c1"] = node("companies", "c1", False, 3, "directors:x1", name="ACME <LIMITED>")
    g["edges"] = [{"kind": "money", "a": "party_return_donors:d1", "b": "party_return_totals:t1", "label": "donated, in the return", "cite": "party_return_donors:d1"},
                  {"kind": "role", "a": "directors:x1", "b": "companies:c1", "label": "director of", "cite": "directors:x1"},
                  {"kind": "same person, near", "a": "party_return_donors:d1", "b": "directors:x1", "label": "full-name@1", "cite": "party_return_donors:d1"}]
    g["drawn"].update({"money": 1, "role": 1, "same person, near": 1})
    g["not_drawn"]["role"] = 7
    return g


def test_the_layout_is_deterministic_and_inside_the_picture():
    a, b = graph.layout(sample()), graph.layout(sample())
    assert a == b and len(a) == 4
    for x, y in a.values():
        assert 0 < x < graph.W and 0 < y < graph.H
    one = sample()
    for k in ("directors:x1", "companies:c1"):
        del one["nodes"][k]
    assert graph.layout(one)["party_return_donors:d1"] == (graph.W / 2, graph.H / 2)     # one row alone sits in the middle


def test_the_picture_is_svg_with_hrefs_and_no_script():
    html = graph.pane(sample(), "doe", search.Boxes(False, ("party_returns",)))
    assert "<script" not in html and "<svg" in html and "</svg>" in html
    assert html[:html.index("<h3>Key")].count("<line ") == 3 and 'stroke-dasharray="6 4"' in html                # near is dashed
    assert "/graph?q=doe&amp;p=&amp;all=0&amp;r=party_returns&amp;c=companies%3Ac1" in html          # a node re-centres
    assert 'href="/?q=doe&amp;p=party_return_donors%3Ad1&amp;all=0&amp;r=party_returns"' in html     # a label cites the asserting row
    assert "Secret Person" not in html and "name suppressed" in html                      # hard limit 16 on every surface
    assert "ACME &lt;LIMITED&gt;" in html
    key = html[html.index("<h3>Key</h3>"):]
    for kind, colour, _ in cat.EDGE_KINDS:
        assert kind in key and colour in key
    assert re.search(r"<td>money</td><td>1</td><td>0</td>", key) and re.search(r"<td>role</td><td>1</td><td>7</td>", key)


def test_an_empty_graph_says_none_found():
    g = {"nodes": {}, "edges": [], "drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS}, "not_drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS},
         "matched_total": 0, "unresolved": 0, "centre": ""}
    assert "none found" in graph.pane(g, "zzz") and "Type a name" in graph.pane(g, "")
    nothing = graph.pane(g, "zzz", search.Boxes(False, ()), ())          # "search all" off, nothing ticked (ruling 81)
    assert "tick a register, or search all" in nothing and "none found" not in nothing
