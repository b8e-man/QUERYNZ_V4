"""The lane's check against the world outside it (contract: the lane), and
the reconciliation of every captured page to typed rows and set-asides.

The register's own figure: the count the feed stated for Organisations on
the first page of the full pass the build read (`$inlinecount=allpages`,
the feed's count on the capture day, recorded by the capture lane in
`charities.capture_passes.stated`; lesson: never `/$count`, which obeys
the 1,000-row cap). Against it, this build's charities. The pass ran for
hours after its count was taken and the register moved meanwhile: a row
whose `ModifiedOn` is on or after the pass began is counted as moved, and
the check passes when the difference between the build's count and the
register's is no larger than the rows that moved, and no page fails to
reconcile. Nothing is fetched: the capture lane's `--measure` is the live
arm, and it is the capture's.

  register          the feed's own count on the capture day
  build             this build's charities (every organisation row with a number)
  registered        of those, status Registered (the register publishes this count too; compared by --measure)
  moved             rows modified on or after the pass began
  difference        build - register
  pages             every listed page: a files row with the same row count, and rows = typed + set aside (+ filtered)

    figures(conn, schema, shared, listing_conn)   the comparison
    failed(f)                                     the reasons the check fails, empty when it passes
    python -m registers.charities_a.check [--schema scratch_charities_a] [--database querynz_v4_sample]

Read-only.
"""
import argparse
import json
import sys

from registers.charities.capture import SCHEMA as CAPTURE
from registers.charities import read as capture_read
from registers.charities_a import load


def pass_of(listing_conn, entity_set: str = "Organisations"):
    """(pass_id, stated, rows_landed, started_at, finished_at) of the newest finished full pass."""
    r = listing_conn.execute(
        f"SELECT pass_id, stated, rows_landed, started_at, finished_at FROM {CAPTURE}.capture_passes "
        "WHERE entity_set = %s AND mode IN ('full', 'whole') AND finished_at IS NOT NULL AND pages > 0 "
        "ORDER BY finished_at DESC LIMIT 1", (entity_set,)).fetchone()
    return r


def reconcile_pages(conn, schema: str, shared: bool, listing_conn) -> list:
    """Plain lines, one per page that does not reconcile; empty when every page does."""
    out = []
    files = {(r[0], r[1]): r for r in conn.execute(
        f"SELECT document, entity_set, rows, typed, set_aside, filtered FROM {load.table(schema, 'files', shared)}")}
    listed = {(r[0], r[1]): r[2] for r in listing_conn.execute(
        f"SELECT g.sha256, g.entity_set, g.rows FROM {CAPTURE}.capture_pages g")}
    for s in load.SETS:
        for sha, _ in capture_read.pages(listing_conn, s):
            f = files.get((sha, s))
            if f is None:
                out.append(f"{s} page {sha[:12]}: listed by the capture, not read by the load")
                continue
            rows, typed, aside, filtered = f[2], f[3], f[4], f[5]
            if typed + aside + filtered != rows:
                out.append(f"{s} page {sha[:12]}: {rows} rows, {typed} typed + {aside} set aside + {filtered} filtered")
            if (sha, s) in listed and listed[(sha, s)] != rows:
                out.append(f"{s} page {sha[:12]}: the load read {rows} rows, the capture listed {listed[(sha, s)]}")
    return out


def figures(conn, schema: str = load.SCHEMA, shared: bool = False, listing_conn=None) -> dict:
    listing_conn = listing_conn or conn
    T = lambda t: load.table(schema, t, shared)
    p = pass_of(listing_conn)
    f = {"schema": schema}
    if p is None:
        f["detail"] = "no finished full pass of Organisations is listed"
        return f
    pass_id, stated, landed, started, finished = p
    f.update({"pass_id": pass_id, "pass_started": started.isoformat(timespec="minutes"),
              "pass_finished": finished.isoformat(timespec="minutes"), "register": stated, "landed": landed})
    f["build"] = conn.execute(f"SELECT count(*) FROM {T('charities')}").fetchone()[0]
    f["registered"] = conn.execute(f"SELECT count(*) FROM {T('charities')} WHERE status = 'Registered'").fetchone()[0]
    f["moved"] = conn.execute(f"SELECT count(*) FROM {T('charities')} WHERE modified_at >= %s", (started,)).fetchone()[0]
    f["registered_since_pass_began"] = conn.execute(
        f"SELECT count(*) FROM {T('charities')} WHERE registered_on >= %s", (started.date(),)).fetchone()[0]
    f["difference"] = (f["build"] - stated) if stated is not None else None
    f["set_aside"] = {f"{s}: {r}": n for s, r, n in conn.execute(
        f"SELECT stage, reason, sum(count) FROM {T('set_aside')} GROUP BY 1, 2 ORDER BY 3 DESC, 1, 2")}
    f["tables"] = {t: conn.execute(f"SELECT count(*) FROM {T(t)}").fetchone()[0]
                   for t in ("charities", "charity_officers", "charity_returns", "charity_groups", "codes")}
    f["pages_not_reconciled"] = reconcile_pages(conn, schema, shared, listing_conn)
    run = conn.execute(f"SELECT counts, seconds FROM {T('runs')} ORDER BY run_id DESC LIMIT 1").fetchone()
    if run:
        f["load_seconds"] = float(run[1])
        f["load_counts"] = run[0] if isinstance(run[0], dict) else json.loads(run[0])
    return f


def failed(f: dict) -> list:
    out = []
    if "register" not in f:
        return [f.get("detail", "no figures")]
    if f["register"] is None:
        out.append("the pass recorded no count from the register")
    elif abs(f["difference"]) > f["moved"]:
        out.append(f"the build holds {f['build']} charities, the register stated {f['register']}: "
                   f"{f['difference']:+d}, more than the {f['moved']} rows that moved during the pass")
    out += f.get("pages_not_reconciled", [])
    return out


def main(argv=None) -> int:
    from support import db, sample
    ap = argparse.ArgumentParser(prog="registers.charities_a.check")
    ap.add_argument("--schema", default=sample.scratch_name("charities-a"))
    ap.add_argument("--database", default="querynz_v4_sample")
    a = ap.parse_args(argv)
    shared = a.schema.startswith(db.SCRATCH_PREFIX)
    # the session's scratch schemas are the owner's (the session reader is not granted them); the listing is read-only
    with db.connect(db.OWNER_KEY, a.database) as conn, db.connect(db.READ_KEY, "querynz_v4") as listing_conn:
        conn.execute("SET statement_timeout = '120s'")
        listing_conn.execute("SET statement_timeout = '60s'")
        f = figures(conn, a.schema, shared, listing_conn if not load.has_listing(conn) else conn)
    why = failed(f)
    print(json.dumps({**f, "ok": not why, "failed": why}, indent=1, default=str))
    return 0 if not why else 1


if __name__ == "__main__":
    sys.exit(main())
