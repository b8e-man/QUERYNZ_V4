"""Loading (plan 1b.7): `build(conn, schema, items, held)` reads the
capture's record into the reading's tables under `schema`; `publish(conn,
staging)` moves them into `councillor_interests` and makes the views, in one
transaction. sample.py uses the same `build`.

Per council (all 78 of `capture.REGISTERS`): how it publishes its register
and what the estate holds of it (`registers`); every register document held
(`documents`: held, never read); and, from each page of the structured shape
(read.py), one row per member and category (`interests`), the newest
capture of each page only. A category that is real property, a home, an
address, a contact, or a spouse's or partner's, is counted by its heading in
`read_withheld` and nothing under it is kept.

    python -m registers.councillor_interests.load [--schema scratch_…] [--database querynz_v4_sample]
    python -m registers.councillor_interests.load --job
"""
import argparse
import os
import re
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.councillor_interests import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "councillor_interests"
JOB = "qv4-councillor-interests-load"
STAGING = "staging_councillor_interests_load"
TABLES = ("registers", "documents", "interests", "read_withheld", "read_set_aside")
COLUMNS = {
    "registers": ("council", "host", "form", "landing_url", "landing_sha256", "documents_held", "members_read", "why"),
    "documents": ("sha256", "council", "url", "found_on", "asked_at"),
    "interests": ("key", "council", "member", "role", "category", "entries", "as_at", "document", "page", "place", "url",
                  "read_from", "reader", "profile", "profile_version"),
    "read_withheld": ("council", "category", "why", "members"),
    "read_set_aside": ("document", "place", "stage", "reason"),
}
PER_MEMBER_FILES = 4          # a council with more register documents than this publishes one file per member
table = capture.table
_NAMES = re.compile(rf"(?<![A-Za-z0-9_]){SCHEMA}\.")


def sql(name: str, schema: str = SCHEMA) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    if name == "tables.sql":
        text = capture.READING + text.split(capture.READING, 1)[1]
    pre = "" if schema == SCHEMA else f"{SCHEMA}_"
    return _NAMES.sub(f"{schema}.{pre}", text)


def create_tables(conn, schema: str) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t)} CASCADE")
    conn.execute(sql("tables.sql", schema))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def build(conn, schema: str, items: list, held: dict, registers: dict = None, read_bytes=read_bytes) -> dict:
    """`items`: the capture's asks, oldest first, as dicts (council, url, kind, found_on, asked_at, sha256, why);
    `held`: host → why for every held host."""
    t0 = time.monotonic()
    registers = registers if registers is not None else capture.REGISTERS
    create_tables(conn, schema)
    T = lambda t: table(schema, t)
    newest = {}
    for it in items:
        if it.get("sha256"):
            newest[it["url"]] = it
    docs = {}
    for it in newest.values():
        if it["kind"] == "document" and it["sha256"] not in docs:
            docs[it["sha256"]] = it
    rows, withheld, asides, members_of = {}, {}, [], {}
    for it in sorted(newest.values(), key=lambda x: x["url"]):
        if it["kind"] != "page":
            continue
        body = read_bytes(it["sha256"])
        if read.recognise(body) != "register":
            continue
        try:
            out = read.read_register(body, it["sha256"], it["url"])
        except read.NotTheShape as exc:
            asides.append({"document": it["sha256"], "place": None, "stage": "read", "reason": str(exc)})
            continue
        members_of[it["council"]] = members_of.get(it["council"], 0) + len(out["members"])
        for i, r in enumerate(out["rows"], 1):
            key = f"{it['council']}/{r['member']}/{r['place']}"
            rows[key] = dict(r, key=key, council=it["council"], as_at=out["as_at"], read_from="text",
                             reader=read.READER, profile=read.PROFILE, profile_version=read.PROFILE_VERSION)
        for (cat, why), n in out["withheld"].items():
            k = (it["council"], cat, why)
            withheld[k] = withheld.get(k, 0) + n
    reg_rows = []
    for council, (host, page, pdf) in registers.items():
        nd = sum(1 for d in docs.values() if d["council"] == council)
        landing = newest.get(page) if page else None
        hosts = {capture.site_of(h) for h in held}
        if council in capture.TERMS_BAR:
            form = "held: its terms bar automated access"
        elif members_of.get(council):
            form = "html register"
        elif nd > PER_MEMBER_FILES:
            form = "per-member files"
        elif nd:
            form = "pdf register"
        elif capture.site_of(host) in hosts:
            form = "not reached"
        elif page or pdf:
            form = "linked, not found" if landing else "not yet captured"
        else:
            form = "not found"
        why = capture.TERMS_BAR.get(council) or next(
            (w for h, w in held.items() if capture.site_of(h) == capture.site_of(host)), None)
        reg_rows.append({"council": council, "host": host, "form": form, "landing_url": page,
                         "landing_sha256": landing["sha256"] if landing else None, "documents_held": nd,
                         "members_read": members_of.get(council, 0), "why": why})
    return {"registers": _copy(conn, T("registers"), COLUMNS["registers"], reg_rows),
            "documents": _copy(conn, T("documents"), COLUMNS["documents"], docs.values()),
            "interests": _copy(conn, T("interests"), COLUMNS["interests"], rows.values()),
            "withheld": _copy(conn, T("read_withheld"), COLUMNS["read_withheld"],
                              [{"council": c, "category": cat, "why": w, "members": n}
                               for (c, cat, w), n in sorted(withheld.items())]),
            "set_aside": _copy(conn, T("read_set_aside"), COLUMNS["read_set_aside"], asides),
            "seconds": round(time.monotonic() - t0, 1)}


def held_record(conn, schema: str = SCHEMA) -> tuple:
    T = lambda t: table(schema, t)
    if conn.execute("SELECT to_regclass(%s)", (T("capture_items"),)).fetchone()[0] is None:
        return [], {}
    cur = conn.execute(f"SELECT council, url, kind, found_on, asked_at, sha256, why FROM {T('capture_items')} "
                       "ORDER BY asked_at, item_id")
    cols = [d.name for d in cur.description]
    items = [dict(zip(cols, r)) for r in cur.fetchall()]
    held = dict(conn.execute(f"SELECT host, why FROM {T('capture_held_hosts')}").fetchall())
    return items, held


def load(conn, schema: str, log=print) -> int:
    """The merge gate's staging step: the capture's record read under `schema`; with none, empty tables."""
    from registers.councillor_interests import check
    items, held = held_record(conn)
    counts = build(conn, schema, items, held)
    problems = check.reading(conn, schema)
    log(f"{SCHEMA}: {counts['registers']} councils, {counts['documents']} documents held, {counts['interests']} "
        f"interests read, {counts['withheld']} categories withheld into {schema}; " + ("; ".join(problems) or "reconciles"))
    return counts["registers"]


def publish(conn, staging: str, log=print) -> None:
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {table(SCHEMA, t)} SELECT * FROM {table(staging, t)}")
        conn.execute(sql("publish.sql"))
    log(f"{SCHEMA}: published from {staging}")


def job(log=print) -> int:
    from support import db
    from registers.councillor_interests import check
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        items, held = held_record(conn)
        with conn.transaction():
            counts = build(conn, STAGING, items, held)
        problems = check.reading(conn, STAGING)
        detail = (f"{counts['registers']} councils, {counts['documents']} documents held, {counts['interests']} interests "
                  f"read, {counts['withheld']} categories withheld; " + ("; ".join(problems) or "reconciles"))
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
    ap = argparse.ArgumentParser(prog="python -m registers.councillor_interests.load")
    ap.add_argument("--schema", default="scratch_councillor_interests_full")
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
        items, held = held_record(src, a.capture_schema)
    with db.connect(db.OWNER_KEY, a.database) as conn:
        with conn.transaction():
            counts = build(conn, a.schema, items, held)
    for k, v in counts.items():
        print(f"{SCHEMA}: {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
