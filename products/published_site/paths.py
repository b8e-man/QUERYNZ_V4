"""Where a published read lives in a version folder.

The frozen site's rule (its `pi/snapshot_paths.py`), kept exactly so the
comparison in checks/ (plan 4.5) can match the two sides path by path: a
readable slug plus a 32-bit FNV-1a hash of the exact name, macrons and all,
so "Te Pāti Māori" and a hypothetical "Te Pati Maori" never collide. A read
not in KINDS has no path: the shape refuses to invent one, which is what
keeps anything that is not one of the ten kinds out of a version.

    path("home")                                -> "data/home.json"
    path("subject", "party", "ACT New Zealand") -> "data/subject/party/act-new-zealand-7b1ffcdc.json"
"""
import unicodedata

KINDS = {"home": "home", "parties": "parties", "electorates": "electorates", "pickers": "pickers",
         "subject": "subject", "electorate": "electorate", "donor": "donor", "board-member": "board-member",
         "size-bands": "size-bands", "cite": "cite"}
ROOT = "data"
#: the three files beside the kinds that the frozen version folder also carries under data/
EXTRA = ("search-index",)


def fnv1a(s: str) -> str:
    h = 0x811C9DC5
    for b in s.encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def slug(s: str) -> str:
    out = []
    for ch in unicodedata.normalize("NFKD", s):
        if unicodedata.combining(ch):
            continue
        out.append(ch if (ch.isascii() and ch.isalnum()) else "-")
    t = "".join(out).lower()
    while "--" in t:
        t = t.replace("--", "-")
    t = t.strip("-")
    return t[:60] or "x"


def path(read: str, *key: str) -> str:
    if read not in KINDS and read not in EXTRA:
        raise KeyError(f"{read!r} is not one of the ten kinds of published file; it has no path")
    parts = [ROOT, KINDS.get(read, read)]
    for k in key[:-1]:
        parts.append(slug(k))
    if key:
        parts.append(f"{slug(key[-1])}-{fnv1a(key[-1])}")
    return "/".join(parts) + ".json"


def kind_of(rel: str) -> str:
    """The kind a file in a version folder belongs to, or '' for a file that
    is none of the ten (the manifest, the extras)."""
    parts = rel.replace("\\", "/").split("/")
    if parts[0] != ROOT or len(parts) < 2:
        return ""
    name = parts[1][:-5] if len(parts) == 2 and parts[1].endswith(".json") else parts[1]
    return name if name in KINDS else ""
