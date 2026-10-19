"""Loading (plan 1b.7, 1.11). The merge gate's staging step calls `load`
to build this lane's tables under a staging schema of the real database,
and `publish` to move the rows into the lane's own tables in one
transaction and refresh the published views. `fill` in sample.py uses the
same pieces for the sample.

Capture, read, insert. The run record goes to support.jobrun; every
document the lane could not take to a row, and every part of a row it
could not publish whole, is a line in `set_aside`. A donor's or lender's
address goes into the private twin of the schema it is loaded into
(`<schema>_private`, never granted to a reader), never into a published
table (hard limit 15).
"""
import os

from support import jobrun
from support import reader as rd
from support.docstore.landing import copy_from_old, read_bytes
from registers.party_returns import amendments, capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "party_returns"
PRIVATE = "party_returns_private"
TABLES = ("returns", "set_aside", "donors", "loans", "amendments")
PRIVATE_TABLES = ("addresses",)
COLUMNS = ("key", "document", "page", "place", "party", "party_label", "party_basis", "year", "year_from", "declared_total",
           "part_a", "part_c", "part_d", "part_f", "part_g", "declared_parts", "total_check", "read_from", "reader",
           "profile", "profile_version", "loaded_at", "loans_h", "loans_i", "loans_total", "donors_check", "loans_check")
DONOR_COLUMNS = ("key", "return_key", "document", "page", "ordinal", "n", "donor", "amount", "dates", "contributions",
                 "paired_by", "read_from", "reader", "profile", "profile_version", "loaded_at")
LOAN_COLUMNS = ("key", "return_key", "document", "page", "ordinal", "lender", "amount", "dates", "interest", "read_from",
                "reader", "profile", "profile_version", "loaded_at")
AMENDMENT_COLUMNS = ("document", "replaced_by", "party_label", "year", "stated", "listing")
COLUMNS_OF = {"returns": COLUMNS, "donors": DONOR_COLUMNS, "loans": LOAN_COLUMNS, "amendments": AMENDMENT_COLUMNS,
              "set_aside": ("document", "stage", "reason", "at"), "addresses": ("key", "document", "address", "cell")}


def private_of(schema: str) -> str:
    """The private twin's name: `<schema>_private`, cut to fit a schema name (63)."""
    return PRIVATE if schema == SCHEMA else f"{schema[:55]}_private"


def sql(name: str, schema: str = SCHEMA) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    return text.replace(f"{PRIVATE}.", f"{private_of(schema)}.").replace(f"{SCHEMA}.", f"{schema}.")


def create_tables(conn, schema: str) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    conn.execute(sql("tables.sql", schema))
    conn.execute(sql("private.sql", schema))


def wipe(conn, schema: str) -> None:
    for t in TABLES:
        conn.execute(f"DELETE FROM {schema}.{t}")
    for t in PRIVATE_TABLES:
        conn.execute(f"DELETE FROM {private_of(schema)}.{t}")


def _insert(conn, table: str, columns: tuple, row: dict) -> None:
    conn.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))}) "
                 "ON CONFLICT DO NOTHING", tuple(row[c] for c in columns))


def insert(conn, schema: str, result: read.Result) -> int:
    for stage, reason in result.set_aside:
        conn.execute(f"INSERT INTO {schema}.set_aside (document, stage, reason) VALUES (%s, %s, %s)",
                     (result.document, stage, reason))
    if not result.row:
        return 0
    r = {**result.row, **result.row["filed"]}
    _insert(conn, f"{schema}.returns", COLUMNS, r)
    for d in result.donors:
        _insert(conn, f"{schema}.donors", DONOR_COLUMNS,
                {**d, "return_key": r["key"], "donor": d["name"], "contributions": d["yes_no"] or None})
        _insert(conn, f"{private_of(schema)}.addresses", COLUMNS_OF["addresses"], d)
    for x in result.loans:
        _insert(conn, f"{schema}.loans", LOAN_COLUMNS, {**x, "return_key": r["key"], "lender": x["name"]})
        _insert(conn, f"{private_of(schema)}.addresses", COLUMNS_OF["addresses"], x)
    return 1


def insert_amendments(conn, schema: str, index: dict = None) -> int:
    """The Commission's listing landed by hash, and each replacement it
    states written beside the returns; an amended return it lists that the
    lane does not hold is a catch-log line against the listing."""
    path = amendments.listing_file()
    ref, _ = copy_from_old(path, capture.SOURCE, conn)
    with open(path, encoding="utf-8", errors="replace") as f:
        groups = amendments.statements(f.read())
    pairs, unheld = amendments.replacements(groups, amendments.held_by_name(index if index is not None else capture.old_index()))
    for old, new, g, stated in pairs:
        _insert(conn, f"{schema}.amendments", AMENDMENT_COLUMNS,
                {"document": old, "replaced_by": new, "party_label": g.party, "year": g.year, "stated": stated,
                 "listing": ref.sha256})
    for line in unheld:
        conn.execute(f"INSERT INTO {schema}.set_aside (document, stage, reason) VALUES (%s, 'amendment', %s)",
                     (ref.sha256, line))
    return len(pairs)


def load(conn, schema: str, log=print) -> int:
    """Every candidate file of the old folder: landed by hash, read, and a
    row or a set-aside line under `schema`. Returns the row count."""
    started = jobrun.now()
    create_tables(conn, schema)
    wipe(conn, schema)
    store = rd.Store()
    rows = aside = donors = loans = 0
    landed = capture.copy_all(conn)
    for ref, path, new in landed:
        result = read.read_return(read_bytes(ref), ref.sha256, store)
        n = insert(conn, schema, result)
        rows += n
        aside += 0 if n else 1
        donors += len(result.donors)
        loans += len(result.loans)
    replaced = insert_amendments(conn, schema, {ref.sha256: path for ref, path, _ in landed})
    detail = (f"{len(landed)} documents: {rows} rows, {aside} set aside; {donors} donor rows, {loans} loan rows; "
              f"{replaced} returns replaced by an amendment; into {schema}")
    log("party_returns: " + detail)
    jobrun.record("qv4-party-returns-load", True, detail, started,
                  {"documents": len(landed), "rows": rows, "set_aside": aside, "donors": donors, "loans": loans,
                   "replaced": replaced})
    return rows


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        wipe(conn, SCHEMA)
        for t in TABLES:
            cols = ", ".join(COLUMNS_OF[t])
            conn.execute(f"INSERT INTO {SCHEMA}.{t} ({cols}) SELECT {cols} FROM {staging}.{t}")
        for t in PRIVATE_TABLES:
            cols = ", ".join(COLUMNS_OF[t])
            conn.execute(f"INSERT INTO {PRIVATE}.{t} ({cols}) SELECT {cols} FROM {private_of(staging)}.{t}")
        conn.execute(sql("publish.sql"))
