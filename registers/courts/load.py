"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's reading under a staging schema of the real database, and
`publish` to move it into the lane's own tables in one transaction and
refresh the published views. `fill` in sample.py uses the same pieces.

The listing is landed from the store (capture.py exported it once), every
listed file copied in by hash, the capture job's landed judgments added,
the documents read (read.py), and the rows copied in. The ledger of
suppression orders and the capture job's tables are the lane's own records
and are never wiped: a staging build reads the orders from the lane's real
schema, so an order recorded today binds the next build.
"""
import os

from support import jobrun
from registers.courts import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "courts"
PRIVATE = "courts_private"
#: the reading's tables, rebuilt at every load
TABLES = ("judgments", "judgment_parties", "paragraphs", "files", "set_aside")
PRIVATE_TABLES = ("withheld_names",)
#: the lane's records, never wiped
RECORDS = ("suppression_orders", "captures", "feeds", "capture_log")
COLUMNS = {
    "judgments": ("key", "citation", "court", "court_name", "registry", "case_numbers", "judgment_date", "date_basis",
                  "hearing", "judges", "heading", "caption_shape", "outcome", "paragraphs", "parties", "suppression",
                  "suppression_kinds", "withheld", "status", "missing", "unrecognised", "notes", "source", "source_url",
                  "source_note", "document", "page", "place", "read_from", "reader", "profile", "profile_version",
                  "loaded_at"),
    "judgment_parties": ("key", "judgment", "citation", "position", "block", "role", "name", "withheld", "anonymised",
                         "crown", "confidence", "capacity", "document", "page", "place", "read_from", "reader",
                         "profile", "profile_version", "loaded_at"),
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
    build; the records are created if absent and never dropped."""
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


def orders(conn, schema: str = SCHEMA, shared: bool = False) -> list:
    """The ledger's orders, oldest first."""
    cur = conn.execute(f"SELECT citation, document, reason FROM {table(schema, 'suppression_orders', shared)} ORDER BY order_id")
    return [{"citation": r[0], "document": r[1], "reason": r[2]} for r in cur]


def captured(conn, schema: str = SCHEMA, shared: bool = False) -> list:
    """[(entry, sha)] of the judgments the capture job landed."""
    cur = conn.execute(f"SELECT url, citation, document, captured_at::text FROM {table(schema, 'captures', shared)} "
                       "WHERE document IS NOT NULL ORDER BY url")
    return [({"source": "capture", "ref": c, "url": u, "file": os.path.basename(u), "captured_at": at,
              "note": "captured once from www.courtsofnz.govt.nz through the fetch gate"}, d) for u, c, d, at in cur]


def build(conn, schema: str, entries: list, held: list, aside: list, ledger: list, only=None,
          shared: bool = False, store=None) -> dict:
    """entries: the listing; held: [(entry, DocumentRef or sha)] of documents in
    the store; aside: [(item, why)] from capture; ledger: the orders. Wipes and
    fills `schema`; returns the counts."""
    create_tables(conn, schema, shared)
    docs = [({**e, "note": e.get("note") or capture.LISTING_NOTE}, getattr(r, "sha256", r)) for e, r in held]
    res = read.read(docs, ledger, store=store)
    listed = {e["sha256"]: e for e in entries if only is None or e["sha256"] in only}
    not_held = {sha for sha, _ in aside}
    files = list(res.files) + [(sha, e["source"], e["ref"], e["url"], None, "not held", e.get("pages"))
                               for sha, e in listed.items() if sha in not_held]
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [(i, "capture", w) for i, w in aside] + list(res.set_aside))
    _copy(conn, table(schema, "files", shared), ("document", "source", "ref", "url", "profile", "outcome", "pages"), files)
    for t, rows in (("judgments", res.judgments), ("judgment_parties", res.parties)):
        _copy(conn, table(schema, t, shared), COLUMNS[t], (tuple(r.get(c) for c in COLUMNS[t]) for r in rows))
    _copy(conn, table(schema, "paragraphs", shared), ("judgment", "number", "page", "document"), res.paragraphs)
    _copy(conn, table(private_of(schema), "withheld_names", shared), ("key", "name", "capacity"), res.withheld)
    return {**res.counts, "listed": len(listed), "not_held": len(not_held)}


def load(conn, schema: str, log=print) -> int:
    """The listing landed, its files copied in, the captures added, all read,
    under `schema`. Returns the judgment count."""
    started = jobrun.now()
    conn.execute(capture_tables_sql(SCHEMA))           # the records live in the lane's own schema
    _, entries = capture.land_listing(conn)
    held, aside = capture.copy_all(conn, entries, log=log)
    held += captured(conn)
    counts = build(conn, schema, entries, held, aside, orders(conn))
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("courts: " + detail)
    jobrun.record("qv4-courts-load", True, detail, started, counts)
    return counts["judgments"]


def publish(conn, staging: str) -> None:
    """The lane's reading wiped and refilled from the staged one, and the
    views refreshed, in one transaction (contract: the lane). The records are
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
