"""How this lane's documents arrive: case 1 of plan 1.10. The old
estate's `ec-disclosures` job keeps the Commission's files for these kinds
under the live old folder's `var/staging/`, and this lane copies each by
hash, read-only, through the one landing wrapper. Nothing is fetched.

  ec-expenses/       party-expenses__<year>__<asset>.pdf   a party's election expense return
  ec-financials/     Financial-statements__<year>__…pdf    a party's annual financial statements (and one
                     under its bare asset name, filed outside the Commission's year folder)
  ec-broadcasting/   broadcasting-allocation__<year>.html  the allocation page (the page is the document)
                     broadcasting__<year>__…pdf            an allocation decision the page links
  ec-promoters/      promoter-register__<year>.html        the register of promoters (the page is the document)
                     promoter-return__<year>__…pdf         a registered promoter's expense return
  ec-donations/index the Commission's own listing pages for these kinds: party expenses
                     (2020, 2023), promoter expenses (2020, 2023), annual financial statements

`ocr/` and `pageread/` beside the files are the old estate's derived
readings, not documents, and are left where they are; so is each folder's
`MANIFEST.jsonl`, which is the old job's record. The manifest is read for
one thing: the Commission's own URL for each hash, because the listing
pages name a return by its link and the link is the join (never the file
name). A manifest row whose bytes are no longer on disk (the old job
overwrites a page on every run) is a catch-log line.

The year in a file name is the old job's label, written from the page it
found the link on; a reading takes its year from the Commission's listing
or the document, and the name stays an attribute.

    candidate_files()      [(kind, old path)], sorted
    manifest()             sha256 → the manifest row (source URL, fetched_at), every folder
    overwritten()          [(folder, sha256, file)]: manifest captures whose bytes are gone
    copy_all(conn)         land everything: [(kind, DocumentRef, old path, new)]
"""
import json
import os
import re

from support.docstore import sha256_file
from support.docstore.landing import copy_from_old

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
STAGING = os.path.join(OLD_LIVE, "var", "staging")
SOURCE = "party_finance"

#: (folder, file-name pattern, kind). The first match wins.
KINDS = (
    ("ec-expenses", re.compile(r"^party-expenses__\d{4}__.+\.pdf$", re.I), "expense-return"),
    # one statement the Commission files outside its year folder is held under its bare asset name
    ("ec-financials", re.compile(r"^.+\.pdf$", re.I), "financial-statements"),
    ("ec-broadcasting", re.compile(r"^broadcasting-allocation__\d{4}\.html$"), "allocation-page"),
    ("ec-broadcasting", re.compile(r"^broadcasting__\d{4}__.+\.pdf$", re.I), "allocation-decision"),
    ("ec-promoters", re.compile(r"^promoter-register__\d{4}\.html$"), "promoter-register"),
    ("ec-promoters", re.compile(r"^promoter-return__\d{4}__.+\.pdf$", re.I), "promoter-return"),
)
FOLDERS = ("ec-expenses", "ec-financials", "ec-broadcasting", "ec-promoters")

#: The Commission's listing pages, as the old job names them under `ec-donations/index/`. Named, not
#: derived: the Commission moved these pages between elections. (file, kind, election or statement year)
LISTINGS = (
    ("live-20-general-election-and-referendums-party-expenses-for-the-2020-general-election.html",
     "expenses-listing", 2020),
    ("live-ctions-nz-democracy-in-nz-historical-events-2023-general-election-party-expenses.html",
     "expenses-listing", 2023),
    ("live-ction-and-referendums-registered-promoter-expenses-for-the-2020-general-election.html",
     "promoter-expenses-listing", 2020),
    ("live-2023-general-election-registered-promoter-expenses-for-the-2023-general-election.html",
     "promoter-expenses-listing", 2023),
    ("live--nz-democracy-in-nz-political-parties-in-new-zealand-annual-financial-statements.html",
     "financials-listing", None),
)
INDEX = os.path.join(STAGING, "ec-donations", "index")


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
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            kind = kind_of(folder, name)
            if kind and os.path.isfile(os.path.join(d, name)):
                out.append((kind, os.path.join(d, name)))
    for name, kind, _ in LISTINGS:
        p = os.path.join(staging, "ec-donations", "index", name)
        if os.path.isfile(p):
            out.append((kind, p))
    return sorted(out, key=lambda kp: (kp[0], kp[1]))


def unrecognised(staging: str = None) -> list:
    """[(folder, file)]: a file in one of the four folders no kind matches,
    other than the manifest. A catch-log line each; an empty list is the
    state measured on 20 October 2026."""
    staging = staging or STAGING
    out = []
    for folder in FOLDERS:
        d = os.path.join(staging, folder)
        for name in sorted(os.listdir(d)) if os.path.isdir(d) else ():
            if os.path.isfile(os.path.join(d, name)) and name != "MANIFEST.jsonl" and not kind_of(folder, name):
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
    """sha256 → {folder, file, source, fetched_at}, the last row for a hash winning."""
    out = {}
    for folder, row in _manifest_rows(staging):
        if row.get("sha256"):
            out[row["sha256"]] = {"folder": folder, "file": row.get("file"), "source": row.get("source"),
                                  "fetched_at": row.get("fetched_at")}
    return out


def overwritten(staging: str = None) -> list:
    """[(folder, sha256, file)]: captures the manifests list whose bytes no
    file in the folder carries any longer."""
    staging = staging or STAGING
    held = {}
    for folder in FOLDERS:
        d = os.path.join(staging, folder)
        held[folder] = {sha256_file(os.path.join(d, n)) for n in os.listdir(d)
                        if os.path.isfile(os.path.join(d, n))} if os.path.isdir(d) else set()
    return sorted({(folder, row["sha256"], row.get("file")) for folder, row in _manifest_rows(staging)
                   if row.get("sha256") and row["sha256"] not in held[folder]})


def copy_all(conn, staging: str = None, log=None) -> list:
    out = []
    for kind, path in candidate_files(staging):
        ref, new = copy_from_old(path, SOURCE, conn)
        out.append((kind, ref, path, new))
        if log:
            log(f"party_finance: {'landed' if new else 'held'} {kind} {ref.sha256[:12]} {os.path.basename(path)}")
    return out
