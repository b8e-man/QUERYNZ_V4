"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Capture (the manifest and the window's pages, by hash), read each distinct
document once from the store, insert its rows, and list every capture in
`pages` with what the reading made of it. Items in equal items out plus
items set aside: every capture is a page row; every name a reading met is
a role row or a catch-log line.

The job's run record is `qv4-party-boards-load` (the integrator adds it to
the catalogue; this lane does not edit it).
"""
import datetime as dt
import os

from support import jobrun
from support.docstore.landing import read_bytes
from registers.party_boards import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "party_boards"
TABLES = ("roles", "pages", "set_aside")
JOB = "qv4-party-boards-load"
COLUMNS = {
    "roles": ("key", "document", "page", "place", "party", "url", "captured_on", "last_captured_on", "captures",
              "capture_kind", "archive_url", "shape", "section", "name_as_declared", "name", "qualifier", "role",
              "role_basis", "tier", "read_from", "reader", "profile", "profile_version", "loaded_at"),
    "pages": ("document", "ts", "url", "party", "captured_on", "capture_kind", "archive_url", "status", "shape",
              "reason", "rows", "set_aside", "reader", "profile", "profile_version", "loaded_at"),
}


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.party_boards_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    return text.replace(f"{SCHEMA}.", f"{schema}.{SCHEMA + '_' if shared else ''}")


def create_tables(conn, schema: str, shared: bool = False) -> None:
    """The lane's tables as tables.sql has them now, made again on every
    build: every row is rebuilt from documents."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _insert(conn, name: str, cols: tuple, row: dict) -> None:
    conn.execute(f"INSERT INTO {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) "
                 f"VALUES ({', '.join(['%s'] * len(cols))})", tuple(row.get(c) for c in cols))


def build(conn, schema: str, landed: list, before: list, manifest_sha: str = None, shared: bool = False,
          loaded_at: str = None, data_of=read_bytes) -> dict:
    """landed: [capture.Capture] whose bytes are in the store; before: the
    captures before the window, listed and not landed. Wipes and fills
    `schema`; returns the counts."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    create_tables(conn, schema, shared)
    prof = read.profile()
    roles_t, pages_t, aside_t = (table(schema, t, shared) for t in TABLES)
    counts = {"captures": len(landed) + len(before), "documents": 0, "rows": 0, "set_aside": 0, "read": 0,
              "board section, no names": 0, "drop-note": 0, "before the window, not landed": len(before)}
    by_party = {}
    for sha, caps in sorted(capture.by_document(landed).items()):
        caps = sorted(caps, key=lambda c: c.ts)
        first, last = caps[0], caps[-1]
        got = read.read(data_of(sha), sha, first, loaded_at, prof)
        counts["documents"] += 1
        counts[got.status] += 1
        for row in got.rows:
            row.update(party=first.party, url=first.url, captured_on=first.captured_on, last_captured_on=last.captured_on,
                       captures=len(caps), capture_kind=first.kind, archive_url=first.archive_url)
            _insert(conn, roles_t, COLUMNS["roles"], row)
        for place, why in got.set_aside:
            conn.execute(f"INSERT INTO {aside_t} (item, stage, reason) VALUES (%s, 'read', %s)", (f"{sha}/{place}", why))
        counts["rows"] += len(got.rows)
        counts["set_aside"] += len(got.set_aside)
        by_party[first.party] = by_party.get(first.party, 0) + len(got.rows)
        for c in caps:
            _insert(conn, pages_t, COLUMNS["pages"], {
                "document": sha, "ts": c.ts, "url": c.url, "party": c.party, "captured_on": c.captured_on,
                "capture_kind": c.kind, "archive_url": c.archive_url, "status": got.status, "shape": got.shape,
                "reason": got.reason, "rows": len(got.rows) if c is first else 0,
                "set_aside": len(got.set_aside) if c is first else 0, "reader": read.READER, "profile": read.PROFILE,
                "profile_version": int(prof["version"]), "loaded_at": loaded_at})
    for c in before:
        _insert(conn, pages_t, COLUMNS["pages"], {
            "document": c.sha256, "ts": c.ts, "url": c.url, "party": c.party, "captured_on": c.captured_on,
            "capture_kind": c.kind, "archive_url": c.archive_url, "status": "before the window, not landed",
            "reason": f"captured before {capture.FIRST_YEAR} (ruling 71)", "rows": 0, "set_aside": 0,
            "loaded_at": loaded_at})
    if manifest_sha:
        _insert(conn, pages_t, COLUMNS["pages"], {"document": manifest_sha, "ts": "", "url": "", "capture_kind": "manifest",
                                                  "status": "the capture's index", "rows": 0, "set_aside": 0,
                                                  "loaded_at": loaded_at})
    counts["by_party"] = by_party
    return counts


def load(conn, schema: str, log=print) -> int:
    """The manifest and the window's pages copied by hash, everything read,
    under `schema`. Returns the role count."""
    started = jobrun.now()
    landed, before = capture.copy_all(conn)
    from support.docstore import sha256_file
    manifest_sha = sha256_file(os.path.join(capture.FOLDER, capture.MANIFEST))
    counts = build(conn, schema, landed, before, manifest_sha)
    by_party = counts.pop("by_party")
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    for p, n in sorted(by_party.items()):
        log(f"party_boards: {p}: {n} role(s)")
    log("party_boards: " + detail)
    jobrun.record(JOB, True, detail, started, {**counts, "by_party": by_party})
    return counts["rows"]


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        conn.execute(sql("publish.sql"))
