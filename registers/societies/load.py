"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Land the three export parts (never run the export: capture.py was run once),
read each, then every entity detail the nightly ask has landed, newest last.
An answer replaces nothing: a role it lists takes the answer's reading and
keeps the earliest day it was first read; a role it no longer lists keeps its
last reading, so its last_read_on is where the register stopped listing it.
"""
import os

from support import jobrun
from support.docstore.landing import read_bytes
from registers.societies import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "societies"
PRIVATE = "societies_private"
TABLES = ("societies", "society_states", "officers", "asks", "files", "set_aside")
PRIVATE_TABLES = ("officer_addresses",)
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at")
COLUMNS = {
    "societies": ("key", "nzbn", "number", "name", "status", "registered_on", "removed_on", "act", "reregistered_on",
                  "charity_number", "in_latest", "last_file", "party_society", "source_note") + _CITE,
    "society_states": ("key", "society_key", "file", "name", "status", "registered_on", "removed_on",
                       "vanished_at") + _CITE,
    "officers": ("key", "society_key", "nzbn", "first_name", "middle_names", "last_name", "full_name", "role_type",
                 "role_status", "started_on", "ended_on", "first_read_on", "last_read_on", "suppressed",
                 "unique_identifier", "old_id", "private_ref", "source_note") + _CITE,
    "asks": ("key", "society_key", "nzbn", "asked_at", "answered", "officers", "note", "source_note") + _CITE,
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.societies_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    return text.replace(f"{PRIVATE}.", f"{private_of(schema)}.{pre}").replace(f"{SCHEMA}.", f"{schema}.{pre}")


def create_tables(conn, schema: str, shared: bool = False) -> None:
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


def _flat(cols: tuple, rows):
    for row in rows:
        flat = {**row, **row.get("filed", {})}
        yield tuple(flat.get(c) for c in cols)


def merge_answer(officers: dict, answer: read.Result) -> dict:
    """Fold one answer's officer rows into `officers` (key → row), in place."""
    counts = {"listed_again": 0, "new": 0}
    for r in answer.rows["officers"]:
        old = officers.get(r["key"])
        if old is not None:
            r["filed"]["first_read_on"] = min(old["filed"]["first_read_on"], r["filed"]["first_read_on"])
            if old["filed"].get("old_id") and not r["filed"].get("old_id"):
                r["filed"]["old_id"] = old["filed"]["old_id"]
            counts["listed_again"] += 1
        else:
            counts["new"] += 1
        officers[r["key"]] = r
    return counts


def build(conn, schema: str, exports: list, aside: list, answers: list = (), only=None, shared: bool = False) -> dict:
    """exports: [(part, sha256, name)]; aside: [(item, why)] from capture;
    answers: [(sha256, asked at)], oldest first; only: the NZBNs and
    incorporation numbers to read (the sample's), None for all."""
    create_tables(conn, schema, shared)
    T = lambda t: table(schema, t, shared)
    _copy(conn, T("set_aside"), ("item", "stage", "reason", "count"), [(i, "capture", w, 1) for i, w in aside])
    counts, res = {"not_held": len(aside)}, {}
    for part, sha, name in sorted(exports, key=lambda e: capture.PARTS.index(e[0])):
        societies = {r["key"] for r in res["societies"].rows["societies"]} if "societies" in res else None
        res[part] = read.read_export(part, read_bytes(sha), sha, only=only, societies=societies)
        conn.execute(f"INSERT INTO {T('files')} VALUES (%s, %s, %s, 'read')", (sha, name, part))
        counts.update({f"{part}.{k}": v for k, v in res[part].counts.items()})
    lines, rc = read.reconcile(res["officers"], res["asks"])
    counts.update({f"reconcile.{k}": v for k, v in rc.items()})
    officers = {r["key"]: r for r in res["officers"].rows["officers"]}
    asks = list(res["asks"].rows["asks"])
    private, entity_aside = [], []
    wanted = None if only is None else {f"societies/{n}" for n in only}
    for sha, at in answers:
        a = read.read_answer(read_bytes(sha), sha, at)
        sk = a.rows["asks"][0]["filed"]["society_key"]
        if wanted is not None and sk not in wanted:
            continue
        for k, v in merge_answer(officers, a).items():
            counts[f"answers.{k}"] = counts.get(f"answers.{k}", 0) + v
        asks += a.rows["asks"]
        private += a.private
        entity_aside += a.set_aside
        counts["answers"] = counts.get("answers", 0) + 1
        conn.execute(f"INSERT INTO {T('files')} VALUES (%s, %s, 'entity', 'read') ON CONFLICT DO NOTHING",
                     (sha, capture.BASE + "/entities/" + sk.split("/")[1]))
    for t, rows in (("societies", res["societies"].rows["societies"]),
                    ("society_states", res["societies"].rows["society_states"]),
                    ("officers", sorted(officers.values(), key=lambda r: r["key"])), ("asks", asks)):
        _copy(conn, T(t), COLUMNS[t], _flat(COLUMNS[t], rows))
        counts[t] = len(rows)
    _copy(conn, T("set_aside"), ("item", "stage", "reason", "count"),
          [x for p in res.values() for x in p.set_aside] + lines + entity_aside)
    import json
    _copy(conn, table(private_of(schema), "officer_addresses", shared), ("key", "address", "document"),
          ((k, json.dumps(a, ensure_ascii=False, sort_keys=True), d) for k, a, d in private))
    counts["private"] = len(private)
    return counts


def load(conn, schema: str, log=print) -> int:
    """The three parts and every landed answer, read, under `schema`. Returns the officer count."""
    started = jobrun.now()
    landed, aside = capture.copy_all(conn)
    capture.land_proof(conn)
    counts = build(conn, schema, [(part, ref.sha256, name) for part, ref, name, at in landed], aside,
                   answers=capture.answers())
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("societies: " + detail)
    jobrun.record("qv4-societies-load", True, detail, started, counts)
    return counts["officers"]


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
