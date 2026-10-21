"""The lane's reading of the NZBN register's answers for limited
partnerships, from profile `nzbn-limited-partnership-detail` (proposed in
`profile-proposed.jsonl`; the integrator appends it to support/profiles at
the merge). No model; nothing fetched.

An answer is first recognised by its shape (`recognise`): a JSON object
with a 13-digit `nzbn`, an `entityTypeCode` of `Y` (a New Zealand limited
partnership) or `Z` (an overseas one), a `roles` list and an
`addresses.addressList` list. An answer that is not that shape is set
aside whole, with the reason, and nothing is read from it.

Read from a recognised answer:

  partnership  one row: NZBN, the register's number, name (withheld where
               the register's privacy settings withhold it), kind, type,
               status, registration date, country of origin, and the
               CURRENT registered address (no end date) with its start date:
               a partnership's registered office is shown
  partners     one row per role of type `Partner` (a general partner, a
               person or a body as the register states it): the name, a
               body's NZBN, Active or Inactive, the role's own dates where
               the answer states them (it states none in every answer read
               so far, and the row says so), the register's suppression
  addresses    every address a partner's role carries, to the private twin
               only (a person's may be a home; hard limit 15)

A role of another type (a person authorised for service) is counted, not
read. A role with no name is set aside. E-mail addresses, phone numbers and
websites stay in the document and are never read.

Every line this module prints is a count.
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
PROFILE = "nzbn-limited-partnership-detail"
READER = "registers.limited_partnerships.read 1"
KEY_PREFIX = "limited_partnerships"
KINDS = {"Y": "nz", "Z": "overseas"}
PARTNER_ROLE = "Partner"


def profile_version() -> int:
    """The current version of the profile: support's ledger, else the
    lane's proposed line (until the integrator appends it)."""
    from support import profiles
    p = profiles.profile(PROFILE) or profiles.profile(PROFILE, path=PROPOSED)
    if p is None:
        raise LookupError(f"no profile {PROFILE}: a reading is made from a profile (profiles before readers)")
    return int(p["version"])


def recognise(body: bytes):
    """(answer, '') when the bytes are the profile's shape, else (None, why)."""
    try:
        j = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return None, "not JSON"
    if not isinstance(j, dict):
        return None, "not a JSON object"
    if not re.fullmatch(r"\d{13}", str(j.get("nzbn") or "")):
        return None, "no 13-digit nzbn"
    if j.get("entityTypeCode") not in KINDS:
        return None, f"entity type {j.get('entityTypeCode')!r} is not a limited partnership"
    if not isinstance(j.get("roles"), list):
        return None, "no roles list"
    if not isinstance((j.get("addresses") or {}).get("addressList"), list):
        return None, "no addresses.addressList list"
    return j, ""


def day(v):
    """The interface's stamp (2008-05-02T00:00:00.000+1200, New Zealand
    local) as its day: the first ten characters. None if absent or not a day."""
    if not v:
        return None
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def text(v):
    if v is None:
        return None
    s = re.sub(r"\s+", " ", str(v)).strip()
    return s or None


def address_text(a: dict):
    parts = [text(a.get(k)) for k in ("careOf", "address1", "address2", "address3", "address4", "postCode")]
    parts = [p for p in parts if p]
    if a.get("countryCode") and a.get("countryCode") != "NZ":
        parts.append(a["countryCode"])
    return ", ".join(parts) or None


def short(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def cite(sha: str, place: str, version: int) -> dict:
    return {"document": sha, "page": 1, "place": place, "read_from": "text", "reader": READER,
            "profile": PROFILE, "profile_version": version}


def read_answer(body: bytes, sha: str, asked_on: dt.date, version: int) -> dict:
    """One answer: {'partnership', 'partners', 'addresses', 'set_aside',
    'roles', 'other_roles'}. A body that is not the profile's shape gives
    no partnership and one catch-log line."""
    out = {"partnership": None, "partners": [], "addresses": [], "set_aside": [], "roles": 0, "other_roles": 0}
    j, why = recognise(body)
    if j is None:
        out["set_aside"].append({"document": sha, "place": "answer", "stage": "recognise", "reason": why})
        return out
    nzbn = j["nzbn"]
    pkey = f"{KEY_PREFIX}/{nzbn}"
    privacy = j.get("privacySettings") or {}
    withheld = bool(privacy.get("namePrivateInformation"))
    office, since = None, None
    current = [a for a in j["addresses"]["addressList"] if a.get("addressType") == "REGISTERED" and not a.get("endDate")]
    if current:
        current.sort(key=lambda a: str(a.get("startDate") or ""))
        office, since = address_text(current[-1]), day(current[-1].get("startDate"))
    ncd = j.get("non-company-details") or {}
    out["partnership"] = {
        "key": pkey, "nzbn": nzbn, "number": text(j.get("sourceRegisterUniqueIdentifier")),
        "name": None if withheld else text(j.get("entityName")), "name_withheld": withheld,
        "kind": KINDS[j["entityTypeCode"]], "entity_type": j["entityTypeCode"],
        "type_description": text(j.get("entityTypeDescription")), "status": text(j.get("entityStatusDescription")),
        "status_code": text(j.get("entityStatusCode")), "registered_on": day(j.get("registrationDate")),
        "country_of_origin": text(ncd.get("countryOfOrigin")), "registered_office": office, "office_since": since,
        "asked_on": asked_on, **cite(sha, "entity", version)}
    partners_private = bool(privacy.get("partnersPrivateInformation"))
    seen = set()
    for i, r in enumerate(j["roles"]):
        out["roles"] += 1
        place = f"roles[{i}]"
        if (r or {}).get("roleType") != PARTNER_ROLE:
            out["other_roles"] += 1
            continue
        person, body_ = r.get("rolePerson"), r.get("roleEntity")
        if person:
            first, middle, last = text(person.get("firstName")), text(person.get("middleNames")), text(person.get("lastName"))
            full = " ".join(p for p in (first, middle, last) if p) or None
            kind, body_nzbn = "person", None
        elif body_:
            first = middle = last = None
            full, kind, body_nzbn = text(body_.get("entityName")), "body", text(body_.get("nzbn"))
        else:
            full = None
        if not full:
            out["set_aside"].append({"document": sha, "place": place, "stage": "read", "reason": "a general partner with no name"})
            continue
        rid = text(r.get("uniqueIdentifier"))
        # the interface's identifier is not unique within an answer: two different bodies were answered under one
        # (9429043218851, 21 October 2026), so the key adds the partner's kind and name
        key = f"{pkey}/partner/{rid or '-'}/{short(kind + '|' + full.lower() + '|' + (body_nzbn or ''))}"
        if key in seen:
            out["set_aside"].append({"document": sha, "place": place, "stage": "key",
                                     "reason": "the same partner again under the same identifier"})
            continue
        seen.add(key)
        started, ended = day(r.get("startDate")), day(r.get("endDate"))
        suppressed = bool(r.get("suppressed") or (person or {}).get("suppressed") or partners_private)
        out["partners"].append({
            "key": key, "partnership_key": pkey, "nzbn": nzbn, "role_id": rid, "kind": kind, "full_name": full,
            "first_name": first, "middle_names": middle, "last_name": last, "body_nzbn": body_nzbn,
            "suppressed": suppressed, "current": r.get("roleStatus") == "Active", "status": text(r.get("roleStatus")),
            "started_on": started, "ended_on": ended, "dates_stated": bool(started or ended), "asked_on": asked_on,
            **cite(sha, place, version)})
        for k, a in enumerate(r.get("roleAddress") or []):
            t = address_text(a or {})
            if t:
                out["addresses"].append({"key": key, "address_type": text(a.get("addressType")), "address": t,
                                         "document": sha, "place": f"{place}.roleAddress[{k}]"})
    return out


def main(argv=None) -> int:
    """Read one held answer alone and print its counts."""
    from support.docstore.landing import read_bytes
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python -m registers.limited_partnerships.read <sha256>")
        return 2
    sha = argv[0]
    out = read_answer(read_bytes(sha), sha, dt.date.today(), profile_version())
    print(f"{KEY_PREFIX}: {sha[:12]}: partnership {1 if out['partnership'] else 0}, roles {out['roles']}, "
          f"general partners {len(out['partners'])}, other roles {out['other_roles']}, set aside {len(out['set_aside'])}, "
          f"private addresses {len(out['addresses'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
