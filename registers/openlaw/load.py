"""Loading (plan 1b.7): `build(conn, schema, docs)` reads the listed pages
into the reading's tables under `schema`; `publish(conn, staging)` moves them
into `openlaw` and `openlaw_private` and makes the views, in one
transaction. `fill` in sample.py uses the same `build`.

Idempotent per listing: the reading's tables are dropped and made again and
every row read again from the same pages inside one transaction, so a
second load gives the same rows under the same keys (only `loaded_at`
moves). The capture's tables are never touched. Records in equal case rows
plus superseded plus set aside, page by page, in the `read_pages` ledger;
a full load that does not reconcile raises and publishes nothing.

    python -m registers.openlaw.load [--schema scratch_openlaw_full] [--database querynz_v4_sample]
    python -m registers.openlaw.load --job      # qv4-openlaw-load: build in staging, check, publish

Every line printed is a count.
"""
import argparse
import collections
import json
import os
import re
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.openlaw import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "openlaw"
PRIVATE = "openlaw_private"
JOB = "qv4-openlaw-load"
SCRATCH = "scratch_openlaw_full"
STAGING = "staging_openlaw_load"
TABLES = ("read_pages", "cases", "parties", "citations", "statutes", "read_set_aside")
PRIVATE_TABLES = ("party_names", "case_titles")
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "read_pages": ("document", "cases", "typed", "set_aside", "superseded", "skipped"),
    "cases": ("key", "openlaw_id", "citation", "citations", "court", "court_name", "registry", "filing_number",
              "decided_on", "pdf_url", "suppressed", "suppression_marks", "parties_from", "is_valid",
              "source_modified_at", "parsers_version") + _CITE,
    "parties": ("key", "case_key", "role", "position", "anonymised", "crown", "withheld", "from_source") + _CITE,
    "citations": ("key", "citing_key", "cited_key", "citation_count") + _CITE,
    "statutes": ("key", "case_key", "legislation_id", "legislation_title", "legislation_year", "section", "mentions",
                 "extraction_confidence") + _CITE,
    "read_set_aside": ("document", "place", "stage", "reason"),
    "party_names": ("key", "name"),
    "case_titles": ("key", "title"),
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t` (a private table: in the schema's private twin); in a
    schema every module shares (the sample's), `schema.openlaw_t`."""
    where = private_of(schema) if t in PRIVATE_TABLES else schema
    return f"{where}.{SCHEMA}_{t}" if shared else f"{where}.{t}"


_NAMES = re.compile(r"(?<![A-Za-z0-9_])openlaw(_private)?\.")


def sql(name: str, schema: str = SCHEMA, shared: bool = False, pub: str = "pub") -> str:
    """A file of this lane's SQL under `schema` (and its private twin), in
    one pass; for tables.sql, the reading's part only. `pub`: where the views
    go (a session's tests give a scratch schema)."""
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    if name == "tables.sql":
        text = capture.READING + text.split(capture.READING, 1)[1]
    pre = f"{SCHEMA}_" if shared else ""
    text = _NAMES.sub(lambda m: f"{private_of(schema) if m.group(1) else schema}.{pre}", text)
    if pub != "pub":
        text = re.sub(r"(?<![A-Za-z0-9_])pub\.", f"{pub}.", text)
    return text


def create_tables(conn, schema: str, shared: bool = False) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    for t in TABLES + PRIVATE_TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def build(conn, schema: str, docs: list, read_bytes=read_bytes, only: set = None, shared: bool = False,
          prof: dict = None) -> dict:
    """Read every listed page (oldest landed first) into the tables under
    `schema`. `only`: the case ids to read (the sample's); None for all.
    Returns the counts."""
    t0 = time.monotonic()
    prof = prof or read.profile()
    create_tables(conn, schema, shared)
    T = lambda t: table(schema, t, shared)
    out = {t: [] for t in ("cases", "parties", "citations", "statutes", "party_names", "case_titles")}
    asides, ledger = [], {}
    for what, sha, x in read.read_pages(docs, read_bytes, prof, only):
        if what == "page":
            ledger.setdefault(sha, {"document": sha, "cases": 0, "typed": 0, "set_aside": 0, "superseded": 0, "skipped": 0})
            ledger[sha]["cases"] += x
        elif what == "case":
            ledger[sha]["typed"] += 1
            out["cases"].append(x["case"])
            if x["title"]:
                out["case_titles"].append(x["title"])
            for k in ("parties", "citations", "statutes"):
                out[k] += x[k]
            out["party_names"] += x["names"]
            asides += x["asides"]
        elif what == "superseded":
            ledger[sha]["superseded"] += 1
        elif what == "aside":
            asides.append(x)
            if x["stage"] != "recognise":
                ledger[sha]["set_aside"] += 1
    for p in ledger.values():
        p["skipped"] = p["cases"] - p["typed"] - p["set_aside"] - p["superseded"]
    if only is None:
        bad = [p for p in ledger.values() if p["skipped"]]
        if bad:
            raise AssertionError(f"openlaw: {len(bad)} page(s) do not reconcile (records in ≠ typed + superseded + set aside)")
    counts = collections.Counter()
    for t in ("cases", "parties", "citations", "statutes", "party_names", "case_titles"):
        counts[t] = _copy(conn, T(t), COLUMNS[t], out[t])
    _copy(conn, T("read_pages"), COLUMNS["read_pages"], ledger.values())
    counts["set_aside"] = _copy(conn, T("read_set_aside"), COLUMNS["read_set_aside"], asides)
    counts["pages"] = len(ledger)
    counts["superseded"] = sum(p["superseded"] for p in ledger.values())
    counts["suppressed"] = sum(1 for c in out["cases"] if c["suppressed"])
    counts["withheld"] = sum(1 for p in out["parties"] if p["withheld"])
    counts["seconds"] = round(time.monotonic() - t0, 1)
    return dict(counts)


def listing(conn, schema: str = SCHEMA) -> list:
    """Every landed page, oldest first (pass, then page)."""
    if conn.execute("SELECT to_regclass(%s)", (f"{schema}.capture_pages",)).fetchone()[0] is None:
        return []
    return list(dict.fromkeys(r[0] for r in conn.execute(
        f"SELECT sha256 FROM {schema}.capture_pages ORDER BY pass_id, page_no")))


def publish(conn, staging: str, log=print) -> None:
    """The reading's tables from `staging` into `openlaw`/`openlaw_private`
    and the views of publish.sql, in one transaction. The capture's tables stay."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES + PRIVATE_TABLES:
            conn.execute(f"INSERT INTO {table(SCHEMA, t)} SELECT * FROM {table(staging, t)}")
        conn.execute(sql("publish.sql"))
    log(f"openlaw: published from {staging}")


def unchanged(conn, listed: list) -> bool:
    """True when the published reading read exactly the pages listed now (register rule 10)."""
    if conn.execute("SELECT to_regclass(%s)", (f"{SCHEMA}.read_pages",)).fetchone()[0] is None:
        return False
    return {r[0] for r in conn.execute(f"SELECT document FROM {SCHEMA}.read_pages")} == set(listed)


def job(log=print) -> int:
    """qv4-openlaw-load: build in STAGING, hold it to the reading's checks,
    publish only then. Held, like the capture, until OpenLaw authorises."""
    from support import db
    from registers.openlaw import check
    started = jobrun.now()
    if not capture.authorisation():
        log("openlaw: held: OpenLaw has not authorised copies (API terms 3.6(a)); nothing loaded")
        jobrun.record(JOB, True, "held: no authorisation on file", started, {})
        return 0
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '600s'")
        listed = listing(conn)
        if unchanged(conn, listed):
            log("openlaw: the listing is the one published; nothing loaded")
            jobrun.record(JOB, True, "unchanged", started, {})
            return 0
        with conn.transaction():
            counts = build(conn, STAGING, listed)
            conn.execute(sql("publish.sql", STAGING, pub=STAGING))
        f = check.reading(conn, STAGING, views=STAGING)
        detail = (f"{counts['cases']} cases, {counts['parties']} parties ({counts['withheld']} withheld), "
                  f"{counts['citations']} citations, {counts['statutes']} statute links, {counts['set_aside']} set aside; "
                  + ("; ".join(f["problems"]) or "reconciles"))
        if not f["ok"]:
            log("openlaw: RED, nothing published: " + detail)
            jobrun.record(JOB, False, "nothing published: " + detail, started, {})
            return 1
        publish(conn, STAGING, log)
    jobrun.record(JOB, True, "published: " + detail, started, counts)
    return 0


def main(argv=None) -> int:
    from support import db
    ap = argparse.ArgumentParser(prog="python -m registers.openlaw.load")
    ap.add_argument("--schema", default=SCRATCH)
    ap.add_argument("--database", default="querynz_v4_sample")
    ap.add_argument("--job", action="store_true")
    a = ap.parse_args(argv)
    if a.job:
        return job()
    if not a.schema.startswith(("scratch_", "staging_")):
        print("openlaw: a session loads only a scratch or staging schema")
        return 2
    with db.connect(db.READ_KEY, "querynz_v4") as src:
        src.execute("SET statement_timeout = '60s'")
        docs = listing(src)
    with db.connect(db.OWNER_KEY, a.database) as conn:
        with conn.transaction():
            counts = build(conn, a.schema, docs)
    for k, v in counts.items():
        print(f"openlaw: {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
