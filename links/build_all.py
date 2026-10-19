"""The whole links build in order, for the merge gate's staging step and the
proposed `qv4-links-build` job: rows, links, watch, groups, test pairs, the
six measurements. The old decisions are copied and mapped by `links.old`
once and promoted here only if the copy exists.

    python -m links.build_all [--schema links]
"""
from __future__ import annotations

import json
import sys

import links
from links import build, measure, old, pairs, rows


def run(conn, reader, s: str, log=print) -> dict:
    out = {"rows": rows.gather(conn, s, log, reader=reader)}
    out["links"] = build.build_links(conn, s, log, reader=reader)
    if conn.execute(f"SELECT count(*) FROM {s}.old_decisions").fetchone()[0]:
        out["promote"] = old.promote(conn, s, log)
    out["watch"] = build.build_watch(conn, s, log)
    out["groups"] = build.build_groups(conn, s, log)
    out["pairs"] = pairs.draw(conn, s, log=log)
    out["measurements"] = {k: v.get("seconds") for k, v in measure.run(conn, s, log).items()}
    return out


def main(argv=None) -> int:
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    s = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn, db.connect(db.OWNER_KEY, "querynz_v4") as reader:
        conn.execute("SET statement_timeout = 0")
        reader.execute("SET statement_timeout = 0")
        conn.execute(links.ddl(s))
        conn.commit()
        print(json.dumps(run(conn, reader, s), default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
