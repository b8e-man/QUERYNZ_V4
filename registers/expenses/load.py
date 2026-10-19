"""Loading (plan 1b.7, 1.11). The merge gate's staging step calls `load`
to build this lane's tables under a staging schema of the real database,
and `publish` to move the rows into the lane's own tables in one
transaction and refresh the published views. `sample.fill` uses `build`
for the sample, where every module shares one scratch schema, so there
this lane's tables carry its name (`expenses_lines`, …; `table`).

Capture, read, insert. Every document lands by hash; every workbook is read
into one or more release tables or is a catch-log line; every member line
is published or is a catch-log line; every workbook a publisher's listing
names is held or is a catch-log line. `reconcile` states those sums, and
the run record carries them.
"""
import os

from support import jobrun
from support.docstore.landing import read_bytes
from registers.expenses import capture, check, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "expenses"
PRIVATE = "expenses_private"
JOB = "qv4-expenses-load"
STAMP = ("reader", "profile", "profile_version", "read_from", "loaded_at")
COLUMNS_OF = {
    "files": ("document", "kind", "old_path", "url", "label", "captured_at"),
    "set_aside": ("item", "stage", "reason"),
    "releases": ("key", "document", "page", "place", "sheet", "publisher", "title", "period_start", "period_end",
                 "period_basis", "label", "label_start", "label_end", "label_differs", "url", "columns") + STAMP,
    "lines": ("key", "release", "document", "page", "place", "member", "name", "party_printed", "party_label", "party",
              "party_basis", "marks", "categories_sum", "total", "check") + STAMP,
    "figures": ("key", "line", "release", "document", "page", "place", "category", "role", "figure", "printed") + STAMP,
    "totals": ("release", "line_place", "label", "scope", "heading", "total_role", "printed", "rows_sum", "equal", "widest"),
    "notes": ("key", "release", "document", "page", "place", "text"),
}
TABLES = tuple(COLUMNS_OF)


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema[:55]}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    return text.replace(f"{PRIVATE}.", f"{private_of(schema)}.{pre}").replace(f"{SCHEMA}.", f"{schema}.{pre}")


def create_tables(conn, schema: str, shared: bool = False) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    conn.execute(sql("tables.sql", schema, shared))


def wipe(conn, schema: str, shared: bool = False) -> None:
    for t in TABLES:
        conn.execute(f"DELETE FROM {table(schema, t, shared)}")


def _q(col: str) -> str:
    return f'"{col}"' if col == "check" else col


def insert_many(conn, schema: str, t: str, rows: list, shared: bool = False) -> None:
    if not rows:
        return
    cols = COLUMNS_OF[t]
    with conn.cursor() as cur:
        cur.executemany(f"INSERT INTO {table(schema, t, shared)} ({', '.join(_q(c) for c in cols)}) "
                        f"VALUES ({', '.join(['%s'] * len(cols))})", [tuple(r.get(c) for c in cols) for r in rows])


def build(conn, schema: str, held: list, capture_lines: list = (), shared: bool = False) -> dict:
    """held: [(kind, sha256, old path, manifest row or {})] for documents already in the store. Wipes and
    refills this lane's tables under `schema`; returns the counts."""
    create_tables(conn, schema, shared)
    wipe(conn, schema, shared)
    at = read.now()
    c = {"documents": 0, "workbooks": 0, "workbooks_read": 0, "workbooks_aside": 0, "listings": 0, "releases": 0,
         "lines": 0, "lines_published": 0, "lines_aside": 0, "figures": 0, "listed": 0, "listed_held": 0,
         "listed_aside": 0, "capture_lines": len(capture_lines), "set_aside": 0}
    aside = [{"item": i, "stage": "capture", "reason": why} for i, why in capture_lines]
    files, urls = {}, set()
    for kind, sha, path, meta in held:
        if sha in files:
            continue
        files[sha] = kind
        insert_many(conn, schema, "files", [{"document": sha, "kind": kind, "old_path": path, "url": meta.get("url"),
                                             "label": meta.get("name"), "captured_at": meta.get("fetched_at")}], shared)
        c["documents"] += 1
        if meta.get("url"):
            urls.add(meta["url"])
    done = set()
    for kind, sha, path, meta in held:
        if kind not in capture.WORKBOOK_KINDS or sha in done:
            continue
        done.add(sha)
        c["workbooks"] += 1
        o = read.release_rows(read_bytes(sha), sha, kind, meta, at)
        for t in ("releases", "lines", "figures", "totals", "notes"):
            insert_many(conn, schema, t, o[t], shared)
        aside += [{"item": i, "stage": s, "reason": why} for i, s, why in o["set_aside"]]
        if o["releases"]:
            c["workbooks_read"] += 1
        elif any(s in ("workbook", "release") for _, s, _ in o["set_aside"]):
            c["workbooks_aside"] += 1
        c["releases"] += len(o["releases"])
        c["lines"] += len(o["lines"])
        c["lines_published"] += sum(1 for x in o["lines"] if x["check"] in check.PUBLISHED_CHECKS)
        c["lines_aside"] += sum(1 for _, s, _ in o["set_aside"] if s == "arithmetic")
        c["figures"] += len(o["figures"])
    for kind, sha, path, meta in held:
        if kind not in capture.LISTING_KINDS or sha in done:
            continue
        done.add(sha)
        c["listings"] += 1
        for url, name in capture.listed_workbooks(read_bytes(sha), kind):
            c["listed"] += 1
            if url in urls:
                c["listed_held"] += 1
            else:
                c["listed_aside"] += 1
                aside.append({"item": url, "stage": "listing",
                              "reason": f"{name}: listed by the publisher ({os.path.basename(path)}), not held by the old job"})
    insert_many(conn, schema, "set_aside", aside, shared)
    c["set_aside"] = len(aside)
    return c


def reconcile(c: dict) -> list:
    """The catch log's sums, as lines that must all be empty: items in equal items out plus items set aside."""
    bad = []
    if c["documents"] != c["workbooks"] + c["listings"]:
        bad.append(f"documents: {c['documents']} held, {c['workbooks']} workbooks + {c['listings']} listings")
    if c["workbooks"] != c["workbooks_read"] + c["workbooks_aside"]:
        bad.append(f"workbooks: {c['workbooks']}, {c['workbooks_read']} read + {c['workbooks_aside']} set aside")
    if c["lines"] != c["lines_published"] + c["lines_aside"]:
        bad.append(f"lines: {c['lines']}, {c['lines_published']} published + {c['lines_aside']} set aside")
    if c["listed"] != c["listed_held"] + c["listed_aside"]:
        bad.append(f"listed: {c['listed']}, {c['listed_held']} held + {c['listed_aside']} set aside")
    return bad


def held_documents(conn, staging: str = None) -> tuple:
    """Land every candidate file by hash: ([(kind, sha, old path, manifest row)], capture catch-log lines)."""
    man = capture.manifest(staging)
    held = [(kind, ref.sha256, path, man.get(ref.sha256) or {}) for kind, ref, path, new in capture.copy_all(conn, staging)]
    lines = [(sha, f"{folder}/MANIFEST.jsonl lists {name} ({url}) as {sha[:12]}…, whose bytes a later download under the "
                   f"same name has overwritten")
             for folder, sha, name, url in capture.overwritten(staging)]
    lines += [(f"{folder}/{name}", f"{folder}/{name}: no kind matches this file") for folder, name in capture.unrecognised(staging)]
    return held, lines


def load(conn, schema: str, log=print, shared: bool = False) -> dict:
    started = jobrun.now()
    held, lines = held_documents(conn)
    c = build(conn, schema, held, lines, shared)
    bad = reconcile(c)
    detail = (f"{c['documents']} documents; {c['workbooks']} workbooks: {c['workbooks_read']} read, "
              f"{c['workbooks_aside']} set aside; {c['releases']} release tables; {c['lines']} lines: "
              f"{c['lines_published']} published, {c['lines_aside']} set aside; {c['listed']} listed: "
              f"{c['listed_held']} held, {c['listed_aside']} not; into {schema}"
              + (f"; DOES NOT RECONCILE: {bad}" if bad else ""))
    log("expenses: " + detail)
    jobrun.record(JOB, not bad, detail, started, c)
    if bad:
        raise RuntimeError("expenses: the catch log does not reconcile: " + "; ".join(bad))
    return c


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        wipe(conn, SCHEMA)
        for t in TABLES:
            cols = ", ".join(_q(c) for c in COLUMNS_OF[t])
            conn.execute(f"INSERT INTO {SCHEMA}.{t} ({cols}) SELECT {cols} FROM {staging}.{t}")
        conn.execute(sql("publish.sql"))
