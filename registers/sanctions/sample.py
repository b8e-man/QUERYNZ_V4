"""The sample filler (plan 1b.6): `fill(conn, schema, items)` reads the list
documents sample.list names (`key: list <list> <sha256> <version>`, `key:
page-1373 <sha256>`), from the document store, through this branch's own
reading, into `schema` of the sample database. The list is empty while every
list is held (sample.list says why), so a fill reads nothing. A document not
in the store fails the fill, naming its hash. No model; nothing fetched."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import path_for  # noqa: E402
from registers.sanctions import load  # noqa: E402


def docs_of(items: list) -> dict:
    out = {}
    for i in items:
        parts = i.split()
        if i.startswith("key: list "):
            out.setdefault(parts[2], {})["list"] = (parts[3], parts[4] if len(parts) > 4 else None)
        elif i.startswith("key: page-1373 "):
            out.setdefault("nz-police-tsa", {})["page-1373"] = parts[2]
    for d in out.values():
        for v in d.values():
            sha = v[0] if isinstance(v, tuple) else v
            if not os.path.exists(path_for(sha)):
                raise LookupError(f"sanctions/sample.list names {sha}, which is not in the document store")
    return out


def fill(conn, schema: str, items: list) -> int:
    docs = docs_of(items)
    if not docs:
        return 0
    return load.build(conn, schema, docs, shared=True)["listings"]
