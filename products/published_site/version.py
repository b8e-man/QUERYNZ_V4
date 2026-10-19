"""A version folder: written once, never edited (the frozen product's rule,
kept). `<out>/v/<stamp>/` holds `data/…` (the ten kinds, by the path rule)
and `SNAPSHOT.json`, the manifest: the stamp, the template and its
version, the listing the build was pinned to, what was written per kind,
the rows left out for citing a document the listing does not hold, and
the kinds this build does not yet write. A row is appended to
`<out>/RELEASES.jsonl` with action `built` — never `publish`: this
pipeline has no deploy step and flips nothing.

Stdlib only."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil

STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{4}")
MANIFEST = "SNAPSHOT.json"


def stamp_now(now: dt.datetime = None) -> str:
    now = now or dt.datetime.now().astimezone()
    return f"{now:%Y-%m-%dT%H%M}"


def versions_root(out: str) -> str:
    return os.path.join(out, "v")


def write(out: str, stamp: str, files: dict, manifest: dict) -> str:
    """files: {relative path: JSON-able object}. Writes into a temporary
    folder and renames, so a half-written version never exists."""
    if not STAMP.fullmatch(stamp):
        raise ValueError(f"a version is named YYYY-MM-DDTHHMM, not {stamp!r}")
    root = versions_root(out)
    final = os.path.join(root, stamp)
    if os.path.exists(final):
        raise FileExistsError(f"{final} exists: a version is written once and never edited")
    tmp = final + ".tmp"
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    written, total = {}, 0
    for rel, obj in files.items():
        if rel.startswith("/") or ".." in rel.split("/"):
            raise ValueError(f"not a relative path inside the version: {rel}")
        full = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        data = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        with open(full, "wb") as f:
            f.write(data)
        total += len(data)
        kind = rel.split("/")[1] if rel.startswith("data/") else rel
        if kind.endswith(".json"):
            kind = kind[:-5]
        written[kind] = written.get(kind, 0) + 1
    m = dict(manifest)
    m.update({"stamp": stamp, "written": written, "files": len(files), "bytes": total,
              "written_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "deploy": "none: this pipeline stops here"})
    with open(os.path.join(tmp, MANIFEST), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.rename(tmp, final)
    return final


def record(out: str, stamp: str, ok: bool, note: str, gates: list) -> None:
    os.makedirs(out, exist_ok=True)
    row = {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "action": "built" if ok else "refused",
           "version": stamp, "note": note, "gates": gates}
    with open(os.path.join(out, "RELEASES.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def manifest_of(version_dir: str) -> dict:
    with open(os.path.join(version_dir, MANIFEST), encoding="utf-8") as f:
        return json.load(f)


def latest(out: str):
    root = versions_root(out)
    try:
        names = [n for n in os.listdir(root) if STAMP.fullmatch(n) and os.path.isfile(os.path.join(root, n, MANIFEST))]
    except OSError:
        return None
    return os.path.join(root, max(names)) if names else None
