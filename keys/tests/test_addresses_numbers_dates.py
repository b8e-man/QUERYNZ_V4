"""Addresses fold for equality only and keep their numbers; official
numbers are read into one spelling and checked; filed dates are read day
first and a pixel-read year is corrected from the file name."""
import datetime as dt

from keys import addresses as a
from keys import dates as d
from keys import numbers as num


def test_address_key_is_for_equality_and_keeps_the_number():
    k = a.address_key
    assert k("12 Example Street, Karori, Wellington") == k("12 Example St, Karori, Wellington 6012"[:-5]) == "12examplestkaroriwellington"
    assert k("1 Main Rd") != k("11 Main Rd")           # the older key dropped short numbers
    assert k("PO Box 123, Wellington") == k("P.O. Box 123 Wellington New Zealand") == "pobox123wellington"
    assert k("Ōtaki Road") == k("Otaki Rd")
    assert k("") == "" and k(None) == ""


def test_po_box_is_not_a_street():
    assert a.is_po_box("PO Box 5, Nelson") and a.is_po_box("Private Bag 92019")
    assert not a.is_po_box("5 Box Street")


def test_clean_address_strips_a_leading_date_and_refuses_a_page_dump():
    assert a.clean_address("28/05/2018 NO") == (None, "28/05/2018")
    assert a.clean_address("12/03/2019, 4 Example Road, Hamilton") == ("4 Example Road, Hamilton", "12/03/2019")
    assert a.clean_address("4 Example Road, Hamilton") == ("4 Example Road, Hamilton", None)
    assert a.clean_address("x" * 300) == (None, "page dump")
    assert a.clean_address("  ") == (None, None) and a.clean_address(None) == (None, None)
    assert a.clean_address("48/09/2014 No $10,000.00") == (None, "48/09/2014")


def test_nzbn_is_thirteen_digits_with_a_check_digit():
    assert num.nzbn("9429041234567") is None          # bad check digit
    good = "942904123456" + str((10 - sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed("942904123456"))) % 10) % 10)
    assert num.nzbn(good) == good
    assert num.nzbn(good[:4] + " " + good[4:]) == good
    assert num.nzbn("123") is None and num.nzbn(None) is None


def test_other_numbers():
    assert num.company_number("0001234") == "1234" and num.company_number("") is None
    assert num.charity_number("cc 0012345") == "CC12345" and num.charity_number("12345") is None
    assert num.society_number("2501234") == "2501234"


def test_filed_dates_are_read_day_first_in_every_shape():
    for text, want in (("07/09/2026", "2026-09-07"), ("21/1/26", "2026-01-21"), ("10 Mar 2026", "2026-03-10"),
                       ("10 March 2026", "2026-03-10"), ("2026-09-07", "2026-09-07"), ("received 3.4.2024", "2024-04-03")):
        assert d.filed_date(text).isoformat() == want, text
    for text in ("45/08/2014", "08/15/2023", "Unclear", "", None, "31/02/2024"):
        assert d.filed_date(text) is None, text


def test_year_from_recovers_the_file_date():
    today = dt.date(2026, 10, 18)
    assert d.year_from("16 May 2093", "Gregory_J_and_Paula_-R_Dickson_16_May_2023.pdf", today) == (2023, "source_file (read year corrected)")
    assert d.year_from("25 AUG 202%", "J_S_Garing_28_August_2023.pdf", today) == (2023, "source_file")
    assert d.year_from("Unclear", "E_Tu_Incorporated_23_May_2023.pdf", today) == (2023, "source_file")
    assert d.year_from("01/06/2023", "x.pdf", today) == (2023, "date_received")
    assert d.year_from(None, "AOTEAR1.PDF", today) == (None, "undated")
    assert d.year_from("20 July 2035", "W_and_A_Norman_20_July_2023.pdf", today) == (2023, "source_file (read year corrected)")
    assert d.year_from("2025-06-26", "Warren-Lewis_26_June_2023.jpg", today) == (2023, "source_file (read year corrected)")
    assert d.year_from("2023-06-26", "Warren-Lewis_26_June_2023.jpg", today) == (2023, "date_received")
    assert d.year_from("2025-07-01", "Warren-Lewis_26_June_2023.jpg", today) == (2025, "date_received")
