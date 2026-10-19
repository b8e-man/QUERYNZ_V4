"""How this lane's documents arrive: case 1 of plan 1.10. The old estate's
monthly `mp-expenses` and `minister-expenses-capture` jobs keep each
publisher's releases under the live old folder's `var/staging/`, and this
lane copies each by hash, read-only, through the one landing wrapper.
Nothing is fetched (step 4.1).

  mp-expenses/        <year>-members-expense-disclosure-….xlsx   Parliamentary Service's quarterly workbook,
                                                                 from the government data catalogue
                      package_show.json                          the catalogue's own list of the package's
                                                                 resources (the publisher's listing)
  minister-expenses/  ….xlsx, ….xls                              Internal Affairs' quarterly workbook for the
                                                                 members of the Executive (2008 onwards)
                      listing-ministers-expense-releases-….html  Internal Affairs' two listing pages

`MANIFEST.jsonl` in each folder is the old job's record, read for the
publisher's URL for each hash (and, for the catalogue, its resource id and
name); `robots-*.txt` are the old job's snapshots and are not documents.
A manifest row whose bytes are no longer on disk is a catch-log line: the
old job names files after the publisher's file name, and Internal Affairs
published two quarters under one name, so the later download replaced the
earlier one.

The year or quarter in a file name, and the catalogue's resource name, are
labels; a release's period is read from its own title row, and the label
stays an attribute (one catalogue name says January to March 2017 for a
workbook whose title says October to December 2017).

    candidate_files()       [(kind, old path)], sorted
    manifest()              sha256 → the manifest row (url, name, resource id, quarter), both folders
    overwritten()           [(folder, sha256, file, url)]: manifest captures whose bytes are gone
    unrecognised()          [(folder, file)]: a file no kind matches
    listed_workbooks(data, kind)   the publisher's listing → [(url, name)] of the workbooks it links
    copy_all(conn)          land everything: [(kind, DocumentRef, old path, new)]
"""
import html
import json
import os
import re
import urllib.parse

from support.docstore import sha256_file
from support.docstore.landing import copy_from_old

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
STAGING = os.path.join(OLD_LIVE, "var", "staging")
SOURCE = "expenses"
FOLDERS = ("mp-expenses", "minister-expenses")

#: (folder, file-name pattern, kind). The first match wins.
KINDS = (
    ("mp-expenses", re.compile(r"^\d{4}-members-expenses?-disclosures?-.+\.xlsx$", re.I), "mp-workbook"),
    ("mp-expenses", re.compile(r"^package_show\.json$"), "catalogue-listing"),
    ("minister-expenses", re.compile(r"^listing-ministers-expense-releases-.+\.html$"), "dia-listing"),
    ("minister-expenses", re.compile(r"^.+\.xlsx?$", re.I), "executive-workbook"),
)
#: the old job's own files beside the documents: not documents, not catch-log lines
NOT_DOCUMENTS = re.compile(r"^(MANIFEST\.jsonl|robots-\d{4}-\d{2}-\d{2}\.txt)$")
WORKBOOK_KINDS = ("mp-workbook", "executive-workbook")
LISTING_KINDS = ("catalogue-listing", "dia-listing")


def kind_of(folder: str, name: str):
    for f, pattern, kind in KINDS:
        if f == folder and pattern.match(name):
            return kind
    return None


def candidate_files(staging: str = None) -> list:
    staging = staging or STAGING
    out = []
    for folder in FOLDERS:
        d = os.path.join(staging, folder)
        for name in sorted(os.listdir(d)) if os.path.isdir(d) else ():
            kind = kind_of(folder, name)
            if kind and os.path.isfile(os.path.join(d, name)):
                out.append((kind, os.path.join(d, name)))
    return sorted(out)


def unrecognised(staging: str = None) -> list:
    staging = staging or STAGING
    out = []
    for folder in FOLDERS:
        d = os.path.join(staging, folder)
        for name in sorted(os.listdir(d)) if os.path.isdir(d) else ():
            if os.path.isfile(os.path.join(d, name)) and not NOT_DOCUMENTS.match(name) and not kind_of(folder, name):
                out.append((folder, name))
    return out


def _manifest_rows(staging: str = None):
    staging = staging or STAGING
    for folder in FOLDERS:
        p = os.path.join(staging, folder, "MANIFEST.jsonl")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield folder, json.loads(line)


def manifest(staging: str = None) -> dict:
    """sha256 → {folder, file, url, name, resource_id, quarter_start, quarter_end, fetched_at}; the last row wins."""
    out = {}
    for folder, row in _manifest_rows(staging):
        if row.get("sha256"):
            out[row["sha256"]] = {"folder": folder, "file": row.get("file"), "url": row.get("url"),
                                  "name": row.get("name"), "resource_id": row.get("resource_id"),
                                  "quarter_start": row.get("quarter_start"), "quarter_end": row.get("quarter_end"),
                                  "fetched_at": row.get("fetched_at")}
    return out


def overwritten(staging: str = None) -> list:
    """[(folder, sha256, file, url)]: captures a manifest lists whose bytes no file in the folder carries."""
    staging = staging or STAGING
    held = {}
    for folder in FOLDERS:
        d = os.path.join(staging, folder)
        held[folder] = {sha256_file(os.path.join(d, n)) for n in os.listdir(d)
                        if os.path.isfile(os.path.join(d, n))} if os.path.isdir(d) else set()
    return sorted({(folder, r["sha256"], r.get("file"), r.get("url")) for folder, r in _manifest_rows(staging)
                   if r.get("sha256") and r["sha256"] not in held[folder]})


_LINK = re.compile(r'href="([^"]+\.xlsx?)"', re.I)


def listed_workbooks(data: bytes, kind: str) -> list:
    """The workbooks a publisher's own listing names: [(url, name)], in order, each once.
    The catalogue's package lists each resource with its format; Internal Affairs' pages link files."""
    if kind == "catalogue-listing":
        doc = json.loads(data.decode("utf-8"))
        res = (doc.get("result") or doc).get("resources") or []
        out = [(r.get("url"), (r.get("name") or "").strip()) for r in res
               if (r.get("format") or "").lower().strip(".") in ("xlsx", "xls")]
    else:
        text = data.decode("utf-8", "replace")
        out = [(urllib.parse.urljoin("https://www.dia.govt.nz/", html.unescape(u)), os.path.basename(html.unescape(u)))
               for u in _LINK.findall(text)]
    seen, uniq = set(), []
    for u, n in out:
        if u and u not in seen:
            seen.add(u)
            uniq.append((u, n))
    return uniq


def copy_all(conn, staging: str = None, log=None) -> list:
    out = []
    for kind, path in candidate_files(staging):
        ref, new = copy_from_old(path, SOURCE, conn)
        out.append((kind, ref, path, new))
        if log:
            log(f"expenses: {'landed' if new else 'held'} {kind} {ref.sha256[:12]} {os.path.basename(path)}")
    return out
