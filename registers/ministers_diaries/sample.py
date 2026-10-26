"""The sample filler (plan 1b.6): `fill(conn, schema, items)` reads the
diary records named in sample.list (their hashes) from the document store
into `schema` of the sample database through this branch's own code.
support/mcpsource landed them (mcp-1's pull, 26 and 27 October 2026); a
hash not in the store fails naming it. No model is called, nothing is
fetched. The items are taken in the list's order, so a record listed twice
(an older version, then the current) is read as the pull saw it.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`ministers_diaries_entries`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import path_for  # noqa: E402
from registers.ministers_diaries import load as L  # noqa: E402


def fill(conn, schema: str, items: list) -> int:
    shas = [i.split()[0] for i in items if not i.startswith("key:")]
    for sha in shas:
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"ministers_diaries/sample.list names {sha}, which is not in the document store: "
                              "run the pull (python -m support.mcpsource --corpus parliament-diaries)")
    return L.build(conn, schema, [(s, None, None) for s in shas], shared=True)["entries"]
