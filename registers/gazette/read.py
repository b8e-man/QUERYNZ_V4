"""The reading: the notices export → this lane's rows, each stamped with its
reader, its profile and version, and read from text. Nothing here calls a
model, so the fast tier runs the same code.

  notices      one per notice number: the Gazette's own section and number, the
               format a reader recognised, and what the reading took from it
  celebrants   one per celebrant a Registrar-General's list names (celebrants.py)
  addresses    an independent celebrant's address: the private schema only (hard limit 15)
  prohibitions one per person a prohibition notice names (prohibitions.py); its
               address goes to the private schema only, like a celebrant's

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
from registers.gazette import capture, celebrants, notices, prohibitions

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
EXPORT_PROFILE = "gazette-notices-export"
CELEBRANT_PROFILE = "gazette-celebrant-list"
PROHIBITION_PROFILE = "gazette-director-prohibition"
READER_NOTICES = "registers.gazette.notices 1"
READER_CELEBRANTS = "registers.gazette.celebrants 1"
READER_PROHIBITIONS = "registers.gazette.prohibitions 1"
NOT_READ = "not read"


@dataclass
class Result:
    notices: list = field(default_factory=list)
    celebrants: list = field(default_factory=list)
    addresses: list = field(default_factory=list)      # (celebrant key, address)
    prohibitions: list = field(default_factory=list)
    prohibition_addresses: list = field(default_factory=list)   # (prohibition key, address, formerly)
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
    pv = profile_version(PROHIBITION_PROFILE)
    base = {"document": export_sha, "page": 1, "read_from": "text", "loaded_at": loaded_at}

    held = lines_of(export_bytes, set(only) if only is not None else None)
    by = defaultdict(list)
    for line in held:
        by[line["notice"]].append(line)

    twice = 0
    acted = []                                         # (notice, action, [notice numbers it acts on])
    recognised = with_records = wholly_aside = 0
    prohibited = prohibited_read = prohibited_aside = 0
    for nid in sorted(by):
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
        elif celebrants.recognise(line["title"], line["text"]):
            recognised += 1
            fmt, reader, profile, version = CELEBRANT_PROFILE, READER_CELEBRANTS, CELEBRANT_PROFILE, cv
            got = celebrants.read(line["text"])
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
    if len({r["key"] for r in out.celebrants}) != len(out.celebrants):
        raise AssertionError("two celebrant rows share a key")
    out.counts = {"lines": len(held), "notices": len(out.notices), "captured_twice": twice,
                  "celebrant_lists": recognised, "celebrant_lists_read": with_records,
                  "celebrant_lists_set_aside": wholly_aside, "celebrants": len(out.celebrants),
                  "celebrant_addresses": len(out.addresses), "prohibition_notices": prohibited,
                  "prohibition_notices_read": prohibited_read, "prohibition_notices_set_aside": prohibited_aside,
                  "prohibitions": len(out.prohibitions), "prohibition_addresses": len(out.prohibition_addresses),
                  "set_aside": len(out.set_aside),
                  "not_read": sum(1 for r in out.notices if r["filed"]["format"] == NOT_READ)}
    return out
