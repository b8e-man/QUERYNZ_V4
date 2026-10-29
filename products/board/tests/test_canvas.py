"""The graph canvas (ruling 100), pure but for one server on a loopback
port: the vendored files are the pinned ones and served from the fixed list
alone; the page and every served script name no address off the box; the
JSON answer is the SVG picture's graph as data, with no address edge and a
suppressed row's name kept out; the SVG stays inside <noscript> and the key
and the edge list under the picture are unchanged."""
import hashlib
import http.client
import json
import os
import re
import threading

from products.board import assets, check, dossier, graph, panes, search, server
from products.board import catalogue as cat
from products.board.tests.test_graph import sample

PINNED = {"cytoscape.min.js": "9c2a3bf2592e0b14a1f7bec07c03a54f16dedf32af9cd0af155c716aa6c87bc3",
          "cytoscape-cola.js": "bb820d9f649827582d005682e26a0cea915539a0dbda32a17964ad2210bbcd08",
          "cola.min.js": "b45eba3fb02d22d9ea9a2bcad07ddbec8296f807f05e96f8c9d4abbc497f65c7"}
LICENCES = {"cytoscape.min.js": "LICENSE.cytoscape", "cytoscape-cola.js": "LICENSE.cytoscape-cola", "cola.min.js": "LICENSE.webcola"}


def test_the_vendored_files_are_the_pinned_ones_with_their_licence_and_their_record():
    readme = open(os.path.join(assets.DIR, "README.md"), encoding="utf-8").read()
    for name, sha in PINNED.items():
        body, ctype = assets.read(name)
        assert hashlib.sha256(body).hexdigest() == sha and ctype.startswith("text/javascript")
        assert sha in readme and f"`{name}`" in readme
        licence = assets.read(LICENCES[name])[0].decode()
        assert "Permission is hereby granted, free of charge" in licence and LICENCES[name] in readme
    for version in ("3.34.0", "2.5.1", "3.4.0"):
        assert version in readme


def test_static_answers_for_its_listed_files_alone():
    for name in assets.FILES:
        assert os.path.isfile(os.path.join(assets.DIR, name)) and assets.read(name)[0]
    for bad in ("README.md", "../server.py", "..", "", "static", "graph.py", "/etc/passwd", "graph.js/", "GRAPH.JS"):
        assert assets.read(bad) is None
    assert set(assets.SCRIPTS) <= set(assets.FILES)
    assert re.fullmatch(r"/static/graph\.js\?v=[0-9a-f]{12}", assets.url("graph.js"))


def test_the_address_reading_finds_an_address_off_the_box_and_passes_a_comment_and_the_namespace():
    assert assets.addresses('fetch("https://cdn.jsdelivr.net/npm/x.js")') == ["https://cdn.jsdelivr.net/npm/x.js"]
    assert assets.addresses('<script src="//unpkg.com/cytoscape"></script>') == ["//unpkg.com/cytoscape"]
    assert assets.addresses("/* MIT License: http://en.wikipedia.org/wiki/MIT_License */ var a = 1;") == []
    assert assets.addresses('<svg xmlns="http://www.w3.org/2000/svg">') == []
    assert assets.addresses("// one line, no address\nvar b = a / 2; // c.d") == []


def page_with_canvas(g=None, q="doe"):
    boxes = search.Boxes(False, ("party_returns",))
    return panes.page(q, [], [graph.pane(g or sample(), q, boxes, script=True)], "", boxes, tab="graph")


def test_the_page_and_every_script_it_serves_name_no_address_off_the_box():
    html = page_with_canvas()
    assert assets.addresses(html) == []
    srcs = re.findall(r'<script\b[^>]*\bsrc="([^"]*)"', html)
    assert srcs == [assets.url(n) for n in assets.SCRIPTS] + [assets.url("chat.js")]     # every script is the board's own; ruling 122's pane last
    assert not re.search(r'<(?:link|img|iframe)\b', html)
    for name in assets.FILES:
        assert assets.addresses(assets.read(name)[0].decode("utf-8", "replace")) == [], name
    js = assets.read("graph.js")[0].decode()
    assert "innerHTML" not in js and "eval(" not in js                          # text goes in by textContent
    assert sorted(re.findall(r"fetch\(([^,]*),", js)) == ['box.getAttribute("data-base") + "&d=" + encodeURIComponent(id)',
                                                         'node.data("grow")', 'node.data("open")', 'url']
    assert "draw(hit.getAttribute(\"data-graph\")" in js and "draw(side.getAttribute(\"data-start\")" in js   # `url`: the server's /graph.json
    assert dossier.base("x", search.FIRST).startswith("/dossier?")                    # ruling 110: the dossier's fetch, the board's own path
    # the node's /graph.json hrefs, and a result's (ruling 108 (4)), which the server writes as /graph.json alone
    assert "data-graph" in js and panes.graph_href("companies:c1").startswith("/graph.json?")


def test_the_svg_stays_inside_noscript_and_the_key_and_the_list_are_unchanged():
    boxes = search.Boxes(False, ("party_returns",))
    plain, canvas = graph.pane(sample(), "doe", boxes), graph.pane(sample(), "doe", boxes, script=True)
    assert "<script" not in plain                                               # without the flag, as before
    picture = check.noscript_picture(canvas)
    assert picture.startswith('<div class="picture"><svg') and picture == plain[plain.index('<div class="picture">'):plain.index("</svg></div>") + 12]
    assert canvas[canvas.index("<h3>Key</h3>"):] == plain[plain.index("<h3>Key</h3>"):]      # rulings 84, 86
    assert 'id="cy"' in canvas and 'id="spread"' in canvas and 'id="tree"' in canvas and 'id="graph-data"' in canvas
    assert canvas.index('id="graph-data"') < canvas.index(assets.url("graph.js"))


def test_the_answer_is_the_picture_s_graph_as_data():
    g = sample()
    html = graph.pane(g, "doe", search.Boxes(False, ("party_returns",)), script=True)
    data = check.inline_data(html)
    ids, places, lines = check.svg_graph(html)
    assert {n["id"] for n in data["nodes"]} == ids == set(g["nodes"])
    assert {(round(n["x"], 1), round(n["y"], 1)) for n in data["nodes"]} == places
    assert sum(lines.values()) == len(data["edges"]) == 3
    assert {(e["title"], e["colour"]) for e in data["edges"]} == set(lines)
    n = next(n for n in data["nodes"] if n["id"] == "companies:c1")
    assert set(n) == {"id", "view", "key", "title", "register", "register_name", "family", "colour", "matched", "centre",
                      "x", "y", "pane", "grow"}
    assert n["view"] == "companies" and n["key"] == "c1" and n["colour"] == cat.REGISTER_COLOUR["companies"]
    assert n["pane"] == "/?q=doe&p=companies%3Ac1&all=0&r=party_returns"
    assert n["grow"] == "/graph.json?c=companies%3Ac1&all=0&r=party_returns"
    for e in data["edges"]:
        assert e["dashed"] == (e["kind"] == graph.NEAR) and e["colour"] == graph.KIND[e["kind"]][0]
        assert "address" not in e["kind"] and e["causes"] and all(c["cite"].startswith("/?q=doe&p=") for c in e["causes"])
    near = next(e for e in data["edges"] if e["kind"] == graph.NEAR)
    assert near["causes"][0]["rule"] == cat.rule_ref("name-only@1") and "name-only@1" not in near["words"]


def test_a_suppressed_row_keeps_its_name_out_of_the_answer_and_the_page():
    data = graph.answer(sample(), "doe")
    text = graph.to_json(data)
    assert "Secret Person" not in text and "Secret Person" not in page_with_canvas()
    assert next(n for n in data["nodes"] if n["id"] == "directors:x1")["title"] == panes.SUPPRESSED


def test_the_inline_data_cannot_end_its_script():
    g = sample()
    g["nodes"]["companies:c1"]["row"]["name"] = "</script><script>alert(1)</script> & co"
    html = graph.pane(g, "doe", script=True)
    data = html[html.index('id="graph-data">'):html.index("</script>", html.index('id="graph-data">'))]
    assert "<" not in data[len('id="graph-data">'):] and "&" not in data[len('id="graph-data">'):]
    assert any(n["title"].startswith("</script>") for n in check.inline_data(html)["nodes"])


def test_a_money_edge_carries_its_addends():
    g = sample()
    g["edges"][0]["addends"] = [{"year": 2023, "amount": 5, "what": "a donation", "cite": "party_return_donors:d1", "not_added": "",
                                 "record": "party_return_totals:t1", "record_words": "the return"}]
    e = next(e for e in graph.answer(g, "doe")["edges"] if e["kind"] == "money")
    a = e["causes"][0]["addends"][0]
    assert a["year"] == 2023 and a["amount"] == panes.fmt(5, "amount") and a["record"] == "/?q=doe&p=party_return_totals%3At1"


def get(port, path):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.request("GET", path)
    r = c.getresponse()
    return r.status, dict(r.getheaders()), r.read()


def test_the_server_serves_static_with_its_type_and_a_long_cache_and_404s_the_rest():
    httpd = server.Server(("127.0.0.1", 0), server.Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        port = httpd.server_address[1]
        status, head, body = get(port, assets.url("graph.js"))
        assert status == 200 and head["Content-Type"] == "text/javascript; charset=utf-8" and "max-age=31536000" in head["Cache-Control"]
        assert body == assets.read("graph.js")[0] and head["X-Content-Type-Options"] == "nosniff"
        assert get(port, "/static/LICENSE.webcola")[1]["Content-Type"].startswith("text/plain")
        for bad in ("/static/README.md", "/static/../server.py", "/static/", "/static/%2e%2e/graph.py", "/static/graph.py"):
            assert get(port, bad)[0] == 404, bad
        status, head, _ = get(port, "/nowhere")
        assert status == 404 and "script-src 'self'" in head["Content-Security-Policy"] and "connect-src 'self'" in head["Content-Security-Policy"]
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_every_register_has_a_node_colour_that_reads_on_the_picture_and_stands_apart():
    assert [r for r, _ in cat.REGISTER_COLOURS] == [r for r, _ in cat.REGISTERS]
    assert sorted(r for _, _, regs in cat.FAMILIES for r in regs) == sorted(r for r, _ in cat.REGISTERS)
    fills = {c for _, c in cat.REGISTER_COLOURS}
    assert len(fills) == len(cat.FAMILIES)
    assert all(panes.contrast(c, "#161a20") >= panes.EDGE_FLOOR for c in fills)
    assert min(panes.apart(a, b) for a in fills for b in fills if a < b) >= panes.EDGE_APART
    assert panes.contrast_problems() == []
    assert any("node" in p and "#202020" in p for p in panes.contrast_problems(nodes=(("parties", "#202020"),)))
    assert any("apart" in p for p in panes.contrast_problems(nodes=(("parties", "#60c0f8"), ("house", "#62c1f8"))))
    assert "div.cy{" in panes.CSS and "background:#161a20" in panes.CSS[panes.CSS.index("div.cy{"):]   # the canvas takes the picture's surface


def test_the_answer_serialises_as_json():
    data = json.loads(graph.to_json(graph.answer(sample(), "doe")))
    assert data["centre"] == "" and len(data["nodes"]) == 4 and data["drawn"]["money"] == 1
