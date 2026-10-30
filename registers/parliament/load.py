"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views; `qv4-parliament-load` runs the same after
each night's pull. `fill` in sample.py uses the same pieces.

Every record of the seven parliament corpora the pull has taken
(support/mcpsource's arrivals) is read by its hash from the document store;
rows go to the tables in batches as they are read (683,524 written
questions do not sit in memory). Items in (the documents) equal records
plus older versions plus items set aside; the pull's own catch lines come
across as set-aside lines at stage `pull`. Every text published whole is
flagged where its shape names an address (shapes.py, ruling 102); the
flagged rows go to `address_flags` by key and the log counts them by
column, never printing a value. The text reader's stored readings
(model_read.py, one per document hash in the reader store) are replayed
as each written question and archived page is read: its names go to
`people`, its summary to `readings`; a document without a reading is
waiting on `qv4-parliament-read`; one whose reading is unusable, or whose
text the profile cannot split, is set aside at stage `read`, named. No
model is called here. Once the views are refreshed, `stamp_scan`
runs the check's second pattern (check.STREET_SQL) over every row of them
and writes what it found to `street_scan`: the check holds that stamp to
the view and re-scans only a fixed sample (the board gives it 120 s).

    python -m registers.parliament.load --database querynz_v4_sample --schema scratch_parliament_1_build --mcp-schema scratch_mcp_1_pull2
"""
import argparse
import os
import sys

from support import jobrun
from support import reader as rd
from support.docstore.landing import read_bytes
from registers.parliament import capture, model_read as M, read, shapes

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "parliament"
PRIVATE = "parliament_private"
JOB = "qv4-parliament-load"
TABLES = ("written_questions", "api_items", "wayback_pages", "files", "set_aside", "address_flags",
          "street_scan", "readings", "people")
PRIVATE_TABLES = ()
PEOPLE_FLAGGED = ("name", "role_text", "of_organisation")      # published whole, flagged (hard limit 15 by the flag)
COLUMNS = {"written_questions": read.columns("wq"), "api_items": read.columns("api"),
           "wayback_pages": read.columns("wayback"),
           "readings": ("document", "source_table", "source_key", "dated", "citation_url", "pieces", "names", "summary",
                        "truncated", "batch", "model", "reader", "profile", "profile_version", "made_at", "loaded_at"),
           "people": ("key", "name", "name_names_address", "kind", "role", "role_text", "role_text_names_address",
                      "of_organisation", "of_organisation_names_address", "source_table", "source_key", "dated",
                      "citation_url", "document", "page", "place", "read_from", "reader", "model", "profile",
                      "profile_version", "loaded_at")}
BATCH = 20000
READ = "read"       # the set-aside stage of a document the text reader could not read
SHAPE_OF = {"written_questions": "wq", "wayback_pages": "wayback"}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.parliament_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    return (text.replace(f"{PRIVATE}.", f"{private_of(schema)}.{pre}").replace(f"{SCHEMA}.", f"{schema}.{pre}")
            .replace("INDEX IF NOT EXISTS parliament_", f"INDEX IF NOT EXISTS {schema}_{pre}"))


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


def document_of(t: str, row: dict) -> dict:
    """What a people row says of its document: the row's key, its own day (the question's release, the page's
    snapshot) and its address."""
    if t == "written_questions":
        return {"source_table": t, "source_key": row["key"], "dated": row.get("question_released_on"),
                "citation_url": None}
    day = (row.get("dated") or "")[:10]
    if not read._iso_day(day):
        day = (row.get("archived_at") or "")[:10] or None
    return {"source_table": t, "source_key": row["key"], "dated": day or None, "citation_url": row.get("citation_url")}


class Sink(read.Result):
    """read.Result whose rows go to the tables in batches as they are read, and which replays each written
    question's and archived page's stored text-reader reading into `people` and `readings` as its row passes
    (`pick`), never calling a model."""

    def __init__(self, conn, schema: str, shared: bool, store: rd.Store = None):
        super().__init__()
        self.conn, self.schema, self.shared = conn, schema, shared
        self.store = store or rd.Store()
        self.rows["readings"], self.rows["people"] = [], []
        self.now = None

    def emit(self, t: str, row: dict) -> None:
        self.rows[t].append(row)
        if t in M.PROFILE_OF:
            self.pick(t, row)
        if len(self.rows[t]) >= BATCH:
            self.flush(t)

    def emit_older(self, t: str, row: dict) -> None:
        """An archived page's older version whose text differs: a document for the text reader, not a row."""
        super().emit_older(t, row)
        self.pick(t, row)

    def pick(self, t: str, row: dict) -> None:
        """The document's stored reading, replayed: people rows and a readings row; else waiting, or set aside
        at stage read when the profile cannot split its text or the reader found it unusable."""
        profile = M.PROFILE_OF[t]
        version = read.PROFILE_VERSION[SHAPE_OF[t]]
        sha = row["document"]
        c = self.counts
        try:
            M.pieces_of(M.document_text(profile, row), M.budget(profile))
        except M.CannotSplit as exc:
            self.set_aside.append((sha, READ, str(exc)))
            c[f"{t}: set aside at read"] = c.get(f"{t}: set aside at read", 0) + 1
            return
        reading = M.stored(sha, profile, version, self.store)
        if reading is None:
            c[f"{t}: waiting on the text reader"] = c.get(f"{t}: waiting on the text reader", 0) + 1
            return
        if reading["unusable"]:
            self.set_aside.append((sha, READ, reading["unusable"]))
            c[f"{t}: set aside at read"] = c.get(f"{t}: set aside at read", 0) + 1
            return
        doc = document_of(t, row)
        now = self.now or row["loaded_at"]
        for p in M.people_rows(sha, reading, doc, profile, version, now):
            for col in PEOPLE_FLAGGED:
                found = shapes.shape(p[col])
                p[f"{col}_names_address"] = found is not None
                if found:
                    self.emit_flag(("people", p["key"], col, found))
                    c[f"people.{col} names an address"] = c.get(f"people.{col} names an address", 0) + 1
            self.rows["people"].append(p)
        self.rows["readings"].append({**doc, "document": sha, "pieces": reading["pieces"] or 1, "names": len(reading["people"]),
                                      "summary": reading["summary"], "truncated": bool(reading["truncated"]),
                                      "batch": reading.get("batch"), "model": reading["model"], "reader": reading["reader"],
                                      "profile": profile, "profile_version": version, "made_at": reading["made_at"],
                                      "loaded_at": now})
        c[f"{t}: read by the text reader"] = c.get(f"{t}: read by the text reader", 0) + 1
        c["names"] = c.get("names", 0) + len(reading["people"])
        for name in ("people", "readings"):
            if len(self.rows[name]) >= BATCH:
                self.flush(name)


    def flush(self, t: str) -> None:
        cols = COLUMNS[t]
        _copy(self.conn, table(self.schema, t, self.shared), cols, (tuple(r[c] for c in cols) for r in self.rows[t]))
        self.rows[t] = []

    def close(self) -> None:
        for t in COLUMNS:
            self.flush(t)


def build(conn, schema: str, items: list, caught: list = (), shared: bool = False, get_bytes=read_bytes,
          store: rd.Store = None) -> dict:
    """items: [(corpus, sha256, seq, record id, served)]; caught: the pull's
    catch lines [(corpus, seq, stage, reason)]. Wipes and fills `schema`;
    returns the counts. `store`: the reader store the text reader's
    readings are replayed from (the shared one by default)."""
    create_tables(conn, schema, shared)
    sink = Sink(conn, schema, shared, store)
    read.read(items, get_bytes, out=sink)
    sink.close()
    _copy(conn, table(schema, "files", shared), ("sha256", "corpus", "record_id", "seq", "status"), sink.files)
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [(f"{c} seq {s}", "pull", f"{st}: {why}") for c, s, st, why in caught] + list(sink.set_aside))
    _copy(conn, table(schema, "address_flags", shared), ("table_name", "key", "column_name", "shape"), sink.flags)
    return {**sink.counts, "pull caught": len(caught)}


def load(conn, schema: str, log=print, mcp_schema: str = capture.MCP_SCHEMA) -> int:
    """Every parliament document the pull landed, read under `schema`. Returns the record count."""
    started = jobrun.now()
    counts = build(conn, schema, capture.arrivals(conn, mcp_schema), capture.caught(conn, mcp_schema))
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("parliament: " + detail)
    jobrun.record(JOB, True, detail, started, counts)
    return counts["records"]


def stamp_scan(conn, schema: str, shared: bool = False) -> dict:
    """The check's street pattern over every row of the published views (`pub` live, `<schema>.pub_parliament_*`
    in a proof), written to `street_scan` per view and text column. {view: rows holding a street unflagged}."""
    from registers.parliament import check
    name = table(schema, "street_scan", shared)
    conn.execute(f"DELETE FROM {name}")
    out = {}
    for v in check.VIEWS:
        vs, vn = check.view_name(schema, v)
        at = conn.execute(f'SELECT max(loaded_at) FROM "{vs}"."{vn}"').fetchone()[0]
        rows, found = check.street_counts(conn, vs, vn)
        for c, n in found.items():
            conn.execute(f"INSERT INTO {name} (view_name, column_name, rows, loaded_at, found) "
                         "VALUES (%s, %s, %s, %s, %s)", (v, c, rows, at, n))
        out[v] = sum(found.values())
    return out


def views(conn, schema: str) -> None:
    """The published views over a scratch build, as `<schema>.pub_parliament_*`, so the check reads a proof
    the way it reads `pub`."""
    conn.execute(sql("publish.sql", schema).replace("pub.", f"{schema}.pub_"))


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
        stamp_scan(conn, SCHEMA)


def main(argv=None) -> int:
    """The job `qv4-parliament-load`: build under a staging schema, publish.
    With --schema, a session's proof: build there and publish nothing."""
    ap = argparse.ArgumentParser(prog="registers.parliament.load")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", help="build here and stop (a scratch proof); default: stage and publish")
    ap.add_argument("--mcp-schema", default=capture.MCP_SCHEMA)
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '600s'")
        if a.schema:
            counts = build(conn, a.schema, capture.arrivals(conn, a.mcp_schema), capture.caught(conn, a.mcp_schema))
            views(conn, a.schema)
            stamp_scan(conn, a.schema)
            conn.commit()
            print("parliament: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {a.database}.{a.schema}")
            return 0
        staging = "staging_parliament_load"
        load(conn, staging, mcp_schema=a.mcp_schema)
        conn.commit()
        publish(conn, staging)
        conn.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
