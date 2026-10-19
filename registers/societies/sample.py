"""The sample filler (plan 1b.6): `fill(conn, schema, items)` loads the
societies named in sample.list (`key: <NZBN>`), with their earlier states,
officers and asks, from the three export parts and the five proved answers
into `schema` of the sample database through this branch's own code. A part
not yet in the document store is landed from the session's scratch folder,
where the once-only export wrote it; found in neither, the fill fails naming
the hash. No model is called, nothing is fetched.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`societies_officers`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore import sha256_file  # noqa: E402
from support.docstore.landing import land, path_for  # noqa: E402
from registers.societies import capture  # noqa: E402
from registers.societies import load as L  # noqa: E402

SCRATCH = os.environ.get("QV4_SOCIETIES_EXPORT_DIR") or "/home/user/querynzv4-work/scratch/societies/export"


def _held(conn, part: str) -> None:
    name, sha = capture.EXPORTS[part]
    if os.path.exists(path_for(sha)):
        return
    p = os.path.join(SCRATCH, name)
    if not (os.path.exists(p) and sha256_file(p) == sha):
        raise LookupError(f"societies/sample.list names {sha} (the {part} export), which is neither in the "
                          f"document store nor at {p}")
    with open(p, "rb") as f:
        land(f.read(), name=name, source=capture.SOURCE, conn=conn, fetched_at=capture.EXPORTED_AT,
             content_type="application/gzip")


def keys_of(items: list) -> set:
    return {i.split()[1] for i in items if i.startswith("key:")}


def fill(conn, schema: str, items: list) -> int:
    listed = {i.split()[0] for i in items if not i.startswith("key:")}
    want = {sha for _, sha in capture.EXPORTS.values()} | {sha for sha, _ in capture.PROOF}
    if listed != want:
        raise LookupError("societies/sample.list must name the three pinned export parts and the five proved answers")
    for part in capture.PARTS:
        _held(conn, part)
    answers = capture.land_proof(conn)
    exports = [(part, sha, name) for part, (name, sha) in capture.EXPORTS.items()]
    return L.build(conn, schema, exports, [], answers=answers, only=keys_of(items), shared=True)["officers"]
