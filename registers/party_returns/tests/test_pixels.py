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


def test_an_image_page_with_no_stored_reading_names_the_document(tmp_path):
    # an empty reader store: the live one has held this return's pages since queue rows 110 and 111 (20 October)
    sha = _sample("no stored page reading")
    if not os.path.exists(path_for(sha)):
        pytest.skip(f"document {sha[:12]} is not in the document store here")
    out = read.read_return(read_bytes(sha), sha, rd.Store(str(tmp_path / "empty")), loaded_at="2026-10-19T20:00:00+13:00")
    assert out.row is None
    stage, why = out.set_aside[0]
    assert stage == "read" and "ask for a re-read of " + _sample("no stored page reading") in why
