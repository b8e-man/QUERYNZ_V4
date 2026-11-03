"""What the LINZ lane's code produces from a page of its profile, and what each page has had extracted (Arthur, 3
November 2026: "the lane asks for something and the profile provides something. we need to ensure that these
somethings are aligned").

One profile, `linz-wfs-page`: a WFS page of any source. Its fields come from the code that makes them, never a second
list: each source's columns as the load writes them (`load.COLUMNS`, the citation stamp and the key apart), a field
named by its column and landing in every table that carries it; a private source's columns land in `linz_private`
(capture.PRIVATE_SOURCES), and so does each title's street address (`load.TITLE_ADDRESS_COLUMNS`). All by rules, no
model. `support/profiles/align.py` holds them to the profile's extract list.

    produces(slug)         {field: (by, kinds)}
    LANE                   the lane as align.py reads it
    problems()             align.problems for the lane
    where(schema)          a lane table → (schema, table) in the database
    extracted(pages)       the docs.extractions rows for a load's pages: (sha256, profile, field, iteration, reader, model)
"""
from support import profiles as pr
from support.profiles import align
from registers.linz import capture, load as L, read as R

SLUG = R.PROFILE
_STAMP = ("key",) + L._CITE


def _table(source: str) -> str:
    return f"{L.PRIVATE}.{source}" if source in capture.PRIVATE_SOURCES else source


#: the lane's tables, in its own naming ("titles", "linz_private.addresses") → their columns
TABLES = {**{_table(s): L.COLUMNS[s] for s in L.SOURCES},
          f"{L.PRIVATE}.title_addresses": L.TITLE_ADDRESS_COLUMNS}
#: what a row says about where it came from or how it was joined, never a field of the page
HOUSEKEEPING = frozenset({"owners.title_key"} | {f"{L.PRIVATE}.title_addresses.{c}" for c in (
    "joined_by", "titles_on_property", "addresses_on_property", "property_title_key", "property_address_key",
    "address_key", "property_title_document", "property_address_document", "address_document")})


def fields_of(source: str) -> tuple:
    """The fields a page of `source` yields: its table's columns, the stamp apart."""
    return tuple(c for c in L.COLUMNS[source] if c not in _STAMP and f"{_table(source)}.{c}" not in HOUSEKEEPING)


def lands() -> dict:
    """field → every lane column it is written to, from the tables (a field is named by its column)."""
    out = {}
    for t, cols in TABLES.items():
        for c in cols:
            col = f"{t}.{c}"
            if c in _STAMP or col in HOUSEKEEPING:
                continue
            out.setdefault(c, []).append(col)
    return out


def produces(slug: str = SLUG) -> dict:
    return {f: ("rules", None) for f in lands()} if slug == SLUG else {}


LANE = align.Lane("linz", TABLES, {SLUG: produces(SLUG)}, HOUSEKEEPING)


def problems(profiles: dict = None) -> list:
    return align.problems(LANE, profiles)


def where(schema: str = L.SCHEMA):
    """A lane table's name → (schema, table) in the database, `schema` the public one (a staging schema renames both)."""
    def at(t: str) -> tuple:
        if t.startswith(L.PRIVATE + "."):
            return L.private_of(schema), t.split(".", 1)[1]
        return schema, t
    return at


def extracted(pages: list, profiles: dict = None) -> list:
    """docs.extractions rows for the pages a load read: `pages` are (sha256, source). A page has had the fields its
    source yields, each at its current item's iteration; a field the profile does not list is not recorded."""
    profiles = pr.current() if profiles is None else profiles
    items = pr.latest((profiles.get(SLUG) or {}).get("extract"))
    out, seen = [], set()
    for sha, source in pages:
        if (sha, source) in seen:
            continue
        seen.add((sha, source))
        for f in fields_of(source):
            if f in items:
                out.append((sha, SLUG, f, items[f]["iteration"], R.READER, None))
    return out
