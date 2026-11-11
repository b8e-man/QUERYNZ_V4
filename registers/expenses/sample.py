"""The sample filler (plan 1b.6): `fill(conn, schema, items)` loads the
documents named in sample.list into `schema` of the sample database
through this branch's own code. A document not yet in the store is copied
by hash from the old folder; one found in neither fails naming the hash,
so the session can ask for a capture. No model is called.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`expenses_lines`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore import sha256_file  # noqa: E402
from support.docstore.landing import copy_from_old, path_for  # noqa: E402
from registers.expenses import capture  # noqa: E402
from registers.expenses import load as L  # noqa: E402


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
        if sha not in index and os.path.exists(path_for(sha)):
            # the old folder's file was fetched again under the same name (the old job ran until 11 November 2026),
            # so the hash the sample names is held in the store under its old path, not on the old disk
            from support.docstore.landing import names_of
            for name in names_of(sha, conn):
                folder = os.path.basename(os.path.dirname(name))
                kind = folder in capture.FOLDERS and capture.kind_of(folder, os.path.basename(name))
                if kind:
                    index[sha] = (kind, name)
                    break
        if sha not in index:
            raise LookupError(f"expenses/sample.list names {sha}, which is not in the old folders: ask for a capture")
        kind, path = index[sha]
        if not os.path.exists(path_for(sha)):
            copy_from_old(path, capture.SOURCE, conn)
        held.append((kind, sha, path, man.get(sha) or {}))
    c = L.build(conn, schema, held, shared=True)
    return c["figures"]
