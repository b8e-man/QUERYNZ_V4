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
               overseas company's leaving (overseas.py), a restoration (restorations.py) or a
               society's or trust board's dissolution (dissolutions.py), an amalgamation, a
               rectification of the register, a transfer out or a deed of company arrangement
               (companyacts.py; a rectification's people by initials and surname only) names,
               and practitioners one per receiver or administrator named; no address is read
  possessions  one per notice of a mortgagee's entry into possession (possessions.py): the
               names it may show decided at the join (load.join_possessions); the property,
               registration numbers and any person's name to the private schema only
  uncut        every published text (a title, a company as printed, …) cut before any
               property it names (cut.py); the uncut value to the private schema only

Items in equal items out plus items set aside, three times over: every
export line is a notice or a second capture set aside; every notice
recognised as a celebrant list gives records or a catch-log line; and the
counts are asserted, so a reading that does not reconcile raises and
publishes nothing.

Since 2 November 2026 the notices after the export come from DigitalNZ's
answers (capture.py), read by the same readers: a notice the export holds
is read from the export, any other from the newest answer that carries it,
and each row names its own document. A notice the Gazette suppresses (its
robots file disallows it by number, a suppression request) is kept whole:
every line held of it in `gazette_private.suppressed_notices`, and a
`notices` row with format and status `suppressed` and no title; no typed
row is read from it (ruling 142, 4 November 2026).

    read(export_bytes, export_sha, only=None, pages=(), suppressed=())   Result
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
from registers.gazette import (appointments, bankruptcies, capture, celebrants, companyacts, creditors, cut, dissolutions, liquidations, notices, offices, overseas,
                               possessions, prohibitions, receiverships, removals, restorations, windingup)

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
READER_POSSESSIONS = "registers.gazette.possessions 1"
#: the company-notice readers: (module, profile, reader stamp, kind), tried in this order
COMPANY_READERS = (
    (removals, "gazette-removal-notice", "registers.gazette.removals 1", "removal"),
    (windingup, "gazette-winding-up-application", "registers.gazette.windingup 1", "winding-up application"),
    (receiverships, "gazette-receivership", "registers.gazette.receiverships 1", "receivership"),
    (creditors.CreditorsNotice, "gazette-creditors-notice", "registers.gazette.creditors 1", "notice to creditors"),
    (creditors.Administration, "gazette-administration", "registers.gazette.creditors 1", "administration"),
    (overseas, "gazette-overseas-company-ceasing", "registers.gazette.overseas 1", "overseas company"),
    (restorations, "gazette-restoration-notice", "registers.gazette.restorations 1", "restoration"),
    (companyacts.Rectification, "gazette-register-rectification", "registers.gazette.companyacts 1", "rectification"),
    (companyacts.Amalgamation, "gazette-amalgamation-proposal", "registers.gazette.companyacts 1", "amalgamation"),
    (companyacts.TransferOut, "gazette-transfer-out", "registers.gazette.companyacts 1", "transfer out"),
    (companyacts.DeedOfArrangement, "gazette-deed-of-company-arrangement", "registers.gazette.companyacts 1", "deed of company arrangement"),
    (dissolutions, "gazette-society-dissolution", "registers.gazette.dissolutions 1", "dissolution"),
)
NOT_READ = "not read"
SUPPRESSED = "suppressed"


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
    board_interventions: list = field(default_factory=list)
    possessions: list = field(default_factory=list)     # names and the property in `_private`, moved out at the join
    uncut: list = field(default_factory=list)          # (row key, column, the value before cut.py cut it)
    #: every line held of a notice the Gazette suppresses, whole: {key, notice, document, article, title, text,
    #: published_on, url} (ruling 142)
    suppressed: list = field(default_factory=list)
    #: what a reader read past for a row and keeps: {key, notice, document, place, kind, value} (ruling 142): an
    #: appointee's or a JP's address, a plaintiff's address for service, an applicant, a liquidator's contact lines,
    #: a record the reader could not cut, a revocation's words
    kept: list = field(default_factory=list)
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


def pick(lines: list) -> tuple:
    """One notice's lines, from the export and from DigitalNZ's landed answers → (the line read, [(line, why)]).
    The export's copy is read where it holds one, so a notice's rows do not change under it; else the newest
    DigitalNZ answer's (the pages come in the order they were asked)."""
    old = [l for l in lines if "_document" not in l]
    dnz = [l for l in lines if "_document" in l]
    if old:
        kept, others = notices.pick(old)
        return kept, others + [(l, "held in the export: the old estate's capture of the notice is read") for l in dnz]
    return dnz[-1], [(l, "asked again from DigitalNZ: the newest answer is read") for l in dnz[:-1]]


def _office_row(out, fam, version, nid, line, base, ordinal, name, role, body, *, statute=None, by_whom=None, starts_on=None,
                ends_on=None, dated_on=None, corrigendum=False, action="appointed", locality=None, kind="person"):
    out.appointments.append({
        "key": f"gazette/{nid}/appointee/{ordinal}", **base, "place": f"notice {nid} appointee {ordinal}",
        "reader": offices.READER, "profile": fam, "profile_version": version,
        "filed": {"notice": nid, "published_on": line["published_on"], "body": body, "name": name, "role": role,
                  "statute": statute, "by_whom": by_whom, "starts_on": starts_on, "ends_on": ends_on, "dated_on": dated_on,
                  "corrigendum": corrigendum, "ordinal": ordinal, "action": action, "locality": locality,
                  "appointee_kind": kind},
    })


def keep(out, nid, doc, got) -> None:
    """What a reader read past and kept (its Reading's `private`: (place, kind, value)) into out.kept (ruling 142)."""
    for k, (place, kind, value) in enumerate(getattr(got, "private", None) or (), start=1):
        if value:
            out.kept.append({"key": f"gazette/{nid}/kept/{k}",
                             "notice": nid, "document": doc, "place": place, "kind": kind, "value": value})


def _read_office(out, fam, version, nid, line, base, doc) -> tuple:
    """One office notice read by its family (offices.py) into appointments or board_interventions: (records, unread)."""
    title, text = line["title"], line["text"]
    unread = []
    if fam == offices.JUDICIAL:
        got = offices.judicial(title, text)
        unread = got.unread
        keep(out, nid, doc, got)
        for x in got.people:
            _office_row(out, fam, version, nid, line, base, x.ordinal, x.name, x.role, got.body, statute=got.statute,
                        by_whom=got.by_whom, starts_on=got.starts_on, ends_on=got.ends_on, dated_on=got.dated_on,
                        corrigendum=got.corrigendum)
        records = len(got.people)
    elif fam == offices.JP:
        got = offices.jp_list(title, text)
        unread = got.unread
        keep(out, nid, doc, got)
        action = {"appointed": "appointed", "retired": "retired", "resigned": "resigned"}[got.kind]
        for ordinal, name, town in got.people:
            _office_row(out, fam, version, nid, line, base, ordinal, name, offices.jp_role(got.kind), "Justices of the Peace",
                        statute=got.statute, by_whom="Governor-General" if got.kind == "appointed" else None,
                        dated_on=got.dated_on, corrigendum=got.corrigendum, action=action, locality=town)
        records = len(got.people)
    elif fam == offices.MENTAL_HEALTH:
        people, unread = offices.mental_health(text)
        d = offices.LQ._DATED.search(text or "")
        for i, (name, area) in enumerate(people, start=1):
            _office_row(out, fam, version, nid, line, base, i, name, "Director of Area Mental Health Services",
                        area or "Area Mental Health Services", statute="Mental Health (Compulsory Assessment and Treatment) Act 1992",
                        by_whom="the Director-General of Health", dated_on=offices.LQ._date(d.group("d")) if d else None,
                        corrigendum=bool(offices.LQ._CORRIGENDUM.match(title or "")))
        records = len(people)
    elif fam == offices.RESERVE:
        got = offices.reserve(title, text)
        if got:
            body, what = got
            d = offices.LQ._DATED.search(text or "")
            _office_row(out, fam, version, nid, line, base, 1, body, what, "a reserve under the Reserves Act 1977",
                        statute="Reserves Act 1977", dated_on=offices.LQ._date(d.group("d")) if d else None,
                        corrigendum=bool(offices.LQ._CORRIGENDUM.match(title or "")),
                        action="revoked" if what.endswith("revoked") else "appointed", kind="body")
        else:
            unread = [("body", "no body appointed to control and manage a reserve the reader can take")]
        records = 1 if got else 0
    else:
        got = offices.intervention(title, text)
        if got.board:
            out.board_interventions.append({
                "key": f"gazette/{nid}/intervention", **base, "place": f"notice {nid} intervention",
                "reader": offices.READER, "profile": fam, "profile_version": version,
                "filed": {"notice": nid, "published_on": line["published_on"], "action": got.action, "board": got.board,
                          "institution_number": got.institution_number, "statute": got.statute,
                          "directed_by": got.directed_by, "dated_on": got.dated_on,
                          "names_notices": ", ".join(n for n in got.names_notices if n != nid) or None,
                          "revoked_by": None, "corrigendum": got.corrigendum},
            })
        else:
            unread = [("board", "no school board the reader can take")]
        records = 1 if got.board else 0
    for place, why in unread:
        out.set_aside.append((f"{doc}/notice {nid} {place}", "offices", why))
    return records, bool(unread)


def read(export_bytes: bytes, export_sha: str, only=None, loaded_at: str = None, pages=(), suppressed=()) -> Result:
    """`pages`: [(sha256, bytes)] of the landed DigitalNZ answers, in the order asked; `suppressed`: notice numbers
    the Gazette's robots file disallows: kept whole privately, flagged, no typed row read."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = Result()
    ev, cv = profile_version(EXPORT_PROFILE), profile_version(CELEBRANT_PROFILE)
    pv, lv = profile_version(PROHIBITION_PROFILE), profile_version(LIQUIDATION_PROFILE)
    base0 = {"document": export_sha, "page": 1, "read_from": "text", "loaded_at": loaded_at}

    held = lines_of(export_bytes, set(only) if only is not None else None)
    for sha, data in pages:
        held += [l for l in capture.lines_of_page(data, sha) if only is None or l["notice"] in only]
    suppressed = set(suppressed)
    by = defaultdict(list)
    for line in held:
        by[line["notice"]].append(line)

    twice = hidden = 0
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
    office = defaultdict(lambda: [0, 0, 0])             # offices.py profile → [recognised, read, set aside]
    ov = {p: profile_version(p) for p in offices.PROFILES}
    mv = profile_version(possessions.PROFILE)
    possessed = [0, 0, 0]                               # recognised, read, set aside
    orgs = None                                         # the celebrant organisation vocabulary, made before the first table
    # the printed celebrant tables last: they are cut by the organisations every other list prints
    for nid in sorted(by, key=lambda n: (any(celebrants.is_table(l["text"]) for l in by[n]), n)):
        if nid in suppressed and notices.number(nid) is not None:
            hidden += 1
            line, others = pick(by[nid])
            twice += len(others)
            for k, l in enumerate(by[nid]):
                out.suppressed.append({"key": f"gazette/{nid}/suppressed/{k}", "notice": nid,
                                       "document": l.get("_document", export_sha), "article": l["article"],
                                       "title": l["title"], "text": l["text"], "published_on": l["published_on"],
                                       "url": l["url"]})
            year, code, n = notices.number(nid)
            out.notices.append({
                "key": f"gazette/{nid}", **base0, "document": line.get("_document", export_sha), "place": f"notice {nid}",
                "reader": READER_NOTICES, "profile": EXPORT_PROFILE, "profile_version": ev,
                "filed": {"notice": nid, "year": year, "section": code, "number": n, "family": notices.family(code),
                          "format": SUPPRESSED, "status": SUPPRESSED, "records": 0, "supersedes": None, "title": "",
                          "published_on": line["published_on"], "url": line["url"], "old_type": line.get("old_type"),
                          "article": line["article"], "source_note": line.get("_note", capture.EXPORT_NOTE)},
            })
            continue
        line, others = pick(by[nid])
        for o, why in others:
            twice += 1
            out.set_aside.append((f"{o.get('_document', export_sha)}/notice {nid} article {o['article']}", "notices", why))
        doc = line.get("_document", export_sha)
        base = {**base0, "document": doc}
        num = notices.number(nid)
        if num is None:
            out.set_aside.append((f"{doc}/notice {nid}", "notices", "not a Gazette notice number"))
            continue
        year, code, n = num
        fmt, status, records, supersedes = NOT_READ, NOT_READ, 0, None
        reader, profile, version = READER_NOTICES, EXPORT_PROFILE, ev
        if prohibitions.recognise(line["title"], line["text"]):
            prohibited += 1
            fmt, reader, profile, version = PROHIBITION_PROFILE, READER_PROHIBITIONS, PROHIBITION_PROFILE, pv
            got = prohibitions.read(line["text"])
            keep(out, nid, doc, got)
            for place, why in got.unread:
                out.set_aside.append((f"{doc}/notice {nid} {place}", "prohibitions", why))
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
                              "superseded_by": None, "superseded_how": None, "superseded_in_error": False,
                              "ordinal": x.ordinal},
                })
                if x.address:
                    out.prohibition_addresses.append((key, x.address, x.formerly))
            if got.acts_on:
                acted.append((nid, got.action, got.acts_on, got.in_error))
                supersedes = ", ".join(got.acts_on)
            records = len(got.persons)
            if records or got.action == "revocation":
                prohibited_read += 1
                status = "read, part set aside" if got.unread else "read"
            else:
                prohibited_aside += 1
                status = "set aside"
                if not got.unread:
                    out.set_aside.append((f"{doc}/notice {nid}", "prohibitions", "recognised, and no person read"))
        elif liquidations.recognise(code, line["title"], line["text"]):
            liquidated += 1
            fmt, reader, profile, version = LIQUIDATION_PROFILE, READER_LIQUIDATIONS, LIQUIDATION_PROFILE, lv
            got = liquidations.read(line["title"], line["text"])
            keep(out, nid, doc, got)
            for place, why in got.unread:
                out.set_aside.append((f"{doc}/notice {nid} {place}", "liquidations", why))
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
                    out.set_aside.append((f"{doc}/notice {nid}", "liquidations", "recognised, and no company read"))
        elif celebrants.recognise(line["title"], line["text"]):     # before the readers by section: a list filed under ar is still a list
            recognised += 1
            fmt, reader, profile, version = CELEBRANT_PROFILE, READER_CELEBRANTS, CELEBRANT_PROFILE, cv
            if celebrants.is_table(line["text"]) and orgs is None:
                orgs = celebrants.organisations(c["filed"]["organisation"] for c in out.celebrants)
            got = celebrants.read(line["text"], orgs if celebrants.is_table(line["text"]) else None)
            for place, why in got.unread:
                out.set_aside.append((f"{doc}/notice {nid} {place}", "celebrants", why))
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
                    out.set_aside.append((f"{doc}/notice {nid}", "celebrants", "recognised, and no record read"))
        elif (hit := next((x for x in COMPANY_READERS if x[0].recognise(code, line["title"], line["text"])), None)):
            mod, profile, reader, kind = hit
            fmt, version = profile, cv_of[profile]
            company[kind][0] += 1
            got = mod.read(line["title"], line["text"])
            keep(out, nid, doc, got)
            for place, why in got.unread:
                out.set_aside.append((f"{doc}/notice {nid} {place}", kind, why))
            stamp = {**base, "reader": reader, "profile": profile, "profile_version": version}
            for c in got.companies:
                out.company_notices.append({
                    "key": f"gazette/{nid}/company/{c.ordinal}", **stamp, "place": f"notice {nid} company {c.ordinal}",
                    "filed": {"notice": nid, "published_on": line["published_on"], "kind": kind, "action": got.action,
                              "company": c.name, "company_number": c.number, "shape": got.shape, "statute": got.statute,
                              "ground": c.ground or got.ground, "by_whom": got.by_whom, "party": c.party or got.party,
                              "role": c.role, "people_named": c.people,
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
                    out.set_aside.append((f"{doc}/notice {nid}", kind, "recognised, and no company read"))
        elif (slug := bankruptcies.kind_of(code, line["title"], line["text"])):
            fmt, reader, profile, version = slug, READER_BANKRUPTCIES, slug, bv_of[slug]
            bankrupt[slug][0] += 1
            got = bankruptcies.read(slug, line["title"], line["text"])
            keep(out, nid, doc, got)
            for place, why in got.unread:
                out.set_aside.append((f"{doc}/notice {nid} {place}", "bankruptcies", why))
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
                    out.set_aside.append((f"{doc}/notice {nid}", "bankruptcies", "recognised, and no person read"))
        elif possessions.recognise(code, line["title"], line["text"]):
            fmt, reader, profile, version = possessions.PROFILE, READER_POSSESSIONS, possessions.PROFILE, mv
            possessed[0] += 1
            got = possessions.read(line["title"], line["text"])
            for place, why in got.unread:
                out.set_aside.append((f"{doc}/notice {nid} {place}", "possessions", why))
            lender, borrower = got.mortgagee, got.mortgagor
            out.possessions.append({
                "key": f"gazette/{nid}/possession", **base, "place": f"notice {nid} possession",
                "reader": READER_POSSESSIONS, "profile": possessions.PROFILE, "profile_version": mv,
                "filed": {"notice": nid, "published_on": line["published_on"], "action": got.action, "asset": got.asset,
                          "statute": got.statute, "mortgagee": None, "mortgagee_kind": lender.kind if lender else "not read",
                          "mortgagee_number": lender.number if lender else None,
                          "mortgagor": None, "mortgagor_kind": borrower.kind if borrower else
                          ("not read" if got.mortgagor_printed else "not printed"),
                          "mortgagor_number": borrower.number if borrower and borrower.kind == "company" else None,
                          "entered_on": got.entered_on, "entered_basis": got.entered_basis, "dated_on": got.dated_on,
                          "corrigendum": got.corrigendum, "property_held": bool(got.property or got.registration)},
                # the join decides which names are shown (load.join_possessions); until then every name is private
                "_private": {"mortgagee": lender, "glued": got.glued, "mortgagor": borrower, "property": got.property,
                             "registration": got.registration},
            })
            records = 1 if lender else 0
            possessed[1 if records else 2] += 1
            status = ("read, part set aside" if got.unread else "read") if records else "set aside"
        elif appointments.recognise(code, line["title"], line["text"]):
            fmt, reader, profile, version = APPOINTMENT_PROFILE, READER_APPOINTMENTS, APPOINTMENT_PROFILE, av
            appointed[0] += 1
            got = appointments.read(line["title"], line["text"])
            keep(out, nid, doc, got)
            for place, why in got.unread:
                out.set_aside.append((f"{doc}/notice {nid} {place}", "appointments", why))
            for x in got.people:
                out.appointments.append({
                    "key": f"gazette/{nid}/appointee/{x.ordinal}", **base, "place": f"notice {nid} appointee {x.ordinal}",
                    "reader": READER_APPOINTMENTS, "profile": APPOINTMENT_PROFILE, "profile_version": av,
                    "filed": {"notice": nid, "published_on": line["published_on"], "body": got.body, "name": x.name,
                              "role": x.role, "statute": got.statute, "by_whom": got.by_whom, "starts_on": got.starts_on,
                              "ends_on": got.ends_on, "dated_on": got.dated_on, "corrigendum": got.corrigendum,
                              "ordinal": x.ordinal, "action": "appointed", "locality": None, "appointee_kind": "person"},
                })
            records = len(got.people)
            appointed[1 if records else 2] += 1
            status = ("read, part set aside" if len(got.unread) else "read") if records else "set aside"
        elif (fam := offices.family(code, line["title"], line["text"])):
            fmt, reader, profile, version = fam, offices.READER, fam, ov[fam]
            office[fam][0] += 1
            records, unread = _read_office(out, fam, ov[fam], nid, line, base, doc)
            office[fam][1 if records else 2] += 1
            status = ("read, part set aside" if unread else "read") if records else "set aside"
        out.notices.append({
            "key": f"gazette/{nid}", **base, "place": f"notice {nid}",
            "reader": reader, "profile": profile, "profile_version": version,
            "filed": {"notice": nid, "year": year, "section": code, "number": n, "family": notices.family(code),
                      "format": fmt, "status": status, "records": records, "supersedes": supersedes,
                      "title": line["title"],
                      "published_on": line["published_on"], "url": line["url"], "old_type": line.get("old_type"),
                      "article": line["article"], "source_note": line.get("_note", capture.EXPORT_NOTE)},
        })

    # a revocation, a substitution or a variation marks the rows of the notice it names
    by_notice = defaultdict(list)
    for p in out.prohibitions:
        by_notice[p["filed"]["notice"]].append(p)
    for nid, how, targets, in_error in acted:
        for t in targets:
            for p in by_notice.get(t, []):
                if p["filed"]["notice"] != nid:
                    p["filed"]["superseded_by"], p["filed"]["superseded_how"] = nid, {
                        "revocation": "revoked", "substitution": "revoked and replaced", "variation": "varied"}[how]
                    p["filed"]["superseded_in_error"] = in_error

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
    # a revocation marks the direction it names, by notice number
    directions = {r["filed"]["notice"]: r for r in out.board_interventions if r["filed"]["action"] != "statutory manager direction revoked"}
    for r in out.board_interventions:
        if r["filed"]["action"] == "statutory manager direction revoked":
            for n in (r["filed"]["names_notices"] or "").split(", "):
                if n in directions and not directions[n]["filed"]["revoked_by"]:
                    directions[n]["filed"]["revoked_by"] = r["filed"]["notice"]
    for slug, (n, ok, aside) in office.items():
        if ok + aside != n:
            raise AssertionError(f"the {slug} notices do not reconcile: {n} recognised, {ok} read, {aside} set aside")
    if possessed[1] + possessed[2] != possessed[0]:
        raise AssertionError(f"the possession notices do not reconcile: {possessed}")
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
    # every published text cut before any property it names; the uncut value is held privately (hard limit 15)
    out.uncut = cut.rows(out)
    out.counts = {"lines": len(held), "notices": len(out.notices), "captured_twice": twice,
                  "pages": len(pages), "from_digitalnz": sum(1 for r in out.notices if r["document"] != export_sha),
                  "suppressed": hidden,
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
                  **{f"{k.split('gazette-')[1].replace('-', '_')}_notices{s}": v[i] for k, v in sorted(office.items())
                     for i, s in enumerate(("", "_read", "_set_aside"))},
                  "office_holders": sum(1 for a in out.appointments if a["profile"] in offices.PROFILES),
                  "board_interventions": len(out.board_interventions),
                  "possession_notices": possessed[0], "possession_notices_read": possessed[1],
                  "possession_notices_set_aside": possessed[2],
                  "set_aside": len(out.set_aside), "cut": len(out.uncut),
                  "not_read": sum(1 for r in out.notices if r["filed"]["format"] == NOT_READ)}
    return out
