"""The sample filler (plan 1b.6). The archive is read in its own scratch schemas from the dump on the 4 TB disk
(tests/test_papers_past_stream.py), and it is searched, never mined (hard limit 17), so the shared sample holds no rows of it."""


def fill(conn, schema: str, items: list) -> int:
    return 0
