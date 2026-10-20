"""The reading: the notices export → this lane's rows, each stamped with its
reader, its profile and version, and read from text. Nothing here calls a
model, so the fast tier runs the same code.

  notices      one per notice number: the Gazette's own section and number, the
               format a reader recognised, and what the reading took from it
  celebrants   one per celebrant a Registrar-General's list names (celebrants.py)
  addresses    an independent celebrant's address: the private schema only (hard limit 15)
  prohibitions one per person a prohibition notice names (prohibitions.py); its
               address goes to the private schema only, like a celebrant's
  liquidations one per company a liquidator's appointment names, and liquidators
               one per liquidator it names (liquidations.py); no address is read
  bankruptcies one per person a bankruptcy notice names (bankruptcies.py); the
               address to the private schema only, and a person an annulment names
               marked so the published view withholds the name
  company_notices  one per company a removal notice (removals.py), a winding-up
               application (windingup.py), a receivership (receiverships.py), an
               overseas company's leaving (overseas.py) or a restoration (restorations.py) names,
               and practitioners one per receiver or administrator named; no address is read

Items in equal items out plus items set aside, three times over: every
export line is a notice or a second capture set aside; every notice
recognised as a celebrant list gives records or a catch-log line; and the
counts are asserted, so a reading that does not reconcile raises and
publishes nothing.

    read(export_bytes, export_sha, only=None)   Result
"""
import datetime as dt
import hashlib
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field

from keys.dates import filed_date
from support import profiles
from registers.gazette import (appointments, bankruptcies, capture, celebrants, creditors, liquidations, notices, overseas,
                               prohibitions, receiverships, removals, restorations, windingup)

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
EXPORT_PROFILE = "gazette-notices-export"
CELEBRANT_PROFILE = "gazette-celebrant-list"
PROHIBITION_PROFILE = "gazette-director-prohibition"
LIQUIDATION_PROFILE = "gazette-liquidator-appointment"
READER_NOTICES = "registers.gazette.notices 1"
READER_CELEBRANTS = "registers.gazette.celebrants 2"
READER_PROHIBITIONS = "registers.gazette.prohibitions 1"
READER_LIQUIDATIONS = "registers.gazette.liquidations 2"
READER_BANKRUPTCIES = "registers.gazette.bankruptcies 1"
APPOINTMENT_PROFILE = "gazette-public-appointment"
READER_APPOINTMENTS = "registers.gazette.appointments 1"
#: the company-notice readers: (module, profile, reader stamp, kind), tried in this order
COMPANY_READERS = (
    (removals, "gazette-removal-notice", "registers.gazette.removals 1", "removal"),
    (windingup, "gazette-winding-up-application", "registers.gazette.windingup 1", "winding-up application"),
    (receiverships, "gazette-receivership", "registers.gazette.receiverships 1", "receivership"),
    (creditors.CreditorsNotice, "gazette-creditors-notice", "registers.gazette.creditors 1", "notice to creditors"),
    (creditors.Administration, "gazette-administration", "registers.gazette.creditors 1", "administration"),
    (overseas, "gazette-overseas-company-ceasing", "registers.gazette.overseas 1", "overseas company"),
    (restorations, "gazette-restoration-notice", "registers.gazette.restorations 1", "restoration"),
)
NOT_READ = "not read"


@dataclass
class Result:
    notices: list = field(default_factory=list)
    celebrants: list = field(default_factory=list)
    addresses: list = field(default_factory=list)      # (celebrant key, address)
    prohibitions: list = field(default_factory=list)
    prohibition_addresses: list = field(default_factory=list)   # (prohibition key, address, formerly)
    liquidations: list = field(default_factory=list)
    liquidators: list = field(default_factory=list)
    company_notices: list = field(default_factory=list)
    practitioners: list = field(default_factory=list)
    bankruptcies: list = field(default_factory=list)
    bankruptcy_addresses: list = field(default_factory=list)   # (bankruptcy key, address, formerly)
    appointments: list = field(default_factory=list)
    set_aside: list = field(default_factory=list)      # (item, stage, reason)
    counts: dict = field(default_factory=dict)


def profile_version(slug: str) -> int:
    """The ledger's version; until the integrator appends it, the lane's
    proposed line (merge request gazette-1)."""
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


def _short(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def _name_key(surname: str, given: str) -> str:
    return re.sub(r"[^a-z]", "", f"{surname}|{given}".lower()) + "|" + f"{surname}|{given}"


def _iso(text):
    d = filed_date(text) if text else None
    return d.isoformat() if d else None


def _person_key(f: dict) -> tuple:
    return tuple(re.sub(r"[^a-z]", "", (f[k] or "").lower()) for k in ("surname", "given_names"))


def lines_of(data: bytes, only=None) -> list:
    """The export's lines; with `only`, the lines of those notice numbers."""
    out = []
    for l in data.decode("utf-8").splitlines():
        if not l.strip():
            continue
        if only is not None:
            i = l.find('"notice": "', 0, 200) + 11
            if i >= 11 and l[i:l.find('"', i)] not in only:
                continue
        line = json.loads(l)
        if only is None or line["notice"] in only:
            out.append(line)
    return out


def read(export_bytes: bytes, export_sha: str, only=None, loaded_at: str = None) -> Result:
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = Result()
    ev, cv = profile_version(EXPORT_PROFILE), profile_version(CELEBRANT_PROFILE)
    pv, lv = profile_version(PROHIBITION_PROFILE), profile_version(LIQUIDATION_PROFILE)
    base = {"document": export_sha, "page": 1, "read_from": "text", "loaded_at": loaded_at}

    held = lines_of(export_bytes, set(only) if only is not None else None)
    by = defaultdict(list)
    for line in held:
        by[line["notice"]].append(line)

    twice = 0
    acted = []                                         # (notice, action, [notice numbers it acts on])
    recognised = with_records = wholly_aside = 0
    prohibited = prohibited_read = prohibited_aside = 0
    liquidated = liquidated_read = liquidated_aside = 0
    company = defaultdict(lambda: [0, 0, 0])            # kind → [recognised, read, set aside]
    cv_of = {p: profile_version(p) for _, p, _, _ in COMPANY_READERS}
    bv_of = {p: profile_version(p) for p in (bankruptcies.LIST, bankruptcies.NAP, bankruptcies.NOTICE)}
    bankrupt = defaultdict(lambda: [0, 0, 0])           # profile → [recognised, read, set aside]
    appointed = [0, 0, 0]                               # recognised, read, set aside
    av = profile_version(APPOINTMENT_PROFILE)
    orgs = None                                         # the celebrant organisation vocabulary, made before the first table
    # the printed celebrant tables last: they are cut by the organisations every other list prints
    for nid in sorted(by, key=lambda n: (any(celebrants.is_table(l["text"]) for l in by[n]), n)):
        line, others = notices.pick(by[nid])
        for o, why in others:
            twice += 1
            out.set_aside.append((f"{export_sha}/notice {nid} article {o['article']}", "notices", why))
        num = notices.number(nid)
        if num is None:
            out.set_aside.append((f"{export_sha}/notice {nid}", "notices", "not a Gazette notice number"))
            continue
        year, code, n = num
        fmt, status, records, supersedes = NOT_READ, NOT_READ, 0, None
        reader, profile, version = READER_NOTICES, EXPORT_PROFILE, ev
        if prohibitions.recognise(line["title"], line["text"]):
            prohibited += 1
            fmt, reader, profile, version = PROHIBITION_PROFILE, READER_PROHIBITIONS, PROHIBITION_PROFILE, pv
            got = prohibitions.read(line["text"])
            for place, why in got.unread:
                out.set_aside.append((f"{export_sha}/notice {nid} {place}", "prohibitions", why))
            for x in got.persons:
                key = f"gazette/{nid}/prohibition/{x.ordinal}"
                out.prohibitions.append({
                    "key": key, **base, "place": f"notice {nid} person {x.ordinal}",
                    "reader": READER_PROHIBITIONS, "profile": PROHIBITION_PROFILE, "profile_version": pv,
                    "filed": {"notice": nid, "published_on": line["published_on"], "action": got.action,
                              "name": x.name, "also_known_as": x.also_known_as, "named_twice": x.named_twice,
                              "statute": got.statute, "months": got.months, "permanent": got.permanent,
                              "starts_on": got.starts_on, "starts_basis": got.starts_basis,
                              "ends_on": None if got.permanent else prohibitions.ends_on(got.starts_on, got.months),
                              "dated_on": got.dated_on, "supersedes": ", ".join(got.acts_on) or None,
                              "superseded_by": None, "superseded_how": None, "ordinal": x.ordinal},
                })
                if x.address:
                    out.prohibition_addresses.append((key, x.address, x.formerly))
            if got.acts_on:
                acted.append((nid, got.action, got.acts_on))
                supersedes = ", ".join(got.acts_on)
            records = len(got.persons)
            if records or got.action == "revocation":
                prohibited_read += 1
                status = "read, part set aside" if got.unread else "read"
            else:
                prohibited_aside += 1
                status = "set aside"
                if not got.unread:
                    out.set_aside.append((f"{export_sha}/notice {nid}", "prohibitions", "recognised, and no person read"))
        elif liquidations.recognise(code, line["title"], line["text"]):
            liquidated += 1
            fmt, reader, profile, version = LIQUIDATION_PROFILE, READER_LIQUIDATIONS, LIQUIDATION_PROFILE, lv
            got = liquidations.read(line["title"], line["text"])
            for place, why in got.unread:
                out.set_aside.append((f"{export_sha}/notice {nid} {place}", "liquidations", why))
            stamp = {**base, "reader": READER_LIQUIDATIONS, "profile": LIQUIDATION_PROFILE, "profile_version": lv}
            for c in got.companies:
                out.liquidations.append({
                    "key": f"gazette/{nid}/company/{c.ordinal}", **stamp, "place": f"notice {nid} company {c.ordinal}",
                    "filed": {"notice": nid, "published_on": line["published_on"], "company": c.name,
                              "company_number": c.number, "shape": got.shape, "appointed_by": got.appointed_by,
                              "statute": got.statute, "appointed_on": c.appointed_on, "appointed_at": c.appointed_at,
                              "date_basis": c.date_basis, "dated_on": got.dated_on, "corrigendum": got.corrigendum,
                              "liquidators": len(got.liquidators), "ordinal": c.ordinal},
                })
            for x in got.liquidators:
                out.liquidators.append({
                    "key": f"gazette/{nid}/liquidator/{x.ordinal}", **stamp, "place": f"notice {nid} liquidator {x.ordinal}",
                    "filed": {"notice": nid, "published_on": line["published_on"], "name": x.name, "role": x.role,
                              "named_in_body": x.named_in_body, "companies": len(got.companies), "ordinal": x.ordinal},
                })
            records = len(got.companies)
            if records:
                liquidated_read += 1
                status = "read, part set aside" if got.unread else "read"
            else:
                liquidated_aside += 1
                status = "set aside"
                if not got.unread:
                    out.set_aside.append((f"{export_sha}/notice {nid}", "liquidations", "recognised, and no company read"))
        elif celebrants.recognise(line["title"], line["text"]):     # before the readers by section: a list filed under ar is still a list
            recognised += 1
            fmt, reader, profile, version = CELEBRANT_PROFILE, READER_CELEBRANTS, CELEBRANT_PROFILE, cv
            if celebrants.is_table(line["text"]) and orgs is None:
                orgs = celebrants.organisations(c["filed"]["organisation"] for c in out.celebrants)
            got = celebrants.read(line["text"], orgs if celebrants.is_table(line["text"]) else None)
            for place, why in got.unread:
                out.set_aside.append((f"{export_sha}/notice {nid} {place}", "celebrants", why))
            taken = got.records if got.action else []
            seen = defaultdict(int)
            for rec in taken:
                k = f"gazette/{nid}/celebrant/{_short(_name_key(rec.surname, rec.given_names))}"
                seen[k] += 1
                key = k if seen[k] == 1 else f"{k}/{seen[k]}"
                out.celebrants.append({
                    "key": key, **base, "place": f"notice {nid} record {rec.ordinal}",
                    "reader": READER_CELEBRANTS, "profile": CELEBRANT_PROFILE, "profile_version": cv,
                    "filed": {"notice": nid, "published_on": line["published_on"], "action": got.action,
                              "statute": got.statute, "period_from": _iso(got.period_from),
                              "period_to": _iso(got.period_to), "surname": rec.surname,
                              "given_names": rec.given_names, "organisation": rec.organisation,
                              "list_shape": got.mode, "marks": rec.marks, "split": rec.split, "ordinal": rec.ordinal},
                })
                if rec.address:
                    out.addresses.append((key, rec.address))
            records = len(taken)
            if records:
                with_records += 1
                status = "read, part set aside" if got.unread else "read"
            else:
                wholly_aside += 1
                status = "set aside"
                if not got.unread:
                    out.set_aside.append((f"{export_sha}/notice {nid}", "celebrants", "recognised, and no record read"))
        elif (hit := next((x for x in COMPANY_READERS if x[0].recognise(code, line["title"], line["text"])), None)):
            mod, profile, reader, kind = hit
            fmt, version = profile, cv_of[profile]
            company[kind][0] += 1
            got = mod.read(line["title"], line["text"])
            for place, why in got.unread:
                out.set_aside.append((f"{export_sha}/notice {nid} {place}", kind, why))
            stamp = {**base, "reader": reader, "profile": profile, "profile_version": version}
            for c in got.companies:
                out.company_notices.append({
                    "key": f"gazette/{nid}/company/{c.ordinal}", **stamp, "place": f"notice {nid} company {c.ordinal}",
                    "filed": {"notice": nid, "published_on": line["published_on"], "kind": kind, "action": got.action,
                              "company": c.name, "company_number": c.number, "shape": got.shape, "statute": got.statute,
                              "ground": got.ground, "by_whom": got.by_whom, "party": got.party,
                              "event_on": c.event_on or got.event_on, "event_at": c.event_at or got.event_at,
                              "event_basis": got.event_basis, "filed_on": got.filed_on, "court": got.court,
                              "reference": got.reference, "dated_on": got.dated_on, "corrigendum": got.corrigendum,
                              "people": len(got.people), "ordinal": c.ordinal},
                })
            for x in got.people:
                out.practitioners.append({
                    "key": f"gazette/{nid}/practitioner/{x.ordinal}", **stamp, "place": f"notice {nid} practitioner {x.ordinal}",
                    "filed": {"notice": nid, "published_on": line["published_on"], "name": x.name, "role": x.role,
                              "named_in_body": x.named_in_body, "companies": len(got.companies), "ordinal": x.ordinal},
                })
            records = len(got.companies)
            if records:
                company[kind][1] += 1
                status = "read, part set aside" if got.unread else "read"
            else:
                company[kind][2] += 1
                status = "set aside"
                if not got.unread:
                    out.set_aside.append((f"{export_sha}/notice {nid}", kind, "recognised, and no company read"))
        elif (slug := bankruptcies.kind_of(code, line["title"], line["text"])):
            fmt, reader, profile, version = slug, READER_BANKRUPTCIES, slug, bv_of[slug]
            bankrupt[slug][0] += 1
            got = bankruptcies.read(slug, line["title"], line["text"])
            for place, why in got.unread:
                out.set_aside.append((f"{export_sha}/notice {nid} {place}", "bankruptcies", why))
            for x in got.persons:
                key = f"gazette/{nid}/person/{x.ordinal}"
                out.bankruptcies.append({
                    "key": key, **base, "place": f"notice {nid} person {x.ordinal}",
                    "reader": READER_BANKRUPTCIES, "profile": slug, "profile_version": version,
                    "filed": {"notice": nid, "published_on": line["published_on"], "kind": got.kind, "shape": got.shape,
                              "surname": x.surname, "given_names": x.given_names, "also_known_as": x.also_known_as,
                              "occupation": x.occupation, "event_on": x.event_on, "event_at": x.event_at,
                              "court": got.court, "statute": got.statute, "dated_on": got.dated_on,
                              "withheld_by": nid if got.kind == "annulment" else None, "ordinal": x.ordinal},
                })
                if x.address or x.formerly:
                    out.bankruptcy_addresses.append((key, x.address, x.formerly))
            records = len(got.persons)
            if records:
                bankrupt[slug][1] += 1
                status = "read, part set aside" if got.unread else "read"
            else:
                bankrupt[slug][2] += 1
                status = "set aside"
                if not got.unread:
                    out.set_aside.append((f"{export_sha}/notice {nid}", "bankruptcies", "recognised, and no person read"))
        elif appointments.recognise(code, line["title"], line["text"]):
            fmt, reader, profile, version = APPOINTMENT_PROFILE, READER_APPOINTMENTS, APPOINTMENT_PROFILE, av
            appointed[0] += 1
            got = appointments.read(line["title"], line["text"])
            for place, why in got.unread:
                out.set_aside.append((f"{export_sha}/notice {nid} {place}", "appointments", why))
            for x in got.people:
                out.appointments.append({
                    "key": f"gazette/{nid}/appointee/{x.ordinal}", **base, "place": f"notice {nid} appointee {x.ordinal}",
                    "reader": READER_APPOINTMENTS, "profile": APPOINTMENT_PROFILE, "profile_version": av,
                    "filed": {"notice": nid, "published_on": line["published_on"], "body": got.body, "name": x.name,
                              "role": x.role, "statute": got.statute, "by_whom": got.by_whom, "starts_on": got.starts_on,
                              "ends_on": got.ends_on, "dated_on": got.dated_on, "corrigendum": got.corrigendum,
                              "ordinal": x.ordinal},
                })
            records = len(got.people)
            appointed[1 if records else 2] += 1
            status = ("read, part set aside" if len(got.unread) else "read") if records else "set aside"
        out.notices.append({
            "key": f"gazette/{nid}", **base, "place": f"notice {nid}",
            "reader": reader, "profile": profile, "profile_version": version,
            "filed": {"notice": nid, "year": year, "section": code, "number": n, "family": notices.family(code),
                      "format": fmt, "status": status, "records": records, "supersedes": supersedes, "title": line["title"],
                      "published_on": line["published_on"], "url": line["url"], "old_type": line.get("old_type"),
                      "article": line["article"], "source_note": capture.EXPORT_NOTE},
        })

    # a revocation, a substitution or a variation marks the rows of the notice it names
    by_notice = defaultdict(list)
    for p in out.prohibitions:
        by_notice[p["filed"]["notice"]].append(p)
    for nid, how, targets in acted:
        for t in targets:
            for p in by_notice.get(t, []):
                if p["filed"]["notice"] != nid:
                    p["filed"]["superseded_by"], p["filed"]["superseded_how"] = nid, {
                        "revocation": "revoked", "substitution": "revoked and replaced", "variation": "varied"}[how]

    if len(out.notices) + twice + sum(1 for i, s, w in out.set_aside if w == "not a Gazette notice number") != len(held):
        raise AssertionError(f"the export does not reconcile: {len(held)} lines, {len(out.notices)} notices, {twice} second captures")
    if with_records + wholly_aside != recognised:
        raise AssertionError(f"the celebrant lists do not reconcile: {recognised} recognised, {with_records} read, {wholly_aside} set aside")
    if prohibited_read + prohibited_aside != prohibited:
        raise AssertionError(f"the prohibitions do not reconcile: {prohibited} recognised, {prohibited_read} read, {prohibited_aside} set aside")
    # a person an annulment names is withheld on every row that names them as bankrupt before it (the same
    # surname and given names, adjudicated on or before the annulment's notice): withholding never publishes
    annulled = defaultdict(list)
    for b in out.bankruptcies:
        if b["filed"]["withheld_by"]:
            annulled[_person_key(b["filed"])].append((b["filed"]["published_on"] or "9999", b["filed"]["notice"]))
    for b in out.bankruptcies:
        f = b["filed"]
        if not f["withheld_by"]:
            later = sorted(a for a in annulled.get(_person_key(f), []) if (f["event_on"] or f["published_on"] or "") <= a[0])
            f["withheld_by"] = later[0][1] if later else None
    if appointed[1] + appointed[2] != appointed[0]:
        raise AssertionError(f"the appointment notices do not reconcile: {appointed}")
    for slug, (n, ok, aside) in bankrupt.items():
        if ok + aside != n:
            raise AssertionError(f"the {slug} notices do not reconcile: {n} recognised, {ok} read, {aside} set aside")
    if liquidated_read + liquidated_aside != liquidated:
        raise AssertionError(f"the liquidations do not reconcile: {liquidated} recognised, {liquidated_read} read, {liquidated_aside} set aside")
    for kind, (n, ok, aside) in company.items():
        if ok + aside != n:
            raise AssertionError(f"the {kind} notices do not reconcile: {n} recognised, {ok} read, {aside} set aside")
    if len({r["key"] for r in out.celebrants}) != len(out.celebrants):
        raise AssertionError("two celebrant rows share a key")
    out.counts = {"lines": len(held), "notices": len(out.notices), "captured_twice": twice,
                  "celebrant_lists": recognised, "celebrant_lists_read": with_records,
                  "celebrant_lists_set_aside": wholly_aside, "celebrants": len(out.celebrants),
                  "celebrant_addresses": len(out.addresses), "prohibition_notices": prohibited,
                  "prohibition_notices_read": prohibited_read, "prohibition_notices_set_aside": prohibited_aside,
                  "prohibitions": len(out.prohibitions), "prohibition_addresses": len(out.prohibition_addresses),
                  "liquidation_notices": liquidated, "liquidation_notices_read": liquidated_read,
                  "liquidation_notices_set_aside": liquidated_aside, "liquidations": len(out.liquidations),
                  "liquidators": len(out.liquidators),
                  **{f"{k.replace(' ', '_').replace('-', '_')}_notices{s}": v[i] for k, v in sorted(company.items())
                     for i, s in enumerate(("", "_read", "_set_aside"))},
                  "company_notices": len(out.company_notices), "practitioners": len(out.practitioners),
                  **{f"{k.split('gazette-')[1].replace('-', '_')}{s}": v[i] for k, v in sorted(bankrupt.items())
                     for i, s in enumerate(("", "_read", "_set_aside"))},
                  "bankruptcies": len(out.bankruptcies), "bankruptcy_addresses": len(out.bankruptcy_addresses),
                  "bankruptcies_withheld": sum(1 for b in out.bankruptcies if b["filed"]["withheld_by"]),
                  "appointment_notices": appointed[0], "appointment_notices_read": appointed[1],
                  "appointment_notices_set_aside": appointed[2], "appointments": len(out.appointments),
                  "set_aside": len(out.set_aside),
                  "not_read": sum(1 for r in out.notices if r["filed"]["format"] == NOT_READ)}
    return out
