"""The Gazette's notices after the export, from DigitalNZ (2 November 2026): the answers read into the export's shape,
read by the same readers beside the export, the suppressed kept whole privately and flagged; the night's asking polite, stopped by a failed
read, and the backwalk closing a short year."""
import json
import os

import pytest

from support import db
from registers.gazette import capture as C
from registers.gazette import read

SHA = "a" * 64
EXPORT_SHA = "0" * 64
APPOINT = ("Pursuant to section 5 of the Example Act 2020, the Minister appoints Ann EXAMPLE as a member of the Example Board "
           "for a term of three years. Dated at Wellington this 20th day of October 2026. HON JANE MINISTER, Minister.")


def _rec(nid, title="Appointment of Members of the Example Board", text=APPOINT, day="2026-10-21", rid=1):
    return {"id": rid, "title": title, "dc_identifier": [f"Notice Number: {nid}"],
            "landing_url": f"https://gazette.govt.nz/notice/id/{nid}", "date": [f"{day}T00:00:00Z"], "fulltext": text}


def _answer(recs, count=None) -> bytes:
    return json.dumps({"search": {"result_count": len(recs) if count is None else count, "results": recs}}).encode()


def test_an_answer_reads_into_the_export_s_shape_and_names_its_own_document():
    recs = [_rec("2026-go6400", title="Appointment of&nbsp;Members", text=" Two  spaces\nand a line "),
            {"id": 2, "title": "no number", "landing_url": "https://example.org/x", "date": [], "fulltext": "x"},
            {"id": 3, "title": "by its page", "dc_identifier": [], "landing_url": "https://gazette.govt.nz/notice/id/2026-AL6401",
             "date": ["2026-10-22T00:00:00Z"], "fulltext": "y"}]
    lines = C.lines_of_page(_answer(recs), SHA)
    assert [l["notice"] for l in lines] == ["2026-go6400", "2026-al6401"], "a record naming no Gazette notice is no line"
    a = lines[0]
    assert a["title"] == "Appointment of Members" and a["text"] == "Two spaces and a line"
    assert a["published_on"] == "2026-10-21" and a["_document"] == SHA and a["article"] == "digitalnz:1"
    assert a["url"] == "https://gazette.govt.nz/notice/id/2026-go6400" and a["_note"] == C.DNZ_NOTE


def test_the_readers_read_a_new_notice_from_its_answer_and_a_held_one_from_the_export():
    held = {"notice": "2026-go6000", "article": "x", "old_article": "x", "url": "u", "title": "Appointment of Members of the Example Board",
            "published_on": "2026-10-10", "posted_on": "2026-10-10", "old_type": None, "text": APPOINT}
    export = (json.dumps(held) + "\n").encode()
    page = _answer([_rec("2026-go6000"), _rec("2026-go6400", rid=2), _rec("2012-ba4936", title="In Bankruptcy", rid=3)])
    later = _answer([_rec("2026-go6400", rid=2, day="2026-10-22")])
    res = read.read(export, EXPORT_SHA, pages=[(SHA, page), ("b" * 64, later)], suppressed={"2012-ba4936"})
    by = {r["filed"]["notice"]: r for r in res.notices}
    assert set(by) == {"2026-go6000", "2026-go6400", "2012-ba4936"}
    hid = by["2012-ba4936"]["filed"]
    assert hid["status"] == hid["format"] == "suppressed" and hid["title"] == "" and hid["records"] == 0, \
        "a suppressed notice is a flagged row with no title"
    assert [r["notice"] for r in res.suppressed] == ["2012-ba4936"] and res.suppressed[0]["title"] == "In Bankruptcy" \
        and res.suppressed[0]["text"], "its line is kept whole for the private twin (ruling 142)"
    assert not any(r["filed"].get("notice") == "2012-ba4936" for t in ("bankruptcies", "prohibitions", "appointments")
                   for r in getattr(res, t)), "no typed row is read from it"
    assert by["2026-go6000"]["document"] == EXPORT_SHA and by["2026-go6000"]["filed"]["source_note"] == C.EXPORT_NOTE
    assert by["2026-go6400"]["document"] == "b" * 64, "the newest answer that carries the notice is read"
    assert by["2026-go6400"]["filed"]["source_note"] == C.DNZ_NOTE and by["2026-go6400"]["filed"]["published_on"] == "2026-10-22"
    new = [a for a in res.appointments if a["filed"]["notice"] == "2026-go6400"]
    assert new and all(a["document"] == "b" * 64 for a in new), "a row read from an answer cites that answer"
    why = [w for _, _, w in res.set_aside]
    assert sum("held in the export" in w for w in why) == 1 and sum("asked again" in w for w in why) == 1
    assert sum("suppressed" in w for w in why) == 0
    assert res.counts["lines"] == 5 and res.counts["suppressed"] == 1 and res.counts["from_digitalnz"] == 2
    assert res.counts["pages"] == 2


def test_a_reading_without_answers_is_the_export_s_reading():
    held = {"notice": "2026-go6000", "article": "x", "old_article": "x", "url": "u", "title": "Appointment of Members of the Example Board",
            "published_on": "2026-10-10", "posted_on": "2026-10-10", "old_type": None, "text": APPOINT}
    a = read.read((json.dumps(held) + "\n").encode(), EXPORT_SHA, loaded_at="2026-11-02T00:00:00+13:00")
    assert a.counts["pages"] == 0 and a.counts["from_digitalnz"] == 0 and a.counts["notices"] == 1


def test_off_peak_is_new_zealand_s_night():
    import datetime as dt
    from zoneinfo import ZoneInfo
    nz = ZoneInfo("Pacific/Auckland")
    assert C.off_peak(dt.datetime(2026, 11, 2, 23, 0, tzinfo=nz)) and C.off_peak(dt.datetime(2026, 11, 2, 6, 59, tzinfo=nz))
    assert not C.off_peak(dt.datetime(2026, 11, 2, 7, 0, tzinfo=nz)) and not C.off_peak(dt.datetime(2026, 11, 2, 14, 0, tzinfo=nz))
    assert C.off_peak(dt.datetime(2026, 11, 2, 10, 0, tzinfo=dt.timezone.utc)), "10:00 UTC is 23:00 in Auckland"


# --- the night, against a scratch schema of the sample database ------------------------------------------------------

class _Got:
    def __init__(self, status, body, blocked=""):
        self.status, self.body, self.blocked = status, body, blocked


class _Host:
    """DigitalNZ and the Gazette's robots file, faked: `years` {year: [notice numbers, newest first]}."""

    def __init__(self, years, robots="User-agent: *\nDisallow: /notice/id/2020-ba77\n", block_at=None):
        self.years, self.robots, self.block_at, self.asked = years, robots, block_at, []

    def __call__(self, url):
        self.asked.append(url)
        if self.block_at is not None and len(self.asked) >= self.block_at:
            return _Got(403, b"", "HTTP 403: a block or a challenge")
        if url == C.ROBOTS:
            return _Got(200, self.robots.encode())
        from urllib.parse import parse_qs, urlsplit
        q = {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}
        ids = self.years.get(int(q["and[year][]"]), [])
        per, page = int(q["per_page"]), int(q["page"])
        chunk = ids[(page - 1) * per:page * per] if per else []
        return _Got(200, _answer([_rec(n, rid=i) for i, n in enumerate(chunk)], count=len(ids)))


@pytest.fixture()
def night(tmp_path):
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    schema = "scratch_gazette_capture_test"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.autocommit = True
        conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        slept = []

        def run(host, held, **kw):
            return C.capture(conn, schema, True, open_url=host, sleep=slept.append, clock=lambda: 0.0, held=set(held),
                             root=str(tmp_path), log=lambda *a: None, today=__import__("datetime").date(2026, 11, 2), **kw)
        yield {"run": run, "conn": conn, "schema": schema, "slept": slept}
        conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")


def test_forward_asks_until_a_page_holds_nothing_new_and_lands_each_answer_once(night, monkeypatch):
    monkeypatch.setattr(C, "PER_PAGE", 2)
    ids = ["2026-go9", "2026-go8", "2026-go7", "2026-go6", "2026-go5"]
    host = _Host({2026: ids})
    got = night["run"](host, held={"2026-go7", "2026-go6", "2026-go5"}, backwalk=False)
    # robots, page 1 (two new), page 2 (nothing new: the night stops there, never asking page 3)
    # (landed, or held already: the sample database's store keeps the bytes of an earlier run)
    assert got["ok"] and got["new notices"] == 2 and got["requests"] == 3 and got["pages landed"] + got["pages held"] == 2, got
    assert got["stopped"] == "done"
    t = f"{night['schema']}.gazette_capture_pages"
    rows = night["conn"].execute(f"SELECT mode, year, page, records, new_notices, sha256 IS NOT NULL FROM {t} ORDER BY asked_id").fetchall()
    assert rows == [("forward", 2026, 1, 2, 2, True), ("forward", 2026, 2, 2, 0, True)]
    supp = {r[0] for r in night["conn"].execute(f"SELECT notice FROM {night['schema']}.gazette_capture_suppressed")}
    assert supp == {"2020-ba77"}, "the robots file's disallowed notices are recorded as suppressed"
    assert night["slept"] and all(abs(s - C.FLOOR_S) < 1e-9 for s in night["slept"]), "every request after the first waits the floor"
    pages = C.pages_held(night["conn"], night["schema"], True)
    assert len(pages) == 2 and C.suppressed_held(night["conn"], night["schema"], True) >= {"2020-ba77", "2012-ba4936"}


def test_a_failed_read_stops_the_night_and_says_so(night):
    host = _Host({2026: ["2026-go9"]}, block_at=2)
    got = night["run"](host, held=set())
    assert not got["ok"] and got["stopped"].startswith("a failed read") and got["requests"] == 2
    t = f"{night['schema']}.gazette_capture_pages"
    assert night["conn"].execute(f"SELECT count(*), bool_and(blocked IS NOT NULL) FROM {t}").fetchone() == (1, True)


def test_an_unreadable_robots_file_means_no_night(night):
    got = night["run"](_Host({2026: ["2026-go9"]}, block_at=1), held=set())
    assert not got["ok"] and "robots" in got["stopped"] and got["requests"] == 1


def test_the_backwalk_closes_a_short_year_and_settles_a_whole_one(night, monkeypatch):
    monkeypatch.setattr(C, "PER_PAGE", 2)
    monkeypatch.setattr(C, "FLOOR_YEAR", 2024)
    years = {2026: ["2026-go9"], 2025: ["2025-go4", "2025-go3", "2025-go2"], 2024: ["2024-go1"]}
    got = night["run"](_Host(years), held={"2026-go9", "2024-go1", "2025-go2"})
    assert got["ok"] and got["new notices"] == 2, got
    settled = dict(night["conn"].execute(f"SELECT year, held FROM {night['schema']}.gazette_capture_years").fetchall())
    assert settled == {2026: 1, 2025: 3, 2024: 1}
    again = night["run"](_Host(years), held=set())
    assert again["requests"] == 2, "robots and the forward page only: every year was settled within the recheck days"
