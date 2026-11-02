"""The legal counterparty and conflict check's rules (plan 5.2, use case 2).
Pure functions over the built report, each returning one flag. A law firm
asks, before acting, "who is this counterparty, who stands on its register,
and does anyone here already act for or against them". The rules stand for
the old estate's legal checks MC-L1 to MC-L5 (data-layer/query/query/
routes.py, the entity web and conflicts endpoints) and its person and
company rules (data-layer/flags/flags/person_rules.py, person-0.2;
entity_rules.py, entity-0.1), taken as ideas and tests, not code, where the
held registers can support them:

  client-overlap         blocked (MC-L4): the firm's client and matter list is not an input; the names to compare are counted
  conflict-web           the companies the person sits on and the people on them, each dated or marked undated (MC-L1)
  shared-boards          a name on two or more of the person's companies: rows that share a name, never one person
  officers-of-record     started from a company: its current directors, or none in the latest file
  holders-of-record      holders that are companies or that hold as nominee or trustee: shown as holders of record, not followed
  shared-office          the registered office, flagged when fifty or more companies share it (MC-L2)
  company-status         the company's own register status, or how each of the person's companies stands (partnership-dissolved, widened)
  insolvency-notices     Gazette liquidations, receiverships, administrations, winding-up applications, creditors' notices and deeds
                         of company arrangement, on the company or the person's companies (MC-L3; liquidation-history)
  repeat-insolvency      two or more of the person's companies with an insolvency (group-receivership, officer scope)
  amalgamation           an amalgamation proposal naming the company: the other companies in it are not reached
  register-events        removals, dissolutions, restorations, the Registrar's rectifications, transfers out, an overseas company
                         ceasing: not insolvency
  mortgagee-possession   blocked: a mortgagee's entry into possession is published but the report cannot reach it
  prohibition            a director prohibition confirmed or near; a clear only when every link was read
  bankruptcy             blocked until a link rule reaches a Gazette bankruptcy notice
  practitioner-roles     the person named as liquidator in Gazette notices: an insolvency practitioner acts for creditors
  young-entity           registered under 24 months
  namesake-exposure      the report's own uncertainty: a conflict search on a common name meets many rows
  walk-coverage          how many of the companies reached had their notices and officers read
  subject-hub            the party is itself a professional director, a nominee or the Crown
  past-roles             blocked: the companies file lists current roles only
  charity-officer-roles    society roles confirmed; charity officer rows that carry the person's name (near: no link joins the
                         Charities Register yet); from a company, its charity by business number and the officer rows on it
  charity-integrity-marks  the Charities Register's own disqualified mark on an officer row, amber (near by name, or on the company's
                         own charity's officers)
  political-money
  court-judgments        fired, or blocked: a party in a judgment the courts corpus holds (a part of the courts' judgments)
  disciplinary-findings  blocked: no disciplinary tribunal's findings are held
  comcom-coverage        fired, or clear: a Commerce Commission case or an FMA warning naming the subject
  securities-register    blocked: the Personal Property Securities Register is not held

The builder adds its common rules for every template (group-standing,
hubs-met, replaced-return); this file carries no copy of them.

Every rule branches on the start: a person, a company, or anything else (a
filed donation, a society, a notice). From a company the walk lists the
officers and holders and follows each officer one step (2 November 2026): the
officer's own records, other companies and notices are read beside the
officer, the officer's and never the company's, and a check clears only when
every officer was followed and every link read; an officer not followed
(suppressed, past the walk's limit) blocks it, saying how many. Evidence on the party's confirmed rows is red or amber; the same
evidence reached only through a near link is amber at most and says it is a
namesake's until confirmed. A check the walk could not have seen is blocked,
never clear. No flag joins two facts with a word of cause, none calls a
holder an owner, and none says there is no conflict: the most a report can
say is that the registers held show no connection.

Imports nothing of products.report: the one-way test holds a template folder
to its own code. The shape loads this file by path and binds the name
`contract` (products/report/contract.py) before it runs."""
from __future__ import annotations

import datetime as dt
import re

V = "0.1"
YOUNG_DAYS = 730          # under 24 months registered: worth a question (the old young-entity rule)
NAMESAKE_NOTE_AT = 5      # namesakes set apart at which the report's caveat fires
NAMESAKE_PARTIAL_AT = 50  # past this many namesakes the report is declared partial
EXAMPLES = 3              # dated examples a fired flag states in its text
#: whether a published view holds past roles with their end dates. It does not (measured 2026-10-20 by banking-1, and again
#: 2026-10-21): the companies file lists current roles only. While False, a check over a person's companies fires on what it sees
#: and never clears; set True when a lane publishes past roles (card the-companies-file-holds-no-past-directorships).
HISTORY = False
PAST_NOT_HELD = ("the companies file lists current roles only: a company the person left, or that was removed with them on it, is not "
                 "seen")

INSOLVENCY_VIEWS = ("gazette_liquidations", "gazette_company_notices", "company_insolvencies")
#: the company notices that are insolvency; every other kind is a register event or an amalgamation, its own flag
INSOLVENCY_KINDS = ("winding-up application", "receivership", "administration", "notice to creditors", "deed of company arrangement")
AMALGAMATION = "amalgamation"
#: what a register event records, by the lane's kind; a removal whose action is a restoration is a restoration
EVENT_KIND = {"removal": "removal", "dissolution": "dissolution", "restoration": "restoration", "overseas company": "an overseas company ceasing",
              "rectification": "the Registrar's rectification", "transfer out": "a transfer out of New Zealand"}
INSOLVENT_STATUS = re.compile(r"liquidation|receiv|administration|statutory management", re.I)
ENDED_STATUS = re.compile(r"^(removed|deregistered|dissolved|closed|cancelled|inactive|suspended)$", re.I)
GOING_STATUS = re.compile(r"^registered$", re.I)
COMPANY_REF = re.compile(r"^companies:companies/[^/]+")

GAZETTE_HELD = "New Zealand Gazette liquidation and company notices (pub.gazette_liquidations, pub.gazette_company_notices)"
NOTICES_HELD = "New Zealand Gazette company notices (pub.gazette_company_notices)"
COMPANIES_HELD = "Companies register (pub.companies, pub.directors, pub.shareholders)"
OFFICERS_HELD = "Companies register directors and shareholders (pub.directors, pub.shareholders)"
NOT_HELD_INSOLVENCY = ("the Insolvency Register (interface awaited since 19 September 2026)", "court judgments (step 5.4)")
COURTS = ("court judgments: the OpenLaw case-law lane and the courts register (step 5.4)", "tribunal decisions (step 5.4)")
DISCIPLINARY = ("the Lawyers and Conveyancers Disciplinary Tribunal's decisions", "the other professional disciplinary bodies' findings "
                "(accountants, real estate agents, health practitioners, builders)")
CLIENT_LIST = ("the firm's own client and matter list, and its opposing parties",)
SECURITIES = "the Personal Property Securities Register (interface awaited since 19 September 2026)"
POSSESSIONS = ("a mortgagee's entry into possession (pub.gazette_possessions: published, not in the report's catalogue)",)
LP_PARTNERS = "a limited partnership's general and limited partners (the limited partnerships register)"

LP_HELD = "the general partners, current and past, the business-number register states for a limited partnership (pub.limited_partnership_partners)"
LP_LIMITED = "a limited partnership's limited partners: the register publishes its general partners only"


def _general_partners(report, rule, severity):
    """A limited partnership start: its general partners as the register states them (read since 1 November 2026, through the
    partnership's row by business number); the limited partners are not public, so they are never counted."""
    gp = [it for it in items(report, ("limited_partnership_partners",), ("confirmed",))
          if not it.get("suppressed") and (it.get("via") or "").startswith("limited_partnerships:")]   # its own partners, not those it is one of
    if not gp:
        return flag(rule, V, "blocked", severity, "a limited partnership has general and limited partners, not directors; the walk reached no "
                    "general partner the register states for it, and the limited partners are not public", sources_held=(LP_HELD,),
                    sources_not_held=(LP_LIMITED,), scope="entity")
    now = [it for it in gp if (it.get("row") or {}).get("current")]
    names = "; ".join(it["statement"] for it in now[:3])
    text = (f"{len(now)} current general partner(s) and {len(gp) - len(now)} past, as the register states them"
            f"{': ' + names if names else ''}; the limited partners are not public")
    if not now:
        return flag(rule, V, "fired", "amber", f"the register names no current general partner: {text}",
                    citations=tuple(it["ref"] for it in gp), sources_held=(LP_HELD,), sources_not_held=(LP_LIMITED,), scope="entity")
    return flag(rule, V, "clear", "info", text, sources_held=(LP_HELD,), sources_not_held=(LP_LIMITED,), scope="entity")
#: the views whose rows the walk looks a person's name up from in the Charities Register (the shape's NAME_JOIN_FROM)
NAME_LOOKED_UP = ("directors", "society_officers", "members", "candidates", "mp_interest_returns", "promoter_people", "gazette_appointments")
CHARITY_HELD = "Charities Register officers (pub.charity_officers), looked up by the person's name"
CHARITY_BY_NAME = ("no link joins the Charities Register's officers to any other row yet, so each is matched by name and is a namesake's "
                   "until a rule confirms it")
MARK_SEVERITY = "amber"   # a disqualified mark on an officer of the company's own charity: a conflict search's question, not a bar
MONEY_VIEWS = ("party_return_donors", "party_return_loans", "disclosures", "disclosure_items", "candidate_return_donors", "promoter_people")


flag, items, section, all_items = contract.flag, contract.items, contract.section, contract.all_items   # noqa: F821  (bound by the loader)

#: the companies file's insolvency appointments (pub.company_insolvencies; the October 2026 package, read 2 November 2026) beside
#: the Gazette's liquidation notices: a liquidator's, receiver's or administrator's appointment as the Companies Office lists it
COMPANY_INSOLVENCY = "company_insolvencies"


def _liq_view(it) -> bool:
    """An insolvency practitioner's appointment: a Gazette liquidation notice, or an appointment the companies file lists that
    follows no resolution of solvency (a solvent winding-up is no failure)."""
    return it["view"] == "gazette_liquidations" or (it["view"] == COMPANY_INSOLVENCY and not (it.get("row") or {}).get("resolution_of_solvency"))


def _liq_kind(it) -> str:
    if it["view"] == COMPANY_INSOLVENCY:
        return f"{((it.get('row') or {}).get('insolvency_type') or 'insolvency').lower()} (the companies file)"
    return "liquidation"



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
    """A person row, or a filed row (a donation, a loan) that takes the group of
    the person row a confirmed link names: the walk reads that person's record."""
    return report["subject"]["kind"] == "person" or bool((report.get("group") or {}).get("via"))


def _other_start(report):
    """A start row that is neither a company nor a person (a filed donation,
    a society, a notice): the record these checks read is not walked from it."""
    if _company_start(report) or _person_start(report):
        return None
    s = report["subject"]
    article = "an" if s["kind"][:1] in "aeiou" else "a"
    return (f"the report starts from {article} {s['kind']} row (pub.{s['view']}), not a person or a company: the record these checks read is not "
            f"walked from it, so no clear is given; start the report from a person row or from the company")


def _subject_key(report) -> str:
    return report["subject"]["ref"].split(":", 1)[1]


def _on_subject(report, it) -> bool:
    """A notice on the company the report starts from."""
    return it.get("via") == report["subject"]["ref"] or (it["row"].get("register_key") or "") == _subject_key(report)


def _walk_short(report) -> bool:
    w = report.get("walk") or {}
    return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))


def _short_text(report) -> str:
    w = report.get("walk") or {}
    n = (w.get("entities_not_expanded") or 0) + (w.get("entities_omitted") or 0)
    return f"; the walk did not read the notices on {n:,} further company(ies)" if n else ""


def _status(it) -> str:
    return (it["row"].get("status") or "").strip()


def _ending(it) -> str:
    """A company's standing as its register status files it: insolvent, ended or going."""
    st = _status(it)
    if INSOLVENT_STATUS.search(st):
        return "insolvent"
    if ENDED_STATUS.match(st) or _date(it["row"].get("removed_on")):
        return "ended"
    return "going"


def _insolvency(it) -> bool:
    return _liq_view(it) or (it["view"] == "gazette_company_notices" and it["row"].get("kind") in INSOLVENCY_KINDS)


def _amalgamation(it) -> bool:
    return it["view"] == "gazette_company_notices" and it["row"].get("kind") == AMALGAMATION


def _event(it) -> bool:
    return it["view"] == "gazette_company_notices" and not _insolvency(it) and not _amalgamation(it)


def _event_kind(it) -> str:
    r = it["row"]
    kind, action = r.get("kind") or "", (r.get("action") or "").lower()
    if "restor" in action or "revocation" in action:
        return "restoration"
    return EVENT_KIND.get(kind, kind or "notice")


def _notice_date(it):
    r = it["row"]
    return _date(r.get("event_on")) or _date(r.get("appointed_on")) or _date(r.get("published_on"))


def _notices(report, grades=("confirmed",)):
    return list(items(report, INSOLVENCY_VIEWS, grades))


def _companies(report, grades=("confirmed",)):
    """The companies the walk reached, other than the one the report starts from."""
    return [it for it in items(report, ("companies",), grades) if it["ref"] != report["subject"]["ref"]]


def _company_of(it) -> str:
    """The company a role, holding or notice sits on, as a ref."""
    if it.get("entity"):
        return it["entity"]["ref"]
    key = it["row"].get("entity_key") or it["row"].get("register_key")
    if key:
        return f"companies:{key}"
    return it.get("via") or ""


def _role_on(report, company_ref: str) -> list:
    """The subject's own confirmed roles and holdings on a company."""
    return [it for it in all_items(report).values()
            if it["view"] in ("directors", "shareholders") and it["grade"] == "confirmed" and _company_of(it) == company_ref]


def _side_by_side(report, notices: list) -> str:
    """'COMPANY: notice D; the party's row: director, from A' for the first
    few notices. Two dates, no word between them."""
    bits = []
    for it in notices[:EXAMPLES]:
        if _company_start(report):
            bits.append(f"{it['title']}: {it['dates']['text']}; the officers' dates are in the officers section")
            continue
        roles = _role_on(report, it.get("via") or "")
        mine = "; ".join(f"the party's row: {r['row'].get('role_type') or 'shareholder of record'}, {r['dates']['text']}" for r in roles[:2]) \
            or "the party's row on it is in the officers section"
        bits.append(f"{it['title']}: {it['dates']['text']}; {mine}")
    more = f"; and {len(notices) - EXAMPLES} more" if len(notices) > EXAMPLES else ""
    return " | ".join(bits) + more


def _fold(name: str) -> str:
    return " ".join((name or "").lower().translate(str.maketrans("āēīōū", "aeiou")).split())


def _clear_or_past(rule, severity, text, **kw):
    """A clear over the person's companies, or, while past roles are not
    held, a blocked flag saying what was seen and what cannot be."""
    if HISTORY:
        return flag(rule, V, "clear", severity, text, **kw)
    kw.pop("sources_held", None)
    return flag(rule, V, "blocked", severity, f"{text}; but {PAST_NOT_HELD}: no clear is given", **kw)


def _counted(xs, label) -> str:
    counts = {}
    for it in xs:
        counts[label(it)] = counts.get(label(it), 0) + 1
    return ", ".join(f"{n} {k}" for k, n in sorted(counts.items()))


# ── the conflict search: who a firm compares ────────────────────────────────

def _names_to_compare(report) -> list:
    """The rows a conflict search compares with the firm's list: the party, its
    officers and holders, the companies of the web and the people on them,
    each once; a suppressed name is never counted, so never shown."""
    out = [report["subject"]]
    for s in ("officers", "web"):
        out += [it for it in section(report, s)["items"] if it["view"] in ("directors", "shareholders", "companies") and not it.get("suppressed")]
    return out


def client_overlap(report):
    """MC-L4. The old endpoint took the firm's client list and resolved each
    name; the shape takes one row, so the comparison is the firm's."""
    if _other_start(report):
        return flag("client-overlap", V, "blocked", "red", _other_start(report), sources_not_held=CLIENT_LIST)
    names = _names_to_compare(report)
    near = sum(1 for it in names if it["grade"] == "near")
    return flag("client-overlap", V, "blocked", "red",
                f"the firm's client and matter list is not an input to this report, so no overlap is checked and none is ruled out; "
                f"compare the {len(names)} name(s) listed (the party, its officers and holders of record, and the conflict web; {near} of them near) "
                f"with it, and each of the namesakes set apart", sources_not_held=CLIENT_LIST)


def conflict_web(report):
    """MC-L1. The companies the person sits on and the other people on them,
    each dated or marked undated. From a company the people are not followed."""
    if _company_start(report):   # the officers the walk followed (2 November 2026)
        return _of_companies(report, "conflict-web", "red", fire="info")
    if _other_start(report):
        return flag("conflict-web", V, "blocked", "red", _other_start(report), scope="officer-group")
    web = section(report, "web")["items"]
    cos = [it for it in web if it["view"] == "companies"]
    people = [it for it in web if it["view"] != "companies" and not it.get("suppressed")]
    undated = [it for it in web if (it.get("dates") or {}).get("undated")]
    if cos or people:
        conf = sum(1 for it in cos if it["grade"] == "confirmed")
        bits = "; ".join(f"{it['title']} ({_status(it) or 'status not filed'}; {it['dates']['text']})" for it in cos[:EXAMPLES])
        return flag("conflict-web", V, "fired", "info",
                    f"the conflict web: {len(cos)} company(ies) ({conf} confirmed, {len(cos) - conf} through a near link) and {len(people)} other "
                    f"director(s) and holder(s) of record on them, each near; {len(undated)} undated, marked so; {bits}"
                    + _short_text(report), citations=tuple(it["ref"] for it in cos + people), scope="officer-group")
    if _walk_short(report):
        return flag("conflict-web", V, "blocked", "red", "the walk stopped before reading every company the person has a row on",
                    scope="officer-group")
    return _clear_or_past("conflict-web", "red", "the person has no company row in the registers held, so there is no company web",
                          sources_held=(COMPANIES_HELD,), scope="officer-group")


def shared_boards(report):
    """A name on two or more of the person's companies. Two rows that share a
    name; no rule says they are one person, and nothing here says what the
    shared seats mean."""
    if _company_start(report):   # the officers the walk followed (2 November 2026)
        return _of_beside(report, "shared-boards", "info")
    if _other_start(report):
        return flag("shared-boards", V, "blocked", "info", _other_start(report), scope="officer-group")
    beside = [it for it in section(report, "web")["items"] if it["view"] != "companies" and not it.get("suppressed")]
    by = {}
    for it in beside:
        name = _fold(it["title"])
        if name:
            by.setdefault(name, {})[it.get("via") or _company_of(it)] = it
    shared = sorted(((n, cos) for n, cos in by.items() if len(cos) >= 2), key=lambda x: (-len(x[1]), x[0]))
    if shared:
        mine = {it["ref"] for it in _companies(report)}
        bits = [f"{next(iter(cos.values()))['title']} on {len(cos)} of the companies reached, {sum(1 for c in cos if c in mine)} of them the "
                f"person's confirmed (" + ", ".join(sorted({it.get('entity_title') or c for c, it in cos.items()})[:EXAMPLES]) + ")"
                for n, cos in shared[:EXAMPLES]]
        return flag("shared-boards", V, "fired", "info",
                    f"of {len(by)} name(s) beside the person, {len(shared)} appear on two or more of the companies reached: " + "; ".join(bits)
                    + "; each is a set of rows that share a name, near, never confirmed one person",
                    citations=tuple(it["ref"] for _, cos in shared for it in cos.values()), scope="near")
    if _walk_short(report):
        return flag("shared-boards", V, "blocked", "info", "the walk stopped before reading the officers of every company the person has a row on",
                    scope="officer-group")
    return flag("shared-boards", V, "clear", "info", f"of {len(by)} name(s) beside the person, none appears on more than one of the companies reached",
                sources_held=(OFFICERS_HELD,), scope="officer-group")


# ── who stands on the register ──────────────────────────────────────────────

def _current(it) -> bool:
    return bool(it["row"].get("in_latest")) and not it["row"].get("ended_on")


def officers_of_record(report):
    if _other_start(report):
        return flag("officers-of-record", V, "blocked", "info", _other_start(report), scope="entity")
    if not _company_start(report):
        return flag("officers-of-record", V, "clear", "info", "the party is a person: its own roles are listed in the officers section",
                    sources_held=(COMPANIES_HELD,), scope="entity")
    r = report["subject"]["row"]
    if "partnership" in (r.get("entity_type") or "").lower():
        return _general_partners(report, "officers-of-record", "amber")
    sec = [it for it in section(report, "officers")["items"] if it.get("via") == report["subject"]["ref"]]
    dirs = [it for it in sec if it["view"] == "directors"]
    holders = [it for it in sec if it["view"] == "shareholders"]
    now = [it for it in dirs if _current(it)]
    omitted = section(report, "officers").get("omitted") or 0
    tail = f"; {omitted:,} row(s) past the walk's limit, not listed" if omitted else ""
    text = (f"{len(now)} current director(s) and {len(dirs) - len(now)} past or not in the latest file; "
            f"{len(holders)} holder(s) of record, {sum(1 for it in holders if _current(it))} in the latest file{tail}")
    reg = [it for it in items(report, ("company_lookup_roles",), ("confirmed",))
           if it.get("via") == report["subject"]["ref"] and not it.get("suppressed")]
    if reg:   # the business-number register's roles no monthly file holds (read since 1 November 2026): listed, never a clear's evidence
        ended = sum(1 for it in reg if (it.get("row") or {}).get("ended_on"))
        text += (f"; the business-number register states {len(reg)} role(s) no monthly file holds, {len(reg) - ended} with no end "
                 f"date and {ended} ended, each listed with the register's dates")
    going = GOING_STATUS.match(_status(report["subject"])) and r.get("in_latest", True)
    if not now and not omitted and going:
        return flag("officers-of-record", V, "fired", "amber", f"the companies file names no current director of the company: {text}",
                    citations=tuple(it["ref"] for it in dirs) or (report["subject"]["ref"],), scope="entity")
    return flag("officers-of-record", V, "clear", "info", text, sources_held=(OFFICERS_HELD,), scope="entity")


def _holds_for_others(it) -> bool:
    return any(f.get("kind") == "nominee" for f in it.get("flags", []))


def holders_of_record(report):
    """Holders of record that are companies or that hold as nominee or
    trustee, on the company or beside the person: each shown as the register
    states it, and the register beyond them is not followed."""
    if _other_start(report):
        return flag("holders-of-record", V, "blocked", "info", _other_start(report))
    rows = [it for s in ("officers", "web") for it in section(report, s)["items"] if it["view"] == "shareholders" and not it.get("suppressed")]
    company = [it for it in rows if it["row"].get("shareholder_type") == "company"]
    nominee = [it for it in rows if _holds_for_others(it) and it not in company]
    scope = "entity" if _company_start(report) else "officer-group"
    if company or nominee:
        bits = []
        if company:
            bits.append(f"{len(company)} holder(s) of record are companies: " + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in company[:EXAMPLES])
                        + "; a company holder's own directors and holders are not followed: start a report from it")
        if nominee:
            bits.append(f"{len(nominee)} hold as nominee or trustee, for others the register does not name: "
                        + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in nominee[:EXAMPLES]))
        return flag("holders-of-record", V, "fired", "amber" if _company_start(report) else "info",
                    "; ".join(bits) + "; each is shown as a holder of record, as the register states it",
                    citations=tuple(it["ref"] for it in company + nominee), scope=scope)
    if _company_start(report) and not [it for it in rows if it.get("via") == report["subject"]["ref"]]:
        return flag("holders-of-record", V, "blocked", "info", "the companies file lists no holder of record on the company", scope=scope)
    return flag("holders-of-record", V, "clear", "info", "no holder of record listed is a company or holds as nominee or trustee",
                sources_held=("Companies register shareholders (pub.shareholders)",), scope=scope)


def _at_office(hub) -> str:
    n = (hub.get("evidence") or {}).get("companies")
    return f"{n:,} companies at it" if isinstance(n, int) else hub["text"]


def shared_office(report):
    """MC-L2. The registered office, as a hub when fifty or more companies
    share it. Which companies share a smaller office is not listed."""
    if _other_start(report):
        return flag("shared-office", V, "blocked", "info", _other_start(report))
    offices = [it for s in ("officers", "web") for it in section(report, s)["items"] if it["view"] == "company_addresses"]
    hubs = [h for h in report.get("hubs", []) if h["kind"] in ("busy-address", "thousand-address")]
    # the walk flags a busy office on the company and on its address row; each company is counted once, by its own ref
    by_company = {}
    for h in hubs:
        by_company.setdefault(COMPANY_REF.match(h["ref"]).group(0) if COMPANY_REF.match(h["ref"]) else h["ref"], h)
    if hubs:
        return flag("shared-office", V, "fired", "info",
                    f"{len(by_company)} company(ies) met on the walk have a registered office shared by fifty or more companies: "
                    + "; ".join(f"{h['title']} ({_at_office(h)})" for h in list(by_company.values())[:EXAMPLES])
                    + "; a shared office here is no connection between the companies", citations=tuple(sorted({h["ref"] for h in hubs})))
    if _company_start(report) and not offices:
        return flag("shared-office", V, "blocked", "info", "the companies file lists no registered office for the company in the latest file",
                    scope="entity")
    return flag("shared-office", V, "clear", "info", "no registered office met on the walk is shared by fifty or more companies; the companies "
                "sharing a smaller office are not listed", sources_held=("Companies register addresses (pub.company_addresses)",),
                sources_not_held=("the companies that share a registered office with fewer than fifty others (not walked)",))


# ── the company's standing and the Gazette on it ────────────────────────────

def company_status(report):
    """The company's own register status; from a person, how each of the
    person's companies stands."""
    if _other_start(report):
        return flag("company-status", V, "blocked", "amber", _other_start(report))
    if _company_start(report):
        s = report["subject"]
        r = s["row"]
        status, kind = _status(s), r.get("entity_type") or "entity"
        nh = (LP_PARTNERS,) if "partnership" in kind.lower() else ()
        reg, removed = _date(r.get("registered_on")), _date(r.get("removed_on"))
        noun = "partnership" if "partnership" in kind.lower() else "society" if "societ" in kind.lower() else "company"
        when = f"registered {reg.isoformat()}" if reg else "registration date not stated"
        if removed:
            when += f", removed {removed.isoformat()}"
        if _ending(s) == "insolvent":
            return flag("company-status", V, "fired", "red", f"the companies file gives the {noun} the status {status!r} ({kind}; {when})",
                        citations=(s["ref"],), sources_not_held=nh + NOT_HELD_INSOLVENCY, scope="entity")
        if _ending(s) == "ended":
            return flag("company-status", V, "fired", "red", f"the {noun} is no longer a registered entity: status {status!r} ({kind}; {when})",
                        citations=(s["ref"],), sources_not_held=nh, scope="entity")
        if not r.get("in_latest", True):
            return flag("company-status", V, "fired", "amber", f"the {noun} is not in the latest companies file; its last status was {status!r} "
                        f"({kind}; {when}); the interface check of step 5.5 would date the change", citations=(s["ref"],), sources_not_held=nh,
                        scope="entity")
        if GOING_STATUS.match(status):
            return flag("company-status", V, "clear", "red", f"registered ({kind}; {when}) in the latest companies file",
                        sources_held=("Companies register status (pub.companies)",), sources_not_held=nh, scope="entity")
        return flag("company-status", V, "fired", "amber", f"the companies file gives a status this check does not know: {status!r} ({kind}; {when})",
                    citations=(s["ref"],), sources_not_held=nh, scope="entity")
    conf = _companies(report)
    nearby = _companies(report, ("near",))
    by = {"insolvent": [], "ended": [], "going": []}
    for it in conf:
        by[_ending(it)].append(it)
    ended_near = [it for it in nearby if _ending(it) != "going"]
    if by["insolvent"] or by["ended"]:
        bits = []
        if by["insolvent"]:
            bits.append(f"{len(by['insolvent'])} with an insolvency status: "
                        + "; ".join(f"{it['title']} ({_status(it)}; {it['dates']['text']})" for it in by["insolvent"][:EXAMPLES]))
        if by["ended"]:
            bits.append(f"{len(by['ended'])} removed or ended: "
                        + "; ".join(f"{it['title']} ({_status(it)}; {it['dates']['text']})" for it in by["ended"][:EXAMPLES]))
        bits.append(f"{len(by['going'])} registered")
        if ended_near:
            bits.append(f"and {len(ended_near)} more ended reached only through a near link, a namesake's until confirmed")
        return flag("company-status", V, "fired", "amber" if by["insolvent"] else "info",
                    f"of {len(conf)} company(ies) the person has a confirmed row on, " + "; ".join(bits),
                    citations=tuple(it["ref"] for it in by["insolvent"] + by["ended"]), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if ended_near:
        return flag("company-status", V, "fired", "amber",
                    f"no confirmed company has ended, but {len(ended_near)} reached only through a near link have: a namesake's companies, not the "
                    f"person's until confirmed: " + "; ".join(f"{it['title']} ({_status(it)})" for it in ended_near[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in ended_near), scope="near")
    if (report.get("walk") or {}).get("entities_omitted"):
        return flag("company-status", V, "blocked", "amber",
                    f"the walk listed the first companies it reached and left {report['walk']['entities_omitted']:,} past its limit; their status is not read",
                    scope="officer-group")
    return _clear_or_past("company-status", "amber",
                          f"each of the {len(conf)} company(ies) the person has a confirmed row on is registered" if conf else "the person has no confirmed company row",
                          sources_held=("Companies register status (pub.companies)",), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")


def insolvency_notices(report):
    """MC-L3. Gazette insolvency notices on the company started from, or on
    every company the person has a row on, each beside the person's own dates."""
    if _other_start(report):
        return flag("insolvency-notices", V, "blocked", "red", _other_start(report), sources_not_held=NOT_HELD_INSOLVENCY)
    if _company_start(report):
        own = [it for it in _notices(report) if _insolvency(it) and _on_subject(report, it)]
        if own:
            return flag("insolvency-notices", V, "fired", "red", f"{len(own)} Gazette insolvency notice(s) on the company ({_counted(own, _kind)}): "
                        f"{_side_by_side(report, own)}", citations=tuple(it["ref"] for it in own), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
        return flag("insolvency-notices", V, "clear", "red",
                    "no Gazette liquidation, receivership, administration, winding-up, creditors' notice or deed of company arrangement on the "
                    "company; its officers' other companies are not read (see repeat-insolvency)",
                    sources_held=(GAZETTE_HELD + ", joined to the company by its number",), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
    conf = [it for it in _notices(report) if _insolvency(it)]
    nearby = [it for it in _notices(report, ("near",)) if _insolvency(it)]
    if conf:
        return flag("insolvency-notices", V, "fired", "red",
                    f"{len(conf)} Gazette insolvency notice(s) on {len({it.get('via') for it in conf})} company(ies) the person has a row on; "
                    f"each date beside the person's: {_side_by_side(report, conf)}{_short_text(report)}",
                    citations=tuple(it["ref"] for it in conf), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if nearby:
        return flag("insolvency-notices", V, "fired", "amber",
                    f"{len(nearby)} Gazette insolvency notice(s) on companies reached only through a near link: a namesake's companies, "
                    f"not the person's until confirmed{_short_text(report)}", citations=tuple(it["ref"] for it in nearby),
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="near")
    if _walk_short(report):
        return flag("insolvency-notices", V, "blocked", "red",
                    "no Gazette insolvency notice on the companies the walk read, but it stopped before reading every company the person has a row on; "
                    "start a report from each company left out", scope="officer-group")
    return _clear_or_past("insolvency-notices", "red",
                          "no Gazette liquidation, receivership, administration, winding-up, creditors' notice or deed of company arrangement on "
                          "any company the person has a row on",
                          sources_held=(GAZETTE_HELD,), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")


def _kind(it) -> str:
    return _liq_kind(it) if _liq_view(it) else (it["row"].get("kind") or "notice")


def _insolvent_companies(report, grades=("confirmed",)) -> dict:
    """{company ref: [the earliest insolvency date or None, evidence refs]}."""
    out = {}
    for it in _companies(report, grades):
        if _ending(it) == "insolvent":
            out.setdefault(it["ref"], [None, []])[1].append(it["ref"])
    for it in _notices(report, grades):
        if not _insolvency(it):
            continue
        e = out.setdefault(it.get("via") or _company_of(it), [None, []])
        e[1].append(it["ref"])
        d = _notice_date(it)
        if d and (e[0] is None or d < e[0]):
            e[0] = d
    return out


def _repeat_insolvency_own(report):
    """Two or more of the person's companies with an insolvency, each with its
    date and the person's own dates on it. Side by side; nothing joins them."""
    if _company_start(report):   # the officers the walk followed (2 November 2026)
        return _of_failed(report, "repeat-insolvency", "red", fire="amber")
    if _other_start(report):
        return flag("repeat-insolvency", V, "blocked", "red", _other_start(report), scope="officer-group")
    bad = _insolvent_companies(report)
    nearby = {c: e for c, e in _insolvent_companies(report, ("near",)).items() if c not in bad}
    titles = {it["ref"]: it["title"] for it in _companies(report, ("confirmed", "near"))}
    if len(bad) >= 2:
        bits = []
        for c, (d, _) in sorted(bad.items(), key=lambda kv: (kv[1][0] is None, kv[1][0] or dt.date.min))[:EXAMPLES + 1]:
            roles = _role_on(report, c)
            mine = "; ".join(f"{r['row'].get('role_type') or 'shareholder of record'}, {r['dates']['text']}" for r in roles[:1]) or "role in the officers section"
            bits.append(f"{titles.get(c, c)} (first insolvency notice {d.isoformat() if d else 'not read; status only'}; the person's row: {mine})")
        return flag("repeat-insolvency", V, "fired", "red", f"{len(bad)} of the person's companies have an insolvency status or notice: " + " | ".join(bits),
                    citations=tuple(sorted({r for _, refs in bad.values() for r in refs})), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if len(bad) + len(nearby) >= 2:
        return flag("repeat-insolvency", V, "fired", "amber",
                    f"{len(bad)} confirmed company(ies) of the person's and {len(nearby)} reached only through a near link have an insolvency status "
                    f"or notice: a namesake's companies, not the person's until confirmed: "
                    + "; ".join(f"{titles.get(c, c)} (first insolvency notice {d.isoformat() if d else 'not read; status only'})"
                                for c, (d, _) in list(nearby.items())[:EXAMPLES]),
                    citations=tuple(sorted({r for _, refs in list(bad.values()) + list(nearby.values()) for r in refs})),
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="near")
    if _walk_short(report):
        return flag("repeat-insolvency", V, "blocked", "red", f"{len(bad)} company(ies) with an insolvency on the companies the walk read, but it "
                    "stopped before reading every company the person has a row on", scope="officer-group")
    return _clear_or_past("repeat-insolvency", "red",
                          f"{'one' if bad else 'no'} company the person has a confirmed row on has an insolvency status or notice; no repeat",
                          sources_held=(GAZETTE_HELD, "Companies register status (pub.companies)"), sources_not_held=NOT_HELD_INSOLVENCY,
                          scope="officer-group")


def amalgamation(report):
    """An amalgamation proposal naming the company, or one of the person's
    companies: the company may continue as, or have absorbed, another. The
    other companies in the proposal are other rows of the same notice, which
    the walk does not reach."""
    if _other_start(report):
        return flag("amalgamation", V, "blocked", "amber", _other_start(report))
    conf = [it for it in _notices(report) if _amalgamation(it)]
    unreached = "the other companies in each proposal are other rows of the same notice and are not reached: read the notice cited"
    if _company_start(report):
        own = [it for it in conf if _on_subject(report, it)]
        if own:
            return flag("amalgamation", V, "fired", "amber",
                        f"{len(own)} Gazette amalgamation proposal(s) name the company: "
                        + "; ".join(f"{it['row'].get('role') or 'role not stated'}, {it['dates']['text']}" for it in own[:EXAMPLES]) + f"; {unreached}",
                        citations=tuple(it["ref"] for it in own), scope="entity")
        return flag("amalgamation", V, "clear", "amber", "no Gazette amalgamation proposal names the company",
                    sources_held=(NOTICES_HELD + ", joined to the company by its number",), scope="entity")
    if conf:
        return flag("amalgamation", V, "fired", "info",
                    f"{len(conf)} Gazette amalgamation proposal(s) name {len({it.get('via') for it in conf})} company(ies) the person has a row on: "
                    + "; ".join(f"{it['title']} ({it['row'].get('role') or 'role not stated'}, {it['dates']['text']})" for it in conf[:EXAMPLES])
                    + f"; {unreached}", citations=tuple(it["ref"] for it in conf), scope="officer-group")
    if _walk_short(report):
        return flag("amalgamation", V, "blocked", "info", "the walk stopped before reading every company the person has a row on", scope="officer-group")
    return _clear_or_past("amalgamation", "info", "no Gazette amalgamation proposal names a company the person has a confirmed row on",
                          sources_held=(NOTICES_HELD,), scope="officer-group")


def register_events(report):
    """Removals, dissolutions, restorations, the Registrar's rectifications,
    transfers out, an overseas company ceasing. Not insolvency. On the
    company started from amber; on the person's companies info."""
    if _other_start(report):
        return flag("register-events", V, "blocked", "info", _other_start(report))
    conf = [it for it in _notices(report) if _event(it)]
    if _company_start(report):
        own = [it for it in conf if _on_subject(report, it)]
        if own:
            return flag("register-events", V, "fired", "amber", f"{len(own)} Gazette notice(s) on the company ({_counted(own, _event_kind)}): "
                        f"{_side_by_side(report, own)}", citations=tuple(it["ref"] for it in own), scope="entity")
        return flag("register-events", V, "clear", "amber", "no Gazette removal, dissolution, restoration, rectification or transfer notice on the company",
                    sources_held=(NOTICES_HELD,), scope="entity")
    if conf:
        return flag("register-events", V, "fired", "info",
                    f"{len(conf)} Gazette notice(s) ({_counted(conf, _event_kind)}) on {len({it.get('via') for it in conf})} company(ies) the person has a "
                    f"row on; each date beside the person's: {_side_by_side(report, conf)}", citations=tuple(it["ref"] for it in conf), scope="officer-group")
    if _walk_short(report):
        return flag("register-events", V, "blocked", "info", "no Gazette register notice on the companies the walk read, but it stopped before "
                    "reading every company the person has a row on", scope="officer-group")
    return _clear_or_past("register-events", "info", "no Gazette removal, dissolution, restoration, rectification or transfer notice on a company "
                          "the person has a confirmed row on", sources_held=(NOTICES_HELD,), scope="officer-group")


POSSESSIONS_HELD = ("a mortgagee's entry into possession as the Gazette states it, the company mortgagor and lender by register key "
                    "(pub.gazette_possessions)",)
POSSESSIONS_NOT_HELD = ("a mortgagee possession whose mortgagor is a person (the name and the property stay in the gazette lane's private "
                        "tables)", "the Personal Property Securities Register (interface awaited since 19 September 2026)")


def mortgagee_possession(report):
    """A mortgagee's entry into possession, as the Gazette states it (pub.gazette_possessions), where the mortgagor is the entity or a
    company the rules confirm the person is on: amber; where a company here is the lender, or the row is near: info. From a company,
    none is clear as the Gazette states them; from a person, none is blocked: a person mortgagor's name stays in the lane's private
    tables. The property is never shown."""
    if _other_start(report):
        return flag("mortgagee-possession", V, "blocked", "amber", _other_start(report), sources_not_held=POSSESSIONS_NOT_HELD)
    subject = report["subject"]["ref"]
    mine = ({subject} | {it["ref"] for it in items(report, ("companies",), ("confirmed",))}
            | {it.get("via") for it in items(report, None, ("confirmed",)) if it.get("via")})
    def key_of(it, col):
        k = (it.get("row") or {}).get(col)
        return f"companies:{k}" if k else None
    ps = [it for it in items(report, ("gazette_possessions",)) if not it.get("suppressed")]
    own = [it for it in ps if it["grade"] == "confirmed" and (key_of(it, "mortgagor_register_key") == subject
                                                               or (_person_start(report) and key_of(it, "mortgagor_register_key") in mine))]
    lender = [it for it in ps if it not in own and key_of(it, "mortgagee_register_key") in mine]
    near = [it for it in ps if it not in own and it not in lender]
    if own:
        return flag("mortgagee-possession", V, "fired", "amber", f"{len(own)} mortgagee entry(ies) into possession where the mortgagor is "
                    + ("the entity" if _company_start(report) else "a company the person is confirmed on") + ": "
                    + "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in own[:3]) + "; the property is not shown",
                    citations=tuple(it["ref"] for it in own), sources_held=POSSESSIONS_HELD, sources_not_held=POSSESSIONS_NOT_HELD)
    if lender or near:
        rows = lender + near
        return flag("mortgagee-possession", V, "fired", "info", f"{len(rows)} mortgagee entry(ies) into possession reached, none on the "
                    f"entity or the person's own companies as mortgagor ({len(lender)} with a company here as the lender, {len(near)} near): "
                    + "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in rows[:3]),
                    citations=tuple(it["ref"] for it in rows), sources_held=POSSESSIONS_HELD, sources_not_held=POSSESSIONS_NOT_HELD)
    if _company_start(report):
        return flag("mortgagee-possession", V, "clear", "amber", "no mortgagee entry into possession in the Gazette names the entity as "
                    "mortgagor", sources_held=POSSESSIONS_HELD, sources_not_held=POSSESSIONS_NOT_HELD)
    return flag("mortgagee-possession", V, "blocked", "amber", "no mortgagee entry into possession in the Gazette names a company the "
                "person is confirmed on as mortgagor; one naming the person as mortgagor is not shown (the name stays in the gazette lane's "
                "private tables), so no clear is given", sources_held=POSSESSIONS_HELD, sources_not_held=POSSESSIONS_NOT_HELD)


# ── the people ──────────────────────────────────────────────────────────────

def _in_force(report, it) -> str:
    as_of = _as_of(report)
    end = _date(it["row"].get("ends_on"))
    if it["row"].get("permanent"):
        return f"permanent; in force on {as_of.isoformat()}"
    if not end:
        return "no end filed"
    return f"in force on {as_of.isoformat()}" if end >= as_of else f"ended before {as_of.isoformat()}"


def prohibition(report):
    if _company_start(report):   # the officers the walk followed (2 November 2026)
        return _of_notice(report, "prohibition", ("gazette_prohibitions",), "Gazette director prohibition", "red")
    live = [it for it in items(report, ("gazette_prohibitions",)) if not it.get("suppressed")]   # a revoked prohibition is never counted
    conf = [it for it in live if it["grade"] == "confirmed"]
    nearby = [it for it in live if it["grade"] == "near"]
    if conf:
        return flag("prohibition", V, "fired", "red", f"{len(conf)} Gazette director prohibition notice(s) confirmed to the person: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']}; {_in_force(report, it)})" for it in conf[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in conf))
    if nearby:
        return flag("prohibition", V, "fired", "amber",
                    f"{len(nearby)} Gazette director prohibition notice(s) under a name near the person's; a namesake's until confirmed: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']}; {_in_force(report, it)}; near: {it.get('reason')})" for it in nearby[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in nearby), scope="near")
    if _other_start(report):
        return flag("prohibition", V, "blocked", "red", _other_start(report))
    w = report.get("walk") or {}
    if not w.get("links_built"):
        return flag("prohibition", V, "blocked", "red", "no links are published, so a prohibition under the person's name cannot be reached")
    if w.get("links_omitted"):
        return flag("prohibition", V, "blocked", "red",
                    f"the walk left {w['links_omitted']:,} link(s) unread past its limit; a prohibition could be among them, so no clear is given")
    return flag("prohibition", V, "clear", "red",
                "no Gazette director prohibition confirmed or near the person: the link rules join every prohibition notice by name, "
                "and every link from the person's rows was read",
                sources_held=("New Zealand Gazette prohibition notices (pub.gazette_prohibitions), joined by name in pub.links",))


def bankruptcy(report):
    if _company_start(report):   # the officers the walk followed (2 November 2026)
        return _of_notice(report, "bankruptcy", ("gazette_bankruptcies",), "Gazette bankruptcy notice", "red",
                          never_clear="no link rule confirms a Gazette bankruptcy notice to a person yet (a notice is reached by name only, near), so a bankruptcy of an officer the walk followed cannot be ruled out; the blank is not a clear")
    live_c = [it for it in items(report, ("gazette_bankruptcies",), ("confirmed",)) if not it.get("suppressed")]
    live_n = [it for it in items(report, ("gazette_bankruptcies",), ("near",)) if not it.get("suppressed")]
    if live_c:
        return flag("bankruptcy", V, "fired", "red", f"{len(live_c)} Gazette bankruptcy notice(s) confirmed to the person: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in live_c[:EXAMPLES]), citations=tuple(it["ref"] for it in live_c))
    if live_n:
        return flag("bankruptcy", V, "fired", "amber", f"{len(live_n)} Gazette bankruptcy notice(s) under a name near the person's; "
                    "a namesake's until confirmed", citations=tuple(it["ref"] for it in live_n), scope="near")
    return flag("bankruptcy", V, "blocked", "red",
                "Gazette bankruptcy notices are published, but no link rule joins one to a person yet, so this report cannot see a bankruptcy "
                "of the person or of a company's officers; the blank is not a clear", sources_not_held=NOT_HELD_INSOLVENCY)


def practitioner_roles(report):
    """The person named as liquidator in Gazette notices: an insolvency
    practitioner acts for a company's creditors, which a firm acting against
    those companies wants to know. Joined to the person by the link rules."""
    if _company_start(report):   # the officers the walk followed (2 November 2026)
        return _of_practitioner(report, "practitioner-roles", "info")
    live = [it for it in items(report, ("gazette_liquidators",)) if not it.get("suppressed")]
    conf = [it for it in live if it["grade"] == "confirmed"]
    nearby = [it for it in live if it["grade"] == "near"]
    if conf:
        return flag("practitioner-roles", V, "fired", "info",
                    f"named as liquidator in {len(conf)} Gazette notice(s): " + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in conf[:EXAMPLES])
                    + "; the companies are named in each notice cited", citations=tuple(it["ref"] for it in conf))
    if nearby:
        return flag("practitioner-roles", V, "fired", "info",
                    f"{len(nearby)} Gazette liquidator appointment(s) under a name near the person's; a namesake's until confirmed",
                    citations=tuple(it["ref"] for it in nearby), scope="near")
    if _other_start(report):
        return flag("practitioner-roles", V, "blocked", "info", _other_start(report))
    if (report.get("walk") or {}).get("links_omitted"):
        return flag("practitioner-roles", V, "blocked", "info", "the walk left links unread past its limit; an appointment could be among them")
    return flag("practitioner-roles", V, "clear", "info", "not named as liquidator in a Gazette notice the link rules join to the person",
                sources_held=("New Zealand Gazette liquidators (pub.gazette_liquidators), joined by name in pub.links",),
                sources_not_held=("receivers and administrators named in notices (pub.gazette_practitioners: no link reaches them)",))


def young_entity(report):
    as_of = _as_of(report)
    if _other_start(report):
        return flag("young-entity", V, "blocked", "info", _other_start(report))
    pool = [report["subject"]] if _company_start(report) else _companies(report)
    young = [(it, _date(it["row"].get("registered_on"))) for it in pool]
    young = [(it, reg) for it, reg in young if reg and (as_of - reg).days < YOUNG_DAYS]
    who = "the company was" if _company_start(report) else f"{len(young)} company(ies) the person has a confirmed row on were"
    if young:
        return flag("young-entity", V, "fired", "info", f"{who} registered under 24 months before {as_of.isoformat()}: "
                    + "; ".join(f"{it['title']} (registered {reg.isoformat()})" for it, reg in young[:EXAMPLES]),
                    citations=tuple(it["ref"] for it, _ in young))
    if not _company_start(report) and (report.get("walk") or {}).get("entities_omitted"):
        return flag("young-entity", V, "blocked", "info", f"the walk left {report['walk']['entities_omitted']:,} company(ies) past its limit, "
                    "and their registration dates are not read")
    return flag("young-entity", V, "clear", "info", "registered 24 months ago or more" if _company_start(report)
                else "no company the person has a confirmed row on was registered under 24 months ago",
                sources_held=("Companies register registration dates (pub.companies)",))


def namesake_exposure(report):
    names = list(section(report, "identity")["items"])
    nearby_elsewhere = [it for s in report["sections"] if s["name"] not in ("identity", "web") for it in s["items"] if it["grade"] == "near"]
    w = report.get("walk") or {}
    g = report.get("group") or {}
    bits = []
    if len(names) >= NAMESAKE_PARTIAL_AT:
        bits.append(f"{len(names)} namesake row(s) set apart: the name is common, and this report is partial; a conflict search on the name "
                    "alone will meet every one of them; confirm the party by a second fact before relying on any row")
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
            bits.append(f"{ne:,} company(ies) listed with their status, their Gazette notices and officers not read")
        if om:
            bits.append(f"{om:,} past the walk's limit, not listed")
        return flag("walk-coverage", V, "fired", "amber", "the walk did not read every company it reached: " + "; ".join(bits)
                    + "; start a report from each company left out", citations=(report["subject"]["ref"],))
    return flag("walk-coverage", V, "clear", "info", "every company the walk reached was read for its notices and officers",
                sources_held=("pub.companies", "pub.gazette_liquidations", "pub.gazette_company_notices", "pub.directors", "pub.shareholders"))


def subject_hub(report):
    if _other_start(report):
        return flag("subject-hub", V, "blocked", "info", _other_start(report))
    own = {report["subject"]["ref"]} | {m["ref"] for m in report.get("members", [])}
    mine = [h for h in report.get("hubs", []) if h["ref"] in own and h["kind"] in ("professional-director", "nominee", "crown")]
    if mine:
        kinds = sorted({h["kind"] for h in mine})
        return flag("subject-hub", V, "fired", "info", f"the party is itself a hub ({', '.join(kinds)}): {mine[0]['text']}",
                    citations=tuple(sorted({h["ref"] for h in mine})))
    return flag("subject-hub", V, "clear", "info", "the party is not a professional director, a nominee or the Crown on the rows held",
                sources_held=("pub.directors", "pub.groups"))


def past_roles(report):
    if HISTORY:
        return flag("past-roles", V, "clear", "info", "past roles and holdings are published with their filed end dates", sources_held=(COMPANIES_HELD,))
    left = [it for it in all_items(report).values() if it["view"] in ("directors", "shareholders") and it["grade"] == "confirmed"
            and not it["row"].get("in_latest", True)]
    seen = f"; {len(left)} of the rows listed left the file since July 2026 and carry no end date" if left else ""
    whose = "the company's past officers and holders" if _company_start(report) else "the person's past directorships and holdings"
    return flag("past-roles", V, "blocked", "amber", f"{whose} are not held: {PAST_NOT_HELD}{seen}; a firm that acted for or against a company "
                "the person has left cannot see it here; the change history and the business-number interface (step 5.5) would date them",
                sources_not_held=("past directorships and shareholdings with their end dates",))


# ── charity, society and political money ────────────────────────────────────

def _charity_unread(report):
    """Why a charity officer row under the subject's name could not have been seen, or None: the template reads
    pub.charity_officers, the walk did not skip it, the subject's row is one the walk looks the name up from, and no row of that
    name was left past the walk's limit."""
    reads = {r["view"] for r in (report.get("template") or {}).get("reads", [])}
    if report.get("template") and "charity_officers" not in reads:
        return "the template does not read pub.charity_officers"
    if "charity_officers" in ((report.get("walk") or {}).get("skipped") or ()):
        return "pub.charity_officers is not published where this report was built"
    s = report["subject"]
    if s.get("suppressed") or s["view"] not in NAME_LOOKED_UP:
        return (f"a charity officer row is looked for under the name a {', '.join(sorted(NAME_LOOKED_UP))} row carries; the report "
                f"starts from pub.{s['view']}, so no name was looked for")
    left = sum(x.get("omitted", 0) for x in report["sections"] if "charity_officers" in (x.get("omitted_views") or ()))
    if left:
        return f"the walk left {left:,} charity officer row(s) of the same name past its limit"
    return None


def _charity_roles(report) -> list:
    """The charity officer rows that carry the subject's name: near by name (rule same-name), never a row of another person on a
    charity; a suppressed name is never counted."""
    return [it for it in items(report, ("charity_officers",)) if it.get("rule") == "same-name" and not it.get("suppressed")]


def _company_charities(report) -> list:
    """Started from a company, its charity by business number (confirmed, rule official-number), with the officer rows on it."""
    if not _company_start(report):
        return []
    out = []
    for c in items(report, ("charities",), ("confirmed",)):
        officers = [it for it in items(report, ("charity_officers",), ("confirmed",)) if it.get("via") == c["ref"]]
        out.append((c, officers))
    return out


def _marked(it) -> bool:
    """The register's own mark on an officer row: its `disqualified` field, as the register states it."""
    return it["row"].get("disqualified") is True


def charity_officer_roles(report):
    if _company_start(report):   # the officers the walk followed (2 November 2026)
        return _of_charity(report, "charity-officer-roles", "info")
    # the officers of a society the report starts from are that society's, not the subject's roles
    conf = [it for it in items(report, ("society_officers",), ("confirmed",)) if it.get("via") != report["subject"]["ref"]]
    by_name, own = _charity_roles(report), _company_charities(report)
    if conf or by_name or own:
        bits = [f"officer of {len({it.get('via') or _company_of(it) for it in conf})} incorporated society(ies): "
                + "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in conf[:EXAMPLES])] if conf else []
        bits += [f"{len(by_name)} charity officer row(s) carry the person's name, near: {CHARITY_BY_NAME}: "
                 + "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in by_name[:EXAMPLES])] if by_name else []
        bits += [f"the company's charity by its business number: {c['statement']} ({c['dates']['text']}), {len(o)} officer row(s) on it"
                 for c, o in own[:EXAMPLES]]
        return flag("charity-officer-roles", V, "fired", "info", " | ".join(bits),
                    citations=tuple(dict.fromkeys([it["ref"] for it in conf + by_name] + [c["ref"] for c, _ in own])),
                    scope="subject" if conf or own else "near")
    if _other_start(report):
        return flag("charity-officer-roles", V, "blocked", "info", _other_start(report))
    why = _charity_unread(report)
    if why:
        return flag("charity-officer-roles", V, "blocked", "info", f"no incorporated society officer role is confirmed to the person, but {why}, "
                    "so no clear is given")
    return flag("charity-officer-roles", V, "clear", "info", "no incorporated society officer role confirmed to the person, and no charity "
                "officer row carries the person's name", sources_held=("Incorporated Societies Register officers (pub.society_officers)", CHARITY_HELD))


def charity_integrity_marks(report):
    """The Charities Register's own mark on an officer row (`disqualified`), with the status it files: red on a row of the company's
    own charity, amber on a row that only carries the person's name (a namesake's until a rule confirms it)."""
    if _company_start(report):   # the officers the walk followed (2 November 2026)
        return _of_marks(report, "charity-integrity-marks", MARK_SEVERITY)
    marked = [it for it in items(report, ("charity_officers",)) if _marked(it) and not it.get("suppressed")]
    if marked:
        conf = [it for it in marked if it["grade"] == "confirmed"]
        return flag("charity-integrity-marks", V, "fired", MARK_SEVERITY if conf else "amber",
                    f"{len(marked)} charity officer row(s) carry the register's disqualified mark, {len(conf)} on a charity confirmed to the "
                    "subject: " + "; ".join(f"{it['statement']} ({it['dates']['text']}" + (f"; near: {it.get('reason')})" if it["grade"] == "near" else ")")
                                            for it in marked[:EXAMPLES])
                    + ("" if len(conf) == len(marked) else f"; a row matched by name: {CHARITY_BY_NAME}"),
                    citations=tuple(it["ref"] for it in marked), scope="entity" if conf else "near")
    if _other_start(report):
        return flag("charity-integrity-marks", V, "blocked", MARK_SEVERITY, _other_start(report))
    why = _charity_unread(report)
    if why:
        return flag("charity-integrity-marks", V, "blocked", MARK_SEVERITY, f"{why}, so no clear is given")
    return flag("charity-integrity-marks", V, "clear", MARK_SEVERITY, "no charity officer row carrying the person's name has the register's "
                "disqualified mark", sources_held=(CHARITY_HELD,))



def political_money(report):
    money = list(items(report, MONEY_VIEWS, ("confirmed",)))
    if money:
        return flag("political-money", V, "fired", "info", f"{len(money)} row(s) of political money or a promoter's role confirmed to the party; "
                    "each listed in its section with its date and the party or candidate filed", citations=tuple(it["ref"] for it in money))
    if _other_start(report):
        return flag("political-money", V, "blocked", "info", _other_start(report))
    near_money = [it for it in section(report, "identity")["items"] if it["view"] in MONEY_VIEWS]
    whose = "the company (its officers' are not read)" if _company_start(report) else "the person"
    return flag("political-money", V, "clear", "info", f"no donation, loan, disclosure or promoter's role confirmed to {whose}"
                + (f"; {len(near_money)} filed under a name it only shares are listed with the namesakes" if near_money else ""),
                sources_held=("Electoral Commission returns and disclosures", "Register of Promoters"),
                sources_not_held=("a candidate's own return, not yet joined to a person",))


# ── what is not held ────────────────────────────────────────────────────────



def disciplinary_findings(report):
    return _tribunal(report, ("NZLCDT", "NZLCRO"), "disciplinary-findings", "amber", "the Lawyers and Conveyancers Disciplinary Tribunal "
                     "and the Legal Complaints Review Officer", "a finding against a lawyer, conveyancer, accountant or other practitioner",
                     DISCIPLINARY[1:])


def comcom_coverage(report):
    return _listed(report, ("commerce_commission_parties", "fma_parties"), "comcom-coverage", "amber",
                   "the Commerce Commission or the Financial Markets Authority")


# ── the regulators' listings (WorkSafe, the Commerce Commission, the FMA; into the report 1 November 2026) ─────────

REG_HELD = {"worksafe_parties": "WorkSafe New Zealand's court summaries and enforceable undertakings as it lists them today (pub.worksafe_parties)",
            "commerce_commission_parties": "the Commerce Commission's cases as it lists them today (pub.commerce_commission_parties)",
            "fma_parties": "the Financial Markets Authority's warnings and actions as it lists them today (pub.fma_parties)"}
REG_EXAMPLES = 3


def _through_officer(rows) -> str:
    """How many of the rows an officer's name reached (an officer the walk followed one step): the officer's namesake, never the entity's."""
    n = sum(1 for it in rows if it.get("through"))
    return f" ({n} under the name of an officer the walk followed: the officer's namesake)" if n else ""


def _listed(report, views, flag_id, severity, what, not_held=(), clears=True):
    """A regulator's listing that names the entity or a person the rules confirm is the subject (fired at `severity`), one that
    names only a namesake (amber: nothing in it is the entity's), or none: clear as the listings stand today, or blocked where a
    register the check also needs is not held."""
    conf = [it for it in items(report, views, ("confirmed",)) if not it.get("suppressed")]
    near = [it for it in items(report, views, ("near",)) if not it.get("suppressed")]
    held = tuple(REG_HELD[v] for v in views)
    if conf:
        shown = "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in conf[:REG_EXAMPLES])
        more = f"; and {len(conf) - REG_EXAMPLES} more, each in the section" if len(conf) > REG_EXAMPLES else ""
        return flag(flag_id, V, "fired", severity, f"{len(conf)} listing(s) by {what} name the entity or a person the rules confirm "
                    f"is the subject: {shown}{more}; a listing states what the regulator published, never a cause",
                    citations=tuple(it["ref"] for it in conf), sources_held=held, sources_not_held=tuple(not_held))
    if near:
        return flag(flag_id, V, "fired", "amber", f"{len(near)} listing(s) by {what} name a namesake the rules do not confirm is the "
                    f"subject{_through_officer(near)}: {'; '.join(it['statement'] for it in near[:REG_EXAMPLES])}; nothing in a namesake's listing is the entity's",
                    citations=tuple(it["ref"] for it in near), sources_held=held, sources_not_held=tuple(not_held))
    text = f"no listing by {what}, as it lists them today, names the entity or a person the rules confirm is the subject"
    if clears:
        return flag(flag_id, V, "clear", severity, text, sources_held=held, sources_not_held=tuple(not_held))
    return flag(flag_id, V, "blocked", severity, f"{text}; but {'; '.join(not_held)} is not held, so no clear is given",
                sources_held=held, sources_not_held=tuple(not_held))


def securities_register(report):
    return flag("securities-register", V, "blocked", "info",
                "who has registered security over the company's assets, and when, is in the Personal Property Securities Register, which is not "
                "held; a secured creditor is a party a firm may act for or against, and this check cannot run", sources_not_held=(SECURITIES,))



# ── a namesake's past role at a failed company (Arthur, 2 November 2026: option b) ───────────────────────────────

PAST_ROLES_HELD = ("the roles and past holdings the business-number register states and no monthly file held (pub.company_lookup_roles, "
                   "pub.company_lookup_holdings), read company by company")
PAST_EXAMPLES = 3


def _namesake_past_failures(report):
    """The register roles under the subject's or a principal's name, near, at a company that later failed (an insolvent status or a
    Gazette liquidation notice, as the walk attaches it); each once."""
    seen, out = set(), []
    for it in items(report, ("company_lookup_roles", "company_lookup_holdings"), ("near",)):   # holdings: Arthur, 2 November 2026
        if it.get("failure") and not it.get("suppressed") and it["ref"] not in seen:
            seen.add(it["ref"])
            out.append(it)
    return out


def _failed_text(it):
    f = it["failure"]
    if f.get("notice"):
        return f"named in a Gazette liquidation notice{' published ' + f['on'] if f.get('on') else ''}"
    return f"{f['status']} in the latest companies file"


def _with_past_failures(f, report, alone=1):
    """Adds the namesake past roles at failed companies to a failure check: appended to a fired flag; otherwise the flag fires amber,
    its own finding kept after it, when they are on at least `alone` failed companies (2 for a check that counts repeats). Never red:
    nothing confirms the namesake is the subject."""
    hit = _namesake_past_failures(report)
    if not hit or (f["status"] != "fired" and len({(it.get("row") or {}).get("entity_key") or it["ref"] for it in hit}) < alone):
        return f
    bits = "; ".join(f"{it['statement']} ({it['dates']['text']}), {_failed_text(it)}" for it in hit[:PAST_EXAMPLES])
    more = f"; and {len(hit) - PAST_EXAMPLES} more, each listed" if len(hit) > PAST_EXAMPLES else ""
    note = (f"{len(hit)} past role(s) or holding(s) the business-number register states under the name, at a company that later failed: {bits}{more}; "
            "a person with this name, not confirmed to be the subject")
    cites = tuple(it["ref"] for it in hit) + tuple(it["failure"]["notice"] for it in hit if it["failure"].get("notice"))
    if f["status"] == "fired":
        return dict(f, text=f"{f['text']} || {note}", citations=tuple(dict.fromkeys(tuple(f["citations"]) + cites)),
                    sources_held=tuple(dict.fromkeys(tuple(f["sources_held"]) + (PAST_ROLES_HELD,))))
    return flag(f["rule"], f["version"], "fired", "amber", f"{note}; on its own finding, {f['status']}: {f['text']}", citations=cites,
                sources_held=tuple(f["sources_held"]) + (PAST_ROLES_HELD,), sources_not_held=f["sources_not_held"], scope=f["scope"])


def repeat_insolvency(report):
    """repeat-insolvency, with a namesake's past role at a failed company as an amber warning (option b, 2 November 2026)."""
    return _with_past_failures(_repeat_insolvency_own(report), report, alone=2)   # a repeat needs two


COURT_V = "1"

# ── the courts corpus held (into the report 2 November 2026) ──────────────────────────────────────────────────────

COURT_VIEWS = ("court_judgment_parties", "court_people")
COURT_HELD = ("the courts corpus held: the judgments' parties as each heading names them (pub.court_judgment_parties) and the people "
              "and bodies the text reader found in a court document (pub.court_people)",)
COURT_NOT_HELD = ("Court judgments the corpus held does not carry: most of the High Court's, the Court of Appeal's and the District "
                  "Court's, and most tribunals'",)
COURT_EXAMPLES = 3


def _court_parties(report, grades):
    """A party to a judgment the corpus holds: every row of a judgment's heading, and a court document's person or body read as a
    party or a company (never its judge, counsel or a witness); withheld and suppressed names never counted; each once."""
    seen, out = set(), []
    for it in items(report, COURT_VIEWS, grades):
        row = it.get("row") or {}
        if it.get("suppressed") or row.get("withheld") or row.get("anonymised") or it["ref"] in seen:
            continue
        if it["ref"].split("/")[-2] == "person" and row.get("role") not in ("party", "company"):
            continue
        seen.add(it["ref"])
        out.append(it)
    return out


def court_judgments(report):
    """A party the rules confirm is the subject, in a judgment the corpus holds: amber (being a party is not a finding against
    anyone); a namesake's: info; none: blocked, because the corpus holds a part of the courts' judgments and none is not a finding."""
    conf = _court_parties(report, ("confirmed",))
    near = [it for it in _court_parties(report, ("near",)) if it["ref"] not in {c["ref"] for c in conf}]
    if conf:
        named = "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in conf[:COURT_EXAMPLES])
        more = f"; and {len(conf) - COURT_EXAMPLES} more, each in the section" if len(conf) > COURT_EXAMPLES else ""
        return flag("court-judgments", COURT_V, "fired", "amber", f"{len(conf)} party row(s) in a judgment the corpus holds name the "
                    f"subject or a person the rules confirm is the subject: {named}{more}; being a party is not a finding against anyone",
                    citations=tuple(it["ref"] for it in conf), sources_held=COURT_HELD, sources_not_held=COURT_NOT_HELD)
    officers = [it for it in near if it.get("rule") == "through-officer"]
    namesakes = [it for it in near if it.get("rule") != "through-officer"]
    if near:
        bits = []
        if officers:
            bits.append(f"{len(officers)} name a person on the subject (an officer or holder of record): "
                        f"{'; '.join(it['statement'] for it in officers[:COURT_EXAMPLES])}; an officer's case is the officer's, not the entity's")
        if namesakes:
            bits.append(f"{len(namesakes)} name a namesake the rules do not confirm is the subject: "
                        f"{'; '.join(it['statement'] for it in namesakes[:COURT_EXAMPLES])}; nothing in a namesake's case is the subject's")
        return flag("court-judgments", COURT_V, "fired", "info", f"{len(near)} party row(s) in a judgment the corpus holds, near: "
                    + " || ".join(bits), citations=tuple(it["ref"] for it in near), sources_held=COURT_HELD, sources_not_held=COURT_NOT_HELD)
    return flag("court-judgments", COURT_V, "blocked", "amber", "no party row in a judgment the corpus holds names the subject or a "
                "person the rules confirm is the subject; the corpus holds a part of the courts' judgments, so no clear is given",
                sources_held=COURT_HELD, sources_not_held=COURT_NOT_HELD)


COURT_CODE = re.compile(r"\[\d{4}\]\s*(NZ[A-Za-z]+)")


def _court_of(it):
    """The court or tribunal code of a party row: the heading's own column, or the citation's ([2024] NZERA 484 is NZERA)."""
    row = it.get("row") or {}
    if row.get("court"):
        return row["court"]
    m = COURT_CODE.search(str(row.get("citation") or it.get("entity_title") or it.get("statement") or ""))
    return m.group(1) if m else None


def _tribunal(report, codes, rule_id, severity, who, what, not_held):
    """A tribunal's decisions as the courts corpus holds them (`codes`): a party the rules confirm is the subject fires at `severity`;
    an officer's or a namesake's fires info; none is blocked, as the corpus holds a part of them and `not_held` is not held."""
    held = (f"the decisions of {who} as the courts corpus holds them (pub.court_judgment_parties, pub.court_people)",)
    not_held = tuple(not_held) + (f"the decisions of {who} the courts corpus does not carry",)
    conf = [it for it in _court_parties(report, ("confirmed",)) if _court_of(it) in codes]
    near = [it for it in _court_parties(report, ("near",)) if _court_of(it) in codes and it["ref"] not in {c["ref"] for c in conf}]
    if conf:
        named = "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in conf[:COURT_EXAMPLES])
        return flag(rule_id, COURT_V, "fired", severity, f"{len(conf)} party row(s) in the decisions of {who} the corpus holds name the subject "
                    f"or a person the rules confirm is the subject: {named}; being a party is not a finding against anyone",
                    citations=tuple(it["ref"] for it in conf), sources_held=held, sources_not_held=not_held)
    if near:
        return flag(rule_id, COURT_V, "fired", "info", f"{len(near)} party row(s) in the decisions of {who} the corpus holds, near, name an officer "
                    f"on the subject or a namesake, not the subject: {'; '.join(it['statement'] for it in near[:COURT_EXAMPLES])}",
                    citations=tuple(it["ref"] for it in near), sources_held=held, sources_not_held=not_held)
    return flag(rule_id, COURT_V, "blocked", severity, f"no party row in the decisions of {who} the corpus holds names the subject or a person "
                f"the rules confirm is the subject; {what} cannot all be seen: the corpus holds a part of them, so no clear is given",
                sources_held=held, sources_not_held=not_held)


# ── started from a company: the officers the walk followed (2 November 2026) ────────────────────────────────────────────────
# The walk follows each current officer of a company start one step (walk.follow_officers): the rows of the officer's group (a
# confirmed link's), role rows only when current, the companies and societies those sit on and the Gazette notices on them, every
# one near by the through-people default and carrying `through` (the officer's row on the start); beside them the rows an
# officer's near link or name alone reaches (`near_link`: a namesake's until a rule confirms it, counted apart). A row reached
# through an officer is the officer's, never the company's: amber at most, scope officer-group. An officer not followed (a
# suppressed name, one past the walk's limit) leaves the check blocked and says how many; a check over the officers' companies
# also waits on past roles (the companies file lists current roles only), as the same check from a person does.

OF_OFFICER_VIEWS = ("directors", "society_officers", "charity_officers")
OF_ROLE_VIEWS = ("directors", "shareholders", "society_officers", "charity_officers")
OF_TROUBLED = ("liquidat", "receiver", "administration", "insolv")
OF_GROUPS = "pub.groups: each officer's confirmed rows, followed one step"


def _of_walk(report) -> dict:
    return report.get("walk") or {}


def _of_officers(report) -> dict:
    """{ref: item} the officers listed on the company the report starts from (its directors; a society's or charity's officers)."""
    s = report["subject"]["ref"]
    return {it["ref"]: it for it in items(report, OF_OFFICER_VIEWS, ("confirmed", "near")) if it.get("via") == s
            and not it.get("through") and it.get("kind", "person") == "person"}


def _of_short(report):
    """Why the walk did not follow every officer of the company, or None when it followed them all."""
    w = _of_walk(report)
    if "officers" not in (w.get("buckets") or ()):
        return "the walk did not follow the company's officers (the officers reach did not run)"
    hidden = w["officers_suppressed"] if w.get("officers_listed") is not None else sum(1 for o in _of_officers(report).values() if o.get("suppressed"))
    bits = ([f"{w['officers_omitted']:,} past the walk's limit"] if w.get("officers_omitted") else []) + \
           ([f"{hidden} whose name is suppressed"] if hidden else [])
    if not bits:
        return None
    return f"the walk followed {w.get('officers_followed', 0)} of the company's officer(s) one step and not {' and '.join(bits)}"


def _of_gap(report):
    """The reason a check over the company's officers cannot clear, or None."""
    listed = _of_walk(report).get("officers_listed")
    if (listed == 0) if listed is not None else not _of_officers(report):
        return "the companies file lists no current officer on the company, so no check over its officers can be given as clear"
    w = _of_walk(report)
    if not w.get("links_built"):
        return "no links are published, so an officer's own rows cannot be reached"
    if w.get("links_omitted"):
        return f"the walk left {w['links_omitted']:,} link(s) unread past its limit"
    return _of_short(report)


def _of_through(report, views=None) -> list:
    """Rows reached through an officer's own confirmed rows: the officer's record, near by the through-people default."""
    return [it for it in items(report, views, ("confirmed", "near"))
            if it.get("through") and not it.get("near_link") and not it.get("above") and not it.get("suppressed")]


def _of_apart(report, views=None) -> list:
    """Rows only an officer's near link or name reaches: a namesake's until a rule confirms it, never the officer's own."""
    return [it for it in items(report, views, ("confirmed", "near"))
            if it.get("through") and it.get("near_link") and not it.get("above") and not it.get("suppressed")]


def _of_current(it) -> bool:
    return bool(it["row"].get("in_latest", True)) and not it["row"].get("ended_on")


def _of_who(report, it) -> str:
    o = _of_officers(report).get(it.get("through"))
    if not o:
        return "an officer"
    return f"{o['title']} ({o['row'].get('role_type') or 'officer'} of the company, {o['dates']['text']})"


def _of_on(it) -> str:
    return it.get("entity_title") or it["title"]


def _of_lines(report, rows, label) -> str:
    bits = [f"{_of_who(report, it)} | {label(it)}" for it in rows[:EXAMPLES]]
    return " ; ".join(bits) + (f"; and {len(rows) - EXAMPLES} more" if len(rows) > EXAMPLES else "")


def _of_set_apart(rows, noun) -> str:
    if not rows:
        return ""
    ex = "; ".join(f"{_of_on(r)} ({r['dates']['text']}; {r.get('rule') or 'near'})" for r in rows[:EXAMPLES])
    return (f"; and {len(rows)} {noun} only an officer's near link or name reaches, set apart (a namesake's until a rule confirms it, "
            f"never the officer's own): {ex}")


def _of_followed(report) -> str:
    return f"the {_of_walk(report).get('officers_followed', 0)} officer(s) the walk followed one step"


def _of_cite(*groups) -> tuple:
    return tuple(dict.fromkeys(it["ref"] for g in groups for it in g))


def _of_when(it):
    r = it["row"]
    return _date(r.get("event_on")) or _date(r.get("appointed_on")) or _date(r.get("published_on")) or _date(r.get("decided_on")) \
        or _date(r.get("started_on")) or _date(r.get("appointed_on")) or dt.date.min


def _of_none(rule, severity, text, past, held, report, apart, apart_noun, **kw):
    """What a check over the officers says when nothing was found on their own records: blocked while an officer was not
    followed, or while past roles are not held for a check over their companies; a namesake's rows only, info; else clear."""
    also = _of_set_apart(apart, apart_noun)
    gap = _of_gap(report)
    if gap:
        return flag(rule, V, "blocked", severity, f"{text}; but {gap}: no clear is given" + also, scope="officer-group", **kw)
    if apart:
        return flag(rule, V, "fired", "info", text + also, citations=_of_cite(apart), scope="near", **kw)
    if past and not globals().get("HISTORY", False):
        return flag(rule, V, "blocked", severity, f"{text}; but the companies file lists current roles only, so a company an officer left, "
                    "or that was removed with the officer on it, is not seen: no clear is given", scope="officer-group", **kw)
    return flag(rule, V, "clear", severity, text, sources_held=held + (OF_GROUPS,), scope="officer-group", **kw)


def _of_failed(report, rule, severity="red", fire="amber"):
    """The other companies the company's officers sit on that have a Gazette insolvency notice or a status that reads as one,
    each beside the officer it came through; amber at most: the company is the officer's."""
    notices = sorted((it for it in _of_through(report) if _insolvency(it)), key=_of_when, reverse=True)
    status = [it for it in _of_through(report, ("companies",)) if it["ref"] != report["subject"]["ref"]
              and any(w in (it["row"].get("status") or "").lower() for w in OF_TROUBLED)]
    apart = [it for it in _of_apart(report) if _insolvency(it)]
    if notices or status:
        on = {it.get("via") for it in notices} | {it["ref"] for it in status}
        text = (f"{len(notices)} Gazette insolvency notice(s) and {len(status)} insolvent status(es) on {len(on)} other company(ies) the "
                "company's officers sit on, newest first: "
                + _of_lines(report, notices + status, lambda it: f"{it['title']}, {it['dates']['text']}"
                            + (f", status {it['row'].get('status')}" if it in status else ""))
                + "; each company is the officer's, not the company's; two dated facts side by side, nothing joins them")
        short = _of_short(report)
        return flag(rule, V, "fired", fire, text + (f"; {short}" if short else "") + _of_set_apart(apart, "insolvency notice(s)"),
                    citations=_of_cite(notices, status, apart), scope="officer-group")
    return _of_none(rule, severity, f"no Gazette insolvency notice and no insolvent status on the other current companies of "
                    f"{_of_followed(report)}", True, ("New Zealand Gazette notices, joined to each company by its number",),
                    report, apart, "insolvency notice(s)")


def _of_notice(report, rule, views, noun, severity="red", never_clear=None):
    """A notice on an officer's own record (a director prohibition, a bankruptcy): red on an officer's confirmed rows, amber on
    a row only a near link or name reaches; blocked while an officer was not followed; `never_clear` keeps it blocked when the
    link rules do not reach the notice at all."""
    own = sorted(_of_through(report, views), key=_of_when, reverse=True)
    apart = _of_apart(report, views)
    if own:
        return flag(rule, V, "fired", severity, f"{len(own)} {noun}(s) on the record of an officer of the company: "
                    + _of_lines(report, own, lambda it: f"{it['title']}, {it['dates']['text']}")
                    + _of_set_apart(apart, f"{noun}(s)"), citations=_of_cite(own, apart), scope="officer-group")
    if never_clear:
        return flag(rule, V, "blocked", severity, never_clear + _of_set_apart(apart, f"{noun}(s)"), scope="officer-group")
    return _of_none(rule, severity, f"no {noun} on the records of {_of_followed(report)}", False,
                    (f"New Zealand Gazette (pub.{views[0]}), joined by name in pub.links",), report, apart, f"{noun}(s)")


def _of_roles(report, rule, severity="amber", noun="other current role(s)", fire=None):
    """The officers' other current roles: the companies and societies each also sits on, dated, beside the officer."""
    roles = [it for it in _of_through(report, OF_ROLE_VIEWS) if _of_current(it)]
    apart = [it for it in _of_apart(report, OF_ROLE_VIEWS) if _of_current(it)]
    if roles:
        by = {}
        for it in roles:
            by.setdefault(it["through"], []).append(it)
        return flag(rule, V, "fired", fire or severity, f"{len(by)} of the company's officer(s) hold {len(roles)} {noun} on "
                    f"{len({_of_on(it) for it in roles})} other organisation(s): "
                    + _of_lines(report, roles, lambda it: f"{it['row'].get('role_type') or it['view'].replace('_', ' ')[:-1]} of {_of_on(it)}, "
                                                          f"{it['dates']['text']}")
                    + "; each role is the officer's, not the company's" + _of_set_apart(apart, "role(s)"),
                    citations=_of_cite(roles, apart), scope="officer-group")
    return _of_none(rule, severity, f"none of {_of_followed(report)} holds another current role in the registers read", False,
                    ("Companies Office companies file (pub.directors, pub.shareholders)", "Incorporated Societies Register officers"),
                    report, apart, "role(s)")


def _of_practitioner(report, rule, severity="info"):
    """An officer named as liquidator in Gazette notices, joined to the officer by the link rules."""
    return _of_notice(report, rule, ("gazette_liquidators",), "Gazette liquidator appointment", severity)


def _of_charity(report, rule, severity="info"):
    """The officers' society roles (their confirmed rows) and the charity officer rows that carry an officer's name (set apart);
    the company's own charity by its business number, with its officer rows."""
    own = [(c, [it for it in items(report, ("charity_officers",), ("confirmed",)) if it.get("via") == c["ref"]])
           for c in items(report, ("charities",), ("confirmed",)) if not c.get("through")]
    roles = [it for it in _of_through(report, ("society_officers", "charity_officers")) if _of_current(it)]
    apart = _of_apart(report, ("society_officers", "charity_officers"))
    if roles or own:
        bits = ([f"the company's charity by its business number: " + "; ".join(f"{c['statement']} ({c['dates']['text']}), {len(o)} officer "
                                                                              "row(s) on it" for c, o in own[:EXAMPLES])] if own else []) + \
               ([f"{len(roles)} society or charity role(s) on an officer's own record: "
                 + _of_lines(report, roles, lambda it: f"{it['statement']} ({it['dates']['text']})")] if roles else [])
        return flag(rule, V, "fired", severity, " | ".join(bits) + _of_set_apart(apart, "society or charity officer row(s)"),
                    citations=_of_cite(roles, apart, [c for c, _ in own]), scope="officer-group" if roles else "entity")
    return _of_none(rule, severity, f"no society or charity officer role on the records of {_of_followed(report)}, and the company has no "
                    "charity row by its business number", False, ("Incorporated Societies Register officers (pub.society_officers)",
                    "Charities Register (pub.charities, pub.charity_officers)"), report, apart, "society or charity officer row(s)")


def _of_marks(report, rule, severity):
    """The Charities Register's disqualified mark: on an officer row of the company's own charity (the company's own record), or on
    a charity officer row reached through an officer (an officer's own, or set apart where only the name meets)."""
    def marked(it):
        return it["row"].get("disqualified") is True and not it.get("suppressed")
    on_charity = [it for it in items(report, ("charity_officers",), ("confirmed",)) if not it.get("through") and not it.get("suppressed")]
    own = [it for it in on_charity if marked(it)]
    through = [it for it in _of_through(report, ("charity_officers",)) if marked(it)]
    apart = [it for it in _of_apart(report, ("charity_officers",)) if marked(it)]
    if own or through:
        return flag(rule, V, "fired", severity, f"{len(own)} officer row(s) on the company's own charity and {len(through)} on an officer's "
                    "own record carry the register's disqualified mark: "
                    + "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in (own + through)[:EXAMPLES])
                    + _of_set_apart(apart, "marked charity officer row(s)"),
                    citations=_of_cite(own, through, apart), scope="entity" if own else "officer-group")
    return _of_none(rule, severity, (f"the {len(on_charity)} officer row(s) on the company's charity carry no disqualified mark; " if on_charity
                                     else "") + f"no charity officer row on the company's own charity or on the records of "
                    f"{_of_followed(report)} carries the register's disqualified mark", False, ("Charities Register officers (pub.charity_officers)",),
                    report, apart, "marked charity officer row(s)")


def _of_companies(report, rule, severity="info", fire=None):
    """The other companies the company's officers sit on, each beside the officer; the people on those companies are not read."""
    cos = [it for it in _of_through(report, ("companies",)) if it["ref"] != report["subject"]["ref"]]
    apart = [it for it in _of_apart(report, ("companies",)) if it["ref"] != report["subject"]["ref"]]
    if cos:
        return flag(rule, V, "fired", fire or severity, f"{len(cos)} other company(ies) the company's officers sit on: "
                    + _of_lines(report, cos, lambda it: f"{it['title']} ({(it['row'].get('status') or 'status not filed')}; {it['dates']['text']})")
                    + "; each is the officer's, not the company's; the other people on them are not read (the walk follows an officer one "
                      "step)" + _of_set_apart(apart, "company(ies)"), citations=_of_cite(cos, apart), scope="officer-group")
    return _of_none(rule, severity, f"none of {_of_followed(report)} sits on another current company", True,
                    ("Companies Office companies file (pub.directors, pub.companies)",), report, apart, "company(ies)")


def _of_beside(report, rule, severity):
    """Who sat beside the officers on their other companies (2 November 2026): the walk's `beside` reach lists the current
    directors of each company a followed officer sits on, near, through the officer; a name on two or more of those companies is
    two rows that share a name, beside the officers twice. Never confirmed one person, and nothing here says what the seats mean."""
    w = _of_walk(report)
    if "beside" not in (w.get("buckets") or ()):
        return flag(rule, V, "blocked", severity, "the walk followed the officers one step and did not read who sat beside them on their other companies (the beside reach did not run)",
                    scope="officer-group")
    officers = _of_officers(report)
    own = {_fold(o["title"]) for o in officers.values()}   # the company's own officers, beside each other elsewhere: counted already
    beside = [it for it in items(report, ("directors",), ("confirmed", "near")) if it.get("beside") and not it.get("suppressed")
              and _fold(it["title"]) not in own]
    by = {}
    for it in beside:
        name = _fold(it["title"])
        if name:
            by.setdefault(name, {})[it.get("via")] = it
    shared = sorted(((n, cos) for n, cos in by.items() if len(cos) > 1), key=lambda x: (-len(x[1]), x[0]))
    gap = _of_short(report)
    tail = f"; {gap}" if gap else ""
    if shared:
        bits = [f"{next(iter(cos.values()))['title']} on {len(cos)} of the officers' other companies ("
                + ", ".join(sorted({it.get('entity_title') or c for c, it in cos.items()})[:EXAMPLES]) + ")"
                for n, cos in shared[:EXAMPLES]]
        return flag(rule, V, "fired", severity,
                    f"of {len(by)} name(s) beside the {len(officers)} officer(s) on their other companies, {len(shared)} appear on two "
                    f"or more of those companies: " + "; ".join(bits) + "; each is a set of rows that share a name, near, through the "
                    "officer and then the company, never confirmed one person" + tail,
                    citations=tuple(it["ref"] for _, cos in shared for it in cos.values()), scope="near")
    if gap or _of_gap(report):
        return flag(rule, V, "blocked", severity, (gap or _of_gap(report)) + f"; of {len(by)} name(s) read beside them, none on two "
                    "of the officers' other companies", scope="officer-group")
    return flag(rule, V, "clear", severity, f"of {len(by)} name(s) beside {_of_followed(report)} on their other companies, none appears "
                "on more than one of those companies", sources_held=(OFFICERS_HELD,), scope="officer-group")


RULES = (client_overlap, conflict_web, shared_boards, officers_of_record, holders_of_record, shared_office, company_status, insolvency_notices,
         repeat_insolvency, amalgamation, register_events, mortgagee_possession, prohibition, bankruptcy, practitioner_roles, young_entity,
         namesake_exposure, walk_coverage, subject_hub, past_roles, charity_officer_roles, charity_integrity_marks, political_money,
         court_judgments, disciplinary_findings, comcom_coverage, securities_register)
