"""The reading: pure, no network, no model. One profile, recognised by shape.

`acc-health-contract-data-workbook` v1: ACC's "Health contract data"
(catalogue package `health-contract-data`, CC BY 3.0 NZ), an Official
Information Act answer (AR-3944, extracted 29 March 2023): injury claims
active, and their costs, by financial year (1 July 2012 to 30 June 2022),
accident region, territorial authority and ACC contract class. It names no
supplier, person or address: it says how much ACC spent through each class of
its health contracts, where. Recognised before anything is read by:

  - three sheets, `Notes`, `Data`, `Appendix`;
  - Notes: "Title:" "Health Contract Data" and "Purpose:" naming the
    Official Information Act;
  - Data: row 1 ten years in alternate columns from B (2013 … 2022), row 2
    "Location" then "Active Claims" and "Total Costs" in turn;
  - Appendix: one column of contract classes.

A Data row's level is its shape, not a word list: a label in the Appendix is
a contract class; "Grand Total" the total; any other label is a territorial
authority when the next row is a class, else a region. Every cell is kept as
published ("<4" claims and "<$100" costs are ACC's suppression, kept as
such and never guessed); the number beside it only where one is printed.
The rows reconcile upward and check.py holds them to it.
"""
import datetime as dt
import re
from dataclasses import dataclass, field

from registers.contract_disclosures import workbook

PROFILE = "acc-health-contract-data-workbook"
PROFILE_VERSION = 1
READER = "registers.contract_disclosures.read"
AGENCY = "Accident Compensation Corporation"
LICENCE = "CC BY 3.0 NZ"
ATTRIBUTION = ("Source: Accident Compensation Corporation, Health contract data (AR-3944), data.govt.nz, "
               "licensed under CC BY 3.0 NZ")
_NUM = re.compile(r"-?\d+(\.\d+)?")


class NotTheShape(ValueError):
    """Not a file this profile reads."""


@dataclass
class Reading:
    rows: list = field(default_factory=list)
    set_aside: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def recognise(data: bytes) -> dict:
    """The workbook's sheets, or NotTheShape naming the landmark missing."""
    try:
        sh = dict(workbook.sheets(data))
    except workbook.NotAWorkbook as exc:
        raise NotTheShape(str(exc))
    if set(sh) != {"Notes", "Data", "Appendix"}:
        raise NotTheShape(f"sheets {sorted(sh)}, not Notes, Data, Appendix")
    notes = {c.get(2): c.get(4, "") for _, c in sh["Notes"]}
    if notes.get("Title:") != "Health Contract Data" or "Official Information Act" not in notes.get("Purpose:", ""):
        raise NotTheShape("the Notes sheet does not title it Health Contract Data, an OIA response")
    data_rows = sh["Data"]
    if len(data_rows) < 3:
        raise NotTheShape("the Data sheet has no rows under its heads")
    (r1, years), (r2, heads) = data_rows[0], data_rows[1]
    if r1 != 1 or r2 != 2 or heads.get(1) != "Location":
        raise NotTheShape("the Data sheet's heads are not Location then the year pairs")
    ys = [years.get(c, "") for c in range(2, 22, 2)]
    if not all(re.fullmatch(r"20\d\d", y) for y in ys) or sorted(ys) != ys or len(set(ys)) != 10:
        raise NotTheShape("row 1 is not ten years in alternate columns")
    for c in range(2, 22):
        if heads.get(c) != ("Active Claims" if c % 2 == 0 else "Total Costs"):
            raise NotTheShape(f"row 2 column {c} is {heads.get(c)!r}")
    return sh


def _number(text: str):
    return text if _NUM.fullmatch(text or "") else None


def read(sha256: str, data: bytes) -> Reading:
    sh = recognise(data)
    out = Reading()
    notes = {c.get(2): c.get(4, "") for _, c in sh["Notes"]}
    out.meta = {"reference": notes.get("Reference:", ""), "period": notes.get("Period:", ""),
                "extracted_on": workbook.serial_date(notes.get("DWH load date:", "")),
                "classes": len(sh["Appendix"])}
    classes = {c.get(1) for _, c in sh["Appendix"]}
    years = sh["Data"][0][1]
    body = sh["Data"][2:]
    region = ta = None
    for i, (rownum, c) in enumerate(body):
        label = c.get(1, "")
        if not label:
            out.set_aside.append({"document": sha256, "place": f"Data!A{rownum}", "stage": "read",
                                  "reason": "a row with no location or class"})
            continue
        if label == "Grand Total":
            level, region, ta, klass = "total", None, None, None
        elif label in classes:
            if ta is None:
                out.set_aside.append({"document": sha256, "place": f"Data!A{rownum}", "stage": "read",
                                      "reason": "a contract class before any territorial authority"})
                continue
            level, klass = "class", label
        else:
            nxt = body[i + 1][1].get(1) if i + 1 < len(body) else None
            if nxt in classes:
                level, ta, klass = "territorial authority", label, None
            else:
                level, region, ta, klass = "region", label, None, None
        for col in range(2, 22, 2):
            fy = years[col]
            claims, costs = c.get(col, ""), c.get(col + 1, "")
            out.rows.append({
                "key": f"{sha256[:16]}:{rownum}:{fy}", "agency": AGENCY, "level": level, "region": region,
                "territorial_authority": ta if level in ("territorial authority", "class") else None,
                "contract_class": klass, "financial_year": fy,
                "year_ended": dt.date(int(fy), 6, 30).isoformat(),
                "active_claims_as_published": claims, "total_costs_as_published": costs,
                "active_claims": _number(claims), "total_costs_nzd": _number(costs),
                "suppressed": claims.startswith("<") or costs.startswith("<"),
                "licence": LICENCE, "attribution": ATTRIBUTION, "document": sha256, "page": "Data",
                "place": f"Data!A{rownum}", "read_from": "workbook cells", "reader": READER,
                "profile": PROFILE, "profile_version": PROFILE_VERSION})
    return out
