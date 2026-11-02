"""The lane's checks (step 8.3). Outside: each source's rows read against the count the LINZ Data Service stated for
the pull (WFS `numberMatched`, read at the pull's start), within `TOLERANCE` (the service changes while a pull pages
through it). Inside: every landed row read or set aside, at most `SET_ASIDE_SHARE` set aside, a title number once in
the titles, every owner's title present among the titles once titles are loaded, and no column of an address.

    reading(conn, schema) -> [problems]       empty when green
    python -m registers.linz.check [--schema linz]
"""
import sys

TOLERANCE = 0.001
SET_ASIDE_SHARE = 0.001
#: owners whose title the titles layer does not carry: LINZ's two products are cut on different days
OWNERS_WITHOUT_TITLE_SHARE = 0.01


def reading(conn, schema: str) -> list:
    one = lambda q, *a: conn.execute(q, a).fetchone()[0]
    out = []
    loaded = conn.execute(f"SELECT source, pull_id, stated, landed, read, aside FROM {schema}.loaded_pulls").fetchall()
    for source, pull_id, stated, landed, read_n, aside in loaded:
        if read_n + aside != landed:
            out.append(f"{source}: {landed} rows landed in {pull_id}, {read_n} read and {aside} set aside")
        if stated and abs(landed - stated) > TOLERANCE * stated:
            out.append(f"{source}: {landed:,} rows landed against {stated:,} the service stated for {pull_id}")
        if landed and aside > SET_ASIDE_SHARE * landed:
            out.append(f"{source}: {aside} of {landed} rows set aside, over {SET_ASIDE_SHARE:.1%}")
    sources = {r[0] for r in loaded}
    if "titles" in sources:
        dup = one(f"SELECT count(*) FROM (SELECT title_no FROM {schema}.titles GROUP BY title_no HAVING count(*) > 1) d")
        if dup:
            out.append(f"titles: {dup} title numbers carried more than once")
        if "owners" in sources:
            n = one(f"SELECT count(*) FROM {schema}.owners")
            orphans = one(f"SELECT count(*) FROM {schema}.owners o WHERE NOT EXISTS "
                          f"(SELECT 1 FROM {schema}.titles t WHERE t.title_no = o.title_no)")
            if n and orphans > OWNERS_WITHOUT_TITLE_SHARE * n:
                out.append(f"owners: {orphans:,} of {n:,} owners name a title the titles layer does not carry")
    cols = [r[0] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = %s", (schema,))]
    bad = [c for c in cols if any(w in c for w in ("address", "street", "geom", "shape"))]
    if bad:
        out.append(f"columns that may carry an address or a geometry: {bad}")
    return out


def main(argv=None) -> int:
    from support import db
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "linz"
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '300s'")
        problems = reading(conn, schema)
    for p in problems:
        print("FAILS " + p)
    print("linz: " + ("; ".join(problems) or "reconciles"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
