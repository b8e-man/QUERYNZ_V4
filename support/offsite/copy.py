"""The off-site copy (track B): changes nightly, a full checkpoint weekly
(ruling 21), one piece per table and per file tree, sorted by the delete
rule in `pieces.py`.

A table travels as its own `COPY ... TO STDOUT` text, read inside one
repeatable-read transaction per database, so every table of a database
copied the same night is from one moment. On the way out the stream is
hashed (sha256) and its rows counted, then compressed (zstd) and sealed
(gpg, AES256, the passphrase on a pipe). A restored table read back the
same way gives the same bytes in the same order (a table loaded by COPY is
scanned in load order), so equality is one hash per table, exact.

Nightly, a table is copied only if its write counters or its file node
moved since the copy the newest manifest names; a tree sends only files
whose size or time changed. Each run writes a complete manifest: for every
piece, the stamp whose object holds its current copy. A restore needs the
newest manifest and nothing else; there is no chain to replay.

The bucket and its keys come from the old estate's off-site credential file
at the moment of use and are never printed (hard limit 1). Every object is
also kept on /mnt/hdd2, so the newest manifest restores from either.

    python -m support.offsite copy            nightly, or full on Sunday
    python -m support.offsite copy --full     the weekly checkpoint now
    python -m support.offsite copy --local    seal and keep, send nothing
    python -m support.offsite plan            what tonight would copy, and sizes

A run killed part-way resumes: a run younger than RESUME_HOURS that wrote
no manifest is carried on, and its sent pieces are not sent again."""
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import time

from support import db, jobrun
from support.offsite import pieces as P
from support.offsite import read_env, s3_client, upload, ENV_FILE, LIVE

SPOOL = os.environ.get("QV4_OFFSITE_SPOOL") or "/mnt/hdd2/qv4-offsite"
PREFIX = "qv4"
RECORD = os.path.join(LIVE, "checks", "offsite-copy-last.json")
JOB = "qv4-offsite-copy"
RESUME_HOURS = 20
STATEMENT_S = 7200
CHUNK = 1 << 20
REPEATABLE_READ = 3   # psycopg.IsolationLevel.REPEATABLE_READ, without importing the driver here

# Both ends of a table's text must render values the same way.
SESSION_SQL = ("SET TimeZone = 'UTC'; SET DateStyle = 'ISO, YMD'; SET IntervalStyle = 'postgres'; "
               "SET extra_float_digits = 1; SET bytea_output = 'hex'; SET synchronize_seqscans = off; "
               "SET client_encoding = 'UTF8'")

TABLES_SQL = """
SELECT n.nspname, c.relname, c.relfilenode::text,
       coalesce(s.n_tup_ins, -1), coalesce(s.n_tup_upd, -1), coalesce(s.n_tup_del, -1),
       pg_table_size(c.oid)
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  LEFT JOIN pg_stat_all_tables s ON s.relid = c.oid
 WHERE c.relkind = 'r' AND n.nspname NOT IN ('pg_catalog', 'information_schema')
   AND n.nspname NOT LIKE 'pg\\_toast%' AND n.nspname NOT LIKE 'pg\\_temp%'
 ORDER BY 1, 2"""

# A crash throws away the write counters; a changed epoch copies the whole
# database again rather than trust a counter that restarted.
EPOCH_SQL = """SELECT coalesce(stats_reset::text, '') || '|' || pg_postmaster_start_time()::text
                 FROM pg_stat_database WHERE datname = current_database()"""

SEQUENCES_SQL = """
SELECT n.nspname, c.relname, has_sequence_privilege(c.oid, 'select')
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE c.relkind = 'S' ORDER BY 1, 2"""


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def object_name(piece: str) -> str:
    """A file and key name for a piece: `extractions:v3.claims` ->
    `extractions--v3.claims`."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", piece.replace(":", "--", 1))


def pg_env(url: str) -> dict:
    """The connection for a pg_dump child, through its environment, which
    only this user can read, never its argv."""
    from urllib.parse import unquote, urlparse
    u = urlparse(url)
    env = dict(os.environ)
    env.update({"PGHOST": u.hostname or "", "PGPORT": str(u.port or 5432), "PGUSER": unquote(u.username or ""),
                "PGPASSWORD": unquote(u.password or ""), "PGDATABASE": u.path.lstrip("/")})
    return env


class Sealed:
    """A write-only stream: bytes are hashed and counted, then zstd, then
    gpg into `dst`. close() returns {sha256, rows, plain_bytes, bytes}."""

    def __init__(self, dst: str, passphrase: str, popen=subprocess.Popen):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        self.dst, self.sha, self.rows, self.plain = dst, hashlib.sha256(), 0, 0
        r_fd, w_fd = os.pipe()
        os.write(w_fd, passphrase.encode("utf-8"))
        os.close(w_fd)
        self.zstd = popen(["zstd", "-q", "-3", "-T4", "-c"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.gpg = popen(["gpg", "--batch", "--yes", "--quiet", "--symmetric", "--cipher-algo", "AES256",
                          "--compress-algo", "none", "--passphrase-fd", str(r_fd), "--output", dst],
                         stdin=self.zstd.stdout, pass_fds=(r_fd,), stderr=subprocess.PIPE)
        os.close(r_fd)
        self.zstd.stdout.close()

    def write(self, b) -> int:
        b = bytes(b)
        self.sha.update(b)
        self.rows += b.count(b"\n")
        self.plain += len(b)
        self.zstd.stdin.write(b)
        return len(b)

    def close(self) -> dict:
        self.zstd.stdin.close()
        zrc, grc = self.zstd.wait(), self.gpg.wait()
        if zrc or grc:
            raise RuntimeError(f"seal failed: zstd rc={zrc} gpg rc={grc}")
        return {"sha256": self.sha.hexdigest(), "rows": self.rows, "plain_bytes": self.plain,
                "bytes": os.path.getsize(self.dst)}


def opened(src: str, passphrase: str, popen=subprocess.Popen):
    """The reverse of Sealed: a readable stream of the plain bytes in `src`."""
    r_fd, w_fd = os.pipe()
    os.write(w_fd, passphrase.encode("utf-8"))
    os.close(w_fd)
    gpg = popen(["gpg", "--batch", "--quiet", "--decrypt", "--passphrase-fd", str(r_fd), src],
                stdout=subprocess.PIPE, pass_fds=(r_fd,), stderr=subprocess.PIPE)
    os.close(r_fd)
    zstd = popen(["zstd", "-q", "-d", "-c"], stdin=gpg.stdout, stdout=subprocess.PIPE)
    gpg.stdout.close()
    return gpg, zstd


class Run:
    """One run of the copy. `prev` is the newest complete manifest (or
    None); `man` is the one this run is writing."""

    def __init__(self, *, full: bool = None, local_only: bool = False, now: dt.datetime = None,
                 spool: str = None, env: dict = None, client=None, connect=None, log=print):
        # a local-only run keeps its own state, so its unsent stamps are
        # never named by a manifest the bucket is meant to hold
        self.spool = os.path.join(spool or SPOOL, "local-only") if local_only else (spool or SPOOL)
        self.now = now or dt.datetime.now().astimezone()
        self.local_only, self.log = local_only, log
        self.env = env if env is not None else read_env(ENV_FILE)
        self.client = client
        self.connect = connect or (lambda database, login: db.connect(login, database, autocommit=False))
        self.prev = load_json(os.path.join(self.spool, "manifest.json"))
        self.man = self._resume() or self._fresh(full)
        self.warnings = self.man.setdefault("warnings", [])

    # ── the manifest ────────────────────────────────────────────────────
    def _fresh(self, full):
        if full is None:
            full = self.prev is None or self.now.weekday() == P.FULL_WEEKDAY
        stamp = self.now.strftime("%Y%m%dT%H%M%S")
        return {"stamp": stamp, "kind": "full" if full else "nightly", "started": self.now.isoformat(timespec="seconds"),
                "databases": {}, "pieces": {}, "trees": {}}

    def _resume(self):
        cur = load_json(os.path.join(self.spool, "current.json"))
        if not cur:
            return None
        age = self.now - dt.datetime.fromisoformat(cur["started"])
        if age > dt.timedelta(hours=RESUME_HOURS):
            return None
        self.log(f"resuming {cur['stamp']} ({cur['kind']}), {len(cur['pieces'])} pieces already done")
        return cur

    def save_progress(self):
        write_json(os.path.join(self.spool, "current.json"), self.man)

    @property
    def stamp(self):
        return self.man["stamp"]

    @property
    def full(self):
        return self.man["kind"] == "full"

    def object_path(self, stamp: str, name: str) -> str:
        return os.path.join(self.spool, "objects", stamp, name)

    def send(self, name: str) -> None:
        """Upload this run's object `name` once, unless running local-only."""
        uploaded = self.man.setdefault("uploaded", [])
        if self.local_only or name in uploaded:
            return
        if self.client is None:
            self.client = s3_client(self.env)
        upload(self.client, self.env["OFFSITE_BUCKET"], f"{PREFIX}/{self.stamp}/{name}",
               self.object_path(self.stamp, name))
        uploaded.append(name)
        self.save_progress()

    # ── databases ───────────────────────────────────────────────────────
    def wants(self, piece: str, sig: str, fate: str, frozen: bool, epoch_moved: bool) -> str:
        """Why this table is copied tonight, or '' to carry the previous copy."""
        old = (self.prev or {}).get("pieces", {}).get(piece)
        if not old or "stamp" not in old:
            return "first copy"
        if old.get("sig") != sig:
            return "changed"
        if epoch_moved:
            return "write counters restarted"
        if fate == P.LOCAL:
            return ""
        if frozen:
            age = self.now - stamp_time(old["stamp"])
            return "refresh" if age >= dt.timedelta(days=P.REFRESH_DAYS) else ""
        return "weekly full" if self.full else ""

    def copy_database(self, database: str, conf: dict) -> None:
        done = self.man["pieces"]
        if self.man["databases"].get(database, {}).get("done"):
            return
        login = conf["login"]
        conn = self.connect(database, login)
        try:
            cur = conn.cursor()
            cur.execute(EPOCH_SQL)
            epoch = cur.fetchone()[0]
            cur.execute(TABLES_SQL)
            tables = cur.fetchall()     # counters read BEFORE the snapshot: a copy holds at least what they count
            conn.commit()
            prev_epoch = (self.prev or {}).get("databases", {}).get(database, {}).get("epoch")
            epoch_moved = prev_epoch is not None and prev_epoch != epoch
            # set on the connection, not by a BEGIN: the driver opens the
            # transaction itself, and a second BEGIN's level is ignored
            conn.isolation_level, conn.read_only = REPEATABLE_READ, True
            for stmt in SESSION_SQL.split("; "):
                cur.execute(stmt)
            if "statement_timeout" not in os.environ.get("PGOPTIONS", ""):
                cur.execute(f"SET statement_timeout = '{STATEMENT_S}s'")
            for schema, table, node, ins, upd, dele, size in tables:
                piece = P.table_piece(database, schema, table)
                if piece in done and done[piece].get("stamp") == self.stamp:
                    continue
                fate, why = P.fate(database, schema, table)
                sig = f"{node}:{ins}:{upd}:{dele}"
                if fate == P.OUT:
                    done[piece] = {"fate": fate, "why": why, "sig": sig}
                    continue
                reason = self.wants(piece, sig, fate, conf["frozen"], epoch_moved)
                if not reason:
                    done[piece] = dict(self.prev["pieces"][piece], sig=sig)
                    continue
                name = object_name(piece) + ".copy.zst.gpg"
                t0 = time.monotonic()
                out = Sealed(self.object_path(self.stamp, name), self.env["OFFSITE_PASSPHRASE"])
                try:
                    with cur.copy(f"COPY {qident(schema)}.{qident(table)} TO STDOUT") as cp:
                        for chunk in cp:
                            out.write(chunk)
                finally:
                    meta = out.close()
                done[piece] = {"fate": fate, "sig": sig, "stamp": self.stamp, "object": name, "why": reason,
                               "seconds": round(time.monotonic() - t0, 1), **meta}
                self.log(f"  {piece}: {meta['rows']:,} rows, {meta['plain_bytes'] / 1e6:,.1f} MB -> "
                         f"{meta['bytes'] / 1e6:,.1f} MB ({reason})")
                self.save_progress()
            seqs = self.sequences(cur)
            conn.commit()
        finally:
            conn.close()
        schema_name = object_name(f"{database}:@schema") + ".dump.gpg"
        self.dump_schema(database, login, schema_name)
        for piece, v in sorted(done.items()):
            if piece.startswith(database + ":") and v.get("stamp") == self.stamp and v["fate"] == P.SEND:
                self.send(v["object"])
        self.send(schema_name)
        self.man["databases"][database] = {"epoch": epoch, "frozen": conf["frozen"], "schema": schema_name,
                                           "sequences": seqs, "done": True, "stamp": self.stamp}
        self.save_progress()

    def sequences(self, cur) -> dict:
        """Each sequence's value where the login may read it, else None (a
        restore then sets an owned sequence from its column's maximum)."""
        cur.execute(SEQUENCES_SQL)
        out = {}
        for schema, name, ok in cur.fetchall():
            val = None
            if ok:
                cur.execute(f"SELECT last_value, is_called FROM {qident(schema)}.{qident(name)}")
                val = list(cur.fetchone())
            out[f"{schema}.{name}"] = val
        return out

    def dump_schema(self, database: str, login: str, name: str, run=subprocess.run) -> None:
        """pg_dump --schema-only, custom format, sealed: the restore's
        before-data and after-data sections."""
        plain = self.object_path(self.stamp, name[:-4])
        os.makedirs(os.path.dirname(plain), exist_ok=True)
        r = run(["pg_dump", "-Fc", "--schema-only", "--no-owner", "--no-privileges", "-f", plain],
                env=pg_env(db.url(login, database)), capture_output=True)
        if r.returncode:
            raise RuntimeError(f"pg_dump --schema-only {database}: rc={r.returncode} "
                               f"{r.stderr.decode(errors='replace')[-300:]}")
        out = Sealed(self.object_path(self.stamp, name), self.env["OFFSITE_PASSPHRASE"])
        with open(plain, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK), b""):
                out.write(chunk)
        out.close()
        os.remove(plain)

    # ── file trees ──────────────────────────────────────────────────────
    def copy_tree(self, tree: str, root: str, exclude=()) -> None:
        if self.man["trees"].get(tree, {}).get("stamp") == self.stamp:
            return
        old = (self.prev or {}).get("trees", {}).get(tree, {}).get("files", {})
        now = scan_tree(root, exclude)
        files, changed = {}, []
        for rel, (size, mtime) in now.items():
            o = old.get(rel)
            if not self.full and o and o[0] == size and o[1] == mtime:
                files[rel] = o
            else:
                changed.append(rel)
        name = object_name(f"tree:{tree}") + ".tar.zst.gpg"
        meta = {}
        if changed:
            out = Sealed(self.object_path(self.stamp, name), self.env["OFFSITE_PASSPHRASE"])
            try:
                with tarfile.open(fileobj=out, mode="w|", format=tarfile.PAX_FORMAT) as tar:
                    for rel in changed:
                        got = add_file(tar, root, rel)
                        if got is None:
                            self.warnings.append(f"{tree}/{rel}: changed or unreadable while copying; next run")
                            continue
                        files[rel] = [got[0], got[1], got[2], self.stamp]
            finally:
                meta = out.close()
            self.send(name)
        self.man["trees"][tree] = {"root": root, "stamp": self.stamp, "files": files,
                                   "sent_files": len(changed), "object": name if changed else None, **meta}
        self.log(f"  tree {tree}: {len(files):,} files, {len(changed):,} copied tonight")
        self.save_progress()

    # ── the whole run ───────────────────────────────────────────────────
    def run(self, databases=None, trees=None) -> dict:
        self.log(f"offsite copy {self.stamp}: {self.man['kind']}{' (local only)' if self.local_only else ''}")
        for database, conf in (P.DATABASES if databases is None else databases).items():
            self.copy_database(database, conf)
        for tree, (root, fate, _why, exclude) in (P.TREES if trees is None else trees).items():
            if fate == P.SEND:
                self.copy_tree(tree, root, exclude)
        self.man["finished"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        self.man["sent"] = not self.local_only
        name = "manifest.json.gpg"
        out = Sealed(self.object_path(self.stamp, name), self.env["OFFSITE_PASSPHRASE"])
        out.write(json.dumps(self.man, sort_keys=True).encode())
        out.close()
        self.send(name)         # last: a stamp with a manifest is a complete copy
        write_json(os.path.join(self.spool, "manifest.json"), self.man)
        os.remove(os.path.join(self.spool, "current.json"))
        return self.man


# ── helpers ─────────────────────────────────────────────────────────────

def stamp_time(stamp: str) -> dt.datetime:
    return dt.datetime.strptime(stamp, "%Y%m%dT%H%M%S").astimezone()


def load_json(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True)
    os.replace(tmp, path)


def scan_tree(root: str, exclude=()) -> dict:
    """relative path -> (size, mtime_ns) for regular files; links and other
    kinds are left out (a tree here holds documents, not links)."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        dirnames[:] = sorted(d for d in dirnames
                             if not excluded(os.path.normpath(os.path.join(rel_dir, d)), exclude))
        for fn in sorted(filenames):
            rel = os.path.normpath(os.path.join(rel_dir, fn))
            if excluded(rel, exclude):
                continue
            try:
                st = os.lstat(os.path.join(dirpath, fn))
            except OSError:
                continue
            if (st.st_mode & 0o170000) == 0o100000:
                out[rel] = (st.st_size, st.st_mtime_ns)
    return out


def excluded(rel: str, exclude) -> bool:
    return any(rel == e or rel.startswith(e.rstrip("/") + "/") for e in exclude)


class _Hashing:
    def __init__(self, f):
        self.f, self.h = f, hashlib.sha256()

    def read(self, n=-1):
        b = self.f.read(n)
        self.h.update(b)
        return b


def add_file(tar, root: str, rel: str):
    """Add one file; (size, mtime_ns, sha256) as copied, or None when it
    could not be read whole."""
    path = os.path.join(root, rel)
    try:
        with open(path, "rb") as f:
            st = os.fstat(f.fileno())
            info = tarfile.TarInfo(rel)
            info.size, info.mtime, info.mode = st.st_size, st.st_mtime, st.st_mode & 0o7777
            hf = _Hashing(f)
            tar.addfile(info, hf)
            if os.fstat(f.fileno()).st_mtime_ns != st.st_mtime_ns:
                return None
            return st.st_size, st.st_mtime_ns, hf.h.hexdigest()
    except OSError:
        return None


def plan(prev_path: str = None, log=print) -> int:
    """What tonight would copy: per database the tables that moved since the
    newest manifest, with on-disk sizes. Reads counters only."""
    prev = load_json(prev_path or os.path.join(SPOOL, "manifest.json")) or {}
    total = 0
    for database, conf in P.DATABASES.items():
        with db.connect(conf["login"], database) as conn:
            rows = conn.execute(TABLES_SQL).fetchall()
        fates = {}
        for schema, table, node, ins, upd, dele, size in rows:
            piece = P.table_piece(database, schema, table)
            fate, _ = P.fate(database, schema, table)
            old = prev.get("pieces", {}).get(piece, {})
            moved = old.get("sig") != f"{node}:{ins}:{upd}:{dele}"
            f = fates.setdefault(fate, [0, 0, 0])
            f[0] += 1
            f[1] += size
            if moved and fate != P.OUT:
                f[2] += size
                total += size
        log(f"{database}{' (frozen)' if conf['frozen'] else ''}: " + "; ".join(
            f"{k} {v[0]} tables {v[1] / 1e9:.1f} GB, moved {v[2] / 1e9:.1f} GB" for k, v in sorted(fates.items())))
    for tree, (root, fate, _w, exclude) in P.TREES.items():
        files = scan_tree(root, exclude)
        log(f"tree {tree}: {fate}, {len(files):,} files, {sum(s for s, _ in files.values()) / 1e9:.2f} GB")
    log(f"tables moved since the newest manifest: {total / 1e9:.1f} GB on disk, heap and TOAST")
    return 0


def run_job(argv) -> int:
    started = jobrun.now()
    full = True if "--full" in argv else None
    ok, why, man = True, "", None
    try:
        r = Run(full=full, local_only="--local" in argv)
        man = r.run()
    except Exception as exc:  # noqa: BLE001 — the record and the alarm carry it
        ok, why = False, f"{type(exc).__name__}: {exc}"[:500]
    rec = summary(man) if man else {}
    rec.update({"ok": ok, "why": why, "at": dt.datetime.now().astimezone().isoformat(timespec="seconds")})
    write_json(RECORD, rec)
    detail = why or f"{rec['kind']} {rec['stamp']}: {rec['copied']} pieces, {rec['sealed_bytes'] / 1e9:.2f} GB sealed"
    jobrun.record(JOB, ok, detail, started, {k: rec.get(k) for k in ("stamp", "kind", "copied", "sealed_bytes")})
    print(f"offsite copy: {'ok' if ok else 'FAILED'} {detail}")
    if not ok or rec.get("warnings"):
        from support import alarm
        alarm.send(f"qv4 {os.uname().nodename}: off-site copy {'failed' if not ok else 'warnings'}",
                   why or "; ".join(rec["warnings"][:5]))
    return 0 if ok else 1


def summary(man: dict) -> dict:
    """The record a board check reads: no paths of files, no values."""
    tonight = [p for p in man["pieces"].values() if p.get("stamp") == man["stamp"]]
    trees = [t for t in man["trees"].values() if t.get("object")]
    sealed = sum(p.get("bytes", 0) for p in tonight) + sum(t.get("bytes", 0) for t in trees)
    frozen = {d: v["stamp"] for d, v in man["databases"].items() if v.get("frozen")}
    frozen_moved = sorted(p for p, v in man["pieces"].items()
                          if v.get("stamp") == man["stamp"] and v.get("why") == "changed"
                          and man["databases"].get(p.split(":")[0], {}).get("frozen"))
    return {"stamp": man["stamp"], "kind": man["kind"], "sent": man.get("sent"), "copied": len(tonight) + len(trees),
            "sealed_bytes": sealed, "pieces": len(man["pieces"]), "frozen_moved": frozen_moved,
            "frozen_checked": frozen, "warnings": man.get("warnings", [])}


if __name__ == "__main__":
    sys.exit(run_job(sys.argv[1:]))
