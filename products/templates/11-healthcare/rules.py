"""The healthcare operator governance rules (plan 5.2, use case 11). Pure
functions over the built report, each returning one flag. An aged-care
investor or a regulator's analyst asks who governs this operator, what its
charity arm files, and where its officers overlap. The rules stand for the
old estate's healthcare checks (its requirements, section 2.5: MC-H1 the
operator web with its roll-up, MC-H2 the charity's financial claims, MC-H3
officer overlap across the web; the statutory-supervisor churn it could not
evidence) and its person rules (data-layer/flags/flags/person_rules.py,
person-0.2: charity-officer-roles, charity-integrity-marks, prohibition,
young-entity, namesake-exposure), taken as ideas and tests, not code, where
the held registers can support them:

  entity-status            the entity's own register status (a company, a society, a charitable trust board, a village row)
  young-entity             registered under 24 months
  insolvency-notice        Gazette insolvency notices on the entity, each dated from its notice
  officer-company-notices  Gazette insolvency notices on the companies the entity's officers (or the person) sit on, each beside the
                           officer's own role on that company, dated
  disqualified-officer     a director prohibition in the Gazette on the person or on an officer, and a charity officer the
                           register marks disqualified
  officer-bankruptcy       a bankruptcy in the Gazette on the person or on an officer
  officer-overlap          the officers' other current roles, dated, care-named companies counted apart, hubs flagged
  charity-arm              the charities the entity or its people are officers of, with their status
  charity-audit-opinion    a modified audit opinion on a charity's return
  charity-return-filed     no return filed for a charity's last period
  namesake-exposure        the report's own uncertainty
  walk-coverage            how much of the web the walk read
  subject-hub              the start is a professional director, a nominee or the Crown
  past-roles               blocked: current roles only
  retirement-villages, hdc-decisions, certification-audits, provider-registers, aged-care-commissioner, court-judgments
                           blocked, never clear: not held

The builder adds its common rules for every template (group-standing,
hubs-met, replaced-return); this file carries no copy of them.

Every rule branches on the start: a company, a society, a person, or
anything else. From an organisation the walk follows its first officers one
step only when the template names the `officers` reach (it does) and says
how many it left; a check through an officer is blocked when an officer was
not followed (the agriculture lesson). An officer's near link (a row the
link rules join to the officer by name alone, `near_link` on the item) is a
namesake's row: the overlap and the notices on the officers' companies count
it apart, never as the officer's own, and a notice reached by one is never
red. A notice on a company above in the holding chain (`above`) is the
holder's: listed in the Gazette section, counted beside the entity's own
notices and never as one. The charity rules read
pub.charities, pub.charity_officers and pub.charity_returns: a company's
charity by its business number (confirmed, with the officers and returns on
it, graded as the company is), and a charity officer row that carries a
person's name (near: no link joins the Charities Register's officers to any
other row yet, so a rule over such a row is amber at most). Evidence on
confirmed rows is red or amber; the same evidence reached through a near
link is amber at most.
Dates sit side by side; no flag joins two facts with a word of cause, none
calls a holder an owner, and none prints an address or an officer's contact
detail.

Imports nothing of products.report: the one-way test holds a template folder
to its own code. The shape loads this file by path and binds the name
`contract` (products/report/contract.py) before it runs."""
from __future__ import annotations

import datetime as dt
import re

V = "0.1"
YOUNG_DAYS = 730          # under 24 months registered (the old young-entity rule)
NAMESAKE_NOTE_AT = 5      # namesakes set apart at which the report's caveat fires
NAMESAKE_PARTIAL_AT = 50  # past this many namesakes the report is declared partial
EXAMPLES = 3              # dated examples a fired flag states in its text
#: a charity has six months after its balance date to file its annual return (Charities Act 2005, s 41); a return is taken as
#: the period's when its period end falls within this many days of the balance date the register states
FILE_WITHIN_DAYS = 183
PERIOD_SLACK_DAYS = 31
#: whether a published view holds past roles with their end dates. It does not (measured 2026-10-20 by banking-1): the companies file
#: lists current roles only. While False, a check over past roles never clears.
HISTORY = False
PAST_NOT_HELD = ("the companies file lists current roles only: a role the person left, or a company struck off with them on it, is not "
                 "seen, nor a notice on it")
#: a word in a registered name that reads as care or retirement living: the registers carry no industry, so this is a sign, never a finding
CARE_NAME = re.compile(r"\b(care|lifecare|healthcare|health|hospital|hospice|rest ?home|retirement|village|villages|aged|senior|seniors|"
                       r"eldercare|nursing|dementia|living|lifestyle|residential)\b", re.I)

INSOLVENCY_KINDS = ("winding-up application", "receivership", "administration", "notice to creditors", "deed of company arrangement")
INSOLVENT_STATUS = re.compile(r"liquidation|receiv|administration|statutory management", re.I)
ENDED_STATUS = re.compile(r"^(removed|deregistered|dissolved|closed|cancelled|inactive|suspended|removed as disqualified|struck off)$", re.I)
GOING_STATUS = re.compile(r"^(registered|active)$", re.I)
HUB_KINDS = ("professional-director", "nominee", "crown")
OFFICER_VIEWS = ("directors", "society_officers")
ROLE_VIEWS = ("directors", "shareholders", "society_officers")
ORGANISATION_VIEWS = ("companies", "societies")
CHARITY_VIEWS = ("charities", "charity_officers", "charity_returns")
#: the views whose rows the walk looks a person's name up from in the Charities Register (the shape's NAME_JOIN_FROM)
NAME_LOOKED_UP = ("directors", "society_officers", "members", "candidates", "mp_interest_returns", "promoter_people", "gazette_appointments")
#: the words a fired flag must not carry, the shape's own (rules 3 and 4): a register's name that holds one is not quoted in a flag
UNSAFE = re.compile(contract.CAUSE.pattern + "|" + contract.OWNER.pattern, re.I)   # noqa: F821  (bound by the loader)

COMPANIES_HELD = "Companies register (pub.companies, pub.directors, pub.shareholders)"
SOCIETIES_HELD = "Incorporated Societies Register (pub.societies, pub.society_officers)"
GAZETTE_HELD = "New Zealand Gazette liquidation and company notices (pub.gazette_liquidations, pub.gazette_company_notices)"
INSOLVENCY_REGISTER = "the Official Assignee's Insolvency Register (interface awaited since 19 September 2026)"
COURTS = "court judgments: the OpenLaw case-law lane and the courts register (step 5.4)"
CHARITIES = "the Charities Register (pub.charities, pub.charity_officers, pub.charity_returns), which this template does not name in its reads"
#: the registers a health regulator keeps, each named first as the catalogue's not-held key names it (the not-held section cites
#: the key, so the flag and the memo's not-held line name the same register), then what the flag needs said
VILLAGES = ("The retirement villages file: each village's operator and statutory supervisor (key retirement_villages; and when the "
            "supervisor changed; the companies lane carries the village's own row only)")
HDC = "Health and Disability Commissioner decisions (key hdc; and case notes; to acquire, plan 5.3)"
CERTIFICATION = ("Certification audits of rest homes and hospitals (key certification; under the Health and Disability Services (Safety) "
                 "Act 2001)")
PROVIDERS = "The Ministry of Health's provider registers (key health_providers; certified providers and their premises)"
AGED_CARE_COMMISSIONER = "The Aged Care Commissioner's reports (key aged_care_commissioner; and findings)"
NOT_FOLLOWED = ("started from an organisation, the report follows its officers one step to their other current roles; some were not "
                "followed, so start a report from each officer listed")


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


def _iso(d) -> str:
    return d.isoformat() if d else "undated"


def _company_start(report) -> bool:
    return report["subject"]["view"] == "companies"


def _organisation_start(report) -> bool:
    return report["subject"]["view"] in ORGANISATION_VIEWS


def _person_start(report) -> bool:
    """A person row, or a filed row that takes the group of the person row a
    confirmed link names: the walk reads that person's record."""
    return report["subject"]["kind"] == "person" or bool((report.get("group") or {}).get("via"))


def _village(report) -> bool:
    """A retirement village's own row in the companies register: a name, a number, a status, and nothing joins it to an operator."""
    return _company_start(report) and "/retirement_village/" in report["subject"]["ref"]


def _other_start(report):
    """A start row that is neither an organisation nor a person (a notice): the record these checks read is not walked from it."""
    if _organisation_start(report) or _person_start(report):
        return None
    s = report["subject"]
    article = "an" if s["kind"][:1] in "aeiou" else "a"
    return (f"the report starts from {article} {s['kind']} row (pub.{s['view']}), not a person, a company or a society: the record these "
            f"checks read is not walked from it, so no clear is given; start the report from a person row or from the organisation")


def _subject_key(report) -> str:
    return report["subject"]["ref"].split(":", 1)[1]


def _on_subject(report, it) -> bool:
    return it.get("via") == report["subject"]["ref"] or (it["row"].get("register_key") or "") == _subject_key(report)


def _reads(report, view) -> bool:
    """Whether the template reads the view (the builder names the template's reads in the report)."""
    return view in {r["view"] for r in (report.get("template") or {}).get("reads", [])}


def _walk(report) -> dict:
    return report.get("walk") or {}


def _officers_short(report):
    """Why an organisation start's officers were not all followed, or None when they were."""
    w = _walk(report)
    if "officers" not in (w.get("buckets") or []):
        return "the walk did not follow the entity's officers (the officers reach did not run)"
    if w.get("officers_omitted"):
        return f"the walk followed {w.get('officers_followed', 0)} officer(s) and left {w['officers_omitted']:,} past its limit"
    return None


def _no_officers(report):
    """Why an organisation start's officers cannot be read at all, or None: a register row that lists no officer (a charitable trust
    board's trustees, an incorporated society's officers on its companies register row, a village's operator) is not a board with
    nobody on it."""
    if any(it["view"] in OFFICER_VIEWS and it.get("via") == report["subject"]["ref"] for it in all_items(report).values()):
        return None
    s = report["subject"]
    kind = (s["row"].get("entity_type") or "").lower()
    trustees = _own_charity_officers(report)
    if _village(report):
        where = "a retirement village's register row names no operator and no officer: the retirement villages file is not held"
    elif "charitable trust" in kind and trustees:
        where = (f"a charitable trust board's trustees are filed with the Charities Register: {len(trustees)} officer row(s) on its charity, "
                 "reached by its business number, are listed and their own disqualified mark is read, but they are not followed to their "
                 "other roles; start a report from each trustee")
    elif "charitable trust" in kind:
        where = ("a charitable trust board's trustees are filed with the Charities Register, and no charity row carries this board's business "
                 "number")
    elif "society" in kind:
        where = ("an incorporated society's officers are in the societies register, under the society's own row there; start the report "
                 "from that row")
    else:
        where = "the register lists no current officer on the entity"
    return f"no officer of the entity is listed: {where}; so no check over its officers can be given as clear"


def _officer_gap(report):
    """The whole reason an organisation start's officer checks cannot clear, or None."""
    if _no_officers(report):
        return _no_officers(report)
    if _officers_short(report):
        return f"{_officers_short(report)}: {NOT_FOLLOWED}"
    return None


def _walk_short(report) -> bool:
    w = _walk(report)
    return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))


def _name(it) -> str:
    """A row's title for a flag's text; a register name that carries a word
    the shape reads as cause or ownership is not quoted (the section lists it)."""
    t = it.get("title") or it["ref"]
    return f"the row cited ({it['ref']})" if UNSAFE.search(t) else t


def _charity_title(it) -> str:
    """The charity an officer row sits on, by its register name, unless that name carries a word the shape reads as cause or ownership."""
    t = it.get("entity_title") or ""
    return t if t and not UNSAFE.search(t) else "a charity (cited)"


def _who(it) -> str:
    return "name suppressed" if it.get("suppressed") else _name(it)


def _entity_name(it) -> str:
    t = it.get("entity_title") or ""
    if not t:
        return "a company"
    return f"the company cited ({it['ref']})" if UNSAFE.search(t) else t


def _status(it) -> str:
    return (it["row"].get("status") or "").strip()


def _ending(it) -> str:
    st = _status(it)
    if INSOLVENT_STATUS.search(st):
        return "insolvent"
    if ENDED_STATUS.match(st) or _date(it["row"].get("removed_on")) or _date(it["row"].get("deregistered_on")):
        return "ended"
    return "going" if GOING_STATUS.match(st) or not st else "ended"


def _current(it) -> bool:
    return bool(it["row"].get("in_latest", True)) and not it["row"].get("ended_on")


def _start_of(it):
    r = it["row"]
    return _date(r.get("appointed_on")) or _date(r.get("started_on"))


def _role(it) -> str:
    r = it["row"]
    return r.get("role_type") or r.get("role") or ("shareholder of record" if it["view"] == "shareholders" else "officer")


def _hub_refs(report) -> dict:
    return {h["ref"]: h for h in report.get("hubs", []) if h.get("kind") in HUB_KINDS}


def _subject_hub(report) -> list:
    own = {report["subject"]["ref"]} | {m["ref"] for m in report.get("members", [])}
    return [h for h in report.get("hubs", []) if h["ref"] in own and h["kind"] in HUB_KINDS]


def _contested(it) -> bool:
    return "contested" in (it.get("reason") or "")


# ── the Gazette ─────────────────────────────────────────────────────────────

def _insolvency(it) -> bool:
    if it["view"] == "gazette_liquidations":
        return True
    r = it["row"]
    return it["view"] == "gazette_company_notices" and r.get("kind") in INSOLVENCY_KINDS and "ceas" not in (r.get("action") or "").lower()


def _kind(it) -> str:
    return "liquidation" if it["view"] == "gazette_liquidations" else (it["row"].get("kind") or "notice")


def _notice_date(it):
    """The day a notice dates: a liquidator's or receiver's appointment where the Gazette states one, otherwise its publication."""
    r = it["row"]
    if it["view"] == "gazette_liquidations":
        return _date(r.get("appointed_on")) or _date(r.get("published_on"))
    if (r.get("event_basis") or "") == "appointment":
        return _date(r.get("event_on")) or _date(r.get("published_on"))
    return _date(r.get("published_on")) or _date(r.get("filed_on"))


def _notices(report, grades=("confirmed", "near")):
    return [it for it in items(report, ("gazette_liquidations", "gazette_company_notices"), grades) if _insolvency(it)]


def _company_of(it) -> str:
    if it.get("entity"):
        return it["entity"]["ref"]
    key = it["row"].get("entity_key") or it["row"].get("register_key")
    if key:
        return f"companies:{key}"
    return it.get("via") or ""


# ── the officers and their other roles ──────────────────────────────────────

def _officer_rows(report) -> dict:
    """{ref: item} the entity's own officers: its directors and society officers as the register lists them on it."""
    s = report["subject"]["ref"]
    return {it["ref"]: it for it in all_items(report).values() if it["view"] in OFFICER_VIEWS and it.get("via") == s}


def _own_charity_officers(report) -> list:
    """The officer rows the Charities Register files on the entity's own charity, reached by the entity's business number (confirmed):
    a charitable trust board's trustees are filed there, not on its companies register row. Not followed to their other roles."""
    s = report["subject"]["ref"]
    mine = {it["ref"] for it in items(report, ("charities",), ("confirmed",)) if it.get("via") == s}
    return [it for it in items(report, ("charity_officers",), ("confirmed",)) if it.get("via") in mine]


def _through(report, views) -> list:
    """Rows the walk reached through an officer of the entity: the officer's own rows (near by the through-people default)."""
    return [it for it in items(report, views, ("confirmed", "near")) if it.get("through") and it.get("rule") == "through-officer"]


def _through_link(report, views) -> list:
    """Rows an officer's near link reaches (the link rules join them to the officer by name alone): a namesake's until confirmed, never
    the officer's own."""
    return [it for it in items(report, views, ("confirmed", "near")) if it.get("through") and it.get("near_link") and not it.get("above")]


def _above(report, views) -> list:
    """Rows read on a company above in the holding chain: the holder's, never the entity's."""
    return [it for it in items(report, views, ("confirmed", "near")) if it.get("above")]


def _namesake_roles(report) -> dict:
    """{officer ref: [current role rows an officer's near link reaches]}."""
    out = {}
    for it in _through_link(report, ROLE_VIEWS):
        if _current(it):
            out.setdefault(it["through"], []).append(it)
    return out


def _apart(rows, noun) -> str:
    """The rows an officer's near link reaches, counted apart: a namesake's until a rule confirms it."""
    if not rows:
        return ""
    ex = "; ".join(f"{_role(r) if r['view'] in ROLE_VIEWS else _kind(r)} on {_entity_name(r)} ({r['dates']['text']}; {r.get('rule') or 'near'})"
                   for r in rows[:EXAMPLES])
    return (f"; and {len(rows)} {noun} an officer's near link reaches (the link rules join the row to the officer by name alone: a "
            f"namesake's until a rule confirms it, never the officer's own): {ex}")


def _companies_through(report) -> dict:
    """{company ref: item} the companies and societies an officer's other roles sit on."""
    return {it["ref"]: it for it in _through(report, ORGANISATION_VIEWS)}


def _overlap(report) -> dict:
    """{officer ref: [the officer's other current role rows]}."""
    out = {}
    for it in _through(report, ROLE_VIEWS):
        if _current(it):
            out.setdefault(it["through"], []).append(it)
    return out


def _person_roles(report) -> list:
    """The person's own current confirmed roles and holdings."""
    return [it for it in all_items(report).values() if it["view"] in ROLE_VIEWS and it["grade"] == "confirmed" and _current(it)
            and not it.get("through")]


def _group_roles(report) -> list:
    """The current roles on the rows of the person's group that a contested group lists near: the group's, not confirmed the person's."""
    if not (report.get("group") or {}).get("contested"):
        return []
    return [it for it in all_items(report).values() if it["view"] in ROLE_VIEWS and it["grade"] == "near" and _current(it)
            and not it.get("through") and _contested(it)]


#: words that lead a registered name and say nothing of whose it is
LEAD_SKIP = frozenset({"the", "nz", "new", "zealand", "a"})


def _lead_word(title: str) -> str:
    """The first word of a registered name that is not an article or the country: 'BUPA CARE SERVICES NZ LIMITED' -> 'bupa'. A company
    whose care-named role carries the entity's own leading word is likely the entity's own subsidiary or sister; it is counted apart,
    and the register does not say so."""
    for w in re.findall(r"[a-zāēīōū0-9']+", (title or "").lower()):
        if w not in LEAD_SKIP:
            return w
    return ""


def _care(title: str) -> bool:
    return bool(CARE_NAME.search(title or ""))


# ── the entity's standing ───────────────────────────────────────────────────

def entity_status(report):
    if _other_start(report):
        return flag("entity-status", V, "blocked", "red", _other_start(report), scope="entity")
    if not _organisation_start(report):
        return flag("entity-status", V, "clear", "info", "the start is a person: how each of the person's companies stands is in the governance "
                    "section and the flag officer-company-notices", sources_held=(COMPANIES_HELD,), scope="entity")
    s = report["subject"]
    r = s["row"]
    status = _status(s)
    kind = r.get("entity_type") or ("incorporated society" if s["view"] == "societies" else
                                     "retirement village (its register row)" if _village(report) else "entity")
    reg, removed = _date(r.get("registered_on")), _date(r.get("removed_on"))
    when = f"registered {reg.isoformat()}" if reg else "registration date not stated"
    if removed:
        when += f", removed {removed.isoformat()}"
    nh = (VILLAGES,) if _village(report) else ()
    held = (SOCIETIES_HELD,) if s["view"] == "societies" else ("Companies register status (pub.companies)",)
    if _ending(s) == "insolvent":
        return flag("entity-status", V, "fired", "red", f"the register gives the entity the status {status!r} ({kind}; {when})",
                    citations=(s["ref"],), sources_not_held=nh + (INSOLVENCY_REGISTER,), scope="entity")
    if _ending(s) == "ended":
        return flag("entity-status", V, "fired", "red", f"the entity is no longer on the register as registered: status {status!r} ({kind}; {when})",
                    citations=(s["ref"],), sources_not_held=nh, scope="entity")
    if not r.get("in_latest", True):
        return flag("entity-status", V, "fired", "amber", f"the entity is not in the latest file; its last status was {status!r} ({kind}; {when})",
                    citations=(s["ref"],), sources_not_held=nh, scope="entity")
    return flag("entity-status", V, "clear", "red", f"registered ({kind}; {when}) in the latest file", sources_held=held, sources_not_held=nh,
                scope="entity")


def young_entity(report):
    """Registered under 24 months: a short record to weigh. Amber on the entity."""
    as_of = _as_of(report)
    if _other_start(report):
        return flag("young-entity", V, "blocked", "amber", _other_start(report), scope="entity")
    if not _organisation_start(report):
        pool = [it for it in all_items(report).values() if it["view"] in ORGANISATION_VIEWS and it["grade"] == "confirmed" and _ending(it) == "going"
                and it["ref"] != report["subject"]["ref"]]
        young = [(it, _date(it["row"].get("registered_on"))) for it in pool]
        young = [(it, reg) for it, reg in young if reg and (as_of - reg).days < YOUNG_DAYS]
        if young:
            return flag("young-entity", V, "fired", "info", f"{len(young)} going organisation(s) the person has a confirmed row on were registered "
                        f"under 24 months before {as_of.isoformat()}: " + "; ".join(f"{_name(it)} (registered {reg.isoformat()})" for it, reg in young[:EXAMPLES]),
                        citations=tuple(it["ref"] for it, _ in young), scope="officer-group")
        return flag("young-entity", V, "clear", "info", "no going company the person has a confirmed row on was registered under 24 months ago",
                    sources_held=("Companies register registration dates (pub.companies)",), scope="officer-group")
    reg = _date(report["subject"]["row"].get("registered_on"))
    if not reg:
        return flag("young-entity", V, "blocked", "amber", "the register states no registration date for the entity", scope="entity")
    if (as_of - reg).days < YOUNG_DAYS:
        return flag("young-entity", V, "fired", "amber", f"the entity was registered {reg.isoformat()}, under 24 months before {as_of.isoformat()}: "
                    "a short record is a short record, not a finding", citations=(report["subject"]["ref"],), scope="entity")
    return flag("young-entity", V, "clear", "amber", f"registered {reg.isoformat()}, 24 months ago or more",
                sources_held=("registration dates (pub.companies, pub.societies)",), scope="entity")


def insolvency_notice(report):
    """Gazette insolvency notices on the entity, each dated from its notice."""
    if _other_start(report):
        return flag("insolvency-notice", V, "blocked", "red", _other_start(report), scope="entity")
    if not _organisation_start(report):
        return flag("insolvency-notice", V, "clear", "info", "the start is a person: the Gazette on each of the person's companies is read by "
                    "officer-company-notices, and on the person by officer-bankruptcy", sources_held=(GAZETTE_HELD,), scope="entity")
    if report["subject"]["view"] == "societies":
        return flag("insolvency-notice", V, "blocked", "red", "a society's Gazette notices are filed under its row in the companies register, "
                    "which the societies register's row does not join: start the report from the society's companies register row",
                    sources_not_held=(INSOLVENCY_REGISTER,), scope="entity")
    own = [it for it in _notices(report, ("confirmed",)) if _on_subject(report, it) and not it.get("above")]
    up = [it for it in _above(report, ("gazette_liquidations", "gazette_company_notices")) if _insolvency(it)]
    beside = (f"; beside it, {len(up)} on a company above in the holding chain, the holder's and not the entity's: "
              + "; ".join(f"{_kind(it)} on {_entity_name(it)}, {it['dates']['text']} ({it.get('depth', '?')} up, {it['grade']})" for it in up[:EXAMPLES])
              ) if up else ""
    if own:
        own.sort(key=lambda it: (_notice_date(it) is None, _notice_date(it) or dt.date.min))
        return flag("insolvency-notice", V, "fired", "red", f"{len(own)} Gazette insolvency notice(s) on the entity, earliest first: "
                    + "; ".join(f"{_kind(it)}, {it['dates']['text']}" for it in own[:EXAMPLES])
                    + (f"; and {len(own) - EXAMPLES} more" if len(own) > EXAMPLES else "") + beside,
                    citations=tuple(it["ref"] for it in own + up), sources_not_held=(INSOLVENCY_REGISTER, COURTS), scope="entity")
    if set(section(report, "gazette").get("omitted_views") or ()) & {"gazette_liquidations", "gazette_company_notices"}:
        return flag("insolvency-notice", V, "blocked", "red", "the entity has more Gazette notices than the walk lists; an insolvency could be "
                    "among those left out", scope="entity")
    if _ending(report["subject"]) == "insolvent":
        return flag("insolvency-notice", V, "fired", "red", f"the companies file gives the entity the status {_status(report['subject'])!r} and "
                    "no Gazette insolvency notice on it is held: the status is undated here", citations=(report["subject"]["ref"],),
                    sources_not_held=(INSOLVENCY_REGISTER,), scope="entity")
    return flag("insolvency-notice", V, "clear", "red", "no Gazette liquidation, winding-up application, receivership, administration, "
                "creditors' notice or deed of company arrangement on the entity" + beside, citations=tuple(it["ref"] for it in up),
                sources_held=(GAZETTE_HELD + ", joined to the company by its number",), sources_not_held=(INSOLVENCY_REGISTER, COURTS),
                scope="entity")


def officer_company_notices(report):
    """Gazette insolvency notices on the other companies the entity's officers sit on (or the person's own companies), each set beside
    the officer's own role on that company, dated; amber at most: the company is the officer's, not the entity's."""
    if _other_start(report):
        return flag("officer-company-notices", V, "blocked", "amber", _other_start(report), scope="officer-group")
    if _organisation_start(report):
        roles = {}
        for it in _through(report, ROLE_VIEWS):
            roles.setdefault(_company_of(it), []).append(it)
        hits = [n for n in _notices(report) if n.get("through") and not n.get("near_link") and not n.get("above")]
        apart = [n for n in _notices(report) if n.get("through") and n.get("near_link") and not n.get("above")]
        also = _apart(apart, "notice(s) on companies")
        if hits:
            hits.sort(key=lambda n: (_notice_date(n) is None, _notice_date(n) or dt.date.min), reverse=True)
            bits = []
            for n in hits[:EXAMPLES]:
                mine = roles.get(n.get("via") or _company_of(n), [])
                r = mine[0] if mine else None
                side = (f"{_who(r)}: {_role(r)}, {'from ' + _start_of(r).isoformat() if _start_of(r) else 'no start filed'}" if r
                        else "the officer's role on it is past the walk's limit")
                bits.append(f"{_kind(n)} on {_entity_name(n)}, {n['dates']['text']} | {side}")
            short = _officers_short(report)
            return flag("officer-company-notices", V, "fired", "amber",
                        f"{len(hits)} Gazette insolvency notice(s) on {len({n.get('via') for n in hits})} other company(ies) the entity's officers "
                        f"sit on, newest first: " + " ; ".join(bits) + (f"; and {len(hits) - EXAMPLES} more" if len(hits) > EXAMPLES else "")
                        + (f"; {short}" if short else "") + "; each company is the officer's, not the entity's" + also,
                        citations=tuple(dict.fromkeys([n["ref"] for n in hits] + [r["ref"] for n in hits for r in roles.get(n.get("via"), [])[:1]]
                                                      + [n["ref"] for n in apart])),
                        sources_not_held=(INSOLVENCY_REGISTER,), scope="officer-group")
        gap = _officer_gap(report)
        if gap:
            return flag("officer-company-notices", V, "blocked", "amber", gap + also, sources_not_held=(INSOLVENCY_REGISTER,),
                        scope="officer-group")
        if apart:   # only a namesake's companies carry a notice: listed, never the officer's, and no clear while they stand
            return flag("officer-company-notices", V, "fired", "info", "no Gazette insolvency notice on the other current companies of the "
                        f"{_walk(report).get('officers_followed', 0)} officer(s) followed" + also, citations=tuple(n["ref"] for n in apart),
                        sources_not_held=(INSOLVENCY_REGISTER,), scope="near")
        return _clear_or_past("officer-company-notices", "amber", f"no Gazette insolvency notice on the other current companies of the "
                              f"{_walk(report).get('officers_followed', 0)} officer(s) followed", sources_held=(GAZETTE_HELD,),
                              sources_not_held=(INSOLVENCY_REGISTER,), scope="officer-group")
    mine = {_company_of(it): it for it in _person_roles(report)}
    hits = [n for n in _notices(report, ("confirmed",)) if (n.get("via") or _company_of(n)) in mine]
    if hits:
        hits.sort(key=lambda n: (_notice_date(n) is None, _notice_date(n) or dt.date.min), reverse=True)
        bits = []
        for n in hits[:EXAMPLES]:
            r = mine[n.get("via") or _company_of(n)]
            bits.append(f"{_kind(n)} on {_entity_name(n)}, {n['dates']['text']} | the person's row: {_role(r)}, "
                        f"{'from ' + _start_of(r).isoformat() if _start_of(r) else 'no start filed'}")
        return flag("officer-company-notices", V, "fired", "amber", f"{len(hits)} Gazette insolvency notice(s) on company(ies) the person has a "
                    "current confirmed role on, newest first: " + " ; ".join(bits), sources_not_held=(INSOLVENCY_REGISTER,),
                    citations=tuple(dict.fromkeys([n["ref"] for n in hits] + [mine[n.get("via") or _company_of(n)]["ref"] for n in hits])),
                    scope="officer-group")
    if _walk_short(report):
        return flag("officer-company-notices", V, "blocked", "amber", "the walk stopped before reading every company the person has a row on",
                    scope="officer-group")
    return _clear_or_past("officer-company-notices", "amber", f"no Gazette insolvency notice on the {len(mine)} company(ies) the person has a "
                          "current confirmed role on", sources_held=(GAZETTE_HELD,), sources_not_held=(INSOLVENCY_REGISTER,), scope="officer-group")


def _clear_or_past(rule, severity, text, **kw):
    """A clear, or, while past roles are not held, a blocked flag saying what was seen and what cannot be."""
    if HISTORY:
        return flag(rule, V, "clear", severity, text, **kw)
    kw.pop("sources_held", None)
    return flag(rule, V, "blocked", severity, f"{text}; but {PAST_NOT_HELD}: no clear is given", **kw)


# ── the people ──────────────────────────────────────────────────────────────

def _in_force(report, it) -> bool:
    end = _date(it["row"].get("ends_on"))
    return bool(it["row"].get("permanent")) or end is None or end >= _as_of(report)


def _people_notice(report, rule, view, noun, extra_not_held=()):
    """A Gazette notice on the person, or on an officer of the entity: confirmed to the person red; on an officer's own record (a
    confirmed link from the officer's row, the group not contested, the notice in force, the officer current on the entity) red;
    otherwise amber; a namesake's amber and said so. Blocked where an officer was not followed or a link was left unread."""
    live = [it for it in items(report, (view,)) if not it.get("suppressed")]
    officer_rows = _officer_rows(report)
    charity_marks = [it for it in items(report, ("charity_officers",)) if it["row"].get("disqualified") and not it.get("suppressed")] \
        if view == "gazette_prohibitions" else []
    not_held = tuple(extra_not_held) + (() if _reads(report, "charity_officers") or view != "gazette_prohibitions" else (CHARITIES,))
    if _person_start(report):
        conf = [it for it in live if it["grade"] == "confirmed"] + [it for it in charity_marks if it["grade"] == "confirmed"]
        nearby = [it for it in live if it["grade"] == "near"] + [it for it in charity_marks if it["grade"] == "near"]
        if conf:
            return flag(rule, V, "fired", "red", f"{len(conf)} {noun}(s) confirmed to the person: "
                        + "; ".join(f"{_name(it)} ({it['dates']['text']})" for it in conf[:EXAMPLES]),
                        citations=tuple(it["ref"] for it in conf), sources_not_held=not_held)
        if nearby:
            return flag(rule, V, "fired", "amber", f"{len(nearby)} {noun}(s) under a name near the person's; a namesake's until confirmed: "
                        + "; ".join(f"{_name(it)} ({it['dates']['text']}; near: {it.get('reason')})" for it in nearby[:EXAMPLES]),
                        citations=tuple(it["ref"] for it in nearby), sources_not_held=not_held, scope="near")
        w = _walk(report)
        if not w.get("links_built"):
            return flag(rule, V, "blocked", "red", f"no links are published, so a {noun} under the person's name cannot be reached",
                        sources_not_held=not_held)
        if w.get("links_omitted"):
            return flag(rule, V, "blocked", "red", f"the walk left {w['links_omitted']:,} link(s) unread past its limit; a {noun} could be "
                        "among them, so no clear is given", sources_not_held=not_held)
        held = (f"New Zealand Gazette (pub.{view}), joined by name in pub.links",)
        if view == "gazette_prohibitions" and _reads(report, "charity_officers"):
            s = report["subject"]
            if s["view"] in NAME_LOOKED_UP and not s.get("suppressed"):
                held += ("Charities Register officers (pub.charity_officers), looked up by the person's name",)
            else:
                return flag(rule, V, "blocked", "red", f"no {noun} in the Gazette confirmed or near the person, but a charity officer row is looked "
                            f"for under the name a {', '.join(NAME_LOOKED_UP)} row carries, and the report starts from pub.{s['view']}, so no "
                            "clear is given", sources_not_held=not_held)
        return flag(rule, V, "clear", "red", f"no {noun} confirmed or near the person: the link rules join every such notice by name, and every "
                    "link from the person's rows was read", sources_held=held, sources_not_held=not_held)
    if _other_start(report):
        return flag(rule, V, "blocked", "red", _other_start(report), sources_not_held=not_held)
    own_marks = [it for it in charity_marks if it in _own_charity_officers(report)]
    if own_marks:   # an officer the register marks disqualified on the entity's own charity: the entity's own record, confirmed
        current = [it for it in own_marks if not _date(it["row"].get("ended_on"))]
        return flag(rule, V, "fired", "red" if current else "amber", f"{len(own_marks)} officer row(s) on the entity's own charity carry the "
                    f"register's disqualified mark, {len(current)} with no end filed: "
                    + "; ".join(f"{_name(it)} ({it['dates']['text']}; {it['row'].get('status') or 'status not filed'})"
                                         for it in own_marks[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in own_marks), sources_not_held=not_held, scope="entity")
    on_officers = [it for it in live + charity_marks if it.get("through")]
    if on_officers:
        red = [it for it in on_officers if it.get("rule") != "same-name" and not it.get("near_link") and not _contested(it) and _in_force(report, it) and it["through"] in officer_rows
               and _current(officer_rows[it["through"]]) and it["through"] not in _hub_refs(report)]
        bits = []
        for it in sorted(on_officers, key=lambda x: x in red, reverse=True)[:EXAMPLES]:
            o = officer_rows.get(it["through"])
            mine = f"{_who(o)}: {_role(o)} of the entity, {'from ' + _start_of(o).isoformat() if _start_of(o) else 'no start filed'}" if o else "an officer"
            bits.append(f"{mine} | {_name(it)}, {it['dates']['text']}{'' if _in_force(report, it) else ', ended'}")
        return flag(rule, V, "fired", "red" if red else "amber", f"{len(on_officers)} {noun}(s) on the record of an officer of the entity, "
                    f"{len(red)} in force on a current officer whose group is not contested: " + " ; ".join(bits),
                    citations=tuple(dict.fromkeys([it["ref"] for it in on_officers] + [it["through"] for it in on_officers])),
                    sources_not_held=not_held, scope="officer-group")
    gap = _officer_gap(report)
    if gap:
        return flag(rule, V, "blocked", "red", f"a {noun} on an officer's record may stand unread: {gap}",
                    sources_not_held=not_held, scope="officer-group")
    return flag(rule, V, "clear", "red", f"no {noun} on the records of the entity's {_walk(report).get('officers_followed', 0)} officer(s), each "
                "followed one step through the rows a confirmed link joins to the officer's row",
                sources_held=(f"New Zealand Gazette (pub.{view}), joined by name in pub.links", "pub.groups: each officer's confirmed rows"),
                sources_not_held=not_held, scope="officer-group")


def disqualified_officer(report):
    return _people_notice(report, "disqualified-officer", "gazette_prohibitions", "director prohibition or charity disqualification")


def officer_bankruptcy(report):
    return _people_notice(report, "officer-bankruptcy", "gazette_bankruptcies", "Gazette bankruptcy notice",
                          extra_not_held=(INSOLVENCY_REGISTER + ": a discharge, a no-asset procedure or a summary instalment order",))


def officer_overlap(report):
    """MC-H3. The officers' other current roles, dated: from an organisation, each officer of the entity with the companies and societies
    the officer also sits on, the officer's role on the entity dated beside the other role; companies whose name reads as care or
    retirement living counted apart (a sign, not a finding); a hub's overlap shown and never amber. From a person, the person's own
    current roles across organisations."""
    if _other_start(report):
        return flag("officer-overlap", V, "blocked", "amber", _other_start(report), scope="officer-group")
    hubs = _hub_refs(report)
    if _organisation_start(report):
        officers = _officer_rows(report)
        overlap = _overlap(report)
        short = _officers_short(report)
        namesake = [r for v in _namesake_roles(report).values() for r in v]
        also = _apart(namesake, "role(s) on organisations")
        if not overlap:
            gap = _officer_gap(report)
            if gap:
                return flag("officer-overlap", V, "blocked", "amber", gap + also, scope="officer-group")
            if namesake:
                return flag("officer-overlap", V, "fired", "info", f"none of the entity's {len(officers)} officer(s) listed holds another current "
                            "role through the rows a confirmed link joins to the officer" + also, citations=tuple(r["ref"] for r in namesake),
                            scope="near")
            return flag("officer-overlap", V, "clear", "info", f"none of the entity's {len(officers)} officer(s) listed holds another current role "
                        "in the registers read", sources_held=(COMPANIES_HELD, SOCIETIES_HELD, "pub.groups: each officer's confirmed rows"),
                        scope="officer-group")
        care_officers, lines = [], []
        word = _lead_word(report["subject"].get("title"))
        for oref, roles in sorted(overlap.items(), key=lambda kv: -len(kv[1])):
            o = officers.get(oref)
            care = [r for r in roles if _care(r.get("entity_title"))]
            own_name = [r for r in care if word and _lead_word(r.get("entity_title")) == word]
            hub = hubs.get(oref)
            if len(care) > len(own_name) and not hub:
                care_officers.append(oref)
            mine = f"{_who(o)} ({_role(o)} of the entity, {'from ' + _start_of(o).isoformat() if _start_of(o) else 'no start filed'})" if o else oref
            shown = sorted(roles, key=lambda r: (r in own_name, not _care(r.get("entity_title")), str(_start_of(r) or "")))[:EXAMPLES]
            lines.append(f"{mine}: {len(roles)} other current role(s), {len(care)} on a care-named organisation"
                         + (f" ({len(own_name)} carrying the entity's own leading name word)" if own_name else "")
                         + (f", a hub ({hub['kind']})" if hub else "") + ": "
                         + "; ".join(f"{_role(r)} of {_entity_name(r)} ({'from ' + _start_of(r).isoformat() if _start_of(r) else 'undated'})" for r in shown))
        n_roles = sum(len(v) for v in overlap.values())
        text = (f"{len(overlap)} of the entity's officer(s) hold {n_roles} other current role(s); {len(care_officers)} officer(s), not hubs, sit on "
                f"another organisation whose registered name reads as care or retirement living and does not carry the entity's own leading name "
                f"word (the registers carry no industry: the name is a sign to read, not a finding): " + " || ".join(lines[:EXAMPLES]) + (f" || and {len(lines) - EXAMPLES} more officer(s)" if len(lines) > EXAMPLES else "")
                + (f"; {short}" if short else "") + also + "; two roles held at once are two dated facts, and nothing more is said of them")
        cites = tuple(dict.fromkeys([oref for oref in overlap] + [r["ref"] for v in overlap.values() for r in v] + [r["ref"] for r in namesake]))
        return flag("officer-overlap", V, "fired", "amber" if care_officers else "info", text, citations=cites, scope="officer-group")
    roles = _person_roles(report)
    orgs = {}
    for r in roles:
        orgs.setdefault(_company_of(r) or r.get("via") or r["ref"], r)
    # a contested group: its other rows are near, and the person's roles on them are the group's, not confirmed the person's
    contested = {}
    for r in _group_roles(report):
        key = _company_of(r) or r["ref"]
        if key not in orgs:
            contested.setdefault(key, r)
    if len(orgs) + len(contested) >= 2:
        care = [r for r in orgs.values() if _care(r.get("entity_title"))]
        hub = _subject_hub(report)
        shown = sorted(orgs.values(), key=lambda r: (not _care(r.get("entity_title")), str(_start_of(r) or "")))[:EXAMPLES * 2]
        also = (f"; and {len(contested)} more organisation(s) through the rows of a contested group, near, {sum(1 for r in contested.values() if _care(r.get('entity_title')))} "
                "care-named: the person's only if the group holds") if contested else ""
        return flag("officer-overlap", V, "fired", "amber" if len(care) >= 2 and not hub else "info",
                    f"the person holds current confirmed roles on {len(orgs)} organisation(s), {len(care)} whose registered name reads as care or "
                    f"retirement living (a sign, not a finding){also}" + (f"; the person is a hub ({hub[0]['kind']})" if hub else "") + ": "
                    + "; ".join(f"{_role(r)} of {_entity_name(r)} ({'from ' + _start_of(r).isoformat() if _start_of(r) else 'undated'})" for r in shown)
                    + "; two roles held at once are two dated facts, and nothing more is said of them",
                    citations=tuple(r["ref"] for r in list(orgs.values()) + list(contested.values())), scope="officer-group")
    if _walk_short(report) or _walk(report).get("links_omitted"):
        return flag("officer-overlap", V, "blocked", "amber", "the walk stopped before reading every row of the person's", scope="officer-group")
    return flag("officer-overlap", V, "clear", "info", f"the person holds current confirmed roles on {len(orgs)} organisation(s): no overlap",
                sources_held=(COMPANIES_HELD, SOCIETIES_HELD, "pub.groups"), scope="officer-group")


# ── the charity arm ─────────────────────────────────────────────────────────

def _charities_unread(report):
    """Why the charity checks cannot run, or None when the template reads the three charity views."""
    missing = [v for v in CHARITY_VIEWS if not _reads(report, v)]
    if missing:
        return ("the template does not read pub." + ", pub.".join(missing) + "; whether the entity or its people sit on a charity, and what it "
                "files, is not shown")
    return None


def _charities(report) -> list:
    return list(items(report, ("charities",)))


def _returns_of(report, charity) -> list:
    key = _subject_key({"subject": charity})
    rs = [it for it in items(report, ("charity_returns",)) if it["row"].get("charity_key") == key or it.get("via") == charity["ref"]]
    return sorted(rs, key=lambda it: str(it["row"].get("period_end") or ""), reverse=True)


def _money(x) -> str:
    try:
        return f"${float(x):,.0f}"
    except (TypeError, ValueError):
        return "not filed"


def charity_arm(report):
    """The charities the entity or its people are officers of, as the links reach them, each with its status. Never clear: a charity arm
    the links do not join cannot be seen."""
    why = _charities_unread(report)
    if why:
        return flag("charity-arm", V, "blocked", "info", why, sources_not_held=(CHARITIES,))
    chars = _charities(report)
    by_name = [it for it in items(report, ("charity_officers",)) if it.get("rule") == "same-name" and not it.get("suppressed")]
    if not chars and by_name:
        return flag("charity-arm", V, "fired", "info", f"{len(by_name)} charity officer row(s) carry the person's name, near: no link joins the "
                    "Charities Register's officers to any other row yet, so each is a namesake's until a rule confirms it: "
                    + "; ".join(f"{_name(it)}, {it['row'].get('role') or 'officer'} of {_charity_title(it)} ({it['dates']['text']})"
                                for it in by_name[:EXAMPLES]), citations=tuple(it["ref"] for it in by_name), scope="near")
    if not chars:
        return flag("charity-arm", V, "blocked", "info", "no charity is reached from the entity or its people: a charity whose officers or "
                    "number the links do not join to the entity cannot be seen here, so no clear is given")
    ended = [c for c in chars if _ending(c) == "ended"]
    return flag("charity-arm", V, "fired", "amber" if ended else "info",
                f"{len(chars)} registered charity(ies) reached, {len(ended)} no longer registered: "
                + "; ".join(f"{_name(c)} ({_status(c) or 'status not filed'}{', ' + c['grade'] if c['grade'] == 'near' else ''})" for c in chars[:EXAMPLES]),
                citations=tuple(c["ref"] for c in chars))


def charity_audit_opinion(report):
    """A modified audit opinion on a charity's return: red on the newest return of a confirmed charity, amber otherwise."""
    why = _charities_unread(report)
    if why:
        return flag("charity-audit-opinion", V, "blocked", "red", why, sources_not_held=(CHARITIES,))
    rets = [it for it in items(report, ("charity_returns",))]
    if not rets:
        return flag("charity-audit-opinion", V, "blocked", "red", "no charity return is reached, so no audit opinion can be read")
    newest = {}
    for c in _charities(report):
        rs = _returns_of(report, c)
        if rs:
            newest[rs[0]["ref"]] = c
    modified = sorted([it for it in rets if it["row"].get("modified_opinion")], key=lambda it: str(it["row"].get("period_end") or ""), reverse=True)
    if modified:
        red = [it for it in modified if it["ref"] in newest and it["grade"] == "confirmed"]
        return flag("charity-audit-opinion", V, "fired", "red" if red else "amber",
                    f"{len(modified)} charity return(s) carry a modified audit opinion, {len(red)} the newest return of a confirmed charity: "
                    + "; ".join(f"period to {_iso(_date(it['row'].get('period_end')))}, {it['row'].get('tier') or 'tier not filed'}, opinion "
                                f"{it['row'].get('opinion') or 'not stated'}" for it in modified[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in modified))
    unaudited = [it for it in rets if it["ref"] in newest and it["row"].get("audited") is False]
    return flag("charity-audit-opinion", V, "clear", "red", f"no modified audit opinion on the {len(rets)} return(s) read"
                + (f"; {len(unaudited)} newest return(s) were not audited, which a smaller tier allows" if unaudited else ""),
                sources_held=("Charities Register annual returns (pub.charity_returns)",))


def _last_period_end(charity, as_of: dt.date):
    """The last balance date whose return is due on or before the report's day, from the register's year end."""
    m, d = charity["row"].get("year_end_month"), charity["row"].get("year_end_day")
    if not m:
        return None
    for year in range(as_of.year, as_of.year - 3, -1):
        try:
            end = dt.date(year, int(m), int(d or 28))
        except ValueError:
            end = dt.date(year, int(m), 28)
        if (as_of - end).days > FILE_WITHIN_DAYS:
            return end
    return None


def charity_return_filed(report):
    """No return filed for a charity's last period: the register's balance date gives the last period whose return is due; the newest
    return held is set beside it."""
    why = _charities_unread(report)
    if why:
        return flag("charity-return-filed", V, "blocked", "amber", why, sources_not_held=(CHARITIES,))
    chars = [c for c in _charities(report) if _ending(c) == "going"]
    if not chars:
        return flag("charity-return-filed", V, "blocked", "amber", "no registered charity is reached, so no filing can be checked")
    as_of, late, unknown = _as_of(report), [], []
    for c in chars:
        due = _last_period_end(c, as_of)
        if due is None:
            unknown.append(c)
            continue
        rs = _returns_of(report, c)
        newest = _date(rs[0]["row"].get("period_end")) if rs else None
        if newest is None or (due - newest).days > PERIOD_SLACK_DAYS:
            late.append((c, due, rs[0] if rs else None))
    if late:
        return flag("charity-return-filed", V, "fired", "amber" if all(c["grade"] == "near" for c, _, _ in late) else "red",
                    f"{len(late)} charity(ies) have no return held for the period to their last balance date, due within six months of it: "
                    + "; ".join(f"{_name(c)}: period to {due.isoformat()} | newest return held: "
                                + (f"period to {_iso(_date(r['row'].get('period_end')))}, {r['row'].get('tier') or 'tier not filed'}" if r else "none")
                                for c, due, r in late[:EXAMPLES]),
                    citations=tuple(dict.fromkeys([c["ref"] for c, _, _ in late] + [r["ref"] for _, _, r in late if r])))
    if unknown:
        return flag("charity-return-filed", V, "blocked", "amber", f"{len(unknown)} charity(ies) carry no balance date on the register, so the "
                    "period due cannot be set", citations=tuple(c["ref"] for c in unknown))
    return flag("charity-return-filed", V, "clear", "amber", f"each of the {len(chars)} registered charity(ies) reached has a return held for "
                "the period to its last balance date", sources_held=("Charities Register (pub.charities, pub.charity_returns)",))


def charity_returns_summary(report):
    """The charity's returns, newest first, each with its period, tier, income, expenditure, surplus, assets, liabilities and equity as
    filed, its audit and its opinion: the section is the table, this the line a reader sees first."""
    why = _charities_unread(report)
    if why:
        return flag("charity-returns", V, "blocked", "info", why, sources_not_held=(CHARITIES,))
    lines, cites = [], []
    for c in _charities(report):
        rs = _returns_of(report, c)
        if not rs:
            continue
        r = rs[0]["row"]
        cites.append(rs[0]["ref"])
        lines.append(f"{_name(c)}: period to {_iso(_date(r.get('period_end')))}, {r.get('tier') or 'tier not filed'}; income "
                     f"{_money(r.get('total_gross_income'))}, expenditure {_money(r.get('total_expenditure'))}, surplus {_money(r.get('net_surplus'))}, "
                     f"assets {_money(r.get('total_assets'))}, liabilities {_money(r.get('total_liabilities'))}, equity {_money(r.get('total_equity'))}; "
                     f"{'audited' if r.get('audited') else 'not audited' if r.get('audited') is False else 'audit not stated'}"
                     f"{', modified opinion' if r.get('modified_opinion') else ''}")
    if not lines:
        return flag("charity-returns", V, "blocked", "info", "no charity return is reached")
    return flag("charity-returns", V, "fired", "info", f"the newest return of {len(lines)} charity(ies), as filed: " + " || ".join(lines[:EXAMPLES]),
                citations=tuple(cites))


# ── the report's own reach ──────────────────────────────────────────────────

def namesake_exposure(report):
    names = list(section(report, "identity")["items"])
    nearby_elsewhere = [it for s in report["sections"] if s["name"] not in ("identity", "overlap") for it in s["items"]
                        if it["grade"] == "near" and not it.get("through")]
    w = _walk(report)
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
    w = _walk(report)
    ne, om = w.get("entities_not_expanded") or 0, w.get("entities_omitted") or 0
    bits = []
    if ne:
        bits.append(f"{ne:,} organisation(s) listed with their status, their Gazette notices, offices and officers not read")
    if om:
        bits.append(f"{om:,} past the walk's limit, not listed")
    if _organisation_start(report) and (_no_officers(report) or _officers_short(report)):
        bits.append(_no_officers(report) or _officers_short(report))
    if bits:
        return flag("walk-coverage", V, "fired", "amber", "the walk did not read the whole web: " + "; ".join(bits)
                    + "; start a report from each organisation or officer left out", citations=(report["subject"]["ref"],))
    return flag("walk-coverage", V, "clear", "info", "every organisation the walk reached was read for its notices, office and officers"
                + (", and every officer was followed one step" if _organisation_start(report) else ""),
                sources_held=("pub.companies", "pub.gazette_liquidations", "pub.gazette_company_notices", "pub.company_addresses", "pub.directors"))


def subject_hub(report):
    if _other_start(report):
        return flag("subject-hub", V, "blocked", "info", _other_start(report))
    mine = _subject_hub(report)
    if mine:
        kinds = sorted({h["kind"] for h in mine})
        return flag("subject-hub", V, "fired", "amber", f"the start is itself a hub ({', '.join(kinds)}): {mine[0]['text']}; an overlap among its "
                    "many roles is shown and means little on its own", citations=tuple(sorted({h["ref"] for h in mine})))
    return flag("subject-hub", V, "clear", "info", "the start is not a professional director, a nominee or the Crown on the rows held",
                sources_held=("pub.directors", "pub.groups"))


def past_roles(report):
    if HISTORY:
        return flag("past-roles", V, "clear", "info", "past roles and holdings are published with their filed end dates", sources_held=(COMPANIES_HELD,))
    left = [it for it in all_items(report).values() if it["view"] in ROLE_VIEWS and it["grade"] == "confirmed" and not it["row"].get("in_latest", True)]
    seen = f"; {len(left)} of the rows listed left the file since July 2026 and carry no end date" if left else ""
    who = "the entity's past officers and holders" if _organisation_start(report) else "the person's past roles and holdings"
    return flag("past-roles", V, "blocked", "amber", f"{who} are not held: {PAST_NOT_HELD}{seen}; an overlap that ended, or a board that "
                "turned over, cannot be seen here", sources_not_held=("past directorships and shareholdings with their end dates",))


# ── what is not held ────────────────────────────────────────────────────────

def retirement_villages(report):
    """The villages the operator runs and their statutory supervisors: not held. A village's own row reached by a name it shares is
    counted, near, and never said to be the operator's."""
    villages = [it for it in items(report, ("companies",)) if "/retirement_village/" in it["ref"] and it["ref"] != report["subject"]["ref"]]
    seen = (f"; {len(villages)} village row(s) of the companies register share a name with a row here and are listed near, not the "
            "operator's until the file says so") if villages else ""
    if _village(report):
        seen = "; the start is a village's own register row, which names no operator and no supervisor" + seen
    return flag("retirement-villages", V, "blocked", "red", "which villages the operator runs, each village's statutory supervisor, and when "
                f"the supervisor changed, are in the retirement villages file, which is not held{seen}; this check cannot run",
                citations=tuple(it["ref"] for it in villages), sources_not_held=(VILLAGES,))


def hdc_decisions(report):
    return flag("hdc-decisions", V, "blocked", "red", "the Health and Disability Commissioner's decisions (a provider found in breach of the "
                "Code of Rights, the recommendations made) are not held; no breach finding in this report is a finding of none; this check "
                "cannot run", sources_not_held=(HDC,))


def certification_audits(report):
    return flag("certification-audits", V, "blocked", "red", "a rest home's or hospital's certification, its period and its audit findings "
                "(the corrective actions raised) are not held; this check cannot run", sources_not_held=(CERTIFICATION,))


def provider_registers(report):
    return flag("provider-registers", V, "blocked", "amber", "which premises the operator is certified to run, and for which services, is in the "
                "Ministry of Health's provider registers, which are not held; the operator's web of homes cannot be read from them; this check "
                "cannot run", sources_not_held=(PROVIDERS,))


def aged_care_commissioner(report):
    return flag("aged-care-commissioner", V, "blocked", "amber", "the Aged Care Commissioner's reports and findings are not held; this check "
                "cannot run", sources_not_held=(AGED_CARE_COMMISSIONER,))


def court_judgments(report):
    return flag("court-judgments", V, "blocked", "amber", "court judgments are not held yet (plan step 5.4): a claim against the operator, a "
                "sentencing on a health and safety charge, a residents' dispute cannot be seen; this check cannot run", sources_not_held=(COURTS,))


RULES = (entity_status, young_entity, insolvency_notice, officer_company_notices, disqualified_officer, officer_bankruptcy, officer_overlap,
         charity_arm, charity_returns_summary, charity_audit_opinion, charity_return_filed, namesake_exposure, walk_coverage, subject_hub,
         past_roles, retirement_villages, hdc_decisions, certification_audits, provider_registers, aged_care_commissioner, court_judgments)
