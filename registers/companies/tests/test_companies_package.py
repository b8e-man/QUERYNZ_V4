"""A later monthly package laid over the export (monthly.py, 2 November 2026). Small zips of CSVs shaped like the
real package's, every name and address invented; no database, no model."""
import gzip
import io
import json
import zipfile

import pytest

from registers.companies import monthly, read

JUL, AUG, OCT = "companies-2026-07", "companies-2026-08", "companies-2026-10"
SHA, PSHA = "0" * 64, "1" * 64

CORE = "NZBN,COMPANY_IDENTIFIER,ENTITY_NAME,REGISTRATION_DATE,REMOVAL_DATE,ENTITY_TYPE,ENTITY_STATUS"
DIRECTOR = "NZBN,ENTITY_NAME,START_DATE,FIRST_NAME,MIDDLE_NAMES,LAST_NAME,ASIC_DIR_YN,ACN,ASIC_COMPANY_NAME"
HOLDER = ("NZBN,ENTITY_NAME,SH_NAME,SH_TYPE,START_DATE,SH_STATUS,PARCEL_IDENTIFIER,ASSIGNMENT_IDENTIFIER,"
          "NUMBER_OF_SHARES,SH_EXTENSIVE_SHAREHOLDING_YN,SH_ADDRESS_PAF_ID,SH_ADDRESS_CARE_OF,SH_ADDRESS_1,"
          "SH_ADDRESS_2,SH_ADDRESS_3,SH_ADDRESS_4,SH_ADDRESS_POSTCODE,SH_ADDRESS_COUNTRY")
RO = ("NZBN,ENTITY_NAME,START_DATE,REGISTERED_OFFICE_ADDRESS_PAF_ID,REGISTERED_OFFICE_ADDRESS_CARE_OF,"
      "REGISTERED_OFFICE_ADDRESS_1,REGISTERED_OFFICE_ADDRESS_2,REGISTERED_OFFICE_ADDRESS_3,"
      "REGISTERED_OFFICE_ADDRESS_4,REGISTERED_OFFICE_ADDRESS_POSTCODE,REGISTERED_OFFICE_ADDRESS_COUNTRY")
OTHER = ("NZBN,INCORPORATION_NUMBER,ENTITY_NAME,ENTITY_TYPE,ENTITY_STATUS,REGISTRATION_DATE,DEREGISTRATION_DATE,"
         "INCORPORATED_SOCIETIES_ACT,INCSOC2022ACT_REREGISTRATION_DATE,CHARITIES_REGISTER_NUMBER,"
         "REGISTERED_OFFICE_ADDRESS_PAF_ID,REGISTERED_OFFICE_ADDRESS_CARE_OF,REGISTERED_OFFICE_ADDRESS_LINE_1,"
         "REGISTERED_OFFICE_ADDRESS_LINE_2,REGISTERED_OFFICE_ADDRESS_LINE_3,REGISTERED_OFFICE_ADDRESS_LINE_4,"
         "REGISTERED_OFFICE_ADDRESS_POSTCODE,REGISTERED_OFFICE_ADDRESS_COUNTRY")
TRUSTS = ("NZBN,INCORPORATION_NUMBER,ENTITY_NAME,ENTITY_TYPE,ENTITY_STATUS,REGISTRATION_DATE,DEREGISTRATION_DATE,"
          "CHARITIES_REGISTER_NUMBER,REGISTERED_OFFICE_ADDRESS_CARE_OF,REGISTERED_OFFICE_ADDRESS_LINE_1,"
          "REGISTERED_OFFICE_ADDRESS_LINE_2,REGISTERED_OFFICE_ADDRESS_LINE_3,REGISTERED_OFFICE_ADDRESS_LINE_4,"
          "REGISTERED_OFFICE_ADDRESS_POSTCODE,REGISTERED_OFFICE_ADDRESS_COUNTRY_CODE")
VILLAGES = ("ENTITY_NUMBER,ENTITY_NAME,REGISTRATION_DATE,ENTITY_STATUS,STATUTORY_SUPERVISOR_NAME,"
            "STATUTORY_SUPERVISOR_DATE_APPOINTED,STATUTORY_SUPERVISOR_ADDRESS_1,STATUTORY_SUPERVISOR_ADDRESS_2,"
            "STATUTORY_SUPERVISOR_ADDRESS_3,STATUTORY_SUPERVISOR_ADDRESS_4,STATUTORY_SUPERVISOR_POSTCODE,"
            "REGISTERED_OFFICE_ADDRESS_1,REGISTERED_OFFICE_ADDRESS_2,REGISTERED_OFFICE_ADDRESS_3,"
            "REGISTERED_OFFICE_ADDRESS_4,REGISTERED_OFFICE_ADDRESS_POSTCODE,ADDRESS_FOR_PREMISES_1,"
            "ADDRESS_FOR_PREMISES_2,ADDRESS_FOR_PREMISES_3,ADDRESS_FOR_PREMISES_4,ADDRESS_FOR_PREMISES_POSTCODE,"
            "OPERATOR_NAME,OPERATOR_NUMBER,OPERATOR_ADDRESS_1,OPERATOR_ADDRESS_2,OPERATOR_ADDRESS_3,"
            "OPERATOR_ADDRESS_4,OPERATOR_ADDRESS_POSTCODE")
PUBLIC = "NZBN,ENTITY_NAME,ENTITY_TYPE,ENTITY_STATUS,REGISTRATION_DATE"
INSOLVENCY = ("NZBN,ENTITY_NAME,START_DATE,INSOLVENCY_TYPE,APPOINTMENT_TYPE,APPOINTEE_FIRST_NAME,APPOINTEE_MIDDLE_NAMES,"
              "APPOINTEE_LAST_NAME,APPOINTMENT_DATE,APPOINTMENT_VACATED_DATE,ORGANISATION,RESSOLUTION_OF_SOLVENCY")


def _zip(files: dict) -> bytes:
    heads = {"companies_core_data.csv": CORE, "companies_director.csv": DIRECTOR,
             "companies_shareholder.csv": HOLDER, "companies_registered_office_address.csv": RO,
             "other_incorporated_entities_core_data.csv": OTHER, "charitable_trust_boards_core_data.csv": TRUSTS,
             "public_sector_entities_core_data.csv": PUBLIC, "retirement_villages_core_data.csv": VILLAGES,
             "companies_insolvency.csv": INSOLVENCY}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, head in heads.items():
            z.writestr(name, "﻿" + "\n".join([head] + files.get(name, [])) + "\n")
    return buf.getvalue()


def _export(part, lines, runs):
    head = {"t": "export", "part": part, "files": [JUL, AUG], "runs": runs, "aux_rows": {}}
    return gzip.compress(("\n".join(json.dumps(l, sort_keys=True) for l in [head] + lines) + "\n").encode())


def _runs(part, jul, aug):
    z = {"entities": 0, "directors": 0, "shareholders": 0}
    return {JUL: {**z, part: jul}, AUG: {**z, part: aug}}


def _director(nzbn, first, last, start, files, **kw):
    return {"t": "director", "nzbn": nzbn, "number": "1", "first_name": first, "middle_names": None,
            "last_name": last, "full_name": f"{first} {last}", "role_type": "DIRECTOR", "appointed_on": start,
            "files": files, "last_file": files[-1], "suppressed": False, "old_id": "x", **kw}


def _read(part, lines, runs, zipped, only=None):
    return read.read(part, _export(part, lines, runs), SHA, package=(OCT, zipped, PSHA), only=only)


def test_the_october_roles_are_merged_a_role_that_left_keeps_august_and_a_new_one_is_october_s():
    lines = [_director("9429000000001", "Ann", "Able", "2019-05-01", [JUL, AUG]),
             _director("9429000000001", "Ben", "Baker", "2018-01-01", [JUL, AUG], suppressed=True),
             _director("9429000000001", "Cy", "Carter", "2017-01-01", [JUL])]
    z = _zip({"companies_director.csv": ["9429000000001,EXAMPLE LIMITED,01/05/2019,Ann,,Able,,,",
                                         "9429000000001,EXAMPLE LIMITED,01/01/2018,Ben,,Baker,,,",
                                         "9429000000001,EXAMPLE LIMITED,20/09/2026,Dee,,Doe,,,",
                                         "9429000000001,EXAMPLE LIMITED,20/09/2026,Dee,,Doe,,,"]})
    r = _read("directors", lines, _runs("directors", 3, 2), z)
    by = {x["filed"]["full_name"]: x for x in r.rows["directors"]}
    ann, ben, cy, dee = by["Ann Able"], by["Ben Baker"], by["Cy Carter"], by["Dee Doe"]
    assert (ann["filed"]["first_file"], ann["filed"]["last_file"], ann["filed"]["in_latest"]) == (JUL, OCT, True)
    assert ann["document"] == PSHA and ann["place"] == "companies_director.csv line 2"
    assert ann["profile"] == read.PACKAGE_PROFILE and ann["filed"]["source_note"] == monthly.NOTE
    assert ben["filed"]["suppressed"] is True and ben["filed"]["in_latest"]          # the export's mark is kept
    assert (cy["filed"]["last_file"], cy["filed"]["in_latest"], cy["document"]) == (JUL, False, SHA)
    assert (dee["filed"]["first_file"], dee["filed"]["in_latest"], dee["filed"]["appointed_on"]) == (OCT, True, "2026-09-20")
    assert all(x["filed"]["ended_on"] is None for x in by.values())
    repeats = [(i, c) for i, _, w, c in r.set_aside if "repeats" in w]
    assert repeats == [(f"{PSHA}/{OCT}", 1)]


def test_a_role_august_held_and_october_does_not_list_is_no_longer_in_the_latest_file():
    lines = [_director("9429000000001", "Ann", "Able", "2019-05-01", [JUL, AUG])]
    r = _read("directors", lines, _runs("directors", 1, 1), _zip({}))
    (a,) = r.rows["directors"]
    assert (a["filed"]["last_file"], a["filed"]["in_latest"], a["filed"]["ended_on"]) == (AUG, False, None)


def test_an_entity_october_changed_keeps_august_s_state_and_a_new_one_is_added():
    lines = [{"t": "entity", "register": "companies", "nzbn": "9429000000001", "number": "11",
              "name": "Example Limited", "type": "LTD", "status": "Registered", "registered_on": "2020-01-01",
              "removed_on": None, "files": [JUL, AUG], "last_file": AUG},
             {"t": "entity", "register": "companies", "nzbn": "9429000000003", "number": "33",
              "name": "Steady Limited", "type": "LTD", "status": "Registered", "registered_on": "2010-01-01",
              "removed_on": None, "files": [AUG], "last_file": AUG},
             {"t": "entity", "register": "other_incorporated", "nzbn": "9429000000009", "number": "99",
              "name": "Old Society", "type": "Incorporated Society", "status": "registered",
              "registered_on": "02/03/1951", "removed_on": None, "files": [], "last_file": AUG, "in_latest": True}]
    z = _zip({"companies_core_data.csv": ["9429000000001,11,Example Limited,01/01/2020,15/09/2026,LTD,Removed",
                                          "9429000000003,33,Steady Limited,01/01/2010,,LTD,Registered",
                                          "9429000000002,22,New Limited,10/09/2026,,LTD,Registered"]})
    r = _read("entities", lines, _runs("entities", 1, 2), z)
    e = {x["key"]: x for x in r.rows["entities"]}
    one = e["companies/9429000000001"]["filed"]
    assert (one["status"], one["removed_on"], one["last_file"], one["in_latest"]) == ("Removed", "2026-09-15", OCT, True)
    assert e["companies/9429000000002"]["filed"]["first_file"] == OCT
    assert e["companies/9429000000003"]["filed"]["last_file"] == OCT
    assert not e["companies/9429000000009"]["filed"]["in_latest"]          # a body the package no longer lists
    (s,) = r.rows["entity_states"]
    assert s["key"] == f"companies/9429000000001/in/{AUG}" and s["filed"]["status"] == "Registered"
    assert s["filed"]["removed_on"] is None


def test_a_holding_and_an_office_match_across_the_export_and_the_package_and_no_holder_address_is_read():
    sh = {"t": "shareholder", "nzbn": "9429000000001", "number": "1", "shareholder_type": "individual",
          "full_name": "Ann Able", "shareholder_entity_name": None, "shareholder_nzbn": None,
          "allocation_type": "active", "suppressed": False, "old_id": "x", "shares": "100", "files": [AUG],
          "last_file": AUG}
    z = _zip({"companies_shareholder.csv": [
        "9429000000001,EXAMPLE LIMITED,Ann Able,Shareholder Individual,01/01/2020,active,1,1,100,N,,,"
        "9 Invented Lane,Nowhere,,,0000,NEW ZEALAND"]})
    r = _read("shareholders", [sh], _runs("shareholders", 0, 1), z)
    (h,) = r.rows["shareholders"]
    assert (h["filed"]["first_file"], h["filed"]["last_file"]) == (AUG, OCT)
    assert "Invented" not in json.dumps(h, default=str)
    ro = {"t": "registered_office", "register": "companies", "nzbn": "9429000000001", "number": None,
          "start": "01/02/2020", "care_of": None, "line_1": "1 Example Street", "line_2": "Exampletown",
          "line_3": None, "line_4": None, "postcode": "1010", "country": "NEW ZEALAND", "last_file": AUG,
          "in_latest": True}
    z = _zip({"companies_registered_office_address.csv": [
        "9429000000001,EXAMPLE LIMITED,01/02/2020,,,1 Example Street,Exampletown,,,1010,NEW ZEALAND",
        "9429000000001,EXAMPLE LIMITED,01/09/2026,,,3 Moved Street,Exampletown,,,1010,NEW ZEALAND"]})
    r = read.read("addresses", _export("addresses", [ro], {}), SHA, package=(OCT, z, PSHA))
    rows = sorted(r.rows["registered_offices"], key=lambda x: x["filed"]["started_on"])
    assert [(x["filed"]["started_on"], x["filed"]["last_file"], x["document"]) for x in rows] == [
        ("2020-02-01", OCT, PSHA), ("2026-09-01", OCT, PSHA)]      # the latest file that carries it is cited


def test_the_package_s_new_lines_obey_the_sample_filter():
    z = _zip({"companies_core_data.csv": ["9429000000002,22,New Limited,10/09/2026,,LTD,Registered",
                                          "9429000000004,44,Other Limited,10/09/2026,,LTD,Registered"]})
    r = _read("entities", [], _runs("entities", 0, 0), z, only={"9429000000004"})
    assert [x["key"] for x in r.rows["entities"]] == ["companies/9429000000004"]


def test_more_package_rows_than_the_file_s_lines_does_not_reconcile(monkeypatch):
    z = _zip({"companies_director.csv": ["9429000000001,EXAMPLE LIMITED,01/05/2019,Ann,,Able,,,"]})
    real = monthly.merge

    def short_count(*a, **k):
        head, lines = real(*a, **k)
        head["runs"][OCT]["directors"] = 0
        return head, lines
    monkeypatch.setattr(monthly, "merge", short_count)
    with pytest.raises(AssertionError):
        _read("directors", [], _runs("directors", 0, 0), z)


# ── the package-only files: insolvency appointments and the villages' operators (2 November 2026) ──────────────

def _pkg(files):
    return read.read_package((OCT, _zip(files), PSHA))


def test_each_insolvency_appointment_is_a_row_with_its_appointee_dates_and_solvency_and_a_repeat_is_one():
    r = _pkg({"companies_insolvency.csv": [
        "9429000000001,EXAMPLE LIMITED,05/03/2020,Liquidation,241(2)(a) - Special Resolution of Shareholders,"
        "Pat,Q,Practitioner,05/03/2020,,EXAMPLE INSOLVENCY LIMITED,Y",
        "9429000000001,EXAMPLE LIMITED,05/03/2020,Liquidation,283(8) - Vacancy in Office,Ray,,Replacement,"
        "01/06/2021,,OTHER INSOLVENCY LIMITED,",
        "9429000000001,EXAMPLE LIMITED,05/03/2020,Liquidation,283(8) - Vacancy in Office,Ray,,Replacement,"
        "01/06/2021,,OTHER INSOLVENCY LIMITED,",
        "9429000000002,SECOND LIMITED,10/10/2019,Receivership,,Sam,,Receiver,10/10/2019,30/11/2020,RECEIVERS LIMITED,",
        ",NO NUMBER LIMITED,01/01/2020,Liquidation,,A,,B,01/01/2020,,X,"]})
    rows = sorted(r.rows["insolvencies"], key=lambda x: (x["filed"]["nzbn"], x["filed"]["appointed_on"]))
    assert [(x["filed"]["appointee"], x["filed"]["appointed_on"], x["filed"]["vacated_on"],
             x["filed"]["resolution_of_solvency"]) for x in rows] == [
        ("Pat Q Practitioner", "2020-03-05", None, True), ("Ray Replacement", "2021-06-01", None, False),
        ("Sam Receiver", "2019-10-10", "2020-11-30", False)]
    first = rows[0]
    assert first["key"].startswith("companies/9429000000001/insolvency/") and first["filed"]["entity_key"] == "companies/9429000000001"
    assert first["filed"]["insolvency_type"] == "Liquidation" and first["filed"]["started_on"] == "2020-03-05"
    assert first["document"] == PSHA and first["place"] == "companies_insolvency.csv line 2"
    assert first["profile"] == read.PACKAGE_PROFILE and first["filed"]["source_note"] == monthly.NOTE
    assert len({x["key"] for x in rows}) == 3
    whys = sorted(w for _, _, w, _ in r.set_aside)
    assert len(whys) == 2 and "no NZBN" in whys[0] and whys[1].startswith("the same line as companies_insolvency.csv line 3")
    assert r.counts["insolvencies.lines"] == 5 and r.counts["insolvencies"] == 3 and r.counts["insolvencies.set_aside"] == 2


def test_a_village_carries_its_operator_and_supervisor_and_no_address_is_read():
    r = _pkg({"retirement_villages_core_data.csv": [
        "2000001,EXAMPLE VILLAGE,01-11-2007,REGISTERED,EXAMPLE SUPERVISOR LIMITED,02-03-2026,"
        "Level 1 Invented Tower,Supervisorville,,Nowhere,0000,1 Office Road,Officeton,,Nowhere,0000,"
        "9 Premises Way,Villageton,,Nowhere,0000,EXAMPLE OPERATOR LIMITED,1234567,2 Operator Road,Opton,,Nowhere,0000"]})
    (v,) = r.rows["villages"]
    f = v["filed"]
    assert v["key"] == f["entity_key"] == "companies/retirement_village/2000001"
    assert (f["operator_name"], f["operator_number"], f["supervisor_name"], f["supervisor_appointed_on"]) == (
        "EXAMPLE OPERATOR LIMITED", "1234567", "EXAMPLE SUPERVISOR LIMITED", "2026-03-02")
    text = json.dumps(r.rows, default=str)
    assert not any(w in text for w in ("Invented", "Premises", "Operator Road", "Office Road"))

