"""The reading of the Charities Register's captured feed pages (plan step 4.1,
the Opus build). Every page is the feed's own JSON, landed verbatim by the
capture lane (`registers/charities`); this reads it and fetches nothing.

What a page becomes, one typed row per feed row or one catch-log line:

  charities   one per organisation, keyed by the register's own number
              (`charities/CC12345`, a suffix like `CC12345-1` kept as filed);
              name, status, registration dates, legal structure, the main
              sector, activity and beneficiary resolved through the code
              lists, the address for service as the register publishes it
              (its street address; the charity's, like a company's registered
              office), and its group
  officers    one per officer row, keyed by the source's `OfficerId`; role,
              window, status and one disqualification flag (the register's
              own status). No address, birth date, email or phone: the feed's
              Officers carry no address or birth date, and nothing else is read
  returns     one per annual return, keyed by `AnnualReturnId`; the period,
              tier, currency, audit opinion and every financial field (ruling
              of 14 August 2026: financial fields in scope, nothing else)
  groups      one per group registration, keyed by its number

A row's citation is the page's sha256, page 1 (a feed page is one document of
one page) and the row's key in it (`OrganisationId=123`). A set's pages are
read newest first, so when a later page (a changes pass) holds a row again,
the later reading is kept and the earlier is a catch-log line; the result is
the same whichever order the pages were landed in.

Never printed: a row's fields. Every line this module prints is a count.

    python -m registers.charities_b.read <sha256>    # one page alone, counted
"""
import collections
import datetime as dt
import decimal
import json
import re
import sys
from zoneinfo import ZoneInfo

from keys.addresses import clean_address
from keys.numbers import nzbn as nzbn_ok

SOURCE = "charities"
READER = "registers.charities_b.read"
PROFILE, PROFILE_VERSION = "charities-odata-page", 1
NZ = ZoneInfo("Pacific/Auckland")

#: the feed's keyed sets this reading types, with each set's own key field
SETS = {"Groups": "GroupId", "Organisations": "OrganisationId", "Officers": "OfficerId",
        "AnnualReturn": "AnnualReturnId"}
#: the code lists it resolves through, and the field that names each entry
CODE_LISTS = ("RegistrationStatus", "LegalStructure", "MainActivity", "MainSector", "MainBeneficiary",
              "OfficerStatus", "ReportingTier", "ReportingCurrency", "AuditModifiedOpinionReceived")
_CODE_ID = {"LegalStructure": "LegalStructureId", "ReportingTier": "ReportingTierId",
            "ReportingCurrency": "ReportingCurrencyId", "AuditModifiedOpinionReceived": "AuditModifiedOpinionReceivedId"}
DISQUALIFIED = ("Disqualified", "Removed as Disqualified")
#: The main sector, activity and beneficiary ids as an organisation row carries them, and the name each
#: stands for. The feed's code lists hold the same names under other ids (its MainSector list calls 7
#: "Emergency / disaster relief"; the 9,521 charities filed under 7 are education, as the register's own
#: vOrganisations view names them for every one of 46,138 rows, 21 October 2026). So an id is resolved
#: here, and the name must still be an entry of the code list; check.py compares every charity with the
#: view, so a renumbering by the register turns it red.
VIEW_IDS = {
    "MainSector": {1: "Accommodation / housing", 2: "Arts / culture / heritage", 3: "Care / protection of animals",
                   4: "Community development", 5: "People with disabilities", 6: "Economic development",
                   7: "Education / training / research", 8: "Emergency / disaster relief", 9: "Employment",
                   10: "Environment / conservation", 11: "Fund-raising", 12: "Health", 13: "International activities",
                   14: "Promotion of volunteering", 15: "Religious activities", 16: "Social services",
                   17: "Sport / recreation", 18: "Marae on reservation land"},
    "MainActivity": {1: "Acts as an umbrella / resource body", 2: "Makes grants / loans to individuals",
                     3: "Makes grants to organisations (including schools or other charities)",
                     4: "Provides advice / information / advocacy", 5: "Provides buildings / facilities / open space",
                     6: "Provides human resources (e.g. staff / volunteers)",
                     7: "Provides other finance (e.g. investment funds)", 8: "Provides religious services / activities",
                     9: "Provides services (e.g. care / counselling)", 10: "Sponsors / undertakes research"},
    "MainBeneficiary": {1: "Animals", 2: "Children / young people", 3: "Family / whanau", 4: "General public",
                        5: "Migrants / refugees", 6: "Older people", 7: "Other charities",
                        8: "People of a certain ethnic / racial origin", 9: "People with disabilities",
                        10: "Religious groups", 11: "Voluntary bodies other than charities"},
}

#: numeric fields of a return that are not money: identifiers, codes, counts of people and hours, and the
#: service-performance quantities. Every other number on a return is a financial field.
NOT_MONEY = {"AnnualReturnId", "GroupId", "OrganisationId", "ReportingTierId", "Status", "PerformanceReportCovers",
             "AvgAllPaidHoursPerWeek", "AvgAllVolunteerHoursPerWeek", "AvgNoVolunteersPerWeek",
             "NumberOfFulltimeEmployees", "NumberOfParttimeEmployees"} | \
            {f"StatementOfServicePerformanceQuantity{i}" for i in range(1, 6)} | \
            {f"Quantity{i}_LastYear" for i in range(1, 6)} | {f"MaterialExpense{i}" for i in range(1, 5)}
#: the headline figures, as typed columns; every financial field is also in `figures`
HEADLINE = {"total_gross_income": "TotalGrossIncome", "total_expenditure": "TotalExpenditure",
            "net_surplus": "NetSurplusDeficitForTheYear", "total_assets": "TotalAssets",
            "total_liabilities": "TotalLiabilities", "total_equity": "TotalEquity"}
STREET = ("StreetAddressLine1", "StreetAddressLine2", "StreetAddressSuburb", "StreetAddressCity", "StreetAddressPostcode")
_WS = re.compile(r"\s+")
_MS_DATE = re.compile(r"^/Date\((-?\d+)(?:[+-]\d{4})?\)/$")


# ── pieces ────────────────────────────────────────────────────────────────────

def parse_page(body: bytes):
    """(stated count or None, rows) from one page of the feed's JSON: rows
    come as {"d": [...]} or {"d": {"results": [...], "__count": "N"}}."""
    d = json.loads(body)["d"]
    if isinstance(d, list):
        return None, d
    rows = d.get("results")
    if not isinstance(rows, list):
        raise ValueError("no results list")
    c = d.get("__count")
    return (int(c) if c is not None else None), rows


def set_of(row: dict) -> str:
    """The feed's set a row belongs to, from its own metadata
    (`Charities_ODATAModel.Officers` → Officers)."""
    return ((row.get("__metadata") or {}).get("type") or "").rsplit(".", 1)[-1]


def text(v):
    """A filed text with its whitespace squashed; None for nothing."""
    if v is None:
        return None
    s = _WS.sub(" ", str(v)).strip()
    return s or None


def feed_moment(v):
    """The feed's datetime as an aware moment, or None. It writes
    `2026-09-02T00:00:00Z` (or `/Date(ms)/` in its older form)."""
    if not v:
        return None
    m = _MS_DATE.match(str(v))
    if m:
        return dt.datetime.fromtimestamp(int(m.group(1)) / 1000, dt.timezone.utc)
    t = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def feed_date(v):
    """The day a feed date names, ISO, or None. The register stores a day as
    midnight UTC (`…T00:00:00Z`): that day as written. Any other time is a
    moment, read as its day in New Zealand (the register's clock)."""
    t = feed_moment(v)
    if t is None:
        return None
    t = t.astimezone(dt.timezone.utc)
    if (t.hour, t.minute, t.second) == (0, 0, 0):
        return t.date().isoformat()
    return t.astimezone(NZ).date().isoformat()


def number(v):
    """A filed number as an int or a Decimal; None for nothing; raises on a
    text that is not a number."""
    if v is None or v == "" or isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    d = decimal.Decimal(str(v).strip().replace(",", ""))
    if not d.is_finite():
        raise ValueError("not a finite number")
    return int(d) if d == d.to_integral_value() else d


def charity_number(raw):
    """The register's own number as filed, upper case, spaces out, or None.
    Kept whole: `CC12345-1` is another charity from `CC12345`, so it is not
    folded through keys.numbers.charity_number, which drops the suffix."""
    s = re.sub(r"\s+", "", str(raw or "")).upper()
    return s if re.fullmatch(r"CC\d+(-\d+)?", s) else None


def charity_key(number_):
    return f"charities/{number_}"


def officer_key(officer_id) -> str:
    return f"charities/officers/{int(officer_id)}"


def return_key(return_id) -> str:
    return f"charities/returns/{int(return_id)}"


def cite(sha: str, entity_set: str, row_id) -> dict:
    return {"document": sha, "page": 1, "place": f"{SETS[entity_set]}={int(row_id)}", "read_from": "text",
            "reader": READER, "profile": PROFILE, "profile_version": PROFILE_VERSION}


def stage_of(why: str) -> str:
    """The catch log's stage for a reason a reader gave: `key` (no usable
    number), `link` (what the row belongs to is not held, or set aside),
    `read` (the row itself)."""
    if "number" in why and not why.startswith("its "):
        return "key"
    if why.startswith("its ") or why.startswith("names no"):
        return "link"
    return "read"


def aside(entity_set: str, sha: str, row_id, stage: str, reason: str) -> dict:
    return {"entity_set": entity_set, "document": sha, "place": f"{SETS.get(entity_set, 'row')}={row_id}",
            "stage": stage, "reason": reason}


def address_for_service(row: dict):
    """(the address as the register publishes it, or None; parts dropped).
    The street address's parts, in order, joined; a part holding an email
    address is no part of an address and is dropped (counted, never shown)."""
    parts, dropped = [], 0
    for f in STREET:
        p = text(row.get(f))
        if not p:
            continue
        if "@" in p:
            dropped += 1
            continue
        parts.append(p)
    if not parts:
        return None, dropped
    a, _ = clean_address(", ".join(parts))
    return a, dropped


class Codes:
    """The code lists, from their pages: `name(list, id)` and `known(list, name)`.
    A list that names its entries per entity (`EntityName`) is read for the
    organisation's entries where it has them."""

    def __init__(self):
        self.by_id = collections.defaultdict(dict)
        self.names = collections.defaultdict(set)
        self.entries = []       # (code list, entity, code, name, document): the rows of the codes table

    def add_page(self, entity_set: str, rows: list, sha: str = "") -> int:
        """Read one page of a code list; returns the entries read (a row
        with no name is none)."""
        idf = _CODE_ID.get(entity_set, "Id")
        n = 0
        for r in rows:
            name = text(r.get("Name"))
            if name is None:
                continue
            n += 1
            self.entries.append((entity_set, r.get("EntityName") or "", r.get(idf), name, sha))
            self.names[entity_set].add(name)
            if r.get("EntityName") in (None, "Organisations", "Officers") or r.get(idf) not in self.by_id[entity_set]:
                self.by_id[entity_set][r.get(idf)] = name
        return n

    def name(self, entity_set: str, code):
        """The name a code stands for, or None. The three main lists resolve
        by the organisation rows' own numbering (VIEW_IDS), and only to a
        name their code list holds."""
        if code is None:
            return None
        if entity_set in VIEW_IDS:
            n = VIEW_IDS[entity_set].get(code)
            return n if n in self.names[entity_set] else None
        return self.by_id[entity_set].get(code)

    def known(self, entity_set: str, name) -> bool:
        return name is None or name in self.names[entity_set]

    def missing(self) -> list:
        return [s for s in CODE_LISTS if not self.names[s]]


# ── one row of each set ───────────────────────────────────────────────────────

def read_group(row: dict, sha: str):
    """(typed row, None) or (None, why)."""
    num = charity_number(row.get("RegistrationNumber"))
    if num is None:
        return None, "no registration number"
    return {"key": charity_key(num), "number": num, "group_id": row["GroupId"], "name": text(row.get("name")),
            "status": text(row.get("RegistrationStatus")), "registered_on": feed_date(row.get("DateRegistered")),
            "deregistered_on": feed_date(row.get("DeregistrationDate")),
            "source_modified_at": feed_moment(row.get("ModifiedOn")), **cite(sha, "Groups", row["GroupId"])}, None


def read_organisation(row: dict, sha: str, codes: Codes, groups: dict, notes: collections.Counter):
    """(typed row, None) or (None, why). `groups`: GroupId → group row.
    `notes` counts what was kept but could not be resolved."""
    num = charity_number(row.get("CharityRegistrationNumber"))
    if num is None:
        return None, ("no registration number" if not text(row.get("CharityRegistrationNumber"))
                      else "a registration number not of the register's shape")
    status = text(row.get("RegistrationStatus"))
    legal = text(row.get("LegalStructure"))
    for lst, v in (("RegistrationStatus", status), ("LegalStructure", legal)):
        if not codes.known(lst, v):
            notes[f"organisation {lst} not in its code list"] += 1
    out = {"key": charity_key(num), "number": num, "organisation_id": row["OrganisationId"],
           "name": text(row.get("Name")), "other_names": text(row.get("OtherNames")), "status": status,
           "registered_on": feed_date(row.get("DateRegistered")),
           "deregistered_on": feed_date(row.get("DeregistrationDate")),
           "deregistration_reason": text(row.get("DeregistrationReasons")),
           "legal_structure": legal, "legal_structure_other": text(row.get("OtherLegalStructure")),
           "charitable_purpose": text(row.get("CharitablePurpose"))}
    for col, lst, f in (("main_sector", "MainSector", "MainSectorId"), ("main_activity", "MainActivity", "MainActivityId"),
                        ("main_beneficiary", "MainBeneficiary", "MainBeneficiaryId")):
        code = row.get(f)
        out[col + "_id"], out[col] = code, codes.name(lst, code)
        if code is not None and out[col] is None:
            notes[f"organisation {f} not in its code list"] += 1
    addr, dropped = address_for_service(row)
    if dropped:
        notes["address part holding an email address dropped"] += dropped
    out["address_for_service"] = addr
    g = groups.get(row.get("GroupId")) if row.get("GroupId") is not None else None
    if row.get("GroupId") is not None and g is None:
        notes["organisation's group not held"] += 1
    out.update({"group_key": g["key"] if g else None, "group_number": g["number"] if g else None,
                "group_name": g["name"] if g else None, "group_type": row.get("GroupType"),
                "nzbn": nzbn_ok(row.get("NZBNNumber")), "incorporation_number": text(row.get("CompaniesOfficeNumber")),
                "year_end_month": row.get("EndOfYearMonth"), "year_end_day": row.get("EndOfYearDayofMonth"),
                "annual_return_due_on": feed_date(row.get("AnnualReturnDueDate")),
                "source_modified_at": feed_moment(row.get("ModifiedOn"))})
    if text(row.get("NZBNNumber")) and out["nzbn"] is None:
        notes["NZBN failing its check digit, left empty"] += 1
    out.update(cite(sha, "Organisations", row["OrganisationId"]))
    return out, None


def read_officer(row: dict, sha: str, codes: Codes, charities: dict, notes: collections.Counter):
    """(typed row, None) or (None, why). `charities`: OrganisationId →
    (charity key, None) or (None, why it is set aside)."""
    held = charities.get(row.get("OrganisationId"))
    if held is None:
        return None, "its organisation is not in the held pages"
    if held[0] is None:
        return None, f"its organisation is set aside ({held[1]})"
    body_name = text(row.get("BodyCorporateName"))
    person = text(row.get("FullName")) or text(" ".join(p for p in (row.get("FirstName"), row.get("MiddleName"),
                                                                     row.get("LastName")) if p))
    is_body = row.get("IsaBodyCorporate") is True or (body_name is not None and not text(row.get("LastName")))
    if (is_body and body_name is None) or (not is_body and person is None):
        return None, "no name"
    status = text(row.get("OfficerStatus"))
    if not codes.known("OfficerStatus", status):
        notes["officer status not in its code list"] += 1
    ended = feed_date(row.get("LastDateAsAnOfficer"))
    out = {"key": officer_key(row["OfficerId"]), "officer_id": row["OfficerId"], "charity_key": held[0],
           "organisation_id": row["OrganisationId"], "kind": "body corporate" if is_body else "person",
           "full_name": body_name if is_body else person,
           "first_name": None if is_body else text(row.get("FirstName")),
           "middle_name": None if is_body else text(row.get("MiddleName")),
           "last_name": None if is_body else text(row.get("LastName")),
           "role": text(row.get("PositioninOrganisation")), "started_on": feed_date(row.get("PositionAppointmentDate")),
           "ended_on": ended, "ended_on_stated": ended is not None, "status": status,
           "disqualified": status in DISQUALIFIED,
           "declared_not_disqualified": row.get("IsNotDisqualified"),
           "source_modified_at": feed_moment(row.get("ModifiedOn")), **cite(sha, "Officers", row["OfficerId"])}
    return out, None


def read_return(row: dict, sha: str, codes: Codes, charities: dict, groups: dict, notes: collections.Counter):
    """(typed row, None) or (None, why). Filed by an organisation (its
    OrganisationId) or by a group (GroupId alone)."""
    oid, gid = row.get("OrganisationId"), row.get("GroupId")
    charity = group = None
    if oid is not None:
        held = charities.get(oid)
        if held is None:
            return None, "its organisation is not in the held pages"
        if held[0] is None:
            return None, f"its organisation is set aside ({held[1]})"
        charity = held[0]
    if gid is not None:
        g = groups.get(gid)
        if g is None and charity is None:
            return None, "its group is not in the held pages"
        group = g["key"] if g else None
    if charity is None and group is None:
        return None, "names no organisation and no group"
    figures, bad = {}, []
    for f, v in row.items():
        if f in NOT_MONEY or f == "__metadata" or isinstance(v, (bool, dict, list)) or v is None:
            continue
        if isinstance(v, (int, float)) or f.endswith("_LastYear"):
            try:
                n = number(v)
            except (decimal.InvalidOperation, ValueError):
                bad.append(f)
                continue
            if n is not None:
                figures[f] = n
    if bad:
        notes["return figure that is not a number, left out"] += len(bad)
    tier_id = row.get("ReportingTierId")
    tier = codes.name("ReportingTier", tier_id)
    if tier_id is not None and tier is None:
        notes["return tier not in its code list"] += 1
    currency, opinion = text(row.get("ReportingCurrency")), text(row.get("AuditAndReviewWhatTypeOfModifiedOpinionWasReceived"))
    if not codes.known("ReportingCurrency", currency):
        notes["return currency not in its code list"] += 1
    if not codes.known("AuditModifiedOpinionReceived", opinion):
        notes["return audit opinion not in its code list"] += 1
    material = []
    for i in range(1, 5):
        try:
            amount = number(row.get(f"MaterialExpense{i}"))
        except (decimal.InvalidOperation, ValueError):
            amount = None
        if amount is not None:
            material.append({"label": text(row.get(f"MaterialExpense{i}Label")), "amount": amount})
    out = {"key": return_key(row["AnnualReturnId"]), "return_id": row["AnnualReturnId"], "charity_key": charity,
           "group_key": group, "organisation_id": oid, "group_id": gid,
           "period_end": feed_date(row.get("YearEnded")), "months_covered": row.get("PerformanceReportCovers"),
           "began_on": feed_date(row.get("DateEntityBegan")), "tier_id": tier_id, "tier": tier, "currency": currency,
           "audited": row.get("IsFinancialReportAudited"), "modified_opinion": row.get("IsModifiedAuditOpinionReceived"),
           "opinion": opinion, "status_code": row.get("Status"),
           **{col: figures.get(f) for col, f in HEADLINE.items()},
           "figures": figures, "material_expenses": material or None,
           "source_modified_at": feed_moment(row.get("ModifiedOn")), **cite(sha, "AnnualReturn", row["AnnualReturnId"])}
    return out, None


# ── a set's pages ─────────────────────────────────────────────────────────────

def newest_first(pages: list, entity_set: str, read_bytes, only=None, on_page=None):
    """Yield (sha, row, None) for each row of a set's pages, newest page
    first, or (sha, None, catch-log line) for a row a later page holds again.
    `pages`: [sha] oldest first, as the capture lists them. `only`: the set's
    ids to read (the sample's), None for all. `on_page(sha, rows)` is told
    each page's row count as it is opened."""
    keyf, seen = SETS[entity_set], {}
    for sha in reversed(pages):
        _, rows = parse_page(read_bytes(sha))
        if on_page:
            on_page(sha, len(rows))
        for r in rows:
            if set_of(r) != entity_set:
                raise ValueError(f"page {sha[:12]} holds a {set_of(r) or 'nameless'} row in the {entity_set} pages")
            rid = r[keyf]
            if only is not None and rid not in only:
                continue
            if rid in seen:
                yield sha, None, aside(entity_set, sha, rid, "supersede", f"read again on a later page {seen[rid][:12]}")
                continue
            seen[rid] = sha
            yield sha, r, None


def main(argv=None) -> int:
    from support.docstore.landing import read_bytes
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1 or not re.fullmatch(r"[0-9a-f]{64}", argv[0]):
        print(__doc__.strip().splitlines()[-1].strip())
        return 2
    stated, rows = parse_page(read_bytes(argv[0]))
    kinds = collections.Counter(set_of(r) for r in rows)
    print(f"{SOURCE}: page {argv[0][:12]}: {len(rows)} rows ({dict(kinds)}), feed count {stated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
