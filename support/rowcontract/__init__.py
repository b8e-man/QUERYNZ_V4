"""The register row's contract (plan 1.9; docs/contracts/register-row.md).

Every row a lane publishes carries:

  key            the stable key: the source's own identifier for a copied
                 register; for a built one, the document's hash plus the
                 place in it. The same across re-reads, amendments and
                 nightly rebuilds. Old donation rows were renumbered nightly,
                 which broke every citation.
  document       the sha256 of the document it came from
  page, place    where on the document (page number from 1; place is a row
                 number, a cell, or a bounding box, as the lane says)
  filed dates    as the file states them; an ended role carries the day it
                 ended, never the load day (contract: dates)
  reader         the reader that made it and the document profile and
                 version it ran from
  read_from      'text' (a text layer) or 'pixels' (the page reader): a
                 figure read from pixels is weaker evidence and is shown so
  loaded_at      when this row was written; never used as a date of anything

A person's home address is not a column of the row. It lives in the lane's
`_private` schema, keyed by the row's key (`private_ref`), and no published
table or export carries it (hard limit 15).

`validate(row, loaded_on)` returns the problems as plain lines; a lane's
tests call it on every row of its sample.
"""
import datetime as dt
import re
from dataclasses import dataclass, field

REQUIRED = ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from", "loaded_at")
READ_FROM = ("text", "pixels")
FORBIDDEN_COLUMNS = ("address", "home_address", "residential_address", "street_address")
_SHA = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class RegisterRow:
    key: str
    document: str
    page: int
    place: str
    reader: str
    profile: str
    profile_version: int
    read_from: str
    loaded_at: str
    filed: dict = field(default_factory=dict)     # the dates and fields as filed; ISO dates
    private_ref: str = ""                          # key into the lane's _private schema, when any


def validate(row: dict, loaded_on: dt.date = None) -> list:
    out = []
    for f in REQUIRED:
        if f not in row or row[f] in (None, ""):
            out.append(f"missing {f}")
    if out:
        return out
    if not _SHA.match(str(row["document"])):
        out.append("document is not a sha256")
    if not isinstance(row["page"], int) or row["page"] < 1:
        out.append("page must be an integer from 1")
    if row["read_from"] not in READ_FROM:
        out.append(f"read_from must be one of {READ_FROM}")
    if not isinstance(row["profile_version"], int) or row["profile_version"] < 1:
        out.append("profile_version must be an integer from 1")
    for col in FORBIDDEN_COLUMNS:
        if col in row:
            out.append(f"a published row must not carry {col} (hard limit 15)")
    filed = row.get("filed") or {}
    for name, val in filed.items():
        if name.endswith(("_on", "_date")) and val not in (None, ""):
            try:
                d = dt.date.fromisoformat(str(val))
            except ValueError:
                out.append(f"filed.{name} is not an ISO date: {val!r}")
                continue
            if name == "ended_on" and loaded_on and d == loaded_on and not filed.get("ended_on_stated"):
                out.append("ended_on equals the load day and the document does not state it (contract: dates)")
    return out
