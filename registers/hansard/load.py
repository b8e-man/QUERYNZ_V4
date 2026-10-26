"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Land the export (never run it: capture.py was run once), read it, copy the
rows in. Items in equal items out plus items set aside (read.py says how).
Then the MCP's two corpora as support/mcpsource landed them (read_mcp.py):
`index_pages` from `parliament-hansard-index`, `days` and `day_sections`
from `parliament-hansard-debates`, each day's text into the private twin.
Items in (the documents) equal rows read plus older versions plus items set
aside; the pull's own catch lines come across as set-aside lines at stage
`pull`. `qv4-hansard-load` runs the same after each night's pull.

    python -m registers.hansard.load                    stage and publish (the job)
    python -m registers.hansard.load --database querynz_v4_sample --schema S --mcp-schema M    a scratch proof
"""
import argparse
import os
import sys

from support import jobrun
from support.docstore.landing import read_bytes
from registers.hansard import capture, read, read_mcp

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "hansard"
PRIVATE = "hansard_private"
JOB = "qv4-hansard-load"
TABLES = ("sittings", "sections", "turns", "members", "old_speeches", "index_pages", "days", "day_sections", "files",
          "set_aside")
PRIVATE_TABLES = ("day_texts",)
CITE = ("source_note", "document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "sittings": ("key", "sitting_on", "parliament", "volume", "progress", "url", "sections", "turns", "attributed",
                 "unattributed", "speakers", "old_sections", "old_speeches", "old_unattributed", "old_speakers",
                 "old_derived_at", "captured_at") + CITE,
    "sections": ("key", "sitting_on", "section_index", "parliament", "volume", "proceeding", "subject", "bill_title",
                 "bill_id", "progress", "old_status", "text", "chars", "text_sha1", "turns", "url", "captured_at",
                 "old_id") + CITE,
    "turns": ("key", "section", "sitting_on", "section_index", "ordinal", "label", "member_id", "roster_name", "role",
              "in_roster") + CITE,
    "members": ("key", "display_name", "sort_name", "parliaments") + CITE,
    "old_speeches": ("key", "sitting_on", "section_index", "member_id", "speaker_label", "speaker_name",
                     "speech_count", "retired_at", "document"),
    "index_pages": ("url", "lastmod", "fetched", "index_on", "record", "raw_file", "versions", "fields_unread") + CITE
                   + ("loaded_at",),
    "days": ("key", "sitting_on", "title", "pdf_url", "pdf_sha256", "pdf_bytes", "http_status", "captured_at",
             "raw_file", "updated_at", "page_count", "word_count", "text_words", "chars", "versions", "fields_unread",
             "old_sections", "old_subjects", "subjects_in_text") + CITE + ("loaded_at",),
    "day_sections": ("key", "sitting_on", "found", "neighbour", "document"),
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
    text = text.replace(f"{PRIVATE}.", f"{private_of(schema)}.{pre}")
    text = text.replace(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};", f"CREATE SCHEMA IF NOT EXISTS {schema};")
    return text.replace(f"{SCHEMA}.", f"{schema}.{pre}")


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
            cp.write_row(tuple(row.get(c) for c in cols))


def build(conn, schema: str, export: tuple, aside: list, only=None, shared: bool = False, mcp: dict = None,
          get_bytes=read_bytes) -> dict:
    """export: (sha256, name); aside: [(item, why)] from capture; only: the
    sitting days to read (the sample's), None for all; mcp: {corpus: (items,
    caught)} for the MCP's two corpora, items [(sha256, seq, record id)] in
    the order the pull landed them. Wipes and fills `schema`; returns the
    counts. A reading that is not balanced raises."""
    create_tables(conn, schema, shared)
    res = read.read(get_bytes(export[0]), export[0], only=only)
    if not read.balanced(res):
        raise AssertionError(f"hansard: items in {res.counts['lines']} do not equal rows out plus set aside: {res.counts}")
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [{"item": i, "stage": "capture", "reason": w} for i, w in aside]
          + [{"item": i, "stage": s, "reason": w} for i, s, w in res.set_aside])
    for t in ("sittings", "sections", "turns", "members", "old_speeches"):
        _copy(conn, table(schema, t, shared), COLUMNS[t], getattr(res, t))
    conn.execute(f"INSERT INTO {table(schema, 'files', shared)} VALUES (%s, %s, 'hansard', 'read')", export)
    mcp = mcp or {}
    idx_items, idx_caught = mcp.get(read_mcp.INDEX, ([], []))
    day_items, day_caught = mcp.get(read_mcp.DAYS, ([], []))
    idx = read_mcp.read_index(idx_items, get_bytes)
    subjects = {}
    for sec in res.sections:
        subjects.setdefault(sec["sitting_on"], []).append((sec["key"], sec.get("subject")))
    with conn.cursor().copy(f"COPY {table(private_of(schema), 'day_texts', shared)} (key, text) FROM STDIN") as cp:
        days = read_mcp.read_days(day_items, get_bytes, subjects, lambda k, t: cp.write_row((k, t)))
    for t, rows in (("index_pages", idx.index_pages), ("days", days.days), ("day_sections", days.day_sections)):
        _copy(conn, table(schema, t, shared), COLUMNS[t], rows)
    _copy(conn, table(schema, "files", shared), ("sha256", "name", "kind", "status"),
          [dict(zip(("sha256", "name", "kind", "status"), f)) for f in idx.files + days.files])
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason"),
          [{"item": f"{c} seq {q}", "stage": "pull", "reason": f"{st}: {why}"}
           for c, lines in ((read_mcp.INDEX, idx_caught), (read_mcp.DAYS, day_caught)) for q, st, why in lines]
          + [{"item": i, "stage": s, "reason": w} for i, s, w in idx.set_aside + days.set_aside])
    return {**res.counts, "not_held": len(aside), **idx.counts, **days.counts,
            "pull caught": len(idx_caught) + len(day_caught)}


def mcp_items(conn, mcp_schema: str = capture.MCP_SCHEMA) -> dict:
    """{corpus: (arrivals, catch lines)} for the MCP's two Hansard corpora."""
    return {c: (capture.arrivals(conn, c, mcp_schema), capture.caught(conn, c, mcp_schema)) for c in capture.CORPORA}


def _export(conn) -> tuple:
    landed, aside = capture.copy_all(conn)
    return next((ref.sha256, name) for kind, ref, name, at in landed if kind == "hansard"), aside


def load(conn, schema: str, log=print, mcp_schema: str = capture.MCP_SCHEMA) -> int:
    """The export landed and read, and the MCP's two corpora, under `schema`. Returns the section count."""
    started = jobrun.now()
    export, aside = _export(conn)
    counts = build(conn, schema, export, aside, mcp=mcp_items(conn, mcp_schema))
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("hansard: " + detail)
    jobrun.record(JOB, True, detail, started, counts)
    return counts["sections"]


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, the
    private twin's day texts with them, and the views refreshed, in one
    transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        for t in PRIVATE_TABLES:
            conn.execute(f"INSERT INTO {PRIVATE}.{t} SELECT * FROM {private_of(staging)}.{t}")
        conn.execute(sql("publish.sql"))


def main(argv=None) -> int:
    """The job `qv4-hansard-load`: build under a staging schema, publish. With
    --schema, a session's proof: build there and publish nothing."""
    ap = argparse.ArgumentParser(prog="registers.hansard.load")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", help="build here and stop (a scratch proof); default: stage and publish")
    ap.add_argument("--mcp-schema", default=capture.MCP_SCHEMA)
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '600s'")
        if a.schema:
            export, aside = _export(conn)
            counts = build(conn, a.schema, export, aside, mcp=mcp_items(conn, a.mcp_schema))
            conn.commit()
            print("hansard: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {a.database}.{a.schema}")
            return 0
        load(conn, "staging_hansard_load", mcp_schema=a.mcp_schema)
        conn.commit()
        publish(conn, "staging_hansard_load")
        conn.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
