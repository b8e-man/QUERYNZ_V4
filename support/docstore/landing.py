"""The one landing wrapper (plan 1.10; docs/contracts/document-store.md).
Rebuilt, not moved: the old one stored an article's text, this stores
bytes keyed by hash. Nothing else writes the store or the `docs` tables.

    from support.docstore.landing import land, copy_from_old
    ref, new = land(data, name="x.pdf", source="party_returns", conn=conn)
    ref, new = copy_from_old("/…/var/staging/ec-donations/archive/x.pdf", "ec-donations", conn)

The bytes go to `<root>/<aa>/<sha256>` (the first two hex characters as a
folder), written to a temporary name and renamed, so a half-written file is
never the document. The row goes to `docs.documents` only after the bytes
are on disk, in the same transaction as its first name; a failed landing
leaves a `docs.landings` line and nothing else, so it is retried. A second
landing of the same bytes adds a name and nothing more: `new` is False.

The store root is the second hard disk (`/mnt/hdd2/qv4-docs`), which step
0 mounted for this. Stdlib plus the psycopg connection a caller passes.
"""
import datetime as dt
import os

from support.docstore import DocumentRef, describe

ROOT = os.environ.get("QV4_DOCS") or "/mnt/hdd2/qv4-docs"
HERE = os.path.dirname(os.path.abspath(__file__))
TABLES_SQL = os.path.join(HERE, "tables.sql")


def tables_sql() -> str:
    with open(TABLES_SQL, encoding="utf-8") as f:
        return f.read()


def path_for(sha256: str, root: str = None) -> str:
    return os.path.join(root or ROOT, sha256[:2], sha256)


def write_bytes(data: bytes, sha256: str, root: str = None) -> str:
    """The bytes on disk, atomically; a file already there is left alone
    (it is the same bytes by construction)."""
    p = path_for(sha256, root)
    if os.path.exists(p):
        return p
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + f".tmp{os.getpid()}"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, p)
    return p


def land(data: bytes, *, name: str, source: str, conn, kind_hint: str = "", name_kind: str = "file",
         fetched_at: str = None, root: str = None, content_type: str = ""):
    """Land bytes: (DocumentRef, new). Raises on a failure after writing
    the landing line; the caller's transaction is committed on success."""
    ref = describe(data, name, content_type, source, fetched_at)
    try:
        path = write_bytes(data, ref.sha256, root)
        with conn.transaction():
            row = conn.execute("SELECT 1 FROM docs.documents WHERE sha256 = %s", (ref.sha256,)).fetchone()
            new = row is None
            if new:
                conn.execute(
                    "INSERT INTO docs.documents (sha256, size, kind, source, content_sha256, fetched_at, path) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (ref.sha256, ref.size, ref.kind, source, ref.content_sha256 or None, ref.fetched_at, path))
            conn.execute(
                "INSERT INTO docs.names (sha256, name, kind) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (ref.sha256, name, name_kind))
            conn.execute("INSERT INTO docs.landings (sha256, source, name, ok, new) VALUES (%s, %s, %s, true, %s)",
                         (ref.sha256, source, name, new))
    except Exception as exc:  # noqa: BLE001 — the landing line is the record of the failure
        try:
            with conn.transaction():
                conn.execute("INSERT INTO docs.landings (sha256, source, name, ok, why) VALUES (%s, %s, %s, false, %s)",
                             (ref.sha256, source, name, f"{type(exc).__name__}: {str(exc)[:300]}"))
        except Exception:  # noqa: BLE001
            pass
        raise
    return ref, new


def copy_from_old(old_path: str, source: str, conn, root: str = None):
    """Case 1 of plan 1.10: a file the old estate holds, copied by hash,
    read-only, into the store; its old path is one of its names."""
    with open(old_path, "rb") as f:
        data = f.read()
    st = os.stat(old_path)
    fetched = dt.datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds")
    ref, new = land(data, name=os.path.basename(old_path), source=source, conn=conn, fetched_at=fetched, root=root)
    with conn.transaction():
        conn.execute("INSERT INTO docs.names (sha256, name, kind) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                     (ref.sha256, old_path, "old-path"))
    return ref, new


def names_of(sha256: str, conn) -> list:
    return [r[0] for r in conn.execute("SELECT name FROM docs.names WHERE sha256 = %s ORDER BY seen_at, name", (sha256,))]


def names_for(conn, shas: list) -> list:
    """Every name of every document in `shas`, as (sha256, name, kind,
    fetched_at), in the order the names were seen: what a module needs to
    land those documents again elsewhere from the store (the adopt of
    support.mcpsource). The only query on the store's tables outside this
    module's own functions."""
    if not shas:
        return []
    return conn.execute("SELECT n.sha256, n.name, n.kind, d.fetched_at FROM docs.names n JOIN docs.documents d USING (sha256) "
                        "WHERE n.sha256 = ANY(%s) ORDER BY n.seen_at, n.sha256", (list(shas),)).fetchall()


def copy_documents(src, dst, shas, *, root: str = None, src_store: str = "docs", dst_store: str = "docs") -> dict:
    """The document and name rows of `shas` copied from the store tables on
    `src` to those on `dst` in one transaction on `dst`: one store on disk,
    two databases naming the same files (the adopt of support.mcpsource).
    A document `dst` already holds is left as it is (only its missing names
    are added); one whose bytes are not on disk is not copied. The bytes
    are neither read nor hashed: the row is the store's record of them. The
    schemas are parameters for the tests' scratch pair; the job uses `docs`
    on both. Returns counts, and `absent`: the shas `dst` lacks after."""
    want = sorted(set(shas))
    out = {"asked": len(want), "copied": 0, "held": 0, "no source row": 0, "no bytes": 0, "names": 0,
           "names copied": 0, "names live": 0, "absent": []}
    if not want:
        return out
    rows = src.execute(f"SELECT sha256, size, kind, source, content_sha256, fetched_at, withdrawn FROM {src_store}.documents "
                       "WHERE sha256 = ANY(%s)", (want,)).fetchall()
    names = src.execute(f"SELECT sha256, name, kind, seen_at FROM {src_store}.names WHERE sha256 = ANY(%s)",
                        (want,)).fetchall()
    held = {r[0] for r in dst.execute(f"SELECT sha256 FROM {dst_store}.documents WHERE sha256 = ANY(%s)", (want,))}
    out["no source row"], out["held"], out["names"] = len(want) - len(rows), len(held), len(names)
    copy = []
    for r in rows:
        if r[0] in held:
            continue
        p = path_for(r[0], root)
        if not os.path.exists(p):
            out["no bytes"] += 1
            continue
        copy.append(tuple(r) + (p,))
    cols = "sha256, size, kind, source, content_sha256, fetched_at, withdrawn, path"
    with dst.transaction():
        dst.execute(f"CREATE TEMP TABLE _copy_d (LIKE {dst_store}.documents INCLUDING DEFAULTS) ON COMMIT DROP")
        dst.execute(f"CREATE TEMP TABLE _copy_n (LIKE {dst_store}.names INCLUDING DEFAULTS) ON COMMIT DROP")
        with dst.cursor() as cur:
            with cur.copy(f"COPY _copy_d ({cols}) FROM STDIN") as cp:
                for r in copy:
                    cp.write_row(r)
            with cur.copy("COPY _copy_n (sha256, name, kind, seen_at) FROM STDIN") as cp:
                for r in names:
                    cp.write_row(r)
            cur.execute(f"WITH ins AS (INSERT INTO {dst_store}.documents ({cols}) SELECT {cols} FROM _copy_d "
                        "ON CONFLICT (sha256) DO NOTHING RETURNING sha256, source) "
                        f"INSERT INTO {dst_store}.landings (sha256, source, name, ok, new) "
                        "SELECT i.sha256, i.source, (SELECT min(n.name) FROM _copy_n n WHERE n.sha256 = i.sha256), true, true "
                        "FROM ins i")
            out["copied"] = cur.rowcount
            cur.execute(f"INSERT INTO {dst_store}.names (sha256, name, kind, seen_at) SELECT n.sha256, n.name, n.kind, "
                        f"n.seen_at FROM _copy_n n JOIN {dst_store}.documents d USING (sha256) ON CONFLICT DO NOTHING")
            out["names copied"] = cur.rowcount
            out["names live"] = cur.execute(f"SELECT count(*) FROM _copy_n n JOIN {dst_store}.names x "
                                            "USING (sha256, kind, name)").fetchone()[0]
            live = {r[0] for r in cur.execute(f"SELECT sha256 FROM {dst_store}.documents WHERE sha256 = ANY(%s)", (want,))}
    out["absent"] = [s for s in want if s not in live]
    return out


def documents_of(shas, conn) -> dict:
    """{sha256: {'kind', 'source', 'withdrawn'}} for the documents the store's
    table holds among `shas`, read only (one query): what a reader needs to
    decide whether to open a document, without querying `docs` itself (the
    one-way test). A sha the table lacks is absent from the answer."""
    want = sorted({s for s in shas if s})
    if not want:
        return {}
    cur = conn.execute("SELECT sha256, kind, source, withdrawn FROM docs.documents WHERE sha256 = ANY(%s)", (want,))
    return {r[0]: {"kind": r[1], "source": r[2], "withdrawn": r[3]} for r in cur}


def find_by_name(name: str, conn) -> list:
    """Every document that has carried this name: the hashes."""
    return [r[0] for r in conn.execute("SELECT DISTINCT sha256 FROM docs.names WHERE name = %s", (name,))]


def read_bytes(ref_or_sha, root: str = None) -> bytes:
    sha = ref_or_sha.sha256 if isinstance(ref_or_sha, DocumentRef) else ref_or_sha
    with open(path_for(sha, root), "rb") as f:
        return f.read()
