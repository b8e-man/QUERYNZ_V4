"""The position page against the lane and what it cites: it names every host listings.tsv asks, the gate files
those hosts under it, and every hash it cites is a document held (named in sample.list) whose text carries the
words the page quotes from it. Fails the day a seed's host is not named, a citation is mistyped or a quote drifts.
Reads the document store; skips where the store is absent."""
import html
import os
import re
import urllib.parse

import pytest

import support.fetchgate as fg
from support import sample
from support.docstore.landing import path_for, read_bytes
from registers.local_elections import capture

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(LANE))
MOVED = os.path.join(REPO, "docs", "legal", "positions", "local-election-candidate-returns.md")
POSITION = MOVED if os.path.exists(MOVED) else os.path.join(LANE, "position", "local-election-candidate-returns.md")
#: a hash the page cites → words the page quotes from that document
QUOTES = {
    "1977eae1": "publish, electronically or in any other manner the electoral officer considers appropriate",
    "e58a2ac9": "You must not use automated tools, such as bots or web scrapers, to access our website",
    "b340b707": "scraping, deep-linking, harvesting, data mining, reverse-engineering, use of a robot or spider, automation",
    "ae3f55ce": "spider, crawl, or scrape",
    "2d7bfc08": "harvesting bot, robot, spider, scraper, or other unauthorised automated means",
    "da864ef1": "Creative Commons Attribution 4.0 International Licence",
    "0c664288": "non-commercial organisations, without requiring specific permission",
    "11a9ea05": "The licence granted above does not extend to such third-party material",
    "4f562426": "for personal, informational and non-commercial purposes only",
    "6513a145": "for personal, informational, and not-for-profit purposes only",
}


def _text():
    with open(POSITION, encoding="utf-8") as f:
        return f.read()


def _plain(data: bytes) -> str:
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", data.decode("utf-8", "replace"), flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


def test_the_position_names_every_host_the_seeds_ask_and_the_gate_files_them_under_it():
    folder = os.path.dirname(POSITION)
    for council, _years, url in capture.seeds():
        host = urllib.parse.urlsplit(url).hostname
        assert fg.position_for(host, folder) == "local-election-candidate-returns", f"{council}: {host} not named"


def test_the_councils_held_on_their_terms_are_not_seeded():
    hosts = {urllib.parse.urlsplit(u).hostname.removeprefix("www.") for _, _, u in capture.seeds()}
    for held in ("aucklandcouncil.govt.nz", "ccc.govt.nz", "southwaikato.govt.nz", "waimakariri.govt.nz",
                 "wellington.govt.nz"):
        assert held not in hosts


def test_every_cited_hash_is_quoted_from_its_own_document():
    cited = set(re.findall(r"`([0-9a-f]{8})…`", _text()))
    assert cited == set(QUOTES), f"cited {sorted(cited)}, quoted {sorted(QUOTES)}"
    held = [i.split()[-1] for i in sample.read_list(os.path.join(LANE, "sample.list")) if i.startswith("key: terms ")]
    if not os.path.exists(os.path.dirname(os.path.dirname(path_for("0" * 64)))):
        pytest.skip("the document store is not on this box")
    for prefix, quote in QUOTES.items():
        sha = next((h for h in held if h.startswith(prefix)), None)
        assert sha, f"{prefix}… is cited but sample.list names no such document"
        assert quote in _plain(read_bytes(sha)), f"{prefix}…: the quote is not in the document"
