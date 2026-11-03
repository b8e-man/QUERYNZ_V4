"""The lane's checks (step 8.3). Outside: each source's rows read against the count the LINZ Data Service stated for
the pull (WFS `numberMatched`, read at the pull's start), within `TOLERANCE` (the service changes while a pull pages
through it). Inside: every landed row read or set aside, at most `SET_ASIDE_SHARE` set aside, a title number once in
the titles, every owner's title present among the titles once titles are loaded, and no column of an address in the lane's public schema or in any published
`pub.linz_*` view. Private (each title's street address, `linz_private`): the reader login cannot see the private
schema; every title address joins a title the titles carry (`TITLE_ADDRESS_ORPHAN_SHARE`); at least
`TITLE_ADDRESS_FLOOR` of the titles have one. By geometry (`title_address_points`, the titles the spine gives no
address): not empty, its titles among the titles and none already on the spine. Each catalogue source staged: one row
an id. Alignment: the lane's code and its profile's extract list agree
(support/profiles/align.py), and every `lands` column exists.

    reading(conn, schema) -> [problems]       empty when green
    python -m registers.linz.check [--schema linz]
"""
import re
import sys

TOLERANCE = 0.001
SET_ASIDE_SHARE = 0.001
#: owners whose title the titles layer does not carry: LINZ's two products are cut on different days
OWNERS_WITHOUT_TITLE_SHARE = 0.01
#: a column name that may carry an address or a geometry: never in the public schema or a published view
ADDRESSY = re.compile(r"address|street|geom|shape", re.I)
#: title addresses whose title the titles layer does not carry (the property spine and the titles are cut on different days)
TITLE_ADDRESS_ORPHAN_SHARE = 0.01
#: the share of titles the property spine gives an address, below which the join is red: 2,270,831 of 2,457,581
#: (92.4%) on the first full build, 4 November 2026 (a scratch build of the pulls of 3 November); a broken join falls far
#: below it, a week's drift does not
TITLE_ADDRESS_FLOOR = 0.85
PRIVATE_SOURCES = ("property_titles", "property_addresses", "addresses")


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
    bad = [c for c in cols if ADDRESSY.search(c)]
    if bad:
        out.append(f"columns that may carry an address or a geometry: {bad}")
    out += published_views(conn)
    out += private(conn, schema, sources)
    out += geometry(conn, schema)
    out += whole(conn, schema, sources)
    out += alignment(conn, schema)
    return out


def published_views(conn) -> list:
    """No `pub.linz_*` view carries a column that may hold an address or a geometry (hard limit 15 at a product's surface;
    the street address of a title is in `linz_private` only)."""
    rows = conn.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'pub' "
                        "AND table_name LIKE 'linz\\_%'").fetchall()
    bad = sorted(f"pub.{t}.{c}" for t, c in rows if ADDRESSY.search(c))
    return [f"published columns that may carry an address or a geometry: {bad}"] if bad else []


def private(conn, schema: str, sources: set) -> list:
    """The private schema is the reader login's blind spot; once all three spine sources are loaded the join is held to
    the titles."""
    from support import db
    from registers.linz import load
    priv = load.private_of(schema)
    out = []
    seen = conn.execute("SELECT has_schema_privilege(%s, n.nspname, 'USAGE') FROM pg_namespace n WHERE n.nspname = %s",
                        (db.ROLES["read"], priv)).fetchone()
    if seen and seen[0]:
        out.append(f"{priv}: the reader login can see the private schema")
    if not set(PRIVATE_SOURCES) <= sources:
        return out
    one = lambda q: conn.execute(q).fetchone()[0]  # noqa: E731
    rows = one(f"SELECT count(*) FROM {priv}.title_addresses")
    with_address = one(f"SELECT count(DISTINCT title_no) FROM {priv}.title_addresses")
    if "titles" in sources:
        titles = one(f"SELECT count(*) FROM {schema}.titles")
        orphans = one(f"SELECT count(DISTINCT a.title_no) FROM {priv}.title_addresses a WHERE NOT EXISTS "
                      f"(SELECT 1 FROM {schema}.titles t WHERE t.title_no = a.title_no)")
        if with_address and orphans > TITLE_ADDRESS_ORPHAN_SHARE * with_address:
            out.append(f"title_addresses: {orphans:,} of {with_address:,} titles with an address are not among the titles")
        if titles and (with_address - orphans) < TITLE_ADDRESS_FLOOR * titles:
            out.append(f"title_addresses: {with_address - orphans:,} of {titles:,} titles have a street address, "
                       f"under {TITLE_ADDRESS_FLOOR:.0%}")
    elif not rows:
        out.append("title_addresses: the three spine sources are loaded and the join is empty")
    return out


def geometry(conn, schema: str) -> list:
    """The geometry join, where this load made it (`<private>.title_address_points`): not empty, its titles among the
    titles, and none of them a title the spine already gives an address (it reaches the rest only)."""
    from registers.linz import load
    priv = load.private_of(schema)
    if not conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"{priv}.title_address_points",)).fetchone()[0]:
        return []
    one = lambda q: conn.execute(q).fetchone()[0]  # noqa: E731
    reached = one(f"SELECT count(DISTINCT title_no) FROM {priv}.title_address_points")
    if not reached:
        return ["title_address_points: the geometry join ran and reached no title"]
    out = []
    titles = f"{schema}.titles" if one(f"SELECT to_regclass('{schema}.titles') IS NOT NULL") else "linz.titles"
    orphans = one(f"SELECT count(DISTINCT g.title_no) FROM {priv}.title_address_points g WHERE NOT EXISTS "
                  f"(SELECT 1 FROM {titles} t WHERE t.title_no = g.title_no)")
    if orphans > TITLE_ADDRESS_ORPHAN_SHARE * reached:
        out.append(f"title_address_points: {orphans:,} of {reached:,} titles reached by geometry are not among the titles")
    spine = f"{priv}.title_addresses" if one(f"SELECT to_regclass('{priv}.title_addresses') IS NOT NULL") \
        else "linz_private.title_addresses"
    both = one(f"SELECT count(DISTINCT g.title_no) FROM {priv}.title_address_points g WHERE EXISTS "
               f"(SELECT 1 FROM {spine} s WHERE s.title_no = g.title_no)")
    if both:
        out.append(f"title_address_points: {both:,} titles reached by geometry already have a spine address")
    return out


def whole(conn, schema: str, sources: set) -> list:
    """Each catalogue source staged by this load: one row an id (the service's own row id or its single sort key)."""
    from registers.linz import capture, load
    out = []
    for s in sorted(sources & set(capture.WHOLE)):
        t = load.table_of(schema, s)
        dup = conn.execute(f"SELECT count(*) FROM (SELECT fid FROM {t} GROUP BY fid HAVING count(*) > 1) d").fetchone()[0]
        if dup:
            out.append(f"{s}: {dup:,} row ids carried more than once")
    return out


def alignment(conn, schema: str) -> list:
    """The lane's code and its profile's extract list agree, and every column a field lands in exists."""
    from support.profiles import align
    from registers.linz import extracts
    return extracts.problems() + align.live_problems(conn, extracts.LANE, extracts.where(schema))


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
