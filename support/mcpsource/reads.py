"""What a lane reads of the pull's tables, through the module that owns them (tests/test_imports_one_way.py: only
support.mcpsource queries the `mcpsource` schema). Read-only; a lane keeps its own ledger and filters by it.

    landed_files(conn, corpus)        [(capture_sha256, url, done_at)]: each landed or held file once, newest first
    arrivals(conn, corpora)           [(corpus, seq, record_sha256, url, landed_at, file_sha256, file_state)]
    urls_outside_sql(corpus)          a SELECT of every address the pull holds outside `corpus` (records and files)
"""
from __future__ import annotations

SCHEMA = "mcpsource"


def landed_files(conn, corpus: str, schema: str = SCHEMA) -> list:
    return conn.execute(
        f"SELECT DISTINCT ON (capture_sha256, url) capture_sha256, url, done_at FROM {schema}.files "
        "WHERE corpus = %s AND state IN ('landed', 'held') ORDER BY capture_sha256, url, done_at DESC",
        (corpus,)).fetchall()


def arrivals(conn, corpora, schema: str = SCHEMA) -> list:
    return conn.execute(
        f"SELECT a.corpus, a.seq, a.sha256, a.url, a.landed_at, f.capture_sha256, f.state FROM {schema}.arrivals a "
        f"LEFT JOIN {schema}.files f ON f.corpus = a.corpus AND f.seq = a.seq AND f.record_sha256 = a.sha256 "
        "WHERE a.corpus = ANY(%s) ORDER BY a.landed_at, a.corpus, a.seq", (list(corpora),)).fetchall()


def urls_outside_sql(corpus: str, schema: str = SCHEMA) -> str:
    c = corpus.replace("'", "''")
    return (f"SELECT url FROM {schema}.files WHERE corpus <> '{c}' "
            f"UNION SELECT url FROM {schema}.arrivals WHERE corpus <> '{c}'")
