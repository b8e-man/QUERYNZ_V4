"""The lane's one check against the outside world (contract: the lane): for
each year the database lists, its own "Search Results (N)" against the
cases this lane holds for that year (abstract and every linked PDF landed).

The source's count is the newest listing read of the year (`listings`,
page 1); `--live` asks again through the fetch gate, off-peak only. A year
where held exceeds the source is `withdrawn` (the database dropped a
decision we hold), not a fault; a year short is a fault until the capture
reaches it.

    compare(source, held)      {"equal": [...], "short": [...], "withdrawn": [...]}
    python -m registers.real_estate_authority.check [--schema real_estate_authority] [--live]

Read-only on the database. Exit 1 when any year is short.
"""
import datetime as dt
import sys


def compare(source: dict, held: dict) -> dict:
    out = {"equal": [], "short": [], "withdrawn": []}
    for y in sorted(set(source) | set(held)):
        s, h = int(source.get(y, 0)), int(held.get(y, 0))
        out["equal" if s == h else "short" if h < s else "withdrawn"].append({"year": y, "source": s, "held": h})
    return out


def source_counts(conn, schema: str) -> dict:
    cur = conn.execute(f"SELECT DISTINCT ON (year) year, num_found FROM {schema}.listings ORDER BY year, read_at DESC")
    return {r[0]: r[1] for r in cur}


def held_counts(conn, schema: str) -> dict:
    cur = conn.execute(f"SELECT year, count(*) FROM {schema}.cases WHERE captured_at IS NOT NULL GROUP BY year")
    return {r[0]: r[1] for r in cur}


def live_counts(years) -> dict:
    from registers.real_estate_authority import capture as C
    import support.fetchgate as fg
    out = {}
    for y in years:
        f = fg.open_url(C.listing_url(y), timeout=60)
        if f.blocked or f.status != 200:
            raise RuntimeError(f"{y}: {f.blocked or f.status}")
        out[y] = C.parse_listing(f.body)[0]
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "real_estate_authority"
    from support import db
    with db.connect(db.READ_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '60s'")
        source, held = source_counts(conn, schema), held_counts(conn, schema)
    if "--live" in argv:
        from registers.real_estate_authority import capture as C
        if not C.off_peak(dt.datetime.now().astimezone()):
            print("--live asks the source again and runs off-peak only")
            return 2
        source = live_counts(sorted(source))
    out = compare(source, held)
    for k in ("equal", "short", "withdrawn"):
        print(f"{k}: {len(out[k])} years, source {sum(r['source'] for r in out[k])}, held {sum(r['held'] for r in out[k])}")
    for r in out["short"]:
        print(f"  short {r['year']}: source {r['source']}, held {r['held']}")
    return 1 if out["short"] else 0


if __name__ == "__main__":
    sys.exit(main())
