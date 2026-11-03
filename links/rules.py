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

One more, ruling 114 (28 October 2026), the organisation rules widened:

8. `organisation-sole-company@2` and `organisation-one-live-company@2`: rules
   3 and 6 with the name looked up on the companies, societies, limited
   partnerships and charities registers together, a body on two of them
   counted once, each body live by its own register's dates
   (`sole_body`). @1 is kept as it was and no longer built (`RETIRED`).

One more, ruling 116 (28 October 2026), of the seat-and-window kind:

9. `member-on-the-day@1`: a speech turn's speaker, a written question's
   asker and its answering minister, a Beehive release's tagged minister
   and a diary release's minister, each as printed with its titles off
   (`links.rows.MEMBER_TITLES`), and the one member row (`pub.members`)
   of the same first and last name sitting in the House on the row's day
   (from its from date, up to but not including its end: one term's end is
   the next term's start). Confirmed. Two or more members of the name
   sitting on the day, or none (a member of the name sat at another time),
   stays near, the reason saying which; a name no member carries, or a day
   before the first term the members view holds, makes no link (the view
   could not have seen it). Middle names that differ on both rows take the
   member out. Parliament's member id rides in the evidence, never decides.

One more, ruling 125 (30 October 2026), the organisation rules on every row:

10. `organisation-sole-company@3` and `organisation-one-live-company@3`: rule
   8 run on every organisation-named row of every people view the lane
   reads (a shareholder, a director, a declared interest, a charity or
   society officer, a Gazette row, a local election return, and the donor
   and disclosure rows as before), "live" judged on the row's own date and
   never today: a body registered on or before that date and not removed
   before it counts; one removed before it or registered after it does
   not. The date is the row's own (`started_on` .. `ended_on`: the
   donation's return period, the interests return's date, the officer's
   appointment, the shareholding's filing). A row with no date of its own
   stays near, the reason "undated" (`body_on_date`). @2 is kept as it was
   and no longer built (`RETIRED`).

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

# Ruling 114 (28 October 2026): the donor's organisation name looked up on four registers together, not the companies register
# alone. A changed test is a new version: @1 stays what it meant (`sole_company`, `one_live_company`, the companies alone) and a
# stored @1 link still reads as that; the build makes @2 (`sole_body`). The near grade stays `organisation-name@1`.
RULE_SOLE_BODY = "organisation-sole-company@2"      # one body of the name across the four registers, live in the donation's year
RULE_ONE_LIVE_BODY = "organisation-one-live-company@2"   # several bodies of the name, exactly one live in the donation's year
RULE_MEMBER_DAY = "member-on-the-day@1"           # a member's printed name and the one member of the name sitting on the row's day
NEAR_DAY_TWO = "two or more members of this name sat in the House on the row's day, and the row does not say which"
NEAR_DAY_NONE = ("a member of this name sat in the House, but not on the row's day; the members view holds every member an election "
                 "returned and the by-election winners, not a list member who filled a vacancy")
#: what a member-on-the-day row came to, for the counts
DAY_ONE, DAY_TWO, DAY_NONE, DAY_NO_MEMBER, DAY_BEFORE, DAY_UNDATED = (
    "one member sitting", "two or more members sitting", "no member of the name sitting on the day", "no member of the name",
    "before the members view's first term", "no day")
RETIRED = {RULE_SOLE_COMPANY, RULE_ONE_LIVE,         # built no longer (ruling 114); kept so a stored link of the version reads as it meant
           RULE_SOLE_BODY, RULE_ONE_LIVE_BODY}        # built no longer (ruling 125): @3 judges every organisation-named row on its own date
#: a body is read from four registers (`links.rows.BODY_SQL`); a Companies Office row's own register (`pub.companies.register`) is its kind
FORMATION_REGISTERS = ("companies", "societies", "limited_partnerships")   # the registers a body is formed on; a charity's is its status
REGISTER_WORDS = {"companies": "companies", "other_incorporated": "other incorporated bodies", "charitable_trust_board": "charitable trust boards",
                  "public_sector": "public sector bodies", "retirement_village": "retirement villages", "societies": "incorporated societies",
                  "limited_partnerships": "limited partnerships", "charities": "charities"}
#: The near tails, one per outcome, worded for the row's date: a donation row's is its year ("in the donation's year", as
#: ruling 114 wrote them); any other row's is its own date ("on the row's date", ruling 125). `{live}` and `{date}` are the
#: two phrasings; the @2 constants below are the templates filled for a donation row, byte for byte as ruling 114 stored them.
BODY_TAILS = {
    "not_yet": "one body carries this name, but it was registered after {date}",
    "gone": "one body carries this name, but it was removed before {date}",
    "undated_body": "one body carries this name, and its register says it was removed but publishes no date, so whether it was live "
                    "{live} is not known",
    "none_live": "several bodies carry this name, and none of them was live {live}",
    "many_live": "several bodies carry this name, and more than one of them was live {live}",
    "other_live": "several bodies carry this name; this one was not live {live}, and the one that was is confirmed",
    "undated_several": "several bodies carry this name, and a register says one was removed but publishes no date, so which was "
                       "live {live} is not known",
}
WHEN_DONATION = {"live": "in the donation's year", "date": "the donation's year", "row": "donation row"}
WHEN_ROW = {"live": "on the row's date", "date": "the row's date", "row": "row"}
NEAR_BODY_NOT_YET = BODY_TAILS["not_yet"].format(**WHEN_DONATION)
NEAR_BODY_GONE = BODY_TAILS["gone"].format(**WHEN_DONATION)
NEAR_BODY_UNDATED = BODY_TAILS["undated_body"].format(**WHEN_DONATION)
NEAR_BODY_NONE_LIVE = BODY_TAILS["none_live"].format(**WHEN_DONATION)
NEAR_BODY_MANY_LIVE = BODY_TAILS["many_live"].format(**WHEN_DONATION)
NEAR_BODY_OTHER_LIVE = BODY_TAILS["other_live"].format(**WHEN_DONATION)
NEAR_BODY_UNDATED_SEVERAL = BODY_TAILS["undated_several"].format(**WHEN_DONATION)
# Ruling 125 (30 October 2026): the two rules on every organisation-named row, judged on the row's own date. A changed test is a
# new version: @2 stays what it meant (`sole_body`: the donation rows, a row with no date not counting against) and a stored @2
# link still reads as that; the build makes @3 (`body_on_date`). The near grade stays `organisation-name@1`.
RULE_SOLE_BODY_DATED = "organisation-sole-company@3"      # one body of the name across the four registers, live on the row's own date
RULE_ONE_LIVE_BODY_DATED = "organisation-one-live-company@3"   # several bodies of the name, exactly one live on the row's own date
NEAR_BODY_UNDATED_ROW = "undated: the row carries no date of its own, so whether a body of the name was live on it is not judged"
#: 3 November 2026: a name never outweighs a number (links.build.number_over_name)
NEAR_NUMBER_ELSEWHERE = ("the row prints the official number of another body, which `official-number@1` confirms; a name match "
                         "never outweighs a number")
#: what a row's date is, by view, for the evidence (ruling 125's words); a view not named here is "the row's date"
VIEW_DATE = {"party_return_donors": "the return's year", "candidate_return_donors": "the return's year",
             "disclosures": "the day the donation was given, else received", "disclosure_items": "the contribution's first date",
             "promoter_people": "the return's year", "mp_interests": "the interests return's date",
             "directors": "the appointment", "shareholders": "the shareholding's filing (not published today)",
             "society_officers": "the appointment", "charity_officers": "the appointment", "limited_partnership_partners": "the appointment",
             "gazette_prohibitions": "the prohibition's start", "gazette_appointments": "the appointment's start",
             "gazette_liquidators": "the notice's date", "gazette_bankruptcies": "the event's date", "gazette_celebrants": "the period's start",
             "gazette_practitioners": "the notice's date", "local_election_returns": "the election year",
             "building_practitioner_decisions": "the decision's date", "party_board_roles": "the capture",
             "gazette_liquidations": "the notice's date", "insolvency_companies": "the liquidation's date",
             "company_insolvencies": "the insolvency's start, or the appointment", "retirement_villages": "the supervisor's appointment",
             "grant_recipients": "the first and last periods granted", "company_lookup_roles": "the appointment",
             "company_lookup_holdings": "the holding's start", "insolvency_people": "the adjudication",
             "rea_parties": "the decision's date", "building_practitioners": "the licence's first grant",
             "council_meeting_attendance": "the meeting's date", "council_meeting_declarations": "the meeting's date",
             "minister_diary_attendees": "the diary entry's date"}


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


def body_dates(rows: list) -> dict:
    """A body's registered and removed dates from its register rows (ruling
    114): the rows of the registers it is formed on (companies, societies,
    limited partnerships) where it has any, else its charities rows; a
    charity's deregistration ends its charitable status, not a company or a
    society. Registered: the earliest. Removed where any of the formation
    rows says so (a removal date, or `removal_undated`: the status says
    removed and no date is published), on the latest date published. A
    body's charities rows, where they decide, are its registrations in turn
    (one NZBN, deregistered and registered again under a new charity
    number): removed only where the last registered says so (the latest
    `registered_on`, none counting earliest, then the largest `entity_ref`
    by bytes). The same in SQL: `body_dates_sql`."""
    used = [r for r in rows if r.get("register") in FORMATION_REGISTERS]
    if used:
        decide = used
    else:
        used = list(rows)
        decide = [max(used, key=lambda r: (_d(r.get("registered_on")) or dt.date.min, r["entity_ref"]))] if used else []
    regs = [d for d in (_d(r.get("registered_on")) for r in used) if d]
    gone = [r for r in decide if r.get("removed_on") or r.get("removal_undated")]
    dated = [d for d in (_d(r.get("removed_on")) for r in gone) if d]
    return {"registered_on": min(regs) if regs else None, "removed": bool(gone), "removed_on": max(dated) if dated else None,
            "removal_undated": bool(gone) and not dated}


def body_dates_sql(s: str) -> str:
    """`body_dates` as two CTEs over `<s>.bodies` for the bodies a CTE `k`
    names (`k.body`): `x` (each row, `formed`, `last_registered`) and `bd`
    (`body`, `reg`, `removed`, `removed_on`), for the check and measurement
    12, which judge every body apart from the build."""
    return f"""x AS (SELECT b.*, bool_or(b.register <> 'charities') OVER (PARTITION BY b.body) AS formed,
                     row_number() OVER (PARTITION BY b.body ORDER BY b.registered_on DESC NULLS LAST, b.entity_ref COLLATE "C" DESC) = 1
                       AS last_registered
              FROM {s}.bodies b WHERE b.body IN (SELECT body FROM k)),
        bd AS (SELECT body, min(registered_on) AS reg,
                      coalesce(bool_or(removed_on IS NOT NULL OR removal_undated) FILTER (WHERE formed OR last_registered), false) AS removed,
                      max(removed_on) FILTER (WHERE formed OR last_registered) AS removed_on
               FROM x WHERE register <> 'charities' OR NOT formed GROUP BY body)"""


def body_live(dates: dict, start, end):
    """True or False as `_live` reads a company (registered by the year's end,
    not removed before its start, an unknown date not counting against); None
    where the body was removed on a date no register publishes: not known."""
    reg = dates["registered_on"]
    if not (reg is None or end is None or reg <= end):
        return False
    if not dates["removed"]:
        return True
    if dates["removed_on"] is None:
        return None
    return start is None or dates["removed_on"] >= start


def _register_word(r: dict, regs: set) -> str:
    """A body row's register in words: a Companies Office row by its own register, the twin of a society or a
    limited partnership by that register's name."""
    k = (r.get("kind") or r["register"]) if r["register"] == "companies" else r["register"]
    if k == "other_incorporated":
        k = next((x for x in ("societies", "limited_partnerships") if x in regs), k)
    return REGISTER_WORDS.get(k, k)


def registers_named(bodies: list) -> list:
    """The registers whose rows carry the name, in words, each once, in REGISTER_WORDS' order."""
    order = list(REGISTER_WORDS.values())
    words = set()
    for b in bodies:
        regs = {r["register"] for r in b["rows"]}
        words |= {_register_word(r, regs) for r in b["rows"] if r.get("named")}
    return sorted(words, key=lambda w: (order.index(w) if w in order else len(order), w))


def body_reason(words: list, tail: str, when: dict = WHEN_DONATION) -> str:
    """The near reason of ruling 114, naming the registers that hold the name; `when` words the row (a donation row, or any row)."""
    regs = words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]
    return f"a name match on the {regs} register{'s' if len(words) > 1 else ''}; the {when['row']} carries no official number; {tail}"


def sole_body(row: dict, bodies: list) -> list:
    """`organisation-sole-company@2` and `organisation-one-live-company@2`
    (ruling 114): a donation row's organisation name looked up on the
    companies, societies, limited partnerships and charities registers
    together. A body on two registers as one thing (a society, a limited
    partnership or a charity whose register carries a Companies Office
    body's NZBN, or its company number) is one body, counted once, its
    `entity_ref` the Companies Office row where it has one. Each body is live
    in the donation's year by `body_dates` and `body_live`. Exactly one body
    of the name, live: confirmed, `organisation-sole-company@2`. Several,
    exactly one live and none whose removal is undated: that one confirmed,
    `organisation-one-live-company@2`, the others near saying another was
    live. Otherwise every pair near under `organisation-name@1`, the reason
    naming the registers that hold the name and saying which. The evidence
    keeps @1's keys (company, company_number, companies_of_that_name, …,
    "company" read as the body) and adds the body's `register`, its rows on
    every register (`registers`) and `registers_holding_the_name`.
    `bodies`: [{"body": entity_ref, "rows": [{entity_ref, register, kind,
    number, name, registered_on, removed_on, removal_undated, named}]}].
    Kept as ruling 114 built it (RETIRED): an undated row does not count
    against a body. The build makes @3, `body_on_date`."""
    return _judge_bodies(row, bodies, 2)


def body_on_date(row: dict, bodies: list) -> list:
    """`organisation-sole-company@3` and `organisation-one-live-company@3`
    (ruling 125): `sole_body` on every organisation-named row of every
    people view, "live" judged on the row's own date and never today. The
    row's date is `started_on` .. `ended_on` as the view files it (the
    donation's return period; the interests return's date; the officer's
    appointment; a shareholding's filing, which `pub.shareholders` does not
    publish today): a body registered on or before the window's end and not
    removed before its start was live. A row with no `started_on` is undated:
    every pair stays near with the reason "undated" (`NEAR_BODY_UNDATED_ROW`),
    whatever the bodies' dates. The grades and the reasons are @2's, worded
    for the row ("on the row's date"; a donation row keeps "in the donation's
    year"); the evidence adds `dated`, `date_is` (what the view's date is,
    `VIEW_DATE`), `row_view`, `row_register` and `outcome` (sole, one_live,
    undated_row, or the near tail's name in `BODY_TAILS`).
    `row`: {ref, register, view, name_filed, name_key, started_on, ended_on}."""
    return _judge_bodies(row, bodies, 3)


def _judge_bodies(row: dict, bodies: list, version: int) -> list:
    start, end = _year(row)
    donation = version == 2 or row.get("register") in DONATION_REGISTERS
    when = WHEN_DONATION if donation else WHEN_ROW
    sole_rule, one_rule = (RULE_SOLE_BODY, RULE_ONE_LIVE_BODY) if version == 2 else (RULE_SOLE_BODY_DATED, RULE_ONE_LIVE_BODY_DATED)
    undated_row = version == 3 and start is None
    words = registers_named(bodies)
    considered = []
    for b in sorted(bodies, key=lambda b: b["body"]):
        regs = {r["register"] for r in b["rows"]}
        head = next((r for r in b["rows"] if r["entity_ref"] == b["body"]), b["rows"][0])
        named = next((r for r in sorted(b["rows"], key=lambda r: r["entity_ref"] != b["body"]) if r.get("named")), head)
        dates = body_dates(b["rows"])
        considered.append({
            "entity_ref": b["body"], "company_number": head.get("number"), "company": named.get("name") or head.get("name"),
            "register": _register_word(head, regs),
            "registered_on": str(dates["registered_on"]) if dates["registered_on"] else None,
            "removed_on": str(dates["removed_on"]) if dates["removed_on"] else None, "removal_undated": dates["removal_undated"],
            "live_in_year": None if undated_row else body_live(dates, start, end), "_registered": dates["registered_on"],
            "registers": [{"register": _register_word(r, set()), "entity_ref": r["entity_ref"], "number": r.get("number"), "name": r.get("name"),
                           "registered_on": str(_d(r["registered_on"])) if r.get("registered_on") else None,
                           "removed_on": str(_d(r["removed_on"])) if r.get("removed_on") else None,
                           "carries_the_name": bool(r.get("named"))} for r in sorted(b["rows"], key=lambda r: r["entity_ref"])]})
    live = [x for x in considered if x["live_in_year"] is True]
    unknown = [x for x in considered if x["live_in_year"] is None]
    the_one = live[0] if len(live) == 1 and not unknown else None
    several = len(considered) > 1
    summary = [{k: x[k] for k in ("entity_ref", "company_number", "company", "register", "registered_on", "removed_on", "live_in_year")}
               for x in considered]
    out = []
    for x in considered:
        ev = {"name": row.get("name_filed"), "organisation_key": row.get("name_key"), "date": str(start) if start else None,
              "year": [str(start) if start else None, str(end) if end else None], "company": x["company"],
              "company_number": x["company_number"], "registered_on": x["registered_on"], "removed_on": x["removed_on"],
              "alive_on_date": x["live_in_year"], "companies_of_that_name": len(considered), "register": x["register"],
              "registers": x["registers"], "registers_holding_the_name": words}
        if version == 3:
            ev.update(dated=not undated_row, date_is=VIEW_DATE.get(row.get("view"), "the row's date"),
                      row_view=row.get("view"), row_register=row.get("register"))
        if several:
            ev.update(companies_alive_on_date=len(live), companies_considered=summary,
                      live_in_year=the_one["company_number"] if the_one else None)
        if the_one is x:
            if version == 3:
                ev["outcome"] = "one_live" if several else "sole"
            out.append({"entity_ref": x["entity_ref"], "rule": one_rule if several else sole_rule, "grade": "confirmed",
                        "reason": None, "evidence": ev})
            continue
        if undated_row:
            outcome, tail = "undated_row", NEAR_BODY_UNDATED_ROW
        elif not several:
            reg = x["_registered"]
            outcome = ("undated_body" if x["live_in_year"] is None
                       else "not_yet" if reg is not None and end is not None and reg > end else "gone")
        else:
            outcome = ("other_live" if the_one else "undated_several" if unknown and len(live) <= 1
                       else "many_live" if len(live) > 1 else "none_live")
        if not undated_row:
            tail = BODY_TAILS[outcome].format(**when)
        if version == 3:
            ev["outcome"] = outcome
        out.append({"entity_ref": x["entity_ref"], "rule": RULE_ORG_NAME, "grade": "near", "reason": body_reason(words, tail, when), "evidence": ev})
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


def sitting(member: dict, day) -> bool:
    """A member sits from `from_on` up to, not on, `to_on` (None while
    sitting): the term an election ends is followed by the one it begins on
    the same polling day, so one person's two terms never both cover a day."""
    return member["from_on"] <= day and (member["to_on"] is None or day < member["to_on"])


def member_on_the_day(row: dict, members: list, held_from) -> tuple:
    """`member-on-the-day@1` (ruling 116). `row`: ref, fl_key, full_key,
    has_middle, day, and its evidence so far (`evidence`); `members`: every
    member row of the row's first and last name (ref, key, election,
    full_key, has_middle, from_on, to_on); `held_from`: the first day of the
    first term the members view holds. Returns (what it came to, [(member
    ref, {rule, grade, reason, evidence})])."""
    day = row.get("day")
    if day is None:
        return DAY_UNDATED, []
    if held_from is None or day < held_from:
        return DAY_BEFORE, []
    named = [m for m in members if m["fl_key"] == row["fl_key"]
             and not (m.get("has_middle") and row.get("has_middle") and m["full_key"] != row["full_key"])]
    if not named:
        return DAY_NO_MEMBER, []
    on = [m for m in named if sitting(m, day)]
    out = []
    for m in (on or named):
        ev = dict(row.get("evidence") or {}, day=day, member=m["key"], election=m.get("election"), term=[m["from_on"], m["to_on"]],
                  members_of_the_name=len(named), members_sitting=len(on), sitting=[x["key"] for x in on])
        if len(on) == 1:
            out.append((m["ref"], {"rule": RULE_MEMBER_DAY, "grade": "confirmed", "reason": None, "evidence": ev}))
        else:
            out.append((m["ref"], {"rule": RULE_MEMBER_DAY, "grade": "near", "reason": NEAR_DAY_TWO if on else NEAR_DAY_NONE, "evidence": ev}))
    return (DAY_ONE if len(on) == 1 else DAY_TWO if on else DAY_NONE), out


# Ruling 1 (Arthur, 3 November 2026): a court party confirmed to the company whose NZBN or company number its judgment
# prints, `official-number@1`'s kind of join. The number alone names the document, not a party: it is tied to a party by the
# party's name, the body-named row of the document whose name key is a name key of the body the number names.
RULE_JUDGMENT_NUMBER = "judgment-number@1"
JUDGMENT_NUMBER_VIEWS = ("court_judgment_parties", "court_people")
NEAR_JN_OTHER_NAME = ("the document prints this body's number and names one body as a party, under a name the body's registers "
                      "do not carry (a trading or former name, or another body)")
NEAR_JN_TWO_BODIES = "two numbers the document prints name two bodies that carry this party's name, so the number does not say which"
#: what a document's printed number came to, for the counts
JN_CONFIRMED, JN_OTHER_NAME, JN_TWO, JN_UNTIED = ("a party of the body's name", "one body party, under another name",
                                                  "two bodies of the party's name", "no party tied to the number")


def _jn_evidence(c: dict, doc: str, bodies: int, matches: bool) -> dict:
    return {"number": "NZBN" if c["kind"] == "nzbn" else "company number", "value": c["value"], "document": doc, "page": c.get("page"),
            "company": c["company"], "as_filed": c["name_filed"], "row_view": c["view"], "name_matches": matches,
            "bodies_named_in_document": bodies}


def judgment_numbers(candidates: list) -> tuple:
    """`judgment-number@1`. `candidates`: one dict per (printed number, body-named row of the same document) where the number
    names exactly one body: document, kind ('nzbn' or 'company_number'), value, page, body, company (the body's name), ref,
    view, name_key, name_filed, name_matches (the row's name key is one of the body's). Per document:
      a row whose name matches exactly one body the document's numbers name: confirmed to that body;
      a row whose name matches two or more of them: near to each (NEAR_JN_TWO_BODIES);
      no row matching any, the numbers naming one body, and the document's judgment parties naming one body (one name key):
      near between each such row and the body (NEAR_JN_OTHER_NAME);
      anything else ties the number to no party and makes no link.
    Returns ({outcome: printed numbers}, [(ref, body, {rule, grade, reason, evidence})]); each printed number is counted
    once, by the best it came to (JN_CONFIRMED, JN_TWO, JN_OTHER_NAME, JN_UNTIED)."""
    by_doc: dict = {}
    for c in candidates:
        by_doc.setdefault(c["document"], []).append(c)
    counts, out = {}, []
    for doc in sorted(by_doc):
        cs = by_doc[doc]
        bodies = {c["body"] for c in cs}
        came: dict = {}                      # (kind, value) -> outcome
        for ref in sorted({c["ref"] for c in cs}):
            hits = sorted((c for c in cs if c["ref"] == ref and c["name_matches"]), key=lambda x: (x["kind"], x["value"]))
            matched = sorted({c["body"] for c in hits})
            for b in matched:
                c = next(x for x in hits if x["body"] == b)
                one = len(matched) == 1
                out.append((ref, b, {"rule": RULE_JUDGMENT_NUMBER, "grade": "confirmed" if one else "near",
                                     "reason": None if one else NEAR_JN_TWO_BODIES, "evidence": _jn_evidence(c, doc, len(bodies), True)}))
                for x in hits:
                    if x["body"] == b:
                        k = (x["kind"], x["value"])
                        came[k] = JN_CONFIRMED if one or came.get(k) == JN_CONFIRMED else JN_TWO
        if not came and len(bodies) == 1:
            parties = sorted((c for c in cs if c["view"] == "court_judgment_parties"), key=lambda x: (x["ref"], x["kind"], x["value"]))
            if len({c["name_key"] for c in parties}) == 1:
                seen = set()
                for c in parties:
                    if c["ref"] in seen:
                        continue
                    seen.add(c["ref"])
                    out.append((c["ref"], c["body"], {"rule": RULE_JUDGMENT_NUMBER, "grade": "near", "reason": NEAR_JN_OTHER_NAME,
                                                      "evidence": _jn_evidence(c, doc, 1, False)}))
                for c in cs:
                    came[(c["kind"], c["value"])] = JN_OTHER_NAME
        for k in {(c["kind"], c["value"]) for c in cs}:
            o = came.get(k, JN_UNTIED)
            counts[o] = counts.get(o, 0) + 1
    return counts, out


# 3 November 2026 (Arthur: "rea_parties (agents, by licence number where a register carries it)"): the Real Estate
# Authority's licence number, which its decisions print beside a licensee, names one licensee
RULE_LICENCE = "licence-number@1"
NEAR_LICENCE_KINDS = "one licence number printed beside a person on one decision and an agency on another; the number is not one licensee's here"
NEAR_LICENCE_NAMES = ("one licence number printed beside two names that do not agree (first and last name, or the agency's name); a number read from a decision's text is not trusted over the names")


# --- ruling 142 (Arthur, 4 November 2026: "go ahead with your recommendations"): the rules that read a private value -----
# measured at links/measurements.md §15 and §16 (rulings 2 and 3), built without the sample pairs. A judgment's street
# address is read by keys.addresses.street_parts on every side and met by keys.addresses.meet; a level of "unit, number,
# street and place" or "number, street and place" is a place level, "number and street" is street only. The value itself
# is never in a link's evidence (links.links is read by the session login): it is in links_private.identifier_links.
RULE_ADDRESS_TITLE = "judgment-address-title@1"           # a judgment's address and a LINZ title's, an owner of the title
RULE_ADDRESS_JUDGMENT = "judgment-address-judgment@1"     # one address printed in two court documents
RULE_ADDRESS_INSOLVENCY = "judgment-address-insolvency@1"   # a judgment's address and an estate's address at adjudication
RULE_ADDRESS_OFFICE = "judgment-address-office@1"         # a judgment's address and a company's registered office
RULE_SHARED_CONTACT = "shared-contact@1"                  # one email or phone printed in two court documents (ruling 2)
PLACE_LEVELS = ("unit, number, street and place", "number, street and place")    # keys.addresses.MATCH_LEVELS[:2]
OFFICE_BUSY = 5         # an office of more than this many companies is busy: near only, and only with a name
NEAR_ADDR_STREET_ONLY = ("the two addresses agree on the number and street but no place is printed on both, so the street "
                         "may be another town's; a name is shared")
NEAR_ADDR_NO_NAME = ("the two addresses agree on the number, street and place (or unit), but no name is shared: the row is "
                     "the name printed nearest the address on its page")
NEAR_OFFICE_BUSY = "the company's name is among the document's parties, but its office is shared by more than five companies"
NEAR_OFFICE_ONE = ("the address is one company's registered office (number, street and town) and the document names no party of "
                   "the company's name: the row is the body printed nearest the address on its page")
NEAR_CONTACT_DIFFERS = ("one email or phone printed in two documents beside two names that differ: one contact, the row on "
                        "each side the name it is tied to")


def _place(level: str) -> bool:
    return level in PLACE_LEVELS


def _aj(rule, grade, reason, ev):
    return {"rule": rule, "grade": grade, "reason": reason, "evidence": ev}


def judge_address_title(m: dict) -> list:
    """`judgment-address-title@1`. `m`: level; named, [(party ref, owner ref)] where an owner of the title carries a party's
    name; tie, the row printed nearest the address ({ref, kind}) or None; owners, [{ref, kind}] of the matched titles.
    Confirmed: a name and a place level; near: a name at street only, or a place level and no name (the tie to each owner
    of its kind). Returns [(a, b, judged)]."""
    ev = {"level": m["level"], "side": "linz title"}
    if m["named"]:
        g, why = ("confirmed", None) if _place(m["level"]) else ("near", NEAR_ADDR_STREET_ONLY)
        return [(a, b, _aj(RULE_ADDRESS_TITLE, g, why, {**ev, "name_shared": True})) for a, b in m["named"]]
    if _place(m["level"]) and m.get("tie"):
        return [(m["tie"]["ref"], o["ref"], _aj(RULE_ADDRESS_TITLE, "near", NEAR_ADDR_NO_NAME,
                                              {**ev, "name_shared": False, "tie": m["tie"]["how"]}))
                for o in m["owners"] if o["kind"] == m["tie"]["kind"]]
    return []


def judge_address_judgment(m: dict) -> list:
    """`judgment-address-judgment@1`. `m`: level; shared, [(row ref, row ref)] of one name in both documents; tie_a, tie_b.
    Confirmed: a place level and a person in both; near: a shared person at street only, or a place level alone (the two
    ties, of one kind)."""
    ev = {"level": m["level"], "side": "other judgment"}
    if m["shared"]:
        g, why = ("confirmed", None) if _place(m["level"]) else ("near", NEAR_ADDR_STREET_ONLY)
        return [(a, b, _aj(RULE_ADDRESS_JUDGMENT, g, why, {**ev, "name_shared": True})) for a, b in m["shared"]]
    a, b = m.get("tie_a"), m.get("tie_b")
    if _place(m["level"]) and a and b and a["kind"] == b["kind"] and a["ref"] != b["ref"]:
        return [(a["ref"], b["ref"], _aj(RULE_ADDRESS_JUDGMENT, "near", NEAR_ADDR_NO_NAME,
                                         {**ev, "name_shared": False, "tie": [a["how"], b["how"]]}))]
    return []


def judge_address_insolvency(m: dict) -> list:
    """`judgment-address-insolvency@1`. `m`: level; named, [(party ref, estate ref)] where the estate's name is a party's;
    tie; estates, [{ref, kind}]. Place levels only: confirmed with the estate's name, near without (the tie to the estate)."""
    if not _place(m["level"]):
        return []
    ev = {"level": m["level"], "side": "insolvency estate"}
    if m["named"]:
        return [(a, b, _aj(RULE_ADDRESS_INSOLVENCY, "confirmed", None, {**ev, "name_shared": True})) for a, b in m["named"]]
    if m.get("tie"):
        return [(m["tie"]["ref"], e["ref"], _aj(RULE_ADDRESS_INSOLVENCY, "near", NEAR_ADDR_NO_NAME,
                                               {**ev, "name_shared": False, "tie": m["tie"]["how"]}))
                for e in m["estates"] if e["kind"] == m["tie"]["kind"]]
    return []


def judge_address_office(m: dict) -> list:
    """`judgment-address-office@1`. `m`: companies, {company ref: level} of every company whose office the address meets;
    named, [(party ref, company ref)] where a party carries the company's name; tie, the body printed nearest (or None).
    Confirmed: the company's name among the parties, the office not busy (OFFICE_BUSY); near: the name at a busy office,
    or no name and exactly one company at the street and town (the tie to it)."""
    cs = m["companies"]
    busy = len(cs) > OFFICE_BUSY
    ev = {"side": "company office", "companies_at_address": len(cs)}
    if m["named"]:
        g, why = ("near", NEAR_OFFICE_BUSY) if busy else ("confirmed", None)
        return [(a, b, _aj(RULE_ADDRESS_OFFICE, g, why, {**ev, "level": cs[b], "name_shared": True})) for a, b in m["named"]]
    at_place = [c for c, lv in cs.items() if _place(lv)]
    if len(at_place) == 1 and len(cs) == 1 and m.get("tie") and m["tie"]["kind"] == "organisation":
        return [(m["tie"]["ref"], at_place[0], _aj(RULE_ADDRESS_OFFICE, "near", NEAR_OFFICE_ONE,
                                                  {**ev, "level": cs[at_place[0]], "name_shared": False, "tie": m["tie"]["how"]}))]
    return []


def judge_shared_contact(kind: str, ties: list) -> list:
    """`shared-contact@1` (ruling 2). `ties`: one {document, ref, kind, name, how} per document printing the value (the row
    it is tied to). Every pair across two documents: confirmed where the two rows are of one kind and name (the first and
    last name, or the organisation's), near where they differ."""
    out = []
    ties = sorted(ties, key=lambda t: (t["document"], t["ref"]))
    for i, a in enumerate(ties):
        for b in ties[i + 1:]:
            if a["document"] == b["document"] or a["ref"] == b["ref"]:
                continue
            same = a["kind"] == b["kind"] and a["name"] == b["name"]
            out.append((a["ref"], b["ref"], _aj(RULE_SHARED_CONTACT, "confirmed" if same else "near",
                                                None if same else NEAR_CONTACT_DIFFERS,
                                                {"contact": kind, "names_agree": same, "tie": [a["how"], b["how"]]})))
    return out
