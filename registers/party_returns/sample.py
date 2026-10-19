"""The sample filler (plan 1b.6): `fill(conn, schema, items)` loads the
documents named in sample.list into `schema` of the sample database
through this branch's own code, with the Commission's statements of which
return an amendment replaces. A document not yet in the store is copied
by hash from the old folder; one found in neither fails naming the hash,
so the session can ask for a capture. No model is called.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support import reader as rd  # noqa: E402
from support.docstore.landing import copy_from_old, land, path_for, read_bytes  # noqa: E402
from registers.party_returns import capture, read  # noqa: E402
from registers.party_returns import load as L  # noqa: E402


def fill(conn, schema: str, items: list) -> int:
    L.create_tables(conn, schema)
    L.wipe(conn, schema)
    store = rd.Store()
    index = None
    rows = 0
    for item in items:
        if item.startswith("key:"):
            continue
        sha = item.strip()
        if os.path.exists(path_for(sha)):
            data = read_bytes(sha)
            land(data, name=f"{sha}.pdf", source=capture.SOURCE, conn=conn)
        else:
            index = index if index is not None else capture.old_index()
            if sha not in index:
                raise LookupError(f"party_returns/sample.list names {sha}, which is neither in the document store "
                                  f"nor in the old folder: ask for a capture")
            ref, _ = copy_from_old(index[sha], capture.SOURCE, conn)
            data = read_bytes(ref)
        rows += L.insert(conn, schema, read.read_return(data, sha, store))
    L.insert_amendments(conn, schema, index if index is not None else capture.old_index())
    return rows
