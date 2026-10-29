"""The whole links build in order, for the merge gate's staging step and the
proposed `qv4-links-build` job: rows, links, watch, groups, entities (ruling
123), test pairs, the six measurements. At each build the copy of the old ledgers is brought
level with the old database (the new rows, the withdrawals re-read),
mapped onto the rows just gathered, and promoted (`links.old`), so the
outside check compares like with like.

    python -m links.build_all [--schema links]
"""
from __future__ import annotations

import json
import sys

import links
from links import build, measure, old, pairs, rows


def run(conn, reader, s: str, log=print, oldconn=None) -> dict:
    """`oldconn`: the old database through its read-only login; without it
    the copy held is promoted as it stands (a session's scratch build)."""
    out = {"rows": rows.gather(conn, s, log, reader=reader)}
    out["links"] = build.build_links(conn, s, log, reader=reader)
    if oldconn is not None:
        out["old_copy"] = old.copy_ledgers(oldconn, conn, s, log)
        out["old_map"] = old.map_all(oldconn, conn, s, log)
    if conn.execute(f"SELECT count(*) FROM {s}.old_decisions").fetchone()[0]:
        out["promote"] = old.promote(conn, s, log)
    out["watch"] = build.build_watch(conn, s, log)
    out["groups"] = build.build_groups(conn, s, log)
    out["entities"] = build.build_entities(conn, s, log)
    out["pairs"] = pairs.draw(conn, s, log=log)
    out["measurements"] = {k: v.get("seconds") for k, v in measure.run(conn, s, log).items()}
    return out


def main(argv=None) -> int:
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    s = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn, db.connect(db.OWNER_KEY, "querynz_v4") as reader, \
            db.connect(db.OLD_READ_KEY, old.OLD_DB) as oldconn:
        conn.execute("SET statement_timeout = 0")
        reader.execute("SET statement_timeout = 0")
        oldconn.execute("SET statement_timeout = '300s'")
        conn.execute(links.ddl(s))
        conn.commit()
        print(json.dumps(run(conn, reader, s, oldconn=oldconn), default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
