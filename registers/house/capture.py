"""How this lane's documents arrive (plan 1.10, case 1: the file is held).
Nothing is fetched (step 4.1).

The old estate holds the Commission's files under the live old folder's
`var/staging/`:

  ec-candidate-list/   the 2026 nominations: the electorate candidates
                       workbook, the party lists as vote.nz prints them and
                       as the Commission's PDF, and the release that states
                       the counts (its MANIFEST.jsonl dates each capture)
  ec-results/pages/    the official results of the 2020 and 2023 general
                       elections: overall, electorate status, successful
                       candidates, and the 72 electorate pages of each
                       (`state.json` dates each capture)
  ec-byelections/      the results site's index of elections, and the
                       by-election pages the old job could read

and Stats NZ's 2020 electorate files under `boundaries/` (general and
Māori), whose name fields are the names the electorates join to. Only the
names are read; the shapes are held, not used. The 2025 boundaries that the
2026 election is fought on are not held; their download needs a key that
is Arthur's to place (card).

Every file is copied by hash, read-only, through the landing wrapper. A
page the results site answered with a challenge or a "Not Found" is a
failed read: it is landed (it is what the old job captured) and recorded
in the catch log, never read for rows. The old job's manifests are its
records, not documents.

    held_files(roots)     [(folder, relative name, old path)] in a fixed order
    captured_on(folder, name, sha256, roots)   when the old job fetched it, by its record
    copy_all(conn)        land everything: ([(folder, DocumentRef, name, captured at)], [(item, why)])
"""
import datetime as dt
import json
import os

from support.docstore.landing import copy_from_old

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
STAGING = os.path.join(OLD_LIVE, "var", "staging")
SOURCE = "house"

#: folder → the files of it this lane takes (None: every file but the job's own record)
FOLDERS = {
    "ec-candidate-list": None,
    "ec-results": None,
    "ec-byelections": None,
    "boundaries": ("general-2020.geojson", "maori-2020.geojson"),
}
RECORDS = ("MANIFEST.jsonl", "state.json")


def roots(staging: str = None) -> dict:
    staging = staging or STAGING
    return {f: os.path.join(staging, f) for f in FOLDERS}


def held_files(where: dict = None) -> list:
    where = where or roots()
    out = []
    for folder, only in FOLDERS.items():
        base = where[folder]
        if only is not None:
            out += [(folder, n, os.path.join(base, n)) for n in only if os.path.isfile(os.path.join(base, n))]
            continue
        for dirpath, dirs, files in os.walk(base):
            dirs.sort()
            for n in sorted(files):
                if n in RECORDS or n.endswith((".tmp", ".part")):
                    continue
                p = os.path.join(dirpath, n)
                out.append((folder, os.path.relpath(p, base), p))
    return out


def _records(folder: str, where: dict) -> dict:
    """The old job's own record of each capture: file name → (sha256 or None, fetched at, source address)."""
    base = where[folder]
    out = {}
    man = os.path.join(base, "MANIFEST.jsonl")
    if os.path.isfile(man):
        with open(man, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    m = json.loads(line)
                    out[m.get("file")] = (m.get("sha256"), m.get("fetched_at"), m.get("source"))
    state = os.path.join(base, "state.json")
    if os.path.isfile(state):
        with open(state, encoding="utf-8") as f:
            for url, d in (json.load(f).get("done") or {}).items():
                out[os.path.join("pages", d.get("file") or "")] = (None, d.get("at"), url)
    return out


def captured_on(folder: str, name: str, sha256: str, where: dict = None):
    """When the old job fetched these bytes, as local time, by its record;
    None where it keeps none (or records other bytes under the name)."""
    rec = _records(folder, where or roots()).get(name)
    if not rec or not rec[1] or (rec[0] and rec[0] != sha256):
        return None
    return dt.datetime.fromisoformat(rec[1]).astimezone().isoformat(timespec="seconds")


def source_of(folder: str, name: str, where: dict = None):
    rec = _records(folder, where or roots()).get(name)
    return rec[2] if rec else None


def copy_all(conn, where: dict = None, log=None) -> tuple:
    """Every held file copied by hash. Returns ([(folder, DocumentRef, name,
    captured at)], [(item, why)]); the second list is what the old job's
    records name and the folder no longer holds."""
    where = where or roots()
    landed, aside = [], []
    held = set()
    for folder, name, path in held_files(where):
        ref, new = copy_from_old(path, SOURCE, conn)
        held.add((folder, name))
        landed.append((folder, ref, name, captured_on(folder, name, ref.sha256, where) or ref.fetched_at))
        if log:
            log(f"house: {'landed' if new else 'held'} {ref.sha256[:12]} {folder}/{name}")
    for folder in FOLDERS:
        for name, (sha, _, url) in _records(folder, where).items():
            if (folder, name) not in held:
                aside.append((f"{folder}/{name}", f"the old job's record lists {url}; the folder does not hold it"))
    return landed, aside
