"""The start page's name search (ruling 92 item 7). The report may not import
the board (imports run one way), so its copy of the board's search is held
equal here by reading the board's files, never by importing them: the
copied pieces are the board's source, the SQL the report runs is the SQL
the board's own functions write for the same view and words, and the
search columns are the board catalogue's."""
import ast
import os
import re
import types

import pytest

from products.report import catalogue as cat
from products.report import memo, search, server

BOARD = os.path.join(os.path.dirname(__file__), "..", "..", "board")
COPIED = ("fold_sql", "words_of", "is_number", "guard_sql")
REF_WORDING = re.compile(r"register:key|as the board names", re.I)


def pieces(path: str) -> dict:
    src = open(path, encoding="utf-8").read()
    return {n.name: ast.get_source_segment(src, n) for n in ast.parse(src).body if isinstance(n, ast.FunctionDef)}


def test_the_copied_pieces_are_the_boards_source():
    mine, theirs = pieces(search.__file__), pieces(os.path.join(BOARD, "search.py"))
    for name in COPIED:
        assert mine[name] == theirs[name], f"search.{name} differs from the board's: copy it again"


def board_sql():
    """The board's own fold_sql, match_sql, guard_sql and view_sql, from its
    source text, in a namespace of their own."""
    theirs = pieces(os.path.join(BOARD, "search.py"))
    ns = {"re": re, "cat": types.SimpleNamespace(View=object), "LIMIT": search.LIMIT,
          "MACRON_FROM": search.MACRON_FROM, "MACRON_TO": search.MACRON_TO}
    for name in ("fold_sql", "match_sql", "guard_sql", "view_sql"):
        exec(theirs[name], ns)
    return ns["view_sql"]


@pytest.mark.parametrize("term", ["hart", "Te Pāti Māori", "acme holdings ltd", "9429037782269", "o'brien, j"])
def test_the_sql_the_report_runs_is_the_sql_the_board_writes(term):
    board_view_sql = board_sql()
    words = search.words_of(term)
    number = re.sub(r"\s", "", term) if search.is_number(term) else None
    assert search.searched_views()
    for v in search.searched_views():
        assert search.view_sql(v, words, number) == board_view_sql(v, words, number), v.name


def board_views() -> dict:
    """{view: {keyword: value}} for every View(...) in the board's catalogue, read from its source."""
    tree = ast.parse(open(os.path.join(BOARD, "catalogue.py"), encoding="utf-8").read())
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "View" and n.args and isinstance(n.args[0], ast.Constant):
            kw = {k.arg: ast.literal_eval(k.value) for k in n.keywords
                  if k.arg in ("search", "numbers", "suppressed", "hide_names", "default_order", "key_col")}
            out[n.args[0].value] = {"register": ast.literal_eval(n.args[1]), **kw}
    return out


def test_the_search_columns_are_the_board_catalogues():
    board = board_views()
    for v in search.searched_views():
        b = board[v.name]
        assert (v.register, v.search, v.numbers, v.suppressed, v.hide_names, v.default_order, v.key_col) == (
            b["register"], b["search"], b.get("numbers", ()), b.get("suppressed", ""), b.get("hide_names", ()),
            b.get("default_order", "key"), b.get("key_col", "key")), v.name


def test_the_searched_views_name_people_or_organisations_and_never_an_address():
    names = {v.name for v in search.searched_views()}
    assert {"companies", "directors", "party_return_donors", "members", "charities"} <= names
    assert not names & {"company_addresses", "charity_returns", "mp_interests"}


def test_the_start_page_offers_the_search_and_never_a_row_reference():
    ctype, body = server.render("")
    assert ctype.startswith("text/html")
    assert '<form method="get" action="/">' in body and 'name="q"' in body
    assert 'placeholder="a person, company or organisation name"' in body
    assert 'name="ref"' not in body and not REF_WORDING.search(body)
    assert "<script" not in body


class Fake:
    """A connection that answers the search's two reads from fixture rows."""
    ROWS = {
        "companies": [{"key": "companies/9429050975815", "name": "ACME HOLDINGS LIMITED", "registered_on": None, "removed_on": None}],
        "directors": [{"key": "companies/9429050975815/director/ab12", "full_name": "Jane Acme", "suppressed": False,
                       "appointed_on": None, "ended_on": None, "in_latest": True}],
    }

    def __init__(self):
        self.asked = []


def test_a_fixture_search_lists_rows_as_report_links(monkeypatch):
    fake = Fake()
    monkeypatch.setattr(search.db, "pub_views", lambda conn: set(Fake.ROWS) | {"members"})

    def rows(conn, sql, params):
        view = re.search(r"from pub\.(\w+)", sql).group(1)
        conn.asked.append((view, sql, params))
        return [dict(r, total=23 if view == "directors" else 1) for r in Fake.ROWS.get(view, [])]

    monkeypatch.setattr(search.db, "rows", rows)
    ctype, body = server.render("", "subject", term="acme", since="2025-01-01", conn=fake)
    assert '<a href="/report/companies:companies/9429050975815?since=2025-01-01">ACME HOLDINGS LIMITED</a>' in body
    assert '<a href="/report/companies:companies/9429050975815/director/ab12?since=2025-01-01">Jane Acme</a>' in body
    assert "23 found, the first 1 listed" in body and "Companies, directors and shareholders" in body
    assert 'value="acme"' in body and not REF_WORDING.search(body)
    # each word begins a word, macrons folded, a suppressed row never matched by name, at most ten a view, on published views only
    views = [a[0] for a in fake.asked]
    assert "companies" in views and "members" in views and "shareholders" not in views
    d = next(a for a in fake.asked if a[0] == "directors")
    assert "not coalesce(suppressed, false)" in d[1] and d[2][0] == r"\macme" and d[2][-1] == 10 and "translate(lower(" in d[1]
    # a template other than the shape's own travels on the link
    _, body2 = server.render("", "windowed" if "windowed" in server.templates() else "subject", term="acme", conn=Fake())
    assert "/report/companies:companies/9429050975815" in body2
    # nothing found says so, and says how the search reads
    monkeypatch.setattr(search.db, "rows", lambda conn, sql, params: [])
    _, none = server.render("", term="zzqx", conn=Fake())
    assert "No row found for “zzqx”" in none and "Every word must begin a word" in none


def test_an_empty_or_blank_term_searches_nothing():
    assert search.search(None, "") == [] and search.search(None, " ,; ") == []


def test_the_report_href_carries_the_template_the_since_date_and_the_parameters():
    assert memo.report_href("companies:companies/1") == "/report/companies:companies/1"
    assert memo.report_href("companies:companies/1", "banking", "2025-01-01", [{"name": "window_days", "given": "90"}]) == \
        "/report/companies:companies/1?template=banking&since=2025-01-01&window_days=90"


def test_the_memo_says_where_it_starts_in_plain_words():
    r = {"ref": "companies:companies/9429050975815", "found": True, "subject": {"title": "ACME HOLDINGS LIMITED"}}
    assert memo.starts_from(r) == ("This report starts from ACME HOLDINGS LIMITED, row companies/9429050975815 "
                                   "of the register Companies, directors and shareholders.")
    assert memo.starts_from({"ref": "party_returns:abc/A/3", "found": False}) == \
        "This report starts from row abc/A/3 of the register Party donation and loan returns."


def test_a_memo_page_asks_no_row_reference(monkeypatch):
    from products.report.tests.test_reaches import canned_walk
    from products.report import build, db as rdb
    monkeypatch.setattr(build.walk, "walk", lambda *a, **k: canned_walk())
    monkeypatch.setattr(rdb, "pub_views", lambda conn: {"companies", "directors"})
    monkeypatch.setattr(server.db, "scan_connect", lambda: __import__("contextlib").nullcontext(None))
    _, body = server.render("companies:companies/1", "subject", "html")
    assert "This report starts from" in body and 'name="q"' in body
    assert 'name="ref" value' not in body.split("<main>")[0] and not REF_WORDING.search(body)
    assert 'action="/report/companies:companies/1"' in body and "run with this template" in body
    text = memo.text(build.build(None, "companies:companies/1", server.tpl.by_name("subject"), held={"companies", "directors"}))
    assert "This report starts from" in text.splitlines()[1]


@pytest.mark.slow
def test_a_known_names_search_answers_and_its_first_link_renders_a_memo():
    from products.report import check, db
    with db.scan_connect() as conn:
        _, company_key = check.known_donor(conn)
        assert company_key, "no donor row is name-linked to a company with directors"
        name = db.rows(conn, "select name from pub.companies where key = %s", (company_key,))[0]["name"]
    assert check.search_route(name) == []
