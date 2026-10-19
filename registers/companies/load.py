"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Land the four export parts (never run the export: capture.py was run once),
read each, copy the rows in. Items in equal items out plus items set aside
(read.py says how). About 5.6 million rows: the entities first, so a role
whose company the package does not name is counted.
"""
import os

from support import jobrun
from support.docstore.landing import read_bytes
from registers.companies import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "companies"
PRIVATE = "companies_private"
TABLES = ("entities", "entity_states", "directors", "shareholders", "registered_offices", "files", "set_aside")
PRIVATE_TABLES = ("residential_addresses",)
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at")
COLUMNS = {
    "entities": ("key", "register", "nzbn", "number", "name", "entity_type", "status", "registered_on", "removed_on",
                 "in_latest", "first_file", "last_file", "extra", "old_id", "source_note") + _CITE,
    "entity_states": ("key", "entity_key", "file", "name", "entity_type", "status", "registered_on",
                      "removed_on") + _CITE,
    "directors": ("key", "entity_key", "nzbn", "company_number", "first_name", "middle_names", "last_name",
                  "full_name", "role_type", "appointed_on", "ended_on", "in_latest", "first_file", "last_file",
                  "suppressed", "old_id", "source_note") + _CITE,
    "shareholders": ("key", "entity_key", "nzbn", "company_number", "shareholder_type", "name", "holder_nzbn",
                     "shares", "allocation_status", "in_latest", "first_file", "last_file", "suppressed", "old_id",
                     "source_note") + _CITE,
    "registered_offices": ("key", "entity_key", "register", "started_on", "care_of", "line_1", "line_2", "line_3",
                           "line_4", "postcode", "country", "in_latest", "last_file", "source_note") + _CITE,
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.companies_t`."""
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


def build(conn, schema: str, exports: list, aside: list, only=None, shared: bool = False) -> dict:
    """exports: [(part, sha256, name)]; aside: [(item, why)] from capture;
    only: the NZBNs and register numbers to read (the sample's), None for
    all. Wipes and fills `schema`; returns the counts."""
    create_tables(conn, schema, shared)
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason", "count"),
          [(i, "capture", w, 1) for i, w in aside])
    counts, entities = {"not_held": len(aside)}, None
    for part, sha, name in sorted(exports, key=lambda e: capture.PARTS.index(e[0])):
        res = read.read(part, read_bytes(sha), sha, only=only, entities=entities)
        if part == "entities":
            entities = {r["key"] for r in res.rows["entities"]}
        for t in read.TABLE_OF[part]:
            _copy(conn, table(schema, t, shared), COLUMNS[t], _flat(COLUMNS[t], res.rows[t]))
        _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason", "count"), res.set_aside)
        conn.execute(f"INSERT INTO {table(schema, 'files', shared)} VALUES (%s, %s, %s, 'read')", (sha, name, part))
        counts.update({f"{part}.{k}" if k in ("lines", "set_aside", "set_aside_lines", "no_entity") else k: v
                       for k, v in res.counts.items()})
        del res
    return counts


def load(conn, schema: str, log=print) -> int:
    """The four parts landed and read, under `schema`. Returns the entity count."""
    started = jobrun.now()
    landed, aside = capture.copy_all(conn)
    counts = build(conn, schema, [(part, ref.sha256, name) for part, ref, name, at in landed], aside)
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("companies: " + detail)
    jobrun.record("qv4-companies-load", True, detail, started, counts)
    return counts["entities"]


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
