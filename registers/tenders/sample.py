"""The sample filler (plan 1b.6): `fill(conn, schema, items)` reads the files
sample.list names, from the document store, through this branch's own
reading, into `schema` of the sample database. A hash pinned in
`capture.OLD_RAWS` is a data file of its set and era; any other hash is a
document the capture holds and the reading does not (the schema workbook,
the catalogue's description). `key: <era> <RFx ID>` lines name the notices
read. A document not in the store fails the fill, naming its hash. No
model is called and nothing is fetched.

Every module fills one shared scratch schema, so the lane's tables there
carry its name (`tenders_notices`, …; load.table)."""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import path_for  # noqa: E402
from registers.tenders import capture, load  # noqa: E402

BY_SHA = {sha: capture.classify(name) for name, sha in capture.OLD_RAWS.items()}


def keys_of(items: list) -> dict:
    """era → the RFx IDs the key lines name."""
    out = collections.defaultdict(set)
    for i in items:
        if i.startswith("key:"):
            _, era, rfx = i.split()
            out[era].add(rfx)
    return dict(out)


def files_of(items: list) -> dict:
    """(set, era) → sha256 for every listed data file."""
    out = {}
    for sha in dict.fromkeys(i for i in items if not i.startswith("key:")):
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"tenders/sample.list names {sha}, which is not in the document store")
        role, s, era = BY_SHA.get(sha, (None, None, None))
        if role == "data":
            out[(s, era)] = sha
    return out


def fill(conn, schema: str, items: list) -> int:
    counts = load.build(conn, schema, files_of(items), only=keys_of(items), shared=True)
    return counts["notices"] + counts["suppliers"]
