"""The reading: the Commission's table of large declarations → register
rows, run from the document profile `ec-disclosure-listing` through the
reader contract (read from text, stamped with reader, profile and version).
One listing document is read alone; nothing here calls a model, so the fast
tier runs the same code.

The scanned declarations are joined to the rows by the Commission's own
link: the file name in the row's link against the names the held files
carry. Where two different files fold to one name the join picks neither
(`collision`). A held file no row links is listed, never read into a row:
which declaration an unlisted file belongs to is the Commission's to say.

The key is stable across captures, amendments and rebuilds: the day the
Commission received the declaration (it keeps the original's date when an
amendment arrives) and a short hash of the regime, the party as printed
and the donor's key; rows equal in all of those are numbered in page order.
No name appears in a key.

    result = read_listing(data, sha256)        Result(rows, items, addresses, set_aside)
    join(rows, held)                           {key: declaration document}, [file lines]
"""
import datetime as dt
import hashlib
import os
import re
from dataclasses import dataclass, field

from keys import parties
from keys.names import is_organisation, organisation_key, person_key
from support import profiles
from registers.disclosures import listing

PROFILE = "ec-disclosure-listing"
READER = "registers.disclosures.listing 1"
HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")


@dataclass
class Result:
    document: str
    rows: list = field(default_factory=list)        # dicts under the row contract
    items: list = field(default_factory=list)
    addresses: list = field(default_factory=list)   # (key, address): the private schema only
    set_aside: list = field(default_factory=list)   # (item, stage, reason)
    seen: int = 0


def current_profile() -> dict:
    """The ledger's version; until the integrator appends it, the lane's
    proposed line (merge request disclosures-1)."""
    p = profiles.profile(PROFILE) or profiles.profile(PROFILE, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {PROFILE}")
    return p


def donor_key(name: str) -> str:
    return organisation_key(name) if is_organisation(name) else person_key(name)


def stable_key(row: listing.Row, n: int) -> str:
    ident = "|".join((row.regime, row.received_on, organisation_key(row.party_label), donor_key(row.donor_name)))
    key = f"ec-listing/{row.received_on}/{hashlib.sha256(ident.encode()).hexdigest()[:12]}"
    return key if n == 1 else f"{key}/{n}"


def file_key(name: str) -> str:
    """A Commission file name folded for the join: the archive's `<tree>__`
    off, the extension off, everything but letters and digits one `_`. The
    Commission itself switches `_` and `-` between weeks."""
    s = (name or "").rsplit("/", 1)[-1].split("__", 1)[-1]
    s = re.sub(r"\.[a-z0-9]{2,4}$", "", s, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def read_listing(data: bytes, sha256: str, loaded_at: str = None) -> Result:
    prof = current_profile()
    version = int(prof["version"])
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    reading = listing.read(data)
    out = Result(sha256, seen=len(reading.rows) + len(reading.skipped))
    for t, r, why in reading.skipped:
        out.set_aside.append((f"{sha256}/table {t} row {r}", "listing", why))
    taken = {}
    for row in reversed(reading.rows):          # oldest first, so a new row at the top never renumbers an old one
        base = stable_key(row, 1)
        taken[base] = taken.get(base, 0) + 1
        key = stable_key(row, taken[base])
        party, basis = parties.party_name(row.party_label)
        items_sum = round(sum(i.amount for i in row.items if i.amount is not None), 2) if row.items else None
        check = "no figures" if items_sum is None else ("equal" if abs(items_sum - row.amount) < 0.005 else "differs")
        out.rows.append({
            "key": key, "document": sha256, "page": 1, "place": f"table {row.table} row {row.row}",
            "reader": READER, "profile": PROFILE, "profile_version": version, "read_from": "text",
            "loaded_at": loaded_at,
            "filed": {
                "regime": row.regime, "threshold": row.threshold, "section": row.section,
                "party": party, "party_label": row.party_label, "party_basis": basis,
                "donor_name": row.donor_name, "amount": round(row.amount, 2),
                "amount_original": row.amount_original, "received_on": row.received_on, "given_on": row.given_on,
                "commission_note": row.commission_note, "amendment": row.amendment, "amended_on": row.amended_on,
                "withdrawn_on": row.withdrawn_on, "returned_on": row.returned_on, "amount_note": row.amount_note,
                "items_sum": items_sum, "items_check": check,
                "at_or_under_threshold": row.amount <= row.threshold, "href": row.href,
            },
        })
        for it in row.items:
            out.items.append({"key": f"{key}/{it.ordinal}", "declaration": key, "ordinal": it.ordinal,
                              "amount": it.amount, "first_date": it.first_date, "contributor": it.contributor,
                              "text": it.text})
        if row.address:
            out.addresses.append((key, ", ".join(row.address)))
    return out


def join(rows: list, held: list) -> tuple:
    """rows: the read rows; held: [(sha256, Commission file name)] of the
    landed declarations. Returns ({key: sha256}, [(sha256, name, linked_by,
    status)]). A link two different files answer is a collision and joins
    neither."""
    by_name = {}
    for sha, name in held:
        by_name.setdefault(file_key(name), set()).add(sha)
    linked, files = {}, []
    used = {}
    for r in rows:
        href = r["filed"].get("href")
        if not href:
            continue
        shas = by_name.get(file_key(href), set())
        if len(shas) == 1:
            sha = next(iter(shas))
            linked[r["key"]] = sha
            used.setdefault(sha, r["key"])
        elif len(shas) > 1:
            for sha in shas:
                used.setdefault(sha, None)
    for sha, name in held:
        if sha in used and used[sha] is None:
            files.append((sha, name, None, "collision"))
        elif sha in used:
            files.append((sha, name, used[sha], "linked"))
        else:
            files.append((sha, name, None, "not linked by the table"))
    return linked, files
