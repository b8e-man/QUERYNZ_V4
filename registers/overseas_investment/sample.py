"""The sample filler (plan 1b.6): `fill(conn, schema, items)` reads the
summaries sample.list names (`key: item <list> <sha256>` lines), from the
document store, through this branch's own reading, into `schema` of the
sample database (the lane's tables there carry its name; the private
statement goes to the schema's private twin). Each page is listed once per
case number it carries, as the office's listing lists it. The listing pages
and the documents about the source are listed for the tests, not read as
summaries. A document not in the store fails the fill, naming its hash. No
model is called and nothing is fetched."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from support.docstore.landing import names_of, path_for, read_bytes  # noqa: E402
from registers.overseas_investment import load, read  # noqa: E402


def entries_of(items: list, conn) -> list:
    """[(list, slug, case number, url, sha256, None)]: the slug from the page's own address, which the landing
    wrapper kept as a name of the document, and the case numbers from the page's own meta block."""
    for sha in (i for i in items if not i.startswith("key:")):
        if not os.path.exists(path_for(sha)):
            raise LookupError(f"overseas_investment/sample.list names {sha}, which is not in the document store")
    out = []
    for i in items:
        if i.startswith("key: item "):
            _, _, lst, sha = i.split()
            urls = [n for n in names_of(sha, conn) if n.startswith("https://")]
            if not os.path.exists(path_for(sha)) or not urls:
                raise LookupError(f"overseas_investment/sample.list names {sha}, which is not in the document store "
                                  "with its address")
            url = urls[0]
            cases = read._meta(read_bytes(sha).decode("utf-8", "replace")).get("case numbers") or ["?"]
            out += [(lst, url.rstrip("/").rsplit("/", 1)[1], c, url, sha, None) for c in cases]
    return out


def fill(conn, schema: str, items: list) -> int:
    return load.build(conn, schema, entries_of(items, conn))["decisions"]
