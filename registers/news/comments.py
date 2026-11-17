"""The comments on the provider's news pages (tables.sql, `news_private.comments`; Arthur, 18 November 2026: "we want
all comments and we want to efficiently link them to both the articles and also the user"; "start with the sites we
already have. build the schema").

    python -m registers.news.comments            read the pages not yet read for comments, then rebuild commenters

- Every landed estate-news page not yet in `news_private.comment_read` is read, oldest fetch first, by the WordPress
  comment reader (extract/wpcomments.py). A page with no comment markup is a ledger line with 0.
- A comment is one row per (site, comment id). A later capture updates its votes and newest text; a new text is a
  new line in `comment_versions`. A comment a later capture of the article no longer shows gets `absent_since`.
- Commenter key, firmest first: the site's own user mark (`byuser comment-author-<slug>`), else the profile link
  the commenter gave, else the display name. `commenters` is rebuilt from the comments.

Collecting only: no link across sites and none to a known person (Arthur: "a secondary processing question").
Fetches nothing. Every line printed is a count; never prints a comment.
"""
import hashlib
import sys

from support import db

CORPUS = "estate-news"


def commenter_key(c) -> tuple[str, str]:
    if c.author_slug:
        return f"user:{c.author_slug}", "site user"
    if c.author_url:
        return f"link:{c.author_url.strip()}", "profile link"
    return f"name:{(c.author_name or '').strip().lower()}", "display name"


def read_comments(conn, limit: int = None, read=None) -> dict:
    if read is None:
        from support.docstore.landing import read_bytes as read
    from registers.news.extract import wpcomments
    rows = conn.execute(
        "SELECT capture_sha256, url, done_at FROM (SELECT DISTINCT ON (f.capture_sha256, f.url) f.capture_sha256, "
        "f.url, f.done_at FROM mcpsource.files f WHERE f.corpus = %s AND f.state IN ('landed', 'held') "
        "AND NOT EXISTS (SELECT 1 FROM news_private.comment_read r WHERE r.capture_sha256 = f.capture_sha256 "
        "AND r.url = f.url) ORDER BY f.capture_sha256, f.url, f.done_at DESC) x ORDER BY done_at, url"
        + (f" LIMIT {int(limit)}" if limit else ""), (CORPUS,)).fetchall()
    n = {"pages": 0, "with comments": 0, "comments": 0, "new": 0, "edited": 0, "absent": 0, "failed": 0}
    for sha, url, seen in rows:
        why, cs = None, []
        try:
            cs = wpcomments.extract(read(sha).decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001 — one page's failure is a ledger line
            why = f"{type(exc).__name__}: {str(exc)[:200]}"
        with conn.transaction():
            host, key = conn.execute("SELECT news_private.host_of(%s), news_private.url_key(%s)", (url, url)).fetchone()
            for c in cs:
                ck, _ = commenter_key(c)
                md5 = hashlib.md5(c.text.encode()).hexdigest()
                new = conn.execute(
                    "INSERT INTO news_private.comment_versions (host, comment_id, text_md5, text, capture_sha256, seen_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", (host, c.comment_id, md5, c.text, sha, seen)).rowcount
                r = conn.execute("""
                    INSERT INTO news_private.comments AS m (host, comment_id, url_key, url, parent_id, commenter_key,
                        author_name, author_slug, author_url, avatar_url, posted_at, text, chars, votes_up, votes_down,
                        first_seen_at, last_seen_at, capture_sha256)
                    VALUES (%(host)s, %(id)s, %(key)s, %(url)s, %(parent)s, %(ck)s, %(name)s, %(slug)s, %(aurl)s,
                        %(avatar)s, %(posted)s, %(text)s, %(chars)s, %(up)s, %(down)s, %(seen)s, %(seen)s, %(sha)s)
                    ON CONFLICT (host, comment_id) DO UPDATE SET
                        text = EXCLUDED.text, chars = EXCLUDED.chars, votes_up = EXCLUDED.votes_up,
                        votes_down = EXCLUDED.votes_down, author_name = EXCLUDED.author_name,
                        avatar_url = EXCLUDED.avatar_url, last_seen_at = EXCLUDED.last_seen_at,
                        capture_sha256 = EXCLUDED.capture_sha256, absent_since = NULL,
                        versions = m.versions + %(new)s
                    WHERE m.last_seen_at <= EXCLUDED.last_seen_at
                    RETURNING (xmax = 0)
                """, {"host": host, "id": c.comment_id, "key": key, "url": url, "parent": c.parent_id, "ck": ck,
                      "name": c.author_name, "slug": c.author_slug, "aurl": c.author_url, "avatar": c.avatar_url,
                      "posted": c.posted_at, "text": c.text, "chars": len(c.text), "up": c.votes_up,
                      "down": c.votes_down, "seen": seen, "sha": sha, "new": new}).fetchone()
                if r and r[0]:
                    n["new"] += 1
                elif r and new:
                    n["edited"] += 1
            if cs:     # a page that shows the thread: what an earlier capture showed and this one does not is absent
                n["absent"] += conn.execute(
                    "UPDATE news_private.comments SET absent_since = %s WHERE url_key = %s AND host = %s "
                    "AND last_seen_at < %s AND absent_since IS NULL AND NOT (comment_id = ANY(%s))",
                    (seen, key, host, seen, [c.comment_id for c in cs])).rowcount
            conn.execute("INSERT INTO news_private.comment_read (capture_sha256, url, comments, why) VALUES "
                         "(%s, %s, %s, %s) ON CONFLICT DO NOTHING", (sha, url, len(cs), why))
        n["pages"] += 1
        n["with comments"] += bool(cs)
        n["comments"] += len(cs)
        n["failed"] += bool(why)
    return n


def commenters(conn) -> int:
    with conn.transaction():
        conn.execute("DELETE FROM news_private.commenters")
        return conn.execute("""
            INSERT INTO news_private.commenters (host, commenter_key, key_kind, names, comments, articles,
                first_comment_at, last_comment_at)
            SELECT host, commenter_key,
                   CASE split_part(commenter_key, ':', 1) WHEN 'user' THEN 'site user' WHEN 'link' THEN 'profile link'
                        ELSE 'display name' END,
                   coalesce(array_agg(DISTINCT author_name) FILTER (WHERE author_name IS NOT NULL), '{}'),
                   count(*), count(DISTINCT url_key), min(posted_at), max(posted_at)
            FROM news_private.comments GROUP BY host, commenter_key
        """).rowcount


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    from registers.news import load
    with db.connect(db.OWNER_KEY, db.LIVE, autocommit=True) as conn:
        load.create(conn)
        print("comments:", read_comments(conn, a.limit), flush=True)
        print("commenters:", commenters(conn), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
