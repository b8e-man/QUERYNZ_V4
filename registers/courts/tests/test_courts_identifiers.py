"""The identifying details a court document prints, found by their shape
(identifiers.py; Arthur, 3 November 2026). Every value here is invented."""
import os
import re

from registers.courts import check, identifiers as I

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT = {1: ("Counsel: A Example, Invented Law, PO Box 4321, Exampletown 6011. Email: a.example@example.invalid\n"
            "Telephone (09) 555 0123; mobile 021 555 0199; from abroad +64 4 555 0177.\n"
            "The respondent, aged 34, lives at 12 Invented Street, Exampletown. Her son, a 16-year-old, was there.\n"),
        2: ("Date of birth: 3 March 1971. The company (company number 1234567, NZBN 9429000000017) and its\n"
            "IRD number 123-456-789. Driver licence number AB123456; registration plate ABC123.\n"
            "Again: a.example@example.invalid, aged 34.\n")}


def _by_kind(found):
    out = {}
    for kind, value, page in found:
        out.setdefault(kind, []).append((value, page))
    return out


def test_each_fixed_shape_is_found_once_per_document_at_the_first_page_that_prints_it():
    got = _by_kind(I.find(TEXT))
    assert got["email"] == [("a.example@example.invalid", 1)]
    assert {v for v, _ in got["phone"]} == {"(09) 555 0123", "021 555 0199", "+64 4 555 0177"}
    assert got["po_box"] == [("PO Box 4321, Exampletown 6011", 1)]
    assert got["address"] == [("12 Invented Street, Exampletown", 1)]
    assert {v for v, _ in got["age"]} == {"34", "16"} and all(p == 1 for _, p in got["age"])
    assert got["date_of_birth"] == [("3 March 1971", 2)]
    assert got["company_number"] == [("1234567", 2)] and got["nzbn"] == [("9429000000017", 2)]
    assert got["ird_number"] == [("123-456-789", 2)]
    assert got["driver_licence"] == [("AB123456", 2)] and got["vehicle_registration"] == [("ABC123", 2)]
    assert set(got) == set(I.SHAPE_KINDS)


def test_the_shapes_a_judgment_prints_that_are_not_identifiers_are_not_taken():
    text = {1: ("CIV-2019-404-1234 [2024] NZSC 161 at [45]. The 1990 Act s 203. A sum of $021 555 019 and 1,234,567.\n"
                "12\nHigh Court Road\n"            # a page number above a heading is not an address
                "The rate rose to 30 per cent. aged 300. The 1998 Ford Ranger. Paragraph 12 The Court found.\n"
                "registered company 123; a registered ABC; registration number 12345; Tel: 555 0123\n")}
    got = _by_kind(I.find(text))
    assert "phone" not in got and "age" not in got and "vehicle_registration" not in got and "nzbn" not in got
    assert "address" not in got, [len(v) for v, _ in got.get("address", [])]


def test_the_rows_are_keyed_by_the_document_and_name_no_person():
    sha = "0" * 64
    rows = I.rows(sha, TEXT, "courts-judgment", 3, "text", "2026-11-03T00:00:00+13:00")
    assert [r["key"] for r in rows] == [f"{sha}/identifier/{n}" for n in range(1, len(rows) + 1)]
    assert all(r["person"] is None and r["model"] is None and r["reader"] == I.READER for r in rows)
    assert all(set(r) == set(I.COLUMNS) for r in rows)


def test_the_closed_vocabulary_is_the_table_s_own():
    sql = open(os.path.join(LANE, "tables.sql"), encoding="utf-8").read()
    block = sql[sql.index("CREATE TABLE IF NOT EXISTS courts_private.identifiers"):]
    block = block[:block.index(");\n")]
    listed = re.findall(r"'([a-z_]+)'", block[block.index("kind IN"):block.index("value")])
    assert tuple(listed) == I.KINDS
    assert set(I.SHAPE_KINDS) <= set(I.KINDS) and set(I.PATTERNS) == set(I.SHAPE_KINDS)


def test_publish_sql_never_names_the_private_table_and_the_check_sees_it_if_it_did():
    text = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read()
    assert not check.publish_sql_names_private(text)
    assert check.publish_sql_names_private(text + "\nCREATE VIEW pub.court_x AS SELECT * FROM courts_private.identifiers;")
    assert check.publish_sql_names_private("CREATE VIEW pub.court_x AS SELECT i.kind FROM courts.people p JOIN identifiers i ON true;")
    # no published view's column is named for a kind of detail (the ruled numbers view's kinds are values, not columns)
    body = "\n".join(ln.split("--", 1)[0].rstrip() for ln in text.splitlines()).replace(check.NUMBERS_VIEW_SQL, "")
    cols = re.findall(r"\b([a-z_]+)\b", body)
    assert not set(cols) & check.FORBIDDEN_COLUMNS - {"age"}, sorted(set(cols) & check.FORBIDDEN_COLUMNS)


def test_the_one_ruled_view_reads_the_private_table_narrowly_and_a_widened_one_is_caught():
    """Ruling 1 (Arthur, 3 November 2026): a company's NZBN or company number, by document, kind, value and page, for
    the links lane; the statement is held to its exact text, so another column, another kind or another table fails."""
    text = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read()
    assert check.NUMBERS_VIEW_SQL in text
    assert "SELECT document, kind, value, page FROM courts_private.identifiers WHERE kind IN ('nzbn', 'company_number');" \
        in check.NUMBERS_VIEW_SQL
    for widened in (check.NUMBERS_VIEW_SQL.replace("page FROM", "page, person FROM"),
                    check.NUMBERS_VIEW_SQL.replace("'company_number')", "'company_number', 'email')"),
                    check.NUMBERS_VIEW_SQL.replace("WHERE kind IN ('nzbn', 'company_number')", "WHERE true")):
        assert check.publish_sql_names_private(text.replace(check.NUMBERS_VIEW_SQL, widened)), widened
    assert check.publish_sql_names_private(text + "\n" + check.NUMBERS_VIEW_SQL.replace("court_company_numbers", "court_more"))


class _Conn:
    def __init__(self, cols, other=0):
        self.cols, self.other = cols, other

    def execute(self, q, *a):
        rows = [(c,) for c in self.cols] if "information_schema.columns" in q else [(self.other,)]
        return type("R", (), {"fetchall": lambda _: rows, "fetchone": lambda _: rows[0]})()


def test_the_live_numbers_view_is_checked_for_its_columns_and_its_kinds():
    assert check.numbers_view_problems(_Conn([])) == []                       # not yet published
    assert check.numbers_view_problems(_Conn(list(check.NUMBERS_COLUMNS))) == []
    assert check.numbers_view_problems(_Conn(list(check.NUMBERS_COLUMNS) + ["person"]))
    assert check.numbers_view_problems(_Conn(list(check.NUMBERS_COLUMNS), other=3))
