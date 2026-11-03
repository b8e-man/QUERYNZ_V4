"""The Insolvency Register lane's checks (exits 1 on failure).

reading(conn, schema) -> [problem]: the staged reading against the terms and against the API's own counts:

  - the removals are asked at least daily: once any estate is held, the removals cursor exists and is at most two days old
  - no published row is suppressed, annulled, or past its window on the day of the check
  - no published or staged column names an address or a birth date (the lane reads none)
  - no estate the removals named holds identifying fields (addresses, month and year of birth) from before the removal
  - in equals out: estates held = published + withheld + set aside (the build raises otherwise; repeated here on the tables)
  - against the API: for each register, the estates the latest walk saw are within 1% of the sum of `totalItems` the API
    reported on the first page of each month searched (a walk not finished says so and is not a failure)

    python -m registers.insolvency.check [--schema insolvency | staging_…]
"""
import datetime as dt
import sys

from registers.insolvency import capture

REMOVALS_MAX_AGE_DAYS = 2
TOLERANCE = 0.01
_FORBIDDEN = ("address", "birth", "street", "suburb", "postcode")


def reading(conn, schema: str, ledger_schema: str = capture.SCHEMA, today: dt.date = None) -> list:
    today = today or capture.now_nz().date()
    out = []
    conn.execute(capture.ledger_sql(ledger_schema))
    held = conn.execute(f"SELECT count(*) FROM {ledger_schema}.search_seen").fetchone()[0] + conn.execute(
        f"SELECT count(DISTINCT estate) FROM {ledger_schema}.calls WHERE why IN ('detail', 'lookup') AND estate NOT IN "
        f"(SELECT estate FROM {ledger_schema}.search_seen)").fetchone()[0]
    cur = conn.execute(f"SELECT value FROM {ledger_schema}.cursor WHERE what = 'removals'").fetchone()
    if held and not cur:
        out.append("estates are held and the removals-and-corrections operation has never been asked")
    elif cur and (today - dt.date.fromisoformat(cur[0])).days > REMOVALS_MAX_AGE_DAYS:
        out.append(f"the removals were last asked to {cur[0]}: more than {REMOVALS_MAX_AGE_DAYS} days ago")
    n = conn.execute(f"SELECT count(*) FROM {schema}.estates WHERE status ILIKE '%%suppress%%' OR insolvency_type ILIKE "
                     f"'%%suppress%%' OR annulled_on IS NOT NULL OR shown_until < %s", (today,)).fetchone()[0]
    if n:
        out.append(f"{n} staged row(s) suppressed, annulled or past their window")
    removed_after = conn.execute(
        f"SELECT count(*) FROM {schema}.estates e WHERE EXISTS (SELECT 1 FROM {ledger_schema}.removals r WHERE "
        f"r.estate = e.estate_number AND NOT EXISTS (SELECT 1 FROM {ledger_schema}.calls c WHERE c.estate = r.estate "
        f"AND c.why IN ('detail', 'lookup') AND c.status = 200 AND c.at > r.seen_at))").fetchone()[0]
    if removed_after:
        out.append(f"{removed_after} staged row(s) the removals named with no answer since")
    stale = conn.execute(
        f"SELECT count(DISTINCT i.estate) FROM {ledger_schema}.identifiers i JOIN {ledger_schema}.removals r ON "
        f"r.estate = i.estate WHERE i.at <= r.seen_at").fetchone()[0] \
        if conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"{ledger_schema}.identifiers",)).fetchone()[0] else 0
    if stale:
        out.append(f"{stale} estate(s) the removals named still hold identifying fields from before")
    for (col,) in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND "
                               "table_name IN ('estates', 'withheld', 'set_aside')", (schema,)).fetchall():
        if any(w in col.lower() for w in _FORBIDDEN):
            out.append(f"a column {col} names an address or a birth date")
    for (col,) in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'pub' AND "
                               "table_name IN ('insolvency_people', 'insolvency_companies')").fetchall():
        if any(w in col.lower() for w in _FORBIDDEN):
            out.append(f"a published column {col} names an address or a birth date")
    pub_, wh, sa = (conn.execute(f"SELECT count(*) FROM {schema}.{t}").fetchone()[0] for t in ("estates", "withheld", "set_aside"))
    if held != pub_ + wh + sa:
        out.append(f"{held} estates held, {pub_} published + {wh} withheld + {sa} set aside")
    if held and sa > held * TOLERANCE:
        out.append(f"{sa} of {held} estates set aside: more than {TOLERANCE:.0%}")
    for register, said, seen in against_api(conn, ledger_schema):
        if said and abs(seen - said) > said * TOLERANCE:
            out.append(f"{register}: the API reported {said:,} estates over the months walked, {seen:,} seen")
    return out


def against_api(conn, schema: str = capture.SCHEMA) -> list:
    """[(register, the API's totalItems summed over the latest first page of each month searched, estates seen)]."""
    out = []
    for (register,) in conn.execute(f"SELECT DISTINCT register FROM {schema}.search_seen").fetchall():
        said = conn.execute(
            f"SELECT coalesce(sum(t), 0) FROM (SELECT DISTINCT ON (split_part(asked, '&page=', 1)) total_items AS t "
            f"FROM {schema}.calls WHERE why = 'search' AND status = 200 AND asked LIKE %s AND asked LIKE '%%&page=1&%%' "
            f"ORDER BY split_part(asked, '&page=', 1), at DESC) x", (f"%register={register}%",)).fetchone()[0]
        seen = conn.execute(f"SELECT count(*) FROM {schema}.search_seen WHERE register = %s", (register,)).fetchone()[0]
        out.append((register, int(said), seen))
    return out


def main(argv=None) -> int:
    from support import db
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else capture.SCHEMA
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '120s'")
        problems = reading(conn, schema)
        for register, said, seen in against_api(conn):
            print(f"{register}: the API reported {said:,}; {seen:,} seen")
    for p in problems:
        print("FAILS " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
