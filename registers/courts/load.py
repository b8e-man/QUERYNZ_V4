"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's reading under a staging schema of the real database, and
`publish` to move it into the lane's own tables in one transaction and
refresh the published views; `qv4-courts-load` runs the same nightly after
the pull. `fill` in sample.py uses the same pieces.

The listing is the MCP's courts corpus (capture.records: one entry per
record, the version the pull saw last); every file is read from the store
by hash (read.py); the stored model readings are replayed; the rows are
copied in. The ledger of suppression orders is the lane's own record and is
never wiped: a staging build reads the orders from the lane's real schema,
so an order recorded today binds the next build.

    python -m registers.courts.load [--database querynz_v4] [--schema staging_courts_load] [--publish]
"""
import argparse
import os
import sys

from support import jobrun
from registers.courts import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "courts"
PRIVATE = "courts_private"
JOB = "qv4-courts-load"
#: the reading's tables, rebuilt at every load
TABLES = ("documents", "cases", "case_links", "judgments", "judgment_parties", "paragraphs", "people", "set_aside")
PRIVATE_TABLES = ("withheld_names",)
#: the lane's record, never wiped
RECORDS = ("suppression_orders",)
STAMP = ("document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at")
COLUMNS = {
    "documents": ("key", "record", "seq", "kind", "case_slug", "url", "content_type", "fetched_at", "document", "state",
                  "profile", "profile_version", "outcome", "pages", "read_from", "text_chars", "pieces", "citation", "case_numbers",
                  "dated", "summary", "model", "model_reader", "loaded_at"),
    "cases": ("key", "case_slug", "url", "case_name", "citation", "case_numbers", "court", "summary", "result", "judges",
              "date_of_judgment", "date_of_hearing", "suppression", "withheld", "links") + STAMP,
    "case_links": ("key", "case", "position", "section", "label", "href", "linked_document", "document", "page", "place"),
    "judgments": ("key", "citation", "court", "court_name", "registry", "case_numbers", "judgment_date", "date_basis",
                  "hearing", "judges", "heading", "caption_shape", "outcome", "paragraphs", "parties", "suppression",
                  "suppression_kinds", "withheld", "status", "missing", "unrecognised", "notes", "case_slug", "source",
                  "source_url", "source_note") + STAMP,
    "judgment_parties": ("key", "judgment", "citation", "position", "block", "role", "name", "withheld", "anonymised",
                         "crown", "confidence", "capacity") + STAMP,
    "people": ("key", "name", "kind", "role", "role_text", "for_party", "citation", "case_slug", "document_kind", "dated",
               "withheld", "document", "page", "place", "read_from", "reader", "model", "profile", "profile_version",
               "loaded_at"),
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.courts_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    return text.replace(f"{PRIVATE}.", f"{private_of(schema)}.{pre}").replace(f"{SCHEMA}.", f"{schema}.{pre}")


def capture_tables_sql(schema: str = SCHEMA, shared: bool = False) -> str:
    return f"CREATE SCHEMA IF NOT EXISTS {schema};\nCREATE SCHEMA IF NOT EXISTS {private_of(schema)};\n" + \
        sql("tables.sql", schema, shared)


def create_tables(conn, schema: str, shared: bool = False) -> None:
    """The reading's tables as tables.sql has them now, made again on every
    build (each dropped and created); the record is created if absent and
    never dropped."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    remove = "DROP TABLE IF EXISTS {} CASCADE"
    for t in TABLES:
        conn.execute(remove.format(table(schema, t, shared)))
    for t in PRIVATE_TABLES:
        conn.execute(remove.format(table(private_of(schema), t, shared)))
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> None:
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(row)


def orders(conn, schema: str = SCHEMA, shared: bool = False) -> list:
    """The ledger's orders, oldest first."""
    cur = conn.execute(f"SELECT citation, document, reason FROM {table(schema, 'suppression_orders', shared)} ORDER BY order_id")
    return [{"citation": r[0], "document": r[1], "reason": r[2]} for r in cur]


def build(conn, schema: str, entries: list, caught: list, ledger: list, shared: bool = False, store=None,
          old_listing: list = None) -> dict:
    """entries: the corpus's records (capture.records); caught: the pull's
    catch lines; ledger: the orders. Wipes and fills `schema`; returns the
    counts."""
    create_tables(conn, schema, shared)
    res = read.read(entries, ledger, store=store)
    gap = capture.old_listing_gap(old_listing if old_listing is not None else capture.old_listing(), entries)
    aside = list(res.set_aside) + [(rid, "pull", f"the pull's catch line at seq {seq}, stage {stage}: {reason}")
                                   for rid, seq, stage, reason in caught if rid] + list(gap)
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"), aside)
    for t, rows in (("documents", res.documents), ("cases", res.cases), ("case_links", res.case_links),
                    ("judgments", res.judgments), ("judgment_parties", res.parties), ("people", res.people)):
        _copy(conn, table(schema, t, shared), COLUMNS[t], (tuple(r.get(c) for c in COLUMNS[t]) for r in rows))
    _copy(conn, table(schema, "paragraphs", shared), ("judgment", "number", "page", "document"), res.paragraphs)
    _copy(conn, table(private_of(schema), "withheld_names", shared), ("key", "name", "capacity"), res.withheld)
    return {**res.counts, "pull_caught": len(caught), "old_listing_gap": len(gap)}


def load(conn, schema: str, log=print, mcp_schema: str = capture.MCP_SCHEMA) -> int:
    """The corpus's records read from the store under `schema`. Returns the
    count of documents read."""
    started = jobrun.now()
    conn.execute(capture_tables_sql(SCHEMA))           # the record lives in the lane's own schema
    entries = capture.records(conn, mcp_schema)
    counts = build(conn, schema, entries, capture.caught(conn, mcp_schema), orders(conn))
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("courts: " + detail)
    jobrun.record(JOB, True, detail, started, counts)
    return counts["read"]


def publish(conn, staging: str) -> None:
    """The lane's reading wiped and refilled from the staged one, and the
    views refreshed, in one transaction (contract: the lane). The record is
    not touched."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        for t in PRIVATE_TABLES:
            conn.execute(f"INSERT INTO {PRIVATE}.{t} SELECT * FROM {private_of(staging)}.{t}")
        # an order recorded between the staging build and now still binds
        from registers.courts import suppress
        suppress.apply_all(conn, SCHEMA)
        conn.execute(sql("publish.sql"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.courts.load", description="Build the courts lane from the MCP's corpus.")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default="staging_courts_load", help="the staging schema to build into")
    ap.add_argument("--mcp-schema", default=capture.MCP_SCHEMA)
    ap.add_argument("--publish", action="store_true", help="after a green check, move the staged reading into place")
    a = ap.parse_args(argv)
    from support import db
    from registers.courts import check
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '600s'")
        load(conn, a.schema, mcp_schema=a.mcp_schema)
        conn.commit()
        out = check.account(conn, a.schema)
        for f in out["failures"]:
            print("FAIL " + f)
        if a.publish:
            if out["failures"]:
                print("not published: the check failed")
                return 1
            publish(conn, a.schema)
            conn.commit()
            print(f"published from {a.schema}")
    return 1 if out["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
