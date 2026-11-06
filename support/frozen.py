"""The frozen site's current version, read the same on both boxes.

`var/pi-snapshot/current` in the live old folder is a symlink to an
absolute path on node2 (`/home/user/Git Repos/QueryNZ_V3/var/pi-snapshot/v/<stamp>`).
node1 reads the folder over NFS at `/mnt/qv4-old-live` (QV4_OLD_LIVE), where
that target does not exist: following the link fails there (7 November 2026:
qv4-disclosures-load on node1, FileNotFoundError on current/data/home.json).
So the link's last part is read and joined under the folder as this box
sees it. Stdlib only."""
from __future__ import annotations

import os


def snapshot(old_live: str) -> str:
    return os.path.join(old_live, "var", "pi-snapshot")


def current_version(old_live: str):
    """The stamp `current` names, or None where there is no link."""
    try:
        target = os.readlink(os.path.join(snapshot(old_live), "current"))
    except OSError:
        return None
    return os.path.basename(target.rstrip("/")) or None


def current_dir(old_live: str):
    """The current version's folder under `old_live`, or None where there is
    no link or the version it names is not held."""
    v = current_version(old_live)
    if not v:
        return None
    d = os.path.join(snapshot(old_live), "v", v)
    return d if os.path.isdir(d) else None


def home_json(old_live: str) -> str:
    """The current version's data/home.json; a path that does not exist (so
    the reader's open fails plainly) where there is no current version."""
    d = current_dir(old_live)
    return os.path.join(d, "data", "home.json") if d else os.path.join(snapshot(old_live), "current", "data", "home.json")
