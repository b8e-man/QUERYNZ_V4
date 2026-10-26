"""How this lane's documents arrive (rulings 78, 94, 96). The estate does
not capture beehive.govt.nz: the ministers' diary releases (monthly PDFs,
a Beehive proactive release) were read on Arthur's provider's box, one
record per meeting, and are served through the ingest MCP
`query-nz-ingest` as the corpus `parliament-diaries`. The shared pull
`support/mcpsource` (job `qv4-mcp-pull`) lands each record whole as a
document of source `query-nz` and writes one `mcpsource.arrivals` row per
record taken. This lane fetches nothing; it reads what the pull landed, by
hash.

    arrivals(conn, mcp_schema)    [(sha256, seq, record id)] in the order the pull saw them
    caught(conn, mcp_schema)      [(seq, stage, reason)]: the pull's catch lines not yet landed
"""
CORPUS = "parliament-diaries"
SOURCE = "query-nz"
MCP_SCHEMA = "mcpsource"


def _held(conn, schema: str, table: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s",
                             (schema, table)).fetchone())


def arrivals(conn, mcp_schema: str = MCP_SCHEMA) -> list:
    """Every diary record the pull has taken, by `landed_at` then `seq`: the
    last a record appears is its current version. A schema with no pull
    record yet answers nothing."""
    if not _held(conn, mcp_schema, "arrivals"):
        return []
    return [tuple(r) for r in conn.execute(f"SELECT sha256, seq, record_id FROM {mcp_schema}.arrivals "
                                           "WHERE corpus = %s ORDER BY landed_at, seq", (CORPUS,))]


def caught(conn, mcp_schema: str = MCP_SCHEMA) -> list:
    if not _held(conn, mcp_schema, "catch"):
        return []
    return [tuple(r) for r in conn.execute(f"SELECT seq, stage, reason FROM {mcp_schema}.catch "
                                           "WHERE corpus = %s AND resolved_at IS NULL ORDER BY seq", (CORPUS,))]
