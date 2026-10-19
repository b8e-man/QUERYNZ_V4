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
