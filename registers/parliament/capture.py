"""How this lane's documents arrive (rulings 78, 94, 96). The estate does
not capture parliament.nz: Arthur's provider captured it on its own box,
outside the estate (through a challenge, with a proxy pool, which hard
limit 6 forbids the estate's own capture), and serves it through the ingest
MCP `query-nz-ingest`. The shared pull `support/mcpsource` (job
`qv4-mcp-pull`) lands each record of the parliament corpora whole as a
document of source `query-nz` and writes one `mcpsource.arrivals` row per
record taken. This lane fetches nothing; the fetch gate holds the host.

    arrivals(conn, mcp_schema)    [(corpus, sha256, seq, record id, served)] in the order the pull landed them
    caught(conn, mcp_schema)      [(corpus, seq, stage, reason)]: the pull's catch lines not yet landed
    corpora_of(conn, shas)        {sha256: corpus} from the documents' own names (`<corpus>/<id>`), for the sample

`served`: whether the MCP still serves the record. The MCP removes records
(246 written questions on 26 October) and every later place moves; the
re-walk lands what it still serves at its new place. So a record is served
when it is the last record landed at some place below the cursor; one that
holds no place any more was withdrawn by the source. Its row is kept (a
captured document is never deleted) and marked.
"""
CORPORA = ("parliament-written-questions", "parliament-bills", "parliament-bills-historical",
           "parliament-sc-submissions", "parliament-sc-reports", "parliament-sops", "parliament-wayback")
WRITTEN_QUESTIONS = "parliament-written-questions"
WAYBACK = "parliament-wayback"
API_CORPORA = tuple(c for c in CORPORA if c not in (WRITTEN_QUESTIONS, WAYBACK))
SOURCE = "query-nz"
MCP_SCHEMA = "mcpsource"


def _has(conn, schema: str, table: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s",
                             (schema, table)).fetchone())


def arrivals(conn, mcp_schema: str = MCP_SCHEMA, corpora=CORPORA) -> list:
    """Every record of this lane's corpora the pull has taken, one row per
    arrival, in the order the pull landed them. A schema with no pull
    record yet answers nothing."""
    if not _has(conn, mcp_schema, "arrivals"):
        return []
    return [tuple(r) for r in conn.execute(f"""
        WITH occupant AS (
            SELECT DISTINCT ON (a.corpus, a.seq) a.corpus, a.record_id
              FROM {mcp_schema}.arrivals a JOIN {mcp_schema}.cursors c ON c.corpus = a.corpus
             WHERE a.corpus = ANY(%s) AND a.seq < c.cursor
             ORDER BY a.corpus, a.seq, a.landed_at DESC),
        served AS (SELECT DISTINCT corpus, record_id FROM occupant)
        SELECT a.corpus, a.sha256, a.seq, a.record_id, s.record_id IS NOT NULL
          FROM {mcp_schema}.arrivals a
          LEFT JOIN served s ON s.corpus = a.corpus AND s.record_id = a.record_id
         WHERE a.corpus = ANY(%s)
         ORDER BY a.landed_at, a.seq""", (list(corpora), list(corpora)))]


def caught(conn, mcp_schema: str = MCP_SCHEMA, corpora=CORPORA) -> list:
    if not _has(conn, mcp_schema, "catch"):
        return []
    return [tuple(r) for r in conn.execute(f"SELECT corpus, seq, stage, reason FROM {mcp_schema}.catch "
                                           "WHERE corpus = ANY(%s) AND resolved_at IS NULL ORDER BY corpus, seq",
                                           (list(corpora),))]


def corpora_of(conn, shas: list) -> dict:
    """{sha256: corpus} from each document's `<corpus>/<id>` name, which
    support/mcpsource gives every record it lands (the profile's signal)."""
    from support.docstore.landing import names_for
    out = {}
    for sha, name, kind, _ in names_for(conn, shas):
        if kind == "file" and "/" in name and name.split("/", 1)[0] in CORPORA:
            out[sha] = name.split("/", 1)[0]
    return out
