"""Ruling 66 (Arthur, 21 October 13:00): a difference below $100 between a
part's figures and the printed total they are held to is reconciled and
named in `issue`; $100 or more is set aside. Each case is held either side
of $100 and at exactly $100, through the lane's own readers."""
import pytest

from registers.party_returns import donors, loans, read, reconcile
from registers.party_returns.tests.test_party_returns import PAGE, filled  # noqa: F401 — the module's filled sample
from registers.party_returns.tests.test_schedules import DECLARATION, LAYOUT, LENDERS

#: (cents the printed figure is below the parts, admitted)
EDGES = ((0, True), (9999, True), (10000, False), (10001, False))


def test_the_tolerance_is_one_constant_below_one_hundred_dollars():
    assert reconcile.RECONCILE_TOLERANCE_CENTS == 10000
    assert reconcile.within(100.0, 0.01) and not reconcile.within(100.0, 0.0) and not reconcile.within(0.0, 100.01)
    assert reconcile.issue(31000.0, 31000.0, "x") is None
    assert reconcile.issue(31000.0, 30900.01, "x") == "+99.99: x"
    assert reconcile.issue(30900.01, 31000.0, "x") == "-99.99: x"


@pytest.mark.parametrize("off,admitted", EDGES)
def test_part_a_rows_against_the_declaration_s_part_a(off, admitted):
    part = donors.read({2: LAYOUT}, {2: "text"}, (3100000 - off) / 100)
    assert (part.check == "parts-sum") is admitted
    assert bool(part.rows) is admitted
    if not admitted:
        assert part.issue is None and any("rows read add to 31,000.00" in p for p in part.problems)
    elif off:
        want = f"+{off / 100:.2f}: the 2 Part A rows against the declaration's Part A"
        assert part.issue == want and all(r["issue"] == want for r in part.rows)
    else:
        assert part.issue is None and all(r["issue"] is None for r in part.rows)


@pytest.mark.parametrize("off,admitted", EDGES)
def test_part_a_rows_against_total_for_part_a(off, admitted):
    printed = f"$ {(3100000 + off) / 100:,.2f}"
    part = donors.read({2: LAYOUT.replace("$ 31,000.00", printed)}, {2: "text"}, 31000.0)
    assert bool(part.rows) is admitted
    if admitted and off:
        assert part.issue == f"-{off / 100:.2f}: the 2 Part A rows against TOTAL FOR PART A"


@pytest.mark.parametrize("off,admitted", EDGES)
def test_the_declaration_s_parts_against_its_declared_total(off, admitted):
    total = f"{(21996470 + off) / 100:.2f}"
    decl = read.declaration.read(PAGE.replace("219964.7    documentation", f"{total}    documentation"))
    out = read.Result("0" * 64)
    assert read._publish_or_set_aside(out, decl) is admitted
    assert bool(out.set_aside) is not admitted
    issue = read.declaration_issue(decl)
    if admitted and off:
        assert issue == f"-{off / 100:.2f}: the declaration's parts (A + C + D + F + G) against its declared total"
        assert decl.total == float(total)                # the printed total is the one published
    elif admitted:
        assert issue is None
    else:
        assert issue is None and "parts sum to" in out.set_aside[0][1]


@pytest.mark.parametrize("off,admitted", EDGES)
def test_part_h_and_part_i_against_the_declared_loans_total(off, admitted):
    got = loans.declared(DECLARATION.replace("Total (H + I) $119,000.00", f"Total (H + I) ${(11900000 + off) / 100:,.2f}"))
    assert (got.problems == []) is admitted
    assert (got.issue is not None) is (admitted and off > 0)


@pytest.mark.parametrize("off,admitted", EDGES)
def test_part_h_lenders_against_the_declaration_s_part_h(off, admitted):
    part = loans.read({13: LENDERS}, {13: "pixels"}, (13000000 - off) / 100)
    assert bool(part.rows) is admitted
    if admitted and off:
        assert all(r["issue"] == f"+{off / 100:.2f}: the 2 Part H loans against the declaration's Part H" for r in part.rows)


def test_a_donor_s_aggregated_total_below_100_dollars_out_carries_the_issue():
    page2 = "\n".join(["PART A: PARTY DONATIONS OF MORE THAN $15,000", "TOTAL FOR PART A $16,025.00",
                       "Donor's name and street address",
                       "1. Example Donor, 2 Model Street, Exampleton 18/04/2019 NO $8,025.00",
                       "2. Example Donor, 2 Model Street, Exampleton 02/12/2019 NO $8,000.00"])
    for agg, admitted in (("$15,925.01", True), ("$15,925.00", False)):
        page3 = f"Donor's name and street address\nExample Donor Aggregated total {agg}\n"
        part = donors.read({2: page2, 3: page3}, {2: "pixels", 3: "pixels"}, 16025.0)
        assert bool(part.rows) is admitted
    assert part.rows == [] and any("aggregated total of 15,925.00" in p for p in part.problems)


def test_every_published_view_ends_with_the_issue_column(filled):  # noqa: F811
    from registers.party_returns import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema).replace("pub.", f"{schema}."))
    for view in ("party_return_totals", "party_return_donors", "party_return_loans"):
        cols = [r[0] for r in conn.execute("select column_name from information_schema.columns where table_schema = %s "
                                           "and table_name = %s order by ordinal_position", (schema, view))]
        assert cols[-1] == "issue", (view, cols[-3:])
    conn.rollback()


def test_the_sample_s_rounding_cent_is_published_with_its_issue(filled):  # noqa: F811
    schema, conn = filled["schema"], filled["conn"]
    got = conn.execute(f"select count(*), min(issue), max(issue) from {schema}.donors "
                       f"where document like '765c53fbeb28%'").fetchone()
    assert got[0] > 0 and got[1] == got[2] and got[1].startswith("+0.01: ")
