"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views; `qv4-ministers-diaries-load` runs the same
after each night's pull. `fill` in sample.py uses the same pieces.

Every diary record the pull has taken (support/mcpsource's arrivals for the
corpus `parliament-diaries`) is read by its hash from the document store.
Items in (the documents) equal entries plus older versions plus items set
aside; the pull's own catch lines come across as set-aside lines at stage
`pull`.

    python -m registers.ministers_diaries.load --database querynz_v4_sample --schema scratch_diaries_2_build --mcp-schema scratch_mcp_1_pull2
"""
import argparse
import os
import sys

from support import jobrun
from support.docstore.landing import read_bytes
from registers.ministers_diaries import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "ministers_diaries"
PRIVATE = "ministers_diaries_private"
JOB = "qv4-ministers-diaries-load"
TABLES = ("releases", "entries", "files", "set_aside")
PRIVATE_TABLES = ("entries",)
STAMP = ("document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at")
COLUMNS = {
    "releases": ("key", "source_url", "pdf_url", "file_name", "upload_folder", "minister", "ministers_named",
                 "portfolios", "month", "month_named", "entries_month", "months", "first_on", "last_on", "entries",
                 "withheld_entries", "locations_held", "source_note") + STAMP,
    "entries": ("key", "release", "rowid", "minister", "portfolio", "entry_on", "date_as_released", "year", "time",
                "meeting", "attendees", "location", "location_held", "addresses_masked", "withheld", "collected_at",
                "updated_at", "text_words", "fields_unread", "versions", "seq", "source_note") + STAMP,
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.ministers_diaries_t`."""
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


def build(conn, schema: str, items: list, caught: list = (), shared: bool = False, get_bytes=read_bytes) -> dict:
    """items: [(sha256, seq, record id)]; caught: the pull's catch lines
    [(seq, stage, reason)]. Wipes and fills `schema`; returns the counts."""
    create_tables(conn, schema, shared)
    res = read.read(items, get_bytes)
    for t, rows in (("releases", res.releases), ("entries", res.entries)):
        _copy(conn, table(schema, t, shared), COLUMNS[t], (tuple(r[c] for c in COLUMNS[t]) for r in rows))
    _copy(conn, table(schema, "files", shared), ("sha256", "record_id", "seq", "status"), res.files)
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [(f"{capture.CORPUS} seq {s}", "pull", f"{st}: {why}") for s, st, why in caught] + list(res.set_aside))
    _copy(conn, table(private_of(schema), "entries", shared), ("key", "location", "meeting", "attendees", "text"),
          res.private)
    return {**res.counts, "pull caught": len(caught)}


def load(conn, schema: str, log=print, mcp_schema: str = capture.MCP_SCHEMA) -> int:
    """Every diary document the pull landed, read under `schema`. Returns the entry count."""
    started = jobrun.now()
    counts = build(conn, schema, capture.arrivals(conn, mcp_schema), capture.caught(conn, mcp_schema))
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("ministers_diaries: " + detail)
    jobrun.record(JOB, True, detail, started, counts)
    return counts["entries"]


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


def main(argv=None) -> int:
    """The job `qv4-ministers-diaries-load`: build under a staging schema,
    publish. With --schema, a session's proof: build there and publish nothing."""
    ap = argparse.ArgumentParser(prog="registers.ministers_diaries.load")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", help="build here and stop (a scratch proof); default: stage and publish")
    ap.add_argument("--mcp-schema", default=capture.MCP_SCHEMA)
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '600s'")
        if a.schema:
            counts = build(conn, a.schema, capture.arrivals(conn, a.mcp_schema), capture.caught(conn, a.mcp_schema))
            conn.commit()
            print("ministers_diaries: " + ", ".join(f"{k} {v}" for k, v in counts.items())
                  + f", into {a.database}.{a.schema}")
            return 0
        staging = "staging_ministers_diaries_load"
        load(conn, staging, mcp_schema=a.mcp_schema)
        conn.commit()
        publish(conn, staging)
        conn.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
