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
    assert a == b and len(a["pos"]) == 4
    for x, y in a["pos"].values():
        assert 0 < x < a["w"] and 0 < y < a["h"]
    one = sample()
    for k in ("directors:x1", "companies:c1"):
        del one["nodes"][k]
    one["edges"] = [e for e in one["edges"] if e["a"] in one["nodes"] and e["b"] in one["nodes"]]
    lay = graph.layout(one)
    assert lay["pos"]["party_return_donors:d1"][0] == lay["w"] / 2                     # one row alone sits in the middle


def edge(kind, a, b, label, rule=None):
    return {"kind": kind, "a": a, "b": b, "label": label, "cite": a, "rule": rule}


def family():
    """A name search's graph: five matched rows (a donor, a candidate, two
    directors, a company) in a scrambled found order; a party two of them
    reach, a company two directors share, the company's people below, two
    same-person rows beside, and a same-person verdict between two matched rows."""
    g = sample()
    g["nodes"] = {}
    rows = [("directors", "x2", None, dict(full_name="Jane SMITH")),          # found order; the parent is the row that reached it first
            ("party_return_donors", "d1", None, dict(donor="John SMITH", amount=500)),
            ("companies", "c9", None, dict(name="SMITH HOLDINGS LIMITED")),
            ("candidates", "k1", None, dict(display_name="John SMITH", election="ge-2023")),
            ("directors", "x1", None, dict(full_name="John SMITH")),
            ("parties", "p1", "party_return_donors:d1", dict(name="A Party")),
            ("companies", "c2", "directors:x2", dict(name="SHARED LIMITED")),
            ("companies", "c3", "directors:x2", dict(name="THIRD LIMITED")),
            ("directors", "y1", "companies:c9", dict(full_name="Ann OTHER")),
            ("directors", "y2", "companies:c9", dict(full_name="Bob OTHER")),
            ("shareholders", "s1", "companies:c9", dict(name="Cat OTHER")),
            ("electorates", "e1", "candidates:k1", dict(name="Somewhere", election="ge-2023")),
            ("members", "mm1", "candidates:k1", dict(display_name="John Smith", route="list")),
            ("companies", "c1", "directors:x1", dict(name="FIRST LIMITED")),
            ("charity_officers", "o1", "directors:x1", dict(full_name="John SMITH"))]
    for i, (v, k, parent, r) in enumerate(rows):
        g["nodes"][f"{v}:{k}"] = node(v, k, parent is None, i, parent, **r)
    near = cat.rule_words("name-only@1")
    g["edges"] = [edge("money", "party_return_donors:d1", "parties:p1", "donated $500.00 (1 return, 2023)"),
                  edge("candidacy", "candidates:k1", "parties:p1", "candidate for"),
                  edge("candidacy", "candidates:k1", "electorates:e1", "stood in"),
                  edge("role", "directors:x1", "companies:c1", "director of"),
                  edge("role", "directors:x1", "companies:c2", "director of"),
                  edge("role", "directors:x2", "companies:c2", "director of"),
                  edge("role", "directors:x2", "companies:c3", "director of"),
                  edge("role", "directors:y1", "companies:c9", "director of"),
                  edge("role", "directors:y2", "companies:c9", "director of"),
                  edge("role", "shareholders:s1", "companies:c9", "shareholder of"),
                  edge("same person, near", "party_return_donors:d1", "candidates:k1", near, "name-only@1"),
                  edge("same person, confirmed", "candidates:k1", "members:mm1", near, "name-only@1"),
                  edge("same person, near", "directors:x1", "charity_officers:o1", near, "name-only@1")]
    return g


#: the shape of a real ten-row name search's graph (the "hart" search of 26 October 2026), every name invented:
#: (view, parent or None for a matched row), in the order build found them; then its edges
SEARCHED_NODES = [("party_return_donors", None), ("party_return_donors", None), ("disclosures", None), ("disclosures", None),
                  ("promoter_people", None), ("promoter_people", None), ("candidates", None), ("candidates", None),
                  ("mp_interest_returns", None), ("mp_interest_returns", None),
                  ("parties", 0), ("parties", 0), ("shareholders", 0), ("promoters", 4), ("directors", 4), ("electorates", 6),
                  ("directors", 6), ("electorates", 7)] + [("mp_interests", 8)] * 5 + [("mp_interests", 9)] * 5
SEARCHED_EDGES = [("money", 0, 10), ("money", 0, 11), ("money", 1, 11), ("money", 2, 10), ("money", 2, 11), ("money", 3, 11),
                  ("same person, near", 0, 12), ("same person, confirmed", 2, 12), ("role", 4, 13), ("same person, near", 4, 14),
                  ("role", 5, 13), ("same person, near", 5, 14), ("candidacy", 6, 15), ("same person, near", 6, 16),
                  ("candidacy", 7, 17), ("same person, near", 7, 16), ("same person, near", 8, 9)] + \
                 [("declaration", i, 8) for i in range(18, 23)] + [("declaration", i, 9) for i in range(23, 28)]


def searched():
    g = sample()
    ids = [f"{v}:n{i}" for i, (v, _) in enumerate(SEARCHED_NODES)]
    g["nodes"] = {}
    for i, (v, parent) in enumerate(SEARCHED_NODES):
        title = {c: f"Invented {v.replace('_', ' ')} {i}" for c in cat.BY_NAME[v].title}
        g["nodes"][ids[i]] = node(v, f"n{i}", parent is None, i, None if parent is None else ids[parent], **title)
    g["edges"] = [edge(kind, ids[a], ids[b], "same name, nothing else" if kind.startswith("same") else kind,
                       "name-only@1" if kind.startswith("same") else None) for kind, a, b in SEARCHED_EDGES]
    return g


#: the old sector layout's crossing counts on family() and searched(): its straight lines, each pair sharing no
#: node, counted where they cross. Measured with the sector layout before it was deleted (board-5, 26 October 2026).
SECTOR_CROSSINGS = {"family": 0, "searched": 7}


def test_the_matched_rows_share_one_line_organisations_above_people_below_and_every_edge_has_right_angles():
    g = family()
    lns = graph.lines(g)
    lay = graph.layout(g, lns)
    pos = lay["pos"]
    matched = [k for k, n in g["nodes"].items() if n["matched"]]
    y0 = {pos[k][1] for k in matched}
    assert len(y0) == 1
    y0 = y0.pop()
    xs = [pos[k][0] for k in graph.matched_order(g)]
    assert xs == sorted(xs) and len({round(b - a, 3) for a, b in zip(xs, xs[1:])}) == 1          # evenly spaced
    assert graph.matched_order(g) == ["party_return_donors:d1", "candidates:k1", "directors:x2", "directors:x1", "companies:c9"]   # register, then title
    for k in ("parties:p1", "electorates:e1", "companies:c1", "companies:c2", "companies:c3"):
        assert pos[k][1] < y0, k                                                                     # what they belong to or pay: above
    for k in ("directors:y1", "directors:y2", "shareholders:s1"):
        assert pos[k][1] > y0, k                                                                     # who belongs to them: below
    for k, m in (("members:mm1", "candidates:k1"), ("charity_officers:o1", "directors:x1")):
        assert pos[k][1] == y0 and abs(pos[k][0] - pos[m][0]) == graph.SLOT                         # same person: beside
    shared = (pos["directors:x1"][0] + pos["directors:x2"][0]) / 2
    assert pos["companies:c2"][0] == shared and pos["parties:p1"][0] == (pos["party_return_donors:d1"][0] + pos["candidates:k1"][0]) / 2
    assert sum(1 for k in pos if k == "companies:c2") == 1                                           # placed once
    ends_c2 = sorted(p[-1][0] for n, p in lay["paths"].items() if p[-1][1] == pos["companies:c2"][1] and abs(p[-1][0] - shared) < 10)
    assert len(ends_c2) == 2 and ends_c2[0] != ends_c2[1]                                            # its edges fan from it
    assert set(lay["paths"]) == {ln["n"] for ln in lns}
    for n, path in lay["paths"].items():
        assert graph.orthogonal(path), (n, path)
        assert all(a[0] == b[0] or a[1] == b[1] for a, b in zip(path, path[1:]))
    html = graph.pane(g, "smith")
    picture = html[html.index("<svg"):html.index("</svg>")]
    for d in re.findall(r'<path class="edge" d="([^"]+)"', picture):
        assert re.fullmatch(r"M[\d.]+ [\d.]+( [HV][\d.]+)+", d), d                                # only H and V after the start
    assert picture.count('<path class="edge"') == len(lns) and "<line " not in picture
    assert graph.touching_text(picture) == []


def test_node_labels_stay_off_the_channels():
    for g in (family(), crowded(40)):
        lns = graph.lines(g)
        lay = graph.layout(g, lns)
        p = graph.place(g, lay, lns)
        for nid, lab in p["labels"].items():
            if lab:
                assert not any(graph.touch(lab[-1], b) for b in lay["bands"]), nid


def test_bars_that_overlap_take_different_channels_and_the_crossings_are_counted():
    for g in (family(), searched()):
        lay = graph.layout(g)
        runs = {}
        for n, p in lay["paths"].items():
            for a, b in graph.segments(p):
                if a[1] == b[1] and a[1] != lay["y0"]:
                    runs.setdefault(a[1], []).append((min(a[0], b[0]), max(a[0], b[0]), n))
        ends = {ln["n"]: {ln["a"], ln["b"]} for ln in graph.lines(g)}
        for y, rs in runs.items():
            for i, (a0, a1, n) in enumerate(rs):
                for b0, b1, m in rs[i + 1:]:
                    if a0 < b1 and b0 < a1:
                        assert ends[n] & ends[m], (y, n, m)                # one channel shares a span only within one bar
        assert lay["crossings"] == graph.crossings(lay["paths"], ends)
    assert len({p[1][1] for p in graph.layout(searched())["paths"].values() if len(p) == 4}) > 2      # searched() needs channels
    assert graph.crossings({1: [(0, 0), (10, 0)], 2: [(5, -5), (5, 5)]}, {1: {"a", "b"}, 2: {"c", "d"}}) == 1
    assert graph.crossings({1: [(0, 0), (10, 0)], 2: [(5, -5), (5, 5)]}, {1: {"a", "b"}, 2: {"a", "d"}}) == 0


def test_the_layered_layout_crosses_no_more_than_the_sector_layout_did():
    assert graph.layout(family())["crossings"] <= SECTOR_CROSSINGS["family"]
    lay = graph.layout(searched())
    assert lay["crossings"] <= SECTOR_CROSSINGS["searched"]
    assert all(graph.orthogonal(p) for p in lay["paths"].values())
    assert len({lay["pos"][f"{v}:n{i}"][1] for i, (v, parent) in enumerate(SEARCHED_NODES) if parent is None}) == 1


def test_the_picture_is_svg_with_hrefs_and_no_script():
    html = graph.pane(sample(), "doe", search.Boxes(False, ("party_returns",)))
    assert "<script" not in html and "<svg" in html and "</svg>" in html
    assert html[:html.index("<h3>Key")].count('<path class="edge"') == 3 and 'stroke-dasharray="6 4"' in html     # near is dashed
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
    assert picture.count('<path class="edge"') == 3
    line = [m for m in re.findall(r'<path class="edge" [^>]*stroke="([^"]+)"[^>]*><title>([^<]*)</title>', picture) if "lent to" in m[1]]
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
    assert picture.count("<title>") >= picture.count('<path class="edge"') + 1     # every line keeps its hover title


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
        lay = graph.layout(g, lns)
        p = graph.place(g, lay, lns)
        assert p == graph.place(g, lay, lns)
        assert all(graph.orthogonal(x) for x in lay["paths"].values())
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
    assert picture.count('<path class="edge"') == 1 and "donated $1,250.50 (2 returns, 2022–2023)" in picture     # the tooltip, whole
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
