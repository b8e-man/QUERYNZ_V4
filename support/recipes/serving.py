"""How a model is served, as one identity a reading can carry (Arthur, 26 November 2026: the reader configuration —
"27b 4 bit on one card using radiance, or qwen flash next on a whole node, along with concurrency information" —
recorded against the records it produces; tranche 1 of the reader-configuration system, support/recipes/README.md).

A serving record is what actually runs, read from the box, never from the catalogue alone (lesson: "a setting that
must agree across units has one home and one writer — and an arm that asks the units, not the file"):

- a standing server (Radiance under its unit): the installed unit files as systemd runs them (the unit, and every
  unit it Requires=, comments left out, ${VAR} filled from the unit's own Environment= lines and the box's
  EnvironmentFile; only QV4_ names, never one that names a key, token, password or secret: hard limit 1), the
  container image by its image id as podman holds it (not the repository digest: node1's copy of the one image
  came by save and load and carries another digest, 26 November 2026), and the weights by their recorded sha256;
- a server the worker starts (llama-server): its argv with the card's port left out, the program's sha256, and the
  weights by their recorded sha256.

`serving_id` is the first 16 hex of the sha256 of the record's canonical JSON. Every new record is appended to
`<live>/recipes/servings.jsonl` (append-only; never edited), so an id always resolves to what it meant. Weights are
hashed once, by `python -m support.recipes.serving weights`, into `support/recipes/weights.jsonl` (model weights are
records); a file not in that ledger is named as unhashed in the record, never silently passed.

    python -m support.recipes.serving weights [--write]   hash every profile's weights on this box
    python -m support.recipes.serving show                 the serving record of every standing server here
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys

from support import appendline

HERE = os.path.dirname(os.path.abspath(__file__))
WEIGHTS = os.path.join(HERE, "weights.jsonl")
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
LEDGER = os.path.join(LIVE, "recipes", "servings.jsonl")
UNIT_DIR = os.environ.get("QV4_UNIT_DIR") or os.path.expanduser("~/.config/systemd/user")
MODELS = os.environ.get("QV4_MODELS") or "/home/user/models"
UNHASHED = "unhashed"
UNMEASURED = "unmeasured"     # a serving id that could not be worked out begins with this, and says why


# ── weights ──────────────────────────────────────────────────────────────────

def weights_ledger(path: str = None) -> dict:
    """(file, size) → sha256, from the weights ledger; the last line for a pair wins."""
    out = {}
    try:
        with open(path or WEIGHTS, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    out[(r["file"], int(r["size"]))] = r["sha256"]
    except FileNotFoundError:
        pass
    return out


def weight_id(file: str, models_dir: str = None, ledger: dict = None) -> dict:
    """{file, size, sha256}: the profile's weights file (relative to the models folder) by its recorded hash; sha256 is
    UNHASHED when the ledger has no line for this file at this size, and None when the file is not here."""
    p = os.path.join(models_dir or MODELS, file)
    try:
        size = os.path.getsize(p)
    except OSError:
        return {"file": file, "size": None, "sha256": None}
    sha = (ledger if ledger is not None else weights_ledger()).get((file, size))
    return {"file": file, "size": size, "sha256": sha or UNHASHED}


def sha256_file(path: str, chunk: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# ── units ────────────────────────────────────────────────────────────────────

def _unit_lines(text: str) -> list[str]:
    """The unit's lines as systemd reads them: comments and blank lines left out, continuations joined."""
    out, cur = [], ""
    for raw in text.splitlines():
        line = raw.strip()
        if not cur and (not line or line.startswith(("#", ";"))):
            continue
        if cur and line.startswith(("#", ";")):
            continue
        if line.endswith("\\"):
            cur += line[:-1].strip() + " "
            continue
        out.append((cur + line).strip())
        cur = ""
    if cur:
        out.append(cur.strip())
    return out


def _env_file(path: str) -> dict:
    out = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def unit_record(name: str, unit_dir: str = None, box: str = None, instance: str = None) -> dict:
    """One installed unit, as it runs: {unit, lines, env}. A template (`x@.service`) is read for `instance`, %i filled;
    %H is the box; ${VAR} is filled from the unit's Environment= lines, then its EnvironmentFile (which wins)."""
    box = box or os.uname().nodename
    path = os.path.join(unit_dir or UNIT_DIR, name)
    with open(path, encoding="utf-8") as f:
        lines = _unit_lines(f.read())
    env = {}
    for l in lines:
        if l.startswith("Environment="):
            for tok in shlex.split(l[len("Environment="):]):
                k, _, v = tok.partition("=")
                env[k] = v
    for l in lines:
        if l.startswith("EnvironmentFile="):
            env.update(_env_file(l[len("EnvironmentFile="):].lstrip("-").replace("%H", box)))
    filled = []
    for l in lines:
        if l.startswith("Environment="):
            l = "Environment=" + " ".join(t if _fillable(t.partition("=")[0]) else f"{t.partition('=')[0]}=<withheld>"
                                          for t in shlex.split(l[len("Environment="):]))
        if instance is not None:
            l = l.replace("%i", instance)
        # %H stays as written: the box's own environment file is read into `env`, so one serving reads the same
        # on both boxes and carries one id
        l = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", lambda m: env.get(m.group(1), m.group(0)) if _fillable(m.group(1))
                   else m.group(0), l)
        filled.append(l)
    return {"unit": name if instance is None else name.replace("@.", f"@{instance}."), "lines": filled,
            "env": {k: v for k, v in sorted(env.items()) if _fillable(k)}}


_SECRET = re.compile(r"KEY|TOKEN|PASSWORD|SECRET|PASS\b", re.I)


def _fillable(name: str) -> bool:
    """A variable the record may carry: a QV4_ name that does not name a credential (hard limit 1)."""
    return name.startswith("QV4_") and not _SECRET.search(name)


def required_units(rec: dict) -> list[str]:
    out = []
    for l in rec["lines"]:
        if l.startswith("Requires="):
            out += l[len("Requires="):].split()
    return out


def images_of(rec: dict) -> list[str]:
    """The container images a unit's `podman run` names."""
    out = []
    for l in rec["lines"]:
        if l.startswith("ExecStart=") and "podman" in l and " run " in f" {l} ":
            out += [t for t in shlex.split(l[len("ExecStart="):]) if re.match(r"^[a-z0-9.-]+\.[a-z]+/[\w./-]+:[\w.-]+$", t)]
    return out


def image_digest(image: str, run=subprocess.run) -> str | None:
    """The image's id (sha256 of its configuration), which one image keeps on every box however it was copied."""
    try:
        r = run(["podman", "image", "inspect", "--format", "{{.Id}}", image], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() or None if r.returncode == 0 else None


# ── the record and its id ────────────────────────────────────────────────────

def canonical(rec: dict) -> str:
    return json.dumps(rec, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def serving_id(rec: dict) -> str:
    return hashlib.sha256(canonical(rec).encode()).hexdigest()[:16]


def standing(prof, unit_dir: str = None, box: str = None, models_dir: str = None, digest=image_digest,
             ledger: dict = None) -> dict:
    """The serving record of a standing profile on this box: its unit and every unit it requires (a template for each
    instance it names), each image by digest, and the weights by hash."""
    top = unit_record(prof.unit, unit_dir, box)
    units = [top]
    for req in required_units(top):
        m = re.match(r"^(.+)@(.+)\.service$", req)
        units.append(unit_record(f"{m.group(1)}@.service", unit_dir, box, instance=m.group(2)) if m
                     else unit_record(req, unit_dir, box))
    images = sorted({i for u in units for i in images_of(u)})
    return {"kind": "standing", "profile": prof.name, "model": prof.model, "binary": prof.binary,
            "units": units, "images": {i: digest(i) for i in images},
            "weights": [weight_id(w, models_dir, ledger) for w in prof.weights], "cards": prof.cards, "slots": prof.slots,
            "context": prof.context}


def spawned(prof, argv: list[str], binary: str, models_dir: str = None, ledger: dict = None, program_sha=None) -> dict:
    """The serving record of a server the worker starts: argv with the port's value left out (it names the card's
    port, not how the model is served), the program by sha256, the weights by hash."""
    a = list(argv)
    if "--port" in a:
        i = a.index("--port")
        a[i + 1] = "<port>"
    return {"kind": "spawned", "profile": prof.name, "model": prof.model, "binary": prof.binary,
            "argv": a[1:], "program": (program_sha or _program_sha)(binary),
            "weights": [weight_id(w, models_dir, ledger) for w in prof.weights], "slots": prof.slots, "context": prof.context}


_PROGRAMS: dict = {}


def _program_sha(path: str) -> str | None:
    try:
        st = os.stat(path)
    except OSError:
        return None
    key = (path, st.st_size, st.st_mtime_ns)
    if key not in _PROGRAMS:
        _PROGRAMS[key] = sha256_file(path)
    return _PROGRAMS[key]


def record(rec: dict, ledger: str = None, box: str = None) -> str:
    """The record's id, appended to the servings ledger the first time this process sees it."""
    sid = serving_id(rec)
    path = ledger or LEDGER
    if (path, sid) not in _RECORDED:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not _in_ledger(path, sid):
            appendline.append_json(path, {"serving_id": sid, "box": box or os.uname().nodename, "record": rec},
                                   ensure_ascii=False, sort_keys=True)
        _RECORDED.add((path, sid))
    return sid


_RECORDED: set = set()


def _in_ledger(path: str, sid: str) -> bool:
    try:
        with open(path, encoding="utf-8") as f:
            return any(f'"serving_id": "{sid}"' in line for line in f)
    except FileNotFoundError:
        return False


def resolve(sid: str, ledger: str = None) -> dict | None:
    """What a serving id meant: its first record in the ledger."""
    try:
        with open(ledger or LEDGER, encoding="utf-8") as f:
            for line in f:
                if f'"serving_id": "{sid}"' in line:
                    return json.loads(line)
    except FileNotFoundError:
        pass
    return None


# ── the command ──────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=("weights", "show"))
    ap.add_argument("--write", action="store_true", help="append new weight hashes to the ledger (main checkout)")
    a = ap.parse_args(argv)
    from support.scheduler import registry as reg
    profs = reg.profiles()
    if a.what == "weights":
        have = weights_ledger()
        files = sorted({w for p in profs.values() for w in p.weights})
        for file in files:
            p = os.path.join(MODELS, file)
            if not os.path.exists(p):
                continue
            size = os.path.getsize(p)
            if (file, size) in have:
                print(f"{file}: recorded")
                continue
            line = {"file": file, "size": size, "sha256": sha256_file(p)}
            print(json.dumps(line))
            if a.write:
                appendline.append_json(WEIGHTS, line, sort_keys=True)
        return 0
    for p in profs.values():
        if p.standing:
            try:
                rec = standing(p)
            except OSError as e:
                print(f"{p.name}: {e}")
                continue
            print(p.name, serving_id(rec), json.dumps({"images": rec["images"], "weights": rec["weights"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
