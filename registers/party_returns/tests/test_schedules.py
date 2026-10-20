"""Tranche 2's tests: Part A's donors, Part H's loans and the Commission's
amendments. The page texts are shaped like the ones measured on the 111
fully-read returns and carry made-up names and addresses only; the filled
sample is checked for the guards that keep an address out of every
published table (hard limit 15)."""
import os

import pytest

from support import db, rowcontract
from registers.party_returns import amendments, donors, loans, schedule
from registers.party_returns.tests.test_party_returns import filled  # noqa: F401 — the module's filled sample

GAP = " " * 30

LAYOUT = f"""    PART A: PARTY DONATIONS OF MORE THAN $5,000
                                                                                   TOTAL FOR PART A        $ 31,000.00
                 Donor's name and street address                      Date donation or
                                                                    aggregated donations         Enter YES or NO        $0.00
1 Example Donor, 12 Sample Road, Exampleton,                          01/02/2023
                                                                                                 No                $ 20,000.00
     Auckland
2 Sample Trust via Ann Example, Level 3, 4 Model Street,              03/04/2023, 05/06/2023
                                                                                                 No                $ 11,000.00
     Wellington
 PART A                                                                                                                Page 2
"""

TABLE = """PART A: PARTY DONATIONS OF MORE THAN $15,000
TOTAL FOR PART A
$ 26,000.00
| Donor's name and street address | Date donation or aggregated donations received | Enter YES or NO | Amount (including GST) |
| :--- | :--- | :--- | :--- |
| Example Donor, 12 Sample Road, Exampleton 1010 | 01/02/2021 | No | $10,000.00 |
| | 03/04/2021 | No | $6,000.00 |
| Sample Holdings Ltd, C/- Model Accountants, Wellington | 05/06/2021 | No | $10,000.00 |
"""

COLUMNS = """PART A: PARTY DONATIONS OF MORE THAN $15,000
Donor's name and street address
Example Donor, 12 Sample Road, Exampleton
Sample Holdings Ltd, 4 Model Street, Wellington
Amount of donation or total aggregated donations (including GST)
$0.00
$20,000.00
$16,000.00
"""


def _rows(text, src="text"):
    return schedule.rows({2: text}, {2: src}, donors.HEADING, donors.END, "A")


def test_the_text_layer_s_rows_take_their_name_above_and_their_address_below():
    rows, printed, problems = _rows(LAYOUT)
    assert problems == [] and printed == 31000.0
    assert [(r.n, r.amount, r.paired_by) for r in rows] == [(1, 20000.0, "layout"), (2, 11000.0, "layout")]
    assert "Auckland" in rows[0].cell and "Wellington" in rows[1].cell and "Auckland" not in rows[1].cell
    part = donors.read({2: LAYOUT}, {2: "text"}, 31000.0)
    assert part.check == "parts-sum" and [r["name"] for r in part.rows] == ["Example Donor", "Sample Trust via Ann Example"]
    assert part.rows[1]["dates"] == "03/04/2023, 05/06/2023"


def test_the_page_reader_s_table_carries_a_donor_on_to_its_next_dated_row():
    part = donors.read({2: TABLE}, {2: "pixels"}, 26000.0)
    assert part.check == "parts-sum" and part.printed == 26000.0
    assert [(r["name"], r["amount"]) for r in part.rows] == [
        ("Example Donor", 10000.0), ("Example Donor", 6000.0), ("Sample Holdings Ltd", 10000.0)]
    assert part.rows[2]["address"].startswith("C/-")


def test_a_page_read_column_by_column_is_refused_never_paired_by_order():
    rows, _, problems = _rows(COLUMNS, "pixels")
    assert rows == [] and problems and "column by column" in problems[0]
    part = donors.read({2: COLUMNS}, {2: "pixels"}, 36000.0)
    assert part.rows == [] and part.check == ""


def test_a_part_publishes_only_what_adds_to_both_printed_totals():
    assert donors.read({2: LAYOUT}, {2: "text"}, 31000.01).check == ""                    # the declaration's Part A differs
    assert donors.read({2: LAYOUT.replace("$ 31,000.00", "$ 30,000.00")}, {2: "text"}, 31000.0).rows == []
    nothing = donors.read({2: LAYOUT.replace("TOTAL FOR PART A        $ 31,000.00", "")}, {2: "text"}, None)
    assert nothing.rows == [] and "nothing to reconcile" in nothing.problems[0]
    nil = donors.read({2: "PART A: PARTY DONATIONS OF MORE THAN $5,000\nDonor's name and street address\nNIL\n$0.00\n"},
                      {2: "pixels"}, 0.0)
    assert nil.check == "declared-nil" and nil.rows == []


def test_a_row_pointing_at_a_schedule_and_a_page_subtotal_are_not_donors():
    page = TABLE.replace("| Example Donor, 12 Sample Road, Exampleton 1010 | 01/02/2021 | No | $10,000.00 |",
                         "| See attached schedule | | | $26,000.00 |\n| Example Donor, 12 Sample Road, Exampleton 1010 | 01/02/2021 | No | $10,000.00 |")
    assert [r["amount"] for r in donors.read({2: page}, {2: "pixels"}, 26000.0).rows] == [10000.0, 6000.0, 10000.0]
    subtotal = LAYOUT.replace(" PART A  ", f"{GAP}{GAP}{GAP}       $ 31,000.00\n PART A  ")
    assert [r.amount for r in _rows(subtotal)[0]] == [20000.0, 11000.0]


def test_a_named_row_left_without_its_figure_refuses_the_page():
    unfinished = LAYOUT.replace(" PART A  ", "3 Third Example, 9 Sample Road, Exampleton\n PART A  ")
    rows, _, problems = _rows(unfinished)
    assert rows == [] and "do not pair" in problems[0]


def test_a_published_name_never_carries_a_figure_or_a_street():
    assert donors.split("Example Donor, 12 Sample Road, Exampleton") == ("Example Donor", "12 Sample Road, Exampleton")
    assert donors.split("Sample Trust, Level 3, 4 Model Street") == ("Sample Trust", "Level 3, 4 Model Street")
    assert donors.split("Example Holdings Ltd C/- Sample Accountants, Wellington")[0] == "Example Holdings Ltd"
    assert donors.split("Ann Example, Sample Road, Exampleton") == ("Ann Example", "Sample Road, Exampleton")
    assert donors.split("Ann Example; I Sample Road Exampleton") == ("Ann Example", "I Sample Road Exampleton")
    assert donors.split("Brian Lane, 4 Example Street")[0] == "Brian Lane"                # a surname, a figure follows
    assert donors.split("Ann Example Sample Road Exampleton") == (None, "Ann Example Sample Road Exampleton")
    assert donors.split("Sample Trust, L3, 4 Model Street")[0] == "Sample Trust"
    assert donors.split("12 Sample Road, Exampleton")[0] is None


DECLARATION = """3. TOTAL PARTY LOANS
   Complete Parts H and I on pages 13 to 14 if you have any loans to declare.
   Part H: Party loans exceeding $30,000 $119,000.00
   Part I: Party loans between $1,500 – $30,000 $0.00
   Total (H + I) $119,000.00
4. I declare that to the best of my knowledge
"""


INLINE = """PART A: PARTY DONATIONS OF MORE THAN $15,000
TOTAL FOR PART A
$ 41,000.00
Donor's name and street address
1 Example Donor 12 Sample Road Exampleton 1010 01/02/2017 No $ 20,000.00
2 Sample Holdings Ltd, Floor 3, 4 Model Street, Wellington 03/04/2017 No $ 21,000.00
3
4
"""

TWO_LINE = """PART A: PARTY DONATIONS OF MORE THAN $15,000
TOTAL FOR PART A
$ 30,000.00
Donor's name and street address
Example Donor 12 Sample Road 01/02/2023 - 03/04/2023
05/06/2023 - 07/08/2023
No $ 18,000.00
Ann Example 4 Model Street 09/10/2023
No $ 12,000.00
"""

#: the reader dropped the second donor's name: its date column ("26 x Monthly Payments") sits where a cell would
NAME_DROPPED = """PART A: PARTY DONATIONS OF MORE THAN $15,000
TOTAL FOR PART A
$ 68,000.00
Donor's name and street address
Example Donor
Sample Retirement Village, 55 Sample Road
Exampleton 1010
9/4/18 no $ 50,000.00
26 x Monthly Payments no $ 18,000.00
"""

NUMBERED_COLUMNS = """PART A: PARTY DONATIONS OF MORE THAN $15,000
Donor's name and street address
1 Example Donor, 12 Sample Road, Exampleton
2 Ann Example, 4 Model Street, Wellington
1 $ 20,000.00
2 $ 16,000.00
"""


def test_a_row_read_on_one_line_pairs_its_cell_with_the_figure_that_ends_it():
    rows, printed, problems = _rows(INLINE, "pixels")
    assert problems == [] and printed == 41000.0
    assert [(r.n, r.amount, r.yes_no, r.paired_by) for r in rows] == [(1, 20000.0, "No", "inline"), (2, 21000.0, "No", "inline")]
    part = donors.read({2: INLINE}, {2: "pixels"}, 41000.0)
    assert part.check == "parts-sum" and [r["name"] for r in part.rows] == ["Example Donor", "Sample Holdings Ltd"]
    assert [r["dates"] for r in part.rows] == ["01/02/2017", "03/04/2017"]


def test_a_figure_on_its_own_line_after_the_cell_closes_the_row_and_its_dates_run_on():
    rows, _, problems = _rows(TWO_LINE, "pixels")
    assert problems == [] and [(r.amount, r.yes_no) for r in rows] == [(18000.0, "No"), (12000.0, "No")]
    assert "05/06/2023" in rows[0].dates and "09/10/2023" in rows[1].dates
    part = donors.read({2: TWO_LINE}, {2: "pixels"}, 30000.0)
    assert [r["name"] for r in part.rows] == ["Example Donor", "Ann Example"]


def test_a_dropped_name_or_numbered_columns_refuse_the_page_even_when_the_sum_holds():
    for text in (NAME_DROPPED, NUMBERED_COLUMNS):
        rows, _, problems = _rows(text, "pixels")
        assert rows == [] and problems and "do not pair" in problems[0], text[:60]


def test_a_cell_over_several_lines_takes_its_name_from_the_first_line_only():
    assert donors.split("Example Donor QC\nSample Retirement Village, 55 Sample Road\nExampleton") == \
        ("Example Donor QC", "Sample Retirement Village, 55 Sample Road Exampleton")
    assert donors.split("Sample Holdings Ltd, Floor 3, 4 Model Street")[0] == "Sample Holdings Ltd"
    assert donors.split("Sample Ltd, Shed 2, 9 Model Road")[0] == "Sample Ltd"


def test_a_row_pointing_at_an_attachment_is_not_a_donor():
    page = INLINE.replace("1 Example Donor 12 Sample Road Exampleton 1010 01/02/2017 No $ 20,000.00\n", "") \
        .replace("2 Sample Holdings Ltd, Floor 3, 4 Model Street, Wellington 03/04/2017 No $ 21,000.00",
                 "1 See attachment for full listing $ 41,000.00")
    rows, _, _ = _rows(page, "pixels")
    assert rows == []
    assert donors.read({2: page}, {2: "pixels"}, 41000.0).check == ""


def test_the_declared_loans_cut_the_thresholds_and_check_their_own_sum():
    got = loans.declared(DECLARATION)
    assert (got.h, got.i, got.total, got.problems) == (119000.0, 0.0, 119000.0, [])
    cents = loans.declared(DECLARATION.replace("$119,000.00\n   Part I", "$180,186.57\n   Part I")
                           .replace("Total (H + I) $119,000.00", "Total (H + I) $180,186.57"))
    assert cents.total == 180186.57 and cents.problems == []
    bad = loans.declared(DECLARATION.replace("Total (H + I) $119,000.00", "Total (H + I) $120,000.00"))
    assert bad.problems and "is not the total" in bad.problems[0]
    assert loans.declared("no loans here").problems == ["no loans step on the declaration page"]


LENDERS = """PART H: PARTY LOANS EXCEEDING $30,000
TOTAL FOR PART H
$ 130,000.00
Lender's name and street address
A. B. Example,
Sample Valley Road, Exampleton
$ 100,000.00
Date loan entered into
1/02/2020
Guarantor's name and street address (if any)
Ann Guarantor, 9 Model Street
Unpaid balance of loan $0.00
40,000
Interest rate or rates
5%
Total aggregated loan amount from the same lender (if applicable)
$ 130,000.00
Lender's name and street address
A. B. Example,
Sample Valley Road, Exampleton
$ 30,000.00
Date loan entered into
1/09/2020
Interest rate or rates
5%
Lender's name and street address
Loan amount (including GST) $0.00
"""


def test_a_lender_block_takes_its_loan_amount_never_the_balance_the_total_or_a_guarantor():
    part = loans.read({13: LENDERS}, {13: "pixels"}, 130000.0)
    assert part.check == "parts-sum" and part.printed == 130000.0
    assert [(r["name"], r["amount"], r["interest"]) for r in part.rows] == [("A. B. Example", 100000.0, "5%"),
                                                                          ("A. B. Example", 30000.0, "5%")]
    assert all("Guarantor" not in r["cell"] and "Model" not in r["cell"] for r in part.rows)
    assert loans.read({13: LENDERS}, {13: "pixels"}, 129000.0).rows == []
    assert loans.read({13: "PART H: PARTY LOANS EXCEEDING $30,000\nLender's name and street address\nNIL\n"},
                      {13: "pixels"}, 0.0).check == "declared-nil"


LISTING = """<table><tr><td><a href="/assets/Annual-Returns/2024/Example-amended-2026.pdf">Example Party</a><br>[PDF, 2.6MB amended 2026]
<br><a href="/assets/Annual-Returns/2024/Amended-Example-2024.pdf">Example Party</a><br>[PDF, 2.6MB amended 2025]
<br><a href="/assets/Annual-Returns/2024/Example-2024.pdf">Example Party</a><br>[PDF, 2.6MB]</td><td>$1.00</td></tr>
<tr><td><a href="/assets/Annual-Returns/2022/Sample-Amended-Return.pdf">Sample Party</a><br>[PDF, 1MB]</td></tr>
<tr><td><a href="/assets/Annual-Returns/2023/Model-a.pdf">Model Party (amended)</a><br><a href="/assets/Annual-Returns/2023/Model-b.pdf">Model Party (amended)</a>
<br><a href="/assets/Annual-Returns/2023/Model.pdf">Model Party</a></td></tr></table>
<p><a href="/assets/2021-annual-returns-/Example-2021.pdf">Download the Example Party annual return 2021 (PDF, 1MB)</a><br>
<a href="/assets/2021-annual-returns-/Amended-Example-2021.pdf">Download the Example Party annual return 2021 (amended) (PDF, 1MB)</a>
<a href="/assets/Party-donations-and-loans/2010-returns/old-amended-2009.pdf">Download the amended Old Party annual return 2009 (PDF)</a></p>
"""


def test_an_amendment_replaces_only_what_the_commission_marks_amended():
    groups = amendments.statements(LISTING)
    names = ["Example-amended-2026.pdf", "Amended-Example-2024.pdf", "Example-2024.pdf", "Sample-Amended-Return.pdf",
             "Model-a.pdf", "Model-b.pdf", "Model.pdf", "Example-2021.pdf", "Amended-Example-2021.pdf"]
    index = {f"{k:064x}": f"/old/residue/party_returns/x/{n}" for k, n in enumerate(names, 1)}
    index[f"{99:064x}"] = "/old/archive/2021-annual-returns-__Amended-Example-2021.pdf"     # the same name, other bytes
    by = amendments.held_by_name(index)
    sha = {n: f"{k:064x}" for k, n in enumerate(names, 1)}
    assert by["amended-example-2021.pdf"] is None
    pairs, unheld = amendments.replacements(groups, by)
    got = {(old, new) for old, new, _, _ in pairs}
    latest = sha["Example-amended-2026.pdf"]
    assert (sha["Example-2024.pdf"], latest) in got and (sha["Amended-Example-2024.pdf"], latest) in got
    assert not any(sha["Sample-Amended-Return.pdf"] in p for p in got)          # its link does not say amended
    assert (sha["Model.pdf"], sha["Model-a.pdf"]) in got and (sha["Model.pdf"], sha["Model-b.pdf"]) in got
    assert not any({sha["Model-a.pdf"], sha["Model-b.pdf"]} == set(p) for p in got)   # no dates: neither replaces the other
    assert not any(sha["Example-2021.pdf"] == old for old, _ in got)             # its amendment's name is held twice
    assert any("Example Party 2021" in u for u in unheld) and not any("2009" in u for u in unheld)


# --- the filled sample ----------------------------------------------------------

def _all(conn, sql):
    cur = conn.execute(sql)
    return [dict(zip([d[0] for d in cur.description], r)) for r in cur]


def test_no_published_table_or_view_has_an_address_column(filled):  # noqa: F811
    from registers.party_returns import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema).replace("pub.", f"{schema}."))
    cols = {r[0] for r in conn.execute(
        "select column_name from information_schema.columns where table_schema = %s", (schema,))}
    conn.rollback()
    assert not cols & set(rowcontract.FORBIDDEN_COLUMNS) and "cell" not in cols


def test_every_schedule_row_keeps_the_contract_and_its_address_is_private(filled):  # noqa: F811
    schema, conn = filled["schema"], filled["conn"]
    rows = _all(conn, f"select *, 'donor' as kind from {schema}.donors") + _all(conn, f"select *, 'loan' as kind from {schema}.loans")
    assert len(rows) >= 100
    for r in rows:
        row = {k: r[k] for k in ("key", "document", "page", "reader", "profile", "profile_version", "read_from")}
        row["place"] = r["key"].split("/", 1)[1]
        row["loaded_at"] = r["loaded_at"].isoformat()
        assert rowcontract.validate(row) == [], r["key"]
        name = r["donor"] if r["kind"] == "donor" else r["lender"]
        assert not any(ch.isdigit() for ch in name), r["key"]
        assert not donors.STREET.search(name) or donors.ADDRESS_START.search(
            conn.execute(f"select cell from {schema}_private.addresses where key = %s", (r["key"],)).fetchone()[0]), r["key"]
    keys = {r["key"] for r in rows}
    private = {r[0] for r in conn.execute(f"select key from {schema}_private.addresses")}
    assert keys == private


def test_every_published_part_adds_to_the_return_s_own_figure(filled):  # noqa: F811
    schema, conn = filled["schema"], filled["conn"]
    for part, table, figure in (("donors_check", "donors", "part_a"), ("loans_check", "loans", "loans_h")):
        bad = conn.execute(f"""select r.key from {schema}.returns r
            left join (select return_key, sum(amount) s from {schema}.{table} group by 1) t on t.return_key = r.key
            where r.{part} is not null and abs(coalesce(t.s, 0) - r.{figure}) >= 0.005""").fetchall()
        assert bad == [], (table, bad)
        orphans = conn.execute(f"select count(*) from {schema}.{table} t join {schema}.returns r on r.key = t.return_key "
                               f"where r.{part} is null").fetchone()[0]
        assert orphans == 0


def test_the_sample_s_amended_returns_carry_what_replaces_them(filled):  # noqa: F811
    schema, conn = filled["schema"], filled["conn"]
    lines = {l.split()[0]: l for l in open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample.list"),
                                           encoding="utf-8") if l[:1].isalnum()}
    nzf_2023 = [s for s, l in lines.items() if "New Zealand First Party 2023 (pixels" in l][0]
    got = conn.execute(f"select replaced_by, stated from {schema}.amendments where document = %s", (nzf_2023,)).fetchone()
    assert got and got[0] in lines and "amended 5/6/2024" in got[1]
    unaudited = [s for s, l in lines.items() if "unaudited" in l][0]
    assert conn.execute(f"select replaced_by from {schema}.amendments where document = %s", (unaudited,)).fetchone()


def test_the_session_reader_cannot_see_the_private_twin(filled):  # noqa: F811
    with db.connect(db.READ_KEY, "querynz_v4_sample") as conn:
        seen = {r[0] for r in conn.execute(
            "select nspname from pg_namespace where has_schema_privilege(current_user, nspname, 'USAGE')")}
    assert f"{filled['schema']}_private" not in seen and "party_returns_private" not in seen


@pytest.mark.parametrize("text", ["", "PART A: PARTY DONATIONS OF MORE THAN $5,000\n"])
def test_a_return_with_no_part_a_page_reconciles_only_when_nil(text):
    assert donors.read({2: text}, {2: "text"}, 0.0).check == "declared-nil"
    assert donors.read({2: text}, {2: "text"}, 10.0).check == ""


# --- session 4: a row over a page break, misread empty rows, figures with no cents, HTML tables --------------------

def _line(n="", cell="", date="", yes_no="", amount=""):
    """One text-layer line with the form's columns where pdftotext puts them."""
    return f"{n:<4}{cell:<62}{date:<28}{yes_no:<17}{amount}".rstrip()


HEAD = "\n".join([
    "    PART A: PARTY DONATIONS OF MORE THAN $15,000",
    " " * 90 + "TOTAL FOR PART A        $ 188,000.00",
    " " * 17 + "Donor's name and street address" + " " * 18 + "Date donation or",
    " " * 66 + "aggregated donations     Enter YES or NO        $0.00"])
HEAD_NEXT = HEAD.split("\n", 2)[2]                    # a continuation sheet: the column headings, no part heading


def test_a_row_whose_figure_is_on_the_next_page_is_carried_there():
    page2 = "\n".join([HEAD,
                       _line("", "    Example Donor via Example Trust, 31 Sample Drive,"),
                       _line(" 1"), _line("", "    Exampleton, 1071"),
                       _line("", "", "03/01/2019", "NO"),
                       _line("2", "", "01/02/2019", "NO", "$ 28,000.00"),
                       _line("", "    Sample Holder, via Model Trust, 21 Sample Street, Exampleton"),
                       _line("3"), _line("", "    0622"),
                       _line("", "", "16/01/2019", "NO"),
                       _line("4", "", "18/02/2019", "NO"),
                       " PART A" + " " * 120 + "Page: 2"])
    page3 = "\n".join([HEAD_NEXT, _line("5", "", "17/06/2019", "NO"),
                       _line("6", "", "16/12/2019", "NO", "$ 160,000.00"), _line("7"), _line("8"),
                       " PART A" + " " * 120 + "Page: 3"])
    rows, printed, problems = schedule.rows({2: page2, 3: page3}, {2: "text", 3: "text"}, donors.HEADING, donors.END, "A")
    assert problems == [] and printed == 188000.0
    assert [(r.page, r.n, r.amount) for r in rows] == [(2, 1, 28000.0), (3, 3, 160000.0)]
    assert rows[1].cell.startswith("Sample Holder") and "Example Donor" not in rows[1].cell
    part = donors.read({2: page2, 3: page3}, {2: "text", 3: "text"}, 188000.0)
    assert part.check == "parts-sum" and [r["name"] for r in part.rows] == ["Example Donor via Example Trust",
                                                                            "Sample Holder, via Model Trust"]
    # a page that names somebody above its first figure leaves the carried row without one: refused, never paired
    crowded = page3.replace(_line("5", "", "17/06/2019", "NO"), _line("5", "Other Donor, 4 Model Road") + "\n" +
                            _line("", "", "17/06/2019", "NO"))
    rows, _, problems = schedule.rows({2: page2, 3: crowded}, {2: "text", 3: "text"}, donors.HEADING, donors.END, "A")
    assert any("does not meet its figure" in p for p in problems)


def test_an_empty_row_number_the_text_layer_misread_is_neither_a_name_nor_a_row():
    page = "\n".join([HEAD,
                      _line("1", "Example Donor, 12 Sample Road, Exampleton", "01/02/2023", "No", "$ 100,000.00"),
                      _line("2", "Sample Holdings Ltd, 4 Model Street, Wellington", "03/04/2023", "No", "$ 88,000.00"),
                      _line("3"), _line("4"), _line("9"), _line("6"), _line("7"),     # `9`: a misread 5
                      " PART A" + " " * 120 + "Page: 2"])
    rows, _, problems = _rows(page)
    assert problems == [] and [(r.n, r.amount) for r in rows] == [(1, 100000.0), (2, 88000.0)]


def test_a_figure_with_no_cents_is_an_amount_only_in_the_amount_column():
    page = "\n".join([HEAD,
                      _line("1", "Example Donor, 12 Sample Road, Exampleton", "01/02/2023", "No", "150000"),
                      _line("2", "Sample Holdings Ltd, 4 Model Street, Wellington", "03/04/2023", "No", "38,000"),
                      " PART A" + " " * 120 + "Page: 2"])
    rows, _, problems = _rows(page)
    assert problems == [] and [r.amount for r in rows] == [150000.0, 38000.0]
    assert all("12" not in str(r.amount) for r in rows)                  # a house number is never an amount
    stacked = "PART A: PARTY DONATIONS OF MORE THAN $15,000\nTOTAL FOR PART A 35000\nDonor's name and street address\n" \
              "1 Example Donor 12 Sample Road Exampleton\n22/12/21\nno 35000\n"
    rows, _, problems = _rows(stacked, "pixels")
    assert problems == [] and [(r.amount, r.yes_no) for r in rows] == [(35000.0, "no")]


def test_the_reader_s_html_table_is_read_only_under_the_form_s_own_heading():
    form = ("PART A: PARTY DONATIONS OF MORE THAN $15,000\n<table><thead><tr><td></td><td>TOTAL FOR PART A</td>"
            "<td>$26,000.00</td></tr><tr><th></th><th>Donor's name and street address</th><th>Date</th><th>Enter YES or NO</th>"
            "<th>Amount</th><th></th></tr></thead><tr><td>1</td><td>Example Donor<br>12 Sample Road, Exampleton</td>"
            "<td>01/02/2024</td><td>No</td><td>$16,000.00</td><td></td></tr><tr><td>2</td><td>3Example Ltd, 4 Model Street"
            "</td><td>03/04/2024</td><td>No</td><td>$10,000.00</td><td></td></tr></table>")
    rows, printed, problems = _rows(form, "pixels")
    assert problems == [] and printed == 26000.0 and [(r.n, r.amount) for r in rows] == [(1, 16000.0), (2, 10000.0)]
    part = donors.read({2: form}, {2: "pixels"}, 26000.0)
    assert part.check == "parts-sum" and [r["name"] for r in part.rows] == ["Example Donor", "3Example Ltd"]
    breakdown = "<table><tr><td>Part A</td><td>Donor Name</td><td>Donor Total</td></tr><tr><td>19/08/2024</td>" \
                "<td>Example Donor</td><td>4,000.00</td><td>$10,275.58</td></tr></table>"
    assert schedule.unhtml(breakdown) == breakdown                       # a filer's own breakdown is not the form's table


def test_an_address_word_run_into_its_number_or_a_park_never_stays_in_a_name():
    assert donors.split("Example Donor, Suite1, 2 Sample Street, Exampleton")[0] == "Example Donor"
    assert donors.split("Example Finance Limited, Sample business Park, 6 Model Road")[0] == "Example Finance Limited"
    assert donors.split("Model Network Limited, Vodafone on The Park, Level 1")[0] == "Model Network Limited"
    assert donors.split("3Example Developments Ltd - 12 Sample Grove, Exampleton")[0] == "3Example Developments Ltd"
    assert donors.split("Park, Jane, 4 Sample Road")[0] == "Park, Jane"
    assert donors.split("Estate of Example Donor formerly of 12 Sample Road, Exampleton")[0] == "Estate of Example Donor"


# --- session 5: rows the totals cannot check, the page reader's other shapes, the name cut ---------------------------

def _head(total):
    return HEAD.replace("$ 188,000.00", total)


def test_a_dated_name_line_opens_the_row_whose_figure_line_carries_no_date():
    # ACT 2022 p2: a donor's later gifts on dated lines of their own, then the next donor's name and date on the
    # line above its figure, whose line carries the end of the address; once read as the $50's donor (the sum held)
    page = "\n".join([_head("$ 170,050.00"),
                      _line("", "    Example One, 1 Sample Road, Exampleton", "02/03/22"),
                      _line(" 1", "", "", "No", "$ 50,000.00"),
                      _line("", "    Example Two, 4 Model Street, Exampleton", "08/03/22"),
                      _line(" 2", "", "", "No", "$ 10,000.00"),
                      _line(" 3", "", "23/05/22", "No", "$ 10,000.00"),
                      _line(" 4", "", "25/06/22", "No", "$ 50.00"),
                      _line("", "    Example Three, 9 Sample Grove, Exampleton", "04/03/22"),
                      _line(" 5", "    Auckland 1010", "", "No", "$ 100,000.00"),
                      " PART A" + " " * 120 + "Page: 2"])
    part = donors.read({2: page}, {2: "text"}, 170050.0)
    assert part.check == "parts-sum"
    assert [(r["name"], r["amount"]) for r in part.rows] == [
        ("Example One", 50000.0), ("Example Two", 10000.0), ("Example Two", 10000.0), ("Example Two", 50.0),
        ("Example Three", 100000.0)]


def test_a_text_cell_takes_its_name_from_its_first_line():
    page = "\n".join([_head("$ 140,000.00"),
                      _line("", "    Hon Example Donor", "25/1/19"),
                      _line(" 1", "", "", "No", "$ 140,000.00"),
                      _line("", "    Sample Gardens Retreat", "25/10/19"),
                      " PART A" + " " * 120 + "Page: 2"])
    part = donors.read({2: page}, {2: "text"}, 140000.0)
    assert part.check == "parts-sum" and part.rows[0]["name"] == "Hon Example Donor"
    assert "Retreat" in part.rows[0]["address"]


NUMBERED_NAME = """PART A: PARTY DONATIONS OF MORE THAN $15,000
TOTAL FOR PART A
$ 25,500.00
Donor's name and street address
1. Example Donor
16 Sample Road, Exampleton
12/03/2018
No
$ 500.00
2. Sample Holdings Ltd
4 Model Street, Wellington
05/07/2018
No
25000
"""


def test_a_numbered_name_takes_the_unnumbered_lines_below_it():
    rows, printed, problems = _rows(NUMBERED_NAME, "pixels")
    assert problems == [] and [(r.n, r.amount) for r in rows] == [(1, 500.0), (2, 25000.0)]
    part = donors.read({2: NUMBERED_NAME}, {2: "pixels"}, 25500.0)
    assert [r["name"] for r in part.rows] == ["Example Donor", "Sample Holdings Ltd"]
    assert all("Road" not in r["name"] and "Street" not in r["name"] for r in part.rows)
    two = NUMBERED_NAME.replace("$ 500.00\n", "$ 500.00\n$ 700.00\n")
    assert schedule._numbered(two.splitlines(), 2) is None            # one row, two figures: whose is which


def test_a_donor_s_aggregated_total_restates_its_rows_and_is_never_one():
    # NZ First 2019: each donor's dated gifts a line each, then its own `Aggregated total`, the second on the next page
    page2 = "\n".join(["PART A: PARTY DONATIONS OF MORE THAN $15,000", "TOTAL FOR PART A $28,100.00",
                       "Donor's name and street address",
                       "1. Example Capital Limited, 1 Sample Road, Exampleton 23/04/2019 NO $4,025.00",
                       "2. Example Capital Limited, 1 Sample Road, Exampleton 20/12/2019 NO $8,050.00",
                       "3. Example Capital Limited Aggregated total $12,075.00",
                       "4. Example Donor, 2 Model Street, Exampleton 18/04/2019 NO $8,025.00",
                       "5. Example Donor, 2 Model Street, Exampleton 02/12/2019 NO $8,000.00"])
    page3 = "Donor's name and street address\nExample Donor Aggregated total $16,025.00\n"
    part = donors.read({2: page2, 3: page3}, {2: "pixels", 3: "pixels"}, 28100.0)
    assert part.check == "parts-sum" and len(part.rows) == 4
    assert {r["name"] for r in part.rows} == {"Example Capital Limited", "Example Donor"}
    wrong = page3.replace("$16,025.00", "$16,000.00")
    part = donors.read({2: page2, 3: wrong}, {2: "pixels", 3: "pixels"}, 28100.0)
    assert part.check == "" and any("aggregated total of 16,000.00" in p for p in part.problems)


def test_a_page_with_one_figure_and_a_pointer_page():
    one = ("PART A: PARTY DONATIONS OF MORE THAN $5,000\nTOTAL FOR PART A $10,000.00\nDonor's name and street address\n"
           "1 Example Donor\n2 Sample Road Exampleton\n12/11/2024\nNO $10,000.00\n")
    part = donors.read({2: one}, {2: "pixels"}, 10000.0)
    assert part.check == "parts-sum" and [r["name"] for r in part.rows] == ["Example Donor"]
    pointer = ("PART A: PARTY DONATIONS OF MORE THAN $5,000\nTOTAL FOR PART A 26000.00\nDonor's name and street address\n"
               "1 See attachment for full listing\n2 $26,000.00\n3\n4\n")
    rows, printed, problems = _rows(pointer, "pixels")
    assert rows == [] and problems == [] and printed == 26000.0


def test_bare_row_numbers_and_a_whole_figure_after_yes_or_no_close_rows():
    stacked = ("PART A: PARTY DONATIONS OF MORE THAN $5,000\nDonor's name and street address\n"
               "1 Example Donor 12 Sample Road Exampleton\n17/08/2023\nNO\n$20,000.00\n"
               "2 Sample Holder 4 Model Street Exampleton\n08/08/2023\nNO\n$25,000.00\n7\n8\n9\n")
    rows, _, problems = _rows(stacked, "pixels")
    assert problems == [] and [r.amount for r in rows] == [20000.0, 25000.0]
    inline = ("PART A: PARTY DONATIONS OF MORE THAN $5,000\nTOTAL FOR PART A 5500\nDonor's name and street address\n"
              "C Example 4 Sample Street, Exampleton 20/11/2024 NO 5500\n")
    part = donors.read({2: inline}, {2: "pixels"}, 5500.0)
    assert part.check == "parts-sum" and [(r["name"], r["amount"]) for r in part.rows] == [("C Example", 5500.0)]


def test_a_donor_s_dated_rows_run_over_a_page_reader_page_break():
    # ACT 2017: a donor's monthly gifts, its name at the foot of page 2 and its one figure on page 3's sixth line
    page2 = ("PART A: PARTY DONATIONS OF MORE THAN $15,000\nTOTAL FOR PART A $146,000.00\n"
             "| Donor's name and street address | Date | Enter YES or NO | Amount |\n"
             "| Example, Ann | 18/05/2017 | No | $25,000.00 |\n"
             "| Sample, Jenny via Sample Trust, 1 Model Road | 04/01/2017 | No | |\n"
             "| | 01/02/2017 | No | |\n| | 01/03/2017 | No | |\n")
    page3 = "Donor's name and street address\n01/04/2017 No\n01/05/2017 No\n01/12/2017 No $121,000.00\n"
    part = donors.read({2: page2, 3: page3}, {2: "pixels", 3: "pixels"}, 146000.0)
    assert part.check == "parts-sum"
    assert [(r["name"], r["amount"]) for r in part.rows] == [("Example, Ann", 25000.0),
                                                             ("Sample, Jenny via Sample Trust", 121000.0)]
    closed = page2.replace("| | 01/03/2017 | No | |", "| | 01/03/2017 | No | $0.50 |")
    part = donors.read({2: closed, 3: page3}, {2: "pixels", 3: "pixels"}, 146000.5)
    assert part.check == ""                     # the row above closed with its figure: page 3's first row names nobody


def test_the_name_stops_before_a_care_of_a_postnominal_s_address_or_parliament():
    assert donors.split("Reti Holdings Ltd, Sample Accountants Ltd")[0] == "Reti Holdings Ltd"
    assert donors.split("Example Farms Limited, BDO Exampleton Limited")[0] == "Example Farms Limited"
    assert donors.split("Example Co Limited - Deloitte")[0] == "Example Co Limited"
    assert donors.split("Example, Simon - Parliament Buildings, Wellington")[0] == "Example, Simon"
    assert donors.split("JANE EXAMPLE, Parliament Buildings")[0] == "JANE EXAMPLE"
    assert donors.split("JANE EXAMPLE, d- Parliament Buildings, Wellington")[0] == "JANE EXAMPLE"
    assert donors.split("Hon Ann Example QC Sample Grace Retirement Village 59/184 Model Road")[0] == "Hon Ann Example QC"
    assert donors.split("EXAMPLE HON ANN, Sample Retirement Village, 184 Model Road")[0] == "EXAMPLE HON ANN"
    assert donors.split("22 E.A.W Limited - 4 Sample Street, Exampleton")[0] == "22 E.A.W Limited"
    # a person after the comma is no care-of: kept
    assert donors.split("Example Trust via Sample Trustee Ltd, Ann Example")[0] == "Example Trust via Sample Trustee Ltd, Ann Example"
