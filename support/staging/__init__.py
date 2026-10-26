"""The full tier's loading step (plan 1b.7; core: "Two tiers of checks").

At a merge the gate loads only the modules the branch touches into a
staging schema of the real database and, on a pass, moves those tables
into place, so nothing is loaded twice. The convention a module follows
to take part: a `load.py` beside its code with

    def load(conn, schema: str) -> int        # build the module's tables under `schema`
    def publish(conn, staging: str) -> None   # move them into the module's own schema (one transaction)

`touched_modules(repo, branch)` is the set of module folders the branch
changed against main that carry a `load.py`. `run(repo, branch, connect)`
loads each into `staging_<branch slug>_<module>` and publishes on success;
a load expected to take more than ten minutes is a scheduler job (step 2)
and before 7 November stays inside the bulk-loading limit. With no module
carrying a `load.py` yet, the step is a no-op that says so.

    python -m support.staging <branch> [--database querynz_v4]
"""
import importlib.util
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOTS = ("keys", "support", "registers", "links", "products", "checks")


def module_of(path: str):
    parts = path.split("/")
    if parts[0] not in ROOTS:
        return None
    if parts[0] in ("keys", "links"):
        return parts[0]
    return "/".join(parts[:2]) if len(parts) > 2 else None


def touched_modules(repo: str, branch: str, base: str = "main") -> list:
    p = subprocess.run(["git", "diff", "--name-only", f"{base}...{branch}"], cwd=repo, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr.strip())
    mods = set()
    for line in p.stdout.splitlines():
        m = module_of(line.strip())
        if m and os.path.isfile(os.path.join(repo, m, "load.py")):
            mods.add(m)
    return sorted(mods)


def loader(repo: str, module: str):
    path = os.path.join(repo, module, "load.py")
    spec = importlib.util.spec_from_file_location(f"load_{module.replace('/', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for fn in ("load", "publish"):
        if not hasattr(mod, fn):
            raise AttributeError(f"{module}/load.py has no {fn}()")
    return mod


PRIVATE_SUFFIX = "_private"   # a lane's private schema is `<schema>_private` (support/db)
SCHEMA_MAX = 63 - len(PRIVATE_SUFFIX)   # Postgres cuts an identifier at 63 bytes silently


def staging_schema(branch: str, module: str) -> str:
    """`staging_<branch>_<module>`, cut so that `<schema>_private` still fits
    Postgres's 63-byte identifier: at 63 the private schema was cut back to
    the public one's name and a lane's two `entries` tables collided
    (integrate/diaries-parliament, 27 October 2026)."""
    slug = re.sub(r"[^a-z0-9]+", "_", (branch + "_" + module).lower()).strip("_")
    return ("staging_" + slug)[:SCHEMA_MAX].rstrip("_")


def run(repo: str, branch: str, connect, log=print) -> dict:
    """module → rows loaded; publishes each on success. A failure stops the
    run before anything is published."""
    mods = touched_modules(repo, branch)
    if not mods:
        log("staging: no touched module carries a load.py; nothing to load")
        return {}
    out = {}
    with connect() as conn:
        for m in mods:
            schema = staging_schema(branch, m)
            t0 = time.monotonic()
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            conn.commit()
            mod = loader(repo, m)
            n = mod.load(conn, schema)
            conn.commit()
            out[m] = n
            log(f"staging: {m}: {n} row(s) into {schema} in {time.monotonic() - t0:.0f} s")
        for m in mods:
            mod = loader(repo, m)
            mod.publish(conn, staging_schema(branch, m))
            conn.commit()
            log(f"staging: {m}: published")
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python -m support.staging <branch> [--database querynz_v4]")
        return 2
    branch = argv[0]
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    run(REPO, branch, lambda: db.connect(db.OWNER_KEY, database))
    return 0


if __name__ == "__main__":
    sys.exit(main())
