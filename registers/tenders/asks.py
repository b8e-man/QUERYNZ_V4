"""The lane's request to the ingest MCP's provider (11 November 2026, Arthur: "move gets to the mcp"): the Ministry's
GETS award-notice files, which the boxes no longer download (www.mbie.govt.nz answers 403 and the fetch gate holds
it; downloads are the provider's since 5 November). The provider's `gets` corpus is the gets.govt.nz pages, not these
files, so the ask is a new corpus, `estate-tenders`, holding each file of the catalogue's package verbatim, by hash,
every time its bytes change.

The request names the files and the copy we hold of each, never a row. Until the MCP serves `estate-tenders` every
file is asked; after that, a current-era file held longer than
REFRESH_DAYS counts as missing (the Ministry refreshes them about quarterly); the historic files and the dictionary
count only if we hold none. checks.source_lights folds the file into the provider's page and mcp-stale.json.

    write(conn, schema)   rewrite <work>/handover/asks/tenders.json; returns the summary"""
import datetime as dt
import json
import os

WORK = os.environ.get("QV4_WORK") or "/home/user/querynzv4-work"
ASK_FILE = os.path.join(WORK, "handover", "asks", "tenders.json")
CORPUS = "estate-tenders"
PACKAGE_URL = "https://catalogue.data.govt.nz/dataset/new-zealand-government-procurement-award-notices"
FILES_URL = "https://www.mbie.govt.nz/assets/Data-Files/NZGPP-GETS-Open-Data/"
CURRENT = ("gets-award-notices.csv", "gets-supplier-data.csv", "gets-region-by-tender.csv", "gets-product-categories.csv")
STATIC = ("gets-award-notices-historic.csv", "gets-supplier-data-historic.csv", "gets-region-by-tender-historic.csv",
          "gets-product-categories-historic.csv", "schema-and-documentation.xlsx")
REFRESH_DAYS = 120
ASKED = ("serve the Ministry's GETS award-notice files (the catalogue package's CSVs and dictionary; your reply of 11 "
         "November says you hold the award CSV raw) as a corpus estate-tenders, each file verbatim by hash whenever its "
         "bytes change, with a collector at the Ministry's cadence (about quarterly); or say why they cannot be")


def short(conn, schema: str = "tenders", now: dt.datetime = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    held = {n: (sha, at) for n, sha, at in conn.execute(
        f"SELECT DISTINCT ON (name) name, sha256, acquired_at FROM {schema}.capture_files "
        f"WHERE name = ANY(%s) ORDER BY name, acquired_at DESC", (list(CURRENT + STATIC),)).fetchall()}
    from support.mcpsource.replay import holds
    copied = holds(conn, CORPUS)                            # until the provider serves the corpus, every file is asked
    files = []
    for n in CURRENT + STATIC:
        sha, at = held.get(n, (None, None))
        stale = not copied or at is None or (n in CURRENT and (now - at).days > REFRESH_DAYS)
        files.append({"file": n, "era": "current" if n in CURRENT else "historic",
                      "we_hold_sha256": sha, "we_hold_from": at.isoformat() if at else None, "wanted": stale})
    missing = sum(f["wanted"] for f in files)
    oldest = min((f["we_hold_from"] for f in files if f["era"] == "current" and f["we_hold_from"]), default=None)
    return {"schema_version": 1, "corpus": CORPUS, "lane": "tenders",
            "source": "MBIE's GETS open data of award notices (CC BY 3.0 NZ, attribution required)",
            "package": PACKAGE_URL, "files_at": FILES_URL, "listed": len(files), "missing": missing,
            "earliest_take_down": None, "files": files, "asked": ASKED,
            "request_id": f"{CORPUS}@files-{missing}-held-{(oldest or 'none')[:10]}"}


def write(conn, schema: str = "tenders", path: str = None, now: dt.datetime = None) -> dict:
    s = short(conn, schema, now)
    s["written_at"] = (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec="seconds")
    path = path or ASK_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return {k: s[k] for k in ("missing", "request_id")}
