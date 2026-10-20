"""What a row shows, on fixtures: a suppressed name reads 'name suppressed'
in the title and the statement; a connection with no date reads 'undated'
and states the files it was seen in; a dated role reads its dates; a
citation names the document or says the original is not held; money is
formatted; the ref form is the board's."""
import datetime as dt
import decimal

from products.report import catalogue as cat
from products.report import rows


def director(**kw):
    r = {"key": "companies/1/director/a", "entity_key": "companies/1", "full_name": "Jane DOE", "role_type": "Director",
         "appointed_on": dt.date(2020, 1, 2), "ended_on": None, "in_latest": True, "first_file": "companies-2020-01",
         "last_file": "companies-2026-07", "suppressed": False, "document": "ab" * 32, "page": 1, "place": "line 9",
         "read_from": "text", "reader": "export", "profile": "companies-export", "nzbn": "9429000000001"}
    r.update(kw)
    return r


def test_ref_form_is_register_colon_key():
    v = cat.BY_NAME["directors"]
    assert rows.ref_of(v, "companies/1/director/a") == "companies:companies/1/director/a"
    assert rows.split_ref("party_returns:abc/A/3") == ("party_returns", "abc/A/3")


def test_a_suppressed_name_is_suppressed_in_title_and_statement():
    v = cat.BY_NAME["directors"]
    r = director(suppressed=True, full_name="Secret Person")
    assert rows.title(v, r) == rows.SUPPRESSED
    s = rows.statement(v, r, "ACME LIMITED")
    assert "Secret Person" not in s and rows.SUPPRESSED in s and "Director of ACME LIMITED" in s


def test_a_revoked_prohibition_hides_its_name():
    v = cat.BY_NAME["gazette_prohibitions"]
    r = {"key": "n/1", "name": "Some Body", "action": "prohibited", "superseded_how": "revoked by a later notice",
         "statute": "s 385", "starts_on": dt.date(2021, 1, 1), "ends_on": None}
    assert rows.is_suppressed(v, r) and rows.title(v, r) == f"{rows.SUPPRESSED} · prohibited"


def test_a_dated_role_reads_its_dates_and_no_end_is_said():
    v = cat.BY_NAME["directors"]
    d = rows.dates(v, director())
    assert not d["undated"] and d["text"].startswith("from 2 January 2020; no end filed (in the latest file)")
    d2 = rows.dates(v, director(ended_on=dt.date(2021, 6, 1)))
    assert "to 1 June 2021" in d2["text"]


def test_an_undated_connection_says_undated_and_the_files_seen():
    v = cat.BY_NAME["shareholders"]
    r = {"key": "companies/1/shareholder/b", "entity_key": "companies/1", "name": "Nominees Ltd", "shareholder_type": "company",
         "shares": decimal.Decimal(100), "allocation_status": "allocated", "first_file": "companies-2019-01", "last_file": "companies-2026-07",
         "suppressed": False}
    d = rows.dates(v, r)
    assert d["undated"] and d["text"] == "undated; in the files from companies-2019-01 to companies-2026-07"
    s = rows.statement(v, r, "ACME LIMITED")
    assert "shareholder of record in ACME LIMITED" in s and "own" not in s.lower()


def test_a_year_only_row_is_dated_by_its_year():
    v = cat.BY_NAME["party_return_donors"]
    r = {"key": "h/A/3", "return_key": "h/declaration", "donor": "Rank Group Limited", "amount": decimal.Decimal("110000"),
         "party": "New Zealand First Party", "year": 2023, "document": "cd" * 32, "page": 4, "read_from": "pixels"}
    d = rows.dates(v, r)
    assert not d["undated"] and d["text"] == "2023 (the year the row is filed under)"
    assert rows.statement(v, r) == "Rank Group Limited · $110,000.00 to New Zealand First Party, in the party's return for 2023 (Part A); dates as printed: not stated"
    c = rows.citation(v, r)
    assert rows.cite_text(c) == "pub.party_return_donors h/A/3; document cdcdcdcdcdcd…; page 4; read from pixels: weaker evidence"


def test_a_row_without_a_document_says_the_original_is_not_held():
    v = cat.BY_NAME["companies"]
    r = {"key": "companies/1", "name": "ACME LIMITED", "status": "Registered", "entity_type": "NZ Limited Company",
         "nzbn": "9429000000001", "registered_on": dt.date(2001, 5, 5), "removed_on": None, "document": None}
    c = rows.citation(v, r)
    assert "not held" in rows.cite_text(c) and rows.statement(v, r) == "ACME LIMITED: Registered NZ Limited Company, NZBN 9429000000001"


def test_a_blank_value_says_not_stated():
    assert rows.fmt(None) == rows.NOT_STATED and rows.fmt("") == rows.NOT_STATED
    assert rows.fmt(decimal.Decimal("1234.5"), "amount") == "$1,234.50" and rows.fmt(2023, "year") == "2023"


def test_a_gazette_notice_date_says_what_it_dates_and_a_publication_day_dates_a_row():
    v = cat.BY_NAME["gazette_company_notices"]
    r = {"key": "gazette/2018-aw3107/company/1", "kind": "winding-up application", "company": "X LIMITED", "action": "application to put into liquidation",
         "event_on": dt.date(2018, 7, 13), "event_basis": "hearing", "filed_on": dt.date(2018, 5, 25), "published_on": dt.date(2018, 7, 5)}
    d = rows.dates(v, r)
    assert d["text"] == "to be heard 13 July 2018; filed 25 May 2018; published 5 July 2018" and not d["undated"]
    r2 = {"key": "k", "kind": "removal", "company": "Y LIMITED", "action": "intention to remove", "event_on": dt.date(2020, 2, 1), "event_basis": "objections by",
          "filed_on": None, "published_on": dt.date(2020, 1, 10)}
    assert rows.dates(v, r2)["text"] == "objections by 1 February 2020; published 10 January 2020"
    r3 = dict(r2, event_on=None, event_basis=None)
    d3 = rows.dates(v, r3)
    assert d3["text"] == "published 10 January 2020" and not d3["undated"]
    lq = cat.BY_NAME["gazette_liquidations"]
    assert rows.dates(lq, {"key": "k", "appointed_on": dt.date(2021, 3, 4), "published_on": dt.date(2021, 3, 9)})["text"] == "appointed 4 March 2021; published 9 March 2021"


def test_an_expense_row_is_a_dated_figure_with_money_formatted():
    v = cat.BY_NAME["mp_expenses"]
    r = {"key": "h/sheet1/C10", "name": "Mark Mitchell", "category": "Grand Total", "role": "total", "figure": decimal.Decimal("8323.28"),
         "period_start": dt.date(2020, 7, 1), "period_end": dt.date(2020, 9, 30)}
    assert rows.statement(v, r) == "Mark Mitchell · Grand Total: $8,323.28, a member's expenses as released for the period"
    assert rows.dates(v, r)["text"] == "from 1 July 2020; to 30 September 2020"
