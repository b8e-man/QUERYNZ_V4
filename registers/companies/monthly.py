"""A monthly package read whole from its own CSVs, after the old estate's export (2 November 2026).

The Companies Office's monthly package is a zip of CSVs. The July and August
2026 packages survive only as the old estate's tables, exported once
(capture.py). A later package Arthur downloads is held whole: the zip lands in
the document store by hash, is pinned in PACKAGES, and is read from the store,
never from where it was downloaded.

`merge(part, header, lines, package)` lays one package over the export's lines
for one part and yields lines in the export's own shape, so read.py reads both
the same way:

  entities       a company (companies_core_data) by its NZBN; the other bodies
                 (other_incorporated_entities, charitable_trust_boards,
                 public_sector_entities, retirement_villages core data) by
                 their NZBN, else their register number. A body the package
                 names gains the package in `files` (companies) or is
                 `in_latest` (the others), and the package's values; where a
                 value changed, its state before goes into `earlier`, dated to
                 the file that carried it. A body the package does not name is
                 left as it was: its last file is not the latest, so it is not
                 in the latest file
  directors      one role per company, names and start (the old loader's key);
                 the package has no role type and no suppression mark, so a
                 role it adds is a DIRECTOR, unsuppressed, as the old loader
                 read the same CSV, and a role it repeats keeps the export's
                 mark
  shareholders   one holding per company, holder's name, shares and status
  addresses      a registered office by its body, start and lines; never a
                 person's address: the shareholder and director CSVs' address
                 columns, the statutory supervisor's and the operator's, are
                 not read

A role the package does not list keeps its files as they were: it left the
register between its last file and the package, and no end date is written.
A line the package repeats (same key) is one row; the file's own line count,
put in the header's `runs`, makes read.py log the repeats as folded.

Two files the export never carried are read from the package alone (2 November
2026, Arthur: "alright do it"):

  insolvencies   companies_insolvency.csv: one line per appointment in a
                 company's liquidation, receivership or voluntary
                 administration: the type, its start, the appointment's basis,
                 the appointee (an insolvency practitioner acting in that
                 office, or the Official Assignee) and the firm, appointed and
                 vacated, and whether the liquidation followed a resolution of
                 solvency. The file carries no address
  villages       retirement_villages_core_data.csv's operator (name and
                 company number) and statutory supervisor (name and day
                 appointed). Never the supervisor's, the operator's or the
                 premises' address

    PACKAGES                          {label: (name, sha256, received at, cut)}
    package_lines(zip_bytes, part)    the package's lines in the export's shape, with their places
    merge(part, header, lines, package_bytes, package_sha, label)    (header, lines)
    insolvency_lines(zip_bytes, label, sha) / village_lines(...)    (line count, lines) of the two package-only files
"""
import csv
import datetime as dt
import io
import zipfile

#: label → (the zip's name, its sha256, when it was received, the file's own date). The zip is the document.
PACKAGES = {
    "companies-2026-10": ("Companies Office Bulk Data October 2026.zip",
                          "99e9ede0dbcb5a168196546fe23246d44f4c570633d14e35f9604aee0aa37051",
                          "2026-11-02T10:00:11+13:00", "2026-10-01"),
}
NOTE = "read from the Companies Office's monthly package"

#: the old loader's shareholder types (nzbn_canonical importers/shareholders.py), so a holding reads the same either way
SH_TYPES = {"individual": "individual", "shareholder": "individual", "shareholder individual": "individual",
            "shareholder company": "company", "company": "company"}
#: the other bodies: CSV → (register, number column)
OTHER = {
    "other_incorporated_entities_core_data.csv": ("other_incorporated", "INCORPORATION_NUMBER"),
    "charitable_trust_boards_core_data.csv": ("charitable_trust_board", "INCORPORATION_NUMBER"),
    "public_sector_entities_core_data.csv": ("public_sector", None),
    "retirement_villages_core_data.csv": ("retirement_village", "ENTITY_NUMBER"),
}
_EXTRA = ("incorporated_societies_act", "incsoc2022act_reregistration_date", "charities_register_number")
_RO = ("REGISTERED_OFFICE_ADDRESS_CARE_OF", "REGISTERED_OFFICE_ADDRESS_1", "REGISTERED_OFFICE_ADDRESS_2",
       "REGISTERED_OFFICE_ADDRESS_3", "REGISTERED_OFFICE_ADDRESS_4", "REGISTERED_OFFICE_ADDRESS_POSTCODE",
       "REGISTERED_OFFICE_ADDRESS_COUNTRY")
_RO_LINE = ("REGISTERED_OFFICE_ADDRESS_CARE_OF", "REGISTERED_OFFICE_ADDRESS_LINE_1",
            "REGISTERED_OFFICE_ADDRESS_LINE_2", "REGISTERED_OFFICE_ADDRESS_LINE_3",
            "REGISTERED_OFFICE_ADDRESS_LINE_4", "REGISTERED_OFFICE_ADDRESS_POSTCODE")
#: registered offices, by CSV: (register, number column, the seven columns as capture.ADDRESS_FIELDS orders them)
ADDRESSES = {
    "companies_registered_office_address.csv": ("companies", None, _RO),
    "other_incorporated_entities_core_data.csv": ("other_incorporated", "INCORPORATION_NUMBER",
                                                  _RO_LINE + ("REGISTERED_OFFICE_ADDRESS_COUNTRY",)),
    "charitable_trust_boards_core_data.csv": ("charitable_trust_board", "INCORPORATION_NUMBER",
                                              _RO_LINE + ("REGISTERED_OFFICE_ADDRESS_COUNTRY_CODE",)),
    "retirement_villages_core_data.csv": ("retirement_village", "ENTITY_NUMBER", (None,) + _RO[1:6] + (None,)),
}
ADDRESS_FIELDS = ("care_of", "line_1", "line_2", "line_3", "line_4", "postcode", "country")
_STATE = ("name", "status", "type", "registered_on", "removed_on")


def _v(s):
    s = (s or "").strip()
    return s or None


def iso(raw):
    """dd/mm/yyyy (the CSVs' form, as the old loader parsed it) → yyyy-mm-dd; another form as it stands."""
    s = _v(raw)
    if s is None:
        return None
    try:
        return dt.datetime.strptime(s, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return s


def shares(raw):
    """Shares as one string either side: '100', '2.5'."""
    s = _v(str(raw) if raw is not None else None)
    if s is None:
        return None
    try:
        f = float(s.replace(",", ""))
    except ValueError:
        return s
    return str(int(f)) if f == int(f) else repr(f)


INSOLVENCY_CSV = "companies_insolvency.csv"
VILLAGES_CSV = "retirement_villages_core_data.csv"


def day(raw):
    """dd/mm/yyyy or dd-mm-yyyy (the villages' form) → yyyy-mm-dd; None for empty; another form as it stands."""
    s = _v(raw)
    if s is None:
        return None
    for f in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(s, f).date().isoformat()
        except ValueError:
            pass
    return s


def insolvency_lines(data: bytes, label: str, sha: str) -> list:
    """Every appointment line of companies_insolvency.csv, each with `_doc` and `_place`. Appointee names are read as
    filed: a practitioner in office (or the Official Assignee); the file carries no address."""
    z = zipfile.ZipFile(io.BytesIO(data))
    out = []
    for n, r in csv_rows(z, INSOLVENCY_CSV):
        first, middle, last = _v(r.get("APPOINTEE_FIRST_NAME")), _v(r.get("APPOINTEE_MIDDLE_NAMES")), _v(r.get("APPOINTEE_LAST_NAME"))
        out.append({"nzbn": _v(r.get("NZBN")), "entity_name": _v(r.get("ENTITY_NAME")),
                    "insolvency_type": _v(r.get("INSOLVENCY_TYPE")), "started_on": day(r.get("START_DATE")),
                    "appointment_type": _v(r.get("APPOINTMENT_TYPE")), "appointee_first_name": first,
                    "appointee_middle_names": middle, "appointee_last_name": last,
                    "appointee": " ".join(x for x in (first, middle, last) if x) or None,
                    "organisation": _v(r.get("ORGANISATION")), "appointed_on": day(r.get("APPOINTMENT_DATE")),
                    "vacated_on": day(r.get("APPOINTMENT_VACATED_DATE")),
                    # the file's own header spells it RESSOLUTION_OF_SOLVENCY
                    "resolution_of_solvency": (_v(r.get("RESSOLUTION_OF_SOLVENCY") or r.get("RESOLUTION_OF_SOLVENCY")) or "").upper() == "Y",
                    "last_file": label, "_doc": sha, "_place": f"{INSOLVENCY_CSV} line {n}", "_note": NOTE})
    return out


def village_lines(data: bytes, label: str, sha: str) -> list:
    """Each village's operator and statutory supervisor; the three address blocks are never read."""
    z = zipfile.ZipFile(io.BytesIO(data))
    out = []
    for n, r in csv_rows(z, VILLAGES_CSV):
        out.append({"number": _v(r.get("ENTITY_NUMBER")), "name": _v(r.get("ENTITY_NAME")),
                    "status": _v(r.get("ENTITY_STATUS")), "operator_name": _v(r.get("OPERATOR_NAME")),
                    "operator_number": _v(r.get("OPERATOR_NUMBER")),
                    "supervisor_name": _v(r.get("STATUTORY_SUPERVISOR_NAME")),
                    "supervisor_appointed_on": day(r.get("STATUTORY_SUPERVISOR_DATE_APPOINTED")),
                    "last_file": label, "_doc": sha, "_place": f"{VILLAGES_CSV} line {n}", "_note": NOTE})
    return out


def csv_rows(z: zipfile.ZipFile, name: str):
    """(line number, row) for each data line of one CSV in the package; line 1 is the header."""
    with z.open(name) as f:
        for n, row in enumerate(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", newline="")), 2):
            yield n, row


def director_key(nzbn, first, middle, last, start) -> tuple:
    return (nzbn, _v(first), _v(middle), _v(last), iso(start))


def holding_key(nzbn, name, n, status) -> tuple:
    return (nzbn, _v(name), shares(n), (_v(status) or "").lower() or None)


def address_key(register, nzbn, number, start, fields: dict) -> tuple:
    return (register, nzbn, number, iso(start)) + tuple((_v(fields.get(k)) or "").upper() for k in ADDRESS_FIELDS[:6])


def package_lines(data: bytes, part: str, label: str, sha: str):
    """The package's lines for one part, in the export's shape, each with `_doc` and `_place`."""
    z = zipfile.ZipFile(io.BytesIO(data))
    here = lambda name, n: {"_doc": sha, "_place": f"{name} line {n}", "_note": NOTE}
    if part == "entities":
        name = "companies_core_data.csv"
        for n, r in csv_rows(z, name):
            yield {"t": "entity", "register": "companies", "nzbn": _v(r["NZBN"]), "number": _v(r["COMPANY_IDENTIFIER"]),
                   "name": _v(r["ENTITY_NAME"]), "type": _v(r["ENTITY_TYPE"]), "status": _v(r["ENTITY_STATUS"]),
                   "registered_on": iso(r["REGISTRATION_DATE"]), "removed_on": iso(r["REMOVAL_DATE"]),
                   "files": [label], "last_file": label, **here(name, n)}
        for name, (register, num) in OTHER.items():
            for n, r in csv_rows(z, name):
                yield {"t": "entity", "register": register, "nzbn": _v(r.get("NZBN")),
                       "number": _v(r.get(num)) if num else None, "name": _v(r.get("ENTITY_NAME")),
                       "type": _v(r.get("ENTITY_TYPE")), "status": _v(r.get("ENTITY_STATUS")),
                       "registered_on": _v(r.get("REGISTRATION_DATE")), "removed_on": _v(r.get("DEREGISTRATION_DATE")),
                       "files": [], "last_file": label, "in_latest": True,
                       "extra": {k: _v(r.get(k.upper())) for k in _EXTRA if _v(r.get(k.upper()))}, **here(name, n)}
    elif part == "directors":
        name = "companies_director.csv"
        for n, r in csv_rows(z, name):
            first, middle, last = _v(r["FIRST_NAME"]), _v(r["MIDDLE_NAMES"]), _v(r["LAST_NAME"])
            yield {"t": "director", "nzbn": _v(r["NZBN"]), "number": None, "first_name": first, "middle_names": middle,
                   "last_name": last, "full_name": " ".join(x for x in (first, middle, last) if x) or None,
                   "role_type": "DIRECTOR", "appointed_on": iso(r["START_DATE"]), "suppressed": False,
                   "files": [label], "last_file": label, **here(name, n)}
    elif part == "shareholders":
        name = "companies_shareholder.csv"
        for n, r in csv_rows(z, name):      # the holder's address columns are never read
            kind = SH_TYPES.get((r["SH_TYPE"] or "").strip().lower(), "individual")
            holder = _v(r["SH_NAME"])
            yield {"t": "shareholder", "nzbn": _v(r["NZBN"]), "number": None, "shareholder_type": kind,
                   "full_name": holder if kind == "individual" else None,
                   "shareholder_entity_name": holder if kind == "company" else None, "shareholder_nzbn": None,
                   "shares": shares(r["NUMBER_OF_SHARES"]), "allocation_type": _v(r["SH_STATUS"]), "suppressed": False,
                   "files": [label], "last_file": label, **here(name, n)}
    elif part == "addresses":
        for name, (register, num, cols) in ADDRESSES.items():
            for n, r in csv_rows(z, name):
                yield {"t": "registered_office", "register": register, "nzbn": _v(r.get("NZBN")),
                       "number": _v(r.get(num)) if num else None, "start": _v(r.get("START_DATE")),
                       **{ADDRESS_FIELDS[i]: (_v(r.get(c)) if c else None) for i, c in enumerate(cols)},
                       "last_file": label, "in_latest": True, **here(name, n)}
    else:
        raise ValueError(f"no part {part}")


def _ekey(line) -> tuple:
    return (line.get("register") or "companies", line.get("nzbn") or None,
            None if line.get("nzbn") else line.get("number"))


def _rkey(part, line) -> tuple:
    if part == "directors":
        return director_key(line.get("nzbn"), line.get("first_name"), line.get("middle_names"), line.get("last_name"),
                            line.get("appointed_on"))
    if part == "shareholders":
        return holding_key(line.get("nzbn"), line.get("full_name") or line.get("shareholder_entity_name"),
                           line.get("shares"), line.get("allocation_type"))
    return address_key(line.get("register") or "companies", line.get("nzbn"),
                       None if line.get("nzbn") else line.get("number"), line.get("start"), line)


def _comparable(line, k):
    v = line.get(k)
    return iso(v) if k.endswith("_on") else _v(v)


def merge(part: str, header: dict, lines, data: bytes, sha: str, label: str):
    """(header, lines): the export's lines for `part` with the package `label` laid over them.
    `lines` yields (line number, object) as read.lines_of does; the package's own lines come
    after, numbered on from the export's last."""
    new = {}                 # key → the package's first line for it
    counts = {"entities": 0, "directors": 0, "shareholders": 0}
    repeats = {}
    for line in package_lines(data, part, label, sha):
        if part in ("entities", "directors", "shareholders") and line.get("register", "companies") == "companies":
            counts[part] += 1
        k = _ekey(line) if part == "entities" else _rkey(part, line)
        if k in new:
            repeats[k] = repeats.get(k, 0) + 1
            continue
        new[k] = line
    head = dict(header)
    head["files"] = list(header["files"]) + [label]
    head["runs"] = {**header["runs"], label: {**counts, "package": sha}}
    return head, _merged(part, lines, new, repeats, label)


def _merged(part, lines, new, repeats, label):
    last_n = 0
    for n, line in lines:
        last_n = n
        k = _ekey(line) if part == "entities" else _rkey(part, line)
        got = new.pop(k, None)
        if got is None:
            if line.get("in_latest") and line.get("last_file") != label:
                line = {**line, "in_latest": False}          # a body or office the package no longer lists
            yield n, line
            continue
        if part == "entities":
            out = {**line, **{f: got.get(f) for f in ("number", "name", "type", "status", "registered_on",
                                                      "removed_on", "extra") if f in got},
                   "last_file": label, "_doc": got["_doc"], "_place": got["_place"], "_note": got["_note"]}
            if line.get("register", "companies") == "companies":
                out["files"] = list(line.get("files") or []) + [label]
            else:
                out["in_latest"] = True
            if any(_comparable(line, k2) != _comparable(got, k2) for k2 in _STATE):
                out["earlier"] = list(line.get("earlier") or []) + [{
                    "file": line.get("last_file"), "name": line.get("name"), "status": line.get("status"),
                    "type": line.get("type"), "registered_on": line.get("registered_on"),
                    "removed_on": line.get("removed_on")}]
            if repeats.get(k) and line.get("register", "companies") != "companies":
                out["also"] = repeats[k]
            yield n, out
        elif part in ("directors", "shareholders"):
            out = {**line, "files": list(line.get("files") or []) + [label], "last_file": label,
                   "suppressed": bool(line.get("suppressed")), "_doc": got["_doc"], "_place": got["_place"],
                   "_note": got["_note"]}
            yield n, out
        else:
            yield n, {**line, "in_latest": True, "last_file": label, "_doc": got["_doc"], "_place": got["_place"],
                      "_note": got["_note"]}
    for i, (k, line) in enumerate(new.items(), 1):
        if part == "entities" and repeats.get(k) and line.get("register") != "companies":
            line = {**line, "also": repeats[k]}
        yield last_n + i, line
