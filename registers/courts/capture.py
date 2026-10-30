"""How this lane's documents arrive (rulings 126 and 127, 30 October 2026).
The estate fetches nothing from any court site. Arthur's provider captures
the courts' pages and files and serves them through the ingest MCP
`query-nz-ingest`; the shared pull `support/mcpsource` (job `qv4-mcp-pull`)
lands each record of the MCP's `courts` corpus as a document of source
`query-nz` (named `courts/<id>`), and each file a record points at (a case
page, a judgment PDF, a media release, a transcript, counsel's submissions)
by hash under the record's url, with one `mcpsource.files` row per pointer.
This lane's listing is the corpus's records; its documents are those files,
read from the store by hash. Nothing here opens a connection.

    records(conn, mcp_schema)        the corpus's records, one per record id, the version the pull saw last
    caught(conn, mcp_schema)         the pull's unresolved catch lines for the corpus (records and files)
    old_listing(conn)                the old estate's once-only listing (courts-1), as held, or None
    old_listing_gap(entries, recs)   the held judgments of that listing the corpus does not carry: catch-log lines

The old listing (`LISTING_SHA`, 359 documents exported 21 October 2026) is
kept as a document in the store and is no longer a source: a document it
names that the corpus lacks is a line in the catch log, stage `listing`,
reported to the provider, never a row (ruling 127).
"""
import json
import os

from support.docstore.landing import path_for, read_bytes

CORPUS = "courts"
SOURCE = "query-nz"
MCP_SCHEMA = "mcpsource"
SOURCE_NOTE = ("a file of the query-nz ingest MCP's courts corpus, captured by Arthur's provider and landed by hash "
               "under the record's url (rulings 126, 127); the estate fetched nothing from a court site")
KINDS = ("case_page", "judgment_pdf", "media_release")
#: the old estate's listing of judgments, exported once by courts-1 (21 October 2026, 14:44): a document, not a source
LISTING_SHA = "8285d0068216f1675561dc260eb370ca9b6f1d78fae26e3d483d3a35aab79572"
LISTING_NAME = "courts-judgments-old-estate.jsonl"


def _has(conn, mcp_schema: str, table: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s",
                             (mcp_schema, table)).fetchone())


def record_of(sha: str) -> dict:
    """The record's JSON as the pull landed it (keys sorted, no `seq`)."""
    return json.loads(read_bytes(sha))


def records(conn, mcp_schema: str = MCP_SCHEMA) -> list:
    """One entry per record id of the corpus: the version the pull saw last
    (by `landed_at`, never the highest `seq`), with its file pointer from
    `mcpsource.files`. A schema with no pull record answers nothing."""
    if not _has(conn, mcp_schema, "arrivals") or not _has(conn, mcp_schema, "files"):
        return []
    rows = conn.execute(f"""
        SELECT DISTINCT ON (a.record_id) a.record_id, a.seq, a.sha256, a.url, f.content_type, f.capture_sha256, f.state, f.bytes
          FROM {mcp_schema}.arrivals a
          LEFT JOIN {mcp_schema}.files f ON f.corpus = a.corpus AND f.record_sha256 = a.sha256
         WHERE a.corpus = %s
         ORDER BY a.record_id, a.landed_at DESC, a.seq DESC""", (CORPUS,)).fetchall()
    return [entry(*r) for r in rows]


def entry(record_id: str, seq, record_sha: str, url: str, content_type, capture_sha, state, nbytes, rec: dict = None) -> dict:
    """The lane's entry for one record: the record's own fields the lane
    uses (kind, case_slug, fetched_at) read from the landed record."""
    rec = rec if rec is not None else (record_of(record_sha) if os.path.exists(path_for(record_sha)) else {})
    cap = rec.get("capture") or {}
    return {"record_id": record_id, "seq": seq, "record": record_sha, "url": url or rec.get("url"),
            "kind": rec.get("kind"), "case_slug": rec.get("case_slug") or None, "court_hint": rec.get("court") or None,
            "fetched_at": cap.get("fetched_at") or rec.get("fetched_at"),
            "content_type": content_type or rec.get("content_type"), "capture": capture_sha or cap.get("sha256"),
            "state": state or ("waiting" if cap.get("sha256") else "no file"), "bytes": nbytes or cap.get("bytes"),
            "source": SOURCE, "note": SOURCE_NOTE}


def caught(conn, mcp_schema: str = MCP_SCHEMA) -> list:
    """[(record_id, seq, stage, reason)]: the pull's catch lines for the corpus not yet resolved."""
    if not _has(conn, mcp_schema, "catch"):
        return []
    return [tuple(r) for r in conn.execute(f"SELECT record_id, seq, stage, reason FROM {mcp_schema}.catch "
                                           "WHERE corpus = %s AND resolved_at IS NULL ORDER BY seq", (CORPUS,))]


def old_listing(sha: str = LISTING_SHA) -> list:
    """The old estate's listing as held: [{sha256, source, ref, url, …}], or
    [] when the store does not hold it (the sample database's store does)."""
    if not os.path.exists(path_for(sha)):
        return []
    out = []
    for line in read_bytes(sha).decode("utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def old_listing_gap(entries: list, recs: list) -> list:
    """The judgments the old listing names, held by hash, that no corpus
    record points at (by hash or by url): [(sha256, stage, reason)], one
    catch-log line each. The Waitangi Tribunal's documents are not courts
    documents and are not counted (ruling 127 names the 148 judgments)."""
    by_hash = {r["capture"] for r in recs if r.get("capture")}
    by_url = {r["url"] for r in recs if r.get("url")}
    out = []
    for e in entries:
        if e.get("source") == "waitangitribunal.govt.nz":
            continue
        sha = e.get("sha256")
        if not sha or sha in by_hash or (e.get("url") and e["url"] in by_url):
            continue
        held = os.path.exists(path_for(sha))
        out.append((sha, "listing", f"the old estate's listing names it ({e.get('ref') or e.get('url')}); "
                                     f"{'held' if held else 'not held'}; no record of the MCP's courts corpus points at it: "
                                     "reported to the provider, not a row (ruling 127)"))
    return out
