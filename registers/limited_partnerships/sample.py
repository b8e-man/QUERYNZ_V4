"""The sample filler (plan 1b.6): `fill(conn, schema, items)` reads the
answers sample.list names, from the document store, through this branch's
own reading, into `schema` of the sample database (the lane's tables there
carry its name, `limited_partnerships_partners`, …). A `key: asked <sha256>
<moment>` line gives the moment an answer was asked. A document not in the
store fails the fill, naming its hash. No model is called and nothing is
fetched."""
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import path_for, read_bytes  # noqa: E402
from registers.limited_partnerships import load  # noqa: E402


def answers_of(items: list) -> list:
    asked = {}
    for i in items:
        if i.startswith("key: asked "):
            _, _, sha, at = i.split()
            asked[sha] = dt.datetime.fromisoformat(at)
    out = []
    for sha in dict.fromkeys(i for i in items if not i.startswith("key:")):
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"limited_partnerships/sample.list names {sha}, which is not in the document store")
        if sha not in asked:
            raise ValueError(f"limited_partnerships/sample.list names {sha} with no `key: asked` line")
        nzbn = json.loads(read_bytes(sha)).get("nzbn")
        out.append((sha, nzbn, asked[sha]))
    return out


def fill(conn, schema: str, items: list) -> int:
    counts = load.build(conn, schema, answers_of(items), shared=True)
    return counts["partnerships"] + counts["partners"]
