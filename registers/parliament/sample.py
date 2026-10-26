"""The sample filler (plan 1b.6): `fill(conn, schema, items)` reads the
parliament records named in sample.list (their hashes) from the document
store into `schema` of the sample database through this branch's own
code. support/mcpsource landed them (mcp-1's pull, 26 and 27 October
2026); each document's corpus is its `<corpus>/<id>` name in the store. A
hash not in the store, or with no such name, fails naming it. No model is
called, nothing is fetched.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`parliament_written_questions`, …; load.table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import path_for  # noqa: E402
from registers.parliament import capture, load as L  # noqa: E402


def fill(conn, schema: str, items: list) -> int:
    shas = [i.split()[0] for i in items if not i.startswith("key:")]
    for sha in shas:
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"parliament/sample.list names {sha}, which is not in the document store: "
                              "run the pull (python -m support.mcpsource)")
    corpus = capture.corpora_of(conn, shas)
    missing = [s for s in shas if s not in corpus]
    if missing:
        raise LookupError(f"parliament/sample.list names {missing[0]}, which has no `<corpus>/<id>` name in the store")
    return L.build(conn, schema, [(corpus[s], s, None, None, True) for s in shas], shared=True)["records"]
