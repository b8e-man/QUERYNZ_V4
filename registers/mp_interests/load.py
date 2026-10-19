"""Loading (plan 1b.7, 1.11). The merge gate's staging step calls `load`
to build this lane's tables under a staging schema of the real database,
and `publish` to move the rows into the lane's own tables in one
transaction and refresh the published views. `sample.fill` uses `build`
for the sample, where every module shares one scratch schema, so there
this lane's tables carry its name (`mp_interests_declarations`, …).

Capture, read, insert. Every edition lands by hash and is read or is a
catch-log line; every declaration parsed is published (its text withheld
where it is real property) or is a catch-log line; every member's return
carries declarations, a printed statement, or a catch-log line. `reconcile`
states those sums, and the run record carries them.
"""
import os

from support import jobrun
from support.docread.pages import text_pages
from support.docstore.landing import read_bytes
from registers.mp_interests import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "mp_interests"
PRIVATE = "mp_interests_private"
JOB = "qv4-mp-interests-load"
STAMP = ("reader", "profile", "profile_version", "read_from", "loaded_at")
COLUMNS_OF = {
    "files": ("document", "year_label", "old_path", "captured_at"),
    "set_aside": ("item", "stage", "reason"),
    "editions": ("key", "document", "page", "place", "year_label", "as_at", "as_at_printed", "categories", "members",
                 "declarations", "wrapped", "annex_page") + STAMP,
    "members": ("key", "edition", "document", "page", "place", "as_at", "printed", "member", "name", "party_label",
                "party", "party_basis", "electorate", "statement") + STAMP,
    "declarations": ("key", "edition", "member", "document", "page", "place", "as_at", "number_printed", "heading",
                     "category", "text", "withheld") + STAMP,
    "numbering": ("edition", "number", "intro_heading", "intro_category", "body_headings", "body_category", "agrees"),
}
TABLES = tuple(COLUMNS_OF)
#: the private twin's tables (hard limit 15): never published, never granted to a reader
PRIVATE_COLUMNS_OF = {"declaration_text": ("key", "text")}


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
    for t in PRIVATE_COLUMNS_OF:
        conn.execute(f"DELETE FROM {table(private_of(schema), t, shared)}")


def insert_many(conn, schema: str, t: str, rows: list, shared: bool = False) -> None:
    if not rows:
        return
    cols = COLUMNS_OF.get(t) or PRIVATE_COLUMNS_OF[t]
    with conn.cursor() as cur:
        cur.executemany(f"INSERT INTO {table(schema, t, shared)} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
                        [tuple(r.get(c) for c in cols) for r in rows])


def build(conn, schema: str, held: list, capture_lines: list = (), shared: bool = False) -> dict:
    """held: [(year label, sha256, old path, captured_at)] for editions already in the store. Wipes and
    refills this lane's tables under `schema`; returns the counts."""
    create_tables(conn, schema, shared)
    wipe(conn, schema, shared)
    at = read.now()
    c = {"documents": 0, "editions_read": 0, "editions_aside": 0, "members": 0, "members_with_declarations": 0,
         "members_with_statement": 0, "members_aside": 0, "parsed": 0, "declarations": 0, "withheld": 0,
         "declarations_aside": 0, "lines_aside": 0, "numbers_differ": 0, "capture_lines": len(capture_lines)}
    aside = [{"item": i, "stage": "capture", "reason": why} for i, why in capture_lines]
    seen = set()
    for year, sha, path, captured in held:
        if sha in seen:
            continue
        seen.add(sha)
        c["documents"] += 1
        insert_many(conn, schema, "files", [{"document": sha, "year_label": year, "old_path": path,
                                             "captured_at": captured}], shared)
        o = read.edition_rows(text_pages(read_bytes(sha)), sha, year, at)
        aside += [{"item": i, "stage": s, "reason": why} for i, s, why in o["set_aside"]]
        if o["edition"] is None:
            c["editions_aside"] += 1
            if not any(s == "edition" for _, s, _ in o["set_aside"]):
                aside.append({"item": sha, "stage": "edition", "reason": "no member read"})
            continue
        c["editions_read"] += 1
        insert_many(conn, schema, "editions", [o["edition"]], shared)
        insert_many(conn, schema, "members", o["members"], shared)
        insert_many(conn, schema, "declarations", o["declarations"], shared)
        insert_many(conn, private_of(schema), "declaration_text", o["private"], shared)
        insert_many(conn, schema, "numbering", o["numbering"], shared)
        verbatim = sum(1 for _, s, _ in o["set_aside"] if s == "verbatim")
        c["parsed"] += o["edition"]["declarations"]
        c["declarations"] += len(o["declarations"])
        c["withheld"] += len(o["private"])
        c["declarations_aside"] += verbatim
        c["lines_aside"] += sum(1 for _, s, _ in o["set_aside"] if s == "line")
        c["numbers_differ"] += sum(1 for n in o["numbering"] if not n["agrees"])
        with_d = {d["member"] for d in o["declarations"]}
        for m in o["members"]:
            c["members"] += 1
            if m["key"] in with_d:
                c["members_with_declarations"] += 1
            elif m["statement"]:
                c["members_with_statement"] += 1
            else:
                c["members_aside"] += 1
                aside.append({"item": m["key"], "stage": "member",
                              "reason": f"{m['printed']}: neither a declaration published nor a statement printed"})
    insert_many(conn, schema, "set_aside", aside, shared)
    return c


def reconcile(c: dict) -> list:
    """The catch log's sums, as lines that must all be empty: items in equal items out plus items set aside."""
    bad = []
    if c["documents"] != c["editions_read"] + c["editions_aside"]:
        bad.append(f"editions: {c['documents']} held, {c['editions_read']} read + {c['editions_aside']} set aside")
    if c["parsed"] != c["declarations"] + c["declarations_aside"]:
        bad.append(f"declarations: {c['parsed']} parsed, {c['declarations']} published + {c['declarations_aside']} set aside")
    if c["members"] != c["members_with_declarations"] + c["members_with_statement"] + c["members_aside"]:
        bad.append(f"members: {c['members']}, {c['members_with_declarations']} with declarations + "
                   f"{c['members_with_statement']} with a statement + {c['members_aside']} set aside")
    return bad


def held_documents(conn, folder: str = None) -> tuple:
    held = [(year, ref.sha256, path, None) for year, ref, path, new in capture.copy_all(conn, folder)]
    lines = [(f"var/mp_interests/{n}", f"var/mp_interests/{n}: not an edition (mp-<year>.pdf)")
             for n in capture.unrecognised(folder)]
    return held, lines


def load(conn, schema: str, log=print, shared: bool = False) -> dict:
    started = jobrun.now()
    held, lines = held_documents(conn)
    c = build(conn, schema, held, lines, shared)
    bad = reconcile(c)
    detail = (f"{c['documents']} editions: {c['editions_read']} read; {c['members']} returns; {c['parsed']} declarations: "
              f"{c['declarations']} published ({c['withheld']} withheld), {c['declarations_aside']} set aside; "
              f"{c['numbers_differ']} numbers differ from their edition's list; into {schema}"
              + (f"; DOES NOT RECONCILE: {bad}" if bad else ""))
    log("mp_interests: " + detail)
    jobrun.record(JOB, not bad, detail, started, c)
    if bad:
        raise RuntimeError("mp_interests: the catch log does not reconcile: " + "; ".join(bad))
    return c


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        wipe(conn, SCHEMA)
        for t in TABLES:
            cols = ", ".join(COLUMNS_OF[t])
            conn.execute(f"INSERT INTO {SCHEMA}.{t} ({cols}) SELECT {cols} FROM {staging}.{t}")
        for t, cols in PRIVATE_COLUMNS_OF.items():
            cols = ", ".join(cols)
            conn.execute(f"INSERT INTO {PRIVATE}.{t} ({cols}) SELECT {cols} FROM {private_of(staging)}.{t}")
        conn.execute(sql("publish.sql"))
