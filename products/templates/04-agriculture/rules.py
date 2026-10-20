"""The agriculture counterparty's rules (plan 5.2, use case 4). Pure
functions over the built report, each returning one flag, in the shape of
products/report/templates/subject/rules.py. They stand for the old estate's
four company rules (data-layer/flags/flags/entity_rules.py, rulepack
entity-0.1), taken as ideas and tests, not code, where the held registers
can support them:

  register-status           the old partnership-dissolved, widened: the counterparty's own status on the companies file
                            (removed, in liquidation, in receivership, deregistered); a sole trader's or partnership's
                            business-number entry is not held, so a person start is blocked
  entity-insolvency         the old group-receivership, entity scope: Gazette insolvency notices on the counterparty itself
  officer-group-insolvency  the old group-receivership, officer-group scope: notices on the other companies its people sit on;
                            blocked from a company start (the walk does not follow its officers yet)
  practitioner-repeat       blocked: practitioner names are published (pub.gazette_liquidators) but no route reaches them
                            from a notice, and from a company the group is not walked; a clear only where there is no notice at all
  mpi-coverage              blocked: MPI prosecutions and animal-tracing enforcement are not a published register, and news is not read

and the ones a counterparty check adds: identity, register-removals (a
removal is not insolvency), prohibition and bankruptcy on the people,
officers-of-record, company-holders, hubs-met, young-entity, other-companies
(what became of the people's other companies), namesake-exposure, the
charity and society checks, political-money and replaced-return.

Imports nothing of products.report: the one-way test holds a template folder
to its own code, and the shape loads this file by path. `flag` below builds
the shape's flag dict and refuses what the contract refuses; the shape's
presentation rules check every flag again on every report (rule 9). When the
report lane exposes its contract to templates, `flag` and the readers below
are replaced by it (card a-template-cannot-reach-the-flag-contract-or-the-shapes-rules).

Evidence on the counterparty's confirmed rows is red; the same evidence
reached only through a near link is amber and says it is a namesake's until
confirmed. No flag joins two facts with a word of cause; dates sit side by
side. A check the walk could not have seen is blocked, never clear."""
from __future__ import annotations

import datetime as dt
import re

V = "0.1"
YOUNG_DAYS = 730          # under 24 months registered: worth a question (the old young-entity rule)
NAMESAKE_NOTE_AT = 5      # namesakes set apart at which the report's caveat fires
EXAMPLES = 3              # dated examples a fired flag states in its text

INSOLVENCY_VIEWS = ("gazette_liquidations", "gazette_company_notices")
#: the company notices that are insolvency; a removal (an intention to remove, a restoration) is not, and is its own flag
INSOLVENCY_KINDS = ("winding-up application", "receivership", "administration", "notice to creditors")
#: register statuses, as the companies file writes them (case folded)
INSOLVENT_STATUS = re.compile(r"liquidation|receiv|administration|statutory management", re.I)
ENDED_STATUS = re.compile(r"^(removed|deregistered|dissolved|closed|cancelled|inactive|suspended)$", re.I)
GOING_STATUS = re.compile(r"^registered$", re.I)

GAZETTE_HELD = "New Zealand Gazette liquidation and company notices (pub.gazette_liquidations, pub.gazette_company_notices)"
COMPANIES_HELD = "Companies register (pub.companies, pub.directors, pub.shareholders)"
NOT_HELD_INSOLVENCY = ("the Insolvency Register (interface awaited since 19 September 2026)", "court judgments (step 5.4)")
UNINCORPORATED = "sole traders, general partnerships and trusts: the business-number register outside the companies file (step 5.5)"
LP_PARTNERS = "a limited partnership's general and limited partners (the limited partnerships register)"
CHARITIES_NOT_HELD = ("the Charities Register and its officers (not yet published)",)
MONEY_VIEWS = ("party_return_donors", "party_return_loans", "disclosures", "disclosure_items", "candidate_return_donors", "promoter_people")
NOT_FOLLOWED = ("started from a company, the report lists its officers and holders of record but does not follow them to their own links "
                "and companies yet; start a report from each person listed")


def flag(rule, version, status, severity, text, citations=(), sources_held=(), sources_not_held=(), scope="subject") -> dict:
    """One verdict, in the shape's contract: fired cites, clear names its
    sources, blocked says why."""
    if status not in ("fired", "clear", "blocked") or severity not in ("red", "amber", "info"):
        raise ValueError(f"{rule}: status {status!r}, severity {severity!r}")
    if status == "fired" and not citations:
        raise ValueError(f"{rule}: a fired flag must cite the rows it rests on")
    if status == "clear" and not sources_held:
        raise ValueError(f"{rule}: a clear flag must name the sources it was checked against")
    if status == "blocked" and not text:
        raise ValueError(f"{rule}: a blocked flag must say why the check could not run")
    return {"rule": rule, "version": version, "status": status, "severity": severity, "text": text, "scope": scope,
            "citations": tuple(citations), "sources_held": tuple(sources_held), "sources_not_held": tuple(sources_not_held)}


# ── reading the built report ────────────────────────────────────────────────

def items(report, views=None, grades=("confirmed", "near")):
    for s in report["sections"]:
        for it in s["items"]:
            if (views is None or it["view"] in views) and it["grade"] in grades:
                yield it


def section(report, name):
    for s in report["sections"]:
        if s["name"] == name:
            return s
    return {"name": name, "items": []}


def _all(report) -> dict:
    out = {}
    for it in [report.get("subject")] + list(report.get("members", [])) + [it for s in report["sections"] for it in s["items"]]:
        if it:
            out.setdefault(it["ref"], it)
    return out


def _as_of(report) -> dt.date:
    try:
        return dt.date.fromisoformat(report.get("as_of") or "")
    except ValueError:
        return dt.date.today()


def _date(x):
    if isinstance(x, dt.datetime):
        return x.date()
    if isinstance(x, dt.date):
        return x
    try:
        return dt.date.fromisoformat(str(x)[:10]) if x else None
    except ValueError:
        return None


def _company_start(report) -> bool:
    return report["subject"]["view"] == "companies"


def _person_start(report) -> bool:
    return report["subject"]["kind"] == "person"


def _other_start(report):
    """A start row that is neither a company nor a person (a filed donation,
    a society, a notice): the checks over a company's or a person's record
    cannot clear from it."""
    if _company_start(report) or _person_start(report):
        return None
    s = report["subject"]
    article = "an" if s["kind"][:1] in "aeiou" else "a"
    return (f"the report starts from {article} {s['kind']} row (pub.{s['view']}), not a company or a person: the record these checks read is not "
            f"walked from it, so no clear is given; start the report from the company or from a person row")


def _subject_key(report) -> str:
    return report["subject"]["ref"].split(":", 1)[1]


def _on_subject(report, it) -> bool:
    """A notice on the counterparty company itself."""
    return it.get("via") == report["subject"]["ref"] or (it["row"].get("register_key") or "") == _subject_key(report)


def _walk_short(report) -> bool:
    w = report.get("walk") or {}
    return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))


def _role_on(report, company_ref: str) -> list:
    """The subject's own rows on a company: the role or holding and its dating text."""
    out = []
    for it in _all(report).values():
        if it["view"] in ("directors", "shareholders") and it["grade"] == "confirmed":
            ent = (it.get("entity") or {}).get("ref")
            if ent == company_ref or it["row"].get("entity_key") and f"companies:{it['row']['entity_key']}" == company_ref:
                out.append(it)
    return out


def _side_by_side(report, notices: list) -> str:
    """'COMPANY: notice D; the subject's row: director, from A to B' for the
    first few notices. Two dates, no word between them."""
    bits = []
    for it in notices[:EXAMPLES]:
        if _company_start(report):
            bits.append(f"{it['title']}: notice {it['dates']['text']}; the officers' dates are in the officers section")
            continue
        roles = _role_on(report, it.get("via") or "")
        mine = "; ".join(f"the subject's row: {r['row'].get('role_type') or 'shareholder of record'}, {r['dates']['text']}" for r in roles[:2]) \
            or "the subject's row on it is in the officers section"
        bits.append(f"{it['title']}: notice {it['dates']['text']}; {mine}")
    more = f"; and {len(notices) - EXAMPLES} more" if len(notices) > EXAMPLES else ""
    return " | ".join(bits) + more


def _insolvency(it) -> bool:
    return it["view"] == "gazette_liquidations" or (it["view"] == "gazette_company_notices" and it["row"].get("kind") in INSOLVENCY_KINDS)


def _removal(it) -> bool:
    return it["view"] == "gazette_company_notices" and not _insolvency(it)


def _notices(report, grades=("confirmed",)):
    return [it for it in items(report, INSOLVENCY_VIEWS, grades)]


# ── the old four, where the held registers support them ─────────────────────

def register_status(report):
    """The counterparty's own status on the companies file: an insolvency
    status or an ended entity is red; one that has left the latest file is
    amber; registered and in the latest file is clear."""
    s = report["subject"]
    if not _company_start(report):
        why = _other_start(report) or (f"the counterparty is a person: a register status is a company's, and the business-number entry "
                                       f"of a sole trader or a partnership is not held")
        return flag("register-status", V, "blocked", "red", why, sources_not_held=(UNINCORPORATED,))
    r = s["row"]
    status = (r.get("status") or "").strip()
    kind = r.get("entity_type") or "entity"
    nh = (UNINCORPORATED,) + ((LP_PARTNERS,) if "partnership" in kind.lower() else ())
    reg = _date(r.get("registered_on"))
    removed = _date(r.get("removed_on"))
    when = f"registered {reg.isoformat()}" if reg else "registration date not stated"
    if removed:
        when += f", removed {removed.isoformat()}"
    if INSOLVENT_STATUS.search(status):
        return flag("register-status", V, "fired", "red", f"the companies file gives the counterparty the status {status!r} ({kind}; {when})",
                    citations=(s["ref"],), sources_not_held=nh + NOT_HELD_INSOLVENCY, scope="entity")
    if ENDED_STATUS.match(status) or removed:
        return flag("register-status", V, "fired", "red", f"the counterparty is no longer a registered entity: status {status!r} ({kind}; {when})",
                    citations=(s["ref"],), sources_not_held=nh, scope="entity")
    if not r.get("in_latest", True):
        return flag("register-status", V, "fired", "amber", f"the counterparty is not in the latest companies file; its last status was {status!r} "
                    f"({kind}; {when}); the interface check of step 5.5 would date the change", citations=(s["ref"],), sources_not_held=nh, scope="entity")
    if GOING_STATUS.match(status):
        return flag("register-status", V, "clear", "red", f"registered ({kind}; {when}) in the latest companies file",
                    sources_held=("Companies register status (pub.companies)",), sources_not_held=nh, scope="entity")
    return flag("register-status", V, "fired", "amber", f"the companies file gives a status this check does not know: {status!r} ({kind}; {when})",
                citations=(s["ref"],), sources_not_held=nh, scope="entity")


def entity_insolvency(report):
    """Gazette insolvency notices on the counterparty company itself."""
    if not _company_start(report):
        if _other_start(report):
            return flag("entity-insolvency", V, "blocked", "red", _other_start(report), sources_not_held=NOT_HELD_INSOLVENCY)
        return flag("entity-insolvency", V, "clear", "red",
                    "the counterparty is a person: a Gazette company notice is on a company, and those on the person's companies are read by "
                    "officer-group-insolvency", sources_held=(GAZETTE_HELD,), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
    own = [it for it in _notices(report) if _insolvency(it) and _on_subject(report, it)]
    if own:
        return flag("entity-insolvency", V, "fired", "red", f"{len(own)} Gazette insolvency notice(s) on the counterparty itself: {_side_by_side(report, own)}",
                    citations=tuple(it["ref"] for it in own), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
    return flag("entity-insolvency", V, "clear", "red",
                "no Gazette liquidation, receivership, administration, winding-up or creditors' notice on the counterparty",
                sources_held=(GAZETTE_HELD + ", joined to the company by its number",), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")


def officer_group_insolvency(report):
    """Gazette insolvency notices on the other companies the counterparty's
    people sit on. From a person start these are the person's companies."""
    if _company_start(report):
        return flag("officer-group-insolvency", V, "blocked", "red", f"{NOT_FOLLOWED}: a liquidation of a director's other company cannot be seen",
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if _other_start(report):
        return flag("officer-group-insolvency", V, "blocked", "red", _other_start(report), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    conf = [it for it in _notices(report) if _insolvency(it)]
    nearby = [it for it in _notices(report, ("near",)) if _insolvency(it)]
    if conf:
        cos = len({it.get("via") for it in conf})
        return flag("officer-group-insolvency", V, "fired", "red",
                    f"{len(conf)} Gazette insolvency notice(s) on {cos} company(ies) the counterparty has or had a row on; "
                    f"each date beside the counterparty's: {_side_by_side(report, conf)}",
                    citations=tuple(it["ref"] for it in conf), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if nearby:
        return flag("officer-group-insolvency", V, "fired", "amber",
                    f"{len(nearby)} Gazette insolvency notice(s) on companies reached only through a near link: a namesake's companies, "
                    f"not the counterparty's until confirmed", citations=tuple(it["ref"] for it in nearby), sources_not_held=NOT_HELD_INSOLVENCY,
                    scope="near")
    if not section(report, "other-companies")["items"]:
        return flag("officer-group-insolvency", V, "clear", "red", "the counterparty has no company row in the registers held, so no company notice can reach it",
                    sources_held=(COMPANIES_HELD,), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if _walk_short(report):
        return flag("officer-group-insolvency", V, "blocked", "red",
                    "no Gazette insolvency notice on the companies the walk read, but the walk stopped before reading every company "
                    "the counterparty has a row on; start a report from each company left out", scope="officer-group")
    return flag("officer-group-insolvency", V, "clear", "red",
                "no Gazette liquidation, receivership, administration, winding-up or creditors' notice on any company the counterparty has or had a row on",
                sources_held=(GAZETTE_HELD,), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")


def practitioner_repeat(report):
    """The same insolvency practitioner across distinct companies of the
    group (the old orchestrated-wind-down question). The notices carry a
    count of practitioners, not their names; the names are in
    pub.gazette_liquidators, which no route reaches from a notice."""
    events = [it for it in _notices(report, ("confirmed", "near")) if _insolvency(it)]
    if not events and _person_start(report) and not _walk_short(report):
        return flag("practitioner-repeat", V, "clear", "amber", "no insolvency notice in the counterparty's companies, so no practitioner pattern to assess",
                    sources_held=(GAZETTE_HELD,), scope="officer-group")
    why = []
    if _company_start(report):
        why.append(NOT_FOLLOWED)
    elif _other_start(report):
        why.append(_other_start(report))
    elif _walk_short(report) and not events:
        why.append("the walk stopped before reading every company the counterparty has a row on")
    if events:
        why.append(f"{len(events)} insolvency notice(s) on {len({it.get('via') for it in events})} company(ies) are listed, but a notice carries only "
                   f"a count of its practitioners; their names (pub.gazette_liquidators) are not reached from a notice")
    return flag("practitioner-repeat", V, "blocked", "info", "; ".join(why) + "; so no practitioner pattern can be assessed", scope="officer-group")


def mpi_coverage(report):
    return flag("mpi-coverage", V, "blocked", "info",
                "MPI's prosecutions and animal-tracing (NAIT) enforcement are not a published register, and news coverage is not read "
                "(the press work is parked); this check cannot run",
                sources_not_held=("MPI prosecutions and NAIT enforcement (not published as data)", "news coverage (not read)"))


# ── the held registers add ──────────────────────────────────────────────────

def register_removals(report):
    """Gazette notices that the company is to be, or was, removed from the
    register, or restored to it. Not insolvency. On the counterparty itself
    amber; on a person's companies info."""
    if _other_start(report):
        return flag("register-removals", V, "blocked", "info", _other_start(report))
    conf = [it for it in _notices(report) if _removal(it)]
    if _company_start(report):
        own = [it for it in conf if _on_subject(report, it)]
        if own:
            return flag("register-removals", V, "fired", "amber", f"{len(own)} Gazette removal or restoration notice(s) on the counterparty: "
                        f"{_side_by_side(report, own)}", citations=tuple(it["ref"] for it in own), scope="entity")
        return flag("register-removals", V, "clear", "amber", "no Gazette removal or restoration notice on the counterparty",
                    sources_held=("New Zealand Gazette company notices (pub.gazette_company_notices)",), scope="entity")
    if conf:
        return flag("register-removals", V, "fired", "info",
                    f"{len(conf)} Gazette removal or restoration notice(s) on {len({it.get('via') for it in conf})} company(ies) the counterparty has "
                    f"or had a row on; each date beside the counterparty's: {_side_by_side(report, conf)}", citations=tuple(it["ref"] for it in conf),
                    scope="officer-group")
    return flag("register-removals", V, "clear", "info", "no Gazette removal or restoration notice on a company the counterparty has a confirmed row on",
                sources_held=("New Zealand Gazette company notices (pub.gazette_company_notices)",), scope="officer-group")


def _in_force(report, it) -> str:
    as_of = _as_of(report)
    end = _date(it["row"].get("ends_on"))
    if it["row"].get("permanent"):
        return f"permanent; in force on {as_of.isoformat()}"
    if not end:
        return "no end filed"
    return f"in force on {as_of.isoformat()}" if end >= as_of else f"ended before {as_of.isoformat()}"


def prohibition(report):
    """A Gazette director prohibition on the counterparty, or on a person
    the counterparty is. From a company, its officers' own links are not
    followed, so it is blocked."""
    live = [it for it in items(report, ("gazette_prohibitions",)) if not it.get("suppressed")]   # a revoked prohibition is never counted
    conf = [it for it in live if it["grade"] == "confirmed"]
    nearby = [it for it in live if it["grade"] == "near"]
    if conf:
        return flag("prohibition", V, "fired", "red", f"{len(conf)} Gazette director prohibition notice(s) confirmed to the counterparty: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']}; {_in_force(report, it)})" for it in conf[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in conf))
    if nearby:
        return flag("prohibition", V, "fired", "amber",
                    f"{len(nearby)} Gazette director prohibition notice(s) under a name near the counterparty's; a namesake's until confirmed: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']}; {_in_force(report, it)}; near: {it.get('reason')})" for it in nearby[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in nearby), scope="near")
    if _company_start(report):
        return flag("prohibition", V, "blocked", "red", f"{NOT_FOLLOWED}: a prohibition on a director is joined to the director's own row, "
                    "which is not followed", scope="officer-group")
    if _other_start(report):
        return flag("prohibition", V, "blocked", "red", _other_start(report))
    w = report.get("walk") or {}
    if not w.get("links_built"):
        return flag("prohibition", V, "blocked", "red", "no links are published, so a prohibition under the counterparty's name cannot be reached")
    if w.get("links_omitted"):
        return flag("prohibition", V, "blocked", "red",
                    f"the walk left {w['links_omitted']:,} link(s) unread past its limit; a prohibition could be among them, so no clear is given")
    return flag("prohibition", V, "clear", "red",
                "no Gazette director prohibition confirmed or near the counterparty: the link rules join every prohibition notice by name, "
                "and every link from the counterparty's rows was read",
                sources_held=("New Zealand Gazette prohibition notices (pub.gazette_prohibitions), joined by name in pub.links",))


def bankruptcy(report):
    live_c = [it for it in items(report, ("gazette_bankruptcies",), ("confirmed",)) if not it.get("suppressed")]
    live_n = [it for it in items(report, ("gazette_bankruptcies",), ("near",)) if not it.get("suppressed")]
    if live_c:
        return flag("bankruptcy", V, "fired", "red", f"{len(live_c)} Gazette bankruptcy notice(s) confirmed to the counterparty: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in live_c[:EXAMPLES]), citations=tuple(it["ref"] for it in live_c))
    if live_n:
        return flag("bankruptcy", V, "fired", "amber", f"{len(live_n)} Gazette bankruptcy notice(s) under a name near the counterparty's; "
                    "a namesake's until confirmed", citations=tuple(it["ref"] for it in live_n), scope="near")
    return flag("bankruptcy", V, "blocked", "red",
                "Gazette bankruptcy notices are published, but no link rule joins one to a person yet, so this report cannot see a bankruptcy "
                "of the counterparty or its people; the blank is not a clear", sources_not_held=NOT_HELD_INSOLVENCY)


def _current(it) -> bool:
    return bool(it["row"].get("in_latest")) and not it["row"].get("ended_on")


def officers_of_record(report):
    """Who the companies file names on the counterparty now: a company with
    no current director in the latest file is a question for the reader."""
    if _other_start(report):
        return flag("officers-of-record", V, "blocked", "info", _other_start(report), scope="entity")
    if not _company_start(report):
        return flag("officers-of-record", V, "clear", "info", "the counterparty is a person: its own roles are listed in the officers section",
                    sources_held=(COMPANIES_HELD,), scope="entity")
    r = report["subject"]["row"]
    if "partnership" in (r.get("entity_type") or "").lower():
        return flag("officers-of-record", V, "blocked", "info", "a limited partnership has general and limited partners, not directors, and the "
                    "limited partnerships register that names them is not held", sources_not_held=(LP_PARTNERS,), scope="entity")
    sec = [it for it in section(report, "officers")["items"] if it.get("via") == report["subject"]["ref"]]
    dirs = [it for it in sec if it["view"] == "directors"]
    holders = [it for it in sec if it["view"] == "shareholders"]
    now = [it for it in dirs if _current(it)]
    omitted = section(report, "officers").get("omitted") or 0
    tail = f"; {omitted:,} row(s) past the walk's limit, not listed" if omitted else ""
    text = (f"{len(now)} current director(s) and {len(dirs) - len(now)} past or not in the latest file; "
            f"{len(holders)} holder(s) of record, {sum(1 for it in holders if _current(it))} in the latest file{tail}")
    going = GOING_STATUS.match((r.get("status") or "").strip()) and r.get("in_latest", True)
    if not now and not omitted and going:
        return flag("officers-of-record", V, "fired", "amber", f"the companies file names no current director of the counterparty: {text}",
                    citations=tuple(it["ref"] for it in dirs) or (report["subject"]["ref"],), scope="entity")
    return flag("officers-of-record", V, "clear", "info", text, sources_held=("Companies register directors and shareholders (pub.directors, pub.shareholders)",),
                scope="entity")


def company_holders(report):
    """A holder of record that is itself a company: the file gives it no
    business number, so who stands behind it is not followed."""
    rows = [it for it in section(report, "officers")["items"] if it["view"] == "shareholders" and it["row"].get("shareholder_type") == "company"]
    if rows:
        return flag("company-holders", V, "fired", "info",
                    f"{len(rows)} holder(s) of record are companies: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in rows[:EXAMPLES])
                    + "; the companies file gives a company holder no business number, so its own holders and directors are not followed",
                    citations=tuple(it["ref"] for it in rows), scope="entity")
    return flag("company-holders", V, "clear", "info", "no holder of record listed is a company",
                sources_held=("Companies register shareholders (pub.shareholders)",), scope="entity")


HUB_WORDS = {"professional-director": "a professional director", "nominee": "a nominee or trustee holder", "crown": "the Crown",
             "busy-address": "a busy registered office", "thousand-address": "a registered office with a thousand companies"}


def _hub_text(h) -> str:
    """One example, in this rule's own words: the shape's hub text is written
    for the memo's hub list, not for a flag."""
    ev = h.get("evidence") if isinstance(h.get("evidence"), dict) else {}
    if h["kind"] == "professional-director":
        return f"{h['title']}, whose group holds {ev.get('directorships', 'many'):,} directorships" if isinstance(ev.get("directorships"), int) else h["title"]
    if h["kind"] in ("busy-address", "thousand-address"):
        return f"{h['title']}, whose registered office {ev.get('companies', 'many'):,} companies share" if isinstance(ev.get("companies"), int) else h["title"]
    if h["kind"] == "nominee":
        return f"{h['title']}, a holder of record for others"
    return h["title"]


def hubs_met(report):
    """The hubs among the counterparty and its officers: a professional
    director, a nominee or trustee holder, the Crown, a busy or thousand-
    company registered office. What a hub joins means little on its own."""
    if not report.get("hubs"):
        return flag("hubs-met", V, "clear", "info", "no professional director, nominee or trustee holder, Crown holder or busy registered office met",
                    sources_held=("pub.directors", "pub.shareholders", "pub.company_addresses", "pub.groups"))
    kinds = {}
    for h in report["hubs"]:
        kinds.setdefault(h["kind"], []).append(h)
    bits = [f"{HUB_WORDS.get(k, k)} ({len({h['title'] for h in v})}): {_hub_text(v[0])}" for k, v in sorted(kinds.items())]
    return flag("hubs-met", V, "fired", "info", "hubs met, each shown as the register states it; a role, holding or address shared through one means little on its own: " + "; ".join(bits),
                citations=tuple(sorted({h["ref"] for h in report["hubs"]})))


def young_entity(report):
    as_of = _as_of(report)
    young = []
    pool = [report["subject"]] if _company_start(report) else list(items(report, ("companies",), ("confirmed",)))
    for it in pool:
        reg = _date(it["row"].get("registered_on"))
        if reg and (as_of - reg).days < YOUNG_DAYS:
            young.append((it, reg))
    who = "the counterparty was" if _company_start(report) else f"{len(young)} company(ies) the counterparty has a confirmed row on were"
    if young:
        return flag("young-entity", V, "fired", "info", f"{who} registered under 24 months before {as_of.isoformat()}: "
                    + "; ".join(f"{it['title']} (registered {reg.isoformat()})" for it, reg in young[:EXAMPLES]),
                    citations=tuple(it["ref"] for it, _ in young))
    if _other_start(report):
        return flag("young-entity", V, "blocked", "info", _other_start(report))
    return flag("young-entity", V, "clear", "info", "registered 24 months ago or more" if _company_start(report)
                else "no company the counterparty has a confirmed row on was registered under 24 months ago",
                sources_held=("Companies register registration dates (pub.companies)",),
                sources_not_held=("GST registration dates (the old rule's measure; not held)",))


def other_companies(report):
    """What became of the people's other companies, by their register
    status. From a person these are the person's companies; from a company
    they are not walked."""
    if _company_start(report):
        return flag("other-companies", V, "blocked", "amber", f"{NOT_FOLLOWED}: the officers' other companies and what became of them cannot be listed",
                    scope="officer-group")
    if _other_start(report):
        return flag("other-companies", V, "blocked", "amber", _other_start(report), scope="officer-group")
    cos = list(items(report, ("companies",), ("confirmed",)))
    failed = [it for it in cos if INSOLVENT_STATUS.search(it["row"].get("status") or "")]
    ended = [it for it in cos if it not in failed and (ENDED_STATUS.match((it["row"].get("status") or "").strip()) or it["row"].get("removed_on"))]
    if failed or ended:
        bits = []
        if failed:
            bits.append(f"{len(failed)} with an insolvency status: " + "; ".join(f"{it['title']} ({it['row'].get('status')}; {it['dates']['text']})"
                                                                                  for it in failed[:EXAMPLES]))
        if ended:
            bits.append(f"{len(ended)} removed or ended: " + "; ".join(f"{it['title']} ({it['row'].get('status')}; {it['dates']['text']})"
                                                                     for it in ended[:EXAMPLES]))
        return flag("other-companies", V, "fired", "amber" if failed else "info",
                    f"of {len(cos)} company(ies) the counterparty has or had a row on, " + "; ".join(bits),
                    citations=tuple(it["ref"] for it in failed + ended), scope="officer-group")
    if _walk_short(report):
        return flag("other-companies", V, "blocked", "amber", "the walk stopped before reading every company the counterparty has a row on",
                    scope="officer-group")
    return flag("other-companies", V, "clear", "amber", f"each of the {len(cos)} company(ies) the counterparty has a confirmed row on is registered"
                if cos else "the counterparty has no confirmed company row", sources_held=("Companies register status (pub.companies)",), scope="officer-group")


def namesake_exposure(report):
    names = list(section(report, "identity")["items"])
    nearby_elsewhere = [it for s in report["sections"] if s["name"] != "identity" for it in s["items"] if it["grade"] == "near"]
    w = report.get("walk") or {}
    g = report.get("group") or {}
    bits = []
    if len(names) >= NAMESAKE_NOTE_AT:
        bits.append(f"{len(names)} namesake row(s) set apart")
    if nearby_elsewhere:
        bits.append(f"{len(nearby_elsewhere)} near row(s) in the record sections, each with its reason")
    if w.get("links_omitted"):
        bits.append(f"{w['links_omitted']:,} link(s) past the walk's limit, not read")
    if g.get("omitted"):
        bits.append(f"{g['omitted']:,} row(s) of the group past the walk's limit, not listed")
    if g.get("contested"):
        bits.append("the group is contested as a whole")
    if bits:
        cites = tuple(it["ref"] for it in names + nearby_elsewhere) or (report["subject"]["ref"],)
        return flag("namesake-exposure", V, "fired", "info", "the report's own uncertainty: " + "; ".join(bits), citations=cites)
    return flag("namesake-exposure", V, "clear", "info", f"low namesake exposure: {len(names)} namesake row(s) set apart and every link read",
                sources_held=("pub.links", "pub.groups"))


def charity_officer_roles(report):
    # the officers of a society the report starts from are that society's, not the counterparty's roles
    conf = [it for it in items(report, ("society_officers",), ("confirmed",)) if it.get("via") != report["subject"]["ref"]]
    if conf:
        return flag("charity-officer-roles", V, "fired", "info",
                    f"officer of {len({it.get('via') for it in conf})} incorporated society(ies): "
                    + "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in conf[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in conf), sources_not_held=CHARITIES_NOT_HELD)
    if _company_start(report):
        return flag("charity-officer-roles", V, "blocked", "info", f"{NOT_FOLLOWED}: their society roles are not read",
                    sources_not_held=CHARITIES_NOT_HELD, scope="officer-group")
    if _other_start(report):
        return flag("charity-officer-roles", V, "blocked", "info", _other_start(report), sources_not_held=CHARITIES_NOT_HELD)
    return flag("charity-officer-roles", V, "clear", "info", "no incorporated society officer role confirmed to the counterparty",
                sources_held=("Incorporated Societies Register officers (pub.society_officers)",), sources_not_held=CHARITIES_NOT_HELD)


def charity_integrity_marks(report):
    return flag("charity-integrity-marks", V, "blocked", "red",
                "the Charities Register, whose officer rows carry its own banned-director and undischarged-bankrupt marks, is not published yet; "
                "this check cannot run", sources_not_held=CHARITIES_NOT_HELD)


def political_money(report):
    money = list(items(report, MONEY_VIEWS, ("confirmed",)))
    if money:
        return flag("political-money", V, "fired", "info", f"{len(money)} row(s) of political money or a promoter's role confirmed to the counterparty; "
                    "each listed in its section with its date and the party or candidate filed", citations=tuple(it["ref"] for it in money))
    near_money = [it for it in section(report, "identity")["items"] if it["view"] in MONEY_VIEWS]
    return flag("political-money", V, "clear", "info", "no donation, loan, disclosure or promoter's role confirmed to the counterparty"
                + (f"; {len(near_money)} filed under a name it only shares are listed with the namesakes" if near_money else ""),
                sources_held=("Electoral Commission returns and disclosures", "Register of Promoters"),
                sources_not_held=("a candidate's own return, not yet joined to a person",))


def replaced_rows(report):
    rep = [it for it in items(report) if it.get("replaced_by")]
    if rep:
        return flag("replaced-return", V, "fired", "info", f"{len(rep)} row(s) come from a return the Commission has since replaced by an amendment; "
                    "each is shown with its replacement named and is never summed", citations=tuple(it["ref"] for it in rep))
    return flag("replaced-return", V, "clear", "info", "no row shown comes from a replaced return",
                sources_held=("pub.party_return_donors", "pub.party_return_totals", "pub.candidate_return_donors"))


def identity(report):
    """Who the counterparty is: a company by its NZBN; a person by the rows a
    rule confirms are the same person, and whether the watch contests them."""
    g = report.get("group") or {}
    subj = report["subject"]
    if _company_start(report):
        nzbn = subj["row"].get("nzbn") or _subject_key(report).rsplit("/", 1)[-1]
        return flag("identity", V, "clear", "info", f"a company, NZBN {nzbn}: its number is the link, and no other row is the counterparty",
                    sources_held=("Companies register (pub.companies)",), scope="entity")
    if _other_start(report):
        return flag("identity", V, "blocked", "info", _other_start(report))
    if not g.get("built"):
        return flag("identity", V, "blocked", "info", "no links are published: the counterparty is this one row, and every same name elsewhere is a namesake")
    if g.get("contested"):
        return flag("identity", V, "fired", "amber", f"the counterparty's group of {g.get('size', 1)} rows is contested as a whole: the watch found a sign "
                    "that its confirmed links cover two people, so every other row of it is listed as near", citations=(subj["ref"],))
    n = g.get("size", 1)
    return flag("identity", V, "clear", "info", "the counterparty is this one row: no confirmed link reaches it" if n == 1 else
                f"the counterparty is a group of {n} rows confirmed the same person, not contested", sources_held=("pub.groups", "pub.links"))


RULES = (identity, register_status, entity_insolvency, officer_group_insolvency, register_removals, prohibition, bankruptcy,
         practitioner_repeat, other_companies, officers_of_record, company_holders, hubs_met, young_entity, namesake_exposure,
         charity_officer_roles, charity_integrity_marks, mpi_coverage, political_money, replaced_rows)
