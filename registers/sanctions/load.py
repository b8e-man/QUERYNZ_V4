"""Loading (plan 1b.7): `build(conn, schema, docs)` reads the newest
landed document of each list into the reading's tables under `schema`;
`publish(conn, staging)` moves them into `sanctions` and makes the views,
in one transaction. sample.py uses the same `build`.

Idempotent per listing: the reading's tables are dropped and made again and
every list read again from its document. One document per list is read, the
newest landed (each is a whole list). Items in equal listings typed plus set
aside plus rows counted and not read (an MFAT Asset or Total row, a Police
row that is not an ID); the build raises if a list does not reconcile.

While a list is held on its publisher's terms nothing of it is landed, so
nothing of it is read: `pub.sanctions_lists` names only the lists read.

    python -m registers.sanctions.load [--schema scratch_…] [--database querynz_v4_sample]
    python -m registers.sanctions.load --job

Every line printed is a count.
"""
import argparse
import os
import re
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.sanctions import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "sanctions"
PRIVATE = "sanctions_private"
JOB = "qv4-sanctions-load"
STAGING = "staging_sanctions_load"
TABLES = ("lists", "listings", "read_set_aside")
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "lists": ("list_id", "name", "publisher", "law", "document", "version", "stated", "stated_where", "listings",
              "ended", "set_aside", "profile", "profile_version"),
    "listings": ("key", "list_id", "list_ref", "other_ref", "kind", "status", "name", "aliases", "original_script",
                 "titles", "positions", "nationalities", "birth_dates", "birth_countries", "countries", "regime", "basis",
                 "designated_on", "renewed_on", "expires_on", "ended_on", "updated_on", "list_version") + _CITE,
    "read_set_aside": ("list_id", "document", "place", "stage", "reason"),
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


_NAMES = re.compile(r"(?<![A-Za-z0-9_])sanctions(_private)?\.")


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    if name == "tables.sql":
        text = capture.READING + text.split(capture.READING, 1)[1]
    pre = f"{SCHEMA}_" if shared else ""
    return _NAMES.sub(lambda m: f"{private_of(schema) if m.group(1) else schema}.{pre}", text)


def create_tables(conn, schema: str, shared: bool = False) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def build(conn, schema: str, docs: dict, read_bytes=read_bytes, shared: bool = False, versions: dict = None) -> dict:
    """`docs`: list → {'list': (sha256, version), 'page-1373': sha256 or None}."""
    t0 = time.monotonic()
    create_tables(conn, schema, shared)
    T = lambda t: table(schema, t, shared)
    rows, asides, lists = [], [], []
    for list_id in capture.LISTS:
        d = docs.get(list_id)
        if not d or not d.get("list"):
            continue
        sha, list_version = d["list"]
        version = (versions or {}).get(list_id) or read.profile_version(list_id)
        extra = read_bytes(d["page-1373"]) if d.get("page-1373") else None
        out = read.read_document(list_id, read_bytes(sha), sha, version, list_version, extra)
        item_asides = [a for a in out["set_aside"] if a["place"] != "document"]
        if out["items"] != len(out["rows"]) + len(item_asides) + out["skipped"]:
            raise AssertionError(f"{SCHEMA}: {list_id} does not reconcile: {out['items']} items, {len(out['rows'])} "
                                 f"listings, {len(item_asides)} set aside, {out['skipped']} counted")
        rows += out["rows"]
        asides += out["set_aside"]
        name, publisher, law = read.LISTS[list_id]
        lists.append({"list_id": list_id, "name": name, "publisher": publisher, "law": law, "document": sha,
                      "version": out["version"] or list_version, "stated": out["stated"],
                      "stated_where": out["stated_where"],
                      "listings": sum(1 for r in out["rows"] if r["status"] == "designated"),
                      "ended": sum(1 for r in out["rows"] if r["status"] != "designated"),
                      "set_aside": len(out["set_aside"]), "profile": read.PROFILES[list_id], "profile_version": version})
    counts = {t: _copy(conn, T(t), COLUMNS[t], src) for t, src in
              (("lists", lists), ("listings", rows), ("read_set_aside", asides))}
    counts["seconds"] = round(time.monotonic() - t0, 1)
    return counts


def listing(conn, schema: str = SCHEMA) -> dict:
    """list → the newest landed list document (sha256, version) and, for Police, the newest 1373 page."""
    out = {}
    for list_id, role, sha, version in conn.execute(
            f"SELECT DISTINCT ON (list_id, role) list_id, role, sha256, version FROM {schema}.capture_documents "
            "WHERE role IN ('list', 'page-1373') ORDER BY list_id, role, at DESC"):
        d = out.setdefault(list_id, {})
        d[role] = (sha, version) if role == "list" else sha
    return out


def load(conn, schema: str, log=print) -> int:
    """The merge gate's staging step (support/staging): the newest landed list documents, read under `schema`
    (none while the lists are held). Added by the integrator at the merge of sanctions-1."""
    from registers.sanctions import check
    capture.Tables(conn).create()
    listed = listing(conn)
    counts = build(conn, schema, listed)
    problems = check.reading(conn, schema)
    log(f"{SCHEMA}: {counts['listings']} listings from {counts['lists']} lists into {schema}; " + ("; ".join(problems) or "reconciles"))
    return counts["listings"]


def publish(conn, staging: str, log=print) -> None:
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {table(SCHEMA, t)} SELECT * FROM {table(staging, t)}")
        conn.execute(sql("publish.sql"))
    log(f"{SCHEMA}: published from {staging}")


def unchanged(conn, listed: dict) -> bool:
    if conn.execute("SELECT to_regclass(%s)", (f"{SCHEMA}.lists",)).fetchone()[0] is None:
        return False
    held = {r[0] for r in conn.execute(f"SELECT document FROM {SCHEMA}.lists")}
    return held == {d["list"][0] for d in listed.values() if d.get("list")}


def job(log=print) -> int:
    from support import db
    from registers.sanctions import check
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        capture.Tables(conn).create()
        listed = listing(conn)
        if unchanged(conn, listed):
            log(f"{SCHEMA}: the listing is the one published; nothing loaded")
            jobrun.record(JOB, True, "unchanged: the listing is the one published", started, {})
            return 0
        with conn.transaction():
            counts = build(conn, STAGING, listed)
        problems = check.reading(conn, STAGING)
        detail = f"{counts['listings']} listings from {counts['lists']} lists; " + ("; ".join(problems) or "reconciles")
        if problems:
            log(f"{SCHEMA}: RED, nothing published: " + detail)
            jobrun.record(JOB, False, "nothing published: " + detail, started, {})
            return 1
        publish(conn, STAGING, log)
    jobrun.record(JOB, True, "published: " + detail, started, counts)
    log(f"{SCHEMA}: published: " + detail)
    return 0


def main(argv=None) -> int:
    from support import db
    ap = argparse.ArgumentParser(prog="python -m registers.sanctions.load")
    ap.add_argument("--schema", default="scratch_sanctions_full")
    ap.add_argument("--database", default="querynz_v4_sample")
    ap.add_argument("--capture-database", default="querynz_v4")
    ap.add_argument("--capture-schema", default=SCHEMA)
    ap.add_argument("--job", action="store_true")
    a = ap.parse_args(argv)
    if a.job:
        return job()
    if not a.schema.startswith(("scratch_", "staging_")):
        print(f"{SCHEMA}: a session loads only a scratch or staging schema")
        return 2
    key = db.READ_KEY if a.capture_database == "querynz_v4" else db.OWNER_KEY
    with db.connect(key, a.capture_database) as src:
        listed = listing(src, a.capture_schema)
    with db.connect(db.OWNER_KEY, a.database) as conn:
        with conn.transaction():
            counts = build(conn, a.schema, listed)
    for k, v in counts.items():
        print(f"{SCHEMA}: {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
