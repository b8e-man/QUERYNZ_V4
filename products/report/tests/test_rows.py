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
