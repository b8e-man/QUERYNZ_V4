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

- The provider's own comment collections (24 November 2026): `estate-comments` (Coral and WordPress threads, one record a
  capture, the provider's parse of each comment in `comments`) and `estate-substack` (each free post's comment tree,
  automod-hidden comments included). Read by `read_records`, one ledger line a record (its sha256, its address); the
  key is the site's user id (`user:#<id>`), then the profile link, then the display name. A WordPress comment the
  page reader already holds keeps its key (the page reader keys by the site's slug, the provider by the numeric id).
  Substack's free posts go into `news_private.articles` (`posts`), so their comments join their article.

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
    from support.mcpsource import reads
    done = set(conn.execute("SELECT capture_sha256, url FROM news_private.comment_read").fetchall())
    rows = sorted((r for r in reads.landed_files(conn, CORPUS) if (r[0], r[1]) not in done),
                  key=lambda r: (r[2] is None, r[2], r[1]))
    rows = rows[:int(limit)] if limit else rows
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


RECORD_CORPORA = ("estate-comments", "estate-substack")

def _when(v, naive_nz: bool = False):
    """A timestamp from the provider's parse; a WordPress time without a zone is the site's own (New Zealand)."""
    import datetime as dt
    from zoneinfo import ZoneInfo
    if not isinstance(v, str) or not v.strip():
        return None
    try:
        t = dt.datetime.fromisoformat(v.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return t.replace(tzinfo=ZoneInfo("Pacific/Auckland")) if t.tzinfo is None and naive_nz else t


def record_comments(rec: dict) -> list[dict]:
    """The comments of one estate-comments or substack_comments record, flat, each a dict of the table's columns."""
    out = []
    if rec.get("kind") == "comment_capture":
        wp = rec.get("comment_system") == "wordpress"
        for c in rec.get("comments") or []:
            if not c.get("comment_id"):
                continue
            uid = c.get("user_id")
            votes = c.get("votes") if isinstance(c.get("votes"), dict) else {}
            up = (votes.get("reaction") or {}).get("total") if isinstance(votes.get("reaction"), dict) else None
            out.append({"id": str(c["comment_id"]), "article": c.get("article") or rec.get("article"),
                        "parent": str(c["parent_id"]) if c.get("parent_id") else None,
                        "uid": str(uid) if uid not in (None, "", "0", 0) else None,
                        "name": c.get("display_name"), "slug": None, "aurl": c.get("profile_link") or None,
                        "avatar": c.get("avatar") or None, "posted": _when(c.get("posted_at"), naive_nz=wp),
                        "text": c.get("text") or "", "up": up if isinstance(up, int) else None, "down": None})
    elif rec.get("kind") == "substack_comments":
        def walk(cs, parent):
            for c in cs or []:
                if not isinstance(c, dict) or c.get("id") is None:
                    continue
                out.append({"id": str(c["id"]), "article": rec.get("post"), "parent": parent,
                            "uid": str(c["user_id"]) if c.get("user_id") else None, "name": c.get("name"),
                            "slug": c.get("handle") or None, "aurl": None, "avatar": c.get("photo_url") or None,
                            "posted": _when(c.get("date")), "text": c.get("body") or "",
                            "up": c.get("reaction_count") if isinstance(c.get("reaction_count"), int) else None,
                            "down": None})
                walk(c.get("children"), str(c["id"]))
        walk(rec.get("comments"), None)
        walk(rec.get("automod_hidden_comments"), None)
    return out


def record_key(c: dict) -> str:
    if c["uid"]:
        return f"user:#{c['uid']}"
    if c["aurl"]:
        return f"link:{c['aurl'].strip()}"
    return f"name:{(c['name'] or '').strip().lower()}"


def read_records(conn, read=None) -> dict:
    """Every estate-comments and substack_comments record not yet read, in landing order."""
    import json
    if read is None:
        from support.docstore.landing import read_bytes as read
    from support.mcpsource import reads
    done = set(conn.execute("SELECT capture_sha256, url FROM news_private.comment_read").fetchall())
    rows = [(c, q, sha, url, at) for c, q, sha, url, at, _, _ in reads.arrivals(conn, RECORD_CORPORA)
            if (sha, url or "") not in done]
    n = {"records": 0, "with comments": 0, "comments": 0, "new": 0, "edited": 0, "absent": 0, "failed": 0}
    for corpus, seq, sha, rurl, landed in rows:
        why, cs, rec = None, [], {}
        try:
            rec = json.loads(read(sha))
            cs = record_comments(rec)
        except Exception as exc:  # noqa: BLE001 — one record's failure is a ledger line
            why = f"{type(exc).__name__}: {str(exc)[:200]}"
        if rec.get("kind") not in ("comment_capture", "substack_comments") and not why:
            conn.execute("INSERT INTO news_private.comment_read (capture_sha256, url, comments, why) VALUES "
                         "(%s, %s, 0, %s) ON CONFLICT DO NOTHING", (sha, rurl or "", f"not a thread: {rec.get('kind')}"))
            continue
        seen = _when(rec.get("captured_at")) or landed
        host = (rec.get("source") or "").lower().removeprefix("www.") or None
        cap = (rec.get("capture") or {}).get("sha256") or sha
        with conn.transaction():
            keys = {}
            for c in cs:
                h = host or conn.execute("SELECT news_private.host_of(%s)", (c["article"],)).fetchone()[0]
                key = conn.execute("SELECT news_private.url_key(%s)", (c["article"],)).fetchone()[0]
                keys.setdefault((h, key), []).append(c["id"])
                md5 = hashlib.md5(c["text"].encode()).hexdigest()
                new = conn.execute(
                    "INSERT INTO news_private.comment_versions (host, comment_id, text_md5, text, capture_sha256, seen_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", (h, c["id"], md5, c["text"], cap, seen)).rowcount
                r = conn.execute("""
                    INSERT INTO news_private.comments AS m (host, comment_id, url_key, url, parent_id, commenter_key,
                        author_name, author_slug, author_url, avatar_url, posted_at, text, chars, votes_up, votes_down,
                        first_seen_at, last_seen_at, capture_sha256)
                    VALUES (%(host)s, %(id)s, %(key)s, %(url)s, %(parent)s, %(ck)s, %(name)s, %(slug)s, %(aurl)s,
                        %(avatar)s, %(posted)s, %(text)s, %(chars)s, %(up)s, %(down)s, %(seen)s, %(seen)s, %(sha)s)
                    ON CONFLICT (host, comment_id) DO UPDATE SET
                        text = EXCLUDED.text, chars = EXCLUDED.chars,
                        votes_up = coalesce(EXCLUDED.votes_up, m.votes_up), author_name = EXCLUDED.author_name,
                        avatar_url = coalesce(EXCLUDED.avatar_url, m.avatar_url), last_seen_at = EXCLUDED.last_seen_at,
                        capture_sha256 = EXCLUDED.capture_sha256, absent_since = NULL,
                        versions = m.versions + %(new)s
                    WHERE m.last_seen_at <= EXCLUDED.last_seen_at
                    RETURNING (xmax = 0)
                """, {"host": h, "id": c["id"], "key": key, "url": c["article"], "parent": c["parent"],
                      "ck": record_key(c), "name": c["name"], "slug": c["slug"], "aurl": c["aurl"],
                      "avatar": c["avatar"], "posted": c["posted"], "text": c["text"], "chars": len(c["text"]),
                      "up": c["up"], "down": c["down"], "seen": seen, "sha": cap, "new": new}).fetchone()
                if r and r[0]:
                    n["new"] += 1
                elif r and new:
                    n["edited"] += 1
            if rec.get("kind") == "substack_comments" or (rec.get("total_at_capture") or 0) <= len(cs):
                # a whole thread: what an earlier capture showed and this one does not is absent (a Coral capture
                # holding fewer than its total is a part of the thread, and proves nothing absent)
                for (h, key), ids in keys.items():
                    n["absent"] += conn.execute(
                        "UPDATE news_private.comments SET absent_since = %s WHERE url_key = %s AND host = %s "
                        "AND last_seen_at < %s AND absent_since IS NULL AND NOT (comment_id = ANY(%s))",
                        (seen, key, h, seen, ids)).rowcount
            conn.execute("INSERT INTO news_private.comment_read (capture_sha256, url, comments, why) VALUES "
                         "(%s, %s, %s, %s) ON CONFLICT DO NOTHING", (sha, rurl or "", len(cs), why))
        n["records"] += 1
        n["with comments"] += bool(cs)
        n["comments"] += len(cs)
        n["failed"] += bool(why)
    return n


def post_text(raw: dict) -> str:
    """A Substack post's text from its JSON's body_html, paragraph by paragraph."""
    from bs4 import BeautifulSoup
    from registers.news.extract.base import clean_text
    soup = BeautifulSoup(raw.get("body_html") or "", "html.parser")
    parts = [t.get_text() for t in soup.find_all(["p", "h1", "h2", "h3", "h4", "li", "blockquote"])
             if not t.find_parent(["li", "blockquote"]) or t.name in ("li", "blockquote")]
    return clean_text(parts) or soup.get_text(" ", strip=True)


def posts(conn, read=None) -> dict:
    """Substack's free posts (estate-substack `substack_post`, their JSON downloaded whole) into news_private.articles,
    the longer text kept. A post whose file is not downloaded yet waits for the next load."""
    import json
    if read is None:
        from support.docstore.landing import read_bytes as read
    n = {"posts": 0, "in": 0, "waiting": 0, "paid": 0}
    from support.mcpsource import reads
    rows = [(sha, fsha, state) for _, _, sha, _, _, fsha, state in reads.arrivals(conn, ("estate-substack",))]
    for rsha, fsha, state in rows:
        rec = json.loads(read(rsha))
        if rec.get("kind") != "substack_post":
            continue
        n["posts"] += 1
        if rec.get("audience") not in (None, "everyone"):       # Arthur: free posts only
            n["paid"] += 1
            continue
        if state not in ("landed", "held") or not fsha:
            n["waiting"] += 1
            continue
        raw = json.loads(read(fsha))
        text = post_text(raw)
        url = rec.get("post") or raw.get("canonical_url")
        author = ", ".join(b.get("name") for b in raw.get("publishedBylines") or [] if b.get("name")) or None
        n["in"] += conn.execute("""
            INSERT INTO news_private.articles AS a (url_key, url, host, title, author, published_at, categories, text,
                                                    chars, source, held_by, capture_sha256, parser, fetched_at)
            VALUES (news_private.url_key(%(url)s), %(url)s, news_private.host_of(%(url)s), %(title)s, %(author)s,
                    %(pub)s, NULL, %(text)s, %(chars)s, 'provider', ARRAY['provider'], %(sha)s, 'substack', %(at)s)
            ON CONFLICT (url_key) DO UPDATE SET
                held_by = (SELECT array_agg(DISTINCT x) FROM unnest(a.held_by || EXCLUDED.held_by) x),
                text = CASE WHEN EXCLUDED.chars > a.chars THEN EXCLUDED.text ELSE a.text END,
                title = coalesce(a.title, EXCLUDED.title), author = coalesce(a.author, EXCLUDED.author),
                capture_sha256 = CASE WHEN EXCLUDED.chars > a.chars THEN EXCLUDED.capture_sha256 ELSE a.capture_sha256 END,
                parser = CASE WHEN EXCLUDED.chars > a.chars THEN EXCLUDED.parser ELSE a.parser END,
                chars = greatest(a.chars, EXCLUDED.chars),
                published_at = coalesce(a.published_at, EXCLUDED.published_at)
        """, {"url": url, "title": rec.get("title") or raw.get("title"), "author": author,
              "pub": _when(rec.get("published_at")), "text": text, "chars": len(text), "sha": fsha,
              "at": _when(rec.get("captured_at"))}).rowcount
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
        print("provider comment records:", read_records(conn), flush=True)
        print("substack posts:", posts(conn), flush=True)
        print("commenters:", commenters(conn), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
