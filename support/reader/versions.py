"""Every reader's version string held to its code (Arthur, 15 November 2026: "do we have reader versions tracked so we
can identify which version of the reader was used to extract which documents?").

A reader names itself in a module constant, `READER = "registers.courts.model_read 3"`, which goes into each reading
it stores (support.reader.Reading.reader) and each row of docs.extractions. It is raised by hand, so it drifted: on 14
November the grants readers changed twice and kept "1". This file holds, per module that defines READER, its string
and a sha256 of its code (the module and the lane's own modules it imports); `tests/test_reader_versions.py` fails
when the code changed and the string did not. Each stored reading also carries the commit it was made at
(support.reader.code_commit), which needs no hand.

    python -m support.reader.versions            what has drifted (exit 1 when anything has)
    python -m support.reader.versions --update   record the current strings and hashes; refuses an entry whose code
                                                 changed under the same string (bump its READER first)
"""
import argparse
import ast
import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(REPO, "support", "reader", "versions.json")
ROOTS = ("registers", "support", "links")
_READER = re.compile(r'^READER\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', re.M)


def readers(repo: str = REPO) -> dict:
    """relative path -> its READER string, for every module (not a test) that defines one."""
    out = {}
    for root in ROOTS:
        for d, dirs, files in os.walk(os.path.join(repo, root)):
            dirs[:] = [x for x in dirs if x not in ("tests", "__pycache__")]
            for n in files:
                if n.endswith(".py"):
                    p = os.path.join(d, n)
                    m = _READER.search(open(p, encoding="utf-8").read())
                    if m:
                        out[os.path.relpath(p, repo)] = ast.literal_eval(m.group(1))
    return dict(sorted(out.items()))


def deps(rel: str, repo: str = REPO) -> list:
    """The module and the modules of its own package it imports (one level): what its reading depends on here."""
    pkg = os.path.dirname(rel)
    dotted = pkg.replace(os.sep, ".")
    tree = ast.parse(open(os.path.join(repo, rel), encoding="utf-8").read())
    found = {rel}
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level == 1:
                mod = dotted + ("." + mod if mod else "")
            if mod == dotted:
                names = [f"{dotted}.{a.name}" for a in node.names]
            elif mod.startswith(dotted + "."):
                names = [mod]
        elif isinstance(node, ast.Import):
            names = [a.name for a in node.names if a.name.startswith(dotted + ".")]
        for name in names:
            p = os.path.join(*name.split(".")) + ".py"
            if os.path.exists(os.path.join(repo, p)):
                found.add(p)
    return sorted(found)


def digest(files: list, repo: str = REPO) -> str:
    h = hashlib.sha256()
    for f in files:
        h.update(f.encode() + b"\0" + open(os.path.join(repo, f), "rb").read() + b"\0")
    return h.hexdigest()


def current(repo: str = REPO) -> dict:
    out = {}
    for rel, reader in readers(repo).items():
        files = deps(rel, repo)
        out[rel] = {"reader": reader, "files": files, "sha256": digest(files, repo)}
    return out


def load(path: str = None) -> dict:
    try:
        with open(path or MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return {}


def drift(now: dict, recorded: dict) -> dict:
    """{"bump": [modules whose code changed under the same READER], "record": [new, renamed or re-versioned modules the
    manifest does not hold as they are], "gone": [modules in the manifest that define no READER now]}."""
    bump, record = [], []
    for rel, x in now.items():
        r = recorded.get(rel)
        if r is None or r["reader"] != x["reader"]:
            record.append(rel)
        elif r["sha256"] != x["sha256"]:
            bump.append(rel)
    return {"bump": bump, "record": record, "gone": sorted(set(recorded) - set(now))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--update", action="store_true")
    a = ap.parse_args(argv)
    now, rec = current(), load()
    d = drift(now, rec)
    for rel in d["bump"]:
        print(f"bump READER in {rel}: its code changed, its string {now[rel]['reader']!r} did not")
    if not a.update:
        for rel in d["record"]:
            print(f"record {rel} ({now[rel]['reader']!r}): run python -m support.reader.versions --update")
        for rel in d["gone"]:
            print(f"gone: {rel}")
        return 1 if any(d.values()) else 0
    if d["bump"]:
        print("versions: nothing written; bump each READER above first")
        return 1
    with open(MANIFEST + ".tmp", "w", encoding="utf-8") as f:
        json.dump(now, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(MANIFEST + ".tmp", MANIFEST)
    print(f"versions: {len(now)} readers recorded in {os.path.relpath(MANIFEST, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
