"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Land the export (never run it: capture.py was run once), read it, copy the
rows in. Items in equal items out plus items set aside (read.py says how).
"""
import os
import re

from support import jobrun
from support.docstore.landing import read_bytes
from registers.gazette import capture, dissolutions, possessions, read, register

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "gazette"
PRIVATE = "gazette_private"
TABLES = ("notices", "celebrants", "prohibitions", "liquidations", "liquidators", "company_notices", "practitioners",
          "bankruptcies", "appointments", "possessions", "files", "set_aside")
PRIVATE_TABLES = ("celebrant_addresses", "prohibition_addresses", "bankruptcy_addresses", "possession_details")
COLUMNS = {
    "notices": ("key", "notice", "year", "section", "number", "family", "format", "status", "records", "supersedes", "title",
                "published_on", "url", "old_type", "article", "source_note", "document", "page", "place",
                "read_from", "reader", "profile", "profile_version", "loaded_at"),
    "celebrants": ("key", "notice", "published_on", "action", "statute", "period_from", "period_to", "surname",
                   "given_names", "organisation", "list_shape", "marks", "split", "ordinal", "document", "page", "place",
                   "read_from", "reader", "profile", "profile_version", "loaded_at"),
    "prohibitions": ("key", "notice", "published_on", "action", "name", "also_known_as", "named_twice", "statute",
                     "months", "permanent", "starts_on", "starts_basis", "ends_on", "dated_on", "supersedes",
                     "superseded_by", "superseded_how", "ordinal", "document", "page", "place", "read_from", "reader",
                     "profile", "profile_version", "loaded_at"),
    "liquidations": ("key", "notice", "published_on", "company", "company_number", "shape", "appointed_by", "statute",
                     "appointed_on", "appointed_at", "date_basis", "dated_on", "corrigendum", "liquidators", "register_key",
                     "register_match", "ordinal",
                     "document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at"),
    "liquidators": ("key", "notice", "published_on", "name", "role", "named_in_body", "companies", "ordinal", "document",
                    "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at"),
    "company_notices": ("key", "notice", "published_on", "kind", "action", "company", "company_number", "shape", "statute",
                        "ground", "by_whom", "party", "event_on", "event_at", "event_basis", "filed_on", "court", "reference",
                        "dated_on", "corrigendum", "people", "register_key", "register_match", "ordinal", "role", "people_named",
                        "document", "page",
                        "place", "read_from", "reader", "profile", "profile_version", "loaded_at"),
}
COLUMNS["practitioners"] = COLUMNS["liquidators"]
COLUMNS["appointments"] = ("key", "notice", "published_on", "body", "name", "role", "statute", "by_whom", "starts_on",
                           "ends_on", "dated_on", "corrigendum", "ordinal", "document", "page", "place", "read_from", "reader",
                           "profile", "profile_version", "loaded_at")
COLUMNS["bankruptcies"] = ("key", "notice", "published_on", "kind", "shape", "surname", "given_names", "also_known_as",
                           "occupation", "event_on", "event_at", "court", "statute", "dated_on", "withheld_by", "ordinal",
                           "document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at")

COLUMNS["possessions"] = ("key", "notice", "published_on", "action", "asset", "statute", "mortgagee", "mortgagee_kind",
                          "mortgagee_number", "mortgagee_register_key", "mortgagee_register_match", "mortgagor",
                          "mortgagor_kind", "mortgagor_number", "mortgagor_register_key", "mortgagor_register_match",
                          "entered_on", "entered_basis", "dated_on", "corrigendum", "property_held", "document", "page",
                          "place", "read_from", "reader", "profile", "profile_version", "loaded_at")
PRIVATE_COLUMNS = {"possession_details": ("key", "mortgagee", "mortgagor", "property", "registration")}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.gazette_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    return text.replace(f"{PRIVATE}.", f"{private_of(schema)}.{pre}").replace(f"{SCHEMA}.", f"{schema}.{pre}")


def create_tables(conn, schema: str, shared: bool = False) -> None:
    """The lane's tables as tables.sql has them now, made again on every
    build: every row is rebuilt from documents."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    for t in PRIVATE_TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(private_of(schema), t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> None:
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(row)


def _flat(cols: tuple, rows: list):
    for row in rows:
        flat = {**row, **row.get("filed", {})}
        yield tuple(flat.get(c) for c in cols)


def build(conn, schema: str, export: tuple, aside: list, only=None, shared: bool = False) -> dict:
    """export: (sha256, name); aside: [(item, why)] from capture; only: the
    notice numbers to read (the sample's), None for all. Wipes and fills
    `schema`; returns the counts."""
    create_tables(conn, schema, shared)
    res = read.read(read_bytes(export[0]), export[0], only=only)
    joined = join_register(conn, res, schema, shared)
    details = join_possessions(res, joined.pop("_index", None))
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [(i, "capture", w) for i, w in aside] + list(res.set_aside))
    for t, rows in (("notices", res.notices), ("celebrants", res.celebrants), ("prohibitions", res.prohibitions),
                    ("liquidations", res.liquidations), ("liquidators", res.liquidators),
                    ("company_notices", res.company_notices), ("practitioners", res.practitioners),
                    ("bankruptcies", res.bankruptcies), ("appointments", res.appointments),
                    ("possessions", res.possessions)):
        _copy(conn, table(schema, t, shared), COLUMNS[t], _flat(COLUMNS[t], rows))
    _copy(conn, table(private_of(schema), "celebrant_addresses", shared), ("key", "address"), res.addresses)
    _copy(conn, table(private_of(schema), "prohibition_addresses", shared), ("key", "address", "formerly"),
          res.prohibition_addresses)
    _copy(conn, table(private_of(schema), "bankruptcy_addresses", shared), ("key", "address", "formerly"),
          res.bankruptcy_addresses)
    _copy(conn, table(private_of(schema), "possession_details", shared), PRIVATE_COLUMNS["possession_details"], details)
    conn.execute(f"INSERT INTO {table(schema, 'files', shared)} VALUES (%s, %s, 'notices', 'read')", export)
    return {**res.counts, **joined, "not_held": len(aside)}


def join_register(conn, res, schema: str, shared: bool = False) -> dict:
    """Each company row (a liquidation, a removal, a winding-up
    application, a receivership) given the companies lane's entity it
    names (register.py), alive on the notice's own date for it: the
    appointment, the filing, else the Dated or published day. A row the
    register does not hold, or holds more than once alive that day, is a
    catch-log line and carries no entity."""
    rows = register.rows_from(conn, schema, shared)
    if rows is None:
        return {"register": "not in this database"}
    idx, n = register.Index(rows), {}
    for r in res.liquidations + res.company_notices:
        f = r["filed"]
        on = f.get("appointed_on") or (f.get("event_on") if f.get("event_basis") == "appointment" else None) \
            or f.get("filed_on") or f.get("dated_on") or f["published_on"]
        regs = dissolutions.REGISTERS if f.get("kind") == "dissolution" else ("companies",)   # a society prints its own number
        f["register_key"], f["register_match"] = idx.match(f["company"], f["company_number"], on, int(f["notice"][:4]), regs)
        n[f["register_match"]] = n.get(f["register_match"], 0) + 1
        if f["register_match"] in register.UNMATCHED:
            res.set_aside.append((f"{r['document']}/{r['place']}", "register", f"the companies register: {f['register_match']}"))
    return {**{f"register_{register.COUNT[k]}": v for k, v in n.items()}, "_index": idx}


def join_possessions(res, idx) -> list:
    """Each possession row's lender and company borrower joined to the register (possessions.join), and the
    names it may show decided: a company by name; a person never; a lender's name that may run on from the
    borrowers' only as the end of it the register holds; a name the register does not hold and that joins
    two names with "and" not shown, since it may be a person's beside a company's. Without the register no
    name that could be a person's is shown. Returns the private rows: (key, mortgagee, mortgagor, property,
    registration), a name only where the published row does not show it."""
    out = []
    for r in res.possessions:
        f, p = r["filed"], r.pop("_private")
        on, year = f["entered_on"] or f["dated_on"] or f["published_on"], int(f["notice"][:4])
        hidden = {}
        for role, party in (("mortgagee", p["mortgagee"]), ("mortgagor", p["mortgagor"])):
            if party is None:
                continue
            if party.kind != "company":
                hidden[role] = party.name
                continue
            glued = p["glued"] and role == "mortgagee"
            if idx is None:
                name, k, how = (None if glued else party.name), None, None
            else:
                name, k, how = possessions.join(idx, party, on, year, glued)
                if how in register.UNMATCHED:
                    res.set_aside.append((f"{r['document']}/{r['place']} {role}", "register", f"the companies register: {how}"))
            if name and k is None and re.search(r"\s(?:and|&)\s", name) and not possessions.firm(name):
                name = None
            if name is None:
                hidden[role] = party.name
            f[role], f[f"{role}_register_key"], f[f"{role}_register_match"] = name, k, how
        if hidden or p["property"] or p["registration"]:
            out.append((r["key"], hidden.get("mortgagee"), hidden.get("mortgagor"), p["property"], p["registration"]))
    return out


def load(conn, schema: str, log=print) -> int:
    """The export landed and read, under `schema`. Returns the notice count."""
    started = jobrun.now()
    landed, aside = capture.copy_all(conn)
    export = next((ref.sha256, name) for kind, ref, name, at in landed if kind == "notices")
    counts = build(conn, schema, export, aside)
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("gazette: " + detail)
    jobrun.record("qv4-gazette-load", True, detail, started, counts)
    return counts["notices"]


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        for t in PRIVATE_TABLES:
            conn.execute(f"INSERT INTO {PRIVATE}.{t} SELECT * FROM {private_of(staging)}.{t}")
        conn.execute(sql("publish.sql"))
