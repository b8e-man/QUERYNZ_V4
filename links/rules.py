"""The two rules that confirm a link between two person rows, exact
(design: "How a link is made"; old rulings 217, 218, 221). Pure functions
over the rows `links.rows` holds. The weights the old estate set by hand
are not here.

1. `full-name@1`: the same first, middle and last name: the full name key
   equal token for token, and a middle name present. Confirmed.
2. `name-and-address@1`: the same first and last name, and the company
   each role sits on has filed the same registered office. Confirmed; but
   an address shared by more than HUB_FLOOR companies (a busy address:
   an accountant's office) counts only when the full name carries a middle
   name. Address alone never confirms.

Everything else that shares a name is near, with the reason. A
politician's row (a candidate, a member, a declared-interests return)
joined to the director register by name is near whatever the name
similarity, until a supporting link holds (design: "Joining a politician
to a company role is stricter"). Organisations with an official number
need none of this: the number is the link (`official-number@1`).
"""
from __future__ import annotations

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
