"""The gates a version passes before it is recorded as built. Each returns
(ok, one line); the build stops at the first red and records it. Every
gate reads the written folder, so what is checked is what would be
published.

  snapshot      the manifest and the folder agree both ways; every kind
                the manifest counts is on disk; every file is one of the
                ten kinds or the manifest or an extra; every file parses;
                no factory surface is inside
"""
from __future__ import annotations

import json
import os

from products.published_site import paths, version

FACTORY = ("review", "gold", "identity", "residue", "private", "sealed")


def files_of(root: str) -> list:
    out = []
    for dirpath, dirs, names in os.walk(root):
        dirs.sort()
        for n in sorted(names):
            out.append(os.path.relpath(os.path.join(dirpath, n), root).replace(os.sep, "/"))
    return out


def snapshot(version_dir: str) -> tuple:
    try:
        m = version.manifest_of(version_dir)
    except (OSError, ValueError) as exc:
        return False, f"no readable manifest: {exc}"
    files = [f for f in files_of(version_dir) if f != version.MANIFEST]
    problems = []
    counted = {}
    for rel in files:
        top = rel.split("/")
        if any(seg in FACTORY for seg in top):
            problems.append(f"factory surface inside the version: {rel}")
        kind = paths.kind_of(rel)
        if not kind and not (len(top) == 2 and top[0] == paths.ROOT and top[1][:-5] in paths.EXTRA):
            problems.append(f"not one of the ten kinds: {rel}")
            continue
        name = kind or top[1][:-5]
        counted[name] = counted.get(name, 0) + 1
        try:
            with open(os.path.join(version_dir, rel), encoding="utf-8") as f:
                json.load(f)
        except (OSError, ValueError) as exc:
            problems.append(f"{rel} does not parse: {exc}")
    for kind, n in (m.get("written") or {}).items():
        if counted.get(kind, 0) != n:
            problems.append(f"manifest counts {n} {kind} file(s), the folder holds {counted.get(kind, 0)}")
    for kind, n in counted.items():
        if kind not in (m.get("written") or {}):
            problems.append(f"{n} {kind} file(s) on disk the manifest does not count")
    if m.get("files") != len(files):
        problems.append(f"manifest says {m.get('files')} files, the folder holds {len(files)}")
    if problems:
        return False, f"{len(problems)} problem(s): " + "; ".join(problems[:6])
    return True, f"{len(files)} files in {len(counted)} kinds agree with the manifest"


GATES = [("snapshot", snapshot)]


def run_all(version_dir: str, gates=None) -> list:
    """[(name, ok, line)], stopping at the first red."""
    out = []
    for name, fn in (gates or GATES):
        ok, line = fn(version_dir)
        out.append((name, ok, line))
        if not ok:
            break
    return out
