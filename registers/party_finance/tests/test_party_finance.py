"""The party-finance lane's tests (fast tier). The readers are tested on
page shapes like the ones measured, written out here with example names;
the filled sample is tested against the row contract, the catch log's
sums, and the Commission's own figures. No model is called."""
import datetime as dt
import os

import pytest

from support import db, lane, rowcontract, sample
from registers.party_finance import check, expenses, listing, promoter_returns, read, reconcile, statements

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "party_finance")

TABLE_2023 = """<html><body><table>
<tr><th>Party</th><th>Election Expense Limit*</th><th>Total Party Expenses</th><th>Broadcasting Allocation</th>
<th>Total Broadcasting Allocation Expenses</th><th>Audit Report</th></tr>
<tr><td><a href="/assets/x/Example-Return-2023.pdf">Example Party</a><br>[PDF, 5.1MB]</td><td>$3,311,400.00</td>
<td>$2,776,458.01</td><td>$368,548.00</td><td>$360,968.65</td><td>Yes</td></tr>
<tr><td><a href="/assets/x/Other-amended.pdf">Other Party (amended)</a><br>[PDF, 1.6MB]<br><br>
<a href="/assets/x/Other.pdf">Other Party</a><br>[PDF, 6.5MB]</td><td>$1,485,800.00</td><td>$51,690.42</td><td>NIL</td>
<td>NIL</td><td>Yes</td></tr>
<tr><td><a href="/assets/x/Third.pdf">Third Party (amended to include </a><br><a href="/assets/x/Third.pdf">audit report)</a>
<br>[PDF, 5.1 MB]</td><td>$1,942,200.00</td><td>$98,781.98</td><td>NIL**</td><td>NIL</td><td>&nbsp;</td></tr>
<tr><td><a href="/assets/x/Broken.pdf">Broken Party</a></td><td>$1.00</td><td>$2.00</td></tr>
</table></body></html>""".encode()

TABLE_2020 = """<table><tr><td>&nbsp;</td><td>Party</td><td>Election expenses limit*</td><td>Total party expenses</td>
<td>Party allocation</td><td>Total party allocation expenses</td><td>&nbsp;</td></tr>
<tr><td>&nbsp;</td><td>Example Party</td><td>$2,806,400.00</td><td>$108,2166.64</td><td>$150,755.00</td><td>$150,740.17</td>
<td><a href="/assets/y/Example-2020.pdf">PDF, 1.8MB</a></td></tr>
<tr><td>Small Party</td><td>$1,452,800.00</td><td>$142,617.99</td><td>N/A</td><td>&nbsp;N/A</td>
<td><a href="/assets/y/Small-2020.pdf">PDF, 4MB</a></td></tr></table>""".encode()


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


def test_the_2023_table_reads_amendments_from_the_link_text():
    r = listing.read_expenses(TABLE_2023, 2023)
    assert [x.label for x in r.rows] == ["Example Party", "Other Party", "Third Party"]
    assert [n for n, _ in r.skipped] == [4] and listing.rows_seen(TABLE_2023) == len(r.rows) + len(r.skipped)
    other = r.rows[1]
    assert other.note == "amended" and [ln.amended for ln in other.links] == [True, False]
    assert other.figures["allocation"] == 0.0 and other.figures["audited"] is True
    third = r.rows[2]
    assert len(third.links) == 1 and third.links[0].amended and third.note == "amended to include audit report"
    assert third.figures["allocation"] == 0.0 and third.printed[2] == "NIL**" and third.figures["audited"] is None
    assert r.rows[0].links[0].url == "https://elections.nz/assets/x/Example-Return-2023.pdf"


def test_the_2020_table_keeps_the_printed_cell_and_reads_na_as_no_figure():
    r = listing.read_expenses(TABLE_2020, 2020)
    assert [x.label for x in r.rows] == ["Example Party", "Small Party"] and r.skipped == []
    ex = r.rows[0]
    assert ex.figures["total_expenses"] == 1082166.64 and ex.printed[1] == "$108,2166.64"
    assert r.rows[1].figures["allocation"] is None and r.rows[1].figures["allocation_spent"] is None
    assert ex.links[0].url.endswith("Example-2020.pdf")


def test_a_link_is_the_current_return_only_where_the_commission_says_so():
    links = [{"ordinal": 1, "amended": True}, {"ordinal": 2, "amended": False}]
    assert read.is_current(links[0], links) and not read.is_current(links[1], links)
    one = [{"ordinal": 1, "amended": False}]
    assert read.is_current(one[0], one)
    two = [{"ordinal": 1, "amended": False}, {"ordinal": 2, "amended": False}]
    assert not read.is_current(two[0], two), "two links and no amendment named: neither is guessed"


DECLARATION = """ELECTION EXPENSES OF REGISTERED PARTY
Expenditure limit for the party: $2,806,400.00
Part A: Party advertisements promoted solely by party            $ 1,000.00
Part B: Shared advertisements with candidates                    $ 200.50
Part C: Advertisements promoted by a third party                 $ 0.00
Total (A + B + C)                                                $ 1,200.50
Part D: Broadcasting allocation                                  $ 9,999.00
"""


def test_the_form_total_is_checked_against_a_b_and_c_and_never_d():
    f = expenses.figures({1: DECLARATION})
    assert f["total"] == 1200.50 and f["basis"] == "form" and f["limit"] == 2806400.00
    assert expenses.judge(f) == (1200.50, "parts-sum", "", None)


def test_the_form_s_total_beats_the_auditor_s():
    pages = {1: DECLARATION, 9: "Total Party Election Expenses: $1,300.00\n"}
    assert expenses.figures(pages)["total"] == 1200.50


def test_a_total_its_parts_contradict_is_refused():
    f = expenses.figures({1: DECLARATION.replace("$ 1,200.50", "$ 1,300.50")})
    total, check_, why, issue = expenses.judge(f, tolerant=True)
    assert total is None and "not A + B + C" in why and issue is None, "$100 off is set aside (ruling 66)"
    f = expenses.figures({1: DECLARATION.replace("$ 1,200.50", "$ 1,200.14")})
    total, check_, why, issue = expenses.judge(f)
    assert total is None and "not A + B + C" in why, "to the cent first: the tolerance only when no pass holds"


def test_a_part_not_read_is_not_zero():
    page = "\n".join(line for line in DECLARATION.splitlines() if not line.startswith(("Part B", "Total")))
    total, _, why, _ = expenses.judge(expenses.figures({1: page}), tolerant=True)
    assert total is None and "a part not read is not zero" in why


def test_a_figure_belongs_to_the_label_on_its_own_line():
    page = "Total (A + B + C)\nTotal Party Election Expenses:\n$ 5,000.00\n"
    assert expenses.figures({1: page})["total"] is None


BOXES = """3. TOTAL PARTY ELECTION EXPENSES
Part A: Party advertisements promoted solely by the party
986

Part B: Party advertisements shared with candidates or other parties
0

Part C: Authorised party advertisements promoted by third parties
0

Total (A + B + C)
986

Part D: Party only allocation expenses
68511.51
"""


def test_a_figure_alone_below_its_label_and_whole_dollars_are_read():
    f = expenses.figures({1: BOXES})
    assert f["parts"] == {"A": 986.0, "B": 0.0, "C": 0.0, "D": 68511.51} and f["total"] == 986.0
    assert expenses.judge(f) == (986.0, "parts-sum", "", None)
    assert expenses.figures({1: "TOTAL FOR PART A 986\nTotal (A + B + C) 986\n"})["total"] == 986.0


def test_a_whole_number_with_more_on_its_line_is_not_a_figure():
    assert expenses.figures({1: "Total (A + B + C) 986 Page 3\n"})["total"] is None
    assert expenses.figures({1: "Total (A + B + C)\n2023 General Election\n"})["total"] is None


PARTY_ROWS = [
    {"party": "ec-party/2020-07-09/cb4e", "name": "ONE Party", "kind": "name", "from_on": "2020-07-09",
     "to_on": "2023-08-16", "registered_on": "2020-07-09", "cancelled_on": "2026-03-30"},
    {"party": "ec-party/2020-07-09/cb4e", "name": "NewZeal", "kind": "name", "from_on": "2023-08-16",
     "to_on": "2026-03-30", "registered_on": "2020-07-09", "cancelled_on": "2026-03-30"},
    {"party": "ec-party/2014-05-13/3b0f", "name": "Internet Party", "kind": "name", "from_on": "2014-05-13",
     "to_on": "2018-06-11", "registered_on": "2014-05-13", "cancelled_on": "2018-06-11"},
]


def test_a_party_label_is_the_registration_live_on_polling_day():
    assert read.party_of("ONE Party", PARTY_ROWS, 2020) == ("ec-party/2020-07-09/cb4e", "exact")
    assert read.party_of("NewZeal", PARTY_ROWS, "2024-12-31")[0] == "ec-party/2020-07-09/cb4e"
    assert read.party_of("ONE Party (currently applying to change its party name to NewZeal)", PARTY_ROWS, 2023) == (
        "ec-party/2020-07-09/cb4e", "exact, before its bracket")
    assert read.party_of("Internet Party", PARTY_ROWS, 2020) == (None, "unresolved"), "cancelled before polling day"


STATEMENT = """Statement of Financial Performance
                                              Note        2025          2024
                                                            $             $
Total Revenue                                   4         17,288       211,147
Total expenses                                            17,627       207,740
Surplus/(Deficit) for the year              -            339             3,407
"""
POSITION = """                                                          2025          2024
Total assets                                               5,870         3,234
Total Liabilities                                             83           166
Total assets less total liabilities (net assets)           5,787         3,068
"""


def test_a_statement_s_pairs_publish_only_where_its_own_arithmetic_holds():
    ls = statements.lines({3: STATEMENT, 4: POSITION})
    figs, why = statements.operating(ls)
    assert why == "" and figs["surplus"].amount == -339 and figs["income"].amount == 17288
    assert figs["income"].prior == 211147, "a note number is not a figure"
    figs, why = statements.position(ls)
    assert why == "" and figs["liabilities"].amount == 83, "a small figure in the figure column is not a note"
    figs, why = statements.operating(statements.lines({3: STATEMENT.replace("17,627", "17,500")}))
    assert figs == {} and "no surplus or deficit line prints it" in why, "$127 off: set aside (ruling 66)"
    figs, why = statements.operating(statements.lines({3: STATEMENT.replace("17,627", "17,600")}))
    assert why == "" and figs["surplus"].amount == -339, "$27 off: reconciled, the printed line published"
    assert {f.issue for f in figs.values()} == {"+27.00: income less expenditure against the surplus or deficit line"}


def test_a_dash_in_a_column_of_its_own_is_nil():
    page = """Total Assets                       32,951            62,320
Total Liabilities                       -           12,143
Net Assets                         32,951            50,177
"""
    figs, why = statements.position(statements.lines({8: page}))
    assert why == "" and figs["liabilities"].amount == 0 and figs["liabilities"].prior == 12143


def test_the_reported_year_is_the_later_column_head():
    page = """Revenue                       2023          2024
Total Revenues               5,355        82,021
Total Expenses               2,852        83,746
Net Income                   2,503        (1,725)
"""
    figs, why = statements.operating(statements.lines({1: page}))
    assert why == "" and (figs["income"].amount, figs["income"].prior, figs["surplus"].amount) == (82021, 5355, -1725)


def test_a_statement_in_thousands_is_scaled_and_rounds_at_its_own_precision():
    page = """                                                     $000
Total Operating Income                                     2,667.7
Total Operating Expenses                                   1,999.8
Surplus/(deficit)                                            667.9
"""
    figs, why = statements.operating(statements.lines({7: page}))
    assert why == "" and figs["income"].amount == 2667700 and figs["income"].scale == 1000


def test_compare_names_equal_part_a_only_differing_and_unread():
    listing_rows = [{"key": k, "year": 2020, "party_label": p, "total_expenses": t}
                    for k, p, t in (("a", "A", 10.0), ("b", "B", 5.0), ("c", "C", 7.0), ("d", "D", 1.0))]
    returns = [
        {"listing_row": "a", "current": True, "total": 10.0, "total_check": "parts-sum", "part_a": 10.0, "document": "x"},
        {"listing_row": "b", "current": True, "total": 9.0, "total_check": "parts-sum", "part_a": 5.0, "document": "y"},
        {"listing_row": "c", "current": True, "total": 9.0, "total_check": "stated-only", "part_a": 7.0, "document": "z"},
        {"listing_row": "d", "current": False, "total": 1.0, "total_check": "parts-sum", "part_a": 1.0, "document": "w"},
    ]
    out = check.compare(listing_rows, returns)
    assert [d["party"] for d in out["equal"]] == ["A"]
    assert [d["party"] for d in out["part_a_only"]] == ["B"]
    assert [d["party"] for d in out["differ"]] == ["C"], "Part A alone is an explanation only where the parts reconcile"
    assert [d["party"] for d in out["unread"]] == ["D"], "a superseded return never stands for its row"


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
    return "scratch_gate_party_finance"


def _items():
    return [i.split()[0] for i in sample.read_list(os.path.join(LANE, "sample.list")) if not i.startswith("key:")]


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    from registers.party_finance import sample as S
    schema = _schema()
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}_private")
        if not conn.execute(f"SELECT to_regclass('{schema}.parties_names') IS NOT NULL").fetchone()[0]:
            # the party labels resolve against the parties lane's published names: its sample first
            parties = os.path.join(REPO, "registers", "parties")
            sample.filler(REPO, "registers/parties")(conn, schema, sample.read_list(os.path.join(parties, "sample.list")))
        S.fill(conn, schema, sample.read_list(os.path.join(LANE, "sample.list")))
        conn.commit()

        def q(t):
            cur = conn.execute(f"SELECT * FROM {schema}.party_finance_{t}")
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        yield {"schema": schema, "conn": conn, **{t: q(t) for t in ("files", "set_aside", "expense_listing",
                                                                     "promoter_listing", "listing_links", "expense_returns",
                                                                     "promoter_returns")}}


def test_every_row_keeps_the_row_contract(filled):
    today = dt.date.today()
    for t in ("expense_listing", "promoter_listing", "expense_returns"):
        for r in filled[t]:
            row = {**r, "loaded_at": r["loaded_at"].isoformat()}
            assert rowcontract.validate(row, today) == [], (t, r["key"])
    assert all(r["key"] == r["document"] + "/declaration" for r in filled["expense_returns"])


def test_every_sample_return_is_a_row_or_a_catch_log_line_and_never_both(filled):
    returns = {f["document"] for f in filled["files"] if f["kind"] == "expense-return"}
    rows = {r["document"] for r in filled["expense_returns"]}
    aside = {a["item"] for a in filled["set_aside"] if a["stage"] == "declaration"}
    assert rows | aside == returns and not (rows & aside)
    assert len(rows) >= 8


def test_the_listings_read_every_row(filled):
    assert len(filled["expense_listing"]) == 37 and len(filled["promoter_listing"]) == 21
    assert not [a for a in filled["set_aside"] if a["stage"] == "listing"]


def test_the_sample_returns_agree_with_the_commission_or_are_explained(filled):
    out = check.compare(filled["expense_listing"], filled["expense_returns"])
    assert out["differ"] == [], out["differ"]
    assert len(out["equal"]) >= 6
    assert [d["party"] for d in out["part_a_only"]] == ["Advance NZ"]


def test_every_sample_party_label_resolves_to_a_registration_or_says_unresolved(filled):
    rows = filled["expense_listing"] + filled["expense_returns"]
    assert all(r["party"] is None or r["party"].startswith("ec-party/") for r in rows)
    assert all((r["party"] is None) == (r["party_basis"] == "unresolved") for r in rows)
    assert sum(r["party"] is not None for r in filled["expense_listing"]) >= 35


def test_every_sample_statement_pair_is_three_figures_or_a_catch_log_line(filled):
    conn, schema = filled["conn"], filled["schema"]
    figs = [dict(zip(("document", "figure", "figure_check", "amount"), r)) for r in conn.execute(
        f"SELECT document, figure, figure_check, amount FROM {schema}.party_finance_statement_figures")]
    aside = {a["item"] for a in filled["set_aside"] if a["stage"] == "statement-figures"}
    linked = {x["document"] for x in filled["listing_links"] if x["document"]} & {
        f["document"] for f in filled["files"] if f["kind"] == "financial-statements"}
    for d in linked:
        for pair, names in statements.PAIRS.items():
            got = {f["figure"] for f in figs if f["document"] == d and f["figure"] in names}
            assert (got == set(names)) != (f"{d}/{pair}" in aside), (d, pair)
    assert len(figs) >= 18
    by = {(f["document"], f["figure"]): float(f["amount"]) for f in figs}
    for d in {f["document"] for f in figs if f["figure"] == "income"}:
        assert abs(by[d, "income"] - by[d, "expenditure"] - by[d, "surplus"]) <= 1000


def test_the_superseded_original_is_never_current(filled):
    current = {r["document"]: r["current"] for r in filled["expense_returns"]}
    assert current["063e003ca5ea4b096f13abb685a4949bdedb689870900892aee90c1eb813cced"] is False
    assert current["3790d0dd53446c607094b22a00b178e1d628eecdcb7a4a4e42f1cf4e22060379"] is True


def test_the_published_views_build_on_the_lane_s_tables(filled):
    from registers.party_finance import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.party_finance_pub_"))
    n = conn.execute(f"SELECT count(*) FROM {schema}.party_finance_pub_party_expenses").fetchone()[0]
    agree = conn.execute(f"SELECT count(*) FROM {schema}.party_finance_pub_party_expenses WHERE agrees").fetchone()[0]
    conn.rollback()
    assert n == len(filled["expense_listing"]) and agree >= 6
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.party_finance_pub_"))
    n = conn.execute(f"SELECT count(*) FROM {schema}.party_finance_pub_promoter_expenses").fetchone()[0]
    agree = conn.execute(f"SELECT count(*) FROM {schema}.party_finance_pub_promoter_expenses "
                         "WHERE election_agrees AND cannabis_referendum_agrees").fetchone()[0]
    conn.rollback()
    assert n == len(filled["promoter_listing"]) and agree >= 1


PROMOTER_DECLARATION = """2. TOTAL ELECTION EXPENSES
   Part A: Election advertising $ 141,224.34
3. TOTAL REFERENDUM EXPENSES FOR THE CANNABIS REFERENDUM
   Part B: Referendum advertising for the Cannabis Referendum
   $ 141,224.34
   Part C: Referendum advertising for the End of Life Choice Act Referendum

   $ 0.00
"""


def test_each_promoter_part_is_its_own_figure_checked_by_the_return_s_two_statements():
    parts = promoter_returns.scan({1: PROMOTER_DECLARATION, 2: "TOTAL FOR PART A $ 141,224.34\n",
                                   4: "TOTAL FOR PART B\n$141,224.34\n"}, "ABC")
    assert [promoter_returns.judge(parts[k]) for k in "ABC"] == ["", "", ""]
    assert [(parts[k].figure, parts[k].check) for k in "ABC"] == [
        (141224.34, "declared-and-schedule"), (141224.34, "declared-and-schedule"), (0.0, "declared-only")]
    assert parts["B"].schedule_page == 4 and parts["C"].page == 1


def test_a_promoter_part_its_two_statements_contradict_or_neither_states_is_not_read():
    parts = promoter_returns.scan({1: PROMOTER_DECLARATION, 2: "TOTAL FOR PART A $ 141,224.00\n"}, "AB")
    assert "not the schedule's total" in promoter_returns.judge(parts["A"])
    parts = promoter_returns.scan({1: "Part A: Election advertising\nWrite 'N/A' if you have none\nN/A\n"}, "A")
    assert parts["A"].declared is None and "no figure read" in promoter_returns.judge(parts["A"])


def test_compare_promoters_never_adds_a_referendum_column_to_the_election_one():
    listing_rows = [{"key": "r", "year": 2020, "promoter": "P", "election_expenses": 5.0,
                     "cannabis_referendum_expenses": 5.0, "end_of_life_referendum_expenses": 0.0},
                    {"key": "s", "year": 2023, "promoter": "Q", "election_expenses": 7.0,
                     "cannabis_referendum_expenses": None, "end_of_life_referendum_expenses": None}]
    returns = [{"listing_row": "r", "spending": "election_expenses", "figure": 5.0, "document": "x"},
               {"listing_row": "r", "spending": "cannabis_referendum_expenses", "figure": 4.0, "document": "x"}]
    out = check.compare_promoters(listing_rows, returns)
    assert [(d["promoter"], d["spending"]) for d in out["equal"]] == [("P", "election_expenses")]
    assert [d["spending"] for d in out["differ"]] == ["cannabis_referendum_expenses"]
    assert [(d["promoter"], d["spending"]) for d in out["unread"]] == [
        ("P", "end_of_life_referendum_expenses"), ("Q", "election_expenses")]


def test_every_sample_promoter_part_is_a_row_or_a_catch_log_line_and_agrees_with_the_commission(filled):
    rows = {r["key"] for r in filled["promoter_returns"]}
    aside = {a["item"] for a in filled["set_aside"] if a["stage"] == "promoter-return"}
    assert rows and not (rows & aside)
    out = check.compare_promoters(filled["promoter_listing"], filled["promoter_returns"])
    assert out["differ"] == [] and len(out["equal"]) >= 4, out
    today = dt.date.today()
    for r in filled["promoter_returns"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}, today) == [], r["key"]


ALLOCATION = """<html><body><ol><li>Past elections</li><li>2023 General Election</li></ol>
<table><tfoot><tr><td>TOTAL allocated</td><td>$300</td><td>$4,000</td></tr>
<tr><td>TOTAL available</td><td>$4,000</td><td>$4000</td></tr></tfoot>
<thead><tr><td>Political Party</td><td>Original allocation<br>12 May</td><td>First variation<br>1 August</td></tr></thead>
<tbody><tr><td colspan="3"><strong>Parties eligible for share of broadcasting allocation</strong></td></tr>
<tr><td>Example Party</td><td>$200</td><td>$3,000</td></tr>
<tr><td>Other Party</td><td>$100</td><td>$1,000</td></tr>
<tr><td colspan="3"><strong>Parties not eligible for allocation</strong></td></tr>
<tr><td>Late Party*</td><td>$0</td></tr>
</tbody></table></body></html>""".encode()


def test_each_round_is_scored_against_the_page_s_own_total():
    from registers.party_finance import broadcasting
    b = broadcasting.read(ALLOCATION)
    assert b.rounds == ["Original allocation 12 May", "First variation 1 August"]
    assert [(r.label, r.mark, r.eligible, r.amounts) for r in b.rows] == [
        ("Example Party", "", True, [200, 3000]), ("Other Party", "", True, [100, 1000]), ("Late Party", "*", False, [0, None])]
    assert b.failed_rounds == [] and b.totals["available"] == [4000, 4000]
    assert broadcasting.election_year(ALLOCATION) == 2023


def test_a_round_that_does_not_add_up_publishes_nothing():
    rows, totals, aside = read.allocation_rows(ALLOCATION.replace(b"$3,000", b"$3,100"), "a" * 64)
    assert rows == [] and totals[1]["rows_sum"] == 4100 and "do not add" in aside[-1][2], "$100 off (ruling 66)"
    rows, totals, aside = read.allocation_rows(ALLOCATION.replace(b"$3,000", b"$3,001"), "a" * 64)
    assert len(rows) == 6 and aside == [] and totals[1]["issue"] == "+1.00: the round 2 rows against TOTAL allocated"
    assert [r["issue"] for r in rows if r["round"] == 2] == [totals[1]["issue"]] * 3
    assert {r["issue"] for r in rows if r["round"] == 1} == {None}
    rows, totals, aside = read.allocation_rows(ALLOCATION, "a" * 64)
    assert len(rows) == 6 and aside == [] and [r["final"] for r in rows[:2]] == [False, True]


def test_the_allocation_pages_reconcile_and_every_document_is_accounted_for(filled):
    assert len([a for a in filled["set_aside"] if a["stage"] == "allocation"]) == 0
    conn, schema = filled["conn"], filled["schema"]
    n = conn.execute(f"SELECT count(*) FROM {schema}.party_finance_allocations").fetchone()[0]
    bad = conn.execute(f"SELECT count(*) FROM {schema}.party_finance_allocation_totals WHERE rows_sum <> allocated").fetchone()[0]
    assert n == 19 * 2 + 17 * 3 and bad == 0
    for r in conn.execute(f"SELECT key, document, page, place, reader, profile, profile_version, read_from, loaded_at "
                          f"FROM {schema}.party_finance_allocations"):
        row = dict(zip(("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from",
                        "loaded_at"), r))
        row["loaded_at"] = row["loaded_at"].isoformat()
        assert rowcontract.validate(row) == [], row["key"]


REGISTER_2023 = """<html><body><ol><li>Past elections</li><li>2023 General Election</li></ol>
<div class="page__accordion accordion"><button class="accordion__title" id="t1">  Example Trust  </button>
<div class="accordion__content" id="c1"><p><strong>Email: </strong><a href="mailto:someone@example.org">someone@example.org</a></p>
<p><strong>Address:</strong><br>1 Example Street<br>Exampletown 9999</p>
<p><strong>Authorised representative: </strong>Alex Example</p>
<p><strong>People in a position comparable with director:</strong>&nbsp;Alex Example</p>
<p><strong>Trustees:<br></strong>Sam Sample<br>Kim Sample</p><p><strong>Registered on:&nbsp;</strong>16 August 2023</p></div></div>
<div class="page__accordion accordion"><button class="accordion__title" id="t2">Example Union</button>
<div class="accordion__content" id="c2"><p><strong>Address:</strong><br>PO Box 1</p><p><br>PO Box 2</p>
<p><strong>Favourite colour:</strong> blue</p><p><strong>Registered on: </strong>1 May 2023</p></div></div>
</body></html>""".encode()

REGISTER_2020 = """<ol><li>Past elections</li><li>2020 General Election</li></ol><button class="accordion__title">Example Society</button>
<div class="accordion__content"><div class="promoter">
<div class="promoter__field"><div class="promoter__field__label">Address</div><div class="promoter__field__value">PO Box 3</div></div>
<div class="promoter__field"><div class="promoter__field__label">People in a position comparable with director</div>
<div class="promoter__field__value">Pat Example, Lee Example</div></div>
<div class="promoter__field"><div class="promoter__field__label">Trustees</div><div class="promoter__field__value">12 trustees (please contact the Commission for details)</div></div>
<div class="promoter__field"><div class="promoter__field__label">Registered as a promoter for</div><div class="promoter__field__value">2020 General Election<br>End of Life Choice referendum</div></div>
<div class="promoter__field"><div class="promoter__field__label">Registered on</div><div class="promoter__field__value">3 June 2020</div></div>
</div></div>""".encode()


def test_the_register_publishes_roles_and_holds_every_contact_line_private():
    rows, ppl, contacts, aside = read.promoter_rows(REGISTER_2023, "b" * 64)
    assert [(r["promoter"], r["registered_on"], r["year"]) for r in rows] == [
        ("Example Trust", "2023-08-16", 2023), ("Example Union", "2023-05-01", 2023)]
    assert [(p["role"], p["name"]) for p in ppl] == [("authorised representative", "Alex Example"),
                                                    ("comparable with director", "Alex Example"),
                                                    ("trustee", "Sam Sample"), ("trustee", "Kim Sample")]
    published = " ".join(str(v) for r in rows + ppl for v in r.values())
    assert "@" not in published and "Example Street" not in published and "PO Box" not in published
    held = {(c["promoter_key"][-7:], c["label"]): c["value"] for c in contacts}
    assert held[("block/2", "address")] == "PO Box 1\nPO Box 2", "an unlabelled paragraph continues the field before"
    assert held[("block/2", "favourite colour")] == "blue" and "not met" in aside[0][2]


def test_the_2020_register_splits_comma_lists_and_keeps_a_statement_apart():
    rows, ppl, contacts, aside = read.promoter_rows(REGISTER_2020, "c" * 64)
    assert [p["name"] for p in ppl] == ["Pat Example", "Lee Example"]
    assert rows[0]["statement"] == "12 trustees (please contact the Commission for details)"
    assert rows[0]["registered_for"] == "2020 General Election / End of Life Choice referendum" and aside == []


def test_no_published_promoter_value_carries_a_contact_line(filled):
    conn, schema = filled["conn"], filled["schema"]
    n = conn.execute(f"SELECT count(*) FROM {schema}.party_finance_promoters").fetchone()[0]
    assert n == 37 + 32
    bad = conn.execute(f"SELECT count(*) FROM {schema}.party_finance_promoter_people "
                       f"WHERE name ~ '[0-9@]' OR name ~* '\\m(po box|private bag)\\M'").fetchone()[0]
    assert bad == 0
    held = conn.execute(f"SELECT count(*) FROM {schema}_private.party_finance_promoter_contacts").fetchone()[0]
    assert held >= 37 + 32


ROSTER = """<p><strong>2025 Financial Statements</strong></p><table>
<tr><td>Party</td><td>Financial statements balance date</td><td>Deadline for filing financial statements</td>
<td>Date filed</td><td>Audit requirement</td></tr>
<tr><td><a href="/assets/f/Example-2025-audited.pdf">Example Party (audited)</a> [PDF, 681KB]<br>
<a href="/assets/f/Example-2025.pdf">Example Party</a> [PDF, 781KB]</td><td>31/12/24</td><td>30/06/25</td>
<td>Statement 30/06/25, amended statement and audit report 18/08/25</td><td>Financial statements must be audited</td></tr>
<tr><td><a href="/assets/f/TOP-2025.pdf">The Example Party (TOP)</a> [PDF, 459KB]</td><td>31/12/24</td><td>30/06/25</td>
<td>09/04/25</td><td>No audit required</td></tr>
<tr><td>Late Party *</td><td>31/3/25</td><td>30/9/25**</td><td></td><td>No audit required</td></tr></table>""".encode()


def test_the_roster_keeps_free_text_filings_as_printed_and_the_name_s_own_brackets():
    rows, out_links, aside = read.statement_rows(ROSTER, "d" * 64, {"https://elections.nz/assets/f/TOP-2025.pdf": "e" * 64})
    assert [(r["party_label"], r["note"], r["mark"]) for r in rows] == [
        ("Example Party", "audited", None), ("The Example Party (TOP)", None, None), ("Late Party", None, "*")]
    assert rows[0]["date_filed"] is None and rows[0]["filed_printed"].startswith("Statement 30/06/25")
    assert rows[1]["balance_date"] == "2024-12-31" and rows[1]["date_filed"] == "2025-04-09"
    assert rows[2]["deadline"] == "2025-09-30" and rows[2]["date_filed"] is None
    assert [x["document"] for x in out_links] == [None, None, "e" * 64]
    assert [a[1] for a in aside] == ["link", "link"], "a link the lane does not hold is a catch-log line"


def test_the_roster_links_every_held_statement(filled):
    conn, schema = filled["conn"], filled["schema"]
    n = conn.execute(f"SELECT count(*) FROM {schema}.party_finance_financial_statements").fetchone()[0]
    years = [r[0] for r in conn.execute(f"SELECT DISTINCT filed_year FROM {schema}.party_finance_financial_statements ORDER BY 1")]
    assert n == 47 and years == [2024, 2025, 2026]
    assert not [a for a in filled["set_aside"] if a["stage"] == "statement"]


# Ruling 66: below $100 reconciled with an issue; $100 or more set aside; the printed figure published.
@pytest.mark.parametrize("off, admitted", [(0, True), (1, True), (9999, True), (10000, False), (10001, False)])
def test_the_tolerance_is_below_one_hundred_dollars_and_exactly_one_hundred_is_not(off, admitted):
    assert reconcile.RECONCILE_TOLERANCE_CENTS == 10000
    printed = 1200.50
    parts = round(printed + off / 100, 2)
    assert reconcile.within(parts, printed) is admitted and reconcile.within(printed - off / 100, printed) is admitted
    assert (reconcile.issue(parts, printed, "x") is None) is (off == 0)
    page = DECLARATION.replace("$ 1,000.00", f"$ {1000 + off / 100:,.2f}")
    total, check_, why, issue = expenses.judge(expenses.figures({1: page}), tolerant=True)
    if admitted:
        assert (total, check_, why) == (1200.50, "parts-sum", ""), "the printed total is the one published"
        assert issue == (None if off == 0 else f"+{off / 100:,.2f}: A + B + C against the form's total")
    else:
        assert total is None and "not A + B + C" in why and issue is None


@pytest.mark.parametrize("off, admitted", [(9999, True), (10000, False), (10001, False)])
def test_a_promoter_s_schedule_below_one_hundred_dollars_off_its_box_publishes_the_box(off, admitted):
    sched = f"TOTAL FOR PART A $ {141224.34 - off / 100:,.2f}\n"
    part = promoter_returns.scan({1: PROMOTER_DECLARATION, 2: sched}, "A")["A"]
    assert "not the schedule's total" in promoter_returns.judge(part), "to the cent first"
    part = promoter_returns.scan({1: PROMOTER_DECLARATION, 2: sched}, "A")["A"]
    why = promoter_returns.judge(part, tolerant=True)
    if admitted:
        assert why == "" and (part.figure, part.check) == (141224.34, "declared-and-schedule")
        assert part.issue == f"-{off / 100:,.2f}: TOTAL FOR PART A against the declaration's Part A"
    else:
        assert "not the schedule's total" in why and part.figure is None and part.issue is None


@pytest.mark.parametrize("off, admitted", [(99, True), (100, False), (101, False)])
def test_a_broadcasting_round_below_one_hundred_dollars_off_publishes_with_its_issue(off, admitted):
    from registers.party_finance import broadcasting
    b = broadcasting.read(ALLOCATION.replace(b"$3,000", f"${3000 + off:,}".encode()))
    assert (b.failed_rounds == []) is admitted
    assert b.issues == ({1: f"+{off}.00: the round 2 rows against TOTAL allocated"} if admitted else {})


@pytest.mark.parametrize("off, admitted", [(99.99, True), (100.00, False), (100.01, False)])
def test_a_statement_pair_below_one_hundred_dollars_off_publishes_with_its_issue(off, admitted):
    page = f"""                                                          2025          2024
Total assets                                               {5870 + off:,.2f}      3,234.00
Total Liabilities                                             83.00        166.00
Total assets less total liabilities (net assets)           5,787.00      3,068.00
"""
    figs, why = statements.position(statements.lines({4: page}))
    if admitted:
        assert why == "" and figs["net_assets"].amount == 5787.0
        assert {f.issue for f in figs.values()} == {f"+{off:,.2f}: assets less liabilities against the net-assets line"}
    else:
        assert figs == {} and "no net-assets line prints it" in why


def test_the_issue_is_a_column_of_every_view_a_sum_admits_and_check_counts_it():
    with open(os.path.join(LANE, "publish.sql"), encoding="utf-8") as f:
        sql = f.read()
    for view in ("party_expense_returns", "promoter_expense_returns", "broadcasting_allocations",
                 "party_statement_figures"):
        body = sql[sql.index(f"VIEW pub.{view} AS"):].split(";")[0]
        assert ", issue\nFROM" in body, view
    assert "r.issue AS return_issue" in sql
    assert set(check.ISSUE_TABLES) <= set(__import__("registers.party_finance.load", fromlist=["x"]).COLUMNS_OF)


def test_the_sample_s_issue_rows_are_counted_and_name_their_difference(filled):
    n = check.issue_rows(filled["conn"], filled["schema"], shared=True)
    assert n["expense_returns"] >= 1 and n["statement_figures"] >= 6, n
    for t in ("expense_returns", "statement_figures"):
        for (issue,) in filled["conn"].execute(f"SELECT issue FROM {filled['schema']}.party_finance_{t} "
                                               "WHERE issue IS NOT NULL"):
            assert reconcile.within(0, float(issue.split(":")[0].replace(",", ""))), issue


def test_ruling_66_a_thousands_statement_s_precision_never_admits_100_or_more():
    from registers.party_finance import statements
    tol = lambda x: 1000.0                            # a statement printed in thousands rounds a line by up to $1,000
    assert statements._pick([500.0], 0.0, lambda x: x, tol) is None
    assert statements._pick([99.99], 0.0, lambda x: x, tol) == 99.99
    assert statements._pick([100.0], 0.0, lambda x: x, tol) is None
