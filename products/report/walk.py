"""The walk outward from one row (plan 5.1): the group the row belongs to
(`pub.groups`), the confirmed links that make it and the near links beside
them with their reasons (`pub.links`), the entities the group's rows sit on
(a company, a society, a return, a promoter), the register's own rows on
each entity (its directors, shareholders, registered office, donors), and
one step further: the other people on those entities, listed as near,
never confirmed, because a connection through more than one person is near
by the design's default. Every item is a published row with its own dates;
a hop is dated by the role row that makes it, or marked undated.

Hubs are flagged as the walk meets them: a person whose group holds many
directorships (a professional director), a holder whose name says nominee
or trustee, the Crown, and a registered office shared by a busy or a
thousand companies. A hub is still walked; the flag tells the reader why
what it joins means little.

Three reaches a template asks for, because each costs queries and most
templates want only some: from an organisation start its officers are
followed one step (the `officers` bucket: each officer's other current
roles and the companies they sit on, with the notices on those, near by
the through-people default); the other companies at the start's registered
office are listed when the office is not a hub (the `office` bucket,
near: an office is not a person); and a company holder of record is
followed up the chain to its own holders (the `chain` bucket, to the
template's `chain_depth`, at most LIMITS["chain"]; a hop by business
number is confirmed, a hop by a name only one company carries is near, a
company met twice is listed once, a chain cut at the depth says it goes
on, and the shares are carried as filed, never as a fraction). A bucket no
section of the template draws on is not walked (`buckets`).

Nothing here reads a view the template did not name: `allowed` is the
template's list and a view outside it is skipped, with the skip recorded.
Limits are declared in the result, never silent: what the walk left out is
counted (lesson L708 of the old estate: a cut-off chain must say it goes on).
Reads `pub.*` only, on the product reader."""
from __future__ import annotations

import re

from products.report import catalogue as cat
from products.report import db, rows

LIMITS = {"members": 300, "links": 400, "roles": 200, "entities": 40, "second": 300, "expand": 12,
          "officers": 12, "officer_rows": 40, "office": 20, "chain": 4, "chain_holders": 25, "chain_companies": 40}
SETTINGS = {"hub_roles": 50, "hub_holdings": 50, "busy_address": 50, "thousand_address": 1000,
            "through_people": "near"}   # design: a connection through more than one person is near, never confirmed
BUCKETS = ("members", "confirmed", "near", "roles", "pointing", "second", "named", "officers", "office", "chain")

NEAR_THROUGH_PEOPLE = "a connection that passes through more than one person is listed as near, never confirmed (the design's default)"
NEAR_CONTESTED_GROUP = "the group this row belongs to is contested as a whole: the watch flagged it"
NEAR_THROUGH_NEAR = "reached through a near link: {reason}"
NEAR_BY_NAME = "the release prints a name only, so these rows are matched to the subject by name: near, never confirmed"
NO_GROUP_FOR_FILED = "a filed row ({view}): no confirmed link names a person row, so there is no group to take; every same name elsewhere is a namesake, apart"
ADOPTED_GROUP = "a filed row ({view}): the group shown is that of the person row a confirmed link names, {via}"
NEAR_THROUGH_OFFICER = "reached through a person on the subject ({who}): an officer's other role is the officer's connection, not the subject's; near, never confirmed"
NEAR_SHARED_OFFICE = "shares the registered office with the subject; an office is not a person, and a shared office is no connection on its own"
NEAR_HOLDER_BY_NAME = "the holder of record is matched to its own register row by name only ({n} company carries the name; the file gives no business number for a holder): near, never confirmed"
CHAIN_GOES_ON = "a company holder at the chain's depth limit: its own holders are not listed; the chain goes on"
NOMINEE = re.compile(r"\b(nominees?|trustees?|custodians?|custodial)\b", re.I)
CROWN = re.compile(r"\b(her majesty|his majesty|the crown|the sovereign|minister (of|for)|crown entity)\b", re.I)
LEGAL_ENDING = re.compile(r"\s+(limited|ltd\.?|tapui \(limited\)|incorporated|inc\.?)$", re.I)
#: the bodies the Crown holds through, named as the register names them (folded, legal ending off): the Crown entities of the
#: Crown Entities Act 2004 schedules 1 and 2, the Crown Research Institutes of its schedule 4, and the State enterprises of the
#: State-Owned Enterprises Act 1986 schedule 2, as read on 21 October 2026; a name pattern catches "the Crown" and a Minister
CROWN_BODIES = frozenset(cat.fold(x) for x in (
    # Crown agents and autonomous and independent Crown entities (schedule 1)
    "Accident Compensation Corporation", "Callaghan Innovation", "Civil Aviation Authority of New Zealand", "Earthquake Commission",
    "Natural Hazards Commission", "Toka Tu Ake", "Education New Zealand", "Energy Efficiency and Conservation Authority",
    "Environmental Protection Authority", "Fire and Emergency New Zealand", "Health New Zealand", "Te Whatu Ora",
    "Health Quality and Safety Commission", "Health Research Council of New Zealand", "Kainga Ora", "Kainga Ora-Homes and Communities",
    "Kāinga Ora–Homes and Communities", "Maritime New Zealand", "New Zealand Antarctic Institute", "New Zealand Blood and Organ Service",
    "New Zealand Blood Service", "New Zealand Qualifications Authority", "New Zealand Tourism Board", "Tourism New Zealand",
    "New Zealand Trade and Enterprise", "New Zealand Transport Agency", "Waka Kotahi", "Pharmaceutical Management Agency", "Pharmac",
    "Real Estate Agents Authority", "Social Workers Registration Board", "Sport and Recreation New Zealand", "Sport New Zealand",
    "Tertiary Education Commission", "WorkSafe New Zealand", "Arts Council of New Zealand Toi Aotearoa", "Creative New Zealand",
    "Broadcasting Standards Authority", "Commerce Commission", "Drug Free Sport New Zealand", "Electricity Authority",
    "External Reporting Board", "Financial Markets Authority", "Government Superannuation Fund Authority", "Guardians of New Zealand Superannuation",
    "Heritage New Zealand Pouhere Taonga", "Human Rights Commission", "Independent Police Conduct Authority", "Law Commission",
    "Museum of New Zealand Te Papa Tongarewa", "New Zealand Artificial Limb Service", "New Zealand Film Commission",
    "New Zealand Infrastructure Commission", "New Zealand Lotteries Commission", "Lotto New Zealand", "New Zealand Productivity Commission",
    "New Zealand Symphony Orchestra", "New Zealand Walking Access Commission", "Office of Film and Literature Classification",
    "Classification Office", "Privacy Commissioner", "Public Trust", "Retirement Commissioner", "Standards New Zealand",
    "Takeovers Panel", "Te Reo Whakapuaki Irirangi", "Te Mangai Paho", "Te Taura Whiri i te Reo Maori", "Maori Language Commission",
    "Transport Accident Investigation Commission", "Children's Commissioner", "Electoral Commission", "Health and Disability Commissioner",
    "Mental Health and Wellbeing Commission", "Climate Change Commission", "Criminal Cases Review Commission", "Maori Health Authority",
    "Te Aka Whai Ora", "Te Pukenga", "New Zealand Institute of Skills and Technology", "Accreditation Council",
    # Crown entity companies (schedule 2)
    "Crown Irrigation Investments", "New Zealand Growth Capital Partners", "New Zealand Venture Investment Fund", "Radio New Zealand",
    "Television New Zealand", "Crown Infrastructure Partners", "Network for Learning", "Education Payroll", "Tamaki Redevelopment Company",
    "New Zealand Green Investment Finance", "Predator Free 2050", "Research and Education Advanced Network New Zealand",
    # Crown Research Institutes (schedule 4), and the public research organisations they became in 2025
    "AgResearch", "Institute of Environmental Science and Research", "Institute of Geological and Nuclear Sciences", "GNS Science",
    "Landcare Research New Zealand", "Manaaki Whenua", "National Institute of Water and Atmospheric Research", "NIWA",
    "New Zealand Forest Research Institute", "Scion", "New Zealand Institute for Plant and Food Research", "Plant and Food Research",
    "New Zealand Institute for Bioeconomy Science", "New Zealand Institute for Earth Science", "New Zealand Institute for Public Health and Forensic Science",
    # State enterprises (State-Owned Enterprises Act 1986, schedule 2)
    "Airways Corporation of New Zealand", "Animal Control Products", "AsureQuality", "Electricity Corporation of New Zealand",
    "Kiwirail Holdings", "KiwiRail", "Kordia Group", "Landcorp Farming", "Pamu", "Meteorological Service of New Zealand", "MetService",
    "New Zealand Post", "New Zealand Railways Corporation", "Quotable Value", "Transpower New Zealand", "Learning Media", "Solid Energy New Zealand",
    # mixed-ownership companies the Crown holds a majority of, and the Reserve Bank
    "Genesis Energy", "Mercury NZ", "Meridian Energy", "Air New Zealand", "Reserve Bank of New Zealand",
))

#: the register's own rows on an entity: (child view, column holding the entity's key, order[, the entity's column joined, when not its key])
ROLES_ON = {
    "companies": (("directors", "entity_key", "appointed_on"), ("shareholders", "entity_key", "name"),
                  ("company_addresses", "entity_key", "started_on"), ("company_states", "entity_key", "file")),
    "societies": (("society_officers", "society_key", "started_on"),),
    "gazette_liquidations": (("gazette_liquidators", "notice", "ordinal", "notice"),),
    "gazette_company_notices": (("gazette_liquidators", "notice", "ordinal", "notice"),),
    "party_return_totals": (("party_return_donors", "return_key", "ordinal"), ("party_return_loans", "return_key", "ordinal")),
    "candidate_return_totals": (("candidate_return_donors", "return_key", "ordinal"),),
    "disclosures": (("disclosure_items", "declaration", "ordinal"),),
    "promoters": (("promoter_people", "promoter_key", "role"),),
    "mp_interest_returns": (("mp_interests", "member_return", "key"),),
}
#: entities expanded only when they are the start row: a return's other donors are not the subject's connections
EXPAND_ONLY_AS_START = frozenset({"party_return_totals", "candidate_return_totals", "disclosures", "mp_interest_returns"})
#: rows of other views that point at a company by its register key (a possession points twice: as lender and as borrower)
POINTING_AT = {"companies": (("gazette_liquidations", "register_key", "published_on"),
                             ("gazette_company_notices", "register_key", "published_on"),
                             ("gazette_possessions", "mortgagee_register_key", "published_on"),
                             ("gazette_possessions", "mortgagor_register_key", "published_on"))}
#: the views an officer is a row of, followed one step from an organisation start
OFFICER_VIEWS = frozenset({"directors", "society_officers"})
#: the role views of a person's group that count as "other current companies": kept only when current
ROLE_VIEWS = frozenset({"directors", "shareholders", "society_officers"})
#: the expense views carry a printed name and per-category lines: reached by link or by name, only the totals and money outside them are listed
EXPENSE_VIEWS = frozenset({"mp_expenses", "minister_expenses"})
EXPENSE_ROLES = ("total", "outside")
#: rows that carry a printed name and no key to a person row (the expense releases), reached from a person's row by name, as near:
#: (child view, its name column, the name column of the person row, the rows wanted)
NAMED_ROWS = {"members": (("mp_expenses", "name", "display_name", ("total", "outside")), ("minister_expenses", "name", "display_name", ("total", "outside"))),
              "mp_interest_returns": (("mp_expenses", "name", "name", ("total", "outside")), ("minister_expenses", "name", "name", ("total", "outside")))}
ADOPT_FROM = 10   # confirmed links from a filed row looked at for a person row whose group to take


# ── items ───────────────────────────────────────────────────────────────────

def item(v: cat.View, r: dict, entity_title: str = None, **extra) -> dict:
    """One row as the report carries it: ref, title, statement, dates,
    citation, grade and reason, flags. The row itself is kept for the
    template's rules; the memo never prints it whole."""
    it = {"ref": rows.ref_of(v, str(r.get(v.key_col))), "view": v.name, "register": v.register, "kind": v.kind,
          "title": rows.title(v, r), "statement": rows.statement(v, r, entity_title), "dates": rows.dates(v, r),
          "citation": rows.citation(v, r), "suppressed": rows.is_suppressed(v, r),
          "note": v.note if not (v.name in ("directors", "society_officers") and r.get("in_latest", True)) else "",
          "grade": "confirmed", "reason": None, "rule": None, "via": None, "flags": [], "row": r, "entity_title": entity_title,
          "replaced_by": r.get("replaced_by") or None}
    it.update(extra)
    return it


def near(it: dict, reason: str, rule: str = None) -> dict:
    it["grade"], it["reason"] = "near", reason
    if rule:
        it["rule"] = rule
    return it


def flag(kind: str, text: str, evidence=None) -> dict:
    return {"kind": kind, "text": text, "evidence": evidence}


# ── reading the links tables ────────────────────────────────────────────────

def links_built(conn) -> bool:
    return db.has_relation(conn, "pub", "links")


def group_of(conn, ref: str) -> dict:
    """{'built', 'why', 'group_id', 'contested', 'settings', 'rows', 'size', 'omitted'}."""
    if not db.has_relation(conn, "pub", "groups"):
        return {"built": False, "why": "no groups built yet: links/ has published nothing", "rows": [ref], "size": 1,
                "contested": False, "omitted": 0, "group_id": None, "settings": None}
    mine = db.rows(conn, "select * from pub.groups where row_key = %s", (ref,))
    if not mine:
        return {"built": True, "why": "this row is in no group: no confirmed link reaches it", "rows": [ref], "size": 1,
                "contested": False, "omitted": 0, "group_id": None, "settings": None}
    g = mine[0]
    got = db.rows(conn, "select row_key, count(*) over () as total from pub.groups where group_id = %s order by row_key limit %s",
                  (g["group_id"], LIMITS["members"]))
    size = got[0]["total"] if got else 1
    return {"built": True, "why": "", "group_id": g["group_id"], "contested": bool(g.get("contested")), "settings": g.get("settings"),
            "rows": [x["row_key"] for x in got], "size": size, "omitted": max(0, size - len(got))}


def links_of(conn, refs: list) -> dict:
    """{'built', 'confirmed': [...], 'near': [...], 'omitted'}: every link
    touching any of the refs; each: this, other, rule, evidence, grade,
    reason, watch, decision."""
    if not links_built(conn) or not refs:
        return {"built": links_built(conn), "confirmed": [], "near": [], "omitted": 0}
    got = db.rows(conn, "select *, count(*) over () as total from pub.links where row_a = any(%s) or row_b = any(%s) "
                        "order by grade, rule, row_a, row_b limit %s", (refs, refs, LIMITS["links"]))
    total = got[0]["total"] if got else 0
    mine = set(refs)
    out = {"built": True, "confirmed": [], "near": [], "omitted": max(0, total - len(got))}
    for l in got:
        this, other = (l["row_a"], l["row_b"]) if l["row_a"] in mine else (l["row_b"], l["row_a"])
        grade = l["grade"] if l["grade"] in ("confirmed", "near") else "near"
        out[grade].append({"this": this, "other": other, "rule": l["rule"], "evidence": l.get("evidence"), "grade": grade,
                           "reason": l.get("reason"), "watch": l.get("watch") or [], "decision": l.get("decision")})
    return out


def resolve(conn, ref: str, cache: dict):
    """(view, row) for a ref, cached across the walk, or None."""
    if ref not in cache:
        v, r = rows.locate(conn, ref)
        cache[ref] = (v, r) if r else None
    return cache[ref]


# ── hubs ────────────────────────────────────────────────────────────────────

def crown_body(name: str) -> bool:
    """True when the name, legal ending off, is a Crown entity, a Crown research
    institute or a State enterprise by its register name (CROWN_BODIES)."""
    return cat.fold(LEGAL_ENDING.sub("", (name or "").strip())) in CROWN_BODIES


def name_hub(name: str) -> dict | None:
    if not name:
        return None
    if CROWN.search(name):
        return flag("crown", "the Crown: a hub that joins thousands of rows; a connection through it means little on its own", name)
    if crown_body(name):
        return flag("crown", "a Crown entity or State enterprise, held by the Crown: a hub that joins thousands of rows; "
                             "a connection through it means little on its own", name)
    if NOMINEE.search(name):
        return flag("nominee", "a nominee or trustee holder: it holds as the register states, for others; it is shown as a "
                               "holder of record and never as an owner", name)
    return None


def role_counts(conn, refs: list) -> dict:
    """{ref: (group_id, directorships in that group, holdings in that group)}
    for person rows, in two queries: a lone row counts its own row (one or none)."""
    if not refs or not db.has_relation(conn, "pub", "names"):
        return {}
    got = db.rows(conn, "select n.ref, n.view, g.group_id from pub.names n left join pub.groups g on g.row_key = n.ref where n.ref = any(%s)", (refs,))
    groups = sorted({x["group_id"] for x in got if x["group_id"]})
    counts = {}
    if groups:
        for x in db.rows(conn, "select g.group_id, n.view, count(*) as n from pub.groups g join pub.names n on n.ref = g.row_key "
                               "where g.group_id = any(%s) and n.view in ('directors', 'shareholders') group by 1, 2", (groups,)):
            counts[(x["group_id"], x["view"])] = x["n"]
    out = {}
    for x in got:
        gid = x["group_id"]
        out[x["ref"]] = (gid, counts.get((gid, "directors"), 1 if x["view"] == "directors" else 0),
                         counts.get((gid, "shareholders"), 1 if x["view"] == "shareholders" else 0))
    return out


def holding_counts(conn, names: list) -> dict:
    """{name: companies held in the latest file} for company holders of record,
    counted on the name because the file gives a holder no business number
    (`a-company-holder-carries-no-business-number`); one query."""
    names = sorted({n for n in names if n})
    if not names:
        return {}
    return {x["name"]: x["n"] for x in db.rows(conn, "select name, count(distinct entity_key) as n from pub.shareholders "
                                                     "where in_latest and name = any(%s) group by 1", (names,))}


def company_holder(r: dict) -> bool:
    """A holder of record that is a company: the file says `company` or
    `individual` (`shareholder_type`); anything not an individual is followed."""
    return (r.get("shareholder_type") or "").strip().lower() not in ("individual", "person")


def holder_item_name(it: dict) -> str:
    return it["row"].get("name") or it["row"].get("full_name") or ""


def flag_people(conn, items: list) -> None:
    """Flags a professional director (a group with `hub_roles` directorships
    or more), a holder of record in `hub_holdings` companies or more (a
    company holder counted on its name, a person on its group), and a name
    that says nominee or trustee, the Crown or a Crown body."""
    counts = role_counts(conn, [it["ref"] for it in items if it["kind"] == "person"])
    company_holders = [holder_item_name(it) for it in items if it["view"] == "shareholders" and not it["suppressed"] and company_holder(it["row"])]
    held = holding_counts(conn, company_holders)
    for it in items:
        gid, n, held_in_group = counts.get(it["ref"], (None, 0, 0))
        if n >= SETTINGS["hub_roles"]:
            it["flags"].append(flag("professional-director", f"a professional director: this person's group holds {n:,} directorships; "
                                                             f"a shared board with them joins little", {"group": gid, "directorships": n}))
        h = name_hub(holder_item_name(it)) if not it["suppressed"] else None
        if h:
            it["flags"].append(h)
        if it["view"] == "shareholders" and not it["suppressed"]:
            name = holder_item_name(it)
            m = held.get(name, 0) if name in held else held_in_group
            it["holdings"] = m
            if m >= SETTINGS["hub_holdings"]:
                it["flags"].append(flag("holding-hub", f"a holder of record in {m:,} companies in the latest file: it holds as the register states, "
                                                       f"for many; a shared holder here joins little", {"holdings": m,
                                                       "counted_on": "name" if name in held else "group"}))


def address_hub(conn, office: dict) -> dict | None:
    """A registered office shared by a busy (50) or a thousand companies in the latest file."""
    if not office.get("in_latest"):
        return None
    n = db.rows(conn, "select count(distinct entity_key) as n from pub.company_addresses where in_latest and line_1 = %s "
                      "and coalesce(line_2, '') = %s and coalesce(postcode, '') = %s",
                (office.get("line_1"), office.get("line_2") or "", office.get("postcode") or ""))[0]["n"]
    if n >= SETTINGS["thousand_address"]:
        return flag("thousand-address", f"an address with a thousand companies: {n:,} companies have their registered office here; "
                                        f"a shared address here is no connection", {"companies": n})
    if n >= SETTINGS["busy_address"]:
        return flag("busy-address", f"a busy address: {n:,} companies have their registered office here", {"companies": n})
    return None


# ── the register's own rows on an entity ────────────────────────────────────

def roles_on(conn, ev: cat.View, e: dict, allowed: set, skipped: list) -> list:
    out = []
    for entry in ROLES_ON.get(ev.name, ()):
        child, column, order = entry[:3]
        parent_col = entry[3] if len(entry) > 3 else ev.key_col
        if child not in allowed:
            skipped.append(child)
            continue
        cv = cat.BY_NAME[child]
        total, got = rows_where(conn, child, column, e[parent_col], order)
        for r in got:
            out.append(item(cv, r, rows.title(ev, e), via=rows.ref_of(ev, str(e[ev.key_col]))))
        if total > len(got):
            out.append({"omitted": total - len(got), "view": child, "via": rows.ref_of(ev, str(e[ev.key_col]))})
    return out


def pointing_at(conn, ev: cat.View, e: dict, allowed: set, skipped: list) -> list:
    out = []
    for child, column, order in POINTING_AT.get(ev.name, ()):
        if child not in allowed:
            skipped.append(child)
            continue
        cv = cat.BY_NAME[child]
        total, got = rows_where(conn, child, column, e[ev.key_col], order)
        for r in got:
            out.append(item(cv, r, rows.title(ev, e), via=rows.ref_of(ev, str(e[ev.key_col]))))
        if total > len(got):
            out.append({"omitted": total - len(got), "view": child, "via": rows.ref_of(ev, str(e[ev.key_col]))})
    return out


def rows_where(conn, view: str, column: str, value, order: str) -> tuple:
    return rows.rows_where(conn, view, column, value, LIMITS["roles"], order)


def first_last(name: str) -> str:
    w = cat.fold(name).split()
    return f"{w[0]} {w[-1]}" if len(w) > 1 else (w[0] if w else "")


def named_rows(conn, pv: cat.View, p: dict, allowed: set, skipped: list, via: str) -> list:
    """The rows of NAMED_ROWS views whose printed name is the person row's
    (folded whole, or first and last word), graded near by name."""
    out = []
    for child, col, person_col, roles in NAMED_ROWS.get(pv.name, ()):
        if child not in allowed:
            skipped.append(child)
            continue
        name = p.get(person_col) or ""
        if not name or rows.is_suppressed(pv, p):
            continue
        cv = cat.BY_NAME[child]
        folded = f"translate(lower({col}), 'āēīōū', 'aeiou')"
        got = db.rows(conn, f"select *, {cv.key_col} as key, count(*) over () as total from pub.{cv.name} "
                            f"where role = any(%s) and ({folded} = %s or split_part({folded}, ' ', 1) || ' ' || regexp_replace({folded}, '^.* ', '') = %s) "
                            f"order by period_start desc nulls last, {cv.key_col} limit %s", (list(roles), cat.fold(name), first_last(name), LIMITS["roles"]))
        total = got[0]["total"] if got else 0
        for r in got:
            r.pop("total", None)
            out.append(near(item(cv, r, via=via), NEAR_BY_NAME, "printed-name"))
        if total > len(got):
            out.append({"omitted": total - len(got), "view": child, "via": via})
    return out


def listable(v: cat.View, r: dict) -> bool:
    """False for a row the report never lists however it is reached: an
    expense release's per-category line (the totals and the money outside
    them are listed; the lines behind them are in the view, not the memo)."""
    return not (v.name in EXPENSE_VIEWS and (r.get("role") or "") not in EXPENSE_ROLES)


def adopted_group(conn, ref: str, sv: cat.View, cache: dict) -> dict:
    """The group a filed row (a donation, a loan, a disclosure, an interest)
    takes: that of the person row a confirmed link names, the first by ref
    when several; how many groups those person rows fall in is counted."""
    none = {"built": True, "why": NO_GROUP_FOR_FILED.format(view=sv.name), "rows": [ref], "size": 1, "contested": False, "omitted": 0,
            "group_id": None, "settings": None, "via": None, "via_groups": 0}
    L = links_of(conn, [ref])
    people = []
    for l in L["confirmed"]:
        hit = resolve(conn, l["other"], cache)
        if hit and hit[0].kind == "person":
            people.append(l["other"])
    if not people:
        return none
    people = sorted(set(people))[:ADOPT_FROM]
    groups = {}
    for pref in people:
        g = group_of(conn, pref)
        groups.setdefault(g.get("group_id") or pref, (pref, g))
    via, g = groups[min(groups, key=lambda k: groups[k][0])]
    g = dict(g, via=via, via_groups=len(groups), why=ADOPTED_GROUP.format(view=sv.name, via=via)
             + (f"; confirmed links name person rows in {len(groups)} groups, and the first by ref is walked" if len(groups) > 1 else ""))
    g["rows"] = [ref] + [r for r in g["rows"] if r != ref]
    g["size"] = g["size"] + (0 if ref in group_of(conn, via)["rows"] else 1)
    return g


# ── the walk ────────────────────────────────────────────────────────────────

def link_item(conn, l: dict, cache: dict, allowed: set, skipped: list, via: str = None) -> dict | None:
    hit = resolve(conn, l["other"], cache)
    if not hit:
        return {"ref": l["other"], "missing": True, "rule": l["rule"], "grade": l["grade"], "reason": l.get("reason"), "via": via or l["this"],
                "statement": f"{l['other']}: row not found in the published views (its key has moved or it was withdrawn)", "flags": [],
                "dates": {"undated": True, "text": rows.UNDATED}, "citation": {"view": "", "key": l["other"]}, "kind": "", "view": "",
                "register": rows.split_ref(l["other"])[0], "title": l["other"], "suppressed": False, "row": {}, "note": ""}
    v, r = hit
    if v.name not in allowed:
        skipped.append(v.name)
        return None
    if not listable(v, r):
        return None   # a per-category expense line: the named route's filter holds for a link too (totals and money outside the total only)
    ev, e = rows.entity_of(conn, v, r)
    it = item(v, r, rows.title(ev, e) if e else None, via=via or l["this"], rule=l["rule"], evidence=l.get("evidence"),
              watch=l.get("watch") or [], decision=l.get("decision"))
    if e:
        it["entity"] = item(ev, e)
    if l["grade"] == "near":
        near(it, l.get("reason") or "the rule that joined these rows grades the link near", l["rule"])
    return it


def current_role(r: dict) -> bool:
    """A role row still in the latest file with no end filed."""
    return bool(r.get("in_latest", True)) and not r.get("ended_on")


def follow_officers(conn, ref: str, officers: list, allowed: set, skipped: list, cache: dict) -> tuple:
    """From an organisation start, each officer on it one step: the rows of
    the officer's group (confirmed links) the template allows, role rows only
    when current, the companies and societies they sit on, and the notices
    pointing at those; every item near by the through-people default
    (NEAR_THROUGH_OFFICER), via the officer's row on the start. Returns
    (items, officers followed, officers past the limit)."""
    out, seen = [], set()
    followed = [o for o in officers if not o["suppressed"]][:LIMITS["officers"]]
    for o in followed:
        g = group_of(conn, o["ref"])
        reason = NEAR_THROUGH_OFFICER.format(who=o["title"])
        if g.get("contested"):
            reason = NEAR_CONTESTED_GROUP + "; " + reason
        n_rows = 0
        for mref in g["rows"]:
            if mref == o["ref"]:
                continue
            hit = resolve(conn, mref, cache)
            if not hit:
                continue
            mv, mr = hit
            if mv.name not in allowed:
                skipped.append(mv.name)
                continue
            if (mv.name in ROLE_VIEWS and not current_role(mr)) or not listable(mv, mr):
                continue
            ev, e = rows.entity_of(conn, mv, mr)
            if e and rows.ref_of(ev, str(e[ev.key_col])) == ref:
                continue   # the officer's row on the start itself is already listed
            if n_rows >= LIMITS["officer_rows"]:
                out.append({"omitted": 1, "view": mv.name, "via": o["ref"]})
                continue
            n_rows += 1
            it = near(item(mv, mr, rows.title(ev, e) if e else None, via=o["ref"], through=o["ref"], depth=1), reason, "through-officer")
            out.append(it)
            if e:
                eref = rows.ref_of(ev, str(e[ev.key_col]))
                if eref in seen:
                    continue
                seen.add(eref)
                eit = near(item(ev, e, via=it["ref"], through=o["ref"], hop=it["dates"], depth=1), reason, "through-officer")
                out.append(eit)
                if ev.name == "companies":
                    for pit in pointing_at(conn, ev, e, allowed, skipped):
                        if "omitted" not in pit:
                            near(pit, reason, "through-officer")
                            pit["through"] = o["ref"]
                        out.append(pit)
    # one omitted line per (view, officer), counted
    merged, counts = [], {}
    for it in out:
        if "omitted" in it:
            counts[(it["view"], it["via"])] = counts.get((it["view"], it["via"]), 0) + it["omitted"]
        else:
            merged.append(it)
    merged += [{"omitted": n, "view": v, "via": via} for (v, via), n in counts.items()]
    return merged, len(followed), max(0, len([o for o in officers if not o["suppressed"]]) - len(followed))


def office_companies(conn, ref: str, office: dict, allowed: set, skipped: list) -> tuple:
    """The other companies whose registered office in the latest file is the
    start's, when the office is not a hub (fewer than `busy_address`), near:
    an office is not a person. Returns (items, companies at the office, listed)."""
    if "companies" not in allowed:
        skipped.append("companies")
        return [], 0, 0
    cv = cat.BY_NAME["companies"]
    got = db.rows(conn, "select c.*, c.key as key, count(*) over () as total from pub.company_addresses a join pub.companies c on c.key = a.entity_key "
                        "where a.in_latest and a.line_1 = %s and coalesce(a.line_2, '') = %s and coalesce(a.postcode, '') = %s and a.entity_key <> %s "
                        "order by c.registered_on desc nulls last, c.key limit %s",
                  (office.get("line_1"), office.get("line_2") or "", office.get("postcode") or "", office["entity_key"], LIMITS["office"]))
    total = got[0]["total"] if got else 0
    if total + 1 >= SETTINGS["busy_address"]:
        return [], total + 1, 0   # a hub: flagged on the entity, and nobody at it is listed
    via = rows.ref_of(cat.BY_NAME["company_addresses"], str(office["key"]))
    out = []
    for r in got:
        r.pop("total", None)
        out.append(near(item(cv, r, via=via, through=ref), NEAR_SHARED_OFFICE, "shared-office"))
    if total > len(got):
        out.append({"omitted": total - len(got), "view": "companies", "via": via})
    return out, total + 1, len(got)


def resolve_holders(conn, holders: list) -> dict:
    """{holder row key: (company row, how, same-name count)} for company
    holders of record: by business number when the file carries one, else by
    the exact name when one company of that name is in the register; two
    queries for the lot."""
    out = {}
    by_nzbn = {h["key"]: h["holder_nzbn"] for h in holders if h.get("holder_nzbn")}
    by_name = {h["key"]: (h.get("name") or "").strip() for h in holders if not h.get("holder_nzbn") and (h.get("name") or "").strip()}
    if by_nzbn:
        found = {r["nzbn"]: r for r in db.rows(conn, "select *, key as key from pub.companies where nzbn = any(%s)", (sorted(set(by_nzbn.values())),))}
        for k, n in by_nzbn.items():
            if n in found:
                out[k] = (found[n], "nzbn", 1)
    if by_name:
        found = {}
        for r in db.rows(conn, "select *, key as key from pub.companies where name = any(%s) order by key", (sorted(set(by_name.values())),)):
            found.setdefault(r["name"], []).append(r)
        for k, n in by_name.items():
            rows_ = found.get(n, [])
            out[k] = (rows_[0] if len(rows_) == 1 else None, "name", len(rows_))
    return out


def chain(conn, start_ref: str, start_row: dict, allowed: set, skipped: list, chain_depth: int) -> tuple:
    """The holding chain above a company: its company holders of record
    resolved to their own register rows (depth 1), their holders, and so on
    to `chain_depth` (at most LIMITS["chain"]). Each company item carries its
    depth, the holder row it came through (`via`), that row's dates as the
    hop and the shares as filed; each holder row its depth and the company it
    is on. A hop by business number is confirmed; by a name one company
    carries, near; a name several carry, or none, is not followed and says
    so; a company met twice is listed once; at the depth limit a company
    holder says the chain goes on. Returns (items, stats)."""
    stats = {"depth": 0, "companies": 0, "holders": 0, "cut": 0, "cycles": 0, "unresolved": 0, "omitted": 0}
    depth = min(int(chain_depth or 0), LIMITS["chain"])
    if depth < 1:
        return [], stats
    if "shareholders" not in allowed or "companies" not in allowed:
        skipped.append("shareholders" if "shareholders" not in allowed else "companies")
        return [], stats
    cv, sv = cat.BY_NAME["companies"], cat.BY_NAME["shareholders"]
    out = []
    seen = {start_row["key"]}
    frontier = [(start_row, 0, "confirmed", None)]   # (company row, depth, grade, reason)
    for d in range(1, depth + 1):
        if not frontier:
            break
        stats["depth"] = d
        keys = [c["key"] for c, *_ in frontier]
        below = {c["key"]: (c, g, why) for c, _, g, why in frontier}
        got = db.rows(conn, "select *, key as key, count(*) over (partition by entity_key) as total, "
                            "row_number() over (partition by entity_key order by shares desc nulls last, key) as rn "
                            "from pub.shareholders where entity_key = any(%s) and in_latest order by entity_key, rn", (keys,))
        holders = []
        for r in got:
            if r.pop("rn") > LIMITS["chain_holders"]:
                stats["omitted"] += 1
                continue
            r.pop("total", None)
            holders.append(r)
        company_holders = [r for r in holders if company_holder(r)]
        resolved = resolve_holders(conn, company_holders)
        next_frontier = []
        for r in holders:
            c, below_grade, below_why = below[r["entity_key"]]
            if d > 1:   # depth 1 holders are the start's own rows, listed in `roles` already; the chain lists the rest
                hit = near(item(sv, r, rows.title(cv, c), via=rows.ref_of(cv, str(c["key"])), depth=d - 1), below_why, "chain") \
                    if below_grade == "near" else item(sv, r, rows.title(cv, c), via=rows.ref_of(cv, str(c["key"])), depth=d - 1)
                out.append(hit)
                stats["holders"] += 1
            if r["key"] not in resolved:
                continue   # a person, or a holder with no name: the chain ends at a person
            crow, how, n = resolved[r["key"]]
            holder_ref = rows.ref_of(sv, str(r["key"]))
            if crow is None:
                stats["unresolved"] += 1
                out.append({"chain_note": f"{rows.title(sv, r)}: not followed; {n} companies of this name in the register" if n
                            else f"{rows.title(sv, r)}: not followed; no company of this name in the register (an overseas company, a trust or a body of another kind)",
                            "via": holder_ref, "depth": d})
                continue
            if crow["key"] in seen:
                stats["cycles"] += 1
                out.append({"chain_note": f"{rows.title(cv, crow)} is listed above: a company met twice (a cycle, or two paths)", "via": holder_ref, "depth": d})
                continue
            if stats["companies"] >= LIMITS["chain_companies"]:
                stats["omitted"] += 1
                continue
            seen.add(crow["key"])
            stats["companies"] += 1
            hop = rows.dates(sv, r)
            it = item(cv, crow, via=holder_ref, through=rows.ref_of(cv, str(c["key"])), hop=hop, depth=d,
                      hop_text=f"holds {rows.fmt(r.get('shares'), 'shares')} shares of record in {rows.title(cv, c)}, as filed ({hop['text']})")
            grade, why = below_grade, below_why
            if how == "name":
                grade, why = "near", NEAR_HOLDER_BY_NAME.format(n=n)
            if grade == "near":
                near(it, why, "chain")
            if d == depth:
                it["chain_goes_on"] = True
                it["note"] = CHAIN_GOES_ON
                stats["cut"] += 1
            out.append(it)
            next_frontier.append((crow, d, grade, why))
        frontier = next_frontier
    return out, stats


def walk(conn, ref: str, allowed: set, depth: int = 2, buckets=None, chain_depth: int = 0) -> dict:
    """The walk from one row. `allowed`: the published views the template
    names. `depth`: 1 = the group and the entities it sits on; 2 = also the
    other rows on those entities (near). `buckets`: the walk's buckets some
    section of the template draws on (all when None); the officers, office
    and chain reaches run only when asked for. `chain_depth`: how many
    company holders up the chain is followed from a company start."""
    cache = {}
    wanted = set(BUCKETS if buckets is None else buckets)
    hit = resolve(conn, ref, cache)
    if not hit:
        return {"found": False, "why": f"{ref}: no published row has this ref"}
    sv, sr = hit
    skipped = []
    sev, se = rows.entity_of(conn, sv, sr)
    out = {"found": True, "start": item(sv, sr, rows.title(sev, se) if se else None), "settings": dict(SETTINGS), "limits": dict(LIMITS), "skipped": skipped,
           "members": [], "confirmed": [], "near": [], "entities": [], "roles": [], "pointing": [], "second": [], "named": [], "hubs": [],
           "officers": [], "office": [], "chain": [], "chain_stats": {},
           "officers_followed": 0, "officers_omitted": 0, "office_companies": 0, "office_listed": 0}
    if sv.name not in allowed:
        out["start_outside_template"] = True
    # 1. the group: a person's own; a filed row takes the group of the person row a confirmed link names; an organisation needs none
    if sv.kind == "person":
        g = group_of(conn, ref)
    elif sv.kind == "figure" and links_built(conn):
        g = adopted_group(conn, ref, sv, cache)
    else:
        g = {"built": links_built(conn), "why": "an organisation needs no group: its official number is the link",
             "rows": [ref], "size": 1, "contested": False, "omitted": 0, "group_id": None, "settings": None}
    out["group"] = {k: g.get(k) for k in ("built", "why", "group_id", "contested", "settings", "size", "omitted", "via", "via_groups")}
    subject_person = sv.kind == "person" or bool(g.get("via"))   # a filed row walking a person's group is graded as a person's walk
    member_refs = [ref] + [r for r in g["rows"] if r != ref]      # the start first: its own entity is confirmed whatever other member reaches it
    members = set(member_refs)
    for mref in member_refs:
        mhit = resolve(conn, mref, cache)
        if not mhit:
            continue
        mv, mr = mhit
        if mv.name not in allowed:
            skipped.append(mv.name)
            continue
        if mref != ref and not listable(mv, mr):
            continue
        ev, e = rows.entity_of(conn, mv, mr)
        it = item(mv, mr, rows.title(ev, e) if e else None, via=None if mref == ref else ref)
        if g["contested"] and mref != ref:
            near(it, NEAR_CONTESTED_GROUP)
        out["members"].append(it)
        if e:
            eit = item(ev, e, via=mref, hop=it["dates"])
            if it["grade"] == "near":
                near(eit, it["reason"])
            out["entities"].append(eit)
        # a member row with child rows of its own (an interests return and its declarations) is its own entity: the subject's own filing
        if mv.name in ROLES_ON and mv.kind != "organisation":
            eit = item(mv, mr, via=None if mref == ref else ref, hop=it["dates"])
            if it["grade"] == "near":
                near(eit, it["reason"])
            out["entities"].append(eit)
        # rows that carry this person's printed name and no key (the expense releases): by name, near
        for nit in named_rows(conn, mv, mr, allowed, skipped, mref):
            if "omitted" in nit:
                out["roles"].append(nit)
            elif it["grade"] == "near":
                out["named"].append(near(nit, NEAR_THROUGH_NEAR.format(reason=it["reason"]), nit["rule"]))
            else:
                out["named"].append(nit)
    # 2. the links, confirmed and near
    L = links_of(conn, member_refs)
    out["links_built"] = L["built"]
    out["links_omitted"] = L["omitted"]
    for l in L["confirmed"]:
        it = link_item(conn, l, cache, allowed, skipped)
        if it:
            it["in_group"] = l["other"] in members
            out["confirmed"].append(it)
            if not it.get("missing") and it["kind"] == "organisation" and l["other"] not in members:
                out["entities"].append(dict(it, hop=it["dates"]))
    for l in L["near"]:
        it = link_item(conn, l, cache, allowed, skipped)
        if it:
            out["near"].append(it)
            if not it.get("missing") and it["kind"] == "organisation":
                out["entities"].append(dict(it, hop=it["dates"]))
    # an organisation start is its own entity (a person start with child rows was added with the members, above)
    if sv.kind == "organisation" and sv.name in allowed and sv.name in ROLES_ON:
        out["entities"].insert(0, item(sv, sr))
    # 3. each entity: the register's own rows on it, rows pointing at it, its own links (one step)
    seen_entities, expanded = {}, 0
    for eit in out["entities"]:   # each once; a confirmed copy is kept over a near one, whichever member reached it first
        have = seen_entities.get(eit["ref"])
        if have is None or (have["grade"] == "near" and eit["grade"] == "confirmed"):
            seen_entities[eit["ref"]] = eit
    entities = list(seen_entities.values())
    out["entities"] = entities[:LIMITS["entities"]]
    out["entities_omitted"] = max(0, len(entities) - LIMITS["entities"])
    start_office = None
    for eit in out["entities"]:
        ev = cat.BY_NAME[eit["view"]]
        e = eit["row"]
        if ev.name == "companies":
            office = [r for r in rows.rows_where(conn, "company_addresses", "entity_key", e["key"], 5, "started_on")[1] if r.get("in_latest")] \
                if "company_addresses" in allowed else []
            for o in office[:1]:
                h = address_hub(conn, o)
                if h:
                    eit["flags"].append(h)
                if eit["ref"] == ref:
                    start_office = o
        h = name_hub(eit["title"]) if not eit["suppressed"] else None
        if h:
            eit["flags"].append(h)
        if ev.name in EXPAND_ONLY_AS_START and eit["ref"] not in members:   # the subject's own filing is expanded; one it is merely filed in is context
            eit["context_only"] = True
            continue
        if expanded >= LIMITS["expand"]:
            eit["not_expanded"] = True
            continue
        expanded += 1
        through_near = eit["grade"] == "near"
        for it in roles_on(conn, ev, e, allowed, skipped):
            if "omitted" in it:
                out["roles"].append(it)
                continue
            if it["ref"] in members or it["ref"] == ref:
                continue
            if it["kind"] == "person" and subject_person:
                near(it, NEAR_THROUGH_PEOPLE)
            elif through_near:
                near(it, NEAR_THROUGH_NEAR.format(reason=eit["reason"]))
            if it["view"] == "company_addresses":
                h = address_hub(conn, it["row"])
                if h:
                    it["flags"].append(h)
            (out["second"] if it["kind"] == "person" and subject_person else out["roles"]).append(it)
        for it in pointing_at(conn, ev, e, allowed, skipped):
            if "omitted" not in it and through_near:
                near(it, NEAR_THROUGH_NEAR.format(reason=eit["reason"]))
            out["pointing"].append(it)
            # the practitioners a notice names: rows on the notice, with the notice's grade
            if "omitted" not in it and it["view"] in ROLES_ON:
                for pit in roles_on(conn, cat.BY_NAME[it["view"]], it["row"], allowed, skipped):
                    if "omitted" not in pit and it["grade"] == "near":
                        near(pit, it["reason"])
                    out["roles"].append(pit)
        if eit["ref"] != ref and ev.kind == "organisation":
            EL = links_of(conn, [eit["ref"]])
            for l in EL["confirmed"] + EL["near"]:
                if l["other"] in members or l["other"] == ref:
                    continue
                it = link_item(conn, l, cache, allowed, skipped, via=eit["ref"])
                if not it:
                    continue
                if through_near and it["grade"] == "confirmed":
                    near(it, NEAR_THROUGH_NEAR.format(reason=eit["reason"]))
                elif it["grade"] == "confirmed" and l["grade"] == "confirmed":
                    pass
                out["near" if it["grade"] == "near" else "confirmed"].append(it)
            out["links_omitted"] += EL["omitted"]
    if depth < 2:
        out["second"] = []
    # 3b. the reaches a template asks for: an organisation start's officers, the companies at its office, the chain above it
    if sv.kind == "organisation" and "officers" in wanted:
        officers = [it for it in out["roles"] if "omitted" not in it and it["view"] in OFFICER_VIEWS and it["via"] == ref and it["kind"] == "person"]
        out["officers"], out["officers_followed"], out["officers_omitted"] = follow_officers(conn, ref, officers, allowed, skipped, cache)
    if sv.name == "companies" and "office" in wanted and start_office is not None:
        out["office"], out["office_companies"], out["office_listed"] = office_companies(conn, ref, start_office, allowed, skipped)
    if sv.name == "companies" and "chain" in wanted and chain_depth:
        out["chain"], out["chain_stats"] = chain(conn, ref, sr, allowed, skipped, chain_depth)
    # 4. hubs on every person met
    people = [it for k in ("members", "confirmed", "near", "second", "roles", "named", "officers", "chain") for it in out[k]
              if it.get("kind") == "person" and "omitted" not in it and "chain_note" not in it]
    flag_people(conn, people)
    for it in out["chain"] + out["officers"] + out["office"]:
        if "omitted" in it or "chain_note" in it or it["kind"] != "organisation" or it["suppressed"]:
            continue
        h = name_hub(it["title"])
        if h:
            it["flags"].append(h)
    out["hubs"] = [{"ref": it["ref"], "title": it["title"], **f} for k in ("start", ) for it in [out["start"]] for f in it["flags"]] + \
                  [{"ref": it["ref"], "title": it["title"], **f} for k in ("members", "entities", "confirmed", "near", "roles", "second", "named", "officers", "office", "chain")
                   for it in out[k] if "omitted" not in it and "chain_note" not in it for f in it["flags"]]
    out["skipped"] = sorted(set(skipped))
    out["entities_not_expanded"] = sum(1 for e in out["entities"] if e.get("not_expanded"))
    return out
