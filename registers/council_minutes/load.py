"""Loading (plan 1b.7): `build(conn, schema, listings, captured)` reads every
listing page held into the reading's tables under `schema`; `publish(conn,
staging)` moves them into `council_minutes` and makes the view, in one
transaction. sample.py uses the same `build`.

A meeting row met on several listings (the weekly asks of one instance) is
the newest listing's; a row that has dropped off the newest (last year's,
after the year turns) stays, cited to the listing that last showed it. Each
meeting's minutes column says what the capture holds of its minutes PDF:
landed (its hash), held by the old estate (the old listed hash, to copy),
failed, not yet captured, html only, or no minutes listed. Listings in equal
listings read plus set aside; the build raises if not.

    python -m registers.council_minutes.load [--schema scratch_…] [--database querynz_v4_sample]
    python -m registers.council_minutes.load --job

Every line printed is a count.
"""
import argparse
import os
import re
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.council_minutes import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "council_minutes"
JOB = "qv4-council-minutes-load"
STAGING = "staging_council_minutes_load"
TABLES = ("read_listings", "meetings", "documents", "read_set_aside")
_CITE = ("document", "page", "place")
COLUMNS = {
    "read_listings": ("document", "host", "asked_at", "state", "year", "grid_rows", "meetings", "documents"),
    "meetings": ("key", "council", "host", "body", "meeting_date", "meeting_time", "kind", "code", "documents",
                 "minutes_file", "minutes_url", "minutes_sha256", "minutes_held") + _CITE +
                ("listing_url", "read_from", "reader", "profile", "profile_version"),
    "documents": ("key", "meeting_key", "kind", "format", "file", "url", "size_as_printed", "sha256", "held") + _CITE,
    "read_set_aside": ("document", "place", "stage", "reason"),
}
#: a meeting's kind, from the words of its listed name (first match wins)
KINDS = (("supplementary", "supplementary"), ("extraordinary", "extraordinary"), ("workshop", "workshop"),
         ("hearing", "hearing"), ("briefing", "briefing"))
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


def kind_of(body: str) -> str:
    low = body.lower()
    return next((k for w, k in KINDS if w in low), "meeting")


def minutes_of(docs: list, captured: dict):
    """(file, url, sha256, held) for a meeting's minutes: the PDF, else the HTML."""
    mins = [d for d in docs if d["kind"] == "minutes"]
    if not mins:
        return None, None, None, "no minutes listed"
    pdf = next((d for d in mins if d["format"] == "pdf"), None)
    if pdf is None:
        return mins[0]["file"], mins[0]["url"], None, "html only"
    state, sha = captured.get(pdf["url"], ("not yet captured", None))
    return pdf["file"], pdf["url"], sha, state


def build(conn, schema: str, listings: list, captured: dict, read_bytes=read_bytes) -> dict:
    """`listings`: [(host, sha256, asked_at)], newest first; `captured`: url → (state, sha256) from the capture."""
    t0 = time.monotonic()
    create_tables(conn, schema)
    T = lambda t: table(schema, t)
    ledger, meetings, documents, asides = [], {}, {}, []
    for host, sha, asked_at in listings:
        base = f"https://{host}"
        body = read_bytes(sha)
        try:
            out = read.read_listing(body, sha, base)
        except read.NotTheShape as exc:
            asides.append({"document": sha, "place": None, "stage": "read", "reason": str(exc)})
            ledger.append({"document": sha, "host": host, "asked_at": asked_at, "state": "set aside"})
            continue
        docs_of = {}
        for d in out["documents"]:
            docs_of.setdefault(d["meeting_key"], []).append(d)
            if d["key"] not in documents:
                state, dsha = captured.get(d["url"], ("listed", None))
                documents[d["key"]] = dict(d, sha256=dsha, held=state)
        for m in out["meetings"]:
            if m["key"] in meetings:
                continue
            if m["meeting_date"] is None:
                asides.append({"document": sha, "place": m["place"], "stage": "read", "reason": "no date in the row"})
                continue
            f, u, s, held = minutes_of(docs_of.get(m["key"], []), captured)
            meetings[m["key"]] = dict(m, council=capture.COUNCIL_OF_HOST.get(host, host), kind=kind_of(m["body"]),
                                      minutes_file=f, minutes_url=u, minutes_sha256=s, minutes_held=held,
                                      listing_url=base + "/", read_from="text", reader=read.READER,
                                      profile=read.PROFILE, profile_version=read.PROFILE_VERSION)
        ledger.append({"document": sha, "host": host, "asked_at": asked_at, "state": "read", "year": out["year"],
                       "grid_rows": capture.grid_rows(body), "meetings": len(out["meetings"]),
                       "documents": len(out["documents"])})
    if len(ledger) != len({s for _, s, _ in listings}):
        raise AssertionError(f"{SCHEMA}: {len(listings)} listings held, {len(ledger)} in the ledger")
    return {"meetings": _copy(conn, T("meetings"), COLUMNS["meetings"], meetings.values()),
            "documents": _copy(conn, T("documents"), COLUMNS["documents"], documents.values()),
            "set_aside": _copy(conn, T("read_set_aside"), COLUMNS["read_set_aside"], asides),
            "listings": _copy(conn, T("read_listings"), COLUMNS["read_listings"], ledger),
            "seconds": round(time.monotonic() - t0, 1)}


def held(conn, schema: str = SCHEMA) -> tuple:
    """(listings newest first [(host, sha256, asked_at)], captured {url: (state, sha256)}) from the capture's record."""
    T = lambda t: table(schema, t)
    if conn.execute("SELECT to_regclass(%s)", (T("capture_listings"),)).fetchone()[0] is None:
        return [], {}
    ls = [tuple(r) for r in conn.execute(
        f"SELECT DISTINCT ON (sha256) host, sha256, asked_at FROM {T('capture_listings')} WHERE sha256 IS NOT NULL "
        "ORDER BY sha256, asked_at DESC")]
    ls.sort(key=lambda r: r[2], reverse=True)
    cap = {r[0]: (r[1], r[2]) for r in conn.execute(f"SELECT url, state, sha256 FROM {T('capture_documents')}")}
    return ls, cap


def load(conn, schema: str, log=print) -> int:
    """The merge gate's staging step (support/staging): every listing held, read under `schema`; with none held the
    tables are made empty. Problems the reading's check finds are logged, as the job logs them."""
    from registers.council_minutes import check
    listings, cap = held(conn)
    if not listings:
        create_tables(conn, schema)
        log(f"{SCHEMA}: no listing is held; nothing read into {schema}")
        return 0
    counts = build(conn, schema, listings, cap)
    problems = check.reading(conn, schema)
    log(f"{SCHEMA}: {counts['meetings']} meetings, {counts['documents']} documents listed, {counts['set_aside']} "
        f"set aside into {schema}; " + ("; ".join(problems) or "reconciles"))
    return counts["meetings"]


def publish(conn, staging: str, log=print) -> None:
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {table(SCHEMA, t)} SELECT * FROM {table(staging, t)}")
        conn.execute(sql("publish.sql"))
    log(f"{SCHEMA}: published from {staging}")


def job(log=print) -> int:
    """qv4-council-minutes-load: build in staging, hold it to the reading's checks, publish only then."""
    from support import db
    from registers.council_minutes import check
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        listings, cap = held(conn)
        if not listings:
            log(f"{SCHEMA}: no listing is held; nothing loaded")
            jobrun.record(JOB, False, "no listing is held", started, {})
            return 1
        with conn.transaction():
            counts = build(conn, STAGING, listings, cap)
        problems = check.reading(conn, STAGING)
        detail = (f"{counts['meetings']} meetings, {counts['documents']} documents listed, {counts['set_aside']} set "
                  "aside; " + ("; ".join(problems) or "reconciles"))
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
    ap = argparse.ArgumentParser(prog="python -m registers.council_minutes.load")
    ap.add_argument("--schema", default="scratch_council_minutes_full")
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
        listings, cap = held(src, a.capture_schema)
    with db.connect(db.OWNER_KEY, a.database) as conn:
        with conn.transaction():
            counts = build(conn, a.schema, listings, cap)
    for k, v in counts.items():
        print(f"{SCHEMA}: {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
