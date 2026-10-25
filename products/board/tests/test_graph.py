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
                  {"kind": "same person, near", "a": "party_return_donors:d1", "b": "directors:x1", "label": cat.rule_words("name-only@1"),
                   "cite": "party_return_donors:d1", "rule": "name-only@1"}]
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
    assert 'href="/?q=doe&amp;p=party_return_donors%3Ad1&amp;all=0&amp;r=party_returns"' in html     # a number cites the asserting row
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


def outside_titles(html: str) -> str:
    return re.sub(r"<title>.*?</title>", "", html, flags=re.S)


def test_a_rule_id_shows_only_in_a_title_and_the_list():
    html = graph.pane(sample(), "doe")
    picture = html[html.index("<svg"):html.index("</svg>")]
    assert "@1" not in outside_titles(picture) and "links rule" not in outside_titles(picture)
    assert "(links rule name-only, version 1)" in picture                                    # the edge's tooltip
    listed = html[html.index("Edges, by the row they reach"):]
    assert "same name, nothing else" in listed and "(links rule name-only, version 1)" in listed
    assert "@1" not in outside_titles(html)


def test_two_rows_joined_twice_get_one_line_listing_both_causes():
    g = sample()
    g["edges"].append({"kind": "money", "a": "directors:x1", "b": "party_return_donors:d1", "label": "lent to", "cite": "directors:x1", "rule": None})
    lns = graph.lines(g)
    assert len(lns) == 3
    both = lns[2]
    assert [e["kind"] for e in both["causes"]] == ["money", "same person, near"] and both["kind"] == "money"   # the key's order sets the stroke
    html = graph.pane(g, "doe")
    picture = html[html.index("<svg"):html.index("</svg>")]
    assert picture.count("<line ") == 3
    line = [m for m in re.findall(r'<line [^>]*stroke="([^"]+)"[^>]*><title>([^<]*)</title>', picture) if "lent to" in m[1]]
    assert len(line) == 1 and line[0][0] == "#3987e5"
    assert line[0][1] == "money: lent to; same person, near: same name, nothing else (links rule name-only, version 1)"
    assert ">lent to (+1)</text>" in picture                                    # the words say there is more, the tooltip says what
    listed = html[html.index('<div class="edges">'):]
    assert listed.index("lent to") < listed.index("same name, nothing else") and listed.count("the row that asserts it") >= 4
    assert '4 connections on 3 lines' in html


def test_no_edge_carries_a_number():
    html = graph.pane(sample(), "doe")
    picture = html[html.index("<svg"):html.index("</svg>")]
    assert not re.search(r"<text[^>]*>\d+</text>", picture) and 'class="num"' not in picture
    assert "<ol" not in html and "by number" not in html and "<li value=" not in html
    assert picture.count("<title>") >= picture.count("<line ") + 1               # every line keeps its hover title


def test_the_list_is_grouped_by_the_far_row_in_the_key_s_order_then_by_title():
    g = sample()
    g["nodes"]["companies:c0"] = node("companies", "c0", False, 4, "directors:x1", name="AARDVARK LIMITED")
    g["edges"].append({"kind": "role", "a": "directors:x1", "b": "companies:c0", "label": "director of", "cite": "directors:x1", "rule": None})
    html = graph.pane(g, "doe")
    listed = html[html.index('<div class="edges">'):]
    heads = re.findall(r"<h4>(.*?) <span", listed)
    assert heads == ["A Party · 2023", "AARDVARK LIMITED", "ACME &lt;LIMITED&gt;", "name suppressed"]   # money, then role by title, then same person
    under = listed[listed.index("<h4>ACME"):listed.index("<h4>name suppressed")]
    assert "director of" in under and 'href="/?q=doe&amp;p=directors%3Ax1' in under and "from name suppressed" in under
    assert listed.count("<h4>") == len({frozenset((e["a"], e["b"])) for e in g["edges"]})        # one heading per connected row


def crowded(n=40):
    """One matched row with n neighbours, long names: the fan the ruling saw."""
    g = sample()
    g["nodes"] = {"party_return_donors:d1": node("party_return_donors", "d1", True, 0, donor="A VERY LONG DONOR NAME LIMITED PARTNERSHIP", amount=5)}
    g["edges"] = []
    for i in range(n):
        nid = f"companies:c{i}"
        g["nodes"][nid] = node("companies", f"c{i}", False, i + 1, "party_return_donors:d1", name=f"COMPANY NUMBER {i} WITH A LONG NAME LIMITED")
        g["edges"].append({"kind": "role", "a": "party_return_donors:d1", "b": nid, "label": "director of", "cite": nid, "rule": None})
        if i % 3 == 0:
            g["edges"].append({"kind": "same person, near", "a": "party_return_donors:d1", "b": nid, "label": cat.rule_words("company-name@1"),
                               "cite": "party_return_donors:d1", "rule": "company-name@1"})
    return g


def test_no_text_box_touches_another_on_the_rendered_crowded_picture_and_placement_is_deterministic():
    for n in (3, 12, 40, 110):
        g = crowded(n)
        lns = graph.lines(g)
        pos = graph.layout(g)
        p = graph.place(g, pos, lns)
        assert p == graph.place(g, pos, lns)
        assert graph.overlaps(p) == [], (n, graph.overlaps(p)[:3])
        html = graph.pane(g, "x")
        picture = html[html.index("<svg"):html.index("</svg>")]
        boxes = graph.text_boxes(picture)
        assert len(boxes) == sum(1 + bool(v[1]) for v in p["labels"].values() if v) + sum(1 for v in p["words"].values() if v)
        assert graph.touching_text(picture) == [], (n, graph.touching_text(picture)[:3])     # read from the SVG's own x, y, anchor, class and text
        drawn = [k for k, v in p["words"].items() if v]
        assert len(drawn) >= min(len(lns), 3), n                      # the picture still says what some edges are
        listed = html[html.index('<div class="edges">'):]
        assert listed.count("the row that asserts it") == len(g["edges"])     # every cause is listed, its words drawn or not
    assert any(graph.place(crowded(110), graph.layout(crowded(110)), graph.lines(crowded(110)))["labels"][k][0].endswith("…")
               for k in crowded(110)["nodes"])                               # names are shortened to clear, not drawn over


def test_the_no_touch_reading_catches_two_texts_that_touch():
    picture = ('<text x="100" y="100" text-anchor="middle">ACME LIMITED</text>'
               '<text class="words" x="100" y="108" text-anchor="middle">director of</text>')
    assert graph.touching_text(picture) == [("ACME LIMITED", "director of")]
    apart = picture.replace('y="108"', 'y="130"')
    assert graph.touching_text(apart) == []
    side = ('<text x="10" y="50" text-anchor="start">ab</text><text x="24" y="50" text-anchor="start">cd</text>')
    assert graph.touching_text(side)                                  # "ab" runs to x 23.8; "cd" starts at 23


def test_overlaps_finds_two_boxes_that_meet():
    p = {"labels": {"a": ("x", "", 0, 0, 0, "middle", (0, 0, 10, 10)), "b": ("y", "", 0, 0, 0, "middle", (5, 5, 15, 15))}, "words": {1: ("w", 40, 40, (35, 35, 45, 45))}}
    assert graph.overlaps(p) == [("label a", "label b")]


def gift_graph():
    """A donor filed under one name in three returns over two years and one
    disclosure, to one party that a candidacy also reaches."""
    g = sample()
    g["nodes"] = {"party_return_donors:d1": node("party_return_donors", "d1", True, 0, donor="Jane DOE", amount=5),
                  "parties:p1": node("parties", "p1", False, 1, "party_return_donors:d1", name="A Party")}
    g["nodes"]["party_return_donors:d1"]["title"] = "Jane DOE"
    adds = [{"year": 2022, "amount": 1000, "what": "party return", "cite": "party_return_donors:d1", "not_added": "", "apart": False,
             "record": "party_return_totals:t1", "record_words": "the return"},
            {"year": 2023, "amount": 250.5, "what": "party return", "cite": "party_return_donors:d2", "not_added": "", "apart": False,
             "record": "party_return_totals:t2", "record_words": "the return"},
            {"year": 2023, "amount": 99, "what": "party return", "cite": "party_return_donors:d3", "not_added": "replaced by an amendment, not added",
             "apart": False, "record": "party_return_totals:t3", "record_words": "the return"},
            {"year": 2023, "amount": 30000, "what": "large-donation disclosure", "cite": "disclosures:x1",
             "not_added": "a disclosure: its gift is also in the year's return, never added to it", "apart": True, "record": "", "record_words": ""}]
    g["edges"] = [{"kind": "money", "a": "party_return_donors:d1", "b": "parties:p1", "label": graph.gift_label(adds),
                   "cite": "party_return_donors:d1", "rule": None, "addends": adds}]
    return g, adds


def test_a_donor_s_gifts_to_one_party_are_one_edge_whose_total_is_the_sum_of_its_listed_addends():
    g, adds = gift_graph()
    s = graph.summed(adds)
    assert s["total"] == graph.decimal.Decimal("1250.5") and s["records"] == 2 and s["years"] == [2022, 2023]
    assert graph.gift_label(adds) == ("donated $1,250.50 (2 returns, 2022–2023); "
                                      "disclosed $30,000.00 (1 disclosure, 2023), not added")
    html = graph.pane(g, "doe")
    picture = html[html.index("<svg"):html.index("</svg>")]
    assert picture.count("<line ") == 1 and "donated $1,250.50 (2 returns, 2022–2023)" in picture       # the tooltip, whole
    listed = html[html.index('<div class="edges">'):]
    shown = [graph.decimal.Decimal(a.replace(",", "")) for a, why in
             re.findall(r"<li>\d{4} · \$([\d,.]+) · [^<]*(<span class=\"warn\">)?", listed) if not why]
    assert sum(shown) == s["total"] and len(shown) == 2                  # the total is checkable from the list
    assert listed.count("not added") >= 2 and listed.count('>the return</a>') == 3
    assert 'href="/?q=doe&amp;p=party_return_donors%3Ad2' in listed
    assert "one donor name exactly as filed" in html


def test_a_label_with_one_return_and_none_added_says_so():
    one = [{"year": 2024, "amount": 10, "what": "candidate return", "cite": "c:1", "not_added": "", "record": "r:1"}]
    assert graph.gift_label(one) == "donated $10.00 (1 return, 2024)"
    none = [{"year": None, "amount": None, "what": "party return", "cite": "c:1", "not_added": "no amount filed, not added", "record": "r:1"}]
    assert "none added" in graph.gift_label(none)


def test_a_filed_name_is_folded_and_a_suppressed_or_non_gift_row_has_none():
    assert graph.filed_name(cat.BY_NAME["party_return_donors"], {"donor": "  Jāne   DOE "}) == "jane doe"
    assert graph.filed_name(cat.BY_NAME["companies"], {"name": "ACME"}) == ""
    assert {g.view for g in cat.GIFTS} == {"party_return_donors", "disclosures", "candidate_return_donors"}
    assert [g.added for g in cat.GIFTS] == [True, False, True]            # a disclosure is never summed with a return
