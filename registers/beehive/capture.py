"""How this lane's documents arrive (rulings 78, 94, 96). The estate does
not capture beehive.govt.nz: Arthur's provider captured and read it on its
own box, and serves it through the ingest MCP `query-nz-ingest`. The
shared pull `support/mcpsource` (job `qv4-mcp-pull`) lands each record of
the MCP's `beehive` corpus whole as a document of source `query-nz`, and
writes one `mcpsource.arrivals` row per record taken: its place in the
MCP's arrival order (`seq`), its id and the hash it landed as. This lane
fetches nothing; it reads what the pull landed, by hash.

    arrivals(conn, mcp_schema)    [(sha256, seq, record id)] for the beehive corpus, in the order the pull saw them
    old_export(conn)              the old estate's Beehive pages, exported once: (sha256, name) or None
    python -m registers.beehive.capture --export PATH    write that export once
"""
import datetime as dt
import json
import os
import sys

CORPUS = "beehive"
SOURCE = "query-nz"
MCP_SCHEMA = "mcpsource"


def arrivals(conn, mcp_schema: str = MCP_SCHEMA) -> list:
    """Every beehive record the pull has taken. A schema with no pull
    record yet answers nothing."""
    held = conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = 'arrivals'",
                        (mcp_schema,)).fetchone()
    if not held:
        return []
    return [tuple(r) for r in conn.execute(f"SELECT sha256, seq, record_id FROM {mcp_schema}.arrivals "
                                           "WHERE corpus = %s ORDER BY landed_at, seq", (CORPUS,))]


def caught(conn, mcp_schema: str = MCP_SCHEMA) -> list:
    """[(seq, stage, reason)]: the pull's catch lines for this corpus not yet landed."""
    held = conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = 'catch'",
                        (mcp_schema,)).fetchone()
    if not held:
        return []
    return [tuple(r) for r in conn.execute(f"SELECT seq, stage, reason FROM {mcp_schema}.catch "
                                           "WHERE corpus = %s AND resolved_at IS NULL ORDER BY seq", (CORPUS,))]


# ── the old estate's Beehive pages, exported once (ruling 96's default; Arthur may strike it) ─────────────
#
# The old estate's news database holds the text of 55,358 Beehive pages (`incoming_news.articles`, the rows whose
# address is on beehive.govt.nz), which its own scraper took before ruling 78. Exported once, by hash, the way the
# Gazette's notices were (registers/gazette/capture.py): one JSON line per article row, sorted by address. The
# file is the document; a row read from it is "taken from the old estate's tables; original not held" and cites
# the export's hash and the page's address. The lane reads only the pages the MCP does not hold, by address.
# Nothing is fetched, the export is never run at load, and a second export would be a new document and a new pin.

OLD_SOURCE = "beehive"
OLD_EXPORT_NAME = "beehive-pages-old-estate.jsonl"
OLD_EXPORT_SHA = "e6511b9f1e0103338f0c27257f5784a548933fad80df076c5bcf2e0f2f72d46d"   # 55,358 lines, run by mcp-1
OLD_EXPORTED_AT = "2026-10-26T18:57:32+13:00"
OLD_NOTE = "taken from the old estate's tables; original not held"
_OLD_SQL = """
SELECT id::text, news_url, title, text_content, author, post_date_nz::text, scrape_date::text, fetched_at::text
  FROM articles
 WHERE news_url LIKE 'https://www.beehive.govt.nz/%%'
"""


def export_old_pages(connect=None) -> bytes:
    """One line per article row, sorted by address then article: the
    article id, address, title, text, author, the NZ post time and when the
    old scraper took it. Read-only, under a time limit; run once."""
    from support import db
    connect = connect or (lambda name: db.connect(db.OLD_READ_KEY, name, connect_timeout=10))
    lines = []
    with connect("incoming_news") as c:
        c.execute("SET statement_timeout = '120s'")
        with c.transaction():
            cur = c.cursor(name="beehive_export")
            cur.itersize = 2000
            cur.execute(_OLD_SQL)
            for aid, url, title, text, author, posted, scraped, fetched in cur:
                lines.append((url, aid, json.dumps({
                    "article": aid, "url": url, "title": title or "", "text": text or "", "author": author,
                    "posted_nz": posted, "scraped": scraped, "fetched": fetched},
                    ensure_ascii=False, sort_keys=True, separators=(",", ":"))))
    lines.sort()
    return ("\n".join(l for _, _, l in lines) + "\n").encode("utf-8")


def old_export(conn, sha: str = None, log=None):
    """The pinned export landed from the store: (sha256, name), or None
    when no export is pinned or the store lacks it."""
    from support.docstore.landing import land, path_for, read_bytes
    sha = sha or OLD_EXPORT_SHA
    if not sha or not os.path.exists(path_for(sha)):
        return None
    ref, new = land(read_bytes(sha), name=OLD_EXPORT_NAME, source=OLD_SOURCE, conn=conn, fetched_at=OLD_EXPORTED_AT)
    if log:
        log(f"beehive: {'landed' if new else 'held'} {ref.sha256[:12]} {OLD_EXPORT_NAME}")
    return ref.sha256, OLD_EXPORT_NAME


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--export" not in argv:
        print("usage: python -m registers.beehive.capture --export PATH")
        return 2
    path = argv[argv.index("--export") + 1]
    if os.path.exists(path):
        print(f"{path} exists: the export is run once")
        return 1
    data = export_old_pages()
    with open(path, "wb") as f:
        f.write(data)
    from support.docstore import sha256_file
    print(f"{path}: {data.count(b'\n')} lines, sha256 {sha256_file(path)}, "
          f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
