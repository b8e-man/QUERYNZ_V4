"""How this lane's documents arrive (plan 1.10, case two: only text is held).

The old estate holds every Gazette notice it captured as article text in the
news database (`incoming_news.articles`, the rows whose address is a
`gazette.govt.nz/notice/id/` page), and its own classification of each in
`nzbn_canonical.gazette.notices`. Both were exported once, on 20 October
2026, to one JSON-lines file (`export_notices`), the way
`registers/parties/capture.py` exported the register's notices, and that
file is the document: every row read from it is "taken from the old
estate's tables; original not held", and cites the export's hash and the
Gazette's own notice number. The export's hash is pinned here; a second
export would be a new document and a new pin. Nothing is fetched, and the
export is never run at load.

One line per article row, so a notice the old estate captured twice is two
lines with one notice number (read.py keeps one and logs the other).

    export_notices()         the export's bytes, read through the old read-only login
    copy_all(conn)           land the export: ([(kind, DocumentRef, name, captured at)], [(item, why)])
    python -m registers.gazette.capture --export PATH    write the export once
"""
import datetime as dt
import html
import json
import os
import re
import sys

from support.docstore.landing import land, path_for, read_bytes

SOURCE = "gazette"
EXPORT_NAME = "gazette-notices-2026-10-20.jsonl"
EXPORT_SHA = "47de7e0963b32e1e54d3a5ca4bea6a54af6e3f57dae8611354aa56ae58b73a95"
EXPORTED_AT = "2026-10-20T04:49:11+13:00"
EXPORT_NOTE = "taken from the old estate's tables; original not held"

_NOTICE_ID = re.compile(r"/notice/id/([^/?#]+)")

#: Both tables are the OLD databases', reached through the old read-only
#: login: the search path names the old schema so the query is not mistaken
#: for one into this estate's gazette lane (tests/test_imports_one_way.py).
_OLD_SCHEMA = "SET search_path TO gazette"
_NOTICES_SQL = "SELECT notice_id, published_date::text, notice_type, article_id FROM notices"
_ARTICLES_SQL = """
SELECT id::text, news_url, title, text_content, post_date_nz::date::text
  FROM articles
 WHERE news_url LIKE '%%gazette.govt.nz/notice/id/%%'
"""


def notice_of(url: str):
    m = _NOTICE_ID.search(url or "")
    return m.group(1) if m else None


def export_notices(connect=None) -> bytes:
    """One line per article row, sorted by notice number then article:
    the notice number, the day the old classifier says it was published (else
    the article's post day), the old type, its title, address and text.
    Read-only, every statement under a time limit; run once."""
    from support import db
    connect = connect or (lambda name: db.connect(db.OLD_READ_KEY, name, connect_timeout=10))
    with connect("nzbn_canonical") as c:
        c.execute("SET statement_timeout = '60s'")
        c.execute(_OLD_SCHEMA)
        typed = {r[0]: r for r in c.execute(_NOTICES_SQL).fetchall()}
    lines = []
    with connect("incoming_news") as c:
        c.execute("SET statement_timeout = '60s'")
        with c.transaction():
            cur = c.cursor(name="gazette_export")
            cur.itersize = 2000
            cur.execute(_ARTICLES_SQL)
            for aid, url, title, text, posted in cur:
                nid = notice_of(url)
                t = typed.get(nid)
                lines.append((nid or "", aid, json.dumps({
                    "notice": nid, "article": aid, "url": url, "title": html.unescape(title or ""),
                    "published_on": t[1] if t else posted, "posted_on": posted,
                    "old_type": t[2] if t else None, "old_article": t[3] if t else None,
                    "text": text or ""}, ensure_ascii=False, sort_keys=True)))
    lines.sort()
    return ("\n".join(l for _, _, l in lines) + "\n").encode("utf-8")


def copy_all(conn, export_sha: str = None, log=None) -> tuple:
    """The export landed from the store. Returns
    ([(kind, DocumentRef, name, captured at)], [(item, why)])."""
    sha = export_sha or EXPORT_SHA
    if not sha or not os.path.exists(path_for(sha)):
        raise LookupError(f"the notices export {sha} is not in the document store")
    ref, new = land(read_bytes(sha), name=EXPORT_NAME, source=SOURCE, conn=conn, fetched_at=EXPORTED_AT)
    if log:
        log(f"gazette: {'landed' if new else 'held'} {ref.sha256[:12]} {EXPORT_NAME}")
    return [("notices", ref, EXPORT_NAME, EXPORTED_AT)], []


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--export" not in argv:
        print("usage: python -m registers.gazette.capture --export PATH")
        return 2
    path = argv[argv.index("--export") + 1]
    if os.path.exists(path):
        print(f"{path} exists: the export is run once")
        return 1
    data = export_notices()
    with open(path, "wb") as f:
        f.write(data)
    from support.docstore import sha256_file
    print(f"{path}: {data.count(b'\n')} lines, sha256 {sha256_file(path)}, {dt.datetime.now().astimezone().isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
