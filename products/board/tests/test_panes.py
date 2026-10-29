"""The rules for what a product shows, on rendered panes: a suppressed name
reads 'name suppressed' everywhere; a withheld text reads withheld; a figure
read from pixels is marked; a blank says not stated; none found and not held
are said; every value is escaped; the citation names the document."""
import datetime as dt
import decimal

import re
import urllib.parse

from products.board import catalogue as cat
from products.board import graph, panes, search

NO_LINKS = {"built": False, "why": "no links built yet", "confirmed": [], "near": []}


def director(**kw):
    r = {"key": "companies/1/director/a", "entity_key": "companies/1", "full_name": "Jane <b>DOE</b>", "role_type": "Director",
         "appointed_on": dt.date(2020, 1, 2), "ended_on": None, "in_latest": True, "first_file": "companies-2020-01",
         "last_file": "companies-2026-07", "suppressed": False, "document": "ab" * 32, "page": 1, "place": "line 9",
         "read_from": "text", "reader": "export", "profile": "companies-export", "loaded_at": dt.datetime(2026, 10, 1, 1, 0),
         "nzbn": "9429000000001", "company_number": "1"}
    r.update(kw)
    return r


def boxes_shown(html: str) -> tuple:
    """(is "search all" ticked, [the register boxes ticked]) as the form shows them."""
    boxes = re.findall(r'<input type="checkbox" name="(all|r)" value="([^"]*)"( checked)?>', html)
    return (any(n == "all" and c for n, _, c in boxes), [x for n, x, c in boxes if n == "r" and c])


def carried(link: str) -> search.Boxes:
    """The check boxes an href carries, read back as the server reads them."""
    return search.boxes_of(urllib.parse.parse_qs(urllib.parse.urlsplit(link.replace("&amp;", "&")).query))


def hrefs(html: str) -> list:
    return [h for h in re.findall(r'href="([^"]*)"', html) if h.startswith(("/?", "/graph?"))]


def ctx(v, r, **kw):
    base = {"v": v, "row": r, "q": "doe", "path": [f"{v.name}:{r['key']}"], "parent": None, "children": [],
            "doc_names": [], "links": NO_LINKS, "group": {}, "same": {"held": set()}, "same_words": ["jane", "doe"],
            "resolve": lambda ref: None, "pinned": False}
    base.update(kw)
    return base


def test_a_suppressed_name_is_suppressed_on_every_surface_and_the_row_stays():
    v = cat.BY_NAME["directors"]
    r = director(suppressed=True, full_name="Secret Person")
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert "Secret Person" not in html
    assert html.count(panes.SUPPRESSED) >= 2          # the title and the fields
    assert "Director" in html and "ab" * 6 in html    # the row and its citation stay
    assert "person: the group" not in html            # no person pane for a name that may not be shown
    assert "not searched: this row" in html


def test_values_are_escaped_and_pixels_are_marked():
    v = cat.BY_NAME["directors"]
    html = panes.row_pane(ctx(v, director(read_from="pixels")))
    assert "<b>DOE</b>" not in html and "&lt;b&gt;DOE&lt;/b&gt;" in html
    assert panes.PIXELS in html


def test_a_blank_says_not_stated_and_dates_are_as_filed():
    v = cat.BY_NAME["directors"]
    html = panes.row_pane(ctx(v, director()))
    assert "2 January 2020" in html and panes.NOT_STATED in html      # ended_on is None: the file states none
    assert "never a date of anything" in html


def test_the_citation_names_the_document_and_says_what_source_opens():
    v = cat.BY_NAME["disclosures"]
    r = {"key": "ec-listing/x", "donor_name": "A Donor", "party": "A Party", "amount": decimal.Decimal("25000.00"),
         "document": "cd" * 32, "page": 3, "place": "row 4", "read_from": "text", "href": "https://elections.nz/x"}
    html = panes.row_pane(ctx(v, r, doc_names=["https://elections.nz/listing.html", "listing-2023.html"]))
    assert "cdcdcdcdcdcd…" in html and 'title="' + "cd" * 32 + '"' in html
    assert 'href="https://elections.nz/listing.html"' in html and "listing-2023.html" in html
    assert "$25,000.00" in html and "the addresses it prints included" in html and "not opened here" not in html
    assert "/doc/" not in html and "document not held here" in html          # no state given: nothing is offered


def test_withheld_text_reads_withheld():
    v = cat.BY_NAME["mp_interests"]
    r = {"key": "h/p3/l11", "name": "Jim ANDERTON", "heading": "Real property", "text": "12 Some Street", "withheld": True,
         "member": "Jim ANDERTON", "as_at": dt.date(2006, 1, 31), "document": "ef" * 32}
    html = panes.row_pane(ctx(v, r, same_words=["jim", "anderton"]))
    assert "12 Some Street" not in html and "withheld" in html


def test_the_search_tab_says_none_found_and_not_held_and_greys_what_is_not_held():
    held = {"companies", "directors", "parties"}       # parties held with no hit: none found; the rest: not held
    regs = ("parties", "companies")
    html = panes.results_pane("doe", {"companies": [(cat.BY_NAME["directors"], 3, [director()])]}, held, regs, search.Boxes(False, regs), ["doe"])
    assert html.count("none found") == 1 and '<span class="count">3</span>' in html and "<mark>DOE</mark>" in html.replace("&lt;b&gt;", "")
    assert "Charities register" not in html                     # an unchecked register is not in the results
    left = panes.left_pane("doe", ["parties", "companies"], search.Boxes(False, regs))
    assert left.count("disabled") == len(cat.REGISTERS) - 2 + len(cat.NOT_HELD)     # greyed and cannot be checked
    assert boxes_shown(left) == (False, ["parties", "companies"])
    assert panes.results_pane("", {}, held, regs, search.Boxes(False, regs)).count("none found") == 0


def test_every_field_the_view_shows_is_in_the_results_and_a_suppressed_name_never_is():
    v = cat.BY_NAME["directors"]
    html = panes.hit("doe", v, director(), ["doe"], search.Boxes(False, ("companies",)))
    for label, c in v.fields + v.dates:
        if director().get(c) not in (None, ""):
            assert f"<th>{label}</th>" in html, label
    assert "not stated: ended on" in html and "ababababab" in html and "r=companies" in html
    secret = panes.hit("doe", v, director(suppressed=True, full_name="Secret Person"), ["secret"])
    assert "Secret" not in secret and panes.SUPPRESSED in secret


def test_the_highlight_folds_macrons_both_ways_and_marks_word_starts_only():
    assert panes.mark("Te Pāti Māori", ["maori"]) == "Te Pāti <mark>Māori</mark>"
    assert panes.mark("Maori Party", ["maori"]) == "<mark>Maori</mark> Party"        # "Māori" folds to the same word
    from products.board import search
    assert panes.mark("Ngā Māori, MAORI", search.words_of("Māori")) == "Ngā <mark>Māori</mark>, <mark>MAORI</mark>"
    assert panes.mark("Hartley Hart", ["hart"]) == "<mark>Hart</mark>ley <mark>Hart</mark>"
    assert panes.mark("Smart", ["art"]) == "Smart"                                  # not a word start: the search would not match it either
    assert panes.mark("<b>x</b> x", ["x"]) == "&lt;b&gt;<mark>x</mark>&lt;/b&gt; <mark>x</mark>"


def test_links_section_says_plainly_when_nothing_is_built_and_lists_confirmed_first():
    html = panes.links_section(NO_LINKS, {}, "q", [], lambda ref: None)
    assert "no links built yet" in html
    v = cat.BY_NAME["directors"]
    links = {"built": True, "why": "", "near": [{"other": "companies:companies/1/director/b", "register": "companies", "rule": "full-name@1",
                                                "reason": "common name", "decisions": [], "evidence": {}}],
             "confirmed": [{"other": "house:ge-2020/x", "register": "house", "rule": "same-role@1", "reason": None, "decisions": [], "evidence": {}}]}
    html = panes.links_section(links, {}, "q", ["directors:k"], lambda ref: (v, director(key=ref.split(":", 1)[1])))
    assert html.index("<strong>confirmed</strong>") < html.index("<strong>near</strong>")
    assert "near because common name" in html and "@1" not in html                           # ruling 84: words, never the id
    assert "same first, middle and last name (links rule full-name, version 1)" in html
    assert "links rule same-role (links rule same-role, version 1)" in html                 # an id the table lacks is named, not hidden


def test_person_pane_keeps_namesakes_apart():
    v = cat.BY_NAME["directors"]
    r = director()
    other = director(key="companies/2/director/z", entity_key="companies/2")
    html = panes.person_pane(ctx(v, r, group={"built": False, "why": "no links built yet", "rows": []},
                                 same={"companies": [(v, 1, [other])], "held": {"directors"}}))
    assert "Possible namesakes, apart" in html and "companies%2F2%2Fdirector%2Fz" in html
    assert "Candidates, not identity" in html


def test_page_wraps_panes_with_the_search_and_the_save_form():
    html = panes.page("doe", ["directors:k"], ["<section class=\"pane\">x</section>"], "pinned")
    assert 'name="q" value="doe"' in html and 'action="/save"' in html and "pinned" in html
    assert re.findall(r'<script src="([^"?]*)', html) == ["/static/chat.js"]     # ruling 122: the chat pane is the one script


def test_every_pane_offers_a_report_from_here_only_when_a_report_server_is_named():
    v = cat.BY_NAME["directors"]
    r = director()
    ref = f"{v.register}:{r['key']}"
    report = panes.report_href("http://10.0.0.2:8440/", ref)
    assert report == f"http://10.0.0.2:8440/report/{v.register}:companies/1/director/a"
    link = f'<a href="{report}">report from here</a>'
    assert panes.row_pane(ctx(v, r, report=report)).count(link) == 1
    person = {"v": v, "row": r, "q": "doe", "path": [], "group": {"built": False, "why": "no links built yet"},
              "same": {"held": set()}, "report": report}
    assert panes.person_pane(person).count(link) == 1
    assert panes.report_href("", ref) == ""                       # no server named, no link
    assert "report from here" not in panes.row_pane(ctx(v, r, report=""))
    assert "report from here" not in panes.person_pane({**person, "report": ""})


# ── ruling 81: "search all" and the register boxes, apart ────────────────

HELD = ["parties", "companies"]


def test_the_first_view_of_either_tab_ticks_search_all_and_no_register():
    for action in ("/", "/graph"):
        left = panes.left_pane("", HELD, search.FIRST, action=action)
        assert boxes_shown(left) == (True, [])
        assert '<input type="hidden" name="all" value="0">' in left      # the form says it was sent; the box says what was ticked
        assert "was_all" not in left


def test_search_all_searches_every_held_register_whatever_is_ticked_and_off_only_the_ticked():
    on = search.boxes_of({"all": ["0", "1"], "r": ["companies"]})
    assert search.selection(on, HELD) == tuple(HELD)
    assert boxes_shown(panes.left_pane("doe", HELD, on)) == (True, ["companies"])     # the tick shows, not acted on
    results = panes.results_pane("doe", {}, set(), search.selection(on, HELD), on)
    assert "every held register" in results and "Registered political parties" in results
    off = search.boxes_of({"all": ["0"], "r": ["companies"]})
    assert search.selection(off, HELD) == ("companies",)
    results = panes.results_pane("doe", {}, set(), search.selection(off, HELD), off)
    assert "Registered political parties" not in results and "every held register" not in results


def test_the_boxes_ride_every_href_so_search_all_off_and_on_loses_no_tick():
    ticks = ["parties", "companies"]
    for form in (["0"], ["0", "1"], ["0"]):              # off, on, off again across three searches
        b = search.boxes_of({"all": form, "r": ticks})
        assert boxes_shown(panes.left_pane("doe", HELD, b)) == ("1" in form, ticks)
        v = cat.BY_NAME["directors"]
        company = {"key": "companies/1", "name": "ACME LIMITED"}
        row = panes.row_pane(ctx(v, director(), boxes=b, parent=("Company", "companies", company)))
        person = panes.person_pane(ctx(v, director(), boxes=b, group={"built": False, "why": "no links built yet"}))
        hit = panes.hit("doe", v, director(), ["doe"], b)
        page = "".join(panes.page("doe", ["directors:k"], [row], "", b, tab=t) for t in ("search", "uses"))
        g = {"nodes": {"directors:a": {"v": v, "row": director(key="a"), "matched": True, "centre": False, "order": 0, "parent": None},
                       "companies:c": {"v": cat.BY_NAME["companies"], "row": company, "matched": False, "centre": False, "order": 1, "parent": "directors:a"}},
             "edges": [{"kind": "role", "a": "directors:a", "b": "companies:c", "label": "Director", "cite": "directors:a"}],
             "drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS}, "not_drawn": {k: 0 for k, _, _ in cat.EDGE_KINDS},
             "matched_total": 1, "unresolved": 0, "centre": ""}
        picture = graph.pane(g, "doe", b, tuple(ticks))
        links = hrefs(row + person + hit + page + picture)
        assert any("gv=1" in h and "d=companies" in h for h in links)              # a node re-centres beside the results
        assert not any(h.startswith("/graph") for h in hrefs(page)) and any(h.startswith("/?") for h in hrefs(page))   # ruling 111: no graph tab
        assert not any("g=" in h for h in links)                                  # the graph has one state (ruling 120)
        assert len(links) >= 8 and all(carried(h) == b for h in links), [h for h in links if carried(h) != b]
        pin = row[row.index('action="/pin"'):]
        sent = urllib.parse.parse_qs(urllib.parse.urlencode(re.findall(r'<input type="hidden" name="(all|r)" value="([^"]*)">', pin)))
        assert search.boxes_of(sent) == b                                         # the pin and save forms carry them too


def test_search_all_off_with_nothing_ticked_searches_nothing_and_says_so():
    b = search.boxes_of({"all": ["0"], "q": ["doe"]})
    assert b == search.Boxes(False, ()) and search.selection(b, HELD) == ()
    results = panes.results_pane("doe", {}, set(HELD), (), b)
    assert panes.NOTHING_TICKED == "tick a register, or search all" and panes.NOTHING_TICKED in results
    assert "none found" not in results and "<h3>" not in results
    assert boxes_shown(panes.left_pane("doe", HELD, b)) == (False, [])


def test_a_saved_path_and_an_old_address_open_as_the_first_view():
    saved = panes.paths_pane([{"name": "walk", "query": "doe", "path": "directors:k\ncompanies:c", "made_at": None}])
    pinned = panes.pins_pane([{"title": "Jane", "view": "directors", "key": "k", "made_at": None}])
    for link in hrefs(saved + pinned) + ["/?q=doe&p=directors%3Ak", "/graph?q=doe"]:
        assert "all=" not in link and "r=" not in link
        assert carried(link) == search.FIRST
    assert boxes_shown(panes.left_pane("doe", HELD, carried("/?q=doe"))) == (True, [])
