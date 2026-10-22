"""The GETS listing of current tenders is not captured: its terms bar any spider or robot (clause 3.2(i)(e)).
These tests hold the position to the terms page it cites, by hash, and the lane to asking nothing of the site.
They fail the day the cited hash is mistyped, a quoted clause is not on the landed page, the position stops
naming the host, or any of the lane's code or jobs names a GETS address to fetch. Reads the document store;
the citation test skips where the store is absent."""
import html
import os
import re

import pytest

import support.fetchgate as fg
from support.docstore.landing import path_for, read_bytes

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(LANE))
NAME = "government-electronic-tenders-listing.md"
TERMS = "507f5b88e776190e8f8b6703247d5202d4e489df63ec3e6e0e01f7aa4012a462"
QUOTES = (
    "By registering as a User or using GETS you are deemed to have accepted the terms of this Agreement",
    "use any software or other method (whether automatic or manual), including any spider or robot, to monitor, "
    "copy, collect or index any data, Information or content found on GETS",
    "the use is non-commercial or is not to create a competing product",
    "Last updated 7 March 2024",
)


def _position() -> str:
    """The lane folder's draft until the integrator moves it; then docs/legal/positions/."""
    for p in (os.path.join(LANE, "position", NAME), os.path.join(REPO, "docs", "legal", "positions", NAME)):
        if os.path.exists(p):
            return p
    raise AssertionError(f"{NAME} is on file nowhere")


def _text(body: bytes) -> str:
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", body.decode("utf-8", "replace"))
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).replace("’", "'").split())


def test_the_position_names_the_host_and_says_not_captured():
    p = _position()
    assert fg.positions(os.path.dirname(p)).get("www.gets.govt.nz") == NAME[:-3]
    body = open(p, encoding="utf-8").read()
    assert "**not captured.**" in body and TERMS in body


def test_the_cited_terms_are_held_and_say_what_the_position_quotes():
    if not os.path.exists(path_for(TERMS)):
        pytest.skip("no document store here")
    text = _text(read_bytes(TERMS))
    for q in QUOTES:
        assert q in text, f"the terms page does not say {q[:50]!r}"
    pos = " ".join(open(_position(), encoding="utf-8").read().split())
    for q in QUOTES[:3]:
        assert q in pos, f"the position does not quote {q[:50]!r} as the page says it"


def test_the_terms_hash_is_in_the_sample_list():
    assert TERMS in open(os.path.join(LANE, "sample.list"), encoding="utf-8").read()


def test_nothing_in_the_lane_asks_the_gets_site():
    """No code, SQL or job of the lane names a GETS address it could fetch; the docs and this test may."""
    url = re.compile(r"https?://(www\.)?gets\.govt\.nz", re.I)
    for root, _, files in os.walk(LANE):
        if os.sep + "tests" in root or os.sep + "position" in root:
            continue
        for n in files:
            if n.endswith((".py", ".sql", ".json", ".jsonl")):
                with open(os.path.join(root, n), encoding="utf-8") as f:
                    assert not url.search(f.read()), f"{n} names a GETS address"
