"""How this lane's documents arrive: case 1 of plan 1.10. Nothing is fetched.

The old estate's party-boards capture (DL-10, 2 and 3 September 2026) holds
each party's governance pages under the live old folder's
`var/staging/party-boards/`: `archive/<party>/<timestamp>__<hash16>.html`,
one file per snapshot, either the Internet Archive's copy of the party's own
page (`kind` wayback, the timestamp is the Archive's) or the old job's own
read of the live page (`kind` current, the timestamp is the fetch). Its
`MANIFEST.jsonl` says, per file, the party, the page's own address, the kind,
the timestamp and the sha256; it also records the robots reads and 366
attempts that landed no file, which are not documents. 1,061 files in the
frozen site's listing: the manifest and 1,060 pages (1,058 distinct bytes:
two pages were archived unchanged on two days).

The lane copies the manifest and every page captured in the window by hash,
read-only, through the one landing wrapper, and never writes under the old
folder. The window is calendar 2017 onward (ruling 71, as the returns lane:
ruling 364); a page captured earlier stays where it is, listed and not
landed, until a lane needs it.

    manifest(folder)        [Capture], every file the manifest names, oldest first
    in_window(capture)      captured in 2017 or later
    by_document(captures)   sha256 → [Capture], one document captured on several days
    copy_all(conn)          land the manifest and the window's pages: ([Capture] landed, [Capture] before the window)
"""
import json
import os
from dataclasses import dataclass

from support.docstore import sha256_file
from support.docstore.landing import copy_from_old

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
FOLDER = os.path.join(OLD_LIVE, "var", "staging", "party-boards")
MANIFEST = "MANIFEST.jsonl"
SOURCE = "party_boards"
FIRST_YEAR = 2017                   # ruling 71: calendar 2017 onward
ARCHIVE = "https://web.archive.org/web/{ts}/{url}"


@dataclass(frozen=True)
class Capture:
    party: str          # as the old capture names it (the register's name in September 2026)
    url: str            # the party's own page
    kind: str           # wayback | current
    ts: str             # yyyymmddhhmmss: the Archive's snapshot, or the old job's fetch
    sha256: str
    file: str           # relative to the folder

    @property
    def captured_on(self) -> str:
        return f"{self.ts[:4]}-{self.ts[4:6]}-{self.ts[6:8]}"

    @property
    def archive_url(self):
        return ARCHIVE.format(ts=self.ts, url=self.url) if self.kind == "wayback" else None

    @property
    def path(self) -> str:
        return os.path.join(FOLDER, self.file)


def manifest(folder: str = None) -> list:
    folder = folder or FOLDER
    out = []
    with open(os.path.join(folder, MANIFEST), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("sha256") and r.get("file"):
                out.append(Capture(r["party"], r["original"], r["kind"], r["ts"], r["sha256"], r["file"]))
    return sorted(out, key=lambda c: (c.ts, c.party, c.url))


def in_window(c: Capture) -> bool:
    return int(c.ts[:4]) >= FIRST_YEAR


def by_document(captures: list) -> dict:
    out = {}
    for c in captures:
        out.setdefault(c.sha256, []).append(c)
    return out


def copy_all(conn, folder: str = None, log=None) -> tuple:
    """The manifest and every page in the window, copied by hash. A file
    whose bytes are not the manifest's hash is not landed: it raises, since
    the citation would be false."""
    folder = folder or FOLDER
    copy_from_old(os.path.join(folder, MANIFEST), SOURCE, conn)
    landed, before = [], []
    for c in manifest(folder):
        if not in_window(c):
            before.append(c)
            continue
        ref, new = copy_from_old(os.path.join(folder, c.file), SOURCE, conn)
        if ref.sha256 != c.sha256:
            raise ValueError(f"{c.file}: the manifest says {c.sha256}, the bytes are {ref.sha256}")
        landed.append(c)
        if log:
            log(f"party_boards: {'landed' if new else 'held'} {c.sha256[:12]} {c.party} {c.ts}")
    return landed, before


def old_index(folder: str = None) -> dict:
    """sha256 → Capture for every page, checked against the bytes on disk."""
    folder = folder or FOLDER
    return {c.sha256: c for c in manifest(folder) if sha256_file(os.path.join(folder, c.file)) == c.sha256}
