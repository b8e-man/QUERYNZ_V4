"""Loading (plan 1b.7, 1.11). The merge gate's staging step calls `load`
to build this lane's tables under a staging schema of the real database,
and `publish` to move the rows into the lane's own tables in one
transaction and refresh the published view. `fill` in sample.py uses the
same pieces for the sample.

Capture, read, insert. The run record goes to support.jobrun; every
document the lane could not take to a row is a line in `set_aside`.
"""
import os

from support import jobrun
from support import reader as rd
from support.docstore.landing import read_bytes
from registers.party_returns import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "party_returns"
TABLES = ("returns", "set_aside")
COLUMNS = ("key", "document", "page", "place", "party", "party_label", "party_basis", "year", "year_from", "declared_total",
           "part_a", "part_c", "part_d", "part_f", "part_g", "declared_parts", "total_check", "read_from", "reader",
           "profile", "profile_version", "loaded_at")


def sql(name: str, schema: str = SCHEMA) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read().replace(f"{SCHEMA}.", f"{schema}.")


def create_tables(conn, schema: str) -> None:
    conn.execute(sql("tables.sql", schema))


def wipe(conn, schema: str) -> None:
    for t in TABLES:
        conn.execute(f"DELETE FROM {schema}.{t}")


def insert(conn, schema: str, result: read.Result) -> int:
    for stage, reason in result.set_aside:
        conn.execute(f"INSERT INTO {schema}.set_aside (document, stage, reason) VALUES (%s, %s, %s)",
                     (result.document, stage, reason))
    if not result.row:
        return 0
    r = {**result.row, **result.row["filed"]}
    conn.execute(f"INSERT INTO {schema}.returns ({', '.join(COLUMNS)}) VALUES ({', '.join(['%s'] * len(COLUMNS))}) "
                 "ON CONFLICT (key) DO NOTHING", tuple(r[c] for c in COLUMNS))
    return 1


def load(conn, schema: str, log=print) -> int:
    """Every candidate file of the old folder: landed by hash, read, and a
    row or a set-aside line under `schema`. Returns the row count."""
    started = jobrun.now()
    create_tables(conn, schema)
    wipe(conn, schema)
    store = rd.Store()
    rows = aside = 0
    landed = capture.copy_all(conn)
    for ref, path, new in landed:
        n = insert(conn, schema, read.read_return(read_bytes(ref), ref.sha256, store))
        rows += n
        aside += 0 if n else 1
    detail = f"{len(landed)} documents: {rows} rows, {aside} set aside, into {schema}"
    log("party_returns: " + detail)
    jobrun.record("qv4-party-returns-load", True, detail, started, {"documents": len(landed), "rows": rows, "set_aside": aside})
    return rows


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the view refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        wipe(conn, SCHEMA)
        for t in TABLES:
            cols = ", ".join(COLUMNS) if t == "returns" else "document, stage, reason, at"
            conn.execute(f"INSERT INTO {SCHEMA}.{t} ({cols}) SELECT {cols} FROM {staging}.{t}")
        conn.execute(sql("publish.sql"))
