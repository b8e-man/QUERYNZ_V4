"""THE INSTALLER (plan step 2.11): one installer puts the same code, job
files and model files on every box, and copies the credential files from
box to box directly, never through the repository.

Seven steps, each a plan before it is an action:

  code          the checkout on the box is the main checkout at a commit;
                another box pulls the same commit (git), never a copy by hand
  venv          `.venv` from requirements.txt, the same Python on every box
  units         every `qv4-*.service` and `qv4-*.timer` the repository ships
                (`checks/jobs/`, `support/*/units/`, `support/*/jobs/`) into the user unit
                folder. ONLY THE PREFIX: a file without `qv4-` is refused as
                a source and never touched as a target (hard limit 23). A
                stale `qv4-` unit the repository no longer ships is reported,
                not removed. A timer whose job is timetabled in the catalogue
                is SUPERSEDED (step 2.12: the clock is the queue's): disabled,
                removed, and the slot it served handed over so nothing runs
                twice; its service unit stays for a hand run. The worker
                instance for this box is enabled, and so is every standing
                service (one with an `[Install]` section: `qv4-radiance`,
                a product's surface), so a boot brings it back. The worker's unit runs
                from the release copy (`release.py`); it is refused, and
                the unit on the box left as it is, until that copy exists.
  release       the release copy: one pushed commit of origin/main,
                detached, never edited, with its own `.venv`; moved after
                every push (`python -m support.installer release`)
  model-server  the estate's own copy of the model server, beside the old
                build and never over it (`<live>/llama/bin`), with its
                version and hash recorded; the frozen product's two servers
                keep running from their own program
  models        every weights file the profiles name is present under the
                box's models folder; on a second box they are copied across
  credentials   `~/.querynz/*.env` copied box to box over ssh when a box is
                named; never read into the repository, a log or a card

`check` is the parity report: what differs between the repository and the
box. node1 is out of the plan (ruling 55), so a second box is a parameter
here and proven when one exists; on one box every step is still real.
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
UNIT_DIR = os.environ.get("QV4_UNIT_DIR") or os.path.expanduser("~/.config/systemd/user")
PREFIX = "qv4-"
OLD_LLAMA_DIR = "/home/user/llama.cpp/build/bin"
QV4_LLAMA_DIR = os.environ.get("QV4_LLAMA_DIR") or os.path.join(LIVE, "llama", "bin")
MODELS_DIR = os.environ.get("QV4_MODELS") or "/home/user/models"
CRED_DIR = os.environ.get("QV4_CRED_DIR") or os.path.expanduser("~/.querynz")
UNIT_GLOBS = ("checks/jobs/qv4-*.service", "checks/jobs/qv4-*.timer", "support/*/units/qv4-*.service", "support/*/units/qv4-*.timer",
              "support/*/jobs/qv4-*.service", "support/*/jobs/qv4-*.timer",     # support/offsite/jobs/ (the founding session's)
              "products/*/units/qv4-*.service", "products/*/units/qv4-*.timer")  # a product's surface on its own port (board-1, 20 October)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sh(cmd: list[str], timeout: int = 600) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return r.returncode, (r.stdout + r.stderr).strip()


# ── units ────────────────────────────────────────────────────────────────────

def unit_sources(repo: str = REPO) -> dict[str, str]:
    """name → path for every unit file the repository ships. Anything in a
    units folder without the prefix is a mistake and is refused loudly."""
    out = {}
    for pattern in UNIT_GLOBS:
        for p in sorted(glob.glob(os.path.join(repo, pattern))):
            out[os.path.basename(p)] = p
    bad = []
    for folder in ("checks/jobs", *glob.glob(os.path.join(repo, "support", "*", "units")), *glob.glob(os.path.join(repo, "support", "*", "jobs")),
                   *glob.glob(os.path.join(repo, "products", "*", "units"))):
        d = folder if os.path.isabs(folder) else os.path.join(repo, folder)
        for n in os.listdir(d) if os.path.isdir(d) else []:
            if (n.endswith(".service") or n.endswith(".timer")) and not n.startswith(PREFIX):
                bad.append(os.path.join(d, n))
    if bad:
        raise ValueError(f"unit files without the {PREFIX} prefix are not installed by this estate (hard limit 23): {bad}")
    return out


def timetabled_jobs(repo: str = REPO) -> set[str]:
    """The jobs whose clock is the queue's (step 2.12): a timer for one of
    these is superseded."""
    from support.scheduler import registry as reg
    path = os.path.join(repo, "support", "scheduler", "jobs.toml")
    if not os.path.exists(path):
        return set()
    import pathlib
    return {jt.name for jt in reg.load(pathlib.Path(path)).values() if jt.every_s or jt.at_utc}


def plan_units(repo: str = REPO, unit_dir: str = UNIT_DIR) -> list[dict]:
    """What installing would do: install, update, same, stale (on the box,
    not in the repository; reported, never removed) or superseded (a timer
    whose job runs on the queue's clock: disabled and removed, its service
    unit kept for a hand run)."""
    src = unit_sources(repo)
    timetabled = timetabled_jobs(repo)
    out = []
    for name, path in src.items():
        target = os.path.join(unit_dir, name)
        if name.endswith(".timer") and name[:-len(".timer")] in timetabled:
            out.append({"unit": name, "action": "superseded", "present": os.path.exists(target), "job": name[:-len(".timer")]})
        elif not os.path.exists(target):
            out.append({"unit": name, "action": "install"})
        elif sha256_file(target) != sha256_file(path):
            out.append({"unit": name, "action": "update"})
        else:
            out.append({"unit": name, "action": "same"})
    for n in sorted(os.listdir(unit_dir)) if os.path.isdir(unit_dir) else []:
        if n.startswith(PREFIX) and (n.endswith(".service") or n.endswith(".timer")) and n not in src:
            out.append({"unit": n, "action": "stale"})
    return out


MAIN_CHECKOUT = "/home/user/querynzv4"
RELEASE_COPY = os.environ.get("QV4_RELEASE") or "/home/user/querynzv4-release"


def unit_text(path: str, repo: str = REPO) -> str:
    """A shipped unit names the main checkout, or (the worker) the release
    copy. Installed from the main checkout or the release copy it is the
    shipped text. Installed from a working copy (a rehearsal before the
    merge) the paths are rewritten to it, and the next install from the
    main checkout puts the shipped text back: the hash differs, so it is
    an `update`."""
    text = open(path, encoding="utf-8").read()
    here = os.path.realpath(repo)
    if here not in (os.path.realpath(MAIN_CHECKOUT), os.path.realpath(RELEASE_COPY)):
        py = os.path.join(here if os.path.exists(os.path.join(here, ".venv", "bin", "python")) else MAIN_CHECKOUT,
                          ".venv", "bin", "python")
        text = text.replace(f"ExecStart={RELEASE_COPY}/.venv/bin/python", f"ExecStart={py}")
        for shipped in (MAIN_CHECKOUT, RELEASE_COPY):
            text = text.replace(f"WorkingDirectory={shipped}\n", f"WorkingDirectory={here}\n")
        text = text.replace("[Service]", f"[Service]\n# REHEARSAL: installed from the working copy {here}; "
                                         f"the merge's install replaces this with the shipped unit", 1)
    return text


def release_missing(text: str) -> str | None:
    """Why a unit that runs from the release copy cannot be placed yet: the
    copy is not made (no record) or has no environment. None when it can."""
    if f"WorkingDirectory={RELEASE_COPY}\n" not in text:
        return None
    from support.installer import release
    if not release.record(RELEASE_COPY):
        return f"the release copy {RELEASE_COPY} is not made: run `python -m support.installer release` first"
    if not os.path.exists(os.path.join(RELEASE_COPY, ".venv", "bin", "python")):
        return f"the release copy {RELEASE_COPY} has no .venv: rerun `python -m support.installer release`"
    return None


def handover_clock(job: str, timer: str):
    """Mark the slot the timer served so the queue's first run is the next
    one (support.scheduler.queue.handover, on the live queue)."""
    import support.db as db
    from support.scheduler import SCHEMA
    from support.scheduler import queue as q
    conn = db.connect(db.OWNER_KEY, "querynz_v4", autocommit=True)
    try:
        return q.handover(conn, SCHEMA, job, by=f"installer: {timer} superseded")
    finally:
        conn.close()


def install_units(repo: str = REPO, unit_dir: str = UNIT_DIR, box: str = None, sh=None, enable: bool = True,
                  only: tuple = (), handover=None) -> list[dict]:
    """Copy the shipped units in, reload, enable the timers and this box's
    worker. Touches nothing without the prefix. `only` restricts the
    install to the named units (a rehearsal places one unit, not all)."""
    sh = sh or _sh
    handover = handover or handover_clock
    done = []
    superseded, refused = set(), set()
    for step in plan_units(repo, unit_dir):
        name = step["unit"]
        if not name.startswith(PREFIX) or step["action"] == "stale":   # never a foreign unit; a stale one is reported only
            continue
        if only and name not in only:
            continue
        if step["action"] == "superseded":
            # the job's clock is the queue's now: the timer goes, the service unit stays for a hand run
            superseded.add(name)
            if step["present"]:
                sh(["systemctl", "--user", "disable", "--now", name])
                os.unlink(os.path.join(unit_dir, name))
                slot = handover(step["job"], name)
                done.append({"unit": name, "action": "superseded", "job": step["job"], "handed_over_slot": str(slot) if slot else None})
            continue
        target = os.path.join(unit_dir, name)
        text = unit_text(unit_sources(repo)[name], repo)
        why = release_missing(text)
        if why:
            # a worker pointed at a copy that is not there would fail and restart for ever; the old unit stays
            refused.add(name)
            done.append({"unit": name, "action": "refused", "why": why})
            continue
        if step["action"] in ("install", "update") or (os.path.exists(target) and open(target, encoding="utf-8").read() != text):
            os.makedirs(unit_dir, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(text)
            done.append({"unit": name, "action": step["action"] if step["action"] != "same" else "update"})
    if any(d["action"] != "refused" for d in done):
        sh(["systemctl", "--user", "daemon-reload"])
    if enable:
        for name in unit_sources(repo):
            if name.endswith(".timer") and name not in superseded and (not only or name in only):
                sh(["systemctl", "--user", "enable", "--now", name])
        if ("qv4-worker@.service" in unit_sources(repo) and "qv4-worker@.service" not in refused
                and (not only or "qv4-worker@.service" in only)):
            inst = f"qv4-worker@{box or os.uname().nodename}.service"
            sh(["systemctl", "--user", "enable", "--now", inst])
            done.append({"unit": inst, "action": "enabled"})
        for name, path in unit_sources(repo).items():
            # a standing service (a model server, a product's surface): enabled, so a boot brings it back
            if (name.endswith(".service") and "@" not in name and name not in refused and (not only or name in only)
                    and standing(open(path, encoding="utf-8").read())):
                sh(["systemctl", "--user", "enable", "--now", name])
                done.append({"unit": name, "action": "enabled"})
    return done


def standing(text: str) -> bool:
    """A service that runs on its own and comes back on a boot: it carries
    an `[Install]` section. A timer's service has none (the timer or the
    queue starts it); a template is enabled by its instance."""
    return any(line.strip() == "[Install]" for line in text.splitlines())


# ── the model server, beside the old one ─────────────────────────────────────

def llama_version(binary: str) -> str | None:
    rc, out = _sh([binary, "--version"], timeout=30)
    import re
    m = re.search(r"version:\s*(\S+)\s*\(([0-9a-f]+)\)", out)
    return f"{m.group(1)} ({m.group(2)})" if m else None


def plan_model_server(src_dir: str = OLD_LLAMA_DIR, dst_dir: str = QV4_LLAMA_DIR) -> dict:
    src = os.path.join(src_dir, "llama-server")
    dst = os.path.join(dst_dir, "llama-server")
    if not os.path.exists(src):
        return {"action": "none", "why": f"no source build at {src}"}
    if os.path.exists(dst) and sha256_file(dst) == sha256_file(src):
        return {"action": "same", "version": llama_version(dst), "at": dst, "self_contained": self_contained(dst),
                "runpath": runpath(dst)}
    return {"action": "install" if not os.path.exists(dst) else "update", "from": src, "to": dst, "version": llama_version(src)}


def install_model_server(src_dir: str = OLD_LLAMA_DIR, dst_dir: str = QV4_LLAMA_DIR) -> dict:
    """Copy the server binary and the shared libraries beside it into the
    estate's own folder. The source is read, never written: the frozen
    product's servers keep their program (hard limit 23)."""
    plan = plan_model_server(src_dir, dst_dir)
    if plan["action"] in ("none", "same"):
        return plan
    os.makedirs(dst_dir, exist_ok=True)
    copied = []
    for n in sorted(os.listdir(src_dir)):
        p = os.path.join(src_dir, n)
        if n == "llama-server" or (n.startswith("lib") and ".so" in n):
            if os.path.islink(p):
                target = os.readlink(p)
                q = os.path.join(dst_dir, n)
                if os.path.lexists(q):
                    os.unlink(q)
                os.symlink(target, q)
            else:
                shutil.copy2(p, os.path.join(dst_dir, n))
            copied.append(n)
    dst = os.path.join(dst_dir, "llama-server")
    rec = {"version": llama_version(dst), "sha256": sha256_file(dst), "from": src_dir, "copied": len(copied),
           "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    with open(os.path.join(dst_dir, "VERSION.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    return {"action": plan["action"], **rec, "to": dst}


# ── models, venv, code, credentials ──────────────────────────────────────────

def plan_models(profiles: dict, models_dir: str = MODELS_DIR) -> list[dict]:
    out = []
    for p in profiles.values():
        for w in p.weight_paths(models_dir):
            out.append({"profile": p.name, "file": w, "present": os.path.exists(w),
                        "gb": round(os.path.getsize(w) / 1024 ** 3, 1) if os.path.exists(w) else None})
    return out


def copy_models(profiles: dict, box: str, models_dir: str = MODELS_DIR, sh=None) -> list[dict]:
    """To a second box, directly, only what is missing there."""
    sh = sh or _sh
    out = []
    for m in plan_models(profiles, models_dir):
        if not m["present"]:
            out.append({**m, "action": "missing here: cannot copy"})
            continue
        rc, msg = sh(["rsync", "-a", "--ignore-existing", m["file"], f"{box}:{m['file']}"], timeout=7200)
        out.append({**m, "action": "copied" if rc == 0 else f"failed: {msg[:200]}"})
    return out


def plan_venv(repo: str = REPO) -> dict:
    py = os.path.join(repo, ".venv", "bin", "python")
    if not os.path.exists(py):
        return {"action": "create", "python": sys.executable}
    rc, ver = _sh([py, "--version"])
    rc2, frozen = _sh([os.path.join(repo, ".venv", "bin", "pip"), "freeze"])
    want = [l.split("==")[0].split("[")[0].lower() for l in open(os.path.join(repo, "requirements.txt")) if "==" in l]
    have = {l.split("==")[0].lower() for l in frozen.splitlines() if "==" in l}
    missing = [w for w in want if w not in have]
    return {"action": "same" if not missing else "install", "python": ver.strip(), "missing": missing}


def install_venv(repo: str = REPO, sh=None) -> dict:
    sh = sh or _sh
    plan = plan_venv(repo)
    if plan["action"] == "create":
        sh([sys.executable, "-m", "venv", os.path.join(repo, ".venv")])
    if plan["action"] in ("create", "install"):
        sh([os.path.join(repo, ".venv", "bin", "pip"), "install", "-q", "-r", os.path.join(repo, "requirements.txt")], timeout=1800)
    return plan_venv(repo)


def plan_code(repo: str = REPO, box: str = None, sh=None) -> dict:
    sh = sh or _sh
    rc, here = sh(["git", "-C", repo, "rev-parse", "HEAD"])
    out = {"here": here[:12] if rc == 0 else None, "repo": repo}
    if box:
        rc, there = sh(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", box, f"git -C {repo} rev-parse HEAD"])
        out["there"] = there[:12] if rc == 0 else None
        out["action"] = "same" if out["there"] == out["here"] else ("pull" if out["there"] else "unreachable")
    else:
        out["action"] = "same"
    return out


def copy_credentials(box: str, cred_dir: str = CRED_DIR, sh=None) -> dict:
    """Box to box over ssh, never through the repository. The files'
    contents are never read here."""
    sh = sh or _sh
    files = sorted(glob.glob(os.path.join(cred_dir, "*.env")))
    rc, msg = sh(["rsync", "-a", "--chmod=600", *files, f"{box}:{cred_dir}/"], timeout=120)
    return {"files": len(files), "to": box, "ok": rc == 0, "detail": "" if rc == 0 else msg[:200]}


def check(profiles: dict, repo: str = REPO, unit_dir: str = UNIT_DIR, box: str = None) -> dict:
    """The parity report, as plain facts."""
    from support.installer import release
    return {"code": plan_code(repo, box), "venv": plan_venv(repo), "release": release.state(), "units": plan_units(repo, unit_dir),
            "model_server": plan_model_server(), "models": plan_models(profiles),
            "credentials": {"dir": cred_dir_state(), "box": box}}


def cred_dir_state(cred_dir: str = CRED_DIR) -> dict:
    files = sorted(glob.glob(os.path.join(cred_dir, "*.env")))
    return {"present": len(files), "mode_ok": all((os.stat(f).st_mode & 0o077) == 0 for f in files)}


# ── the model server built from source, beside the copy ─────────────────────
# The copy above is the old build's binary, taken as it is. The build here is
# the estate's own, from a clone of the source the old build came from (read,
# never written), at a recorded commit, for the card architecture the box
# reports. Which of the two a card runs is a setting (profiles.toml,
# `[server] binary`), so the choice is a line and not a rewrite.

OLD_LLAMA_SRC = "/home/user/llama.cpp"
QV4_LLAMA_SRC = os.path.join(LIVE, "llama", "src")
QV4_LLAMA_BUILD = os.path.join(LIVE, "llama", "build")
QV4_LLAMA_BUILT_DIR = os.environ.get("QV4_LLAMA_BUILT_DIR") or os.path.join(LIVE, "llama", "built", "bin")
DEFAULT_ARCH = "gfx1201"      # the two R9700s; probed below, this is the fallback the record names as such


def card_arch(sh=None) -> tuple[str, str]:
    """(architecture, how it was found). rocminfo first; then the old build's
    cache (a record of what ran); then the default, named as a guess."""
    sh = sh or _sh
    rc, out = sh(["/opt/rocm/bin/rocminfo"], timeout=30)
    if rc == 0:
        import re
        found = sorted({m.group(1) for m in re.finditer(r"Name:\s+(gfx[0-9a-f]+)", out)})
        if found:
            return found[0], "rocminfo"
    cache = os.path.join(OLD_LLAMA_SRC, "build", "CMakeCache.txt")
    if os.path.exists(cache):
        for line in open(cache, encoding="utf-8", errors="replace"):
            if line.startswith("CMAKE_HIP_ARCHITECTURES:STRING="):
                arch = line.split("=", 1)[1].strip().split(";")[0]
                if arch:
                    return arch, "the old build's CMakeCache"
    return DEFAULT_ARCH, "default (unprobed)"


def cmake_flags(arch: str) -> list[str]:
    """The old build's flags that matter (its CMakeCache, 18 October),
    minus examples and tests: HIP for the one architecture, shared ggml,
    release, native."""
    return ["-DCMAKE_BUILD_TYPE=Release", "-DGGML_HIP=ON", f"-DCMAKE_HIP_ARCHITECTURES={arch}",
            "-DCMAKE_HIP_COMPILER=/opt/rocm/lib/llvm/bin/clang++", "-DBUILD_SHARED_LIBS=ON", "-DGGML_NATIVE=ON",
            "-DLLAMA_BUILD_SERVER=ON", "-DLLAMA_BUILD_TOOLS=ON", "-DLLAMA_BUILD_EXAMPLES=OFF", "-DLLAMA_BUILD_TESTS=OFF",
            "-DLLAMA_CURL=OFF",
            # the binary finds its libraries beside itself ($ORIGIN), so the folder is whole on its own; the copy of
            # the old build carries the old build tree's path and the card manager covers it with LD_LIBRARY_PATH
            "-DCMAKE_BUILD_RPATH_USE_ORIGIN=ON"]


def runpath(binary: str) -> str | None:
    """The library search path baked into a binary (RUNPATH), or None."""
    rc, out = _sh(["readelf", "-d", binary], timeout=30)
    if rc:
        return None
    import re
    m = re.search(r"\((?:RUNPATH|RPATH)\)\s+Library r(?:un)?path:\s+\[([^\]]*)\]", out)
    return m.group(1) if m else ""


def self_contained(binary: str) -> bool:
    """True when the binary looks for its libraries beside itself and
    nowhere in another build tree."""
    rp = runpath(binary)
    if rp is None:
        return False
    parts = [p for p in rp.split(":") if p]
    return any(p.startswith("$ORIGIN") for p in parts) and not any("/build/bin" in p for p in parts)


def plan_source_build(src_dir: str = QV4_LLAMA_SRC, built_dir: str = QV4_LLAMA_BUILT_DIR, source_repo: str = OLD_LLAMA_SRC) -> dict:
    out = {"source_repo": source_repo, "source_present": os.path.isdir(os.path.join(source_repo, ".git")),
           "clone": os.path.isdir(os.path.join(src_dir, ".git")), "built": os.path.exists(os.path.join(built_dir, "llama-server"))}
    rec = os.path.join(built_dir, "VERSION.json")
    if os.path.exists(rec):
        with open(rec, encoding="utf-8") as f:
            out["record"] = json.load(f)
    if out["clone"]:
        rc, head = _sh(["git", "-C", src_dir, "rev-parse", "HEAD"])
        out["clone_commit"] = head[:12] if rc == 0 else None
    out["action"] = "none" if not out["source_present"] else ("same" if out["built"] else "build")
    return out


def build_model_server(source_repo: str = OLD_LLAMA_SRC, ref: str = None, *, src_dir: str = QV4_LLAMA_SRC,
                       build_dir: str = QV4_LLAMA_BUILD, built_dir: str = QV4_LLAMA_BUILT_DIR, jobs: int = None,
                       sh=None, log=print) -> dict:
    """Clone (locally, read-only on the source), configure, build the
    server target, copy the binary and its libraries into `built_dir`
    beside the copy, and record what was built. Returns the record."""
    sh = sh or _sh
    jobs = jobs or max(2, (os.cpu_count() or 4) - 4)
    if not os.path.isdir(os.path.join(source_repo, ".git")):
        return {"action": "none", "why": f"no source checkout at {source_repo}"}
    os.makedirs(os.path.dirname(src_dir), exist_ok=True)
    if not os.path.isdir(os.path.join(src_dir, ".git")):
        log(f"installer: cloning {source_repo} into {src_dir}")
        rc, out = sh(["git", "clone", "--quiet", source_repo, src_dir], timeout=1800)
        if rc:
            return {"action": "failed", "step": "clone", "detail": out[-400:]}
    if ref:
        rc, out = sh(["git", "-C", src_dir, "checkout", "--quiet", ref])
        if rc:
            return {"action": "failed", "step": "checkout", "detail": out[-400:]}
    rc, commit = sh(["git", "-C", src_dir, "rev-parse", "HEAD"])
    rc2, describe = sh(["git", "-C", src_dir, "describe", "--tags", "--always"])
    arch, arch_how = card_arch(sh)
    flags = cmake_flags(arch)
    log(f"installer: configuring for {arch} ({arch_how}) in {build_dir}")
    rc, out = sh(["cmake", "-S", src_dir, "-B", build_dir, *flags], timeout=1800)
    if rc:
        return {"action": "failed", "step": "configure", "detail": out[-1200:]}
    log(f"installer: building llama-server with {jobs} jobs (this takes a while)")
    rc, out = sh(["cmake", "--build", build_dir, "--target", "llama-server", "-j", str(jobs)], timeout=7200)
    if rc:
        return {"action": "failed", "step": "build", "detail": out[-1200:]}
    src_bin = os.path.join(build_dir, "bin")
    os.makedirs(built_dir, exist_ok=True)
    copied = []
    for n in sorted(os.listdir(src_bin)):
        p = os.path.join(src_bin, n)
        if n == "llama-server" or (n.startswith("lib") and ".so" in n):
            q = os.path.join(built_dir, n)
            if os.path.islink(p):
                if os.path.lexists(q):
                    os.unlink(q)
                os.symlink(os.readlink(p), q)
            else:
                shutil.copy2(p, q)
            copied.append(n)
    dst = os.path.join(built_dir, "llama-server")
    rec = {"version": llama_version(dst), "sha256": sha256_file(dst), "from": "source", "source_repo": source_repo,
           "commit": commit.strip(), "describe": describe.strip(), "arch": arch, "arch_from": arch_how, "flags": flags,
           "copied": len(copied), "runpath": runpath(dst), "self_contained": self_contained(dst),
           "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    with open(os.path.join(built_dir, "VERSION.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    log(f"installer: built {rec['version']} at {dst}")
    return {"action": "build", **rec, "to": dst}
