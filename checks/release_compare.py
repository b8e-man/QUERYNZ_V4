"""Compare two versions of the frozen site file by file (plan step 1.4,
items 2 and 4; step 4.5 builds on it).

A version is a folder under `var/pi-snapshot/v/` in the live old folder.
Every file is compared by content; the result is grouped by the kind of page
data (`data/<kind>/`, or the top folder for everything else) with counts of
same, changed, added and removed files, and for changed JSON files the
top-level keys whose values differ, so "what always changes" can be read off
and "anything beyond that" seen.

    python -m checks.release_compare 2026-10-16T0616 2026-10-17T0616

Read-only: it never writes into the old folder. Stdlib only.
Tests: checks/tests/test_release_compare.py."""
import hashlib
import json
import os
import sys
from collections import defaultdict

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
VERSIONS = os.path.join(OLD_LIVE, "var", "pi-snapshot", "v")


def kind_of(rel: str) -> str:
    parts = rel.split("/")
    if parts[0] == "data" and len(parts) > 2:
        return "data/" + parts[1]
    if parts[0] == "data":
        return "data/" + parts[1]          # a top-level data file, named
    return parts[0] if len(parts) > 1 else "(root)"


def files_of(root: str) -> dict:
    out = {}
    for dirpath, dirs, names in os.walk(root):
        dirs.sort()
        for n in names:
            full = os.path.join(dirpath, n)
            if os.path.isfile(full) and not os.path.islink(full):
                out[os.path.relpath(full, root)] = full
    return out


def digest(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def json_key_diff(a: str, b: str):
    """Top-level keys whose values differ between two JSON files, or None
    when either is not a JSON object."""
    try:
        with open(a, encoding="utf-8") as f:
            da = json.load(f)
        with open(b, encoding="utf-8") as f:
            db = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(da, dict) or not isinstance(db, dict):
        return ["(not an object)"]
    keys = sorted(set(da) | set(db))
    return [k for k in keys if da.get(k) != db.get(k)]


def compare(a_root: str, b_root: str, sample_per_kind: int = 25) -> dict:
    fa, fb = files_of(a_root), files_of(b_root)
    kinds = defaultdict(lambda: {"same": 0, "changed": 0, "added": 0, "removed": 0,
                                 "changed_keys": defaultdict(int), "changed_sample": [],
                                 "added_sample": [], "removed_sample": []})
    for rel in sorted(set(fa) | set(fb)):
        k = kinds[kind_of(rel)]
        if rel in fa and rel in fb:
            if digest(fa[rel]) == digest(fb[rel]):
                k["same"] += 1
            else:
                k["changed"] += 1
                if len(k["changed_sample"]) < sample_per_kind:
                    k["changed_sample"].append(rel)
                    if rel.endswith(".json"):
                        for key in json_key_diff(fa[rel], fb[rel]) or []:
                            k["changed_keys"][key] += 1
        elif rel in fb:
            k["added"] += 1
            if len(k["added_sample"]) < 5:
                k["added_sample"].append(rel)
        else:
            k["removed"] += 1
            if len(k["removed_sample"]) < 5:
                k["removed_sample"].append(rel)
    out = {}
    for name, k in sorted(kinds.items()):
        k["changed_keys"] = dict(sorted(k["changed_keys"].items(), key=lambda kv: -kv[1]))
        out[name] = dict(k)
    return {"a": a_root, "b": b_root, "files_a": len(fa), "files_b": len(fb), "kinds": out}


def render(r: dict) -> str:
    lines = [f"{os.path.basename(r['a'])} ({r['files_a']} files) -> {os.path.basename(r['b'])} ({r['files_b']} files)",
             f"{'kind':<24} {'same':>6} {'chg':>6} {'add':>6} {'rem':>6}  changed keys (sampled)"]
    for name, k in r["kinds"].items():
        keys = ", ".join(f"{kk}:{n}" for kk, n in list(k["changed_keys"].items())[:6])
        lines.append(f"{name:<24} {k['same']:>6} {k['changed']:>6} {k['added']:>6} {k['removed']:>6}  {keys}")
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print("usage: python -m checks.release_compare <version-a> <version-b>")
        return 2
    a, b = (v if os.path.isdir(v) else os.path.join(VERSIONS, v) for v in argv)
    r = compare(a, b)
    print(render(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
