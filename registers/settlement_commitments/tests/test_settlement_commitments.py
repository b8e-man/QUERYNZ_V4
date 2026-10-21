"""The watch: the wall recognised on Te Haeata's real pages (sample.list), the
capture's politeness on a fake transport, the check red on a fallen wall or a
stale watch, and the position against what it cites. No model is called and
nothing is fetched."""
import datetime as dt
import os
import re

import pytest

import support.fetchgate as fg
from support import db, sample
from support.docstore.landing import path_for, read_bytes
from support.lane import check_folder
from registers.settlement_commitments import capture, check, load, read
from registers.settlement_commitments import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSITION = os.path.join(os.path.dirname(os.path.dirname(LANE)), "docs", "legal", "positions", "treaty-settlement-commitments.md")   # moved there at the merge
SCHEMA = "scratch_test_settlement_commitments"
ITEMS = sample.read_list(os.path.join(LANE, "sample.list"))
QUOTES = {
    "ca096c67": "Please log in",
    "beb33252": "Crown copyright protection",
    "4e9b9c0a": "not the authoritative record",
    "e54c2a99": "creative commons attribution licence (BY) 4.0",
    "0f944146": "You must not carry out any data collection activities (including data mining, data extraction and data harvesting)",
    "1d65bbea": "signed a Deed of Settlement on 11 November 2021",
}


def _store_or_skip():
    if not os.path.exists(path_for(ITEMS[0].split()[-1])):
        pytest.skip("no document store here")


def test_the_lane_folder_has_the_shape():
    assert check_folder(LANE) == []


def test_the_position_names_its_hosts():
    pos = fg.positions(os.path.dirname(POSITION))
    assert pos["tehaeata.govt.nz"] == pos["whakatau.govt.nz"] == "treaty-settlement-commitments"


def test_every_cited_hash_is_held_and_every_quote_is_on_its_page():
    _store_or_skip()
    held = [i.split()[-1] for i in ITEMS]
    cited = re.findall(r"`([0-9a-f]{8})…`", open(POSITION, encoding="utf-8").read())
    robots = os.listdir(fg.ROBOTS_DIR) if os.path.isdir(fg.ROBOTS_DIR) else []
    assert len(cited) >= 7
    for p in cited:
        assert any(h.startswith(p) for h in held) or any(n.rsplit(".", 2)[-2].startswith(p) for n in robots), p
    for p, quote in QUOTES.items():
        h = next(h for h in held if h.startswith(p))
        page = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", read_bytes(h).decode("utf-8", "replace")))
        assert quote in page, f"{p}… does not say {quote[:40]!r}"


def test_the_wall_and_the_open_pages_are_recognised_on_the_real_pages():
    _store_or_skip()
    assert S.fill(None, SCHEMA, ITEMS) == 5


def test_a_page_not_te_haeata_s_is_refused():
    with pytest.raises(read.NotTheShape):
        read.recognise(b"<html><title>Something | Elsewhere</title></html>")
    assert read.recognise(b"<title>About | Te Haeata</title><p>About</p>") == "open"


class FakeTables:
    def __init__(self, due=True):
        self.rows, self.due = [], due

    def docs_due(self, days):
        return self.due

    def add(self, url, purpose, status, sha, answer):
        self.rows.append((url, purpose, status, answer))


class Ref:
    sha256 = "a" * 64


def _run(answers, now=None, due=True):
    t, clock, asked = FakeTables(due), [0.0], []

    def opener(url, timeout):
        asked.append(url)
        st, body = answers.get(url, (200, b"<title>x | Te Haeata</title>"))
        return fg.Fetched(url, st, body, url, fg.looks_challenged(st, body))
    out = capture.Run(t, land_fn=lambda *a, **k: (Ref(), True), opener=opener, clock=lambda: clock[0],
                      sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                      now=now or (lambda: dt.datetime(2026, 10, 25, 23, 15, tzinfo=capture.NZ))).run()
    return out, t, asked, clock


WALL = b'<title>Nau mai | Te Haeata</title><form data-drupal-selector="user-login-form">Please log in</form>'


def test_the_watch_asks_the_records_once_and_the_pages_about_the_source_when_due():
    out, t, asked, clock = _run({capture.RECORDS: (200, WALL)})
    assert out["records"] == "wall" and asked == [capture.RECORDS, *capture.DOCS] and clock[0] >= 4 * capture.FLOOR_S
    out, t, asked, _ = _run({capture.RECORDS: (200, WALL)}, due=False)
    assert asked == [capture.RECORDS]


def test_a_challenge_stops_the_watch_and_nothing_is_asked_by_day():
    out, t, asked, _ = _run({capture.RECORDS: (403, b"")})
    assert out["stopped"].startswith("stopped:") and asked == [capture.RECORDS] and not out["records"]
    out, t, asked, _ = _run({}, now=lambda: dt.datetime(2026, 10, 25, 12, 0, tzinfo=capture.NZ))
    assert asked == [] and out["stopped"] == "stopped: off-peak is over"


def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


def test_the_check_is_green_on_the_wall_and_red_on_a_fallen_wall_or_a_stale_watch():
    _db_or_skip()
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        try:
            t = capture.Tables(conn, SCHEMA)
            t.create()
            conn.execute(f"DELETE FROM {capture.table(SCHEMA, 'capture_watch')}")
            assert check.outside(conn, SCHEMA) == ["no watch of Te Haeata's records address is held"]
            t.add(capture.RECORDS, "records", 200, "a" * 64, "wall")
            assert check.outside(conn, SCHEMA) == []
            later = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=9)
            assert any("days old" in p for p in check.outside(conn, SCHEMA, now=later))
            t.add(capture.RECORDS, "records", 200, "b" * 64, "open")
            assert any("without the login wall" in p for p in check.outside(conn, SCHEMA))
            assert load.load(conn, SCHEMA, log=lambda *_: None) == 0
        finally:
            conn.rollback()
