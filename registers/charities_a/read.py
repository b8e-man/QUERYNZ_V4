"""The reading of the Charities Register's captured feed pages (plan step
4.1, the Fable build): charities, their officers, their annual returns and
their groups, typed, under the register's own identifiers, each row stamped
with the page it came from and the row's key in that page. Nothing here
calls a model, fetches, or touches a database: pages in, rows and catch-log
lines out. The pages are the capture lane's (`registers/charities`), landed
verbatim by hash: one JSON page of up to 1,000 rows of one entity set.

  charities         one per organisation, keyed by its charity number
                    (`charities/CC12345`): name, status, the registration
                    dates, legal structure, the main sector, activity and
                    beneficiary resolved through the code lists, the lists
                    the register publishes beside them (from the
                    vOrganisations page), the address for service and the
                    postal address as the register publishes them, the group
  charity_officers  one per officer row, keyed by the feed's OfficerId
                    (`charities/officer/<id>`): names as filed, role, status,
                    the window as the register states it, a disqualification
                    flag with its grounds. No address, no birth date, no
                    contact detail: the feed carries none and none is read
  charity_returns   one per annual return, keyed by AnnualReturnId
                    (`charities/return/<id>`): period, tier, currency, audit,
                    and the financial fields (ruling of 14 August 2026)
  charity_groups    one per group, keyed by GroupId (`charities/group/<id>`)
  codes             the code lists, as the feed publishes them

Items in equal items out plus items set aside: every row of every page is a
typed row or a catch-log line with its reason. A row met again in a later
page (a changes pass) replaces the earlier reading of the same key; the
loader counts those as `replaced`. A page that is not a page of the set it
is listed under raises: nothing is published from a page not trusted.

    read_page(entity_set, data, sha, codes, held=None, only=None) -> Result
    read_codes(entity_set, data) -> {id: name}, rows
"""
import datetime as dt
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field

from keys.numbers import charity_number as cc_of, nzbn as nzbn_of
from support import profiles
from registers.charities.capture import parse_page

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
PROFILE = "charities-odata-page"
READER = "registers.charities_a.read 1"
READ_FROM = "text"

#: the feed's key field per entity set the reading takes rows from
KEY_OF = {"Organisations": "OrganisationId", "vOrganisations": "OrganisationId", "Officers": "OfficerId",
          "AnnualReturn": "AnnualReturnId", "Groups": "GroupId"}
#: the code lists: entity set → (id field, name field); `Id` lists carry an EntityName the list applies to
CODE_LISTS = {"LegalStructure": ("LegalStructureId", "Name"), "ReportingTier": ("ReportingTierId", "Name"),
              "ReportingCurrency": ("ReportingCurrencyId", "Name"), "OfficerStatus": ("Id", "Name"),
              "RegistrationStatus": ("Id", "Name"), "AuditModifiedOpinionReceived": ("AuditModifiedOpinionReceivedId", "Name"),
              "MainActivity": ("Id", "Name"), "MainSector": ("Id", "Name"), "MainBeneficiary": ("Id", "Name"),
              "AreaOfOperations": ("AreaOfOperationId", "Name"), "Activities": ("ActivityId", "Name"),
              "Beneficiaries": ("BeneficiaryId", "Name"), "Sectors": ("SectorId", "Name"),
              "SourceOfFunds": ("SourceOfFundsId", "Name")}
#: the Officers flags that each state a ground of disqualification when true (the feed's own names; one is a
#: truncated twin of another and both are read). IsNotDisqualified false is a ground with no name.
DISQUALIFICATION_FLAGS = ("BannedDirector", "DisqualifiedByBoard", "OfficerUndischargedBankrupt", "SubjectToBanningOrder",
                          "OfficerProhibitedFromBeingDirector", "OfficerProhibitedFromBeingDirect", "OfficerBeenConvicted",
                          "OfficerDisqualifiedByRules", "OfficerDisqualifiedUnderSixteenYears", "OfficerSubjectToPropertyOrder",
                          "ConvictedOfAnOffenseRelatingToTerrorism")
DISQUALIFIED_STATUSES = ("Disqualified", "Not Qualified")
#: the annual return's financial fields that take a column of their own (the feed's names → the column); every
#: other numeric field the return carries, when not null and not zero, goes to `figures` as filed
NAMED_FIGURES = {
    "TotalGrossIncome": "total_gross_income", "TotalExpenditure": "total_expenditure",
    "NetSurplusDeficitForTheYear": "net_surplus_deficit", "SurplusDeficit": "surplus_deficit",
    "TotalAssets": "total_assets", "TotalLiabilities": "total_liabilities", "TotalEquity": "total_equity",
    "Totalassetslesstotalliabilities": "total_assets_less_liabilities", "TotalOverallLiabilities": "total_overall_liabilities",
    "AllCurrentAssets": "current_assets", "AllNonCurrentAssets": "non_current_assets",
    "AllCurrentLiabilities": "current_liabilities", "AllNonCurrentLiabilities": "non_current_liabilities",
    "CashAndBankBalances": "cash_and_bank", "Investments": "investments", "Inventory": "inventory",
    "Land": "land", "Buildings": "buildings", "LandAndBuildings": "land_and_buildings",
    "PropertyPlantAndEquipmment": "property_plant_equipment", "AllOtherFixedAssets": "other_fixed_assets",
    "ComputersAndOfficeEquipment": "computers_and_office_equipment", "Vehicles": "vehicles",
    "IntangibleAssets": "intangible_assets", "InvestmentProperty": "investment_property",
    "InvestmentsSharesBondsUnitsInManagedFunds": "investments_shares_bonds_funds",
    "LoansAndOtherBorrowings": "loans_and_borrowings",
    "AmountsBorrowedFromOtherOrganisationsPersons": "amounts_borrowed", "AmountsLoanedToOtherOrganisationsOrPersons": "amounts_loaned",
    "GeneralAccumulatedFunds": "general_accumulated_funds", "RestrictedPurposeFunds": "restricted_purpose_funds",
    "EndowmentFunds": "endowment_funds", "Reserves": "reserves", "AccumulatedSurplusOrDeficits": "accumulated_surplus",
    "DonationsKoha": "donations_koha", "Bequests": "bequests", "MembershipFees": "membership_fees",
    "GovtGrantsContracts": "government_grants_contracts", "GovernmentServiceDeliveryGrantsContracts": "government_service_delivery_grants",
    "NonGovernmentServiceDeliveryGrantsContracts": "non_government_service_delivery_grants",
    "ServiceDeliveryGrantsContracts": "service_delivery_grants", "GeneralGrantsReceived": "general_grants_received",
    "CapitalGrantsAndDonations": "capital_grants_and_donations", "AllOtherGrantsAndSponsorship": "other_grants_and_sponsorship",
    "GrantsRevenueFromLocalOrCentralGovernment": "grants_from_government", "GrantsRevenueFromOtherSources": "grants_from_other_sources",
    "ServiceTradingIncome": "service_trading_income", "RevenueFromCommercialActivities": "commercial_revenue",
    "OtherRevenueFromExchangeTransactions": "other_exchange_revenue", "OtherRevenueFromNonExchangeTransactions": "other_non_exchange_revenue",
    "InterestOfDividendsReceived": "interest_or_dividends", "OtherInvestmentIncome": "other_investment_income",
    "NewZealandDividends": "new_zealand_dividends", "AllOtherIncome": "all_other_income",
    "GrantsPaidWithinNZ": "grants_paid_within_nz", "GrantsPaidOutsideNZ": "grants_paid_outside_nz",
    "GrantsorDonationsPaid": "grants_or_donations_paid", "GrantsAndDonationsMade": "grants_and_donations_made",
    "SalariesAndWages": "salaries_and_wages", "EmployeeRemunerationAndOtherRelatedExpenses": "employee_remuneration",
    "VolunteerRelatedExpenses": "volunteer_expenses", "FundRaisingExpenses": "fundraising_expenses",
    "ExpensesRelatedToFundraising": "expenses_related_to_fundraising", "CostOfTradingOperations": "cost_of_trading",
    "ExpensesRelatedToCommercialActivities": "commercial_expenses", "CostOfServiceProvision": "cost_of_service_provision",
    "OtherExpensesRelatedToServiceDelivery": "other_service_delivery_expenses",
    "OtherRelatedToDeliveryOfEntityObjectives": "other_objective_delivery_expenses",
    "Depreciation": "depreciation", "InterestPaid": "interest_paid", "AllOtherExpenditure": "all_other_expenditure",
    "TotalOperatingExpenditure": "total_operating_expenditure",
    "TotalComprehensiveRevenueAndExpenseForThePeriod": "total_comprehensive_revenue_and_expense",
    "TotalResources": "total_resources", "TotalCommittments": "total_commitments",
    "TotalResourcesLessCommittments": "total_resources_less_commitments", "Guarantees": "guarantees",
    "NumberOfFulltimeEmployees": "fulltime_employees", "NumberOfParttimeEmployees": "parttime_employees",
    "AvgAllPaidHoursPerWeek": "paid_hours_per_week", "AvgNoVolunteersPerWeek": "volunteers_per_week",
    "AvgAllVolunteerHoursPerWeek": "volunteer_hours_per_week",
}
#: numeric fields of a return that are identifiers or codes, never figures
NOT_FIGURES = {"AnnualReturnId", "OrganisationId", "GroupId", "ReportingTierId", "Status", "PerformanceReportCovers",
               "EndOfYearDayOfMonth", "EndOfYearMonth"}
_ISO_DAY = re.compile(r"^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.\d+)?(Z|[+-]\d\d:?\d\d)?$")
_MS_DATE = re.compile(r"^/Date\((-?\d+)(?:[+-]\d{4})?\)/$")
#: a name field that reads as an address (lesson: a mis-cut list of people can publish a street as a name): a box
#: or bag, or a leading street number. The feed's name fields are structured, so a thoroughfare word alone never
#: flags: Street, Lane, Court, Way, Close and Grove are surnames, and a street without its number is not an address
_ADDRESS_BLOCK = ("po box", "p o box", "p.o. box", "private bag", "rural delivery")
_STREET_NUMBER = re.compile(r"^\d+[a-z]?[\s/,]")
#: a name field that holds a date: a filer's birth date typed where a name goes. The feed has no birth-date field;
#: this is the one way one reaches a page, and it is never published (hard limit: no birth date)
_DATE_IN_NAME = re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b|\b(19|20)\d\d-\d\d-\d\d\b")
#: digits in a name that are not a lone year: an organisation named in a person's fields keeps its "(2014)"
_DIGITS = re.compile(r"\d+")
_YEAR = re.compile(r"^(19|20)\d\d$")


@dataclass
class Result:
    rows: dict = field(default_factory=lambda: defaultdict(list))   # table → [row]
    set_aside: list = field(default_factory=list)                   # (item, stage, reason, count)
    counts: dict = field(default_factory=dict)
    entity_set: str = ""
    rows_in: int = 0
    stated: int = None                                              # the feed's own count on the page, when asked


def profile_version(slug: str = PROFILE) -> int:
    """The ledger's version; until the integrator appends it, the lane's proposed line."""
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


# ── field readings ──────────────────────────────────────────────────────────

def day_of(v):
    """The day of a feed date (`2013-06-17T00:00:00Z`, or the older
    `/Date(ms)/`), as ISO; None for none or for a value that is not a day."""
    if v in (None, ""):
        return None
    s = str(v).strip()
    m = _ISO_DAY.match(s)
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            return None
    m = _MS_DATE.match(s)
    if m:
        try:
            return dt.datetime.fromtimestamp(int(m.group(1)) / 1000, dt.timezone.utc).date().isoformat()
        except (ValueError, OverflowError, OSError):
            return None
    return None


def moment_of(v):
    """A feed timestamp as ISO with its zone (the feed states Z); None for none."""
    if v in (None, ""):
        return None
    s = str(v).strip()
    m = _ISO_DAY.match(s)
    if m:
        zone = m.group(7) or "Z"
        try:
            d = dt.datetime(*(int(m.group(i)) for i in range(1, 7)))
        except ValueError:
            return None
        return d.isoformat() + ("+00:00" if zone == "Z" else zone)
    m = _MS_DATE.match(s)
    if m:
        try:
            return dt.datetime.fromtimestamp(int(m.group(1)) / 1000, dt.timezone.utc).isoformat()
        except (ValueError, OverflowError, OSError):
            return None
    return None


def text_of(v):
    """A string field as filed, stripped; None for null, blank or whitespace."""
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def number_of(v):
    """A figure as filed (int or float, never a bool); None otherwise."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    return None


def entity_set_of(url: str) -> str:
    """The feed's entity set a page URL asks for."""
    path = url.split("?", 1)[0].rstrip("/")
    return path.rsplit("/", 1)[-1]


def entity_set_of_rows(rows: list) -> str:
    """The entity set the rows say they are (`__metadata.type`), or ''."""
    for r in rows:
        t = (r.get("__metadata") or {}).get("type") or ""
        if "." in t:
            return t.rsplit(".", 1)[-1]
    return ""


def address_of(r: dict, prefix: str):
    """An organisation's address as the register publishes it (street or
    postal): the lines, suburb, city, postcode and country, joined; None
    when every part is blank."""
    parts = [text_of(r.get(prefix + f)) for f in ("Line1", "Line2", "Suburb", "City", "Postcode", "Country")]
    if parts[3] is None:
        parts[3] = text_of(r.get(prefix + "TownCity"))   # the Groups set's name for the city
    parts = [p for p in parts if p]
    return ", ".join(parts) if parts else None


def name_holds_a_date(name: str) -> bool:
    """True when a name field holds a date (a birth date typed where a name goes)."""
    return bool(_DATE_IN_NAME.search(name or ""))


def name_reads_as_address(name: str) -> bool:
    """True when a name field is an address and must not be published as a
    name: a box or bag, or a leading street number."""
    s = (name or "").strip()
    if not s:
        return False
    low = s.lower()
    return any(low.startswith(b) or f" {b}" in low for b in _ADDRESS_BLOCK) or bool(_STREET_NUMBER.match(low))


def name_holds_digits(name: str) -> bool:
    """True when a name field holds digits that are not a lone year (an
    organisation's "(2014)" is a name; "Smith02" or "3/11/66" is not)."""
    runs = _DIGITS.findall(name or "")
    return any(not _YEAR.match(r) for r in runs)


def name_fault(name: str):
    """Why a name field cannot be published as filed, or None: a date, an address, digits."""
    if not name:
        return None
    if name_holds_a_date(name):
        return "holds a date"
    if name_reads_as_address(name):
        return "reads as an address"
    if name_holds_digits(name):
        return "holds digits"
    return None


def disqualification_of(r: dict):
    """(disqualified, grounds): the flags that are true, the status when it
    is a disqualified one, and `IsNotDisqualified` false; grounds as text."""
    grounds = [f for f in DISQUALIFICATION_FLAGS if r.get(f) is True]
    status = text_of(r.get("OfficerStatus"))
    if status in DISQUALIFIED_STATUSES:
        grounds.append(f"status {status}")
    if r.get("IsNotDisqualified") is False and not grounds:
        grounds.append("IsNotDisqualified false")
    return bool(grounds), ("; ".join(grounds) if grounds else None)


# ── the pages ───────────────────────────────────────────────────────────────

def page_rows(entity_set: str, data: bytes):
    """(stated, rows) of one page, which must be a page of the set it is listed under."""
    stated, rows = parse_page(data)
    said = entity_set_of_rows(rows)
    if rows and said and said != entity_set:
        raise ValueError(f"a page listed as {entity_set} holds rows of {said}")
    return stated, rows


def read_codes(entity_set: str, data: bytes) -> tuple:
    """A code list page: ({id: name}, rows for the codes table)."""
    id_field, name_field = CODE_LISTS[entity_set]
    _, rows = page_rows(entity_set, data)
    codes, out = {}, []
    for r in rows:
        i, name = r.get(id_field), text_of(r.get(name_field))
        if i is None or name is None:
            continue
        codes[int(i)] = name
        out.append((entity_set, int(i), name, text_of(r.get("EntityName")) or "", text_of(r.get("AttributeName"))))
    return codes, out


class Codes:
    """The code lists a reading resolves ids through; a missing list resolves nothing and is counted."""

    def __init__(self, lists: dict = None):
        self.lists = dict(lists or {})
        self.unresolved = defaultdict(int)

    def name(self, list_name: str, i, *also):
        """The name for an id in a list, or in the lists named after it; None, counted, when no list names it."""
        if i is None:
            return None
        for ln in (list_name,) + also:
            got = self.lists.get(ln, {}).get(int(i))
            if got is not None:
                return got
        self.unresolved[list_name] += 1
        return None


def _stamp(sha: str, key_field: str, key, loaded_at: str, version: int) -> dict:
    return {"document": sha, "page": 1, "place": f"{key_field}={key}", "reader": READER, "profile": PROFILE,
            "profile_version": version, "read_from": READ_FROM, "loaded_at": loaded_at}


def read_page(entity_set: str, data: bytes, sha: str, codes: Codes, held: dict = None, only=None,
              loaded_at: str = None, version: int = None, groups: dict = None) -> Result:
    """One page read. `held`: OrganisationId → charity key, for officers and
    returns (a row whose organisation is not held is set aside); `groups`:
    GroupId → group key; `only`: the charity numbers a sample keeps (rows of
    others are counted `filtered`, never set aside)."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    version = version or profile_version()
    res = Result(entity_set=entity_set)
    stated, rows = page_rows(entity_set, data)
    res.stated, res.rows_in = stated, len(rows)
    key_field = KEY_OF[entity_set]
    reader = {"Organisations": _organisation, "vOrganisations": _vorganisation, "Officers": _officer,
              "AnnualReturn": _return, "Groups": _group}[entity_set]
    c = defaultdict(int)
    for r in rows:
        key = r.get(key_field)
        item = f"{sha}/{key_field}={key}"
        if key is None:
            res.set_aside.append((item, entity_set, "no key field", 1))
            c["set_aside"] += 1
            continue
        try:
            table, row, why = reader(r, codes, held, groups)
        except (TypeError, ValueError) as exc:
            table, row, why = None, None, f"not readable: {type(exc).__name__}"
        if row is None:
            if only is not None and "the register's copy does not hold" in why:
                c["filtered"] += 1          # a sample holds a few charities; the others' rows are not faults
                continue
            res.set_aside.append((item, entity_set, why, 1))
            c["set_aside"] += 1
            continue
        if only is not None and row["filed"].get("charity_number") not in only and \
                not (entity_set == "AnnualReturn" and row["filed"].get("charity_key") is None):
            c["filtered"] += 1
            continue
        row.update(_stamp(sha, key_field, key, loaded_at, version))
        res.rows[table].append(row)
        c["typed"] += 1
    res.counts = dict(c)
    return res


def _organisation(r: dict, codes: Codes, held, groups):
    cc = cc_of(r.get("CharityRegistrationNumber"))
    if cc is None:
        return None, None, "no charity number"
    name = text_of(r.get("Name"))
    if name is None:
        return None, None, "no name"
    group_id = r.get("GroupId")
    filed = {
        "key": f"charities/{cc}", "charity_number": cc, "organisation_id": int(r["OrganisationId"]),
        "nzbn": nzbn_of(r.get("NZBNNumber")), "nzbn_filed": text_of(r.get("NZBNNumber")),
        "companies_office_number": text_of(r.get("CompaniesOfficeNumber")),
        "name": name, "other_names": text_of(r.get("OtherNames")),
        "status": text_of(r.get("RegistrationStatus")),
        "registered_on": day_of(r.get("DateRegistered")), "deregistered_on": day_of(r.get("DeregistrationDate")),
        "deregistration_note": text_of(r.get("DeregistrationReasons")),
        "legal_structure": text_of(r.get("LegalStructure")), "legal_structure_other": text_of(r.get("OtherLegalStructure")),
        "entity_structure": text_of(r.get("EntityStructure")),
        "main_activity_id": r.get("MainActivityId"), "main_activity": codes.name("MainActivity", r.get("MainActivityId")),
        "main_sector_id": r.get("MainSectorId"), "main_sector": codes.name("MainSector", r.get("MainSectorId")),
        "main_beneficiary_id": r.get("MainBeneficiaryId"), "main_beneficiary": codes.name("MainBeneficiary", r.get("MainBeneficiaryId")),
        "charitable_purpose": text_of(r.get("CharitablePurpose")),
        "address_for_service": address_of(r, "StreetAddress"), "postal_address": address_of(r, "PostalAddress"),
        "year_end_day": r.get("EndOfYearDayofMonth"), "year_end_month": r.get("EndOfYearMonth"),
        "annual_return_due_on": day_of(r.get("AnnualReturnDueDate")),
        "group_id": group_id, "group_key": f"charities/group/{group_id}" if group_id is not None else None,
        "group_type": r.get("GroupType"), "incorporated": r.get("IsIncorporated"),
        "percent_spent_overseas": r.get("PercentageSpentOverseas"),
        "modified_at": moment_of(r.get("ModifiedOn")),
    }
    return "charities", {"key": filed["key"], "filed": filed}, None


def _vorganisation(r: dict, codes: Codes, held, groups):
    """The register's lists beside an organisation: activities, sectors,
    beneficiaries, areas of operation, sources of funds, the group's name
    and the coded deregistration reason. Merged into the charity row by the
    loader; cites its own page through `lists_document`."""
    cc = cc_of(r.get("CharityRegistrationNumber"))
    if cc is None:
        return None, None, "no charity number"
    filed = {"key": f"charities/{cc}", "charity_number": cc, "organisation_id": int(r["OrganisationId"]),
             "activities": text_of(r.get("Activities")), "sectors": text_of(r.get("Sectors")),
             "beneficiaries": text_of(r.get("Beneficiaries")), "areas_of_operation": text_of(r.get("AreasOfOperation")),
             "sources_of_funds": text_of(r.get("SourcesOfFunds")), "group_name": text_of(r.get("GroupName")),
             "deregistration_reason": text_of(r.get("DeregistrationReasonNew"))}
    return "charity_lists", {"key": filed["key"], "filed": filed}, None


def _officer(r: dict, codes: Codes, held, groups):
    oid = r.get("OrganisationId")
    charity_key = (held or {}).get(oid)
    if charity_key is None:
        return None, None, "officer of an organisation the register's copy does not hold"
    body = bool(r.get("IsaBodyCorporate"))
    # a name field that holds a date, an address or stray digits is withheld, named by its fault in name_note, and
    # the row stays (recover over exclude): the role and its window are the register's record whatever was typed
    names, notes = {}, []
    for f, col in (("FirstName", "first_name"), ("MiddleName", "middle_names"), ("LastName", "last_name"),
                   ("FullName", "full_name"), ("BodyCorporateName", "body_corporate_name")):
        v = text_of(r.get(f))
        why = name_fault(v)
        if why:
            notes.append(f"{f} withheld: {why}")
            v = None
        names[col] = v
    if names["full_name"] is None:
        parts = [names[c] for c in ("first_name", "middle_names", "last_name") if names[c]]
        names["full_name"] = " ".join(parts) if parts else names["body_corporate_name"]
    if names["full_name"] is None:
        return None, None, "no publishable name" if notes else "no name"
    disq, grounds = disqualification_of(r)
    ended = day_of(r.get("LastDateAsAnOfficer"))
    filed = {
        "key": f"charities/officer/{int(r['OfficerId'])}", "officer_id": int(r["OfficerId"]),
        "charity_key": charity_key, "charity_number": charity_key.rsplit("/", 1)[-1], "organisation_id": int(oid),
        "contact_id": text_of(r.get("ContactId")),
        **names, "name_note": "; ".join(notes) if notes else None,
        "body_corporate": body,
        "role": text_of(r.get("PositioninOrganisation")), "status": text_of(r.get("OfficerStatus")),
        "started_on": day_of(r.get("PositionAppointmentDate")), "ended_on": ended, "ended_on_stated": ended is not None,
        "disqualified": disq, "disqualification": grounds,
        "appointed_officer": bool(r.get("IsAppointedOfficer")), "suppressed": False,
        "modified_at": moment_of(r.get("ModifiedOn")),
    }
    if filed["started_on"] is None and r.get("PositionAppointmentDate") not in (None, ""):
        return None, None, "appointment date is not a day"
    return "charity_officers", {"key": filed["key"], "filed": filed}, None


def _return(r: dict, codes: Codes, held, groups):
    oid, gid = r.get("OrganisationId"), r.get("GroupId")
    charity_key = (held or {}).get(oid) if oid is not None else None
    group_key = (groups or {}).get(gid) if gid is not None else None
    if oid is None and gid is None:
        return None, None, "a return of no organisation and no group"
    if oid is not None and charity_key is None and group_key is None:
        return None, None, "return of an organisation the register's copy does not hold"
    if oid is None and group_key is None:
        return None, None, "return of a group the register's copy does not hold"
    ended = day_of(r.get("YearEnded"))
    if ended is None:
        return None, None, "no period end"
    tier_id = r.get("ReportingTierId")
    opinion = text_of(r.get("AuditAndReviewWhatTypeOfModifiedOpinionWasReceived"))
    if opinion is not None and opinion not in codes.lists.get("AuditModifiedOpinionReceived", {}).values():
        codes.unresolved["AuditModifiedOpinionReceived"] += 1
    filed = {
        "key": f"charities/return/{int(r['AnnualReturnId'])}", "annual_return_id": int(r["AnnualReturnId"]),
        "charity_key": charity_key, "charity_number": charity_key.rsplit("/", 1)[-1] if charity_key else None,
        "organisation_id": int(oid) if oid is not None else None,
        "group_key": group_key, "group_id": int(gid) if gid is not None else None,
        "period_ended_on": ended, "as_at_on": day_of(r.get("AsAtDate")), "covers_months": r.get("PerformanceReportCovers"),
        "status_code": r.get("Status"),
        "tier_id": tier_id, "tier": codes.name("ReportingTier", tier_id) if tier_id is not None else None,
        "currency": text_of(r.get("ReportingCurrency")),
        "audited": r.get("IsFinancialReportAudited"), "audit_opinion_modified": r.get("IsModifiedAuditOpinionReceived"),
        "audit_opinion": opinion, "accounting_method_flag": r.get("AccountingMethod"),
        "withheld": bool(r.get("WithHoldAnnualReturn")), "first_time_reporting": r.get("FirstTimeReporting"),
        "gst_inclusive": r.get("IsGSTInclusive"), "modified_at": moment_of(r.get("ModifiedOn")),
    }
    figures = {}
    for f, v in r.items():
        n = number_of(v)
        if n is None or f in NOT_FIGURES:
            continue
        col = NAMED_FIGURES.get(f)
        if col:
            filed[col] = n
        elif n != 0:
            figures[f] = n
    for col in NAMED_FIGURES.values():
        filed.setdefault(col, None)
    filed["figures"] = json.dumps(figures, sort_keys=True) if figures else None
    return "charity_returns", {"key": filed["key"], "filed": filed}, None


def _group(r: dict, codes: Codes, held, groups):
    name = text_of(r.get("name")) or text_of(r.get("Name"))
    if name is None:
        return None, None, "no name"
    gid = int(r["GroupId"])
    filed = {"key": f"charities/group/{gid}", "group_id": gid,
             "registration_number": cc_of(r.get("RegistrationNumber")), "name": name,
             "other_names": text_of(r.get("OtherNamesTheSingleEntityIsKnown")),
             "group_type": r.get("GroupType"), "status": text_of(r.get("RegistrationStatus")),
             "registered_on": day_of(r.get("DateRegistered")), "deregistered_on": day_of(r.get("DeregistrationDate")),
             "deregistration_note": text_of(r.get("DeregistrationReasons")),
             # a group's main codes index the keyed Activities, Sectors and Beneficiaries sets (ids in the thousands),
             # where an organisation's index the Main* lists; both are tried, the keyed set first
             "main_activity": codes.name("Activities", r.get("MainActivityId"), "MainActivity"),
             "main_sector": codes.name("Sectors", r.get("MainSectorId"), "MainSector"),
             "main_beneficiary": codes.name("Beneficiaries", r.get("MainBeneficiaryId"), "MainBeneficiary"),
             "address_for_service": address_of(r, "StreetAddress"), "postal_address": address_of(r, "PostalAddress"),
             "modified_at": moment_of(r.get("ModifiedOn"))}
    return "charity_groups", {"key": filed["key"], "filed": filed}, None
