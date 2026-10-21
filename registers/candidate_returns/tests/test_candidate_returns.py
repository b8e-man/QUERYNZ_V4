"""The candidate-returns lane's tests. The declaration reader, the
Commission's listing and spreadsheet parsers and the join are tested on
texts shaped like the ones measured (figures and names made up); the filled
sample is tested against the row contract, the catch log and the cases its
list names. No model is called."""
import os

import pytest

from support import db, lane, rowcontract, sample
from registers.candidate_returns import check, commission, declaration, join, read

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "candidate_returns")

PAGE_2020 = """                                        Return of Electorate Candidate Donations
                                        and Expenses for the 2020 General Election
DECLARATION
1.   Candidate name:                                                                          COMPLETING THE RETURN
      Example Person
     Party name (if applicable):                                                              You can complete the return electronically
      Example Party                                                                           or by hand. If you complete the form
     Electorate contested:
      Example Electorate
2.   TOTAL CANDIDATE DONATIONS                                                                Electorate Candidate Donations and
     Complete Parts A to E on pages 2 to 6 if you have any donations to declare.
     Write 'NIL' if you have NO donations, or contributions                                   CHECKLIST
     to a donation, to declare under Parts A, C or D                                 NIL
                                                                                    $ 2,000.00
                                                                                              Step 1 completed                       x
     Part A: Candidate donations of more than $1,500
     Part C: Anonymous candidate donations of more                                            Parts A to E completed or              x
             than $1,500                                                            $ 0.00    'NIL' entered at step 2
     Part D: Overseas candidate donations of more                                   $ 0.00    Parts F and G completed or             x
             than $50                                                                         'NIL' entered at step 3
                                                  Total (A + C + D)                 $ 2,000.00
                                                                                              Declaration signed and dated
3.   TOTAL CANDIDATE ELECTION EXPENSES                                                        FILING THE RETURN
     Complete Parts F and G on pages 7 to 9 if you have any expenses to declare.
     Write 'NIL' if you have NO expenses to declare
     Part F: Candidate only election advertising                                    $ 1,211.13 fail to comply with these requirements
     Part G: Election advertisements shared with the                                          commit an offence and may be referred
                                                                                    $ 2,000.00
             party and/or other candidates                                                    to the Police.
                                                     Total (F + G)                  $ 3,211.13 by post to PO Box 3220,
4.   I declare that to the best of my knowledge this return, filed pursuant to sections 205K and 209
     SIGNATURE                                               DATE: DD / MM / YYYY
                                                                      20/12/2020
"""

PAGE_2023 = """                                         Return of Electorate Candidate Donations, Expenses
                                         and Loans for the 2023 General Election
2.   TOTAL CANDIDATE DONATIONS
     Write 'NIL' if you have NO donations, or contributions to
     a donation, to declare under Parts A, C or D                                                        CHECKLIST
     Part A: Candidate donations of more than $1,500                                    2317.50
     Part C: Anonymous candidate donations of more
             than $1,500                                                                     0           Parts A to E completed or
     Part D: Overseas candidate donations of more                                             0
             than $50                                                                                    Parts F and G completed or
                                                         Total (A + C + D)              2317.50          'NIL' entered at step 3
3.   TOTAL CANDIDATE ELECTION EXPENSES
     Write 'NIL' if you have NO expenses to declare
     Part F: Candidate only election advertising                                              0          FILING THE RETURN
     Part G: Election advertisements shared with the
                                                                                      1271.3005
             party and/or other candidates
                                                             Total (F + G)            1271.3005
4.   TOTAL CANDIDATE LOANS
     Write 'NIL' if you have NO loans to declare                                             NIL
     Part H: Candidate loans                                                                  0            34-42 Manners Street,
5.   I declare that to the best of my knowledge this return
"""

PIXELS = """2. TOTAL CANDIDATE DONATIONS
Complete Parts A to E on pages 2 to 7 if you have any donations to declare.
Write 'NIL' if you have NO donations, or contributions to a donation, to declare under Parts A, C or D
Part A: Candidate donations of more than $1,500
Part C: Anonymous candidate donations of more than $1,500
Part D: Overseas candidate donations of more than $50
Total (A + C + D) $44,000.00
3. TOTAL CANDIDATE ELECTION EXPENSES
Write 'NIL' if you have NO expenses to declare
Part F: Candidate only election advertising
Part G: Election advertisements shared with the party and/or other candidates
Total (F + G) $2915-82
4. TOTAL CANDIDATE LOANS
Part H: Candidate loans
$0.00
5. I declare that to the best of my knowledge this return, filed pursuant to sections 205K, 209 and 214GA
"""


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


def test_a_figure_above_its_label_and_the_checklist_column_are_read_right():
    d = declaration.read(PAGE_2020)
    assert d.year == 2020 and d.signed == "20/12/2020"
    assert d.sections["donations"].parts == {"A": 2000.0, "C": 0.0, "D": 0.0} and d.figure("donations") == 2000.0
    assert d.sections["expenses"].parts == {"F": 1211.13, "G": 2000.0} and d.figure("expenses") == 3211.13
    assert d.sections["donations"].step == [0.0] and d.problems("donations") == [] and d.problems("expenses") == []


def test_a_form_field_s_four_decimals_round_to_the_cent_and_part_h_is_the_loans():
    d = declaration.read(PAGE_2023)
    assert d.year == 2023 and d.figure("donations") == 2317.5 and d.figure("expenses") == 1271.3
    assert d.figure("loans") == 0.0 and d.check("loans") == "part-h"
    assert all(d.problems(s) == [] for s in ("donations", "expenses", "loans"))


def test_the_page_reader_s_plain_text_and_a_hyphen_for_the_point():
    d = declaration.read(PIXELS, layout=False)
    assert d.figure("donations") == 44000.0 and d.check("donations") == "total"
    assert d.figure("expenses") == 2915.82                     # `$2915-82`: a hyphen counts only after `$`
    assert d.sections["donations"].step == []                 # the sentence's own quoted 'NIL' is the form's text


def test_the_step_cell_s_figure_stands_when_the_parts_are_the_form_s_zeros():
    page = PAGE_2020.replace("Write 'NIL' if you have NO expenses to declare",
                             "                                                       1495.86\n     Write 'NIL' if you have NO expenses to declare")
    page = page.replace("$ 1,211.13", "$ 0.00    ").replace("$ 2,000.00\n             party", "$ 0.00\n             party")
    page = page.replace("Total (F + G)                  $ 3,211.13", "Total (F + G)                  $ 0.00    ")
    d = declaration.read(page)
    assert d.figure("expenses") == 1495.86 and d.check("expenses") == "step-cell" and d.problems("expenses") == []


def test_a_typed_figure_over_the_form_s_printed_zero():
    page = PAGE_2020.replace("     Part F: Candidate only election advertising                                    $ 1,211.13",
                             "     Part F: Candidate only election advertising                        0      $1,211.13")
    d = declaration.read(page)
    assert d.sections["expenses"].parts["F"] == 1211.13 and d.problems("expenses") == []


def test_parts_that_do_not_sum_to_the_total_are_a_problem_not_a_number():
    d = declaration.read(PAGE_2020.replace("$ 3,211.13", "$ 3,999.13"))
    assert any("parts sum to" in p for p in d.problems("expenses"))


def _expenses_total(total: str):
    return declaration.read(PAGE_2020.replace("$ 3,211.13", total))


@pytest.mark.parametrize("total, issue", [("$ 3,111.14", "+99.99"), ("$ 3,311.12", "-99.99"), ("$ 3,211.12", "+0.01")])
def test_ruling_66_parts_within_100_publish_the_printed_total_with_the_difference_named(total, issue):
    d = _expenses_total(total)
    assert d.problems("expenses") == [] and d.check("expenses") == "parts-sum"
    assert d.figure("expenses") == float(total.strip("$ ").replace(",", ""))      # the printed total, never the parts' sum
    assert d.issues("expenses") == [f"{issue}: expenses Parts F + G against the printed total"]
    assert d.issues("donations") == []


@pytest.mark.parametrize("total", ["$ 3,111.13", "$ 3,311.13", "$ 3,111.12"])
def test_ruling_66_a_difference_of_100_or_more_is_set_aside(total):
    d = _expenses_total(total)
    assert any("parts sum to 3211.13" in p for p in d.problems("expenses")) and d.issues("expenses") == []


def test_ruling_66_the_tolerance_is_one_constant_and_100_exactly_is_out():
    from registers.candidate_returns import reconcile
    assert reconcile.RECONCILE_TOLERANCE_CENTS == 10000
    assert reconcile.within(99.99, 0) and not reconcile.within(100, 0) and not reconcile.within(0, 100.01)
    assert reconcile.issue(5.0, 5.0, "x") is None and reconcile.issue(4.5, 5.0, "x") == "-0.50: x"


LISTING = """<table><thead><tr><th>Year</th></tr></thead>
<tbody><tr><td><h4 class="key">Download</h4><div class="value"><a href="/assets/x/other.pdf"></a>
<a href="/assets/candidate-returns/2023/P/2023_P_Example-Electorate_ROE_Jane.pdf"><span class="sr-only">Download the return</span></a></div></td>
<td><h4 class="key">Year</h4><div class="value">2023</div></td>
<td><h4 class="key">Candidate</h4><div class="value"><span style="text-transform: uppercase">ROE</span>,<br>Jane</div></td>
<td><h4 class="key">Electorate</h4><div class="value">Ōtaki</div></td>
<td><h4 class="key">Party</h4><div class="value">Example Party</div></td>
<td><h4 class="key">Donations</h4><div class="value"> $2,000.00 </div></td>
<td><h4 class="key">Expenses</h4><div class="value"> nil </div></td></tr></tbody></table>"""


def test_a_listing_row_takes_the_link_that_carries_text():
    [r] = commission.listing_rows(LISTING)
    assert r.href.endswith("ROE_Jane.pdf") and r.surname == "ROE" and r.given == "Jane"
    assert (r.donations, r.expenses, r.year, r.electorate) == (2000.0, 0.0, 2023, "Ōtaki")


def test_the_spreadsheet_s_own_typing_and_a_challenge_page():
    data = ("Year,Electorate,LastName,FirstName,Party, Donations , Expenses ,Total loans\n"
            '2023,Ōtaki,ROE,Jane,Example," $4,250,00 "," $20.895.09 ",NIL\n'
            "2023,Ōtaki,DOE,John,,Return not received,Return not received,Return not received\n").encode()
    a, b = commission.spreadsheet_rows(data, "x.csv")
    assert (a.donations, a.expenses, a.loans, a.problems) == (4250.0, 20895.09, 0.0, ())
    assert not b.received and b.donations is None
    with pytest.raises(commission.NotATable):
        commission.spreadsheet_rows(b'<html><script src="/_Incapsula_Resource"></script></html>', "y.csv")


def _sheet(year, surname, electorate, given="Jane"):
    return commission.SheetRow(year, electorate, surname, given, "P", 0.0, 0.0, None, 2)


def _row(year, surname, electorate, href):
    return commission.ListingRow(year, surname, "Jane", electorate, "P", 0.0, 0.0, href)


def test_the_listing_s_link_replaces_an_original_and_a_file_without_a_year_abstains():
    listing = [_row(2023, "ROE", "Ōtaki", "/assets/Uploads/Roe-J-Otaki-amended-010224.pdf"),
               _row(2020, "DOE", "Example Electorate", "/assets/c/2020_P_Example-Electorate_DOE_Jane.pdf")]
    sheet = {2023: [_sheet(2023, "ROE", "Ōtaki"), _sheet(2023, "DOE", "Example Electorate")],
             2020: [_sheet(2020, "DOE", "Example Electorate")]}
    held = {"a" * 64: ["2023_P_Otaki_ROE_Jane.pdf"], "b" * 64: ["Roe-J-Otaki-amended-010224.pdf"],
            "c" * 64: ["Doe-J-Example-Electorate-v2.pdf"]}
    j = join.join(held, listing, sheet, {"a" * 64: 2023})
    orig, amended = j.placed["a" * 64], j.placed["b" * 64]
    assert amended.how == "listing link" and amended.status == "current"
    assert orig.how == "listing name" and orig.status == "replaced" and orig.replaced_by == "b" * 64
    assert orig.sheet is amended.sheet is sheet[2023][0]                 # macrons aside: Ōtaki is Otaki
    assert [s for s, _ in j.unplaced] == ["c" * 64]                      # 2020's listing and 2023's spreadsheet both answer


def test_the_outside_check_compares_current_returns_only():
    files = [{"document": "a", "status": "current", "sheet_key": "s/2", "year": 2023, "surname": "ROE", "electorate": "X"},
             {"document": "b", "status": "replaced", "sheet_key": "s/2", "year": 2023, "surname": "ROE", "electorate": "X"}]
    returns = [{"document": "a", "donations": 10.0, "expenses": 5.0, "loans": None, "loans_check": None},
               {"document": "b", "donations": 99.0, "expenses": 5.0, "loans": None, "loans_check": None}]
    com = [{"key": "s/2", "source": "spreadsheet", "donations": 10.0, "expenses": 5.004, "loans": None, "received": True,
            "year": 2023, "surname": "ROE", "electorate": "X"}]
    res = check.compare(files, returns, com)
    assert len(res["equal"]) == 1 and res["differs"] == []


# ---------------------------------------------------------------- the filled sample

def _schema():
    scope = os.path.join(REPO, ".scope")
    if os.path.exists(scope):
        for line in open(scope, encoding="utf-8"):
            if line.startswith("name:"):
                return sample.scratch_name(line.split(":", 1)[1].strip())
    return "scratch_gate_candidate_returns"


def _cases():
    out = {}
    for line in open(os.path.join(LANE, "sample.list"), encoding="utf-8"):
        if line.strip() and not line.startswith(("#", "key:")):
            sha, case = line.split(None, 1)
            out[case.strip()] = sha
    return out


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    from registers.candidate_returns import sample as S
    schema = _schema()
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        S.fill(conn, schema, sample.read_list(os.path.join(LANE, "sample.list")))
        conn.commit()
        q = lambda sql: [dict(zip([d[0] for d in c.description], r)) for c in [conn.execute(sql)] for r in c.fetchall()]
        yield {"schema": schema, "conn": conn, "files": q(f"SELECT * FROM {schema}.candidate_returns_files"),
               "returns": q(f"SELECT * FROM {schema}.candidate_returns_returns"), "aside": q(f"SELECT * FROM {schema}.candidate_returns_set_aside"),
               "commission": q(f"SELECT * FROM {schema}.candidate_returns_commission")}


def test_every_sample_return_is_a_row_or_set_aside_and_never_both(filled):
    rows = {r["document"] for r in filled["returns"]}
    aside = {a["document"] for a in filled["aside"] if a["stage"] in ("recognise", "read", "declaration", "join")}
    assert rows & aside == set()
    assert {f["document"] for f in filled["files"]} == rows | aside == set(_cases().values())


def test_every_row_keeps_the_row_contract(filled):
    for r in filled["returns"]:
        row = {**r, "loaded_at": str(r["loaded_at"])}
        assert rowcontract.validate(row) == [], r["key"]
        assert r["key"] == f"{r['document']}/declaration"


def test_the_sample_s_cases_land_where_the_list_says(filled):
    c, files = _cases(), {f["document"]: f for f in filled["files"]}
    rows = {r["document"]: r for r in filled["returns"]}
    stages = {}
    for a in filled["aside"]:
        stages.setdefault(a["document"], []).append(a["stage"])
    assert rows[c["a form field prints four decimals (1271.3005)"]]["expenses"] is not None
    assert rows[c["scan: the stored page reading, totals only"]]["read_from"] == "pixels"
    assert rows[c["a scanner's own OCR layer without the heading: the stored page reading"]]["read_from"] == "pixels"
    assert rows[c["the figure typed in the step cell, the form's $0.00 left in the parts"]]["expenses_check"] == "step-cell"
    assert stages[c["set aside: the expenses parts do not sum to the printed total"]] == ["declaration"]
    # read against an empty store (`key: empty-store` in sample.list), whatever a job has since stored for it
    assert stages[c["scan with no stored page reading: set aside for a re-read"]] == ["read"]
    assert rows[c["Part A on a candidate's copy of the form without the part's heading"]]["donors_check"] == "parts-sum"
    assert rows[c["Part A from pixels: the stored page reading, reconciled"]]["donors_check"] == "parts-sum"
    assert stages[c["Part A from pixels refused: the reader went down the columns"]] == ["part-a"]
    assert stages[c["a scanner's text layer with no printed total: set aside"]] == ["declaration"]
    no_year = files[c["no year in the path: the form's own title names the election"]]
    assert no_year["year"] == 2023 and no_year["placed_by"] == "spreadsheet name"
    rep, amd = c["replaced: the listing links the amendment"], c["the amendment that replaces it"]
    assert files[rep]["status"] == "replaced" and files[rep]["replaced_by"] == amd and files[amd]["status"] == "current"
    assert files[c["the 2022 Tauranga by-election, placed by its file name"]]["placed_by"] == "file name"
    over = rows[c["ruling 66: the expenses parts $0.03 over the printed total, published on the total with an issue"]]
    assert float(over["expenses"]) == 337.23 and over["issue"] == "+0.03: expenses Parts F + G against the printed total"
    under = rows[c["ruling 66: the expenses parts a cent under the printed total, the issue named"]]
    assert under["issue"] == "-0.01: expenses Parts F + G against the printed total"


def test_ruling_66_the_check_counts_the_issue_rows(filled):
    conn, schema = filled["conn"], filled["schema"]
    donors_ = [dict(zip(("key", "return_key", "issue"), r)) for r in
               conn.execute(f"SELECT key, return_key, issue FROM {schema}.candidate_returns_donors").fetchall()]
    got = check.issues(filled["returns"], donors_)
    assert got["returns"] == sum(1 for r in filled["returns"] if r["issue"]) >= 2
    assert got["largest_cents"] == 3


def test_the_outside_check_runs_on_the_sample(filled):
    res = check.compare(filled["files"], filled["returns"], filled["commission"])
    c = _cases()
    assert any(d[0] == c["reads under its own arithmetic; differs from the spreadsheet"] for d in res["differs"])
    assert any(e[0] == c["text 2020 form, parts sum, equal to the spreadsheet"] for e in res["equal"])


def test_the_published_views_build_on_the_lane_s_tables(filled):
    from registers.candidate_returns import load
    conn, schema = filled["conn"], filled["schema"]
    view = load.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.pub_")
    conn.execute(view)
    n = conn.execute(f"SELECT count(*) FROM {schema}.pub_candidate_return_totals").fetchone()[0]
    assert n == len(filled["returns"])
    cols = [d[0] for d in conn.execute(f"SELECT * FROM {schema}.pub_candidate_return_totals LIMIT 0").description]
    assert not any("address" in c for c in cols)
    assert cols[-1] == "issue"
    cols = [d[0] for d in conn.execute(f"SELECT * FROM {schema}.pub_candidate_return_donors LIMIT 0").description]
    assert cols[-1] == "issue"


def test_the_scan_route_never_calls_a_model(monkeypatch):
    from support.docread import pagereader
    monkeypatch.setattr(pagereader, "ocr_pages", lambda *a, **k: (_ for _ in ()).throw(AssertionError("a model was called")))
    r = read.read_return(b"%PDF-1.4 not really", "0" * 64)
    assert r.row is None and r.set_aside


# ---------------------------------------------------------------- Part A

PART_A = """    PART A: CANDIDATE DONATIONS OF MORE THAN $1,500
    OTHER THAN ANONYMOUS OR OVERSEAS DONATIONS
                                        WRITE 'NIL' IF YOU HAVE NO DONATIONS TO DECLARE
                                                                                                 TOTAL FOR PART A                 $ 9,500.00
                                                                                                 Does the donation
                                                                       Date donation or         contain contributions      Amount of donation or total
                                                                     aggregated donations       from another person          aggregated donations
                Donor's name and street address
                                                                           received             of more than $1,500            (including GST)
                                                                            dd/mm/yyyy            Enter YES or NO                    $0.00
                                                                                                If YES complete Part B
    Sample Form Person
    1 Sample Street, Sampletown                                      2/06/2020- 14/07/2020               Yes                      $5,000.00
    Sampleshire
    Jane Example                                                         18/8/2020
                                                                                                         No                       $ 7,000.00
    12 Example Road, Exampletown
    Example Holdings Limited, Exampleville                               1/09/2020
    PO Box 1, Exampletown                                                                                No                       $ 2,500.00
PART A                                                                                                                                          Page: 2
"""


def test_part_a_drops_the_form_s_example_and_keeps_every_address_private(monkeypatch):
    from registers.candidate_returns import donors
    example = "Sample Form Person 1 Sample Street, Sampletown Sampleshire"
    monkeypatch.setattr(donors, "EXAMPLE_CELL", donors._fold_hash(example))
    part = donors.read({2: PART_A}, 9500.0)
    assert part.problems == [] and part.check == "parts-sum" and part.examples == 1
    assert [(r["name"], r["amount"]) for r in part.rows] == [("Jane Example", 7000.0), ("Example Holdings Limited", 2500.0)]
    assert "Example Road" in part.rows[0]["address"] and "Exampleville" in part.rows[1]["address"]
    assert all(not any(ch.isdigit() for ch in r["name"]) for r in part.rows)


def test_part_a_that_does_not_add_up_is_set_aside_whole(monkeypatch):
    from registers.candidate_returns import donors
    monkeypatch.setattr(donors, "EXAMPLE_CELL", donors._fold_hash("Sample Form Person 1 Sample Street, Sampletown Sampleshire"))
    part = donors.read({2: PART_A}, 10000.0)
    assert part.rows == [] and any("add to 9,500.00" in p for p in part.problems)


@pytest.mark.parametrize("printed, admitted, issue", [("9,599.99", True, "-99.99"), ("9,400.01", True, "+99.99"),
                                                      ("9,600.00", False, None), ("9,400.00", False, None),
                                                      ("9,600.01", False, None), ("9,500.00", True, None)])
def test_ruling_66_part_a_rows_within_100_of_both_totals_publish_with_the_issue_on_every_row(monkeypatch, printed, admitted,
                                                                                             issue):
    from registers.candidate_returns import donors
    monkeypatch.setattr(donors, "EXAMPLE_CELL", donors._fold_hash("Sample Form Person 1 Sample Street, Sampletown Sampleshire"))
    part = donors.read({2: PART_A.replace("$ 9,500.00", f"$ {printed}")}, float(printed.replace(",", "")))
    if not admitted:
        assert part.rows == [] and part.problems
        return
    assert part.problems == [] and len(part.rows) == 2
    want = None if issue is None else (f"{issue}: the 2 Part A rows against the declaration's Part A; "
                                       f"{issue}: the 2 Part A rows against TOTAL FOR PART A")
    assert part.issue == want and all(r["issue"] == want for r in part.rows)


def test_a_name_ends_at_its_comma_and_a_long_one_line_name_is_not_vouched_for():
    from registers.candidate_returns import donors
    assert donors.trim("Jane Example, Exampleville", False)[:2] == ("Jane Example", "Exampleville")
    assert donors.trim("Example, Jane", False)[0] == "Example, Jane"
    assert donors.trim("Jane Mary Example Exampleville Exampleshire", True)[2]
    assert donors.trim("The Example Electorate Committee Of Somewhere", True)[2] == ""


def test_published_donors_keep_the_row_contract_and_their_addresses_stay_private(filled):
    conn, schema = filled["conn"], filled["schema"]
    cur = conn.execute(f"SELECT * FROM {schema}.candidate_returns_donors")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    assert rows, "the sample holds returns whose Part A reconciles"
    assert not any("address" in c for c in cols)
    private = {r[0] for r in conn.execute(f"SELECT key FROM {schema}_private.candidate_returns_addresses")}
    for r in rows:
        assert rowcontract.validate({**r, "loaded_at": str(r["loaded_at"])}) == [], r["key"]
        assert r["key"] in private and not any(ch.isdigit() for ch in r["donor"])
    by_return = {}
    for r in rows:
        by_return[r["return_key"]] = round(by_return.get(r["return_key"], 0) + float(r["amount"]), 2)
    parts = {r["key"]: float(r["part_a"] or 0) for r in filled["returns"]}
    assert all(abs(by_return[k] - parts[k]) < 0.005 for k in by_return)


def test_a_copy_of_the_form_without_its_heading_is_known_by_its_printed_total(monkeypatch):
    """A candidate's own copy of the form (`To add more rows …`) keeps the table and `TOTAL FOR PART A` but drops
    the part's heading and footer; a cell's note in money (`($10,000 of it …`) never ends a name."""
    from registers.candidate_returns import donors
    monkeypatch.setattr(donors, "EXAMPLE_CELL", donors._fold_hash("Sample Form Person 1 Sample Street, Sampletown Sampleshire"))
    page = "\n".join(l for l in PART_A.splitlines() if "CANDIDATE DONATIONS OF" not in l and not l.startswith("PART A "))
    page = page.replace("Example Holdings Limited, Exampleville", "Example Holdings Limited ($2,000 cash) Exampleville")
    part = donors.read({2: "  To add more rows to this table\n" + page}, 9500.0)
    assert part.problems == [] and [r["name"] for r in part.rows] == ["Jane Example", "Example Holdings Limited"]


PIXELS_A = """PART A: CANDIDATE DONATIONS OF MORE THAN $1,500
OTHER THAN ANONYMOUS OR OVERSEAS DONATIONS
TOTAL FOR PART A $9,500.00
Donor's name and street address
Date donation or aggregated donations received dd/mm/yyyy
Does the donation contain contributions from another person of more than $1,500
Enter YES or NO
If YES complete Part B
Amount of donation or total aggregated donations (including GST) $0.00
Sample Form Person
1 Sample Street, Sampletown Sampleshire
2/06/2020 - 14/07/2020 Yes $5,000.00
Jane Example, 12 Example Road, Exampletown
18/8/2020
No
$7,000.00
Example Holdings Limited, PO Box 1, Exampletown
1/09/2020 No $2,500.00
PART A
Page: 2
"""


def _pixels_example(monkeypatch):
    from registers.candidate_returns import donors
    monkeypatch.setattr(donors, "EXAMPLE_CELL", donors._fold_hash("Sample Form Person 1 Sample Street, Sampletown Sampleshire"))


def test_part_a_from_pixels_drops_the_example_and_reconciles(monkeypatch):
    from registers.candidate_returns import pixels
    _pixels_example(monkeypatch)
    part = pixels.read({2: PIXELS_A}, 9500.0)
    assert part.problems == [] and part.check == "parts-sum" and part.examples == 1
    assert [(r["name"], r["amount"], r["yes_no"]) for r in part.rows] == [("Jane Example", 7000.0, "No"),
                                                                          ("Example Holdings Limited", 2500.0, "No")]
    assert all("Ex" in r["address"] and not any(ch.isdigit() for ch in r["name"]) for r in part.rows)


def test_part_a_from_pixels_read_column_by_column_is_refused(monkeypatch):
    """The reader listed the names, then the headings, then the figures: pairing them by order is the one fault the
    total cannot see, so the page is set aside."""
    from registers.candidate_returns import pixels
    _pixels_example(monkeypatch)
    lines = PIXELS_A.splitlines()
    names = ["Jane Example, 12 Example Road, Exampletown", "Example Holdings Limited, PO Box 1, Exampletown"]
    body = [l for l in lines if l not in names]
    body.insert(4, names[0])
    body.insert(5, names[1])
    part = pixels.read({2: "\n".join(body)}, 9500.0)
    assert part.rows == [] and any("among its column headings" in p for p in part.problems)
    swapped = PIXELS_A.replace("18/8/2020\nNo\n$7,000.00\n", "18/8/2020\n").replace("1/09/2020 No $2,500.00", "Exampleville\nNo\n$7,000.00\n$2,500.00")
    part = pixels.read({2: swapped}, 9500.0)
    assert part.rows == [] and part.problems


def test_a_part_a_not_read_is_not_a_nil_and_its_pages_are_listed_for_a_re_read():
    from registers.candidate_returns import replay
    sha = "e" * 64
    run = {sha: {"year": 2023, "set_aside": [("part-a", f"{read.REREAD} {sha} pages 2, 3, 4")]},
           "f" * 64: {"year": 2020, "set_aside": [("read", "no text page carries the declaration; 3 of 3 pages are images, "
                                                           "with no stored page reading (pages 1, 2, 3): ask for a re-read of x")]}}
    assert replay.rereads(run) == [(sha, 2023, "part-a", [2, 3, 4]), ("f" * 64, 2020, "read", [1, 2, 3])]


def test_a_scanner_s_text_layer_stands_only_on_its_printed_total():
    """A scanner's own OCR layer dropped a handwritten Part G and total whole (`ca579c46524e`: the page shows $470,
    the layer nothing), leaving NIL in Part F to read as expenses of 0.00: on a picture page parts alone never stand."""
    page = PAGE_2020.replace("$ 2,000.00\n             party", "\n             party")
    page = page.replace("Total (F + G)                  $ 3,211.13", "Total (F + G)                            ")
    page = page.replace("$ 1,211.13", "NIL       ")
    d = declaration.read(page)
    assert d.check("expenses") == "parts" and d.figure("expenses") == 0.0 and d.problems("expenses") == []
    from types import SimpleNamespace
    r = SimpleNamespace(reader="text-layer", model="pdftotext", profile=read.TEXT, profile_version=1, read_from="text")
    typed = read._publish_or_set_aside(read.Result("a" * 64), d, 1, r, "x", scanner=False)
    assert typed.set_aside == [] and typed.row["filed"]["expenses"] == 0.0
    scanned = read._publish_or_set_aside(read.Result("b" * 64), d, 1, r, "x", scanner=True)
    assert scanned.row is None and read.SCANNER in scanned.set_aside[0][1]
    from registers.candidate_returns import replay
    assert replay.rereads({"b" * 64: {"year": 2020, "set_aside": scanned.set_aside}}) == [("b" * 64, 2020, "declaration", [1])]
