"""The subcontractor vetting and phoenix detection rules (plan 5.2, use case
7). Pure functions over the built report, each returning one flag. A head
contractor's procurement lead asks "is this the failed firm again under a
new name". The rules stand for the old estate's construction checks (its
requirements, section 2.4: MC-C1 the phoenix signature, MC-C2 the officer
web, MC-C3 liquidation history) and its company rules (data-layer/flags/
flags/entity_rules.py, entity-0.1: group-receivership, practitioner-repeat,
partnership-dissolved; person_rules.py, person-0.2: liquidation-history,
prohibition, young-entity, namesake-exposure), taken as ideas and tests, not
code, where the held registers can support them:

  phoenix-signature      every company that failed, dated from its Gazette notice, beside each going company's start with the gap
                         in days, signed, nearest first, whatever the gap (ruling 65: the window is the reader's setting); raised only
                         on a shared person (from a person) or a shared registered office (from a company, with a company of the
                         same name), never on a name alone
  same-name-failed       a company that only shares a going company's name and failed: names only, near, never the signature
  shared-office          a failed and a going company at one registered office that is not a hub
  entity-status          the company's own register status
  insolvency-notices     Gazette liquidations (by the shareholders or the court), receiverships, administrations, winding-up
                         applications, creditors' notices and deeds of company arrangement, on the company or the person's companies
  repeat-failure         two or more of the person's companies failed (group-receivership, liquidation-history)
  register-events        removals, dissolutions, restorations, rectifications, amalgamations: not insolvency
  other-current-companies  the person's going companies and their states
  officers-of-record     started from a company: its current directors, or none in the latest file
  young-entity           registered under 24 months: the shape a new firm in a failed one's place takes
  prohibition, bankruptcy  on the person, confirmed or near; blocked from a company
  practitioner-roles     the person named as liquidator: an insolvency practitioner, not a director of the failed company
  practitioner-repeat    blocked: a liquidator row does not name its company
  society-roles          incorporated society roles, confirmed
  namesake-exposure      the report's own uncertainty
  walk-coverage          how many companies reached had their notices and officers read
  subject-hub            the person is a professional director, a nominee or the Crown
  past-roles, change-history  blocked: current roles only; the change history is not held before 16 August 2026
  building-practitioners, insolvency-register, court-judgments, employment-determinations, securities-register,
  mortgagee-possession   blocked: not held, or published and not reachable

The builder adds its common rules for every template (group-standing,
hubs-met, replaced-return); this file carries no copy of them.

Every rule branches on the start: a person, a company, or anything else.
From a company the walk lists the officers and holders and does not follow
them (the agriculture lesson), so a check through a person is blocked and
says to start a report from each person; it does read the companies that
share the company's name (the links lane's company-name rule, near), their
officers, offices and notices. Evidence on confirmed rows is red or amber;
the same evidence reached only through a near link is amber at most and
says it is a namesake's until confirmed. A check the walk could not have
seen is blocked, never clear. Dates sit side by side; no flag joins two
facts with a word of cause, none calls a holder an owner, and none prints an
address: the office section shows it.

Imports nothing of products.report: the one-way test holds a template folder
to its own code. The shape loads this file by path and binds the name
`contract` (products/report/contract.py) before it runs."""
from __future__ import annotations

import datetime as dt
import re

V = "0.2"
#: the phoenix window is the reader's setting, not the template's (ruling 65, 21 October 2026): every dated failure is set beside
#: every going company whatever the gap, nearest first, and a window cuts only when the reader passes one as the report's
#: `window_days` (days either side of the failure). The shape carries no such parameter yet (card
#: the-report-carries-no-template-parameters); until it does, no cut is applied.
WINDOW_KEY = "window_days"
#: the gaps a flag counts its pairs within, so a reader sees the old defaults without losing the rest: the old estate's MC-C1 used 90
#: days after, construction-1 365 either side. Measured 2026-10-21 on the confirmed groups: 476 going companies at 90 days, 1,191 at
#: 365, 1,858 at 730 (of 784,993 registered).
OLD_WINDOWS = (90, 365)
YOUNG_DAYS = 730          # under 24 months registered (the old young-entity rule)
NAMESAKE_NOTE_AT = 5      # namesakes set apart at which the report's caveat fires
NAMESAKE_PARTIAL_AT = 50  # past this many namesakes the report is declared partial
EXAMPLES = 3              # dated examples a fired flag states in its text
#: whether a published view holds past roles with their end dates. It does not (measured 2026-10-20 by banking-1): the companies file
#: lists current roles only. While False, a check over a person's companies fires on what it sees and never clears.
HISTORY = False
PAST_NOT_HELD = ("the companies file lists current roles only: a company the person left, or that was struck off with them on it, is not "
                 "seen, nor its failure")

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
OFFICE_HUBS = ("busy-address", "thousand-address")
#: the words a fired flag must not carry, the shape's own (rules 3 and 4): a register's name that holds one is not quoted in a flag
UNSAFE = re.compile(contract.CAUSE.pattern + "|" + contract.OWNER.pattern, re.I)   # noqa: F821  (bound by the loader)

GAZETTE_HELD = "New Zealand Gazette liquidation and company notices (pub.gazette_liquidations, pub.gazette_company_notices)"
NOTICES_HELD = "New Zealand Gazette company notices (pub.gazette_company_notices)"
COMPANIES_HELD = "Companies register (pub.companies, pub.directors, pub.shareholders)"
OFFICES_HELD = "Companies register addresses (pub.company_addresses)"
INSOLVENCY_REGISTER = "the Official Assignee's Insolvency Register (interface awaited since 19 September 2026)"
NOT_HELD_INSOLVENCY = (INSOLVENCY_REGISTER, "court judgments (step 5.4)")
CHANGE_HISTORY = "the companies change history: not held before 16 August 2026, held and unread since (former names, trading names, earlier directors)"
LIQUIDATOR_OFFICE = ("a failed company's registered office from before its failure, where the file no longer holds it: a liquidated "
                     "company's office is its liquidator's from the day of the appointment (4,735 of 4,945 measured 2026-10-21), and the "
                     "office it traded from is in the change history")
OFFICE_NEIGHBOURS = "the companies that share a registered office with the entity and neither its name nor a person (counted by the walk, not listed)"
BUILDING = ("the licensed building practitioners register (licence, class and discipline)",)
EMPLOYMENT = ("the Employment Relations Authority's determinations, and the Employment Court's judgments",)
COURTS = ("court judgments: the OpenLaw case-law lane and the courts register (step 5.4)",)
SECURITIES = "the Personal Property Securities Register (interface awaited since 19 September 2026)"
POSSESSIONS = ("a mortgagee's entry into possession (pub.gazette_possessions: published, not in the report's catalogue)",)
LIQUIDATOR_COMPANY = ("the company a Gazette liquidator row was appointed to (pub.gazette_liquidators names its notice, not its company)",)
LP_PARTNERS = "a limited partnership's general and limited partners (the limited partnerships register)"
CHARITIES_NOT_HELD = ("the Charities Register and its officers (not yet published)",)
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


def _removal(it) -> bool:
    r = it["row"]
    action = (r.get("action") or "").lower()
    return it["view"] == "gazette_company_notices" and r.get("kind") == "removal" and "restor" not in action and "revocation" not in action


def _event(it) -> bool:
    return it["view"] == "gazette_company_notices" and not _insolvency(it) and (it["row"].get("kind") or "") not in INSOLVENCY_KINDS


def _event_kind(it) -> str:
    r = it["row"]
    kind, action = r.get("kind") or "", (r.get("action") or "").lower()
    if "restor" in action or "revocation" in action:
        return "restoration"
    return EVENT_KIND.get(kind, kind or "notice")


def _failure_date(it):
    """The day a failure notice dates it from: a liquidator's or receiver's appointment where the Gazette states one, otherwise the
    day the notice was published (a winding-up application's own date is its hearing, a removal's the last day for objections, and
    neither is the day the company failed)."""
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


def _companies(report, grades=("confirmed",)):
    """The companies the walk reached, other than the one the report starts from."""
    return [it for it in items(report, ("companies",), grades) if it["ref"] != report["subject"]["ref"]]


def _same_name(it) -> bool:
    """A company reached by the links lane's company-name rule: it shares a name and nothing else."""
    return bool(SAME_NAME.match(it.get("rule") or ""))


def _role_on(report, company_ref: str) -> list:
    """The subject's own confirmed roles and holdings on a company."""
    return [it for it in all_items(report).values()
            if it["view"] in ("directors", "shareholders") and it["grade"] == "confirmed" and _company_of(it) == company_ref]


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


def _iso(d) -> str:
    return d.isoformat() if d else "undated"


def _subject_hub(report) -> list:
    own = {report["subject"]["ref"]} | {m["ref"] for m in report.get("members", [])}
    return [h for h in report.get("hubs", []) if h["ref"] in own and h["kind"] in HUB_KINDS]


# ── failures and the going companies beside them ────────────────────────────

def _failures(report, companies: list, grades=("confirmed",)) -> dict:
    """{company ref: {'company', 'date', 'kind', 'evidence', 'notice'}} for each company that failed: an insolvency (a notice, or
    the status alone, undated) or a removal. 'date' is the earliest failure date a notice gives; an insolvency outranks a removal."""
    by_ref = {it["ref"]: it for it in companies}
    out = {}
    for it in companies:
        if _ending(it) == "insolvent":
            out[it["ref"]] = {"company": it, "date": None, "kind": "insolvency", "evidence": [it["ref"]], "notice": None}
    for n in _notices(report, grades):
        c = n.get("via") or _company_of(n)
        if c not in by_ref:
            continue
        kind = "insolvency" if _insolvency(n) else "removal" if _removal(n) else None
        if not kind:
            continue
        e = out.setdefault(c, {"company": by_ref[c], "date": None, "kind": kind, "evidence": [c], "notice": None})
        if kind == "removal" and e["kind"] == "insolvency":
            continue
        if kind == "insolvency" and e["kind"] == "removal":
            e.update(kind="insolvency", date=None, notice=None)
        e["evidence"].append(n["ref"])
        d = _failure_date(n)
        if d and (e["date"] is None or d < e["date"]):
            e["date"], e["notice"] = d, n
    return out


def _how(f) -> str:
    """'liquidator appointed by the court, 13 July 2020' as the notice dates it; the status alone when no notice is reached."""
    n = f["notice"]
    if n is None:
        return f"status {_status(f['company'])!r}, no dated Gazette notice reached"
    by = n["row"].get("appointed_by")
    what = f"liquidation (liquidator appointed by the {by})" if n["view"] == "gazette_liquidations" and by else _kind(n)
    return f"{what}, {n['dates']['text']}"


def _window_days(report):
    """The reader's window in days, or None: no cut. A value that is not a whole number of days, zero or more, is no window, and
    _window says so."""
    w = report.get(WINDOW_KEY)
    if w is None or w == "" or isinstance(w, bool):
        return None
    try:
        w = int(str(w).strip())
    except ValueError:
        return None
    return w if w >= 0 else None


def _pairs(failed: dict, going: list, window=None) -> list:
    """(failure, going company, days from the failure to the going company's start, within the reader's window): every dated failure
    beside every going company with a start, nearest first, whatever the gap; with no window every pair is within."""
    out = []
    for f in failed.values():
        for g in going:
            if g["ref"] == f["company"]["ref"]:
                continue
            start = _date(g["row"].get("registered_on"))
            if f["date"] is None or start is None:
                continue
            days = (start - f["date"]).days
            out.append((f, g, days, window is None or abs(days) <= window))
    out.sort(key=lambda p: (abs(p[2]), p[1]["ref"], p[0]["company"]["ref"]))
    return out


def _side(p) -> str:
    """'FAILED LTD: liquidation, appointed 13 July 2020 | GOING LTD: registered 2020-09-01, 50 days after': two dates, no word between."""
    f, g, days = p[:3]
    when = f"{abs(days)} days {'after' if days >= 0 else 'before'}"
    return f"{_name(f['company'])}: {_how(f)} | {_name(g)}: registered {_iso(_date(g['row'].get('registered_on')))}, {when}"


def _window(report, pairs=()) -> str:
    """What the flag's pairs span: how many fall within 90 and 365 days, and the reader's window, if one is set, with what it
    leaves out."""
    gaps = [abs(p[2]) for p in pairs]
    counts = " and ".join(f"{sum(1 for g in gaps if g <= d)} within {d} days" for d in OLD_WINDOWS)
    text = f"of {len(gaps)} pair(s), nearest first, {counts}" if gaps else "no pair"
    w, raw = _window_days(report), report.get(WINDOW_KEY)
    if w is not None:
        out = sum(1 for p in pairs if not p[3])
        text += f"; the reader's window is {w} days either side of the failure's Gazette date" + (f", and {out} of them fall outside it and are not listed" if out else "")
    elif raw not in (None, ""):
        text += f"; the window asked for ({str(raw)[:20]!r}) is not a whole number of days, so no cut is applied"
    else:
        text += "; no window is set, so every gap is shown"
    return text


def _going(report, grades=("confirmed",)) -> list:
    return [it for it in _companies(report, grades) if _ending(it) == "going" and not _same_name(it)]


def _offices(report) -> dict:
    """{company ref: [(office key, address item, its start)]} for every registered-office row the walk listed, in the latest file
    or not; the key is the folded first line and postcode, never printed."""
    out = {}
    for it in items(report, ("company_addresses",)):
        r = it["row"]
        if "regist" not in (r.get("kind") or "registered office").lower():
            continue
        key = (_fold(r.get("line_1")), _fold(r.get("postcode")))
        if key[0]:
            out.setdefault(_company_of(it), []).append((key, it, _date(r.get("started_on"))))
    return out


def _office_hub(report, company_ref: str, office_item) -> bool:
    hubs = {h["ref"] for h in report.get("hubs", []) if h["kind"] in OFFICE_HUBS}
    return company_ref in hubs or office_item["ref"] in hubs or any(f.get("kind") in OFFICE_HUBS for f in office_item.get("flags", []))


def _office_pairs(report, failed: dict, going: list) -> list:
    """The pairs of _pairs whose two companies shared a registered office: the failed company's office from before its failure (the
    office a company takes at its liquidation is its liquidator's, so it is never compared) and the going company's office in the
    latest file, which is not a hub. Each pair carries the two address items."""
    offices = _offices(report)
    out = []
    for p in _pairs(failed, going, _window_days(report)):
        f, g, fdate = p[0]["company"]["ref"], p[1]["ref"], p[0]["date"]
        before = {k: it for k, it, st in offices.get(f, []) if st and st < fdate and not _office_hub(report, f, it)}
        now = [(k, it) for k, it, _ in offices.get(g, []) if it["row"].get("in_latest", True) and not _office_hub(report, g, it)]
        hit = next(((before[k], it) for k, it in now if k in before), None)
        if hit:
            out.append(p + hit)
    return out


# ── the phoenix signature ───────────────────────────────────────────────────

def phoenix_signature(report):
    """MC-C1. From a person: each of the person's companies that failed, dated from its Gazette notice, beside each of the person's
    going companies with its start, whatever the gap, nearest first, counted within 90 and 365 days and cut only by the reader's
    window; red on a confirmed insolvency, amber through a hub, a removal or a near link. From a company: a company of the same name
    that failed and shares the entity's registered office, beside the entity's start; the signature through a person is blocked,
    the people not being followed."""
    if _other_start(report):
        return flag("phoenix-signature", V, "blocked", "red", _other_start(report), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if _company_start(report):
        s = report["subject"]
        same = [it for it in _companies(report, ("near",)) if _same_name(it)]
        failed = _failures(report, same, ("confirmed", "near"))
        by_office = _office_pairs(report, failed, [s]) if _ending(s) == "going" else []
        inside = [p for p in by_office if p[3]]
        if inside:
            return flag("phoenix-signature", V, "fired", "red",
                        f"{len(inside)} company(ies) of the same name carry a failure notice in the Gazette and had, before the failure, the "
                        f"registered office the entity has now, not a hub; each failure beside the entity's start: "
                        + " ; ".join(_side(p) for p in inside[:EXAMPLES]) + (f"; and {len(inside) - EXAMPLES} more" if len(inside) > EXAMPLES else "")
                        + f"; {_window(report, by_office)}; the shared office and the dated failure are each "
                        f"filed by a register; whether one firm's people stand in both is not read from a company: start a report from each "
                        f"director listed", citations=tuple(dict.fromkeys(r for p in inside for r in p[0]["evidence"] + [p[4]["ref"], p[5]["ref"]])),
                        sources_not_held=NOT_HELD_INSOLVENCY + (CHANGE_HISTORY,), scope="office")
        cut = f" ({_window(report, by_office)})" if by_office else ""
        return flag("phoenix-signature", V, "blocked", "red",
                    f"{NOT_FOLLOWED}: the other companies its directors and holders sit on, and how those failed, are not read; of the companies "
                    f"that share its name, {len(failed)} failed and none listed had the entity's registered office before its failure{cut}"
                    + (" (see same-name-failed)" if failed else "") + f"; {OFFICE_NEIGHBOURS} are not read either",
                    sources_not_held=(OFFICE_NEIGHBOURS, LIQUIDATOR_OFFICE, CHANGE_HISTORY) + NOT_HELD_INSOLVENCY, scope="officer-group")
    conf = _companies(report)
    failed = _failures(report, conf)
    going = _going(report)
    pairs = _pairs(failed, going, _window_days(report))
    inside = [p for p in pairs if p[3]]
    hub = _subject_hub(report)
    if inside:
        insolvent = [p for p in inside if p[0]["kind"] == "insolvency"]
        pick = insolvent or inside
        basis = [p for p in pairs if (p[0]["kind"] == "insolvency") == bool(insolvent)]
        red = bool(insolvent) and not hub
        why = f"; the person is a hub ({hub[0]['kind']}): {hub[0]['text']}" if hub else ""
        what = "an insolvency" if insolvent else "a removal from the register (not an insolvency)"
        return flag("phoenix-signature", V, "fired", "red" if red else "amber",
                    f"{len({p[0]['company']['ref'] for p in pick})} of the person's companies carry {what} in the Gazette, each set beside "
                    f"the start of {len({p[1]['ref'] for p in pick})} going company(ies) the person sits on or holds, whatever the gap: "
                    + " ; ".join(_side(p) for p in pick[:EXAMPLES])
                    + (f"; and {len(pick) - EXAMPLES} more pair(s)" if len(pick) > EXAMPLES else "") + f"; {_window(report, basis)}; the person's "
                    f"confirmed rows on both are in the officers section{why}",
                    citations=tuple(dict.fromkeys([r for p in pick for r in p[0]["evidence"]] + [p[1]["ref"] for p in pick])),
                    sources_not_held=NOT_HELD_INSOLVENCY + (CHANGE_HISTORY,), scope="officer-group")
    near_c = _companies(report, ("near",))
    near_failed = _failures(report, [it for it in near_c if not _same_name(it)], ("confirmed", "near"))
    near_all = [p for p in _pairs({**near_failed, **failed}, going + [it for it in near_c if _ending(it) == "going" and not _same_name(it)],
                                  _window_days(report)) if p[0]["kind"] == "insolvency"]
    near_pairs = [p for p in near_all if p[3]]
    if near_pairs:
        return flag("phoenix-signature", V, "fired", "amber",
                    f"{len(near_pairs)} failure(s) beside a going company's start, one side of each reached only through a "
                    f"near link: a namesake's companies, not the person's until confirmed: " + " ; ".join(_side(p) for p in near_pairs[:EXAMPLES])
                    + f"; {_window(report, near_all)}", citations=tuple(dict.fromkeys([r for p in near_pairs for r in p[0]["evidence"]] + [p[1]["ref"] for p in near_pairs])),
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="near")
    if _walk_short(report):
        return flag("phoenix-signature", V, "blocked", "red", "the walk stopped before reading every company the person has a row on; a "
                    "failure among those left out cannot be set beside the going companies: start a report from each company left out",
                    scope="officer-group")
    undated = [f for f in failed.values() if f["date"] is None]
    seen = (f"of {len(conf)} company(ies) the person has a confirmed row on, {len(failed)} failed and {len(going)} are going; "
            + (f"no pair is listed ({_window(report, pairs)})" if pairs else "no dated failure has a going company to set beside it"))
    if undated:
        seen += f"; {len(undated)} failed by status with no dated Gazette notice reached, so no gap can be measured for them"
    return _clear_or_past("phoenix-signature", "red", seen, sources_held=(GAZETTE_HELD, COMPANIES_HELD),
                          sources_not_held=NOT_HELD_INSOLVENCY + (CHANGE_HISTORY,), scope="officer-group")


def same_name_failed(report):
    """A company that only shares the name of the entity, or of one of the person's going companies, and failed. Names only: a name
    is never the signature, so this is amber at most and says so; the officers' names beside each are compared as names."""
    if _other_start(report):
        return flag("same-name-failed", V, "blocked", "amber", _other_start(report), scope="near")
    same = [it for it in _companies(report, ("near", "confirmed")) if _same_name(it)]
    failed = _failures(report, same, ("confirmed", "near"))
    live = [report["subject"]] if _company_start(report) else _going(report)
    by_via = {}
    for f in failed.values():
        by_via.setdefault(f["company"].get("via") or "", []).append(f)
    pairs = []
    for g in live:
        mine = {f["company"]["ref"]: f for f in by_via.get(g["ref"], [])}
        pairs += _pairs(mine, [g], _window_days(report))
    pairs.sort(key=lambda p: (abs(p[2]), p[1]["ref"], p[0]["company"]["ref"]))
    inside = [p for p in pairs if p[3]]
    if inside:
        names = {}
        for it in items(report, ("directors", "shareholders")):
            if not it.get("suppressed"):
                names.setdefault(_company_of(it), set()).add(_fold(it["title"]))
        shared = [p for p in inside if names.get(p[0]["company"]["ref"], set()) & names.get(p[1]["ref"], set())]
        pick = shared or inside
        bits = []
        for p in pick[:EXAMPLES]:
            k = len(names.get(p[0]["company"]["ref"], set()) & names.get(p[1]["ref"], set()))
            bits.append(_side(p) + (f"; {k} officer name(s) on both, names only" if k else ""))
        return flag("same-name-failed", V, "fired", "amber" if shared else "info",
                    f"{len(failed)} company(ies) that only share a name with "
                    f"{'the entity' if _company_start(report) else 'a going company the person sits on'} failed; "
                    f"{len(shared)} with an officer of the same name on both: " + " ; ".join(bits)
                    + f"; {_window(report, pairs)}; a company name and a person's name are names, never one firm or one person: the phoenix flag is not "
                    f"raised on them", citations=tuple(dict.fromkeys([r for p in pick for r in p[0]["evidence"]] + [p[1]["ref"] for p in pick])),
                    scope="near")
    if failed:
        return flag("same-name-failed", V, "fired", "info", f"{len(failed)} company(ies) that only share a name failed, with no date or start to "
                    "set beside" + (f" listed ({_window(report, pairs)})" if pairs else "") + ": " + "; ".join(f"{_name(f['company'])} ({_how(f)})" for f in list(failed.values())[:EXAMPLES]),
                    citations=tuple(r for f in failed.values() for r in f["evidence"]), scope="near")
    if _walk_short(report) or (report.get("walk") or {}).get("links_omitted"):
        return flag("same-name-failed", V, "blocked", "amber", "the walk left links or companies unread past its limit; a company of the same "
                    "name could be among them", scope="near")
    whose = "the entity" if _company_start(report) else "a going company the person sits on"
    return flag("same-name-failed", V, "clear", "amber", f"no company that shares a name with {whose} has failed, among the companies of the "
                "same name the links lane joins", sources_held=("pub.links (company-name rule)", GAZETTE_HELD),
                sources_not_held=(CHANGE_HISTORY,), scope="near")


def shared_office(report):
    """A failed company and a going one at one registered office that is not a hub, with the failure's date and the start beside.
    From a company, the companies at its office that share neither its name nor a person are counted, not listed: blocked, never clear."""
    if _other_start(report):
        return flag("shared-office", V, "blocked", "amber", _other_start(report), scope="office")
    hubs = {}
    for h in report.get("hubs", []):
        if h["kind"] in OFFICE_HUBS:
            m = re.match(r"^companies:companies/[^/]+", h["ref"])
            hubs.setdefault(m.group(0) if m else h["ref"], h)
    hub_text = (f"; {len(hubs)} company(ies) met have an office that fifty or more companies share, a hub that joins nothing: "
                + "; ".join(_name(h) for h in list(hubs.values())[:EXAMPLES])) if hubs else ""
    if _company_start(report):
        s = report["subject"]
        same = [it for it in _companies(report, ("near",)) if _same_name(it)]
        every = _office_pairs(report, _failures(report, same, ("confirmed", "near")), [s])
    else:
        conf = _companies(report)
        every = _office_pairs(report, _failures(report, conf), _going(report))
    pairs = [p for p in every if p[3]]
    if pairs:
        return flag("shared-office", V, "fired", "amber",
                    f"{len(pairs)} failed and going company pair(s): the failed company's registered office before its failure is the going "
                    f"company's office now, not a hub, as the companies file states them: "
                    + " ; ".join(_side(p) for p in pairs[:EXAMPLES]) + f"; {_window(report, every)}; the office is in the office section" + hub_text,
                    citations=tuple(dict.fromkeys(r for p in pairs for r in [p[0]["company"]["ref"], p[1]["ref"], p[4]["ref"], p[5]["ref"]])),
                    sources_not_held=(OFFICE_NEIGHBOURS, LIQUIDATOR_OFFICE), scope="office")
    return flag("shared-office", V, "blocked", "amber",
                "no failed company met on the walk had, before its failure, the registered office a going one has"
                + (f" among the pairs listed ({_window(report, every)})" if every else "") + hub_text
                + f"; but {OFFICE_NEIGHBOURS} are not read, and {LIQUIDATOR_OFFICE}, so no clear is given",
                sources_not_held=(OFFICE_NEIGHBOURS, LIQUIDATOR_OFFICE), scope="office")


# ── the entity's standing and the Gazette on it ─────────────────────────────

def entity_status(report):
    if _other_start(report):
        return flag("entity-status", V, "blocked", "red", _other_start(report), scope="entity")
    if not _company_start(report):
        return flag("entity-status", V, "clear", "info", "the start is a person: how each of the person's companies stands is in the phoenix "
                    "section and the flags other-current-companies and repeat-failure", sources_held=(COMPANIES_HELD,), scope="entity")
    s = report["subject"]
    r = s["row"]
    status, kind = _status(s), r.get("entity_type") or "entity"
    nh = (LP_PARTNERS,) if "partnership" in kind.lower() else ()
    reg, removed = _date(r.get("registered_on")), _date(r.get("removed_on"))
    when = f"registered {reg.isoformat()}" if reg else "registration date not stated"
    if removed:
        when += f", removed {removed.isoformat()}"
    if _ending(s) == "insolvent":
        return flag("entity-status", V, "fired", "red", f"the companies file gives the entity the status {status!r} ({kind}; {when}): it is "
                    "itself a failed firm", citations=(s["ref"],), sources_not_held=nh + NOT_HELD_INSOLVENCY, scope="entity")
    if _ending(s) == "ended":
        return flag("entity-status", V, "fired", "red", f"the entity is no longer a registered company: status {status!r} ({kind}; {when})",
                    citations=(s["ref"],), sources_not_held=nh, scope="entity")
    if not r.get("in_latest", True):
        return flag("entity-status", V, "fired", "amber", f"the entity is not in the latest companies file; its last status was {status!r} "
                    f"({kind}; {when}); the interface check of step 5.5 would date the change", citations=(s["ref"],), sources_not_held=nh,
                    scope="entity")
    return flag("entity-status", V, "clear", "red", f"registered ({kind}; {when}) in the latest companies file",
                sources_held=("Companies register status (pub.companies)",), sources_not_held=nh, scope="entity")


def insolvency_notices(report):
    """MC-C3. Gazette insolvency notices on the company started from, or on every company the person has a row on, each with the
    person's own dates on the company beside it."""
    if _other_start(report):
        return flag("insolvency-notices", V, "blocked", "red", _other_start(report), sources_not_held=NOT_HELD_INSOLVENCY)
    if _company_start(report):
        own = [it for it in _notices(report) if _insolvency(it) and _on_subject(report, it)]
        if own:
            return flag("insolvency-notices", V, "fired", "red", f"{len(own)} Gazette insolvency notice(s) on the entity ({_counted(own, _kind)}): "
                        + "; ".join(f"{_kind(it)}, {it['dates']['text']}" for it in own[:EXAMPLES]),
                        citations=tuple(it["ref"] for it in own), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
        if set(section(report, "gazette").get("omitted_views") or ()) & {"gazette_liquidations", "gazette_company_notices"}:
            return flag("insolvency-notices", V, "blocked", "red", "the entity has more Gazette notices than the walk lists; an insolvency could "
                        "be among those left out", scope="entity")
        return flag("insolvency-notices", V, "clear", "red",
                    "no Gazette liquidation, receivership, administration, winding-up application, creditors' notice or deed of company "
                    "arrangement on the entity; its officers' other companies are not read (see phoenix-signature)",
                    sources_held=(GAZETTE_HELD + ", joined to the company by its number",), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
    conf = [it for it in _notices(report) if _insolvency(it)]
    nearby = [it for it in _notices(report, ("near",)) if _insolvency(it)]
    if conf:
        bits = []
        for it in conf[:EXAMPLES]:
            roles = _role_on(report, it.get("via") or _company_of(it))
            mine = "; ".join(f"the person's row: {r['row'].get('role_type') or 'shareholder of record'}, {r['dates']['text']}" for r in roles[:1]) \
                or "the person's row on it is in the officers section"
            bits.append(f"{_name(it)}: {_kind(it)}, {it['dates']['text']}; {mine}")
        return flag("insolvency-notices", V, "fired", "red",
                    f"{len(conf)} Gazette insolvency notice(s) on {len({it.get('via') for it in conf})} company(ies) the person has a row on: "
                    + " | ".join(bits) + _short_text(report), citations=tuple(it["ref"] for it in conf), sources_not_held=NOT_HELD_INSOLVENCY,
                    scope="officer-group")
    if nearby:
        return flag("insolvency-notices", V, "fired", "amber",
                    f"{len(nearby)} Gazette insolvency notice(s) on companies reached only through a near link: a namesake's companies, "
                    f"not the person's until confirmed{_short_text(report)}", citations=tuple(it["ref"] for it in nearby),
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="near")
    if _walk_short(report):
        return flag("insolvency-notices", V, "blocked", "red", "no Gazette insolvency notice on the companies the walk read, but it stopped "
                    "before reading every company the person has a row on", scope="officer-group")
    return _clear_or_past("insolvency-notices", "red", "no Gazette liquidation, receivership, administration, winding-up application, "
                          "creditors' notice or deed of company arrangement on any company the person has a row on",
                          sources_held=(GAZETTE_HELD,), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")


def repeat_failure(report):
    """Two or more of the person's companies failed (an insolvency status or notice), each with its date. Side by side."""
    if _company_start(report):
        return flag("repeat-failure", V, "blocked", "red", f"{NOT_FOLLOWED}: whether a director's other companies failed cannot be seen",
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if _other_start(report):
        return flag("repeat-failure", V, "blocked", "red", _other_start(report), scope="officer-group")
    bad = {c: f for c, f in _failures(report, _companies(report)).items() if f["kind"] == "insolvency"}
    nearby = {c: f for c, f in _failures(report, [it for it in _companies(report, ("near",)) if not _same_name(it)], ("confirmed", "near")).items()
              if f["kind"] == "insolvency" and c not in bad}
    if len(bad) >= 2:
        ordered = sorted(bad.values(), key=lambda f: (f["date"] is None, f["date"] or dt.date.min))
        return flag("repeat-failure", V, "fired", "red", f"{len(bad)} of the person's companies have an insolvency status or notice: "
                    + " | ".join(f"{_name(f['company'])} ({_how(f)})" for f in ordered[:EXAMPLES + 1]),
                    citations=tuple(dict.fromkeys(r for f in ordered for r in f["evidence"])), sources_not_held=NOT_HELD_INSOLVENCY,
                    scope="officer-group")
    if len(bad) + len(nearby) >= 2:
        return flag("repeat-failure", V, "fired", "amber", f"{len(bad)} confirmed company(ies) of the person's and {len(nearby)} reached only "
                    "through a near link have an insolvency status or notice: a namesake's companies, not the person's until confirmed: "
                    + "; ".join(f"{_name(f['company'])} ({_how(f)})" for f in list(nearby.values())[:EXAMPLES]),
                    citations=tuple(dict.fromkeys(r for f in list(bad.values()) + list(nearby.values()) for r in f["evidence"])),
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="near")
    if _walk_short(report):
        return flag("repeat-failure", V, "blocked", "red", f"{len(bad)} company(ies) with an insolvency on the companies the walk read, but it "
                    "stopped before reading every company the person has a row on", scope="officer-group")
    return _clear_or_past("repeat-failure", "red", f"{'one' if bad else 'no'} company the person has a confirmed row on has an insolvency "
                          "status or notice; no repeat", sources_held=(GAZETTE_HELD, "Companies register status (pub.companies)"),
                          sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")


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


def other_current_companies(report):
    """The person's going companies and their states, each with its start: the firms a failed one's people now run."""
    if _company_start(report):
        return flag("other-current-companies", V, "blocked", "amber", f"{NOT_FOLLOWED}: the other companies its people sit on are not read",
                    scope="officer-group")
    if _other_start(report):
        return flag("other-current-companies", V, "blocked", "amber", _other_start(report), scope="officer-group")
    conf = _companies(report)
    going = _going(report)
    if conf:
        by = _counted(conf, lambda it: {"going": "registered", "insolvent": "in an insolvency", "ended": "removed or ended"}[_ending(it)])
        return flag("other-current-companies", V, "fired", "info", f"the person has a confirmed row on {len(conf)} company(ies) ({by}); the going "
                    f"ones, newest first: " + "; ".join(f"{_name(it)} (registered {_iso(_date(it['row'].get('registered_on')))})"
                                                        for it in sorted(going, key=lambda x: str(x['row'].get('registered_on') or ''),
                                                                         reverse=True)[:EXAMPLES]) + _short_text(report),
                    citations=tuple(it["ref"] for it in conf), scope="officer-group")
    if _walk_short(report):
        return flag("other-current-companies", V, "blocked", "amber", "the walk stopped before reading every company the person has a row on",
                    scope="officer-group")
    return _clear_or_past("other-current-companies", "amber", "the person has no confirmed company row", sources_held=(COMPANIES_HELD,),
                          scope="officer-group")


def _current(it) -> bool:
    return bool(it["row"].get("in_latest")) and not it["row"].get("ended_on")


def officers_of_record(report):
    if _other_start(report):
        return flag("officers-of-record", V, "blocked", "info", _other_start(report), scope="entity")
    if not _company_start(report):
        return flag("officers-of-record", V, "clear", "info", "the start is a person: its own roles are listed in the officers section",
                    sources_held=(COMPANIES_HELD,), scope="entity")
    r = report["subject"]["row"]
    if "partnership" in (r.get("entity_type") or "").lower():
        return flag("officers-of-record", V, "blocked", "amber", "a limited partnership has general and limited partners, not directors, and the "
                    "limited partnerships register that names them is not held", sources_not_held=(LP_PARTNERS,), scope="entity")
    sec = [it for it in section(report, "officers")["items"] if it.get("via") == report["subject"]["ref"]]
    dirs = [it for it in sec if it["view"] == "directors"]
    holders = [it for it in sec if it["view"] == "shareholders"]
    now = [it for it in dirs if _current(it)]
    omitted = section(report, "officers").get("omitted") or 0
    tail = f"; {omitted:,} row(s) past the walk's limit, not listed" if omitted else ""
    text = (f"{len(now)} current director(s) and {len(dirs) - len(now)} past or not in the latest file; {len(holders)} holder(s) of record"
            f"{tail}; start a report from each director to read the companies they sit on")
    going = GOING_STATUS.match(_status(report["subject"])) and r.get("in_latest", True)
    if not now and not omitted and going:
        return flag("officers-of-record", V, "fired", "amber", f"the companies file names no current director of the entity: {text}",
                    citations=tuple(it["ref"] for it in dirs) or (report["subject"]["ref"],), scope="entity")
    return flag("officers-of-record", V, "clear", "info", text, sources_held=(COMPANIES_HELD,), scope="entity")


def young_entity(report):
    """Registered under 24 months: the shape a firm set up in a failed one's place takes. Amber on the entity, info on the person's
    companies (the phoenix signature is where a young one meets a failure)."""
    as_of = _as_of(report)
    if _other_start(report):
        return flag("young-entity", V, "blocked", "info", _other_start(report))
    pool = [report["subject"]] if _company_start(report) else _going(report)
    young = [(it, _date(it["row"].get("registered_on"))) for it in pool]
    young = [(it, reg) for it, reg in young if reg and (as_of - reg).days < YOUNG_DAYS]
    if young:
        who = "the entity was" if _company_start(report) else f"{len(young)} going company(ies) the person has a confirmed row on were"
        return flag("young-entity", V, "fired", "amber" if _company_start(report) else "info",
                    f"{who} registered under 24 months before {as_of.isoformat()}: "
                    + "; ".join(f"{_name(it)} (registered {reg.isoformat()})" for it, reg in young[:EXAMPLES]),
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


# ── its people ──────────────────────────────────────────────────────────────

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
    one of its directors."""
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


def practitioner_repeat(report):
    """The old entity-0.1 rule: one insolvency practitioner across several of a group's failed companies. A liquidation notice
    carries a count of its liquidators and their rows name the notice, not the company, so the walk cannot set them side by side."""
    return flag("practitioner-repeat", V, "blocked", "amber",
                "whether one liquidator recurs across the failed companies cannot be read: a Gazette liquidation notice publishes a count of "
                "its liquidators, and a liquidator's row names its notice, not its company, which the walk does not reach from a company; "
                "this check cannot run", sources_not_held=LIQUIDATOR_COMPANY, scope="officer-group")


def society_roles(report):
    conf = [it for it in items(report, ("society_officers",), ("confirmed",)) if it.get("via") != report["subject"]["ref"]]
    if conf:
        return flag("society-roles", V, "fired", "info", f"officer of {len({it.get('via') or _company_of(it) for it in conf})} incorporated "
                    "society(ies): " + "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in conf[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in conf), sources_not_held=CHARITIES_NOT_HELD)
    if _company_start(report):
        return flag("society-roles", V, "blocked", "info", f"{NOT_FOLLOWED}: their society roles are not read", sources_not_held=CHARITIES_NOT_HELD,
                    scope="officer-group")
    if _other_start(report):
        return flag("society-roles", V, "blocked", "info", _other_start(report), sources_not_held=CHARITIES_NOT_HELD)
    return flag("society-roles", V, "clear", "info", "no incorporated society officer role confirmed to the person",
                sources_held=("Incorporated Societies Register officers (pub.society_officers)",), sources_not_held=CHARITIES_NOT_HELD)


# ── the report's own reach ──────────────────────────────────────────────────

def namesake_exposure(report):
    names = list(section(report, "identity")["items"])
    nearby_elsewhere = [it for s in report["sections"] if s["name"] not in ("identity", "people") for it in s["items"] if it["grade"] == "near"]
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
        return flag("subject-hub", V, "fired", "amber", f"the start is itself a hub ({', '.join(kinds)}): {mine[0]['text']}; a failure beside a "
                    "going company among its many is shown and never raised red", citations=tuple(sorted({h["ref"] for h in mine})))
    return flag("subject-hub", V, "clear", "info", "the start is not a professional director, a nominee or the Crown on the rows held",
                sources_held=("pub.directors", "pub.groups"))


def past_roles(report):
    if HISTORY:
        return flag("past-roles", V, "clear", "info", "past roles and holdings are published with their filed end dates", sources_held=(COMPANIES_HELD,))
    left = [it for it in all_items(report).values() if it["view"] in ("directors", "shareholders") and it["grade"] == "confirmed"
            and not it["row"].get("in_latest", True)]
    seen = f"; {len(left)} of the rows listed left the file since July 2026 and carry no end date" if left else ""
    whose = "the entity's past officers and holders" if _company_start(report) else "the person's past directorships and holdings"
    return flag("past-roles", V, "blocked", "amber", f"{whose} are not held: {PAST_NOT_HELD}{seen}; a phoenix whose people left the failed "
                "company before it failed, or were struck off with it, cannot be seen here", sources_not_held=("past directorships and "
                                                                                                             "shareholdings with their end dates",))


def change_history(report):
    return flag("change-history", V, "blocked", "amber",
                "a company's earlier names, trading names, directors and offices are in the companies change history, which is not held before "
                "16 August 2026 and is held but not published since: a firm that failed under one name and trades under another, or whose "
                "office moved, cannot be seen by its history; this check cannot run", sources_not_held=(CHANGE_HISTORY,))


# ── what is not held ────────────────────────────────────────────────────────

def building_practitioners(report):
    return flag("building-practitioners", V, "blocked", "amber",
                "whether the firm's people hold a building practitioner's licence, of which class, and any disciplinary finding against them, "
                "is in the licensed building practitioners register, which is not held yet (plan step 5.3); this check cannot run",
                sources_not_held=BUILDING)


def insolvency_register(report):
    return flag("insolvency-register", V, "blocked", "red",
                "the Official Assignee's Insolvency Register (a bankruptcy's discharge, a no-asset procedure, a summary instalment order, and the "
                "removals it records daily) is not held; the Gazette's own notices are read above; this check cannot run",
                sources_not_held=(INSOLVENCY_REGISTER,))


def court_judgments(report):
    return flag("court-judgments", V, "blocked", "red",
                "court judgments are not held yet (plan step 5.4): a creditor's judgment, a winding-up order's reasons, a claim under a "
                "construction contract cannot be seen; this check cannot run", sources_not_held=COURTS)


def employment_determinations(report):
    return flag("employment-determinations", V, "blocked", "amber",
                "the Employment Relations Authority's determinations (unpaid wages and holiday pay, arrears orders, penalties) are not held: a "
                "firm that left its workers unpaid cannot be seen here; this check cannot run", sources_not_held=EMPLOYMENT)


def securities_register(report):
    return flag("securities-register", V, "blocked", "info",
                "who has registered security over the firm's assets, and when, is in the Personal Property Securities Register, which is not "
                "held; this check cannot run", sources_not_held=(SECURITIES,))


def mortgagee_possession(report):
    return flag("mortgagee-possession", V, "blocked", "amber",
                "a lender's entry into possession of a company's land or goods is published in the Gazette (pub.gazette_possessions), but the "
                "report's catalogue does not know the view, so this report cannot reach it; this check cannot run", sources_not_held=POSSESSIONS)


RULES = (phoenix_signature, same_name_failed, shared_office, entity_status, insolvency_notices, repeat_failure, register_events,
         other_current_companies, officers_of_record, young_entity, prohibition, bankruptcy, practitioner_roles, practitioner_repeat,
         society_roles, namesake_exposure, walk_coverage, subject_hub, past_roles, change_history, building_practitioners,
         insolvency_register, court_judgments, employment_determinations, securities_register, mortgagee_possession)
