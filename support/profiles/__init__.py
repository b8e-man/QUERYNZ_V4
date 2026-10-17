"""The document profile's contract (plan 1.9; docs/contracts/document-profile.md).

A document profile describes one kind of document: how to recognise it
(by shape, measured without reading: page count, text-layer presence,
image pages, landmarks), which pages need the page reader, how its tables
are laid out, and the prompt and checks the reader runs. A reading is made
FROM a profile and is stamped with the profile's slug and version, so a
profile is never edited: a new version is a new line in `profiles.jsonl`,
one higher, and every old version stays readable.

Fields (the old estate's, kept): kind, slug, version, at, by, title,
recognise, signals, ocr, tables, prompt, notes, role, applies_to, tooling,
config, process, gates, on_fail. `recognise` and `signals` are the
recognition markers the plan asks for before a reader is built
(memory: profiles before readers).

    current()            slug → the newest version of every profile
    profile(slug)        the newest version of one
    history(slug)        every version, oldest first
    add_version(slug, fields, by)   append the next version; never edit
"""
import datetime as dt
import json
import os

PROFILES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.jsonl")
FIELDS = ("title", "recognise", "signals", "signals_note", "ocr", "tables", "prompt", "notes", "role",
          "applies_to", "tooling", "config", "process", "gates", "on_fail")
KIND = "document-profile"


def _read(path: str = None) -> list:
    out = []
    try:
        with open(path or PROFILES, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    except OSError:
        return []
    return out


def history(slug: str, path: str = None) -> list:
    rows = [r for r in _read(path) if r.get("slug") == slug and r.get("kind") == KIND]
    return sorted(rows, key=lambda r: int(r.get("version") or 0))


def current(path: str = None) -> dict:
    """The newest version of every slug, by version and not by position in
    the file (the ledger is append-only and may be restored out of order)."""
    out = {}
    for r in _read(path):
        if r.get("kind") != KIND:
            continue
        cur = out.get(r["slug"])
        if cur is None or int(r.get("version") or 0) >= int(cur.get("version") or 0):
            out[r["slug"]] = r
    return out


def profile(slug: str, path: str = None):
    return current(path).get(slug)


def valid_slug(slug: str) -> bool:
    return bool(slug) and all(ch.isalnum() or ch in "-_" for ch in slug) and slug == slug.lower()


def add_version(slug: str, fields: dict, by: str, path: str = None, at: str = None) -> dict:
    """Append the next version of `slug`. The version is read at write time,
    so two writers cannot both write version 3. Nothing is ever edited."""
    if not valid_slug(slug):
        raise ValueError("a profile slug is lower-case letters, digits, - and _")
    if not by:
        raise ValueError("a version says who made it")
    path = path or PROFILES
    have = history(slug, path)
    rec = {"kind": KIND, "slug": slug, "version": (int(have[-1]["version"]) if have else 0) + 1,
           "at": at or dt.datetime.now().astimezone().isoformat(timespec="seconds"), "by": by}
    for k in FIELDS:
        rec[k] = fields.get(k)
    for k, v in fields.items():
        rec.setdefault(k, v)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec
