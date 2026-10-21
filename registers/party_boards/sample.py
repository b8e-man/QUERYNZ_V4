"""The sample filler (plan 1b.6): `fill(conn, schema, items)` loads the
pages named in sample.list into `schema` of the sample database through
this branch's own code. Each page's party, address and capture day come
from the capture's manifest; its bytes from the document store by hash, or
copied by hash from the old folder where the store does not hold them yet.
A hash in neither fails naming it, so the session can ask for a capture. A
page captured before the window is listed and not landed, as the load
does. No model is called.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`party_boards_roles`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import copy_from_old, land, path_for, read_bytes  # noqa: E402
from registers.party_boards import capture  # noqa: E402
from registers.party_boards import load as L  # noqa: E402


def fill(conn, schema: str, items: list) -> int:
    caps = capture.manifest()
    by_sha = capture.by_document(caps)
    landed, before = [], []
    for item in items:
        if item.startswith("key:"):
            continue
        sha = item.split()[0]
        mine = by_sha.get(sha)
        if not mine:
            raise LookupError(f"party_boards/sample.list names {sha}, which the capture's manifest does not list")
        if not capture.in_window(mine[0]):
            before += mine
            continue
        if os.path.exists(path_for(sha)):
            land(read_bytes(sha), name=os.path.basename(mine[0].file), source=capture.SOURCE, conn=conn)
        elif os.path.exists(mine[0].path):
            ref, _ = copy_from_old(mine[0].path, capture.SOURCE, conn)
            if ref.sha256 != sha:
                raise LookupError(f"party_boards/sample.list names {sha}; the old file holds {ref.sha256}")
        else:
            raise LookupError(f"party_boards/sample.list names {sha}, which is neither in the document store "
                              f"nor in the old folder: ask for a capture")
        landed += mine
    return L.build(conn, schema, landed, before, shared=True)["rows"]
