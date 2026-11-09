"""The one report's checks (ruling 157, 9 November 2026): one set of red, amber
and clear checks, made by merging the checks of the retired use-case
templates 02 to 13 (their `rules.py`, `limits.md` and `checkpoint.list`,
frozen and read, never edited) with the diagnostic report's, each check once.

How the merge was made:

  - A check is a question, not a template's wording of it. Every retired
    function is mapped to the one combined check that asks its question
    (`MERGED`, held complete against the template folders by
    tests/test_checks_combined.py while they stand, and against the frozen
    inventory `RETIRED` after they go). Ten templates asked "has this person
    a Gazette prohibition?" nine times; here it is asked once.
  - A finding takes the highest severity any retired template gave the same
    finding (a director prohibition confirmed to the subject was red in every
    template that asked; an ended company was red in four and amber in five,
    and is red here). A check's clear and blocked severities follow.
  - Every check reads the built report by view, grade and the walk's own
    marks (`via`, `through`, `near_link`, `depth`, `rule`), never by a
    template's section names, so it reads the one report whatever its
    sections are called. A check that cannot see what it needs says so and
    is blocked, never clear (the contract's three statuses).
  - The use-case wording ("the counterparty", "the client") is the
    subject's here. A sign that belonged to one use case only (a care-named
    organisation, the firm's own client list) is kept as text where it is
    a fact, and as a source not held where it was an input the report never
    had (`registers-not-held`).
  - The common rules the contract runs for every template (group-standing,
    hubs-met, replaced-return) stay the contract's; the retired copies of
    them map there.

Pure: a built report in, a flag out (contract.flag). Version: V."""
from __future__ import annotations

import datetime as dt
import re

from products.report.contract import all_items, flag, items

V = "1.0"
EXAMPLES = 3

YOUNG_DAYS = 730          # registered under 24 months (every retired young-entity)
NAMESAKE_NOTE_AT = 5      # namesake rows set apart at which the report's caveat fires
NAMESAKE_PARTIAL_AT = 50  # past this many the report is declared partial
CHURN_DAYS = 365          # a current director appointed this recently counts toward churn
CHURN_AT = 2              # this many such directors fire churn
AT_START_DAYS = 30        # a director appointed this close to registration is the first board, not churn
RECENT_DAYS = 90          # a Gazette notice this recent is a recent adverse change
LEFT_WITHIN_DAYS = 365    # a role's filed end this close before an insolvency notice on the same company
PERIOD_SLACK_DAYS = 31    # a charity's newest return may end this far before the balance date due
FILE_WITHIN_DAYS = 183    # a charity's return is due within six months of its balance date
PHOENIX_DAYS = 365        # a going company registered this close to another's failure is set beside it

#: whether a published view holds a person's past roles with their end dates: the companies file lists current roles (and rows
#: that left it since July 2026, undated); the business-number register's past roles reach a person by name only. While False, a
#: check over a person's companies fires on what it sees and never clears (every retired template held the same).
HISTORY = False
PAST_NOT_HELD = ("the companies file lists current roles only: a company the person left, or that was struck off with them on it, is "
                 "not seen, nor its failure")

INSOLVENCY_KINDS = ("winding-up application", "receivership", "administration", "notice to creditors", "deed of company arrangement")
EVENT_KIND = {"removal": "removal", "dissolution": "dissolution", "restoration": "restoration", "overseas company": "an overseas company ceasing",
              "rectification": "the Registrar's rectification", "transfer out": "a transfer out of New Zealand", "amalgamation": "amalgamation"}
INSOLVENT_STATUS = re.compile(r"liquidation|receiv|administration|statutory management", re.I)
ENDED_STATUS = re.compile(r"^(removed|deregistered|dissolved|closed|cancelled|inactive|suspended)$", re.I)
GOING_STATUS = re.compile(r"^registered$", re.I)
TROUBLED = re.compile(r"liquidation|receivership|administration|removed|dissolved", re.I)
CUSTODIAL = re.compile(r"\b(nominees?|trustees?|trusts?|custodians?|custodial|fiduciary)\b", re.I)
PARTNERSHIP = re.compile(r"\b(limited partnership|l\.?p\.?)$|\blimited partnership\b", re.I)
OVERSEAS_FORM = re.compile(r"\b(pty\.? ?(ltd|limited)\.?|pte\.? ?(ltd|limited)\.?|llc|l\.l\.c\.|gmbh|ag|s\.a\.?|b\.?v\.?|n\.v\.?|nv|plc|"
                           r"inc\.?|corp\.?|corporation|s\.a\.r\.l\.?|sarl|kk|k\.k\.|sdn\.? bhd\.?|bhd\.?)$", re.I)
NAME_RULES = re.compile(r"^(name-only|full-name|owner-full-name|organisation-name|company-name|filed-name|candidate-name-form|coupled-name|"
                        r"same-name|printed-name)")
HUB_KINDS = ("professional-director", "nominee", "crown")
OFFICE_HUBS = ("busy-address", "thousand-address")

NOTICE_VIEWS = ("gazette_liquidations", "gazette_company_notices", "company_insolvencies")
ROLE_VIEWS = ("directors", "shareholders", "society_officers", "charity_officers", "limited_partnership_partners")
COURT_VIEWS = ("court_judgment_parties", "court_people")
MONEY_VIEWS = ("party_return_donors", "party_return_loans", "disclosures", "disclosure_items", "candidate_return_donors", "promoter_people")
OFFICE_VIEWS = ("members", "candidates", "mp_interest_returns", "mp_interests")

COMPANIES_HELD = "Companies register (pub.companies, pub.directors, pub.shareholders)"
GAZETTE_HELD = "New Zealand Gazette liquidation and company notices (pub.gazette_liquidations, pub.gazette_company_notices), and the companies file's insolvency appointments (pub.company_insolvencies)"
NOTICES_HELD = "New Zealand Gazette company notices (pub.gazette_company_notices)"
STATES_HELD = "the earlier states a later monthly file changed (pub.company_states)"
OFFICES_HELD = "Companies register addresses (pub.company_addresses)"
LINKS_HELD = ("pub.links", "pub.groups")
CHARITIES_HELD = "Charities Register (pub.charities, pub.charity_officers, pub.charity_returns)"
SOCIETIES_HELD = "Incorporated Societies Register officers (pub.society_officers)"
POSSESSIONS_HELD = "New Zealand Gazette mortgagee possessions (pub.gazette_possessions), the company mortgagor and lender by register key"
PERSON_MORTGAGORS = "a mortgagee possession whose mortgagor is a person (the name and the property stay in the gazette lane's private tables)"
CHANGE_HISTORY = "the companies change history: earlier names, trading names, earlier directors and offices"
LP_HELD = "the general partners the business-number register states for a limited partnership (pub.limited_partnership_partners)"
LP_LIMITED = "a limited partnership's limited partners: the register publishes its general partners only"
FOR_WHOM = "for whom a holder of record holds, and a trust's trustees, settlors and beneficiaries: New Zealand keeps no register of them"
COURT_HELD = ("the courts corpus held: the judgments' parties as each heading names them (pub.court_judgment_parties) and the people "
              "a court document names (pub.court_people)",)
COURT_NOT_HELD = ("court judgments the corpus does not carry: most of the High Court's, the Court of Appeal's and the District Court's, "
                  "and most tribunals'",)
REG_HELD = {"worksafe_parties": "WorkSafe New Zealand's court summaries and enforceable undertakings (pub.worksafe_parties)",
            "commerce_commission_parties": "the Commerce Commission's cases (pub.commerce_commission_parties)",
            "fma_parties": "the Financial Markets Authority's actions (pub.fma_parties)",
            "overseas_investment_parties": "the Overseas Investment Office's decision summaries (pub.overseas_investment_parties)",
            "sanctions_listings": "the sanctions lists copied by ruling 132 (pub.sanctions_listings)",
            "insolvency_people": "the Insolvency Register's people (pub.insolvency_people)",
            "insolvency_companies": "the Insolvency Register's companies (pub.insolvency_companies)",
            "rea_parties": "the Real Estate Authority's decisions (pub.rea_parties)",
            "building_practitioner_decisions": "the Building Practitioners Board's decisions for three years from each (pub.building_practitioner_decisions)",
            "gazette_prohibitions": "New Zealand Gazette director prohibitions (pub.gazette_prohibitions)",
            "gazette_bankruptcies": "New Zealand Gazette bankruptcy notices (pub.gazette_bankruptcies)",
            "gazette_liquidators": "New Zealand Gazette liquidators (pub.gazette_liquidators)",
            "award_suppliers": "government contract award notices as GETS publishes them (pub.award_suppliers)",
            "retirement_villages": "the retirement villages file (pub.retirement_villages)"}
#: the sources no lane holds that a retired template's check named, each once, with the question it would answer
NOT_HELD = (
    ("securities", "the Personal Property Securities Register", "who holds a registered security over a company's assets, and since when"),
    ("change-history", CHANGE_HISTORY, "a firm that failed under one name and trades under another, by its history"),
    ("credit-bureau", "the credit bureaux (not a public register)", "payment defaults and credit enquiries"),
    ("interface", "the business-number interface check (plan step 5.5)", "what the register filed after the latest monthly file held"),
    ("for-whom", FOR_WHOM, "the people a holder of record holds for"),
    ("mpi", "MPI's prosecutions and animal-tracing enforcement (not published as data)", "a farming counterparty's enforcement record"),
    ("hdc", "the Health and Disability Commissioner's decisions", "a provider found in breach of the Code of Rights"),
    ("certification", "rest home and hospital certification audits", "a care provider's certification and its corrective actions"),
    ("providers", "the Ministry of Health's provider registers", "which premises an operator is certified to run"),
    ("aged-care", "the Aged Care Commissioner's reports", "the Commissioner's findings on a provider"),
    ("consents", "building consents and code compliance certificates", "what a project was consented to build, and whether it was signed off"),
    ("client-list", "a firm's own client and matter list (an input this report does not take)", "a conflict with the firm's clients"),
)
NOT_HELD_INSOLVENCY = ("court judgments the corpus does not carry",)


# ── reading the report ──────────────────────────────────────────────────────

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


def _row(it) -> dict:
    return it.get("row") or {}


def _walk(report) -> dict:
    return report.get("walk") or {}


def _subject(report) -> dict:
    return report["subject"]


def _key(ref: str) -> str:
    return ref.split(":", 1)[1] if ":" in ref else ref


def company_start(report) -> bool:
    return _subject(report)["view"] == "companies"


def person_start(report) -> bool:
    """A person row, or a filed row that takes the group of the person row a confirmed link names."""
    return _subject(report)["kind"] == "person" or bool((report.get("group") or {}).get("via"))


def organisation_start(report) -> bool:
    return _subject(report)["kind"] == "organisation"


def other_start(report):
    """Why a check over a person's or a company's record cannot run from this start, or None."""
    if company_start(report) or person_start(report):
        return None
    s = _subject(report)
    article = "an" if s["kind"][:1] in "aeiou" else "a"
    return (f"the report starts from {article} {s['kind']} row (pub.{s['view']}), not a person or a company: the record this check reads "
            f"is not walked from it, so no clear is given; start the report from a person row or from the company")


def _live(xs):
    return [it for it in xs if not it.get("suppressed")]


def _name(it) -> str:
    return it.get("title") or it["ref"]


def _status(it) -> str:
    return (_row(it).get("status") or "").strip()


def ending(it) -> str:
    """A company's standing as its register status files it: insolvent, ended or going."""
    st = _status(it)
    if INSOLVENT_STATUS.search(st):
        return "insolvent"
    if ENDED_STATUS.match(st) or _date(_row(it).get("removed_on")):
        return "ended"
    return "going" if GOING_STATUS.match(st) or not st else "ended"


def company_of(it) -> str:
    """The company (or body) a role, holding, office or notice sits on, as a ref."""
    if it.get("entity"):
        return it["entity"]["ref"]
    key = _row(it).get("entity_key") or _row(it).get("register_key")
    if key:
        return f"companies:{key}"
    return it.get("via") or ""


def on_subject(report, it) -> bool:
    return it.get("via") == _subject(report)["ref"] or (_row(it).get("register_key") or "") == _key(_subject(report)["ref"]) \
        or (it["view"] == "company_insolvencies" and company_of(it) == _subject(report)["ref"])


def companies(report, grades=("confirmed",)):
    """The companies the walk reached, other than the start; never one reached through an officer or up the chain."""
    return [it for it in items(report, ("companies",), grades) if it["ref"] != _subject(report)["ref"]
            and not it.get("through") and not it.get("depth")]


def through_officer(report, views, own_only=True):
    """Rows reached through an officer the walk followed from an organisation start; `own_only` keeps the officer's own rows
    (a confirmed link's), never a near link's or a name's."""
    return [it for it in items(report, views) if it.get("through") and not it.get("above") and not it.get("beside")
            and (not own_only or not it.get("near_link"))]


def notices(report, grades=("confirmed",)):
    return list(items(report, NOTICE_VIEWS, grades))


def is_insolvency(it) -> bool:
    """A notice that is an insolvency: a liquidator's appointment (the Gazette's, or one the companies file lists that follows no
    resolution of solvency), or a company notice of an insolvency kind that is not a receiver ceasing to act."""
    r = _row(it)
    if it["view"] == "gazette_liquidations":
        return True
    if it["view"] == "company_insolvencies":
        return not r.get("resolution_of_solvency")
    return it["view"] == "gazette_company_notices" and r.get("kind") in INSOLVENCY_KINDS and "ceas" not in (r.get("action") or "").lower()


def is_removal(it) -> bool:
    action = (_row(it).get("action") or "").lower()
    return it["view"] == "gazette_company_notices" and _row(it).get("kind") == "removal" and "restor" not in action and "revocation" not in action


def is_event(it) -> bool:
    return it["view"] == "gazette_company_notices" and not is_insolvency(it) and (_row(it).get("kind") or "") not in INSOLVENCY_KINDS


def notice_kind(it) -> str:
    r = _row(it)
    if it["view"] == "gazette_liquidations":
        return "liquidation"
    if it["view"] == "company_insolvencies":
        return f"{(r.get('insolvency_type') or 'insolvency').lower()} (the companies file)"
    kind, action = r.get("kind") or "", (r.get("action") or "").lower()
    if "restor" in action or "revocation" in action:
        return "restoration"
    return EVENT_KIND.get(kind, kind or "notice")


def failure_date(it):
    r = _row(it)
    if it["view"] in ("gazette_liquidations", "company_insolvencies"):
        return _date(r.get("appointed_on")) or _date(r.get("published_on"))
    if (r.get("event_basis") or "") == "appointment":
        return _date(r.get("event_on")) or _date(r.get("published_on"))
    return _date(r.get("published_on")) or _date(r.get("filed_on"))


def failures(report, cos: list, grades=("confirmed",)) -> dict:
    """{company ref: {'company', 'date', 'kind', 'evidence'}} for each company of `cos` that failed: an insolvency (a notice, or the
    status alone, undated) or a removal; the date is the earliest a notice gives; an insolvency outranks a removal."""
    by_ref = {it["ref"]: it for it in cos}
    out = {}
    for it in cos:
        if ending(it) == "insolvent":
            out[it["ref"]] = {"company": it, "date": None, "kind": "insolvency", "evidence": [it["ref"]]}
    for n in notices(report, grades):
        c = n.get("via") if n.get("via") in by_ref else company_of(n)
        if c not in by_ref:
            continue
        kind = "insolvency" if is_insolvency(n) else "removal" if is_removal(n) else None
        if not kind:
            continue
        e = out.setdefault(c, {"company": by_ref[c], "date": None, "kind": kind, "evidence": [c]})
        if kind == "removal" and e["kind"] == "insolvency":
            continue
        if kind == "insolvency" and e["kind"] == "removal":
            e.update(kind="insolvency", date=None)
        e["evidence"].append(n["ref"])
        d = failure_date(n)
        if d and (e["date"] is None or d < e["date"]):
            e["date"] = d
    return out


def walk_short(report) -> bool:
    w = _walk(report)
    return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))


def _short_text(report) -> str:
    w = _walk(report)
    n = (w.get("entities_not_expanded") or 0) + (w.get("entities_omitted") or 0)
    return f"; the walk did not read the notices on {n:,} further company(ies)" if n else ""


def clear_or_past(rule, severity, text, **kw):
    """A clear over the person's companies, or, while past roles are not held, a blocked flag saying what was seen."""
    if HISTORY:
        return flag(rule, V, "clear", severity, text, **kw)
    kw.pop("sources_held", None)
    return flag(rule, V, "blocked", severity, f"{text}; but {PAST_NOT_HELD}: no clear is given", **kw)


def _counted(xs, label) -> str:
    counts = {}
    for it in xs:
        counts[label(it)] = counts.get(label(it), 0) + 1
    return ", ".join(f"{n} {k}" for k, n in sorted(counts.items()))


def _lines(xs, fmt, n=EXAMPLES) -> str:
    return "; ".join(fmt(it) for it in xs[:n]) + (f"; and {len(xs) - n} more" if len(xs) > n else "")


def _cites(*groups) -> tuple:
    return tuple(dict.fromkeys(r for g in groups for r in g))


def _reads(report, view) -> bool:
    reads = {r["view"] for r in (report.get("template") or {}).get("reads", [])}
    return not report.get("template") or view in reads


def stage_one(report) -> bool:
    """True on a first-stage report (ruling 151): near links are not followed; what a check would read from them waits for stage 2."""
    return bool((_walk(report).get("stage1") or {}).get("stage") == 1)


def _near_wait(report, what: str) -> str:
    n = (_walk(report).get("stage1") or {}).get("near_set_aside", 0)
    return (f"{what} is read from the near links, which the first stage does not follow ({n:,} near link(s) set aside for the second "
            f"stage, on request)")


def _company_holder(it) -> bool:
    return (_row(it).get("shareholder_type") or "").strip().lower() not in ("individual", "person")


def _holder_name(it) -> str:
    return _row(it).get("name") or _row(it).get("full_name") or it.get("title") or ""


# ── identity, hubs, coverage ────────────────────────────────────────────────

def subject_hub(report):
    if other_start(report):
        return flag("subject-hub", V, "blocked", "amber", other_start(report))
    own = {_subject(report)["ref"]} | {m["ref"] for m in report.get("members", [])}
    mine = [h for h in report.get("hubs", []) if h["ref"] in own and h["kind"] in HUB_KINDS]
    s = _subject(report)
    named = CUSTODIAL.search(_row(s).get("name") or _row(s).get("full_name") or "") if not s.get("suppressed") else None
    if mine or named:
        kinds = sorted({h["kind"] for h in mine} | ({"named as a nominee, trustee or custodian"} if named else set()))
        return flag("subject-hub", V, "fired", "amber", f"the subject is itself a holder for others or a hub ({', '.join(kinds)}): what it "
                    "holds is held as the register states it, and a connection through it means little on its own",
                    citations=tuple(sorted({h["ref"] for h in mine} | ({s["ref"]} if named else set()))))
    return flag("subject-hub", V, "clear", "amber", "the subject is not named as a nominee, trustee or custodian, and is not a professional "
                "director or the Crown on the rows held", sources_held=("pub.directors", "pub.shareholders", "pub.groups"))


def namesake_exposure(report):
    """The report's own uncertainty: namesakes set apart (rows reached by a name only), near rows elsewhere, links and group rows past
    the walk's limits, a contested group; on a first-stage report, the near links set aside for the second stage."""
    near_rows = [it for it in items(report, None, ("near",)) if not it.get("through")]
    namesakes = [it for it in near_rows if NAME_RULES.match(it.get("rule") or "")]
    others = [it for it in near_rows if it not in namesakes]
    w, g = _walk(report), report.get("group") or {}
    aside = (w.get("stage1") or {}).get("near_set_aside", 0)
    bits = []
    count = len(namesakes) + aside
    if count >= NAMESAKE_PARTIAL_AT and len(namesakes) >= NAMESAKE_PARTIAL_AT:
        bits.append(f"{count:,} namesake row(s) or near link(s) set apart: the name is common, and this report is partial; confirm the "
                    "entity by a second fact (a business number, a date of appointment) before relying on any row")
    elif count >= NAMESAKE_PARTIAL_AT:
        bits.append(f"{count:,} near link(s) met on the subject and the people followed, set apart: what they would add is not on this "
                    "report")
    elif count >= NAMESAKE_NOTE_AT:
        bits.append(f"{count:,} namesake row(s) or near link(s) set apart")
    if aside:
        bits.append(f"{aside:,} near link(s) are held for the second stage, on request, and none is shown here")
    if others:
        bits.append(f"{len(others)} near row(s) in the record sections, each with its reason")
    if w.get("links_omitted"):
        bits.append(f"{w['links_omitted']:,} link(s) past the walk's limit, not read")
    if g.get("omitted"):
        bits.append(f"{g['omitted']:,} row(s) of the group past the walk's limit, not listed")
    if g.get("contested"):
        bits.append("the group is contested as a whole")
    if bits:
        partial = count >= NAMESAKE_PARTIAL_AT or g.get("contested")
        return flag("namesake-exposure", V, "fired", "amber" if partial else "info", "the report's own uncertainty: " + "; ".join(bits),
                    citations=tuple(it["ref"] for it in namesakes + others) or (_subject(report)["ref"],))
    return flag("namesake-exposure", V, "clear", "amber", f"low namesake exposure: {len(namesakes)} namesake row(s) set apart and every link read",
                sources_held=LINKS_HELD)


def walk_coverage(report):
    """What the walk did not read: organisations listed and not expanded, past the limit, officers not followed, and the first
    stage's levels and hubs not taken further."""
    w = _walk(report)
    st = w.get("stage1") or {}
    bits = []
    if w.get("entities_not_expanded"):
        bits.append(f"{w['entities_not_expanded']:,} organisation(s) listed with their status, their notices, offices and officers not read")
    if w.get("entities_omitted"):
        bits.append(f"{w['entities_omitted']:,} organisation(s) past the walk's limit, not listed")
    if w.get("officers_omitted"):
        bits.append(f"{w['officers_omitted']} officer(s) past the first {(w.get('limits') or {}).get('officers', 12)} not followed")
    if w.get("officers_suppressed"):
        bits.append(f"{w['officers_suppressed']} suppressed officer(s) not followed")
    if st.get("cut"):
        nxt = [f"{st[k]:,} {noun}" for k, noun in (("beyond_entities", "organisation(s)"), ("beyond_people", "person(s)")) if st.get(k)]
        bits.append(f"the confirmed links go on past the first stage's depth of {st.get('depth')} hop(s): {' and '.join(nxt)} at the next "
                    "hop are counted, not listed")
    if st.get("hubs_not_expanded"):
        bits.append(f"{st['hubs_not_expanded']:,} hub(s) listed and not followed further (an organisation with more than "
                    f"{st.get('hub_people')} people on it, or a person on more than {st.get('hub_entities')} organisations)")
    if st.get("omitted"):
        bits.append(f"{st['omitted']:,} row(s) of the first stage past its limit, not listed")
    if bits:
        return flag("walk-coverage", V, "fired", "amber", "the walk did not read the whole web: " + "; ".join(bits)
                    + "; start a report from each organisation or person left out", citations=(_subject(report)["ref"],))
    return flag("walk-coverage", V, "clear", "amber", "every organisation the walk reached was read for its notices, office and officers",
                sources_held=("pub.companies", "pub.gazette_liquidations", "pub.gazette_company_notices", "pub.company_addresses", "pub.directors"))


def past_roles(report):
    """Past roles and holdings with their end dates: not held, so the checks over a person's companies never clear."""
    if HISTORY:
        return flag("past-roles", V, "clear", "amber", "past roles and holdings are published with their filed end dates", sources_held=(COMPANIES_HELD,))
    left = [it for it in all_items(report).values() if it["view"] in ("directors", "shareholders") and it["grade"] == "confirmed"
            and not _row(it).get("in_latest", True)]
    seen = f"; {len(left)} of the rows listed left the file since July 2026 and carry no end date" if left else ""
    whose = "the entity's past officers and holders" if company_start(report) else "the person's past directorships and holdings"
    return flag("past-roles", V, "blocked", "amber", f"{whose} are not held: {PAST_NOT_HELD}{seen}; a phoenix whose people left the failed "
                "company before it failed, or were struck off with it, cannot be seen here",
                sources_not_held=("past directorships and shareholdings with their end dates",))


def registers_not_held(report):
    """Every source a retired template's check needed that no lane holds, said once: none of them can be a clear."""
    return flag("registers-not-held", V, "blocked", "red", "not held, so no finding here is a finding of none: "
                + "; ".join(f"{what} ({name})" for _, name, what in NOT_HELD), sources_not_held=tuple(name for _, name, _ in NOT_HELD))


# ── the entity's own standing ───────────────────────────────────────────────

def entity_status(report):
    """The start's own register status, its earlier states, and an insolvency or removal notice on it the file does not yet show."""
    s = _subject(report)
    if person_start(report):
        return flag("entity-status", V, "blocked", "info", "the report starts from a person: a register status is an organisation's; the "
                    "person's companies are read by companies-standing")
    if s["view"] in ("charities", "societies", "limited_partnerships"):
        st = _status(s) or "not stated"
        ended = bool(_date(_row(s).get("deregistered_on")) or _date(_row(s).get("removed_on"))) or bool(re.search(r"deregist|remov|dissol|wound", st, re.I))
        if ended:
            return flag("entity-status", V, "fired", "red", f"the register gives the body the status {st!r}", citations=(s["ref"],))
        return flag("entity-status", V, "clear", "red", f"the body is {st!r} on its register", sources_held=(f"pub.{s['view']}",))
    if not company_start(report):
        return flag("entity-status", V, "blocked", "red", other_start(report) or "the start is not an organisation row")
    r = _row(s)
    own = [n for n in notices(report) if on_subject(report, n) and not n.get("above")]
    ins = [n for n in own if is_insolvency(n)]
    rem = [n for n in own if is_removal(n)]
    earlier = [it for it in items(report, ("company_states",)) if _row(it).get("entity_key") == r.get("key") or it.get("via") == s["ref"]]
    st, end = ending(s), _status(s) or "no status"
    kind = r.get("entity_type") or "entity"
    reg, removed = _date(r.get("registered_on")), _date(r.get("removed_on"))
    when = (f"registered {reg.isoformat()}" if reg else "registration date not stated") + (f", removed {removed.isoformat()}" if removed else "")
    troubled = [it for it in earlier if TROUBLED.search(_status(it))]
    was = (f"; earlier states: {_counted(earlier, lambda it: _status(it) or 'no status')}" if earlier else "")
    cites = _cites([s["ref"]], [n["ref"] for n in ins + rem], [it["ref"] for it in earlier])
    if st == "insolvent" or ins:
        gap = ("; the latest file still states " + repr(end) + ": the Gazette is read daily and the companies file monthly, so the notice "
               "is newer than the file") if ins and st != "insolvent" else ""
        first = min(ins, key=lambda n: failure_date(n) or dt.date.max) if ins else None
        return flag("entity-status", V, "fired", "red", f"the entity's register status is {end!r} ({kind}; {when})"
                    + (f"; {len(ins)} insolvency notice(s) on it, the first {notice_kind(first)}, {first['dates']['text']}" if first else "")
                    + gap + was, citations=cites, scope="entity")
    if st == "ended":
        return flag("entity-status", V, "fired", "red", f"the entity is no longer a registered entity: status {end!r} ({kind}; {when})"
                    + (f"; {len(rem)} removal notice(s) on it" if rem else "") + "; a removal from the register is not an insolvency" + was,
                    citations=cites, scope="entity")
    if not r.get("in_latest", True):
        return flag("entity-status", V, "fired", "amber", f"the entity is not in the latest companies file; its last status was {end!r} "
                    f"({kind}; {when}){was}", citations=cites, scope="entity")
    pending = [n for n in rem if (_date(_row(n).get("event_on")) or dt.date.min) >= _as_of(report)]
    if pending or troubled:
        return flag("entity-status", V, "fired", "amber", f"the entity is {end!r} in the latest file ({kind}; {when})"
                    + (f"; {len(pending)} notice(s) of an intention to remove it whose last day for objections has not passed" if pending else "")
                    + (f"; {len(troubled)} earlier state(s) of an insolvency or a removal a later file changed" if troubled else "") + was,
                    citations=cites, scope="entity")
    if not GOING_STATUS.match(_status(s)) and _status(s):
        return flag("entity-status", V, "fired", "amber", f"the companies file gives a status this check does not know: {end!r} ({kind}; {when})",
                    citations=cites, scope="entity")
    if rem or earlier:
        return flag("entity-status", V, "fired", "info", f"the entity is {end!r} in the latest file ({kind}; {when})"
                    + (f"; {len(rem)} notice(s) of an intention to remove it were published and the file still states {end!r}" if rem else "") + was,
                    citations=cites, scope="entity")
    return flag("entity-status", V, "clear", "red", f"the entity is {end!r} in the latest file ({kind}; {when}), with no earlier state and no "
                "insolvency or removal notice on it", sources_held=(COMPANIES_HELD, STATES_HELD, GAZETTE_HELD), scope="entity")


def young_entity(report):
    """Registered under 24 months: amber on the entity, info on the person's going companies; a short record is a short record."""
    as_of = _as_of(report)
    if other_start(report):
        return flag("young-entity", V, "blocked", "amber", other_start(report))
    if company_start(report):
        s = _subject(report)
        reg = _date(_row(s).get("registered_on"))
        if not reg:
            return flag("young-entity", V, "blocked", "amber", "the companies file states no registration date for the entity", scope="entity")
        days = (as_of - reg).days
        if days < YOUNG_DAYS:
            return flag("young-entity", V, "fired", "amber", f"the entity was registered {reg.isoformat()}, {days} days before {as_of.isoformat()} "
                        f"(under {YOUNG_DAYS} days): a short record is a short record, not a finding", citations=(s["ref"],), scope="entity")
        return flag("young-entity", V, "clear", "amber", f"the entity was registered {reg.isoformat()}, {days} days before {as_of.isoformat()}",
                    sources_held=("Companies register registration dates (pub.companies)",), scope="entity")
    pool = [it for it in companies(report) if ending(it) == "going"]
    young = [(it, _date(_row(it).get("registered_on"))) for it in pool]
    young = sorted([(it, reg) for it, reg in young if reg and (as_of - reg).days < YOUNG_DAYS], key=lambda x: x[1], reverse=True)
    if young:
        return flag("young-entity", V, "fired", "info", f"{len(young)} going company(ies) the person has a confirmed row on were registered under "
                    f"{YOUNG_DAYS} days before {as_of.isoformat()}: " + _lines(young, lambda x: f"{_name(x[0])} (registered {x[1].isoformat()})"),
                    citations=tuple(it["ref"] for it, _ in young), scope="officer-group")
    if walk_short(report):
        return flag("young-entity", V, "blocked", "info", "the walk left companies past its limit, and their registration dates are not read")
    return flag("young-entity", V, "clear", "info", "no going company the person has a confirmed row on was registered under 24 months ago",
                sources_held=("Companies register registration dates (pub.companies)",))


def _current(it) -> bool:
    return bool(_row(it).get("in_latest", True)) and not _row(it).get("ended_on")


def officers_of_record(report):
    """Who the companies file names on the company now: no current director on a going company is a question; one person the sole
    director and the sole holder of record is a one-person vehicle's shape, read as a shape."""
    if other_start(report):
        return flag("officers-of-record", V, "blocked", "amber", other_start(report), scope="entity")
    if not company_start(report):
        return flag("officers-of-record", V, "clear", "amber", "the subject is a person: its own roles are listed in the companies sections",
                    sources_held=(COMPANIES_HELD,), scope="entity")
    s = _subject(report)
    r = _row(s)
    if "partnership" in (r.get("entity_type") or "").lower():
        gp = [it for it in _live(items(report, ("limited_partnership_partners",), ("confirmed",))) if (it.get("via") or "").startswith("limited_partnerships:")]
        if not gp:
            return flag("officers-of-record", V, "blocked", "amber", "a limited partnership has general and limited partners, not directors; the "
                        "walk reached no general partner the register states for it", sources_held=(LP_HELD,), sources_not_held=(LP_LIMITED,), scope="entity")
        now = [it for it in gp if _row(it).get("current")]
        return flag("officers-of-record", V, "clear", "amber", f"{len(now)} current general partner(s) and {len(gp) - len(now)} past, as the "
                    "register states them", sources_held=(LP_HELD,), sources_not_held=(LP_LIMITED,), scope="entity")
    on = [it for it in all_items(report).values() if it.get("via") == s["ref"] and not it.get("through")]
    dirs = [it for it in on if it["view"] == "directors"]
    holders = [it for it in on if it["view"] == "shareholders"]
    now = [it for it in dirs if _current(it)]
    holders_now = [it for it in holders if _row(it).get("in_latest", True)]
    text = (f"{len(now)} current director(s) and {len(dirs) - len(now)} past or not in the latest file; {len(holders)} holder(s) of record, "
            f"{len(holders_now)} in the latest file")
    going = GOING_STATUS.match(_status(s)) and r.get("in_latest", True)
    if not now and going:
        return flag("officers-of-record", V, "fired", "amber", f"the companies file names no current director of the entity: {text}",
                    citations=tuple(it["ref"] for it in dirs) or (s["ref"],), scope="entity")
    if len(now) == 1 and len(holders_now) == 1 and not now[0].get("suppressed") and \
            " ".join((now[0].get("title") or "").lower().split()) == " ".join((holders_now[0].get("title") or "").lower().split()):
        return flag("officers-of-record", V, "fired", "info", f"one name is the entity's sole current director and its sole holder of record, "
                    "as the file states it: a one-person vehicle's shape; a holder of record may hold for others",
                    citations=(now[0]["ref"], holders_now[0]["ref"]), scope="entity")
    return flag("officers-of-record", V, "clear", "amber", text,
                sources_held=("Companies register directors and shareholders (pub.directors, pub.shareholders)",), scope="entity")


def officer_churn(report):
    """From a company: current directors appointed in the last CHURN_DAYS (the first board not counted), and director rows that left
    the latest file. Departures before July 2026 are not seen, so it fires or blocks and never clears."""
    if other_start(report):
        return flag("officer-churn", V, "blocked", "amber", other_start(report), scope="entity")
    if not company_start(report):
        return flag("officer-churn", V, "blocked", "amber", "a board's churn is read from the company: start a report from each company listed",
                    scope="entity")
    s = _subject(report)
    as_of, reg = _as_of(report), _date(_row(s).get("registered_on"))
    dirs = [it for it in all_items(report).values() if it["view"] == "directors" and it.get("via") == s["ref"] and not it.get("through")]
    now = [it for it in dirs if _current(it)]
    left = [it for it in dirs if not _current(it)]
    recent = []
    for it in now:
        start = _date(_row(it).get("appointed_on"))
        if start and (as_of - start).days <= CHURN_DAYS and not (reg and (start - reg).days <= AT_START_DAYS):
            recent.append((it, start))
    if len(recent) >= CHURN_AT or left:
        bits = []
        if recent:
            bits.append(f"{len(recent)} of {len(now)} current director(s) appointed in the {CHURN_DAYS} days before {as_of.isoformat()}, "
                        "after the first board")
        if left:
            bits.append(f"{len(left)} director row(s) left the companies file or carry an end date")
        return flag("officer-churn", V, "fired", "amber", "; ".join(bits) + "; a departure before July 2026 is not seen",
                    citations=tuple(it["ref"] for it, _ in recent) + tuple(it["ref"] for it in left), sources_not_held=(CHANGE_HISTORY,), scope="entity")
    return flag("officer-churn", V, "blocked", "amber", f"{len(recent)} of {len(now)} current director(s) appointed in the {CHURN_DAYS} days "
                f"before {as_of.isoformat()}, after the first board; but a departure before July 2026 is not seen, so no clear is given",
                sources_not_held=(CHANGE_HISTORY,), scope="entity")


def _files_of(report) -> list:
    out = set()
    for it in all_items(report).values():
        for col in ("first_file", "last_file", "file"):
            v = _row(it).get(col)
            if v:
                out.add(str(v))
    return sorted(out)


def monthly_changes(report):
    """Arrivals and departures of directors and holders, office moves and earlier states between the monthly files held, each dated
    by its file; with a since date, how many rows are new since it."""
    if other_start(report):
        return flag("monthly-changes", V, "blocked", "info", other_start(report))
    files = _files_of(report)
    since = f"; since {report['since']}: {report.get('new') or 0} row(s) new, {report.get('cannot_say') or 0} that cannot say" \
        if report.get("since") else ""
    if len(files) < 2:
        return flag("monthly-changes", V, "blocked", "info", f"the rows read name {len(files)} monthly file(s): a change between files needs two"
                    + since, sources_not_held=(CHANGE_HISTORY,))
    first, last = files[0], files[-1]
    ch = []
    for it in all_items(report).values():
        r = _row(it)
        if it["view"] == "company_states":
            ch.append((str(r.get("file") or ""), it, f"an earlier state of {it.get('entity_title') or _name(it)}: {_status(it) or 'no status'}"))
        elif it["view"] in ("directors", "shareholders", "company_addresses"):
            if r.get("first_file") and str(r["first_file"]) > first:
                ch.append((str(r["first_file"]), it, f"{it['view'].replace('_', ' ')[:-1]} row arrived on {it.get('entity_title') or 'a company'}"))
            if "in_latest" in r and not r.get("in_latest") and r.get("last_file"):
                ch.append((str(r["last_file"]), it, f"{it['view'].replace('_', ' ')[:-1]} row left {it.get('entity_title') or 'a company'}"))
    ch.sort(key=lambda c: c[0], reverse=True)
    if ch:
        return flag("monthly-changes", V, "fired", "info", f"{len(ch)} change(s) between the monthly files {first} and {last}, newest first: "
                    + _lines(ch, lambda c: f"{c[0]}: {c[2]}") + "; a change is dated to its file, a month and not a day" + since,
                    citations=_cites([c[1]["ref"] for c in ch]), sources_held=(COMPANIES_HELD, STATES_HELD), sources_not_held=(CHANGE_HISTORY,))
    return flag("monthly-changes", V, "clear", "info", f"no director, holder of record or registered office arrived or left between the monthly "
                f"files {first} and {last}, and no state a later file changed" + since, sources_held=(COMPANIES_HELD, STATES_HELD),
                sources_not_held=(CHANGE_HISTORY,))


def _in_scope(report) -> set:
    return {_subject(report)["ref"]} | ({it["ref"] for it in companies(report)} if person_start(report) else set())


def recent_adverse_change(report):
    """What turned lately: a Gazette insolvency notice in the last RECENT_DAYS (red), a removal notice in them (amber), the entity gone
    from the latest file (red), a director row gone from it (amber); each dated as its source dates it."""
    if other_start(report):
        return flag("recent-adverse-change", V, "blocked", "red", other_start(report))
    as_of = _as_of(report)
    since = as_of - dt.timedelta(days=RECENT_DAYS)
    scope = _in_scope(report)
    ns = [it for it in notices(report) if (it.get("via") in scope or company_of(it) in scope or on_subject(report, it)) and not it.get("through")]
    recent = [it for it in ns if (_date(_row(it).get("published_on")) or failure_date(it) or dt.date.min) >= since]
    insolv = [it for it in recent if is_insolvency(it)]
    removal = [it for it in recent if is_removal(it)]
    files = _files_of(report)
    gone = [it for it in [_subject(report)] + companies(report) if it["view"] == "companies" and it["ref"] in scope
            and "in_latest" in _row(it) and not _row(it).get("in_latest") and files and str(_row(it).get("last_file") or "") == files[-2:][0]]
    left = [it for it in all_items(report).values() if it["view"] == "directors" and company_of(it) in scope and "in_latest" in _row(it)
            and not _row(it).get("in_latest") and files and len(files) > 1 and str(_row(it).get("last_file") or "") == files[-2]]
    window = f"recent is a Gazette notice published on or after {since.isoformat()} ({RECENT_DAYS} days before {as_of.isoformat()})"
    if insolv or removal or gone or left:
        bits = [f"{_name(it)}: {notice_kind(it)}, {it['dates']['text']}" for it in (insolv + removal)[:EXAMPLES]]
        if gone:
            bits.append(f"{len(gone)} company(ies) gone from the latest file")
        if left:
            bits.append(f"{len(left)} director row(s) gone from the latest file")
        return flag("recent-adverse-change", V, "fired", "red" if insolv or gone else "amber",
                    f"{len(insolv)} insolvency notice(s), {len(removal)} removal notice(s), {len(gone)} company(ies) and {len(left)} director "
                    f"row(s) gone from the latest file: " + " | ".join(bits) + f"; {window}",
                    citations=_cites([it["ref"] for it in insolv + removal + gone + left]), scope="entity" if company_start(report) else "officer-group")
    if walk_short(report):
        return flag("recent-adverse-change", V, "blocked", "red", f"none seen on the companies the walk read, but it stopped before reading "
                    f"every company{_short_text(report)}; {window}")
    return flag("recent-adverse-change", V, "clear", "red", f"no Gazette insolvency or removal notice in the window, and nothing gone from the "
                f"latest file on {'the entity' if company_start(report) else 'the companies the person has a confirmed row on'}; {window}",
                sources_held=(GAZETTE_HELD, COMPANIES_HELD), sources_not_held=("the business-number interface check (plan step 5.5)",))


# ── insolvency and the companies' standing ──────────────────────────────────

def insolvency_notices(report):
    """Gazette insolvency notices (and the companies file's insolvency appointments) on the company started from, or on every company
    the person has a row on, each dated; from a company, an insolvent status with no notice held is red and undated."""
    if other_start(report):
        return flag("insolvency-notices", V, "blocked", "red", other_start(report), sources_not_held=NOT_HELD_INSOLVENCY)
    if company_start(report):
        own = sorted([n for n in notices(report) if is_insolvency(n) and on_subject(report, n) and not n.get("above")],
                     key=lambda n: (failure_date(n) is None, failure_date(n) or dt.date.min))
        up = [n for n in items(report, NOTICE_VIEWS) if n.get("above") and is_insolvency(n)]
        beside = (f"; beside it, {len(up)} on a company above in the holding chain, the holder's and not the entity's" if up else "")
        if own:
            return flag("insolvency-notices", V, "fired", "red", f"{len(own)} insolvency notice(s) on the entity ({_counted(own, notice_kind)}), "
                        "earliest first: " + _lines(own, lambda n: f"{notice_kind(n)}, {n['dates']['text']}") + beside,
                        citations=_cites([n["ref"] for n in own + up]), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
        if any(set(s.get("omitted_views") or ()) & set(NOTICE_VIEWS) for s in report["sections"]):
            return flag("insolvency-notices", V, "blocked", "red", "the entity has more notices than the walk lists; an insolvency could be "
                        "among those left out", scope="entity")
        if ending(_subject(report)) == "insolvent":
            return flag("insolvency-notices", V, "fired", "red", f"the companies file gives the entity the status {_status(_subject(report))!r} "
                        "and no insolvency notice on it is held: the status is undated here", citations=(_subject(report)["ref"],), scope="entity")
        return flag("insolvency-notices", V, "clear", "red", "no Gazette liquidation, receivership, administration, winding-up application, "
                    "creditors' notice or deed of company arrangement, and no insolvency appointment in the companies file, on the entity" + beside,
                    sources_held=(GAZETTE_HELD + ", joined to the company by its number",), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
    mine = {it["ref"] for it in companies(report)}
    conf = [n for n in notices(report) if is_insolvency(n) and not n.get("through") and (n.get("via") in mine or company_of(n) in mine)]
    nearby = [n for n in notices(report, ("near",)) if is_insolvency(n) and not n.get("through")]
    if conf:
        return flag("insolvency-notices", V, "fired", "red", f"{len(conf)} insolvency notice(s) on {len({n.get('via') for n in conf})} "
                    "company(ies) the person has a row on: " + _lines(conf, lambda n: f"{n.get('entity_title') or _name(n)}: {notice_kind(n)}, "
                                                                     f"{n['dates']['text']}") + _short_text(report),
                    citations=tuple(n["ref"] for n in conf), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if nearby:
        return flag("insolvency-notices", V, "fired", "amber", f"{len(nearby)} insolvency notice(s) on companies reached only through a near "
                    f"link or a person on them: not the person's own companies{_short_text(report)}", citations=tuple(n["ref"] for n in nearby),
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="near")
    if walk_short(report):
        return flag("insolvency-notices", V, "blocked", "red", "no insolvency notice on the companies the walk read, but it stopped before "
                    "reading every company the person has a row on", scope="officer-group")
    return clear_or_past("insolvency-notices", "red", "no insolvency notice on any company the person has a confirmed row on",
                         sources_held=(GAZETTE_HELD,), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")


def _namesake_past_failures(report):
    """The business-number register's roles under the subject's name, near, at a company that later failed (2 November 2026)."""
    seen, out = set(), []
    for it in items(report, ("company_lookup_roles", "company_lookup_holdings"), ("near",)):
        if it.get("failure") and not it.get("suppressed") and it["ref"] not in seen:
            seen.add(it["ref"])
            out.append(it)
    return out


def companies_standing(report):
    """How each company the person has a confirmed row on stands (insolvent, ended, going); from a company, how the other current
    companies of the officers the walk followed stand, and the insolvency notices on them, each the officer's and never the entity's;
    a namesake's past role at a company that later failed is said apart (2 November 2026)."""
    if other_start(report):
        return flag("companies-standing", V, "blocked", "amber", other_start(report), scope="officer-group")
    past = _namesake_past_failures(report)
    apart = (f"; apart, {len(past)} past role(s) under the name at a company that later failed, near: a namesake's until a rule confirms it"
             if past else "")
    if company_start(report):
        w = _walk(report)
        cos = [it for it in through_officer(report, ("companies",)) if it["ref"] != _subject(report)["ref"]]
        ns = [n for n in through_officer(report, NOTICE_VIEWS) if is_insolvency(n)]
        bad = [it for it in cos if ending(it) != "going"]
        if bad or ns:
            return flag("companies-standing", V, "fired", "amber", f"of {len(cos)} other company(ies) the {w.get('officers_followed', 0)} officer(s) "
                        f"followed sit on, {sum(1 for it in bad if ending(it) == 'insolvent')} have an insolvency status, "
                        f"{sum(1 for it in bad if ending(it) == 'ended')} are removed or ended, and {len(ns)} insolvency notice(s) are on them: "
                        + _lines(bad, lambda it: f"{_name(it)} ({_status(it) or 'no status'})") + "; each company is the officer's, not the entity's"
                        + apart, citations=_cites([it["ref"] for it in bad + ns + past]), scope="officer-group")
        if w.get("officers_omitted") or w.get("officers_suppressed"):
            return flag("companies-standing", V, "blocked", "amber", f"{w.get('officers_omitted', 0) + w.get('officers_suppressed', 0)} officer(s) "
                        "were not followed (past the limit or suppressed), so their companies are not read" + apart,
                        citations=tuple(it["ref"] for it in past))
        if past:
            return flag("companies-standing", V, "fired", "amber", f"none of the {len(cos)} other company(ies) the officers sit on has failed"
                        + apart, citations=tuple(it["ref"] for it in past), scope="near")
        return clear_or_past("companies-standing", "amber", f"each of the {len(cos)} other company(ies) the {w.get('officers_followed', 0)} "
                             "officer(s) followed sit on is registered, with no insolvency notice on it",
                             sources_held=(COMPANIES_HELD, GAZETTE_HELD), scope="officer-group")
    conf = companies(report)
    by = {"insolvent": [], "ended": [], "going": []}
    for it in conf:
        by[ending(it)].append(it)
    ended_near = [it for it in companies(report, ("near",)) if ending(it) != "going"]
    if by["insolvent"] or by["ended"]:
        bits = []
        if by["insolvent"]:
            bits.append(f"{len(by['insolvent'])} with an insolvency status: " + _lines(by["insolvent"], lambda it: f"{_name(it)} ({_status(it)})"))
        if by["ended"]:
            bits.append(f"{len(by['ended'])} removed or ended: " + _lines(by["ended"], lambda it: f"{_name(it)} ({_status(it) or 'no status'})"))
        bits.append(f"{len(by['going'])} registered")
        if ended_near:
            bits.append(f"and {len(ended_near)} more ended reached only through a near link or a person on them")
        return flag("companies-standing", V, "fired", "amber" if by["insolvent"] else "info",
                    f"of {len(conf)} company(ies) the person has a confirmed row on, " + "; ".join(bits) + apart,
                    citations=_cites([it["ref"] for it in by["insolvent"] + by["ended"] + past]), scope="officer-group")
    if ended_near or past:
        return flag("companies-standing", V, "fired", "amber", f"no confirmed company of the person's has ended; {len(ended_near)} reached only "
                    f"through a near link or a person on them have" + apart, citations=_cites([it["ref"] for it in ended_near + past]), scope="near")
    if walk_short(report):
        return flag("companies-standing", V, "blocked", "amber", f"the walk left {_walk(report).get('entities_omitted', 0):,} company(ies) past "
                    "its limit; their status is not read", scope="officer-group")
    return clear_or_past("companies-standing", "amber", f"each of the {len(conf)} company(ies) the person has a confirmed row on is registered"
                         if conf else "the person has no confirmed company row", sources_held=(COMPANIES_HELD,), scope="officer-group")


def repeat_failure(report):
    """Two or more of the person's companies failed (an insolvency status or notice), each with its date; from a company, two or more
    of the officers' other companies, the officers' and never the entity's."""
    if other_start(report):
        return flag("repeat-failure", V, "blocked", "red", other_start(report), scope="officer-group")
    past = _namesake_past_failures(report)
    if company_start(report):
        cos = [it for it in through_officer(report, ("companies",)) if it["ref"] != _subject(report)["ref"]]
        bad = {c: f for c, f in failures(report, cos, ("confirmed", "near")).items() if f["kind"] == "insolvency"}
        if len(bad) >= 2:
            return flag("repeat-failure", V, "fired", "amber", f"{len(bad)} of the officers' other companies have an insolvency status or "
                        "notice: " + _lines(list(bad.values()), lambda f: f"{_name(f['company'])} ({_iso(f['date'])})")
                        + "; each is the officer's, not the entity's", citations=_cites([r for f in bad.values() for r in f["evidence"]]),
                        scope="officer-group")
        return clear_or_past("repeat-failure", "red", f"{len(bad)} of the officers' other companies has an insolvency status or notice; no "
                             "repeat", sources_held=(GAZETTE_HELD, COMPANIES_HELD), scope="officer-group")
    bad = {c: f for c, f in failures(report, companies(report)).items() if f["kind"] == "insolvency"}
    nearby = {c: f for c, f in failures(report, companies(report, ("near",)), ("confirmed", "near")).items()
              if f["kind"] == "insolvency" and c not in bad}
    if len(bad) >= 2:
        ordered = sorted(bad.values(), key=lambda f: (f["date"] is None, f["date"] or dt.date.min))
        return flag("repeat-failure", V, "fired", "red", f"{len(bad)} of the person's companies have an insolvency status or notice: "
                    + " | ".join(f"{_name(f['company'])} ({_iso(f['date'])})" for f in ordered[:EXAMPLES + 1]),
                    citations=_cites([r for f in ordered for r in f["evidence"]]), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if len(bad) + len(nearby) + len(past) >= 2:
        return flag("repeat-failure", V, "fired", "amber", f"{len(bad)} confirmed company(ies) of the person's, {len(nearby)} reached only "
                    f"through a near link or a person on them, and {len(past)} past role(s) under the name have an insolvency: a namesake's or "
                    "an officer's until confirmed", citations=_cites([r for f in list(bad.values()) + list(nearby.values()) for r in f["evidence"]]
                                                                   + [it["ref"] for it in past]), scope="near")
    if walk_short(report):
        return flag("repeat-failure", V, "blocked", "red", f"{len(bad)} company(ies) with an insolvency on the companies the walk read, but it "
                    "stopped before reading every company the person has a row on", scope="officer-group")
    return clear_or_past("repeat-failure", "red", f"{'one' if bad else 'no'} company the person has a confirmed row on has an insolvency "
                         "status or notice; no repeat", sources_held=(GAZETTE_HELD, COMPANIES_HELD), sources_not_held=NOT_HELD_INSOLVENCY,
                         scope="officer-group")


def phoenix_signature(report):
    """A failed company beside a going company of the same person (from a person: their own; from a company: the entity beside the
    failed other companies of its officers), registered within PHOENIX_DAYS of the failure, nearest first; red on the person's own
    confirmed companies, amber through an officer."""
    if other_start(report):
        return flag("phoenix-signature", V, "blocked", "red", other_start(report), scope="officer-group")
    if company_start(report):
        s = _subject(report)
        reg = _date(_row(s).get("registered_on"))
        cos = [it for it in through_officer(report, ("companies",)) if it["ref"] != s["ref"]]
        failed = failures(report, cos, ("confirmed", "near"))
        pairs = [(f, (reg - f["date"]).days) for f in failed.values() if f["date"] and reg and abs((reg - f["date"]).days) <= PHOENIX_DAYS]
        if pairs:
            pairs.sort(key=lambda p: abs(p[1]))
            return flag("phoenix-signature", V, "fired", "amber", f"{len(pairs)} failed company(ies) of the officers' within {PHOENIX_DAYS} days of "
                        f"the entity's registration ({_iso(reg)}): " + _lines(pairs, lambda p: f"{_name(p[0]['company'])} failed {_iso(p[0]['date'])}, "
                                                                                         f"{p[1]} days before")
                        + "; the failed company is the officer's, never the entity's", citations=_cites([s["ref"]] + [r for f, _ in pairs for r in f["evidence"]]),
                        scope="officer-group")
        return clear_or_past("phoenix-signature", "red", f"no failed company of the officers' within {PHOENIX_DAYS} days of the entity's "
                             f"registration ({_iso(reg)}); {len(failed)} failed with no date in the window",
                             sources_held=(GAZETTE_HELD, COMPANIES_HELD), scope="officer-group")
    cos = companies(report)
    failed = failures(report, cos)
    going = [it for it in cos if ending(it) == "going" and it["ref"] not in failed]
    pairs = []
    for f in failed.values():
        for g in going:
            gr = _date(_row(g).get("registered_on"))
            if f["date"] and gr and abs((gr - f["date"]).days) <= PHOENIX_DAYS:
                pairs.append((f, g, (gr - f["date"]).days))
    if pairs:
        pairs.sort(key=lambda p: abs(p[2]))
        return flag("phoenix-signature", V, "fired", "red" if any(f["kind"] == "insolvency" for f, _, _ in pairs) else "amber",
                    f"{len(pairs)} pair(s) of the person's companies: a failed one beside a going one registered within {PHOENIX_DAYS} days: "
                    + _lines(pairs, lambda p: f"{_name(p[0]['company'])} ({p[0]['kind']}, {_iso(p[0]['date'])}) | {_name(p[1])} "
                                              f"(registered {_iso(_date(_row(p[1]).get('registered_on')))}, {p[2]:+d} days)")
                    + "; two dated facts side by side, nothing more", citations=_cites([r for f, g, _ in pairs for r in f["evidence"] + [g["ref"]]]),
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if walk_short(report):
        return flag("phoenix-signature", V, "blocked", "red", "the walk stopped before reading every company the person has a row on",
                    scope="officer-group")
    return clear_or_past("phoenix-signature", "red", f"of the person's {len(cos)} confirmed companies, {len(failed)} failed and none beside a "
                         f"going one registered within {PHOENIX_DAYS} days", sources_held=(GAZETTE_HELD, COMPANIES_HELD), scope="officer-group")


def left_before_notice(report):
    """A role whose end the register files within LEFT_WITHIN_DAYS before an insolvency notice on the same company. A role that left
    the file with no end filed cannot be placed, so it blocks a clear."""
    if company_start(report):
        return flag("left-before-notice", V, "blocked", "amber", f"an officer's past roles on other companies are not held: {PAST_NOT_HELD}",
                    scope="officer-group")
    if other_start(report):
        return flag("left-before-notice", V, "blocked", "amber", other_start(report), scope="officer-group")
    bad = failures(report, companies(report))
    roles = [it for it in all_items(report).values() if it["view"] in ("directors", "shareholders") and it["grade"] == "confirmed"]
    hits, unknown = [], []
    for c, f in bad.items():
        if f["kind"] != "insolvency" or not f["date"]:
            continue
        for r in [r for r in roles if company_of(r) == c]:
            end = _date(_row(r).get("ended_on"))
            if end is None:
                if not _row(r).get("in_latest", True):
                    unknown.append(r)
                continue
            gap = (f["date"] - end).days
            if 0 <= gap <= LEFT_WITHIN_DAYS:
                hits.append((r, end, f["date"], gap))
    if hits:
        return flag("left-before-notice", V, "fired", "amber", f"{len(hits)} of the person's roles end, as the register files them, within "
                    f"{LEFT_WITHIN_DAYS} days before an insolvency on the same company: "
                    + _lines(hits, lambda h: f"{h[0]['statement']}: end filed {h[1].isoformat()}, insolvency {h[2].isoformat()} ({h[3]} days apart)"),
                    citations=tuple(h[0]["ref"] for h in hits), scope="officer-group")
    if unknown:
        return flag("left-before-notice", V, "blocked", "amber", f"{len(unknown)} of the person's roles on a company with an insolvency left the "
                    "companies file with no end filed, so their end cannot be set beside the notice", scope="officer-group")
    return clear_or_past("left-before-notice", "amber", f"no role of the person's ends within {LEFT_WITHIN_DAYS} days before an insolvency "
                         "on the same company", sources_held=(GAZETTE_HELD, COMPANIES_HELD), scope="officer-group")


def register_events(report):
    """Removals, restorations, dissolutions, rectifications, amalgamations, transfers out: not insolvency. On the entity amber, on
    the person's companies info; an amalgamation's other companies are other rows of the notice, not reached."""
    if other_start(report):
        return flag("register-events", V, "blocked", "amber", other_start(report))
    conf = sorted([n for n in notices(report) if is_event(n) and not n.get("through") and not n.get("above")],
                  key=lambda n: _date(_row(n).get("published_on")) or dt.date.min, reverse=True)
    if company_start(report):
        own = [n for n in conf if on_subject(report, n)]
        if own:
            return flag("register-events", V, "fired", "amber", f"{len(own)} Gazette notice(s) on the entity ({_counted(own, notice_kind)}), newest "
                        "first: " + _lines(own, lambda n: f"{notice_kind(n)}, {n['dates']['text']}") + "; none is an insolvency, a restoration "
                        "reverses a removal, and an amalgamation's other companies are in the notice cited", citations=tuple(n["ref"] for n in own),
                        scope="entity")
        return flag("register-events", V, "clear", "amber", "no Gazette removal, restoration, dissolution, rectification, amalgamation or "
                    "transfer notice on the entity", sources_held=(NOTICES_HELD,), scope="entity")
    if conf:
        return flag("register-events", V, "fired", "info", f"{len(conf)} Gazette notice(s) ({_counted(conf, notice_kind)}) on "
                    f"{len({n.get('via') for n in conf})} company(ies) the person has a row on: "
                    + _lines(conf, lambda n: f"{n.get('entity_title') or _name(n)}, {n['dates']['text']}") + "; none is an insolvency",
                    citations=tuple(n["ref"] for n in conf), scope="officer-group")
    if walk_short(report):
        return flag("register-events", V, "blocked", "info", "the walk stopped before reading every company the person has a row on",
                    scope="officer-group")
    return clear_or_past("register-events", "info", "no Gazette removal, restoration, dissolution, rectification, amalgamation or transfer "
                         "notice on a company the person has a confirmed row on", sources_held=(NOTICES_HELD,), scope="officer-group")


def same_name_failed(report):
    """A company that only shares the name of the entity, or of one of the person's going companies, and failed: names only, amber at
    most. Read from the company-name near links, so on a first-stage report it waits for the second stage."""
    if other_start(report):
        return flag("same-name-failed", V, "blocked", "amber", other_start(report), scope="near")
    same = [it for it in items(report, ("companies",), ("near",)) if (it.get("rule") or "").startswith("company-name")]
    if not same and stage_one(report):
        return flag("same-name-failed", V, "blocked", "amber", _near_wait(report, "a company that only shares a name"), scope="near")
    failed = failures(report, same, ("confirmed", "near"))
    if failed:
        return flag("same-name-failed", V, "fired", "amber", f"{len(failed)} company(ies) that only share a name with "
                    f"{'the entity' if company_start(report) else 'a company of the person'} failed: "
                    + _lines(list(failed.values()), lambda f: f"{_name(f['company'])} ({f['kind']}, {_iso(f['date'])})")
                    + "; a company name is a name, never one firm", citations=_cites([r for f in failed.values() for r in f["evidence"]]), scope="near")
    if walk_short(report) or _walk(report).get("links_omitted"):
        return flag("same-name-failed", V, "blocked", "amber", "the walk left links or companies unread past its limit; a company of the same "
                    "name could be among them", scope="near")
    return flag("same-name-failed", V, "clear", "amber", f"none of the {len(same)} company(ies) of the same name the links lane joins has failed",
                sources_held=("pub.links (company-name rule)", GAZETTE_HELD), scope="near")


def practitioner_roles(report):
    """The subject named as liquidator in Gazette notices; and the practitioners on the insolvencies of the subject's companies, whether
    one practitioner recurs across them (the notices name them in pub.gazette_liquidators)."""
    if other_start(report):
        return flag("practitioner-roles", V, "blocked", "info", other_start(report))
    live = [it for it in _live(items(report, ("gazette_liquidators",))) if not it.get("through")]
    mine = [it for it in live if it["grade"] == "confirmed" and not it.get("via")]
    on_cos = [it for it in live if it.get("via")]
    names = {}
    for it in on_cos:
        names.setdefault(" ".join(_name(it).lower().split()), set()).add(it.get("via"))
    repeat = {n: v for n, v in names.items() if len(v) >= 2}
    bits, cites = [], []
    if mine:
        bits.append(f"named as liquidator in {len(mine)} Gazette notice(s): " + _lines(mine, lambda it: f"{_name(it)} ({it['dates']['text']})"))
        cites += [it["ref"] for it in mine]
    if repeat:
        bits.append(f"{len(repeat)} practitioner name(s) recur on the insolvency notices of two or more of the companies here")
        cites += [it["ref"] for it in on_cos if " ".join(_name(it).lower().split()) in repeat]
    if bits:
        return flag("practitioner-roles", V, "fired", "info", "; ".join(bits) + "; a practitioner acts for a company's creditors",
                    citations=_cites(cites))
    if _walk(report).get("links_omitted"):
        return flag("practitioner-roles", V, "blocked", "info", "the walk left links unread past its limit; an appointment could be among them")
    return flag("practitioner-roles", V, "clear", "info", "not named as liquidator in a Gazette notice the link rules join to the subject, and no "
                "practitioner recurs on the companies here", sources_held=(REG_HELD["gazette_liquidators"],),
                sources_not_held=("receivers and administrators named in notices (pub.gazette_practitioners: no link reaches them)",))


def mortgagee_possession(report):
    """A mortgagee's entry into possession (pub.gazette_possessions) where the mortgagor is the entity or a company the person is
    confirmed on: red on the entity's own, amber on the person's companies; a company here as the lender, or a near row: info. The
    property is never shown; a person mortgagor's name stays in the lane's private tables, so from a person none is blocked."""
    if other_start(report):
        return flag("mortgagee-possession", V, "blocked", "red", other_start(report), sources_not_held=(PERSON_MORTGAGORS,))
    s = _subject(report)["ref"]
    mine = {s} | {it["ref"] for it in companies(report)}
    def k(it, col):
        v = _row(it).get(col)
        return f"companies:{v}" if v else None
    ps = _live(items(report, ("gazette_possessions",)))
    own = [it for it in ps if it["grade"] == "confirmed" and k(it, "mortgagor_register_key") in mine]
    lender = [it for it in ps if it not in own and k(it, "mortgagee_register_key") in mine]
    other = [it for it in ps if it not in own and it not in lender]
    if own:
        on_entity = any(k(it, "mortgagor_register_key") == s for it in own)
        return flag("mortgagee-possession", V, "fired", "red" if on_entity else "amber", f"{len(own)} mortgagee entry(ies) into possession where "
                    f"the mortgagor is {'the entity' if on_entity else 'a company the person is confirmed on'}: "
                    + _lines(own, lambda it: f"{it['statement']} ({it['dates']['text']})") + "; the property is not shown",
                    citations=tuple(it["ref"] for it in own), sources_held=(POSSESSIONS_HELD,), sources_not_held=(PERSON_MORTGAGORS,))
    if lender or other:
        rows = lender + other
        return flag("mortgagee-possession", V, "fired", "info", f"{len(rows)} mortgagee entry(ies) into possession reached, none with the entity "
                    f"or the person's own companies as mortgagor ({len(lender)} with a company here as the lender, {len(other)} through a person "
                    "on them or near): " + _lines(rows, lambda it: f"{it['statement']} ({it['dates']['text']})"),
                    citations=tuple(it["ref"] for it in rows), sources_held=(POSSESSIONS_HELD,), sources_not_held=(PERSON_MORTGAGORS,))
    if company_start(report):
        return flag("mortgagee-possession", V, "clear", "red", "no mortgagee entry into possession in the Gazette names the entity as mortgagor",
                    sources_held=(POSSESSIONS_HELD,), sources_not_held=(PERSON_MORTGAGORS,))
    return flag("mortgagee-possession", V, "blocked", "red", "no mortgagee entry into possession names a company the person is confirmed on as "
                "mortgagor; one naming the person as mortgagor is not shown, so no clear is given", sources_held=(POSSESSIONS_HELD,),
                sources_not_held=(PERSON_MORTGAGORS,))


# ── notices on people, and the lists ────────────────────────────────────────

def _in_force(report, it) -> str:
    as_of = _as_of(report)
    end = _date(_row(it).get("ends_on"))
    if _row(it).get("permanent"):
        return "permanent"
    if not end:
        return "no end filed"
    return f"in force on {as_of.isoformat()}" if end >= as_of else f"ended before {as_of.isoformat()}"


def _person_notice(report, rule, view, noun, never_clear: str | None):
    """A notice on a person's record (a director prohibition, a bankruptcy): red confirmed to the subject; red on an officer's own
    confirmed rows from a company (the officer's); amber near (a namesake's until confirmed); a revoked or annulled one never counted."""
    live = _live(items(report, (view,)))
    own = [it for it in live if it["grade"] == "confirmed" and not it.get("through")]
    officer = [it for it in through_officer(report, (view,))]
    nearby = [it for it in live if it["grade"] == "near" and it not in officer]
    extra = (lambda it: f"; {_in_force(report, it)}") if view == "gazette_prohibitions" else (lambda it: "")
    if own:
        return flag(rule, V, "fired", "red", f"{len(own)} {noun}(s) confirmed to the subject: "
                    + _lines(own, lambda it: f"{_name(it)} ({it['dates']['text']}{extra(it)})"), citations=tuple(it["ref"] for it in own))
    if officer:
        return flag(rule, V, "fired", "red", f"{len(officer)} {noun}(s) on the record of an officer of the company: "
                    + _lines(officer, lambda it: f"{_name(it)} ({it['dates']['text']}{extra(it)})") + "; the officer's, not the company's",
                    citations=tuple(it["ref"] for it in officer), scope="officer-group")
    if nearby:
        return flag(rule, V, "fired", "amber", f"{len(nearby)} {noun}(s) under a name near the subject's; a namesake's until confirmed: "
                    + _lines(nearby, lambda it: f"{_name(it)} ({it['dates']['text']}; near: {it.get('reason')})"),
                    citations=tuple(it["ref"] for it in nearby), scope="near")
    if other_start(report):
        return flag(rule, V, "blocked", "red", other_start(report))
    if stage_one(report):
        return flag(rule, V, "blocked", "red", _near_wait(report, f"a {noun} under the subject's name and not confirmed to them"))
    w = _walk(report)
    if not w.get("links_built"):
        return flag(rule, V, "blocked", "red", f"no links are published, so a {noun} under the subject's name cannot be reached")
    if w.get("links_omitted"):
        return flag(rule, V, "blocked", "red", f"the walk left {w['links_omitted']:,} link(s) unread past its limit; a {noun} could be among them")
    if never_clear:
        return flag(rule, V, "blocked", "red", never_clear)
    return flag(rule, V, "clear", "red", f"no {noun} confirmed or near the subject, and every link from the subject's rows was read",
                sources_held=(REG_HELD[view] + ", joined by name in pub.links",))


def prohibition(report):
    return _person_notice(report, "prohibition", "gazette_prohibitions", "Gazette director prohibition", None)


def bankruptcy(report):
    return _person_notice(report, "bankruptcy", "gazette_bankruptcies", "Gazette bankruptcy notice",
                          "no Gazette bankruptcy notice is confirmed or near the subject; a notice reaches a person by name, and a discharge "
                          "or annulment is not always gazetted, so the blank is not a clear (the Insolvency Register is read by "
                          "insolvency-register)")


def _listed(report, rule, views, severity: dict, what: str, not_held=(), clears=True):
    """A list or register that names the entity or a person the rules confirm is the subject: fired at the view's severity (the
    highest of the rows found); one under a namesake's or an officer's name: amber; none: clear as the lists stand today, or blocked
    where a source the check also needs is not held."""
    rows = _live(items(report, views))
    conf = [it for it in rows if it["grade"] == "confirmed" and not it.get("through")]
    near = [it for it in rows if it not in conf]
    held = tuple(REG_HELD[v] for v in views if v in REG_HELD)
    if conf:
        sev = max((severity.get(it["view"], "amber") for it in conf), key=("info", "amber", "red").index)
        return flag(rule, V, "fired", sev, f"{len(conf)} row(s) of {what} name the subject or a person the rules confirm is the subject: "
                    + _lines(conf, lambda it: f"{it['statement']} ({it['dates']['text']})") + "; a listing states what its publisher published",
                    citations=tuple(it["ref"] for it in conf), sources_held=held, sources_not_held=tuple(not_held))
    if near:
        officer = sum(1 for it in near if it.get("through"))
        return flag(rule, V, "fired", "amber", f"{len(near)} row(s) of {what} name a namesake the rules do not confirm is the subject"
                    + (f" ({officer} through an officer the walk followed, the officer's)" if officer else "") + ": "
                    + _lines(near, lambda it: it["statement"]) + "; nothing in a namesake's row is the subject's",
                    citations=tuple(it["ref"] for it in near), sources_held=held, sources_not_held=tuple(not_held), scope="near")
    top = max(severity.values(), key=("info", "amber", "red").index)
    text = f"no row of {what}, as they stand today, names the subject or a person the rules confirm is the subject"
    if stage_one(report):
        return flag(rule, V, "blocked", top, f"{text}; " + _near_wait(report, "a row under the subject's name and not confirmed to them"),
                    sources_held=held, sources_not_held=tuple(not_held))
    if clears:
        return flag(rule, V, "clear", top, text, sources_held=held, sources_not_held=tuple(not_held))
    return flag(rule, V, "blocked", top, f"{text}; but {'; '.join(not_held)} is not held, so no clear is given", sources_held=held,
                sources_not_held=tuple(not_held))


def insolvency_register(report):
    return _listed(report, "insolvency-register", ("insolvency_people", "insolvency_companies"),
                   {"insolvency_people": "red", "insolvency_companies": "red"}, "the Insolvency Register")


def sanctions(report):
    """New Zealand's sanctions lists: a listing the rules confirm is the subject's, red; one under a name only, amber, a reason to
    check the list's own identifiers."""
    return _listed(report, "sanctions", ("sanctions_listings",), {"sanctions_listings": "red"}, "New Zealand's sanctions lists")


def regulator_listings(report):
    """WorkSafe (red: a safety prosecution), the Commerce Commission, the Financial Markets Authority and the Overseas Investment
    Office (amber); Fire and Emergency's notices and the FSP register are not held, so none is never a clear."""
    return _listed(report, "regulator-listings", ("worksafe_parties", "commerce_commission_parties", "fma_parties", "overseas_investment_parties"),
                   {"worksafe_parties": "red", "commerce_commission_parties": "amber", "fma_parties": "amber", "overseas_investment_parties": "amber"},
                   "WorkSafe, the Commerce Commission, the Financial Markets Authority or the Overseas Investment Office",
                   not_held=("Fire and Emergency New Zealand's notices", "the Financial Service Providers Register"), clears=False)


def professional_discipline(report):
    """The Real Estate Authority's decisions and the Building Practitioners Board's upheld decisions; the licence registers' own
    status and the other professional bodies are not held, so none is never a clear."""
    rows = [it for it in _live(items(report, ("rea_parties", "building_practitioner_decisions")))
            if it["view"] != "building_practitioner_decisions" or _row(it).get("upheld") is True]
    held = (REG_HELD["rea_parties"], REG_HELD["building_practitioner_decisions"])
    nh = ("the professional bodies' own registers and tribunals beyond the courts corpus (lawyers, accountants, the licensed building "
          "practitioners register's classes)",)
    conf = [it for it in rows if it["grade"] == "confirmed" and not it.get("through")]
    near = [it for it in rows if it not in conf]
    if conf:
        return flag("professional-discipline", V, "fired", "amber", f"{len(conf)} decision(s) name the subject or a person the rules confirm "
                    "is the subject: " + _lines(conf, lambda it: f"{it['statement']} ({it['dates']['text']})")
                    + "; a decision states the body's finding", citations=tuple(it["ref"] for it in conf), sources_held=held, sources_not_held=nh)
    if near:
        return flag("professional-discipline", V, "fired", "amber" if any(not it.get("through") for it in near) else "info",
                    f"{len(near)} decision(s) name a person who shares a name with the subject or an officer: "
                    + _lines(near, lambda it: it["statement"]) + "; a namesake's until the licence number is checked (ruling 148)",
                    citations=tuple(it["ref"] for it in near), sources_held=held, sources_not_held=nh, scope="near")
    return flag("professional-discipline", V, "blocked", "amber", "no decision of the Real Estate Authority or upheld decision of the "
                "Building Practitioners Board names the subject" + ("; " + _near_wait(report, "a decision under the subject's name")
                                                                    if stage_one(report) else "")
                + f"; but {nh[0]} are not held, so no clear is given", sources_held=held, sources_not_held=nh)


def _court_parties(report, grades):
    seen, out = set(), []
    for it in items(report, COURT_VIEWS, grades):
        r = _row(it)
        if it.get("suppressed") or r.get("withheld") or r.get("anonymised") or it["ref"] in seen:
            continue
        if it["view"] == "court_people" and r.get("role") not in ("party", "company"):
            continue
        seen.add(it["ref"])
        out.append(it)
    return out


COURT_CODE = re.compile(r"\[\d{4}\]\s*(NZ[A-Za-z]+)")
TRIBUNALS = {"NZERA": "the Employment Relations Authority", "NZEmpC": "the Employment Court", "NZLCDT": "the Lawyers and Conveyancers "
             "Disciplinary Tribunal", "NZLCRO": "the Legal Complaints Review Officer", "NZREADT": "the Real Estate Agents Disciplinary Tribunal"}


def _court_of(it):
    r = _row(it)
    if r.get("court"):
        return r["court"]
    m = COURT_CODE.search(str(r.get("citation") or it.get("statement") or ""))
    return m.group(1) if m else None


def court_judgments(report):
    """A party the rules confirm is the subject, in a judgment the corpus holds: amber (being a party is not a finding against
    anyone), with the tribunals' decisions counted by tribunal; a namesake's or an officer's: info; none: blocked, the corpus holding a
    part of the courts' judgments."""
    conf = [it for it in _court_parties(report, ("confirmed",)) if not it.get("through")]
    near = [it for it in _court_parties(report, ("confirmed", "near")) if it not in conf]
    trib = sorted({TRIBUNALS[c] for c in (_court_of(it) for it in conf) if c in TRIBUNALS})
    if conf:
        return flag("court-judgments", V, "fired", "amber", f"{len(conf)} party row(s) in a judgment the corpus holds name the subject or a person "
                    "the rules confirm is the subject: " + _lines(conf, lambda it: f"{it['statement']} ({it['dates']['text']})")
                    + (f"; among them decisions of {', '.join(trib)}" if trib else "") + "; being a party is not a finding against anyone",
                    citations=tuple(it["ref"] for it in conf), sources_held=COURT_HELD, sources_not_held=COURT_NOT_HELD)
    if near:
        return flag("court-judgments", V, "fired", "info", f"{len(near)} party row(s) in a judgment the corpus holds name an officer on the subject "
                    "or a namesake the rules do not confirm is the subject: " + _lines(near, lambda it: it["statement"])
                    + "; nothing in a namesake's or an officer's case is the subject's", citations=tuple(it["ref"] for it in near),
                    sources_held=COURT_HELD, sources_not_held=COURT_NOT_HELD)
    return flag("court-judgments", V, "blocked", "amber", "no party row in a judgment the corpus holds names the subject or a person the rules "
                "confirm is the subject; the corpus holds a part of the courts' and tribunals' judgments, so no clear is given",
                sources_held=COURT_HELD, sources_not_held=COURT_NOT_HELD)


# ── holders, the chain, the office ──────────────────────────────────────────

HOLDER_HUB_KINDS = ("nominee", "crown", "professional-director")


def _holders(report):
    """The holders of record listed on the entity (from a company) or on the person's companies (from a person), never up the chain."""
    s = _subject(report)
    rows = [it for it in _live(items(report, ("shareholders",))) if not it.get("above") and not it.get("depth")]
    if company_start(report):
        return [it for it in rows if it.get("via") == s["ref"] or company_of(it) == s["ref"]]
    mine = {it["ref"] for it in companies(report)}
    return [it for it in rows if company_of(it) in mine and it["ref"] not in {m["ref"] for m in report.get("members", [])}]


def _chain_holders(report):
    return [it for it in _live(items(report, ("shareholders",))) if it.get("above") or it.get("depth")]


def holders_of_record(report):
    """The holders of record (on the entity, or on the person's companies) that are companies, are named as a nominee, trustee or
    custodian, are a hub, are a limited partnership, or carry an overseas company form: each shown as the register states it; for
    whom a holder holds is in no register held."""
    if other_start(report):
        return flag("holders-of-record", V, "blocked", "amber", other_start(report), sources_not_held=(FOR_WHOM,))
    holders, up = _holders(report), _chain_holders(report)
    every = holders + [it for it in up if it not in holders]
    marks = {
        "a company": [it for it in every if _company_holder(it)],
        "named as a nominee, trustee or custodian": [it for it in every if CUSTODIAL.search(_holder_name(it))
                                                     or any(f.get("kind") == "nominee" for f in it.get("flags", []))],
        "a hub": [it for it in every if any(f.get("kind") in HOLDER_HUB_KINDS for f in it.get("flags", []))],
        "a limited partnership by its name": [it for it in every if PARTNERSHIP.search(_holder_name(it).strip())],
        "named with an overseas company form": [it for it in every if _company_holder(it) and OVERSEAS_FORM.search(_holder_name(it).strip())],
    }
    hit = {k: v for k, v in marks.items() if v}
    scope = "entity" if company_start(report) else "officer-group"
    nh = (FOR_WHOM, LP_LIMITED, "overseas company registers")
    if hit:
        strong = any(k in hit for k in ("named as a nominee, trustee or custodian", "a limited partnership by its name",
                                        "named with an overseas company form"))
        return flag("holders-of-record", V, "fired", "amber" if strong and company_start(report) else "info",
                    f"of {len(every)} holder(s) of record listed ({len(up)} up the holding chain), "
                    + "; ".join(f"{len(v)} {k}: " + _lines(v, _holder_name) for k, v in hit.items())
                    + "; each is a holder of record as the register states it, and for whom it holds is in no register held",
                    citations=_cites([it["ref"] for v in hit.values() for it in v]), sources_held=(COMPANIES_HELD,), sources_not_held=nh,
                    scope=scope)
    if company_start(report) and not holders:
        return flag("holders-of-record", V, "blocked", "amber", "the companies file lists no holder of record on the entity", scope=scope)
    if walk_short(report) or any("shareholders" in (s.get("omitted_views") or ()) for s in report["sections"]):
        return flag("holders-of-record", V, "blocked", "amber", "the walk left holder rows or companies past its limit unread", scope=scope)
    return flag("holders-of-record", V, "clear", "amber", f"none of the {len(every)} holder(s) of record listed is a company, a nominee, "
                "trustee or custodian by its name, a hub, a limited partnership or an overseas company by its form; a holder can hold for "
                "others without saying so in its name", sources_held=(COMPANIES_HELD,), sources_not_held=nh, scope=scope)


def holding_chain(report):
    """The companies above the entity in the holding chain, and where the chain is cut or a holder could not be followed."""
    if not company_start(report):
        return flag("holding-chain", V, "blocked", "info", "the holding chain is read from a company start: start a report from each company "
                    "listed" if person_start(report) else other_start(report), scope="chain")
    w = _walk(report)
    above = [it for it in items(report, ("companies",)) if it.get("rule") == "chain" or (it.get("depth") and it.get("hop_text"))]
    notes, st = w.get("chain_notes") or [], w.get("chain") or {}
    if notes or st.get("cut"):
        return flag("holding-chain", V, "blocked", "amber" if above else "info", f"{len(above)} company(ies) above the entity were reached; "
                    f"{len(notes)} holder(s) could not be followed (a name several companies carry or none: an overseas company, a trust or a "
                    "body of another kind)" + (f"; the chain goes on past {w.get('chain_depth')} up" if st.get("cut") else ""),
                    sources_not_held=("overseas company registers", "trusts: no New Zealand register exists"), scope="chain")
    if above:
        return flag("holding-chain", V, "fired", "info", f"{len(above)} company(ies) hold shares of record above the entity, up to "
                    f"{st.get('depth') or 1} up: " + _lines(above, lambda it: f"{_name(it)} ({it.get('hop_text') or 'a holder of record'})")
                    + "; a holder of record is shown as the register states it, the holder's and not the entity's",
                    citations=tuple(it["ref"] for it in above), scope="chain")
    return flag("holding-chain", V, "clear", "info", "no company holds shares of record in the entity: its holders of record are people",
                sources_held=(COMPANIES_HELD,), scope="chain")


PROFESSIONAL_OFFICE = re.compile(r"\b(chartered accountants?|accountants?|accounting|lawyers?|solicitors?|barristers?|legal|law|"
                                 r"formation|company services|secretarial|registered office services)\b", re.I)


def _office_lines(it) -> str:
    r = _row(it)
    return " ".join(str(r.get(c) or "") for c in ("care_of", "line_1", "line_2", "line_3", "line_4"))


def _office_key(it):
    r = _row(it)
    k = (" ".join(str(r.get("line_1") or "").lower().split()), str(r.get("postcode") or "").strip())
    return k if k[0] else None


def _offices(report) -> dict:
    """{company ref: [(office key, item, started_on)]} from the registered-office rows the walk listed; the key is compared, never shown."""
    out = {}
    for it in items(report, ("company_addresses",)):
        k = _office_key(it)
        if k:
            out.setdefault(company_of(it), []).append((k, it, _date(_row(it).get("started_on"))))
    return out


def _office_hub(report, it) -> bool:
    return bool(_row(it).get("care_of")) or bool(PROFESSIONAL_OFFICE.search(_office_lines(it))) \
        or any(f.get("kind") in OFFICE_HUBS for f in it.get("flags", []))


def shared_office(report):
    """From a company: whether its registered office is a hub (a professional firm's, or fifty or more companies'), and if not, the
    companies at it that failed. From a person: a failed company's office from before its failure that a going company of the person's
    has now, not a hub. An office is not a person, and the lines are compared, never quoted."""
    if other_start(report):
        return flag("shared-office", V, "blocked", "amber", other_start(report), scope="office")
    offices = _offices(report)
    if company_start(report):
        s = _subject(report)
        w = _walk(report)
        mine = [it for _, it, _ in offices.get(s["ref"], []) if _row(it).get("in_latest", True)]
        if not mine:
            return flag("shared-office", V, "blocked", "amber", "the companies file lists no registered office on the entity in the latest "
                        "file", scope="office")
        busy = (w.get("office_companies") or 0) >= ((w.get("settings") or {}).get("busy_address") or 50)
        hub = [it for it in mine if _office_hub(report, it)]
        if hub or busy:
            return flag("shared-office", V, "fired", "info", "the entity's registered office is a hub: "
                        + ("it is kept in the care of another or names a professional firm" if hub else "")
                        + (" and " if hub and busy else "") + (f"{w.get('office_companies')} companies share it" if busy else "")
                        + "; a company met there shares an office and nothing more, and none is compared",
                        citations=tuple(it["ref"] for it in (hub or mine)), scope="office")
        at = [it for it in items(report, ("companies",), ("confirmed", "near")) if it.get("rule") == "shared-office"]
        if not at and stage_one(report):
            return flag("shared-office", V, "blocked", "amber", "the companies at the entity's registered office are reached by the office's "
                        "lines, not by a confirmed link; the first stage does not follow them (the second stage does, on request)", scope="office")
        bad = sorted([it for it in at if ending(it) != "going"], key=lambda it: (ending(it) != "insolvent", it["ref"]))
        if bad:
            return flag("shared-office", V, "fired", "amber", f"{len(bad)} of the {len(at)} other companies listed at the entity's registered "
                        "office have failed or ended: " + _lines(bad, lambda it: f"{_name(it)} ({_status(it) or 'no status'})")
                        + f"; the entity was registered {_iso(_date(_row(s).get('registered_on')))}; a shared office is no connection on its own",
                        citations=_cites([it["ref"] for it in bad] + [m["ref"] for m in mine]), sources_not_held=(CHANGE_HISTORY,), scope="office")
        if (w.get("office_companies") or 0) - 1 > (w.get("office_listed") or 0):
            return flag("shared-office", V, "blocked", "amber", f"{(w.get('office_companies') or 0) - 1} other companies share the entity's "
                        f"registered office and {w.get('office_listed') or 0} were listed, none failed; the rest were not read", scope="office")
        return flag("shared-office", V, "clear", "amber", f"the entity's registered office is not a hub, and none of the {len(at)} other "
                    "companies at it has failed in the latest file", sources_held=(OFFICES_HELD, COMPANIES_HELD), scope="office")
    cos = companies(report)
    failed = failures(report, cos)
    going = [c for c in cos if ending(c) == "going" and c["ref"] not in failed]
    hits = []
    for f in failed.values():
        if f["date"] is None:
            continue
        before = {k: it for k, it, st in offices.get(f["company"]["ref"], []) if st and st < f["date"] and not _office_hub(report, it)}
        for g in going:
            now = [(k, it) for k, it, _ in offices.get(g["ref"], []) if _row(it).get("in_latest", True) and not _office_hub(report, it)]
            hit = next(((before[k], it) for k, it in now if k in before), None)
            if hit:
                hits.append((f, g, hit))
    if hits:
        return flag("shared-office", V, "fired", "amber", f"{len(hits)} pair(s) of the person's companies: a failed company's registered office "
                    "from before its failure is a going company's office now, not a hub: "
                    + _lines(hits, lambda h: f"{_name(h[0]['company'])} ({h[0]['kind']}, {_iso(h[0]['date'])}) | {_name(h[1])}")
                    + "; a shared office is no connection on its own",
                    citations=_cites([r for f, g, (a, b) in hits for r in (f["company"]["ref"], g["ref"], a["ref"], b["ref"])]),
                    sources_not_held=(CHANGE_HISTORY,), scope="office")
    return flag("shared-office", V, "blocked", "amber", f"of the person's {len(cos)} companies, {len(failed)} failed and none had, before its "
                "failure, an office a going one has now; a failed company's earlier office is seen only where the file still holds it, so no "
                "clear is given", sources_not_held=(CHANGE_HISTORY,), scope="office")


# ── boards, roles, the web ──────────────────────────────────────────────────

CARE = re.compile(r"\b(care|rest ?home|retirement|lifecare|aged|hospital|hospice|health|healthcare|village|nursing|dementia)\b", re.I)


def _fold(name: str) -> str:
    return " ".join(re.sub(r"[^a-z ]", " ", (name or "").lower()).split())


def _person_key(it):
    """One person across rows: the confirmed group the first stage names (`person`), else the folded name, which is near only."""
    if it.get("person"):
        return ("group", it["person"]), True
    return ("name", _fold(it.get("title"))), False


def shared_boards(report):
    """A person on two or more of the companies here. From a person: the people beside the person on the person's companies (the first
    stage's confirmed groups, or by name, near). From a company: the officers' other companies two or more of them share."""
    if other_start(report):
        return flag("shared-boards", V, "blocked", "info", other_start(report), scope="officer-group")
    if company_start(report):
        cos = {}
        for it in through_officer(report, ("companies",)):
            if it["ref"] != _subject(report)["ref"]:
                cos.setdefault(it["ref"], {"company": it, "officers": set()})["officers"].add(it.get("through"))
        shared = sorted([c for c in cos.values() if len(c["officers"]) >= 2], key=lambda c: -len(c["officers"]))
        if shared:
            return flag("shared-boards", V, "fired", "info", f"{len(shared)} other company(ies) carry two or more of the officers the walk "
                        "followed: " + _lines(shared, lambda c: f"{_name(c['company'])} ({len(c['officers'])} officers)")
                        + "; two officers on one board are two dated rows, and nothing more is said of them",
                        citations=tuple(c["company"]["ref"] for c in shared), scope="officer-group")
        if _walk(report).get("officers_omitted"):
            return flag("shared-boards", V, "blocked", "info", "officers past the walk's limit were not followed", scope="officer-group")
        return flag("shared-boards", V, "clear", "info", f"no other company carries two of the officers the walk followed ({len(cos)} read)",
                    sources_held=(COMPANIES_HELD,), scope="officer-group")
    mine = {it["ref"] for it in companies(report)}
    own = {_subject(report)["ref"]} | {m["ref"] for m in report.get("members", [])}
    by, confirmed = {}, {}
    for it in _live(items(report, ("directors", "shareholders"), ("confirmed", "near"))):
        c = company_of(it)
        if c not in mine or it["ref"] in own:
            continue
        k, conf = _person_key(it)
        if not k[1]:
            continue
        by.setdefault(k, {})[c] = it
        confirmed[k] = conf
    shared = sorted(((k, v) for k, v in by.items() if len(v) >= 2), key=lambda kv: -len(kv[1]))
    if shared:
        conf = [k for k, _ in shared if confirmed[k]]
        return flag("shared-boards", V, "fired", "info", f"of {len(by)} person(s) beside the subject, {len(shared)} sit on two or more of the "
                    f"person's companies ({len(conf)} by a confirmed group, {len(shared) - len(conf)} by name only, near): "
                    + _lines(shared, lambda kv: f"{next(iter(kv[1].values()))['title']} on {len(kv[1])}")
                    + "; shared seats are dated rows, and nothing more is said of them",
                    citations=_cites([it["ref"] for _, v in shared for it in v.values()]), scope="officer-group" if conf else "near")
    if walk_short(report):
        return flag("shared-boards", V, "blocked", "info", "the walk stopped before reading the officers of every company the person has a "
                    "row on", scope="officer-group")
    return flag("shared-boards", V, "clear", "info", f"of {len(by)} person(s) beside the subject, none sits on more than one of the person's "
                "companies", sources_held=(COMPANIES_HELD, "pub.groups"), scope="officer-group")


def officer_other_roles(report):
    """The officers' other current roles, dated: from an organisation, each officer followed with the companies and societies the officer
    also sits on, those whose registered name reads as care or retirement living counted apart (a sign, not a finding); from a person,
    the person's own current roles across organisations. A hub's roles are shown and never amber."""
    if other_start(report):
        return flag("officer-other-roles", V, "blocked", "amber", other_start(report), scope="officer-group")
    hubs = {h["ref"]: h for h in report.get("hubs", [])}
    if organisation_start(report):
        roles = {}
        for it in through_officer(report, ROLE_VIEWS):
            if company_of(it) != _subject(report)["ref"] and _current(it):
                roles.setdefault(it.get("through"), []).append(it)
        if not roles:
            w = _walk(report)
            if w.get("officers_omitted") or w.get("officers_suppressed"):
                return flag("officer-other-roles", V, "blocked", "amber", "officers past the walk's limit or suppressed were not followed",
                            scope="officer-group")
            return flag("officer-other-roles", V, "clear", "info", f"none of the {w.get('officers_followed', 0)} officer(s) followed holds "
                        "another current role in the registers read", sources_held=(COMPANIES_HELD, SOCIETIES_HELD, "pub.groups"),
                        scope="officer-group")
        care = [o for o, rs in roles.items() if o not in hubs and any(CARE.search(r.get("entity_title") or "") for r in rs)]
        return flag("officer-other-roles", V, "fired", "amber" if care and CARE.search(_name(_subject(report))) else "info",
                    f"{len(roles)} officer(s) hold {sum(len(v) for v in roles.values())} other current role(s); {len(care)} officer(s), not hubs, "
                    "sit on an organisation whose registered name reads as care or retirement living (the registers carry no industry: a sign, "
                    "not a finding): " + _lines(sorted(roles.items(), key=lambda kv: -len(kv[1])),
                                                lambda kv: f"{len(kv[1])} role(s), among them {kv[1][0]['statement']}")
                    + "; two roles held at once are two dated facts, and nothing more is said of them",
                    citations=_cites([r["ref"] for v in roles.values() for r in v]), scope="officer-group")
    orgs = {}
    for it in _live(items(report, ROLE_VIEWS)):
        if it["grade"] == "confirmed" and not it.get("through") and not it.get("depth") and _current(it):
            orgs.setdefault(company_of(it) or it["ref"], it)
    if len(orgs) >= 2:
        care = [r for r in orgs.values() if CARE.search(r.get("entity_title") or "")]
        hub = [h for h in report.get("hubs", []) if h["ref"] == _subject(report)["ref"]]
        return flag("officer-other-roles", V, "fired", "amber" if len(care) >= 2 and not hub else "info",
                    f"the person holds current confirmed roles on {len(orgs)} organisation(s), {len(care)} whose registered name reads as care "
                    "or retirement living (a sign, not a finding)" + (f"; the person is a hub ({hub[0]['kind']})" if hub else "") + ": "
                    + _lines(list(orgs.values()), lambda r: r["statement"]), citations=tuple(r["ref"] for r in orgs.values()),
                    scope="officer-group")
    if walk_short(report) or _walk(report).get("links_omitted"):
        return flag("officer-other-roles", V, "blocked", "amber", "the walk stopped before reading every row of the person's", scope="officer-group")
    return flag("officer-other-roles", V, "clear", "info", f"the person holds current confirmed roles on {len(orgs)} organisation(s): no overlap",
                sources_held=(COMPANIES_HELD, SOCIETIES_HELD, "pub.groups"), scope="officer-group")


def stage_web(report):
    """The first stage's web: the organisations and people the confirmed links reach, hop by hop, with the failed organisations among
    those past the subject's own, each the holder's or the officer's and never the subject's."""
    st = _walk(report).get("stage1")
    if not st:
        return flag("stage-web", V, "blocked", "info", "the report did not walk the first stage's confirmed web", scope="officer-group")
    own = {_subject(report)["ref"]} | {it["ref"] for it in companies(report)}
    ents = [it for it in all_items(report).values() if it["view"] in ("companies", "societies", "charities", "limited_partnerships")
            and it["ref"] not in own and not it.get("above") and not it.get("missing")]
    failed = [it for it in ents if ending(it) == "insolvent"]
    hops = st.get("levels") or []
    shape = "; ".join(f"hop {l['hop']}: {l['entities']} organisation(s), {l['people']} person(s)" for l in hops) or "no hop"
    if failed:
        return flag("stage-web", V, "fired", "info", f"the confirmed web to {st.get('depth')} hop(s) ({shape}) reaches {len(failed)} "
                    "organisation(s) with an insolvency status past the subject's own: " + _lines(failed, lambda it: f"{_name(it)} (hop "
                                                                                               f"{it.get('stage_hop')}, {_status(it)})")
                    + "; each sits on the web through the people and holders listed, never the subject's own",
                    citations=tuple(it["ref"] for it in failed), scope="officer-group")
    return flag("stage-web", V, "clear", "info", f"the confirmed web to {st.get('depth')} hop(s) ({shape}) reaches no organisation with an "
                "insolvency status past the subject's own", sources_held=(COMPANIES_HELD, "pub.links (confirmed)", "pub.groups"),
                scope="officer-group")


# ── charities and societies ─────────────────────────────────────────────────

CHARITY_HELD = "Charities Register (pub.charities, pub.charity_officers, pub.charity_returns)"


def _charities(report):
    s = _subject(report)
    out = [s] if s["view"] == "charities" else []
    return out + [it for it in items(report, ("charities",)) if it["ref"] != s["ref"] and not it.get("through")]


def _returns_of(report, c):
    k = _key(c["ref"])
    rs = [it for it in items(report, ("charity_returns",)) if _row(it).get("charity_key") == k or it.get("via") == c["ref"]]
    return sorted(rs, key=lambda it: str(_row(it).get("period_end") or ""), reverse=True)


def _charity_ending(c) -> str:
    st = _status(c).lower()
    return "going" if st in ("registered", "") and not _date(_row(c).get("deregistered_on")) else "ended"


def _last_period_end(c, as_of):
    """The last balance date whose return is due by `as_of` (due within FILE_WITHIN_DAYS of it), or None without a balance date."""
    r = _row(c)
    try:
        m, d = int(r.get("year_end_month")), int(r.get("year_end_day") or 0)
    except (TypeError, ValueError):
        return None
    for year in (as_of.year, as_of.year - 1, as_of.year - 2):
        try:
            end = dt.date(year, m, d or 28)
        except ValueError:
            end = dt.date(year, m, 28)
        if (as_of - end).days > FILE_WITHIN_DAYS:
            return end
    return None


def _charity_unread(report) -> str | None:
    if other_start(report) and _subject(report)["view"] not in ("charities", "charity_officers", "societies", "society_officers"):
        return other_start(report)
    if not _reads(report, "charity_officers"):
        return "the template does not read the Charities Register's officers"
    return None


def charity_and_society_roles(report):
    """The incorporated societies and charities the subject is an officer of (confirmed, never the officers of a society the report
    starts from), the charities a company is by its business number, and the charity officer rows under the person's name (near)."""
    s = _subject(report)
    if company_start(report):
        rows = [it for it in through_officer(report, ("society_officers", "charity_officers")) if not it.get("suppressed")]
        own = [c for c in _charities(report) if c["grade"] == "confirmed"]
        if rows or own:
            return flag("charity-and-society-roles", V, "fired", "info", (f"the entity's charity by its business number: "
                        + _lines(own, lambda c: f"{_name(c)} ({_status(c) or 'status not filed'})") + "; " if own else "")
                        + (f"{len(rows)} society or charity officer role(s) on the record of an officer the walk followed, the officer's: "
                           + _lines(rows, lambda it: it["statement"]) if rows else ""),
                        citations=_cites([c["ref"] for c in own] + [it["ref"] for it in rows]), scope="officer-group")
        return flag("charity-and-society-roles", V, "clear", "info", "no charity is the entity's by its business number, and no officer the walk "
                    "followed holds a society or charity officer role", sources_held=(SOCIETIES_HELD, CHARITY_HELD), scope="officer-group")
    conf = [it for it in _live(items(report, ("society_officers", "charity_officers"), ("confirmed",)))
            if it.get("via") != s["ref"] and company_of(it) != s["ref"] and not it.get("through") and not it.get("depth")]
    named = [it for it in _live(items(report, ("charity_officers", "society_officers"), ("near",))) if not it.get("through")]
    if conf or named:
        return flag("charity-and-society-roles", V, "fired", "info", " | ".join(
            ([f"officer of {len({company_of(it) for it in conf})} society(ies) or charity(ies), confirmed: " + _lines(conf, lambda it: it["statement"])]
             if conf else []) + ([f"{len(named)} officer row(s) carry the person's name, near, a namesake's until a rule confirms it: "
                                 + _lines(named, lambda it: it["statement"])] if named else [])),
            citations=_cites([it["ref"] for it in conf + named]), scope="subject" if conf else "near")
    why = _charity_unread(report)
    if why:
        return flag("charity-and-society-roles", V, "blocked", "info", why)
    if stage_one(report):
        return flag("charity-and-society-roles", V, "blocked", "info", "no society or charity officer role is confirmed to the subject; "
                    + _near_wait(report, "a charity officer row under the person's name (the Charities Register's officers are joined by name)"))
    return flag("charity-and-society-roles", V, "clear", "info", "no society or charity officer role confirmed to the subject, and no charity "
                "officer row carries the subject's name", sources_held=(SOCIETIES_HELD, CHARITY_HELD))


def charity_integrity_marks(report):
    """The Charities Register's own mark on an officer row (`disqualified`): red on a row confirmed to the subject or on a charity
    confirmed to it; amber on a row only under the name, or on an officer's record (the officer's)."""
    marked = [it for it in _live(items(report, ("charity_officers",))) if _row(it).get("disqualified")]
    if marked:
        conf = [it for it in marked if it["grade"] == "confirmed" and not it.get("through")]
        return flag("charity-integrity-marks", V, "fired", "red" if conf else "amber", f"{len(marked)} charity officer row(s) carry the "
                    f"register's disqualified mark, {len(conf)} confirmed to the subject or its charity: "
                    + _lines(marked, lambda it: f"{it['statement']} ({it['dates']['text']}" + (f"; near: {it.get('reason')})"
                                                                                                if it["grade"] == "near" else ")")),
                    citations=tuple(it["ref"] for it in marked), scope="entity" if conf else "near")
    why = _charity_unread(report)
    if why:
        return flag("charity-integrity-marks", V, "blocked", "red", why)
    if stage_one(report) and not _charities(report):
        return flag("charity-integrity-marks", V, "blocked", "red", _near_wait(report, "a charity officer row under the subject's name"))
    return flag("charity-integrity-marks", V, "clear", "red", f"no charity officer row read ({len(list(items(report, ('charity_officers',))))}) carries "
                "the register's disqualified mark", sources_held=(CHARITY_HELD,))


def charity_returns(report):
    """The newest return of each charity reached, as filed: its period, tier, income, expenditure and assets, and its audit."""
    chars = _charities(report)
    if not chars:
        return flag("charity-returns", V, "blocked", "info", "no charity is reached from the subject, so no return is read")
    lines, cites = [], []
    for c in chars:
        rs = _returns_of(report, c)
        if rs:
            r = _row(rs[0])
            cites.append(rs[0]["ref"])
            lines.append(f"{_name(c)}: period to {_iso(_date(r.get('period_end')))}, {r.get('tier') or 'tier not filed'}; income "
                         f"{r.get('total_gross_income')}, expenditure {r.get('total_expenditure')}, assets {r.get('total_assets')}; "
                         + ("audited" if r.get("audited") else "not audited" if r.get("audited") is False else "audit not stated"))
    if not lines:
        return flag("charity-returns", V, "blocked", "info", f"{len(chars)} charity(ies) reached and no return of theirs is listed")
    return flag("charity-returns", V, "fired", "info", f"the newest return of {len(lines)} charity(ies), as filed: " + " || ".join(lines[:EXAMPLES]),
                citations=tuple(cites))


def charity_audit_opinion(report):
    """A modified audit opinion on a charity's return: red on the newest return of a confirmed charity, amber otherwise."""
    rets = list(items(report, ("charity_returns",)))
    if not rets:
        return flag("charity-audit-opinion", V, "blocked", "red", "no charity return is reached, so no audit opinion can be read")
    newest = {rs[0]["ref"] for c in _charities(report) for rs in [_returns_of(report, c)] if rs}
    modified = [it for it in rets if _row(it).get("modified_opinion")]
    if modified:
        red = [it for it in modified if it["ref"] in newest and it["grade"] == "confirmed"]
        return flag("charity-audit-opinion", V, "fired", "red" if red else "amber", f"{len(modified)} charity return(s) carry a modified "
                    f"audit opinion, {len(red)} the newest return of a confirmed charity: "
                    + _lines(modified, lambda it: f"period to {_iso(_date(_row(it).get('period_end')))}, opinion {_row(it).get('opinion') or 'not stated'}"),
                    citations=tuple(it["ref"] for it in modified))
    return flag("charity-audit-opinion", V, "clear", "red", f"no modified audit opinion on the {len(rets)} return(s) read",
                sources_held=("Charities Register annual returns (pub.charity_returns)",))


def charity_return_filed(report):
    """No return held for a registered charity's last period whose return is due: red on a confirmed charity, amber on a near one."""
    chars = [c for c in _charities(report) if _charity_ending(c) == "going"]
    if not chars:
        return flag("charity-return-filed", V, "blocked", "amber", "no registered charity is reached, so no filing can be checked")
    as_of, late, unknown = _as_of(report), [], []
    for c in chars:
        due = _last_period_end(c, as_of)
        if due is None:
            unknown.append(c)
            continue
        rs = _returns_of(report, c)
        newest = _date(_row(rs[0]).get("period_end")) if rs else None
        if newest is None or (due - newest).days > PERIOD_SLACK_DAYS:
            late.append((c, due, rs[0] if rs else None))
    if late:
        return flag("charity-return-filed", V, "fired", "amber" if all(c["grade"] == "near" for c, _, _ in late) else "red",
                    f"{len(late)} charity(ies) have no return held for the period to their last balance date: "
                    + _lines(late, lambda x: f"{_name(x[0])}: period to {x[1].isoformat()} | newest held: "
                             + (f"period to {_iso(_date(_row(x[2]).get('period_end')))}" if x[2] else "none")),
                    citations=_cites([c["ref"] for c, _, _ in late] + [r["ref"] for _, _, r in late if r]))
    if unknown:
        return flag("charity-return-filed", V, "blocked", "amber", f"{len(unknown)} charity(ies) carry no balance date on the register, so the "
                    "period due cannot be set", citations=tuple(c["ref"] for c in unknown))
    return flag("charity-return-filed", V, "clear", "amber", f"each of the {len(chars)} registered charity(ies) reached has a return held for "
                "the period to its last balance date", sources_held=("Charities Register (pub.charities, pub.charity_returns)",))


# ── public life and the rest ────────────────────────────────────────────────

PUBLIC_HELD = ("Candidates and the House (pub.members, pub.candidates)", "MPs' declared interests (pub.mp_interest_returns, pub.mp_interests)")


def public_office(report):
    """A seat or candidacy confirmed to the person (amber, a domestic public office); one on an officer's record (the officer's); under a
    name the subject only shares (info, near)."""
    office = [it for it in _live(items(report, OFFICE_VIEWS, ("confirmed",))) if not it.get("through")]
    officer = [it for it in through_officer(report, OFFICE_VIEWS) if not it.get("suppressed")]
    near = [it for it in _live(items(report, OFFICE_VIEWS, ("near",))) if it not in officer]
    if office:
        return flag("public-office", V, "fired", "amber", f"{len(office)} row(s) of public office confirmed to the subject: "
                    + _lines(office, lambda it: f"{_name(it)} ({it['dates']['text']})"), citations=tuple(it["ref"] for it in office),
                    sources_held=PUBLIC_HELD)
    if officer:
        return flag("public-office", V, "fired", "amber", f"{len(officer)} row(s) of public office on the record of an officer of the company: "
                    + _lines(officer, lambda it: f"{_name(it)} ({it['dates']['text']})") + "; the officer's, not the company's",
                    citations=tuple(it["ref"] for it in officer), sources_held=PUBLIC_HELD, scope="officer-group")
    if near:
        return flag("public-office", V, "fired", "info", f"{len(near)} row(s) of public office under a name the subject only shares: a "
                    "namesake's until confirmed", citations=tuple(it["ref"] for it in near), sources_held=PUBLIC_HELD, scope="near")
    if other_start(report):
        return flag("public-office", V, "blocked", "amber", other_start(report))
    nh = ("local-government office, Crown entity boards and the public service: no register joined to a person",)
    if stage_one(report):
        return flag("public-office", V, "blocked", "amber", "no seat or candidacy confirmed to the subject; " + _near_wait(report, "a seat or "
                    "candidacy under the subject's name"), sources_held=PUBLIC_HELD, sources_not_held=nh)
    w = _walk(report)
    if not w.get("links_built") or w.get("links_omitted"):
        return flag("public-office", V, "blocked", "amber", "the links were not all read; a seat or candidacy under the subject's name could be "
                    "among those not read", sources_not_held=nh)
    return flag("public-office", V, "clear", "amber", "no seat in the House, candidacy or declared interest confirmed to the subject, and no near "
                "one", sources_held=PUBLIC_HELD, sources_not_held=nh)


def political_money(report):
    """Donations, loans and disclosures filed under the subject's name: confirmed, or near (the Electoral Commission files a donor's
    name, never a number), each the filed donor's (ruling 253)."""
    money = [it for it in _live(items(report, MONEY_VIEWS, ("confirmed",))) if not it.get("through")]
    near = [it for it in _live(items(report, MONEY_VIEWS, ("near",))) if not it.get("through")]
    held = ("Electoral Commission returns and disclosures",)
    if money:
        return flag("political-money", V, "fired", "info", f"{len(money)} row(s) of political money filed under the subject's name, each "
                    "listed with its date and the party or candidate filed: " + _lines(money, lambda it: f"{_name(it)} ({it['dates']['text']})"),
                    citations=tuple(it["ref"] for it in money), sources_held=held)
    if near:
        return flag("political-money", V, "fired", "info", f"{len(near)} row(s) of political money under the subject's name or one near it, "
                    "joined near: the filed donor's until a rule confirms it: " + _lines(near, lambda it: f"{_name(it)} ({it['dates']['text']})"),
                    citations=tuple(it["ref"] for it in near), sources_held=held, scope="near")
    if other_start(report):
        return flag("political-money", V, "blocked", "info", other_start(report))
    if stage_one(report):
        return flag("political-money", V, "blocked", "info", "no political money is confirmed to the subject; "
                    + _near_wait(report, "a donation filed under the subject's name (the Commission files a name, never a number)"))
    if _walk(report).get("links_omitted"):
        return flag("political-money", V, "blocked", "info", "the walk left links unread past its limit; a donation filed under the subject's "
                    "name could be among them")
    return flag("political-money", V, "clear", "info", "no donation, loan or disclosure filed under the subject's name, confirmed or near",
                sources_held=held, sources_not_held=("a candidate's own return, not yet joined to a person",))


CONTRACTS_NOT_HELD = ("contracts awarded without a GETS notice",)


def public_contracts(report):
    """Government contract award notices naming the subject as a supplier: a track record, never a finding."""
    conf = sorted([it for it in _live(items(report, ("award_suppliers",), ("confirmed",))) if not it.get("through")],
                  key=lambda it: str(_row(it).get("awarded_on") or ""), reverse=True)
    near = [it for it in _live(items(report, ("award_suppliers",), ("near",)))]
    held = (REG_HELD["award_suppliers"],)
    if conf:
        agencies = sorted({_row(it).get("posting_agency") for it in conf} - {None, ""})
        return flag("public-contracts", V, "fired", "info", f"{len(conf)} government contract award notice(s) name the subject as a supplier, "
                    f"from {len(agencies)} agency(ies); newest: " + _lines(conf, lambda it: f"{it['statement']} ({it['dates']['text']})")
                    + "; a notice's value is the whole award's", citations=tuple(it["ref"] for it in conf), sources_held=held,
                    sources_not_held=CONTRACTS_NOT_HELD)
    if near:
        return flag("public-contracts", V, "fired", "info", f"{len(near)} award notice(s) name a supplier the rules do not confirm is the subject: "
                    + _lines(near, lambda it: it["statement"]), citations=tuple(it["ref"] for it in near), sources_held=held,
                    sources_not_held=CONTRACTS_NOT_HELD, scope="near")
    return flag("public-contracts", V, "clear", "info", "no government contract award notice, as GETS publishes them, names the subject as a "
                "supplier", sources_held=held, sources_not_held=CONTRACTS_NOT_HELD)


def retirement_villages(report):
    """The villages the retirement villages file names the company the operator of, and their statutory supervisors."""
    own = [it for it in items(report, ("retirement_villages",), ("confirmed",)) if not it.get("through")]
    held, nh = (REG_HELD["retirement_villages"],), ("when a village's supervisor changed: the file names the one in office",)
    if own:
        return flag("retirement-villages", V, "fired", "info", f"the retirement villages file names {len(own)} village(s) with the "
                    "subject as operator: " + _lines(own, lambda it: f"{_name(it)} (supervisor {_row(it).get('supervisor_name') or 'not stated'})"),
                    citations=tuple(it["ref"] for it in own), sources_held=held, sources_not_held=nh)
    if company_start(report):
        return flag("retirement-villages", V, "clear", "info", "no village in the retirement villages file names the company its operator",
                    sources_held=held, sources_not_held=nh)
    return flag("retirement-villages", V, "blocked", "info", "a village's operator is a company: started from a person or another row, the "
                "villages file is read from each company's report", sources_not_held=nh)


def land_titles(report):
    """The titles of the land register on which the entity is a registered proprietor, counted by status; a person's titles are never
    listed (ruling 102 binds the products; a title can locate a home)."""
    rows = [it for it in items(report, ("linz_title_owners",), ("confirmed",)) if not it.get("through")]
    held = ("the land register's title proprietors (pub.linz_title_owners)",)
    if company_start(report):
        mine = [it for it in rows if (_row(it).get("owner_type") or "").lower() != "person"]
        if mine:
            by = {}
            for it in mine:
                by[_status(it) or "status not filed"] = by.get(_status(it) or "status not filed", 0) + 1
            return flag("land-titles", V, "fired", "info", f"the land register names the entity a registered proprietor on {len(mine)} title(s) ("
                        + ", ".join(f"{n} {k}" for k, n in sorted(by.items())) + "); the land itself is not shown",
                        citations=tuple(it["ref"] for it in mine), sources_held=held)
        if stage_one(report):
            return flag("land-titles", V, "blocked", "amber", "no title is joined to the entity by a confirmed link; "
                        + _near_wait(report, "a title under the entity's name (the land register files a name, never a number)"), sources_held=held)
        return flag("land-titles", V, "blocked", "amber", "no title is joined to the entity; the land register files a proprietor's name, never "
                    "a number, so a title not joined is not ruled out", sources_held=held)
    return flag("land-titles", V, "blocked", "amber", "a person's land titles are not listed by this report", sources_held=held)


# ── the set ─────────────────────────────────────────────────────────────────

CHECKS = (subject_hub, namesake_exposure, walk_coverage, stage_web, past_roles, registers_not_held,
          entity_status, young_entity, officers_of_record, officer_churn, monthly_changes, recent_adverse_change,
          insolvency_notices, companies_standing, repeat_failure, phoenix_signature, left_before_notice, register_events, same_name_failed,
          practitioner_roles, mortgagee_possession, prohibition, bankruptcy, insolvency_register,
          holders_of_record, holding_chain, shared_office, shared_boards, officer_other_roles,
          charity_and_society_roles, charity_integrity_marks, charity_returns, charity_audit_opinion, charity_return_filed,
          court_judgments, sanctions, regulator_listings, professional_discipline,
          public_office, political_money, public_contracts, retirement_villages, land_titles)

#: the contract's common rules (contract.COMMON_RULES) already carry these three on every report; they are not checked twice here
COMMON = {"group-standing": ("identity",), "hubs-met": ("hubs_met",), "replaced-return": ("replaced_rows",)}

#: each combined check, and the retired templates' functions it carries (ruling 157: every retired check once)
MERGED = {
    "subject-hub": ("subject_hub",),
    "namesake-exposure": ("namesake_exposure",),
    "walk-coverage": ("walk_coverage", "history_reach"),
    "stage-web": ("conflict_web",),
    "past-roles": ("past_roles",),
    "registers-not-held": ("securities_register", "change_history", "credit_bureau", "interface_freshness", "ultimate_holders",
                           "mpi_coverage", "hdc_decisions", "certification_audits", "provider_registers", "aged_care_commissioner",
                           "building_consents", "client_overlap"),
    "entity-status": ("entity_status", "company_status", "company_endings", "register_status", "status_history", "status_name_changes"),
    "young-entity": ("young_entity",),
    "officers-of-record": ("officers_of_record", "sole_vehicle"),
    "officer-churn": ("officer_churn",),
    "monthly-changes": ("monthly_changes", "since_date"),
    "recent-adverse-change": ("recent_adverse_change",),
    "insolvency-notices": ("insolvency_notices", "insolvency_notice", "insolvency_event", "entity_insolvency", "liquidation_history"),
    "companies-standing": ("other_companies", "other_current_companies", "people_failed_companies", "sister_company_failure",
                           "officer_group_insolvency", "officer_company_notices"),
    "repeat-failure": ("repeat_failure", "repeat_insolvency", "serial_pattern"),
    "phoenix-signature": ("phoenix_signature", "earlier_failure"),
    "left-before-notice": ("left_before_notice",),
    "register-events": ("register_events", "register_removals", "amalgamation"),
    "same-name-failed": ("same_name_failed",),
    "practitioner-roles": ("practitioner_roles", "practitioner_repeat"),
    "mortgagee-possession": ("mortgagee_possession", "possession"),
    "prohibition": ("prohibition", "disqualified_officer"),
    "bankruptcy": ("bankruptcy", "officer_bankruptcy"),
    "insolvency-register": ("insolvency_register",),
    "holders-of-record": ("holders_of_record", "company_holders", "custodial_holders", "holder_hubs", "partnership_holders",
                          "overseas_holders"),
    "holding-chain": ("holding_chain",),
    "shared-office": ("shared_office", "professional_office"),
    "shared-boards": ("shared_boards",),
    "officer-other-roles": ("officer_overlap",),
    "charity-and-society-roles": ("charity_officer_roles", "society_roles", "charity_arm"),
    "charity-integrity-marks": ("charity_integrity_marks",),
    "charity-returns": ("charity_returns_summary",),
    "charity-audit-opinion": ("charity_audit_opinion",),
    "charity-return-filed": ("charity_return_filed",),
    "court-judgments": ("court_judgments", "disciplinary_findings", "tribunals", "employment_determinations"),
    "sanctions": ("sanctions", "sanctions_lists"),
    "regulator-listings": ("comcom_coverage", "regulator_actions", "safety_record", "other_regulators", "overseas_investment"),
    "professional-discipline": ("professional_discipline", "building_practitioners", "real_estate_authority"),
    "public-office": ("public_office", "public_life"),
    "political-money": ("political_money",),
    "public-contracts": ("public_contracts",),
    "retirement-villages": ("retirement_villages",),
    "land-titles": ("land_titles",),
}

#: the retired templates' RULES, by template, as frozen on 9 November 2026 (step 9 tranche 1; ruling 150)
RETIRED = {
    "02-legal": ("client_overlap", "conflict_web", "shared_boards", "officers_of_record", "holders_of_record", "shared_office", "company_status",
                 "insolvency_notices", "repeat_insolvency", "amalgamation", "register_events", "mortgagee_possession", "prohibition", "bankruptcy",
                 "practitioner_roles", "young_entity", "namesake_exposure", "walk_coverage", "subject_hub", "past_roles", "charity_officer_roles",
                 "charity_integrity_marks", "political_money", "court_judgments", "disciplinary_findings", "comcom_coverage",
                 "securities_register", "insolvency_register", "professional_discipline", "sanctions", "other_regulators"),
    "03-banking": ("past_roles", "company_endings", "insolvency_notices", "repeat_insolvency", "left_before_notice", "register_removals",
                   "prohibition", "bankruptcy", "young_entity", "namesake_exposure", "shared_boards", "walk_coverage", "subject_hub",
                   "officers_of_record", "company_holders", "charity_officer_roles", "charity_integrity_marks", "political_money",
                   "comcom_coverage", "securities_register"),
    "04-agriculture": ("identity", "register_status", "entity_insolvency", "officer_group_insolvency", "register_removals", "prohibition",
                       "bankruptcy", "practitioner_repeat", "other_companies", "officers_of_record", "company_holders", "hubs_met",
                       "young_entity", "namesake_exposure", "charity_officer_roles", "charity_integrity_marks", "mpi_coverage",
                       "political_money", "replaced_rows"),
    "05-credit": ("entity_status", "monthly_changes", "recent_adverse_change", "officer_churn", "insolvency_notices", "register_events",
                  "officers_of_record", "young_entity", "people_failed_companies", "other_current_companies", "prohibition", "bankruptcy",
                  "subject_hub", "namesake_exposure", "walk_coverage", "status_name_changes", "since_date", "interface_freshness",
                  "past_roles", "change_history", "securities_register", "insolvency_register", "court_judgments", "credit_bureau",
                  "mortgagee_possession"),
    "06-insurance": ("entity_status", "young_entity", "insolvency_event", "register_events", "officer_churn", "sister_company_failure",
                     "other_current_companies", "prohibition", "bankruptcy", "practitioner_roles", "namesake_exposure", "walk_coverage",
                     "subject_hub", "past_roles", "safety_record", "regulator_actions", "court_judgments", "tribunals", "change_history",
                     "status_history", "mortgagee_possession", "insolvency_register", "securities_register"),
    "07-construction": ("phoenix_signature", "same_name_failed", "shared_office", "entity_status", "insolvency_notices", "repeat_failure",
                        "register_events", "other_current_companies", "officers_of_record", "young_entity", "prohibition", "bankruptcy",
                        "practitioner_roles", "practitioner_repeat", "society_roles", "namesake_exposure", "walk_coverage", "subject_hub",
                        "past_roles", "change_history", "building_practitioners", "insolvency_register", "court_judgments",
                        "employment_determinations", "securities_register", "mortgagee_possession", "public_contracts"),
    "08-recruitment": ("subject_hub", "prohibition", "bankruptcy", "liquidation_history", "register_removals", "namesake_exposure",
                       "charity_officer_roles", "charity_integrity_marks", "comcom_coverage", "young_entity", "public_life"),
    "11-healthcare": ("entity_status", "young_entity", "insolvency_notice", "officer_company_notices", "disqualified_officer",
                      "officer_bankruptcy", "officer_overlap", "charity_arm", "charity_returns_summary", "charity_audit_opinion",
                      "charity_return_filed", "namesake_exposure", "walk_coverage", "subject_hub", "past_roles", "retirement_villages",
                      "hdc_decisions", "certification_audits", "provider_registers", "aged_care_commissioner", "court_judgments"),
    "12-property": ("serial_pattern", "earlier_failure", "entity_status", "young_entity", "sole_vehicle", "professional_office",
                    "shared_office", "possession", "prohibition", "bankruptcy", "insolvency_notices", "holding_chain", "history_reach",
                    "namesake_exposure", "land_titles", "overseas_investment", "building_consents", "court_judgments", "securities_register",
                    "insolvency_register", "real_estate_authority", "building_practitioners", "past_roles"),
    "13-ownership": ("holding_chain", "ultimate_holders", "custodial_holders", "holder_hubs", "partnership_holders", "overseas_holders",
                     "sanctions_lists", "public_office", "political_money", "company_status", "insolvency_notices", "prohibition", "bankruptcy",
                     "young_entity", "officers_of_record", "namesake_exposure", "walk_coverage", "subject_hub", "securities_register"),
}


def run(report) -> list:
    """Every combined check on a built report, in order; the contract's common rules are the build's."""
    return [c(report) for c in CHECKS]
