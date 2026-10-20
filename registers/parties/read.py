"""The reading: the register page and the notices export → this lane's rows,
each stamped with its reader, its document's profile and version, and read
from text. Nothing here calls a model, so the fast tier runs the same code.

  registrations   one per registration: the party (lifecycle.py says why a registration is the party)
  names           every name, abbreviation and printing a registration has carried, with its window
  events          every resolution read from a notice, with the registration it was resolved to
  contacts        the secretary's contact lines from the page: the private schema only (hard limit 15)

Each notice is read from the document that holds it (capture.notices_held:
the Gazette lane's export where it holds the same text, else the parties
export) and every row from it cites that document and the notice.

Items in equal items out plus items set aside: every notice held gives
events or a catch-log line, every resolution the lifecycle needs is
resolved or a catch-log line, and every party block on the page is an
entry or a catch-log line.

    read(page_bytes, page_sha, page_date, held)   Result   (held: capture.notices_held)
"""
import datetime as dt
import hashlib
import json
import os
from dataclasses import dataclass, field

from support import profiles
from registers.parties import lifecycle, notices, register

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
PAGE_PROFILE = "ec-party-register-page"
NOTICES_PROFILE = "gazette-party-register-notices"
READER_PAGE = "registers.parties.register 1"
READER_NOTICES = "registers.parties.notices 2"


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
    got = [p for p in (profiles.profile(slug), profiles.profile(slug, path=PROPOSED)) if p]
    if not got:
        raise LookupError(f"no document profile {slug}")
    return max(int(p["version"]) for p in got)


def _short(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def read_export(data: bytes) -> list:
    return [json.loads(l) for l in data.decode("utf-8").splitlines() if l.strip()]


def _same_name(registrations: list, names: list) -> None:
    """Two registrations that carried one name (a party cancelled and
    registered again, or two parties a decade apart) stay two: each says
    which other carried the name, and both windows."""
    by_key = {}
    for n in names:
        if n["filed"]["kind"] == "name":
            by_key.setdefault(n["filed"]["name_key"], set()).add(n["filed"]["party"])
    regs = {r["key"]: r for r in registrations}
    for r in registrations:
        others = sorted({k for ks in by_key.values() if r["key"] in ks for k in ks} - {r["key"]})
        if not others:
            r["filed"]["same_name_as"] = r["filed"]["same_name_note"] = None
            continue
        def span(k):
            f = regs[k]["filed"]
            start = f["registered_on"] or f"before {str(f['registered_by'])[:4]}"
            return f"{k}, {start} to {f['cancelled_on'] or 'now'}"
        r["filed"]["same_name_as"] = ", ".join(others)
        r["filed"]["same_name_note"] = (
            f"{len(others) + 1} registrations carried the name {r['filed']['name']}: " + "; ".join(span(k) for k in [r["key"]] + others)
            + ". A party cancelled and registered again is a new registration; a filing joins the one live on its day"
              " (pub.party_labels).")


def read(page_bytes: bytes, page_sha: str, page_date: str, held: list, loaded_at: str = None) -> Result:
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = Result()
    pv, nv = profile_version(PAGE_PROFILE), profile_version(NOTICES_PROFILE)
    page_stamp = {"document": page_sha, "page": 1, "reader": READER_PAGE, "profile": PAGE_PROFILE,
                  "profile_version": pv, "read_from": "text", "loaded_at": loaded_at}
    notice_stamp = {"page": 1, "reader": READER_NOTICES, "profile": NOTICES_PROFILE,
                    "profile_version": nv, "read_from": "text", "loaded_at": loaded_at}

    page = register.read(page_bytes)
    for place, why in page.skipped:
        out.set_aside.append((f"{page_sha}/{place}", "page", why))

    by_notice, published, events, with_events = {}, {}, [], 0
    for n in held:
        got = notices.read(n["text"], n["notice"], n["published_on"])
        by_notice[n["notice"]] = n
        published[n["notice"]] = n["published_on"]
        for place, why in got.unread:
            out.set_aside.append((f"{n['document']}/{place}", "notices", why))
        with_events += bool(got.events)
        events += got.events
    wholly_aside = sum(1 for n in held if not any(e.notice == n["notice"] for e in events))
    if with_events + wholly_aside != len(held):
        raise AssertionError(f"the notices do not reconcile: {len(held)} held, {with_events} read, {wholly_aside} set aside")

    life = lifecycle.build(events, page.entries, page_date, published)
    doc_of = lambda notice: by_notice[notice.split("/")[0]]["document"] if notice.split("/")[0] in by_notice else page_sha
    out.set_aside += [(f"{doc_of(i)}/{i}" if stage != "page" else f"{page_sha}/{i}", stage, why)
                      for i, stage, why in life.set_aside]

    def notice_place(notice, ordinal=None):
        return f"notice {notice}" + (f" resolution {ordinal}" if ordinal else "")

    def cite(notice, ordinal=None):
        return {**notice_stamp, "document": by_notice[notice]["document"], "place": notice_place(notice, ordinal)}

    for r in life.registrations:
        en = r.entry
        if r.registered_notice:
            at = cite(r.registered_notice, r.registered_ordinal)
        elif en is not None:
            at = {**page_stamp, "place": f"party {en.ordinal}"}
        else:
            first = next(n for n in r.names if n.notice)
            at = cite(first.notice, first.ordinal)
        a = r.current("abbreviation")
        status = ("cancelled" if r.cancelled_on else "on the register" if en is not None
                  else "not on the register page; no cancellation held")
        out.registrations.append({
            "key": r.key, **at,
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
                "cancelled_document": by_notice[r.cancelled_notice]["document"] if r.cancelled_notice else None,
                "cancelled_place": notice_place(r.cancelled_notice, r.cancelled_ordinal) if r.cancelled_notice else None,
            },
        })
        if en is not None and en.contact:
            out.contacts.append((r.key, en.contact))
        seen = {}
        for n in r.names:
            base = f"{r.key}/{n.kind}/{_short(lifecycle.name_key(n.name) + '|' + n.name)}"
            seen[base] = seen.get(base, 0) + 1
            stamp = (cite(n.notice, n.ordinal) if n.notice
                     else {**page_stamp, "place": f"party {en.ordinal}" if en is not None else "page"})
            out.names.append({"key": base if seen[base] == 1 else f"{base}/{seen[base]}", **stamp,
                              "filed": {"party": r.key, "name": n.name, "kind": n.kind, "from_on": n.from_on,
                                        "to_on": n.to_on, "basis": n.basis, "name_key": lifecycle.name_key(n.name)}})

    _same_name(out.registrations, out.names)

    for e in events:
        r = life.resolved.get((e.notice, e.ordinal))
        n = by_notice[e.notice]
        out.events.append({
            "key": f"gazette/{e.notice}/{e.ordinal}", **cite(e.notice, e.ordinal),
            "filed": {"notice": e.notice, "published_on": n["published_on"], "decided_on": e.decided_on,
                      "kind": e.kind, "party_label": e.name, "new_name": e.new_name, "abbreviation": e.abbreviation,
                      "old_abbreviation": e.old_abbreviation, "ref": e.ref, "party": r.key if r else None,
                      "url": n.get("url"), "title": n.get("title"), "clause": e.clause,
                      "source_note": n["source_note"], "gazette_key": n.get("gazette_key")},
        })
    needs = [e for e in events if e.kind in ("registered", "cancelled", "renamed", "abbreviation")]
    resolved = sum(1 for e in needs if (e.notice, e.ordinal) in life.resolved)
    aside_life = len(life.set_aside)
    if resolved + sum(1 for i, s, w in life.set_aside if s == "lifecycle") != len(needs):
        raise AssertionError(f"the lifecycle does not reconcile: {len(needs)} resolutions, {resolved} resolved, {aside_life} set aside")
    out.counts = {"page_parties": len(page.entries) + len(page.skipped), "page_read": len(page.entries),
                  "notices": len(held), "notices_read": with_events,
                  "from_gazette_lane": sum(1 for n in held if n.get("taken_from") == "gazette"), "events": len(events),
                  "resolutions": len(needs), "resolved": resolved, "registrations": len(out.registrations),
                  "names": len(out.names), "corrections": len(life.corrections),
                  "on_register": sum(1 for r in out.registrations if r["filed"]["on_register"]),
                  "off_register_no_cancellation": sum(1 for r in life.registrations if r.off_register_by),
                  "set_aside": len(out.set_aside)}
    return out
