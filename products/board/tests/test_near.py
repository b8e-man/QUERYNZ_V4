"""Near matches (ruling 83): a person name with its given name and surname
reversed against the query, and an address that is a close match by keys'
address fold; never among the exact results or in their count; capped,
with the whole count; the same panes, highlighting and suppression as an
exact row; only over the registered addresses organisations publish."""
import re

from products.board import catalogue as cat
from products.board import near, panes, search


def test_a_reversed_name_is_found_with_or_without_a_comma():
    rev = near.is_reversed
    assert rev("MILLS PHILLIP", "phillip", [], ["mills"])
    assert rev("Phillip, Mills", "phillip", [], ["mills"])                 # the given name filed in the family's place
    assert not rev("Phillip Mills", "phillip", [], ["mills"])               # the right way round is exact, not near
    assert not rev("Mills, Phillip", "phillip", [], ["mills"])              # the Commission's inversion, read right
    assert rev("Hon Mills Phillip", "phillip", [], ["mills"])               # honorifics off, as keys.names does
    assert not rev("Mills Phillip Holdings Ltd", "phillip", [], ["mills"])  # an organisation is no person's name
    assert not rev("Millsom Phillip", "phillip", [], ["mills"])


def test_a_middle_name_may_be_absent_and_an_initial_matches_the_name_it_begins():
    rev = near.is_reversed
    assert rev("Smith John Graham", "john", ["graham"], ["smith"])
    assert rev("Smith John", "john", ["graham"], ["smith"])                 # absent on the row's side
    assert rev("Smith John Graham", "john", [], ["smith"])                  # absent on the query's side
    assert not rev("Smith John Peter", "john", ["graham"], ["smith"])
    assert rev("SMITH J", "john", [], ["smith"]) and rev("Smith John", "j", [], ["smith"])
    assert not rev("Smith Jane", "john", [], ["smith"])
    assert rev("Lu, Janet De", "janet", [], ["de", "lu"]) is False          # 'De Lu, Janet' read right is not reversed
    assert rev("De Lu Janet", "janet", [], ["de", "lu"])


def test_the_query_comes_from_the_name_fields_else_a_name_in_the_box():
    assert near.name_query("", {"first": "Phillip", "last": "Mills"}) == ("phillip", [], ["mills"])
    assert near.name_query("", {"first": "John Graham", "last": "Smith"}) == ("john", ["graham"], ["smith"])
    assert near.name_query("Graeme Hart", {}) == ("graeme", [], ["hart"])
    assert near.name_query("Hart", {}) is None and near.name_query("12 Queen St", {}) is None
    assert near.name_query("Rank Group Ltd", {}) is None


def test_the_sql_filter_holds_every_reversed_form():
    def are(p):
        return p.replace(r"\m", r"(?<!\w)(?=\w)").replace(r"\M", r"(?<=\w)(?!\w)")
    _, ps = near.name_filter(cat.Name("donor"), "phillip", ["mills"])
    whole, hon, nocomma, _, comma = ps
    for name in ("mills phillip", "mills  phillip graham", "hon mills phillip", "phillip, mills", "p, mills", "mills p."):
        n = re.sub(are(hon), "", name)
        assert re.search(are(whole), name) and (re.search(are(nocomma), n) or re.search(are(comma), n)), name
    assert not re.search(are(nocomma), "mills, phillip") and not re.search(are(comma), "mills, phillip")


def test_a_close_address_is_the_same_street_number_and_street_by_the_fold():
    q = near.reading("253 Queen Street, Auckland")
    near_to = lambda text: near.is_near_address(q, near.reading(text))
    assert near_to("Level 4, 253 Queen St, Auckland Central, Auckland 1010")    # a level, a spelling, a suburb
    assert near_to("Unit 3, 253 Queen Street")
    assert near_to("3/253 Queen St")
    assert not near_to("255 Queen Street, Auckland")                            # another number
    assert not near_to("253 Queen Street, Masterton")                           # another town
    assert not near_to("253 King Street, Auckland")
    p = near.reading("253 Queen Street, Auckland 1010")
    assert not near.is_near_address(p, near.reading("253 Queen Street, Auckland 0600"))   # another postcode
    assert near.reading("PO Box 253, Auckland")["street"] == ""                 # a box is not a street
    fb = near.reading("Unit 3, 12 Flat Bush Road")
    assert fb["street"] == near.reading("12 Flat Bush Rd")["street"] != ""       # 'Flat' before a street is no unit
    assert near.reading("12 Post Office Road")["street"] == "12postofficerd"
    b = near.reading("Level 2, Vero Centre, Auckland")
    assert near.is_near_address(b, near.reading("Level 9, Vero Centre, Auckland"))   # the same building, another level


def test_near_reads_only_the_registered_address_columns_and_keeps_the_guards():
    seen = []

    class Conn:
        pass

    orig = near.db.rows
    near.db.rows = lambda conn, sql, params=(): seen.append(sql) or []
    held = {v.name for v in cat.VIEWS}
    try:
        out = near.near(Conn(), "", {"address": "253 Queen St"}, held=held)
        addr_views = {re.search(r"from pub\.(\w+)", s).group(1) for s in seen}
        seen.clear()
        names = near.near(Conn(), "", {"first": "Phillip", "last": "Mills"}, held=held)
        both = near.near(Conn(), "", {"address": "253 Queen St", "first": "Phillip", "last": "Mills"}, held=held)
    finally:
        near.db.rows = orig
    assert addr_views == {v for v, _ in cat.ADDRESS_COLUMNS}                      # never a person's view
    assert names["addresses"]["why"].startswith("not tried") and out["names"]["why"].startswith("not tried")
    for s in seen:
        v = cat.BY_NAME[re.search(r"from pub\.(\w+)", s).group(1)]
        assert v.kind in ("person", "figure", "event", "organisation", "document") and cat.fields_of(v).names
        assert not v.suppressed or f"not coalesce({v.suppressed}, false)" in s     # the suppression guard is kept (hard limit 16)
        assert " and not coalesce((" in s                                         # the exact rows are ruled out
    assert both["addresses"]["total"] == 0 and both["names"]["total"] == 0        # no view holds both: "and" finds none


def test_the_section_is_closed_below_the_results_capped_and_never_in_the_exact_count():
    v = cat.BY_NAME["party_return_donors"]
    rows = [(v, {"key": f"k{i}", "donor": "MILLS PHILLIP", "amount": 1, "document": "ab" * 32}) for i in range(near.NEAR_LIMIT)]
    nb = {"names": {"total": 40, "more": False, "rows": rows, "refs": []},
          "addresses": {"total": 0, "why": "not tried: fill the address field"}}
    held = {"party_return_donors"}
    html = panes.results_pane("", {}, held, ("party_returns",), search.Boxes(True, (), (("first", "Phillip"), ("last", "Mills"))),
                              ["phillip", "mills"], nb)
    exact, below = html.split('<details class="near" id="near">')
    assert '<span class="count">0</span>' in exact                                # the exact count is the exact rows alone
    assert "<details class=\"near\" id=\"near\" open" not in html                  # closed until clicked
    assert below.count('class="nearwhy">near: given name and surname reversed') == near.NEAR_LIMIT
    assert "and 15 more" in below and "Near matches <span class=\"count\">40</span>" in below
    assert "<mark>MILLS</mark> <mark>PHILLIP</mark>" in below and "p=party_return_donors%3Ak0" in below
    assert "not tried: fill the address field" in below


def test_a_suppressed_near_row_shows_no_name():
    v = cat.BY_NAME["directors"]
    r = {"key": "d1", "full_name": "Hidden Person", "suppressed": True, "document": "ab" * 32}
    html = panes.near_section("", {"names": {"total": 1, "rows": [(v, r)], "refs": []}, "addresses": {"total": 0, "rows": []}},
                              ["hidden"], None)
    assert "Hidden Person" not in html and panes.SUPPRESSED in html
