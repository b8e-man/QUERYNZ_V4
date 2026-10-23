"""The restore rehearsal (track B): the newest off-site copy brought back
into a scratch database server on /mnt/hdd2 and checked to equality, every
step timed.

Equality is exact, not "90% of the primary", and holds two ways. On the
way in, every object's text has the sha256 the copy recorded as it left the
source, so the loaded rows are the source's rows. On the way out, the table
read back with the same `COPY ... TO STDOUT` holds the same rows: the same
count and the same order-free sum of each row's hash (a multiset hash).
Order cannot be compared: a table loaded by COPY does not read back in load
order (PostgreSQL 18's bulk insert, measured 19 October). Every file of
every tree gives its recorded sha256.

The order of a restore: the schema before data (pg_restore
--section=pre-data), every table's rows, the sequences (a value the copy
could read, else an owned sequence set from its column's maximum), then the
schema after data (indexes, constraints; pg_restore --section=post-data in
parallel), then the trees.

Each database is created as its source was: the encoding, locale provider,
collation and ctype the copy recorded from pg_database (a CHECK or an
index on text holds only under the collation it was validated with; under
"C" three links.links rows broke `row_a < row_b`, 22 October). A copy
made before the manifest carried them takes the live server's settings,
read at restore time, and the record says which was used. The scratch
server's initdb takes the first database's.

The scratch server is our own: initdb under the work folder, socket only
(no TCP), port 5434, run as a transient user unit so it outlives a caller
started by systemd-run. Its tuning is a bulk load's (no fsync, minimal WAL),
which a real restore would use too. It never touches the server on 5432.
The restored copy holds what the registers hold, home addresses included,
so it is removed after the rehearsal unless --keep.

Keys: the bucket through the old estate's read-only off-site key
(`offsite-read.env`: Get and List only), the passphrase from the push file
(`offsite.env`), each read at the moment of use and never printed.

    python -m support.offsite restore                       from the bucket
    python -m support.offsite restore --source local        from /mnt/hdd2/qv4-offsite
    python -m support.offsite restore --databases querynz_v4 --trees qv4-inbox
    python -m support.offsite restore --keep                leave the server running

Record: `<live>/checks/offsite-restore-last.json`."""
import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time

from support import db
from support.offsite import read_env, ENV_FILE, LIVE
from support.offsite import copy as C
from support.offsite import pieces as P

ROOT = os.environ.get("QV4_RESTORE_ROOT") or "/mnt/hdd2/qv4-restore"
PORT = 5434
UNIT = "qv4-restore-scratch"
READ_ENV = os.path.join(db.CRED_DIR, "offsite-read.env")
RECORD = os.path.join(LIVE, "checks", "offsite-restore-last.json")
SERVER_SETTINGS = ("listen_addresses=", "fsync=off", "synchronous_commit=off", "full_page_writes=off",
                   "wal_level=minimal", "max_wal_senders=0", "shared_buffers=2GB", "maintenance_work_mem=1GB",
                   "max_parallel_maintenance_workers=2", "checkpoint_timeout=30min", "max_wal_size=16GB",
                   "autovacuum=off")
# initdb's settings when the rehearsal restores no database (trees only)
SERVER_LOCALE = {"encoding": "UTF8", "provider": "libc", "collate": "C.UTF-8", "ctype": "C.UTF-8",
                 "locale": None, "icu_rules": None, "from": "default"}


class Source:
    """Where the objects come from: `fetch(stamp, name)` gives a local path."""

    def __init__(self, kind: str, work: str, spool: str = None, client=None, bucket: str = None):
        self.kind, self.work, self.spool = kind, work, spool or C.SPOOL
        self.client, self.bucket = client, bucket
        self.fetched_bytes, self.fetch_s = 0, 0.0

    @classmethod
    def bucket_source(cls, work: str):
        import boto3
        env = read_env(READ_ENV)
        client = boto3.client("s3", region_name=env.get("OFFSITE_REGION", "ap-southeast-2"),
                              aws_access_key_id=env["OFFSITE_READ_ACCESS_KEY_ID"],
                              aws_secret_access_key=env["OFFSITE_READ_SECRET_ACCESS_KEY"])
        return cls("bucket", work, client=client, bucket=env.get("OFFSITE_BUCKET", "querynz-offsite"))

    def newest_stamp(self) -> str:
        if self.kind == "local":
            return C.load_json(os.path.join(self.spool, "manifest.json"))["stamp"]
        stamps, token = [], None
        while True:
            kw = {"Bucket": self.bucket, "Prefix": C.PREFIX + "/"}
            if token:
                kw["ContinuationToken"] = token
            page = self.client.list_objects_v2(**kw)
            stamps += [o["Key"].split("/")[1] for o in page.get("Contents", [])
                       if o["Key"].endswith("/manifest.json.gpg")]
            if not page.get("IsTruncated"):
                break
            token = page["NextContinuationToken"]
        if not stamps:
            raise RuntimeError("no complete copy in the bucket")
        return max(stamps)

    def prefetch(self, wanted: list) -> None:
        """Download `wanted` [(stamp, name)] in order on a thread, so the
        link and the load overlap; `fetch` then waits for its object."""
        import threading
        if self.kind == "local":
            return
        self._lock = getattr(self, "_lock", None) or threading.Lock()

        def run():
            for stamp, name in wanted:
                try:
                    self.fetch(stamp, name)
                except Exception:  # noqa: BLE001 — fetch() retries in the caller and raises there
                    return
        threading.Thread(target=run, daemon=True).start()

    def fetch(self, stamp: str, name: str) -> str:
        if self.kind == "local":
            return os.path.join(self.spool, "objects", stamp, name)
        path = os.path.join(self.work, "objects", stamp, name)
        lock = getattr(self, "_lock", None)
        if lock is None or os.path.exists(path):
            return self._download(stamp, name, path)
        with lock:          # one download at a time; the loader waits its turn
            return self._download(stamp, name, path)

    def _download(self, stamp: str, name: str, path: str) -> str:
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            t0 = time.monotonic()
            self.client.download_file(self.bucket, f"{C.PREFIX}/{stamp}/{name}", path + ".part")
            os.replace(path + ".part", path)
            self.fetch_s += time.monotonic() - t0
            self.fetched_bytes += os.path.getsize(path)
        return path


def objects_needed(man: dict, databases=None, trees=None) -> list:
    """Every object a restore of `man` reads, in the order it reads them."""
    out = []
    for database in (sorted(man["databases"]) if databases is None else databases):
        dbm = man["databases"][database]
        out.append((dbm["stamp"], dbm["schema"]))
        for piece, v in sorted(man["pieces"].items()):
            if piece.startswith(database + ":") and v["fate"] == "send":
                out += [(seg["stamp"], seg["object"]) for seg in segments(v)]
    for tree in (sorted(man["trees"]) if trees is None else trees):
        name = C.object_name(f"tree:{tree}") + ".tar.zst.gpg"
        out += [(st, name) for st in sorted({f[3] for f in man["trees"][tree]["files"].values()})]
    return out


def read_manifest(src: Source, stamp: str, passphrase: str) -> dict:
    gpg, zstd = C.opened(src.fetch(stamp, "manifest.json.gpg"), passphrase)
    data = zstd.stdout.read()
    zstd.wait()
    gpg.wait()
    return json.loads(data)


# ── locales ─────────────────────────────────────────────────────────────

def live_locale(database: str) -> dict:
    """The live server's settings for `database`, read now, through the
    login the copy reads it with."""
    login = P.DATABASES.get(database, {}).get("login", db.OWNER_KEY)
    with db.connect(login, database) as conn:
        return C.database_locale(conn.cursor())


def database_locales(man: dict, databases, live=live_locale) -> dict:
    """{database: its locale, with "from": "manifest" or "live server"}."""
    out = {}
    for database in databases:
        recorded = man["databases"][database].get("locale")
        out[database] = (dict(recorded, **{"from": "manifest"}) if recorded
                         else dict(live(database), **{"from": "live server"}))
    return out


def literal(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def initdb_locale_args(loc: dict) -> list:
    args = ["-E", loc["encoding"], f"--locale-provider={loc['provider']}", f"--locale={loc['collate']}",
            f"--lc-collate={loc['collate']}", f"--lc-ctype={loc['ctype']}"]
    if loc["provider"] == "icu":
        args.append(f"--icu-locale={loc['locale']}")
        if loc.get("icu_rules"):
            args.append(f"--icu-rules={loc['icu_rules']}")
    elif loc["provider"] == "builtin":
        args.append(f"--builtin-locale={loc['locale']}")
    return args


def create_database_sql(database: str, loc: dict) -> str:
    if loc["provider"] not in C.PROVIDERS.values():
        raise ValueError(f"{database}: unknown locale provider")
    sql = (f"CREATE DATABASE {C.qident(database)} TEMPLATE template0 ENCODING {literal(loc['encoding'])} "
           f"LOCALE_PROVIDER {loc['provider']} LC_COLLATE {literal(loc['collate'])} LC_CTYPE {literal(loc['ctype'])}")
    if loc["provider"] == "icu":
        sql += f" ICU_LOCALE {literal(loc['locale'])}"
        if loc.get("icu_rules"):
            sql += f" ICU_RULES {literal(loc['icu_rules'])}"
    elif loc["provider"] == "builtin":
        sql += f" BUILTIN_LOCALE {literal(loc['locale'])}"
    return sql


def create_database(root: str, database: str, loc: dict, connect=None) -> None:
    import psycopg
    with (connect or psycopg.connect)(conninfo(root, "postgres"), autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {C.qident(database)}")
        c.execute(create_database_sql(database, loc))


# ── the scratch server ──────────────────────────────────────────────────

def socket_dir(root: str) -> str:
    return os.path.join(root, "sock")


def start_server(root: str, locale: dict, port: int = PORT, run=subprocess.run) -> None:
    pgdata, sock = os.path.join(root, "pgdata"), socket_dir(root)
    os.makedirs(sock, mode=0o700, exist_ok=True)
    if not os.path.exists(os.path.join(pgdata, "PG_VERSION")):
        r = run(["initdb", "-D", pgdata, "-A", "trust", *initdb_locale_args(locale), "-U", "restore"],
                capture_output=True)
        if r.returncode:
            raise RuntimeError(f"initdb: {r.stderr.decode(errors='replace')[-300:]}")
    if run(["pg_isready", "-q", "-h", sock, "-p", str(port)]).returncode == 0:
        return
    cmd = ["systemd-run", "--user", "--unit", UNIT, "--collect", "--quiet", "/usr/bin/postgres", "-D", pgdata,
           "-k", sock, "-p", str(port)]
    for s in SERVER_SETTINGS:
        cmd += ["-c", s]
    r = run(cmd, capture_output=True)
    if r.returncode:
        raise RuntimeError(f"scratch server did not start: {r.stderr.decode(errors='replace')[-300:]}")
    for _ in range(60):
        if run(["pg_isready", "-q", "-h", sock, "-p", str(port)]).returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("scratch server not ready after 60 s")


def stop_server(run=subprocess.run) -> None:
    run(["systemctl", "--user", "stop", UNIT], capture_output=True)


def conninfo(root: str, database: str, port: int = PORT) -> str:
    return f"host={socket_dir(root)} port={port} user=restore dbname={database}"


def scratch_env(root: str, database: str, port: int = PORT) -> dict:
    env = dict(os.environ)
    env.update({"PGHOST": socket_dir(root), "PGPORT": str(port), "PGUSER": "restore", "PGDATABASE": database})
    env.pop("PGPASSWORD", None)
    env.pop("PGOPTIONS", None)
    return env


# ── one database ────────────────────────────────────────────────────────

def pg_restore_section(dump: str, section: str, root: str, database: str, jobs: int = 1, run=subprocess.run):
    r = run(["pg_restore", f"--section={section}", "--no-owner", "--no-privileges", "--exit-on-error",
             "-j", str(jobs), "-d", database, dump], env=scratch_env(root, database), capture_output=True)
    if r.returncode:
        raise RuntimeError(f"pg_restore {section} {database}: {r.stderr.decode(errors='replace')[-400:]}")


def restore_database(database: str, man: dict, src: Source, passphrase: str, root: str, jobs: int, locale: dict,
                     log=print) -> dict:
    import psycopg
    rec = {"tables": 0, "rows": 0, "plain_bytes": 0, "in_bad": [], "out_bad": [], "skipped": [], "seconds": {},
           "locale": locale}
    dbm = man["databases"][database]
    t = time.monotonic()
    work_plain = os.path.join(root, "work", f"{database}-schema.dump")
    os.makedirs(os.path.dirname(work_plain), exist_ok=True)
    gpg, zstd = C.opened(src.fetch(dbm["stamp"], dbm["schema"]), passphrase)
    with open(work_plain, "wb") as f:
        shutil.copyfileobj(zstd.stdout, f)
    if zstd.wait() or gpg.wait():
        raise RuntimeError(f"{database}: schema object does not open")
    create_database(root, database, locale)
    pg_restore_section(work_plain, "pre-data", root, database)
    rec["seconds"]["schema_before"] = round(time.monotonic() - t, 1)

    t = time.monotonic()
    mine = {p: v for p, v in man["pieces"].items() if p.startswith(database + ":")}
    loaded = {}
    with psycopg.connect(conninfo(root, database), autocommit=True) as conn:
        for piece, v in sorted(mine.items()):
            if v["fate"] == "out":
                continue
            if v["fate"] == "local" and src.kind != "local":
                rec["skipped"].append(f"{piece}: kept on the box only, not in the bucket")
                continue
            schema, table = piece.split(":", 1)[1].split(".", 1)
            if v.get("plain_bytes", 0) > 100e6:
                log(f"    {piece}: {v['plain_bytes'] / 1e6:,.0f} MB")
            rows_in = Multiset()
            with conn.cursor().copy(f"COPY {C.qident(schema)}.{C.qident(table)} FROM STDIN") as cp:
                for seg in segments(v):          # a big table's ranges
                    gpg, zstd = C.opened(src.fetch(seg["stamp"], seg["object"]), passphrase)
                    h, rows, n = hashlib.sha256(), 0, 0
                    for chunk in iter(lambda: zstd.stdout.read(C.CHUNK), b""):
                        h.update(chunk)
                        rows += chunk.count(b"\n")
                        n += len(chunk)
                        rows_in.feed(chunk)
                        cp.write(chunk)
                    if zstd.wait() or gpg.wait():
                        raise RuntimeError(f"{piece}: object does not open")
                    if h.hexdigest() != seg["sha256"] or rows != seg["rows"]:
                        rec["in_bad"].append(piece)
                    rec["rows"] += rows
                    rec["plain_bytes"] += n
            loaded[piece] = (schema, table, rows_in.digest())
            rec["tables"] += 1
    rec["seconds"]["rows_in"] = round(time.monotonic() - t, 1)

    t = time.monotonic()
    set_sequences(root, database, dbm.get("sequences") or {})
    rec["seconds"]["sequences"] = round(time.monotonic() - t, 1)
    t = time.monotonic()
    pg_restore_section(work_plain, "post-data", root, database, jobs=jobs)
    os.remove(work_plain)
    rec["seconds"]["schema_after"] = round(time.monotonic() - t, 1)

    t = time.monotonic()
    with psycopg.connect(conninfo(root, database)) as conn:
        cur = conn.cursor()
        for stmt in C.SESSION_SQL.split("; "):
            cur.execute(stmt)
        for piece, (schema, table, want) in sorted(loaded.items()):
            back = Multiset()
            with cur.copy(f"COPY {C.qident(schema)}.{C.qident(table)} TO STDOUT") as cp:
                for chunk in cp:
                    back.feed(bytes(chunk))
            if back.digest() != want or want[1] != mine[piece]["rows"]:
                rec["out_bad"].append(piece)
    rec["seconds"]["check"] = round(time.monotonic() - t, 1)
    rec["equal"] = rec["tables"] - len(set(rec["in_bad"]) | set(rec["out_bad"]))
    log(f"  {database}: {rec['tables']} tables, {rec['rows']:,} rows, {rec['equal']} equal; {rec['seconds']}")
    return rec


def segments(entry: dict) -> list:
    """The objects that hold one table: its page ranges, or itself."""
    return entry.get("chunks") or [entry]


class Multiset:
    """An order-free hash of a table's text: the number of rows and the sum,
    modulo 2**128, of each row's 128-bit BLAKE2b. Two tables with the same
    rows in any order give the same digest."""

    def __init__(self):
        self.acc, self.rows, self.tail = 0, 0, b""

    def feed(self, b: bytes) -> None:
        lines = (self.tail + b).split(b"\n")
        self.tail = lines.pop()
        self.rows += len(lines)
        h = hashlib.blake2b
        self.acc += sum(int.from_bytes(h(ln, digest_size=16).digest(), "little") for ln in lines)

    def digest(self) -> tuple:
        if self.tail:
            raise ValueError("a table's text ends mid-row")
        return f"{self.acc % (1 << 128):032x}", self.rows


OWNED_SEQUENCES_SQL = """
SELECT sn.nspname, s.relname, tn.nspname, t.relname, a.attname
  FROM pg_class s JOIN pg_namespace sn ON sn.oid = s.relnamespace
  JOIN pg_depend d ON d.objid = s.oid AND d.classid = 'pg_class'::regclass AND d.deptype IN ('a', 'i')
  JOIN pg_class t ON t.oid = d.refobjid JOIN pg_namespace tn ON tn.oid = t.relnamespace
  JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
 WHERE s.relkind = 'S'"""


def set_sequences(root: str, database: str, recorded: dict) -> None:
    import psycopg
    q = C.qident
    with psycopg.connect(conninfo(root, database), autocommit=True) as conn:
        owned = {f"{sn}.{s}": (tn, t, a) for sn, s, tn, t, a in conn.execute(OWNED_SEQUENCES_SQL).fetchall()}
        for name, val in recorded.items():
            schema, seq = name.split(".", 1)
            if val is not None:
                conn.execute(f"SELECT setval('{q(schema)}.{q(seq)}', %s, %s)", val)
            elif name in owned:
                tn, t, a = owned[name]
                conn.execute(f"SELECT setval('{q(schema)}.{q(seq)}', coalesce(max({q(a)}), 1), max({q(a)}) IS NOT NULL) "
                             f"FROM {q(tn)}.{q(t)}")


# ── one tree ────────────────────────────────────────────────────────────

def restore_tree(tree: str, tm: dict, src: Source, passphrase: str, root: str, log=print) -> dict:
    t = time.monotonic()
    dest = os.path.join(root, "trees", tree)
    want = tm["files"]
    by_stamp = {}
    for rel, (_size, _mtime, _sha, stamp) in want.items():
        by_stamp.setdefault(stamp, set()).add(rel)
    got, bad = {}, []
    for stamp, rels in sorted(by_stamp.items()):
        name = C.object_name(f"tree:{tree}") + ".tar.zst.gpg"
        gpg, zstd = C.opened(src.fetch(stamp, name), passphrase)
        with tarfile.open(fileobj=zstd.stdout, mode="r|") as tar:
            for m in tar:
                if m.name not in rels or not m.isfile():
                    continue
                out = os.path.join(dest, m.name)
                if not os.path.realpath(out).startswith(os.path.realpath(dest) + os.sep):
                    bad.append(m.name)
                    continue
                os.makedirs(os.path.dirname(out), exist_ok=True)
                h = hashlib.sha256()
                with tar.extractfile(m) as f, open(out, "wb") as o:
                    for chunk in iter(lambda: f.read(C.CHUNK), b""):
                        h.update(chunk)
                        o.write(chunk)
                got[m.name] = h.hexdigest()
        zstd.wait()
        gpg.wait()
    for rel, (_size, _mtime, sha, _stamp) in want.items():
        if got.get(rel) != sha:
            bad.append(rel)
    rec = {"files": len(want), "equal": len(want) - len(set(bad)), "bad": len(set(bad)),
           "seconds": round(time.monotonic() - t, 1)}
    log(f"  tree {tree}: {rec['files']:,} files, {rec['equal']:,} equal, {rec['seconds']} s")
    return rec


# ── the rehearsal ───────────────────────────────────────────────────────

def rehearse(source: str = "bucket", databases=None, trees=None, keep: bool = False, root: str = None,
             jobs: int = 4, stamp: str = None, spool: str = None, log=print, live=live_locale,
             run=subprocess.run) -> dict:
    root = root or ROOT
    started = time.monotonic()
    work = os.path.join(root, "work")
    os.makedirs(work, exist_ok=True)
    src = Source.bucket_source(work) if source == "bucket" else Source("local", work, spool=spool)
    passphrase = read_env(ENV_FILE)["OFFSITE_PASSPHRASE"]
    stamp = stamp or src.newest_stamp()
    man = read_manifest(src, stamp, passphrase)
    src.prefetch(objects_needed(man, databases, trees))
    log(f"restore rehearsal from the {source}: copy {stamp} ({man['kind']})")
    rec = {"stamp": stamp, "kind": man["kind"], "source": source,
           "started": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "databases": {}, "trees": {}}
    wanted = list(man["databases"]) if databases is None else databases
    failed = False
    try:
        locales = database_locales(man, wanted, live)    # a live read that fails is recorded like any failure
        rec["server_locale"] = locales[wanted[0]] if wanted else SERVER_LOCALE
        t = time.monotonic()
        start_server(root, rec["server_locale"], run=run)
        rec["server_s"] = round(time.monotonic() - t, 1)
        for database in wanted:
            loc = locales[database]
            log(f"  {database}: {loc['collate']} ({loc['provider']}), from the {loc['from']}")
            rec["databases"][database] = restore_database(database, man, src, passphrase, root, jobs, loc, log)
        for tree in (list(man["trees"]) if trees is None else trees):
            rec["trees"][tree] = restore_tree(tree, man["trees"][tree], src, passphrase, root, log)
    except Exception as exc:
        failed = True
        rec["why"] = f"{type(exc).__name__}: {exc}"[:500]
        raise
    finally:
        rec["seconds"] = round(time.monotonic() - started, 1)
        rec["fetched_bytes"], rec["fetch_s"] = src.fetched_bytes, round(src.fetch_s, 1)
        dbs, trs = rec["databases"].values(), rec["trees"].values()
        rec["equal"] = not failed and (bool(dbs) or bool(trs)) and all(
            d["equal"] == d["tables"] for d in dbs) and all(t["bad"] == 0 for t in trs)
        rec["finished"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        C.write_json(RECORD, rec)
        if not keep and not failed:     # a failed rehearsal keeps its server, log and downloads for the next look
            stop_server(run=run)
            for sub in ("pgdata", "trees", "work", "sock"):
                path = os.path.join(root, sub)
                if os.path.realpath(path).startswith(os.path.realpath(root) + os.sep):
                    shutil.rmtree(path, ignore_errors=True)
    log(f"restore {'EQUAL' if rec['equal'] else 'NOT EQUAL'} in {rec['seconds']:,} s")
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="support.offsite restore")
    ap.add_argument("--source", choices=("bucket", "local"), default="bucket")
    ap.add_argument("--databases", nargs="*")
    ap.add_argument("--trees", nargs="*")
    ap.add_argument("--stamp")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--spool", help="the local copy to restore from (default the copy's own)")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args(argv)
    rec = rehearse(a.source, a.databases, a.trees, a.keep, jobs=a.jobs, stamp=a.stamp, spool=a.spool)
    return 0 if rec["equal"] else 1


if __name__ == "__main__":
    sys.exit(main())
