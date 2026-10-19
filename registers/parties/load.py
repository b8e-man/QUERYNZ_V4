"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Capture, read the page and the notices, build the lifecycle, insert. Items
in equal items out plus items set aside (read.py says how).
"""
import os

from support import jobrun
from support.docstore.landing import read_bytes
from registers.parties import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "parties"
PRIVATE = "parties_private"
TABLES = ("registrations", "names", "events", "files", "set_aside")
COLUMNS = {
    "registrations": ("key", "document", "page", "place", "name", "first_name", "registered_on",
                      "notice_registered_on", "registered_by", "registered_basis", "cancelled_on", "status",
                      "on_register", "register_seen_on", "off_register_by", "page_basis", "window", "abbreviation",
                      "abbreviation_on_ballot", "components", "logo_registered_on", "statement_deadline", "audit",
                      "website", "rules_title", "rules_href", "secretary", "register_document", "register_place",
                      "cancelled_document", "cancelled_place", "read_from", "reader", "profile", "profile_version",
                      "loaded_at"),
    "names": ("key", "party", "name", "name_key", "kind", "from_on", "to_on", "basis", "document", "page", "place",
              "read_from", "reader", "profile", "profile_version", "loaded_at"),
    "events": ("key", "notice", "published_on", "decided_on", "kind", "party_label", "new_name", "abbreviation",
               "old_abbreviation", "ref", "party", "url", "title", "clause", "source_note", "document", "page", "place",
               "read_from", "reader", "profile", "profile_version", "loaded_at"),
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.parties_t`."""
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
    conn.execute(f"DROP TABLE IF EXISTS {table(private_of(schema), 'secretary_contacts', shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _insert(conn, name: str, cols: tuple, row: dict) -> None:
    flat = {**row, **row.get("filed", {})}
    conn.execute(f"INSERT INTO {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) "
                 f"VALUES ({', '.join(['%s'] * len(cols))})", tuple(flat.get(c) for c in cols))


def build(conn, schema: str, page: tuple, export: tuple, others: list, aside: list, shared: bool = False) -> dict:
    """page: (sha256, captured on, name); export: (sha256, name); others:
    [(sha256, name, kind)] held and not read; aside: [(item, why)] from
    capture. Wipes and fills `schema`; returns the counts."""
    create_tables(conn, schema, shared)
    for item, why in aside:
        conn.execute(f"INSERT INTO {table(schema, 'set_aside', shared)} (item, stage, reason) VALUES (%s, 'capture', %s)",
                     (item, why))
    res = read.read(read_bytes(page[0]), page[0], page[1], read_bytes(export[0]), export[0])
    for item, stage, reason in res.set_aside:
        conn.execute(f"INSERT INTO {table(schema, 'set_aside', shared)} (item, stage, reason) VALUES (%s, %s, %s)",
                     (item, stage, reason))
    for t, rows in (("registrations", res.registrations), ("names", res.names), ("events", res.events)):
        for row in rows:
            _insert(conn, table(schema, t, shared), COLUMNS[t], row)
    for key, contact in res.contacts:
        conn.execute(f"INSERT INTO {table(private_of(schema), 'secretary_contacts', shared)} (key, contact) VALUES (%s, %s)",
                     (key, contact))
    files = table(schema, "files", shared)
    conn.execute(f"INSERT INTO {files} VALUES (%s, %s, 'register', 'read')", (page[0], page[2]))
    conn.execute(f"INSERT INTO {files} VALUES (%s, %s, 'notices', 'read')", (export[0], export[1]))
    for sha, name, kind in others:
        conn.execute(f"INSERT INTO {files} VALUES (%s, %s, %s, 'held, not read') ON CONFLICT DO NOTHING", (sha, name, kind))
    return {**res.counts, "not_held": len(aside)}


def load(conn, schema: str, log=print) -> int:
    """The two pages copied by hash, the export landed, everything read,
    under `schema`. Returns the registration count."""
    started = jobrun.now()
    landed, aside = capture.copy_all(conn)
    page = next((ref.sha256, at[:10], name) for kind, ref, name, at in landed if kind == "register")
    export = next((ref.sha256, name) for kind, ref, name, at in landed if kind == "notices")
    others = [(ref.sha256, name, kind) for kind, ref, name, at in landed if kind == "applications"]
    counts = build(conn, schema, page, export, others, aside)
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("parties: " + detail)
    jobrun.record("qv4-parties-load", True, detail, started, counts)
    return counts["registrations"]


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        conn.execute(f"INSERT INTO {PRIVATE}.secretary_contacts SELECT * FROM {private_of(staging)}.secretary_contacts")
        conn.execute(sql("publish.sql"))
