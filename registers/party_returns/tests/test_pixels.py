"""The pixel route (plan 4.1): a return's image pages replayed from the page
reader's stored readings, its declaration read from the page reader's
text, its year from the form's own words elsewhere. The page shapes below
are the ones measured on GLM-OCR's readings of 74 returns on 19 October
2026; the last tests read real sample documents from the document store
and the reader store, calling no model and writing nothing live."""
import os

import pytest

from support import reader as rd
from support.docstore.landing import path_for, read_bytes
from registers.party_returns import pixels, read

GLM_PAGE = """DECLARATION

1. Party name:
   Example Party
2. TOTAL PARTY DONATIONS
   Part A: Party donations of more than $5,000 1455429.63
   Part C: Anonymous party donations of more than $1,500 0
   Part D: Overseas party donations of more than $50 0
   Part F: Donations protected from disclosure 5000
   Part G: Other party donations up to $5,000 416987.06
   Total Party Donations (A + C + D + F + G) 1877416.69
   Total Monetary Party Donations
3. TOTAL PARTY LOANS
   Part H: Party loans exceeding $15,000 255000
   Total (H + I) 255000
"""

TABLE_PAGE = """1. Party name:
   Example Party
<table><tr><td>Part A: Party donations of more than $15,000</td><td>$ 1,000.00</td></tr>
<tr><td>Part C: Anonymous party donations of more than $1,500</td><td>$0.00</td></tr>
<tr><td>Part D: Overseas party donations of more than $50</td><td>Nil</td></tr>
<tr><td>Part F: Donations protected from disclosure</td></tr>
<tr><td>$ 500.00</td></tr>
<tr><td>Part G: Other party donations up to $15,000</td><td>$0.00</td></tr>
<tr><td>Total (A + C + D + F + G)</td><td>$1,500.00</td></tr></table>
"""


def test_a_figure_one_space_after_its_threshold_is_the_part_s():
    d = pixels.read(GLM_PAGE)
    assert d.party_label == "Example Party"
    assert d.parts == {"A": 1455429.63, "C": 0.0, "D": 0.0, "F": 5000.0, "G": 416987.06}
    assert d.total == 1877416.69 and d.unpaired == []
    d.year = 2023
    assert d.problems() == []


def test_table_cells_and_a_figure_on_the_next_line_are_paired():
    d = pixels.read(TABLE_PAGE)
    assert d.parts == {"A": 1000.0, "C": 0.0, "D": 0.0, "F": 500.0, "G": 0.0}
    assert d.total == 1500.0


def test_the_loans_are_never_read_as_donations():
    d = pixels.read(GLM_PAGE.replace("   Total Party Donations (A + C + D + F + G) 1877416.69\n", ""))
    assert d.total is None


def test_the_declaration_page_is_the_one_with_the_donations_total():
    assert pixels.declaration_page({1: "cover letter", 2: GLM_PAGE, 3: GLM_PAGE}) == 2
    assert pixels.declaration_page({1: "Total (H + I) 0"}) is None


def test_the_year_comes_from_the_loans_page_even_where_the_2021_form_misprints_it():
    loans = "other loans from the same lender during 2020 or unpaid balances as at 31 December 2021 of a"
    auditor = "for the year ended 31 December 2020. And again the year ended 31 December 2020."
    assert pixels.return_year({1: GLM_PAGE, 11: loans, 13: auditor}) == (2021, "loans page")


def test_otherwise_the_most_stated_year_and_a_tie_refuses():
    a = "for the period 1 January 2021 to 31 December 2021. RETURN FOR 2021. comparatives: year ended 31 December 2020"
    assert pixels.return_year({1: a}) == (2021, "year ended")
    tie = "year ended 31 December 2021; year ended 31 December 2020"
    year, why = pixels.return_year({1: tie})
    assert year is None and "equally often" in why
    assert pixels.return_year({1: GLM_PAGE}) == (None, "no year stated on any page")
    assert pixels.return_year({1: "1 January 2020 to 31 December 2021"}) == (None, "no year stated on any page")


def test_the_lane_replays_exactly_the_settings_the_trial_stamped():
    from support.trials import readers as R
    assert read.PAGE_SETTINGS[0] == R.settings(R.READERS[R.INCUMBENT], 300)


# --- real sample documents, replayed -----------------------------------------

class ReplayOnly(rd.Store):
    """The reader store for reading; nothing is written."""

    def put(self, reading):
        return ""


def _sample(case: str) -> str:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for line in open(os.path.join(here, "sample.list"), encoding="utf-8"):
        if case in line and not line.startswith("#"):
            return line.split()[0]
    raise LookupError(case)


def _read(case: str):
    sha = _sample(case)
    if not os.path.exists(path_for(sha)):
        pytest.skip(f"document {sha[:12]} is not in the document store here")
    return read.read_return(read_bytes(sha), sha, ReplayOnly(), loaded_at="2026-10-19T20:00:00+13:00")


def test_a_scanned_return_reads_to_its_printed_total_from_pixels():
    out = _read("year from the loans page")
    assert [a for a in out.set_aside if a[0] in ("recognise", "read", "declaration")] == [], out.set_aside
    r = out.row
    assert r["read_from"] == "pixels" and r["reader"].endswith(": glm-ocr")
    assert r["profile"].startswith("ec-party-return-") and r["profile_version"] >= 1
    assert r["filed"]["year"] == 2023 and r["filed"]["year_from"] == "loans page"
    assert r["filed"]["declared_total"] == 1877416.69 and r["filed"]["total_check"] == "parts-sum"


def test_the_misprinted_2021_loans_sentence_still_gives_2021():
    out = _read("misprints its loans sentence")
    assert out.row and out.row["filed"]["year"] == 2021


def test_parts_that_miss_the_total_publish_nothing():
    out = _read("parts miss the total")
    assert out.row is None
    assert out.set_aside[0][0] == "declaration" and "parts sum to" in out.set_aside[0][1]


def test_a_misread_total_is_mended_only_by_the_part_pages_own_totals():
    out = _read("the total misread by $1,000")
    f = out.row["filed"]
    assert f["total_check"] == "parts-confirmed" and f["declared_total"] == 369535.17 and f["part_a"] == 52325.0
    assert f["donors_check"] == "parts-sum" and len(out.donors) == 11          # each donor's aggregated total dropped
    out = _read("a handwritten Part G the reader missed")
    f = out.row["filed"]
    assert f["total_check"] == "part-pages" and f["declared_total"] == 20776.49 and f["part_g"] == 20776.49
    assert f["part_a"] == 0.0 and f["donors_check"] == "declared-nil"


PART_PAGES = {2: "PART A: PARTY DONATIONS OF MORE THAN $15,000\nTOTAL FOR PART A $52,325.00\n",
              5: "TOTAL FOR PART C: $0.00\n", 9: "TOTAL FOR PART F $0.00\n",
              10: "PART G\nTOTAL FOR PART G\nTotal number of donations\n317,210.17\n"}


def test_recover_wants_every_part_page_to_agree():
    from support.docread.declaration import Declaration
    d = Declaration(parts={"A": 52325.0, "C": 0.0, "D": 0.0, "F": 0.0, "G": 317210.17}, total=368535.17,
                    total_letters="A+C+D+F+G")
    assert read.recover(d, {1: "", **PART_PAGES}, 1) == "parts-confirmed" and d.total == 369535.17
    d = Declaration(parts={"A": 52325.0, "C": 0.0, "D": 0.0, "F": 0.0, "G": 317210.17}, total=368535.17,
                    total_letters="A+C+D+F+G")
    other = {**PART_PAGES, 10: PART_PAGES[10].replace("317,210.17", "316,210.17")}
    assert read.recover(d, {1: "", **other}, 1) == "" and d.total == 368535.17      # a page disagrees: no mend
    d = Declaration(parts={}, total=317210.17, total_letters="A+C+D+F+G")
    assert read.recover(d, {1: "", 10: PART_PAGES[10]}, 1) == "part-pages" and d.parts["G"] == 317210.17
    d = Declaration(parts={}, total=400000.0, total_letters="A+C+D+F+G")
    assert read.recover(d, {1: "", 10: PART_PAGES[10]}, 1) == "" and d.parts == {}   # the pages do not make the total
    d = Declaration(parts={}, total=317210.17, total_letters="A+B+C+D+E")
    assert read.recover(d, {1: "", 10: PART_PAGES[10]}, 1) == ""                     # page letters not the form's own


def test_part_a_is_read_again_over_the_page_reader_s_stored_readings():
    # Labour 2024: a scanner's text layer garbles a figure; the re-read job's pages of Part A add up
    sha = [l.split()[0] for l in open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample.list"),
                                      encoding="utf-8") if "New Zealand Labour Party 2024" in l][0]
    if not os.path.exists(path_for(sha)):
        pytest.skip(f"document {sha[:12]} is not in the document store here")
    store = ReplayOnly()
    if read.stored_page(store, sha, 3) is None:
        pytest.skip(f"no stored page reading of {sha[:12]} page 3 here")
    out = read.read_return(read_bytes(sha), sha, store, loaded_at="2026-10-19T20:00:00+13:00")
    assert out.row["filed"]["donors_check"] == "parts-sum"
    assert "pixels" in {d["read_from"] for d in out.donors} and abs(sum(d["amount"] for d in out.donors) - 452766.53) < 0.005


def test_an_image_page_with_no_stored_reading_names_the_document(tmp_path):
    # an empty reader store: the live one has held this return's pages since queue rows 110 and 111 (20 October)
    sha = _sample("no stored page reading")
    if not os.path.exists(path_for(sha)):
        pytest.skip(f"document {sha[:12]} is not in the document store here")
    out = read.read_return(read_bytes(sha), sha, rd.Store(str(tmp_path / "empty")), loaded_at="2026-10-19T20:00:00+13:00")
    assert out.row is None
    stage, why = out.set_aside[0]
    assert stage == "read" and "ask for a re-read of " + _sample("no stored page reading") in why
