"""The sample filler (plan 1b.6): `fill(conn, schema, items)` loads the
documents named in sample.list into `schema` of the sample database
through this branch's own code. A document not yet in the store is copied
by hash from the old folder; one found in neither fails naming the hash,
so the session can ask for a capture. No model is called: a return's image
pages are replayed from the page reader's stored readings.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`party_finance_expense_listing`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support import reader as rd  # noqa: E402
from support.docstore import sha256_file  # noqa: E402
from support.docstore.landing import copy_from_old, path_for  # noqa: E402
from registers.party_finance import capture  # noqa: E402
from registers.party_finance import load as L  # noqa: E402


def old_index() -> dict:
    """sha256 → (kind, old path) for every candidate file of the old folders."""
    return {sha256_file(p): (kind, p) for kind, p in capture.candidate_files()}


def fill(conn, schema: str, items: list) -> int:
    index, man = old_index(), capture.manifest()
    held = []
    for item in items:
        if item.startswith("key:"):
            continue
        sha = item.split()[0]
        if sha not in index:
            raise LookupError(f"party_finance/sample.list names {sha}, which is not in the old folders: ask for a capture")
        kind, path = index[sha]
        if not os.path.exists(path_for(sha)):
            copy_from_old(path, capture.SOURCE, conn)
        m = man.get(sha) or {}
        held.append((kind, sha, path, m.get("source"), m.get("fetched_at")))
    c = L.build(conn, schema, held, rd.Store(), shared=True)
    return c["listing_rows"] + c["returns_read"] + c["allocation_rows"]
