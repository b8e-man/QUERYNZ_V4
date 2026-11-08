"""The Insolvency Register lane's checks (exits 1 on failure).

reading(conn, schema) -> [problem]: the staged reading against the terms and against the API's own counts:

  - the removals are asked at least daily: once any estate is held, the removals cursor exists and is at most two days old
  - every estate is kept and flagged (ruling 142): a row whose status or type says suppressed carries `suppressed`, its
    names in the private schema and none in the row; a row the removals named after its answer carries `removal_seen_at`
  - no published or staged column names an address or a birth date (the identifying fields are in the private schema)
  - every identifying field of an estate the removals named, from before the removal, is kept and flagged `removed_at`
  - in equals out: estates held = read + unanswered + set aside (the build raises otherwise; repeated here on the tables)
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
    capture.ensure_ledger(conn, ledger_schema)
    held = conn.execute(f"SELECT count(*) FROM {ledger_schema}.search_seen").fetchone()[0] + conn.execute(
        f"SELECT count(DISTINCT estate) FROM {ledger_schema}.calls WHERE why IN ('detail', 'lookup') AND estate NOT IN "
        f"(SELECT estate FROM {ledger_schema}.search_seen)").fetchone()[0]
    cur = conn.execute(f"SELECT value FROM {ledger_schema}.cursor WHERE what = 'removals'").fetchone()
    if held and not cur:
        out.append("estates are held and the removals-and-corrections operation has never been asked")
    elif cur and (today - dt.date.fromisoformat(cur[0])).days > REMOVALS_MAX_AGE_DAYS:
        out.append(f"the removals were last asked to {cur[0]}: more than {REMOVALS_MAX_AGE_DAYS} days ago")
    p = capture.private_of(schema)
    n = conn.execute(f"SELECT count(*) FROM {schema}.estates WHERE (status ILIKE '%%suppress%%' OR insolvency_type ILIKE "
                     f"'%%suppress%%') IS DISTINCT FROM suppressed").fetchone()[0]
    if n:
        out.append(f"{n} staged row(s) whose suppression flag is not the register's words")
    n = conn.execute(f"SELECT count(*) FROM {schema}.estates e WHERE e.suppressed AND (e.name <> '' OR e.alternate_names "
                     f"IS NOT NULL OR e.trading_names IS NOT NULL OR e.organisation_name IS NOT NULL OR NOT EXISTS "
                     f"(SELECT 1 FROM {p}.suppressed_names s WHERE s.key = e.key))").fetchone()[0] \
        if conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"{p}.suppressed_names",)).fetchone()[0] else \
        conn.execute(f"SELECT count(*) FROM {schema}.estates WHERE suppressed").fetchone()[0]
    if n:
        out.append(f"{n} suppressed row(s) with a name in the row or none kept privately")
    removed_after = conn.execute(
        f"SELECT count(*) FROM {schema}.estates e WHERE e.removal_seen_at IS NULL AND EXISTS (SELECT 1 FROM "
        f"{ledger_schema}.removals r WHERE r.estate = e.estate_number AND NOT EXISTS (SELECT 1 FROM {ledger_schema}.calls c "
        f"WHERE c.estate = r.estate AND c.why IN ('detail', 'lookup') AND c.status = 200 AND c.at > r.seen_at) AND NOT "
        f"EXISTS (SELECT 1 FROM {ledger_schema}.search_seen s JOIN {ledger_schema}.calls c ON c.id = s.call WHERE "
        f"s.estate = r.estate AND c.status = 200 AND c.at > r.seen_at))").fetchone()[0]
    # a search page naming the estate after the removal is the register's answer since, as the load reads it
    # (load.build: the latest answer, detail or search, against read.removed); 3 November 2026: 982 estates the first
    # removals run named came back in the night's search walk, and the check, counting details only, held the load
    if removed_after:
        out.append(f"{removed_after} staged row(s) the removals named with no answer since, not flagged")
    stale = conn.execute(
        f"SELECT count(DISTINCT i.estate) FROM {capture.private_of(ledger_schema)}.identifiers i JOIN {ledger_schema}.removals r ON "
        f"r.estate = i.estate WHERE i.at <= r.seen_at AND i.removed_at IS NULL").fetchone()[0] \
        if conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"{capture.private_of(ledger_schema)}.identifiers",)).fetchone()[0] else 0
    if stale:
        out.append(f"{stale} estate(s) the removals named hold identifying fields from before, not flagged")
    # the identifying fields only in the private schema (4 November 2026: they had sat in the lane's own schema, which
    # the session login reads), and that schema hidden from the session and product logins
    for s in {schema, ledger_schema}:
        if conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"{s}.identifiers",)).fetchone()[0]:
            out.append(f"{s}.identifiers holds identifying fields outside the private schema")
    for role in ("qv4_read", "qv4_product"):
        if conn.execute("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s) AND EXISTS (SELECT 1 FROM pg_namespace "
                        "WHERE nspname = %s AND has_schema_privilege(%s, oid, 'USAGE'))",
                        (role, capture.private_of(ledger_schema), role)).fetchone()[0]:
            out.append(f"{role} can see {capture.private_of(ledger_schema)}")
    for (col,) in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND "
                               "table_name IN ('estates', 'unanswered', 'set_aside')", (schema,)).fetchall():
        if any(w in col.lower() for w in _FORBIDDEN):
            out.append(f"a column {col} names an address or a birth date")
    for (col,) in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'pub' AND "
                               "table_name IN ('insolvency_people', 'insolvency_companies')").fetchall():
        if any(w in col.lower() for w in _FORBIDDEN):
            out.append(f"a published column {col} names an address or a birth date")
    pub_, wh, sa = (conn.execute(f"SELECT count(*) FROM {schema}.{t}").fetchone()[0] for t in ("estates", "unanswered", "set_aside"))
    if held != pub_ + wh + sa:
        out.append(f"{held} estates held, {pub_} read + {wh} unanswered + {sa} set aside")
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
