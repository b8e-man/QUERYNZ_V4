"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Capture by hash, read every file, insert. Items in equal items out plus
items set aside (read.py says how).
"""
import os

from support import jobrun
from support.docstore.landing import read_bytes
from registers.house import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "house"
PRIVATE = "house_private"
TABLES = ("elections", "electorates", "candidates", "members", "figures", "files", "set_aside")
COLUMNS = {
    "elections": ("key", "kind", "name", "electorate", "polled_on", "polled_basis", "results_href"),
    "electorates": ("key", "election", "name", "number", "statsnz_code", "statsnz_name", "layer", "statsnz_document",
                    "join_basis", "votes_counted", "candidate_total", "candidate_informals", "party_total",
                    "party_informals", "poll_cancelled", "result_held"),
    "candidates": ("key", "election", "name", "display_name", "name_key", "party", "party_registered", "party_basis",
                   "electorate", "list_place", "list_document", "list_place_cite", "votes", "poll_cancelled",
                   "joined_basis"),
    "members": ("key", "election", "name", "display_name", "name_key", "party", "party_registered", "party_basis",
                "route", "electorate", "candidate", "from_on", "from_basis", "to_by", "to_basis", "ended_on"),
    "figures": ("key", "election", "what", "party", "value"),
}
STAMP = ("document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at")


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.house_t`."""
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
    conn.execute(sql("tables.sql", schema, shared))


def _insert(conn, name: str, cols: tuple, row: dict) -> None:
    conn.execute(f"INSERT INTO {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) "
                 f"VALUES ({', '.join(['%s'] * len(cols))})", tuple(row.get(c) for c in cols))


def build(conn, schema: str, docs: list, aside: list, shared: bool = False) -> dict:
    """docs: [(folder, sha256, name, captured at)] landed; aside: [(item,
    why)] from capture. Wipes and fills `schema`; returns the counts."""
    create_tables(conn, schema, shared)
    res = read.read([(f, sha, n, at, read_bytes(sha)) for f, sha, n, at in docs])
    for item, why in aside:
        res.set_aside.append((item, "capture", why))
    for t in ("elections", "electorates", "candidates", "members", "figures"):
        for row in getattr(res, t):
            _insert(conn, table(schema, t, shared), COLUMNS[t] + STAMP, row)
    for sha, name, kind, status in res.files:
        conn.execute(f"INSERT INTO {table(schema, 'files', shared)} VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                     (sha, name, kind, status))
    for item, stage, reason in res.set_aside:
        conn.execute(f"INSERT INTO {table(schema, 'set_aside', shared)} (item, stage, reason) VALUES (%s, %s, %s)",
                     (item, stage, reason))
    return {**res.counts, "set_aside": len(res.set_aside), "not_held": len(aside)}


def load(conn, schema: str, log=print) -> int:
    """Every held file copied by hash and read, under `schema`. Returns the
    candidate count."""
    started = jobrun.now()
    landed, aside = capture.copy_all(conn)
    counts = build(conn, schema, [(f, ref.sha256, name, at) for f, ref, name, at in landed], aside)
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("house: " + detail)
    jobrun.record("qv4-house-load", True, detail, started, counts)
    return counts["candidates"]


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        conn.execute(sql("publish.sql"))
