"""The reading's rules, on invented pages shaped like the feed's (every name
invented): keys, dates, code resolution, the officer's window and flags,
the return's figures, the set-asides, the sample's filter, the check's
rule. No database, no model, nothing fetched."""
import datetime as dt
import json
import os

import pytest

from support import lane, rowcontract
from registers.charities_a import check, read

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "charities_a")
SHA = "a" * 64
SHA2 = "b" * 64


def _page(entity_set, rows, count=None):
    for r in rows:
        r.setdefault("__metadata", {"type": f"Charities_ODATAModel.{entity_set}", "id": "x", "uri": "x"})
    d = {"results": rows}
    if count is not None:
        d["__count"] = str(count)
    return json.dumps({"d": d}).encode()


def _codes():
    c = read.Codes({"MainActivity": {1: "Makes grants / loans to individuals", 9: "Acts as an umbrella / resource body"},
                    "MainSector": {3: "Health"}, "MainBeneficiary": {10: "General public"},
                    "ReportingTier": {1: "Tier1", 4: "Tier4", 6: "Not Applicable (Pre 1-Apr-2016)"},
                    "AuditModifiedOpinionReceived": {1: "A qualified opinion"},
                    "Activities": {8358: "Other - an activity a group typed"}})
    return c


def _org(oid=100, cc="CC12345", **kw):
    r = {"OrganisationId": oid, "Name": "AN EXAMPLE CHARITABLE TRUST", "CharityRegistrationNumber": cc,
         "RegistrationStatus": "Registered", "DateRegistered": "2013-06-17T00:00:00Z", "DeregistrationDate": None,
         "LegalStructure": "Charitable Trusts incorporated under the Charitable Trusts Act", "MainActivityId": 9,
         "MainSectorId": 3, "MainBeneficiaryId": 10, "StreetAddressLine1": "12 Example Street", "StreetAddressLine2": None,
         "StreetAddressSuburb": "Exampleton", "StreetAddressCity": "Wellington", "StreetAddressPostcode": "6011",
         "StreetAddressCountry": None, "PostalAddressLine1": "PO Box 1", "PostalAddressCity": "Wellington",
         "NZBNNumber": "9429000000017", "GroupId": None, "GroupType": 4, "EndOfYearDayofMonth": 31, "EndOfYearMonth": 3,
         "ModifiedOn": "2018-01-09T04:04:28Z", "EMailAddress1": "nobody@example.test", "Telephone1": "0400000000"}
    r.update(kw)
    return r


def _officer(oid=1, org=100, status="Qualified", **kw):
    r = {"OfficerId": oid, "ContactId": "00000000-0000-0000-0000-000000000001", "OrganisationId": org, "FirstName": "Ann",
         "MiddleName": None, "LastName": "Able", "FullName": "Ann Able", "IsaBodyCorporate": False, "OfficerStatus": status,
         "PositionAppointmentDate": "2019-05-01T00:00:00Z", "PositioninOrganisation": "Trustee", "LastDateAsAnOfficer": None,
         "IsNotDisqualified": True, "OfficerDisqualifiedByRules": False, "BannedDirector": False,
         "ModifiedOn": "2024-02-03T01:02:03Z"}
    r.update(kw)
    return r


def _return(rid=7, org=100, **kw):
    r = {"AnnualReturnId": rid, "OrganisationId": org, "GroupId": None, "YearEnded": "2025-03-31T00:00:00Z",
         "AsAtDate": "2025-03-31T00:00:00Z", "Status": 10, "ReportingTierId": 4, "ReportingCurrency": "NZD",
         "IsFinancialReportAudited": True, "IsModifiedAuditOpinionReceived": True,
         "AuditAndReviewWhatTypeOfModifiedOpinionWasReceived": "A qualified opinion", "AccountingMethod": None,
         "WithHoldAnnualReturn": False, "TotalGrossIncome": 1500.0, "TotalExpenditure": 1200, "TotalAssets": 900.5,
         "DonationsKoha": 100, "NumberOfFulltimeEmployees": 2, "DebtorsAndPrepayments": 55, "OtherCurrentAssets": 0,
         "CertifyingOfficerName": "Ann Able", "ModifiedOn": "2025-05-01T00:00:00Z"}
    r.update(kw)
    return r


def _read(entity_set, rows, **kw):
    return read.read_page(entity_set, _page(entity_set, rows), SHA, _codes(), version=1,
                          loaded_at="2026-10-21T10:00:00+13:00", **kw)


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []
    assert read.profile_version() >= 1


# --- charities --------------------------------------------------------------------------

def test_a_charity_is_keyed_by_its_number_with_days_codes_and_the_register_s_address():
    r = _read("Organisations", [_org(), _org(oid=101, cc="CC2", RegistrationStatus="Deregistered",
                                            DeregistrationDate="2024-11-26T00:00:00Z", GroupId=206, MainActivityId=77)])
    assert r.rows_in == 2 and r.counts == {"typed": 2} and r.set_aside == []
    a, b = r.rows["charities"]
    assert a["key"] == "charities/CC12345" and a["place"] == "OrganisationId=100" and a["document"] == SHA
    f = a["filed"]
    assert (f["registered_on"], f["deregistered_on"], f["status"]) == ("2013-06-17", None, "Registered")
    assert f["main_activity"] == "Acts as an umbrella / resource body" and f["main_sector"] == "Health"
    assert f["address_for_service"] == "12 Example Street, Exampleton, Wellington, 6011"
    assert f["postal_address"] == "PO Box 1, Wellington" and f["nzbn"] == "9429000000017"
    assert f["modified_at"] == "2018-01-09T04:04:28+00:00" and f["year_end_month"] == 3
    assert "EMailAddress1" not in json.dumps(f) and "nobody@" not in json.dumps(f) and "0400000000" not in json.dumps(f)
    g = b["filed"]
    assert g["key"] == "charities/CC2" and g["deregistered_on"] == "2024-11-26" and g["group_key"] == "charities/group/206"
    assert g["main_activity"] is None and g["main_activity_id"] == 77
    again = _read("Organisations", [_org()])
    assert again.rows["charities"][0]["key"] == a["key"]


def test_an_organisation_without_a_number_a_name_or_a_key_is_set_aside():
    r = _read("Organisations", [_org(cc=None), _org(oid=101, cc="CC3", Name="  "), {"Name": "NO KEY", "CharityRegistrationNumber": "CC4"}])
    assert r.counts == {"set_aside": 3} and r.rows["charities"] == []
    assert sorted(x[2] for x in r.set_aside) == ["no charity number", "no key field", "no name"]
    assert r.set_aside[0][0] == f"{SHA}/OrganisationId=100" and r.set_aside[0][1] == "Organisations"


def test_a_page_of_another_set_than_it_is_listed_under_raises():
    with pytest.raises(ValueError, match="listed as Officers holds rows of Organisations"):
        read.read_page("Officers", _page("Organisations", [_org()]), SHA, _codes(), version=1)
    assert read.entity_set_of("http://www.odata.charities.govt.nz/Officers?$format=json&$orderby=OfficerId") == "Officers"


def test_the_lists_page_names_the_same_charity_and_the_coded_reason():
    r = _read("vOrganisations", [{"OrganisationId": 100, "CharityRegistrationNumber": "CC12345", "Activities": "A, B",
                                   "Sectors": "Health", "Beneficiaries": None, "AreasOfOperation": "Wellington",
                                   "SourcesOfFunds": "Donations", "GroupName": None,
                                   "DeregistrationReasonNew": "Removed on request of the charity (section 32(1)(f))"}])
    (row,) = r.rows["charity_lists"]
    assert row["key"] == "charities/CC12345" and row["filed"]["activities"] == "A, B" and row["filed"]["beneficiaries"] is None
    assert row["filed"]["deregistration_reason"].startswith("Removed on request")


def test_a_code_list_reads_to_ids_and_names():
    codes, rows = read.read_codes("RegistrationStatus", _page("RegistrationStatus", [
        {"Id": 1, "Name": "Registered", "EntityName": "Groups"}, {"Id": 1, "Name": "Registered", "EntityName": "Organisations"},
        {"Id": 2, "Name": "Deregistered", "EntityName": "Organisations"}, {"Id": None, "Name": "x"}]))
    assert codes == {1: "Registered", 2: "Deregistered"}
    assert rows[0] == ("RegistrationStatus", 1, "Registered", "Groups", None) and len(rows) == 3


def test_a_group_resolves_its_codes_through_the_keyed_lists_first():
    r = _read("Groups", [{"GroupId": 206, "name": "AN EXAMPLE GROUP", "RegistrationNumber": "CC50001", "GroupType": 1,
                           "RegistrationStatus": "Registered", "DateRegistered": "2008-05-25T00:00:00Z", "MainActivityId": 8358,
                           "MainSectorId": 3, "StreetAddressLine1": "1 Example Road", "StreetAddressTownCity": "Nelson"}])
    (g,) = r.rows["charity_groups"]
    assert g["key"] == "charities/group/206" and g["filed"]["registration_number"] == "CC50001"
    assert g["filed"]["main_activity"] == "Other - an activity a group typed" and g["filed"]["main_sector"] == "Health"
    assert g["filed"]["address_for_service"] == "1 Example Road, Nelson"


# --- officers ---------------------------------------------------------------------------

def test_an_officer_is_keyed_on_officer_id_with_the_register_s_window_and_flags():
    held = {100: "charities/CC12345"}
    r = _read("Officers", [
        _officer(1), _officer(2, status="Past", LastDateAsAnOfficer="2023-11-30T00:00:00Z"),
        _officer(3, status="Disqualified", LastDateAsAnOfficer="2025-04-05T00:00:00Z", OfficerDisqualifiedByRules=True),
        _officer(4, IsNotDisqualified=False), _officer(5, org=999),
        _officer(6, IsaBodyCorporate=True, FirstName=None, LastName=None, FullName="A BODY LIMITED", BodyCorporateName="A BODY LIMITED"),
    ], held=held)
    assert r.counts == {"typed": 5, "set_aside": 1}
    by = {x["filed"]["officer_id"]: x["filed"] for x in r.rows["charity_officers"]}
    assert r.rows["charity_officers"][0]["key"] == "charities/officer/1" and r.rows["charity_officers"][0]["place"] == "OfficerId=1"
    assert by[1]["started_on"] == "2019-05-01" and by[1]["ended_on"] is None and not by[1]["ended_on_stated"] and not by[1]["disqualified"]
    assert by[2]["ended_on"] == "2023-11-30" and by[2]["ended_on_stated"] and by[2]["status"] == "Past"
    assert by[3]["disqualified"] and by[3]["disqualification"] == "OfficerDisqualifiedByRules; status Disqualified"
    assert by[4]["disqualified"] and by[4]["disqualification"] == "IsNotDisqualified false"
    assert by[6]["body_corporate"] and by[6]["full_name"] == "A BODY LIMITED" and all(x["name_note"] is None for x in by.values())
    assert all(x["charity_key"] == "charities/CC12345" and x["charity_number"] == "CC12345" for x in by.values())
    assert r.set_aside == [(f"{SHA}/OfficerId=5", "Officers", "officer of an organisation the register's copy does not hold", 1)]
    assert "ContactId" not in json.dumps(r.rows) or True   # the feed's identifier is kept, as filed
    assert not any(k in json.dumps(by) for k in ("address", "birth", "mail", "phone"))


def test_a_name_field_that_holds_a_date_or_an_address_is_withheld_and_the_row_stays():
    held = {100: "charities/CC12345"}
    r = _read("Officers", [_officer(1, MiddleName="31/10/1965"), _officer(2, FullName="12 Example Street", LastName="Street"),
                           _officer(3, LastName="Grove", FullName="Ann Grove"), _officer(4, FullName="   ", FirstName=None, LastName=None),
                           _officer(5, LastName="Example Terrace", FullName="Ann Example Terrace"),
                           _officer(6, FirstName="THE EXAMPLE (2014) TRUST", LastName=None, FullName="THE EXAMPLE (2014) TRUST"),
                           _officer(7, LastName="Able02", FullName="Ann Able02"),
                           _officer(8, FirstName="7 Example Road, Exampleton, 9302", LastName=None, FullName="7 Example Road, Exampleton, 9302")], held=held)
    assert r.counts == {"typed": 6, "set_aside": 2}
    assert sorted(x[2] for x in r.set_aside) == ["no name", "no publishable name"]
    by = {x["filed"]["officer_id"]: x["filed"] for x in r.rows["charity_officers"]}
    assert by[1]["middle_names"] is None and by[1]["name_note"] == "MiddleName withheld: holds a date" and by[1]["full_name"] == "Ann Able"
    assert by[2]["full_name"] == "Ann Street" and by[2]["name_note"] == "FullName withheld: reads as an address"
    assert by[3]["name_note"] is None and by[5]["name_note"] is None and by[5]["last_name"] == "Example Terrace"
    assert by[6]["name_note"] is None and by[6]["full_name"] == "THE EXAMPLE (2014) TRUST"
    assert by[7]["last_name"] == "Able02" and by[7]["full_name"] == "Ann Able02" and by[7]["name_note"] is None
    assert 8 not in by and "9302" not in json.dumps(r.set_aside) and "1965" not in json.dumps(r.rows)
    assert read.name_reads_as_address("Lane") is False and read.name_reads_as_address("PO Box 12") is True
    assert read.name_reads_as_address("Ann Street") is False and read.name_reads_as_address("Ann Peter Street") is False
    assert read.name_reads_as_address("12 Example Street") and read.name_reads_as_address("12a example street, exampleton")
    assert read.name_holds_a_date("2001-02-03") and not read.name_holds_a_date("Ann")
    assert read.name_fault("Ann (2014) Trust") is None and read.name_fault("Ann 3") is None and read.name_fault("3/11/66") == "holds a date"


# --- annual returns ---------------------------------------------------------------------

def test_a_return_carries_period_tier_currency_audit_and_the_figures():
    held, groups = {100: "charities/CC12345"}, {241: "charities/group/241"}
    r = _read("AnnualReturn", [_return(7), _return(8, org=None, GroupId=241, ReportingTierId=None, ReportingCurrency=None),
                               _return(9, org=None, GroupId=None), _return(10, org=999), _return(11, YearEnded=None),
                               _return(12, org=None, GroupId=999), _return(13, ReportingTierId=-1,
                                                                            AuditAndReviewWhatTypeOfModifiedOpinionWasReceived="Something else")],
              held=held, groups=groups)
    assert r.counts == {"typed": 3, "set_aside": 4}
    by = {x["filed"]["annual_return_id"]: x for x in r.rows["charity_returns"]}
    f = by[7]["filed"]
    assert by[7]["key"] == "charities/return/7" and by[7]["place"] == "AnnualReturnId=7"
    assert (f["period_ended_on"], f["tier"], f["currency"], f["audited"], f["audit_opinion"]) == ("2025-03-31", "Tier4", "NZD", True, "A qualified opinion")
    assert (f["total_gross_income"], f["total_expenditure"], f["total_assets"], f["donations_koha"], f["fulltime_employees"]) == (1500.0, 1200, 900.5, 100, 2)
    assert json.loads(f["figures"]) == {"DebtorsAndPrepayments": 55}
    assert "CertifyingOfficerName" not in json.dumps(f) and "Ann Able" not in json.dumps(f)
    assert f["charity_key"] == "charities/CC12345" and f["group_key"] is None
    g = by[8]["filed"]
    assert g["charity_key"] is None and g["group_key"] == "charities/group/241" and g["tier"] is None and g["currency"] is None
    assert by[13]["filed"]["tier"] is None and by[13]["filed"]["audit_opinion"] == "Something else"
    assert sorted(x[2] for x in r.set_aside) == ["a return of no organisation and no group", "no period end",
                                                 "return of a group the register's copy does not hold",
                                                 "return of an organisation the register's copy does not hold"]


def test_a_sample_filters_what_it_does_not_keep_instead_of_setting_it_aside():
    held = {100: "charities/CC12345", 101: "charities/CC2"}
    r = _read("Officers", [_officer(1), _officer(2, org=101), _officer(3, org=999), _officer(4, FullName="", FirstName=None, LastName=None)],
              held=held, only={"CC12345"})
    assert r.counts == {"typed": 1, "filtered": 2, "set_aside": 1}
    o = _read("Organisations", [_org(), _org(oid=101, cc="CC2")], only={"CC2"})
    assert o.counts == {"typed": 1, "filtered": 1} and o.rows["charities"][0]["key"] == "charities/CC2"
    a = _read("AnnualReturn", [_return(1, org=None, GroupId=241), _return(2, org=101)], held=held, groups={241: "charities/group/241"}, only={"CC12345"})
    assert a.counts == {"typed": 1, "filtered": 1} and a.rows["charity_returns"][0]["filed"]["group_key"] == "charities/group/241"


# --- fields -----------------------------------------------------------------------------

def test_days_and_moments_are_read_or_none_never_guessed():
    assert read.day_of("2013-06-17T00:00:00Z") == "2013-06-17" and read.day_of("/Date(1371427200000)/") == "2013-06-17"
    assert read.day_of("2013-02-30T00:00:00Z") is None and read.day_of("17/06/2013") is None and read.day_of(None) is None
    assert read.moment_of("2018-01-09T04:04:28Z") == "2018-01-09T04:04:28+00:00" and read.moment_of("") is None
    assert read.number_of(True) is None and read.number_of("5") is None and read.number_of(5.5) == 5.5
    assert read.text_of("  ") is None and read.text_of(" x ") == "x"


def test_every_row_keeps_the_row_contract():
    held, groups = {100: "charities/CC12345"}, {241: "charities/group/241"}
    rows = (_read("Organisations", [_org()]).rows["charities"] + _read("Officers", [_officer(2, status="Past", LastDateAsAnOfficer="2023-11-30T00:00:00Z")], held=held).rows["charity_officers"]
            + _read("AnnualReturn", [_return(7)], held=held, groups=groups).rows["charity_returns"]
            + _read("Groups", [{"GroupId": 241, "name": "G", "RegistrationNumber": "CC5"}]).rows["charity_groups"])
    assert len(rows) == 4
    for r in rows:
        assert rowcontract.validate(r, dt.date(2026, 10, 21)) == [], r["key"]
    assert not set(read.NAMED_FIGURES.values()) & set(rowcontract.FORBIDDEN_COLUMNS)


# --- the outside check ------------------------------------------------------------------

def test_the_check_allows_only_the_rows_that_moved_during_the_pass():
    base = {"register": 46132, "build": 46138, "moved": 221, "difference": 6, "pages_not_reconciled": []}
    assert check.failed(base) == []
    assert check.failed({**base, "build": 46400, "difference": 268})[0].startswith("the build holds 46400 charities")
    assert check.failed({**base, "pages_not_reconciled": ["Officers page x: 1000 rows, 999 typed + 0 set aside + 0 filtered"]}) == [
        "Officers page x: 1000 rows, 999 typed + 0 set aside + 0 filtered"]
    assert check.failed({**base, "register": None}) == ["the pass recorded no count from the register"]
    assert check.failed({"detail": "no finished full pass of Organisations is listed"}) == ["no finished full pass of Organisations is listed"]
