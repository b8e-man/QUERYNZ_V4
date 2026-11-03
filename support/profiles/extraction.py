"""What each document has had extracted: one row per document, profile and field, the iteration it was extracted at
(Arthur, 3 November 2026: "store the profile id + iterator along with the document so we know what has been
extracted"). The table, `docs.extractions`, is in support/docstore/tables.sql beside `docs.documents`; it is a
ledger, never wiped by a load. A reader writes it in the same transaction as the reading it stores.

    done(conn, sha256, profile)         field → iteration extracted
    record(conn, sha256, profile, items, reader=, model=)   the items just extracted, at their iterations
    behind(conn, profile)               documents of a profile with a field below the profile's iteration: counts only
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
    out = {}
    for f, it in pr.latest((prof or {}).get("extract")).items():
        have = conn.execute("SELECT count(*) FROM docs.extractions WHERE profile = %s AND field = %s AND "
                            "iteration >= %s AND sha256 = ANY(%s)", (profile, f, it["iteration"], documents)).fetchone()[0]
        out[f] = len(documents) - have
    return out
