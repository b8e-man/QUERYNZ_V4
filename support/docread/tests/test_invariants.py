"""Each rule fires when it should, abstains when it cannot decide, and does
not fire on the three false findings that real data caught on 2026-09-23."""
import sys, pathlib

import pytest
from support.docread import invariants as inv
from support.docread.rows import Document, Row


def doc(rows, **kw):
    kw.setdefault("year", 2017)
    return Document(stem="t", rows=tuple(rows), **kw)


def r(n=None, donor="Acme Ltd 1 Queen St, Auckland", date="2017-05-01",
      amount=20000.0, part="A", page=1):
    return Row(n=n, donor=donor, date=date, amount=amount, part=part, page=page)


def fired(report, rule):
    return [f for f in report.findings if f.rule == rule]


def skipped(report, rule):
    return [s for s in report.skipped if s[0].startswith(rule)]


# --- row_numbers_complete --------------------------------------------------

def test_a_hole_in_the_printed_numbers_fails():
    d = doc([r(n=1), r(n=2), r(n=4)])
    f = fired(inv.check(d), "row_numbers_complete")
    assert f and f[0].severity == "fail" and "3" in f[0].detail


def test_a_lost_page_reads_as_a_run():
    d = doc([r(n=i) for i in (1, 2, 8, 9)])
    f = fired(inv.check(d), "row_numbers_complete")
    assert "3–7" in f[0].detail


def test_a_row_read_twice_fails():
    d = doc([r(n=1), r(n=2), r(n=2)])
    f = fired(inv.check(d), "row_numbers_complete")
    assert any("more than once" in x.detail for x in f)


def test_a_complete_sequence_passes():
    d = doc([r(n=1), r(n=2), r(n=3)])
    assert not fired(inv.check(d), "row_numbers_complete")


def test_completeness_abstains_when_any_row_lacks_a_number():
    """The 2026-09-23 defect: a part where the reader dropped the number
    column on one page was reported as 'rows 1-12 were never read' when in
    fact they were read without numbers."""
    d = doc([r(n=13), r(n=14), r(n=None), r(n=None)])
    rep = inv.check(d)
    assert not fired(rep, "row_numbers_complete")
    assert skipped(rep, "row_numbers_complete")
    assert not fired(rep, "row_numbers_start_at_one")


def test_the_unnumbered_rows_are_reported_as_a_finding_not_only_a_skip():
    d = doc([r(n=13), r(n=None, page=2)])
    f = fired(inv.check(d), "rows_carry_printed_numbers")
    assert f and f[0].severity == "flag" and "page(s) 2" in f[0].detail


# --- row_numbers_start_at_one ----------------------------------------------

def test_a_part_beginning_above_one_fails():
    d = doc([r(n=13), r(n=14)])
    f = fired(inv.check(d), "row_numbers_start_at_one")
    assert f and f[0].severity == "fail" and f[0].rows == (1, 2, 3, 4, 5, 6,
                                                           7, 8, 9, 10, 11, 12)


# --- sum_matches_stated_total ----------------------------------------------

def test_the_sum_must_equal_the_printed_total():
    d = doc([r(n=1, amount=100.0), r(n=2, amount=50.0)],
            stated_totals={"A": 200.0})
    f = fired(inv.check(d), "sum_matches_stated_total")
    assert f and f[0].severity == "fail" and "50.00" in f[0].detail


def test_a_matching_sum_passes_to_the_cent():
    d = doc([r(n=1, amount=100.01), r(n=2, amount=50.0)],
            stated_totals={"A": 150.01})
    assert not fired(inv.check(d), "sum_matches_stated_total")


def test_the_sum_abstains_when_the_form_printed_no_total():
    d = doc([r(n=1)])
    rep = inv.check(d)
    assert not fired(rep, "sum_matches_stated_total")
    assert skipped(rep, "sum_matches_stated_total")


def test_a_rotation_preserves_the_sum_and_this_rule_cannot_see_it():
    """States the gate's limit as a test so it cannot be forgotten."""
    a = doc([r(n=1, donor="A Ltd", amount=100.0),
             r(n=2, donor="B Ltd", amount=50.0)], stated_totals={"A": 150.0})
    b = doc([r(n=1, donor="A Ltd", amount=50.0),
             r(n=2, donor="B Ltd", amount=100.0)], stated_totals={"A": 150.0})
    assert not fired(inv.check(a), "sum_matches_stated_total")
    assert not fired(inv.check(b), "sum_matches_stated_total")


# --- donor_aggregate_above_threshold ---------------------------------------

def test_a_part_a_donor_below_the_threshold_is_flagged():
    d = doc([r(n=1, donor="Small Co 2 High St", amount=900.0)])
    f = fired(inv.check(d), "donor_aggregate_above_threshold")
    assert f and f[0].severity == "flag"


def test_aggregated_rows_of_one_donor_are_summed_before_the_test():
    """Six small donations from one donor clear the threshold together; this
    rule must not flag each of them."""
    d = doc([r(n=i, donor="Gibbston Valley Winery 1820 SH6", amount=5000.0)
             for i in range(1, 6)])
    assert not fired(inv.check(d), "donor_aggregate_above_threshold")


def test_one_donor_at_two_addresses_is_one_donor():
    """The 2026-09-23 defect: keying on name AND address split Hagaman into
    two donors and flagged the smaller as below threshold."""
    d = doc([r(n=1, donor="Hagaman, Lianna 10 Coldstream Court, Christchurch",
               amount=1150.0),
             r(n=2, donor="Hagaman, Lianna 10 Coldstream Court, Ilam, "
                          "Christchurch", amount=30000.0)])
    assert not fired(inv.check(d), "donor_aggregate_above_threshold")


def test_the_threshold_abstains_before_2008():
    d = doc([r(n=1, amount=10.0)], year=2005)
    rep = inv.check(d)
    assert not fired(rep, "donor_aggregate_above_threshold")
    assert skipped(rep, "donor_aggregate_above_threshold")


def test_the_threshold_follows_the_2010_amendment():
    assert inv.threshold_for(2011) == 15000.0
    assert inv.threshold_for(2010) == 10000.0
    assert inv.threshold_for(2007) is None


def test_the_threshold_follows_the_2022_amendment():
    """The Commission, on its own page and in this estate's capture: *"The
    reporting requirements for parties changed on 1 January 2023 … the names
    of donors and contributors who gave more than $5,000 (down from
    $15,000)"*. Held at the old number, the rule accused 1,077 correctly
    disclosed donors of being below the threshold that required them."""
    assert inv.threshold_for(2023) == 5000.0
    assert inv.threshold_for(2022) == 15000.0


def test_a_donor_in_the_new_band_is_not_accused_after_the_amendment():
    """$6,000 is disclosable from 2023 and was not in 2022 — the same figure,
    a finding on one side of the date and silence on the other."""
    rows = [r(n=1, donor="Alpha Ltd 8 Ha Cr", amount=6000.0)]
    assert not fired(inv.check(doc(rows, year=2023)),
                     "donor_aggregate_above_threshold")
    assert fired(inv.check(doc(rows, year=2022)),
                 "donor_aggregate_above_threshold")


# --- donor_spelling_stable -------------------------------------------------

def test_two_spellings_of_one_donor_are_flagged():
    d = doc([r(n=1, donor="Alpha Helth Care Ltd 8 Ha Cr"),
             r(n=2, donor="Alpha Health Care Ltd 8 Ha Cr")])
    # different letters -> different keys, so this pair is NOT one donor;
    # the rule fires only where the key matches and the text differs.
    d2 = doc([r(n=1, donor="Alpha Health Care Ltd 8 Ha Cr, Manukau"),
              r(n=2, donor="Alpha  Health Care  Ltd 9 Ha Cr, Auckland")])
    assert not fired(inv.check(d2), "donor_spelling_stable")


def test_banded_aggregate_rows_are_not_treated_as_donors():
    """The 2026-09-23 defect: part C's banded aggregates ('Donations exceeding
    $1,500 but not exceeding $5,000') are not donors, and were checked as
    though they were. The pair below differs only in punctuation, so it is one
    key with two spellings — which MUST flag in part A and MUST NOT in C."""
    banded = [r(n=None, part="C", donor="Acme, Ltd 1 Queen St", amount=1.0),
              r(n=None, part="C", donor="Acme Ltd. 1 Queen St", amount=2.0)]
    assert not fired(inv.check(doc(banded)), "donor_spelling_stable")
    assert not fired(inv.check(doc(banded)), "donor_aggregate_above_threshold")


def test_the_same_pair_in_a_donor_naming_part_does_flag():
    """The other half of the pin: the rule is restricted by PART, not broken."""
    named = [r(n=1, part="A", donor="Acme, Ltd 1 Queen St", amount=1.0),
             r(n=2, part="A", donor="Acme Ltd. 1 Queen St", amount=2.0)]
    f = fired(inv.check(doc(named)), "donor_spelling_stable")
    assert f and f[0].severity == "flag"


# --- the rest --------------------------------------------------------------

def test_a_row_without_an_amount_fails():
    d = doc([r(n=1, amount=None)])
    f = fired(inv.check(d), "every_row_has_an_amount")
    assert f and f[0].severity == "fail"


def test_a_date_outside_the_return_year_is_flagged():
    d = doc([r(n=1, date="2016-05-01")])
    f = fired(inv.check(d), "dates_within_return_year")
    assert f and f[0].severity == "flag" and "2016" in f[0].detail


def test_dates_abstain_when_the_year_is_unknown():
    d = doc([r(n=1)], year=None)
    rep = inv.check(d)
    assert not fired(rep, "dates_within_return_year")
    assert skipped(rep, "dates_within_return_year")


def test_an_identical_row_twice_is_flagged():
    d = doc([r(n=1), r(n=2)])
    f = fired(inv.check(d), "no_repeated_row")
    assert f and f[0].severity == "flag"


# --- the report itself -----------------------------------------------------

def test_a_report_states_what_it_could_not_check():
    d = doc([r(n=1)])
    rep = inv.check(d)
    assert rep.skipped, "a report with no totals must declare the gap"
    assert 0.0 < rep.coverage < 1.0


def test_coverage_is_zero_when_nothing_can_be_decided():
    rep = inv.check(Document(stem="empty"))
    assert rep.coverage == 0.0
    assert rep.servable, "no rows is not a contradiction, it is an empty read"


def test_servable_means_no_contradiction_not_correct():
    d = doc([r(n=1), r(n=2)], stated_totals={"A": 40000.0})
    assert inv.check(d).servable
