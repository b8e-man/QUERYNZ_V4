"""The links tables found empty are built again at once (Arthur, 26 November 2026).

The tables a build makes again are UNLOGGED (tables.sql): a crash of the database server or a takeover leaves them
empty, and without this the board and every product would show no links until the 07:45 build. Every 15 minutes
`qv4-links-empty` asks whether `links.links` holds a row; when it holds none and no `qv4-links-build` is queued or
running, it queues one.

    python -m links.empty            one look; prints what it found and did
"""
from __future__ import annotations

import sys

BUILD = "qv4-links-build"


def look(conn, schema: str, enqueue=None) -> str:
    """One look: the line the job prints."""
    held = conn.execute("SELECT EXISTS (SELECT 1 FROM links.links)").fetchone()[0]
    if held:
        return "links.links holds rows: nothing to do"
    have = conn.execute(f"SELECT id, state FROM {schema}.queue WHERE job = %s AND state IN ('queued', 'leased') "
                        f"ORDER BY id LIMIT 1", (BUILD,)).fetchone()
    if have:
        return f"links.links is empty; {BUILD} already {have[1]} as row {have[0]}"
    if enqueue is None:
        from support.scheduler import queue as q
        enqueue = q.enqueue
    row = enqueue(conn, schema, BUILD, cls="whenever", created_by="links.empty: links.links found empty")
    return f"links.links is empty (a crash or a takeover leaves the unlogged tables so): queued {BUILD} as row {row}"


def main(argv=None) -> int:
    from support import db
    from support.scheduler import SCHEMA
    with db.connect(db.OWNER_KEY, "querynz_v4", autocommit=True) as conn:
        print(look(conn, SCHEMA))
    return 0


if __name__ == "__main__":
    sys.exit(main())
