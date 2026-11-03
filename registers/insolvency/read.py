"""Reading the Insolvency Register API's answers (registers/insolvency, 2 November 2026).

Three kinds of answer, each under its profile (profile-proposed.jsonl; recognised by its own keys, pinned both ways):

  insolvency-register-estate     GET /insolvencies/{estate-id}: one estate's public detail
  insolvency-register-search     GET /insolvencies: a page of search results (`searchResults`, `totalItems`)
  insolvency-register-removals   GET /insolvencies/removalorcorrections: a page of estates removed or corrected

The terms the API's own page sets on holding a copy are rules here, each a function the load applies and a test pins:

  removed(...)       an estate the removals operation named after our latest answer for it is not published, and the
                     removals job deletes its rows from the lane's tables the moment it is named (capture.run_removals)
  shown_until(...)   four years from discharge from bankruptcy or from a no asset procedure, five from a debt repayment
                     order; no limit for a person bankrupt two or more times (the register's `multipleInsolvencies`),
                     the API's stated exception; a discharged estate with no discharge date is not shown
  suppressed(...)    an estate whose status or type says suppressed is never published

No address of a person is ever read: `strip(...)` takes every address field and the month and year of birth out of an
answer before it is landed (the bytes as received are hashed, never kept), and the reader has no address column to fill.
"""
import datetime as dt
import json
import re

READER = "registers.insolvency.read 1"
PROFILES = {"estate": "insolvency-register-estate", "search": "insolvency-register-search",
            "removals": "insolvency-register-removals"}

#: never landed, never read: any key naming an address, and the month and year of birth
_DROP = re.compile(r"address|monthofbirth|yearofbirth", re.I)

#: the display windows the API's page states, in years, by what the window runs from
WINDOW_YEARS = {"discharge": 4, "dro": 5}


def strip(obj):
    """The answer without any address field or birth month and year, at any depth."""
    if isinstance(obj, dict):
        return {k: strip(v) for k, v in obj.items() if not _DROP.search(k)}
    if isinstance(obj, list):
        return [strip(v) for v in obj]
    return obj


def strip_bytes(body: bytes) -> bytes:
    """The bytes to land: the parsed answer stripped and written back canonically (sorted keys, no spaces)."""
    return json.dumps(strip(json.loads(body)), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def recognise(obj) -> str | None:
    """Which of the three answers this is, by its own keys; None for anything else."""
    if not isinstance(obj, dict):
        return None
    if "removedOrCorrectedInsolvencies" in obj and "totalItems" in obj:
        return "removals"
    if "searchResults" in obj and "totalItems" in obj:
        return "search"
    if "estateNumber" in obj and ("insolvencyTypeDescription" in obj or "insolvencyStatus" in obj):
        return "estate"
    return None


def _date(v) -> dt.date | None:
    if not v or not isinstance(v, str):
        return None
    try:
        return dt.date.fromisoformat(v[:10])
    except ValueError:
        return None


def _years_after(d: dt.date, n: int) -> dt.date:
    try:
        return d.replace(year=d.year + n)
    except ValueError:            # 29 February
        return d.replace(year=d.year + n, day=28)


def suppressed(e: dict) -> bool:
    """The register marks an estate suppressed in its status or type; such an estate is never published."""
    return any("suppress" in str(e.get(k) or "").lower() for k in ("insolvencyStatus", "insolvencyTypeDescription", "status"))


def discharged(e: dict) -> bool:
    s = str(e.get("insolvencyStatus") or "").lower()
    return bool(e.get("dischargeOrCompletionDate")) or any(w in s for w in ("discharg", "completed", "complete"))


def shown_until(e: dict, register: str = "Insolvency") -> tuple:
    """(last day it may be shown or None for no limit, why). A company's liquidation by the Official Assignee carries no
    stated window and is shown while the register returns it."""
    if e.get("organisationName") and not e.get("estateName"):
        return None, "a company's estate: shown while the register returns it"
    if e.get("multipleInsolvencies"):
        return None, "bankrupt two or more times: the API's stated exception"
    if register.upper() == "DRO":
        start = _date(e.get("adjudicationOrLiquidationDate"))
        if not start:
            return dt.date.min, "a debt repayment order with no date: not shown"
        return _years_after(start, WINDOW_YEARS["dro"]), "five years from the debt repayment order"
    if not discharged(e):
        return None, "current: shown while the register returns it"
    end = _date(e.get("dischargeOrCompletionDate"))
    if not end:
        return dt.date.min, "discharged with no discharge date: not shown until a detail answer gives one"
    return _years_after(end, WINDOW_YEARS["discharge"]), "four years from discharge"


def removed(estate: int, answered_at, removals: dict) -> bool:
    """An estate the removals operation named at or after our latest answer for it: {estate: [seen_at, ...]}."""
    return any(seen >= answered_at for seen in removals.get(estate, ()))


def name_text(n) -> str:
    """One name as text: the register answers an alternate name as {firstName, middleName, lastName} (seen 3 November
    2026, 106 of them), a trading name as text; either is taken."""
    if isinstance(n, dict):
        return " ".join(str(n.get(k) or "").strip() for k in ("firstName", "middleName", "lastName") if n.get(k)).strip()
    return str(n or "").strip()


def names(v) -> list:
    return [t for t in (name_text(n) for n in (v or [])) if t] or None


def estate_row(e: dict, *, register: str, read_from: str, document: str, version: int, place: str = None) -> dict:
    """One estate's row from a detail answer or one search result; no address column exists to fill."""
    org = e.get("organisationName")
    name = e.get("estateName") or org or ""
    until, _ = shown_until(e, register)
    return {
        "key": f"insolvency/{int(e['estateNumber'])}", "estate_number": int(e["estateNumber"]),
        "kind": "company" if org and not e.get("estateName") else "person", "register": register,
        "name": name.strip(), "alternate_names": names(e.get("alternateNames")),
        "trading_names": names(e.get("tradingNames")), "organisation_name": org,
        "nzbn": e.get("nzbn") or None, "company_number": e.get("companyNumber") or None,
        "insolvency_type": e.get("insolvencyTypeDescription"), "status": e.get("insolvencyStatus"),
        "adjudicated_on": _date(e.get("adjudicationOrLiquidationDate")),
        "discharged_on": _date(e.get("dischargeOrCompletionDate")),
        "discharge_type": e.get("dischargeOrCompletionType"), "discharge_suspended": e.get("dischargeSuspended"),
        "annulled_on": _date(e.get("annulmentDate")), "multiple": e.get("multipleInsolvencies"),
        "occupation": e.get("occupationAtAdjudicationOrIndustryAtLiquidation"), "court": e.get("courtName"),
        "office": e.get("officeForEnquiries") or e.get("officer"),
        "partnered_estates": [int(p["estateNumber"]) for p in (e.get("partneredEstates") or []) if p.get("estateNumber")] or None,
        "shown_until": None if until is None or until == dt.date.min else until,
        "read_from": read_from, "document": document, "page": None, "place": place, "reader": READER,
        "profile": PROFILES["estate" if read_from == "detail" else "search"], "profile_version": version,
    }


def why_withheld(e: dict, register: str, today: dt.date) -> str | None:
    """Why an estate is not published, or None: suppressed, annulled, past its window, or no name."""
    if suppressed(e):
        return "suppressed: never published"
    if e.get("annulmentDate"):
        return "annulled: the bankruptcy was set aside"
    until, why = shown_until(e, register)
    if until is not None and until < today:
        return f"past its window ({why})"
    if not (e.get("estateName") or e.get("organisationName")):
        return "no name the register gives"
    return None


def search_results(body: bytes) -> tuple:
    """(results, totalItems) of a search page."""
    obj = json.loads(body)
    return list(obj.get("searchResults") or []), obj.get("totalItems")


def removals_named(body: bytes) -> tuple:
    """([(estate, removedDate)], totalItems) of a removals page: the estate numbers only are read."""
    obj = json.loads(body)
    return ([(int(r["estateNumber"]), r.get("removedDate")) for r in (obj.get("removedOrCorrectedInsolvencies") or [])
             if r.get("estateNumber") is not None], obj.get("totalItems"))
