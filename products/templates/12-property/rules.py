"""The property developer due diligence rules (plan 5.2, use case 12). Pure
functions over the built report, each returning one flag. An investor or
an apartment buyer asks "who is really building this, and what happened to
their last projects". The rules stand for the old estate's property
requirement (USE_CASE_REQUIREMENTS.md section 2.6: MC-P1 the SPV
incorporation web, the SPV-serial rule: the same principals, sequential
special-purpose companies, a liquidation after settlement) and its company
and person rules (data-layer/flags/flags: liquidation-history,
group-receivership, prohibition, young-entity, namesake-exposure), taken as
ideas and tests, not code, where the held registers can support them:

  serial-pattern         one principal's companies, two or more failed (a liquidation, a receivership, an administration or a
                         removal, each dated from its Gazette notice), beside the principal's going companies, the gap in days
  earlier-failure        a principal's other company that failed, its date beside the entity's start (from a person, beside
                         each going company's), the gap in days; the window is the reader's setting
  entity-status          the entity's own register status, and an insolvency notice on it the latest file does not yet show
  young-entity           registered under 24 months
  sole-vehicle           one person the sole director and the sole holder of record: a one-person vehicle's shape
  shared-office          a failed company at the entity's registered office (not a hub); from a person, a failed company's
                         office from before its failure shared with a going one
  professional-office    the entity's registered office carries an accountant's, a lawyer's or a formation agent's name: a hub
  possession             a mortgagee's entry into possession where the entity or a principal's company is the mortgagor
  prohibition, bankruptcy  on the person, or on a director of the entity reached through the officers reach
  insolvency-notices     Gazette insolvency notices on the entity and on the principals' companies
  holding-chain          the companies above it, and where the chain is cut
  history-reach          how many of the entity's directors reached any other company: a name the links lane joins only
                         near is not followed, so an empty history is not a clean one
  namesake-exposure      the report's own uncertainty
  land-titles, overseas-investment, building-consents, court-judgments, securities-register, insolvency-register,
  real-estate-authority, building-practitioners, past-roles
                         blocked: not held

The builder adds its common rules for every template (group-standing,
hubs-met, replaced-return); this file carries no copy of them.

Every rule branches on the start: a company, a person, or anything else.
From a company the walk follows its directors one step (the `officers`
reach): a director's other company is the director's connection, near,
so evidence there is amber at most and says to start a report from the
director; from a person the person's own confirmed companies are the
record, and evidence there may be red. A holder of record is listed and
never followed, and never called an owner. A check the walk could not
have seen is blocked, never clear; a check over a principal's companies is
never clear while the companies file lists current roles only. A
director's near link (a row the link rules join to the director by name
alone, `near_link` on the item) reaches a namesake's companies: they are
kept apart as their own principal, amber at most, never the director's
own. The directors and the notices on a company above in the holding chain
(`above`) are the holder's: listed, and counted by no check as the
entity's or a principal's. Dates sit
side by side with the gap in days; no flag joins two facts with a word of
cause, and none prints an address: the office section shows a company's.

Imports nothing of products.report: the one-way test holds a template folder
to its own code. The shape loads this file by path and binds the name
`contract` (products/report/contract.py) before it runs."""
from __future__ import annotations

import datetime as dt
import re

V = "0.1"
#: the window is the reader's setting, not the template's (ruling 65, 21 October 2026, as the construction template reads it):
#: every dated failure is set beside every going company whatever the gap, nearest first, and a window cuts only when the reader
#: passes one as the report's `window_days` (days either side of the failure), a parameter template.toml declares.
WINDOW_KEY = "window_days"
#: the gaps a flag counts its pairs within, so a reader sees the old defaults without losing the rest (the old MC-C1 90 days, 365)
COUNTED_WINDOWS = (90, 365)
YOUNG_DAYS = 730          # under 24 months registered (the old young-entity rule)
SERIAL_AT = 2             # failed companies under one principal at which the serial pattern fires
NAMESAKE_NOTE_AT = 5      # namesakes set apart at which the report's caveat fires
EXAMPLES = 4              # dated examples a fired flag states in its text
#: whether a published view holds past roles with their end dates. It does not (measured 2026-10-20 by banking-1, and 2026-10-21
#: here: of 4,960 director rows on a removed company, 4,941 are not in the latest file and the rest were seen only in July and August
#: 2026). While False, a check over a principal's companies fires on what it sees and never clears.
HISTORY = False
PAST_NOT_HELD = ("the companies file lists current roles only, and a company removed from the register carries no directors in it: a "
                 "principal's earlier company that was liquidated and then removed is not seen, nor its failure")

INSOLVENCY_KINDS = ("winding-up application", "receivership", "administration", "notice to creditors", "deed of company arrangement")
INSOLVENT_STATUS = re.compile(r"liquidation|receiv|administration|statutory management", re.I)
ENDED_STATUS = re.compile(r"^(removed|deregistered|dissolved|closed|cancelled|inactive|suspended)$", re.I)
GOING_STATUS = re.compile(r"^registered$", re.I)
SAME_NAME = re.compile(r"^company-name")
HUB_KINDS = ("professional-director", "nominee", "crown")
OFFICE_HUBS = ("busy-address", "thousand-address")
#: an office line that names a professional firm: an accountant's, a lawyer's, a formation agent's. Read, never printed. Measured
#: 2026-10-21: 5,551 of 855,489 registered offices in the latest file carry such words; most such offices are hubs by count instead.
PROFESSIONAL_OFFICE = re.compile(r"accountant|chartered|\bca\b|lawyer|solicitor|barrister|\blegal\b|\blaw\b|\bbdo\b|kpmg|deloitte|\bpwc\b|"
                                 r"pricewaterhouse|thornton|baker tilly|crowe|\brsm\b|staples rodway|formation", re.I)
#: an office the file says is kept care of another (a `care_of` line, or "c/-" in a line): another's office, read as a hub too
CARE_OF = re.compile(r"\bc/-|\bcare of\b", re.I)
#: the words a fired flag must not carry, the shape's own (rules 3 and 4): a register's name that holds one is not quoted in a flag
UNSAFE = re.compile(contract.CAUSE.pattern + "|" + contract.OWNER.pattern, re.I)   # noqa: F821  (bound by the loader)

COMPANIES_HELD = "Companies register (pub.companies, pub.directors, pub.shareholders)"
STATES_HELD = "Companies register earlier states (pub.company_states)"
OFFICES_HELD = "Companies register addresses (pub.company_addresses)"
GAZETTE_HELD = "New Zealand Gazette liquidation and company notices (pub.gazette_liquidations, pub.gazette_company_notices)"
POSSESSIONS_HELD = "New Zealand Gazette mortgagee possessions (pub.gazette_possessions)"
PEOPLE_HELD = "New Zealand Gazette prohibitions and bankruptcies (pub.gazette_prohibitions, pub.gazette_bankruptcies), through pub.links"
INSOLVENCY_REGISTER = "the Official Assignee's Insolvency Register (interface awaited since 19 September 2026)"
CHANGE_HISTORY = "the companies change history: not held before 16 August 2026, held and unread since (former names, earlier directors and offices)"
LIQUIDATOR_OFFICE = ("a failed company's registered office from before its failure: a liquidated company's office is usually its "
                     "liquidator's from the day of the appointment, and the office it traded from is in the change history")
PERSON_MORTGAGORS = "a mortgagee possession whose mortgagor is a person (the name and the property stay in the gazette lane's private tables)"
SECURITIES = "the Personal Property Securities Register (interface awaited since 19 September 2026)"
LINZ = "land titles (LINZ): which company holds which title, and since when"
NOT_FOLLOWED_HOLDERS = "a holder of record is listed and not followed: start a report from each holder listed"
#: the registers a developer check would read, each named first as the catalogue's not-held key names it (card
#: the-not-held-list-has-no-key-for-the-property-registers, closed by fix-report-2): the not-held section cites the key, so the
#: flag and the memo's not-held line name the same register
OIO = "Overseas Investment Office decisions (key oio; applicant, vendor, price)"
CONSENTS = "Building consents, code compliance certificates and council minutes (key building_consents)"
REA = "Real Estate Authority decisions (key rea; the lane captures and publishes no view yet)"
#: the key a director's namesake principal takes beside the director's own: the companies the director's near links reach
NAMESAKE_KEY = " near-link"


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


def _person_start(report) -> bool:
    """A person row, or a filed row that takes the group of the person row a confirmed link names."""
    return report["subject"]["kind"] == "person" or bool((report.get("group") or {}).get("via"))


def _other_start(report):
    """A start that is neither a company nor a person (a society, a notice): the record these checks read is not walked from it."""
    if _company_start(report) or _person_start(report):
        return None
    s = report["subject"]
    article = "an" if s["kind"][:1] in "aeiou" else "a"
    return (f"the report starts from {article} {s['kind']} row (pub.{s['view']}), not a person or a company: the record these checks read "
            f"is not walked from it, so no clear is given; start the report from the developer company or from a person row")


def _subject_key(report) -> str:
    return report["subject"]["ref"].split(":", 1)[1]


def _walk(report) -> dict:
    return report.get("walk") or {}


def _links_whole(report) -> bool:
    w = _walk(report)
    return bool(w.get("links_built")) and not w.get("links_omitted")


def _walk_short(report) -> bool:
    w = _walk(report)
    return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))


def _name(it) -> str:
    """A row's title for a flag's text; a register name that carries a word the shape reads as cause or ownership, or has a street
    address's shape, is not quoted (the section lists it)."""
    t = it.get("title") or it["ref"]
    return f"the company cited ({it['ref']})" if UNSAFE.search(t) or contract.address_shaped(t) else t   # noqa: F821


def _status(it) -> str:
    return str((it.get("row") or {}).get("status") or "").strip()


def _ending(it) -> str:
    """A company's standing as its register status files it: insolvent, ended or going."""
    st = _status(it)
    if INSOLVENT_STATUS.search(st):
        return "insolvent"
    if ENDED_STATUS.match(st) or _date((it.get("row") or {}).get("removed_on")):
        return "ended"
    return "going" if GOING_STATUS.match(st) or not st else "ended"


def _registered(it):
    return _date((it.get("row") or {}).get("registered_on"))


def _company_of(it) -> str:
    """The company a role, holding, office or notice sits on, as a ref."""
    if it.get("entity"):
        return it["entity"]["ref"]
    r = it.get("row") or {}
    if it["view"] == "gazette_possessions":
        key = r.get("mortgagor_register_key") or r.get("mortgagee_register_key")
    else:
        key = r.get("entity_key") or r.get("register_key")
    if key:
        return f"companies:{key}"
    return it.get("via") or ""


def _fold(name: str) -> str:
    return " ".join((name or "").lower().translate(str.maketrans("āēīōū", "aeiou")).split())


def _hub_refs(report, kinds) -> set:
    return {h["ref"] for h in report.get("hubs", []) if h.get("kind") in kinds}


def _counted(xs, label) -> str:
    counts = {}
    for x in xs:
        counts[label(x)] = counts.get(label(x), 0) + 1
    return ", ".join(f"{n} {k}" for k, n in sorted(counts.items()))


def _clear_or_past(rule, severity, text, **kw):
    """A clear over the principals' companies, or, while past roles are not held, a blocked flag saying what was seen and what
    cannot be."""
    if HISTORY:
        return flag(rule, V, "clear", severity, text, **kw)
    kw.pop("sources_held", None)
    return flag(rule, V, "blocked", severity, f"{text}; but {PAST_NOT_HELD}: no clear is given", **kw)


# ── notices ─────────────────────────────────────────────────────────────────

def _notices(report, grades=("confirmed", "near")):
    return list(items(report, ("gazette_liquidations", "gazette_company_notices"), grades))


def _kind(it) -> str:
    return "liquidation" if it["view"] == "gazette_liquidations" else (it["row"].get("kind") or "notice")


def _insolvency(it) -> bool:
    """A liquidator's appointment, or a company notice of an insolvency kind that is not a receiver ceasing to act."""
    if it["view"] == "gazette_liquidations":
        return True
    r = it["row"]
    return it["view"] == "gazette_company_notices" and r.get("kind") in INSOLVENCY_KINDS and "ceas" not in (r.get("action") or "").lower()


def _removal(it) -> bool:
    r = it["row"]
    action = (r.get("action") or "").lower()
    return it["view"] == "gazette_company_notices" and r.get("kind") == "removal" and "restor" not in action and "revocation" not in action


def _failure_date(it):
    """The day a failure notice dates it from: a liquidator's or receiver's appointment where the Gazette states one, otherwise the day
    the notice was published (a winding-up application's own date is its hearing, a removal's the last day for objections)."""
    r = it["row"]
    if it["view"] == "gazette_liquidations":
        return _date(r.get("appointed_on")) or _date(r.get("published_on"))
    if (r.get("event_basis") or "") == "appointment":
        return _date(r.get("event_on")) or _date(r.get("published_on"))
    return _date(r.get("published_on")) or _date(r.get("filed_on"))


def _failures(report, companies: list) -> dict:
    """{company ref: {'company', 'date', 'kind', 'evidence', 'notice'}} for each company that failed: an insolvency (a notice, or the
    status alone, undated) or a removal. 'date' is the earliest failure date a notice gives; an insolvency outranks a removal."""
    by_ref = {it["ref"]: it for it in companies}
    out = {}
    for it in companies:
        if _ending(it) == "insolvent":
            out[it["ref"]] = {"company": it, "date": None, "kind": "insolvency", "evidence": [it["ref"]], "notice": None}
    for n in _notices(report):
        c = _company_of(n)
        if c not in by_ref:
            continue
        # an intention to remove a company the file still calls going lapsed (it filed, or someone objected): it is no failure
        kind = "insolvency" if _insolvency(n) else "removal" if _removal(n) and _ending(by_ref[c]) != "going" else None
        if not kind:
            continue
        e = out.setdefault(c, {"company": by_ref[c], "date": None, "kind": kind, "evidence": [c], "notice": None})
        if kind == "removal" and e["kind"] == "insolvency":
            continue
        if kind == "insolvency" and e["kind"] == "removal":
            e.update(kind="insolvency", date=None, notice=None, evidence=[c])
        e["evidence"].append(n["ref"])
        d = _failure_date(n)
        if d and (e["date"] is None or d < e["date"]):
            e["date"], e["notice"] = d, n
    return out


def _how(f) -> str:
    """'liquidation (liquidator appointed by the shareholders), appointed 12 August 2026' as the notice dates it."""
    n = f["notice"]
    if n is None:
        return f"status {_status(f['company'])!r}, no dated Gazette notice reached"
    by = n["row"].get("appointed_by")
    what = f"liquidation (liquidator appointed by the {by})" if n["view"] == "gazette_liquidations" and by else _kind(n)
    return f"{what}, {n['dates']['text']}"


# ── the window ──────────────────────────────────────────────────────────────

def _window_days(report):
    """The reader's window in days, or None: no cut. A value that is not a whole number of days, zero or more, is no window."""
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
            start = _registered(g)
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
    return f"{_name(f['company'])}: {_how(f)} | {_name(g)}: registered {_iso(_registered(g))}, {when}"


def _window(report, pairs=()) -> str:
    """What the pairs span: how many fall within 90 and 365 days, and the reader's window if one is set, with what it leaves out."""
    gaps = [abs(p[2]) for p in pairs]
    counts = " and ".join(f"{sum(1 for g in gaps if g <= d)} within {d} days" for d in COUNTED_WINDOWS)
    text = f"of {len(gaps)} pair(s), nearest first, {counts}" if gaps else "no dated pair"
    w, raw = _window_days(report), report.get(WINDOW_KEY)
    if w is not None:
        out = sum(1 for p in pairs if not p[3])
        text += f"; the reader's window is {w} days either side of the failure's Gazette date" + (
            f", and {out} pair(s) fall outside it and are not listed" if out else "")
    elif raw not in (None, ""):
        text += f"; the window asked for ({str(raw)[:20]!r}) is not a whole number of days, so no cut is applied"
    else:
        text += "; no window is set, so every gap is shown"
    return text


# ── the principals and their companies ──────────────────────────────────────

def _own_people(report, views=("directors",)) -> list:
    """The entity's own current officers (a company start), each once, suppressed rows kept out of every text."""
    ref = report["subject"]["ref"]
    return [it for it in all_items(report).values() if it["view"] in views and it.get("kind") == "person"
            and _company_of(it) == ref and it["grade"] == "confirmed" and (it.get("row") or {}).get("in_latest", True)
            and not (it.get("row") or {}).get("ended_on")]


def _principals(report) -> dict:
    """{principal ref: {'title', 'grade', 'hub', 'companies': {ref: company item}}}: from a company, each current director of the
    entity, with the entity and the director's other companies the officers reach listed (near); from a person, the person, with
    the companies of the person's own confirmed rows (confirmed), and apart, under the key 'near', a namesake's (near)."""
    every = all_items(report)
    companies = {ref: it for ref, it in every.items() if it["view"] == "companies"}
    hubs = _hub_refs(report, HUB_KINDS)
    out = {}
    if _company_start(report):
        s = report["subject"]
        for d in _own_people(report):
            out[d["ref"]] = {"title": "a director whose name is suppressed" if d.get("suppressed") else d["title"], "grade": "near",
                             "hub": d["ref"] in hubs, "item": d, "companies": {s["ref"]: s}}
        own = dict(out)
        for it in every.values():
            t = it.get("through")
            if it["view"] not in ("directors", "shareholders") or t not in own:
                continue
            c = companies.get(_company_of(it))
            if c is None:
                continue
            if it.get("near_link"):   # a namesake's company: its own principal, apart
                out.setdefault(t + NAMESAKE_KEY, {"title": f"rows a near link of {own[t]['title']} reaches", "grade": "near", "hub": False,
                                                  "item": own[t]["item"], "companies": {}, "namesake": True})["companies"].setdefault(c["ref"], c)
            else:
                own[t]["companies"].setdefault(c["ref"], c)
        return out
    if _person_start(report):
        s = report["subject"]
        own = {"title": "the person" if s.get("suppressed") else s["title"], "grade": "confirmed",
               "hub": bool(({s["ref"]} | {m["ref"] for m in report.get("members", [])}) & hubs), "item": s, "companies": {}}
        near_p = {"title": "rows reached only through a near link", "grade": "near", "hub": False, "item": s, "companies": {}}
        mine = {s["ref"]} | {m["ref"] for m in report.get("members", [])}
        for it in every.values():
            if it["view"] not in ("directors", "shareholders") or it.get("kind") != "person":
                continue
            if not (it["ref"] in mine or it.get("via") == s["ref"] or it.get("via") in mine or it["ref"] == s["ref"]):
                continue
            c = companies.get(_company_of(it))
            if c is None:
                continue
            (own if it["grade"] == "confirmed" and c["grade"] == "confirmed" else near_p)["companies"].setdefault(c["ref"], c)
        if s["view"] in ("directors", "shareholders"):
            c = companies.get(_company_of(s))
            if c is not None:
                own["companies"].setdefault(c["ref"], c)
        out[s["ref"]] = own
        if near_p["companies"]:
            out["near"] = near_p
        return out
    return out


def _evidence_grade(report, p) -> str:
    """'red' where the record is the person's own confirmed rows and the person is no hub; 'amber' through a director (near), a
    director's near link (a namesake's) or a hub."""
    return "red" if p["grade"] == "confirmed" and not p["hub"] and not p.get("namesake") else "amber"


def _own_principals(principals) -> dict:
    return {k: p for k, p in principals.items() if not p.get("namesake")}


def _namesakes(principals) -> dict:
    return {k: p for k, p in principals.items() if p.get("namesake")}


def _whose(report, p) -> str:
    if p.get("namesake"):
        return ("companies a director's near link reaches (the link rules join the row to the director by name alone: a namesake's until a "
                "rule confirms it, never the director's own; start a report from the director)")
    if _company_start(report):
        hub = "; the director is a hub (a professional director or a nominee): a pattern through a hub means little on its own" if p["hub"] else ""
        return (f"the director {p['title']}'s companies, reached through the director's row on the entity (near: a director's other "
                f"company is the director's connection, not the entity's; start a report from the director for the confirmed record){hub}")
    if p["grade"] == "near":
        return "companies reached only through a near link, each listed with its reason (a namesake's, or a contested group's): not the person's until confirmed"
    return "the person's own confirmed companies" + ("; the person is a hub" if p["hub"] else "")


def _reach_short(report) -> str:
    """Why the walk cannot have seen every principal's company, or ''."""
    w = _walk(report)
    bits = []
    if _company_start(report) and w.get("officers_omitted"):
        bits.append(f"{w['officers_omitted']} director(s) past the first {w.get('limits', {}).get('officers', 12)} were not followed")
    if _walk_short(report):
        n = (w.get("entities_not_expanded") or 0) + (w.get("entities_omitted") or 0)
        bits.append(f"the walk did not read the notices on {n:,} further company(ies)")
    if w.get("links_built") is False:
        bits.append("no links are published")
    if w.get("links_omitted"):
        bits.append(f"{w['links_omitted']} link(s) past the walk's limit were not read")
    om = sum(s.get("omitted") or 0 for s in report.get("sections", []) if s["name"] in ("history", "serial"))
    if om:
        bits.append(f"{om} row(s) on the principals' companies past the walk's limit were not listed")
    return "; ".join(bits)


# ── the serial pattern ──────────────────────────────────────────────────────

def serial_pattern(report):
    """MC-P1, the SPV-serial rule. For each principal, the companies under them, two or more of which failed (a liquidation, a
    receivership, an administration or a removal, each dated from its Gazette notice), set out in the order they were registered,
    each with its life from registration to failure, beside the principal's going companies and the gap in days. Red on a person's
    own confirmed companies with two or more insolvencies; amber through a director, a hub or a namesake; info where every failure
    is a removal (a company removed after its project is the special-purpose shape too, and is not an insolvency)."""
    if _other_start(report):
        return flag("serial-pattern", V, "blocked", "red", _other_start(report), sources_not_held=(INSOLVENCY_REGISTER, CHANGE_HISTORY))
    principals = _principals(report)
    if _company_start(report) and not principals:
        return flag("serial-pattern", V, "blocked", "red", "the companies file lists no current director on the entity, so there is no "
                    "principal to follow; the holders of record are listed and not followed: start a report from each holder listed",
                    sources_not_held=(CHANGE_HISTORY,), scope="principals")
    found = []
    for pref, p in principals.items():
        cos = list(p["companies"].values())
        failed = _failures(report, cos)
        if len(failed) < SERIAL_AT:
            continue
        going = [c for c in cos if _ending(c) == "going" and c["ref"] not in failed and not _same_name(c)]
        found.append((pref, p, failed, going))
    if found:
        window = _window_days(report)
        severities, bits, cites = [], [], []
        shared = _shared_by_directors(report, principals)
        for pref, p, failed, going in sorted(found, key=lambda x: (-len(x[2]), x[0]))[:EXAMPLES]:
            insolvencies = [f for f in failed.values() if f["kind"] == "insolvency"]
            sev = _evidence_grade(report, p) if len(insolvencies) >= SERIAL_AT else "amber" if insolvencies else "info"
            if sev == "red" and len(insolvencies) < SERIAL_AT:
                sev = "amber"
            severities.append(sev)
            seq = sorted(failed.values(), key=lambda f: (_registered(f["company"]) or dt.date.max, f["company"]["ref"]))
            lives = []
            for f in seq[:EXAMPLES]:
                start = _registered(f["company"])
                life = f", {(f['date'] - start).days} days from registration" if f["date"] and start else ""
                lives.append(f"{_name(f['company'])} (registered {_iso(start)}; {_how(f)}{life})")
            pairs = [x for x in _pairs(failed, going, window) if x[3]]
            text = (f"{p['title']}: {len(failed)} of {len(p['companies'])} companies failed ({len(insolvencies)} an insolvency, "
                    f"{len(failed) - len(insolvencies)} a removal from the register, which is not an insolvency), in the order registered: "
                    + "; ".join(lives) + (f"; and {len(seq) - EXAMPLES} more" if len(seq) > EXAMPLES else "")
                    + f"; {len(going)} going company(ies) under the same principal"
                    + (": " + " ; ".join(_side(x) for x in pairs[:EXAMPLES]) if pairs else "") + f" ({_window(report, _pairs(failed, going, window))})"
                    + f"; these are {_whose(report, p)}")
            bits.append(text)
            cites += [r for f in seq for r in f["evidence"]] + [g["ref"] for g in going[:EXAMPLES]]
        sev = "red" if "red" in severities else "amber" if "amber" in severities else "info"
        more = f"; {len(found) - EXAMPLES} more principal(s) show the pattern" if len(found) > EXAMPLES else ""
        return flag("serial-pattern", V, "fired", sev,
                    f"{len(found)} principal(s) with {SERIAL_AT} or more failed companies: " + " || ".join(bits) + more + shared
                    + "; each failure and each start is a dated fact set beside the other with the gap in days, and nothing here says one "
                    "followed from the other", citations=tuple(dict.fromkeys(cites)),
                    sources_not_held=(INSOLVENCY_REGISTER, CHANGE_HISTORY), scope="principals")
    short = _reach_short(report)
    if short:
        return flag("serial-pattern", V, "blocked", "red", f"the walk could not read every principal's companies ({short}): a failure "
                    "among those left out cannot be counted", sources_not_held=(CHANGE_HISTORY,), scope="principals")
    n = sum(len(p["companies"]) for p in principals.values())
    ns = _namesakes(principals)
    return _clear_or_past("serial-pattern", "red", f"no principal has {SERIAL_AT} or more failed companies among the {n} company "
                          f"row(s) the walk reached under {len(principals) - len(ns)} principal(s)"
                          + (f", {sum(len(p['companies']) for p in ns.values())} of them through a director's near link and counted apart"
                             if ns else ""), sources_held=(COMPANIES_HELD, GAZETTE_HELD),
                          sources_not_held=(INSOLVENCY_REGISTER, CHANGE_HISTORY), scope="principals")


def _same_name(it) -> bool:
    """A company reached by the links lane's company-name rule: it shares a name and nothing else."""
    return bool(SAME_NAME.match(it.get("rule") or ""))


def _shared_by_directors(report, principals) -> str:
    """From a company: how many of the directors' other companies have two or more of the entity's directors on them, as a count."""
    principals = _own_principals(principals)
    if not _company_start(report) or len(principals) < 2:
        return ""
    on = {}
    for pref, p in principals.items():
        for cref in p["companies"]:
            if cref != report["subject"]["ref"]:
                on.setdefault(cref, set()).add(pref)
    k = sum(1 for v in on.values() if len(v) >= 2)
    return f"; {k} of the directors' other companies have two or more of the entity's directors on them" if k else ""


def earlier_failure(report):
    """A principal's company that failed, its date beside the entity's start (from a company) or beside each of the person's going
    companies (from a person), the gap in days, nearest first; the window is the reader's. One failure is enough: the serial pattern
    counts the repeats."""
    if _other_start(report):
        return flag("earlier-failure", V, "blocked", "red", _other_start(report), sources_not_held=(INSOLVENCY_REGISTER,))
    principals = _principals(report)
    window = _window_days(report)
    all_pairs, cites, sev = [], [], []
    for pref, p in principals.items():
        cos = list(p["companies"].values())
        failed = _failures(report, [c for c in cos if c["ref"] != report["subject"]["ref"]])
        if _company_start(report):
            beside = [report["subject"]]
        else:
            beside = [c for c in cos if _ending(c) == "going" and c["ref"] not in failed and not _same_name(c)]
        ps = _pairs(failed, beside, window)
        if ps:
            all_pairs.append((p, ps))
            sev.append(_evidence_grade(report, p) if any(x[0]["kind"] == "insolvency" for x in ps) else "info")
            cites += [r for x in ps if x[3] for r in x[0]["evidence"]] + [x[1]["ref"] for x in ps if x[3]]
    inside = [(p, [x for x in ps if x[3]]) for p, ps in all_pairs]
    inside = [(p, ps) for p, ps in inside if ps]
    if inside:
        bits = []
        for p, ps in inside[:EXAMPLES]:
            bits.append(f"{p['title']}: " + " ; ".join(_side(x) for x in ps[:EXAMPLES]) + (f"; and {len(ps) - EXAMPLES} more" if len(ps) > EXAMPLES else "")
                        + f" ({_window(report, next(q for pp, q in all_pairs if pp is p))}); {_whose(report, p)}")
        s = "red" if "red" in sev else "amber" if "amber" in sev else "info"
        return flag("earlier-failure", V, "fired", s, f"{sum(len(ps) for _, ps in inside)} failure(s) on a principal's company set beside "
                    f"{'the entity' if _company_start(report) else 'a going company'}'s start: " + " || ".join(bits),
                    citations=tuple(dict.fromkeys(cites)), sources_not_held=(INSOLVENCY_REGISTER, CHANGE_HISTORY), scope="principals")
    if all_pairs:   # pairs exist but the reader's window leaves out every one
        return flag("earlier-failure", V, "clear", "info", "every dated failure on a principal's company falls outside the reader's window ("
                    + _window(report, [x for _, ps in all_pairs for x in ps]) + ")", sources_held=(COMPANIES_HELD, GAZETTE_HELD),
                    scope="principals")
    short = _reach_short(report)
    if short or (_company_start(report) and not principals):
        return flag("earlier-failure", V, "blocked", "red", f"the walk could not read every principal's companies ({short or 'no current director to follow'})",
                    sources_not_held=(CHANGE_HISTORY,), scope="principals")
    undated = sum(1 for p in principals.values() for f in _failures(report, list(p["companies"].values())).values() if f["date"] is None)
    text = "no dated failure on a principal's company reached" + (f"; {undated} failed by status with no dated Gazette notice reached, so no gap can be measured" if undated else "")
    return _clear_or_past("earlier-failure", "red", text, sources_held=(COMPANIES_HELD, GAZETTE_HELD),
                          sources_not_held=(INSOLVENCY_REGISTER, CHANGE_HISTORY), scope="principals")


# ── the entity ──────────────────────────────────────────────────────────────

def _latest(notices):
    return max(notices, key=lambda n: (_date(n["row"].get("published_on")) or dt.date.min, n["ref"]))


def entity_status(report):
    """The entity's own status as the latest file states it, its earlier states, and an insolvency notice on it the file does not yet
    show (the Gazette is daily, the file monthly)."""
    if not _company_start(report):
        return flag("entity-status", V, "blocked", "info", "the report starts from a person: each company's status is in the project history, "
                    "and the flags serial-pattern and earlier-failure read them" if _person_start(report) else _other_start(report))
    s = report["subject"]
    own = [n for n in _notices(report, ("confirmed",)) if _company_of(n) == s["ref"]]
    ins = [n for n in own if _insolvency(n)]
    rem = [n for n in own if _removal(n)]
    earlier = [it for it in items(report, ("company_states",)) if _company_of(it) == s["ref"]]
    st, end = _ending(s), _status(s) or "no status"
    was = f"; earlier states: {_counted(earlier, lambda it: _status(it) or 'no status')}" if earlier else ""
    if st == "insolvent" or ins:
        first = min(ins, key=lambda n: _failure_date(n) or dt.date.max) if ins else None
        gap = ""
        if ins and st != "insolvent":
            gap = (f"; the latest file still states {end!r}: the Gazette is read daily and the companies file monthly, so the notice is "
                   f"newer than the file")
        return flag("entity-status", V, "fired", "red", f"the entity's register status is {end!r}" + (
            f"; {len(ins)} insolvency notice(s) on it, the first {_kind(first)}, {first['dates']['text']}" if first else "") + gap + was,
                    citations=tuple([s["ref"]] + [n["ref"] for n in ins] + [it["ref"] for it in earlier]), scope="subject")
    pending = [n for n in rem if (_date(n["row"].get("event_on")) or dt.date.min) >= _as_of(report)]
    if st == "ended" or pending:
        return flag("entity-status", V, "fired", "amber", f"the entity's register status is {end!r}" + (
            f"; {len(rem)} removal notice(s) on it, the latest {_latest(rem)['dates']['text']}" if rem else "") + (
            "; the last day for objections has not passed" if pending and st != "ended" else "") + ": a removal from the register is not an insolvency" + was,
                    citations=tuple([s["ref"]] + [n["ref"] for n in rem] + [it["ref"] for it in earlier]), scope="subject")
    if rem:
        return flag("entity-status", V, "fired", "info", f"the entity is {end!r} in the latest file; {len(rem)} notice(s) of an intention to remove "
                    f"it were published, the latest {_latest(rem)['dates']['text']}, and the file still states {end!r}, so the company was not "
                    f"removed" + was, citations=tuple([s["ref"]] + [n["ref"] for n in rem] + [it["ref"] for it in earlier]), scope="subject")
    if earlier:
        return flag("entity-status", V, "fired", "info", f"the entity is {end!r} in the latest file{was}",
                    citations=tuple([s["ref"]] + [it["ref"] for it in earlier]), scope="subject")
    return flag("entity-status", V, "clear", "info", f"the entity is {end!r} in the latest file, with no earlier state and no insolvency or "
                "removal notice on it", sources_held=(COMPANIES_HELD, STATES_HELD, GAZETTE_HELD), sources_not_held=(INSOLVENCY_REGISTER,),
                scope="subject")


def young_entity(report):
    """Registered under 24 months: from a company the entity; from a person the person's going companies. A new special-purpose company
    is the shape a development takes, and the reader asks what came before it."""
    if _other_start(report):
        return flag("young-entity", V, "blocked", "amber", _other_start(report))
    as_of = _as_of(report)
    if _company_start(report):
        s = report["subject"]
        start = _registered(s)
        if start is None:
            return flag("young-entity", V, "blocked", "amber", "the companies file states no registration day for the entity")
        days = (as_of - start).days
        if days < YOUNG_DAYS:
            return flag("young-entity", V, "fired", "amber", f"the entity was registered {_iso(start)}, {days} days before {_iso(as_of)} "
                        f"(under {YOUNG_DAYS} days): the project history section lists its directors' earlier companies",
                        citations=(s["ref"],), scope="subject")
        return flag("young-entity", V, "clear", "amber", f"the entity was registered {_iso(start)}, {days} days before {_iso(as_of)}",
                    sources_held=(COMPANIES_HELD,), scope="subject")
    p = _principals(report).get(report["subject"]["ref"]) or {"companies": {}}
    young = [c for c in p["companies"].values() if _ending(c) == "going" and _registered(c) and (as_of - _registered(c)).days < YOUNG_DAYS]
    if young:
        young.sort(key=lambda c: _registered(c), reverse=True)
        return flag("young-entity", V, "fired", "info", f"{len(young)} of the person's going companies were registered under {YOUNG_DAYS} days "
                    f"before {_iso(as_of)}: " + "; ".join(f"{_name(c)} ({_iso(_registered(c))})" for c in young[:EXAMPLES]),
                    citations=tuple(c["ref"] for c in young), scope="principals")
    return flag("young-entity", V, "clear", "info", f"none of the person's {len(p['companies'])} confirmed companies is a going company "
                f"registered under {YOUNG_DAYS} days", sources_held=(COMPANIES_HELD,), scope="principals")


def _people_on(report, company_ref: str) -> tuple:
    """(directors, holders) current on a company, as items; suppressed rows counted, never named."""
    ds, hs = [], []
    for it in all_items(report).values():
        if it["view"] not in ("directors", "shareholders"):
            continue
        if _company_of(it) != company_ref or not (it.get("row") or {}).get("in_latest", True) or (it.get("row") or {}).get("ended_on"):
            continue
        if it["view"] == "directors":
            ds.append(it)
        elif it["view"] == "shareholders":
            hs.append(it)
    return ds, hs


def _one_person(ds, hs) -> bool:
    return len(ds) == 1 and len(hs) == 1 and not ds[0].get("suppressed") and _fold(ds[0]["title"]) == _fold(hs[0]["title"])


def sole_vehicle(report):
    """One person the sole current director and the sole holder of record, as the file states it: a one-person vehicle's shape, read
    as a shape and nothing more. From a person, each of the person's companies of that shape."""
    if _other_start(report):
        return flag("sole-vehicle", V, "blocked", "info", _other_start(report))
    if _company_start(report):
        s = report["subject"]
        ds, hs = _people_on(report, s["ref"])
        if not ds:
            return flag("sole-vehicle", V, "blocked", "info", "the companies file lists no current director on the entity")
        if _one_person(ds, hs):
            return flag("sole-vehicle", V, "fired", "info", f"{ds[0]['title']} is the entity's sole director and its sole holder of record, "
                        f"as the file states it: a one-person vehicle's shape; a holder of record may hold for others, and for whom is in no "
                        f"register held", citations=(ds[0]["ref"], hs[0]["ref"]), scope="subject")
        return flag("sole-vehicle", V, "clear", "info", f"{len(ds)} current director(s) and {len(hs)} holder(s) of record on the entity",
                    sources_held=(COMPANIES_HELD,), scope="subject")
    p = _principals(report).get(report["subject"]["ref"]) or {"companies": {}}
    sole = [c for c in p["companies"].values() if _one_person(*_people_on(report, c["ref"]))]
    if sole:
        return flag("sole-vehicle", V, "fired", "info", f"{len(sole)} of the person's {len(p['companies'])} confirmed companies have one "
                    f"person as the sole director and the sole holder of record: " + "; ".join(f"{_name(c)} ({_status(c) or 'no status'}, "
                    f"registered {_iso(_registered(c))})" for c in sole[:EXAMPLES]), citations=tuple(c["ref"] for c in sole), scope="principals")
    return flag("sole-vehicle", V, "clear", "info", f"none of the person's {len(p['companies'])} confirmed companies has one person as its "
                "only director and holder", sources_held=(COMPANIES_HELD,), scope="principals")


# ── registered offices ──────────────────────────────────────────────────────

def _offices(report) -> dict:
    """{company ref: [(office key, address item, its start)]} for every registered-office row listed; the key is the folded first line
    and postcode, never printed."""
    out = {}
    for it in items(report, ("company_addresses",)):
        r = it["row"]
        if "regist" not in (r.get("kind") or "registered office").lower():
            continue
        key = (_fold(r.get("line_1")), _fold(r.get("postcode")))
        if key[0]:
            out.setdefault(_company_of(it), []).append((key, it, _date(r.get("started_on"))))
    return out


def _office_lines(office_item) -> str:
    r = office_item.get("row") or {}
    return " ".join(str(r.get(c) or "") for c in ("line_1", "line_2", "line_3", "care_of"))


def _professional(office_item) -> bool:
    return bool(PROFESSIONAL_OFFICE.search(_office_lines(office_item)) or _care_of(office_item))


def _care_of(office_item) -> bool:
    return bool(((office_item.get("row") or {}).get("care_of") or "").strip()) or bool(CARE_OF.search(_office_lines(office_item)))


def _office_hub(report, company_ref: str, office_item) -> bool:
    hubs = _hub_refs(report, OFFICE_HUBS)
    return company_ref in hubs or office_item["ref"] in hubs or any(f.get("kind") in OFFICE_HUBS for f in office_item.get("flags", [])) \
        or _professional(office_item)


def professional_office(report):
    """The entity's registered office carries an accountant's, a lawyer's or a formation agent's name, or fifty or more companies share
    it: a hub. A company met there shares an office and nothing more."""
    if not _company_start(report):
        return flag("professional-office", V, "blocked", "info", "read from a company start: the entity's own registered office"
                    if _person_start(report) else _other_start(report))
    s = report["subject"]
    mine = [it for _, it, _ in _offices(report).get(s["ref"], []) if it["row"].get("in_latest", True)]
    if not mine:
        return flag("professional-office", V, "blocked", "info", "the companies file lists no registered office on the entity in the latest file")
    prof = [it for it in mine if _professional(it)]
    w = _walk(report)
    busy = [it for it in mine if any(f.get("kind") in OFFICE_HUBS for f in it.get("flags", []))] or (
        [mine[0]] if (w.get("office_companies") or 0) >= (w.get("settings") or {}).get("busy_address", 50) else [])
    if prof or busy:
        why = []
        if any(PROFESSIONAL_OFFICE.search(_office_lines(it)) for it in prof):
            why.append("its lines name a professional firm (an accountant's, a lawyer's or a formation agent's office)")
        elif prof:
            why.append("the file states it is kept care of another (an accountant's, a lawyer's or an agent's office, as a rule)")
        if busy:
            why.append(f"{w.get('office_companies') or 'fifty or more'} companies share it")
        return flag("professional-office", V, "fired", "info", "the entity's registered office is a hub: " + " and ".join(why)
                    + "; a company met there shares an office and nothing more, and the office section lists none of them",
                    citations=tuple(it["ref"] for it in (prof or busy)), scope="office")
    return flag("professional-office", V, "clear", "info", "the entity's registered office names no professional firm and fewer than fifty "
                "companies share it", sources_held=(OFFICES_HELD,), scope="office")


def shared_office(report):
    """From a company: the companies at the entity's registered office in the latest file (the `office` reach) that failed, beside
    the entity's start; never through a hub. From a person: a failed company's office from before its failure that a going company
    of the person's has now, not a hub (a liquidated company's office is usually its liquidator's, so it is never compared after)."""
    if _other_start(report):
        return flag("shared-office", V, "blocked", "amber", _other_start(report), scope="office")
    if _company_start(report):
        s = report["subject"]
        w = _walk(report)
        mine = [it for _, it, _ in _offices(report).get(s["ref"], []) if it["row"].get("in_latest", True)]
        if mine and any(_office_hub(report, s["ref"], it) for it in mine):
            return flag("shared-office", V, "clear", "info", "the entity's registered office is a hub (see professional-office): the "
                        "companies at it are not compared", sources_held=(OFFICES_HELD,), scope="office")
        at = [it for it in items(report, ("companies",)) if it.get("rule") == "shared-office"]
        bad = [it for it in at if _ending(it) != "going"]
        if bad:
            bad.sort(key=lambda it: (_ending(it) != "insolvent", it["ref"]))
            return flag("shared-office", V, "fired", "amber", f"{len(bad)} of the {len(at)} other companies listed at the entity's registered "
                        f"office have failed or ended: " + "; ".join(f"{_name(it)} ({_status(it) or 'no status'}, registered {_iso(_registered(it))})"
                        for it in bad[:EXAMPLES]) + f"; the entity was registered {_iso(_registered(s))}; an office is not a person, and a "
                        f"shared office is no connection on its own; whether a failed company had this office before its failure is not read",
                        citations=tuple([it["ref"] for it in bad] + [m["ref"] for m in mine]), sources_not_held=(LIQUIDATOR_OFFICE, CHANGE_HISTORY),
                        scope="office")
        if not mine:
            return flag("shared-office", V, "blocked", "amber", "the companies file lists no registered office on the entity in the latest file",
                        scope="office")
        if (w.get("office_companies") or 0) - 1 > (w.get("office_listed") or 0):
            return flag("shared-office", V, "blocked", "amber", f"{(w.get('office_companies') or 0) - 1} other companies share the entity's "
                        f"registered office and {w.get('office_listed') or 0} were listed, none failed; the rest were not read", scope="office")
        return flag("shared-office", V, "clear", "amber", f"none of the {len(at)} other companies at the entity's registered office has failed "
                    "in the latest file", sources_held=(OFFICES_HELD, COMPANIES_HELD), sources_not_held=(LIQUIDATOR_OFFICE,), scope="office")
    p = _principals(report).get(report["subject"]["ref"]) or {"companies": {}}
    cos = list(p["companies"].values())
    failed = _failures(report, cos)
    going = [c for c in cos if _ending(c) == "going" and c["ref"] not in failed]
    offices = _offices(report)
    hits = []
    for f in failed.values():
        fref, fdate = f["company"]["ref"], f["date"]
        if fdate is None:
            continue
        before = {k: it for k, it, st in offices.get(fref, []) if st and st < fdate and not _office_hub(report, fref, it)}
        for g in going:
            now = [(k, it) for k, it, _ in offices.get(g["ref"], []) if it["row"].get("in_latest", True) and not _office_hub(report, g["ref"], it)]
            hit = next(((before[k], it) for k, it in now if k in before), None)
            if hit:
                hits.append((f, g, hit))
    if hits:
        return flag("shared-office", V, "fired", "amber", f"{len(hits)} pair(s) of the person's companies: a failed company's registered office "
                    "from before its failure is a going company's office now, not a hub: " + "; ".join(
                        f"{_name(f['company'])} ({_how(f)}) | {_name(g)} (registered {_iso(_registered(g))})" for f, g, _ in hits[:EXAMPLES])
                    + "; an office is not a person, and a shared office is no connection on its own",
                    citations=tuple(dict.fromkeys(r for f, g, (a, b) in hits for r in (f["company"]["ref"], g["ref"], a["ref"], b["ref"]))),
                    sources_not_held=(CHANGE_HISTORY,), scope="office")
    return flag("shared-office", V, "blocked", "amber", f"of the person's {len(cos)} companies, {len(failed)} failed and none had, before its "
                f"failure, an office a going one has now; but {LIQUIDATOR_OFFICE}, so a failed company's earlier office is seen only where the "
                f"file still holds it: no clear is given", sources_not_held=(CHANGE_HISTORY,), scope="office")


# ── mortgagee possessions ───────────────────────────────────────────────────

def _possessions(report):
    return list(items(report, ("gazette_possessions",)))


def _mortgagor_is(it, company_ref: str) -> bool:
    key = (it.get("row") or {}).get("mortgagor_register_key")
    return bool(key) and f"companies:{key}" == company_ref


def possession(report):
    """A mortgagee's entry into possession of a property the entity, or a principal's company, mortgaged, dated by the day of entry.
    Red on the entity's own or the person's own confirmed company; amber on a director's other company (near). Where the entity is
    the lender, info: a lender's enforcement is not the developer's default."""
    if _other_start(report):
        return flag("possession", V, "blocked", "red", _other_start(report), sources_not_held=(PERSON_MORTGAGORS, SECURITIES, LINZ))
    s = report["subject"]
    ps = _possessions(report)
    principals = _principals(report)
    on_principal = {c for p in _own_principals(principals).values() for c in p["companies"]}
    on_namesake = {c for p in _namesakes(principals).values() for c in p["companies"]} - on_principal - {s["ref"]}
    as_borrower = [it for it in ps if any(_mortgagor_is(it, c) for c in on_principal | {s["ref"]})]
    as_namesake = [it for it in ps if it not in as_borrower and any(_mortgagor_is(it, c) for c in on_namesake)]
    as_lender = [it for it in ps if it not in as_borrower and it not in as_namesake]
    if as_namesake and not as_borrower:
        return flag("possession", V, "fired", "amber", f"{len(as_namesake)} mortgagee entry(ies) into possession where the mortgagor is a "
                    "company a director's near link reaches (a namesake's until a rule confirms it, never a principal's): "
                    + "; ".join(f"{_name(it)} on the mortgagor {_mortgagor_name(report, it)}, {it['dates']['text']}" for it in as_namesake[:EXAMPLES])
                    + "; the property and a person mortgagor's name are not shown", citations=tuple(it["ref"] for it in as_namesake),
                    sources_not_held=(PERSON_MORTGAGORS, SECURITIES, LINZ), scope="near")
    if as_borrower:
        own = [it for it in as_borrower if _mortgagor_is(it, s["ref"]) or (it["grade"] == "confirmed" and _person_start(report))]
        sev = "red" if own else "amber"
        rows = (own or as_borrower)[:EXAMPLES]
        text = "; ".join(f"{_name(it)} on the mortgagor {_mortgagor_name(report, it)}, {it['dates']['text']}" for it in rows)
        whose = ("the mortgagor is the entity itself" if any(_mortgagor_is(it, s["ref"]) for it in own) else
                 "the mortgagor is one of the person's own confirmed companies" if own else
                 "the mortgagor is a director's other company (near: the director's connection, not the entity's)")
        apart = (f"; apart, {len(as_namesake)} where the mortgagor is a company a director's near link reaches (a namesake's)"
                 if as_namesake else "")
        return flag("possession", V, "fired", sev, f"{len(as_borrower)} mortgagee entry(ies) into possession where {whose}: {text}{apart}; "
                    "the property and a person mortgagor's name are not shown", citations=tuple(it["ref"] for it in as_borrower + as_namesake),
                    sources_not_held=(PERSON_MORTGAGORS, SECURITIES, LINZ), scope="principals")
    if as_lender:
        return flag("possession", V, "fired", "info", f"{len(as_lender)} mortgagee entry(ies) into possession where a company here is the "
                    f"lender, not the mortgagor: " + "; ".join(f"{_name(it)}, {it['dates']['text']}" for it in as_lender[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in as_lender), sources_not_held=(PERSON_MORTGAGORS,), scope="principals")
    short = _reach_short(report)
    if short:
        return flag("possession", V, "blocked", "red", f"the walk could not read every principal's companies ({short})",
                    sources_not_held=(PERSON_MORTGAGORS, SECURITIES, LINZ), scope="principals")
    return _clear_or_past("possession", "red", f"no mortgagee entry into possession names the entity or any of the {len(on_principal)} "
                          "principal company row(s) reached as the mortgagor", sources_held=(POSSESSIONS_HELD,),
                          sources_not_held=(PERSON_MORTGAGORS, SECURITIES, LINZ), scope="principals")


def _mortgagor_name(report, it) -> str:
    key = (it.get("row") or {}).get("mortgagor_register_key")
    c = all_items(report).get(f"companies:{key}") if key else None
    return _name(c) if c else "a company cited"


# ── the people ──────────────────────────────────────────────────────────────

def _people_guard(report):
    """Why a people check cannot clear, or None."""
    if _other_start(report):
        return _other_start(report)
    w = _walk(report)
    if not w.get("links_built"):
        return "no links are published, so no notice can be joined to a person"
    if w.get("links_omitted"):
        return f"{w['links_omitted']} link(s) past the walk's limit were not read"
    if _company_start(report):
        if not _own_people(report):
            return "the companies file lists no current director on the entity; the holders of record are not followed"
        if w.get("officers_omitted"):
            return f"{w['officers_omitted']} director(s) past the walk's limit were not followed"
    return None


def _in_force(it, as_of) -> bool:
    end = _date((it.get("row") or {}).get("ends_on"))
    return end is None or end >= as_of


def _people_rule(report, rule, view, what):
    rows = list(items(report, (view,)))
    conf = [it for it in rows if it["grade"] == "confirmed"]
    if rows:
        as_of = _as_of(report)
        live = [it for it in rows if view != "gazette_prohibitions" or _in_force(it, as_of)]
        red = [it for it in conf if _person_start(report) and (view != "gazette_prohibitions" or _in_force(it, as_of))]
        sev = "red" if red else "amber" if live else "info"
        linked = [it for it in rows if it.get("near_link")]
        whose = ("on the person's own confirmed record" if red else
                 "reached through a director's near link (the link rules join the row to the director by name alone: a namesake's until "
                 "confirmed)" if linked and len(linked) == len(rows) else
                 "on a director of the entity, reached through the director's row (near: start a report from the director)"
                 + (f"; {len(linked)} of them through a director's near link, a namesake's until confirmed" if linked else "")
                 if _company_start(report) else "reached only by a shared name (near: a namesake's, until confirmed)")
        pick = (red or live or rows)[:EXAMPLES]
        return flag(rule, V, "fired", sev, f"{len(rows)} {what}(s), {whose}: " + "; ".join(
            f"{'a name suppressed' if it.get('suppressed') else it['title']}, {it['dates']['text']}" for it in pick)
                    + ("" if live else "; every one has ended"), citations=tuple(it["ref"] for it in rows),
                    sources_not_held=(INSOLVENCY_REGISTER,) if view == "gazette_bankruptcies" else (), scope="people")
    why = _people_guard(report)
    if why:
        return flag(rule, V, "blocked", "red", why, sources_not_held=(INSOLVENCY_REGISTER,) if view == "gazette_bankruptcies" else (), scope="people")
    who = f"any of the entity's {len(_own_people(report))} director(s)" if _company_start(report) else "the person"
    return flag(rule, V, "clear", "red", f"no {what} is joined to {who} by the link rules", sources_held=(PEOPLE_HELD,),
                sources_not_held=(INSOLVENCY_REGISTER,) if view == "gazette_bankruptcies" else (), scope="people")


def prohibition(report):
    """A director prohibition on the person, or on a director of the entity; red in force on the person's own record, amber through a
    director or a shared name, info once ended. A revoked prohibition is never shown (the shape withholds it)."""
    return _people_rule(report, "prohibition", "gazette_prohibitions", "director prohibition")


def bankruptcy(report):
    """A Gazette bankruptcy notice on the person, or on a director of the entity; an annulled one is withheld by the shape. The
    Insolvency Register, which holds discharges and no-asset procedures, is not held."""
    return _people_rule(report, "bankruptcy", "gazette_bankruptcies", "bankruptcy notice")


# ── the Gazette ─────────────────────────────────────────────────────────────

def insolvency_notices(report):
    """The Gazette's insolvency notices (liquidations, receiverships, administrations, winding-up applications, creditors' notices,
    deeds of company arrangement) on the entity, and on the principals' companies, counted by kind."""
    if _other_start(report):
        return flag("insolvency-notices", V, "blocked", "red", _other_start(report), sources_not_held=(INSOLVENCY_REGISTER,))
    s = report["subject"]
    ins = [n for n in _notices(report) if _insolvency(n)]
    own = [n for n in ins if _company_of(n) == s["ref"]]
    principals = _principals(report)
    theirs = {c for p in _own_principals(principals).values() for c in p["companies"] if c != s["ref"]}
    other = [n for n in ins if _company_of(n) in theirs]
    namesake = {c for p in _namesakes(principals).values() for c in p["companies"]} - theirs - {s["ref"]}
    apart = [n for n in ins if _company_of(n) in namesake]
    up = [n for n in ins if n.get("above") and n not in own + other + apart]
    beside = ((f"; apart, {len(apart)} on {len({_company_of(n) for n in apart})} company(ies) a director's near link reaches "
               f"({_counted(apart, _kind)}): a namesake's until a rule confirms it, never a principal's") if apart else "") + \
        ((f"; beside them, {len(up)} on a company above in the holding chain ({_counted(up, _kind)}): the holder's, not the entity's")
         if up else "")
    if own or other:
        conf = [n for n in other if n["grade"] == "confirmed"]
        sev = "red" if own or (conf and _person_start(report)) else "amber"
        bits = []
        if own:
            bits.append(f"{len(own)} on the entity ({_counted(own, _kind)})")
        if other:
            bits.append(f"{len(other)} on {len({_company_of(n) for n in other})} of the principals' other companies ({_counted(other, _kind)})"
                        + ("" if _person_start(report) else ", reached through the directors (near)"))
        return flag("insolvency-notices", V, "fired", sev, "Gazette insolvency notices: " + "; ".join(bits) + beside + "; each is listed with "
                    "its own date, which says what it dates", citations=tuple(n["ref"] for n in own + other + apart + up),
                    sources_not_held=(INSOLVENCY_REGISTER,), scope="principals")
    if apart or up:   # only a namesake's or a holder's: listed, amber at most, and no clear while they stand
        return flag("insolvency-notices", V, "fired", "amber" if apart else "info", "no Gazette insolvency notice on the entity or on the "
                    f"{len(theirs)} principal company row(s) reached" + beside, citations=tuple(n["ref"] for n in apart + up),
                    sources_not_held=(INSOLVENCY_REGISTER,), scope="near")
    short = _reach_short(report)
    if short:
        return flag("insolvency-notices", V, "blocked", "red", f"the walk could not read every principal's companies ({short})",
                    sources_not_held=(INSOLVENCY_REGISTER,), scope="principals")
    return _clear_or_past("insolvency-notices", "red", f"no Gazette insolvency notice on the entity or on the {len(theirs)} principal company "
                          "row(s) reached", sources_held=(GAZETTE_HELD,), sources_not_held=(INSOLVENCY_REGISTER,), scope="principals")


# ── reach ───────────────────────────────────────────────────────────────────

def holding_chain(report):
    """The companies above the entity in the holding chain, and where the chain is cut or a holder could not be followed."""
    if not _company_start(report):
        return flag("holding-chain", V, "blocked", "info", "the holding chain is read from a company start: start a report from each company "
                    "listed" if _person_start(report) else _other_start(report))
    w = _walk(report)
    above = [it for it in items(report, ("companies",)) if it.get("rule") == "chain" or (it.get("depth") and it.get("hop_text"))]
    notes = w.get("chain_notes") or []
    st = w.get("chain") or {}
    if notes or st.get("cut"):
        return flag("holding-chain", V, "blocked", "info", f"{len(above)} company(ies) above the entity were reached; {len(notes)} holder(s) "
                    f"could not be followed (a name several companies carry or none: an overseas company, a trust or a body of another kind)"
                    + (f"; the chain goes on past {w.get('chain_depth')} up" if st.get("cut") else "") + f"; {NOT_FOLLOWED_HOLDERS}",
                    sources_not_held=("overseas company registers", "trusts: no New Zealand register exists"), scope="chain")
    if above:
        return flag("holding-chain", V, "fired", "info", f"{len(above)} company(ies) hold shares of record above the entity, up to "
                    f"{st.get('depth') or 1} up: " + "; ".join(f"{_name(it)} ({it.get('hop_text') or 'a holder of record'})" for it in above[:EXAMPLES])
                    + f"; a holder of record is shown as the register states it; on the companies above, {st.get('above_directors', 0)} current "
                    f"director(s) and {st.get('above_notices', 0)} Gazette notice(s) are listed with each company's grade, the holder's and "
                    "not the entity's", citations=tuple(it["ref"] for it in above), scope="chain")
    return flag("holding-chain", V, "clear", "info", "no company holds shares of record in the entity: its holders of record are people",
                sources_held=(COMPANIES_HELD,), scope="chain")


def history_reach(report):
    """How many of the entity's directors reached any other company. A director whose other rows the links lane joins only near (a
    name with no middle name, say) is not followed by the officers reach, so an empty project history is not a clean one."""
    if _other_start(report):
        return flag("history-reach", V, "blocked", "amber", _other_start(report), scope="principals")
    w = _walk(report)
    if _person_start(report):
        size = (report.get("group") or {}).get("size", 1)
        p = _principals(report).get(report["subject"]["ref"]) or {"companies": {}}
        if size <= 1 or len(p["companies"]) <= 1:
            return flag("history-reach", V, "blocked", "amber", f"the person's group of {size} row(s) reaches {len(p['companies'])} confirmed "
                        "company: no confirmed link joins the person's row to a role on any other company (a name the links lane joins only "
                        "near is listed near, as a namesake's, and is not the person's record), so the project history may be the one "
                        "company the row sits on", scope="principals")
        return flag("history-reach", V, "fired", "info", f"the person's group of {size} rows reaches {len(p['companies'])} confirmed "
                    "company(ies)", citations=tuple(p["companies"]) or (report["subject"]["ref"],), scope="principals")
    ds = _own_people(report)
    if not ds:
        return flag("history-reach", V, "blocked", "amber", "the companies file lists no current director on the entity", scope="principals")
    principals = _principals(report)
    ns = _namesakes(principals)
    empty = [p for k, p in _own_principals(principals).items() if len(p["companies"]) <= 1 and k + NAMESAKE_KEY not in ns]
    only_near = [p for k, p in _own_principals(principals).items() if len(p["companies"]) <= 1 and k + NAMESAKE_KEY in ns]
    m = len({c for p in ns.values() for c in p["companies"]})
    apart = (f"; apart, {m} company(ies) a director's near link reaches ({len(only_near)} director(s) reached other companies only so): a "
             "namesake's until a rule confirms it, never the director's own") if ns else ""
    bits = []
    if empty:
        bits.append(f"{len(empty)} of the {len(ds)} director(s) reached no other company ("
                    + "; ".join(p["title"] for p in empty[:EXAMPLES]) + "): either none is current, or no link, confirmed or near, joins the "
                    "director's row to another company's; start a report from each")
    if w.get("officers_omitted"):
        bits.append(f"{w['officers_omitted']} director(s) past the first {w.get('limits', {}).get('officers', 12)} were not followed")
    om = sum(s.get("omitted") or 0 for s in report.get("sections", []) if s["name"] in ("history", "serial"))
    if om:
        bits.append(f"{om} row(s) past the walk's limit were not listed")
    n = len({c for p in _own_principals(principals).values() for c in p["companies"] if c != report["subject"]["ref"]})
    if bits:
        return flag("history-reach", V, "blocked", "amber", f"{w.get('officers_followed', 0)} director(s) followed, {n} other company(ies) "
                    "reached; " + "; ".join(bits) + apart, scope="principals")
    return flag("history-reach", V, "fired", "info", f"each of the {len(ds)} director(s) was followed: {n} other company(ies) reached" + apart,
                citations=tuple(d["ref"] for d in ds), scope="principals")


def namesake_exposure(report):
    near = [it for it in section(report, "identity")["items"] if it["grade"] == "near"]
    if len(near) >= NAMESAKE_NOTE_AT:
        return flag("namesake-exposure", V, "fired", "info", f"{len(near)} rows share the subject's name and no rule confirms them: each is "
                    "set apart as a namesake, and nothing in them is the subject's", citations=tuple(it["ref"] for it in near), scope="near")
    return flag("namesake-exposure", V, "clear", "info", f"{len(near)} namesake(s) set apart", sources_held=("pub.links",), scope="near")


# ── not held: blocked, never clear ──────────────────────────────────────────

def _not_held(rule, severity, register, what):
    def check(report):
        return flag(rule, V, "blocked", severity, f"not held: {register}; {what} cannot be read here, and no such finding here is a finding of none",
                    sources_not_held=(register,), scope="not-held")
    check.__name__ = rule.replace("-", "_")
    check.__doc__ = f"Blocked, never clear: {register} is not held."
    return check


land_titles = _not_held("land-titles", "amber", LINZ, "what land the entity or its principals' companies hold, and the company side of each title")
overseas_investment = _not_held("overseas-investment", "info", OIO, "whether the developer or a vendor to it applied for or was granted consent")
building_consents = _not_held("building-consents", "amber", CONSENTS, "what the project was consented to build, and whether it was signed off")
court_judgments = _not_held("court-judgments", "amber", "court judgments (the OpenLaw case-law lane and the courts register, step 5.4)",
                            "a body corporate's, a buyer's or a council's claim against the developer, a weathertightness case")
securities_register = _not_held("securities-register", "amber", SECURITIES, "the security interests registered against the entity")
insolvency_register = _not_held("insolvency-register", "amber", INSOLVENCY_REGISTER, "a principal's bankruptcy discharge, no-asset procedure or summary instalment order")
real_estate_authority = _not_held("real-estate-authority", "info", REA, "a complaint or a disciplinary finding on a licensee selling the project")
building_practitioners = _not_held("building-practitioners", "info", "the licensed building practitioners register", "whether the builder's people hold a licence")
past_roles = _not_held("past-roles", "amber", CHANGE_HISTORY, f"a principal's past roles and the companies removed with them ({PAST_NOT_HELD})")


RULES = (serial_pattern, earlier_failure, entity_status, young_entity, sole_vehicle, professional_office, shared_office, possession,
         prohibition, bankruptcy, insolvency_notices, holding_chain, history_reach, namesake_exposure,
         land_titles, overseas_investment, building_consents, court_judgments, securities_register, insolvency_register,
         real_estate_authority, building_practitioners, past_roles)
