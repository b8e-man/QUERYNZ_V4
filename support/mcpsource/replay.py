"""A lane's walk answered from the ingest MCP, never from the web (Arthur, 9 November 2026).

On 5 November 2026 every website crawl moved to the MCP's provider, which runs the lanes' own capture code in its
own store and serves each source as an `estate-<lane>` corpus: one record per page or file it fetched, the bytes by
hash, the page's address in `urls`. The nightly pull copies those records and their bytes into our store
(`mcpsource.files`: corpus, seq, url, the bytes' hash, the state). A lane whose crawl was handed over keeps its own
walk, ledger and reading unchanged and swaps only its opener for `opener(conn, corpora)`: each address it would have
asked the web for is answered with the newest copy the MCP holds of it (the highest `seq`: the MCP numbers its
records in the order they arrived, which is the order the provider fetched them). An address the MCP does not hold
raises `NotHeld`, which the lane's walk counts as a failed read, as it would a page the web did not answer.

No request leaves the boxes, so no pacing or off-peak hours apply."""
from __future__ import annotations

from support import fetchgate as fg

NEWEST = ("SELECT capture_sha256 FROM {schema}.files WHERE url = %s AND corpus = ANY(%s) "
          "AND state IN ('landed', 'held') ORDER BY seq DESC LIMIT 1")


class NotHeld(OSError):
    """The MCP holds no copy of the address (or its bytes are not in our store yet)."""


def newest(conn, url: str, corpora, schema: str = "mcpsource"):
    """The hash of the newest copy of `url` in `corpora`, or None."""
    row = conn.execute(NEWEST.format(schema=schema), (url, list(corpora))).fetchone()
    return row[0] if row else None


def opener(conn, corpora, schema: str = "mcpsource", read_bytes=None):
    """An `opener(url, timeout)` answering from the MCP's copies: a 200 with the newest copy's bytes, or NotHeld."""
    if read_bytes is None:
        from support.docstore.landing import read_bytes
    corpora = list(corpora)

    def open_url(url: str, timeout=None, **_):
        sha = newest(conn, url, corpora, schema)
        if sha is None:
            raise NotHeld(f"the MCP holds no copy of {url} in {', '.join(corpora)}")
        try:
            body = read_bytes(sha)
        except OSError as exc:
            raise NotHeld(f"the copy of {url} ({sha[:12]}…) is not in the store: {exc}") from exc
        return fg.Fetched(url=url, status=200, body=body, final_url=url)
    return open_url
