"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Capture, read every listing, join the scans, insert. Items in equal items
out plus items set aside: every table row on a listing is a declaration or
a catch-log line, and every file taken from the old folder is landed or a
catch-log line. A linked scan whose printed total could not be read is a
catch-log line of its own (stage `form`, its hash and pages): its row is
still a declaration, so it is counted apart.
"""
import os

from support import jobrun
from support.docstore.landing import read_bytes
from registers.disclosures import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "disclosures"
PRIVATE = "disclosures_private"
TABLES = ("declarations", "items", "files", "set_aside")
COLUMNS = ("key", "document", "page", "place", "regime", "threshold", "section", "party", "party_label", "party_basis",
           "donor_name", "amount", "amount_original", "received_on", "given_on", "commission_note", "amendment",
           "amended_on", "withdrawn_on", "returned_on", "amount_note", "items_sum", "items_check",
           "at_or_under_threshold", "href", "declaration_document", "form_total", "form_check", "form_reading",
           "read_from", "reader", "profile",
           "profile_version", "loaded_at", "issue")
ITEM_COLUMNS = ("key", "declaration", "ordinal", "amount", "first_date", "contributor", "text")


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.disclosures_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    return text.replace(f"{PRIVATE}.", f"{private_of(schema)}.{pre}").replace(f"{SCHEMA}.", f"{schema}.{pre}")


def create_tables(conn, schema: str, shared: bool = False) -> None:
    """The lane's tables as tables.sql has them now: made again on every
    build, since every row is rebuilt from documents (a register can be
    regenerated). The published views go with them; publish makes them
    again in the same transaction."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    conn.execute(f"DROP TABLE IF EXISTS {table(private_of(schema), 'donor_addresses', shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def wipe(conn, schema: str, shared: bool = False) -> None:
    for t in TABLES:
        conn.execute(f"DELETE FROM {table(schema, t, shared)}")
    conn.execute(f"DELETE FROM {table(private_of(schema), 'donor_addresses', shared)}")


def insert(conn, schema: str, result: read.Result, linked: dict, forms: dict, shared: bool = False) -> int:
    for item, stage, reason in result.set_aside:
        conn.execute(f"INSERT INTO {table(schema, 'set_aside', shared)} (item, stage, reason) VALUES (%s, %s, %s)",
                     (item, stage, reason))
    for row in result.rows:
        doc = linked.get(row["key"])
        r = {**row, **row["filed"], "declaration_document": doc,
             **read.form_check(row["filed"]["amount"], doc, forms)}
        conn.execute(f"INSERT INTO {table(schema, 'declarations', shared)} ({', '.join(COLUMNS)}) "
                     f"VALUES ({', '.join(['%s'] * len(COLUMNS))})", tuple(r[c] for c in COLUMNS))
    for it in result.items:
        conn.execute(f"INSERT INTO {table(schema, 'items', shared)} ({', '.join(ITEM_COLUMNS)}) "
                     f"VALUES ({', '.join(['%s'] * len(ITEM_COLUMNS))})", tuple(it[c] for c in ITEM_COLUMNS))
    for key, address in result.addresses:
        conn.execute(f"INSERT INTO {table(private_of(schema), 'donor_addresses', shared)} (key, address) VALUES (%s, %s)",
                     (key, address))
    return len(result.rows)


def build(conn, schema: str, listings: list, declarations: list, aside: list, shared: bool = False) -> dict:
    """listings: [(sha256, Commission name)]; declarations: [(sha256,
    Commission name)]; aside: [(item, why)] from capture. Wipes and fills
    `schema`; returns the counts."""
    create_tables(conn, schema, shared)
    wipe(conn, schema, shared)
    for item, why in aside:
        conn.execute(f"INSERT INTO {table(schema, 'set_aside', shared)} (item, stage, reason) VALUES (%s, 'capture', %s)",
                     (item, why))
    results = [read.read_listing(read_bytes(sha), sha) for sha, _ in listings]
    rows = [r for res in results for r in res.rows]
    linked, files = read.join(rows, declarations)
    forms = {sha: read.form_reading(sha) for sha in set(linked.values())}
    # ruling 62: a scan whose total could not be read is set aside with its hash and pages, never queued from here;
    # its row stays (the table is the source for the amount), so these lines are not in the reconciliation
    needs = read.needs_reading(forms, linked)
    for item, stage, reason in needs:
        conn.execute(f"INSERT INTO {table(schema, 'set_aside', shared)} (item, stage, reason) VALUES (%s, %s, %s)",
                     (item, stage, reason))
    n = seen = aside_n = 0
    for res in results:
        n += insert(conn, schema, res, linked, forms, shared)
        seen += res.seen
        aside_n += len(res.set_aside)
    files_t = table(schema, "files", shared)
    for sha, name in listings:
        conn.execute(f"INSERT INTO {files_t} VALUES (%s, %s, 'listing', NULL, 'read') ON CONFLICT DO NOTHING", (sha, name))
    for sha, name, by, status in files:
        conn.execute(f"INSERT INTO {files_t} VALUES (%s, %s, 'declaration', %s, %s) ON CONFLICT DO NOTHING",
                     (sha, name, by, status))
    if seen != n + aside_n:
        raise AssertionError(f"the catch log does not reconcile: {seen} table rows, {n} read, {aside_n} set aside")
    return {"listings": len(listings), "table_rows": seen, "rows": n, "set_aside": aside_n,
            "declarations_held": len({s for s, _ in declarations}), "linked": len(linked),
            "files_not_linked": sum(1 for f in files if f[3] == "not linked by the table"),
            "collisions": sum(1 for f in files if f[3] == "collision"), "not_documents": len(aside),
            "need_a_reading": len(needs)}


def load(conn, schema: str, log=print) -> int:
    """Every candidate file of the old folder landed by hash, every listing
    read, the scans joined, under `schema`. Returns the row count."""
    started = jobrun.now()
    landed, aside = capture.copy_all(conn)
    listings = [(ref.sha256, capture.commission_name(p)) for kind, ref, p, _ in landed if kind == "listing"]
    declarations = [(ref.sha256, capture.commission_name(p)) for kind, ref, p, _ in landed if kind == "declaration"]
    counts = build(conn, schema, listings, declarations, [(os.path.basename(p), why) for p, why in aside])
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("disclosures: " + detail)
    jobrun.record("qv4-disclosures-load", True, detail, started, counts)
    return counts["rows"]


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        wipe(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        conn.execute(f"INSERT INTO {PRIVATE}.donor_addresses SELECT * FROM {private_of(staging)}.donor_addresses")
        conn.execute(sql("publish.sql"))
