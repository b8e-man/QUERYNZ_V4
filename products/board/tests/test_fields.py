"""The field search (ruling 82): six fields, each matched as whole words in
the columns a view declares for it; a one-string name read in its places
by its view's declared order (ruling 85), a comma read family then given;
the address field only over the registered addresses organisations
publish; the fields ride every href with the ticks; the plain box alone is
unchanged. Pure: the database's patterns are run here through Python's re."""
import re
import urllib.parse

from products.board import catalogue as cat
from products.board import panes, search


def fold(text: str) -> str:
    """The SQL's fold: lower, then macrons off."""
    return text.lower().translate(str.maketrans(*cat.MACRONS))


def are(pattern: str) -> str:
    """The database's word bounds in Python's dialect."""
    return pattern.replace(r"\m", r"(?<!\w)(?=\w)").replace(r"\M", r"(?<=\w)(?!\w)").replace(r"\y", r"\b")


def whole_name_matches(name: str, want: dict, order: str = cat.GIVEN_FAMILY) -> bool:
    """The one-string name rule as the SQL applies it (search._name_whole)."""
    n = re.sub(are(search._POST_SQL), "", re.sub(are(search._HON_SQL), "", fold(name)))
    for f, value in want.items():
        plain, comma, one = search.name_patterns(f, value, order)
        if not re.search(are(search.phrase(value)), fold(name)):
            return False
        ok = ("," not in n and re.search(are(plain), n)) or ("," in n and re.search(are(comma), n)) \
            or (one and not re.search(r"\S\s+\S", n) and re.search(are(one), n))
        if not ok:
            return False
    return True


def test_a_last_name_is_a_whole_word_and_in_a_given_family_name_the_last():
    assert not whole_name_matches("John Graham HARTNELL", {"last": "Hart"})        # ruling 82's case
    assert not whole_name_matches("John Graham HARTNELL", {"first": "graham", "last": "hart"})
    assert whole_name_matches("Graeme Richard Hart", {"last": "Hart"})
    assert not whole_name_matches("Hart Graeme", {"last": "Hart"})                 # given-first: the first word of two is not a surname
    assert not whole_name_matches("John Graham Smith", {"last": "Graham"})         # nor a middle word: the family place is the end
    assert whole_name_matches("Jacqui Dean MP (H)", {"first": "Jacqui", "last": "Dean"})   # a post-nominal and a bracket after it
    assert whole_name_matches("Hon Chris Bishop, MP", {"last": "Bishop"})          # a post-nominal's comma is no inversion
    assert whole_name_matches("Hart", {"last": "Hart"}) and whole_name_matches("Hart", {"first": "Hart"})   # one word: either
    assert whole_name_matches("Hart, Graeme", {"last": "hart", "first": "graeme"})  # the Commission's inversion
    assert not whole_name_matches("Graeme, Hart", {"last": "hart"})
    assert whole_name_matches("Rt Hon Dr Winston Peters", {"first": "Winston", "last": "Peters"})   # honorifics are no word


def test_in_a_given_family_name_a_first_name_is_the_first_word_and_a_middle_name_neither_end():
    assert not whole_name_matches("MILLS PHILLIP", {"first": "Phillip", "last": "Mills"})
    assert not whole_name_matches("John Graham Smith", {"first": "Graham"})
    assert whole_name_matches("Mills, Phillip & Jackie", {"first": "Phillip", "last": "Mills"})
    assert whole_name_matches("John Graham Smith", {"middle": "Graham"})
    assert not whole_name_matches("John Graham Smith", {"middle": "John"}) and not whole_name_matches("John Smith", {"middle": "Smith"})
    assert whole_name_matches("Smith, John Graham", {"middle": "graham"}) and not whole_name_matches("Smith, John Graham", {"middle": "john"})
    assert whole_name_matches("Māui Pōmare", {"first": "maui", "last": "Pomare"})     # macrons folded both ways


def test_an_ambiguous_name_matches_last_and_first_in_either_order():
    """Ruling 85: a donor form fixes no order, so MILLS PHILLIP and Phillip Mills are both exact."""
    want = {"first": "Phillip", "last": "Mills"}
    for name in ("Mills Phillip", "MILLS PHILLIP", "Phillip Mills", "Hon Phillip Mills"):
        assert whole_name_matches(name, want, cat.AMBIGUOUS), name
    assert whole_name_matches("Mills Phillip", {"first": "Mills"}, cat.AMBIGUOUS)      # a first name alone: any word
    assert whole_name_matches("Phillip Mills", {"last": "Phillip"}, cat.AMBIGUOUS)
    assert not whole_name_matches("Mills Jackie", want, cat.AMBIGUOUS)                 # both words, or no match
    assert not whole_name_matches("Millsom Phillip", want, cat.AMBIGUOUS)              # whole words still
    assert whole_name_matches("Mills Phillip John", {"middle": "John"}, cat.AMBIGUOUS)
    assert not whole_name_matches("Mills Phillip John", {"middle": "Mills"}, cat.AMBIGUOUS)   # the first word is never a middle
    assert not whole_name_matches("Phillip Mills", {"middle": "Mills"}, cat.AMBIGUOUS)        # two words have no middle
    # the view's declaration carries it to the SQL
    sql, params = search.fields_sql(cat.BY_NAME["party_return_donors"], want)
    assert search.name_patterns("last", "Mills", cat.AMBIGUOUS)[0] in params
    assert search.name_patterns("last", "Mills", cat.GIVEN_FAMILY)[0] not in params


def test_a_comma_reads_family_then_given_in_every_order():
    for order in (cat.GIVEN_FAMILY, cat.FAMILY_GIVEN, cat.AMBIGUOUS):
        assert whole_name_matches("Mills, Phillip", {"last": "Mills", "first": "Phillip"}, order), order
        assert not whole_name_matches("Mills, Phillip", {"last": "Phillip"}, order), order
        assert not whole_name_matches("Mills, Phillip", {"first": "Mills"}, order), order
        assert whole_name_matches("MILLS, Phillip John", {"middle": "John"}, order), order


def test_a_given_family_name_is_not_matched_by_its_given_name_as_the_last():
    assert not whole_name_matches("Phillip Mills", {"last": "Phillip"}, cat.GIVEN_FAMILY)
    assert whole_name_matches("Phillip Mills", {"last": "Mills"}, cat.GIVEN_FAMILY)
    assert not whole_name_matches("Phillip Mills", {"first": "Mills"}, cat.GIVEN_FAMILY)


def test_a_family_given_name_with_no_comma_puts_the_last_name_first():
    assert whole_name_matches("Logie Jan", {"first": "Jan", "last": "Logie"}, cat.FAMILY_GIVEN)    # the workbook's form
    assert not whole_name_matches("Logie Jan", {"last": "Jan"}, cat.FAMILY_GIVEN)
    assert not whole_name_matches("Logie Jan", {"first": "Logie"}, cat.FAMILY_GIVEN)
    assert whole_name_matches("Smith John Graham", {"middle": "Graham"}, cat.FAMILY_GIVEN)
    assert not whole_name_matches("Smith John Graham", {"middle": "John"}, cat.FAMILY_GIVEN)


def test_every_name_declares_an_order_and_parts_are_parts():
    for name, fs in cat.FIELDS_OF.items():
        for g in fs.names:
            assert g.order in cat.ORDERS, (name, g)
            assert (g.order == cat.PARTS) == (not g.whole), (name, g)
    assert cat.FIELDS_OF["party_return_donors"].names[0].order == cat.AMBIGUOUS      # ruling 85's own example
    assert cat.FIELDS_OF["disclosures"].names[0].order == cat.AMBIGUOUS
    assert cat.FIELDS_OF["candidate_return_donors"].names[0].order == cat.AMBIGUOUS


def test_parts_are_matched_in_their_own_columns():
    sql, params = search.fields_sql(cat.BY_NAME["directors"], {"first": "Graeme", "middle": "Richard", "last": "Hart"})
    assert "lower(first_name)" in sql and "lower(middle_names)" in sql and "lower(last_name)" in sql and "full_name" not in sql
    assert params == [r"\mgraeme\M", r"\mrichard\M", r"\mhart\M"]
    sql, params = search.fields_sql(cat.BY_NAME["gazette_celebrants"], {"middle": "Ann"})
    assert "lower(given_names)" in sql and params == [r"\S\s+\S*\mann\M"]        # one column of given names: not its first word


def test_a_view_with_no_column_for_a_field_is_not_searched():
    assert search.fields_sql(cat.BY_NAME["companies"], {"last": "Hart"}) is None
    assert search.fields_sql(cat.BY_NAME["directors"], {"address": "1 Queen St"}) is None
    assert search.fields_sql(cat.BY_NAME["directors"], {"year": "20x3"}) is None
    assert search.view_sql(cat.BY_NAME["companies"], ["hart"], fields={"last": "Hart"}) is None
    sql, params = search.fields_sql(cat.BY_NAME["directors"], {"year": "2023"})
    assert "extract(year from appointed_on) = %s" in sql and params == [2023, 2023]


def test_organisation_matches_organisation_names_and_a_named_column_only_with_an_organisation_word():
    sql, params = search.fields_sql(cat.BY_NAME["party_return_donors"], {"org": "Rank Group"})
    assert "concat_ws(' ', party, party_label)" in sql and search.ORG_WORDS_SQL in params
    assert re.search(are(search.ORG_WORDS_SQL), "rank group ltd via graeme hart") and not re.search(are(search.ORG_WORDS_SQL), "graeme hart")
    assert "\\b" not in search.ORG_WORDS_SQL


def test_the_address_field_reads_only_registered_addresses_organisations_publish():
    for v in cat.VIEWS:
        fs = cat.fields_of(v)
        for c in fs.address:
            assert (v.name, c) in cat.ADDRESS_COLUMNS, (v.name, c)
        if fs.address:
            assert v.kind != "person", v.name                      # never a person's address (hard limit 15)
    assert {v for v, _ in cat.ADDRESS_COLUMNS} == {"company_addresses", "charities", "limited_partnerships"}


def test_every_declaration_names_a_view_and_a_column_the_board_knows_of():
    for name, fs in cat.FIELDS_OF.items():
        assert name in cat.BY_NAME, name
        for g in fs.names:
            assert g.columns() and (bool(g.whole) != bool(g.first or g.given or g.last)), (name, g)
    assert cat.field_columns(cat.BY_NAME["company_changes"]) == {"effective_on", "seen_on", "register_updated_on"}   # dates by default


def test_the_plain_box_alone_is_unchanged():
    for v in (cat.BY_NAME["companies"], cat.BY_NAME["directors"], cat.BY_NAME["gazette_prohibitions"]):
        assert search.view_sql(v, ["hart"], None) == search.view_sql(v, ["hart"], None, fields={})
        sql, _ = search.view_sql(v, ["hart"], None)
        assert "regexp_replace" not in sql and "extract(" not in sql


def test_fields_and_the_box_combine_with_and_and_keep_the_suppression_guard():
    sql, params = search.view_sql(cat.BY_NAME["directors"], ["graeme"], None, fields={"last": "Hart"})
    assert sql.index("concat_ws(' ', full_name, last_name)") < sql.index("translate(lower(last_name),")
    assert ") and (" in sql and "not coalesce(suppressed, false)" in sql
    assert params[:2] == [r"\mgraeme", r"\mhart\M"]


def test_the_fields_ride_every_href_and_the_form_shows_them():
    qs = {"all": ["0"], "r": ["companies"], "last": ["  Hart "], "year": ["2023"], "nonsense": ["x"]}
    b = search.boxes_of(qs)
    assert b == search.Boxes(False, ("companies",), (("last", "Hart"), ("year", "2023")))
    back = search.boxes_of(urllib.parse.parse_qs(urllib.parse.urlsplit(panes.href("q", ["companies:1"], b)).query))
    assert back == b
    assert search.boxes_of({}) == search.FIRST and search.FIRST.fields == ()
    left = panes.left_pane("", ["companies"], b)
    assert '<details class="fields" open>' in left and 'name="last" value="Hart"' in left
    assert left.count("<input name=") == 6
    closed = panes.left_pane("", ["companies"], search.FIRST)
    assert '<details class="fields">' in closed                      # closed by default
    assert "<script" not in left


def test_the_results_pane_says_which_fields_narrowed_the_search():
    b = search.Boxes(True, (), (("first", "Phillip"), ("last", "Mills")))
    held = {"party_return_donors", "agency_contract_costs"}
    html = panes.results_pane("", {}, held, ("party_returns", "contract_disclosures"), b, ["phillip", "mills"], None)
    assert "narrowed by: first name “Phillip”, last name “Mills”" in html
    party, acc = html.split("Party donation")[1].split("Agency contract")
    assert "none found</div>" in party                                                    # it holds names: none matched
    assert "none of its views holds a column for first name, last name" in acc           # ACC's costs name nobody
    assert panes.search_words("graeme", b) == ["graeme", "phillip", "mills"]


def test_the_graph_tab_searches_by_the_fields_and_says_so():
    from products.board import graph
    seen = {}
    orig, orig_pub = search.search, graph.db.pub_views
    search.search = lambda conn, q, **kw: seen.update(kw) or {"held": set()}
    graph.db.pub_views = lambda conn: set()
    try:
        g = graph.build(object(), "", regs=("party_returns",), fields={"last": "Hart"})
    finally:
        search.search, graph.db.pub_views = orig, orig_pub
    assert seen["fields"] == {"last": "Hart"} and seen["registers"] == ("party_returns",)
    html = graph.pane(g, "", search.Boxes(True, (), (("last", "Hart"),)), ("party_returns",))
    assert "none found" in html
