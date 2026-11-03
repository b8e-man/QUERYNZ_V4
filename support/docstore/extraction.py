"""What each document has had extracted: one row per document, profile and field, the iteration it was extracted at
(Arthur, 3 November 2026: "store the profile id + iterator along with the document so we know what has been
extracted"). The table, `docs.extractions`, is in support/docstore/tables.sql beside `docs.documents`; it is a
ledger, never wiped by a load. A reader writes it in the same transaction as the reading it stores.

    done(conn, sha256, profile)         field → iteration extracted
    record(conn, sha256, profile, items, reader=, model=)   the items just extracted, at their iterations
    record_many(conn, rows)             a load's whole ledger at once: (sha256, profile, field, iteration, reader, model)
    behind(conn, profile, documents)    field → how many of the documents still want it at the profile's iteration
"""
import support.profiles as pr


def done(conn, sha256: str, profile: str) -> dict:
    return dict(conn.execute("SELECT field, iteration FROM docs.extractions WHERE sha256 = %s AND profile = %s",
                             (sha256, profile)).fetchall())


def record(conn, sha256: str, profile: str, items: list, *, reader: str, model: str = None) -> int:
    """Each item extracted, at its iteration; a row never moves back an iteration."""
    for it in items:
        conn.execute("INSERT INTO docs.extractions (sha256, profile, field, iteration, reader, model) "
                     "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (sha256, profile, field) DO UPDATE SET "
                     "iteration = EXCLUDED.iteration, reader = EXCLUDED.reader, model = EXCLUDED.model, at = now() "
                     "WHERE docs.extractions.iteration <= EXCLUDED.iteration",
                     (sha256, profile, it["field"], it["iteration"], reader, model))
    return len(items)


def behind(conn, profile: str, documents: list) -> dict:
    """field → how many of `documents` (sha256s of this profile) still want it at the profile's current iteration."""
    prof = pr.profile(profile)
    items = pr.latest((prof or {}).get("extract"))
    documents = sorted(set(documents))
    have = conn.execute("SELECT field, iteration, count(*) FROM docs.extractions WHERE profile = %s AND sha256 = ANY(%s) "
                        "GROUP BY 1, 2", (profile, documents)).fetchall()
    return {f: len(documents) - sum(n for field, i, n in have if field == f and i >= it["iteration"]) for f, it in items.items()}


def record_many(conn, rows) -> dict:
    """A load's extractions in one statement: `rows` are (sha256, profile, field, iteration, reader, model). A row
    never moves back an iteration, and a row unchanged is not written again (the ledger is not churned nightly). A
    document the store does not hold (docs.documents) has no row: its rows are counted as `not held`."""
    best = {}
    for sha, prof, f, n, reader, model in rows:
        k = (sha, prof, f)
        if k not in best or n > best[k][3]:
            best[k] = (sha, prof, f, n, reader, model)
    cols = list(zip(*best.values())) or [(), (), (), (), (), ()]
    arrays = "unnest(%s::text[], %s::text[], %s::text[], %s::int[], %s::text[], %s::text[]) AS i(sha256, profile, field, iteration, reader, model)"
    held = conn.execute(f"SELECT count(*) FILTER (WHERE d.sha256 IS NOT NULL), count(*) FILTER (WHERE d.sha256 IS NULL) "
                        f"FROM {arrays} LEFT JOIN docs.documents d ON d.sha256 = i.sha256", [list(c) for c in cols]).fetchone()
    written = conn.execute(
        f"INSERT INTO docs.extractions (sha256, profile, field, iteration, reader, model) "
        f"SELECT i.sha256, i.profile, i.field, i.iteration, i.reader, i.model FROM {arrays} "
        "JOIN docs.documents d ON d.sha256 = i.sha256 "
        "ON CONFLICT (sha256, profile, field) DO UPDATE SET iteration = EXCLUDED.iteration, reader = EXCLUDED.reader, "
        "model = EXCLUDED.model, at = now() WHERE docs.extractions.iteration <= EXCLUDED.iteration AND "
        "(docs.extractions.iteration, docs.extractions.reader, docs.extractions.model) IS DISTINCT FROM "
        "(EXCLUDED.iteration, EXCLUDED.reader, EXCLUDED.model)", [list(c) for c in cols]).rowcount
    return {"rows": len(best), "held": held[0], "not held": held[1], "written": written}


def held(conn, documents: list) -> set:
    """The documents of `documents` the store registers (docs.documents): only those can carry a ledger row."""
    return {r[0] for r in conn.execute("SELECT sha256 FROM docs.documents WHERE sha256 = ANY(%s)",
                                       (sorted(set(documents)),)).fetchall()}
