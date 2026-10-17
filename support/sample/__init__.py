"""The sample (plan 1b.6; core: "Two tiers of checks").

Each module keeps `sample.list` in its own folder: document hashes and
source keys, one per line (`#` lines ignored), never bytes or rows, so no
personal data enters git. A module with a list also has `sample.py` with

    def fill(conn, schema: str, items: list[str]) -> int

which loads those documents and keys into tables under `schema` in
`querynz_v4_sample`, through the code of the branch it runs from, and
returns the row count. Tables that hold a person's home address go in
`<schema>_private`, there as everywhere.

    fill_schema("scratch_fix-keys-1", conn_factory)   every module's list → that schema

One command gathers the lists and fills a named scratch schema. Each
session fills its own, so two sessions on different branches never disturb
each other; a lock per schema name keeps two fills of the same schema
apart. The integrator's own fill from the main line is what other sessions
read as published tables. The first list is the thin slice's (1.11).
"""
import fcntl
import importlib.util
import os
import re
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.environ.get("QV4_WORK") or "/home/user/querynzv4-work"
ROOTS = ("keys", "support", "registers", "links", "products", "checks")
_ITEM = re.compile(r"^(?:([0-9a-f]{64})(?:\s+\S.*)?|(key:\s*\S.*))$")   # a hash may carry a comment after it
SCHEMA = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def read_list(path: str) -> list:
    """The items of one sample.list; a line that is neither a hash nor a key is refused."""
    items = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = _ITEM.match(line)
            if not m:
                raise ValueError(f"{path}:{i}: not a sha256 or a `key:` line (no bytes or rows in a sample list)")
            items.append(m.group(1) or m.group(2))
    return items


def lists(repo: str = None) -> list:
    """(module folder, items) for every sample.list in the repository."""
    repo = repo or REPO
    out = []
    for root in ROOTS:
        base = os.path.join(repo, root)
        for dirpath, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", ".venv", "tests"))
            if "sample.list" in files:
                out.append((os.path.relpath(dirpath, repo), read_list(os.path.join(dirpath, "sample.list"))))
    return sorted(out)


def filler(repo: str, module: str):
    """The module's `sample.py` `fill` function, loaded from the branch's own code."""
    path = os.path.join(repo, module, "sample.py")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{module}/sample.list has no {module}/sample.py beside it")
    spec = importlib.util.spec_from_file_location(f"sample_{module.replace('/', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "fill"):
        raise AttributeError(f"{module}/sample.py has no fill(conn, schema, items)")
    return mod.fill


def lock_path(schema: str) -> str:
    return os.path.join(WORK, "locks", f"sample-{schema}.lock")


def fill_schema(schema: str, connect, repo: str = None, log=print, sleep=time.sleep) -> dict:
    """Fill `schema` (and `<schema>_private`) in the sample database from every
    module's list. `connect()` returns a psycopg connection to querynz_v4_sample.
    Returns module → rows. Two fills of different schemas run side by side;
    two of the same schema take turns."""
    if not SCHEMA.match(schema):
        raise ValueError(f"not a schema name: {schema!r}")
    repo = repo or REPO
    os.makedirs(os.path.dirname(lock_path(schema)), exist_ok=True)
    t0 = time.monotonic()
    out = {}
    with open(lock_path(schema), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            with connect() as conn:
                conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}_private")
                conn.commit()
                for module, items in lists(repo):
                    n = filler(repo, module)(conn, schema, items)
                    conn.commit()
                    out[module] = n
                    log(f"sample: {module}: {len(items)} item(s) → {n} row(s) in {schema}")
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
    log(f"sample: {schema} filled from {len(out)} module(s) in {time.monotonic() - t0:.1f} s")
    return out


def scratch_name(session: str) -> str:
    return "scratch_" + re.sub(r"[^a-z0-9_]", "_", session.lower())
