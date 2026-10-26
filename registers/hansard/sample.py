"""The sample filler (plan 1b.6): `fill(conn, schema, items)` loads the
sitting days named in sample.list (`key: <YYYY-MM-DD>`), with every member,
from the export into `schema` of the sample database through this branch's
own code. The export not yet in the document store is landed from the
scratch folder the once-only export wrote it to; found in neither, the fill
fails naming the hash. The other hashes are records of the MCP's two Hansard
corpora that support/mcpsource landed, read by hash from the store; one not
there fails naming it. No model is called, nothing is fetched.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`hansard_sittings`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import json  # noqa: E402

from support.docstore import sha256_file  # noqa: E402
from support.docstore.landing import land, path_for, read_bytes  # noqa: E402
from registers.hansard import capture, read_mcp  # noqa: E402
from registers.hansard import load as L  # noqa: E402

SCRATCH = os.environ.get("QV4_HANSARD_EXPORT_DIR") or "/home/user/querynzv4-work/scratch/hansard-1"


def _held(conn, sha: str) -> None:
    if os.path.exists(path_for(sha)):
        data = read_bytes(sha)
    else:
        p = os.path.join(SCRATCH, capture.EXPORT_NAME)
        if not (os.path.exists(p) and sha256_file(p) == sha):
            raise LookupError(f"hansard/sample.list names {sha} (the Hansard export), which is neither in the "
                              f"document store nor at {p}")
        with open(p, "rb") as f:
            data = f.read()
    land(data, name=capture.EXPORT_NAME, source=capture.SOURCE, conn=conn, fetched_at=capture.EXPORTED_AT)


def days_of(items: list) -> set:
    return {i.split()[1] for i in items if i.startswith("key:")}


def mcp_of(items: list) -> dict:
    """{corpus: ([(sha256, None, None)], [])} for the MCP records the list names, by each record's own address."""
    out = {c: ([], []) for c in capture.CORPORA}
    for sha in [i.split()[0] for i in items if not i.startswith("key:")][1:]:
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"hansard/sample.list names {sha}, which is not in the document store: "
                              "run the pull (python -m support.mcpsource --corpus parliament-hansard-debates)")
        rec = json.loads(read_bytes(sha))
        corpus = read_mcp.DAYS if read_mcp.PDF.match(str(rec.get("url"))) else read_mcp.INDEX
        out[corpus][0].append((sha, None, None))
    return out


def fill(conn, schema: str, items: list) -> int:
    sha = next((i.split()[0] for i in items if not i.startswith("key:")), None)
    if sha != capture.EXPORT_SHA:
        raise LookupError("hansard/sample.list must name the pinned Hansard export first")
    _held(conn, sha)
    return L.build(conn, schema, (sha, capture.EXPORT_NAME), [], only=days_of(items), shared=True,
                   mcp=mcp_of(items))["sections"]
