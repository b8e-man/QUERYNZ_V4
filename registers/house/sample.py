"""The sample filler (plan 1b.6): `fill(conn, schema, items)` loads the
documents named in sample.list into `schema` of the sample database
through this branch's own code. A document not yet in the store is copied
by hash from the old folders; one found in neither fails naming the hash,
so the session can ask for a capture. No model is called.

The lane is small (167 files, 2 s to read), so its sample is the whole of
what it reads, the failed reads among them: the hard cases are all in it.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`house_candidates`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore import sha256_file  # noqa: E402
from support.docstore.landing import copy_from_old, names_of, path_for  # noqa: E402
from registers.house import capture  # noqa: E402
from registers.house import load as L  # noqa: E402


def _where(conn, sha: str, held: dict, roots: dict):
    """(folder, name, captured at) of a sample hash: from the old folders
    when they still hold those bytes, else from the name the store kept."""
    if sha in held:
        folder, name, path = held[sha]
        ref, _ = copy_from_old(path, capture.SOURCE, conn)
        return folder, name, capture.captured_on(folder, name, sha, roots) or ref.fetched_at
    if os.path.exists(path_for(sha)):
        for n in names_of(sha, conn):
            for folder, base in roots.items():
                if n.startswith(base + os.sep):
                    return folder, os.path.relpath(n, base), None
    raise LookupError(f"house/sample.list names {sha}, which is neither in the old folders nor in the document "
                      f"store under an old path: ask for a capture")


def fill(conn, schema: str, items: list) -> int:
    roots = capture.roots()
    held = {sha256_file(p): (f, n, p) for f, n, p in capture.held_files(roots)}
    docs = []
    for item in items:
        if item.startswith("key:"):
            continue
        sha = item.split()[0]
        folder, name, at = _where(conn, sha, held, roots)
        docs.append((folder, sha, name, at))
    return L.build(conn, schema, docs, [], shared=True)["candidates"]
