"""THE INSTALLER (plan step 2.11): one installer puts the same code, job
files and model files on every box, and copies the credential files from
box to box directly, never through the repository.

Six steps, each a plan before it is an action:

  code          the checkout on the box is the main checkout at a commit;
                another box pulls the same commit (git), never a copy by hand
  venv          `.venv` from requirements.txt, the same Python on every box
  units         every `qv4-*.service` and `qv4-*.timer` the repository ships
                (`checks/jobs/`, `support/*/units/`) into the user unit
                folder. ONLY THE PREFIX: a file without `qv4-` is refused as
                a source and never touched as a target (hard limit 23). A
                stale `qv4-` unit the repository no longer ships is reported,
                not removed. The worker instance for this box is enabled.
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
UNIT_GLOBS = ("checks/jobs/qv4-*.service", "checks/jobs/qv4-*.timer", "support/*/units/qv4-*.service", "support/*/units/qv4-*.timer")


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
    for folder in ("checks/jobs", *glob.glob(os.path.join(repo, "support", "*", "units"))):
        d = folder if os.path.isabs(folder) else os.path.join(repo, folder)
        for n in os.listdir(d) if os.path.isdir(d) else []:
            if (n.endswith(".service") or n.endswith(".timer")) and not n.startswith(PREFIX):
                bad.append(os.path.join(d, n))
    if bad:
        raise ValueError(f"unit files without the {PREFIX} prefix are not installed by this estate (hard limit 23): {bad}")
    return out


def plan_units(repo: str = REPO, unit_dir: str = UNIT_DIR) -> list[dict]:
    """What installing would do: install, update, same, or stale (on the
    box, not in the repository; reported, never removed)."""
    src = unit_sources(repo)
    out = []
    for name, path in src.items():
        target = os.path.join(unit_dir, name)
        if not os.path.exists(target):
            out.append({"unit": name, "action": "install"})
        elif sha256_file(target) != sha256_file(path):
            out.append({"unit": name, "action": "update"})
        else:
            out.append({"unit": name, "action": "same"})
    for n in sorted(os.listdir(unit_dir)) if os.path.isdir(unit_dir) else []:
        if n.startswith(PREFIX) and (n.endswith(".service") or n.endswith(".timer")) and n not in src:
            out.append({"unit": n, "action": "stale"})
    return out


def install_units(repo: str = REPO, unit_dir: str = UNIT_DIR, box: str = None, sh=None, enable: bool = True) -> list[dict]:
    """Copy the shipped units in, reload, enable the timers and this box's
    worker. Touches nothing without the prefix."""
    sh = sh or _sh
    done = []
    for step in plan_units(repo, unit_dir):
        name = step["unit"]
        if not name.startswith(PREFIX):          # belt and braces: never a foreign unit
            continue
        if step["action"] in ("install", "update"):
            os.makedirs(unit_dir, exist_ok=True)
            shutil.copyfile(unit_sources(repo)[name], os.path.join(unit_dir, name))
            done.append(step)
    if done:
        sh(["systemctl", "--user", "daemon-reload"])
    if enable:
        for name in unit_sources(repo):
            if name.endswith(".timer"):
                sh(["systemctl", "--user", "enable", "--now", name])
        if "qv4-worker@.service" in unit_sources(repo):
            inst = f"qv4-worker@{box or os.uname().nodename}.service"
            sh(["systemctl", "--user", "enable", "--now", inst])
            done.append({"unit": inst, "action": "enabled"})
    return done


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
        return {"action": "same", "version": llama_version(dst), "at": dst}
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
    return {"code": plan_code(repo, box), "venv": plan_venv(repo), "units": plan_units(repo, unit_dir),
            "model_server": plan_model_server(), "models": plan_models(profiles),
            "credentials": {"dir": cred_dir_state(), "box": box}}


def cred_dir_state(cred_dir: str = CRED_DIR) -> dict:
    files = sorted(glob.glob(os.path.join(cred_dir, "*.env")))
    return {"present": len(files), "mode_ok": all((os.stat(f).st_mode & 0o077) == 0 for f in files)}
