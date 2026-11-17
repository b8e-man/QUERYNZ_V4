"""The news register's load (tables.sql): the old estate's copy and the provider's pages into one table, then each
site's move (Arthur, 17 November 2026: "go site by site. after the site is migrated and the provider is providing,
retire the old").

    python -m registers.news.load --job            all three steps, as the job runs them
    python -m registers.news.load --old            the old estate's copy only (rows fetched since the last take)
    python -m registers.news.load --provider [--limit N]   the provider's landed pages not yet read
    python -m registers.news.load --sites          each site's move only

- **The old estate's copy** (`old_incoming_news_private.articles`, topped up nightly by support.oldcopy while the old
  collection runs): every row fetched since the last take, one per address (the longest text where the copy holds
  an address twice).
- **The provider's pages** (`estate-news`, the whole page as fetched, landed by the pull): read by the old estate's
  own parser for the site (registers/news/extract), the generic one where the site has none. Fetches nothing.
- Where both hold an address the longer text is kept, and `held_by` names both.
- **Each site** (`news.sites`): `ready` when the provider has published articles from the site in the last 7 days
  and its earliest article reaches back to where the old copy stops, so stopping the old collection leaves no gap;
  `retired` once `news.retirements` records the old collection stopped for it.

Every line printed is a count. Never prints an article's text.
"""
import argparse
import datetime as dt
import importlib
import os
import re
import sys

from support import db, jobrun

HERE = os.path.dirname(os.path.abspath(__file__))
JOB = "qv4-news-load"
CORPUS = "estate-news"
OLD = "old_incoming_news_private.articles"
#: days a site's provider must have published in, to count as providing
PROVIDING_DAYS = 7
#: the most days between where the old copy stops and the provider's earliest article that is not a gap
GAP_DAYS = 2
#: the largest share of a site's provider pages that may be stubs (a paywall prompt, no text, or under half the old
#: copy's text for the same address) and the site still be ready (Arthur, 18 November 2026: gathering stubs from
#: paywalls "would undermine the system")
STUB_SHARE = 0.05
#: a paywall prompt in a page's last 400 characters
PAYWALL = re.compile(r"(14-day free trial|free trial now|Subscribe to (continue|read)|subscribers? only|"
                     r"Already a subscriber|Premium (content|article)|Sign in to (continue|read)|"
                     r"Unlock this (story|article))", re.I)


def is_stub(text: str) -> bool:
    return bool(PAYWALL.search((text or "")[-400:]))


def create(conn) -> None:
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        conn.execute(f.read())


# ── the old estate's copy ──

def take_old(conn) -> int:
    """Rows of the old copy fetched since the last take, in; returns the rows offered."""
    upto = conn.execute("SELECT max(upto) FROM news_private.old_taken").fetchone()[0]
    newest = conn.execute(f"SELECT max(coalesce(fetched_at, scrape_date, post_date)) FROM {OLD}").fetchone()[0]
    if newest is None or (upto is not None and newest <= upto):
        return 0
    since = "" if upto is None else "WHERE coalesce(fetched_at, scrape_date, post_date) > %(upto)s"
    cur = conn.execute(f"""
        INSERT INTO news_private.articles AS a (url_key, url, host, title, author, published_at, categories, text,
                                                chars, source, held_by, old_id, fetched_at)
        SELECT DISTINCT ON (k) k, news_url, news_private.host_of(news_url), title, author,
               coalesce(post_date_nz, post_date), categories, text_content, coalesce(length(text_content), 0),
               'old estate', ARRAY['old estate'], id, coalesce(fetched_at, scrape_date)
        FROM (SELECT *, news_private.url_key(news_url) AS k FROM {OLD} {since}) o
        WHERE k IS NOT NULL AND k <> '' AND news_private.host_of(news_url) IS NOT NULL
        ORDER BY k, coalesce(length(text_content), 0) DESC, fetched_at DESC NULLS LAST
        ON CONFLICT (url_key) DO UPDATE SET
            held_by = (SELECT array_agg(DISTINCT x) FROM unnest(a.held_by || EXCLUDED.held_by) x),
            url = CASE WHEN EXCLUDED.chars > a.chars THEN EXCLUDED.url ELSE a.url END,
            title = CASE WHEN EXCLUDED.chars > a.chars THEN EXCLUDED.title ELSE a.title END,
            author = CASE WHEN EXCLUDED.chars > a.chars THEN EXCLUDED.author ELSE a.author END,
            published_at = coalesce(a.published_at, EXCLUDED.published_at),
            categories = CASE WHEN EXCLUDED.chars > a.chars THEN EXCLUDED.categories ELSE a.categories END,
            text = CASE WHEN EXCLUDED.chars > a.chars THEN EXCLUDED.text ELSE a.text END,
            source = CASE WHEN EXCLUDED.chars > a.chars THEN EXCLUDED.source ELSE a.source END,
            chars = greatest(a.chars, EXCLUDED.chars),
            old_id = EXCLUDED.old_id
    """, {"upto": upto})
    n = cur.rowcount
    conn.execute("INSERT INTO news_private.old_taken (upto, rows) VALUES (%s, %s)", (newest, n))
    return n


# ── the provider's pages ──

#: parsers this estate added for sites the old estate never collected (registers/news/extract)
OWN_PARSERS = {"thepost.co.nz": "stuffmasthead", "thepress.co.nz": "stuffmasthead", "waikatotimes.co.nz": "stuffmasthead"}


def parser_for(host: str):
    """(name, module) of the old estate's parser for a host: the host, else each parent domain, else the generic."""
    from registers.news.extract.registry import REGISTRY
    keys = {k.split("/")[0].removeprefix("www."): v.module for k, v in REGISTRY.items()}
    keys.update(OWN_PARSERS)
    h = (host or "").removeprefix("www.")
    while h:
        if h in keys:
            name = keys[h]
            break
        h = h.partition(".")[2]
    else:
        name = "genericrss"
    return name, importlib.import_module(f"registers.news.extract.{name}")


def _when(t):
    if isinstance(t, dt.datetime):
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    return None


def read_provider(conn, limit: int = None, read=None, reread_empty: bool = False) -> dict:
    """The provider's landed pages not yet read: each read by its site's parser and offered to the table. With
    `reread_empty`, the pages whose ledger line says no text, no parser or failed are read again (after a parser is
    fixed); their line is replaced by the new outcome."""
    if read is None:
        from support.docstore.landing import read_bytes as read
    again = " OR r.state IN ('no text', 'no parser', 'failed')" if reread_empty else ""
    rows = conn.execute(
        "SELECT DISTINCT ON (f.capture_sha256, f.url) f.capture_sha256, f.url, f.done_at FROM mcpsource.files f "
        "WHERE f.corpus = %s AND f.state IN ('landed', 'held') AND NOT EXISTS (SELECT 1 FROM news_private.provider_read r "
        f"WHERE r.capture_sha256 = f.capture_sha256 AND r.url = f.url AND NOT (false{again})) "
        "ORDER BY f.capture_sha256, f.url, f.done_at DESC"
        + (f" LIMIT {int(limit)}" if limit else ""), (CORPUS,)).fetchall()
    n = {"read": 0, "stub": 0, "no text": 0, "no parser": 0, "failed": 0}
    for sha, url, fetched in rows:
        host = conn.execute("SELECT news_private.host_of(%s)", (url,)).fetchone()[0]
        name, why, x = None, None, None
        try:
            name, mod = parser_for(host)
            html = read(sha).decode("utf-8", "replace")
            x = mod.extract(html, url)
        except Exception as exc:  # noqa: BLE001 — one page's failure is a ledger line, not the run's end
            why = f"{type(exc).__name__}: {str(exc)[:200]}"
        text = (getattr(x, "text", None) or "").strip() if x else ""
        state = "failed" if why else ("stub" if is_stub(text) else "read") if text else "no text"
        with conn.transaction():
            conn.execute("INSERT INTO news_private.provider_read (capture_sha256, url, state, parser, chars, why) "
                         "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (capture_sha256, url) DO UPDATE SET state = EXCLUDED.state, "
                         "parser = EXCLUDED.parser, chars = EXCLUDED.chars, why = EXCLUDED.why, at = now() "
                         "WHERE news_private.provider_read.state IN ('no text', 'no parser', 'failed')",
                         (sha, url, state, name, len(text) if text else None, why))
            if state == "read":
                conn.execute("""
                    INSERT INTO news_private.articles AS a (url_key, url, host, title, author, published_at,
                        categories, text, chars, source, held_by, capture_sha256, parser, fetched_at)
                    VALUES (news_private.url_key(%(url)s), %(url)s, %(host)s, %(title)s, %(author)s, %(pub)s,
                        %(cats)s, %(text)s, %(chars)s, 'provider', ARRAY['provider'], %(sha)s, %(parser)s, %(fetched)s)
                    ON CONFLICT (url_key) DO UPDATE SET
                        held_by = (SELECT array_agg(DISTINCT x) FROM unnest(a.held_by || EXCLUDED.held_by) x),
                        url = CASE WHEN EXCLUDED.chars >= a.chars THEN EXCLUDED.url ELSE a.url END,
                        title = CASE WHEN EXCLUDED.chars >= a.chars THEN EXCLUDED.title ELSE a.title END,
                        author = CASE WHEN EXCLUDED.chars >= a.chars THEN coalesce(EXCLUDED.author, a.author) ELSE a.author END,
                        published_at = coalesce(a.published_at, EXCLUDED.published_at),
                        categories = CASE WHEN EXCLUDED.chars >= a.chars AND cardinality(EXCLUDED.categories) > 0
                                          THEN EXCLUDED.categories ELSE a.categories END,
                        text = CASE WHEN EXCLUDED.chars >= a.chars THEN EXCLUDED.text ELSE a.text END,
                        source = CASE WHEN EXCLUDED.chars >= a.chars THEN EXCLUDED.source ELSE a.source END,
                        parser = CASE WHEN EXCLUDED.chars >= a.chars THEN EXCLUDED.parser ELSE a.parser END,
                        chars = greatest(a.chars, EXCLUDED.chars),
                        capture_sha256 = EXCLUDED.capture_sha256
                """, {"url": url, "host": host, "title": (x.title or None), "author": x.author,
                      "pub": _when(x.published_at), "cats": list(x.categories or []), "text": text,
                      "chars": len(text), "sha": sha, "parser": name, "fetched": fetched})
        n[state] += 1
    return n


# ── each site's move ──

SITES = f"""
WITH o AS (
    SELECT host, count(*) AS n, max(published_at)::date AS newest, max(fetched_at)::date AS last_fetch
    FROM news_private.articles WHERE 'old estate' = ANY (held_by) GROUP BY host),
p AS (
    SELECT host, count(*) AS n, min(published_at)::date AS earliest, max(published_at)::date AS newest,
           count(*) FILTER (WHERE published_at > now() - interval '{PROVIDING_DAYS} days') AS week
    FROM news_private.articles WHERE 'provider' = ANY (held_by) GROUP BY host),
b AS (
    SELECT host, count(*) AS held FROM news_private.articles
    WHERE 'old estate' = ANY (held_by) AND 'provider' = ANY (held_by) GROUP BY host),
s AS (
    SELECT news_private.host_of(r.url) AS host, count(*) AS pages,
           count(*) FILTER (WHERE r.state IN ('stub', 'no text')
                            OR (r.state = 'read' AND a.old_id IS NOT NULL AND r.chars < a.chars / 2)) AS stubs
    FROM news_private.provider_read r
    LEFT JOIN news_private.articles a ON a.url_key = news_private.url_key(r.url)
    GROUP BY 1)
SELECT coalesce(o.host, p.host), coalesce(o.n, 0), o.newest, o.last_fetch, coalesce(p.n, 0), p.earliest, p.newest,
       coalesce(p.week, 0), r.host IS NOT NULL, coalesce(s.pages, 0), coalesce(s.stubs, 0), coalesce(b.held, 0)
FROM o FULL JOIN p ON p.host = o.host LEFT JOIN news.retirements r ON r.host = coalesce(o.host, p.host)
LEFT JOIN b ON b.host = coalesce(o.host, p.host) LEFT JOIN s ON s.host = coalesce(o.host, p.host)
"""


def judge(old_n, old_newest, prov_n, prov_earliest, prov_newest, week, retired, pages=0, stubs=0,
          old_held=0) -> tuple:
    """(state, why) for one site. `pages`: provider pages read; `stubs`: of them, stubs (STUB_SHARE); `old_held`:
    the old copy's addresses the provider also holds."""
    share = stubs / pages if pages else 0.0
    if retired:
        if share > STUB_SHARE:
            return "retired", (f"the old collection is stopped for this site, but {stubs} of the provider's {pages} "
                               f"pages are stubs: ask the provider")
        return "retired", "the old collection is stopped for this site; the provider carries it"
    if not prov_n:
        return "old only", "the provider has delivered nothing from this site yet"
    if not old_n:
        return "provider only", "only the provider holds this site; the old estate never collected it"
    if share > STUB_SHARE:
        return "providing, stubs", (f"{stubs} of the provider's {pages} pages are stubs (a paywall prompt, no text, "
                                    f"or under half the old copy's text)")
    if prov_newest is None:     # an undated site: ready when the provider holds every address the old copy holds
        if old_held >= old_n:
            return "ready", f"undated; the provider holds all {old_n} of the old copy's addresses"
        return "providing, gap", f"undated; the provider holds {old_held} of the old copy's {old_n} addresses"
    if not week:
        return "providing, gap", f"the provider's newest article is {prov_newest}: nothing in the last {PROVIDING_DAYS} days"
    if old_newest and prov_earliest and (prov_earliest - old_newest).days > GAP_DAYS:
        return "providing, gap", (f"the old copy stops at {old_newest}, the provider starts at {prov_earliest}: "
                                  f"{(prov_earliest - old_newest).days} days between")
    return "ready", f"the provider published {week} articles in the last {PROVIDING_DAYS} days and reaches back to {prov_earliest}"


def sites(conn) -> dict:
    rows = conn.execute(SITES).fetchall()
    out = []
    for host, on, onew, olast, pn, pe, pnew, week, retired, pages, stubs, held in rows:
        state, why = judge(on, onew, pn, pe, pnew, week, retired, pages, stubs, held)
        out.append((host, on, onew, olast, pn, pe, pnew, week, state, why))
    with conn.transaction():
        conn.execute("DELETE FROM news.sites")
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO news.sites (host, old_articles, old_newest, old_last_fetch, provider_articles, "
                            "provider_earliest, provider_newest, provider_week, state, why) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", out)
    from collections import Counter
    return dict(Counter(r[8] for r in out))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--job", action="store_true")
    ap.add_argument("--old", action="store_true")
    ap.add_argument("--provider", action="store_true")
    ap.add_argument("--sites", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--reread-empty", action="store_true", help="read again the pages that gave no text")
    a = ap.parse_args(argv)
    every = a.job or not (a.old or a.provider or a.sites)
    started, counts = jobrun.now(), {}
    try:
        with db.connect(db.OWNER_KEY, db.LIVE, autocommit=True) as conn:
            conn.execute("SET statement_timeout = 5400000")   # the job's query limit
            create(conn)
            if every or a.old:
                counts["old"] = take_old(conn)
                print("old estate rows offered:", counts["old"], flush=True)
            if every or a.provider:
                counts["provider"] = read_provider(conn, a.limit, reread_empty=a.reread_empty)
                print("provider pages:", counts["provider"], flush=True)
            if every or a.sites:
                counts["sites"] = sites(conn)
                print("sites:", counts["sites"], flush=True)
            if every:          # a ready site is retired from the old collection (registers/news/retire.py)
                from registers.news import retire
                counts["retire"] = retire.retire(conn)
                print("retire:", counts["retire"], flush=True)
                if counts["retire"]["logged"]:
                    counts["sites"] = sites(conn)
                    print("sites:", counts["sites"], flush=True)
    except Exception as exc:
        if a.job:
            jobrun.record(JOB, False, f"{type(exc).__name__}: {str(exc)[:300]}", started, counts)
        raise
    if a.job:
        jobrun.record(JOB, True, f"loaded: {counts}", started, counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
