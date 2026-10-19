"""The search SQL: every word must appear, after the fold; a number also
matches the number columns exactly; a suppressed or revoked row is never
matched by name; the term never reaches the SQL text (parameters only)."""
from products.board import catalogue as cat
from products.board import search


def test_words_and_numbers():
    assert search.words_of("Tāmaki, Makaurau") == ["tamaki", "makaurau"]
    assert search.is_number("9429000001311") and search.is_number("94290 0000 1311") and not search.is_number("9429a")


def test_every_word_must_appear_and_the_term_is_a_parameter():
    sql, params = search.view_sql(cat.BY_NAME["companies"], ["foley", "wines"], None)
    assert sql.count(" ~ %s") == 2 and " and " in sql and "foley" not in sql
    assert params[:2] == ["\\mfoley", "\\mwines"] and params[-1] == search.LIMIT
    _, whole = search.view_sql(cat.BY_NAME["companies"], ["hart"], None, whole=True)
    assert whole[0] == "\\mhart\\M"
    assert "translate(lower(" in sql and "from pub.companies" in sql


def test_a_number_also_matches_the_number_columns():
    sql, params = search.view_sql(cat.BY_NAME["companies"], ["9429000001311"], "9429000001311")
    assert "nzbn = %s" in sql and "number = %s" in sql
    assert params.count("9429000001311") == 2


def test_a_suppressed_or_revoked_row_never_matches_by_name():
    sql, _ = search.view_sql(cat.BY_NAME["directors"], ["smith"], None)
    assert "not coalesce(suppressed, false)" in sql
    sql, params = search.view_sql(cat.BY_NAME["gazette_prohibitions"], ["smith"], None)
    assert "not coalesce(superseded_how, '') ~* %s" in sql and "^revoked" in params
    assert search.names_of_row(cat.BY_NAME["directors"], {"key": "k", "full_name": "A B", "suppressed": True}) == []
    assert search.names_of_row(cat.BY_NAME["gazette_prohibitions"], {"key": "k", "name": "A B", "superseded_how": "revoked and replaced"}) == []
    assert search.names_of_row(cat.BY_NAME["directors"], {"key": "k", "full_name": "Anne Bō", "suppressed": False}) == ["anne", "bo"]


def test_regex_characters_in_a_term_are_escaped():
    _, params = search.view_sql(cat.BY_NAME["companies"], ["a.b(c"], None)
    assert params[0] == "\\m" + "a\\.b\\(c"
