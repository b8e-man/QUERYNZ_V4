"""One old table copied verbatim, in checked batches by key range (support/oldcopy/__init__.py says the whole).

The source connection is the old estate's, through the read-only old login, prepared by `prepare_source`
(autocommit off a snapshot per batch, read only, statement and lock timeouts); the destination is the new
database's owner connection, prepared by `prepare_dest`. Both carry the same output settings, so a row's text
is the same string on both sides and the md5s can be compared."""
import json
import time

from psycopg import IsolationLevel, sql

from support.oldcopy import DEST_PREFIX, DEST_SUFFIX, LEDGER, keytext, keyvalues

BATCH_ROWS = 5000
#: a table with no usable key is copied whole, in one checked batch, when it is no bigger than this; its md5 is
#: taken over the rows' md5s sorted, since there is no key to order them by. A bigger keyless table is refused.
WHOLE_MAX_BYTES = 1_000_000_000
STATEMENT_TIMEOUT_S = 300
# the same text for the same value on both sides: these settings govern every type's output
OUTPUT_SETTINGS = (("TimeZone", "UTC"), ("DateStyle", "ISO, YMD"), ("IntervalStyle", "postgres"),
                   ("extra_float_digits", "3"), ("bytea_output", "hex"))


class Refused(Exception):
    """The table is not copied: no usable key, a type the new database lacks, a shape that differs."""


class Mismatch(Exception):
    """A batch's rows or md5 at the destination are not the source's; rolled back and recorded."""


def _settings(conn, timeout_s: int) -> None:
    for k, v in OUTPUT_SETTINGS:
        conn.execute(sql.SQL("SELECT set_config({}, {}, false)").format(sql.Literal(k), sql.Literal(v)))
    conn.execute(sql.SQL("SELECT set_config('statement_timeout', {}, false)").format(sql.Literal(f"{int(timeout_s)}s")))
    conn.execute("SELECT set_config('lock_timeout', '30s', false)")


def prepare_source(conn, timeout_s: int = STATEMENT_TIMEOUT_S):
    """Every batch in one repeatable-read, read-only snapshot; nothing can be written through it (limit 22)."""
    conn.autocommit = True
    _settings(conn, timeout_s)
    conn.execute("SELECT set_config('default_transaction_read_only', 'on', false)")
    conn.isolation_level = IsolationLevel.REPEATABLE_READ
    return conn


def prepare_dest(conn, timeout_s: int = STATEMENT_TIMEOUT_S):
    conn.autocommit = False
    _settings(conn, timeout_s)
    conn.commit()
    return conn


def dest_schema(database: str) -> str:
    return f"{DEST_PREFIX}{database}{DEST_SUFFIX}"


def dest_table(schema: str, table: str) -> str:
    name = table if schema == "public" else f"{schema}__{table}"
    if len(name) > 63:
        raise Refused(f"the destination name {schema}__{table} is over 63 characters")
    return name


# ── the old catalogue ─────────────────────────────────────────────────────────

def catalogue(src, schema: str, table: str, key=()) -> dict:
    """The table's columns (name, type, collation) in order, its key, its size; Refused when it has no usable key or a
    column type outside pg_catalog that no extension owns."""
    with src.transaction():
        rel = src.execute(
            "SELECT c.oid, c.relkind, c.reltuples::bigint, pg_relation_size(c.oid) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relname = %s",
            (schema, table)).fetchone()
        if rel is None:
            raise Refused("no such table at the source")
        oid, kind, est_rows, size = rel
        if kind not in ("r", "p"):
            raise Refused(f"not a table (relkind {kind})")
        cols = src.execute(
            "SELECT a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull, "
            "  CASE WHEN a.attcollation <> 0 AND a.attcollation <> t.typcollation THEN co.collname END, "
            "  tn.nspname, EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = 'pg_type'::regclass "
            "    AND d.objid = COALESCE(NULLIF(t.typelem, 0), t.oid) AND d.deptype = 'e'), "
            "  COALESCE(et.typtype, t.typtype) "
            "FROM pg_attribute a JOIN pg_type t ON t.oid = a.atttypid JOIN pg_namespace tn ON tn.oid = t.typnamespace "
            "LEFT JOIN pg_type et ON et.oid = NULLIF(t.typelem, 0) AND t.typcategory = 'A' "
            "LEFT JOIN pg_collation co ON co.oid = a.attcollation "
            "WHERE a.attrelid = %s AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum", (oid,)).fetchall()
        idx = src.execute(
            "SELECT i.indisprimary, i.indkey::int2[], i.indexprs IS NULL AND i.indpred IS NULL "
            "FROM pg_index i WHERE i.indrelid = %s AND i.indisunique AND i.indisvalid "
            "ORDER BY i.indisprimary DESC, i.indnatts, i.indexrelid", (oid,)).fetchall()
        attnames = dict(src.execute(
            "SELECT attnum, attname FROM pg_attribute WHERE attrelid = %s AND attnum > 0", (oid,)).fetchall())
    columns = []
    for name, typ, notnull, coll, tns, ext, ttype in cols:
        if tns != "pg_catalog" and not ext:
            raise Refused(f"column {name}: type {typ} is the old database's own (an enum, domain, range or composite), "
                          f"not carried")
        columns.append({"name": name, "type": typ, "notnull": notnull, "collation": coll, "extension": ext})
    notnull = {c["name"] for c in columns if c["notnull"]}
    usable = []
    for primary, indkey, plain in idx:
        if not plain or 0 in indkey:
            continue
        names = tuple(attnames[k] for k in indkey)
        if primary or all(n in notnull for n in names):
            usable.append(names)
    if key:
        key = tuple(key)
        if key not in usable:
            raise Refused(f"the inventory's key {list(key)} is not a primary key or a unique NOT NULL index")
    elif usable:
        key = usable[0]
    elif int(size) <= WHOLE_MAX_BYTES:
        key = ()          # copied whole, in one batch
    else:
        raise Refused(f"no usable key (no primary key and no unique index on NOT NULL columns) and "
                      f"{int(size)} bytes, past the {WHOLE_MAX_BYTES} copied whole")
    types = {c["name"]: c["type"] for c in columns}
    return {"columns": columns, "key": key, "key_types": tuple(types[k] for k in key),
            "est_rows": int(est_rows), "bytes": int(size), "whole": not key}


def check_types(dst, cat: dict) -> None:
    missing = []
    for c in cat["columns"]:
        if dst.execute("SELECT to_regtype(%s) IS NOT NULL", (c["type"],)).fetchone()[0] is not True:
            missing.append(f"{c['name']} ({c['type']})")
    dst.rollback()
    if missing:
        raise Refused("the new database lacks the type of " + ", ".join(missing))


def _ident(*parts):
    return sql.SQL(".").join(sql.Identifier(p) for p in parts)


def ensure_dest(dst, cat: dict, schema: str, table: str) -> None:
    """The destination table with the old columns and types in the old order and the key as its primary key; a table
    already there must have exactly that shape."""
    dst.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema)))
    dst.execute(sql.SQL("REVOKE ALL ON SCHEMA {} FROM PUBLIC").format(sql.Identifier(schema)))
    have = dst.execute(
        "SELECT a.attname, format_type(a.atttypid, a.atttypmod) FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid "
        "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relname = %s AND a.attnum > 0 "
        "AND NOT a.attisdropped ORDER BY a.attnum", (schema, table)).fetchall()
    want = [(c["name"], c["type"]) for c in cat["columns"]]
    if have:
        if [tuple(h) for h in have] != want:
            dst.rollback()
            raise Refused(f"{schema}.{table} is already there with another shape")
        dst.commit()
        return
    defs = []
    for c in cat["columns"]:
        d = sql.SQL("{} {}").format(sql.Identifier(c["name"]), sql.SQL(c["type"]))
        if c["collation"]:
            d = sql.SQL("{} COLLATE {}").format(d, sql.Identifier(c["collation"]))
        defs.append(d)
    if cat["key"]:
        defs.append(sql.SQL("PRIMARY KEY ({})").format(sql.SQL(", ").join(sql.Identifier(k) for k in cat["key"])))
    dst.execute(sql.SQL("CREATE TABLE {} ({})").format(_ident(schema, table), sql.SQL(", ").join(defs)))
    dst.commit()


# ── one batch ─────────────────────────────────────────────────────────────────

def _keyrow(cat):
    return sql.SQL("({})").format(sql.SQL(", ").join(sql.Identifier(k) for k in cat["key"]))


def _bound(cat, values):
    return sql.SQL("({})").format(sql.SQL(", ").join(
        sql.SQL("{}::{}").format(sql.Literal(v), sql.SQL(t)) for v, t in zip(values, cat["key_types"])))


def _kept(cat):
    """The rows copied: none matching a leave_out pair (a NULL value never matches, so its row is kept)."""
    return [sql.SQL("NOT COALESCE({} ILIKE {}, false)").format(sql.Identifier(c), sql.Literal(p))
            for c, p in cat.get("leave_out", ())]


def _where(cat, after, through):
    parts = _kept(cat)
    if after is not None:
        parts.append(sql.SQL("{} > {}").format(_keyrow(cat), _bound(cat, after)))
    if through is not None:
        parts.append(sql.SQL("{} <= {}").format(_keyrow(cat), _bound(cat, through)))
    return sql.SQL(" AND ").join(parts) if parts else sql.SQL("true")


def _order(cat, desc=False):
    return sql.SQL(", ").join(sql.SQL("{}{}").format(sql.Identifier(k), sql.SQL(" DESC" if desc else ""))
                              for k in cat["key"])


def _cols(cat):
    return sql.SQL(", ").join(sql.Identifier(c["name"]) for c in cat["columns"])


def _keytext_select(cat):
    # aliased: an output column named like the key would make ORDER BY sort by its text
    return sql.SQL(", ").join(sql.SQL("{}::text AS {}").format(sql.Identifier(k), sql.Identifier(f"_oldcopy_k{i}"))
                              for i, k in enumerate(cat["key"]))


def next_bound(src, rel, cat, after, through, rows: int):
    """The inclusive upper key of the next batch: the key `rows` past `after`, else the last key up to `through`;
    None when nothing is left. Bounded by the key's index (LIMIT), never a scan of the table."""
    where = _where(cat, after, through)
    r = src.execute(sql.SQL("SELECT {} FROM {} WHERE {} ORDER BY {} LIMIT 1 OFFSET {}").format(
        _keytext_select(cat), rel, where, _order(cat), sql.Literal(rows - 1))).fetchone()
    if r is None:
        r = src.execute(sql.SQL("SELECT {} FROM {} WHERE {} ORDER BY {} LIMIT 1").format(
            _keytext_select(cat), rel, where, _order(cat, desc=True))).fetchone()
    return None if r is None else list(r)


def measure(conn, rel, cat, after, through) -> tuple:
    """(rows, md5) of a key range: md5 over each row's md5, in key order; the empty range's md5 is md5('')."""
    r = conn.execute(sql.SQL(
        "SELECT count(*), md5(COALESCE(string_agg(md5(s::text), '' ORDER BY {}), '')) "
        "FROM (SELECT {} FROM {} WHERE {}) s").format(_order(cat), _cols(cat), rel, _where(cat, after, through))
    ).fetchone()
    return int(r[0]), r[1]


def _stream(src, dst, src_rel, dst_rel, cat, after, through) -> int:
    """COPY the range out of the source and into the destination, block by block (two connections: a COPY and
    a cursor never share one, lessons/a-server-side-cursor-and-a-copy-cannot-share-one-connection.md)."""
    out = sql.SQL("COPY (SELECT {} FROM {} WHERE {} ORDER BY {}) TO STDOUT").format(
        _cols(cat), src_rel, _where(cat, after, through), _order(cat))
    into = sql.SQL("COPY {} ({}) FROM STDIN").format(dst_rel, _cols(cat))
    with src.cursor() as sc, dst.cursor() as dc:
        with sc.copy(out) as cin, dc.copy(into) as cout:
            for block in cin:
                cout.write(block)
        return dc.rowcount


def measure_whole(conn, rel, cat) -> tuple:
    """(rows, md5) of a whole keyless table: md5 over each row's md5, the row md5s sorted."""
    r = conn.execute(sql.SQL(
        "SELECT count(*), md5(COALESCE(string_agg(m, '' ORDER BY m), '')) FROM (SELECT md5(s::text) AS m "
        "FROM (SELECT {} FROM {} WHERE {}) s) h").format(_cols(cat), rel, _where(cat, None, None))).fetchone()
    return int(r[0]), r[1]


def _stream_whole(src, dst, src_rel, dst_rel, cat) -> int:
    out = sql.SQL("COPY (SELECT {} FROM {} WHERE {}) TO STDOUT").format(_cols(cat), src_rel, _where(cat, None, None))
    into = sql.SQL("COPY {} ({}) FROM STDIN").format(dst_rel, _cols(cat))
    with src.cursor() as sc, dst.cursor() as dc:
        with sc.copy(out) as cin, dc.copy(into) as cout:
            for block in cin:
                cout.write(block)
        return dc.rowcount


def copy_whole(src, dst, piece, cat, src_rel, dst_rel, ledger, log=print) -> dict:
    """A keyless table in one batch: the destination emptied, the rows streamed, counted and hashed on both sides,
    committed together with the ledger line or rolled back. Run again (--again), it replaces the copy whole."""
    b0 = time.monotonic()
    with src.transaction():
        n_src, md5_src = measure_whole(src, src_rel, cat)
        dst.execute(sql.SQL("TRUNCATE {}").format(dst_rel))
        n_copied = _stream_whole(src, dst, src_rel, dst_rel, cat)
    n_dst, md5_dst = measure_whole(dst, dst_rel, cat)
    secs = time.monotonic() - b0
    ok = n_src == n_copied == n_dst and md5_src == md5_dst
    why = None if ok else f"source {n_src} rows {md5_src}, copied {n_copied}, landed {n_dst} rows {md5_dst}"
    if not ok:
        dst.rollback()
    _ledger_line(dst, ledger, piece, 0, None, None, n_src, n_copied, n_dst, md5_src, md5_dst, ok,
                 why or "copied whole: no key", secs)
    if ok:
        _set_cursor(dst, ledger, piece, 0, None, True, n_dst)
    dst.commit()
    if not ok:
        raise Mismatch(f"{piece} (whole): {why}")
    log(f"support.oldcopy: {piece}: copied whole (no key), {n_dst} rows")
    return {"batches": 1, "rows": n_dst, "caught_up": True, "stopped": ""}


def _ledger_line(dst, ledger, piece, range_no, after, through, rs, rc, rl, ms, ml, ok, why, secs):
    dst.execute(sql.SQL(
        "INSERT INTO {}.batches (piece, range_no, after_key, through_key, rows_source, rows_copied, rows_landed, "
        "md5_source, md5_landed, ok, why, seconds) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)").format(
        sql.Identifier(ledger)), (piece, range_no, keytext(after), keytext(through), rs, rc, rl, ms, ml, ok, why,
                                  round(secs, 3)))


def cursor_of(dst, ledger, piece, range_no):
    r = dst.execute(sql.SQL("SELECT after_key, caught_up FROM {}.cursors WHERE piece = %s AND range_no = %s").format(
        sql.Identifier(ledger)), (piece, range_no)).fetchone()
    return (None, False) if r is None else (keyvalues(r[0]), r[1])


def _set_cursor(dst, ledger, piece, range_no, after, caught_up, rows):
    dst.execute(sql.SQL(
        "INSERT INTO {}.cursors (piece, range_no, after_key, caught_up, batches, rows) VALUES (%s,%s,%s,%s,%s,%s) "
        "ON CONFLICT (piece, range_no) DO UPDATE SET after_key = EXCLUDED.after_key, caught_up = EXCLUDED.caught_up, "
        "batches = {}.cursors.batches + EXCLUDED.batches, rows = {}.cursors.rows + EXCLUDED.rows, updated_at = now()"
    ).format(sql.Identifier(ledger), sql.Identifier(ledger), sql.Identifier(ledger)),
        (piece, range_no, keytext(after), caught_up, 1 if rows else 0, rows))


def refuse(dst, ledger, piece, why) -> None:
    dst.rollback()
    dst.execute(sql.SQL("INSERT INTO {}.refusals (piece, why) VALUES (%s, %s)").format(sql.Identifier(ledger)),
                (piece, why[:500]))
    dst.commit()


def copy_table(src, dst, spec, *, schema: str = None, ledger: str = LEDGER, rows: int = BATCH_ROWS,
               budget_s: float = 1200, stop=lambda: False, log=print) -> dict:
    """Copy `spec` (an inventory.Table) into `schema` (default old_<database>_private) until it is caught up, the
    budget is spent or `stop()` says so (dawn). Returns {"batches", "rows", "caught_up", "stopped"}. Raises Refused
    (recorded) or Mismatch (recorded, the batch rolled back)."""
    piece = spec.piece
    schema = schema or dest_schema(spec.database)
    try:
        cat = catalogue(src, spec.schema, spec.table, spec.key)
        cat["leave_out"] = tuple(spec.leave_out)
        for c, _ in spec.leave_out:
            if c not in {x["name"] for x in cat["columns"]}:
                raise Refused(f"leave_out names {c}, not a column of the table")
        check_types(dst, cat)
        table = dest_table(spec.schema, spec.table)
        ensure_dest(dst, cat, schema, table)
    except Refused as exc:
        refuse(dst, ledger, piece, str(exc))
        raise
    src_rel, dst_rel = _ident(spec.schema, spec.table), _ident(schema, table)
    t0, done = time.monotonic(), {"batches": 0, "rows": 0, "caught_up": True, "stopped": ""}
    if cat["whole"]:
        if tuple(spec.ranges) != ((None, None),):
            refuse(dst, ledger, piece, "no usable key, so its missing ranges cannot be named")
            raise Refused(f"{piece}: no usable key, so its missing ranges cannot be named")
        if stop():
            done.update(caught_up=False, stopped="window")
            return done
        return copy_whole(src, dst, piece, cat, src_rel, dst_rel, ledger, log=log)
    for range_no, (lo, hi) in enumerate(spec.ranges):
        after, _ = cursor_of(dst, ledger, piece, range_no)
        dst.rollback()
        after = after if after is not None else lo
        while True:
            if time.monotonic() - t0 > budget_s:
                done.update(caught_up=False, stopped="budget")
                return done
            if stop():
                done.update(caught_up=False, stopped="window")
                return done
            b0 = time.monotonic()
            with src.transaction():           # one snapshot: the bound, the measure and the rows
                bound = next_bound(src, src_rel, cat, after, hi, rows)
                if bound is None:
                    _set_cursor(dst, ledger, piece, range_no, after, True, 0)
                    dst.commit()
                    break
                n_src, md5_src = measure(src, src_rel, cat, after, bound)
                n_copied = _stream(src, dst, src_rel, dst_rel, cat, after, bound)
            n_dst, md5_dst = measure(dst, dst_rel, cat, after, bound)
            secs = time.monotonic() - b0
            if n_src == n_copied == n_dst and md5_src == md5_dst:
                _ledger_line(dst, ledger, piece, range_no, after, bound, n_src, n_copied, n_dst, md5_src, md5_dst,
                             True, None, secs)
                _set_cursor(dst, ledger, piece, range_no, bound, False, n_dst)
                dst.commit()
                done["batches"] += 1
                done["rows"] += n_dst
                after = bound
                continue
            dst.rollback()
            why = f"source {n_src} rows {md5_src}, copied {n_copied}, landed {n_dst} rows {md5_dst}"
            _ledger_line(dst, ledger, piece, range_no, after, bound, n_src, n_copied, n_dst, md5_src, md5_dst,
                         False, why, secs)
            dst.commit()
            raise Mismatch(f"{piece} range {range_no}: {why}")
    log(f"support.oldcopy: {piece}: {done['batches']} batch(es), {done['rows']} rows, caught up")
    return done


def dry_run(src, spec, *, rows: int = BATCH_ROWS, max_batches: int = 10_000, types_in=None, log=print) -> dict:
    """The table's catalogue and its batches measured at the source, nothing written anywhere: rows, the md5 of each
    batch and a combined md5 (md5 over the batch md5s in order, so it depends on `rows`; the ledger's md5_source
    column gives the same figure for a copy made with the same batch size). `types_in`, a read connection to the new
    database, checks every column's type is there (Refused if not)."""
    cat = catalogue(src, spec.schema, spec.table, spec.key)
    cat["leave_out"] = tuple(spec.leave_out)
    if types_in is not None:
        check_types(types_in, cat)
    rel = _ident(spec.schema, spec.table)
    if cat["whole"]:
        with src.transaction():
            n, m = measure_whole(src, rel, cat)
        out = {"piece": spec.piece, "key": [], "whole": True, "columns": len(cat["columns"]),
               "est_rows": cat["est_rows"], "bytes": cat["bytes"], "rows": n, "batches": 1, "md5": m, "complete": True}
        log("support.oldcopy: dry run " + json.dumps(out))
        return out
    total, md5s = 0, []
    for lo, hi in spec.ranges:
        after = lo
        while len(md5s) < max_batches:
            with src.transaction():
                bound = next_bound(src, rel, cat, after, hi, rows)
                if bound is None:
                    break
                n, m = measure(src, rel, cat, after, bound)
            total += n
            md5s.append(m)
            after = bound
    import hashlib
    combined = hashlib.md5("".join(md5s).encode()).hexdigest()
    out = {"piece": spec.piece, "key": list(cat["key"]), "columns": len(cat["columns"]), "est_rows": cat["est_rows"],
           "bytes": cat["bytes"], "rows": total, "batches": len(md5s), "md5": combined,
           "complete": len(md5s) < max_batches}
    log("support.oldcopy: dry run " + json.dumps(out))
    return out
