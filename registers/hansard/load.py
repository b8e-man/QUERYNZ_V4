"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Land the export (never run it: capture.py was run once), read it, copy the
rows in. Items in equal items out plus items set aside (read.py says how).
`index_pages` is made empty: hansard-2 fills it from the MCP's index.
"""
import os

from support import jobrun
from support.docstore.landing import read_bytes
from registers.hansard import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "hansard"
PRIVATE = "hansard_private"
JOB = "qv4-hansard-load"
TABLES = ("sittings", "sections", "turns", "members", "old_speeches", "index_pages", "files", "set_aside")
CITE = ("source_note", "document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "sittings": ("key", "sitting_on", "parliament", "volume", "progress", "url", "sections", "turns", "attributed",
                 "unattributed", "speakers", "old_sections", "old_speeches", "old_unattributed", "old_speakers",
                 "old_derived_at") + CITE,
    "sections": ("key", "sitting_on", "section_index", "parliament", "volume", "proceeding", "subject", "bill_title",
                 "bill_id", "progress", "old_status", "text", "chars", "text_sha1", "turns", "url", "captured_at",
                 "old_id") + CITE,
    "turns": ("key", "section", "sitting_on", "section_index", "ordinal", "label", "member_id", "roster_name", "role",
              "in_roster") + CITE,
    "members": ("key", "display_name", "sort_name", "parliaments") + CITE,
    "old_speeches": ("key", "sitting_on", "section_index", "member_id", "speaker_label", "speaker_name",
                     "speech_count", "retired_at", "document"),
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.hansard_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    text = text.replace(f"CREATE SCHEMA IF NOT EXISTS {PRIVATE};", f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)};")
    text = text.replace(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};", f"CREATE SCHEMA IF NOT EXISTS {schema};")
    return text.replace(f"{SCHEMA}.", f"{schema}.{pre}")


def create_tables(conn, schema: str, shared: bool = False) -> None:
    """The lane's tables as tables.sql has them now, made again on every
    build: every row is rebuilt from documents."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> None:
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))


def build(conn, schema: str, export: tuple, aside: list, only=None, shared: bool = False) -> dict:
    """export: (sha256, name); aside: [(item, why)] from capture; only: the
    sitting days to read (the sample's), None for all. Wipes and fills
    `schema`; returns the counts. A reading that is not balanced raises."""
    create_tables(conn, schema, shared)
    res = read.read(read_bytes(export[0]), export[0], only=only)
    if not read.balanced(res):
        raise AssertionError(f"hansard: items in {res.counts['lines']} do not equal rows out plus set aside: {res.counts}")
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [{"item": i, "stage": "capture", "reason": w} for i, w in aside]
          + [{"item": i, "stage": s, "reason": w} for i, s, w in res.set_aside])
    for t in ("sittings", "sections", "turns", "members", "old_speeches"):
        _copy(conn, table(schema, t, shared), COLUMNS[t], getattr(res, t))
    conn.execute(f"INSERT INTO {table(schema, 'files', shared)} VALUES (%s, %s, 'hansard', 'read')", export)
    return {**res.counts, "not_held": len(aside)}


def load(conn, schema: str, log=print) -> int:
    """The export landed and read, under `schema`. Returns the section count."""
    started = jobrun.now()
    landed, aside = capture.copy_all(conn)
    export = next((ref.sha256, name) for kind, ref, name, at in landed if kind == "hansard")
    counts = build(conn, schema, export, aside)
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("hansard: " + detail)
    jobrun.record(JOB, True, detail, started, counts)
    return counts["sections"]


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane). The MCP's
    index rows are hansard-2's; once it fills them they are carried over too."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        conn.execute(sql("publish.sql"))
