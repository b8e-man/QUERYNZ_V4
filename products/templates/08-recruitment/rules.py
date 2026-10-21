"""The recruitment board screen's rules (plan 5.2, use case 8). Pure
functions over the built report, each returning one flag, in the shape of
products/report/templates/subject/rules.py. They stand for the old estate's
seven person rules (data-layer/flags/flags/person_rules.py, rulepack
person-0.2), taken as ideas and tests, not code, where the held registers
can support them:

  liquidation-history      Gazette insolvency notices on a company the subject has a role on, the role's dates beside the notice's
                           (a removal from the register is not insolvency: register-removals, info)
  prohibition              director prohibitions confirmed or near; a clear only when the walk read every link
  young-entity             a confirmed directorship at a company registered under 24 months (the old rule read GST age, not held;
                           the company's own registration date stands in)
  namesake-exposure        the screen's own uncertainty: how many namesakes it set apart, and whether the walk stopped short
  charity-officer-roles    society officer roles; charity officer rows that carry the subject's name (near: no link joins the
                           Charities Register yet); from a company, its charity by business number and the officer rows on it
  charity-integrity-marks  the Charities Register's own disqualified mark on an officer row: red on the company's own charity's
                           officers, amber on a row that only carries the subject's name
  comcom-coverage          blocked: the Commerce Commission's cases are not published

and the ones a board screen adds: subject-hub (the subject is itself a
professional director or a nominee), register-removals, bankruptcy (blocked
until a link rule reaches a Gazette bankruptcy notice: a blank there is not a
clear) and public-life (seats, candidacies, declared interests, political
money). Who the subject is, the hubs met on the walk and rows from a replaced
return are the builder's common rules (group-standing, hubs-met,
replaced-return), run for every template; this file carries no copy.

Imports nothing of products.report: the one-way test holds a template folder
to its own code. The shape loads this file by path and binds the name
`contract` (products/report/contract.py) before it runs: `flag` and the
helpers over a built report below are the contract's, and the shape's
presentation rules check every flag again on every report (rule 9).

The A-1 property of the old set runs through all of them: evidence on the
subject's confirmed rows is red; the same evidence reached only through a
near link is amber and says it is a namesake's until confirmed. No flag joins
two facts with a word of cause; dates sit side by side."""
from __future__ import annotations

import datetime as dt

V = "0.1"
YOUNG_DAYS = 730          # under 24 months registered: worth a question (the old young-entity rule)
NAMESAKE_NOTE_AT = 5      # namesakes set apart at which the screen's caveat fires (the old namesake-exposure rule)
EXAMPLES = 3              # dated examples a fired flag states in its text

INSOLVENCY_VIEWS = ("gazette_liquidations", "gazette_company_notices")
#: the company notices that are insolvency: a removal from the register (an intention to remove, a restoration) is not, and is its own flag
INSOLVENCY_KINDS = ("winding-up application", "receivership", "administration", "notice to creditors")
GAZETTE_HELD = ("New Zealand Gazette liquidation and company notices (pub.gazette_liquidations, pub.gazette_company_notices), "
                "on every company the subject's rows sit on")
NOT_HELD_INSOLVENCY = ("the Insolvency Register (interface awaited since 19 September 2026)", "court judgments (step 5.4)")
#: the views whose rows the walk looks a person's name up from in the Charities Register (the shape's NAME_JOIN_FROM)
NAME_LOOKED_UP = ("directors", "society_officers", "members", "candidates", "mp_interest_returns", "promoter_people", "gazette_appointments")
CHARITY_HELD = "Charities Register officers (pub.charity_officers), looked up by the person's name"
CHARITY_BY_NAME = ("no link joins the Charities Register's officers to any other row yet, so each is matched by name and is a namesake's "
                   "until a rule confirms it")
MARK_SEVERITY = "red"   # a disqualified mark on an officer of the company's own charity: the screen's red
PUBLIC_VIEWS = ("members", "candidates", "mp_interest_returns", "mp_interests")
NOT_FOLLOWED = ("started from a company, the screen lists its officers and does not follow them to their own rows; start a screen from each "
                "person listed")
MONEY_VIEWS = ("party_return_donors", "party_return_loans", "disclosures", "disclosure_items", "candidate_return_donors", "promoter_people")


flag, items, section, all_items = contract.flag, contract.items, contract.section, contract.all_items   # noqa: F821  (bound by the loader)


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


def _not_a_person_start(report):
    """A start row that is neither a person nor an organisation (a filed
    donation, a disclosure, an interest) has no group of its own: the walk
    reads its links but not the links of the person rows it is confirmed to,
    nor their companies, so a check over those cannot clear."""
    k = report["subject"]["kind"]
    if k in ("person", "organisation"):
        return None
    return (f"the screen starts from a {k} row ({report['subject']['view']}), which has no group of its own: the companies and links of the "
            f"person rows it is confirmed to are not walked, so no clear is given; start the screen from a person row")


def _company_start(report) -> bool:
    return report["subject"]["view"] == "companies"


def _other_start(report):
    return _not_a_person_start(report)


def _role_on(report, company_ref: str) -> list:
    """The subject's own rows on a company: the role or holding and its dating text."""
    by = all_items(report)
    out = []
    for it in by.values():
        if it["view"] in ("directors", "shareholders") and it["grade"] == "confirmed":
            ent = (it.get("entity") or {}).get("ref")
            if ent == company_ref or it["row"].get("entity_key") and f"companies:{it['row']['entity_key']}" == company_ref:
                out.append(it)
    return out


def _side_by_side(report, notices: list) -> str:
    """'COMPANY: notice dated D; the subject's role: director, from A to B'
    for the first few notices. Two dates, no word between them."""
    bits = []
    for it in notices[:EXAMPLES]:
        roles = _role_on(report, it.get("via") or "")
        mine = "; ".join(f"the subject's row: {r['row'].get('role_type') or 'shareholder of record'}, {r['dates']['text']}" for r in roles[:2]) \
            or "the subject's row on it is in the companies section"
        bits.append(f"{it['title']}: notice {it['dates']['text']}; {mine}")
    more = f"; and {len(notices) - EXAMPLES} more" if len(notices) > EXAMPLES else ""
    return " | ".join(bits) + more


# ── the old seven, where the held registers support them ────────────────────

def _insolvency(it) -> bool:
    return it["view"] == "gazette_liquidations" or (it["view"] == "gazette_company_notices" and it["row"].get("kind") in INSOLVENCY_KINDS)


def _removal(it) -> bool:
    return it["view"] == "gazette_company_notices" and not _insolvency(it)


def liquidation_history(report):
    conf = [it for it in items(report, INSOLVENCY_VIEWS, ("confirmed",)) if _insolvency(it)]
    nearby = [it for it in items(report, INSOLVENCY_VIEWS, ("near",)) if _insolvency(it)]
    if conf:
        cos = len({it.get("via") for it in conf})
        return flag("liquidation-history", V, "fired", "red",
                    f"{len(conf)} Gazette insolvency notice(s) on {cos} company(ies) the subject has or had a row on; "
                    f"each date beside the subject's: {_side_by_side(report, conf)}",
                    citations=tuple(it["ref"] for it in conf), sources_not_held=NOT_HELD_INSOLVENCY)
    if nearby:
        return flag("liquidation-history", V, "fired", "amber",
                    f"{len(nearby)} Gazette insolvency notice(s) on companies reached only through a near link: "
                    f"a namesake's companies, not the subject's until confirmed",
                    citations=tuple(it["ref"] for it in nearby), sources_not_held=NOT_HELD_INSOLVENCY, scope="near")
    if _not_a_person_start(report):
        return flag("liquidation-history", V, "blocked", "red", _not_a_person_start(report), sources_not_held=NOT_HELD_INSOLVENCY)
    if not section(report, "companies")["items"] and not report["subject"]["view"] in ("directors", "shareholders"):
        return flag("liquidation-history", V, "clear", "red", "the subject has no company row in the registers held, so no company notice can reach it",
                    sources_held=("Companies register (pub.directors, pub.shareholders)",), sources_not_held=NOT_HELD_INSOLVENCY)
    if (report.get("walk") or {}).get("entities_not_expanded") or (report.get("walk") or {}).get("entities_omitted"):
        return flag("liquidation-history", V, "blocked", "red",
                    "no Gazette insolvency notice on the companies the walk read, but the walk stopped before reading every company "
                    "the subject has a row on; start a report from each company left out")
    return flag("liquidation-history", V, "clear", "red",
                "no Gazette liquidation, receivership, administration, winding-up or creditors' notice on any company the subject has or had a row on",
                sources_held=(GAZETTE_HELD,), sources_not_held=NOT_HELD_INSOLVENCY)


def register_removals(report):
    """Gazette notices that a company the subject sits on is to be, or was,
    removed from the register, or restored to it. Not insolvency, so info."""
    conf = [it for it in items(report, ("gazette_company_notices",), ("confirmed",)) if _removal(it)]
    if conf:
        return flag("register-removals", V, "fired", "info",
                    f"{len(conf)} Gazette removal or restoration notice(s) on {len({it.get('via') for it in conf})} company(ies) the subject has or had a row on; "
                    f"each date beside the subject's: {_side_by_side(report, conf)}", citations=tuple(it["ref"] for it in conf))
    if _not_a_person_start(report):
        return flag("register-removals", V, "blocked", "info", _not_a_person_start(report))
    return flag("register-removals", V, "clear", "info", "no Gazette removal or restoration notice on a company the subject has a confirmed row on",
                sources_held=("New Zealand Gazette company notices (pub.gazette_company_notices)",))


def _in_force(report, it) -> str:
    """'in force on D' or 'ended before D', from the notice's own dates; a
    prohibition with no end filed says so."""
    as_of = _as_of(report)
    end = _date(it["row"].get("ends_on"))
    if it["row"].get("permanent"):
        return f"permanent; in force on {as_of.isoformat()}"
    if not end:
        return "no end filed"
    return f"in force on {as_of.isoformat()}" if end >= as_of else f"ended before {as_of.isoformat()}"


def prohibition(report):
    rows = list(items(report, ("gazette_prohibitions",)))
    live = [it for it in rows if not it.get("suppressed")]       # a revoked prohibition's name is never shown; it is not counted
    conf = [it for it in live if it["grade"] == "confirmed"]
    nearby = [it for it in live if it["grade"] == "near"]
    if conf:
        return flag("prohibition", V, "fired", "red",
                    f"{len(conf)} Gazette director prohibition notice(s) confirmed to the subject: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']}; {_in_force(report, it)})" for it in conf[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in conf))
    if nearby:
        return flag("prohibition", V, "fired", "amber",
                    f"{len(nearby)} Gazette director prohibition notice(s) under a name near the subject's; a namesake's until confirmed: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']}; {_in_force(report, it)}; near: {it.get('reason')})" for it in nearby[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in nearby), scope="near")
    w = report.get("walk") or {}
    if _not_a_person_start(report):
        return flag("prohibition", V, "blocked", "red", _not_a_person_start(report))
    if not w.get("links_built"):
        return flag("prohibition", V, "blocked", "red", "no links are published, so a prohibition under the subject's name cannot be reached")
    if w.get("links_omitted"):
        return flag("prohibition", V, "blocked", "red",
                    f"the walk left {w['links_omitted']:,} link(s) unread past its limit; a prohibition could be among them, so no clear is given")
    if report["subject"]["kind"] != "person":
        return flag("prohibition", V, "clear", "red", "an organisation: a director prohibition is on a person",
                    sources_held=("New Zealand Gazette prohibition notices (pub.gazette_prohibitions)",))
    return flag("prohibition", V, "clear", "red",
                "no Gazette director prohibition confirmed or near the subject: the link rules join every prohibition notice by name, "
                "and every link from the subject's rows was read",
                sources_held=("New Zealand Gazette prohibition notices (pub.gazette_prohibitions), joined by name in pub.links",))


def young_entity(report):
    as_of = _as_of(report)
    young = []
    for it in items(report, ("companies",), ("confirmed",)):
        reg = _date(it["row"].get("registered_on"))
        if reg and (as_of - reg).days < YOUNG_DAYS:
            young.append((it, reg))
    if young:
        return flag("young-entity", V, "fired", "info",
                    f"{len(young)} company(ies) the subject has a confirmed row on were registered under 24 months before {as_of.isoformat()}: "
                    + "; ".join(f"{it['title']} (registered {reg.isoformat()})" for it, reg in young[:EXAMPLES]),
                    citations=tuple(it["ref"] for it, _ in young))
    return flag("young-entity", V, "clear", "info", "no company the subject has a confirmed row on was registered under 24 months ago",
                sources_held=("Companies register registration dates (pub.companies)",),
                sources_not_held=("GST registration dates (the old rule's measure; not held)",))


def namesake_exposure(report):
    names = [it for it in section(report, "identity")["items"]]
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
        return flag("namesake-exposure", V, "fired", "info", "the screen's own uncertainty: " + "; ".join(bits), citations=cites)
    return flag("namesake-exposure", V, "clear", "info",
                f"low namesake exposure: {len(names)} namesake row(s) set apart and every link read",
                sources_held=("pub.links", "pub.groups"))


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
    # the officers of a society the report starts from are that society's, not the subject's roles
    conf = [it for it in items(report, ("society_officers",), ("confirmed",)) if it.get("via") != report["subject"]["ref"]]
    by_name, own = _charity_roles(report), _company_charities(report)
    if conf or by_name or own:
        bits = [f"officer of {len({it.get('via') for it in conf})} incorporated society(ies): "
                + "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in conf[:EXAMPLES])] if conf else []
        bits += [f"{len(by_name)} charity officer row(s) carry the person's name, near: {CHARITY_BY_NAME}: "
                 + "; ".join(f"{it['statement']} ({it['dates']['text']})" for it in by_name[:EXAMPLES])] if by_name else []
        bits += [f"the company's charity by its business number: {c['statement']} ({c['dates']['text']}), {len(o)} officer row(s) on it"
                 for c, o in own[:EXAMPLES]]
        return flag("charity-officer-roles", V, "fired", "info", " | ".join(bits),
                    citations=tuple(dict.fromkeys([it["ref"] for it in conf + by_name] + [c["ref"] for c, _ in own])),
                    scope="subject" if conf or own else "near")
    if _company_start(report):
        return flag("charity-officer-roles", V, "blocked", "info", f"{NOT_FOLLOWED}: their society and charity roles are not read; the company "
                    "has no charity row by its business number", scope="officer-group")
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
    marked = [it for it in items(report, ("charity_officers",)) if _marked(it) and not it.get("suppressed")]
    if marked:
        conf = [it for it in marked if it["grade"] == "confirmed"]
        return flag("charity-integrity-marks", V, "fired", MARK_SEVERITY if conf else "amber",
                    f"{len(marked)} charity officer row(s) carry the register's disqualified mark, {len(conf)} on a charity confirmed to the "
                    "subject: " + "; ".join(f"{it['statement']} ({it['dates']['text']}" + (f"; near: {it.get('reason')})" if it["grade"] == "near" else ")")
                                            for it in marked[:EXAMPLES])
                    + ("" if len(conf) == len(marked) else f"; a row matched by name: {CHARITY_BY_NAME}"),
                    citations=tuple(it["ref"] for it in marked), scope="entity" if conf else "near")
    if _company_start(report):
        own = _company_charities(report)
        return flag("charity-integrity-marks", V, "blocked", MARK_SEVERITY, f"{NOT_FOLLOWED}: the charity officer rows under their names are not "
                    "read" + (f"; the {sum(len(o) for _, o in own)} officer row(s) on the company's charity carry no disqualified mark" if own else ""),
                    scope="officer-group")
    if _other_start(report):
        return flag("charity-integrity-marks", V, "blocked", MARK_SEVERITY, _other_start(report))
    why = _charity_unread(report)
    if why:
        return flag("charity-integrity-marks", V, "blocked", MARK_SEVERITY, f"{why}, so no clear is given")
    return flag("charity-integrity-marks", V, "clear", MARK_SEVERITY, "no charity officer row carrying the person's name has the register's "
                "disqualified mark", sources_held=(CHARITY_HELD,))


def comcom_coverage(report):
    return flag("comcom-coverage", V, "blocked", "amber",
                "the Commerce Commission's cases and the Financial Markets Authority's warnings are held but not published (plan step 5.3); "
                "this check cannot run",
                sources_not_held=("Commerce Commission cases and FMA warnings (not yet published)",))


# ── the held registers add ──────────────────────────────────────────────────

def bankruptcy(report):
    conf = list(items(report, ("gazette_bankruptcies",), ("confirmed",)))
    nearby = list(items(report, ("gazette_bankruptcies",), ("near",)))
    live_c = [it for it in conf if not it.get("suppressed")]
    live_n = [it for it in nearby if not it.get("suppressed")]
    if live_c:
        return flag("bankruptcy", V, "fired", "red", f"{len(live_c)} Gazette bankruptcy notice(s) confirmed to the subject: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in live_c[:EXAMPLES]), citations=tuple(it["ref"] for it in live_c))
    if live_n:
        return flag("bankruptcy", V, "fired", "amber", f"{len(live_n)} Gazette bankruptcy notice(s) under a name near the subject's; a namesake's until confirmed",
                    citations=tuple(it["ref"] for it in live_n), scope="near")
    return flag("bankruptcy", V, "blocked", "red",
                "Gazette bankruptcy notices are published, but no link rule joins one to a person yet, so this report cannot see a bankruptcy; "
                "the blank is not a clear",
                sources_not_held=NOT_HELD_INSOLVENCY)


def public_life(report):
    office = list(items(report, PUBLIC_VIEWS, ("confirmed",)))
    money = list(items(report, MONEY_VIEWS, ("confirmed",)))
    if office or money:
        bits = []
        if office:
            bits.append(f"{len(office)} row(s) of public office: seats, candidacies, declared interests")
        if money:
            bits.append(f"{len(money)} row(s) of political money or a promoter's role")
        return flag("public-life", V, "fired", "info", "the subject has a public political record: " + "; ".join(bits)
                    + "; each listed in its section with its date", citations=tuple(it["ref"] for it in office + money))
    return flag("public-life", V, "clear", "info", "no seat, candidacy, declared interest, donation, loan or promoter's role confirmed to the subject",
                sources_held=("Electoral Commission returns and disclosures", "Candidates and the House", "MPs' declared interests",
                              "Register of Promoters"),
                sources_not_held=("a candidate's own return, not yet joined to a person", "MPs' and ministers' expenses, not yet readable by the report"))


def subject_hub(report):
    """The subject itself a professional director or a nominee: what its
    shared boards join means little (the hubs the walk met on others are
    listed by the memo under "hubs met")."""
    own = {report["subject"]["ref"]} | {m["ref"] for m in report.get("members", [])}
    mine = [h for h in report.get("hubs", []) if h["ref"] in own and h["kind"] in ("professional-director", "nominee", "crown")]
    if mine:
        kinds = sorted({h["kind"] for h in mine})
        return flag("subject-hub", V, "fired", "info", f"the subject is itself a hub ({', '.join(kinds)}): {mine[0]['text']}",
                    citations=tuple(sorted({h["ref"] for h in mine})))
    return flag("subject-hub", V, "clear", "info", "the subject is not a professional director, a nominee or the Crown on the rows held",
                sources_held=("pub.directors", "pub.groups"))


RULES = (subject_hub, prohibition, bankruptcy, liquidation_history, register_removals, namesake_exposure,
         charity_officer_roles, charity_integrity_marks, comcom_coverage, young_entity, public_life)
