"""The reading: the listed CSV files → one row per award notice and one per
supplier named on a notice, each stamped with its reader, its profile and
version, and read from text. Nothing here calls a model.

Each file is recognised by its header line (its profile's `recognise`)
before a field is read; a file no profile recognises is set aside whole.
The ministry's files mix encodings, so each field is decoded on its own:
UTF-8, else Windows-1252, else Latin-1, each fallback counted in the notes.

  notices    one per record of a notices file, keyed by the era and GETS's
             own RFx ID; the regions and categories as published gathered
             onto it, in file order; the award date and value as published
             (a `0` amount is kept as published and is not a value; the
             historic file has no amount column)
  suppliers  one per record of a supplier file: the name and the business-
             number field as published, the NZBN only where that field is a
             valid 13-digit one, the country. The address and website
             columns are never read (hard limit 15)

Items in equal items out plus items set aside, file by file: every record is
a row, a counted note (an empty or NULL region), or a catch-log line. A
reading that does not reconcile raises and publishes nothing.

    recognise(data)                               the profile slug, or None
    records(data)                                 (header, [(record no, fields)], notes)
    read(files, only=None)                        Result
"""
import collections
import csv
import datetime as dt
import hashlib
import io
import os
import re
from dataclasses import dataclass, field

from keys.dates import filed_date
from keys.numbers import nzbn as nzbn_ok
from support import profiles

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profiles-proposed.jsonl")
READER = "registers.tenders.read 1"
LICENCE = "CC BY 3.0 NZ"
LICENCE_URL = "https://creativecommons.org/licenses/by/3.0/nz/"
ATTRIBUTION = ("Source: Ministry of Business, Innovation and Employment, New Zealand Government procurement award "
               "notices (GETS open data), licensed under CC BY 3.0 NZ")
#: (set, era) → the profile that must recognise its file
PROFILE_OF = {("notices", "current"): "gets-award-notices-current",
              ("notices", "historic"): "gets-award-notices-historic",
              ("suppliers", "current"): "gets-supplier-data", ("suppliers", "historic"): "gets-supplier-data",
              ("regions", "current"): "gets-region-by-tender", ("regions", "historic"): "gets-region-by-tender",
              ("categories", "current"): "gets-product-categories",
              ("categories", "historic"): "gets-product-categories"}
SETS = ("notices", "suppliers", "regions", "categories")
ERAS = ("historic", "current")
NONE_WORDS = ("", "null")
_EXPONENT = re.compile(r"^\d(?:\.\d+)?e\+?\d+$", re.I)
_DIGITS = re.compile(r"^\d+$")
_YMD = re.compile(r"^(\d{4})(\d{2})(\d{2})$")


@dataclass
class Result:
    notices: list = field(default_factory=list)
    suppliers: list = field(default_factory=list)
    ledger: list = field(default_factory=list)       # one per file read
    set_aside: list = field(default_factory=list)
    notes: collections.Counter = field(default_factory=collections.Counter)


def profile(slug: str) -> dict:
    """The ledger's newest version; until the integrator appends them, the
    lane's proposed lines (merge request tenders-1)."""
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return p


def short(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


# ── bytes → fields ────────────────────────────────────────────────────────────

def _field(s: str, notes) -> str:
    """One field decoded on its own: UTF-8 as read, else its bytes as
    Windows-1252, else Latin-1 (which maps every byte)."""
    if not any(0xDC80 <= ord(c) <= 0xDCFF for c in s):
        return s
    raw = s.encode("utf-8", "surrogateescape")
    try:
        out = raw.decode("cp1252")
        notes["a field read as Windows-1252"] += 1
    except UnicodeDecodeError:
        out = raw.decode("latin-1")
        notes["a field read as Latin-1"] += 1
    return out


def records(data: bytes, notes=None):
    """(header, [(record number from 1, fields)]). Quoted line breaks stay in
    their field; a record number is the record's place after the header."""
    notes = notes if notes is not None else collections.Counter()
    text = data.decode("utf-8", "surrogateescape")
    if text.startswith("﻿"):
        text = text[1:]
    rows = csv.reader(io.StringIO(text, newline=""))
    try:
        header = [_field(h, notes) for h in next(rows)]
    except StopIteration:
        return [], []
    out = []
    for n, r in enumerate(rows, 1):
        out.append((n, [_field(f, notes) for f in r]))
    return header, out


def header_of(data: bytes) -> list:
    """The header line alone, measured without reading a record."""
    first = data.split(b"\n", 1)[0].rstrip(b"\r")
    if first.startswith(b"\xef\xbb\xbf"):
        first = first[3:]
    try:
        return next(csv.reader([first.decode("utf-8", "replace")]))
    except StopIteration:
        return []


def recognise(data: bytes, candidates=None):
    """The profile whose header the file's header line is, exactly; None
    when no profile recognises it (a challenge page, another layout)."""
    head = header_of(data)
    for slug in candidates or sorted(set(PROFILE_OF.values())):
        r = profile(slug).get("recognise") or {}
        if r.get("kind") == "csv" and head == r.get("header_exact") and len(head) == r.get("columns"):
            return slug
    return None


# ── fields → values ───────────────────────────────────────────────────────────

def text(v):
    v = (v or "").strip()
    return v or None


def date_of(raw: str, era: str, notes, what: str):
    """A date as published: day first in the current file, yyyymmdd in the
    historic; one that is not a real day is left empty and counted."""
    s = (raw or "").strip()
    if not s:
        return None
    if era == "historic":
        m = _YMD.match(s)
        d = None
        if m:
            try:
                d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                d = None
    else:
        d = filed_date(s) if "/" in s else None
    if d is None:
        notes[f"{what} not a real day in the {era} file: left empty"] += 1
        return None
    return d.isoformat()


def report_date(raw: str):
    m = _YMD.match((raw or "").strip())
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def value_of(raw, era: str):
    """(amount as published, value in dollars or None, the note)."""
    if era == "historic":
        return None, None, "the historic file has no amount column"
    s = (raw or "").strip()
    if not s:
        return None, None, "no amount published"
    if not _DIGITS.match(s):
        return s, None, "not a whole-dollar figure: kept as published"
    if int(s) == 0:
        return s, None, "0 as published: no value given"
    return s, int(s), "published"


def nzbn_form(raw: str) -> tuple:
    """(nzbn or None, the shape of the field as published)."""
    s = (raw or "").strip()
    if s.lower() in NONE_WORDS:
        return None, "empty" if not s else "NULL"
    n = nzbn_ok(s) if _DIGITS.match(s) else None
    if n:
        return n, "nzbn"
    if _EXPONENT.match(s):
        return None, "exponent form: digits lost"
    if _DIGITS.match(s):
        return None, f"{len(s)} digits" + (", check digit fails" if len(s) == 13 else "")
    return None, "other"


def cite(sha: str, n: int, slug: str, version: int) -> dict:
    return {"document": sha, "page": 1, "place": f"record {n}", "read_from": "text", "reader": READER,
            "profile": slug, "profile_version": version}


def aside(set_name, era, sha, n, stage, reason):
    return {"set_name": set_name, "era": era, "document": sha, "place": f"record {n}" if n else "whole file",
            "stage": stage, "reason": reason}


# ── the reading ───────────────────────────────────────────────────────────────

def _open(set_name, era, sha, data, out: Result):
    """(slug, version, column index, records) for a file, or None when its
    profile does not recognise it (the whole file set aside)."""
    want = PROFILE_OF[(set_name, era)]
    slug = recognise(data, [want])
    if slug is None:
        out.set_aside.append(aside(set_name, era, sha, None, "recognise",
                                   f"the file's header is not the `{want}` layout: nothing read from it"))
        out.ledger.append({"document": sha, "set_name": set_name, "era": era, "profile": None, "records": 0,
                           "typed": 0, "set_aside": 0, "skipped": 0, "report_date": None})
        return None
    header, recs = records(data, out.notes)
    col = {h: i for i, h in enumerate(header)}
    return slug, int(profile(slug)["version"]), col, recs


def read(files: dict, only: dict = None) -> Result:
    """`files`: (set, era) → (sha256, bytes). `only`: era → the RFx IDs to
    read (the sample's); None for every record. A record outside `only` is
    counted as skipped in the ledger, never as read."""
    out = Result()
    pick = (lambda era, rfx: True) if only is None else (lambda era, rfx: rfx in only.get(era, ()))
    by_key = {}
    for era in ERAS:
        if ("notices", era) not in files:
            continue
        sha, data = files[("notices", era)]
        opened = _open("notices", era, sha, data, out)
        if opened is None:
            continue
        slug, ver, col, recs = opened
        led = {"document": sha, "set_name": "notices", "era": era, "profile": slug, "records": len(recs),
               "typed": 0, "set_aside": 0, "skipped": 0, "report_date": None}
        seen, reports = set(), collections.Counter()
        g = lambda f, name: f[col[name]] if name in col and col[name] < len(f) else ""
        for n, f in recs:
            rfx = text(g(f, "RFx ID"))
            if not pick(era, rfx):
                led["skipped"] += 1
                continue
            if len(f) != len(col):
                out.set_aside.append(aside("notices", era, sha, n, "read", f"{len(f)} fields, the layout has {len(col)}"))
                led["set_aside"] += 1
                continue
            if rfx is None:
                out.set_aside.append(aside("notices", era, sha, n, "key", "no RFx ID"))
                led["set_aside"] += 1
                continue
            if rfx in seen:
                out.set_aside.append(aside("notices", era, sha, n, "key", "the RFx ID repeats an earlier record of the file"))
                led["set_aside"] += 1
                continue
            seen.add(rfx)
            amount, value, note = value_of(g(f, "Awarded Amount") if "Awarded Amount" in col else None, era)
            rd = report_date(g(f, "Report Date"))
            reports[rd] += 1
            row = {"key": f"tenders/{era}/{rfx}", "rfx_id": rfx, "era": era,
                   "posting_agency": text(g(f, "Posting Agency")), "department": text(g(f, "Department")),
                   "rfx_type": text(g(f, "RFx Type")), "competition_type": text(g(f, "Competition Type")),
                   "tender_coverage": text(g(f, "Tender Coverage")),
                   "prequalification_required": text(g(f, "Prequalification Required?")),
                   "title": text(g(f, "Title")), "reference_number": text(g(f, "Reference Number")),
                   "opened_on": date_of(g(f, "Open Date"), era, out.notes, "an open date"),
                   "closed_on": date_of(g(f, "Close Date"), era, out.notes, "a close date"),
                   "awarded_on": date_of(g(f, "Awarded Date "), era, out.notes, "an award date"),
                   "award_type": text(g(f, "Award Type")), "awarded_amount_as_published": amount,
                   "value_nzd": value, "value_note": note, "regions": [], "categories": [], "suppliers_named": 0,
                   "report_date": rd, **cite(sha, n, slug, ver)}
            out.notices.append(row)
            by_key[row["key"]] = row
            led["typed"] += 1
        led["report_date"] = reports.most_common(1)[0][0] if reports else None
        out.ledger.append(led)

    for set_name in ("suppliers", "regions", "categories"):
        for era in ERAS:
            if (set_name, era) not in files:
                continue
            sha, data = files[(set_name, era)]
            opened = _open(set_name, era, sha, data, out)
            if opened is None:
                continue
            slug, ver, col, recs = opened
            led = {"document": sha, "set_name": set_name, "era": era, "profile": slug, "records": len(recs),
                   "typed": 0, "set_aside": 0, "skipped": 0, "report_date": None}
            reports, repeats = collections.Counter(), collections.Counter()
            g = lambda f, name: f[col[name]] if col[name] < len(f) else ""
            for n, f in recs:
                rfx = text(g(f, "RFx ID"))
                if not pick(era, rfx):
                    led["skipped"] += 1
                    continue
                if len(f) != len(col):
                    out.set_aside.append(aside(set_name, era, sha, n, "read", f"{len(f)} fields, the layout has {len(col)}"))
                    led["set_aside"] += 1
                    continue
                notice = by_key.get(f"tenders/{era}/{rfx}")
                if notice is None:
                    out.set_aside.append(aside(set_name, era, sha, n, "join",
                                               f"the RFx ID names no notice of the {era} notices file"))
                    led["set_aside"] += 1
                    continue
                reports[report_date(g(f, "Report Date"))] += 1
                if set_name == "suppliers":
                    name = text(g(f, "Business Name"))
                    raw = text(g(f, "Supplier NZBN"))
                    nz, form = nzbn_form(raw)
                    base = f"{notice['key']}/{short((name or '') + chr(31) + (raw or ''))}"
                    repeats[base] += 1
                    out.suppliers.append({
                        "key": base if repeats[base] == 1 else f"{base}/{repeats[base]}", "notice_key": notice["key"],
                        "rfx_id": rfx, "era": era, "business_name": name, "nzbn_as_published": raw, "nzbn": nz,
                        "nzbn_form": form, "country": None if (text(g(f, "Country")) or "").lower() == "null"
                        else text(g(f, "Country")), "report_date": report_date(g(f, "Report Date")),
                        **cite(sha, n, slug, ver)})
                    notice["suppliers_named"] += 1
                    if name is None:
                        out.notes["a supplier record with no business name: kept"] += 1
                elif set_name == "regions":
                    region = text(g(f, "Region"))
                    if (region or "").lower() in NONE_WORDS:
                        out.notes[f"a region record empty or NULL ({era}): no region kept"] += 1
                    elif region in notice["regions"]:
                        out.notes[f"a region named twice on one notice ({era}): kept once"] += 1
                    else:
                        notice["regions"].append(region)
                else:
                    notice["categories"].append({"code": text(g(f, "UNSPC Classification")),
                                                 "description": text(g(f, "UNSPC Description"))})
                led["typed"] += 1
            led["report_date"] = reports.most_common(1)[0][0] if reports else None
            out.ledger.append(led)
    for led in out.ledger:
        if led["typed"] + led["set_aside"] + led["skipped"] != led["records"]:
            raise AssertionError(f"tenders: {led['set_name']} {led['era']} {led['document'][:12]} does not reconcile")
    return out
