"""The sample filler (plan 1b.6): `fill(conn, schema, items)` loads the
entities named in sample.list (`key: <NZBN or register number>`), with their
directors, shareholders and registered offices, from the four export parts
into `schema` of the sample database through this branch's own code. A part
not yet in the document store is landed from the session's scratch folder,
where the once-only export wrote it; found in neither, the fill fails naming
the hash. No model is called.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`companies_entities`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore import sha256_file  # noqa: E402
from support.docstore.landing import land, path_for  # noqa: E402
from registers.companies import capture  # noqa: E402
from registers.companies import load as L  # noqa: E402

SCRATCH = os.environ.get("QV4_COMPANIES_EXPORT_DIR") or "/home/user/querynzv4-work/scratch/companies/export"


def _held(conn, part: str) -> None:
    name, sha = capture.EXPORTS[part]
    if os.path.exists(path_for(sha)):
        return
    p = os.path.join(SCRATCH, name)
    if not (os.path.exists(p) and sha256_file(p) == sha):
        raise LookupError(f"companies/sample.list names {sha} (the {part} export), which is neither in the "
                          f"document store nor at {p}")
    with open(p, "rb") as f:
        land(f.read(), name=name, source=capture.SOURCE, conn=conn, fetched_at=capture.EXPORTED_AT,
             content_type="application/gzip")


def keys_of(items: list) -> set:
    return {i.split()[1] for i in items if i.startswith("key:")}


def fill(conn, schema: str, items: list) -> int:
    listed = {i.split()[0] for i in items if not i.startswith("key:")}
    if listed != {sha for _, sha in capture.EXPORTS.values()}:
        raise LookupError("companies/sample.list must name the four pinned export parts")
    for part in capture.PARTS:
        _held(conn, part)
    exports = [(part, sha, name) for part, (name, sha) in capture.EXPORTS.items()]
    return L.build(conn, schema, exports, [], only=keys_of(items), shared=True)["entities"]
