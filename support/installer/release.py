"""THE RELEASE COPY: the checkout the worker and every job it starts run
from (card the-scheduler-s-worker-runs-the-main-checkout-…, finding 2).

The main checkout is where the integrator works: it checks an integrate
branch out there for about twenty-five minutes before each gate, so a job
started from it in that window ran the branch's code, unreviewed, on the
live database. The release copy is a separate clone at
`/home/user/querynzv4-release` that holds exactly one pushed commit of
origin/main, checked out detached, never a branch and never edited. It
moves only by `python -m support.installer release`, the integrator's step
after every push:

  1. clone the main checkout's origin, if the copy is not there yet
  2. refuse a copy with any edit, untracked file or branch checked out
  3. fetch origin; refuse unless the target commit is on origin/main
  4. check the commit out detached; delete any local branch
  5. bring the copy's own `.venv` to its requirements.txt
  6. record the commit and the time in `<copy>/.git/qv4-release.json`
     (inside `.git`, so the record never makes the copy dirty) and log
     one line to `<live>/installer/release.log`

WHY ITS OWN `.venv`, NOT A LINK TO THE MAIN CHECKOUT'S: a shared
environment is upgraded by whoever runs pip in the main checkout, so a
branch that changes requirements.txt would change the packages under the
live jobs before its gate, the same fault one level down. The copy's
environment is built the way the main checkout's is (`python -m venv`,
then `pip install -r requirements.txt`, about 80 MB) and rebuilt only when
the copy's requirements.txt hash differs from the one it was built from.
Nothing is installed outside the copy.

A moved copy does not restart the worker: its own code is already in
memory. The result says `worker_restart: owed` when the move touched the
worker's code (or the copy was just made); the integrator restarts the idle
worker then. A child mid-run keeps the code it has imported."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

RELEASE = os.environ.get("QV4_RELEASE") or "/home/user/querynzv4-release"
RECORD = "qv4-release.json"                 # under <copy>/.git/
STAMP = "qv4-requirements.sha256"           # under <copy>/.venv/
ORIGIN_MAIN = "refs/remotes/origin/main"
# what the worker process itself imports: a move touching these leaves the running worker on old code
WORKER_CODE = ("support/scheduler/", "support/db", "support/alarm", "support/__init__.py", "requirements.txt")


class Refused(Exception):
    """The copy was not moved; the message says why."""


def _git(path: str, *args: str, timeout: int = 600) -> tuple[int, str]:
    try:
        p = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return p.returncode, (p.stdout.strip() if p.returncode == 0 else (p.stdout + p.stderr).strip())


def _sh(cmd: list[str], timeout: int = 1800) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return p.returncode, (p.stdout + p.stderr).strip()


def origin_url(repo: str) -> str | None:
    rc, url = _git(repo, "config", "--get", "remote.origin.url")
    return url if rc == 0 and url else None


def record(copy: str = RELEASE) -> dict | None:
    path = os.path.join(copy, ".git", RECORD)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _dirty(copy: str) -> list[str]:
    rc, out = _git(copy, "status", "--porcelain", "--untracked-files=normal")
    if rc:
        return [f"git status failed: {out[:200]}"]
    return [l for l in out.splitlines() if l.strip()]


def state(copy: str = RELEASE) -> dict:
    """The copy as it stands, for `check`: where, which commit, whether
    that commit is on origin/main as the copy last fetched it, edits."""
    if not os.path.isdir(os.path.join(copy, ".git")):
        return {"copy": copy, "present": False}
    rc, head = _git(copy, "rev-parse", "HEAD")
    rcb, branch = _git(copy, "symbolic-ref", "-q", "--short", "HEAD")
    on = _git(copy, "merge-base", "--is-ancestor", "HEAD", ORIGIN_MAIN)[0] == 0 if rc == 0 else False
    return {"copy": copy, "present": True, "commit": head[:12] if rc == 0 else None, "branch": branch if rcb == 0 else None,
            "on_origin_main": on, "dirty": len(_dirty(copy)), "venv": os.path.exists(os.path.join(copy, ".venv", "bin", "python")),
            "record": record(copy)}


def ensure_venv(copy: str, sh=None) -> dict:
    """The copy's own environment, built as the main checkout's is; pip runs
    only when requirements.txt differs from the hash it was built from."""
    sh = sh or _sh
    venv = os.path.join(copy, ".venv")
    py = os.path.join(venv, "bin", "python")
    req = os.path.join(copy, "requirements.txt")
    want = hashlib.sha256(open(req, "rb").read()).hexdigest() if os.path.exists(req) else None
    stamp = os.path.join(venv, STAMP)
    have = open(stamp, encoding="utf-8").read().strip() if os.path.exists(stamp) else None
    action = "same"
    if not os.path.exists(py):
        rc, out = sh([sys.executable, "-m", "venv", venv])
        if rc:
            raise Refused(f"the copy moved, but its .venv could not be made: {out[-300:]}")
        action = "create"
    if want and want != have:
        rc, out = sh([os.path.join(venv, "bin", "pip"), "install", "-q", "-r", req])
        if rc:
            raise Refused(f"the copy moved, but pip failed in its .venv (worker not restarted): {out[-300:]}")
        with open(stamp, "w", encoding="utf-8") as f:
            f.write(want + "\n")
        action = "install" if action == "same" else action
    return {"action": action, "requirements_sha256": (want or "")[:12]}


def _restart_owed(copy: str, prev: str | None, sha: str) -> tuple[bool, list[str]]:
    if not prev:
        return True, ["(the copy is new)"]
    if prev == sha:
        return False, []
    rc, out = _git(copy, "diff", "--name-only", prev, sha)
    if rc:
        return True, [f"(git cannot diff {prev[:12]}..{sha[:12]})"]
    hits = [p for p in out.splitlines() if p.startswith(WORKER_CODE) and "/tests/" not in p
            and not p.endswith(("jobs.toml", "profiles.toml"))]     # the catalogue reloads itself
    return bool(hits), hits


def release(copy: str = RELEASE, commit: str = None, *, origin: str = None, repo: str = None, log_path: str = None,
            venv: bool = True, sh=None, log=print, now=None) -> dict:
    """Create or move the release copy to `commit` (default: origin/main
    after a fetch). Raises Refused, with the copy untouched, on a dirty
    copy, a branch, or a commit not on origin/main."""
    from support import installer as inst
    repo = repo or inst.REPO
    now = now or dt.datetime.now(dt.timezone.utc)
    created = False
    if not os.path.lexists(copy):
        origin = origin or origin_url(repo)
        if not origin:
            raise Refused(f"no origin to clone: {repo} names no remote.origin.url")
        rc, out = _git(os.path.dirname(copy) or ".", "clone", "--quiet", "--no-checkout", origin, copy, timeout=1800)
        if rc:
            raise Refused(f"clone of origin failed: {out[-300:]}")
        created = True
    elif not os.path.isdir(os.path.join(copy, ".git")):
        raise Refused(f"{copy} exists and is not a clone; it is not touched")
    else:
        have = origin_url(copy)
        if origin and have != origin:
            raise Refused("the copy's origin is not the one asked for; it is not touched")
        dirty = _dirty(copy)
        if dirty:
            raise Refused(f"the copy is edited ({len(dirty)} path(s), first: {dirty[0]}); a release copy is never "
                          f"edited, so nothing was moved: find out who wrote there")
        rc, branch = _git(copy, "symbolic-ref", "-q", "--short", "HEAD")
        if rc == 0 and _git(copy, "rev-parse", "--verify", "--quiet", "HEAD")[0] == 0:
            raise Refused(f"the copy has the branch {branch} checked out; a release copy is only ever detached")
    rc, out = _git(copy, "fetch", "--quiet", "--prune", "origin", timeout=1800)
    if rc:
        raise Refused(f"fetch from origin failed: {out[-300:]}")
    target = commit or ORIGIN_MAIN
    rc, sha = _git(copy, "rev-parse", "--verify", "--quiet", f"{target}^{{commit}}")
    if rc:
        raise Refused(f"{target} is not a commit the copy can see after the fetch")
    if _git(copy, "merge-base", "--is-ancestor", sha, ORIGIN_MAIN)[0] != 0:
        raise Refused(f"{sha[:12]} is not on origin/main: only a pushed commit of main is released")
    old = record(copy)
    rc, head = _git(copy, "rev-parse", "--verify", "--quiet", "HEAD")
    prev = None if created else ((old or {}).get("commit") or (head if rc == 0 else None))
    rc, out = _git(copy, "checkout", "--quiet", "--detach", sha)
    if rc:
        raise Refused(f"checkout of {sha[:12]} failed: {out[-300:]}")
    rc, branches = _git(copy, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    for b in (branches.splitlines() if rc == 0 else []):
        _git(copy, "branch", "-D", b)
    rc, head = _git(copy, "rev-parse", "HEAD")
    if head != sha or _dirty(copy) or _git(copy, "symbolic-ref", "-q", "HEAD")[0] == 0:
        raise Refused(f"after the checkout the copy is not clean and detached at {sha[:12]}: look before rerunning")
    env = ensure_venv(copy, sh) if venv else {"action": "skipped"}
    owed, why = _restart_owed(copy, prev if not created else None, sha)
    rec = {"commit": sha, "previous": prev, "at": now.astimezone(dt.timezone.utc).isoformat(timespec="seconds"),
           "by": os.environ.get("USER") or "?", "created": created, "venv": env["action"],
           "worker_restart": "owed" if owed else "not needed", "worker_code_changed": why[:20]}
    tmp = os.path.join(copy, ".git", RECORD + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    os.replace(tmp, os.path.join(copy, ".git", RECORD))
    verb = "created at" if created else "stays at" if prev == sha else "moved to"
    line = (f"{rec['at']} release {copy} {verb} {sha[:12]}"
            f"{f' (was {prev[:12]})' if verb == 'moved to' and prev else ''} by {rec['by']}; venv {env['action']}; "
            f"worker restart {rec['worker_restart']}")
    log_path = log_path or os.path.join(inst.LIVE, "installer", "release.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    log(line)
    return {**rec, "copy": copy, "log": log_path}
