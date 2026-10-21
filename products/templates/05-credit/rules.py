"""The business credit and monitoring rules (plan 5.2, use case 5). Pure
functions over the built report, each returning one flag. A trade credit
team asks "has anything changed for the companies I am exposed to, and what
stands against this one today". The rules stand for the old estate's
company and person rules (data-layer/flags/flags/entity_rules.py,
entity-0.1: entity-status, group-receivership, young-entity;
person_rules.py, person-0.2: liquidation-history, prohibition,
namesake-exposure) and use case 5's checklist, taken as ideas and tests, not
code, where the held registers can support them:

  entity-status          the company's status, type and age, and the latest monthly file it is in
  monthly-changes        every director, holder and registered office that arrived or left between the monthly files held, each
                         dated by the file that first shows it, newest first, the grain stated; status and name changes blocked
  recent-adverse-change  a Gazette insolvency or removal notice in the last RECENT_DAYS, the entity leaving the file, a director
                         leaving in the latest file, an office moved to a busy address in it
  officer-churn          directors arriving and leaving between the files, and appointed in the last CHURN_DAYS as filed
  insolvency-notices     Gazette liquidations, receiverships, administrations, winding-up applications, creditors' notices and
                         deeds of company arrangement, on the entity or the person's companies
  register-events        removals, restorations, dissolutions, rectifications, amalgamations: not insolvency
  officers-of-record     a going company the latest file names no current director of
  young-entity           registered under 24 months
  people-failed-companies  the person's other companies that failed (an insolvency status or notice); blocked from a company
  other-current-companies  the person's going companies and their states; blocked from a company
  prohibition, bankruptcy  on the person, confirmed or near; blocked from a company
  subject-hub            the person is a professional director, a nominee or the Crown
  namesake-exposure      the report's own uncertainty
  walk-coverage          how many companies reached had their notices and officers read
  status-name-changes    blocked: published in pub.company_states, which the report's catalogue does not know
  since-date             blocked: the shape takes no "since" date; every change is listed, dated
  interface-freshness    blocked: the business-number interface check of step 5.5 is not built
  past-roles, change-history  blocked: current roles only; the change history is not held before 16 August 2026
  securities-register, insolvency-register, court-judgments, credit-bureau, mortgagee-possession
                         blocked: not held, or published and not reachable

The builder adds its common rules for every template (group-standing,
hubs-met, replaced-return); this file carries no copy of them.

Every rule branches on the start: a person, a company, or anything else.
From a company the walk lists the officers and holders and does not follow
them (the agriculture lesson), so a check through a person is blocked and
says to start a report from each person. Evidence on confirmed rows is red
or amber; the same evidence reached only through a near link is amber at
most and says it is a namesake's until confirmed. A check the registers
cannot see is blocked, never clear: a change check never clears while the
status and name changes between files are unreachable. Dates sit side by
side; no flag joins two facts with a word of cause, none calls a holder an
owner, none prints an address (the changes section shows the office), and
a suppressed name is never quoted.

Imports nothing of products.report: the one-way test holds a template folder
to its own code. The shape loads this file by path and binds the name
`contract` (products/report/contract.py) before it runs."""
from __future__ import annotations

import datetime as dt
import re

V = "0.1"
RECENT_DAYS = 90          # a Gazette notice published this many days before the report's date is recent (a setting)
CHURN_DAYS = 365          # a current director appointed this many days before the report's date, as filed, counts as an arrival
CHURN_AMBER = 3           # arrivals and departures together at which officer churn is amber
YOUNG_DAYS = 730          # under 24 months registered (the old young-entity rule)
NAMESAKE_NOTE_AT = 5      # namesakes set apart at which the report's caveat fires
NAMESAKE_PARTIAL_AT = 50  # past this many namesakes the report is declared partial
EXAMPLES = 3              # dated examples a fired flag states in its text
CHANGES_SHOWN = 12        # changes the monthly-changes flag states in its text; the rest are in the changes section
#: whether a published view holds past roles with their end dates. It does not (measured 2026-10-20 by banking-1): the companies file
#: lists current roles only. While False, a check over a person's companies fires on what it sees and never clears.
HISTORY = False
#: whether the report can reach a status or name change between files. pub.company_states holds them (5,629 earlier states in the July
#: file, measured 2026-10-21) and the report's catalogue does not know the view. While False, no change check clears.
STATES = False
#: the monthly files the companies lane holds, measured 2026-10-21 (pub.directors first_file and last_file): a report's own rows cannot
#: say which files exist (a company new in the later file has no row in the earlier one; a removed one none in the later), so these are
#: added to the files its rows name; a file loaded later is picked up from the rows. The lane publishes no list of its files (carded).
FILES_MEASURED = ("companies-2026-07", "companies-2026-08")
FOUNDING_DAYS = 31        # a director appointed within this many days of the company's registration founded it: not churn
PROHIBITION_RED_ENDED = False   # a prohibition that ended before the report's date is amber, one in force red
BANKRUPTCY_RECENT_DAYS = 5 * 365   # a bankruptcy notice older than this is amber: most are discharged after three years, and the
#:                                   discharge is in the Insolvency Register, which is not held
PAST_NOT_HELD = ("the companies file lists current roles only: a company the person left, or that was struck off with them on it, is not "
                 "seen, nor its failure")

#: the company notices that are an insolvency; a receiver's ceasing to act ends one and dates nothing
INSOLVENCY_KINDS = ("winding-up application", "receivership", "administration", "notice to creditors", "deed of company arrangement")
EVENT_KIND = {"removal": "removal", "dissolution": "dissolution", "restoration": "restoration", "overseas company": "an overseas company ceasing",
              "rectification": "the Registrar's rectification", "transfer out": "a transfer out of New Zealand", "amalgamation": "amalgamation"}
INSOLVENT_STATUS = re.compile(r"liquidation|receiv|administration|statutory management", re.I)
ENDED_STATUS = re.compile(r"^(removed|deregistered|dissolved|closed|cancelled|inactive|suspended)$", re.I)
GOING_STATUS = re.compile(r"^registered$", re.I)
FILE = re.compile(r"^companies-(\d{4})-(\d{2})$")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
HUB_KINDS = ("professional-director", "nominee", "crown")
OFFICE_HUBS = ("busy-address", "thousand-address")
PEOPLE = ("directors", "shareholders")
CHANGE_VIEWS = ("directors", "shareholders", "company_addresses")
#: the words a fired flag must not carry, the shape's own (rules 3 and 4): a register's name that holds one is not quoted in a flag
UNSAFE = re.compile(contract.CAUSE.pattern + "|" + contract.OWNER.pattern, re.I)   # noqa: F821  (bound by the loader)

GAZETTE_HELD = "New Zealand Gazette liquidation and company notices (pub.gazette_liquidations, pub.gazette_company_notices)"
NOTICES_HELD = "New Zealand Gazette company notices (pub.gazette_company_notices)"
COMPANIES_HELD = "Companies register (pub.companies, pub.directors, pub.shareholders)"
FILES_HELD = "Companies register monthly files (pub.directors, pub.shareholders, pub.company_addresses: the files each row is in)"
INSOLVENCY_REGISTER = "the Official Assignee's Insolvency Register (interface awaited since 19 September 2026)"
NOT_HELD_INSOLVENCY = (INSOLVENCY_REGISTER, "court judgments (step 5.4)")
SECURITIES = "the Personal Property Securities Register (interface awaited since 19 September 2026)"
STATES_NOT_REACHED = ("a status or name change between the monthly files (pub.company_states: published, not in the report's catalogue)")
INTERFACE = "the business-number interface's state on the day of the lookup (plan step 5.5, not built)"
CHANGE_HISTORY = "the companies change history: not held before 16 August 2026, held and unread since (former names, trading names, earlier directors)"
CREDIT_BUREAU = "credit-bureau defaults and payment records (no lane; not a public register)"
COURTS = ("court judgments: the OpenLaw case-law lane and the courts register (step 5.4)",)
POSSESSIONS = ("a mortgagee's entry into possession (pub.gazette_possessions: published, not in the report's catalogue)",)
CHARITIES_NOT_HELD = ("the Charities Register and its officers (not yet published)",)
NOT_FOLLOWED = ("started from a company, the report lists its officers and holders of record but does not follow them to their own links "
                "and companies yet; start a report from each person listed")
GRAIN = "the grain is the monthly file: a change is dated to the file that first shows it, a month and not a day"


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
    """A row's title for a flag's text: a suppressed name is never quoted, and a register name that carries a word the shape reads
    as cause or ownership is not quoted either (the section lists it)."""
    if it.get("suppressed"):
        return f"a row whose name is suppressed ({it['ref']})"
    t = " ".join((it.get("title") or it["ref"]).split())
    return f"the row cited ({it['ref']})" if UNSAFE.search(t) else t


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
    """A liquidator's appointment, or a company notice of an insolvency kind that is not a receiver ceasing to act."""
    if it["view"] == "gazette_liquidations":
        return True
    r = it["row"]
    return it["view"] == "gazette_company_notices" and r.get("kind") in INSOLVENCY_KINDS and "ceas" not in (r.get("action") or "").lower()


def _restoration(it) -> bool:
    action = (it["row"].get("action") or "").lower()
    return "restor" in action or "revocation" in action


def _removal(it) -> bool:
    return it["view"] == "gazette_company_notices" and it["row"].get("kind") == "removal" and not _restoration(it)


def _event(it) -> bool:
    return it["view"] == "gazette_company_notices" and not _insolvency(it) and (it["row"].get("kind") or "") not in INSOLVENCY_KINDS


def _event_kind(it) -> str:
    if _restoration(it):
        return "restoration"
    kind = it["row"].get("kind") or ""
    return EVENT_KIND.get(kind, kind or "notice")


def _published(it):
    r = it["row"]
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


def _fold(name: str) -> str:
    return " ".join((name or "").lower().translate(str.maketrans("āēīōū", "aeiou")).split())


def _clear_or(flagged: bool, rule, severity, text, why_not, **kw):
    """A clear, or, while a register the check needs cannot be seen, a blocked flag saying what was seen and what cannot be."""
    if flagged:
        return flag(rule, V, "clear", severity, text, **kw)
    kw.pop("sources_held", None)
    return flag(rule, V, "blocked", severity, f"{text}; but {why_not}: no clear is given", **kw)


def _counted(xs, label) -> str:
    counts = {}
    for it in xs:
        counts[label(it)] = counts.get(label(it), 0) + 1
    return ", ".join(f"{n} {k}" for k, n in sorted(counts.items()))


def _age(as_of, reg) -> str:
    days = (as_of - reg).days
    return f"{days // 365} year(s)" if days >= 365 else f"{days // 30} month(s)"


def _subject_hub(report) -> list:
    own = {report["subject"]["ref"]} | {m["ref"] for m in report.get("members", [])}
    return [h for h in report.get("hubs", []) if h["ref"] in own and h["kind"] in HUB_KINDS]


# ── the monthly files ───────────────────────────────────────────────────────

def _month(file) -> str:
    """'companies-2026-08' -> 'the August 2026 file'."""
    m = FILE.match(file or "")
    return f"the {MONTHS[int(m.group(2)) - 1]} {m.group(1)} file" if m else f"the file {file or 'not stated'}"


def _files(report) -> list:
    """The monthly files held, oldest first: those measured and those the report's rows name. A file name sorts by its date."""
    out = set(FILES_MEASURED)
    for it in all_items(report).values():
        r = it.get("row") or {}
        for c in ("first_file", "last_file"):
            if FILE.match(r.get(c) or ""):
                out.add(r[c])
    return sorted(out)


def _in_scope(report) -> set:
    """The companies whose changes the report lists: the entity, or the companies the person has a confirmed row on."""
    if _company_start(report):
        return {report["subject"]["ref"]}
    return {it["ref"] for it in _companies(report)}


def _role_word(it) -> str:
    if it["view"] == "directors":
        return (it["row"].get("role_type") or "director").lower()
    return "holder of record"


def _changes(report) -> list:
    """[(file, order, text, citations)] for each change between the files held on the companies in scope: a director or holder that
    arrived (first shown in a later file) or left (last shown in an earlier one), a holding or a role whose filed details changed (one
    row leaving and one arriving under the same name), a registered office that moved, the company itself first shown or gone.
    Newest file first. A change is never dated finer than its file; the register's own day is printed beside where it files one."""
    files = _files(report)
    if len(files) < 2:
        return []
    first, latest = files[0], files[-1]
    scope = _in_scope(report)
    rows = [it for it in all_items(report).values() if it["view"] in CHANGE_VIEWS and _company_of(it) in scope]
    arrived = [it for it in rows if it["view"] in PEOPLE and (it["row"].get("first_file") or first) > first]
    left = [it for it in rows if it["view"] in PEOPLE and not it["row"].get("in_latest", True) and (it["row"].get("last_file") or latest) < latest]
    out = []
    # a holding whose shares changed, or a role whose filed details changed, is one row leaving and one arriving under the same name
    paired = set()
    for a in arrived:
        if a.get("suppressed"):
            continue
        for b in left:
            if b["ref"] in paired or b["view"] != a["view"] or _company_of(b) != _company_of(a) or b.get("suppressed"):
                continue
            if _fold(a["title"]) == _fold(b["title"]):
                paired |= {a["ref"], b["ref"]}
                if a["view"] == "shareholders":
                    what = (f"{_name(a)}'s holding of record changed: {b['row'].get('shares')} shares in {_month(b['row'].get('last_file'))}, "
                            f"{a['row'].get('shares')} in {_month(a['row'].get('first_file'))}")
                else:
                    what = f"{_name(a)}'s filed details as {_role_word(a)} changed between {_month(b['row'].get('last_file'))} and {_month(a['row'].get('first_file'))}"
                out.append((a["row"].get("first_file"), 2, what, (b["ref"], a["ref"])))
                break
    for it in arrived:
        if it["ref"] in paired:
            continue
        f = it["row"].get("first_file")
        filed = _date(it["row"].get("appointed_on"))
        out.append((f, 0, f"{_name(it)} arrived as {_role_word(it)}: first shown in {_month(f)}"
                    + (f" (appointed {filed.isoformat()}, as the register files it)" if filed else ""), (it["ref"],)))
    for it in left:
        if it["ref"] in paired:
            continue
        last = it["row"].get("last_file")
        nxt = next((x for x in files if x > last), latest)
        out.append((nxt, 1, f"{_name(it)} left as {_role_word(it)}: last shown in {_month(last)}, not in {_month(nxt)}; the file states no end",
                    (it["ref"],)))
    # a registered office that moved: an office last shown in an earlier file beside the office in the latest file
    offices = {}
    for it in rows:
        if it["view"] == "company_addresses":
            offices.setdefault(_company_of(it), []).append(it)
    for c, xs in offices.items():
        gone = [it for it in xs if not it["row"].get("in_latest", True) and (it["row"].get("last_file") or latest) < latest]
        now = [it for it in xs if it["row"].get("in_latest", True)]
        for g in gone:
            last = g["row"].get("last_file")
            nxt = next((x for x in files if x > last), latest)
            new = sorted(now, key=lambda it: str(it["row"].get("started_on") or ""), reverse=True)[:1]
            hub = [f for it in new for f in it.get("flags", []) if f.get("kind") in OFFICE_HUBS]
            text = (f"the registered office of {_name(_co(report, c))} moved: the earlier office last shown in {_month(last)}; the office in "
                    f"{_month(nxt)}" + (f" filed as from {_iso(_date(new[0]['row'].get('started_on')))}" if new else " not listed")
                    + (f", an office {hub[0]['evidence']['companies']:,} companies share" if hub and isinstance(hub[0].get("evidence"), dict) else "")
                    + "; both are in the changes section")
            out.append((nxt, 3, text, tuple([g["ref"]] + [it["ref"] for it in new])))
    # the company itself: first shown in a later file, or gone from the latest
    for c in scope:
        co = _co(report, c)
        if not co or co.get("view") != "companies":
            continue
        r = co["row"]
        if (r.get("first_file") or first) > first:
            reg = _date(r.get("registered_on"))
            out.append((r["first_file"], 4, f"{_name(co)} first shown in {_month(r['first_file'])}" + (f" (registered {reg.isoformat()}, as filed)" if reg else ""),
                        (co["ref"],)))
        if not r.get("in_latest", True) and (r.get("last_file") or latest) < latest:
            nxt = next((x for x in files if x > r["last_file"]), latest)
            out.append((nxt, 5, f"{_name(co)} is not in {_month(nxt)}: last shown in {_month(r['last_file'])}", (co["ref"],)))
    out.sort(key=lambda x: (x[0] or "", -x[1]), reverse=True)
    return out


def _co(report, ref):
    if ref == report["subject"]["ref"]:
        return report["subject"]
    return all_items(report).get(ref) or {"ref": ref, "title": ref, "view": "", "row": {}}


# ── the entity's standing ───────────────────────────────────────────────────

def entity_status(report):
    """Status, type, age and the latest file the entity appears in."""
    if _other_start(report):
        return flag("entity-status", V, "blocked", "red", _other_start(report), scope="entity")
    if not _company_start(report):
        return flag("entity-status", V, "blocked", "info", "the start is a person: how each of the person's companies stands is in the standing "
                    "section and the flags other-current-companies and people-failed-companies; start a report from a company for its standing",
                    scope="entity")
    s = report["subject"]
    r = s["row"]
    status, kind = _status(s) or "not stated", r.get("entity_type") or "entity"
    reg, removed = _date(r.get("registered_on")), _date(r.get("removed_on"))
    age = f", {_age(_as_of(report), reg)} before {_as_of(report).isoformat()}" if reg else ""
    when = (f"registered {reg.isoformat()}{age}" if reg else "registration date not stated") + (f", removed {removed.isoformat()}" if removed else "")
    latest = _files(report)[-1:] or [None]
    seen = r.get("last_file")
    in_file = (f"last shown in {_month(seen)}" + ("" if r.get("in_latest", True) else ", not in the latest file")) if seen else "the file it is in is not stated"
    text = f"status {status!r} ({kind}; {when}); {in_file}; the latest file held is {_month(latest[0]) if latest[0] else 'not stated'}"
    if _ending(s) == "insolvent":
        return flag("entity-status", V, "fired", "red", f"the companies file gives the entity the status {status!r}: {text}",
                    citations=(s["ref"],), sources_not_held=NOT_HELD_INSOLVENCY + (INTERFACE,), scope="entity")
    if _ending(s) == "ended":
        return flag("entity-status", V, "fired", "red", f"the entity is no longer a registered company: {text}", citations=(s["ref"],),
                    sources_not_held=(INTERFACE,), scope="entity")
    if not r.get("in_latest", True):
        return flag("entity-status", V, "fired", "amber", f"the entity is not in the latest companies file: {text}; the interface check of step 5.5 "
                    "would date the change", citations=(s["ref"],), sources_not_held=(INTERFACE,), scope="entity")
    return flag("entity-status", V, "clear", "red", f"registered in the latest companies file: {text}",
                sources_held=("Companies register status (pub.companies)",), sources_not_held=(INTERFACE,), scope="entity")


# ── what changed ────────────────────────────────────────────────────────────

def monthly_changes(report):
    """Every arrival and departure of a director or holder, every office move, and the company first shown or gone, between the
    monthly files held, newest first, each dated by its file. The status and name changes are not reachable, so it never clears."""
    if _other_start(report):
        return flag("monthly-changes", V, "blocked", "info", _other_start(report))
    files = _files(report)
    whose = "the entity" if _company_start(report) else f"the {len(_in_scope(report))} company(ies) the person has a confirmed row on"
    held = f"the files held: {', '.join(files)}" if files else "no monthly file is named by the rows read"
    if len(files) < 2:
        return flag("monthly-changes", V, "blocked", "info", f"{held}: a change between files needs two, so none can be seen; {GRAIN}",
                    sources_not_held=(STATES_NOT_REACHED, INTERFACE))
    ch = _changes(report)
    tail = (f"; {GRAIN}; {held}; a status or name change between the files is published and not reachable by this report, so the list "
            f"is not complete")
    if ch:
        shown = "; ".join(f"{_month(f)}: {text}" for f, _, text, _ in ch[:CHANGES_SHOWN])
        more = f"; and {len(ch) - CHANGES_SHOWN} more, each in the changes section" if len(ch) > CHANGES_SHOWN else ""
        return flag("monthly-changes", V, "fired", "info", f"{len(ch)} change(s) on {whose} between the monthly files, newest first: {shown}{more}{tail}",
                    citations=tuple(dict.fromkeys(r for c in ch for r in c[3])), sources_not_held=(STATES_NOT_REACHED, INTERFACE, CHANGE_HISTORY),
                    scope="entity" if _company_start(report) else "officer-group")
    if _walk_short(report):
        return flag("monthly-changes", V, "blocked", "info", f"no change seen on the companies the walk read, but it stopped before reading every "
                    f"company the person has a row on{tail}", sources_not_held=(STATES_NOT_REACHED, INTERFACE))
    return _clear_or(STATES, "monthly-changes", "info", f"no director, holder of record or registered office of {whose} arrived or left between "
                     f"the monthly files ({held}); {GRAIN}", f"{STATES_NOT_REACHED} cannot be seen",
                     sources_held=(FILES_HELD,), sources_not_held=(STATES_NOT_REACHED, INTERFACE, CHANGE_HISTORY))


def _removed_before(report, change) -> bool:
    """A company gone from a file that the register had already removed before its last file: the drop is the file catching up with a
    removal dated on the row, not a new change (entity-status states the removal)."""
    co = _co(report, change[3][0])
    removed, m = _date(co["row"].get("removed_on")), FILE.match(co["row"].get("last_file") or "")
    return bool(removed and m and removed < dt.date(int(m.group(1)), int(m.group(2)), 1))


def recent_adverse_change(report):
    """What turned against the entity lately: a Gazette insolvency notice published in the last RECENT_DAYS (red), a removal notice
    in them (amber), the entity gone from the latest file (red), and in the latest file a director leaving or an office moving to an
    address fifty or more companies share (amber). Each is dated as its source dates it, side by side."""
    if _other_start(report):
        return flag("recent-adverse-change", V, "blocked", "red", _other_start(report))
    as_of = _as_of(report)
    since = as_of - dt.timedelta(days=RECENT_DAYS)
    scope = _in_scope(report)
    notes = [it for it in _notices(report) if (it.get("via") or _company_of(it)) in scope or _on_subject(report, it)]
    recent = [it for it in notes if (_published(it) or dt.date.min) >= since]
    insolv = [it for it in recent if _insolvency(it)]
    removal = [it for it in recent if _removal(it)]
    files = _files(report)
    latest = files[-1] if files else None
    ch = [c for c in _changes(report) if c[0] == latest]
    views = {ref: it["view"] for ref, it in all_items(report).items()}
    adverse_file = [c for c in ch if (c[1] == 1 and views.get(c[3][0]) == "directors") or (c[1] == 5 and not _removed_before(report, c))
                    or (c[1] == 3 and "companies share" in c[2])]
    bits, cites = [], []
    for it in insolv[:EXAMPLES]:
        bits.append(f"{_name(it)}: {_kind(it)}, {it['dates']['text']}")
    for it in removal[:EXAMPLES]:
        bits.append(f"{_name(it)}: removal notice, {it['dates']['text']}")
    for c in adverse_file[:EXAMPLES]:
        bits.append(f"{_month(c[0])}: {c[2]}")
    cites = [it["ref"] for it in insolv + removal] + [r for c in adverse_file for r in c[3]]
    window = (f"recent is a Gazette notice published on or after {since.isoformat()} ({RECENT_DAYS} days before {as_of.isoformat()}), and a "
              f"change first shown in the latest file held, {_month(latest) if latest else 'none'}, which dates it to a month")
    gone = [c for c in adverse_file if c[1] == 5]
    if bits:
        red = bool(insolv) or bool(gone)
        return flag("recent-adverse-change", V, "fired", "red" if red else "amber",
                    f"{len(insolv)} insolvency notice(s), {len(removal)} removal notice(s) and {len(adverse_file)} adverse change(s) between the "
                    f"files on {'the entity' if _company_start(report) else 'the companies the person has a confirmed row on'}: "
                    + " | ".join(bits) + f"; {window}; side by side, each with its own date",
                    citations=tuple(dict.fromkeys(cites)), sources_not_held=(STATES_NOT_REACHED, INTERFACE) + NOT_HELD_INSOLVENCY,
                    scope="entity" if _company_start(report) else "officer-group")
    if _walk_short(report):
        return flag("recent-adverse-change", V, "blocked", "red", f"none seen on the companies the walk read, but it stopped before reading every "
                    f"company{_short_text(report)}; {window}", sources_not_held=(STATES_NOT_REACHED, INTERFACE))
    whose = "the entity" if _company_start(report) else "the companies the person has a confirmed row on"
    return _clear_or(STATES, "recent-adverse-change", "red", f"on {whose}: no Gazette insolvency or removal notice in the window, none gone from "
                     f"the latest file, and no director left nor did an office move to a busy address in it; {window}",
                     f"{STATES_NOT_REACHED} cannot be seen, nor {INTERFACE}",
                     sources_held=(GAZETTE_HELD, FILES_HELD), sources_not_held=(STATES_NOT_REACHED, INTERFACE) + NOT_HELD_INSOLVENCY)


def officer_churn(report):
    """Directors arriving and leaving between the files, and current directors appointed in the last CHURN_DAYS as the register files
    it: amber at CHURN_AMBER together with a departure, info below. From a person, start a report from each company."""
    if _other_start(report):
        return flag("officer-churn", V, "blocked", "amber", _other_start(report), scope="entity")
    if not _company_start(report):
        return flag("officer-churn", V, "blocked", "amber", "the start is a person: churn is read on a company's directors; the arrivals and "
                    "departures on the person's companies are in the flag monthly-changes; start a report from each company", scope="entity")
    as_of = _as_of(report)
    s = report["subject"]
    dirs = [it for it in all_items(report).values() if it["view"] == "directors" and _company_of(it) == s["ref"]]
    holders = [it for it in all_items(report).values() if it["view"] == "shareholders" and _company_of(it) == s["ref"]]
    ch = _changes(report)
    mine = lambda kind, view: [c for c in ch if c[1] == kind and any(r in {d["ref"] for d in view} for r in c[3])]   # noqa: E731
    left, came = mine(1, dirs), mine(0, dirs)
    came_refs = {r for c in came for r in c[3]}
    reg = _date(s["row"].get("registered_on"))
    founding = lambda it: bool(reg and _date(it["row"].get("appointed_on")) and (_date(it["row"]["appointed_on"]) - reg).days <= FOUNDING_DAYS)   # noqa: E731
    lately = [it for it in dirs if it["row"].get("in_latest", True) and it["ref"] not in came_refs and not founding(it)
              and (as_of - (_date(it["row"].get("appointed_on")) or dt.date.min)).days <= CHURN_DAYS]
    came = [c for c in came if not all(founding(all_items(report)[r]) for r in c[3] if r in all_items(report))]
    now = [it for it in dirs if it["row"].get("in_latest", True)]
    h_moves = len(mine(0, holders)) + len(mine(1, holders)) + len(mine(2, holders))
    n = len(left) + len(came) + len(lately)
    text = (f"{len(left)} director(s) left and {len(came)} arrived between the files, and {len(lately)} more current director(s) were appointed "
            f"on or after {(as_of - dt.timedelta(days=CHURN_DAYS)).isoformat()} as the register files it (a director appointed within "
            f"{FOUNDING_DAYS} days of the registration founded the company and is not counted); {len(now)} current director(s); "
            f"{h_moves} change(s) among the holders of record; {GRAIN}")
    cites = [r for c in left + came for r in c[3]] + [it["ref"] for it in lately]
    if n >= CHURN_AMBER and left:
        return flag("officer-churn", V, "fired", "amber", text, citations=tuple(dict.fromkeys(cites)), sources_not_held=(CHANGE_HISTORY,), scope="entity")
    if n:
        return flag("officer-churn", V, "fired", "info", text, citations=tuple(dict.fromkeys(cites)), sources_not_held=(CHANGE_HISTORY,), scope="entity")
    return _clear_or(HISTORY, "officer-churn", "amber", text, "a director who left before the first file held is not seen, and "
                     + CHANGE_HISTORY, sources_held=(FILES_HELD,), sources_not_held=(CHANGE_HISTORY,), scope="entity")


# ── the Gazette on the entity ───────────────────────────────────────────────

def insolvency_notices(report):
    """Gazette insolvency notices on the entity, or on every company the person has a row on, each with its own date."""
    if _other_start(report):
        return flag("insolvency-notices", V, "blocked", "red", _other_start(report), sources_not_held=NOT_HELD_INSOLVENCY)
    if _company_start(report):
        own = [it for it in _notices(report) if _insolvency(it) and _on_subject(report, it)]
        if own:
            own.sort(key=lambda it: _published(it) or dt.date.min, reverse=True)
            return flag("insolvency-notices", V, "fired", "red", f"{len(own)} Gazette insolvency notice(s) on the entity ({_counted(own, _kind)}), "
                        "newest first: " + "; ".join(f"{_kind(it)}, {it['dates']['text']}" for it in own[:EXAMPLES]),
                        citations=tuple(it["ref"] for it in own), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
        if set(section(report, "gazette").get("omitted_views") or ()) & {"gazette_liquidations", "gazette_company_notices"}:
            return flag("insolvency-notices", V, "blocked", "red", "the entity has more Gazette notices than the walk lists; an insolvency could "
                        "be among those left out", scope="entity")
        return flag("insolvency-notices", V, "clear", "red",
                    "no Gazette liquidation, receivership, administration, winding-up application, creditors' notice or deed of company "
                    "arrangement on the entity", sources_held=(GAZETTE_HELD + ", joined to the company by its number",),
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
    conf = [it for it in _notices(report) if _insolvency(it)]
    nearby = [it for it in _notices(report, ("near",)) if _insolvency(it)]
    if conf:
        return flag("insolvency-notices", V, "fired", "red",
                    f"{len(conf)} Gazette insolvency notice(s) on {len({it.get('via') for it in conf})} company(ies) the person has a row on: "
                    + "; ".join(f"{_name(it)}: {_kind(it)}, {it['dates']['text']}" for it in conf[:EXAMPLES]) + _short_text(report),
                    citations=tuple(it["ref"] for it in conf), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if nearby:
        return flag("insolvency-notices", V, "fired", "amber",
                    f"{len(nearby)} Gazette insolvency notice(s) on companies reached only through a near link: a namesake's companies, "
                    f"not the person's until confirmed{_short_text(report)}", citations=tuple(it["ref"] for it in nearby),
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="near")
    if _walk_short(report):
        return flag("insolvency-notices", V, "blocked", "red", "no Gazette insolvency notice on the companies the walk read, but it stopped "
                    "before reading every company the person has a row on", scope="officer-group")
    return _clear_or(HISTORY, "insolvency-notices", "red", "no Gazette liquidation, receivership, administration, winding-up application, "
                     "creditors' notice or deed of company arrangement on any company the person has a row on", PAST_NOT_HELD,
                     sources_held=(GAZETTE_HELD,), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")


def register_events(report):
    """Removals, restorations, dissolutions, rectifications, amalgamations, transfers out: not insolvency. On the entity amber, on
    the person's companies info."""
    if _other_start(report):
        return flag("register-events", V, "blocked", "info", _other_start(report))
    conf = [it for it in _notices(report) if _event(it)]
    conf.sort(key=lambda it: _published(it) or dt.date.min, reverse=True)
    if _company_start(report):
        own = [it for it in conf if _on_subject(report, it)]
        if own:
            return flag("register-events", V, "fired", "amber", f"{len(own)} Gazette notice(s) on the entity ({_counted(own, _event_kind)}), newest "
                        "first: " + "; ".join(f"{_event_kind(it)}, {it['dates']['text']}" for it in own[:EXAMPLES]) + "; none is an insolvency, "
                        "and a restoration reverses a removal", citations=tuple(it["ref"] for it in own), scope="entity")
        return flag("register-events", V, "clear", "amber", "no Gazette removal, restoration, dissolution, rectification, amalgamation or "
                    "transfer notice on the entity", sources_held=(NOTICES_HELD,), scope="entity")
    if conf:
        return flag("register-events", V, "fired", "info",
                    f"{len(conf)} Gazette notice(s) ({_counted(conf, _event_kind)}) on {len({it.get('via') for it in conf})} company(ies) the "
                    "person has a row on: " + "; ".join(f"{_name(it)}, {it['dates']['text']}" for it in conf[:EXAMPLES]) + "; none is an insolvency",
                    citations=tuple(it["ref"] for it in conf), scope="officer-group")
    if _walk_short(report):
        return flag("register-events", V, "blocked", "info", "the walk stopped before reading every company the person has a row on",
                    scope="officer-group")
    return _clear_or(HISTORY, "register-events", "info", "no Gazette removal, restoration, dissolution, rectification, amalgamation or transfer "
                     "notice on a company the person has a confirmed row on", PAST_NOT_HELD, sources_held=(NOTICES_HELD,), scope="officer-group")


def officers_of_record(report):
    if _other_start(report):
        return flag("officers-of-record", V, "blocked", "info", _other_start(report), scope="entity")
    if not _company_start(report):
        return flag("officers-of-record", V, "blocked", "info", "the start is a person: its own roles are in the changes section; start a "
                    "report from a company for its officers of record", scope="entity")
    s = report["subject"]
    r = s["row"]
    rows = [it for it in all_items(report).values() if it["view"] in PEOPLE and _company_of(it) == s["ref"]]
    dirs = [it for it in rows if it["view"] == "directors"]
    holders = [it for it in rows if it["view"] == "shareholders"]
    now = [it for it in dirs if it["row"].get("in_latest", True) and not it["row"].get("ended_on")]
    omitted = section(report, "changes").get("omitted") or 0
    tail = f"; {omitted:,} row(s) past the walk's limit, not listed" if omitted else ""
    text = (f"{len(now)} current director(s) and {len(dirs) - len(now)} not in the latest file; {len(holders)} holder(s) of record{tail}; "
            "start a report from each director to read the companies they sit on")
    going = GOING_STATUS.match(_status(s)) and r.get("in_latest", True)
    if not now and not omitted and going:
        return flag("officers-of-record", V, "fired", "amber", f"the latest companies file names no current director of the entity: {text}",
                    citations=tuple(it["ref"] for it in dirs) or (s["ref"],), scope="entity")
    return flag("officers-of-record", V, "clear", "info", text, sources_held=(COMPANIES_HELD,), scope="entity")


def young_entity(report):
    """Registered under 24 months: amber on the entity, info on the person's going companies."""
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
                    + "; ".join(f"{_name(it)} (registered {reg.isoformat()}, {_age(as_of, reg)})" for it, reg in young[:EXAMPLES]),
                    citations=tuple(it["ref"] for it, _ in young), scope="entity" if _company_start(report) else "officer-group")
    if _company_start(report):
        if not _date(report["subject"]["row"].get("registered_on")):
            return flag("young-entity", V, "blocked", "amber", "the companies file states no registration date for the entity", scope="entity")
        return flag("young-entity", V, "clear", "amber", "registered 24 months ago or more",
                    sources_held=("Companies register registration dates (pub.companies)",), scope="entity")
    if (report.get("walk") or {}).get("entities_omitted"):
        return flag("young-entity", V, "blocked", "info", f"the walk left {report['walk']['entities_omitted']:,} company(ies) past its limit, and "
                    "their registration dates are not read")
    return flag("young-entity", V, "clear", "info", "no going company the person has a confirmed row on was registered under 24 months ago",
                sources_held=("Companies register registration dates (pub.companies)",))


# ── its people ──────────────────────────────────────────────────────────────

def _failed(report, companies, grades=("confirmed",)) -> dict:
    """{company ref: (company, [evidence refs], the earliest dated notice or None)} for each company with an insolvency status or a
    Gazette insolvency notice."""
    by_ref = {it["ref"]: it for it in companies}
    out = {it["ref"]: (it, [it["ref"]], None) for it in companies if _ending(it) == "insolvent"}
    for n in _notices(report, grades):
        c = n.get("via") or _company_of(n)
        if c not in by_ref or not _insolvency(n):
            continue
        co, ev, first = out.get(c, (by_ref[c], [c], None))
        ev = ev + [n["ref"]]
        if first is None or (_published(n) or dt.date.max) < (_published(first) or dt.date.max):
            first = n
        out[c] = (co, ev, first)
    return out


def _how(entry) -> str:
    co, _, n = entry
    if n is None:
        return f"status {_status(co)!r}, no dated Gazette notice reached"
    return f"{_kind(n)}, {n['dates']['text']}"


def people_failed_companies(report):
    """A people exposure through other failed companies: from a person, the companies the person has a row on that have an insolvency
    status or notice, beside the going ones; red on confirmed rows, amber through a near link. From a company: blocked."""
    if _company_start(report):
        return flag("people-failed-companies", V, "blocked", "red", f"{NOT_FOLLOWED}: whether a director's other companies failed cannot be seen",
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if _other_start(report):
        return flag("people-failed-companies", V, "blocked", "red", _other_start(report), scope="officer-group")
    conf = _companies(report)
    bad = _failed(report, conf)
    going = [it for it in conf if _ending(it) == "going"]
    hub = _subject_hub(report)
    if bad:
        ordered = sorted(bad.values(), key=lambda e: (e[2] is None, _published(e[2]) if e[2] else dt.date.min), reverse=False)
        why = f"; the person is a hub ({hub[0]['kind']}): a failure among many companies means less" if hub else ""
        return flag("people-failed-companies", V, "fired", "amber" if hub else "red",
                    f"{len(bad)} of the {len(conf)} company(ies) the person has a confirmed row on have an insolvency status or notice, and "
                    f"{len(going)} are going: " + " | ".join(f"{_name(e[0])} ({_how(e)})" for e in ordered[:EXAMPLES + 1]) + why + _short_text(report),
                    citations=tuple(dict.fromkeys(r for e in ordered for r in e[1])), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    nearby = _failed(report, _companies(report, ("near",)), ("confirmed", "near"))
    if nearby:
        return flag("people-failed-companies", V, "fired", "amber", f"{len(nearby)} company(ies) reached only through a near link have an "
                    "insolvency status or notice: a namesake's companies, not the person's until confirmed: "
                    + "; ".join(f"{_name(e[0])} ({_how(e)})" for e in list(nearby.values())[:EXAMPLES]),
                    citations=tuple(dict.fromkeys(r for e in nearby.values() for r in e[1])), sources_not_held=NOT_HELD_INSOLVENCY, scope="near")
    if _walk_short(report):
        return flag("people-failed-companies", V, "blocked", "red", "the walk stopped before reading every company the person has a row on",
                    scope="officer-group")
    return _clear_or(HISTORY, "people-failed-companies", "red", f"none of the {len(conf)} company(ies) the person has a confirmed row on has an "
                     "insolvency status or notice", PAST_NOT_HELD, sources_held=(GAZETTE_HELD, COMPANIES_HELD), sources_not_held=NOT_HELD_INSOLVENCY,
                     scope="officer-group")


def other_current_companies(report):
    """The person's going companies and their states, newest first."""
    if _company_start(report):
        return flag("other-current-companies", V, "blocked", "amber", f"{NOT_FOLLOWED}: the other companies its people sit on are not read",
                    scope="officer-group")
    if _other_start(report):
        return flag("other-current-companies", V, "blocked", "amber", _other_start(report), scope="officer-group")
    conf = _companies(report)
    going = sorted([it for it in conf if _ending(it) == "going"], key=lambda x: str(x["row"].get("registered_on") or ""), reverse=True)
    if conf:
        by = _counted(conf, lambda it: {"going": "registered", "insolvent": "in an insolvency", "ended": "removed or ended"}[_ending(it)])
        return flag("other-current-companies", V, "fired", "info", f"the person has a confirmed row on {len(conf)} company(ies) ({by}); the going "
                    "ones, newest first: " + ("; ".join(f"{_name(it)} (registered {_iso(_date(it['row'].get('registered_on')))})" for it in going[:EXAMPLES])
                                              or "none") + _short_text(report), citations=tuple(it["ref"] for it in conf), scope="officer-group")
    if _walk_short(report):
        return flag("other-current-companies", V, "blocked", "amber", "the walk stopped before reading every company the person has a row on",
                    scope="officer-group")
    return _clear_or(HISTORY, "other-current-companies", "amber", "the person has no confirmed company row", PAST_NOT_HELD,
                     sources_held=(COMPANIES_HELD,), scope="officer-group")


def _in_force(report, it) -> str:
    as_of = _as_of(report)
    end = _date(it["row"].get("ends_on"))
    if it["row"].get("permanent"):
        return f"permanent; in force on {as_of.isoformat()}"
    if not end:
        return "no end filed"
    return f"in force on {as_of.isoformat()}" if end >= as_of else f"ended before {as_of.isoformat()}"


def _person_notice(report, rule, view, noun, severity, extra_clear="", not_held=(), current=lambda it: True, current_word="current"):
    """A Gazette notice the link rules join to the person by name: confirmed red while `current`, amber once past it; near amber;
    never a suppressed or withheld row; blocked from a company, or where the walk left a link unread."""
    live = [it for it in items(report, (view,)) if not it.get("suppressed")]
    conf = [it for it in live if it["grade"] == "confirmed"]
    nearby = [it for it in live if it["grade"] == "near"]
    show = (lambda it: f"{it['dates']['text']}; {_in_force(report, it)}") if view == "gazette_prohibitions" else (lambda it: it["dates"]["text"])
    if conf:
        live_now = [it for it in conf if current(it)]
        return flag(rule, V, "fired", severity if live_now else "amber", f"{len(conf)} Gazette {noun} notice(s) confirmed to the person, "
                    f"{len(live_now)} {current_word}: " + "; ".join(f"{_name(it)} ({show(it)})" for it in conf[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in conf), sources_not_held=not_held)
    if nearby:
        return flag(rule, V, "fired", "amber", f"{len(nearby)} Gazette {noun} notice(s) under a name near the person's; a namesake's until "
                    f"confirmed: " + "; ".join(f"{_name(it)} ({show(it)}; near: {it.get('reason')})" for it in nearby[:EXAMPLES]),
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
    return _person_notice(report, "prohibition", "gazette_prohibitions", "director prohibition", "red",
                          current=lambda it: PROHIBITION_RED_ENDED or not _in_force(report, it).startswith("ended"), current_word="in force or with no end filed")


def bankruptcy(report):
    as_of = _as_of(report)
    return _person_notice(report, "bankruptcy", "gazette_bankruptcies", "bankruptcy", "red",
                          "; a name the Gazette later withheld (an annulment) makes no row and is never shown",
                          not_held=(INSOLVENCY_REGISTER + ": a discharge, a no-asset procedure or a summary instalment order",),
                          current=lambda it: (as_of - (_date(it["row"].get("event_on")) or _published(it) or dt.date.min)).days <= BANKRUPTCY_RECENT_DAYS,
                          current_word=f"dated within {BANKRUPTCY_RECENT_DAYS // 365} years (an older one is amber: a discharge, usual after three "
                                       f"years, is in the Insolvency Register, which is not held)")


def subject_hub(report):
    if _other_start(report):
        return flag("subject-hub", V, "blocked", "info", _other_start(report))
    mine = _subject_hub(report)
    if mine:
        kinds = sorted({h["kind"] for h in mine})
        return flag("subject-hub", V, "fired", "amber", f"the start is itself a hub ({', '.join(kinds)}): {mine[0]['text']}; a failure among its "
                    "many companies is shown and means less", citations=tuple(sorted({h["ref"] for h in mine})))
    return flag("subject-hub", V, "clear", "info", "the start is not a professional director, a nominee or the Crown on the rows held",
                sources_held=("pub.directors", "pub.groups"))


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


# ── what the registers cannot see ───────────────────────────────────────────

def status_name_changes(report):
    if STATES:
        return flag("status-name-changes", V, "clear", "amber", "status and name changes between files are read", sources_held=("pub.company_states",))
    return flag("status-name-changes", V, "blocked", "amber",
                "a status change (registered to in liquidation, say) or a name change between the monthly files is published in "
                "pub.company_states, which the report's catalogue does not know, so this report cannot list it: the status today is shown, "
                "how it stood in the earlier file is not; this check cannot run", sources_not_held=(STATES_NOT_REACHED,))


def since_date(report):
    return flag("since-date", V, "blocked", "info",
                "the report takes no \"since\" date and keeps no watched list: every change it can see is listed in monthly-changes, each "
                "dated, newest first, and what is new to the reader is theirs to pick out; this check cannot run",
                sources_not_held=("a since-date and a watched list on the subject-report shape (carded)",))


def interface_freshness(report):
    return flag("interface-freshness", V, "blocked", "amber",
                "the entity's state today is not checked against the business-number interface (plan step 5.5, not built): what the register "
                "filed after the latest monthly file held is not seen; this check cannot run", sources_not_held=(INTERFACE,))


def past_roles(report):
    if HISTORY:
        return flag("past-roles", V, "clear", "info", "past roles and holdings are published with their filed end dates", sources_held=(COMPANIES_HELD,))
    left = [it for it in all_items(report).values() if it["view"] in PEOPLE and it["grade"] == "confirmed" and not it["row"].get("in_latest", True)]
    seen = f"; {len(left)} of the rows listed left the file since July 2026 and carry no end date" if left else ""
    whose = "the entity's past officers and holders" if _company_start(report) else "the person's past directorships and holdings"
    return flag("past-roles", V, "blocked", "amber", f"{whose} before the first file held are not held: {PAST_NOT_HELD}{seen}",
                sources_not_held=("past directorships and shareholdings with their end dates",))


def change_history(report):
    return flag("change-history", V, "blocked", "amber",
                "a company's earlier names, trading names, directors and offices are in the companies change history, which is not held before "
                "16 August 2026 and is held but not published since; this check cannot run", sources_not_held=(CHANGE_HISTORY,))


def securities_register(report):
    return flag("securities-register", V, "blocked", "red",
                "who holds a registered security interest over the company's assets, and since when, is in the Personal Property Securities "
                "Register, which is not held; for a trade creditor this is where another creditor's priority shows; this check cannot run",
                sources_not_held=(SECURITIES,))


def insolvency_register(report):
    return flag("insolvency-register", V, "blocked", "red",
                "the Official Assignee's Insolvency Register (a bankruptcy's discharge, a no-asset procedure, a summary instalment order, and the "
                "removals it records daily) is not held; the Gazette's own notices are read above; this check cannot run",
                sources_not_held=(INSOLVENCY_REGISTER,))


def court_judgments(report):
    return flag("court-judgments", V, "blocked", "red",
                "court judgments are not held yet (plan step 5.4): a creditor's judgment or a winding-up order's reasons cannot be seen; this "
                "check cannot run", sources_not_held=COURTS)


def credit_bureau(report):
    return flag("credit-bureau", V, "blocked", "amber",
                "payment defaults and credit enquiries are kept by the credit bureaux, which are not a public register and are not held; this "
                "check cannot run", sources_not_held=(CREDIT_BUREAU,))


def mortgagee_possession(report):
    return flag("mortgagee-possession", V, "blocked", "amber",
                "a lender's entry into possession of a company's land or goods is published in the Gazette (pub.gazette_possessions), but the "
                "report's catalogue does not know the view, so this report cannot reach it; this check cannot run", sources_not_held=POSSESSIONS)


RULES = (entity_status, monthly_changes, recent_adverse_change, officer_churn, insolvency_notices, register_events, officers_of_record,
         young_entity, people_failed_companies, other_current_companies, prohibition, bankruptcy, subject_hub, namesake_exposure, walk_coverage,
         status_name_changes, since_date, interface_freshness, past_roles, change_history, securities_register, insolvency_register,
         court_judgments, credit_bureau, mortgagee_possession)
