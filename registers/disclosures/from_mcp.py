"""The lane's files from the ingest MCP first, the old folder filling what the MCP could not get (Arthur,
9 November 2026: option 2, the new estate stops depending on the old folder; the old estate's own job is left as
it is).

The Commission's site was handed to the MCP's provider on 5 November and is served as `estate-disclosures`; the
six-hourly pull copies each record and its bytes into our store (`mcpsource.files`). On 9 November the two held
the same files but for three: the MCP had the one declaration filed since the old job last ran (J-Swap
Contractors), and for two others (Rank Group, E and R Congreve) it held the site's Incapsula challenge page where
the PDF should be, which the old estate's headed browser was not shown. So until the MCP gets every declaration
the old folder fills the gaps:

- a declaration: per Commission file name, the MCP's newest real copy, else the old folder's. One file per name,
  as the old folder held it, so no name is answered by two files (`read.join` would call that a collision). A copy
  that is a web page under a document's name is not a document: a `capture` line, as the old folder's challenge
  shells are.
- each of the Commission's two tables: the newer of the MCP's newest copy and the old folder's, by when each was
  fetched (the frozen site's check compares with the table the old job fetched that night).

Nothing is fetched.

    rows(conn)                         [(url, sha256, seq, content_type)] the MCP's copies we hold
    commission_name(url)               a declaration's file name, or None
    listing_of(url)                    which of the two tables an address is, or None
    documents(mcp_rows, landed, aside, fetched_at)   build's three arguments
"""
import os
import re
from urllib.parse import unquote

from registers.disclosures import capture, read

CORPUS = "estate-disclosures"
ROWS = ("SELECT url, capture_sha256, seq, content_type FROM {schema}.files WHERE corpus = %s "
        "AND state IN ('landed', 'held') AND url IS NOT NULL AND capture_sha256 IS NOT NULL ORDER BY seq")
DECLARATION = re.compile(r"^https?://(?:www\.)?elections\.nz/assets/(?:.+/)?([^/?]+\.(?:pdf|jpe?g|png))(?:\?.*)?$", re.I)
# the two tables by their path, the old folder's names for them (capture.LISTINGS)
LISTING = {
    "/donations-exceeding-20000/donations-exceeding-30000": capture.LISTINGS[1],
    "/donations-exceeding-20000": capture.LISTINGS[0],
}


def rows(conn, schema: str = "mcpsource", corpus: str = CORPUS) -> list:
    return [tuple(r) for r in conn.execute(ROWS.format(schema=schema), (corpus,)).fetchall()]


def commission_name(url: str):
    m = DECLARATION.match(url or "")
    return unquote(m.group(1)) if m else None


def listing_of(url: str):
    path = re.sub(r"^https?://(?:www\.)?elections\.nz", "", (url or "").split("?")[0]).rstrip("/")
    for tail, name in LISTING.items():
        if path.endswith(tail):
            return name
    return None


def _web_page(content_type) -> bool:
    return (content_type or "").split(";")[0].strip().lower() in ("text/html", "application/xhtml+xml")


def documents(mcp_rows: list, landed: list, aside: list, fetched_at) -> tuple:
    """(listings, declarations, aside) for `load.build`, from the MCP's rows and the old folder's
    `capture.copy_all` output; `fetched_at(sha256)` is when a file was fetched (comparable values)."""
    newest = {}
    for url, sha, seq, ct in mcp_rows:
        if url not in newest or seq > newest[url][1]:
            newest[url] = (sha, seq, ct)
    declared, out_aside, tables = {}, [], {}
    for url, (sha, seq, ct) in newest.items():
        name, table = commission_name(url), listing_of(url)
        if table:
            if table not in tables or seq > tables[table][1]:
                tables[table] = (sha, seq)
        elif name:
            if _web_page(ct):
                out_aside.append((name, "a challenge page the MCP saved under a document's name"))
            else:
                key = read.file_key(name)
                if key not in declared or seq > declared[key][2]:
                    declared[key] = (sha, name, seq)
    declarations = [(sha, name) for sha, name, _ in declared.values()]
    for kind, ref, path, _ in landed:
        name = capture.commission_name(path)
        if kind == "declaration" and read.file_key(name) not in declared:
            declarations.append((ref.sha256, name))
            declared[read.file_key(name)] = (ref.sha256, name, -1)
    listings = []
    old_tables = {os.path.basename(p): ref.sha256 for kind, ref, p, _ in landed if kind == "listing"}
    for table in capture.LISTINGS:
        picks = [s for s in ((tables.get(table) or (None,))[0], old_tables.get(table)) if s]
        if picks:
            listings.append((max(picks, key=lambda s: fetched_at(s) or ""), table))
    filled = {n for n, _ in out_aside} - {name for _, name in declarations}
    out_aside = [(n, w) for n, w in out_aside if n in filled]
    out_aside += [(os.path.basename(p), why) for p, why in aside]
    return listings, sorted(declarations), out_aside
