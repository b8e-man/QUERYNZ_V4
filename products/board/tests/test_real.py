"""Against the real published tables through the session reader (slow):
the outside check is green, a search is quick, a four-pane walk renders,
the search tab marks a macron-folded word in the registers checked only,
and the graph tab draws a busy row quickly with every far end real."""
import re
import time

import pytest

from products.board import catalogue as cat
from products.board import assets, check, db, graph, people, search, server

pytestmark = pytest.mark.slow


def test_the_outside_check_is_green():
    with db.read_connect() as conn:
        assert check.problems(conn) == []


def test_a_search_answers_within_two_seconds():
    with db.read_connect() as conn:
        t = time.time()
        res = search.search(conn, "Graeme Hart")
        assert time.time() - t < 2.0
        assert "party_returns" in res or "disclosures" in res


def test_a_person_pane_renders_with_namesakes_apart():
    with db.read_connect() as conn:
        d = db.rows(conn, "select key from pub.directors where not coalesce(suppressed, false) order by key limit 1")[0]["key"]
        html = server.render("", server.parse_path(f"directors:{d}|person:directors:{d}"), conn=conn)
    assert html.count('<section class="pane') == 4 and "Possible namesakes, apart" in html     # the left pane, the results, two panes


def test_the_search_tab_marks_maori_as_maori_in_the_registers_checked_only():
    with db.read_connect() as conn:
        html = server.render("Maori", [], conn=conn, boxes=search.Boxes(False, ("iwi_directory",)))
    results = html[html.index('id="results"'):]
    assert "<mark>Māori</mark>" in results                        # "Maori" typed marks "Māori" filed
    assert "<strong>iwi_directory_entities</strong>" in results
    assert "Registered political parties" not in results           # an unchecked register is not searched


def test_the_graph_of_a_busy_company_is_quick_and_every_far_end_is_a_row():
    with db.read_connect() as conn:
        c = db.rows(conn, "select entity_key from pub.directors group by 1 order by count(*) desc limit 1")[0]["entity_key"]
        t = time.time()
        g = graph.build(conn, "", centre=f"companies:{c}")
        assert time.time() - t < 5.0
        assert g["drawn"]["role"] >= 1 and len(g["nodes"]) <= graph.MAX_NODES
        for nid in g["nodes"]:
            view, _, key = nid.partition(":")
            assert search.row(conn, view, key) is not None, nid


def test_the_field_search_is_quick_and_a_last_name_is_a_whole_word():
    with db.read_connect() as conn:
        t = time.time()
        res = search.search(conn, "", limit=search.RESULTS_LIMIT, fields={"first": "Graeme", "last": "Hart"})
        assert time.time() - t < 3.0
        names = [n for reg, hits in res.items() if reg != "held" for v, _, rows in hits for r in rows for n in check._names(v, r)]
    assert names and all("hart" in cat.fold_term(n).replace(",", " ").split() for n in names)


def test_near_matches_render_closed_below_the_results_within_three_seconds():
    """A reversed name where the order is stated (the directors' parts) is near;
    on a form that fixes none (the party donors, ruling 85) it is exact."""
    with db.read_connect() as conn:
        t = time.time()
        html = server.render("", [], conn=conn, boxes=search.Boxes(True, (), (("first", "James"), ("last", "Taylor"))))
        assert time.time() - t < 3.0
        mills = server.render("", [], conn=conn, boxes=search.Boxes(True, (), (("first", "Phillip"), ("last", "Mills"))))
    exact, below = html.split('<details class="near" id="near">')
    assert "directors" in below and "near: given name and surname reversed" in below
    assert "narrowed by: first name" in exact
    scripts = re.findall(r'<script\b[^>]*\bsrc="([^"]*)"', html)                    # ruling 108: the graph beside the results,
    assert scripts == [assets.url(n) for n in assets.SCRIPTS]                            # from the board's own files alone
    exact, below = mills.split('<details class="near" id="near">')
    assert "party_return_donors" in exact and "near: given name and surname reversed" not in below


def test_every_links_rule_in_pub_links_has_its_words():
    """Ruling 84: each rule id pub.links carries is in catalogue.RULE_WORDS,
    so no edge falls back to "links rule <id>" on the live data."""
    with db.read_connect() as conn:
        rules = {r["rule"] for r in db.rows(conn, "select distinct rule from pub.links")}
    assert rules
    lacking = sorted(r for r in rules if r.partition("@")[0] not in cat.RULE_WORDS)
    assert not lacking, lacking


def test_a_known_donor_with_returns_in_two_years_gets_one_party_edge_whose_total_equals_its_listed_addends():
    """Ruling 86 (3), on the live tables: check.gift_problems reads the
    rendered list under the party and the register's own sum."""
    with db.read_connect() as conn:
        centre = check.known_donor(conn)
        assert centre
        g = graph.build(conn, "", centre=centre)
        assert check.gift_problems(conn) == []
    money = [e for e in g["edges"] if e["kind"] == "money"]
    assert len(money) == 1 and money[0]["b"].startswith("parties:")
    assert sum(1 for n in g["nodes"] if n.startswith("party_return_donors:")) == 1     # one donor node, not one per row
    assert len(money[0]["addends"]) >= 2


def test_a_known_cited_document_opens_from_its_source_link_and_a_wrong_sha_does_not():
    """Rulings 86 (4) and 88, on the live store: check.doc_problems answers each case."""
    with db.read_connect() as conn:
        assert check.doc_problems(conn) == []


def test_a_cited_document_of_every_cited_source_opens():
    """Ruling 88: no source is refused; the party returns among those a row cites."""
    with db.read_connect() as conn:
        by_source = check.cited_by_source(conn)
        assert "party_returns" in by_source and "house" in by_source
        for source, (sha, kind) in by_source.items():
            assert check.opened_problems(conn, sha, kind, source) == [], source


def test_a_directors_row_shows_its_companys_name_not_its_key():
    """Ruling 92 (2), live: the company field reads the company's name, linked, the key on hover."""
    with db.read_connect() as conn:
        d = db.rows(conn, "select d.key, d.entity_key, c.name from pub.directors d join pub.companies c on c.key = d.entity_key "
                          "where not coalesce(d.suppressed, false) order by d.key desc limit 1")[0]
        html = server.render("", [f"directors:{d['key']}"], conn=conn)
    from products.board import panes
    assert f'title="{panes.esc(d["entity_key"])}">{panes.esc(d["name"])}</a>' in html
    assert f"<td>{d['entity_key']}</td>" not in html


def test_the_near_names_button_answers_200_and_lists_counts():
    """Ruling 92 (4), live over HTTP: the button's GET (`near=1`) answers 200 with the pane and its counts."""
    import re
    import threading
    import urllib.request
    httpd = server.Server(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{httpd.server_address[1]}/?q=garry+payinda&all=1&near=1"
        with urllib.request.urlopen(url, timeout=60) as r:
            assert r.status == 200
            html = r.read().decode()
    finally:
        httpd.shutdown()
    pane = html[html.index('id="near-names"'):html.index('id="results"')]
    assert re.search(r'<h3>garry payinda <span class="count">[\d,]+ rows</span></h3>', pane)
    assert re.search(r'</a> <span class="count">[1-9][\d,]*</span>', pane)       # at least one variant, with its count


def test_a_registers_table_answers_with_100_rows_and_its_count():
    """Ruling 92 (5), live: the directors table, 100 one-line rows and the count of all rows."""
    import re
    with db.read_connect() as conn:
        n = db.rows(conn, "select count(*) as n from pub.directors")[0]["n"]
        t = time.time()
        html = server.render("", [], conn=conn, boxes=search.Boxes(table="directors"))
        assert time.time() - t < 5.0
    tab = html[html.index('id="table"'):]
    assert f"{n:,} rows in directors" in tab and len(re.findall(r"<tr><td", tab)) == 100


def test_both_field_modes_against_the_same_fixture_rows():
    """Ruling 92 (6): four fixture rows in a temporary table of pub.directors' shape (gone with the connection),
    searched by the board's own SQL under "all" and "any" (first Garry, last Payinda, year 2020)."""
    import datetime as dt
    rows = [("a", "Garry", "PAYINDA", dt.date(2020, 3, 1)),      # all three
            ("b", "Garry", "SMITH", dt.date(2019, 3, 1)),        # first only
            ("c", "Ann", "PAYINDA", dt.date(2018, 3, 1)),        # last only
            ("d", "Ann", "SMITH", dt.date(2001, 3, 1))]          # none
    fields = {"first": "Garry", "last": "Payinda", "year": "2020"}
    got = {}
    with db.read_connect() as conn:
        conn.execute("create temporary table directors (like pub.directors)")
        for key, first, last, on in rows:
            conn.execute("insert into pg_temp.directors (key, first_name, last_name, full_name, appointed_on, suppressed) "
                         "values (%s, %s, %s, %s, %s, false)", (key, first, last, f"{first} {last}", on))
        for mode in (search.ALL, search.ANY):
            sql, params = search.view_sql(cat.BY_NAME["directors"], [], None, 50, fields=fields, mode=mode)
            got[mode] = {r["key"]: r for r in db.rows(conn, sql.replace("from pub.directors", "from pg_temp.directors"), params)}
    assert sorted(got[search.ALL]) == ["a"]
    assert sorted(got[search.ANY]) == ["a", "b", "c"]
    said = lambda k: sorted(f[len("_matched_"):] for f, x in got[search.ANY][k].items() if f.startswith("_matched_") and x)
    assert said("a") == ["first", "last", "year"] and said("b") == ["first"] and said("c") == ["last"]


def test_removed_companies_against_fixture_rows_under_both_settings():
    """Ruling 93: five fixture rows in a temporary table of pub.companies' shape (gone with the connection),
    searched by the board's own SQL with "show removed companies" unticked and ticked, at a limit of two."""
    rows = [("a", "Registered"), ("b", "REMOVED"), ("c", " dissolved"), ("d", "In Liquidation"), ("e", None)]
    got = {}
    with db.read_connect() as conn:
        conn.execute("create temporary table companies (like pub.companies)")
        for key, status in rows:
            conn.execute("insert into pg_temp.companies (key, name, status) values (%s, %s, %s)",
                         (key, f"FIXTURE FLETCHER {key.upper()} LIMITED", status))
        for removed in (False, True):
            sql, params = search.view_sql(cat.BY_NAME["companies"], ["fixture", "fletcher"], None, 2, removed=removed)
            got[removed] = db.rows(conn, sql.replace("from pub.companies", "from pg_temp.companies"), params)
        sql, params = search.view_sql(cat.BY_NAME["companies"], ["fixture", "fletcher", "c"], None, 2, removed=False)
        only_removed = db.rows(conn, sql.replace("from pub.companies", "from pg_temp.companies"), params)
    assert [r["key"] for r in got[False]] == ["a", "d"] and got[False][0]["total"] == 3 and got[False][0]["hidden"] == 2
    assert [r["key"] for r in got[True]] == ["a", "b"] and got[True][0]["total"] == 5 and "hidden" not in got[True][0]
    assert len(only_removed) == 1 and only_removed[0]["key"] is None and only_removed[0]["hidden"] == 1


def test_the_tabbed_search_answers_within_two_seconds_in_both_states():
    """Ruling 108: the search with the results pane's tabs, and the entity state's gathering and entity search on top
    of it, inside the search's floor."""
    with db.read_connect() as conn:
        regs = search.held_registers(db.pub_views(conn))
        t = time.time()
        res = search.search(conn, "Graeme Hart", limit=search.RESULTS_LIMIT, registers=regs, tabs=True)
        rows_state = time.time() - t
        hits = [(v, r) for reg in regs for v, _, rs in res.get(reg, []) for r in rs]
        ents = people.gather(conn, hits, people.named_groups(conn, "Graeme Hart", registers=regs))
        both = time.time() - t
    assert res["tabs"] == search.BOX and rows_state < 2.0 and both < 2.0, (rows_state, both)
    assert ents["entity"] and ents["named"]                       # he is gathered, and found by name


def test_the_entity_search_finds_a_group_no_row_of_the_list_heads():
    """Ruling 108 (3): with every register's list cut to one row, the groups found by name are still listed."""
    with db.read_connect() as conn:
        regs = search.held_registers(db.pub_views(conn))
        res = search.search(conn, "Graeme Hart", limit=1, registers=regs, tabs=True)
        hits = [(v, r) for reg in regs for v, _, rs in res.get(reg, []) for r in rs]
        named = people.named_groups(conn, "Graeme Hart", registers=regs)
        ents = people.gather(conn, hits, named)
    in_hand = set(ents["group"].values())
    assert set(ents["named"]) - in_hand                            # a group no row in hand falls in, found by its rows' name
    for gid in set(ents["named"]) - in_hand:
        assert ents["entity"][gid]["label"] and ents["entity"][gid]["centre"]


def test_a_succession_is_one_frame_in_both_states_within_the_floor():
    """Ruling 106 (2): a company of links-3's sample, centred, draws its lineage frame in date order with its people
    on both, in the rows and the entity state, and the lineage step costs the graph little (one query by key, and
    one more for a chain's new ends)."""
    from products.board import lineage
    with db.read_connect() as conn:
        centre, links = check.lineage_case(conn)
        assert centre and links
        for people_state in (False, True):
            t = time.time()
            g = graph.build(conn, "", centre=centre, people=people_state)
            assert time.time() - t < 2.0
            f = next(f for f in g["lineage"] if f["companies"])
            assert len(set(f["companies"])) == len(f["companies"]) >= 2 and f["people"]
        t = time.time()
        found = lineage.chain(conn, [links_ref for l in links for links_ref in (l["row_a"], l["row_b"])])
        assert time.time() - t < 0.5 and found


def test_the_lineage_check_goes_red_when_a_frame_merges_its_companies(monkeypatch):
    """Item 24 can fail on the real tables: two companies of the frame drawn as one node."""
    from products.board import lineage
    real = lineage.relabel

    def merged(frames, node_of):
        out = real(frames, node_of)
        for f in out:
            f["companies"] = [f["companies"][0]] * len(f["companies"])
        return out
    monkeypatch.setattr(people.lineage, "relabel", merged)
    with db.read_connect() as conn:
        assert any("merged" in p for p in check.lineage_problems(conn))
