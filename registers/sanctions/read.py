"""The lane's reading of the three sanctions lists, each from its own
profile (proposed in `profile-proposed.jsonl`; the integrator appends them at
the merge). No model; nothing fetched.

Each document is first recognised by its shape (`recognise`); a document
that is not its profile's shape is set aside whole and nothing is read from
it. Then one row per listed person or entity per list (`Listing`), with the
list's own identifier, names and aliases as published, the designation's
date and basis, and the version of the list it came from.

What is never read: an individual's address beyond the country the list
names (the UN's `COUNTRY` element; Police's and MFAT's free-text addresses
are not read at all), passport and identity numbers, and the lists'
narrative comments. A list names people because a government or the
Security Council designated them; birth dates, nationalities and countries
of birth are read because they are how a reader tells a listed person from
someone else with the same name.

  un-sc          profile `un-sc-consolidated-list-xml`: INDIVIDUALS and
                 ENTITIES, keyed by REFERENCE_NUMBER (QDi.001)
  nz-police-tsa  profile `nz-police-designated-entities-workbook`: the
                 Individuals and Organisations sheets (UN-derived; an
                 integer ID is a listing, each decimal an alias of it), the
                 UNSCR 1373 sheet (New Zealand's own designations), and the
                 Revocations and UNSCR 1373 Expirations sheets (ended)
  mfat-russia    profile `mfat-russia-sanctions-register-workbook`: written
                 from a published description of the workbook, not from the
                 workbook (its automated download is barred); the first file
                 a person lands confirms it or a version 2 follows

Every line this module prints is a count.
"""
import collections
import datetime as dt
import hashlib
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

from registers.sanctions import workbook

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
READER = "registers.sanctions.read 1"
PROFILES = {"un-sc": "un-sc-consolidated-list-xml", "nz-police-tsa": "nz-police-designated-entities-workbook",
            "mfat-russia": "mfat-russia-sanctions-register-workbook"}
LISTS = {
    "un-sc": ("United Nations Security Council Consolidated List", "United Nations Security Council",
              "United Nations Act 1946 and the regulations made under it"),
    "nz-police-tsa": ("Designated terrorist entities", "New Zealand Police (for the Prime Minister)",
                      "Terrorism Suppression Act 2002"),
    "mfat-russia": ("Russia Sanctions Register", "Ministry of Foreign Affairs and Trade",
                    "Russia Sanctions Act 2022 and the Russia Sanctions Regulations 2022"),
}
POLICE_SHEETS = ("Individuals", "Organisations", "Revocations", "UNSCR 1373", "UNSCR 1373 Expirations")
POLICE_REGIME = {"TA": "Taliban (resolution 1988)", "QD": "ISIL (Da'esh) and Al-Qaida (resolutions 1267/1989/2253)"}
_DMY = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_STATED_1373 = re.compile(rb"currently has\s+(\d+)\s+non-UN listed entities", re.I)


def profile_version(list_id: str) -> int:
    from support import profiles
    slug = PROFILES[list_id]
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no profile {slug}: a reading is made from a profile (profiles before readers)")
    return int(p["version"])


def text(v):
    if v is None:
        return None
    s = re.sub(r"\s+", " ", str(v)).strip()
    return s or None


def once(values) -> list:
    out = []
    for v in values:
        v = text(v)
        if v and v not in out:
            out.append(v)
    return out


def iso(v):
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except (TypeError, ValueError):
        return None


def dmy(v):
    m = _DMY.search(v or "")
    if not m:
        return None
    try:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def all_dmy(v) -> list:
    out = []
    for m in _DMY.finditer(v or ""):
        try:
            out.append(dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))))
        except ValueError:
            pass
    return out


def cell_day(v):
    """A workbook cell as a day: a serial number, a dd/mm/yyyy, or an ISO day."""
    return workbook.serial_date(v) if re.fullmatch(r"\d+(\.\d+)?", str(v or "").strip()) else (dmy(v) or iso(v))


def cell_birth(v):
    """A birth date as the list gives it: a serial becomes a day; text stays as written ("1963 (Approx)")."""
    s = text(v)
    if s is None:
        return None
    if re.fullmatch(r"\d{4,5}(\.0+)?", s) and not re.fullmatch(r"(1[89]|20)\d\d", s):
        d = workbook.serial_date(s)
        return d.isoformat() if d else s
    return s


def listing(list_id, ref, kind, status, name, *, sha, place, version, list_version, **kw) -> dict:
    row = {"key": f"sanctions/{list_id}/{ref}", "list_id": list_id, "list_ref": ref, "other_ref": None, "kind": kind,
           "status": status, "name": name, "aliases": [], "original_script": None, "titles": [], "positions": [],
           "nationalities": [], "birth_dates": [], "birth_countries": [], "countries": [], "regime": None,
           "basis": "", "designated_on": None, "renewed_on": [], "expires_on": None, "ended_on": None,
           "updated_on": None, "list_version": list_version,
           "document": sha, "page": 1, "place": place, "read_from": "text", "reader": READER,
           "profile": PROFILES[list_id], "profile_version": version}
    row.update(kw)
    row["aliases"] = [a for a in once(row["aliases"]) if a != name]
    return row


def aside(list_id, sha, place, stage, reason) -> dict:
    return {"list_id": list_id, "document": sha, "place": place, "stage": stage, "reason": reason}


def result(list_id, stated=None, stated_where=None, version=None) -> dict:
    return {"list_id": list_id, "rows": [], "set_aside": [], "items": 0, "skipped": 0, "stated": stated,
            "stated_where": stated_where, "version": version}


# ── the UN's consolidated list (XML) ──────────────────────────────────────────

def recognise_un(body: bytes):
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None, "not XML"
    if root.tag != "CONSOLIDATED_LIST" or not root.get("dateGenerated"):
        return None, "not a CONSOLIDATED_LIST with a dateGenerated"
    if root.find("INDIVIDUALS") is None or root.find("ENTITIES") is None:
        return None, "no INDIVIDUALS or no ENTITIES"
    return root, ""


def _vals(el, path):
    return [v.text for v in el.findall(path) if v.text]


def read_un(body: bytes, sha: str, version: int) -> dict:
    root, why = recognise_un(body)
    if root is None:
        out = result("un-sc")
        out["set_aside"].append(aside("un-sc", sha, "document", "recognise", why))
        return out
    lv = root.get("dateGenerated")
    out = result("un-sc", version=lv)
    for section, tag, kind in (("INDIVIDUALS", "INDIVIDUAL", "individual"), ("ENTITIES", "ENTITY", "entity")):
        for i, e in enumerate(root.find(section).findall(tag)):
            out["items"] += 1
            ref = text(e.findtext("REFERENCE_NUMBER"))
            place = f"{section}/{tag}[{i + 1}]"
            if not ref:
                out["set_aside"].append(aside("un-sc", sha, place, "key", "no REFERENCE_NUMBER"))
                continue
            names = once(e.findtext(k) for k in ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME"))
            if not names:
                out["set_aside"].append(aside("un-sc", sha, place, "read", "no name"))
                continue
            al = e.findall(f"{tag}_ALIAS")
            births = []
            for b in e.findall("INDIVIDUAL_DATE_OF_BIRTH"):
                if b.findtext("DATE"):
                    births.append(b.findtext("DATE")[:10])
                elif b.findtext("YEAR"):
                    births.append(b.findtext("YEAR"))
                elif b.findtext("FROM_YEAR"):
                    births.append(f"{b.findtext('FROM_YEAR')}-{b.findtext('TO_YEAR') or ''}")
            regime = text(e.findtext("UN_LIST_TYPE"))
            updated = sorted(d for d in (iso(v) for v in _vals(e, "LAST_DAY_UPDATED/VALUE")) if d)
            out["rows"].append(listing(
                "un-sc", ref, kind, "designated", " ".join(names), sha=sha, place=f"REFERENCE_NUMBER={ref}",
                version=version, list_version=lv,
                aliases=[a.findtext("ALIAS_NAME") for a in al], original_script=text(e.findtext("NAME_ORIGINAL_SCRIPT")),
                titles=once(_vals(e, "TITLE/VALUE")), positions=once(_vals(e, "DESIGNATION/VALUE")),
                nationalities=once(_vals(e, "NATIONALITY/VALUE")), birth_dates=once(births),
                birth_countries=once(p.findtext("COUNTRY") for p in e.findall("INDIVIDUAL_PLACE_OF_BIRTH")),
                countries=once(a.findtext("COUNTRY") for a in e.findall(f"{tag}_ADDRESS")),
                regime=regime, designated_on=iso(e.findtext("LISTED_ON")), updated_on=updated[-1] if updated else None,
                basis=(f"UN Security Council {regime} sanctions list, as the UN publishes it; given effect in New "
                       "Zealand under the United Nations Act 1946 and its regulations")))
    return out


# ── the Police workbook ───────────────────────────────────────────────────────

def police_id(v):
    """(base, alias number) from an ID cell: '3', '3.01', '2.0099999999999998', '913. 00'. None if not an ID."""
    s = re.sub(r"\s+", "", str(v or ""))
    if not re.fullmatch(r"\d+(\.\d*)?", s):
        return None
    try:
        d = Decimal(s)
    except InvalidOperation:
        return None
    base = int(d)
    return base, int(((d - base) * 100).quantize(Decimal(1)))


def recognise_police(body: bytes):
    try:
        sheets = dict(workbook.sheets(body))
    except (zipfile.BadZipFile, KeyError, ET.ParseError):
        return None, "not a workbook"
    missing = [s for s in POLICE_SHEETS if s not in sheets]
    if missing:
        return None, f"no sheet {', '.join(missing)}"
    head = lambda s: [text(v) or "" for _, v in sorted(sheets[s].get(1, {}).items())]
    if not {"ID", "LastName", "Name_1"} <= set(head("Individuals")) or "Sanctions_List_Permanent_Reference_Numbe" not in "|".join(head("Individuals")):
        return None, "the Individuals sheet's header is not the profile's"
    if not {"ID", "Name"} <= set(head("Organisations")) or "NZ UNSCR 1373 ID CODE" not in head("UNSCR 1373"):
        return None, "the Organisations or UNSCR 1373 header is not the profile's"
    return sheets, ""


def _groups(rows: dict, first_row: int = 2):
    """Sheet rows grouped by ID base, in order; (base, [(sub, row number, cells)]) and rows that are not IDs."""
    groups, odd = collections.OrderedDict(), []
    for r in sorted(rows):
        if r < first_row:
            continue
        cells = rows[r]
        pid = police_id(cells.get(1))
        if pid is None:
            odd.append((r, cells))
            continue
        groups.setdefault(pid[0], []).append((pid[1], r, cells))
    return groups, odd


def _primary(members):
    members = sorted(members)
    return members[0]


def read_police(body: bytes, sha: str, version: int, list_version: str = None, page_1373: bytes = None) -> dict:
    sheets, why = recognise_police(body)
    stated = None
    if page_1373:
        m = _STATED_1373.search(page_1373)
        stated = int(m.group(1)) if m else None
    out = result("nz-police-tsa", stated=stated, stated_where="the Resolution 1373 page: 'currently has N non-UN listed entities'"
                 if stated is not None else None, version=list_version)
    if sheets is None:
        out["set_aside"].append(aside("nz-police-tsa", sha, "document", "recognise", why))
        return out
    seen = set()

    def add(row):
        if row["key"] in seen:
            out["set_aside"].append(aside("nz-police-tsa", sha, row["place"], "key",
                                          f"the list's identifier {row['list_ref']} is listed twice"))
            return
        seen.add(row["key"])
        out["rows"].append(row)

    def person_name(c, last=2, given=(3, 4, 5, 6)):
        g = " ".join(text(c.get(k)) for k in given if text(c.get(k)))
        return text(f"{g} {text(c.get(last)) or ''}")

    # the UN-derived individuals and organisations (current)
    for sheet, kind in (("Individuals", "individual"), ("Organisations", "entity")):
        groups, odd = _groups(sheets[sheet])
        out["items"] += len(groups) + len(odd)          # an ID and its decimal aliases are one item
        out["skipped"] += len(odd)
        for base, members in groups.items():
            sub, r, c = _primary(members)
            if kind == "individual":
                nm, ref = person_name(c), text(c.get(51))
                al = [person_name(m[2]) for m in members if m is not (sub, r, c)]
                extra = dict(titles=once([c.get(7)]), birth_dates=once(cell_birth(c.get(k)) for k in range(18, 27)),
                             birth_countries=once(c.get(k) for k in (9, 11, 13, 15, 17)),
                             nationalities=once(c.get(k) for k in (27, 28, 29)), designated_on=cell_day(c.get(49)),
                             updated_on=(all_dmy(c.get(50)) or [None])[-1])
            else:
                nm, ref = text(c.get(2)), text(c.get(23))
                al = [text(m[2].get(2)) for m in members if m is not (sub, r, c)]
                extra = dict(designated_on=cell_day(c.get(21)), updated_on=(all_dmy(c.get(22)) or [None])[-1])
            place = f"{sheet}!row {r}"
            if not nm:
                out["set_aside"].append(aside("nz-police-tsa", sha, place, "read", "no name"))
                continue
            regime = POLICE_REGIME.get((ref or "")[:2].upper())
            add(listing("nz-police-tsa", f"{kind}/{base}", kind, "designated", nm, sha=sha, place=place, version=version,
                        list_version=list_version, other_ref=ref, aliases=al, regime=regime or "UN-listed (resolutions 1267/1989/2253 and 1988)",
                        basis="Terrorism Suppression Act 2002: a UN Security Council listing (resolutions "
                              "1267/1989/2253 and 1988) included as a designated terrorist entity", **extra))
    # New Zealand's own designations under resolution 1373: current, then expired
    for sheet, status in (("UNSCR 1373", "designated"), ("UNSCR 1373 Expirations", "expired")):
        groups, odd = _groups(sheets[sheet])
        out["items"] += len(groups) + len(odd)
        out["skipped"] += len(odd)
        for base, members in groups.items():
            sub, r, c = _primary(members)
            nm = text(c.get(2))
            place = f"{sheet}!row {r}"
            if not nm:
                out["set_aside"].append(aside("nz-police-tsa", sha, place, "read", "no name"))
                continue
            kind, births = "entity", []
            m = re.match(r"^(?P<name>.+?),\s*DOB\s+(?P<dob>.+)$", nm)
            if m:                                        # one individual is written "NAME, DOB 27 October 1990"
                kind, nm, births = "individual", m.group("name").strip(), [m.group("dob").strip()]
            al = [text(x[2].get(2)) for x in members if x is not (sub, r, c)] + [text(c.get(3))]
            add(listing("nz-police-tsa", f"1373/{base}", kind, status, nm, sha=sha, place=place, version=version,
                        list_version=list_version, aliases=[re.sub(r",\s*DOB\s+.+$", "", a or "") for a in al],
                        countries=once([c.get(4)]), birth_dates=births, regime="New Zealand designation (resolution 1373)",
                        basis="Terrorism Suppression Act 2002, s 22: designated by the Prime Minister (resolution 1373); "
                              "renewed under s 35", designated_on=cell_day(c.get(5)), renewed_on=all_dmy(c.get(6)),
                        expires_on=cell_day(c.get(7)) if status == "designated" else None,
                        ended_on=cell_day(c.get(7)) if status == "expired" else None))
    # revocations: an individuals section, then an organisations section, each headed by a one-cell row
    rv = sheets["Revocations"]
    groups, odd = collections.OrderedDict(), []
    kind = None
    for r in sorted(rv):
        c = rv[r]
        if r == 1:
            continue
        pid = police_id(c.get(1))
        if pid is None:
            if set(c) == {1}:
                kind = "entity" if "ORGANISATION" in c[1].upper() else "individual"
            else:
                out["items"] += 1
                out["skipped"] += 1
            continue
        groups.setdefault((kind, pid[0]), []).append((pid[1], r, c))
    out["items"] += len(groups)
    for (kind, base), members in groups.items():
        sub, r, c = _primary(members)
        place = f"Revocations!row {r}"
        if kind is None:
            out["set_aside"].append(aside("nz-police-tsa", sha, place, "read", "a revocation before any section heading"))
            continue
        nm = person_name(c) if kind == "individual" else text(c.get(2))
        if not nm:
            out["set_aside"].append(aside("nz-police-tsa", sha, place, "read", "no name"))
            continue
        al = [(person_name(m[2]) if kind == "individual" else text(m[2].get(2))) for m in members if m is not (sub, r, c)]
        ref = text(c.get(22))
        add(listing("nz-police-tsa", f"{kind}/{base}", kind, "revoked", nm, sha=sha, place=place, version=version,
                    list_version=list_version, other_ref=ref, aliases=al,
                    regime=POLICE_REGIME.get((ref or "")[:2].upper()) or "UN-listed (resolutions 1267/1989/2253 and 1988)",
                    basis="Terrorism Suppression Act 2002: a UN Security Council listing, revoked by the UN or New Zealand",
                    designated_on=cell_day(c.get(19)), ended_on=cell_day(c.get(21)),
                    nationalities=once(c.get(k) for k in (15, 16)) if kind == "individual" else []))
    return out


# ── MFAT's Russia sanctions register ──────────────────────────────────────────

MFAT_HEADER = ("Unique Identifier", "DOB")
MFAT_KINDS = {"individual": "individual", "indiividual": "individual", "entity": "entity", "bank": "entity"}
MFAT_COUNTED = ("asset", "total")


def recognise_mfat(body: bytes):
    try:
        sheets = workbook.sheets(body)
    except (zipfile.BadZipFile, KeyError, ET.ParseError):
        return None, "not a workbook"
    found = []
    for name, rows in sheets:
        for r in sorted(rows)[:30]:
            vals = {(text(v) or "").lower(): k for k, v in rows[r].items()}
            if all(h.lower() in vals for h in MFAT_HEADER) and "type" in vals:
                found.append((name, r, {h: k for h, k in vals.items()}, rows))
                break
    if not found:
        return None, "no sheet has a header row with 'Unique Identifier', 'DOB' and 'Type'"
    return found, ""


def read_mfat(body: bytes, sha: str, version: int, list_version: str = None) -> dict:
    found, why = recognise_mfat(body)
    out = result("mfat-russia", version=list_version)
    if found is None:
        out["set_aside"].append(aside("mfat-russia", sha, "document", "recognise", why))
        return out
    seen = collections.Counter()
    for name, hr, cols, rows in found:
        col = lambda c, h: text(c.get(cols.get(h.lower())))
        for r in sorted(rows):
            if r <= hr:
                continue
            c = rows[r]
            if not any(text(v) for v in c.values()):
                continue
            out["items"] += 1
            place = f"{name}!row {r}"
            typ = (col(c, "Type") or "").lower()
            if typ in MFAT_COUNTED:
                out["skipped"] += 1
                if typ == "total":
                    nums = [int(float(v)) for v in c.values() if re.fullmatch(r"\d+(\.0+)?", str(v).strip())]
                    if nums and out["stated"] is None:
                        out["stated"], out["stated_where"] = max(nums), f"the Total row ({place})"
                continue
            kind = MFAT_KINDS.get(typ)
            if kind is None:
                out["set_aside"].append(aside("mfat-russia", sha, place, "read", f"a Type the profile does not know: {typ[:40]!r}"))
                continue
            uid = col(c, "Unique Identifier")
            nm = text(" ".join(x for x in (col(c, "First name"), col(c, "Middle name(s)"), col(c, "Last name")) if x))
            if not uid or not nm:
                out["set_aside"].append(aside("mfat-russia", sha, place, "read", "no Unique Identifier" if not uid else "no name"))
                continue
            seen[uid] += 1
            ref = uid if seen[uid] == 1 else f"{uid}/{hashlib.sha256(nm.lower().encode()).hexdigest()[:8]}"
            status = (col(c, "Sanction Status") or "").lower()
            out["rows"].append(listing(
                "mfat-russia", ref, kind, "revoked" if "revok" in status else "designated", nm, sha=sha, place=place,
                version=version, list_version=list_version,
                aliases=[a for a in re.split(r";|,\s*(?=\S)", col(c, "Alias/Alternate Spellings") or "") if a.strip()],
                titles=once([col(c, "Title")]),
                nationalities=once(col(c, h) for h in ("Citizenship", "Citizenship 2", "Citizenship 3")),
                birth_dates=once([cell_birth(col(c, "DOB"))]) if kind == "individual" else [],
                regime=", ".join(h for h in ("Asset Freeze", "Travel Ban", "Service Prohibition", "Dealing with Securities",
                                             "Ship Ban", "Aircraft Ban") if (col(c, h) or "").lower() in ("yes", "y", "x", "true", "1")) or None,
                basis="Russia Sanctions Act 2022: designated in the Russia Sanctions Regulations 2022",
                designated_on=cell_day(col(c, "Date of Sanction")),
                updated_on=cell_day(col(c, "Date of Additional Sanction"))))
    return out


def read_document(list_id: str, body: bytes, sha: str, version: int, list_version: str = None, extra: bytes = None) -> dict:
    if list_id == "un-sc":
        return read_un(body, sha, version)
    if list_id == "nz-police-tsa":
        return read_police(body, sha, version, list_version, extra)
    if list_id == "mfat-russia":
        return read_mfat(body, sha, version, list_version)
    raise ValueError(f"no such list: {list_id}")


def main(argv=None) -> int:
    from support.docstore.landing import read_bytes
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: python -m registers.sanctions.read <list> <sha256>")
        return 2
    out = read_document(argv[0], read_bytes(argv[1]), argv[1], profile_version(argv[0]))
    c = collections.Counter((r["kind"], r["status"]) for r in out["rows"])
    print(f"sanctions: {argv[0]}: items {out['items']}, rows {len(out['rows'])} {dict(c)}, set aside "
          f"{len(out['set_aside'])}, counted not read {out['skipped']}, stated {out['stated']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
