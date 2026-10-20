"""Every party label the other lanes publish, resolved to a registration by
name and window, for any lane and the site to join on (`pub.party_labels`).

A label is the party as a document prints it: a return's party line, a
declaration's, a candidate's party on the ballot, a member's party in the
expenses or interests registers. Each distinct (label, on) is one row,
`on` being the day the filing speaks for, or its year where the lane keeps
only the year. It resolves through the one party-name function,
`keys.parties.party_name(label, rows, on=…)`, against this lane's own names
and windows (the rows the load has just built, not yesterday's), with two
rules of the register's own:

  a renamed party is the same party: a label in any name the registration
                 carried, on any day it was live, is that registration
  a party cancelled and registered again is two registrations: a label in
                 a name two registrations carried joins the one live on the
                 day (`same_name` says so and names the other); where both
                 were live within the year the lane gives, it joins neither

and one rule of the filings', the one `registers/party_finance` already
applies: a label that does not resolve and ends in a bracket is tried
before the bracket, then inside it, and joins only where both parts that
resolve name one registration ("The Maori Party (Te Pati Maori)").
"Independent" is a candidate or member standing for no party, not a
label that failed. Nothing else is guessed: unresolved says why.

Items in equal items out: every distinct (label, on) a source publishes is
one row here; a blank label is no label and is counted, not kept.

    SOURCES                         (lane, table, label column, the `on` expression, its grain)
    collect(conn)                   ({(label, on): {source: rows}}, {source: (rows, blank, or why absent)})
    resolve(label, on, rows, regs)  the row's fields
    build(conn, names, registrations, loaded_at)   (rows, measured)
"""
import hashlib
import re

from keys import parties as P
from keys.names import organisation_key

READER = "registers.parties.labels 1"
RESOLVER = "keys.parties.party_name(label, rows, on) over this load's names and windows"

#: (lane, table, label column, `on`, grain). `on` is the day a filing speaks for, else its year.
SOURCES = (
    ("party_returns", "party_return_totals", "party_label", "year::text", "year"),
    ("party_returns", "party_return_donors", "party_label", "year::text", "year"),
    ("party_returns", "party_return_loans", "party_label", "year::text", "year"),
    ("disclosures", "disclosures", "party_label", "coalesce(received_on, given_on)::text", "day"),
    ("candidate_returns", "candidate_return_totals", "party", "year::text", "year"),
    ("candidate_returns", "candidate_return_donors", "party", "year::text", "year"),
    ("house", "candidates", "party", "substring(election from '\\d{4}')", "year"),
    ("house", "members", "party", "from_on::text", "day"),
    ("expenses", "mp_expenses", "party_label", "period_start::text", "day"),
    ("expenses", "minister_expenses", "party_label", "period_start::text", "day"),
    ("mp_interests", "mp_interest_returns", "party_label", "as_at::text", "day"),
    ("mp_interests", "mp_interests", "party_label", "as_at::text", "day"),
    ("party_finance", "party_expense_returns", "party_label", "year::text", "year"),
    ("party_finance", "party_expenses", "party_label", "year::text", "year"),
    ("party_finance", "party_financial_statements", "party_label", "coalesce(balance_date::text, filed_year::text)", "day"),
    ("party_finance", "party_statement_figures", "party_label", "coalesce(balance_date::text, filed_year::text)", "day"),
    ("party_finance", "broadcasting_allocations", "party_label", "year::text", "year"),
)
NOT_A_PARTY = {"independent"}
_BRACKET = re.compile(r"^(.*?\S)\s*\(([^()]*)\)\s*$")


def _short(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def key_of(label: str, on: str) -> str:
    return f"label/{_short(label)}/{on}"


def collect(conn) -> tuple:
    """({(label, on): {"lane.table": rows}}, {"lane.table": (labelled rows, blank rows) or why absent})."""
    found, per = {}, {}
    for lane, t, col, on, grain in SOURCES:
        src = f"{lane}.{t}"
        if not conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"pub.{t}",)).fetchone()[0]:
            per[src] = "not published here"
            continue
        rows = conn.execute(f"SELECT {col}, {on}, count(*) FROM pub.{t} GROUP BY 1, 2").fetchall()
        blank = sum(n for label, d, n in rows if not (label or "").strip())
        for label, d, n in rows:
            if (label or "").strip():
                found.setdefault((label, d or ""), {})[src] = n
        per[src] = (sum(n for _, _, n in rows) - blank, blank)
    return found, per


def _registrations_named(label: str, names: list) -> list:
    k = P.name_key(label)
    return sorted({n["party"] for n in names if n["kind"] in ("name", "printed") and P.name_key(n["name"]) == k})


def _window(reg: dict) -> str:
    start = str(reg.get("registered_on") or f"before {str(reg.get('registered_by') or '')[:4]}")
    end = reg.get("cancelled_on")
    return f"{start} to {end}" if end else (f"{start}, off the register page by {reg['off_register_by']}"
                                            if reg.get("off_register_by") else f"{start}, on the register")


def resolve(label: str, on: str, rows: list, regs: dict) -> dict:
    """The fields of one label row: party, basis, why, same_name."""
    out = {"party": None, "basis": "unresolved", "why": None, "same_name": None}
    if organisation_key(label) in NOT_A_PARTY:
        return {**out, "basis": "not a party", "why": "a candidate or member standing for no party"}
    when = on or None
    party, basis = P.party_name(label, rows, on=when)
    if party is None:
        m = _BRACKET.match(label)
        if m:
            got = {p for p in (P.party_name(m.group(1), rows, on=when)[0], P.party_name(m.group(2), rows, on=when)[0]) if p}
            if len(got) == 1:
                party, basis = got.pop(), "before its bracket and inside it, one registration"
    named = _registrations_named(label, rows)
    if len(named) > 1:
        out["same_name"] = ("the name is carried by " + str(len(named)) + " registrations, kept apart: "
                            + "; ".join(f"{k} ({_window(regs[k])})" for k in named if k in regs))
    if party is not None:
        return {**out, "party": party, "basis": basis}
    if not when:
        return {**out, "why": "the filing gives no day or year"}
    live = [k for k in named if k in regs and _live(regs[k], when)]
    if len(live) > 1:
        return {**out, "why": f"{len(live)} registrations of this name were live within {when}: neither is taken"}
    return {**out, "why": "no registration live then answers to it by any name it carried"}


def _span(on: str) -> tuple:
    """`on` as (first day, last day): a year is its whole span."""
    return (f"{on}-01-01", f"{on}-12-31") if re.fullmatch(r"\d{4}", on) else (on[:10], on[:10])


def _live(reg: dict, on: str) -> bool:
    first, last = _span(on)
    start, end = reg.get("registered_on"), reg.get("cancelled_on")
    return (start is None or str(start) <= last) and (end is None or str(end) >= first)


def _cite(party, on, names, regs, page_stamp) -> dict:
    """The name row the registration carried on the day, else the
    registration's own row; for a label nothing answers to, the register page."""
    if party is None:
        return {**page_stamp, "place": "the register as read: no registration answers"}
    span = _span(on) if on else None
    mine = [n for n in names if n["party"] == party and n["kind"] == "name"]
    for n in mine:
        if span and (n["from_on"] is None or str(n["from_on"]) <= span[1]) and (n["to_on"] is None or str(n["to_on"]) >= span[0]):
            return {k: n[k] for k in ("document", "page", "place", "read_from", "profile", "profile_version")}
    r = regs[party]
    return {k: r[k] for k in ("document", "page", "place", "read_from", "profile", "profile_version")}


def build(conn, names: list, registrations: list, page_stamp: dict, loaded_at: str) -> tuple:
    """names, registrations: this load's rows (read.Result, flattened);
    page_stamp: the register page's citation. Returns (rows, measured)."""
    regs = {r["key"]: r for r in registrations}
    rows = [{"party": n["party"], "name": n["name"], "kind": n["kind"], "from_on": n["from_on"], "to_on": n["to_on"],
             "registered_on": regs[n["party"]]["registered_on"], "cancelled_on": regs[n["party"]]["cancelled_on"]}
            for n in names]
    found, per = collect(conn)
    out = []
    for (label, on), srcs in sorted(found.items()):
        f = resolve(label, on, rows, regs)
        cite = _cite(f["party"], on, names, regs, page_stamp)
        out.append({"key": key_of(label, on), **cite, "reader": READER, "loaded_at": loaded_at,
                    "label": label, "on": on, "grain": "year" if re.fullmatch(r"\d{4}", on or "") else "day",
                    "party_name": regs[f["party"]]["name"] if f["party"] else None, **f,
                    "sources": "; ".join(f"{s} {n}" for s, n in sorted(srcs.items())),
                    "rows": sum(srcs.values()), "resolver": RESOLVER})
    if len(out) != len(found):
        raise AssertionError(f"the labels do not reconcile: {len(found)} in, {len(out)} out")
    return out, measure(out, per)


def measure(out: list, per: dict) -> dict:
    """source → {labelled, blank, resolved, not a party, unresolved} in rows."""
    m = {s: ({"labelled": v[0], "blank": v[1], "resolved": 0, "not a party": 0, "unresolved": 0}
             if isinstance(v, tuple) else v) for s, v in per.items()}
    for r in out:
        for part in r["sources"].split("; "):
            src, n = part.rsplit(" ", 1)
            bucket = "resolved" if r["party"] else ("not a party" if r["basis"] == "not a party" else "unresolved")
            m[src][bucket] += int(n)
    return m
