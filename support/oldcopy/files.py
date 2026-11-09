"""The old file stores' PDFs and images into the document store, by their bytes (ruling 160; support/oldcopy says the
whole). The store dedups: a file whose bytes it holds adds a name and costs no write, and a file already landed under
its old path is not read again. The tree is walked in sorted order and the walk's cursor is the last relative path
done, so a stopped run resumes past it; every file tried is a ledger line, committed with the cursor per batch."""
import datetime as dt
import os
import time

from psycopg import sql

from support.docstore import kind_of
from support.docstore import landing
from support.oldcopy import LEDGER

BATCH_FILES = 200
MAX_BYTES = 256 * 1024 * 1024          # a file over this is recorded (too-big), never read into memory
_MAGIC = ((b"%PDF-", "pdf", "application/pdf"), (b"\x89PNG\r\n\x1a\n", "image", "image/png"),
          (b"\xff\xd8\xff", "image", "image/jpeg"), (b"GIF87a", "image", "image/gif"), (b"GIF89a", "image", "image/gif"),
          (b"II*\x00", "image", "image/tiff"), (b"MM\x00*", "image", "image/tiff"))


def sniff(path: str, name: str) -> tuple:
    """(kind, content_type) by the name, then by the first bytes when the name says nothing (stores kept by hash)."""
    k = kind_of(name)
    if k != "other":
        return k, ""
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError:
        return "other", ""
    for magic, kind, ct in _MAGIC:
        if head.startswith(magic):
            return kind, ct
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image", "image/webp"
    return "other", ""


def wanted(kind: str, html: bool) -> bool:
    return kind in ("pdf", "image") or (html and kind == "web-page")


def walk(root: str, after: str = None, exclude=()):
    """Relative paths under `root` in sorted order, every one after `after`; whole subtrees at or before the cursor
    are not descended. Symbolic links are not followed."""
    ex = set(exclude)
    # the order is by path components (a depth-first walk sorted by name), so the cursor compares as a tuple of
    # components: as strings, "a-c" sorts before "a/b" though the walk reaches a/b first
    at = None if after is None else tuple(after.split(os.sep))

    def rec(rel):
        full = os.path.join(root, rel) if rel else root
        try:
            entries = sorted(os.scandir(full), key=lambda e: e.name)
        except OSError:
            return
        for e in entries:
            r = os.path.join(rel, e.name) if rel else e.name
            if r in ex:
                continue
            t = tuple(r.split(os.sep))
            if e.is_dir(follow_symlinks=False):
                if at is not None and at[:len(t)] > t:
                    continue                      # everything under it was walked before the cursor
                yield from rec(r)
            elif e.is_file(follow_symlinks=False):
                if at is None or t > at:
                    yield r
    yield from rec("")


def _line(conn, ledger, store, rel, size, mtime, sha, outcome, why=None):
    conn.execute(sql.SQL("INSERT INTO {}.files (store, old_path, size, mtime, sha256, outcome, why) "
                         "VALUES (%s,%s,%s,%s,%s,%s,%s)").format(sql.Identifier(ledger)),
                 (store, rel, size, mtime, sha, outcome, why))


def _cursor(conn, ledger, store):
    r = conn.execute(sql.SQL("SELECT after_path FROM {}.file_cursors WHERE store = %s").format(sql.Identifier(ledger)),
                     (store,)).fetchone()
    return r[0] if r else None


def _set_cursor(conn, ledger, store, after, caught_up, n):
    conn.execute(sql.SQL(
        "INSERT INTO {}.file_cursors (store, after_path, caught_up, files) VALUES (%s,%s,%s,%s) "
        "ON CONFLICT (store) DO UPDATE SET after_path = EXCLUDED.after_path, caught_up = EXCLUDED.caught_up, "
        "files = {}.file_cursors.files + EXCLUDED.files, updated_at = now()").format(
        sql.Identifier(ledger), sql.Identifier(ledger)), (store, after, caught_up, n))


def _held_by_path(conn, old_path):
    """The document already landed under this absolute old path (only an old path is absolute among the names)."""
    shas = landing.find_by_name(old_path, conn)
    return shas[:1] or None


def land_one(conn, store, rel, *, root=None, ledger=LEDGER) -> str:
    """One file: its outcome (landed-new, landed-held, held-by-path, failed, too-big, not-wanted), its ledger line
    written in the caller's transaction."""
    full = os.path.join(store.root, rel)
    try:
        st = os.stat(full)
    except OSError as exc:
        _line(conn, ledger, store.name, rel, None, None, None, "failed", type(exc).__name__)
        return "failed"
    kind, ct = sniff(full, rel)
    if not wanted(kind, store.html):
        return "not-wanted"
    held = _held_by_path(conn, full)
    if held:
        _line(conn, ledger, store.name, rel, st.st_size, st.st_mtime, held[0], "held-by-path")
        return "held-by-path"
    if st.st_size > MAX_BYTES:
        _line(conn, ledger, store.name, rel, st.st_size, st.st_mtime, None, "too-big", f"over {MAX_BYTES} bytes")
        return "too-big"
    try:
        with open(full, "rb") as f:
            data = f.read()
        fetched = dt.datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds")
        ref, new = landing.land(data, name=os.path.basename(full), source=store.source, conn=conn,
                                fetched_at=fetched, root=root, content_type=ct)
        # its old path as a name too, as landing.copy_from_old does (the second landing adds the name, no bytes)
        landing.land(data, name=full, name_kind="old-path", source=store.source, conn=conn, fetched_at=fetched,
                     root=root, content_type=ct)
    except Exception as exc:  # noqa: BLE001 — one file's failure is its ledger line; the walk goes on
        _line(conn, ledger, store.name, rel, st.st_size, st.st_mtime, None, "failed", f"{type(exc).__name__}")
        return "failed"
    outcome = "landed-new" if new else "landed-held"
    _line(conn, ledger, store.name, rel, st.st_size, st.st_mtime, ref.sha256, outcome)
    return outcome


def copy_store(conn, store, *, root=None, ledger=LEDGER, batch: int = BATCH_FILES, budget_s: float = 3000,
               stop=lambda: False, log=print) -> dict:
    """Walk one store from its cursor, landing what is wanted, committing ledger and cursor every `batch` files tried,
    until the walk ends, the budget is spent or `stop()` says so."""
    after = _cursor(conn, ledger, store.name)
    conn.commit()
    t0, counts, n_batch, last = time.monotonic(), {}, 0, after
    stopped = ""
    for rel in walk(store.root, after, store.exclude):
        if n_batch == 0:
            if time.monotonic() - t0 > budget_s:
                stopped = "budget"
                break
            if stop():
                stopped = "window"
                break
        out = land_one(conn, store, rel, root=root, ledger=ledger)
        counts[out] = counts.get(out, 0) + 1
        last = rel
        n_batch += 1
        if n_batch >= batch:
            _set_cursor(conn, ledger, store.name, last, False, n_batch)
            conn.commit()
            n_batch = 0
    _set_cursor(conn, ledger, store.name, last, not stopped, n_batch)
    conn.commit()
    log(f"support.oldcopy: store {store.name}: {counts}" + (f", stopped ({stopped})" if stopped else ", caught up"))
    return {"counts": counts, "caught_up": not stopped, "stopped": stopped}
