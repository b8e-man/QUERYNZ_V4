"""The watch: each watched page recognised on its real bytes (sample.list), a changed page and a page that is not
the one watched told apart, the capture's politeness on a fake transport, the check red on a changed page or a stale
or failed watch, and the position against what it cites. No model is called and nothing is fetched."""
import datetime as dt
import os
import re

import pytest

import support.fetchgate as fg
from support import db, sample
from support.docstore.landing import path_for, read_bytes
from support.lane import check_folder
from registers.council_procurement import capture, check, load, read
from registers.council_procurement import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(LANE))
NAME = "council-procurement-platforms.md"
SCHEMA = "scratch_test_council_procurement"
ITEMS = sample.read_list(os.path.join(LANE, "sample.list"))
QUOTES = {
    "8ec7239c": "The Data may not be distributed or copied for any commercial purpose.",
    "b8f6c4fd": "for personal, informational and non-commercial purposes only",
    "673bdefd": "Upon request, information available on this website may be used free of charge provided that the "
                "source status of the information is acknowledged.",
    "1f27cf1b": "Once registered you'll receive notifications of Public Tenders",
}


def _position() -> str:
    for p in (os.path.join(LANE, "position", NAME), os.path.join(REPO, "docs", "legal", "positions", NAME)):
        if os.path.exists(p):
            return p
    raise AssertionError(f"{NAME} is on file nowhere")


def _store_or_skip():
    if not os.path.exists(path_for(ITEMS[0].split()[-1])):
        pytest.skip("no document store here")


def test_the_lane_folder_has_the_shape():
    assert check_folder(LANE) == []


def test_the_position_names_every_watched_host_and_the_platforms():
    pos = fg.positions(os.path.dirname(_position()))
    text = open(_position(), encoding="utf-8").read()
    mine = {x.strip().lower() for x in re.search(r"^hosts:\s*(.+)$", text, re.M).group(1).split(",")}
    for url in read.WATCHED:
        h = fg.host_of(url)
        # named by this position, and known to the gate (another position may name the same council host:
        # the councillors' interests position does, and the gate's map takes the later file; either permits)
        assert any(p in mine for p in (h, h.split(".", 1)[1])), h
        assert any(p in pos for p in (h, h.split(".", 1)[1])), h
    assert pos["tenderlink.com"] == pos["vendorpanel.nz"] == NAME[:-3]


def test_every_cited_hash_is_held_and_every_quote_is_on_its_page():
    _store_or_skip()
    held = [i.split()[-1] for i in ITEMS]
    body = open(_position(), encoding="utf-8").read()
    cited = re.findall(r"`([0-9a-f]{8})…`", body)
    assert sorted(cited) == sorted(QUOTES)
    flat = " ".join(body.split())
    for p, quote in QUOTES.items():
        h = next(h for h in held if h.startswith(p))
        assert quote in read.text(read_bytes(h).decode("utf-8", "replace")), f"{p}… does not say {quote[:40]!r}"
        assert quote.rstrip(".")[:60] in flat.replace("’", "'"), f"the position does not quote {p}… as it reads"


def test_every_watched_page_is_recognised_on_its_real_bytes():
    _store_or_skip()
    assert S.fill(None, SCHEMA, ITEMS) == len(read.WATCHED) == 4


def test_a_changed_page_and_a_page_that_is_not_the_one_watched_are_told_apart():
    _store_or_skip()
    url, sha = next((i.split()[2], i.split()[3]) for i in ITEMS if "cluthadc" in i)
    page = read_bytes(sha)
    assert read.recognise(url, page) == "bars"
    assert read.recognise(url, page.replace(b"commercial purpose", b"unlawful purpose")) == "changed"
    with pytest.raises(read.NotTheShape):
        read.recognise(url, page.replace(b"Clutha District Council</title>", b"Elsewhere</title>"))
    with pytest.raises(read.NotTheShape):
        read.recognise("https://www.cluthadc.govt.nz/rules-regulations-and-licenses/tenders", page)


def test_no_tender_or_award_page_is_ever_asked():
    import urllib.parse
    for url in capture.PAGES:
        assert not re.search(r"tender|award|contract", urllib.parse.urlsplit(url).path, re.I), url
        assert not any(h in fg.host_of(url) for h in ("tenderlink", "qldc", "gets.govt")), url


class FakeTables:
    def __init__(self, due=True):
        self.rows, self._due = [], due

    def due(self, days):
        return self._due

    def add(self, url, status, sha, answer):
        self.rows.append((url, status, answer))


class Ref:
    sha256 = "a" * 64


def _page(url, words=True):
    t, w, _ = read.WATCHED[url]
    return f"<html><title>{t}</title><p>{w if words else 'other words'}</p></html>".encode()


def _run(answers=None, now=None, due=True):
    t, clock, asked = FakeTables(due), [0.0], []

    def opener(url, timeout):
        asked.append((url, clock[0]))
        st, body = (answers or {}).get(url, (200, _page(url)))
        return fg.Fetched(url, st, body, url, fg.looks_challenged(st, body))
    out = capture.Run(t, land_fn=lambda *a, **k: (Ref(), True), opener=opener, clock=lambda: clock[0],
                      sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                      now=now or (lambda: dt.datetime(2026, 10, 25, 22, 50, tzinfo=capture.NZ))).run()
    return out, t, asked


def test_the_watch_asks_each_page_once_and_asks_nothing_when_not_due():
    out, t, asked = _run()
    assert [u for u, _ in asked] == list(capture.PAGES) and out["bars"] == 4 and not out["stopped"]
    out, t, asked = _run(due=False)
    assert asked == [] and out["stopped"].startswith("not due")


def test_a_changed_page_is_recorded_changed():
    url = capture.PAGES[1]
    out, t, _ = _run({url: (200, _page(url, words=False))})
    assert out["changed"] == 1 and (url, 200, "changed") in t.rows


def test_a_challenge_stops_the_watch_and_nothing_is_asked_by_day():
    out, t, asked = _run({capture.PAGES[0]: (403, b"")})
    assert out["stopped"].startswith("stopped:") and len(asked) == 1
    out, t, asked = _run(now=lambda: dt.datetime(2026, 10, 25, 12, 0, tzinfo=capture.NZ))
    assert asked == [] and out["stopped"] == "stopped: off-peak is over"


def test_a_redirect_is_not_followed():
    url = capture.PAGES[0]
    out, t, _ = _run({url: (302, b"")})
    assert out["set_aside"] == 1 and t.rows[0][2].startswith("set aside: HTTP 302")


def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


def test_the_check_is_green_when_every_page_bars_and_red_on_a_change_or_a_stale_or_failed_watch():
    _db_or_skip()
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        try:
            t = capture.Tables(conn, SCHEMA)
            t.create()
            conn.execute(f"DELETE FROM {capture.table(SCHEMA, 'capture_watch')}")
            assert len(check.outside(conn, SCHEMA)) == 4          # each page never watched
            for url in capture.PAGES:
                t.add(url, 200, "a" * 64, "bars")
            assert check.outside(conn, SCHEMA) == []
            later = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=41)
            assert len([p for p in check.outside(conn, SCHEMA, now=later) if "days old" in p]) == 4
            t.add(capture.PAGES[2], 200, "b" * 64, "changed")
            assert [p for p in check.outside(conn, SCHEMA)] == [
                "Dunedin City Council: its page no longer says what bars the capture: read the position again"]
            t.add(capture.PAGES[3], 403, None, "set aside: HTTP 403")
            assert any(p.startswith("VendorPanel: the newest watch was a failed read") for p in check.outside(conn, SCHEMA))
            assert load.load(conn, SCHEMA, log=lambda *_: None) == 0
        finally:
            conn.rollback()
