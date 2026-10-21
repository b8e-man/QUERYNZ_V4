"""The sample filler (plan 1b.6): `fill(conn, schema, items)` lands the
pinned listing (from the document store, or the session's scratch folder
where the once-only export wrote it), copies the listed documents that
sample.list names into the store by hash, reads them through this branch's
own code and fills `schema` of the sample database. No model is called;
nothing is fetched.

Every module fills one shared scratch schema, so this lane's tables there
carry its name (`courts_judgments`, …; load.table). The ledger of orders
there is the sample's own.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from registers.courts import capture  # noqa: E402
from registers.courts import load as L  # noqa: E402


def fill(conn, schema: str, items: list) -> int:
    hashes = [i.split()[0] for i in items if not i.startswith("key:")]
    if not hashes or hashes[0] != capture.LISTING_SHA:
        raise LookupError("courts/sample.list must name the pinned listing first")
    _, entries = capture.land_listing(conn)
    only = set(hashes[1:])
    unknown = only - {e["sha256"] for e in entries}
    if unknown:
        raise LookupError(f"courts/sample.list names {len(unknown)} hashes the listing does not: {sorted(unknown)[:3]}")
    conn.execute(L.capture_tables_sql(schema, shared=True))
    held, aside = capture.copy_all(conn, entries, only=only)
    return L.build(conn, schema, entries, held, aside, L.orders(conn, schema, shared=True), only=only,
                   shared=True)["judgments"]
