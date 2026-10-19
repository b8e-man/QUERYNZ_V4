"""The reading: each kind of document through the reader contract from its
own document profile (profiles before readers), turned into register rows
under the row contract, or catch-log lines saying why not. No model is
called anywhere here: the Commission's pages are read as HTML
(`listing.py`), and a return's pages come from its text layer or the page
reader's stored readings (`expenses.py`), so the fast tier runs the same
code.

A profile this lane proposes (`profile-proposed.jsonl`) is read from there
until the integrator appends it to `support/profiles`; the shared ledger
wins once it holds the slug.

    profile(slug)                                     the current version, shared ledger first
    party_of(label, rows, on)                         (registration key | None, basis): keys.parties over the
                                                      parties lane's published names, live on the day
    listing_rows(kind, data, sha, year, by_url, at)   -> (rows, links, set_aside)
    expense_return_row(result, link, at)              the register row, or None
    allocation_rows(data, sha, at)                    -> (rows, totals, set_aside)
    promoter_return_rows(result, listing_row, at)     -> (rows, set_aside), one row per part read
    promoter_rows(data, sha, at)                      -> (promoters, people, private contacts, set_aside)
    statement_rows(data, sha, by_url, at)             -> (rows, links, set_aside)
"""
import datetime as dt
import os
import re

from keys import parties
from support import profiles
from registers.party_finance import broadcasting, expenses, financials, listing, promoter_returns, promoters

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
PROFILE_OF = {"expenses-listing": listing.EXPENSES_PROFILE, "promoter-expenses-listing": listing.PROMOTERS_PROFILE}


def profile(slug: str) -> dict:
    p = profiles.profile(slug) or profiles.profile(slug, PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}: profiles come before readers")
    return p


#: polling day of each general election the lane holds: a party is the registration live that day
ELECTION_DAY = {2020: "2020-10-17", 2023: "2023-10-14"}
#: a remark the Commission prints after a party's name, `ONE Party (currently applying to change its party name …)`
BRACKET = re.compile(r"^(.*?\S)\s*\([^()]*\)\s*$")


def party_of(label: str, rows, on) -> tuple:
    """(registration key | None, basis) through `keys.parties.party_name(label, rows, on=…)`; an election year is
    its polling day. A label unresolved with a trailing bracket is tried once without it."""
    on = ELECTION_DAY.get(on, on)
    key, basis = parties.party_name(label, rows, on=on)
    m = BRACKET.match(label or "")
    if key is None and m:
        key, basis = parties.party_name(m.group(1), rows, on=on)
        basis = f"{basis}, before its bracket" if key else basis
    return key, basis


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def listing_rows(kind: str, data: bytes, sha256: str, year: int, by_url: dict, loaded_at: str = None,
                 party_rows=()) -> tuple:
    """One Commission listing page → (rows, links, set_aside). `by_url` is
    the Commission URL → held document hash. Rows seen equal rows read plus
    rows set aside; every link is a held document or a catch-log line."""
    loaded_at = loaded_at or now()
    prof = profile(PROFILE_OF[kind])
    reading = (listing.read_expenses if kind == "expenses-listing" else listing.read_promoters)(data, year)
    rows, links, aside = [], [], []
    for n, why in reading.skipped:
        aside.append((f"{sha256}/row/{n}", "listing", why))
    for r in reading.rows:
        key = f"{sha256}/row/{r.ordinal}"
        row = {"key": key, "document": sha256, "page": 1, "place": f"row {r.ordinal}", "year": year, "note": r.note or None,
               "printed": " | ".join(r.printed), "reader": f"{listing.READER}: {listing.MODEL}", "profile": prof["slug"],
               "profile_version": int(prof["version"]), "read_from": "text", "loaded_at": loaded_at, **r.figures}
        if kind == "expenses-listing":
            party, basis = party_of(r.label, party_rows, year)
            row.update(party_label=r.label, party=party, party_basis=basis)
        else:
            row.update(promoter=r.label)
        rows.append(row)
        for i, ln in enumerate(r.links, 1):
            doc = by_url.get(ln.url)
            links.append({"row_key": key, "ordinal": i, "link_text": ln.text, "url": ln.url, "amended": ln.amended,
                          "document": doc})
            if doc is None:
                aside.append((key, "link", f"{r.label} {year}: the Commission links {ln.url}, which the lane does not hold"))
    return rows, links, aside


def is_current(link: dict, row_links: list) -> bool:
    """The Commission's figure for a row belongs to the amendment where the
    row names one, else to the row's only link."""
    amended = [x for x in row_links if x["amended"]]
    if amended:
        return link["ordinal"] == amended[0]["ordinal"]
    return len(row_links) == 1


PLACE = {"form": "Total (A + B + C)", "auditor": "Total Party Election Expenses (the auditor's report)",
         "parts": "TOTAL FOR PART A, B and C", "nil": "Total (A + B + C): NIL"}


def expense_return_row(result: expenses.Result, listing_row: dict, link: dict, current: bool, loaded_at: str = None):
    if result.total is None:
        return None
    return {"key": f"{result.document}/declaration", "document": result.document, "page": result.page,
            "place": PLACE[result.basis], "listing_row": listing_row["key"], "year": listing_row["year"],
            "party_label": listing_row["party_label"], "party": listing_row["party"],
            "party_basis": listing_row["party_basis"], "current": current, "total": result.total,
            "total_check": result.total_check, "part_a": result.parts.get("A"), "part_b": result.parts.get("B"),
            "part_c": result.parts.get("C"), "expense_limit": result.limit, "read_from": result.read_from,
            "reader": ("support.docread 1: text-layer" if result.read_from == "text" else f"{expenses.PAGE_MODEL} (stored reading)"),
            "profile": result.reading_profile, "profile_version": result.reading_version,
            "loaded_at": loaded_at or now()}


def allocation_rows(data: bytes, sha256: str, loaded_at: str = None, party_rows=()) -> tuple:
    """One allocation page → (rows, totals, set_aside). A page whose rounds do
    not each add to its own printed total publishes no row."""
    loaded_at = loaded_at or now()
    prof = profile(broadcasting.PROFILE)
    year = broadcasting.election_year(data)
    if year is None:
        return [], [], [(sha256, "allocation", "the page states no general election in its breadcrumb")]
    b = broadcasting.read(data)
    aside = [(f"{sha256}/{where}", "allocation", why) for where, why in b.skipped]
    totals = []
    for i, label in enumerate(b.rounds):
        totals.append({"key": f"{sha256}/round/{i + 1}", "document": sha256, "year": year, "round": i + 1,
                       "round_label": label, "allocated": (b.totals.get("allocated") or [None] * len(b.rounds))[i],
                       "available": (b.totals.get("available") or [None] * len(b.rounds))[i],
                       "rows_sum": sum(r.amounts[i] or 0 for r in b.rows),
                       "printed": " | ".join(f"{k}: {v[i] if i < len(v) else ''}" for k, v in b.printed_totals.items())})
    if b.failed_rounds:
        bad = ", ".join(f"round {i + 1} rows {totals[i]['rows_sum']} against {totals[i]['allocated']}" for i in b.failed_rounds)
        return [], totals, aside + [(sha256, "allocation", f"{year}: the rounds do not add to the page's own totals ({bad}); "
                                    "nothing from the page is published")]
    rows = []
    for r in b.rows:
        party, basis = party_of(r.label, party_rows, year)
        for i, label in enumerate(b.rounds):
            rows.append({"key": f"{sha256}/row/{r.ordinal}/round/{i + 1}", "document": sha256, "page": 1,
                         "place": f"row {r.ordinal}, round {i + 1}", "year": year, "round": i + 1, "round_label": label,
                         "final": i == len(b.rounds) - 1, "party_label": r.label, "party": party, "party_basis": basis,
                         "mark": r.mark or None, "eligible": r.eligible, "amount": r.amounts[i], "printed": r.printed[i],
                         "reader": f"{broadcasting.READER}: {broadcasting.MODEL}", "profile": prof["slug"],
                         "profile_version": int(prof["version"]), "read_from": "text", "loaded_at": loaded_at})
    return rows, totals, aside


def promoter_return_rows(result: promoter_returns.Result, listing_row: dict, loaded_at: str = None) -> tuple:
    """A promoter's return → (one row per part read, set_aside); every part the year's form has is one or the other."""
    loaded_at = loaded_at or now()
    rows, aside = [], []
    whys = dict(result.set_aside)
    for letter, spending in promoter_returns.COLUMNS.get(result.year, {}).items():
        part = result.parts.get(letter)
        if part is None or part.figure is None:
            why = whys.get(letter) or whys.get("") or f"Part {letter}: not read"
            aside.append((f"{result.document}/part/{letter}", "promoter-return",
                          f"{listing_row['promoter']} {result.year}: {why}"))
            continue
        how, prof, version = result.pages[part.page]
        rows.append({"key": f"{result.document}/part/{letter}", "document": result.document, "page": part.page,
                     "place": promoter_returns.PLACE[part.check].format(letter), "listing_row": listing_row["key"],
                     "year": result.year, "promoter": listing_row["promoter"], "part": letter, "spending": spending,
                     "figure": part.figure, "figure_check": part.check, "declared": part.declared,
                     "schedule": part.schedule, "read_from": how,
                     "reader": ("support.docread 1: text-layer" if how == "text"
                                else f"{expenses.PAGE_MODEL} (stored reading)"),
                     "profile": prof, "profile_version": version, "loaded_at": loaded_at})
    return rows, aside


ROLE = {"authorised_representative": "authorised representative", "comparable_with_director": "comparable with director",
        "trustees": "trustee"}


def promoter_rows(data: bytes, sha256: str, loaded_at: str = None) -> tuple:
    """One register page → (promoters, people, contacts, set_aside). The
    contacts are private rows; nothing of them reaches a published table."""
    loaded_at = loaded_at or now()
    prof = profile(promoters.PROFILE)
    year = broadcasting.election_year(data)
    if year is None:
        return [], [], [], [(sha256, "promoter", "the page states no general election in its breadcrumb")]
    reading = promoters.read(data)
    stamp = {"page": 1, "reader": f"{promoters.READER}: {promoters.MODEL}", "profile": prof["slug"],
             "profile_version": int(prof["version"]), "read_from": "text", "loaded_at": loaded_at}
    out, ppl, contacts = [], [], []
    aside = [(f"{sha256}/block/{n}", "promoter", why) for n, why in reading.skipped]
    for p in reading.promoters:
        key = f"{sha256}/block/{p.ordinal}"
        said = []
        for field_, role in ROLE.items():
            names, statements = promoters.people(p.public.get(field_, []))
            said += statements
            for i, name in enumerate(names, 1):
                tag = role.replace(" ", "-")
                ppl.append({"key": f"{key}/{tag}/{i}", "promoter_key": key, "document": sha256,
                            "place": f"block {p.ordinal}, {role} {i}", "role": role, "name": name, **stamp})
        out.append({"key": key, "document": sha256, "place": f"block {p.ordinal}", "year": year, "promoter": p.name,
                    "registered_on": p.registered_on, "registered_for": " / ".join(p.public.get("registered_for", [])) or None,
                    "statement": " / ".join(said) or None, **stamp})
        for label, vals in p.private.items():
            contacts.append({"promoter_key": key, "label": label, "value": "\n".join(vals)})
        for label in p.unknown:
            aside.append((key, "promoter", f"{p.name}: a field labelled {label!r} the reader has not met; held private"))
    return out, ppl, contacts, aside


def statement_rows(data: bytes, sha256: str, by_url: dict, loaded_at: str = None, party_rows=()) -> tuple:
    """The Commission's roster page → (rows, links, set_aside). Every table
    row is a roster row or a catch-log line; every link a held statement or
    a catch-log line."""
    loaded_at = loaded_at or now()
    prof = profile(financials.PROFILE)
    reading = financials.read(data)
    aside = [(f"{sha256}/{y}/row/{n}", "statement", why) for y, n, why in reading.skipped]
    rows, out_links = [], []
    for r in reading.rows:
        key = f"{sha256}/{r.filed_year}/row/{r.ordinal}"
        party, basis = party_of(r.label, party_rows, r.dates["balance_date"] or r.filed_year)
        rows.append({"key": key, "document": sha256, "page": 1, "place": f"{r.filed_year} table, row {r.ordinal}",
                     "filed_year": r.filed_year, "party_label": r.label, "party": party, "party_basis": basis,
                     "note": r.note or None, "mark": r.mark or None, "balance_date": r.dates["balance_date"],
                     "deadline": r.dates["deadline"], "date_filed": r.dates["date_filed"],
                     "balance_printed": r.printed["balance_date"], "deadline_printed": r.printed["deadline"],
                     "filed_printed": r.printed["date_filed"], "audit_requirement": r.printed["audit_requirement"],
                     "reader": f"{financials.READER}: {financials.MODEL}", "profile": prof["slug"],
                     "profile_version": int(prof["version"]), "read_from": "text", "loaded_at": loaded_at})
        for i, ln in enumerate(r.links, 1):
            doc = by_url.get(ln.url)
            out_links.append({"row_key": key, "ordinal": i, "link_text": ln.text, "url": ln.url, "amended": ln.amended,
                              "document": doc})
            if doc is None:
                aside.append((key, "link", f"{r.label} {r.filed_year}: the Commission links {ln.url}, which the lane does not hold"))
    return rows, out_links, aside
