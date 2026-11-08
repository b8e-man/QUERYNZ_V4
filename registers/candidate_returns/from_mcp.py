"""The lane's files as the ingest MCP holds them (Arthur, 9 November 2026: option 2, the new estate stops depending
on the old folder; the old estate's own job is left as it is).

The Electoral Commission's site was handed to the MCP's provider on 5 November and is served as the corpus
`estate-candidate_returns`; the six-hourly pull copies each record and its bytes into our store
(`mcpsource.files`: url, the bytes' hash, the state). This module gives `load` the same three things `capture`
gives it from the old folder, by address instead of by file name:

- the returns: every copy at an address under `/assets/` (a return the Commission replaced keeps both copies, as
  the old folder did: `Uploads/Manning-R-Tukituki.pdf` has two), named as the old folder named them, the path after
  `/assets/` with each `/` a `__` (`candidate-returns/2020/Labour-Party/X.pdf` is
  `candidate-returns__2020__Labour-Party__X.pdf`), so `capture.ARCHIVE`, `capture.held_name` and `load.year_of`
  read them unchanged;
- the listing pages, per election: the newest copy at each `start=N` address;
- the summary spreadsheets, per election: the newest copy at each address, oldest version first.

Proven on 9 November 2026: the 1,105 returns the live register held are exactly the in-window returns the MCP
holds, under the same names. Nothing is fetched; a file whose bytes are not in our store yet is a failed read.

    rows(conn)                    [(url, sha256, seq)] the MCP's copies we hold
    name_of(url)                  the old folder's name for an address under /assets/, else None
    returns(rows)                 {sha256: [name]} the in-window returns
    listings(rows, read_bytes)    {year: [(name, take)]}
    sheets(rows, read_bytes)      {year: [(name, take)]}, oldest version first
"""
import re

from registers.candidate_returns import capture

CORPUS = "estate-candidate_returns"
ROWS = ("SELECT url, capture_sha256, seq FROM {schema}.files WHERE corpus = %s AND state IN ('landed', 'held') "
        "AND url IS NOT NULL AND capture_sha256 IS NOT NULL ORDER BY seq")
LISTING = {
    2020: re.compile(r"/candidate-expenses-and-donations-for-the-2020-general-election\?Year=2020&start=(\d+)$"),
    2023: re.compile(r"/2023-general-election/candidate-expenses-donations-and-loans\?Year=2023&start=(\d+)$"),
}


def rows(conn, schema: str = "mcpsource", corpus: str = CORPUS) -> list:
    return [tuple(r) for r in conn.execute(ROWS.format(schema=schema), (corpus,)).fetchall()]


def name_of(url: str):
    m = re.match(r"^https?://(?:www\.)?elections\.nz/assets/(.+?)(?:\?.*)?$", url or "")
    return m.group(1).replace("/", "__") if m else None


def returns(held: list) -> dict:
    out = {}
    for url, sha, _ in held:
        name = name_of(url)
        m = name and capture.ARCHIVE.match(name)
        if m and (m.group("year") is None or int(m.group("year")) in capture.YEARS):
            if name not in out.setdefault(sha, []):
                out[sha].append(name)
    return out


def _newest(held: list) -> dict:
    """{url: sha256} the newest copy at each address (the highest seq: the MCP numbers records as they arrived)."""
    out = {}
    for url, sha, seq in held:
        if url not in out or seq > out[url][1]:
            out[url] = (sha, seq)
    return {u: s for u, (s, _) in out.items()}


def _take(sha: str, read_bytes):
    return lambda: (sha, read_bytes(sha))


def listings(held: list, read_bytes) -> dict:
    out = {}
    for url, sha in _newest(held).items():
        for year, rx in LISTING.items():
            m = rx.search(url)
            if m:
                out.setdefault(year, []).append((int(m.group(1)), url, sha))
    return {y: [(url, _take(sha, read_bytes)) for _, url, sha in sorted(ps)] for y, ps in out.items()}


def sheets(held: list, read_bytes) -> dict:
    out = {}
    for url, sha in _newest(held).items():
        name = name_of(url)
        if not name:
            continue
        for year, rx in capture.SPREADSHEET.items():
            if rx.match(name) or rx.match(capture.held_name(name)):
                out.setdefault(year, []).append((name, sha))
    return {y: [(n, _take(s, read_bytes)) for n, s in sorted(ps, key=lambda p: capture._version(p[0]))]
            for y, ps in out.items()}
