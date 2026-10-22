"""The sample filler (plan 1b.6): `fill(conn, schema, items)` reads each
`key: data <package> <sha256>` file of sample.list from the document store,
through this branch's own reading, into `schema` of the sample database
(the lane's tables carry its name there: `contract_disclosures_costs`, …).
Any other hash is a document the capture holds and the reading does not.
A document not in the store fails the fill, naming its hash. No model is
called and nothing is fetched."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import path_for  # noqa: E402
from registers.contract_disclosures import load  # noqa: E402


def files_of(items: list) -> dict:
    out = {}
    for i in items:
        sha = i.split()[-1]
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"contract_disclosures/sample.list names {sha}, which is not in the document store")
        if i.startswith("key: data "):
            out[sha] = i.split()[2]
    return out


def fill(conn, schema: str, items: list) -> int:
    return load.build(conn, schema, files_of(items), shared=True)["rows"]
