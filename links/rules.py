"""The rules that judge a pair of rows, exact. Two confirm a link between
two person rows by name (design: "How a link is made"; old rulings 217,
218, 221). Pure functions
over the rows `links.rows` holds. The weights the old estate set by hand
are not here.

1. `full-name@1`: the same first, middle and last name: the full name key
   equal token for token, and a middle name present. Confirmed.
2. `name-and-address@1`: the same first and last name, and the company
   each role sits on has filed the same registered office. Confirmed; but
   an address shared by more than HUB_FLOOR companies (a busy address:
   an accountant's office) counts only when the full name carries a middle
   name. Address alone never confirms.

Three more, ruling 106 (28 October 2026), each from a measured near gap:

3. `organisation-sole-company@1`: a donation row's organisation name and the
   one company on the register under that name key, live in the donation's
   year. Confirmed. Several companies of the name, or the one not live,
   stays near under `organisation-name@1` with the reason saying which.
4. `successor-name@1`: two companies under one name key, one with a year in
   brackets, and a person confirmed on both (a director or shareholder row
   on each, in one group). Related, "succeeded by", earlier registered to
   later: a relation between two entities, never an identity, and the
   groups never follow it. The name alone stays near (`company-name@1`).
5. `candidate-same-party@1`: candidate rows of one name key standing for one
   registered party in different elections are one person. Confirmed; but
   where two rows of the name stand for the party in one election, no pair
   of that name and party confirms, near with the reason.

One more, ruling 107 (28 October 2026), from the gap links-3 measured:

6. `organisation-one-live-company@1`: a donation row's organisation name
   carried by several companies on the register, exactly one of them live
   in the donation's year. Confirmed to that one; the others stay near,
   saying another was live. Where none or more than one was live, every
   pair stays near under `organisation-name@1` and the reason says which.

One more, ruling 109 (28 October 2026), from the Christopher & Banks case:

7. `refiled-name@1`: two companies under one name key, neither with a year
   in brackets, the earlier registered removed and the later registered
   within twelve months of that removal, before or after it, and a person
   confirmed on both (as rule 4). Related, "delisted/refiled same year",
   earlier to later: a relation between two entities, never an identity,
   and the groups never follow it. The name alone, or the name with the
   dates and no shared person, stays near (`company-name@1`).

Everything else that shares a name is near, with the reason. A
politician's row (a candidate, a member, a declared-interests return)
joined to the director register by name is near whatever the name
similarity, until a supporting link holds (design: "Joining a politician
to a company role is stricter"). Organisations with an official number
need none of this: the number is the link (`official-number@1`).
"""
from __future__ import annotations

import datetime as dt
import re

HUB_FLOOR = 50          # ruling 217: an address shared by more than this many companies is busy
RULE_FULL = "full-name@1"
RULE_ADDRESS = "name-and-address@1"
RULE_NUMBER = "official-number@1"
RULE_ORG_NAME = "organisation-name@1"
RULE_NAME_ONLY = "name-only@1"      # the near grade for a shared name that neither rule confirms

NEAR_NO_MIDDLE = "the two rows share a first and last name but no middle name is filed to compare, and no shared address"
NEAR_MIDDLE_DIFFERS = "the two rows share a first and last name but their middle names differ"
NEAR_ONE_MIDDLE = "the two rows share a first and last name; only one files a middle name, and no shared address"
NEAR_BUSY_ADDRESS = "the shared address is a busy one (more than 50 companies) and the name has no middle name"
NEAR_POLITICIAN = "a politician's name on another register needs a supporting link: a shared directorship, a shareholding, or a declared company"
NEAR_ORG_NAME = "a name match to a company; the donation row carries no official number"

# Rules added by links-2 (20 October 2026). Confirmed: a register's own structure joins the rows. Near: the rows name a
# circumstance beside the name, which is evidence a reader can weigh and not a confirmation; whether any of them may
# confirm is Arthur's (docs/decisions/queue/).
RULE_SEAT = "seat-and-window@1"              # a House-published row (an interests return, an expense line) and the seat whose term covers it
RULE_DECLARED = "declared-directorship@1"    # a member's return and a director row of the member's name on a company the member declared
RULE_FILED_NAME = "filed-name@1"             # two donation rows filed under one organisation name (near)
RULE_OWN_RETURN = "own-return@1"             # a donor row on a candidate's own return in the candidate's name (near)
RULE_PARTY_DONOR = "member-and-party-donor@1"   # a politician's name on a donor row to the politician's own party, dated in the term (near)
RULE_COMPANY_NAME = "company-name@1"         # two companies under one name (near): the number is the only confirmation
RULE_NAME_FORM = "candidate-name-form@1"     # one name under two printings across elections, same party (near)
RULE_COUPLED = "coupled-name@1"              # a coupled donor row to each person its filed name names (near; ruling 73)

NEAR_SEAT_AMBIGUOUS = "more than one member of this name sat in the window, and the rows do not say which filed this"
NEAR_DECLARED_TWO = "the declared company has two directors of this name; the rows do not say which is the member"
NEAR_FILED_NAME = "two donation rows filed under one organisation name; neither carries an official number (the filed name is the Commission's donor, ruling 253)"
NEAR_OWN_RETURN = "a donor row on the candidate's own return in the candidate's name; a name on the candidate's own form, not an identifier"
NEAR_PARTY_DONOR = "a politician's name on a donor row to the politician's own party, dated in the term; a name with a circumstance, not a confirmation"
NEAR_COMPANY_SAME = "two companies under one name; only the official number confirms a company"
NEAR_COMPANY_YEAR = "two companies under one name apart from a year in brackets (a successor's name); only the official number confirms a company"
NEAR_NAME_FORM = "one first and last name under two printings in different elections for one party; a printing is a name relationship, not an identity"
# Rules added by links-3 (ruling 106, 28 October 2026), each proposed from a measured near gap with its count and twenty
# pairs read on the board. Pure functions here; build.py reads the facts, calls them, and stores what they return.
RULE_SOLE_COMPANY = "organisation-sole-company@1"   # a donation row's organisation name and the one company of the name, live in its year
RULE_SUCCESSOR = "successor-name@1"                # two companies under one name, one with a year in brackets, a person confirmed on both
RULE_SAME_PARTY = "candidate-same-party@1"         # one candidate name key standing for one party in different elections

NEAR_SAME_ELECTION = ("two candidate rows of this name stand for the party in one election, so the name is two people at least once; "
                      "no pair of its rows confirms")

GRADE_RELATED = "related"           # neither an identity nor a near identity: a relation between two rows, named in `relation`
RELATION_SUCCEEDED_BY = "succeeded by"   # read from the earlier registered company to the later
SHARED_SHOWN = 20                   # shared people listed in a successor's evidence; the count is always whole
# Ruling 109 (28 October 2026): Arthur's words for the relation, exactly; "same year" read as within twelve months, either order
RULE_REFILED = "refiled-name@1"     # two companies under one name, no year in brackets, removed and registered within twelve months, a person on both
RELATION_REFILED = "delisted/refiled same year"   # read from the earlier registered (the one removed) to the later
REFILED_MONTHS = 12
DONATION_REGISTERS = ("party_returns", "candidate_returns", "disclosures")
NEAR_ORG_SEVERAL = NEAR_ORG_NAME + "; several companies carry this name"
NEAR_ORG_NOT_YET = NEAR_ORG_NAME + "; one company carries this name, but it was registered after the donation's year"
NEAR_ORG_GONE = NEAR_ORG_NAME + "; one company carries this name, but it was removed before the donation's year"
NEAR_ORG_ONE = NEAR_ORG_NAME + "; one company carries this name"      # a declared interest (mp_interests), not a donation: unchanged
# Ruling 107 (28 October 2026): several companies of the name, judged by which were live in the donation's year.
RULE_ONE_LIVE = "organisation-one-live-company@1"   # a donation row's organisation name and the one of several companies live in its year
NEAR_ORG_NONE_LIVE = NEAR_ORG_SEVERAL + ", and none of them was live in the donation's year"
NEAR_ORG_MANY_LIVE = NEAR_ORG_SEVERAL + ", and more than one of them was live in the donation's year"
NEAR_ORG_OTHER_LIVE = NEAR_ORG_SEVERAL + "; this one was not live in the donation's year, and the one that was is confirmed"

NEAR_COUPLED = ("the Commission filed this donor as two people on one line; this person is one of the names in it, read from the filed "
                "string, not an identifier; the donor stays one row (ruling 73)")


def same_full_name(a: dict, b: dict) -> bool:
    """Rule 1: the full name key equal, with a middle name on both."""
    return bool(a.get("has_middle") and b.get("has_middle") and a.get("full_key") and a["full_key"] == b["full_key"])


def shared_addresses(a_keys: set, b_keys: set) -> set:
    return set(a_keys or ()) & set(b_keys or ())


def same_name_and_address(a: dict, b: dict, a_keys: set, b_keys: set, hub_sizes: dict) -> tuple:
    """Rule 2 → (confirmed, shared keys used, reason when not confirmed).
    The first and last name equal; a shared address key; a busy key counts
    only with a middle name on the row (then rule 1 would usually hold
    first; here the middle names must not differ)."""
    if not (a.get("fl_key") and a["fl_key"] == b.get("fl_key")):
        return False, set(), "different first or last name"
    if a.get("middle") and b.get("middle") and a["full_key"] != b["full_key"]:
        return False, set(), NEAR_MIDDLE_DIFFERS
    shared = shared_addresses(a_keys, b_keys)
    if not shared:
        return False, set(), None
    quiet = {k for k in shared if int(hub_sizes.get(k, 0)) <= HUB_FLOOR}
    if quiet:
        return True, quiet, None
    if a.get("has_middle") and b.get("has_middle"):
        return True, shared, None
    return False, shared, NEAR_BUSY_ADDRESS


def judge(a: dict, b: dict, a_keys: set = (), b_keys: set = (), hub_sizes: dict = None) -> dict:
    """What the rules say about two person rows that share a first and last
    name: {rule, grade, reason, evidence}. A politician's row is never
    confirmed here."""
    hub_sizes = hub_sizes or {}
    if a.get("politician") or b.get("politician"):
        shared = shared_addresses(a_keys, b_keys)
        return {"rule": RULE_NAME_ONLY, "grade": "near", "reason": NEAR_POLITICIAN,
                "evidence": {"name": a.get("full_key"), "other": b.get("full_key"), "shared_addresses": sorted(shared)[:6]}}
    if same_full_name(a, b):
        return {"rule": RULE_FULL, "grade": "confirmed", "reason": None,
                "evidence": {"full_name": a["full_key"], "middle": a.get("middle"), "as_filed": [a.get("name_filed"), b.get("name_filed")]}}
    ok, shared, reason = same_name_and_address(a, b, a_keys, b_keys, hub_sizes)
    if ok:
        return {"rule": RULE_ADDRESS, "grade": "confirmed", "reason": None,
                "evidence": {"first_last": a["fl_key"], "shared_addresses": sorted(shared)[:6],
                             "busiest": max(int(hub_sizes.get(k, 1)) for k in shared), "as_filed": [a.get("name_filed"), b.get("name_filed")]}}
    if reason is None:
        if a.get("has_middle") and b.get("has_middle"):
            reason = NEAR_MIDDLE_DIFFERS
        elif a.get("has_middle") or b.get("has_middle"):
            reason = NEAR_ONE_MIDDLE
        else:
            reason = NEAR_NO_MIDDLE
    return {"rule": RULE_NAME_ONLY, "grade": "near", "reason": reason,
            "evidence": {"first_last": a.get("fl_key"), "as_filed": [a.get("name_filed"), b.get("name_filed")],
                         "shared_addresses": sorted(shared)[:6] if shared else []}}


def _d(x):
    if x is None or isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x)[:10])


def _year(row: dict) -> tuple:
    """A donation row's year as (start, end): `started_on` .. `ended_on` as the
    row files them; a dated declaration is a year of one day."""
    start = _d(row.get("started_on"))
    return start, _d(row.get("ended_on")) or start


def _live(c: dict, start, end) -> tuple:
    """(registered by the year's end, not removed before its start); an unknown date does not count against."""
    reg, rem = _d(c.get("registered_on")), _d(c.get("removed_on"))
    return ((reg is None or end is None or reg <= end), (rem is None or start is None or rem >= start))


def sole_company(row: dict, companies: list) -> list:
    """`organisation-sole-company@1` (ruling 106 (1)): a donation row's
    organisation name and the companies on the register under that name key
    (every one, live or not). Confirmed when exactly one company carries the
    name and it was live in the donation's year: registered on or before the
    year's end and not removed before its start (`started_on` .. `ended_on`
    as the row files them; a dated declaration is a year of one day).
    Otherwise near under `organisation-name@1`, the reason saying which:
    the one registered after, or removed before. Several companies of the
    name are judged by `one_live_company` (ruling 107).
    `companies`: [{entity_ref, number, name, registered_on, removed_on}]."""
    if len(companies) > 1:
        return one_live_company(row, companies)
    start, end = _year(row)
    out = []
    for c in companies:
        registered_in_time, not_removed = _live(c, start, end)
        ev = {"name": row.get("name_filed"), "organisation_key": row.get("name_key"), "date": str(start) if start else None,
              "year": [str(start) if start else None, str(end) if end else None], "company": c.get("name"),
              "company_number": c.get("number"), "registered_on": str(_d(c["registered_on"])) if c.get("registered_on") else None,
              "removed_on": str(_d(c["removed_on"])) if c.get("removed_on") else None,
              "alive_on_date": registered_in_time and not_removed, "companies_of_that_name": len(companies)}
        if registered_in_time and not_removed:
            out.append({"entity_ref": c["entity_ref"], "rule": RULE_SOLE_COMPANY, "grade": "confirmed", "reason": None, "evidence": ev})
            continue
        reason = NEAR_ORG_NOT_YET if not registered_in_time else NEAR_ORG_GONE
        out.append({"entity_ref": c["entity_ref"], "rule": RULE_ORG_NAME, "grade": "near", "reason": reason, "evidence": ev})
    return out


def one_live_company(row: dict, companies: list) -> list:
    """`organisation-one-live-company@1` (ruling 107): a donation row's
    organisation name carried by several companies on the register. Each
    company is live in the donation's year as `sole_company` reads it
    (registered by the year's end, not removed before its start). Exactly
    one live: that pair is confirmed, and each other company's pair stays
    near under `organisation-name@1` saying another was live. None, or more
    than one: every pair stays near, the reason saying which. The evidence
    on every pair names the companies considered (number, name, registered
    and removed dates, live or not), the one live in the year when there is
    one, and the donation's date and year.
    `companies`: [{entity_ref, number, name, registered_on, removed_on}]."""
    start, end = _year(row)
    considered = []
    for c in sorted(companies, key=lambda c: c["entity_ref"]):
        considered.append({"entity_ref": c["entity_ref"], "company_number": c.get("number"), "company": c.get("name"),
                           "registered_on": str(_d(c["registered_on"])) if c.get("registered_on") else None,
                           "removed_on": str(_d(c["removed_on"])) if c.get("removed_on") else None,
                           "live_in_year": all(_live(c, start, end))})
    live = [x for x in considered if x["live_in_year"]]
    the_one = live[0] if len(live) == 1 else None
    out = []
    for x in considered:
        ev = {"name": row.get("name_filed"), "organisation_key": row.get("name_key"), "date": str(start) if start else None,
              "year": [str(start) if start else None, str(end) if end else None], "company": x["company"],
              "company_number": x["company_number"], "registered_on": x["registered_on"], "removed_on": x["removed_on"],
              "alive_on_date": x["live_in_year"], "companies_of_that_name": len(considered),
              "companies_alive_on_date": len(live), "companies_considered": considered,
              "live_in_year": the_one["company_number"] if the_one else None}
        if the_one is x:
            out.append({"entity_ref": x["entity_ref"], "rule": RULE_ONE_LIVE, "grade": "confirmed", "reason": None, "evidence": ev})
            continue
        reason = NEAR_ORG_OTHER_LIVE if the_one else (NEAR_ORG_NONE_LIVE if not live else NEAR_ORG_MANY_LIVE)
        out.append({"entity_ref": x["entity_ref"], "rule": RULE_ORG_NAME, "grade": "near", "reason": reason, "evidence": ev})
    return out


_YEAR = re.compile(r"\s*\(\d{4}\)\s*")


def bare_name(org_key: str) -> str:
    """An organisation key with any year in brackets taken out, as the build's
    `company-name@1` step does it in SQL: 'speirs foods (2018) lp' → 'speirs foods lp'."""
    return _YEAR.sub(" ", org_key or "").strip()


def successor(a: dict, b: dict, shared: list) -> dict | None:
    """`successor-name@1` (ruling 106 (2)): a relation, never an identity.
    Two companies under one name key where exactly one carries a year in
    brackets, and at least one person confirmed on both: a director or
    shareholder row on each, the two rows in one confirmed group (a group
    is made by confirmed links, so a confirmed link between them is one).
    Related, `relation` "succeeded by", read from the earlier registered
    company to the later; the shared people's row keys are the evidence.
    None when the names do not fit or no person is shared: the name pattern
    alone stays near (`company-name@1`). The groups never follow it.
    `a`, `b`: {entity_ref, org_key, name, registered_on, removed_on};
    `shared`: [{"a": row on a, "b": row on b, "group": group id, "name": as filed on a}]."""
    ka, kb = a.get("org_key") or "", b.get("org_key") or ""
    if (ka == bare_name(ka)) == (kb == bare_name(kb)) or bare_name(ka) != bare_name(kb) or not bare_name(ka):
        return None
    if not shared:
        return None
    ra, rb = _d(a.get("registered_on")), _d(b.get("registered_on"))
    known = ra is not None and rb is not None and ra != rb
    first, then = (a, b) if (ra or dt.date.max, a["entity_ref"]) <= (rb or dt.date.max, b["entity_ref"]) else (b, a)
    flip = first is b
    people = [{"earlier": x["b" if flip else "a"], "later": x["a" if flip else "b"], "group": x.get("group"), "name": x.get("name")}
              for x in sorted(shared, key=lambda x: (x.get("group") or "", x["a"], x["b"]))]
    return {"rule": RULE_SUCCESSOR, "grade": GRADE_RELATED, "relation": RELATION_SUCCEEDED_BY, "reason": None,
            "evidence": {"earlier": first["entity_ref"], "later": then["entity_ref"], "relation": RELATION_SUCCEEDED_BY,
                         "names": [first.get("name") or first.get("org_key"), then.get("name") or then.get("org_key")],
                         "name_key": bare_name(ka),
                         "registered": [str(_d(first.get("registered_on")) or "") or None, str(_d(then.get("registered_on")) or "") or None],
                         "removed": [str(_d(first.get("removed_on")) or "") or None, str(_d(then.get("removed_on")) or "") or None],
                         "order": "by registration date" if known else "registration dates equal or missing: by key",
                         "shared_people": len({p["group"] for p in people}), "shared_rows": people[:SHARED_SHOWN],
                         "registers": ["companies", "companies"]}}


def _months_after(d: dt.date, months: int) -> dt.date:
    """`d` moved by whole calendar months, the day held to the month's last (29 February plus twelve months is 28 February)."""
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    last = (dt.date(y + m // 12, m % 12 + 1, 1) - dt.timedelta(days=1)).day
    return dt.date(y, m, min(d.day, last))


def within_months(removed, registered, months: int = REFILED_MONTHS) -> bool:
    """True when `registered` falls within `months` calendar months of `removed`, before or after it; False when either is unknown."""
    removed, registered = _d(removed), _d(registered)
    if removed is None or registered is None:
        return False
    return _months_after(removed, -months) <= registered <= _months_after(removed, months)


def refiled(a: dict, b: dict, shared: list) -> dict | None:
    """`refiled-name@1` (ruling 109): a relation, never an identity. Two
    companies under one name key where neither carries a year in brackets;
    the earlier registered was removed, and the later was registered within
    twelve calendar months of that removal, before or after it ("same year",
    either order); and at least one person confirmed on both, as
    `successor` reads it. Related, `relation` "delisted/refiled same year"
    (Arthur's words), read from the earlier registered company to the later.
    Equal registration dates put the removed one first. The evidence is
    `successor`'s, with the removal date, the refiling's registration date
    and the gap in days (negative where the new company was registered
    before the old was removed). None when the names, the dates or the
    people do not fit: the name alone stays near (`company-name@1`).
    `a`, `b`, `shared` as `successor` takes them."""
    ka, kb = a.get("org_key") or "", b.get("org_key") or ""
    if ka != kb or not ka or ka != bare_name(ka):
        return None
    if not shared:
        return None
    first, then = sorted((a, b), key=lambda c: (_d(c.get("registered_on")) or dt.date.max, c.get("removed_on") is None, c["entity_ref"]))
    removed, registered = _d(first.get("removed_on")), _d(then.get("registered_on"))
    if not within_months(removed, registered):
        return None
    ra, rb = _d(first.get("registered_on")), _d(then.get("registered_on"))
    flip = first is b
    people = [{"earlier": x["b" if flip else "a"], "later": x["a" if flip else "b"], "group": x.get("group"), "name": x.get("name")}
              for x in sorted(shared, key=lambda x: (x.get("group") or "", x["a"], x["b"]))]
    return {"rule": RULE_REFILED, "grade": GRADE_RELATED, "relation": RELATION_REFILED, "reason": None,
            "evidence": {"earlier": first["entity_ref"], "later": then["entity_ref"], "relation": RELATION_REFILED,
                         "names": [first.get("name") or first.get("org_key"), then.get("name") or then.get("org_key")],
                         "name_key": ka,
                         "registered": [str(ra) if ra else None, str(rb) if rb else None],
                         "removed": [str(removed), str(_d(then.get("removed_on")) or "") or None],
                         "removed_on": str(removed), "refiled_on": str(registered), "gap_days": (registered - removed).days,
                         "order": "by registration date" if ra is not None and ra != rb else "registration dates equal or missing: the removed one first",
                         "shared_people": len({p["group"] for p in people}), "shared_rows": people[:SHARED_SHOWN],
                         "registers": ["companies", "companies"]}}


def same_party_candidates(rows: list) -> list:
    """`candidate-same-party@1` (ruling 106 (3)): the candidate rows of one
    name key standing for one registered party, `rows`: [{ref, election,
    electorate, list_place, name_filed, party}]. One person: a star of
    confirmed pairs from the smallest ref, each pair in different elections,
    the evidence the party, the two elections, the seats and the printings.
    Where two of the rows stand in one election, the name is two people
    there, and no pair confirms: every pair of the star is near with the
    reason and the elections that carry two. Returns [(ref, ref, judgment)]."""
    rows = sorted(rows, key=lambda r: r["ref"])
    if len(rows) < 2:
        return []
    by_election: dict = {}
    for r in rows:
        by_election.setdefault(r.get("election"), []).append(r["ref"])
    twice = sorted(e for e, refs in by_election.items() if len(refs) > 1)
    if not twice and len(by_election) < 2:
        return []
    head, out = rows[0], []
    for r in rows[1:]:
        ev = {"party": head.get("party"), "elections": [head.get("election"), r.get("election")],
              "seats": [_seat(head), _seat(r)], "as_filed": [head.get("name_filed"), r.get("name_filed")],
              "name_key": head.get("name_key"), "registers": ["house", "house"]}
        if twice:
            ev["elections_with_two_of_this_name"] = twice
            out.append((head["ref"], r["ref"], {"rule": RULE_SAME_PARTY, "grade": "near", "reason": NEAR_SAME_ELECTION, "evidence": ev}))
        else:
            out.append((head["ref"], r["ref"], {"rule": RULE_SAME_PARTY, "grade": "confirmed", "reason": None, "evidence": ev}))
    return out


def _seat(r: dict) -> str:
    """A candidacy's seat as the House prints it: the electorate, the list place, or both."""
    bits = [r["electorate"]] if r.get("electorate") else []
    if r.get("list_place") is not None:
        bits.append(f"list {r['list_place']}")
    return ", ".join(bits) or "no seat printed"
