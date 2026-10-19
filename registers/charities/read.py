"""What the capture holds, listed: the pages of the feed landed in the
document store, per entity set and pass, and the catch log reconciled. No row
is read here. The reading of the captured feed (charities, officers and annual
returns) is built twice, in registers/charities_a (Fable) and
registers/charities_b (Opus), against the same tests; the one kept moves here.

A build reads its pages through `pages()`: the newest finished full pass of a
set, then every changes pass finished after it, in order. A row met in a later
page replaces the same key from an earlier one.

    python -m registers.charities.read            # the listing and the reconciliation, counts only
"""
import os
import sys

from registers.charities.capture import SCHEMA
from support.docstore.landing import names_of, path_for


def held(conn, schema: str = SCHEMA) -> list:
    """One line per entity set: its newest finished full pass, the changes
    passes since, and any pass half-done."""
    out = []
    names = [r[0] for r in conn.execute(f"SELECT DISTINCT entity_set FROM {schema}.capture_passes ORDER BY 1")]
    for s in names:
        full = conn.execute(f"SELECT pass_id, stated, pages, rows_landed, finished_at FROM {schema}.capture_passes "
                            "WHERE entity_set = %s AND mode IN ('full', 'whole') AND finished_at IS NOT NULL AND pages > 0 "
                            "ORDER BY finished_at DESC LIMIT 1", (s,)).fetchone()
        since = full[4] if full else None
        changes = conn.execute(f"SELECT count(*), coalesce(sum(rows_landed), 0) FROM {schema}.capture_passes "
                               "WHERE entity_set = %s AND mode = 'changes' AND finished_at IS NOT NULL "
                               "AND (%s::timestamptz IS NULL OR started_at >= %s)", (s, since, since)).fetchone()
        half = conn.execute(f"SELECT pass_id, mode, stated, pages, rows_landed FROM {schema}.capture_passes "
                            "WHERE entity_set = %s AND finished_at IS NULL ORDER BY pass_id DESC LIMIT 1", (s,)).fetchone()
        out.append({"set": s,
                    "full": None if not full else {"pass_id": full[0], "stated": full[1], "pages": full[2],
                                                   "rows": full[3], "finished": full[4].isoformat(timespec="minutes")},
                    "changes_passes": changes[0], "changes_rows": int(changes[1]),
                    "half_done": None if not half else {"pass_id": half[0], "mode": half[1], "stated": half[2],
                                                        "pages": half[3], "rows": half[4]}})
    return out


def pages(conn, entity_set: str, schema: str = SCHEMA) -> list:
    """(sha256, url) of every page a build reads for a set, in order: the
    newest finished full pass, then each finished changes pass after it."""
    full = conn.execute(f"SELECT pass_id, finished_at FROM {schema}.capture_passes WHERE entity_set = %s "
                        "AND mode IN ('full', 'whole') AND finished_at IS NOT NULL AND pages > 0 "
                        "ORDER BY finished_at DESC LIMIT 1", (entity_set,)).fetchone()
    if full is None:
        return []
    return [(r[0], r[1]) for r in conn.execute(
        f"SELECT g.sha256, g.url FROM {schema}.capture_pages g JOIN {schema}.capture_passes p USING (pass_id) "
        "WHERE p.pass_id = %s OR (p.entity_set = %s AND p.mode = 'changes' AND p.finished_at IS NOT NULL "
        "AND p.started_at >= %s) ORDER BY p.pass_id, g.page_no", (full[0], entity_set, full[1]))]


def reconcile(conn, schema: str = SCHEMA) -> list:
    """The catch log reconciled, as plain lines; empty when it does.
    Every pass: its listed pages add up to its own count of pages and rows,
    and every page's hash is a document in the store. A finished pass that
    asked for the feed's count holds that many rows, or says by how many it
    differs (the register moves while a pass runs). A pass with a catch-log
    line is half-done or finished with nothing landed for that item."""
    out = []
    for pid, s, mode, stated, pages_, rows, aside, done in conn.execute(
            f"SELECT pass_id, entity_set, mode, stated, pages, rows_landed, set_aside, finished_at IS NOT NULL "
            f"FROM {schema}.capture_passes ORDER BY pass_id"):
        n, r = conn.execute(f"SELECT count(*), coalesce(sum(rows), 0) FROM {schema}.capture_pages WHERE pass_id = %s",
                            (pid,)).fetchone()
        if (n, int(r)) != (pages_, rows):
            out.append(f"pass {pid} {s}: lists {n} pages / {r} rows, counts {pages_} / {rows}")
        shas = [r[0] for r in conn.execute(f"SELECT sha256 FROM {schema}.capture_pages WHERE pass_id = %s", (pid,))]
        missing = sum(1 for sha in shas if not os.path.exists(path_for(sha)) or not names_of(sha, conn))
        if missing:
            out.append(f"pass {pid} {s}: {missing} pages listed but not in the document store")
        logged = conn.execute(f"SELECT count(*) FROM {schema}.capture_set_aside WHERE pass_id = %s", (pid,)).fetchone()[0]
        if logged != aside:
            out.append(f"pass {pid} {s}: {logged} catch-log lines, counts {aside}")
        if done and mode == "full" and stated is not None and rows != stated:
            out.append(f"pass {pid} {s}: holds {rows} rows, the feed stated {stated} at its start ({rows - stated:+d})")
    return out


def main(argv=None) -> int:
    from support import db
    with db.connect(db.READ_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '30s'")
        for h in held(conn):
            print(h)
        lines = reconcile(conn)
    print("reconciles" if not lines else "\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
