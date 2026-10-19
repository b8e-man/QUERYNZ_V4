"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Land the export (never run it: capture.py was run once), read it, copy the
rows in. Items in equal items out plus items set aside (read.py says how).
"""
import os

from support import jobrun
from support.docstore.landing import read_bytes
from registers.gazette import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "gazette"
PRIVATE = "gazette_private"
TABLES = ("notices", "celebrants", "prohibitions", "liquidations", "liquidators", "files", "set_aside")
PRIVATE_TABLES = ("celebrant_addresses", "prohibition_addresses")
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
                     "appointed_on", "appointed_at", "date_basis", "dated_on", "corrigendum", "liquidators", "ordinal",
                     "document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at"),
    "liquidators": ("key", "notice", "published_on", "name", "role", "named_in_body", "companies", "ordinal", "document",
                    "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at"),
}


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
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [(i, "capture", w) for i, w in aside] + list(res.set_aside))
    for t, rows in (("notices", res.notices), ("celebrants", res.celebrants), ("prohibitions", res.prohibitions),
                    ("liquidations", res.liquidations), ("liquidators", res.liquidators)):
        _copy(conn, table(schema, t, shared), COLUMNS[t], _flat(COLUMNS[t], rows))
    _copy(conn, table(private_of(schema), "celebrant_addresses", shared), ("key", "address"), res.addresses)
    _copy(conn, table(private_of(schema), "prohibition_addresses", shared), ("key", "address", "formerly"),
          res.prohibition_addresses)
    conn.execute(f"INSERT INTO {table(schema, 'files', shared)} VALUES (%s, %s, 'notices', 'read')", export)
    return {**res.counts, "not_held": len(aside)}


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
