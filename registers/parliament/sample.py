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
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import path_for, read_bytes  # noqa: E402
from registers.parliament import capture, load as L, model_read  # noqa: E402


def corpus_of_record(rec) -> str:
    """The corpus a record names by its own shape, for one landed after the sample database's copy of the
    store's names: a question has questionNumber, an archived page snapshot_url (the text reader's profiles);
    an API item names its corpus in the provider's `_corpus` ("papers", "SOPs", none on a current bill). '' when
    neither says one of this lane's corpora."""
    if not isinstance(rec, dict):
        return ""
    profile = model_read._profile_of_record(rec)
    if profile == model_read.WQ:
        return capture.WRITTEN_QUESTIONS
    if profile == model_read.WAYBACK:
        return capture.WAYBACK
    named = rec.get("_corpus")
    if isinstance(named, str) and named:
        named = named.lower() if named.lower().startswith("parliament-") else f"parliament-{named.lower()}"
        if named in capture.API_CORPORA:
            return named
    return ""


def fill(conn, schema: str, items: list) -> int:
    shas = [i.split()[0] for i in items if not i.startswith("key:")]
    for sha in shas:
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"parliament/sample.list names {sha}, which is not in the document store: "
                              "run the pull (python -m support.mcpsource)")
    corpus = capture.corpora_of(conn, shas)
    for sha in [s for s in shas if s not in corpus]:
        # landed after the sample database's copy of the store's names: the record's own shape says which corpus
        # of the two the text reader reads (a question has questionNumber; an archived page has snapshot_url)
        rec = json.loads(read_bytes(sha))
        corpus_of = corpus_of_record(rec)
        if corpus_of:
            corpus[sha] = corpus_of
    missing = [s for s in shas if s not in corpus]
    if missing:
        raise LookupError(f"parliament/sample.list names {missing[0]}, which has no `<corpus>/<id>` name in the store")
    return L.build(conn, schema, [(corpus[s], s, None, None, True) for s in shas], shared=True)["records"]
