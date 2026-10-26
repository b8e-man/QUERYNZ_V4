"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views; `qv4-beehive-load` runs the same after
each night's pull. `fill` in sample.py uses the same pieces.

Every beehive record the pull has taken (support/mcpsource's arrivals) is
read by its hash from the document store. Items in (the documents) equal
releases plus older versions plus items set aside; the pull's own catch
lines come across as set-aside lines at stage `pull`.

    python -m registers.beehive.load --database querynz_v4_sample --schema scratch_mcp_1_beehive --mcp-schema scratch_mcp_1_pull
"""
import argparse
import os
import sys

from support import jobrun
from support.docstore.landing import read_bytes
from registers.beehive import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "beehive"
PRIVATE = "beehive_private"
JOB = "qv4-beehive-load"
TABLES = ("releases", "release_ministers", "release_portfolios", "release_topics", "release_quotes", "files", "set_aside")
PRIVATE_TABLES = ("texts",)
COLUMNS = {
    "releases": ("key", "url", "type", "final_url", "http_status", "kind", "captured_sha256", "captured_at",
                 "capture_status", "provider_file", "provider_path", "model", "extracted_at", "annotation_fields",
                 "annotation_generator", "annotation_created_at", "updated_at", "title", "published_at", "published_on",
                 "word_count", "ministers", "portfolios", "topics", "quotes", "fields_unread", "versions", "seq",
                 "origin", "source_note", "document", "page", "place", "read_from", "reader", "profile", "profile_version",
                 "loaded_at"),
    "release_ministers": ("key", "release", "ordinal", "name", "slug"),
    "release_portfolios": ("key", "release", "ordinal", "portfolio"),
    "release_topics": ("key", "release", "ordinal", "topic", "model_made", "made_by"),
    "release_quotes": ("key", "release", "ordinal", "quote", "speaker", "model_made", "made_by"),
}
STAMP = ("document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at")
for _t in ("release_ministers", "release_portfolios", "release_topics", "release_quotes"):
    COLUMNS[_t] += STAMP


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.beehive_t`."""
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


def build(conn, schema: str, items: list, caught: list = (), shared: bool = False, get_bytes=read_bytes,
          old=None) -> dict:
    """items: [(sha256, seq, record id)]; caught: the pull's catch lines
    [(seq, stage, reason)]; old: the old estate's export (sha256, name), or
    None. Wipes and fills `schema`; returns the counts."""
    create_tables(conn, schema, shared)
    res = read.read(items, get_bytes)
    if old:
        read.read_old(get_bytes(old[0]), old[0], {r["key"] for r in res.releases}, res)
        res.files.append((old[0], None, None, "read"))
    for t, rows in (("releases", res.releases), ("release_ministers", res.ministers),
                    ("release_portfolios", res.portfolios), ("release_topics", res.topics),
                    ("release_quotes", res.quotes)):
        _copy(conn, table(schema, t, shared), COLUMNS[t], (tuple(r[c] for c in COLUMNS[t]) for r in rows))
    _copy(conn, table(schema, "files", shared), ("sha256", "record_id", "seq", "status"), res.files)
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [(f"beehive seq {s}", "pull", f"{st}: {why}") for s, st, why in caught] + list(res.set_aside))
    _copy(conn, table(private_of(schema), "texts", shared), ("key", "body_text", "text"), res.texts)
    return {**res.counts, "pull caught": len(caught)}


def load(conn, schema: str, log=print, mcp_schema: str = capture.MCP_SCHEMA) -> int:
    """Every beehive document the pull landed, read under `schema`. Returns the release count."""
    started = jobrun.now()
    counts = build(conn, schema, capture.arrivals(conn, mcp_schema), capture.caught(conn, mcp_schema),
                   old=capture.old_export(conn))
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("beehive: " + detail)
    jobrun.record(JOB, True, detail, started, counts)
    return counts["releases"]


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
    """The job `qv4-beehive-load`: build under a staging schema, publish. With
    --schema, a session's proof: build there and publish nothing."""
    ap = argparse.ArgumentParser(prog="registers.beehive.load")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", help="build here and stop (a scratch proof); default: stage and publish")
    ap.add_argument("--mcp-schema", default=capture.MCP_SCHEMA)
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '600s'")
        if a.schema:
            started = jobrun.now()
            counts = build(conn, a.schema, capture.arrivals(conn, a.mcp_schema), capture.caught(conn, a.mcp_schema),
                           old=capture.old_export(conn))
            conn.commit()
            print("beehive: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {a.database}.{a.schema}")
            return 0
        staging = "staging_beehive_load"
        load(conn, staging, mcp_schema=a.mcp_schema)
        conn.commit()
        publish(conn, staging)
        conn.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
