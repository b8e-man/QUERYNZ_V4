"""The reading: the register page and the notices export → this lane's rows,
each stamped with its reader, its document's profile and version, and read
from text. Nothing here calls a model, so the fast tier runs the same code.

  registrations   one per registration: the party (lifecycle.py says why a registration is the party)
  names           every name, abbreviation and printing a registration has carried, with its window
  events          every resolution read from a notice, with the registration it was resolved to
  contacts        the secretary's contact lines from the page: the private schema only (hard limit 15)

Items in equal items out plus items set aside: every notice in the export
gives events or a catch-log line, every resolution the lifecycle needs is
resolved or a catch-log line, and every party block on the page is an
entry or a catch-log line.

    read(page_bytes, page_sha, page_date, export_bytes, export_sha)   Result
"""
import datetime as dt
import hashlib
import json
import os
from dataclasses import dataclass, field

from support import profiles
from registers.parties import capture, lifecycle, notices, register

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
PAGE_PROFILE = "ec-party-register-page"
NOTICES_PROFILE = "gazette-party-register-notices"
READER_PAGE = "registers.parties.register 1"
READER_NOTICES = "registers.parties.notices 1"


@dataclass
class Result:
    registrations: list = field(default_factory=list)
    names: list = field(default_factory=list)
    events: list = field(default_factory=list)
    contacts: list = field(default_factory=list)       # (registration key, contact lines)
    set_aside: list = field(default_factory=list)      # (item, stage, reason)
    counts: dict = field(default_factory=dict)


def profile_version(slug: str) -> int:
    """The ledger's version; until the integrator appends it, the lane's
    proposed line (merge request parties-1)."""
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


def _short(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def read_export(data: bytes) -> list:
    return [json.loads(l) for l in data.decode("utf-8").splitlines() if l.strip()]


def read(page_bytes: bytes, page_sha: str, page_date: str, export_bytes: bytes, export_sha: str,
         loaded_at: str = None) -> Result:
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = Result()
    pv, nv = profile_version(PAGE_PROFILE), profile_version(NOTICES_PROFILE)
    page_stamp = {"document": page_sha, "page": 1, "reader": READER_PAGE, "profile": PAGE_PROFILE,
                  "profile_version": pv, "read_from": "text", "loaded_at": loaded_at}
    notice_stamp = {"document": export_sha, "page": 1, "reader": READER_NOTICES, "profile": NOTICES_PROFILE,
                    "profile_version": nv, "read_from": "text", "loaded_at": loaded_at}

    page = register.read(page_bytes)
    for place, why in page.skipped:
        out.set_aside.append((f"{page_sha}/{place}", "page", why))

    held = read_export(export_bytes)
    by_notice, published, events, with_events = {}, {}, [], 0
    for n in held:
        got = notices.read(n["text"], n["notice"], n["published_on"])
        by_notice[n["notice"]] = n
        published[n["notice"]] = n["published_on"]
        for place, why in got.unread:
            out.set_aside.append((f"{export_sha}/{place}", "notices", why))
        with_events += bool(got.events)
        events += got.events
    wholly_aside = sum(1 for n in held if not any(e.notice == n["notice"] for e in events))
    if with_events + wholly_aside != len(held):
        raise AssertionError(f"the notices do not reconcile: {len(held)} held, {with_events} read, {wholly_aside} set aside")

    life = lifecycle.build(events, page.entries, page_date, published)
    out.set_aside += [(f"{export_sha}/{i}" if stage != "page" else f"{page_sha}/{i}", stage, why)
                      for i, stage, why in life.set_aside]

    def notice_place(notice, ordinal=None):
        return f"notice {notice}" + (f" resolution {ordinal}" if ordinal else "")

    for r in life.registrations:
        en = r.entry
        if r.registered_notice:
            cite = {**notice_stamp, "place": notice_place(r.registered_notice, r.registered_ordinal)}
        elif en is not None:
            cite = {**page_stamp, "place": f"party {en.ordinal}"}
        else:
            first = next(n for n in r.names if n.notice)
            cite = {**notice_stamp, "place": notice_place(first.notice, first.ordinal)}
        a = r.current("abbreviation")
        status = ("cancelled" if r.cancelled_on else "on the register" if en is not None
                  else "not on the register page; no cancellation held")
        out.registrations.append({
            "key": r.key, **cite,
            "filed": {
                "name": r.name, "first_name": r.first_name,
                "registered_on": en.registered_on if en is not None else r.registered_on,
                "notice_registered_on": r.registered_on if r.registered_notice else None,
                "registered_by": r.registered_by, "registered_basis": r.registered_basis,
                "cancelled_on": r.cancelled_on, "status": status,
                "on_register": en is not None, "register_seen_on": page_date,
                "off_register_by": r.off_register_by, "page_basis": r.page_basis, "window": r.window,
                "abbreviation": en.abbreviation if en is not None else (a.name if a else None),
                "abbreviation_on_ballot": bool(en and en.abbreviation_on_ballot),
                "components": en.components if en else None,
                "logo_registered_on": en.logo_registered_on if en else None,
                "statement_deadline": en.statement_deadline if en else None,
                "audit": en.audit if en else None, "website": en.website if en else None,
                "rules_title": en.rules_title if en else None, "rules_href": en.rules_href if en else None,
                "secretary": en.secretary if en else None,
                "register_document": page_sha if en is not None else None,
                "register_place": f"party {en.ordinal}" if en is not None else None,
                "cancelled_document": export_sha if r.cancelled_notice else None,
                "cancelled_place": notice_place(r.cancelled_notice, r.cancelled_ordinal) if r.cancelled_notice else None,
            },
        })
        if en is not None and en.contact:
            out.contacts.append((r.key, en.contact))
        seen = {}
        for n in r.names:
            base = f"{r.key}/{n.kind}/{_short(lifecycle.name_key(n.name) + '|' + n.name)}"
            seen[base] = seen.get(base, 0) + 1
            stamp = ({**notice_stamp, "place": notice_place(n.notice, n.ordinal)} if n.notice
                     else {**page_stamp, "place": f"party {en.ordinal}" if en is not None else "page"})
            out.names.append({"key": base if seen[base] == 1 else f"{base}/{seen[base]}", **stamp,
                              "filed": {"party": r.key, "name": n.name, "kind": n.kind, "from_on": n.from_on,
                                        "to_on": n.to_on, "basis": n.basis, "name_key": lifecycle.name_key(n.name)}})

    for e in events:
        r = life.resolved.get((e.notice, e.ordinal))
        n = by_notice[e.notice]
        out.events.append({
            "key": f"gazette/{e.notice}/{e.ordinal}", **notice_stamp, "place": notice_place(e.notice, e.ordinal),
            "filed": {"notice": e.notice, "published_on": n["published_on"], "decided_on": e.decided_on,
                      "kind": e.kind, "party_label": e.name, "new_name": e.new_name, "abbreviation": e.abbreviation,
                      "old_abbreviation": e.old_abbreviation, "ref": e.ref, "party": r.key if r else None,
                      "url": n.get("url"), "title": n.get("title"), "clause": e.clause,
                      "source_note": capture.EXPORT_NOTE},
        })
    needs = [e for e in events if e.kind in ("registered", "cancelled", "renamed", "abbreviation")]
    resolved = sum(1 for e in needs if (e.notice, e.ordinal) in life.resolved)
    aside_life = len(life.set_aside)
    if resolved + sum(1 for i, s, w in life.set_aside if s == "lifecycle") != len(needs):
        raise AssertionError(f"the lifecycle does not reconcile: {len(needs)} resolutions, {resolved} resolved, {aside_life} set aside")
    out.counts = {"page_parties": len(page.entries) + len(page.skipped), "page_read": len(page.entries),
                  "notices": len(held), "notices_read": with_events, "events": len(events),
                  "resolutions": len(needs), "resolved": resolved, "registrations": len(out.registrations),
                  "names": len(out.names), "corrections": len(life.corrections),
                  "on_register": sum(1 for r in out.registrations if r["filed"]["on_register"]),
                  "off_register_no_cancellation": sum(1 for r in life.registrations if r.off_register_by),
                  "set_aside": len(out.set_aside)}
    return out
