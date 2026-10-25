"""Night mode (ruling 86 (1)), pure: one dark stylesheet in panes.CSS; every
text colour it sets reads at 4.5:1 or more on every background it sets, the
picture's labels and surface included; the key's edge colours are 3:1 or
more on the picture and apart from each other; no page carries a colour of
its own outside the stylesheet but an edge's stroke."""
import re

from products.board import catalogue as cat
from products.board import graph, panes
from products.board.tests.test_graph import sample


def test_the_contrast_formula_on_known_pairs():
    assert round(panes.contrast("#000000", "#ffffff"), 1) == 21.0
    assert round(panes.contrast("#777777", "#ffffff"), 2) == 4.48          # the classic grey that just misses
    assert panes.contrast("#fff", "#000") == panes.contrast("#000000", "#FFFFFF")


def test_every_text_colour_reads_on_every_background_of_the_sheet():
    text, back = panes.sheet_colours()
    assert "#e8eaed" in text and "#0e1014" in back and "#161a20" in back     # body text, page, panes and the picture
    assert len(text) >= 5 and len(back) >= 4
    assert all(panes.luminance(b) < 0.06 for b in back)                       # every background is dark
    assert panes.contrast_problems() == []


def test_the_floor_fails_a_sheet_that_breaks_it():
    bad = panes.CSS.replace(".note,.why{font-size:12px;color:#aab1bc", ".note,.why{font-size:12px;color:#666666")
    assert any("#666666" in p for p in panes.contrast_problems(bad))
    light = panes.CSS + "\nmark{background:#fde68a}"                           # the day scheme's highlight left behind
    assert any("#fde68a" in p for p in panes.contrast_problems(light))
    svg = panes.CSS.replace("svg text.reg{font-size:9px;fill:#aab1bc}", "svg text.reg{font-size:9px;fill:#555555}")
    assert any("#555555" in p for p in panes.contrast_problems(svg))
    assert any("edge" in p for p in panes.contrast_problems(edges=(("money", "#2a2a40", ""),)))
    assert any("apart" in p for p in panes.contrast_problems(edges=(("money", "#3987e5", ""), ("role", "#3a88e6", ""))))


def test_the_key_tells_its_edges_apart_on_dark():
    colours = {c for _, c, _ in cat.EDGE_KINDS}
    assert len(colours) == len(cat.EDGE_KINDS) - 1                  # same person, confirmed and near, share a hue; near is dashed
    assert all(panes.contrast(c, "#161a20") >= panes.EDGE_FLOOR for c in colours)
    assert min(panes.apart(a, b) for a in colours for b in colours if a < b) >= panes.EDGE_APART


def test_the_pages_take_their_colours_from_the_one_stylesheet():
    html = panes.page("x", [], [graph.pane(sample(), "x")])
    assert html.count("<style>") == 1 and ":root{color-scheme:dark}" in html
    picture = html[html.index("<svg"):html.index("</svg>")]
    assert "<style" not in picture and 'class="bg"' in picture
    assert not re.search(r'\b(fill|color|background)="?#', picture)       # nothing but a stroke carries its own colour
    strokes = set(re.findall(r'<line [^>]*stroke="(#[0-9a-f]+)"', picture))
    assert strokes and strokes <= {c for _, c, _ in cat.EDGE_KINDS}
    assert ' style="' not in html
