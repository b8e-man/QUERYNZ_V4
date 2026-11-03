"""The terms of holding a copy, as read's rules, on answers shaped like the API definition's own examples (every name and
number invented), and a mutant of each term rule (removal, window, suppression, and the address strip) caught. The mutants
are built in memory from read.py's source; no file is edited. Nothing is fetched."""
import datetime as dt
import json
import types

import pytest

from registers.insolvency import read

TODAY = dt.date(2026, 11, 2)
T0 = dt.datetime(2026, 11, 1, 21, 10, tzinfo=dt.timezone.utc)


def _estate(**kw):
    e = {"estateNumber": 1001, "estateName": "Invented Person Example", "insolvencyTypeDescription": "Creditor Application",
         "insolvencyStatus": "Current", "adjudicationOrLiquidationDate": "2024-02-01T00:00:00", "multipleInsolvencies": False,
         "addressAtAdjudication": {"addressLine1": "1 Invented Street", "suburb": "Exampletown"},
         "currentAddresses": [{"addressLine1": "2 Invented Road"}], "monthOfBirth": 3, "yearOfBirth": 1970,
         "partneredEstates": [{"estateNumber": 1009, "addressAtAdjudication": "3 Invented Lane"}],
         "occupationAtAdjudicationOrIndustryAtLiquidation": "Invented trade", "courtName": "High Court"}
    e.update(kw)
    return e


def rules(mod) -> list:
    """Every term rule on invented answers; the names of those that do not hold."""
    broken = []
    s = json.loads(mod.strip_bytes(json.dumps(_estate()).encode()))
    if "Invented Street" in json.dumps(s) or "Invented Road" in json.dumps(s) or "Invented Lane" in json.dumps(s) \
            or "monthOfBirth" in s or "yearOfBirth" in s or s.get("estateName") != "Invented Person Example":
        broken.append("every address field and the month and year of birth are taken out before landing; the rest kept")
    if any("address" in k for k in mod.estate_row(_estate(), register="Insolvency", read_from="detail", document="d" * 64,
                                                    version=1)):
        broken.append("the row has no address column")
    # the window: four years from discharge
    old = _estate(insolvencyStatus="Discharged", dischargeOrCompletionDate="2020-01-01T00:00:00")
    if mod.shown_until(old)[0] != dt.date(2024, 1, 1) or not (mod.why_withheld(old, "Insolvency", TODAY) or "").startswith("past"):
        broken.append("a bankruptcy discharged more than four years ago is not shown")
    recent = _estate(insolvencyStatus="Discharged", dischargeOrCompletionDate="2023-06-01")
    if mod.why_withheld(recent, "Insolvency", TODAY) is not None:
        broken.append("a bankruptcy discharged less than four years ago is shown")
    if mod.why_withheld(_estate(insolvencyStatus="Discharged"), "Insolvency", TODAY) is None:
        broken.append("a discharged estate with no discharge date is not shown")
    # five years from a debt repayment order
    if mod.why_withheld(_estate(adjudicationOrLiquidationDate="2021-10-01"), "DRO", TODAY) is None:
        broken.append("a debt repayment order more than five years old is not shown")
    if mod.why_withheld(_estate(adjudicationOrLiquidationDate="2021-12-01"), "DRO", TODAY) is not None:
        broken.append("a debt repayment order less than five years old is shown")
    # the stated exception, and a current estate
    if mod.why_withheld(_estate(multipleInsolvencies=True, insolvencyStatus="Discharged",
                                dischargeOrCompletionDate="2010-05-05"), "Insolvency", TODAY) is not None:
        broken.append("a person bankrupt two or more times is the stated exception")
    if mod.why_withheld(_estate(), "Insolvency", TODAY) is not None:
        broken.append("a current bankruptcy is shown")
    # suppression and annulment
    for kw in ({"insolvencyStatus": "Suppressed"}, {"insolvencyTypeDescription": "Suppressed estate"}):
        if not (mod.why_withheld(_estate(**kw), "Insolvency", TODAY) or "").startswith("suppressed"):
            broken.append(f"a suppressed estate is never published ({kw})")
    if mod.why_withheld(_estate(annulmentDate="2025-01-01"), "Insolvency", TODAY) is None:
        broken.append("an annulled bankruptcy is not published")
    # the removals
    if not mod.removed(1001, T0, {1001: [T0 + dt.timedelta(hours=1)]}) or not mod.removed(1001, T0, {1001: [T0]}):
        broken.append("an estate the removals named at or after our latest answer is removed")
    if mod.removed(1001, T0, {1001: [T0 - dt.timedelta(days=1)]}) or mod.removed(1001, T0, {1002: [T0]}):
        broken.append("an answer after the removal (a correction) stands")
    return broken


def test_every_rule_holds():
    assert rules(read) == []


def test_recognised_both_ways():
    est, srch, rem = _estate(), {"searchResults": [], "totalItems": 0, "page": 1}, \
        {"removedOrCorrectedInsolvencies": [{"estateNumber": 5, "removedDate": "2026-11-01"}], "totalItems": 1}
    assert [read.recognise(x) for x in (est, srch, rem)] == ["estate", "search", "removals"]
    assert read.recognise({}) is None and read.recognise([]) is None and read.recognise({"estateNumber": 1}) is None
    assert read.recognise({"searchResults": []}) is None and read.recognise({"message": "Access denied"}) is None
    assert read.removals_named(json.dumps(rem).encode()) == ([(5, "2026-11-01")], 1)


def test_a_company_is_a_company_and_a_leap_day_has_an_end():
    co = _estate(estateName=None, organisationName="Invented Trading Limited", nzbn="9429000000017")
    row = read.estate_row(co, register="Insolvency", read_from="search", document="d" * 64, version=1, place="estateNumber=1001")
    assert row["kind"] == "company" and row["shown_until"] is None and row["name"] == "Invented Trading Limited"
    assert read.shown_until(_estate(insolvencyStatus="Discharged", dischargeOrCompletionDate="2024-02-29"))[0] == dt.date(2028, 2, 29)
    assert read._years_after(dt.date(2024, 2, 29), 1) == dt.date(2025, 2, 28)


def test_an_alternate_name_answered_as_parts_is_read_as_text():
    """3 November 2026: the live register answers alternateNames as {firstName, middleName, lastName}; the load's COPY
    could not write a dict into text[] and the first load failed."""
    e = _estate(alternateNames=[{"firstName": "Invented", "middleName": None, "lastName": "Other"},
                                {"firstName": "", "middleName": "", "lastName": ""}, "Plain Alias"],
                tradingNames=["Invented Trading"])
    row = read.estate_row(e, register="Insolvency", read_from="detail", document="d" * 64, version=1)
    assert row["alternate_names"] == ["Invented Other", "Plain Alias"] and row["trading_names"] == ["Invented Trading"]
    assert all(isinstance(n, str) for n in row["alternate_names"])


def test_a_liquidation_is_a_company_however_it_is_answered():
    """3 November 2026: every company found by a search, and every detail naming it twice, was filed a person."""
    def row(e):
        return read.estate_row(e, register="Insolvency", read_from="search", document="d" * 64, version=1)
    from_search = _estate(estateName="Invented Holdings Limited", insolvencyTypeDescription="Court Liquidation",
                          insolvencyStatus="Currently In Liquidation")
    from_detail = _estate(estateName="Invented Holdings Limited", organisationName="Invented Holdings Limited",
                          companyNumber="1234567", insolvencyTypeDescription="Court Liquidation")
    assert row(from_search)["kind"] == "company" and row(from_detail)["kind"] == "company"
    assert row(_estate())["kind"] == "person"
    assert row(_estate(insolvencyTypeDescription="No Asset Procedure"))["kind"] == "person"


MUTANTS = {
    "removal": ("return any(seen >= answered_at for seen in removals.get(estate, ()))", "return False"),
    "window (discharge)": ('return _years_after(end, WINDOW_YEARS["discharge"]), "four years from discharge"',
                           'return None, "four years from discharge"'),
    "window (debt repayment order)": ('WINDOW_YEARS = {"discharge": 4, "dro": 5}', 'WINDOW_YEARS = {"discharge": 4, "dro": 50}'),
    "suppression": ('    if suppressed(e):\n        return "suppressed: never published"\n', ""),
    "address strip": ('_DROP = re.compile(r"address|monthofbirth|yearofbirth", re.I)',
                      '_DROP = re.compile(r"monthofbirth|yearofbirth", re.I)'),
}


def _mutant(old, new):
    src = open(read.__file__, encoding="utf-8").read()
    assert src.count(old) == 1, f"the mutant's anchor is not in read.py once: {old}"
    mod = types.ModuleType("read_mutant")
    exec(compile(src.replace(old, new), read.__file__, "exec"), mod.__dict__)
    return mod


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutant_is_caught(name):
    assert rules(_mutant(*MUTANTS[name])), f"the mutant '{name}' passes every rule: a rule is missing"
