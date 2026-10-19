"""The inputs a build is pinned to (plan 4.5, "Same inputs").

At each frozen release the watcher (checks/frozen_product.py) records the
version's name and a listing, by path and sha256, of the captured-document
folders the old estate built from. A build here names one such listing and
reads it into a set of document hashes. Every published row cites its
document by hash, so a row whose document is not in the listing arrived
after that release and is left out of the version; the version's manifest
records which listing it was built from and how many rows were left out
for that reason. So the comparison with the frozen site counts no timing
difference, and a day's version can be rebuilt later from the same listing.

    listing_path(version) -> str
    load(path) -> Listing       header (version, listed_at, files, bytes), hashes (set), folders ({top folder: n})
    latest(folder) -> str|None  the newest listing's version name

Stdlib only; reads the watcher's state folder, never the old folder.
"""
import json
import os
from collections import Counter
from dataclasses import dataclass, field

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
LISTINGS = os.path.join(LIVE, "checks", "frozen-product", "listings")


@dataclass
class Listing:
    version: str
    listed_at: str
    root: str
    files: int
    bytes: int
    hashes: frozenset
    folders: dict = field(default_factory=dict)
    path: str = ""

    def holds(self, sha256) -> bool:
        return bool(sha256) and sha256 in self.hashes


def listing_path(version: str, folder: str = None) -> str:
    return os.path.join(folder or LISTINGS, f"{version}.jsonl")


def versions(folder: str = None) -> list:
    folder = folder or LISTINGS
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    return sorted(n[:-6] for n in names if n.endswith(".jsonl"))


def latest(folder: str = None):
    v = versions(folder)
    return v[-1] if v else None


def load(path: str) -> Listing:
    hashes = set()
    folders = Counter()
    with open(path, encoding="utf-8") as f:
        head = json.loads(f.readline())
        if "version" not in head or "files" not in head:
            raise ValueError(f"{path}: not a release listing (no header line)")
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            hashes.add(r["sha256"])
            folders[r["path"].split("/")[0]] += 1
    n = sum(folders.values())
    if n != int(head["files"]):
        raise ValueError(f"{path}: the header says {head['files']} files but {n} are listed")
    return Listing(version=head["version"], listed_at=head.get("listed_at", ""), root=head.get("root", ""),
                   files=n, bytes=int(head.get("bytes", 0)), hashes=frozenset(hashes), folders=dict(folders), path=path)
