"""The ingest MCP as a source of the estate (rulings 94, 96).

`query-nz-ingest` (on Arthur's provider's box, reached through the tunnel
unit `qv4-mcp-tunnel`) serves corpora of beehive.govt.nz and parliament.nz
records, captured and read on that box, outside the estate. There is no
push: `corpora` reports each corpus's `ingest_cursor` (its record count;
records are appended in a stable arrival order) and `records` pages from
any cursor. So a pull polls `corpora` and takes `records` from the cursor
it stored last, 200 a page, one request at a time.

Every record lands whole as a captured document through the landing
wrapper: its bytes are the record's JSON, keys sorted, no spaces, UTF-8,
without `seq` (the record's place in the MCP's arrival order, which is the
server's bookkeeping and not the record: an unchanged record that arrives
again is the same document). Source `query-nz`; names `<corpus>/<id>` and
the record's `url` where it has one. A record the MCP later serves changed
has other bytes, so it lands as a second document under the same names,
never over the first (one frozen reading each). `arrivals` keeps each
record's `seq`, hash and `landed_at`; a lane takes as a record's current
version the one the pull saw last (by `landed_at`), never the highest `seq`
(after the MCP removes records, a re-rendered one comes back at a lower
place).

The cursor advances only after its page is landed, in the same transaction
as the page's arrival rows and catch lines. A record that cannot be landed
(no `id`, or a landing that failed twice) is a catch line and the cursor
passes it; `--retry-caught` asks for each such record again by its place.
The MCP changes records in place (re-processing moves `updated_at`), where
a cursor never looks: after the cursor, the pull follows the MCP's own
change feed `changes` from the newest stamp it has read to the end, and
each changed record lands as a second document. `--rewalk` (from 0, the
cursor unmoved) is the fallback if the feed is ever in doubt. A
page whose shape is not the MCP's (no `records`, a `seq` out of place) stops
the run and the cursor holds. A field the recorded shapes (`shapes.json`)
do not hold is landed (the bytes are whole) and logged in `drift`, and the
run is red until a register carries it.

    pull(conn, client, corpus)            one corpus, from its stored cursor
    pull_all(conn, client)                every corpus `corpora` names, then each one's change feed
    follow_changes(conn, client, corpus)  the MCP's `changes` from the stamp followed last
    python -m support.mcpsource [--database D] [--schema S] [--corpus C …]

Tests: support/mcpsource/tests/ (a fake server; the live shape, slow).
"""
import datetime as dt
import json
import os
import re
import time

from support.mcpsource.client import Client, McpError  # noqa: F401  (re-exported)

SOURCE = "query-nz"
SCHEMA = "mcpsource"
JOB = "qv4-mcp-pull"
PAGE = 200
PAUSE_S = 1.0
HERE = os.path.dirname(os.path.abspath(__file__))
LOCK_KEY = 0x6D6370                                   # 'mcp': one pull at a time per database
_TYPES = {str: "str", int: "int", float: "float", bool: "bool", type(None): "null", list: "list", dict: "dict"}


class ShapeError(Exception):
    """A page that is not the MCP's shape: the run stops, the cursor holds."""


def record_bytes(record: dict) -> bytes:
    """The document: the record's JSON, keys sorted, no spaces, without `seq`."""
    body = {k: v for k, v in record.items() if k != "seq"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def record_name(corpus: str, record_id: str) -> str:
    return f"{corpus}/{record_id}"


def shapes(path: str = None) -> dict:
    with open(path or os.path.join(HERE, "shapes.json"), encoding="utf-8") as f:
        return json.load(f)


def drift_of(record: dict, shape: dict) -> list:
    """[(field, type)] the recorded shape does not hold: a new field, or a
    type other than null it was not seen with; a list's items field by
    field (`quotes.speaker`), and a block's fields too (`capture.status`). A field a record lacks is not drift: the
    MCP's older records carry fewer fields."""
    out = []
    fields, items = (shape or {}).get("fields", {}), (shape or {}).get("items", {})
    for k, v in record.items():
        t = _TYPES.get(type(v), type(v).__name__)
        if k not in fields or (t != "null" and t not in fields[k]):
            out.append((k, t))
        if isinstance(v, (list, dict)):
            for x in (v if isinstance(v, list) else [v]):
                subs = x.items() if isinstance(x, dict) else (("*", x),)
                for kk, vv in subs:
                    tt = _TYPES.get(type(vv), type(vv).__name__)
                    known = items.get(k, {}).get(kk)
                    if known is None or (tt != "null" and tt not in known):
                        out.append((f"{k}.{kk}", tt))
    return sorted(set(out))


def check_page(page, corpus: str, cursor: int) -> list:
    """The page's records, or ShapeError: the MCP's page carries `records`
    and `next_cursor`, starts where it was asked, and numbers its records
    from there one by one."""
    if not isinstance(page, dict) or not isinstance(page.get("records"), list) or "next_cursor" not in page:
        raise ShapeError(f"{corpus}: the page at {cursor} is not the MCP's shape: "
                         f"{sorted(page) if isinstance(page, dict) else type(page).__name__}")
    recs = page["records"]
    if page.get("cursor", cursor) != cursor:
        raise ShapeError(f"{corpus}: asked for {cursor}, the page starts at {page.get('cursor')}")
    if page["next_cursor"] != cursor + len(recs):
        raise ShapeError(f"{corpus}: {len(recs)} records from {cursor} but next_cursor {page['next_cursor']}")
    for i, r in enumerate(recs):
        if not isinstance(r, dict) or r.get("seq") != cursor + i:
            raise ShapeError(f"{corpus}: record {i} of the page at {cursor} has seq "
                             f"{r.get('seq') if isinstance(r, dict) else type(r).__name__}, not {cursor + i}")
    return recs


class Tables:
    def __init__(self, conn, schema: str = SCHEMA):
        self.conn, self.schema = conn, schema

    def t(self, name: str) -> str:
        return f"{self.schema}.{name}"

    def create(self) -> None:
        with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
            # one pass: a schema whose own name holds `mcpsource_` (a session's scratch) is not replaced twice
            sql = re.sub(rf"\b{SCHEMA}(?=[._])", self.schema, f.read())
        with self.conn.transaction():
            self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
            self.conn.execute(sql)

    def cursor_of(self, corpus: str) -> int:
        row = self.conn.execute(f"SELECT cursor FROM {self.t('cursors')} WHERE corpus = %s", (corpus,)).fetchone()
        return row[0] if row else 0

    def cursors(self) -> dict:
        return {r[0]: r[1] for r in self.conn.execute(f"SELECT corpus, cursor FROM {self.t('cursors')}")}

    def try_lock(self) -> bool:
        return self.conn.execute("SELECT pg_try_advisory_lock(%s, hashtext(%s))", (LOCK_KEY, self.schema)).fetchone()[0]

    def unlock(self) -> None:
        self.conn.execute("SELECT pg_advisory_unlock(%s, hashtext(%s))", (LOCK_KEY, self.schema))

    def changes_since(self, corpus: str):
        """The stamp the change feed was last followed to; with none yet, an
        hour before this corpus was first taken (UTC), so every record the
        MCP changed since the first pull began is asked for."""
        row = self.conn.execute(f"SELECT changes_since FROM {self.t('cursors')} WHERE corpus = %s", (corpus,)).fetchone()
        if row and row[0]:
            return row[0]
        first = self.conn.execute(f"SELECT min(landed_at) FROM {self.t('arrivals')} WHERE corpus = %s", (corpus,)).fetchone()
        if not first or first[0] is None:
            return None
        return (first[0] - dt.timedelta(hours=1)).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def rewalk_at(self, corpus: str) -> int:
        row = self.conn.execute(f"SELECT rewalk_at FROM {self.t('cursors')} WHERE corpus = %s", (corpus,)).fetchone()
        return row[0] if row and row[0] is not None else 0

    def set_rewalk_at(self, corpus: str, at) -> None:
        self.conn.execute(f"UPDATE {self.t('cursors')} SET rewalk_at = %s WHERE corpus = %s", (at, corpus))

    def set_changes_since(self, corpus: str, stamp: str) -> None:
        self.conn.execute(f"UPDATE {self.t('cursors')} SET changes_since = %s WHERE corpus = %s", (stamp, corpus))

    def commit_page(self, corpus: str, cursor: int, total, arrivals: list, catches: list, drift: dict,
                    move: bool = True) -> None:
        """The page's arrival rows, catch lines and drift, and the cursor
        moved past it (unless `move` is false: a re-walk), in one transaction."""
        with self.conn.transaction():
            with self.conn.cursor() as cur:
                if arrivals:
                    cur.executemany(f"INSERT INTO {self.t('arrivals')} (corpus, seq, record_id, url, sha256, new) "
                                    "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (corpus, seq, sha256) DO NOTHING", arrivals)
                if catches:
                    cur.executemany(f"INSERT INTO {self.t('catch')} (corpus, seq, record_id, stage, reason) "
                                    "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (corpus, seq, stage) "
                                    "DO UPDATE SET reason = EXCLUDED.reason, at = now(), resolved_at = NULL", catches)
                for (field, t), (first, n) in sorted(drift.items()):
                    cur.execute(f"INSERT INTO {self.t('drift')} (corpus, field, type, first_seq, records) "
                                "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (corpus, field, type) "
                                f"DO UPDATE SET records = {self.t('drift')}.records + EXCLUDED.records", (corpus, field, t, first, n))
            if not move:
                return
            self.conn.execute(f"INSERT INTO {self.t('cursors')} (corpus, cursor, source_total, updated_at) "
                              "VALUES (%s, %s, %s, now()) ON CONFLICT (corpus) DO UPDATE SET cursor = EXCLUDED.cursor, "
                              "source_total = EXCLUDED.source_total, updated_at = now()", (corpus, cursor, total))


def land_record(conn, corpus: str, record: dict, fetched_at: str, root: str = None, land=None):
    """(sha256, new) for one record landed under its names (its bytes as served: an `id` stays its own type)."""
    if land is None:
        from support.docstore.landing import land
    data = record_bytes(record)
    ref, new = land(data, name=record_name(corpus, str(record["id"])), source=SOURCE, conn=conn, name_kind="file",
                    content_type="application/json", fetched_at=fetched_at, root=root)
    url = record.get("url")
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        land(data, name=url, source=SOURCE, conn=conn, name_kind="url", content_type="application/json",
             fetched_at=fetched_at, root=root)
    return ref.sha256, new


def _land_page(conn, corpus: str, recs: list, shape: dict, root, land, log):
    at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    arrivals, catches, drift, n = [], [], {}, {"landed": 0, "held": 0, "caught": 0}
    for r in recs:
        for d in drift_of(r, shape):
            first, k = drift.get(d, (r["seq"], 0))
            drift[d] = (first, k + 1)
        rid = r.get("id")
        if not isinstance(rid, (str, int)) or str(rid) == "":
            catches.append((corpus, r["seq"], None, "shape", f"no id: fields {sorted(r)[:12]}"))
            n["caught"] += 1
            continue
        rid = str(rid)
        why = None
        for attempt in (1, 2):                         # a failed landing is retried once, then caught
            try:
                sha, new = land_record(conn, corpus, r, at, root, land)
                break
            except Exception as exc:  # noqa: BLE001 — one record's failure is a catch line, not the night's end
                why = f"{type(exc).__name__}: {str(exc)[:300]}"
        else:
            catches.append((corpus, r["seq"], rid, "land", why))
            n["caught"] += 1
            if log:
                log(f"mcpsource: {corpus} seq {r['seq']}: not landed ({why[:120]})")
            continue
        url = r.get("url") if isinstance(r.get("url"), str) else None
        arrivals.append((corpus, r["seq"], rid, url, sha, new))
        n["landed" if new else "held"] += 1
    return arrivals, catches, drift, n


def pull(conn, client, corpus: str, schema: str = SCHEMA, limit: int = PAGE, pause_s: float = PAUSE_S,
         budget_s: float = None, max_pages: int = None, root: str = None, land=None, shape=None, log=None,
         sleep=time.sleep, rewalk: bool = False) -> dict:
    """Take `corpus` from its stored cursor to the end the MCP serves (or
    the budget). Returns the counts; ShapeError or McpError leaves the
    cursor at the last page landed.

    `rewalk`: walk again from 0 up to the stored cursor without moving it.
    The MCP may change a record in place (its `updated_at` moves), where a
    cursor never looks; a re-walk lands each changed record as a second
    document (an arrival row at the same `seq` with the new hash) and
    finds the rest already held."""
    t = Tables(conn, schema)
    shape = shape if shape is not None else shapes().get(corpus)
    stop = t.cursor_of(corpus) if rewalk else None
    cursor = start = t.rewalk_at(corpus) if rewalk else t.cursor_of(corpus)       # a re-walk resumes where it stopped
    t0 = time.monotonic()
    out = {"corpus": corpus, "from": start, "pages": 0, "landed": 0, "held": 0, "caught": 0, "drift": 0,
           "total": None, "stopped": "end", "rewalk": rewalk}
    while True:
        if max_pages is not None and out["pages"] >= max_pages:
            out["stopped"] = "page limit"
            break
        if budget_s is not None and time.monotonic() - t0 > budget_s:
            out["stopped"] = "budget"
            break
        if stop is not None and cursor >= stop:
            break
        page = client.call_retrying("records", {"corpus": corpus, "cursor": cursor,
                                                "limit": limit if stop is None else min(limit, stop - cursor),
                                                "include_text": True}, sleep=sleep, log=log)
        recs = check_page(page, corpus, cursor)
        out["total"] = page.get("total")
        if not recs:
            break
        arrivals, catches, drift, n = _land_page(conn, corpus, recs, shape, root, land, log)
        cursor += len(recs)
        t.commit_page(corpus, cursor, page.get("total"), arrivals, catches, drift, move=not rewalk)
        if rewalk:
            t.set_rewalk_at(corpus, cursor)
        out["pages"] += 1
        out["drift"] += sum(k for _, k in drift.values())
        for k, v in n.items():
            out[k] += v
        if page.get("total") is not None and cursor >= page["total"]:
            break
        if pause_s:
            sleep(pause_s)
    if rewalk and out["stopped"] == "end":
        t.set_rewalk_at(corpus, None)                    # walked to the end: the next re-walk starts from 0
    if rewalk and out["total"] is not None and stop is not None and out["total"] < stop and out["stopped"] == "end":
        # the MCP removed records: every one it still serves was walked and landed or found held, so the cursor
        # comes back to its count and the next arrivals are taken from there
        t.commit_page(corpus, out["total"], out["total"], [], [], {}, move=True)
        out["cursor reset"] = f"{stop} to {out['total']}"
        cursor = out["total"]
    out["to"] = cursor
    return out


def check_changes_page(page, corpus: str, cursor: int) -> list:
    """A `changes` page: `records` and `next_cursor` from where it was
    asked; its records come in (updated_at, seq) order, each with its own
    `seq` and `updated_at`."""
    if not isinstance(page, dict) or not isinstance(page.get("records"), list) or "next_cursor" not in page:
        raise ShapeError(f"{corpus}: the change page at {cursor} is not the MCP's shape: "
                         f"{sorted(page) if isinstance(page, dict) else type(page).__name__}")
    recs = page["records"]
    if page["next_cursor"] != cursor + len(recs):
        raise ShapeError(f"{corpus}: {len(recs)} changes from {cursor} but next_cursor {page['next_cursor']}")
    for r in recs:
        if not isinstance(r, dict) or not isinstance(r.get("seq"), int) or not isinstance(r.get("updated_at"), str):
            raise ShapeError(f"{corpus}: a change without its seq and updated_at")
    return recs


def _earlier(stamp: str, seconds: int = 0) -> str:
    """`stamp`, or a moment earlier. Asked strictly after the newest stamp
    seen (0 s): on 27 October 203,464 diary records shared one second, and a
    margin re-served them all every night. A record changed later in that
    same second is the weekly re-walk's."""
    if not seconds:
        return stamp
    try:
        t = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return stamp
    return (t - dt.timedelta(seconds=seconds)).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def follow_changes(conn, client, corpus: str, schema: str = SCHEMA, limit: int = PAGE, pause_s: float = PAUSE_S,
                   root: str = None, land=None, shape=None, log=None, sleep=time.sleep, budget_s: float = None) -> dict:
    """The MCP's change feed for `corpus` from the stamp followed last: each
    record it serves lands (bytes it changed are a second document under
    the same names; the rest are found held) with an arrival row at its
    own `seq`. Only records already taken by the cursor (`seq` below it) are
    counted as changes; a fresh arrival is left to the cursor."""
    t = Tables(conn, schema)
    shape = shape if shape is not None else shapes().get(corpus)
    since, upto = t.changes_since(corpus), t.cursor_of(corpus)
    out = {"since": since, "changes": 0, "changed": 0, "unchanged": 0, "caught": 0, "drift": 0, "pages": 0}
    if since is None:
        out["stopped"] = "nothing taken yet"
        return out
    newest, cursor, t0 = since, 0, time.monotonic()
    while True:
        if budget_s is not None and time.monotonic() - t0 > budget_s:
            out["stopped"] = "budget"
            break
        page = client.call_retrying("changes", {"corpus": corpus, "since": _earlier(since), "cursor": cursor,
                                                "limit": limit, "include_text": True}, sleep=sleep, log=log)
        recs = check_changes_page(page, corpus, cursor)
        if not recs:
            out["stopped"] = "end"
            break
        cursor += len(recs)
        taken = [r for r in recs if r["seq"] < upto]
        newest = max([newest] + [r["updated_at"] for r in recs])
        arrivals, catches, drift, n = _land_page(conn, corpus, taken, shape, root, land, log)
        t.commit_page(corpus, upto, page.get("total"), arrivals, catches, drift, move=False)
        out["pages"] += 1
        out["changes"] += len(taken)
        out["changed"] += n["landed"]
        out["unchanged"] += n["held"]
        out["caught"] += n["caught"]
        out["drift"] += sum(k for _, k in drift.values())
        if pause_s:
            sleep(pause_s)
    if out.get("stopped") == "end" and not out["caught"]:
        t.set_changes_since(corpus, newest)     # moved only when the feed was read to its end and every change landed
    out["to"] = newest
    return out


def retry_caught(conn, client, schema: str = SCHEMA, root: str = None, land=None, log=None, sleep=time.sleep) -> dict:
    """Each unresolved catch line asked for again by its place (one record a request) and landed; resolved when it lands."""
    t = Tables(conn, schema)
    rows = conn.execute(f"SELECT corpus, seq FROM {t.t('catch')} WHERE resolved_at IS NULL ORDER BY corpus, seq").fetchall()
    n = {"asked": 0, "landed": 0}
    for corpus, seq in rows:
        page = client.call_retrying("records", {"corpus": corpus, "cursor": seq, "limit": 1, "include_text": True},
                                    sleep=sleep, log=log)
        recs = check_page(page, corpus, seq)[:1]
        n["asked"] += 1
        if not recs:
            continue
        arrivals, catches, drift, k = _land_page(conn, corpus, recs, shapes().get(corpus), root, land, log)
        if arrivals:
            with conn.transaction():
                conn.execute(f"INSERT INTO {t.t('arrivals')} (corpus, seq, record_id, url, sha256, new) "
                             "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (corpus, seq, sha256) DO NOTHING", arrivals[0])
                conn.execute(f"UPDATE {t.t('catch')} SET resolved_at = now() WHERE corpus = %s AND seq = %s", (corpus, seq))
            n["landed"] += 1
    return n


def pull_all(conn, client, schema: str = SCHEMA, only=None, log=None, follow: bool = True, **kw) -> dict:
    """Every corpus `corpora` names (or `only`), each from its cursor, then
    (with `follow`) each one's change feed from the stamp followed last:
    {corpus: counts}. A corpus that fails is recorded with its error and
    the others still run."""
    listing = client.call_retrying("corpora", {}, log=log, sleep=kw.get("sleep", time.sleep))
    corpora = listing.get("corpora") if isinstance(listing, dict) else None
    if not isinstance(corpora, list) or not all(isinstance(c, dict) and "name" in c for c in corpora):
        raise ShapeError(f"`corpora` is not the MCP's shape: {type(listing).__name__}")
    held = Tables(conn, schema).cursors()
    res = {}
    for c in corpora:
        name = c["name"]
        if only and name not in only:
            continue
        want = c.get("ingest_cursor", c.get("records"))
        if want is not None and held.get(name, 0) > want and not kw.get("rewalk"):
            # the MCP counts fewer records than we have taken: it removed some, every later place moved, and a
            # cursor would pass over the next arrivals. Red until a re-walk (`--rewalk`) has reconciled it
            res[name] = {"corpus": name, "error": f"the MCP counts {want} records, fewer than the {held[name]} taken: "
                         "it removed records and the places after them moved; run --rewalk"}
            res[name]["source_cursor"] = want
            continue
        if not kw.get("rewalk") and want is not None and held.get(name, 0) >= want:
            res[name] = {"corpus": name, "from": held.get(name, 0), "to": held.get(name, 0), "pages": 0, "landed": 0,
                         "held": 0, "caught": 0, "drift": 0, "total": want, "stopped": "nothing new"}
            continue
        try:
            res[name] = pull(conn, client, name, schema, log=log, **kw)
        except (McpError, ShapeError) as e:
            res[name] = {"corpus": name, "error": f"{type(e).__name__}: {e}"[:500]}
        res[name]["source_cursor"] = want
    if follow and not kw.get("rewalk"):
        for name in [c["name"] for c in corpora if (not only or c["name"] in only)]:
            if "error" in res.get(name, {}):
                continue
            try:
                ch = follow_changes(conn, client, name, schema, log=log,
                                    **{k: v for k, v in kw.items() if k in ("sleep", "pause_s", "land", "root", "budget_s")})
            except (McpError, ShapeError) as e:
                res[name]["error"] = f"changes: {type(e).__name__}: {e}"[:500]
                continue
            res[name]["changes"] = ch
            res[name]["caught"] += ch["caught"]
            res[name]["drift"] += ch["drift"]
    return res


# ── the integrator, once: a session's proven pull carried into the live database ─────────────

ADOPT_TABLES = ("cursors", "arrivals", "catch", "drift")
ADOPT_BATCH = 20_000


def _by_corpus(conn, table: str) -> dict:
    return {r[0]: r[1] for r in conn.execute(f"SELECT corpus, count(*) FROM {table} GROUP BY corpus")}


def _copy_table(src, dst, src_table: str, dst_table: str) -> int:
    """The rows of `src_table` that `dst_table` lacks (by its key), streamed
    from one database to the other through a COPY each way, in one
    transaction on `dst`: rows the next statement adds or nothing."""
    cols = [r[0] for r in dst.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = %s "
                                      "AND table_name = %s ORDER BY ordinal_position", tuple(dst_table.split(".")))]
    cl = ", ".join(cols)
    with dst.transaction():
        dst.execute(f"CREATE TEMP TABLE _adopt (LIKE {dst_table} INCLUDING DEFAULTS) ON COMMIT DROP")
        with src.cursor() as rc, dst.cursor() as wc:
            with rc.copy(f"COPY (SELECT {cl} FROM {src_table}) TO STDOUT") as out, \
                    wc.copy(f"COPY _adopt ({cl}) FROM STDIN") as into:
                for block in out:
                    into.write(block)
            wc.execute(f"INSERT INTO {dst_table} ({cl}) SELECT {cl} FROM _adopt ON CONFLICT DO NOTHING")
            return wc.rowcount


def adopt(src, dst, src_schema: str, dst_schema: str = SCHEMA, log=print, batch: int = ADOPT_BATCH, root: str = None,
          src_store: str = "docs", dst_store: str = "docs", copy=None) -> dict:
    """Carry a session's pull record (its schema in the sample database)
    into `dst_schema` on `dst`, and the store rows of its documents into
    the store tables on `dst` (the bytes are already in the one store on
    disk; no request to the MCP). Resumable and idempotent: a table is
    copied only where the live one holds fewer rows than the source (rows
    it holds are kept), and documents are copied in batches of `batch`
    hashes, those the live store holds skipped; a rerun after a kill
    finishes the rest. Ends with a count per table and per corpus, source
    against live: `ok` is false where any differs, a document has no bytes
    on disk, or the source store lacks its row."""
    if copy is None:
        from support.docstore.landing import copy_documents as copy
    t = Tables(dst, dst_schema)
    t.create()
    if not t.try_lock():
        raise RuntimeError(f"{dst_schema}: a pull or another adopt holds the record; nothing adopted")
    try:
        t0 = time.monotonic()
        out = {"tables": {}, "documents": {}, "red": []}
        for x in ADOPT_TABLES:
            n_src = src.execute(f"SELECT count(*) FROM {src_schema}.{x}").fetchone()[0]
            n_dst = dst.execute(f"SELECT count(*) FROM {t.t(x)}").fetchone()[0]
            added = _copy_table(src, dst, f"{src_schema}.{x}", t.t(x)) if n_dst < n_src else 0
            out["tables"][x] = {"source": n_src, "live before": n_dst, "added": added}
            log(f"mcpsource: adopt {x}: {n_src} in the source, {n_dst} live before, {added} added "
                f"({time.monotonic() - t0:.0f} s)")
        docs = {"asked": 0, "copied": 0, "held": 0, "no source row": 0, "no bytes": 0, "names": 0, "names copied": 0,
                "names live": 0}
        per = {}                                       # corpus: [documents in the source, held live after]
        after, last = "", time.monotonic()
        while True:
            rows = src.execute(f"SELECT sha256, array_agg(DISTINCT corpus) FROM {src_schema}.arrivals WHERE sha256 > %s "
                               "GROUP BY sha256 ORDER BY sha256 LIMIT %s", (after, batch)).fetchall()
            if not rows:
                break
            n = copy(src, dst, [r[0] for r in rows], root=root, src_store=src_store, dst_store=dst_store)
            absent = set(n["absent"])
            for sha, corpora in rows:
                for c in corpora:
                    k = per.setdefault(c, [0, 0])
                    k[0] += 1
                    k[1] += sha not in absent
            for f in docs:
                docs[f] += n[f]
            after = rows[-1][0]
            if time.monotonic() - last > 60:
                last = time.monotonic()
                log(f"mcpsource: adopt documents: {docs['asked']} hashes, {docs['copied']} copied, {docs['held']} held "
                    f"({docs['asked'] / max(last - t0, 1):.0f} a second)")
        out["documents"] = docs
        out["per corpus"] = per
        for x in ADOPT_TABLES:
            s, d = _by_corpus(src, f"{src_schema}.{x}"), _by_corpus(dst, t.t(x))
            for c in sorted(set(s) | set(d)):
                if s.get(c, 0) != d.get(c, 0):
                    out["red"].append(f"{x} {c}: {s.get(c, 0)} in the source, {d.get(c, 0)} live")
        for c, (s, d) in sorted(per.items()):
            if s != d:
                out["red"].append(f"documents {c}: {s} in the source, {d} live")
        for f in ("no source row", "no bytes"):
            if docs[f]:
                out["red"].append(f"documents: {docs[f]} with {f}")
        if docs["names live"] != docs["names"]:
            out["red"].append(f"names: {docs['names']} in the source, {docs['names live']} live")
        out["seconds"] = round(time.monotonic() - t0, 1)
        out["ok"] = not out["red"]
        log(f"mcpsource: adopt documents: {docs['asked']} hashes, {docs['copied']} copied, {docs['held']} already held, "
            f"{docs['names copied']} names copied, in {out['seconds']} s")
        for line in out["red"]:
            log(f"mcpsource: adopt RED: {line}")
        return out
    finally:
        t.unlock()


def summary(res: dict) -> str:
    parts = []
    for name, r in sorted(res.items()):
        if "error" in r:
            parts.append(f"{name}: FAILED {r['error'][:160]}")
        else:
            ch = r.get("changes") or {}
            parts.append(f"{name}: {r['from']}→{r['to']} of {r.get('source_cursor', r.get('total'))}, "
                         f"{r['landed']} landed, {r['held']} held, {r['caught']} caught, {r['drift']} drift ({r['stopped']})"
                         + (f"; changes since {ch['since']}: {ch['changed']} changed, {ch['unchanged']} unchanged "
                            f"({ch.get('stopped')})" if ch else ""))
    return "; ".join(parts)


def outcome(res: dict) -> bool:
    """Green when every corpus answered and reached the MCP's cursor with
    nothing caught and no field new to us."""
    for r in res.values():
        if "error" in r or r["caught"] or r["drift"]:
            return False
        if (not r.get("rewalk") and r.get("source_cursor") is not None and r["to"] < r["source_cursor"]
                and r["stopped"] == "end"):
            return False
    return True
