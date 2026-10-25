"""Ruling 92 (4): the near-names button and pane. The variants table is data
with no duplicate and every entry folded; "garry payinda" lists its variants
filed with the surname, each with its count; a variant's link adds it to the
search as an alternative in the given name's place ("garry|garreth"), and
the search then matches either name there; the pane says a variant is a
candidate, never a link."""
import re
import urllib.parse

from products.board import catalogue as cat
from products.board import given_names, near, panes, search


def test_the_variants_table_has_no_duplicates_and_every_entry_is_lower_case_folded():
    seen = set()
    for g in given_names.GROUPS:
        assert len(g) == len(set(g)) >= 2, g                       # no name twice in a group
        assert frozenset(g) not in seen, g                          # no group twice
        seen.add(frozenset(g))
        for n in g:
            assert n == cat.fold_term(n) and re.fullmatch(r"[a-z]+", n), n
    for a, b in (("garry", "gareth"), ("garry", "garreth"), ("bill", "william"), ("mike", "michael"),
                 ("hemi", "james"), ("hone", "john"), ("wiremu", "william")):
        assert b in given_names.variants_of(a) and a in given_names.variants_of(b), (a, b)
    assert "garry" not in given_names.variants_of("garry")


def test_why_a_held_name_is_offered():
    assert given_names.why_near("garry", "garreth") == given_names.COMMON
    assert given_names.why_near("garry", "garfield") == given_names.PREFIX
    assert given_names.why_near("ana", "ann") == given_names.ONE_APART
    assert given_names.why_near("garry", "g") is None and given_names.why_near("garry", "garry") is None
    assert given_names.why_near("garry", "john") is None
    assert given_names.levenshtein("garry", "gary") == 1 and given_names.levenshtein("kitten", "sitting") == 3


HELD = {"garry": 4, "garreth": 2, "gary": 1, "garfield": 1, "john": 9, "harry": 3}


def test_garry_payinda_lists_its_variants_with_their_counts():
    d = near.near_names(None, "garry payinda", {}, words=HELD)
    assert d["surname"] == ["payinda"]
    (g,) = d["given"]
    assert g["typed"] == "garry" and g["count"] == 4
    got = {w: (n, why) for w, n, why in g["variants"]}
    assert got["garreth"] == (2, given_names.COMMON) and got["gary"][0] == 1 and got["garfield"][1] == given_names.PREFIX
    assert got["harry"][1] == given_names.ONE_APART and "john" not in got and "garry" not in got
    assert [w for w, _, _ in g["variants"]][0] == "harry"            # by count, then name
    assert near.near_names(None, "payinda", {}, words=HELD)["why"] == near.NO_NAME


def test_a_variant_link_adds_an_alternative_in_the_given_names_place_and_keeps_the_pane_open():
    boxes = search.Boxes(False, ("companies",))
    html = panes.near_names_pane("Garry Payinda", near.near_names(None, "Garry Payinda", {}, words=HELD), boxes)
    assert "never a link the board made" in html and "no link by looking" in html
    links = dict((re.sub("<[^>]+>", "", t), h.replace("&amp;", "&")) for h, t in re.findall(r'<a href="([^"]*)">([^<]*)</a>', html))
    qs = urllib.parse.parse_qs(urllib.parse.urlsplit(links["garreth"]).query)
    assert qs["q"] == ["Garry|garreth Payinda"] and qs["near"] == ["1"] and qs["r"] == ["companies"] and qs["all"] == ["0"]
    chosen = panes.near_names_pane("Garry|garreth Payinda", near.near_names(None, "Garry|garreth Payinda", {}, words=HELD), boxes)
    assert "in the search as alternatives: garreth" in chosen
    remove = re.search(r'garreth <a href="([^"]*)">remove</a>', chosen).group(1).replace("&amp;", "&")
    assert urllib.parse.parse_qs(urllib.parse.urlsplit(remove).query)["q"] == ["Garry Payinda"]


def test_from_the_name_fields_the_variant_goes_into_the_first_name_field():
    boxes = search.Boxes(True, (), (("first", "garry"), ("last", "payinda")))
    asked = boxes.asked()
    html = panes.near_names_pane("", near.near_names(None, "", asked, words=HELD), boxes)
    h = re.search(r'<a href="([^"]*)">garreth</a>', html).group(1).replace("&amp;", "&")
    qs = urllib.parse.parse_qs(urllib.parse.urlsplit(h).query)
    assert qs["first"] == ["garry|garreth"] and qs["last"] == ["payinda"] and qs.get("q", [""]) == [""]


def test_an_alternative_is_an_or_within_the_name_position():
    v = cat.BY_NAME["directors"]
    clause, params = search.match_sql(v, search.words_of("garry|garreth payinda"))
    assert params[:2] == [r"\m(?:garry|garreth)", r"\mpayinda"] and clause.count(" ~ %s") == 2
    plain, comma, one = search.name_patterns("first", "garry|garreth", cat.GIVEN_FAMILY)
    assert "(?:garry|garreth)" in plain and re.search(plain.replace(r"\m", r"\b").replace(r"\M", r"\b"), "garreth payinda")
    assert search.words_of("a || b|") == ["a", "b"] and search.base_term("Garry|garreth Payinda") == "Garry Payinda"
    assert panes.search_words("garry|garreth payinda", None) == ["garry", "garreth", "payinda"]


def test_the_button_sits_beside_the_search_box_on_the_search_tab_only():
    assert '<button name="near" value="1"' in panes.left_pane("x", [], search.FIRST)
    assert 'name="near"' not in panes.left_pane("x", [], search.FIRST, action="/graph")
