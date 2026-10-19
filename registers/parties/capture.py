"""How this lane's documents arrive (plan 1.10). Two cases, both already
held by the old estate; nothing is fetched.

Case 1, the file is held. The old `ec-disclosures --party-register` job
keeps the Commission's register page and its applications page as rendered
HTML under the live old folder's `var/staging/ec-party-register/`. It
overwrites both on every run, so only the latest bytes are on disk; the
captures its `MANIFEST.jsonl` lists under other hashes are gone, and each
is a catch-log line. The manifest itself is the job's record, not a
document. Each page is copied by hash, read-only, through the landing
wrapper.

Case 2, only text is held. The Commission's Gazette notices on the
register (registrations, cancellations, changes of name and abbreviation)
reach the old estate as article text in the news database, classified in
`nzbn_canonical.gazette.notices`. They were exported once, on 19 October
2026, to one JSON-lines file (`export_notices`), and that file is the
document: every row read from it is "taken from the old estate's tables;
original not held", and cites the export's hash and the Gazette's own
notice number. The export's hash is pinned here; a second export would be
a new document and a new pin.

    candidate_files()        [(kind, old path)]: the two pages
    export_notices()         the export's bytes, read through the old read-only login
    captured_on(sha256)      when the old job fetched those bytes, by its manifest
    copy_all(conn)           land everything: ([(kind, DocumentRef, name, captured at)], [(item, why)])
    python -m registers.parties.capture --export PATH    write the export once
"""
import datetime as dt
import html
import json
import os
import sys

from support.docstore.landing import copy_from_old, land, path_for, read_bytes

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
FOLDER = os.path.join(OLD_LIVE, "var", "staging", "ec-party-register")
PAGES = {"register-of-political-parties.html": "register", "current-party-and-logo-applications.html": "applications"}
SOURCE = "parties"

EXPORT_NAME = "gazette-party-register-notices-2026-10-19.jsonl"
EXPORT_SHA = "dc19fb7f12fe3a0d78574df9f2673c97c5c559e8f2ce9e42f8e765997cd7855d"
EXPORTED_AT = "2026-10-19T21:30:00+13:00"
EXPORT_NOTE = "taken from the old estate's tables; original not held"

#: the notices the old classifier typed as the register's, and four it typed
#: as an authority's that are the register's by their title (logo notices and
#: the 2008 year's list). The table is the OLD database's (`nzbn_canonical`,
#: schema `gazette`), reached through the old read-only login: the search path
#: names that schema so the query is not mistaken for one into this estate's
#: gazette lane (tests/test_imports_one_way.py guards the new schemas; merge
#: request parties-1 says so).
_OLD_SCHEMA = "SET search_path TO gazette"
_NOTICES_SQL = """
SELECT notice_id, published_date::text, title, url, notice_type, article_id::text
  FROM notices
 WHERE notice_type = 'party_register'
    OR title ILIKE '%%political part%%' OR title ILIKE '%%party logo%%' OR title ILIKE '%%registration of party%%'
 ORDER BY published_date, notice_id
"""


def candidate_files(folder: str = None) -> list:
    folder = folder or FOLDER
    return [(kind, os.path.join(folder, name)) for name, kind in sorted(PAGES.items())
            if os.path.isfile(os.path.join(folder, name))]


def overwritten(folder: str = None) -> list:
    """[(sha256, file name)]: captures the old job's manifest lists whose
    bytes are no longer on disk."""
    folder = folder or FOLDER
    from support.docstore import sha256_file
    held = {sha256_file(p) for _, p in candidate_files(folder)}
    out = []
    try:
        with open(os.path.join(folder, "MANIFEST.jsonl"), encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    m = json.loads(line)
                    if m.get("sha256") and m["sha256"] not in held and os.path.exists(path_for(m["sha256"])) is False:
                        out.append((m["sha256"], m.get("file") or ""))
    except OSError:
        pass
    return sorted(set(out))


def captured_on(sha256: str, folder: str = None):
    """The old job's own record of when it fetched these bytes (its
    manifest), as local time; None when it lists no such capture."""
    folder = folder or FOLDER
    try:
        with open(os.path.join(folder, "MANIFEST.jsonl"), encoding="utf-8") as f:
            for line in f:
                m = json.loads(line) if line.strip() else {}
                if m.get("sha256") == sha256 and m.get("fetched_at"):
                    return dt.datetime.fromisoformat(m["fetched_at"]).astimezone().isoformat(timespec="seconds")
    except OSError:
        pass
    return None


def export_notices(connect=None) -> bytes:
    """One line per notice, oldest first: the Gazette's notice number, the
    day it was published, its title and address, and the text the old
    estate holds. Read-only; run once."""
    from support import db
    connect = connect or (lambda name: db.connect(db.OLD_READ_KEY, name, connect_timeout=10))
    with connect("nzbn_canonical") as c:
        c.execute("SET statement_timeout = '30s'")
        c.execute(_OLD_SCHEMA)
        notices = c.execute(_NOTICES_SQL).fetchall()
    with connect("incoming_news") as c:
        c.execute("SET statement_timeout = '30s'")
        text = dict(c.execute("SELECT id::text, text_content FROM articles WHERE id::text = ANY(%s)",
                              ([n[5] for n in notices],)).fetchall())
    lines = []
    for nid, published, title, url, ntype, article in notices:
        if article not in text:
            raise LookupError(f"notice {nid}: the old estate holds no text for it")
        lines.append(json.dumps({"notice": nid, "published_on": published, "title": html.unescape(title or ""),
                                 "url": url, "old_type": ntype, "text": text[article]},
                                ensure_ascii=False, sort_keys=True))
    return ("\n".join(lines) + "\n").encode("utf-8")


def copy_all(conn, folder: str = None, export_sha: str = None, log=None) -> tuple:
    """Every page copied, the export landed from the store. Returns
    ([(kind, DocumentRef, name, captured at)], [(item, why)])."""
    landed, aside = [], []
    for kind, path in candidate_files(folder):
        ref, new = copy_from_old(path, SOURCE, conn)
        landed.append((kind, ref, os.path.basename(path), captured_on(ref.sha256, folder) or ref.fetched_at))
        if log:
            log(f"parties: {'landed' if new else 'held'} {ref.sha256[:12]} {os.path.basename(path)}")
    for sha, name in overwritten(folder):
        aside.append((sha, f"{name}: the old job's manifest lists this capture; a later fetch overwrote its bytes, not held"))
    sha = export_sha or EXPORT_SHA
    if not os.path.exists(path_for(sha)):
        raise LookupError(f"the notices export {sha} is not in the document store")
    ref, _ = land(read_bytes(sha), name=EXPORT_NAME, source=SOURCE, conn=conn, fetched_at=EXPORTED_AT)
    landed.append(("notices", ref, EXPORT_NAME, EXPORTED_AT))
    return landed, aside


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--export" not in argv:
        print("usage: python -m registers.parties.capture --export PATH")
        return 2
    path = argv[argv.index("--export") + 1]
    data = export_notices()
    with open(path, "wb") as f:
        f.write(data)
    from support.docstore import sha256_file
    print(f"{path}: {data.count(b'\n')} notices, sha256 {sha256_file(path)}, {dt.date.today().isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
