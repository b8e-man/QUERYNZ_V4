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

The Gazette lane (tranche 2). That lane exported every Gazette notice
the old estate holds, 20 October 2026 (`gazette-notices-2026-10-20.jsonl`),
and publishes each as a row of `pub.gazette_notices` (number, section,
title, citation; never the text). Its notices in the authorities section
(`au`) whose titles are the register's (`TITLE_RULE`) are this lane's
notices: 137, the export's 136 and one more (2023-au2700, Heartland New
Zealand's cancellation, which the old classifier typed as an authority's).
A notice both hold is read from the Gazette lane's document where its text
is the export's, word for word after the reader's normalising, and cited
to it and to the notice's own row there (`gazette_key`); a notice whose two
texts differ keeps the export's and is a catch-log line; a notice only the
export holds keeps the export's. The export stays landed and listed: a
document is never dropped. The texts come from the store by hash; this
lane imports nothing of the Gazette lane's.

    candidate_files()        [(kind, old path)]: the two pages
    export_notices()         the export's bytes, read through the old read-only login
    captured_on(sha256)      when the old job fetched those bytes, by its manifest
    gazette_listing(conn)    the Gazette lane's rows for the register's notices, from pub.gazette_notices
    notices_held(listing)    (the notices to read, one each, cited to their document; [(item, why)])
    copy_all(conn)           land everything: ([(kind, DocumentRef, name, captured at)], [(item, why)])
    python -m registers.parties.capture --export PATH    write the export once
"""
import datetime as dt
import html
import json
import os
import re
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

#: the Gazette lane's export, as its capture pins it (registers/gazette/capture.py; read by hash, never imported)
GAZETTE_EXPORT_SHA = "47de7e0963b32e1e54d3a5ca4bea6a54af6e3f57dae8611354aa56ae58b73a95"
GAZETTE_EXPORT_NAME = "gazette-notices-2026-10-20.jsonl"
GAZETTE_NOTE = "taken from the old estate's tables; original not held; the Gazette lane's copy"
#: a register notice by its title, in the authorities section: 137 of the Gazette lane's notices, 20 October 2026
TITLE_RULE = r"(political|registered) part|party logos?\M|registration of party|register of political"
_TITLE_RX = re.compile(TITLE_RULE.replace("\\M", r"\b"), re.I)
_GAZETTE_SQL = f"""
SELECT notice, key, document, published_on::text, title, url
  FROM pub.gazette_notices
 WHERE section = 'au' AND title ~* '{TITLE_RULE}'
 ORDER BY published_on, notice
"""

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


def lines_of(sha: str, wanted=None) -> dict:
    """notice → [its lines] in the stored JSON-lines document `sha`; with
    `wanted`, only those notice numbers (the Gazette lane's export is 395 MB:
    a line is parsed only when its number is wanted)."""
    out = {}
    with open(path_for(sha), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            if wanted is not None:
                i = line.find('"notice": "', 0, 400) + 11
                if i < 11 or line[i:line.find('"', i)] not in wanted:
                    continue
            d = json.loads(line)
            out.setdefault(d["notice"], []).append(d)
    return out


def one_copy(lines: list) -> dict:
    """A notice the old estate captured twice: the copy its classifier read
    (the Gazette lane keeps the same one), else the first article."""
    if len(lines) == 1:
        return lines[0]
    return next((l for l in lines if l.get("old_article") == l.get("article")), None) or min(lines, key=lambda l: l["article"])


def gazette_listing(conn) -> list:
    """[{notice, key, document, published_on, title, url}]: the Gazette lane's
    rows for the register's notices; [] where it publishes none (the sample)."""
    try:
        with conn.transaction():
            rows = conn.execute(_GAZETTE_SQL).fetchall()
    except Exception:                       # no pub.gazette_notices in this database
        return []
    cols = ("notice", "key", "document", "published_on", "title", "url")
    return [dict(zip(cols, r)) for r in rows]


def listing_from_document(sha: str = None) -> list:
    """The same listing read from the Gazette lane's document by the same
    rule, for a database whose pub.gazette_notices holds no `au` row (the
    shared sample): the section code from the notice number, the title rule."""
    sha = sha or GAZETTE_EXPORT_SHA
    out = []
    for nid, lines in lines_of(sha, _AU).items():
        l = one_copy(lines)
        if _TITLE_RX.search(l.get("title") or ""):
            out.append({"notice": nid, "key": None, "document": sha, "published_on": l.get("published_on"),
                        "title": l.get("title"), "url": l.get("url")})
    return sorted(out, key=lambda r: (r["published_on"] or "", r["notice"]))


class _AnyAu:
    """`wanted` for lines_of: every notice number in section `au`."""
    def __contains__(self, nid):
        return "-au" in nid


_AU = _AnyAu()


def notices_held(listing: list, export_sha: str = None) -> tuple:
    """([notice line, one per notice, with `document`, `gazette_key` and
    `source_note`], [(item, why)]). The Gazette lane's copy where its text
    is the export's; the export's where they differ (a catch-log line) or
    where only the export holds the notice."""
    from registers.parties.notices import normalise
    export_sha = export_sha or EXPORT_SHA
    mine = {n: one_copy(ls) for n, ls in lines_of(export_sha).items()}
    by_doc = {}
    for r in listing:
        by_doc.setdefault(r["document"], {})[r["notice"]] = r
    theirs = {}
    for sha, rows in by_doc.items():
        for nid, ls in lines_of(sha, set(rows)).items():
            theirs[nid] = ({**one_copy(ls), "published_on": rows[nid]["published_on"] or one_copy(ls).get("published_on")},
                           sha, rows[nid])
    held, aside = [], []
    for sha, rows in by_doc.items():
        aside += [(f"{sha}/notice {nid}", "listed by the Gazette lane and not in its document")
                  for nid in sorted(set(rows) - set(theirs))]
    for nid in sorted(set(mine) | set(theirs)):
        m, t = mine.get(nid), theirs.get(nid)
        if t is not None and (m is None or normalise(t[0]["text"]) == normalise(m["text"])):
            line, sha, row = t
            held.append({"notice": nid, "published_on": line["published_on"], "title": line.get("title"),
                         "url": row.get("url") or line.get("url"), "text": line["text"], "document": sha,
                         "gazette_key": row.get("key"), "source_note": GAZETTE_NOTE, "taken_from": "gazette"})
            continue
        if t is not None:
            aside.append((f"{t[1]}/notice {nid}", "the Gazette lane's text of this notice differs from the export's; "
                                                  "the export's is read"))
        held.append({"notice": nid, "published_on": m["published_on"], "title": m.get("title"), "url": m.get("url"),
                     "text": m["text"], "document": export_sha, "gazette_key": t[2].get("key") if t else None,
                     "source_note": EXPORT_NOTE, "taken_from": "export"})
    return held, aside


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
