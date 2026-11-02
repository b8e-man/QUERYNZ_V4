"""The sample filler (plan 1b.6). The lane is proven on fakes built from the API definition's own examples
(tests/test_insolvency_capture.py), so the sample holds no rows of it, and no bankrupt's name goes into the sample."""


def fill(conn, schema: str, items: list) -> int:
    return 0
