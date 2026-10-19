"""The sample filler (plan 1b.6): `fill(conn, schema, items)` loads the
notices named in sample.list (`key: <notice number>`) from the export into
`schema` of the sample database through this branch's own code. The export
not yet in the document store is landed from the session's scratch folder,
where the once-only export wrote it; found in neither, the fill fails
naming the hash. No model is called.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`gazette_notices`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore import sha256_file  # noqa: E402
from support.docstore.landing import land, path_for, read_bytes  # noqa: E402
from registers.gazette import capture  # noqa: E402
from registers.gazette import load as L  # noqa: E402

SCRATCH = os.environ.get("QV4_GAZETTE_EXPORT_DIR") or "/home/user/querynzv4-work/scratch/gazette"


def _held(conn, sha: str) -> None:
    if os.path.exists(path_for(sha)):
        data = read_bytes(sha)
    else:
        p = os.path.join(SCRATCH, capture.EXPORT_NAME)
        if not (os.path.exists(p) and sha256_file(p) == sha):
            raise LookupError(f"gazette/sample.list names {sha} (the notices export), which is neither in the "
                              f"document store nor at {p}")
        with open(p, "rb") as f:
            data = f.read()
    land(data, name=capture.EXPORT_NAME, source=capture.SOURCE, conn=conn, fetched_at=capture.EXPORTED_AT)


def notices_of(items: list) -> set:
    return {i.split()[1] for i in items if i.startswith("key:")}


def fill(conn, schema: str, items: list) -> int:
    sha = next((i.split()[0] for i in items if not i.startswith("key:")), None)
    if sha != capture.EXPORT_SHA:
        raise LookupError("gazette/sample.list must name the pinned notices export")
    _held(conn, sha)
    return L.build(conn, schema, (sha, capture.EXPORT_NAME), [], only=notices_of(items), shared=True)["notices"]
