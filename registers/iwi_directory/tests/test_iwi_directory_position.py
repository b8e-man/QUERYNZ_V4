"""The position page against what it cites: every hash it names is a document held (the store, or the gate's
robots archive), and each phrase it quotes is in that document. Fails the day a citation is mistyped or a quote
drifts from the page. Reads the document store; skips where the store is absent."""
import os
import re

import pytest

import support.fetchgate as fg
from support import sample
from support.docstore.landing import path_for, read_bytes
from registers.iwi_directory import read

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSITION = os.path.join(LANE, "position", "iwi-and-hapu-directory.md")
QUOTES = {
    "6c3d13e5": "may be reproduced for personal, not-for-profit or in-house use without formal permission or charge",
    "3377b9be": "CC-BY-NZ-3.0",
    "050687f6": "supplied by representative Māori organisations",
    "74031896": "Any member of the public may anonymously access and browse this website",
}


def _held():
    hashes = [i.split()[-1] for i in sample.read_list(os.path.join(LANE, "sample.list"))]
    return hashes


def _resolve(prefix, hashes):
    for h in hashes:
        if h.startswith(prefix):
            return ("store", h)
    for n in os.listdir(fg.ROBOTS_DIR) if os.path.isdir(fg.ROBOTS_DIR) else []:
        if n.rsplit(".", 2)[-2].startswith(prefix):
            return ("robots", os.path.join(fg.ROBOTS_DIR, n))
    return None


def test_the_position_names_its_hosts():
    assert fg.positions(os.path.dirname(POSITION))["www.tkm.govt.nz".split(".", 1)[1]] == "iwi-and-hapu-directory"


def test_every_cited_hash_is_held_and_every_quote_is_on_its_page():
    hashes = _held()
    if not os.path.exists(path_for(hashes[0])):
        pytest.skip("no document store here")
    cited = re.findall(r"`([0-9a-f]{8})…`", open(POSITION, encoding="utf-8").read())
    assert len(cited) >= 5
    for prefix in cited:
        assert _resolve(prefix, hashes), f"the position cites {prefix}…, which is not held"
    for prefix, quote in QUOTES.items():
        where, h = _resolve(prefix, hashes)
        body = read_bytes(h).decode("utf-8", "replace") if where == "store" else open(h, encoding="utf-8").read()
        assert quote in read.text(body), f"{prefix}… does not say {quote[:40]!r}"
