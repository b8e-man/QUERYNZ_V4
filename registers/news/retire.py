"""Retiring the old estate's collection of a news site (Arthur, 17 November 2026: "go site by site. after the site
is migrated and the provider is providing, retire the old").

    python -m registers.news.retire                 every `ready` site, listed and logged
    python -m registers.news.retire HOST [HOST…]    these, each only when `ready`
    python -m registers.news.retire --check         is the old estate reading the list?

The old estate's registry (ingestion/newsscrapers/registry.py) reads RETIRED, one host a line, and treats each host
listed as not ready, so neither its coverage job nor its runners collect it. That reading is a one-time edit Arthur
applies to the old folder (notes/old-news-retired-file.patch); this estate never writes the old folder (hard
limit 19). A host is listed only when news.sites says `ready`, and logged in news.retirements only once the old
registry reads the list.
"""
import argparse
import os
import sys

from support import db

RETIRED = "/home/user/querynzv4-work/live/news-retired.txt"
OLD_REGISTRY = "/home/user/Git Repos/QueryNZ_V3/ingestion/newsscrapers/registry.py"
WORD = ("Arthur, 17 November 2026: go site by site; after the site is migrated and the provider is providing, "
        "retire the old")


def listed(path: str = RETIRED) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            return [h for h in (x.split("#")[0].strip() for x in f) if h]
    except OSError:
        return []


def old_reads_the_list(path: str = OLD_REGISTRY) -> bool:
    try:
        with open(path, encoding="utf-8") as f:
            return RETIRED in f.read()
    except OSError:
        return False


def retire(conn, hosts: list = None, path: str = RETIRED, reads: bool = None) -> dict:
    """List each `ready` host (all of them when none named); log each listed host once the old registry reads it."""
    ready = {h for (h,) in conn.execute("SELECT host FROM news.sites WHERE state = 'ready'").fetchall()}
    want = ready if not hosts else {h for h in hosts if h in ready}
    refused = sorted(set(hosts or []) - ready)
    have = listed(path)
    add = sorted(want - set(have))
    if add:
        with open(path, "a", encoding="utf-8") as f:
            for h in add:
                f.write(f"{h}\n")
    reads = old_reads_the_list() if reads is None else reads
    logged = []
    if reads:
        for h in listed(path):
            cur = conn.execute("INSERT INTO news.retirements (host, how, by_word) VALUES (%s, %s, %s) "
                               "ON CONFLICT DO NOTHING",
                               (h, f"listed in {path}; the old registry reads the list and treats the host as "
                                   "retired:qv4, so its coverage job and runners skip it", WORD))
            if cur.rowcount:
                logged.append(h)
    return {"listed": add, "not ready": refused, "logged": logged, "old reads the list": reads}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("hosts", nargs="*")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        print("old reads the list:", old_reads_the_list(), "| listed:", listed())
        return 0
    with db.connect(db.OWNER_KEY, db.LIVE, autocommit=True) as conn:
        print(retire(conn, a.hosts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
