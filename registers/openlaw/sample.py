"""The sample filler (plan 1b.6): `fill(conn, schema, items)` reads the pages
sample.list names, from the document store, through this branch's own
reading, into `schema` of the sample database; `key: case <id>` lines name
the cases read from them (none: every case of the listed pages). The list is
empty while the lane is held (sample.list says why), so a fill reads nothing.
A document not in the store fails the fill, naming its hash. No model is
called and nothing is fetched."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import path_for  # noqa: E402
from registers.openlaw import load  # noqa: E402


def fill(conn, schema: str, items: list) -> int:
    docs = [i for i in items if not i.startswith("key:")]
    ids = {i.split()[2] for i in items if i.startswith("key:")} or None
    for sha in docs:
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"openlaw/sample.list names {sha}, which is not in the document store")
    if not docs:
        return 0
    counts = load.build(conn, schema, docs, only=ids, shared=True)
    return counts["cases"] + counts["parties"] + counts["citations"] + counts["statutes"]
