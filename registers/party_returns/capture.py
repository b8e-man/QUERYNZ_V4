"""How this lane's documents arrive: case 1 of plan 1.10. The old estate
holds the Commission's party returns as captured files under the live old
folder's `var/staging/ec-donations/`: the archive-replay captures in
`archive/` (named `Party-donations-and-loans__<year>-returns__…` and
`2021-annual-returns-__…`) and Arthur's browser download in
`residue/party_returns/<year>/`. Both folders are the bytes as fetched;
`pageread/` and `index/` beside them are derived output and are not
documents. The lane copies each file by hash, read-only, through the one
landing wrapper, and never writes under the old folder.

Scope: the returns for calendar 2017 onward (ruling 364), every party.
Earlier trees are left where they are until a lane needs them.

    candidate_files()          the old paths, sorted
    old_index()                sha256 → old path, for finding a sample item
    copy_all(conn)             land every candidate: [(DocumentRef, old path, new)]
"""
import os
import re

from support.docstore import sha256_file
from support.docstore.landing import copy_from_old

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
FOLDER = os.path.join(OLD_LIVE, "var", "staging", "ec-donations")
ARCHIVE = re.compile(r"^(Party-donations-and-loans__(2018|2019|2020|2021)-returns__|2021-annual-returns-__).*\.pdf$", re.I)
SOURCE = "party_returns"
FIRST_YEAR = 2017                   # ruling 364: the returns for calendar 2017 onward


def candidate_files(folder: str = None) -> list:
    folder = folder or FOLDER
    out = []
    archive = os.path.join(folder, "archive")
    if os.path.isdir(archive):
        out += [os.path.join(archive, f) for f in os.listdir(archive) if ARCHIVE.match(f)]
    residue = os.path.join(folder, "residue", "party_returns")
    for dirpath, dirs, files in os.walk(residue):
        dirs.sort()
        out += [os.path.join(dirpath, f) for f in files if f.lower().endswith(".pdf")]
    return sorted(out)


def old_index(folder: str = None) -> dict:
    return {sha256_file(p): p for p in candidate_files(folder)}


def copy_all(conn, folder: str = None, log=None) -> list:
    out = []
    for path in candidate_files(folder):
        ref, new = copy_from_old(path, SOURCE, conn)
        out.append((ref, path, new))
        if log:
            log(f"party_returns: {'landed' if new else 'held'} {ref.sha256[:12]} {os.path.basename(path)}")
    return out
