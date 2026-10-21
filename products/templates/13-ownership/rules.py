"""The beneficial ownership and AML checks' rules, domestic half (plan 5.2,
use case 13). Pure functions over the built report, each returning one flag.
A compliance team asks "who ultimately holds or runs this, and are they
exposed". The rules stand for the old estate's person and company rules
(data-layer/flags/flags/person_rules.py, person-0.2; entity_rules.py,
entity-0.1) and its ownership-chain page (/api/use-case/bo/chain: the depth
limit, a cut chain that says it goes on, an empty holder list that says why,
an unresolved holder shown as a leaf), taken as ideas and tests, not code,
where the held registers can support them:

  holding-chain        the holders of record of the company, the companies among them, and the chain above them as far as the
                       template follows it: each company reached by business number (confirmed) or by a name one company carries
                       (near), the holders not followed, where the chain is cut, and what was read on the companies above
  ultimate-holders     blocked, never clear: a holder of record is not the person the shares are held for, and no register held names that person
  custodial-holders    a holder of record named as a nominee, trustee or custodian: shown as a holder of record, never more
  holder-hubs          a holder of record the walk flagged as a hub; blocked otherwise, because how many companies a holder holds is not read
  partnership-holders  a holder of record named as a limited partnership: its partners are not held
  overseas-holders     a holder of record named with an overseas company form: its own register is not held
  sanctions-lists      blocked, never clear: no sanctions list is held, so the exposure check has nothing to read
  public-office        a seat or candidacy confirmed to a person, or a member's declared interest naming the company (the domestic list of
                       politically exposed persons that rides on this use case); from a company its people are not followed
  political-money      donations and loans filed under the subject's name
  company-status       the company's register status (the old partnership-dissolved, widened)
  insolvency-notices   Gazette insolvency notices on the company, or on a person's companies (liquidation-history, group-receivership)
  prohibition          a director prohibition confirmed or near; blocked from a company, whose directors are not followed
  bankruptcy           blocked until a link rule reaches a Gazette bankruptcy notice
  young-entity         a company registered under 24 months
  officers-of-record   started from a company: no current director in the latest file
  namesake-exposure    the report's own uncertainty
  walk-coverage        how many of the companies reached had their notices and officers read
  subject-hub          the subject is itself a nominee, trustee, professional director or the Crown
  securities-register  blocked: the Personal Property Securities Register is not held

The builder adds its common rules for every template (group-standing,
hubs-met, replaced-return); this file carries no copy of them.

Every rule branches on the start: a company, a person, or anything else (a
filed donation, a notice). From a company the walk lists the directors and
holders of record and does not follow the people, so every check on the
people is blocked and says to start a report from each one; it follows a
company holder up the chain (the `chain` section), and the holders, directors
and notices read on a company above are the holder's: the holder checks read
the holders up the chain beside the company's own, saying where each sits,
and `insolvency-notices` sets a notice above beside the company's own. A check the walk could not
have seen is blocked, never clear. No flag joins two facts with a word of
cause, and none calls a holder of record more than that: dates sit side by
side, and a share count is the count filed for that holding.

Imports nothing of products.report: the one-way test holds a template folder
to its own code. The shape loads this file by path and binds the name
`contract` (products/report/contract.py) before it runs."""
from __future__ import annotations

import datetime as dt
import re

V = "0.1"
#: the old chain page's ceiling (its default was three); the template follows the chain `chain_depth` companies up (template.toml),
#: a company holder by its business number where the file carries one, otherwise by a name one company carries
CHAIN_DEPTH = 4
YOUNG_DAYS = 730          # under 24 months registered: worth a question (the old young-entity rule)
NAMESAKE_NOTE_AT = 5
NAMESAKE_PARTIAL_AT = 50
EXAMPLES = 3
#: whether a published view holds the person's past roles with their end dates; it does not (banking's measure, 2026-10-20), so a
#: check over a person's companies fires on what it sees and never clears
HISTORY = False
PAST_NOT_HELD = ("the companies file lists current roles only, so a company the person left, or that was removed with them on it, is not "
                 "seen")

#: a holder's name that says it holds for others (the walk flags nominee, trustee, custodian; a trust and a fiduciary are added here)
CUSTODIAL = re.compile(r"\b(nominees?|trustees?|trusts?|custodians?|custodial|fiduciary)\b", re.I)
PARTNERSHIP = re.compile(r"\b(limited partnership|l\.?p\.?)$|\blimited partnership\b", re.I)
#: company forms that are not New Zealand's: a holder so named is registered elsewhere, and its own register is not held; never
#: "corporation", which names NZ statutory bodies (ACCIDENT COMPENSATION CORPORATION holds shares; the checkpoint caught it), and
#: never "Inc", which NZ incorporated societies and Maori land incorporations also write (Gore District Memorial RSA Inc)
OVERSEAS_FORM = re.compile(r"\b(pty\.? ?(ltd|limited)\.?|pte\.? ?(ltd|limited)\.?|llc|l\.l\.c\.|gmbh|ag|s\.a\.?|b\.?v\.?|n\.v\.?|nv|plc|"
                           r"sdn\.? bhd\.?|k\.k\.|co\.,? ltd\.?|s\.a\.r\.l\.?|sarl|oy|ab|a/s|aps|s\.p\.a\.?|spa)$", re.I)
INSOLVENCY_VIEWS = ("gazette_liquidations", "gazette_company_notices")
INSOLVENCY_KINDS = ("winding-up application", "receivership", "administration", "notice to creditors", "deed of company arrangement")
INSOLVENT_STATUS = re.compile(r"liquidation|receiv|administration|statutory management", re.I)
ENDED_STATUS = re.compile(r"^(removed|deregistered|dissolved|closed|cancelled|inactive|suspended)$", re.I)
GOING_STATUS = re.compile(r"^registered$", re.I)
OFFICE_VIEWS = ("members", "candidates", "mp_interest_returns")
MONEY_VIEWS = ("party_return_donors", "party_return_loans", "disclosures", "disclosure_items", "candidate_return_donors")

HOLDERS_HELD = "Companies register shareholders (pub.shareholders)"
COMPANIES_HELD = "Companies register (pub.companies, pub.directors, pub.shareholders)"
GAZETTE_HELD = "New Zealand Gazette liquidation and company notices (pub.gazette_liquidations, pub.gazette_company_notices)"
NOT_HELD_INSOLVENCY = ("the Insolvency Register (interface awaited since 19 September 2026)", "court judgments (step 5.4)")
SANCTIONS = ("the Russia Sanctions Act 2022 sanctions register (Foreign Affairs and Trade)", "the United Nations Security Council consolidated list",
             "the Police list of designated terrorist entities (Terrorism Suppression Act 2002)")
LP_PARTNERS = "the limited partnerships register: a partnership's general and limited partners"
OVERSEAS = "overseas company registers: an overseas holder's own holders and directors"
FOR_WHOM = ("for whom a holder of record holds", "a trust's trustees, settlors and the people it holds for (New Zealand keeps no "
            "register of trusts, nor of the people shares are held for)", LP_PARTNERS, OVERSEAS)
SECURITIES = "the Personal Property Securities Register (interface awaited since 19 September 2026)"
NOT_FOLLOWED = ("started from a company, the report lists its directors and holders of record but does not follow them to their own links "
                "and companies yet; start a report from each person listed")
CHAIN_STOPS = (f"past the companies the chain reaches, and above a company holder it cannot place (a name several companies carry, or none: an "
               f"overseas company, a trust, a body of another kind), the holders and directors are not reached; the depth limit is {CHAIN_DEPTH} hops")


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
    return report["subject"]["kind"] == "person"


def _other_start(report):
    """A start row that is neither a company nor a person: the record these checks read is not walked from it."""
    if _company_start(report) or _person_start(report):
        return None
    s = report["subject"]
    article = "an" if s["kind"][:1] in "aeiou" else "a"
    return (f"the report starts from {article} {s['kind']} row (pub.{s['view']}), not a company or a person: the record these checks read is "
            f"not walked from it, so no clear is given; start the report from the company or from a person row")


def _subject_key(report) -> str:
    return report["subject"]["ref"].split(":", 1)[1]


def _walk_short(report) -> bool:
    w = report.get("walk") or {}
    return bool(w.get("entities_not_expanded") or w.get("entities_omitted"))


def _status(it) -> str:
    return (it["row"].get("status") or "").strip()


def _ending(it) -> str:
    st = _status(it)
    if INSOLVENT_STATUS.search(st):
        return "insolvent"
    if ENDED_STATUS.match(st) or _date(it["row"].get("removed_on")):
        return "ended"
    return "going"


def _insolvency(it) -> bool:
    return it["view"] == "gazette_liquidations" or (it["view"] == "gazette_company_notices" and it["row"].get("kind") in INSOLVENCY_KINDS)


def _on_subject(report, it) -> bool:
    return it.get("via") == report["subject"]["ref"] or (it["row"].get("register_key") or it["row"].get("entity_key") or "") == _subject_key(report)


def _holders(report) -> list:
    """The shareholders of record the holders section lists: from a company, those on the company itself (a namesake company's are near and
    apart); from a person, the person's own holdings and the other holders on the person's companies."""
    rows = [it for it in section(report, "holders")["items"] if it["view"] == "shareholders"]
    if _company_start(report):
        return [it for it in rows if _on_subject(report, it)]
    return rows


def _chain(report) -> list:
    """The rows the walk read up the holding chain (the chain section): the companies above, their holders, directors and notices."""
    names = {s["name"] for s in report["sections"]}
    return list(section(report, "chain")["items"]) if "chain" in names and _company_start(report) else []


def _above(report) -> list:
    """The companies above the company in the holding chain, nearest first."""
    return sorted([it for it in _chain(report) if it["view"] == "companies"], key=lambda it: (it.get("depth") or 0, it["ref"]))


def _chain_holders(report) -> list:
    """The holders of record on the companies above: the holder's, beside the company's own."""
    return [it for it in _chain(report) if it["view"] == "shareholders"]


def _is_company_holder(it) -> bool:
    return (it["row"].get("shareholder_type") or "").lower() == "company"


def _holder_name(it) -> str:
    """The name the register files the holder under; nothing for a suppressed row (a suppressed name is never read for a pattern or shown)."""
    return "" if it.get("suppressed") else (it["row"].get("name") or "")


def _hop(it) -> str:
    shares = it["row"].get("shares")   # numeric in the view, so a Decimal; an int in a fixture
    if shares is None:
        filed = "no share count filed"
    else:
        filed = f"{int(shares):,} shares filed for the holding" if shares == int(shares) else f"{shares} shares filed for the holding"
    up = f"; on a company {it['depth']} up the chain, {it['grade']}" if it.get("depth") else ""
    return f"{it['title']}: {filed} ({it['dates']['text']}{up})"


def _hops(rows) -> str:
    more = f"; and {len(rows) - EXAMPLES} more" if len(rows) > EXAMPLES else ""
    return "; ".join(_hop(it) for it in rows[:EXAMPLES]) + more


def _companies(report, grades=("confirmed",)):
    return [it for it in items(report, ("companies",), grades) if it["ref"] != report["subject"]["ref"]]


def _notices(report, grades=("confirmed",)):
    return list(items(report, INSOLVENCY_VIEWS, grades))


def _clear_or_past(rule, severity, text, **kw):
    if HISTORY:
        return flag(rule, V, "clear", severity, text, **kw)
    kw.pop("sources_held", None)
    return flag(rule, V, "blocked", severity, f"{text}; but {PAST_NOT_HELD}: no clear is given", **kw)


def _no_holders(report):
    """Why the company has no holder of record listed, or None when it has some."""
    r = report["subject"]["row"]
    if (r.get("entity_type") or "").lower().find("partnership") >= 0:
        return f"a limited partnership has partners, not shareholders, and {LP_PARTNERS} is not held"
    if _ending(report["subject"]) == "ended":
        return "the company is off the register, and the companies file keeps almost no holder of a removed company"
    return "the companies file lists no shareholder of record on the company: an entity of this type may have none, or the file omits them"


# ── the chain ───────────────────────────────────────────────────────────────

def holding_chain(report):
    """The holders of record of the company, and the companies among them, each with its shares and files: the chain stops at them."""
    if _other_start(report):
        return flag("holding-chain", V, "blocked", "amber", _other_start(report))
    if not _company_start(report):
        return flag("holding-chain", V, "blocked", "amber", "the chain is read upward from a company; started from a person, the companies the "
                    "person holds are listed in the holders section with their other holders of record: start a report from each company")
    holders = _holders(report)
    omitted = section(report, "holders").get("omitted") or 0
    companies = [it for it in holders if _is_company_holder(it)]
    tail = f"; {omitted:,} holder row(s) past the walk's limit, not read" if omitted else ""
    if companies:
        return flag("holding-chain", V, "fired", "amber",
                    f"{len(companies)} of the {len(holders)} holder(s) of record are companies. Each first hop, with the shares filed for it (no "
                    f"fraction is computed: a parcel held jointly is filed once per holder): {_hops(companies)}{tail}. {_up_the_chain(report)}",
                    citations=tuple(it["ref"] for it in companies + _above(report)), sources_not_held=(OVERSEAS, LP_PARTNERS), scope="entity")
    if not holders:
        return flag("holding-chain", V, "blocked", "amber", f"no holder of record is listed: {_no_holders(report)}; an empty list is not a "
                    "finding", scope="entity")
    if omitted:
        return flag("holding-chain", V, "blocked", "amber", f"{len(holders)} holder(s) of record read, none a company{tail}: a company could be "
                    "among those not read", scope="entity")
    return flag("holding-chain", V, "clear", "amber", f"the chain ends at the first hop: each of the {len(holders)} holder(s) of record is filed "
                "as an individual, not a company", sources_held=(HOLDERS_HELD,), scope="entity")


def _up_the_chain(report) -> str:
    """What the walk read above the first hop: the companies reached and how, the holders it could not follow, where it was cut, and
    the rows listed on the companies above."""
    w = report.get("walk") or {}
    depth = w.get("chain_depth") or 0
    if not depth:
        return f"The chain is not followed past the first hop (the template sets no chain depth): {CHAIN_STOPS}"
    above = _above(report)
    notes = w.get("chain_notes") or []
    st = w.get("chain") or {}
    conf = [it for it in above if it["grade"] == "confirmed"]
    bits = [f"Up the chain, followed {depth} up: {len(above)} company(ies) reached, {len(conf)} by business number (confirmed) and "
            f"{len(above) - len(conf)} by a name one company carries (near)"]
    if above:
        bits.append("; ".join(f"{it['title']} ({it.get('depth', '?')} up, {it['grade']}; {it.get('hop_text') or 'a holder of record'})"
                              for it in above[:EXAMPLES]) + (f"; and {len(above) - EXAMPLES} more" if len(above) > EXAMPLES else ""))
    if notes:
        bits.append(f"{len(notes)} holder(s) not followed: " + "; ".join(n["text"] for n in notes[:EXAMPLES]))
    cut = [it for it in above if it.get("chain_goes_on")]
    if cut:
        bits.append(f"the chain goes on past {depth} up at {len(cut)} company(ies)")
    rows = _chain(report)
    bits.append(f"on the companies above, {sum(1 for it in rows if it['view'] == 'shareholders')} holder(s) of record, "
                f"{sum(1 for it in rows if it['view'] == 'directors')} current director(s) and {sum(1 for it in rows if it['view'] in INSOLVENCY_VIEWS)} "
                "Gazette notice(s) are listed, each with its company's grade: the holder's rows, not the company's")
    if st.get("omitted"):
        bits.append(f"{st['omitted']} holder(s) or company(ies) past the walk's limit, not read")
    return "; ".join(bits) + f"; {CHAIN_STOPS}"


def ultimate_holders(report):
    """Never clear: the companies register names holders of record, and no register held names the person the shares are held for."""
    if _other_start(report):
        return flag("ultimate-holders", V, "blocked", "red", _other_start(report), sources_not_held=FOR_WHOM)
    if _person_start(report):
        return flag("ultimate-holders", V, "blocked", "red", "what the person holds through a company, a trust or a nominee, and for whom the "
                    "person's own holdings are held, is in no register held: the holdings listed are the person's of record only",
                    sources_not_held=FOR_WHOM)
    holders = _holders(report)
    people = [it for it in holders if not _is_company_holder(it)]
    custodial = [it for it in holders if CUSTODIAL.search(_holder_name(it))]
    counted = (f"{len(holders)} holder(s) of record listed: {len(people)} filed as individuals, {len(holders) - len(people)} as companies, "
               f"{len(custodial)} named as a nominee, trustee or custodian") if holders else f"no holder of record listed ({_no_holders(report)})"
    return flag("ultimate-holders", V, "blocked", "red", f"{counted}. A holder of record is the name on the share register; for whom it holds, "
                f"and who stands above the last company the chain reaches, is in no register held ({CHAIN_STOPS}); this report names no one for whom the shares "
                "are held", sources_not_held=FOR_WHOM, scope="entity")


def custodial_holders(report):
    """A holder of record named as a nominee, trustee or custodian: a holder of record, and nothing more."""
    if _other_start(report):
        return flag("custodial-holders", V, "blocked", "amber", _other_start(report))
    holders = _holders(report)
    hit = [it for it in holders + _chain_holders(report) if CUSTODIAL.search(_holder_name(it)) or any(f.get("kind") == "nominee" for f in it.get("flags", []))]
    on_subject = [it for it in hit if it["grade"] == "confirmed"]
    if hit:
        where = ("on the company or up its holding chain" if any(it.get("depth") for it in hit) else "on the company") if _company_start(report) \
            else "on the person's companies"
        return flag("custodial-holders", V, "fired", "amber" if on_subject else "info",
                    f"{len(hit)} holder(s) of record {where} are named as a nominee, trustee or custodian: each is shown as a holder of record, "
                    f"as the register states it; for whom it holds is in no register held: {_hops(hit)}",
                    citations=tuple(it["ref"] for it in hit), sources_not_held=FOR_WHOM[:2], scope="entity" if _company_start(report) else "near")
    if _company_start(report) and not holders:
        return flag("custodial-holders", V, "blocked", "amber", f"no holder of record is listed: {_no_holders(report)}", scope="entity")
    if section(report, "holders").get("omitted") or _walk_short(report):
        return flag("custodial-holders", V, "blocked", "amber", "the walk left holder rows or companies past its limit unread; a nominee could be "
                    "among them")
    up = len(_chain_holders(report))
    return flag("custodial-holders", V, "clear", "amber", f"none of the {len(holders)} holder(s) of record listed"
                + (f", nor of the {up} up its holding chain," if up else "") + " is named as a nominee, trustee or "
                "custodian; a holder can hold for others without saying so in its name", sources_held=(HOLDERS_HELD,), sources_not_held=FOR_WHOM[:2])


def holder_hubs(report):
    """A holder of record the walk flagged as a hub. How many companies a holder holds is not read, so no hub-free clear is given."""
    if _other_start(report):
        return flag("holder-hubs", V, "blocked", "info", _other_start(report))
    hit = [it for it in _holders(report) + _chain_holders(report) if any(f.get("kind") in ("nominee", "crown", "professional-director") for f in it.get("flags", []))]
    if hit:
        kinds = sorted({f["kind"] for it in hit for f in it["flags"] if f.get("kind") in ("nominee", "crown", "professional-director")})
        return flag("holder-hubs", V, "fired", "info", f"{len(hit)} holder(s) of record are hubs ({', '.join(kinds)}): a holding shared through a hub "
                    f"means little on its own: {_hops(hit)}", citations=tuple(it["ref"] for it in hit))
    return flag("holder-hubs", V, "blocked", "info", "no holder of record listed is flagged as a nominee, the Crown or a professional director, "
                "but how many companies a holder holds is not read by the walk, so a holder of a thousand companies is not flagged by its count")


def partnership_holders(report):
    if _other_start(report):
        return flag("partnership-holders", V, "blocked", "amber", _other_start(report), sources_not_held=(LP_PARTNERS,))
    hit = [it for it in _holders(report) + _chain_holders(report) if PARTNERSHIP.search(_holder_name(it).strip())]
    if _company_start(report) and "partnership" in (report["subject"]["row"].get("entity_type") or "").lower():
        hit = [report["subject"]] + hit
    if hit:
        return flag("partnership-holders", V, "fired", "amber", f"{len(hit)} limited partnership(s) on the chain, by the register's own words: "
                    f"{'; '.join(it['title'] for it in hit[:EXAMPLES])}; its general and limited partners are in {LP_PARTNERS}, which is not held",
                    citations=tuple(it["ref"] for it in hit), sources_not_held=(LP_PARTNERS,))
    return flag("partnership-holders", V, "blocked", "info", "no holder of record listed is named as a limited partnership, but the limited "
                "partnerships register is not held, so one named otherwise is not known as one", sources_not_held=(LP_PARTNERS,))


def overseas_holders(report):
    if _other_start(report):
        return flag("overseas-holders", V, "blocked", "amber", _other_start(report), sources_not_held=(OVERSEAS,))
    hit = [it for it in _holders(report) + _chain_holders(report) if _is_company_holder(it) and OVERSEAS_FORM.search(_holder_name(it).strip())]
    if hit:
        return flag("overseas-holders", V, "fired", "amber", f"{len(hit)} holder(s) of record are named with an overseas company form: "
                    f"{_hops(hit)}; its own register is not held, so its holders and directors are not reached",
                    citations=tuple(it["ref"] for it in hit), sources_not_held=(OVERSEAS,))
    return flag("overseas-holders", V, "blocked", "info", "no holder of record listed is named with an overseas company form, but overseas "
                "registers are not held, and a holder the chain finds no company of that name for is not said to be overseas, so an overseas "
                "holder named otherwise is not known as one", sources_not_held=(OVERSEAS,))


# ── exposure ────────────────────────────────────────────────────────────────

def _screened(report) -> int:
    """The names a sanctions screen would read: the subject, its group's rows, and every person or company listed."""
    return len({it["ref"] for it in all_items(report).values() if it["kind"] in ("person", "organisation") and it["view"] != "company_addresses"})


def sanctions_lists(report):
    return flag("sanctions-lists", V, "blocked", "red",
                f"no sanctions list is held, so the exposure check has nothing to read and is never clear: {_screened(report):,} name(s) on this "
                f"report would be screened against {'; '.join(SANCTIONS)}", sources_not_held=SANCTIONS)


def public_office(report):
    """A seat or candidacy confirmed to a person, or a member's declared interest naming the company."""
    office = list(items(report, OFFICE_VIEWS, ("confirmed",)))
    declared = [it for it in items(report, ("mp_interests",), ("confirmed",))]
    nearby = [it for it in section(report, "identity")["items"] if it["view"] in OFFICE_VIEWS] + \
        [it for it in items(report, OFFICE_VIEWS + ("mp_interests",), ("near",)) if it not in section(report, "identity")["items"]]
    if office or declared:
        bits = []
        if office:
            bits.append(f"{len(office)} row(s) of public office confirmed to the person: " + "; ".join(f"{it['title']} ({it['dates']['text']})"
                                                                                                    for it in office[:EXAMPLES]))
        if declared:
            bits.append(f"{len(declared)} member's declared interest(s) name the company: " + "; ".join(f"{it['title']} ({it['dates']['text']})"
                                                                                                         for it in declared[:EXAMPLES]))
        return flag("public-office", V, "fired", "amber", "a domestic public office on the record: " + "; ".join(bits)
                    + "; each listed with its date in the exposure section", citations=tuple(it["ref"] for it in office + declared))
    if nearby:
        return flag("public-office", V, "fired", "info", f"{len(nearby)} row(s) of public office under a name the subject only shares: a "
                    "namesake's until confirmed; a member's or candidate's name on the companies register is joined only with a supporting link",
                    citations=tuple(it["ref"] for it in nearby), scope="near")
    if _company_start(report):
        return flag("public-office", V, "blocked", "amber", "no link yet joins a member's declared interest to a company row, and "
                    f"{NOT_FOLLOWED}: whether any of them sat in the House or stood is not read", scope="officer-group")
    if _other_start(report):
        return flag("public-office", V, "blocked", "amber", _other_start(report))
    w = report.get("walk") or {}
    if not w.get("links_built") or w.get("links_omitted"):
        return flag("public-office", V, "blocked", "amber", "the links were not all read, so a seat or candidacy under the person's name could "
                    "be among those not read")
    return flag("public-office", V, "clear", "amber", "no seat in the House, candidacy or declared interest confirmed to the person, and no near "
                "one: the domestic offices held are the House's members and candidates since the lane's first election",
                sources_held=("Candidates and the House (pub.members, pub.candidates)", "MPs' declared interests (pub.mp_interest_returns)"),
                sources_not_held=("local-government office, Crown entity boards and the public service: no register joined to a person",))


def political_money(report):
    money = list(items(report, MONEY_VIEWS, ("confirmed",)))
    if money:
        return flag("political-money", V, "fired", "info", f"{len(money)} row(s) of political money filed under the subject's name; each listed "
                    "in the exposure section with its date and the party or candidate filed", citations=tuple(it["ref"] for it in money))
    if _other_start(report):
        return flag("political-money", V, "blocked", "info", _other_start(report))
    near_money = list(items(report, MONEY_VIEWS, ("near",)))
    if near_money:
        return flag("political-money", V, "fired", "info", f"{len(near_money)} row(s) of political money filed under the subject's name or one "
                    "near it, joined near: the Electoral Commission files a donor's name, never a number, so each is listed with the namesakes "
                    "and its reason, and is the filed donor's until a rule confirms it: " + "; ".join(f"{it['title']} ({it['dates']['text']})"
                                                                                                     for it in near_money[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in near_money), scope="near")
    if (report.get("walk") or {}).get("links_omitted"):
        return flag("political-money", V, "blocked", "info", f"the walk left {report['walk']['links_omitted']:,} link(s) unread past its limit; "
                    "a donation filed under the subject's name could be among them")
    whose = "the company's own; its directors' and holders' are not read" if _company_start(report) else "the person"
    return flag("political-money", V, "clear", "info", f"no donation, loan or disclosure filed under {whose}, confirmed or near",
                sources_held=("Electoral Commission returns and disclosures",),
                sources_not_held=("a candidate's own return, not yet joined to a person",))


# ── the company and the Gazette ─────────────────────────────────────────────

def company_status(report):
    if _other_start(report):
        return flag("company-status", V, "blocked", "red", _other_start(report))
    if _company_start(report):
        s = report["subject"]
        end = _ending(s)
        if end == "going":
            return flag("company-status", V, "clear", "red", f"the register files the company as {_status(s) or 'registered'} ({s['dates']['text']})",
                        sources_held=("Companies register (pub.companies)",), scope="entity")
        return flag("company-status", V, "fired", "red" if end == "insolvent" else "amber",
                    f"the register files the company as {_status(s) or 'removed'} ({s['dates']['text']})", citations=(s["ref"],), scope="entity")
    conf = [it for it in _companies(report) if _ending(it) != "going"]
    nearby = [it for it in _companies(report, ("near",)) if _ending(it) != "going"]
    if conf:
        return flag("company-status", V, "fired", "red" if any(_ending(it) == "insolvent" for it in conf) else "amber",
                    f"{len(conf)} of the person's companies are filed as insolvent or ended: "
                    + "; ".join(f"{it['title']}, {_status(it) or 'removed'} ({it['dates']['text']})" for it in conf[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in conf), scope="officer-group")
    if nearby:
        return flag("company-status", V, "fired", "amber", f"{len(nearby)} company(ies) reached only through a near link are filed as insolvent or "
                    "ended: a namesake's, not the person's until confirmed", citations=tuple(it["ref"] for it in nearby), scope="near")
    if _walk_short(report):
        return flag("company-status", V, "blocked", "red", "the walk stopped before listing every company the person has a row on")
    return _clear_or_past("company-status", "red", "every company the person has a row on is filed as registered",
                          sources_held=(COMPANIES_HELD,), scope="officer-group")


def insolvency_notices(report):
    if _other_start(report):
        return flag("insolvency-notices", V, "blocked", "red", _other_start(report), sources_not_held=NOT_HELD_INSOLVENCY)
    if _company_start(report):
        own = [it for it in _notices(report) if _insolvency(it) and _on_subject(report, it) and not it.get("above")]
        up = [it for it in _chain(report) if it["view"] in INSOLVENCY_VIEWS and _insolvency(it)]
        beside = ("; beside it, " + f"{len(up)} on a company above in the holding chain, the holder's and not the company's: "
                  + "; ".join(f"{it['title']} ({it['dates']['text']}; {it.get('depth', '?')} up, {it['grade']})" for it in up[:EXAMPLES])) if up else ""
        if own:
            return flag("insolvency-notices", V, "fired", "red", f"{len(own)} Gazette insolvency notice(s) on the company: "
                        + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in own[:EXAMPLES]) + beside,
                        citations=tuple(it["ref"] for it in own + up), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
        if up:
            return flag("insolvency-notices", V, "fired", "amber", "no Gazette insolvency notice on the company" + beside,
                        citations=tuple(it["ref"] for it in up), sources_not_held=NOT_HELD_INSOLVENCY, scope="chain")
        read = ("the notices on the companies the chain reaches above were read too" if (report.get("walk") or {}).get("chain_depth")
                else "a company holder's own notices are not read")
        return flag("insolvency-notices", V, "clear", "red", "no Gazette liquidation, receivership, administration, winding-up, creditors' notice or "
                    f"deed of company arrangement on the company; {read}",
                    sources_held=(GAZETTE_HELD + ", joined to the company by its number",), sources_not_held=NOT_HELD_INSOLVENCY, scope="entity")
    conf = [it for it in _notices(report) if _insolvency(it)]
    nearby = [it for it in _notices(report, ("near",)) if _insolvency(it)]
    if conf:
        return flag("insolvency-notices", V, "fired", "red", f"{len(conf)} Gazette insolvency notice(s) on {len({it.get('via') for it in conf})} "
                    "company(ies) the person has a row on, each with its own date; the person's dates on each are in the holders and officers "
                    "sections: " + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in conf[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in conf), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")
    if nearby:
        return flag("insolvency-notices", V, "fired", "amber", f"{len(nearby)} Gazette insolvency notice(s) on companies reached only through a near "
                    "link: a namesake's companies, not the person's until confirmed", citations=tuple(it["ref"] for it in nearby),
                    sources_not_held=NOT_HELD_INSOLVENCY, scope="near")
    if _walk_short(report):
        return flag("insolvency-notices", V, "blocked", "red", "no Gazette insolvency notice on the companies the walk read, but it stopped before "
                    "reading every company the person has a row on", scope="officer-group")
    return _clear_or_past("insolvency-notices", "red", "no Gazette insolvency notice on any company the person has a row on",
                          sources_held=(GAZETTE_HELD,), sources_not_held=NOT_HELD_INSOLVENCY, scope="officer-group")


def _in_force(report, it) -> str:
    as_of = _as_of(report)
    end = _date(it["row"].get("ends_on"))
    if it["row"].get("permanent"):
        return f"permanent; in force on {as_of.isoformat()}"
    if not end:
        return "no end filed"
    return f"in force on {as_of.isoformat()}" if end >= as_of else f"ended before {as_of.isoformat()}"


def prohibition(report):
    live = [it for it in items(report, ("gazette_prohibitions",)) if not it.get("suppressed")]   # a revoked prohibition is never counted
    conf = [it for it in live if it["grade"] == "confirmed"]
    nearby = [it for it in live if it["grade"] == "near"]
    if conf:
        return flag("prohibition", V, "fired", "red", f"{len(conf)} Gazette director prohibition notice(s) confirmed to the person: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']}; {_in_force(report, it)})" for it in conf[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in conf))
    if nearby:
        return flag("prohibition", V, "fired", "amber", f"{len(nearby)} Gazette director prohibition notice(s) under a name near the person's; a "
                    "namesake's until confirmed: " + "; ".join(f"{it['title']} ({it['dates']['text']}; near: {it.get('reason')})"
                                                              for it in nearby[:EXAMPLES]),
                    citations=tuple(it["ref"] for it in nearby), scope="near")
    if _company_start(report):
        return flag("prohibition", V, "blocked", "red", f"{NOT_FOLLOWED}: a prohibition is joined to a director's own row, which is not followed",
                    scope="officer-group")
    if _other_start(report):
        return flag("prohibition", V, "blocked", "red", _other_start(report))
    w = report.get("walk") or {}
    if not w.get("links_built"):
        return flag("prohibition", V, "blocked", "red", "no links are published, so a prohibition under the person's name cannot be reached")
    if w.get("links_omitted"):
        return flag("prohibition", V, "blocked", "red", f"the walk left {w['links_omitted']:,} link(s) unread past its limit; a prohibition could be "
                    "among them, so no clear is given")
    return flag("prohibition", V, "clear", "red", "no Gazette director prohibition confirmed or near the person: the link rules join every "
                "prohibition notice by name, and every link from the person's rows was read",
                sources_held=("New Zealand Gazette prohibition notices (pub.gazette_prohibitions), joined by name in pub.links",))


def bankruptcy(report):
    live_c = [it for it in items(report, ("gazette_bankruptcies",), ("confirmed",)) if not it.get("suppressed")]
    live_n = [it for it in items(report, ("gazette_bankruptcies",), ("near",)) if not it.get("suppressed")]
    if live_c:
        return flag("bankruptcy", V, "fired", "red", f"{len(live_c)} Gazette bankruptcy notice(s) confirmed to the person: "
                    + "; ".join(f"{it['title']} ({it['dates']['text']})" for it in live_c[:EXAMPLES]), citations=tuple(it["ref"] for it in live_c))
    if live_n:
        return flag("bankruptcy", V, "fired", "amber", f"{len(live_n)} Gazette bankruptcy notice(s) under a name near the person's; a namesake's "
                    "until confirmed", citations=tuple(it["ref"] for it in live_n), scope="near")
    return flag("bankruptcy", V, "blocked", "red", "Gazette bankruptcy notices are published, but no link rule joins one to a person yet, so this "
                "report cannot see a bankruptcy of the person or of a company's directors and holders; the blank is not a clear",
                sources_not_held=NOT_HELD_INSOLVENCY)


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
    if not _company_start(report) and _walk_short(report):
        return flag("young-entity", V, "blocked", "info", "the walk left companies past its limit, and their registration dates are not read")
    return flag("young-entity", V, "clear", "info", "registered 24 months ago or more" if _company_start(report)
                else "no company the person has a confirmed row on was registered under 24 months ago",
                sources_held=("Companies register (pub.companies)",))


def _current(it) -> bool:
    return bool(it["row"].get("in_latest")) and not it["row"].get("ended_on")


def officers_of_record(report):
    if _other_start(report):
        return flag("officers-of-record", V, "blocked", "info", _other_start(report), scope="entity")
    if not _company_start(report):
        return flag("officers-of-record", V, "clear", "info", "the subject is a person: its own roles are listed in the holders and officers "
                    "sections", sources_held=(COMPANIES_HELD,), scope="entity")
    if "partnership" in (report["subject"]["row"].get("entity_type") or "").lower():
        return flag("officers-of-record", V, "blocked", "info", f"a limited partnership has general and limited partners, not directors, and "
                    f"{LP_PARTNERS} is not held", sources_not_held=(LP_PARTNERS,), scope="entity")
    dirs = [it for it in section(report, "officers")["items"] if it["view"] == "directors" and _on_subject(report, it)]
    now = [it for it in dirs if _current(it)]
    omitted = section(report, "officers").get("omitted") or 0
    text = f"{len(now)} current director(s), {len(dirs) - len(now)} past or not in the latest file" + \
        (f"; {omitted:,} row(s) past the walk's limit, not listed" if omitted else "")
    if not now and not omitted and GOING_STATUS.match(_status(report["subject"])):
        return flag("officers-of-record", V, "fired", "amber", f"the companies file names no current director of the company: {text}",
                    citations=tuple(it["ref"] for it in dirs) or (report["subject"]["ref"],), scope="entity")
    return flag("officers-of-record", V, "clear", "info", text, sources_held=("Companies register directors (pub.directors)",), scope="entity")


# ── the report's own reach ──────────────────────────────────────────────────

def namesake_exposure(report):
    names = list(section(report, "identity")["items"])
    near_companies = [it for it in section(report, "holders")["items"] if it["view"] == "companies" and it["grade"] == "near"]
    w = report.get("walk") or {}
    g = report.get("group") or {}
    bits = []
    if len(names) >= NAMESAKE_PARTIAL_AT:
        bits.append(f"{len(names)} namesake row(s) set apart: the name is common, and this report is partial; confirm the subject by a second "
                    "fact before relying on any row")
    elif len(names) >= NAMESAKE_NOTE_AT:
        bits.append(f"{len(names)} namesake row(s) set apart")
    if near_companies:
        bits.append(f"{len(near_companies)} company(ies) that share the name or nearly do, listed near with their reason: the NZBN is the only "
                    "confirmation")
    if w.get("links_omitted"):
        bits.append(f"{w['links_omitted']:,} link(s) past the walk's limit, not read")
    if g.get("omitted"):
        bits.append(f"{g['omitted']:,} row(s) of the group past the walk's limit, not listed")
    if g.get("contested"):
        bits.append("the group is contested as a whole")
    if bits:
        cites = tuple(it["ref"] for it in names + near_companies) or (report["subject"]["ref"],)
        partial = len(names) >= NAMESAKE_PARTIAL_AT or g.get("contested")
        return flag("namesake-exposure", V, "fired", "amber" if partial else "info", "the report's own uncertainty: " + "; ".join(bits),
                    citations=cites)
    return flag("namesake-exposure", V, "clear", "info", f"low namesake exposure: {len(names)} namesake row(s) set apart and every link read",
                sources_held=("pub.links", "pub.groups"))


def walk_coverage(report):
    w = report.get("walk") or {}
    ne, om = w.get("entities_not_expanded") or 0, w.get("entities_omitted") or 0
    if ne or om:
        bits = []
        if ne:
            bits.append(f"{ne:,} company(ies) listed with their status, their holders, directors and notices not read")
        if om:
            bits.append(f"{om:,} past the walk's limit, not listed")
        return flag("walk-coverage", V, "fired", "amber", "the walk did not read every company it reached: " + "; ".join(bits)
                    + "; start a report from each company left out", citations=(report["subject"]["ref"],))
    return flag("walk-coverage", V, "clear", "info", "every company the walk reached was read for its holders, directors and notices",
                sources_held=("pub.companies", "pub.shareholders", "pub.directors", "pub.gazette_liquidations", "pub.gazette_company_notices"))


def subject_hub(report):
    if _other_start(report):
        return flag("subject-hub", V, "blocked", "info", _other_start(report))
    own = {report["subject"]["ref"]} | {m["ref"] for m in report.get("members", [])}
    mine = [h for h in report.get("hubs", []) if h["ref"] in own and h["kind"] in ("professional-director", "nominee", "crown")]
    named = CUSTODIAL.search(report["subject"]["row"].get("name") or report["subject"]["row"].get("full_name") or "") \
        if not report["subject"].get("suppressed") else None
    if mine or named:
        kinds = sorted({h["kind"] for h in mine} | ({"named as a nominee, trustee or custodian"} if named else set()))
        return flag("subject-hub", V, "fired", "info", f"the subject is itself a holder for others or a hub ({', '.join(kinds)}): what it holds "
                    "is held as the register states it, and a connection through it means little on its own",
                    citations=tuple(sorted({h["ref"] for h in mine} | ({report["subject"]["ref"]} if named else set()))))
    return flag("subject-hub", V, "clear", "info", "the subject is not named as a nominee, trustee or custodian, and is not a professional "
                "director or the Crown on the rows held", sources_held=("pub.directors", "pub.shareholders", "pub.groups"))


def securities_register(report):
    return flag("securities-register", V, "blocked", "amber", "who has registered security over the company's assets, and when, is in the "
                "Personal Property Securities Register, which is not held; this check cannot run", sources_not_held=(SECURITIES,))


RULES = (holding_chain, ultimate_holders, custodial_holders, holder_hubs, partnership_holders, overseas_holders, sanctions_lists, public_office,
         political_money, company_status, insolvency_notices, prohibition, bankruptcy, young_entity, officers_of_record, namesake_exposure,
         walk_coverage, subject_hub, securities_register)
