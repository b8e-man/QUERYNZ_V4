"""The sample filler (plan 1b.6): `fill(conn, schema, items)` reads the feed
pages named in sample.list (hashes; already in the document store, landed by
the capture lane) and keeps the charities named by its `key: CC…` lines,
with their officers and returns on those pages, the groups whole, and the
code lists, into `schema` of the sample database through this branch's own
code. Each page says which entity set it is (`__metadata.type` of its rows);
a listed document that is not a JSON page (the feed's metadata) is skipped.
No model is called, nothing is fetched.

Every module fills one shared scratch schema, so this build's tables there
carry its name (`charities_a_charities`, …; load.table).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import path_for, read_bytes  # noqa: E402
from registers.charities_a import load as L  # noqa: E402
from registers.charities_a import read as R  # noqa: E402


def keys_of(items: list) -> set:
    return {i.split(None, 1)[1].strip() for i in items if i.startswith("key:")}


def pages_of(items: list, read_fn=read_bytes) -> dict:
    """set → [(sha, name)] for every listed hash that is a JSON page of the feed."""
    out = {}
    for sha in (i for i in items if not i.startswith("key:")):
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"charities_a/sample.list names {sha}, which is not in the document store")
        data = read_fn(sha)
        try:
            _, rows = R.parse_page(data)
        except (ValueError, KeyError, TypeError, UnicodeDecodeError):
            continue
        s = R.entity_set_of_rows(rows)
        if s not in L.SETS:
            continue
        out.setdefault(s, []).append((sha, f"sample page of {s}"))
    return out


def fill(conn, schema: str, items: list) -> int:
    only = keys_of(items)
    if not only:
        raise LookupError("charities_a/sample.list names no `key: CC…` line")
    counts = L.build(conn, schema, pages_of(items), only=only, shared=True, log=lambda *a: None)
    return counts["charities"] + counts["charity_officers"] + counts["charity_returns"]
