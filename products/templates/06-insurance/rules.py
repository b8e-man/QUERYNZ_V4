"""The insurance underwriting rules (plan 5.2, use case 6). Pure functions
over the built report, each returning one flag. A commercial underwriter asks
"what stands against this business and its people" before pricing the risk.
The rules stand for the old estate's insurance checks (its requirements,
section 2.7: MC-I2 the Gazette events, the sister-company receivership
through the Gazette and shared directors, the industry-classification
change; WorkSafe's prosecution facts, absent from the official interface)
and its company and person rules (data-layer/flags/flags/entity_rules.py,
entity-0.1: group-receivership; person_rules.py, person-0.2:
liquidation-history, prohibition, young-entity, namesake-exposure), taken as
ideas and tests, not code, where the held registers can support them:

  entity-status            the company's own register status
  young-entity             registered under 24 months
  insolvency-event         Gazette liquidations, winding-up applications, receiverships, administrations, creditors' notices
                           and deeds of company arrangement on the entity, each dated from its notice
  register-events          removals, restorations, dissolutions, rectifications, amalgamations: not insolvency
  officer-churn            started from a company: directors appointed in the last twelve months, or rows that left the file;
                           never clear, because a director who left before July 2026 is not seen
  sister-company-failure   started from a person: each of the person's companies that failed, the failure dated from its Gazette
                           notice and the person's own role on that company dated beside it
  other-current-companies  the person's going companies and their states
  prohibition, bankruptcy  on the person, confirmed or near; blocked from a company
  practitioner-roles       the person named as liquidator: an insolvency practitioner, not an officer of the failed company
  namesake-exposure        the report's own uncertainty
  walk-coverage            how many companies reached had their notices and officers read
  subject-hub              the person is a professional director, a nominee or the Crown
  past-roles               blocked: current roles only
  safety-record            blocked, never clear: WorkSafe's prosecutions and enforceable undertakings, Fire and Emergency's notices
  regulator-actions, court-judgments, tribunals, change-history, status-history, mortgagee-possession, insolvency-register,
  securities-register      blocked: not held, or published and not reachable

The builder adds its common rules for every template (group-standing,
hubs-met, replaced-return); this file carries no copy of them.

Every rule branches on the start: a person, a company, or anything else.
From a company the walk lists the officers and holders and does not follow
them (the agriculture lesson), so a check through a person is blocked and
says to start a report from each person. Evidence on confirmed rows is red
or amber; the same evidence reached only through a near link is amber at
most and says it is a namesake's until confirmed. A check the walk could not
have seen is blocked, never clear. Dates sit side by side; no flag joins two
facts with a word of cause, none calls a holder an owner, and none prints an
address: the standing section shows it.

Imports nothing of products.report: the one-way test holds a template folder
to its own code. The shape loads this file by path and binds the name
`contract` (products/report/contract.py) before it runs."""
from __future__ import annotations

import datetime as dt
import re

V = "0.1"
YOUNG_DAYS = 730          # under 24 months registered (the old young-entity rule)
#: officer churn: this many current directors appointed within CHURN_DAYS of the report's day, not counting those appointed within
#: AT_START_DAYS of the company's registration (a new company's first board is not churn). Settings, not findings.
CHURN_DAYS = 365
CHURN_AT = 2
AT_START_DAYS = 30
NAMESAKE_NOTE_AT = 5      # namesakes set apart at which the report's caveat fires
NAMESAKE_PARTIAL_AT = 50  # past this many namesakes the report is declared partial
EXAMPLES = 3              # dated examples a fired flag states in its text
#: whether a published view holds past roles with their end dates. It does not (measured 2026-10-20 by banking-1): the companies file
#: lists current roles only. While False, a check over a person's companies, or over a board's departures, fires on what it sees and
#: never clears.
HISTORY = False
PAST_NOT_HELD = ("the companies file lists current roles only: a company the person left, or that was struck off with them on it, is not "
                 "seen, nor its failure")
DEPARTED_NOT_HELD = ("the companies file lists current roles only: a director who left the board before July 2026 is not seen, and one who "
                     "left since carries no end date")

#: the company notices that are an insolvency; a receiver's ceasing to act ends one and dates nothing
INSOLVENCY_KINDS = ("winding-up application", "receivership", "administration", "notice to creditors", "deed of company arrangement")
#: what a register event records, by the lane's kind; a removal whose action is a restoration is a restoration
EVENT_KIND = {"removal": "removal", "dissolution": "dissolution", "restoration": "restoration", "overseas company": "an overseas company ceasing",
              "rectification": "the Registrar's rectification", "transfer out": "a transfer out of New Zealand", "amalgamation": "amalgamation"}
INSOLVENT_STATUS = re.compile(r"liquidation|receiv|administration|statutory management", re.I)
ENDED_STATUS = re.compile(r"^(removed|deregistered|dissolved|closed|cancelled|inactive|suspended)$", re.I)
GOING_STATUS = re.compile(r"^registered$", re.I)
SAME_NAME = re.compile(r"^company-name")
HUB_KINDS = ("professional-director", "nominee", "crown")
#: the words a fired flag must not carry, the shape's own (rules 3 and 4): a register's name that holds one is not quoted in a flag
UNSAFE = re.compile(contract.CAUSE.pattern + "|" + contract.OWNER.pattern, re.I)   # noqa: F821  (bound by the loader)

GAZETTE_HELD = "New Zealand Gazette liquidation and company notices (pub.gazette_liquidations, pub.gazette_company_notices)"
NOTICES_HELD = "New Zealand Gazette company notices (pub.gazette_company_notices)"
COMPANIES_HELD = "Companies register (pub.companies, pub.directors, pub.shareholders)"
INSOLVENCY_REGISTER = "the Official Assignee's Insolvency Register (interface awaited since 19 September 2026)"
COURTS = "court judgments: the OpenLaw case-law lane and the courts register (step 5.4)"
NOT_HELD_INSOLVENCY = (INSOLVENCY_REGISTER, COURTS)
CHANGE_HISTORY = ("the companies change history: not held before 16 August 2026, held and unread since (former names, trading names, "
                  "industry classification, earlier directors)")
WORKSAFE = "WorkSafe New Zealand's prosecutions and enforceable undertakings (the release texts are held and not yet read into a register)"
FIRE = "Fire and Emergency New Zealand's notices"
REGULATORS = ("the Commerce Commission's cases (held and not yet read into a register)",
              "the Financial Markets Authority's warnings and actions (held and not yet read into a register)")
TRIBUNALS = ("the Employment Relations Authority's determinations, and the Employment Court's judgments", "the Disputes Tribunal's decisions")
SECURITIES = "the Personal Property Securities Register (interface awaited since 19 September 2026)"
FSP = "the financial service providers register (interface awaited since 19 September 2026)"
POSSESSIONS = "a mortgagee's entry into possession (pub.gazette_possessions: published, not in the report's catalogue)"
STATES = "a company's dated status history (pub.company_states: published, not in the report's catalogue)"
LP_PARTNERS = "a limited partnership's general and limited partners (the limited partnerships register)"
NOT_FOLLOWED = ("started from a company, the report lists its officers and holders of record but does not follow them to their own links "
                "and companies yet; start a report from each person listed")


flag, items, section, all_items = contract.flag, contract.items, contract.section, contract.all_items   # noqa: F821  (bound by the loader)


# ── reading the built report ────────────────────────────────────────────────

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
    """A person row, or a filed row that takes the group of the person row a
    confirmed link names: the walk reads that person's record."""
    return report["subject"]["kind"] == "person" or bool((report.get("group") or {}).get("via"))


def _other_start(report):
    """A start row that is neither a company nor a person (a society, a
    notice): the record these checks read is not walked from it."""
    if _company_start(report) or _person_start(report):
        return None
    s = report["subject"]
    article = "an" if s["kind"][:1] in "aeiou" else "a"
    return (f"the report starts from {article} {s['kind']} row (pub.{s['view']}), not a person or a company: the record these checks read is not "
            f"walked from it, so no clear is given; start the report from a person row or from the company")


def _subject_key(report) -> str:
    return report["subject"]["ref"].split(":", 1)[1]


def _on_subject(report, it) -> bool:
    return it.get("via") == report["subject"]["ref"] or (it["row"].get("register_key") or "") == _subject_key(report)


def _walk_short(report) -> bool:
    w = report.get("walk") or {}
    return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))


def _short_text(report) -> str:
    w = report.get("walk") or {}
    n = (w.get("entities_not_expanded") or 0) + (w.get("entities_omitted") or 0)
    return f"; the walk did not read the notices on {n:,} further company(ies)" if n else ""


def _name(it) -> str:
    """A row's title for a flag's text; a register name that carries a word
    the shape reads as cause or ownership is not quoted (the section lists it)."""
    t = it.get("title") or it["ref"]
    return f"the company cited ({it['ref']})" if UNSAFE.search(t) else t


def _status(it) -> str:
    return (it["row"].get("status") or "").strip()


def _ending(it) -> str:
    """A company's standing as its register status files it: insolvent, ended or going."""
    st = _status(it)
    if INSOLVENT_STATUS.search(st):
        return "insolvent"
    if ENDED_STATUS.match(st) or _date(it["row"].get("removed_on")):
        return "ended"
    return "going" if GOING_STATUS.match(st) or not st else "ended"


def _notices(report, grades=("confirmed",)):
    return list(items(report, ("gazette_liquidations", "gazette_company_notices"), grades))


def _kind(it) -> str:
    return "liquidation" if it["view"] == "gazette_liquidations" else (it["row"].get("kind") or "notice")


def _insolvency(it) -> bool:
    """A notice that is an insolvency: a liquidator's appointment, or a company notice of an insolvency kind that is not a receiver
    ceasing to act."""
    if it["view"] == "gazette_liquidations":
        return True
    r = it["row"]
    return it["view"] == "gazette_company_notices" and r.get("kind") in INSOLVENCY_KINDS and "ceas" not in (r.get("action") or "").lower()


def _event(it) -> bool:
    return it["view"] == "gazette_company_notices" and (it["row"].get("kind") or "") not in INSOLVENCY_KINDS


def _event_kind(it) -> str:
    r = it["row"]
    kind, action = r.get("kind") or "", (r.get("action") or "").lower()
    if "restor" in action or "revocation" in action:
        return "restoration"
    return EVENT_KIND.get(kind, kind or "notice")


def _failure_date(it):
    """The day a failure notice dates it from: a liquidator's or receiver's appointment where the Gazette states one, otherwise the
    day the notice was published (a winding-up application's own date is its hearing, and that is not the day the company failed)."""
    r = it["row"]
    if it["view"] == "gazette_liquidations":
        return _date(r.get("appointed_on")) or _date(r.get("published_on"))
    if (r.get("event_basis") or "") == "appointment":
        return _date(r.get("event_on")) or _date(r.get("published_on"))
    return _date(r.get("published_on")) or _date(r.get("filed_on"))


def _company_of(it) -> str:
    """The company a role, holding, office or notice sits on, as a ref."""
    if it.get("entity"):
        return it["entity"]["ref"]
    key = it["row"].get("entity_key") or it["row"].get("register_key")
    if key:
        return f"companies:{key}"
    return it.get("via") or ""


def _start_company(report) -> str:
    """The company the start row itself sits on (a role or a holding): the person's own by definition, whatever grade a contested
    group gives it (the shape can file it near when another row of the group reaches it first)."""
    s = report["subject"]
    return _company_of(s) if s["view"] in ("directors", "shareholders") else ""


def _companies(report, grades=("confirmed",)):
    """The companies the walk reached, other than the one the report starts from; the start row's own company is confirmed."""
    own = _start_company(report)
    return [it for it in items(report, ("companies",), ("confirmed", "near"))
            if it["ref"] != report["subject"]["ref"] and ("confirmed" if it["ref"] == own else it["grade"]) in grades]


def _same_name(it) -> bool:
    """A company reached by the links lane's company-name rule: it shares a name and nothing else."""
    return bool(SAME_NAME.match(it.get("rule") or ""))


def _roles_on(report, company_ref: str) -> list:
    """The subject's own confirmed roles and holdings on a company: the start row, its group's rows and confirmed links (the other
    people on the person's companies are near by the walk's default, so a confirmed role is the person's own)."""
    return [it for it in all_items(report).values()
            if it["view"] in ("directors", "shareholders") and it["grade"] == "confirmed" and _company_of(it) == company_ref]


def _clear_or_past(rule, severity, text, not_held=PAST_NOT_HELD, **kw):
    """A clear, or, while past roles are not held, a blocked flag saying what was seen and what cannot be."""
    if HISTORY:
        return flag(rule, V, "clear", severity, text, **kw)
    kw.pop("sources_held", None)
    return flag(rule, V, "blocked", severity, f"{text}; but {not_held}: no clear is given", **kw)


def _counted(xs, label) -> str:
    counts = {}
    for it in xs:
        counts[label(it)] = counts.get(label(it), 0) + 1
    return ", ".join(f"{n} {k}" for k, n in sorted(counts.items()))


def _iso(d) -> str:
    return d.isoformat() if d else "undated"


def _subject_hub(report) -> list:
    own = {report["subject"]["ref"]} | {m["ref"] for m in report.get("members", [])}
    return [h for h in report.get("hubs", []) if h["ref"] in own and h["kind"] in HUB_KINDS]


def _current(it) -> bool:
    return bool(it["row"].get("in_latest", True)) and not it["row"].get("ended_on")


# ── failures ────────────────────────────────────────────────────────────────

def _failures(report, companies: list) -> dict:
    """{company ref: {'company', 'date', 'evidence', 'notice'}} for each company that is in an insolvency: by its register status
    (undated) or by a Gazette insolvency notice on it (joined by the company's number, so it is the company's whatever the walk's grade
    of the company). 'date' is the earliest appointment a notice dates (a liquidator, a receiver, an administrator); only where no
    notice dates one, the earliest other insolvency notice (a winding-up application, which may be dismissed). A removal is not a
    failure here."""
    by_ref = {it["ref"]: it for it in companies}
    out = {}
    for it in companies:
        if _ending(it) == "insolvent":
            out[it["ref"]] = {"company": it, "date": None, "evidence": [it["ref"]], "notice": None}
    for n in _notices(report, ("confirmed", "near")):
        c = n.get("via") or _company_of(n)
        if c not in by_ref or not _insolvency(n):
            continue
        e = out.setdefault(c, {"company": by_ref[c], "date": None, "evidence": [c], "notice": None, "rank": None})
        e["evidence"].append(n["ref"])
        d = _failure_date(n)
        rank = (0 if _appointment(n) else 1, d) if d else None
        if rank and (e.get("rank") is None or rank < e["rank"]):
            e["date"], e["notice"], e["rank"] = d, n, rank
    return out


def _appointment(n) -> bool:
    """A notice that dates an appointment: a liquidator's, or a receiver's or administrator's appointment."""
    return n["view"] == "gazette_liquidations" or (n["row"].get("event_basis") or "") == "appointment"


def _how(f) -> str:
    """'liquidation (liquidator appointed by the court), appointed 13 July 2020' as the notice dates it; the status alone when no
    notice is reached."""
    n = f["notice"]
    if n is None:
        return f"status {_status(f['company'])!r}, no dated Gazette notice reached"
    by = n["row"].get("appointed_by")
    what = f"liquidation (liquidator appointed by the {by})" if n["view"] == "gazette_liquidations" and by else _kind(n)
    return f"{what}, {n['dates']['text']}"


def _held_at(f, roles: list) -> tuple:
    """How the person's own rows on a failed company stand beside its failure date, by the dates the companies file states:
    ('on', role) a role that began on or before the failure and is still listed; ('after', role) one that began after it;
    ('undated', role or None) where either date is missing (a holding of record carries no start)."""
    best = None
    for r in roles:
        start = _date(r["row"].get("appointed_on"))
        if f["date"] and start and start <= f["date"] and _current(r):
            return ("on", r)
        if f["date"] and start and start > f["date"]:
            best = best or ("after", r)
    return best or ("undated", roles[0] if roles else None)


def _beside(f, how) -> str:
    """'FAILED LTD: liquidation, appointed 13 July 2020 | the person's row: DIRECTOR, from 3 March 2011': two dates, no word between."""
    stand, r = how
    if r is None:
        mine = "no role or holding of the person's on it is among the rows listed"
    else:
        start = _date(r["row"].get("appointed_on"))
        role = r["row"].get("role_type") or "shareholder of record"
        mine = f"the person's row: {role}, {'from ' + start.isoformat() if start else 'no start filed'}"
        if stand == "on":
            mine += ", on or before the failure date and still listed"
        elif stand == "after":
            mine += ", after the failure date"
    return f"{_name(f['company'])}: {_how(f)} | {mine}"


# ── the entity's standing and the Gazette on it ─────────────────────────────

def entity_status(report):
    if _other_start(report):
        return flag("entity-status", V, "blocked", "red", _other_start(report), scope="entity")
    if not _company_start(report):
        return flag("entity-status", V, "clear", "info", "the start is a person: how each of the person's companies stands is in the companies "
                    "section and the flags sister-company-failure and other-current-companies", sources_held=(COMPANIES_HELD,), scope="entity")
    s = report["subject"]
    r = s["row"]
    status, kind = _status(s), r.get("entity_type") or "entity"
    nh = (LP_PARTNERS,) if "partnership" in kind.lower() else ()
    reg, removed = _date(r.get("registered_on")), _date(r.get("removed_on"))
    when = f"registered {reg.isoformat()}" if reg else "registration date not stated"
    if removed:
        when += f", removed {removed.isoformat()}"
    if _ending(s) == "insolvent":
        return flag("entity-status", V, "fired", "red", f"the companies file gives the entity the status {status!r} ({kind}; {when})",
                    citations=(s["ref"],), sources_not_held=nh + (STATES,) + NOT_HELD_INSOLVENCY, scope="entity")
    if _ending(s) == "ended":
        return flag("entity-status", V, "fired", "red", f"the entity is no longer a registered company: status {status!r} ({kind}; {when})",
                    citations=(s["ref"],), sources_not_held=nh + (STATES,), scope="entity")
    if not r.get("in_latest", True):
        return flag("entity-status", V, "fired", "amber", f"the entity is not in the latest companies file; its last status was {status!r} "
                    f"({kind}; {when}); the interface check of step 5.5 would date the change", citations=(s["ref"],),
                    sources_not_held=nh + (STATES,), scope="entity")
    return flag("entity-status", V, "clear", "red", f"registered ({kind}; {when}) in the latest companies file",
                sources_held=("Companies register status (pub.companies)",), sources_not_held=nh + (STATES,), scope="entity")


def young_entity(report):
    """Registered under 24 months: a short record to price. Amber on the entity, info on the person's going companies."""
    as_of = _as_of(report)
    if _other_start(report):
        return flag("young-entity", V, "blocked", "info", _other_start(report))
    pool = [report["subject"]] if _company_start(report) else [it for it in _companies(report) if _ending(it) == "going"]
    young = [(it, _date(it["row"].get("registered_on"))) for it in pool]
    young = [(it, reg) for it, reg in young if reg and (as_of - reg).days < YOUNG_DAYS]
    if young:
        who = "the entity was" if _company_start(report) else f"{len(young)} going company(ies) the person has a confirmed row on were"
        return flag("young-entity", V, "fired", "amber" if _company_start(report) else "info",
                    f"{who} registered under 24 months before {as_of.isoformat()}: "
                    + "; ".join(f"{_name(it)} (registered {reg.isoformat()})" for it, reg in young[:EXAMPLES])
                    + "; a short record is a short record, not a finding",
                    citations=tuple(it["ref"] for it, _ in young), scope="entity" if _company_start(report) else "officer-group")
    if _company_start(report):
        if not _date(report["subject"]["row"].get("registered_on")):
            return flag("young-entity", V, "blocked", "amber", "the companies file states no registration date for the entity", scope="entity")
        return flag("young-entity", V, "clear", "amber", "registered 24 months ago or more", sources_held=("Companies register registration dates "
                    "(pub.companies)",), scope="entity")
    if (report.get("walk") or {}).get("entities_omitted"):
        return flag("young-entity", V, "blocked", "info", f"the walk left {report['walk']['entities_omitted']:,} company(ies) past its limit, and "
                    "their registration dates are not read")
    return flag("young-entity", V, "clear", "info", "no going company the person has a confirmed row on was registered under 24 months ago",
                sources_held=("Companies register registration dates (pub.companies)",))


def insolvency_event(report):
    """MC-I2. Gazette insolvency notices on the company started from, each dated from its notice. From a person the notices on the
    person's companies are read by sister-company-failure."""
    if _other_start(report):
        return flag("insolvency-event", V, "blocked", "red", _other_start(report), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
    if not _company_start(report):
        return flag("insolvency-event", V, "clear", "info", "the start is a person: the Gazette on each of the person's companies is read by "
                    "sister-company-failure, and on the person by bankruptcy", sources_held=(GAZETTE_HELD,), scope="entity")
    own = [it for it in _notices(report) if _insolvency(it) and _on_subject(report, it)]
    if own:
        own.sort(key=lambda it: (_failure_date(it) is None, _failure_date(it) or dt.date.min))
        return flag("insolvency-event", V, "fired", "red", f"{len(own)} Gazette insolvency notice(s) on the entity ({_counted(own, _kind)}), "
                    "earliest first: " + "; ".join(f"{_kind(it)}, {it['dates']['text']}" for it in own[:EXAMPLES])
                    + (f"; and {len(own) - EXAMPLES} more" if len(own) > EXAMPLES else ""),
                    citations=tuple(it["ref"] for it in own), sources_not_held=NOT_HELD_INSOLVENCY + (SECURITIES, POSSESSIONS), scope="entity")
    if set(section(report, "solvency").get("omitted_views") or ()) & {"gazette_liquidations", "gazette_company_notices"}:
        return flag("insolvency-event", V, "blocked", "red", "the entity has more Gazette notices than the walk lists; an insolvency could be "
                    "among those left out", scope="entity")
    if _ending(report["subject"]) == "insolvent":
        return flag("insolvency-event", V, "fired", "red", f"the companies file gives the entity the status {_status(report['subject'])!r} and "
                    "no Gazette insolvency notice on it is held: the status is undated here", citations=(report["subject"]["ref"],),
                    sources_not_held=NOT_HELD_INSOLVENCY + (STATES,), scope="entity")
    return flag("insolvency-event", V, "clear", "red",
                "no Gazette liquidation, winding-up application, receivership, administration, creditors' notice or deed of company "
                "arrangement on the entity; its people's other companies are not read from a company (see sister-company-failure)",
                sources_held=(GAZETTE_HELD + ", joined to the company by its number",),
                sources_not_held=NOT_HELD_INSOLVENCY + (SECURITIES, POSSESSIONS), scope="entity")


def register_events(report):
    """Removals, dissolutions, restorations, rectifications, amalgamations, transfers out. Not insolvency; on the entity amber, on the
    person's companies info."""
    if _other_start(report):
        return flag("register-events", V, "blocked", "info", _other_start(report))
    conf = [it for it in _notices(report) if _event(it)]
    if _company_start(report):
        own = [it for it in conf if _on_subject(report, it)]
        if own:
            return flag("register-events", V, "fired", "amber", f"{len(own)} Gazette notice(s) on the entity ({_counted(own, _event_kind)}): "
                        + "; ".join(f"{_event_kind(it)}, {it['dates']['text']}" for it in own[:EXAMPLES]) + "; none is an insolvency",
                        citations=tuple(it["ref"] for it in own), scope="entity")
        return flag("register-events", V, "clear", "amber", "no Gazette removal, dissolution, restoration, rectification, amalgamation or "
                    "transfer notice on the entity", sources_held=(NOTICES_HELD,), scope="entity")
    if conf:
        return flag("register-events", V, "fired", "info",
                    f"{len(conf)} Gazette notice(s) ({_counted(conf, _event_kind)}) on {len({it.get('via') for it in conf})} company(ies) the "
                    "person has a row on: " + "; ".join(f"{_name(it)}, {it['dates']['text']}" for it in conf[:EXAMPLES]) + "; none is an insolvency",
                    citations=tuple(it["ref"] for it in conf), scope="officer-group")
    if _walk_short(report):
        return flag("register-events", V, "blocked", "info", "the walk stopped before reading every company the person has a row on",
                    scope="officer-group")
    return _clear_or_past("register-events", "info", "no Gazette removal, dissolution, restoration, rectification, amalgamation or transfer "
                          "notice on a company the person has a confirmed row on", sources_held=(NOTICES_HELD,), scope="officer-group")


def officer_churn(report):
    """Started from a company: its current directors appointed in the last twelve months (not counting the first board), and director
    rows that left the latest file. Arrivals are seen; departures before July 2026 are not, so this fires or blocks and never clears."""
    if _other_start(report):
        return flag("officer-churn", V, "blocked", "amber", _other_start(report), scope="entity")
    if not _company_start(report):
        return flag("officer-churn", V, "blocked", "amber", "a board's churn is read from the company: start a report from each company in the "
                    "companies section", scope="entity")
    s = report["subject"]
    r = s["row"]
    if "partnership" in (r.get("entity_type") or "").lower():
        return flag("officer-churn", V, "blocked", "amber", "a limited partnership has general and limited partners, not directors, and the "
                    "limited partnerships register that names them is not held", sources_not_held=(LP_PARTNERS,), scope="entity")
    as_of, reg = _as_of(report), _date(r.get("registered_on"))
    dirs = [it for it in section(report, "people")["items"] if it["view"] == "directors" and it.get("via") == s["ref"]]
    now = [it for it in dirs if _current(it)]
    left = [it for it in dirs if not _current(it)]
    recent = []
    for it in now:
        start = _date(it["row"].get("appointed_on"))
        if start and (as_of - start).days <= CHURN_DAYS and not (reg and (start - reg).days <= AT_START_DAYS):
            recent.append((it, start))
    omitted = section(report, "people").get("omitted") or 0
    tail = f"; {omitted:,} row(s) past the walk's limit, not listed" if omitted else ""
    going = GOING_STATUS.match(_status(s)) and r.get("in_latest", True)
    if not now and not omitted and going:
        return flag("officer-churn", V, "fired", "amber", f"the companies file names no current director of the entity ({len(left)} row(s) that "
                    "left the file)", citations=tuple(it["ref"] for it in dirs) or (s["ref"],), sources_not_held=(CHANGE_HISTORY,), scope="entity")
    if len(recent) >= CHURN_AT or left:
        bits = []
        if recent:
            bits.append(f"{len(recent)} of {len(now)} current director(s) appointed in the {CHURN_DAYS} days before {as_of.isoformat()}: "
                        + "; ".join(f"{it['title'] if not it.get('suppressed') else 'name suppressed'} (from {d.isoformat()})"
                                    for it, d in sorted(recent, key=lambda x: x[1])[:EXAMPLES]))
        if left:
            bits.append(f"{len(left)} director row(s) left the companies file since July 2026, with no end date filed")
        return flag("officer-churn", V, "fired", "amber", "; ".join(bits) + tail + f"; {DEPARTED_NOT_HELD}",
                    citations=tuple(it["ref"] for it, _ in recent) + tuple(it["ref"] for it in left), sources_not_held=(CHANGE_HISTORY,),
                    scope="entity")
    return _clear_or_past("officer-churn", "amber", f"{len(recent)} of {len(now)} current director(s) appointed in the {CHURN_DAYS} days before "
                          f"{as_of.isoformat()}, after the first board{tail}", not_held=DEPARTED_NOT_HELD, sources_held=(COMPANIES_HELD,),
                          sources_not_held=(CHANGE_HISTORY,), scope="entity")


# ── its people ──────────────────────────────────────────────────────────────

def sister_company_failure(report):
    """Group receivership, liquidation history. From a person: each of the person's companies that failed, the failure dated from its
    Gazette notice and the person's own role on that company dated beside it; red where a confirmed role began on or before the failure
    date and is still listed, the person not a hub. From a company: blocked, the people not being followed."""
    if _company_start(report):
        return flag("sister-company-failure", V, "blocked", "red", f"{NOT_FOLLOWED}: whether a director's other companies failed cannot be seen",
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if _other_start(report):
        return flag("sister-company-failure", V, "blocked", "red", _other_start(report), scope="officer-group")
    failed = _failures(report, [it for it in _companies(report) if not _same_name(it)])
    hub = _subject_hub(report)
    if failed:
        pairs = [(f, _held_at(f, _roles_on(report, ref))) for ref, f in failed.items()]
        order = {"on": 0, "after": 1, "undated": 2}
        pairs.sort(key=lambda p: (order[p[1][0]], p[0]["date"] is None, p[0]["date"] or dt.date.min))
        on = [p for p in pairs if p[1][0] == "on"]
        red = bool(on) and not hub
        why = f"; the person is a hub ({hub[0]['kind']}): {hub[0]['text']}" if hub else ""
        return flag("sister-company-failure", V, "fired", "red" if red else "amber",
                    f"{len(failed)} company(ies) the person has a confirmed row on are in an insolvency, {len(on)} with the person's role "
                    f"starting on or before the failure date: " + " ; ".join(_beside(f, how) for f, how in pairs[:EXAMPLES])
                    + (f"; and {len(pairs) - EXAMPLES} more" if len(pairs) > EXAMPLES else "") + _short_text(report) + why,
                    citations=tuple(dict.fromkeys(r for f, how in pairs for r in f["evidence"] + ([how[1]["ref"]] if how[1] else []))),
                    sources_not_held=NOT_HELD_INSOLVENCY + (CHANGE_HISTORY,), scope="officer-group")
    nearby = _failures(report, [it for it in _companies(report, ("near",)) if not _same_name(it)])
    if nearby:
        return flag("sister-company-failure", V, "fired", "amber",
                    f"{len(nearby)} company(ies) reached only through a near link are in an insolvency: a namesake's companies, not the person's "
                    "until confirmed: " + "; ".join(f"{_name(f['company'])} ({_how(f)})" for f in list(nearby.values())[:EXAMPLES]),
                    citations=tuple(dict.fromkeys(r for f in nearby.values() for r in f["evidence"])), sources_not_held=NOT_HELD_INSOLVENCY,
                    scope="near")
    if _walk_short(report):
        return flag("sister-company-failure", V, "blocked", "red", "no insolvency on the companies the walk read, but it stopped before reading "
                    "every company the person has a row on", scope="officer-group")
    return _clear_or_past("sister-company-failure", "red", f"none of the {len(_companies(report))} company(ies) the person has a confirmed row "
                          "on has an insolvency status or Gazette insolvency notice", sources_held=(GAZETTE_HELD, COMPANIES_HELD),
                          sources_not_held=NOT_HELD_INSOLVENCY + (CHANGE_HISTORY,), scope="officer-group")


def other_current_companies(report):
    """The person's companies and their states, the going ones newest first."""
    if _company_start(report):
        return flag("other-current-companies", V, "blocked", "amber", f"{NOT_FOLLOWED}: the other companies its people sit on are not read",
                    scope="officer-group")
    if _other_start(report):
        return flag("other-current-companies", V, "blocked", "amber", _other_start(report), scope="officer-group")
    conf = [it for it in _companies(report) if not _same_name(it)]
    going = [it for it in conf if _ending(it) == "going"]
    if conf:
        by = _counted(conf, lambda it: {"going": "registered", "insolvent": "in an insolvency", "ended": "removed or ended"}[_ending(it)])
        return flag("other-current-companies", V, "fired", "info", f"the person has a confirmed row on {len(conf)} company(ies) ({by}); the going "
                    f"ones, newest first: " + ("; ".join(f"{_name(it)} (registered {_iso(_date(it['row'].get('registered_on')))})"
                                                         for it in sorted(going, key=lambda x: str(x['row'].get('registered_on') or ''),
                                                                          reverse=True)[:EXAMPLES]) or "none") + _short_text(report),
                    citations=tuple(it["ref"] for it in conf), scope="officer-group")
    if _walk_short(report):
        return flag("other-current-companies", V, "blocked", "amber", "the walk stopped before reading every company the person has a row on",
                    scope="officer-group")
    return _clear_or_past("other-current-companies", "amber", "the person has no confirmed company row", sources_held=(COMPANIES_HELD,),
                          scope="officer-group")


def _in_force(report, it) -> str:
    as_of = _as_of(report)
    end = _date(it["row"].get("ends_on"))
    if it["row"].get("permanent"):
        return f"permanent; in force on {as_of.isoformat()}"
    if not end:
        return "no end filed"
    return f"in force on {as_of.isoformat()}" if end >= as_of else f"ended before {as_of.isoformat()}"


def _person_notice(report, rule, view, noun, severity, extra_clear="", not_held=()):
    """A Gazette notice the link rules join to the person by name: confirmed red, near amber, never a suppressed or withheld row;
    blocked from a company, or where the walk left a link unread."""
    live = [it for it in items(report, (view,)) if not it.get("suppressed")]
    conf = [it for it in live if it["grade"] == "confirmed"]
    nearby = [it for it in live if it["grade"] == "near"]
    show = (lambda it: f"{it['dates']['text']}; {_in_force(report, it)}") if view == "gazette_prohibitions" else (lambda it: it["dates"]["text"])
    if conf:
        return flag(rule, V, "fired", severity, f"{len(conf)} Gazette {noun} notice(s) confirmed to the person: "
                    + "; ".join(f"{it['title']} ({show(it)})" for it in conf[:EXAMPLES]), citations=tuple(it["ref"] for it in conf),
                    sources_not_held=not_held)
    if nearby:
        return flag(rule, V, "fired", "amber", f"{len(nearby)} Gazette {noun} notice(s) under a name near the person's; a namesake's until "
                    f"confirmed: " + "; ".join(f"{it['title']} ({show(it)}; near: {it.get('reason')})" for it in nearby[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in nearby), sources_not_held=not_held, scope="near")
    if _company_start(report):
        return flag(rule, V, "blocked", severity, f"{NOT_FOLLOWED}: a {noun} notice is joined to a director's own row, which is not followed",
                    sources_not_held=not_held, scope="officer-group")
    if _other_start(report):
        return flag(rule, V, "blocked", severity, _other_start(report), sources_not_held=not_held)
    w = report.get("walk") or {}
    if not w.get("links_built"):
        return flag(rule, V, "blocked", severity, f"no links are published, so a {noun} notice under the person's name cannot be reached",
                    sources_not_held=not_held)
    if w.get("links_omitted"):
        return flag(rule, V, "blocked", severity, f"the walk left {w['links_omitted']:,} link(s) unread past its limit; a {noun} notice could be "
                    "among them, so no clear is given", sources_not_held=not_held)
    return flag(rule, V, "clear", severity, f"no Gazette {noun} notice confirmed or near the person: the link rules join every such notice by "
                f"name, and every link from the person's rows was read{extra_clear}",
                sources_held=(f"New Zealand Gazette {noun} notices (pub.{view}), joined by name in pub.links",), sources_not_held=not_held)


def prohibition(report):
    return _person_notice(report, "prohibition", "gazette_prohibitions", "director prohibition", "red")


def bankruptcy(report):
    return _person_notice(report, "bankruptcy", "gazette_bankruptcies", "bankruptcy", "red",
                          "; a name the Gazette later withheld (an annulment) makes no row and is never shown",
                          not_held=(INSOLVENCY_REGISTER + ": a discharge, a no-asset procedure or a summary instalment order",))


def practitioner_roles(report):
    """The person named as liquidator in Gazette notices: an insolvency practitioner, who is appointed to a failed company and is not
    one of its officers."""
    live = [it for it in items(report, ("gazette_liquidators",)) if not it.get("suppressed")]
    conf = [it for it in live if it["grade"] == "confirmed"]
    nearby = [it for it in live if it["grade"] == "near"]
    if conf:
        return flag("practitioner-roles", V, "fired", "info", f"named as liquidator in {len(conf)} Gazette notice(s): "
                    + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in conf[:EXAMPLES])
                    + "; a practitioner is appointed to a failed company and is not one of its officers", citations=tuple(it["ref"] for it in conf))
    if nearby:
        return flag("practitioner-roles", V, "fired", "info", f"{len(nearby)} Gazette liquidator appointment(s) under a name near the person's; "
                    "a namesake's until confirmed", citations=tuple(it["ref"] for it in nearby), scope="near")
    if _company_start(report):
        return flag("practitioner-roles", V, "blocked", "info", f"{NOT_FOLLOWED}: its officers' appointments as liquidator are not read",
                    scope="officer-group")
    if _other_start(report):
        return flag("practitioner-roles", V, "blocked", "info", _other_start(report))
    if (report.get("walk") or {}).get("links_omitted"):
        return flag("practitioner-roles", V, "blocked", "info", "the walk left links unread past its limit; an appointment could be among them")
    return flag("practitioner-roles", V, "clear", "info", "not named as liquidator in a Gazette notice the link rules join to the person",
                sources_held=("New Zealand Gazette liquidators (pub.gazette_liquidators), joined by name in pub.links",))


# ── the report's own reach ──────────────────────────────────────────────────

def namesake_exposure(report):
    names = list(section(report, "identity")["items"])
    nearby_elsewhere = [it for s in report["sections"] if s["name"] not in ("identity", "beside") for it in s["items"] if it["grade"] == "near"]
    w = report.get("walk") or {}
    g = report.get("group") or {}
    bits = []
    if len(names) >= NAMESAKE_PARTIAL_AT:
        bits.append(f"{len(names)} namesake row(s) set apart: the name is common, and this report is partial; confirm the entity by a second "
                    "fact (a business number, a date of appointment) before relying on any row")
    elif len(names) >= NAMESAKE_NOTE_AT:
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
        partial = len(names) >= NAMESAKE_PARTIAL_AT or g.get("contested")
        return flag("namesake-exposure", V, "fired", "amber" if partial else "info", "the report's own uncertainty: " + "; ".join(bits), citations=cites)
    return flag("namesake-exposure", V, "clear", "info", f"low namesake exposure: {len(names)} namesake row(s) set apart and every link read",
                sources_held=("pub.links", "pub.groups"))


def walk_coverage(report):
    w = report.get("walk") or {}
    ne, om = w.get("entities_not_expanded") or 0, w.get("entities_omitted") or 0
    if ne or om:
        bits = []
        if ne:
            bits.append(f"{ne:,} company(ies) listed with their status, their Gazette notices, offices and officers not read")
        if om:
            bits.append(f"{om:,} past the walk's limit, not listed")
        return flag("walk-coverage", V, "fired", "amber", "the walk did not read every company it reached: " + "; ".join(bits)
                    + "; start a report from each company left out", citations=(report["subject"]["ref"],))
    return flag("walk-coverage", V, "clear", "info", "every company the walk reached was read for its notices, office and officers",
                sources_held=("pub.companies", "pub.gazette_liquidations", "pub.gazette_company_notices", "pub.company_addresses", "pub.directors"))


def subject_hub(report):
    if _other_start(report):
        return flag("subject-hub", V, "blocked", "info", _other_start(report))
    mine = _subject_hub(report)
    if mine:
        kinds = sorted({h["kind"] for h in mine})
        return flag("subject-hub", V, "fired", "amber", f"the start is itself a hub ({', '.join(kinds)}): {mine[0]['text']}; a failure among its "
                    "many companies is shown and never raised red", citations=tuple(sorted({h["ref"] for h in mine})))
    return flag("subject-hub", V, "clear", "info", "the start is not a professional director, a nominee or the Crown on the rows held",
                sources_held=("pub.directors", "pub.groups"))


def past_roles(report):
    if HISTORY:
        return flag("past-roles", V, "clear", "info", "past roles and holdings are published with their filed end dates", sources_held=(COMPANIES_HELD,))
    left = [it for it in all_items(report).values() if it["view"] in ("directors", "shareholders") and it["grade"] == "confirmed"
            and not it["row"].get("in_latest", True)]
    seen = f"; {len(left)} of the rows listed left the file since July 2026 and carry no end date" if left else ""
    if _company_start(report):
        text = f"the entity's past officers and holders are not held: {DEPARTED_NOT_HELD}{seen}"
    else:
        text = (f"the person's past directorships and holdings are not held: {PAST_NOT_HELD}{seen}; a sister company that failed after "
                "the person left it cannot be seen here")
    return flag("past-roles", V, "blocked", "amber", text,
                sources_not_held=("past directorships and shareholdings with their end dates",))


# ── the safety record, and what else is not held ────────────────────────────

def safety_record(report):
    """The heart of use case 6, and not held: never clear."""
    return flag("safety-record", V, "blocked", "red",
                "the safety record is not held: WorkSafe's prosecutions (the charge, the plea, the fine) and enforceable undertakings, and Fire "
                "and Emergency New Zealand's notices, are in no published register yet; no prosecution, undertaking or notice in this report "
                "is a finding of none; this check cannot run", sources_not_held=(WORKSAFE, FIRE))


def regulator_actions(report):
    return flag("regulator-actions", V, "blocked", "amber",
                "the Commerce Commission's cases (fair trading, competition, consumer credit) and the Financial Markets Authority's warnings "
                "and actions are held as documents and not yet read into a register; this check cannot run", sources_not_held=REGULATORS + (FSP,))


def court_judgments(report):
    return flag("court-judgments", V, "blocked", "red",
                "court judgments are not held yet (plan step 5.4): a creditor's judgment, a winding-up order's reasons, a sentencing on a "
                "health and safety charge cannot be seen; this check cannot run", sources_not_held=(COURTS,))


def tribunals(report):
    return flag("tribunals", V, "blocked", "amber",
                "the Employment Relations Authority's determinations (unpaid wages, arrears, penalties) and the Disputes Tribunal's decisions "
                "are not held: a claim history against the firm cannot be seen here; this check cannot run", sources_not_held=TRIBUNALS)


def change_history(report):
    return flag("change-history", V, "blocked", "amber",
                "a company's earlier names, trading names, industry classification, directors and offices are in the companies change history, "
                "which is not held before 16 August 2026 and is held but not published since: a change of trade before a proposal, or a "
                "firm that failed under one name and trades under another, cannot be seen by its history; this check cannot run",
                sources_not_held=(CHANGE_HISTORY,))


def status_history(report):
    return flag("status-history", V, "blocked", "info",
                "the dated history of a company's status, file by file, is published (pub.company_states) but the report's catalogue does not "
                "know the view, so this report reads only the latest file's status; this check cannot run", sources_not_held=(STATES,))


def mortgagee_possession(report):
    return flag("mortgagee-possession", V, "blocked", "amber",
                "a lender's entry into possession of a company's land or goods is published in the Gazette (pub.gazette_possessions), but the "
                "report's catalogue does not know the view, so this report cannot reach it; this check cannot run", sources_not_held=(POSSESSIONS,))


def insolvency_register(report):
    return flag("insolvency-register", V, "blocked", "red",
                "the Official Assignee's Insolvency Register (a bankruptcy's discharge, a no-asset procedure, a summary instalment order, and the "
                "removals it records daily) is not held; the Gazette's own notices are read above; this check cannot run",
                sources_not_held=(INSOLVENCY_REGISTER,))


def securities_register(report):
    return flag("securities-register", V, "blocked", "info",
                "who has registered security over the firm's assets, and when, is in the Personal Property Securities Register, which is not "
                "held; this check cannot run", sources_not_held=(SECURITIES,))


RULES = (entity_status, young_entity, insolvency_event, register_events, officer_churn, sister_company_failure, other_current_companies,
         prohibition, bankruptcy, practitioner_roles, namesake_exposure, walk_coverage, subject_hub, past_roles, safety_record,
         regulator_actions, court_judgments, tribunals, change_history, status_history, mortgagee_possession, insolvency_register,
         securities_register)
