"""The expenses lane's tests (fast tier). The readers are tested on table
shapes like the ones measured, written out here with example names; the
filled sample is tested against the row contract, the catch log's sums and
the releases' own printed totals. No model is called."""
import datetime as dt
import io
import os
import zipfile

import pytest

from support import db, lane, rowcontract, sample
from registers.expenses import check, sheet, table
from registers.expenses.sheet import Cell, ref_of

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "expenses")


def cells(rows: dict) -> list:
    """{row: {col: value}} → cells; a str is text, a number a number."""
    out = []
    for r, cols in rows.items():
        for c, v in cols.items():
            text = v if isinstance(v, str) else repr(v)
            out.append(Cell(ref_of(r, c), r, c, float(v) if isinstance(v, (int, float)) else v, text))
    return out


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


def test_a_period_is_read_from_every_title_shape():
    assert table.period("MEMBERS OF THE EXECUTIVE EXPENSES FROM 1 OCTOBER 2019-31 DECEMBER 2019") == (
        dt.date(2019, 10, 1), dt.date(2019, 12, 31))
    assert table.period("54th GOVERNMENT - MEMBERS OF THE EXECUTIVE EXPENSES FROM 1 APIL TO 30 JUNE 2024") == (
        dt.date(2024, 4, 1), dt.date(2024, 6, 30)), "the publisher's own misspelling"
    assert table.period("Members Expense Disclosure - October to December 2025") == (dt.date(2025, 10, 1), dt.date(2025, 12, 31))
    assert table.period("Members' Expense Disclosure - April - June 2022") == (dt.date(2022, 4, 1), dt.date(2022, 6, 30))
    assert table.period("EXPENSES FROM 01 JULY - 30 SEPTEMBER  2020") == (dt.date(2020, 7, 1), dt.date(2020, 9, 30))
    assert table.period("FROM 27 NOVEMBER TO 31 DECEMBER 2023") == (dt.date(2023, 11, 27), dt.date(2023, 12, 31))
    assert table.period("Department of Internal Affairs") is None


def test_a_figure_cell_keeps_its_marker_apart_and_words_are_no_figure():
    assert table.number(" - ") == (0.0, None)
    assert table.number("1,391 (D)") == (1391.0, "D")
    assert table.number("(6,904) (B)") == (-6904.0, "B")
    assert table.number("- 52") == (-52.0, None)
    assert table.number("Allocated Crown Owned Property") == (None, None)
    assert table.number("N/A") == (None, None)


MP_SHEET = {
    1: {1: "Members Expense Disclosure - October to December 2025"},
    3: {4: "Party", 5: "Member", 6: "Accommodation", 8: "Travel", 10: "Grand Total", 11: "Inter-Parliamentary Office of the Clerk"},
    4: {1: "New Cost Centre", 2: "Name", 6: "Wellington", 7: "Non Wellington", 8: "International", 9: "Domestic",
        10: "Grand Total", 11: "Grand Total"},
    5: {4: "Independent", 5: "Example, Alex", 6: 100, 7: 50, 8: 0, 9: 25, 10: 175, 11: 0},
    6: {1: 1125, 2: "Someone Else", 4: "Example Party", 5: "Sample, Sam (3)", 6: 200, 7: " - ", 8: 0, 9: 10.5, 10: 210.5, 11: 40},
    7: {5: "Sample, Kim", 6: 1, 7: 2, 8: 3, 9: 4, 10: 10, 11: 0},
    8: {4: "Example Party Total", 6: 201, 7: 2, 8: 3, 9: 14.5, 10: 220.5, 11: 40},
    10: {4: "Grand Total", 6: 301, 7: 52, 8: 3, 9: 39.5, 10: 395.5, 11: 40},
    12: {4: "1) The Speaker is eligible for VIP Transport services."},
}


def test_the_members_table_joins_its_two_header_rows_and_ignores_the_hidden_helper_columns():
    tabs, skipped = table.read(cells(MP_SHEET), "ALL", 1)
    assert len(tabs) == 1 and skipped == []
    t = tabs[0]
    assert t.period == (dt.date(2025, 10, 1), dt.date(2025, 12, 31))
    assert [(c.heading, c.role) for c in t.columns] == [
        ("Accommodation / Wellington", "category"), ("Accommodation / Non Wellington", "category"),
        ("Travel / International", "category"), ("Travel / Domestic", "category"), ("Grand Total", "total"),
        ("Inter-Parliamentary Office of the Clerk / Grand Total", "outside")]
    m = t.members()
    assert [(x.name, x.party) for x in m] == [("Example, Alex", "Independent"), ("Sample, Sam (3)", "Example Party"),
                                             ("Sample, Kim", "Example Party")]
    assert m[1].marks == ["3"] and m[1].figures[7][0] == 0.0, "a dash is nil"
    assert all("Someone Else" not in str(f) for x in m for f in x.figures.values()), "the hidden Name column is not read"
    assert t.notes == [("D12", "1) The Speaker is eligible for VIP Transport services.")]


def test_every_member_row_adds_to_its_own_total_and_the_party_total_finds_its_party():
    t = table.read(cells(MP_SHEET), "ALL", 1)[0][0]
    assert [check.row_check(x, t)[0] for x in t.members()] == ["adds", "adds", "adds"]
    tt = check.totals(t)
    assert tt[0]["scope"] == "party" and all(e for *_, e in tt[0]["columns"]), "the independent before it is not Example Party's"
    out = check.outside(t)
    assert out["result"] == "equal" and out["line"].name == "Grand Total"


def test_a_row_whose_categories_do_not_add_up_is_named_and_rounding_is_not_a_difference():
    t = table.read(cells(MP_SHEET), "ALL", 1)[0][0]
    ln = t.members()[2]
    ln.figures[6] = (100.0, "100", "F7")
    assert check.row_check(ln, t)[0] == "differs"
    ln.figures[6] = (1.0, "1", "F7")
    ln.figures[10] = (11.0, "11", "J7")
    assert check.row_check(ln, t)[0] == "rounding", "five whole-dollar cells may be up to $2.50 apart"
    for c in (6, 7, 8, 9, 10):
        ln.figures.pop(c)
    assert check.row_check(ln, t)[0] == "nothing-to-add"


EXEC_SHEET = {
    1: {2: "54th GOVERNMENT - MEMBERS OF THE EXECUTIVE EXPENSES FROM 27 NOVEMBER TO 31 DECEMBER 2023"},
    2: {2: "Member of the Executive", 4: "Wellington Accommodation", 5: "Out of Wellington Accommodation",
        6: "Domestic Air Travel", 7: "Surface Travel (Ministers, Spouses and Staff)", 8: "Sub Total Internal Costs",
        9: "Official Cabinet Approved International Travel (A)"},
    3: {2: "Example Party"},
    4: {2: "Rt Hon Alex Example", 4: 0, 5: 10, 6: 20, 7: 30, 8: 60, 9: 1000},
    5: {2: "Hon Sam Sample", 3: "(C)", 4: 5, 5: 0, 6: "1,391 (D)", 7: 4, 8: 1500, 9: 0},
    6: {2: "Example Party Total", 4: 5, 5: 10, 6: 1411, 7: 34, 8: 1560, 9: 1000},
    8: {2: "Notes"},
    9: {2: "(A) Ministers, spouse, staff and officials."},
    11: {2: "53rd GOVERNMENT - MEMBERS OF THE EXECUTIVE EXPENSES FROM 1 OCTOBER TO 26 NOVEMBER 2023"},
    12: {2: "Member of the Executive", 4: "Wellington Accommodation", 5: "Out of Wellington Accommodation",
         6: "Domestic Air Travel", 7: "Surface Travel", 8: "Sub Total Internal Costs", 9: "Official Cabinet Approved International Travel"},
    13: {2: "Other Party"},
    14: {2: "Hon Kim Sample", 4: "Allocated Crown Owned Property", 5: 1, 6: 2, 7: 3, 8: 6, 9: 0},
    15: {2: "Total All Parties", 4: 0, 5: 1, 6: 2, 7: 3, 8: 6, 9: 0},
    16: {1: "Lee Example MP (B)", 9: 12198},
    18: {2: "Totals for the quarter", 4: 5, 5: 11, 6: 1413, 7: 37, 8: 1566, 9: 13198},
}


def test_a_quarter_split_by_an_election_is_two_tables_each_with_its_own_period():
    tabs, skipped = table.read(cells(EXEC_SHEET), "Sheet1", 1)
    assert [t.period for t in tabs] == [(dt.date(2023, 11, 27), dt.date(2023, 12, 31)),
                                        (dt.date(2023, 10, 1), dt.date(2023, 11, 26))]
    a, b = tabs
    assert [(x.name, x.party, x.marks) for x in a.members()] == [("Rt Hon Alex Example", "Example Party", []),
                                                                ("Hon Sam Sample", "Example Party", ["C", "D"])]
    assert [c.role for c in a.columns] == ["category"] * 4 + ["total", "outside"]
    assert a.notes[0][1] == "Notes" and len(a.notes) == 2
    assert [x.figures[6][0] for x in a.members()] == [20.0, 1391.0]
    assert check.row_check(a.members()[1], a)[0] == "differs", "5 + 0 + 1,391 + 4 is not 1,500"
    kim = b.members()[0]
    assert kim.figures[4] == (None, "Allocated Crown Owned Property", "D14") and check.row_check(kim, b)[0] == "adds"


def test_a_name_in_the_party_column_below_the_party_totals_is_a_member_of_no_stated_party():
    with_party = {**EXEC_SHEET, 12: {**EXEC_SHEET[12], 1: "Party"}}
    t = table.read(cells(with_party), "Sheet1", 1)[0][1]
    lee = [x for x in t.members() if x.name.startswith("Lee")]
    assert lee and lee[0].party is None and lee[0].marks == ["B"]
    assert check.row_check(lee[0], t)[0] == "nothing-to-add"
    assert check.totals(t, table.read(cells(with_party), "Sheet1", 1)[0][0].members())[-1]["scope"] == "sheet"


def _xlsx(sheet_xml: str, shared: list) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   '<sheet name="ALL" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/sharedStrings.xml", '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   + "".join(f"<si><t>{s}</t></si>" for s in shared) + "</sst>")
        z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   f"<sheetData>{sheet_xml}</sheetData></worksheet>")
    return b.getvalue()


def test_the_xlsx_reader_keeps_a_formula_with_no_cached_result_as_no_value():
    data = _xlsx('<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><v>12.5</v></c>'
                 '<c r="C1"><f>SUM(B1:B1)</f></c><c r="D1" t="inlineStr"><is><t>inline</t></is></c></row>', ["Party"])
    [(name, cs)] = sheet.sheets(data)
    got = {c.ref: (c.value, c.formula) for c in cs}
    assert name == "ALL" and got == {"A1": ("Party", ""), "B1": (12.5, ""), "C1": (None, "SUM(B1:B1)"), "D1": ("inline", "")}


def test_a_file_that_is_no_workbook_is_refused_by_name():
    with pytest.raises(ValueError):
        sheet.sheets(b"%PDF-1.4", "x.pdf")


# --- the filled sample -------------------------------------------------------

def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_expenses"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    from registers.expenses import sample as S
    schema = _schema()
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}_private")
        S.fill(conn, schema, sample.read_list(os.path.join(LANE, "sample.list")))
        conn.commit()

        def q(t):
            cur = conn.execute(f"SELECT * FROM {schema}.expenses_{t}")
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        yield {"schema": schema, "conn": conn, **{t: q(t) for t in ("files", "set_aside", "releases", "lines", "figures",
                                                                     "totals", "notes")}}


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for t in ("releases", "lines", "figures"):
        for r in filled[t]:
            row = {**r, "loaded_at": r["loaded_at"].isoformat()}
            assert rowcontract.validate(row, today) == [], (t, r["key"])
    assert all(f["key"].startswith(f["document"] + "/sheet") for f in filled["figures"])


def test_every_line_is_published_or_a_catch_log_line_and_never_both(filled):
    published = {x["key"] for x in filled["lines"] if x["check"] in check.PUBLISHED_CHECKS}
    aside = {a["item"] for a in filled["set_aside"] if a["stage"] == "arithmetic"}
    assert published | aside == {x["key"] for x in filled["lines"]} and not (published & aside)
    assert len(filled["releases"]) == 15 and len(filled["files"]) == 13


def test_the_title_is_the_period_and_the_publisher_s_label_stays_beside_it(filled):
    r = [x for x in filled["releases"] if x["document"].startswith("c2fc5d76")]
    assert len(r) == 1 and (r[0]["period_start"], r[0]["period_end"]) == (dt.date(2017, 10, 1), dt.date(2017, 12, 31))
    assert r[0]["label_differs"] and r[0]["label_start"] == dt.date(2017, 1, 1)


def test_a_sub_total_that_is_not_its_categories_is_set_aside_and_never_published(filled):
    joyce = [x for x in filled["lines"] if x["document"].startswith("576558dd") and x["check"] == "differs"]
    assert len(joyce) == 1 and float(joyce[0]["categories_sum"]) == 55179 and float(joyce[0]["total"]) == 27215


def test_the_releases_own_totals_are_checked_and_the_publisher_s_slip_is_reported(filled):
    w = {(x["release"][:8], x["heading"]): x for x in filled["totals"] if x["widest"]}
    ipo = w[("22e7631e", "Inter-Parliamentary Office of the Clerk / Grand Total")]
    assert float(ipo["printed"]) == 131106 and float(ipo["rows_sum"]) == 296474 and not ipo["equal"]
    assert w[("22e7631e", "Grand Total")]["equal"]
    acc = w[("f40f8f5c", "Accommodation / Wellington")]
    assert round(float(acc["printed"]) - float(acc["rows_sum"]), 2) == 516.19
    mp = [x for x in filled["totals"] if x["widest"] and x["total_role"] == "total" and x["release"][:8] in
          ("c2fc5d76", "22e7631e", "f40f8f5c", "61bc10b3")]
    assert len(mp) == 4 and all(x["equal"] for x in mp), "every members' grand total equals its rows"


def test_working_sheets_are_catch_log_lines_and_a_quarter_split_by_an_election_is_two_releases(filled):
    sheets = [a for a in filled["set_aside"] if a["stage"] == "sheet" and a["item"].startswith("9be0852e")]
    assert len(sheets) == 4
    split = sorted((x["period_start"], x["period_end"]) for x in filled["releases"] if x["document"].startswith("f1bc3388"))
    assert split == [(dt.date(2023, 10, 1), dt.date(2023, 12, 31)), (dt.date(2023, 11, 27), dt.date(2023, 12, 31))], \
        "the 53rd government's table is titled for the whole quarter, and the title is what is read"


def test_a_listed_workbook_is_held_or_a_catch_log_line(filled):
    listed = [a for a in filled["set_aside"] if a["stage"] == "listing"]
    assert len(listed) == 3, "the recent listing names four workbooks; this sample holds one of them"


def test_a_rebuild_gives_every_row_the_same_key(filled):
    from registers.expenses import sample as S
    conn, schema = filled["conn"], filled["schema"]
    S.fill(conn, schema, sample.read_list(os.path.join(LANE, "sample.list")))
    again = {r[0] for r in conn.execute(f"SELECT key FROM {schema}.expenses_figures")}
    assert again == {f["key"] for f in filled["figures"]}
    conn.rollback()


def test_the_published_views_build_on_the_lane_s_tables(filled):
    from registers.expenses import load as L
    conn, schema = filled["conn"], filled["schema"]
    views = L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.pub_expenses_")
    conn.execute(views)
    n = conn.execute(f"SELECT count(*) FROM {schema}.pub_expenses_mp_expenses").fetchone()[0]
    bad = conn.execute(f"SELECT count(*) FROM {schema}.pub_expenses_minister_expenses WHERE line_check = 'differs'").fetchone()[0]
    assert n > 0 and bad == 0
    conn.rollback()
