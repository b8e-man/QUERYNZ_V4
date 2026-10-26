"""The sample filler (plan 1b.6): `fill(conn, schema, items)` reads the
beehive records named in sample.list (their hashes) from the document
store into `schema` of the sample database through this branch's own
code. support/mcpsource landed them (mcp-1's first pull, 26 October 2026);
a hash not in the store fails naming it. No model is called, nothing is
fetched.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`beehive_releases`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import path_for  # noqa: E402
from registers.beehive import load as L  # noqa: E402


def fill(conn, schema: str, items: list) -> int:
    shas = [i.split()[0] for i in items if not i.startswith("key:")]
    for sha in shas:
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"beehive/sample.list names {sha}, which is not in the document store: "
                              "run the pull (python -m support.mcpsource --corpus beehive)")
    return L.build(conn, schema, [(s, None, None) for s in shas], shared=True)["releases"]
