"""The old news copy, one line a site (Arthur, 14 November 2026: a light for every source, news by site).

    python -m support.oldcopy.news_sites            write <live>/checks/news-sites.json
    python -m support.oldcopy.news_sites --print    print, write nothing

Reads old_incoming_news_private.articles on the owner login (the read login has no grant on a _private schema) and
writes counts and dates only, never an article's text or address: per site (the address's host, `www.` dropped) the
articles held, the earliest and newest dated article, and the last fetch. The source lights (checks/source_lights.py)
read the file; about six seconds over 2.8 million rows."""
import argparse
import datetime as dt
import json
import os
import sys

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
OUT = os.path.join(LIVE, "checks", "news-sites.json")
TABLE = "old_incoming_news_private.articles"
QUERY = (f"SELECT lower(regexp_replace(substring(news_url FROM '^https?://([^/:]+)'), '^www\\.', '')) AS host, "
         f"count(*), min(coalesce(post_date_nz, post_date)), max(coalesce(post_date_nz, post_date)), max(fetched_at) "
         f"FROM {TABLE} GROUP BY 1 ORDER BY 2 DESC")


def _day(t):
    return t.date().isoformat() if isinstance(t, dt.datetime) else t.isoformat() if isinstance(t, dt.date) else None


def sites(conn) -> list:
    return [{"host": h, "articles": int(n), "earliest": _day(a), "newest": _day(b), "fetched": _day(f)}
            for h, n, a, b, f in conn.execute(QUERY).fetchall() if h]


def write(rows: list, path: str = None) -> str:
    path = path or OUT
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = {"computed_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "table": TABLE,
            "sites": rows}
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False, indent=0)
    os.replace(path + ".tmp", path)
    return path


def read(path: str = None) -> list:
    try:
        with open(path or OUT, encoding="utf-8") as f:
            return json.load(f).get("sites") or []
    except (OSError, ValueError):
        return []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.OWNER_KEY, db.LIVE, autocommit=True) as conn:
        conn.execute("SET default_transaction_read_only = on")
        conn.execute("SET statement_timeout = 300000")
        rows = sites(conn)
    if a.print:
        for r in rows:
            print(f"{r['host']:<36} {r['articles']:>9,}  {r['earliest']} to {r['newest']}")
        return 0
    print(f"support.oldcopy.news_sites: {len(rows)} sites written to {write(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
