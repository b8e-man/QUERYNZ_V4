"""THE HARDWARE PROFILE, probed never typed (plan step 2.3; the parsers are
carried from ops/fleet/probe.py).

A typed profile goes stale the day hardware changes, and identical code on
two boxes is not identical capability: node1 lacked the page-reading
program and blanked the return totals every night for 17 days with the
board green. So the worker probes its own box at start and on a clock:
cores, memory, each graphics card and its memory, each disk and its free
space, and THE PROGRAMS INSTALLED. The profile is what the queue matches a
job's `requires` against.

Every shell-out is injected so the parsing (the part that gets things
wrong) is tested without a card in the room. A FAILED COMMAND IS NOT DATA:
a non-zero exit with empty output reads exactly like a box with nothing in
it, so it is reported as `None`, never as zero cards.

The two live checks on a model server are carried whole: `served_model`
(what a server says it holds; over 334,763 old calls the model asked for was
the model that answered in 13.8%) and `free_slots` (0 is busy, -1 is
unreachable, and they mean different things).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import socket
import subprocess
import urllib.request

# The programs jobs depend on (docs/baseline.md "Programs the jobs depend on"),
# plus the new estate's own model server (installed beside the old one).
PROGRAMS = ("pdftotext", "pdftoppm", "pdfinfo", "tesseract", "xvfb-run", "google-chrome", "psql", "pg_dump", "gpg",
            "rocm-smi", "llama-server", "qv4-llama-server", "qv4-llama-server-built")
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
QV4_LLAMA = os.environ.get("QV4_LLAMA_SERVER") or os.path.join(LIVE, "llama", "bin", "llama-server")
QV4_LLAMA_BUILT = os.environ.get("QV4_LLAMA_SERVER_BUILT") or os.path.join(LIVE, "llama", "built", "bin", "llama-server")
OLD_LLAMA = "/home/user/llama.cpp/build/bin/llama-server"      # the frozen product's build (baseline); never touched
REAL_FS = {"ext4", "xfs", "btrfs", "ntfs3", "fuseblk", "vfat", "exfat", "f2fs"}


def _sh(cmd: list[str], timeout: int = 20) -> str | None:
    """stdout on success; None on any failure (a failed command is not data)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


# ── the box ──────────────────────────────────────────────────────────────────

def meminfo(text: str = None) -> dict:
    """MemTotal and MemAvailable in GB from /proc/meminfo (available, not
    free: the kernel's own figure for what a new process could take)."""
    if text is None:
        try:
            with open("/proc/meminfo", encoding="utf-8") as f:
                text = f.read()
        except OSError:
            return {}
    out = {}
    for key, name in (("MemTotal", "memory_total_gb"), ("MemAvailable", "memory_available_gb"), ("SwapTotal", "swap_total_gb"),
                      ("SwapFree", "swap_free_gb")):
        m = re.search(rf"^{key}:\s+(\d+) kB", text, re.M)
        if m:
            out[name] = round(int(m.group(1)) / 1024 / 1024, 1)
    return out


def pressure(text: str = None) -> dict:
    """The kernel's memory-pressure figures (/proc/pressure/memory): swap
    fullness says nothing about memory health, these do."""
    if text is None:
        try:
            with open("/proc/pressure/memory", encoding="utf-8") as f:
                text = f.read()
        except OSError:
            return {}
    out = {}
    for line in text.splitlines():
        m = re.match(r"(some|full) avg10=([\d.]+) avg60=([\d.]+)", line)
        if m:
            out[m.group(1)] = {"avg10": float(m.group(2)), "avg60": float(m.group(3))}
    return out


def cards(payload: str = None, run=None) -> list[dict] | None:
    """Each graphics card: index, product, total and used memory in GB, from
    `rocm-smi --showmeminfo vram --showproductname --json`. None when the
    tool failed or is absent (not an empty box)."""
    if payload is None:
        payload = (run or _sh)(["rocm-smi", "--showmeminfo", "vram", "--showproductname", "--json"])
        if payload is None:
            return None
    try:
        body = json.loads(payload)
    except (ValueError, TypeError):
        return None
    if not isinstance(body, dict):
        return None
    out = []
    for key, v in sorted(body.items()):
        m = re.match(r"card(\d+)$", key)
        if not m or not isinstance(v, dict):
            continue
        total = v.get("VRAM Total Memory (B)")
        used = v.get("VRAM Total Used Memory (B)")
        try:
            total_gb = round(int(total) / 1024 ** 3, 1) if total is not None else None
            used_gb = round(int(used) / 1024 ** 3, 1) if used is not None else None
        except (TypeError, ValueError):
            total_gb = used_gb = None
        out.append({"index": int(m.group(1)), "product": v.get("Card Series") or v.get("Card series"),
                    "memory_total_gb": total_gb, "memory_used_gb": used_gb})
    return out


def disks(mounts_text: str = None, usage=None) -> list[dict]:
    """Each real filesystem and its free space."""
    if mounts_text is None:
        try:
            with open("/proc/mounts", encoding="utf-8") as f:
                mounts_text = f.read()
        except OSError:
            return []
    usage = usage or shutil.disk_usage
    out, seen = [], set()
    for line in mounts_text.splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[2] not in REAL_FS or parts[1] in seen:
            continue
        mount = parts[1].replace("\\040", " ")
        try:
            u = usage(mount)
        except OSError:
            continue
        seen.add(parts[1])
        out.append({"mount": mount, "fs": parts[2], "total_gb": round(u.total / 1024 ** 3), "free_gb": round(u.free / 1024 ** 3)})
    return out


def programs(names=PROGRAMS, which=None) -> dict:
    """name → path, or None when absent. `qv4-llama-server` is the new
    estate's own model server at its fixed place, not on the PATH."""
    which = which or shutil.which
    out = {}
    for n in names:
        if n == "qv4-llama-server":
            out[n] = QV4_LLAMA if os.path.exists(QV4_LLAMA) else None
        elif n == "qv4-llama-server-built":
            out[n] = QV4_LLAMA_BUILT if os.path.exists(QV4_LLAMA_BUILT) else None
        elif n == "llama-server":
            out[n] = which(n) or (OLD_LLAMA if os.path.exists(OLD_LLAMA) else None)
        else:
            out[n] = which(n)
    return out


def llama_version(path: str, run=None) -> str | None:
    """`llama-server --version` prints to stderr; the build id is the fact."""
    if not path or not os.path.exists(path):
        return None
    try:
        r = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"version:\s*(\S+)\s*\(([0-9a-f]+)\)", (r.stdout or "") + (r.stderr or ""))
    return f"{m.group(1)} ({m.group(2)})" if m else None


def profile(box: str = None, run=None) -> dict:
    """The whole hardware profile of this box, now."""
    progs = programs()
    return {
        "box": box or socket.gethostname(), "host": socket.gethostname(),
        "probed_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "cores": os.cpu_count(), **meminfo(), "pressure": pressure(),
        "cards": cards(run=run), "disks": disks(), "programs": progs,
        "llama_server": {"old": llama_version(progs.get("llama-server")), "qv4": llama_version(progs.get("qv4-llama-server"))},
        "python": os.sys.version.split()[0],
    }


def missing_programs(prof: dict, requires) -> list[str]:
    """The programs a job requires that this profile lacks."""
    have = prof.get("programs") or {}
    return [r for r in requires if not have.get(r)]


# ── a model server, asked ────────────────────────────────────────────────────

def running_instances(listing: str) -> list[str]:
    """Unit names from `systemctl --user list-units --state=running`; a bare
    template (`x@`) is not an instance."""
    out = []
    for line in listing.splitlines():
        m = re.match(r"\s*\**\s*(\S+)\.service\s", line)
        if m and not m.group(1).endswith("@"):
            out.append(m.group(1))
    return out


def served_model(payload: str | None) -> str | None:
    """The model a server says it holds, from GET /v1/models (llama.cpp
    answers with the `--alias` when one is set)."""
    if not payload:
        return None
    try:
        body = json.loads(payload)
    except (ValueError, TypeError):
        return None
    if not isinstance(body, dict):
        return None
    items = body.get("models") or body.get("data") or []
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        return None
    first = items[0]
    return first.get("name") or first.get("id") or first.get("model") or None


def free_slots(payload: str | None) -> tuple[int, int]:
    """(free, total) from GET /slots. (-1, 0) when it could not be read: -1
    is a server that did not answer (send it nothing); 0 is a live server
    with every slot busy (queue for it)."""
    if not payload:
        return -1, 0
    try:
        slots = json.loads(payload)
    except (ValueError, TypeError):
        return -1, 0
    if not isinstance(slots, list):
        return -1, 0
    return sum(1 for s in slots if isinstance(s, dict) and not s.get("is_processing")), len(slots)


def get(url: str, timeout: float = 5.0) -> str | None:
    """A GET of a loopback model server; None on any failure."""
    if not url.startswith("http://127.0.0.1:") and not url.startswith("http://localhost:"):
        return None
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — a server that is down answers with any of a dozen exceptions
        return None


def ask_server(port: int, getter=None) -> dict:
    """What a local server holds and how busy it is."""
    getter = getter or get
    served = served_model(getter(f"http://127.0.0.1:{port}/v1/models"))
    free, total = free_slots(getter(f"http://127.0.0.1:{port}/slots"))
    healthy = getter(f"http://127.0.0.1:{port}/health")
    return {"port": port, "served": served, "free": free, "total": total, "healthy": healthy is not None}
